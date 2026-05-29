from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import settings
from backend.tools.zoho_tools import ACTION_TOOLS, create_task, update_task, delete_task, _fetch_all_projects, list_tasks
from langchain_core.messages import SystemMessage, AIMessage
import json
import re

_llm_with_tools = None

def get_action_llm():
    global _llm_with_tools
    if _llm_with_tools is None:
        llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", google_api_key=settings.GEMINI_API_KEY, temperature=0, max_retries=1)
        _llm_with_tools = llm.bind_tools(ACTION_TOOLS)
    return _llm_with_tools

async def _resolve_project_id(project_id_or_name: str, user_id: str, state: dict) -> tuple[str, str]:
    """
    Given what might be a project name or ID, try to resolve it to (project_id, project_name).
    Returns the validated ID and name, or raises ValueError if not found.
    """
    if not project_id_or_name or str(project_id_or_name).lower() in ("none", ""):
        raise ValueError("no_project")

    # Check if it matches active project (by name OR id)
    active_id = state.get("active_project_id")
    active_name = state.get("active_project_name")
    if active_id and active_name:
        if (project_id_or_name.lower() == active_name.lower() or
                project_id_or_name == active_id):
            return active_id, active_name

    # Check recent_projects cache first
    recent = state.get("recent_projects") or []
    for p in recent:
        if (p["project_name"].lower() == project_id_or_name.lower() or
                p["project_id"] == project_id_or_name):
            return p["project_id"], p["project_name"]

    # As a last resort, fetch from Zoho API directly
    try:
        all_projects = await _fetch_all_projects(user_id)
        for p in all_projects:
            if (p["project_name"].lower() == project_id_or_name.lower() or
                    p["project_id"] == str(project_id_or_name)):
                return p["project_id"], p["project_name"]
    except Exception as e:
        raise ValueError(f"Error fetching projects: {e}")

    raise ValueError(f"Cannot find project: '{project_id_or_name}'")

async def _resolve_task_id(task_name_or_id: str, project_id: str, user_id: str) -> str:
    if not task_name_or_id:
        raise ValueError("No task specified.")
    if str(task_name_or_id).isdigit():
        return str(task_name_or_id)
    
    tasks = await list_tasks.ainvoke({"user_id": user_id, "project_id": project_id})
    for t in tasks:
        if t["task_name"].lower() == str(task_name_or_id).lower():
            return t["task_id"]
    raise ValueError(f"Cannot find task '{task_name_or_id}' in this project.")

async def action_agent_node(state: dict):
    pending = state.get("pending_action")
    confirmed = state.get("confirmed")
    user_id = state.get("user_id")

    if pending is None:
        # ── Mode 1: Planning ─────────────────────────────────────────────
        active_project_name = state.get("active_project_name") or "none"
        active_project_id = state.get("active_project_id") or "none"

        sys_msg = f"""You are a Zoho Projects assistant handling write operations.
You MUST call the correct tool when the user asks to create/update/delete.
The current user_id is {user_id}.
Active project name: {active_project_name}.
Active project ID: {active_project_id}.

IMPORTANT RULES:
- When calling create_task, update_task, or delete_task, pass project_id and task_id as whatever the user mentioned (name or ID). The system will resolve them automatically.
- DO NOT ask the user for an ID if they already gave a name. Use the name directly.
- If the user does not specify a project name, leave project_id blank or pass "none". DO NOT guess the project name.
- DO NOT say you cannot do something. If you have the tool, use it."""

        messages = [SystemMessage(content=sys_msg)] + state["messages"]
        llm_with_tools = get_action_llm()
        response = await llm_with_tools.ainvoke(messages)

        if response.tool_calls:
            tc = response.tool_calls[0]
            params = dict(tc["args"])
            tool_name = tc["name"]

            # ── Python-side resolution ──────────────────────────
            if tool_name in ("create_task", "update_task", "delete_task"):
                raw_proj = params.get("project_id", "")

                # If LLM left project_id blank, try active project
                if not raw_proj or str(raw_proj).lower() in ("none", ""):
                    raw_proj = active_project_id

                try:
                    resolved_id, resolved_name = await _resolve_project_id(raw_proj, user_id, state)
                    params["project_id"] = resolved_id
                    proj_display = resolved_name
                    
                    task_display = params.get("task_name", "")
                    if tool_name in ("update_task", "delete_task"):
                        raw_task = params.get("task_id", "")
                        task_display = raw_task
                        params["task_id"] = await _resolve_task_id(raw_task, resolved_id, user_id)
                        
                except ValueError as e:
                    if "no_project" in str(e):
                        ask_msg = AIMessage(content="Which project should I perform this action in? Please give me the project name.")
                    else:
                        ask_msg = AIMessage(content=str(e) + "\nPlease double-check the name and try again.")
                    return {"messages": [ask_msg], "active_agent": "action_agent"}
            else:
                proj_display = active_project_name
                task_display = ""

            # ── Build readable description ───────────────────────────────
            if tool_name == "create_task":
                desc = f"Create task '{task_display}' in project '{proj_display}'"
            elif tool_name == "update_task":
                desc = f"Update task '{task_display}' in project '{proj_display}'"
            elif tool_name == "delete_task":
                desc = f"Delete task '{task_display}' from project '{proj_display}'"
            else:
                desc = f"Run '{tool_name}' with args {params}"

            pending_action = {"tool": tool_name, "params": params, "description": desc}
            confirm_msg = AIMessage(content=f"I'm about to {desc}. Shall I proceed?")
            return {
                "pending_action": pending_action,
                "confirmed": None,
                "active_agent": "action_agent",
                "messages": [confirm_msg]
            }
        else:
            return {"messages": [response], "active_agent": "action_agent"}

    else:
        # ── Mode 2: Executing ─────────────────────────────────────────────
        if confirmed:
            tool_name = pending["tool"]
            params = dict(pending["params"])
            params["user_id"] = user_id

            tool_map = {
                "create_task": create_task,
                "update_task": update_task,
                "delete_task": delete_task,
            }
            tool_func = tool_map.get(tool_name)
            if not tool_func:
                return {
                    "pending_action": None, "confirmed": None, "active_agent": "action_agent",
                    "messages": [AIMessage(content=f"Unknown tool: {tool_name}")]
                }

            try:
                result = await tool_func.ainvoke(params)
                success_msg = AIMessage(content=f"Done! ✅ {pending['description']}\n\nDetails: {json.dumps(result, indent=2)}")
                return {"pending_action": None, "confirmed": None, "active_agent": "action_agent", "messages": [success_msg]}
            except Exception as e:
                error_msg = AIMessage(content=f"Failed to execute: {str(e)}")
                return {"pending_action": None, "confirmed": None, "active_agent": "action_agent", "messages": [error_msg]}
        else:
            return {
                "pending_action": None, "confirmed": None, "active_agent": "action_agent",
                "messages": [AIMessage(content="Cancelled. No changes were made.")]
            }

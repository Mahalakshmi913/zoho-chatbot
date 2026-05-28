from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import settings
from backend.tools.zoho_tools import ACTION_TOOLS, create_task, update_task, delete_task
from langchain_core.messages import SystemMessage, AIMessage
import json

_llm_with_tools = None

def get_action_llm():
    global _llm_with_tools
    if _llm_with_tools is None:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GEMINI_API_KEY, temperature=0)
        _llm_with_tools = llm.bind_tools(ACTION_TOOLS)
    return _llm_with_tools

async def action_agent_node(state: dict):
    pending = state.get("pending_action")
    confirmed = state.get("confirmed")
    
    if pending is None:
        # Mode 1: Planning
        sys_msg = f"""You are a Zoho Projects assistant handling write operations.
When asked to create/update/delete, identify the exact parameters needed.
If any required parameter is missing (like project_id), ask the user for it before proceeding.
The current user_id is {state.get('user_id')}.
Active project name: {state.get('active_project_name') or "none"}.
Active project ID: {state.get('active_project_id') or "none"}.
If you need project_id and it's not provided or active, ask the user to specify which project."""
        
        messages = [SystemMessage(content=sys_msg)] + state["messages"]
        llm_with_tools = get_action_llm()
        response = await llm_with_tools.ainvoke(messages)
        
        if response.tool_calls:
            tc = response.tool_calls[0]
            # Construct pending action
            pending_action = {
                "tool": tc["name"],
                "params": tc["args"],
                "description": f"{tc['name']} with args {tc['args']}"
            }
            
            # Human readable description
            if tc["name"] == "create_task":
                proj_name = state.get("active_project_name", tc["args"].get("project_id"))
                desc = f"Create task '{tc['args'].get('task_name')}' in project '{proj_name}'"
                pending_action["description"] = desc
            elif tc["name"] == "delete_task":
                desc = f"Delete task ID {tc['args'].get('task_id')}"
                pending_action["description"] = desc
                
            confirm_msg = AIMessage(content=f"I'm about to {pending_action['description']}. Shall I proceed? (yes/no)")
            return {
                "pending_action": pending_action,
                "confirmed": None,
                "messages": [confirm_msg]
            }
        else:
            # LLM just responded (e.g. asking for missing params)
            return {"messages": [response]}
            
    else:
        # Mode 2: Executing
        if confirmed:
            tool_name = pending["tool"]
            params = pending["params"]
            
            # Map tool name to actual function
            tool_map = {
                "create_task": create_task,
                "update_task": update_task,
                "delete_task": delete_task
            }
            tool_func = tool_map[tool_name]
            
            try:
                # Inject user_id which LLM doesn't have in tool calls
                params["user_id"] = state.get("user_id")
                
                # Execute tool
                result = await tool_func.ainvoke(params)
                success_msg = AIMessage(content=f"Action completed successfully! Result:\n{json.dumps(result, indent=2)}")
                return {
                    "pending_action": None,
                    "confirmed": None,
                    "messages": [success_msg]
                }
            except Exception as e:
                error_msg = AIMessage(content=f"Failed to execute action: {str(e)}")
                return {
                    "pending_action": None,
                    "confirmed": None,
                    "messages": [error_msg]
                }
        else:
            cancel_msg = AIMessage(content="Cancelled. No changes have been made.")
            return {
                "pending_action": None,
                "confirmed": None,
                "messages": [cancel_msg]
            }

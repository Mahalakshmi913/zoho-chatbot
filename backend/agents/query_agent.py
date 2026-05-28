from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from backend.config import settings
from backend.tools.zoho_tools import QUERY_TOOLS
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
import json

_query_react_agent = None

def get_query_agent():
    global _query_react_agent
    if _query_react_agent is None:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GEMINI_API_KEY, temperature=0)
        _query_react_agent = create_react_agent(llm, tools=QUERY_TOOLS)
    return _query_react_agent

async def query_agent_node(state: dict):
    query_react_agent = get_query_agent()
    sys_msg = f"""You are a helpful Zoho Projects assistant. You help users query their projects and tasks.
The current user_id is {state.get('user_id')}.
{state.get('long_term_context', '')}
Currently active project: {state.get('active_project_name') or "none selected"}.
When the user refers to "the first one", "that project", or "it", use the active project.
Always be concise. Format task lists as readable text, not raw JSON."""

    input_messages = [SystemMessage(content=sys_msg)] + state["messages"]
    
    response = await query_react_agent.ainvoke({"messages": input_messages})
    new_messages = response["messages"][len(input_messages):]
    
    updates = {"messages": new_messages}
    
    # State update logic: find list_projects output to save recent_projects
    for msg in new_messages:
        if isinstance(msg, ToolMessage) and msg.name == "list_projects":
            try:
                projects = json.loads(msg.content)
                if isinstance(projects, list):
                    updates["recent_projects"] = projects
            except Exception:
                pass
                
    # Update active project if we can infer it
    recent = updates.get("recent_projects") or state.get("recent_projects", [])
    if recent and state["messages"]:
        last_user = state["messages"][-1].content.lower()
        if "first" in last_user and len(recent) > 0:
            updates["active_project_id"] = recent[0]["project_id"]
            updates["active_project_name"] = recent[0]["project_name"]
        elif "second" in last_user and len(recent) > 1:
            updates["active_project_id"] = recent[1]["project_id"]
            updates["active_project_name"] = recent[1]["project_name"]
            
    return updates

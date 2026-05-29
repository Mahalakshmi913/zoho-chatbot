from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from backend.agents.query_agent import query_agent_node
from backend.agents.action_agent import action_agent_node

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    active_project_id: Optional[str]
    active_project_name: Optional[str]
    pending_action: Optional[Dict[str, Any]]
    confirmed: Optional[bool]
    long_term_context: str
    recent_projects: Optional[list[dict]]
    active_agent: Optional[str]

async def router_node(state: AgentState):
    pending = state.get("pending_action")
    confirmed = state.get("confirmed")
    messages = state.get("messages", [])
    
    # If there is a pending action and it hasn't been confirmed yet
    if pending is not None and confirmed is None and messages:
        last_msg = messages[-1].content.lower()
        # Parse yes/no
        is_yes = any(word in last_msg for word in ["yes", "y", "confirm", "proceed", "sure", "ok"])
        is_no = any(word in last_msg for word in ["no", "n", "cancel", "stop", "abort"])
        
        if is_yes:
            return {"confirmed": True}
        else:
            # Default to cancel if not explicitly yes
            return {"confirmed": False}
            
    return {}

def router_condition(state: AgentState) -> str:
    pending = state.get("pending_action")
    if pending is not None:
        # router_node just processed this and set confirmed to True/False
        # Route to action_agent to execute or cancel
        return "action_agent"
        
    messages = state.get("messages", [])
    active_agent = state.get("active_agent")
    
    if messages:
        last_msg = messages[-1].content.lower()
        action_keywords = ["create", "add", "make", "update", "change", "delete", "remove", "assign"]
        if any(keyword in last_msg for keyword in action_keywords):
            return "action_agent"
            
        # If the action agent was active and asked a question in the previous turn
        if active_agent == "action_agent" and len(messages) >= 2:
            prev_msg = messages[-2].content.strip()
            if prev_msg.endswith("?"):
                return "action_agent"
            
    return "query_agent"

builder = StateGraph(AgentState)

builder.add_node("router", router_node)
builder.add_node("query_agent", query_agent_node)
builder.add_node("action_agent", action_agent_node)

builder.add_edge(START, "router")
builder.add_conditional_edges(
    "router", 
    router_condition, 
    {"query_agent": "query_agent", "action_agent": "action_agent"}
)
builder.add_edge("query_agent", END)
builder.add_edge("action_agent", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

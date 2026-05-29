import json
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
from typing import Optional

from backend.config import settings
from backend.auth import token_store, oauth
from backend.memory.memory_store import memory_store
from backend.agents.graph import graph
from langchain_core.messages import HumanMessage

app = FastAPI(title="Zoho Project Chatbot")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# In-memory session store
# This holds the state for each user between HTTP requests.
# Note: For production, this should be backed by Redis or similar.
session_states = {}

ALGORITHM = "HS256"

# Pydantic Models
class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    pending_confirmation: bool
    action_description: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    await token_store.async_init()
    await memory_store.async_init()

# --- Auth Dependency ---
def get_current_user(request: Request) -> str:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid session token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid session token")

# --- Endpoints ---

@app.get("/auth/login")
async def login():
    """Redirects to Zoho OAuth login page."""
    url = oauth.get_auth_url()
    return RedirectResponse(url)

@app.get("/auth/callback")
async def auth_callback(code: str, response: Response):
    """Exchanges code for tokens, creates JWT session."""
    user_id = await oauth.exchange_code(code)
    
    # Create JWT
    token_data = {"sub": user_id}
    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    # Set HttpOnly Cookie
    response = RedirectResponse("http://localhost:3000")
    response.set_cookie(
        key="session", 
        value=token, 
        httponly=True, 
        samesite="lax",
        secure=False # Set to True in prod with HTTPS
    )
    return response

@app.get("/me")
async def get_me(user_id: str = Depends(get_current_user)):
    """Frontend checks this to see if logged in."""
    return {"user_id": user_id, "email": user_id}

@app.post("/auth/logout")
async def logout(response: Response, user_id: str = Depends(get_current_user)):
    """Clears the session cookie."""
    response.delete_cookie("session")
    if user_id in session_states:
        del session_states[user_id]
    return {"status": "logged out"}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user_id: str = Depends(get_current_user)):
    # 1. Ensure token is fresh
    await oauth.refresh_if_needed(user_id)
    
    # 2. Load or initialize session state
    if user_id not in session_states:
        long_term_context = await memory_store.get_context_prompt(user_id)
        session_states[user_id] = {
            "user_id": user_id,
            "messages": [],
            "active_project_id": None,
            "active_project_name": None,
            "pending_action": None,
            "confirmed": None,
            "long_term_context": long_term_context,
            "recent_projects": [],
            "active_agent": None
        }
    
    state = session_states[user_id]
    user_msg = req.message.strip()
    
    # 3. Detect Yes/No for Human-in-the-loop (HIL)
    if state.get("pending_action"):
        msg_lower = user_msg.lower()
        if msg_lower in ["yes", "y", "confirm", "proceed", "do it"]:
            state["confirmed"] = True
        elif msg_lower in ["no", "n", "cancel", "stop", "abort"]:
            state["confirmed"] = False
            # Clear it immediately to reset
            state["pending_action"] = None
            
    # 4. Append message and invoke graph
    state["messages"].append(HumanMessage(content=user_msg))
    
    config = {"configurable": {"thread_id": req.session_id}}
    try:
        result = await asyncio.wait_for(
            graph.ainvoke(state, config=config),
            timeout=60.0  # 60-second hard timeout
        )
    except asyncio.TimeoutError:
        return ChatResponse(
            response="Sorry, the request timed out. The AI model may be rate-limited. Please wait a moment and try again.",
            pending_confirmation=False,
            action_description=None
        )
    except Exception as e:
        return ChatResponse(
            response=f"Sorry, an error occurred: {str(e)[:200]}. Please try again.",
            pending_confirmation=False,
            action_description=None
        )
    
    # 5. Save updated state back to dict
    session_states[user_id] = result
    
    # 6. Save long-term memory (Session end/update simulation)
    # For a real app, this might be debounced or done on actual session termination
    await memory_store.update_from_state(user_id, result)
    
    # 7. Construct response
    last_message = result["messages"][-1].content
    if isinstance(last_message, list):
        last_message = " ".join([part.get("text", "") for part in last_message if isinstance(part, dict) and "text" in part]) or str(last_message)
    elif not isinstance(last_message, str):
        last_message = str(last_message)
    pending = result.get("pending_action")
    
    action_desc = None
    if pending:
        action_desc = pending.get("description", "A pending action requires your approval.")
        
    return ChatResponse(
        response=last_message,
        pending_confirmation=pending is not None,
        action_description=action_desc
    )

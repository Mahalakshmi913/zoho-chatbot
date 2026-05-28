from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from backend.auth.token_store import TokenStore
from backend.auth.zoho_oauth import ZohoOAuth
from backend.config import settings

app = FastAPI()

token_store = TokenStore(settings.DATABASE_URL)
oauth = ZohoOAuth(token_store)

@app.on_event("startup")
async def startup():
    await token_store.async_init()

@app.get("/auth/login")
def login():
    return RedirectResponse(oauth.get_auth_url())

@app.get("/auth/callback")
async def callback(code: str):
    user_id = await oauth.exchange_code(code)
    return {"message": "Successfully authenticated and tokens saved!", "user_id": user_id}

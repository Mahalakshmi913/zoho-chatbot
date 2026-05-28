import httpx
from urllib.parse import urlencode
from backend.config import settings
from backend.auth.token_store import TokenStore
from backend.zoho_client import ZohoAuthError

class ZohoOAuth:
    def __init__(self, token_store: TokenStore):
        self.token_store = token_store
        
    async def _fetch_token_data(self, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{settings.ZOHO_ACCOUNTS_URL}/oauth/v2/token", data=data)
            if not resp.is_success:
                raise ZohoAuthError(f"Token request failed: {resp.text}")
                
            token_data = resp.json()
            if "error" in token_data:
                raise ZohoAuthError(f"OAuth Error: {token_data}")
            return token_data
        
    def get_auth_url(self) -> str:
        params = {
            "client_id": settings.ZOHO_CLIENT_ID,
            "redirect_uri": settings.ZOHO_REDIRECT_URI,
            "scope": "ZohoProjects.portals.READ,ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.users.READ",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"{settings.ZOHO_ACCOUNTS_URL}/oauth/v2/auth?{urlencode(params)}"
        
    async def exchange_code(self, code: str) -> str:
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.ZOHO_CLIENT_ID,
            "client_secret": settings.ZOHO_CLIENT_SECRET,
            "redirect_uri": settings.ZOHO_REDIRECT_URI,
            "code": code
        }
        
        token_data = await self._fetch_token_data(data)
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token", "")
        expires_in = token_data["expires_in"]
        
        async with httpx.AsyncClient() as client:
            # Immediately call portals to get portal_name and user email
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            portal_resp = await client.get(f"{settings.ZOHO_PROJECTS_URL}/restapi/portals/", headers=headers)
            
            if not portal_resp.is_success:
                raise Exception(f"Failed to fetch portals: {portal_resp.text}")
                
            portals_data = portal_resp.json()
            if not portals_data.get("portals"):
                raise Exception("User has no Zoho Projects portals.")
                
            # Default to the first portal
            portal = portals_data["portals"][0]
            zoho_portal = portal["id_string"]
            
            # If login_id is missing, let's query the portal users list
            user_id = portal.get("login_id")
            if not user_id:
                users_resp = await client.get(f"{settings.ZOHO_PROJECTS_URL}/restapi/portal/{zoho_portal}/users/", headers=headers)
                if users_resp.is_success:
                    users_data = users_resp.json()
                    for u in users_data.get("users", []):
                        if u.get("email"):
                            user_id = u["email"]
                            break
            
            # Fallback to default_user only if absolutely everything fails
            if not user_id:
                user_id = "default_user"
            
            # Save to TokenStore
            await self.token_store.save_tokens(
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in_seconds=expires_in,
                zoho_portal=zoho_portal
            )
            
            return user_id

    async def refresh_if_needed(self, user_id: str):
        is_expired = await self.token_store.is_expired(user_id)
        if not is_expired:
            return
            
        record = await self.token_store.get_tokens(user_id)
        if not record or not record.refresh_token:
            raise ZohoAuthError("No refresh token available. User must log in again.")
            
        data = {
            "grant_type": "refresh_token",
            "client_id": settings.ZOHO_CLIENT_ID,
            "client_secret": settings.ZOHO_CLIENT_SECRET,
            "refresh_token": record.refresh_token
        }
        
        token_data = await self._fetch_token_data(data)
        new_access_token = token_data["access_token"]
        expires_in = token_data["expires_in"]
            
        await self.token_store.save_tokens(
            user_id=user_id,
            access_token=new_access_token,
            refresh_token=record.refresh_token,
            expires_in_seconds=expires_in,
            zoho_portal=record.zoho_portal
        )

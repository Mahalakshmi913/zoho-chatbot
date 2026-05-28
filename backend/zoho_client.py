import httpx
from typing import Optional, Dict, Any
from backend.config import settings

class ZohoAuthError(Exception):
    """Raised when Zoho returns a 401 Unauthorized, indicating token expiration or invalidity."""
    pass

class ZohoAPIError(Exception):
    """Raised for 4xx and 5xx errors from the Zoho API."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Zoho API Error {status_code}: {message}")

class ZohoClient:
    def __init__(self, access_token: str, portal_name: str = None):
        self.access_token = access_token
        self.portal_name = portal_name or settings.ZOHO_PORTAL_NAME
        # Base URL pattern: https://projectsapi.zoho.com/restapi/portal/{portal_name}
        self.base_url = f"{settings.ZOHO_PROJECTS_URL}/restapi/portal/{self.portal_name}".rstrip("/")
        
        self.headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=self.headers, **kwargs)
            
            if response.status_code == 401:
                raise ZohoAuthError("Unauthorized: Invalid or expired access token.")
            
            if not response.is_success:
                raise ZohoAPIError(response.status_code, response.text)
                
            # For 204 No Content or empty responses
            if not response.text:
                return {}
                
            return response.json()

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, data: Dict[str, Any]) -> Any:
        return await self._request("POST", path, json=data)

    async def patch(self, path: str, data: Dict[str, Any]) -> Any:
        return await self._request("PATCH", path, json=data)

    async def delete(self, path: str) -> Any:
        return await self._request("DELETE", path)

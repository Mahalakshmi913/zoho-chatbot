from backend.config import settings
from .token_store import TokenStore
from .zoho_oauth import ZohoOAuth

token_store = TokenStore(settings.DATABASE_URL)
oauth = ZohoOAuth(token_store)

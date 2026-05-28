from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    ZOHO_CLIENT_ID: str = ""
    ZOHO_CLIENT_SECRET: str = ""
    ZOHO_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    ZOHO_PORTAL_NAME: str = ""
    GEMINI_API_KEY: str = ""
    SECRET_KEY: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    
    # Allow switching region if the user is on zoho.in, zoho.eu, etc.
    ZOHO_ACCOUNTS_URL: str = "https://accounts.zoho.com"
    ZOHO_PROJECTS_URL: str = "https://projectsapi.zoho.com"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

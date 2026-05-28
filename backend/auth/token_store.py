from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.dialects.sqlite import insert
from datetime import datetime, timedelta
from typing import Optional

Base = declarative_base()

class TokenRecord(Base):
    __tablename__ = "oauth_tokens"
    
    user_id: Mapped[str] = mapped_column(primary_key=True)
    access_token: Mapped[str]
    refresh_token: Mapped[str]
    expires_at: Mapped[datetime]
    zoho_portal: Mapped[Optional[str]]

class TokenStore:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def async_init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def save_tokens(
        self, 
        user_id: str, 
        access_token: str, 
        refresh_token: str, 
        expires_in_seconds: int,
        zoho_portal: str = None
    ):
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        
        async with self.SessionLocal() as session:
            stmt = insert(TokenRecord).values(
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                zoho_portal=zoho_portal
            )
            # Upsert logic for SQLite
            stmt = stmt.on_conflict_do_update(
                index_elements=['user_id'],
                set_={
                    'access_token': stmt.excluded.access_token,
                    'refresh_token': stmt.excluded.refresh_token,
                    'expires_at': stmt.excluded.expires_at,
                    # Only update zoho_portal if provided, otherwise preserve existing
                    'zoho_portal': stmt.excluded.zoho_portal
                }
            )
            await session.execute(stmt)
            await session.commit()
            
    async def get_tokens(self, user_id: str) -> Optional[TokenRecord]:
        async with self.SessionLocal() as session:
            result = await session.get(TokenRecord, user_id)
            return result
            
    async def delete_tokens(self, user_id: str):
        async with self.SessionLocal() as session:
            record = await session.get(TokenRecord, user_id)
            if record:
                await session.delete(record)
                await session.commit()
                
    async def is_expired(self, user_id: str) -> bool:
        record = await self.get_tokens(user_id)
        if not record:
            return True
        # 5 minutes buffer before actual expiration
        return datetime.utcnow() >= (record.expires_at - timedelta(minutes=5))

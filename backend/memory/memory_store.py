from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import select
from datetime import datetime
import json
from typing import Dict, Any
from backend.config import settings
import logging

Base = declarative_base()

class MemoryRecord(Base):
    __tablename__ = "memory_store"
    
    user_id: Mapped[str] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str]
    updated_at: Mapped[datetime]

class MemoryStore:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def async_init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def save(self, user_id: str, key: str, value: Any):
        value_str = json.dumps(value)
        updated_at = datetime.utcnow()
        
        async with self.SessionLocal() as session:
            stmt = insert(MemoryRecord).values(
                user_id=user_id,
                key=key,
                value=value_str,
                updated_at=updated_at
            )
            # Upsert logic for SQLite
            stmt = stmt.on_conflict_do_update(
                index_elements=['user_id', 'key'],
                set_={
                    'value': stmt.excluded.value,
                    'updated_at': stmt.excluded.updated_at
                }
            )
            await session.execute(stmt)
            await session.commit()
            
    async def load(self, user_id: str) -> Dict[str, Any]:
        async with self.SessionLocal() as session:
            stmt = select(MemoryRecord).where(MemoryRecord.user_id == user_id)
            result = await session.execute(stmt)
            records = result.scalars().all()
            
            return {r.key: json.loads(r.value) for r in records}
            
    async def get_context_prompt(self, user_id: str) -> str:
        data = await self.load(user_id)
        if not data:
            return ""
            
        prompt = "User context from previous sessions:\n"
        
        if "frequent_projects" in data:
            fp = data["frequent_projects"]
            if fp and isinstance(fp, dict):
                most_accessed = max(fp.items(), key=lambda x: x[1])
                prompt += f"- Most accessed project: {most_accessed[0]} (accessed {most_accessed[1]} times)\n"
                
        if "last_query" in data:
            prompt += f"- Last session focus: {data['last_query']}\n"
            
        if "preferences" in data:
            for p in data["preferences"]:
                prompt += f"- Preferred style: {p}\n"
                
        return prompt

    async def update_from_state(self, user_id: str, state: dict):
        """Helper to extract and save memory bits from the current state"""
        # Save last accessed project
        if state.get("active_project_name"):
            data = await self.load(user_id)
            fp = data.get("frequent_projects", {})
            proj_name = state["active_project_name"]
            fp[proj_name] = fp.get(proj_name, 0) + 1
            await self.save(user_id, "frequent_projects", fp)
            
        # Save last query
        messages = state.get("messages", [])
        if messages:
            for msg in reversed(messages):
                if msg.type == "human":
                    await self.save(user_id, "last_query", msg.content)
                    break
                    
        # Naive preference extraction 
        if messages:
            data = await self.load(user_id)
            prefs = data.get("preferences", [])
            for msg in messages:
                if msg.type == "human":
                    content = msg.content.lower()
                    if "always" in content or "prefer" in content or "only show" in content:
                        if content not in prefs:
                            prefs.append(content)
            
            if prefs:
                await self.save(user_id, "preferences", prefs)

# Global instance for use across the app
memory_store = MemoryStore(settings.DATABASE_URL)

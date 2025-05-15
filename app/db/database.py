from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import asyncio
from app.db.base import Base
from app.db import models  # Ensure models are imported so tables are registered

# DATABASE_URL = "sqlite+aiosqlite:///./test.db"  # Use async SQLite driver
DATABASE_URL = "postgresql+asyncpg://postgres:vek422@localhost:5432/ai_quiz"

engine = create_async_engine(
    DATABASE_URL
)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def async_create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(async_create_all())

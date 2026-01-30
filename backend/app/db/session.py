"""
Database Session Management

Async SQLAlchemy session with SQLite (dev) or PostgreSQL (prod).
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from app.config import settings
from app.db.models import Base


# Create async engine
# SQLite for development, PostgreSQL for production
if settings.database_url.startswith("sqlite"):
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args={"check_same_thread": False},
    )
else:
    # Ensure postgresql:// schema (SQLAlchemy doesn't support postgres:// anymore)
    db_url = settings.database_url
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Check for sslmode in the URL and handle it for asyncpg
    connect_args = {}
    if "sslmode=" in db_url:
        # Simple string check first to avoid imports if not needed, 
        # but for robustness we should probably handle it properly or just strip it.
        # However, a cleaner way for asyncpg is to pass ssl context or string in connect_args.
        # Render/Neon usually sends ?sslmode=require
        
        # We need to strip sslmode from db_url because SQLAlchemy/asyncpg will try to pass it as kwarg
        # and asyncpg doesn't accept 'sslmode'
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(db_url)
        qs = parse_qs(parsed.query)
        
        if "sslmode" in qs:
            ssl_mode = qs.pop("sslmode")[0]
            if ssl_mode == "require":
                connect_args["ssl"] = "require"
            
            # Rebuild URL without sslmode
            new_query = urlencode(qs, doseq=True)
            parsed = parsed._replace(query=new_query)
            db_url = urlunparse(parsed)

    engine = create_async_engine(
        db_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args=connect_args,
    )

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Initialize the database, creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for FastAPI routes.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

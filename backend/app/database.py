from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base
from app.config import settings

# Convert postgresql:// to postgresql+asyncpg:// for async
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Determine if we're using SQLite (single connection) or PostgreSQL (pooled)
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # SQLite doesn't support connection pooling well - use NullPool
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
    )
    # Replica uses same connection for SQLite
    replica_engine = engine
else:
    # PostgreSQL with proper connection pooling for production
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
        # Connection pool settings from config
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
    )

    # Read replica engine (if configured)
    if settings.DATABASE_REPLICA_URL:
        replica_url = settings.DATABASE_REPLICA_URL.replace("postgresql://", "postgresql+asyncpg://")
        replica_engine = create_async_engine(
            replica_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=settings.DATABASE_POOL_SIZE // 2,  # Smaller pool for replica
            max_overflow=settings.DATABASE_MAX_OVERFLOW // 2,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
        )
    else:
        # No replica configured - use primary for reads
        replica_engine = engine

# Primary session factory (writes)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Replica session factory (reads)
AsyncReplicaSessionLocal = async_sessionmaker(
    replica_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """Get primary database session (for writes)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_replica_db() -> AsyncSession:
    """Get replica database session (for reads/analytics).

    Use this for read-only queries like analytics, reports, dashboards.
    Falls back to primary if no replica configured.
    """
    async with AsyncReplicaSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database - migrations are managed by Alembic, not this function.

    For initial setup or development with fresh database, use:
        alembic upgrade head

    For production, always use Alembic migrations.
    """
    # Migrations are handled by Alembic, not create_all
    # This function kept for backwards compatibility during transition
    pass

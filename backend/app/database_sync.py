from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Sync engine for initial setup
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
SyncSessionLocal = sessionmaker(bind=sync_engine)

def run_migrations():
    """Run SQL initialization script"""
    with open("app/init.sql", "r") as f:
        sql = f.read()

    with sync_engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()

# Import text for SQL execution
from sqlalchemy import text
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings

# 1. Configuration Handling
class Settings(BaseSettings):
    # This looks for DATABASE_URL in your .env (local) or Railway Variables (production)
    database_url: str = os.getenv("DATABASE_URL")

    class Config:
        # Tells pydantic to look for a .env file if it exists
        env_file = ".env"

settings = Settings()

# 2. Universal Engine Logic
# Checks if we are using Postgres (Supabase) or MSSQL (Azure)
if settings.database_url and settings.database_url.startswith("postgresql"):
    # pool_pre_ping=True is critical for Supabase to handle idle connection timeouts
    engine = create_engine(
        settings.database_url, 
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
elif settings.database_url and settings.database_url.startswith("mssql"):
    # Logic for future Azure SQL migration
    engine = create_engine(settings.database_url, echo=False)
else:
    # Fallback for local dev if no DATABASE_URL is found
    print("Warning: DATABASE_URL not found. Falling back to local SQLite.")
    engine = create_engine("sqlite:///./ascenda_local.db", connect_args={"check_same_thread": False})

# 3. Session and Base Setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models.py to inherit from
Base = declarative_base()

# 4. FastAPI Dependency
def get_db():
    """
    Creates a new database session for each request and closes it after.
    This ensures we don't leak connections on Supabase's free tier.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
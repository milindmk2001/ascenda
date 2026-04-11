import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings

# 1. Configuration Handling (Pydantic V2 Style)
class Settings(BaseSettings):
    """
    Handles loading credentials. 
    It will prioritize Railway/System environment variables, 
    then look at a .env file if it exists.
    """
    # database_url is optional to prevent crash-on-start if env-vars are loading slowly
    database_url: str | None = os.getenv("DATABASE_URL")

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

# Initialize settings
settings = Settings()

# 2. Universal Engine Logic
# This block ensures "Zero Code Changes" when migrating to Azure SQL in the future.
if settings.database_url and settings.database_url.startswith("postgresql"):
    # Settings optimized for Supabase/Postgres
    engine = create_engine(
        settings.database_url, 
        pool_pre_ping=True,  # Checks if connection is alive before using it
        pool_size=5,         # Efficient for Railway's shared resources
        max_overflow=10
    )
elif settings.database_url and settings.database_url.startswith("mssql"):
    # Logic for future Azure SQL (T-SQL) migration
    engine = create_engine(settings.database_url, echo=False)
else:
    # Fallback for local development or if Railway variables are misconfigured
    print("⚠️ WARNING: DATABASE_URL not found or invalid. Falling back to local SQLite.")
    engine = create_engine(
        "sqlite:///./ascenda_local.db", 
        connect_args={"check_same_thread": False}
    )

# 3. Session and Base Setup
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models.py to inherit from
Base = declarative_base()

# 4. FastAPI Dependency
def get_db():
    """
    Database session lifecycle management.
    Ensures every request gets a fresh connection and closes it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
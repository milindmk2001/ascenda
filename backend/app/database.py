import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str | None = os.getenv("DATABASE_URL")

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
        "env_file_encoding": "utf-8"
    }

settings = Settings()

# SQLAlchemy Setup
if settings.database_url and "postgresql" in settings.database_url:
    # Fixed syntax error (added missing comma)
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        echo=True,        # Added missing comma here
        max_overflow=10,
        pool_recycle=300 
    )
else:
    # Fallback for local development
    engine = create_engine(
        "sqlite:///./ascenda_local.db", 
        connect_args={"check_same_thread": False}
    )

# These are required by your curriculum.py and courses.py files
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
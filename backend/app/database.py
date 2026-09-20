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

# Resolve URL from BaseSettings or direct environment
db_url = settings.database_url or os.getenv("DATABASE_URL")

# SQLAlchemy Connection Setup
if db_url and ("postgresql" in db_url or "postgres" in db_url):
    # Fix legacy dialect prefix if present
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=5,
        echo=True,
        max_overflow=10,
        pool_recycle=300
    )
else:
    engine = create_engine(
        "sqlite:///./ascenda_local.db", 
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
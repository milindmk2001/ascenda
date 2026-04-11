import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # This change ensures we check the OS environment directly
    database_url: str | None = os.getenv("DATABASE_URL")

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
        "env_file_encoding": "utf-8"
    }

settings = Settings()

# Debug print (will show in Railway logs to confirm the URL is being picked up)
if settings.database_url:
    print(f"✅ Database URL detected: {settings.database_url[:20]}...")
else:
    print("❌ DATABASE_URL is still None")

# SQLAlchemy Connection
if settings.database_url and "postgresql" in settings.database_url:
    # Supabase Transaction Pooler (Port 6543) requires specific handling
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        # Force the driver to stay alive for cloud environments
        pool_recycle=300 
    )
else:
    print("⚠️ WARNING: Falling back to local SQLite.")
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
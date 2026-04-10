from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    CORS_ORIGINS: str = "https://ascenda-umber.vercel.app"
    DEBUG: bool = False  # <--- Add this line!

    class Config:
        env_file = ".env"

settings = Settings()
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    # Default to your Vercel URL if the env var is missing
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://ascenda-umber.vercel.app").split(",")
    PORT = int(os.getenv("PORT", 8000))
    # This is the line your main.py is dying for:
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

settings = Settings()
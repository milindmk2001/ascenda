import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our database engine and base for startup initialization
from .database import engine
from . import models

# Import our modular routers
from .routers import organizations, courses

# --- Database Initialization ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ascenda Admin API",
    description="Core API for managing Boards, Exams, and Course Content",
    version="1.0.0"
)

# --- CORS Configuration ---
# We combine hardcoded defaults with the environment variable from Railway
raw_origins = os.getenv("CORS_ORIGINS", "https://ascenda-umber.vercel.app")
origins = [origin.strip() for origin in raw_origins.split(",")]

# Always include local development URLs
origins.extend([
    "http://localhost:3000",
    "http://localhost:5173",
    "https://ascenda-umber.vercel.app"
])

# Remove duplicates
origins = list(set(origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    # This is important for cloud deployments to prevent 
    # the browser from losing the handshake.
    expose_headers=["*"],
)

# --- Router Registration ---
app.include_router(organizations.router)
app.include_router(courses.router)

@app.get("/")
def health_check():
    return {
        "status": "Online",
        "system": "Ascenda Modular Backend",
        "allowed_origins": origins, # Useful for debugging in the browser
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "production")
    }

# --- Optional: Custom Error Handlers ---
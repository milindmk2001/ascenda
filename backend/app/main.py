import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our database engine and base for startup initialization
from .database import engine
from . import models

# Import our modular routers
from .routers import organizations, courses

# --- Database Initialization ---
# This ensures that even if you add new columns later, 
# SQLAlchemy will try to sync the schema on startup.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ascenda Admin API",
    description="Core API for managing Boards, Exams, and Course Content",
    version="1.0.0"
)

# --- CORS Configuration ---
# This allows your Vercel frontend (ascenda-umber.vercel.app) 
# to make requests to this Railway backend.
# --- CORS Configuration ---
origins = [
    "http://localhost:3000",
    "http://localhost:5173",          # Added for Vite local dev
    "https://ascenda-umber.vercel.app" # Your production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # This must match your Vercel URL exactly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Router Registration ---
# Each router handles a specific domain of the admin panel
app.include_router(organizations.router)
app.include_router(courses.router)

@app.get("/")
def health_check():
    """
    Standard health check to confirm the backend is live 
    and identify the environment.
    """
    return {
        "status": "Online",
        "system": "Ascenda Modular Backend",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development")
    }

# --- Optional: Custom Error Handlers could go here ---
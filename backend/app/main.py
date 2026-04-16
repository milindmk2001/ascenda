import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our database engine and base for startup initialization
from .database import engine
from . import models

# Import modular routers
from .routers import organizations, courses, curriculum

# --- Database Initialization ---
# This creates tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ascenda Admin API",
    description="Core API for managing Boards, Exams, and Course Content",
    version="1.0.0"
)

# --- CORS Configuration ---
# Allows your Vercel frontend and local development to communicate with this API
raw_origins = os.getenv("CORS_ORIGINS", "https://ascenda-umber.vercel.app")
origins = [origin.strip() for origin in raw_origins.split(",")]

# Include local development URLs
origins.extend([
    "http://localhost:3000",
    "http://localhost:5173",
    "https://ascenda-umber.vercel.app"
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# --- Router Registration ---
app.include_router(organizations.router)
app.include_router(courses.router)
app.include_router(curriculum.router)

@app.get("/")
def health_check():
    return {
        "status": "online", 
        "database": "connected" if engine else "error",
        "version": "1.0.0"
    }
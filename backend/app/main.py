import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine  # Changed from .database
from app import models           # Changed from .
from app.routers import organizations, curriculum, studio, ai_tutor 

# Initialize database tables
# This creates tables in your Railway PostgreSQL instance based on models.py
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ascenda API")

# CORS Middleware
# Essential for your Vercel frontend to talk to your Railway backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
# These map your modular files to actual URL endpoints
app.include_router(organizations.router)
app.include_router(curriculum.router)
app.include_router(studio.router)
app.include_router(ai_tutor.router)

@app.get("/")
def health():
    """Quick check to see if the API is alive and the DB is reachable."""
    return {
        "status": "active", 
        "project": "Ascenda",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development")
    }
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

# Import our database logic and models using the apps folder context
from backend.apps.database import get_db
from backend.apps import models

app = FastAPI(title="Ascenda API")

# --- CORS CONFIGURATION ---
# Vital for Vercel (Frontend) to communicate with Railway (Backend)
origins = [
    "http://localhost:3000",           # Local React
    "https://ascenda-umber.vercel.app"  # Your Vercel URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {
        "status": "Online",
        "app": "Ascenda Backend",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }

@app.get("/api/home/categories")
def get_categories(db: Session = Depends(get_db)):
    """
    Fetches all Organizations (Boards/Exams).
    This handles the logic for the Home Page selection bar.
    """
    # Using SQLAlchemy ORM for Azure compatibility
    organizations = db.query(models.Organization).all()
    
    return [
        {
            "id": str(org.id), 
            "name": org.name, 
            "type": org.org_type,
            "icon": org.icon_url
        } 
        for org in organizations
    ]

@app.get("/api/home/featured-courses")
def get_featured_courses(db: Session = Depends(get_db)):
    """
    Fetches courses where is_featured = True for the Byju's style carousel.
    """
    featured = db.query(models.Course).filter(models.Course.is_featured == True).all()
    
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "description": c.description,
            "thumbnail": c.thumbnail_url,
            "rigor": c.rigor_level
        }
        for c in featured
    ]
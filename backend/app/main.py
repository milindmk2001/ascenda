import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine  
from app import models           
from app.routers import curriculum, organizations, studio, ai_tutor 

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ascenda API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(organizations.router)
app.include_router(curriculum.admin_router)
app.include_router(curriculum.router)
app.include_router(studio.router)
app.include_router(ai_tutor.router)

@app.get("/")
def health():
    return {
        "status": "active", 
        "project": "Ascenda",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development")
    }
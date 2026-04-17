import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import organizations, courses, curriculum

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ascenda API")

# Widen CORS for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporarily allow all to bypass CORS false positives
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(organizations.router)
app.include_router(courses.router)
app.include_router(curriculum.router)
app.include_router(studio.router)   # For Content Studio
app.include_router(ai_tutor.router) # For AI Tutor Chat

@app.get("/")
def health():
    return {"status": "active", "db": "connected"}
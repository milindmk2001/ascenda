import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
# Consistent absolute import mapping matching the rest of the application ecosystem
from app.routers import organizations, curriculum, studio, ai_tutor, visual_lesson 

app = FastAPI(title="Ascenda API")

# Setup clean explicit allowed frontend production URLs
origins = [
    "https://ascenda-umber.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
) # ✅ Closed cleanly with correct parenthesis

# ── ROUTE MOUNTING REGISTRATION ───────────────────────────
app.include_router(organizations.router)
app.include_router(curriculum.admin_router) # Mounts /api/admin/curriculum
app.include_router(curriculum.router)       # Mounts /api/curriculum
app.include_router(studio.router)
app.include_router(ai_tutor.router)         # Mounts /api/ai_tutor
app.include_router(visual_lesson.router)    # Mounts /api/visual-lesson

@app.get("/")
def health():
    return {
        "status": "healthy",
        "engine": "Ascenda Dynamic Core Engine V2"
    }
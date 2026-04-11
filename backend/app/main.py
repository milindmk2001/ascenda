import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# These imports look for the files inside your new 'routers' folder
from .routers import organizations, courses

app = FastAPI(
    title="Ascenda Admin API",
    description="Modular API for managing Boards, Exams, and Course Content",
    version="1.0.0"
)

# --- CORS CONFIGURATION ---
# Vital for allowing your Vercel frontend to talk to this Railway backend
origins = [
    "http://localhost:3000",
    "https://ascenda-umber.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTER ROUTERS ---
# This pulls in all the CRUD logic we wrote in the separate files
app.include_router(organizations.router)
app.include_router(courses.router)

@app.get("/")
def health_check():
    """
    Root endpoint to verify the API is online and 
    confirming the environment (Local vs Production).
    """
    return {
        "status": "Online",
        "system": "Ascenda Modular Backend",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }
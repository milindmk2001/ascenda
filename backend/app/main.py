import random
import os
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .core.config import settings
from .services.prompt_service import PromptService

app = FastAPI(title="Ascenda API")

# --- CORS CONFIGURATION ---
# We split the string from Railway (e.g., "url1,url2") into a Python List
raw_origins = os.getenv("CORS_ORIGINS", "")
origins_list = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI CONFIGURATION ---
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Request model for the chat endpoint
class ChatRequest(BaseModel):
    message: str

# --- ROUTES ---

@app.get("/")
async def root():
    return {"status": "Online", "message": "Physics API is active"}

@app.post("/api/chat")
async def chat_lesson(request: ChatRequest):
    """
    This matches the 'fetch' call in your App.jsx
    """
    # We use the user's message to guide the AI
    response = model.generate_content(request.message)
    return {"response": response.text}

@app.get("/lesson/coulombs-law")
async def get_coulombs_law():
    scenario = random.choice(["attraction", "repulsion"])
    prompt = PromptService.get_coulombs_law_prompt(scenario)
    response = model.generate_content(prompt)
    return PromptService.clean_ai_response(response.text)
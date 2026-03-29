import random
import os
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .core.config import settings

app = FastAPI(title="Ascenda API")

# FOR TESTING: Use the Wildcard to bypass all CORS checks
# If this works, we know the "guest list" was just messy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False, # Must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI CONFIGURATION
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"status": "Online"}

@app.post("/api/chat")
async def chat_lesson(request: ChatRequest):
    try:
        response = model.generate_content(request.message)
        return {"response": response.text}
    except Exception as e:
        return {"response": f"AI Error: {str(e)}"}
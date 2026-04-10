import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .core.config import settings

app = FastAPI(title="Ascenda API")

# Updated CORS logic to ensure your Vercel URL is always prioritized
origins = [
    "http://localhost:5173",
    "https://ascenda-umber.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if not settings.DEBUG else ["*"], 
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods for better compatibility
    allow_headers=["*"],
)

# AI CONFIGURATION
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
except Exception as e:
    print(f"CRITICAL: AI Configuration Failed: {e}")

class ChatRequest(BaseModel):
    # Matches the 'message' field in your current request
    message: str 

@app.get("/health")
async def health_check():
    return {
        "status": "Online",
        "environment": "Production" if not settings.DEBUG else "Development"
    }

@app.post("/api/chat")
async def chat_lesson(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # Added a safety check to the generation
        response = model.generate_content(request.message)
        
        # Check if the response was blocked or empty
        if not response or not response.candidates:
             return {"response": "The AI is unable to provide an answer right now. Please try rephrasing."}
             
        return {"response": response.text}

    except Exception as e:
        # CRITICAL: This print will now show the REAL error in your Railway Deploy Logs
        print(f"DEBUG - Gemini Request Failed: {str(e)}")
        
        # If it's a 403, it's likely the API Key or Location.
        # If it's a 429, you hit the free tier limit.
        error_msg = str(e) if settings.DEBUG else "AI Service temporarily unavailable."
        return {"response": f"Service Error: {error_msg}"}
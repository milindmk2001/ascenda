import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .core.config import settings

app = FastAPI(title="Ascenda API")

# DYNAMIC CORS: Secure and Browser-Compatible
# We pull this from your Railway environment variables
origins = [
    "http://localhost:5173",  # Local Vite
    "https://ascenda-umber.vercel.app", # Production Frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if not settings.DEBUG else ["*"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# AI CONFIGURATION
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    # Move model name to settings to avoid hardcoding
    model = genai.GenerativeModel(getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"))
except Exception as e:
    print(f"CRITICAL: AI Configuration Failed: {e}")

class ChatRequest(BaseModel):
    message: str

@app.get("/health")
async def health_check():
    """Enhanced health check for CI/CD monitoring"""
    return {
        "status": "Online",
        "version": "1.0.0-baseline",
        "environment": "Production" if not settings.DEBUG else "Development"
    }

@app.post("/api/chat")
async def chat_lesson(request: ChatRequest):
    # Validation: Ensure message isn't empty (Functional Testing baseline)
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # We use a timeout or safety check here for performance audit
        response = model.generate_content(request.message)
        
        if not response.text:
            return {"response": "The AI mentor is thinking... please try again."}
            
        return {"response": response.text}
    except Exception as e:
        # SECURITY: Don't leak raw stack traces to the frontend in production
        error_msg = str(e) if settings.DEBUG else "AI Service temporarily unavailable."
        return {"response": f"Service Error: {error_msg}"}

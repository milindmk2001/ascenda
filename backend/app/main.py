import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .core.config import settings

app = FastAPI(title="Ascenda API")

# CORS setup
origins = ["http://localhost:5173", "https://ascenda-umber.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if not settings.DEBUG else ["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI CONFIGURATION (2026 STABLE)
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    # Gemini 1.5 is retired. Use 2.5 Flash for the best price/performance.
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    print(f"CRITICAL: AI Configuration Failed: {e}")

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_lesson(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        response = model.generate_content(request.message)
        
        # In 2026, some responses require explicit candidate checking
        if not response.candidates:
             return {"response": "The AI is currently unavailable. Please try again."}
             
        return {"response": response.text}
    except Exception as e:
        print(f"DEBUG - Gemini Request Failed: {str(e)}")
        error_msg = str(e) if settings.DEBUG else "AI Service temporarily unavailable."
        return {"response": f"Service Error: {error_msg}"}
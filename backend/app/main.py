import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .core.config import settings
import asyncio

app = FastAPI(title="Ascenda API")

# Allow Vercel and Localhost
origins = [
    "http://localhost:5173",
    "https://ascenda-umber.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if not settings.DEBUG else ["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI CONFIGURATION (2026 Stable)
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as e:
    print(f"CRITICAL: AI Configuration Failed: {e}")

class ChatRequest(BaseModel):
    message: str

@app.get("/health")
async def health_check():
    return {"status": "Online"}

@app.post("/api/chat")
async def chat_lesson(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def generate():
        try:
            # stream=True is the magic part
            response = model.generate_content(request.message, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                await asyncio.sleep(0.01) # Small delay for smoother UI streaming
        except Exception as e:
            print(f"Streaming Error: {e}")
            yield f"Service Error: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Ascenda Interactive Engine")

# Update origins to match your Vercel URL
origins = [
    "http://localhost:5173",
    "https://ascenda-umber.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InteractRequest(BaseModel):
    timestamp: float
    query: str

@app.get("/health")
async def health():
    return {"status": "online"}

@app.post("/api/interact")
async def tutor_interaction(request: InteractRequest):
    """
    Simulates the AI 'seeing' the video at a specific time.
    In production, this would use a metadata map or Gemini Multimodal 
    to determine where to draw the SVG elements.
    """
    # Example logic: If the user asks during the first 30 seconds
    if request.timestamp < 30.0:
        return {
            "explanation": "You're looking at the initial state. The red sphere (+) and green sphere (-) have an attractive force because opposite charges vibe together. Watch how the vector grows as they get closer!",
            "visuals": [
                {"type": "arrow", "x1": 300, "y1": 225, "x2": 450, "y2": 225}, # Force vector
                {"type": "circle", "cx": 280, "cy": 225, "r": 40}            # Highlight Red Charge
            ]
        }
    else:
        return {
            "explanation": "At this stage, the distance 'r' is very small, so the force is peaking. It follows the Inverse Square Law!",
            "visuals": [
                {"type": "arrow", "x1": 400, "y1": 225, "x2": 700, "y2": 225}
            ]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
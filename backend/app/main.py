from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Ascenda Interactive Tutor")

# 1. CORS CONFIGURATION
# Matches your Vercel URL from your previous logs
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ascenda-umber.vercel.app", 
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. DATA MODELS
class InteractRequest(BaseModel):
    timestamp: float
    query: str

# 3. INTERACTIVE TUTOR ENDPOINT
@app.post("/api/interact")
async def tutor_interaction(request: InteractRequest):
    """
    Analyzes the video timestamp to return SVG drawing instructions.
    This replaces the old text-only streaming that caused JSON errors.
    """
    # logic for Coulomb's Law visuals
    if request.timestamp < 5.0:
        return {
            "explanation": "We're starting with two opposite charges. The Red sphere is positive, and the Green is negative. Opposite charges attract—it's physics, bestie!",
            "visuals": [
                {"type": "circle", "cx": 250, "cy": 225, "r": 60}, # Focus on Red charge
                {"type": "arrow", "x1": 310, "y1": 225, "x2": 450, "y2": 225} # Attraction vector
            ]
        }
    else:
        return {
            "explanation": "Notice the force vector growing! As they get closer, the 'vibe' gets stronger. This follows the inverse square law.",
            "visuals": [
                {"type": "arrow", "x1": 310, "y1": 225, "x2": 550, "y2": 225}, # Longer vector
                {"type": "circle", "cx": 600, "cy": 225, "r": 60}  # Focus on Green charge
            ]
        }

# 4. ENTRY POINT
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
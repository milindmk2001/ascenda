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
    # Logic: Point the AI to specific pixel coordinates 
    # based on where the charges are in YOUR video.
    
    return {
        "explanation": "Notice the force vectors between these two spheres. Because they are both positive (red), they are repelling. The length of the yellow arrow represents the magnitude of that 'beef' between them.",
        "visuals": [
            # Drawing a 'Repulsion' arrow on the right
            {"type": "arrow", "x1": 500, "y1": 225, "x2": 650, "y2": 225},
            # Drawing a 'Repulsion' arrow on the left
            {"type": "arrow", "x1": 300, "y1": 225, "x2": 150, "y2": 225},
            # Highlighting the charges
            {"type": "circle", "cx": 300, "cy": 225, "r": 50},
            {"type": "circle", "cx": 500, "cy": 225, "r": 50}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
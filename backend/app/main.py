import random
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .services.prompt_service import PromptService

app = FastAPI(title="Ascenda API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@app.get("/lesson/coulombs-law")
async def get_coulombs_law():
    scenario = random.choice(["attraction", "repulsion"])
    prompt = PromptService.get_coulombs_law_prompt(scenario)
    response = model.generate_content(prompt)
    return PromptService.clean_ai_response(response.text)
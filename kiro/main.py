# Dummy get_symptom_list to prevent NameError if not using symptom extraction
def get_symptom_list():
    # If you want to support symptom extraction, implement this to return a list of all symptom names from your training data
    return []
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import os
from dotenv import load_dotenv
import logging
import joblib
import pandas as pd
import re
import math
os.environ["HF_HOME"] = "E:/huggingface"
os.environ["TRANSFORMERS_CACHE"] = "E:/huggingface/transformers"
os.environ["HUGGINGFACE_HUB_CACHE"] = "E:/huggingface/hub"

# Import retrieval and LLM chatbots, and joblib for disease model
from rag_engine import RAGEngine
from retrieval_chatbot import RetrievalChatbot
from llm_chatbot import LLMChatbot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Health Chatbot", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

disease_info = {
    # ...existing code...
}

# Initialize components
rag_engine = RAGEngine()
retrieval_bot = RetrievalChatbot()
llm_bot = LLMChatbot()
disease_model = joblib.load('datasets/disease_symptom_model.joblib')
disease_info = {
    "Fungal infection": {
        "description": "Fungal infections are caused by fungi and can affect the skin, nails, lungs, or other organs. They often present as rashes, itching, or respiratory symptoms.",
        "common_symptoms": ["itching", "skin rash", "nodal skin eruptions"],
        "advice": "Maintain good hygiene, keep affected areas dry, and consult a doctor for antifungal treatment if symptoms persist."
    },
    "Allergy": {
        "description": "Allergies are immune responses to substances like pollen, dust, or foods. Symptoms may include sneezing, itching, rashes, or swelling.",
        "common_symptoms": ["continuous sneezing", "shivering", "chills"],
        "advice": "Avoid known allergens, use antihistamines if needed, and seek medical advice for severe reactions."
    },
    "GERD": {
        "description": "Gastroesophageal reflux disease (GERD) is a digestive disorder where stomach acid frequently flows back into the esophagus, causing irritation.",
        "common_symptoms": ["acidity", "stomach pain", "chest pain"],
        "advice": "Eat smaller meals, avoid lying down after eating, and consult a doctor for persistent symptoms."
    }
}

# Simple symptom extraction from free text
def extract_symptoms_from_text(text):
    symptoms = get_symptom_list()
    found = []
    text_lower = text.lower()
    for s in symptoms:
        s_clean = s.replace('_', ' ').replace('-', ' ').replace('  ', ' ').strip().lower()
        # Allow for minor variations and ignore underscores
        pattern = r'\\b' + re.escape(s_clean) + r'\\b'
        if re.search(pattern, text_lower):
            found.append(s)
        elif s.replace('_', ' ') in text_lower:
            found.append(s)
    return list(set(found))


@app.on_event("startup")
async def startup_event():
    """Initialize the RAG engine on startup"""
    logger.info("Starting AI Health Chatbot...")
    await rag_engine.initialize()
    logger.info("RAG Engine initialized successfully")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main web widget page"""
    return templates.TemplateResponse("index.html", {"request": request})




# RAG pipeline: retrieve top Q&A for context, pass to LLM, generate answer
@app.post("/chat")
async def chat_endpoint(request: Request):
    """Handle chat messages from web widget using RAG pipeline (retrieval-augmented generation)"""
    try:
        data = await request.json()
        message = data.get("message", "")
        language = data.get("language", "en")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Retrieve top 1 relevant Q&A pair for context (faster, less tokens)
        top_k = 1
        user_vec = retrieval_bot.vectorizer.transform([message])
        sims = retrieval_bot.question_vecs.dot(user_vec.T).toarray().flatten()
        top_indices = sims.argsort()[-top_k:][::-1]
        context = ""
        for idx in top_indices:
            context += f"Q: {retrieval_bot.questions[idx]}\nA: {retrieval_bot.answers[idx]}\n"

        # Prompt LLM to generate a new, original answer using context
        prompt = (
            "You are a helpful, empathetic medical assistant. Use the following Q&A as context, but do NOT copy the answers. Always generate a new, original, and supportive answer.\n"
            f"{context}Q: {message}\nA:"
        )
        # Log prompt for debugging
        print("PROMPT:", prompt)


        response = llm_bot.generate_text(prompt)

        # Log raw response for debugging
        print("RAW RESPONSE:", response)

        answer = response.strip()

        # Fallback: If answer is empty, return a default message
        if not answer:
            answer = "I'm sorry, I couldn't generate an answer. Please try rephrasing your question."

        # Paraphrase if answer matches any dataset answer
        for dataset_answer in retrieval_bot.answers:
            if answer.strip().lower() == str(dataset_answer).strip().lower():
                paraphrase_prompt = (
                    "Paraphrase the following medical advice in a new, original way, making it more conversational and supportive. Do NOT use the same wording:\n"
                    f"{answer}"
                )
                answer = llm_bot.generate_text(paraphrase_prompt)
                break
        answer = answer.replace('\n', '\n\n')
        return JSONResponse({
            "response": answer,
            "language": language
        })
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# New endpoint for disease prediction
@app.post("/predict-disease")
async def predict_disease(request: Request):
    """Predict disease from symptoms (expects a list of symptom names)"""
    try:
        data = await request.json()
        symptoms = data.get("symptoms", [])
        if not symptoms or not isinstance(symptoms, list):
            raise HTTPException(status_code=400, detail="A list of symptoms is required.")

        # Load columns from new training data for correct order
        df = pd.read_csv('datasets/training_data.csv', nrows=1)
        df = df.loc[:, ~df.columns.str.startswith('Unnamed:')]
        all_symptoms = [col for col in df.columns if col != 'prognosis']
        input_vec = [1 if s in symptoms else 0 for s in all_symptoms]
        pred = disease_model.predict([input_vec])[0]
        return {"predicted_disease": pred}
    except Exception as e:
        logger.error(f"Disease prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _lookup_hospitals(lat: float, lon: float, radius_m: int = 100000):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "ai-health-assistant-web"}
    params = {
        "format": "json",
        "q": "hospital",
        "limit": 20,
        "lat": lat,
        "lon": lon,
    }

    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    hospitals = []
    max_km = radius_m / 1000.0
    for item in data:
        try:
            h_lat = float(item.get("lat"))
            h_lon = float(item.get("lon"))
        except (TypeError, ValueError):
            continue

        dist = _distance_km(lat, lon, h_lat, h_lon)
        if dist <= max_km:
            hospitals.append(
                {
                    "name": item.get("display_name", "Hospital"),
                    "lat": h_lat,
                    "lon": h_lon,
                    "distance_km": round(dist, 2),
                }
            )

    hospitals.sort(key=lambda h: h["distance_km"])
    return hospitals[:5]


@app.get("/hospitals")
@app.get("/nearby-hospitals")
@app.get("/nearby_hospitals")
@app.get("/api/hospitals")
async def get_nearby_hospitals(lat: float, lon: float):
    try:
        hospitals = _lookup_hospitals(lat, lon, 100000)
        return {"hospitals": hospitals}
    except requests.RequestException as e:
        logger.warning(f"Hospital lookup failed: {e}")
        return {"hospitals": []}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Health Chatbot"}

@app.get("/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "hi", "name": "हिंदी"},
            {"code": "es", "name": "Español"},
            {"code": "fr", "name": "Français"},
            {"code": "ar", "name": "العربية"},
        ]
    }

import multiprocessing
import subprocess

host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", 8000))
debug = os.getenv("DEBUG", "True").lower() == "true"

def run_fastapi():
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

def run_telegram():
    subprocess.run(["python", "telegram_handler.py"])

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_fastapi)
    p2 = multiprocessing.Process(target=run_telegram)
    p1.start()
    p2.start()
    p1.join()
    p2.join()
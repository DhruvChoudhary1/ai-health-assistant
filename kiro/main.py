from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from dotenv import load_dotenv

from rag_engine import RAGEngine

# --------------------------------
# Logging
# --------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

print(">>> Starting FastAPI...", flush=True)

# --------------------------------
# Load environment variables
# --------------------------------
load_dotenv()

# --------------------------------
# FastAPI APP
# --------------------------------
app = FastAPI(title="AI Health Chatbot", version="1.0.0")

# Static + Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------
# RAG Engine (lightweight Wikipedia search)
# --------------------------------
rag_engine = RAGEngine()

# --------------------------------
# ROUTES
# --------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        message = data.get("message")
        language = data.get("language", "en")

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        response = await rag_engine.process_query(message, language)

        return JSONResponse({
            "response": response["answer"],
            "citations": response["citations"],
            "language": response["language"],
            "timestamp": response["timestamp"],
        })

    except Exception as e:
        logger.exception("Chat endpoint error")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/languages")
async def languages():
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "hi", "name": "हिंदी"},
            {"code": "es", "name": "Español"},
            {"code": "fr", "name": "Français"},
        ]
    }

# --------------------------------
# Local development
# --------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,
        log_level="info" #Trial
    )

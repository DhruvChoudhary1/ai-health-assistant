from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import logging
import threading
import asyncio

from rag_engine import RAGEngine
from telegram_handler import run_bot   # ← correct import

# Load env
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(title="AI Health Chatbot", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static + Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# RAG engine (web only)
rag_engine = RAGEngine()

@app.on_event("startup")
async def startup_event():
    # Start RAG engine for website
    logger.info("Initializing RAG engine (web)...")
    asyncio.create_task(rag_engine.initialize())

    # Start Telegram bot in background thread
    logger.info("Starting Telegram bot thread…")
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()

    logger.info("Startup completed.")


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

        result = await rag_engine.process_query(message, language)

        return JSONResponse({
            "response": result["answer"],
            "citations": result.get("citations", []),
            "language": language,
            "timestamp": result.get("timestamp")
        })

    except Exception as e:
        logger.error(f"/chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=False,
    )

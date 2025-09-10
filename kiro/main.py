from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import logging
from rag_engine import RAGEngine


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
templates = Jinja2Templates(directory="templates")

# Initialize components
rag_engine = RAGEngine()


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

@app.post("/chat")
async def chat_endpoint(request: Request):
    """Handle chat messages from web widget"""
    try:
        data = await request.json()
        message = data.get("message", "")
        language = data.get("language", "en")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Process message through RAG engine
        response = await rag_engine.process_query(message, language)
        
        return JSONResponse({
            "response": response["answer"],
            "citations": response["citations"],
            "language": language,
            "timestamp": response["timestamp"]
        })
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
            {"code": "fr", "name": "Français"}
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
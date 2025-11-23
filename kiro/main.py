from fastapi import FastAPI, Request, HTTPException
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# RAG engine (shared by all web requests)
rag_engine = RAGEngine()

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG engine on startup"""
    logger.info("Starting AI Health Chatbot...")
    await rag_engine.initialize()
    logger.info("RAG Engine initialized successfully")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve main web UI"""
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

        response = await rag_engine.process_query(message, language)

        return JSONResponse({
            "response": response["answer"],
            "citations": response.get("citations", []),
            "language": language,
            "timestamp": response.get("timestamp"),
        })

    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Health Chatbot"}

@app.get("/languages")
async def get_supported_languages():
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "hi", "name": "हिंदी"},
            {"code": "es", "name": "Español"},
            {"code": "fr", "name": "Français"},
        ]
    }

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "true").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info",
    )

# AI Health Assistant

AI-powered health assistant with a FastAPI web app, embeddable web widget, Telegram bot, retrieval-augmented answers, disease prediction, and nearby hospital lookup.

## Current Features
- Web chat UI with multilingual input (`en`, `hi`, `es`, `fr`, `ar`)
- Telegram bot with health commands (`/symptoms`, `/medicine`, `/hospital`, `/voice`, `/report`, `/history`)
- RAG engine with ChromaDB + sentence-transformers for knowledge-grounded answers
- Local/LLM-assisted response generation (rule-based + optional local model paths)
- Disease prediction endpoint from symptom list (`/predict-disease`)
- Nearby hospital search from live internet data (OpenStreetMap/Nominatim)
  - Backend enforces a fixed 100 km search radius
- Medical report support (PDF text extraction + OCR for images; optional dependencies)
- Voice symptom flow in Telegram (Whisper, optional)
- Basic health logging in Telegram (`/log_weight`, `/log_bp`, `/log_sugar`)

## Project Location
Main application code lives in the `kiro/` folder.

## Setup
1. Open terminal in `kiro/`.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv311
   # Windows PowerShell
   venv311\Scripts\Activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create `.env` in `kiro/` with required values:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   # optional
   HUGGINGFACE_API_KEY=your_key_here
   USE_LOCAL_LLM=false
   HOST=0.0.0.0
   PORT=8000
   DEBUG=true
   ```

## Run
- Start API + Telegram bot together:
  ```bash
  python main.py
  ```
- API default URL: `http://localhost:8000`

## API Endpoints
- `GET /` - Web chat UI page
- `POST /chat` - Main chat endpoint
  - body: `{ "message": "...", "language": "en" }`
- `POST /predict-disease` - Predict disease from symptoms
  - body: `{ "symptoms": ["itching", "skin_rash"] }`
- `GET /hospitals?lat=<lat>&lon=<lon>` - Nearby hospitals lookup (fixed 100 km backend radius)
  - aliases: `/nearby-hospitals`, `/nearby_hospitals`, `/api/hospitals`
- `GET /languages` - Supported UI languages
- `GET /health` - Health-check endpoint

## Important Notes
- Hospital results are fetched online from OpenStreetMap; internet is required.
- Some features are optional and require extra packages/tools:
  - Voice: `openai-whisper`
  - PDF parsing: `pdfplumber`
  - OCR: `pytesseract` + Tesseract installed on system
- Current health logs in Telegram are in-memory (not persistent across restarts).

## Key Files
- `kiro/main.py` - FastAPI app and endpoints
- `kiro/telegram_handler.py` - Telegram bot flows and health tracking commands
- `kiro/rag_engine.py` - Retrieval and response pipeline
- `kiro/retrieval_chatbot.py` - TF-IDF retrieval support
- `kiro/llm_chatbot.py` - GGUF LLM wrapper (llama.cpp)
- `kiro/templates/`, `kiro/static/` - Web UI
- `kiro/web_widget/` - Embeddable widget assets

## License
MIT

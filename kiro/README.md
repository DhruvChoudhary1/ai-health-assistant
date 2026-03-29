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

## Setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv311
   # Windows PowerShell
   venv311\Scripts\Activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env` with required values:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   # optional
   HUGGINGFACE_API_KEY=your_key_here
   USE_LOCAL_LLM=false
  LLM_MODEL_PATH=E:/models/mistral.gguf
  LLM_GPU_LAYERS=35
  LLM_THREADS=7
  LLM_N_CTX=2048
  LLM_N_BATCH=512
  LLM_MAX_TOKENS=160
  LLM_TEMPERATURE=0.6
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

## Project Structure
- `main.py` - FastAPI app and endpoints
- `telegram_handler.py` - Telegram bot flows and health tracking commands
- `rag_engine.py` - Retrieval and response pipeline
- `retrieval_chatbot.py` - TF-IDF retrieval support
- `llm_chatbot.py` - GGUF LLM wrapper (llama.cpp)
- `templates/`, `static/` - Web UI
- `web_widget/` - Embeddable widget assets

## License
MIT

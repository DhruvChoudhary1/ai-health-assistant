# AI Health Chatbot

A conversational AI assistant for health-related queries, built with FastAPI, Telegram integration, and RAG (Retrieval-Augmented Generation) engine.

## Features
- Chatbot UI (web and Telegram)
- Multilingual support
- Health knowledge base
- Privacy-focused (no data stored)
- Modern, responsive design

## Getting Started
1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. Add your Telegram bot token to a `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ```
4. Run the web server:
   ```
   python main.py
   ```
5. Run the Telegram bot:
   ```
   python telegram_handler.py
   ```

## Project Structure
- `main.py` - FastAPI web server
- `telegram_handler.py` - Telegram bot integration
- `rag_engine.py` - RAG engine for health Q&A
- `static/` - CSS, JS, and assets
- `templates/` - HTML templates
- `knowledge_base/` - Health documents

## Contributing
Pull requests and suggestions are welcome!

## License
MIT

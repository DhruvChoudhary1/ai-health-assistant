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

## How Kiro Was Used in This Project

This project was built using the **Kiro** framework, which provided a modular and scalable foundation for developing the AI Health Assistant. Kiro was instrumental in organizing the codebase, managing dependencies, and streamlining the integration of various components such as the RAG engine, Telegram bot handler, and translation services.

### Key Roles of Kiro in the Project

- **Project Structure:** Kiro helped maintain a clean and organized directory structure, making it easier to manage source code, static files, templates, and configuration.
- **Dependency Management:** By leveraging Kiro’s setup, all required Python packages and modules were efficiently managed through the `requirements.txt` file.
- **Integration:** Kiro facilitated the seamless integration of third-party libraries like `deep_translator` and `python-telegram-bot`, enabling advanced features such as multilingual support and real-time chat interactions.
- **Extensibility:** The modular nature of Kiro allowed for easy addition of new features and components, such as the RAG engine for retrieval-augmented generation and custom handlers for Telegram interactions.

### Getting Started with Kiro

To replicate or extend this project, simply follow the setup instructions provided in the repository. Make sure to install all dependencies and activate the virtual environment as described.

Kiro’s robust foundation ensures that the project remains maintainable, extensible, and easy to collaborate on.

### Category

I'm submitting to Wildcard/Freestyle category. 

## Contributing
Pull requests and suggestions are welcome!

## License
MIT

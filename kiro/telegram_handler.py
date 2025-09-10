import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from rag_engine import RAGEngine
import logging
from deep_translator import GoogleTranslator 
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize RAG engine synchronously at module level
rag_engine = RAGEngine()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am dr_haathi_bot, your AI Health Assistant. Ask me anything!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = await rag_engine.process_query(user_message)
        await update.message.reply_text(response["answer"])
    except Exception as e:
        logger.error(f"Telegram handler error: {str(e)}")
        await update.message.reply_text("Sorry, something went wrong.")

def main():
    """Main function using synchronous approach"""
    # Initialize RAG engine in a separate thread if needed
    import threading
    
    def init_rag():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(rag_engine.initialize())
        loop.close()
    
    # Initialize RAG engine
    logger.info("Initializing RAG engine...")
    init_thread = threading.Thread(target=init_rag)
    init_thread.start()
    init_thread.join()
    logger.info("RAG engine initialized")
    
    # Create the application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Starting Telegram bot...")
    
    # Run the bot using the polling method
    app.run_polling(
        poll_interval=1,
        timeout=10,
        bootstrap_retries=5,
        read_timeout=10,
        write_timeout=10,
        connect_timeout=10,
        pool_timeout=10
    )

if __name__ == "__main__":
    import sys
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise 
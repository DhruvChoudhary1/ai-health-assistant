import os
import asyncio
import logging
from dotenv import load_dotenv

import ssl
import certifi
import httpx   # used by python-telegram-bot
from telegram.ext import ApplicationBuilder

# FIX WINDOWS SSL ISSUE FOR TELEGRAM + HTTPX
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Patch httpx for ALL Telegram API calls
old_async_client = httpx.AsyncClient

class PatchedAsyncClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        # Force Telegram to use valid SSL certificates
        kwargs["verify"] = ssl_context
        super().__init__(*args, **kwargs)

httpx.AsyncClient = PatchedAsyncClient
# -----------------------------------------

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from rag_engine import RAGEngine

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env")

# Global RAG engine
rag_engine = RAGEngine()
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()


# -----------------------------------------
# COMMAND HANDLERS
# -----------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am dr_haathi_bot 🐘💊\n"
        "Your AI Health Assistant.\n\n"
        "Ask me anything related to health!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        response = await rag_engine.process_query(user_message, "en")
        await update.message.reply_text(response["answer"])

    except Exception as e:
        logger.error(f"Telegram error: {str(e)}")
        await update.message.reply_text("⚠️ Sorry, something went wrong. Try again later.")


# -----------------------------------------
# MAIN FUNCTION
# -----------------------------------------
def main():
    # Initialize RAG engine
    def init_rag():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(rag_engine.initialize())
        loop.close()

    logger.info("Initializing RAG engine for Telegram...")
    import threading
    t = threading.Thread(target=init_rag)
    t.start()
    t.join()
    logger.info("RAG engine initialized.")

    # Build Telegram bot normally (NO ssl_context here!)
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command/message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Starting Telegram bot polling...")
    app.run_polling()


# -----------------------------------------
# ENTRY POINT
# -----------------------------------------
if __name__ == "__main__":
    import sys
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

def run_bot():
    application.run_polling()


import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram import Update
from telegram.ext import ContextTypes

from rag_engine import RAGEngine

load_dotenv()
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN missing!")

# Shared RAG engine for Telegram bot
rag_engine = RAGEngine()

# Build Telegram application once
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()


# ───────────────────────────────
# Telegram Handlers
# ───────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am dr_haathi_bot 🐘💊\n"
        "Ask me anything related to health!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = await rag_engine.process_query(user_text, "en")
        await update.message.reply_text(response["answer"])
    except Exception as e:
        logger.error(f"Telegram Error: {e}")
        await update.message.reply_text("⚠️ Error. Try again later.")


# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ───────────────────────────────
# Function called from main.py
# ───────────────────────────────
def run_bot():
    """
    Run Telegram bot inside its own event loop (required when running inside FastAPI thread).
    """
    logger.info("Starting Telegram bot thread…")

    # Create a new event loop for THIS thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_all():
        # Initialize RAG engine inside this loop
        logger.info("Initialising RAG engine for Telegram...")
        await rag_engine.initialize()
        logger.info("RAG engine ready. Starting polling...")
        await application.run_polling()

    loop.run_until_complete(start_all())

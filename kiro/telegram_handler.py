import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

from rag_engine import RAGEngine

load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Shared RAG engine for Telegram bot
rag_engine = RAGEngine()

# Build telegram application ONCE
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()


# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am dr_haathi_bot 🐘💊\n"
        "Ask me anything related to health!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        response = await rag_engine.process_query(text, "en")
        await update.message.reply_text(response["answer"])
    except Exception as e:
        logger.error(str(e))
        await update.message.reply_text("⚠️ Error. Try again later.")


# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

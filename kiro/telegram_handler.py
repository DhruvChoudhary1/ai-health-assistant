import os
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from rag_engine import RAGEngine

# --------------------------------
# Setup
# --------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram_bot")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in .env")

# Use same lightweight wiki-based RAG
rag_engine = RAGEngine()

# --------------------------------
# Handlers
# --------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I am dr_haathi_bot 🐘💊\n"
        "Ask me anything related to health.\n\n"
        "⚠️ I provide educational information only, not medical advice."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    try:
        result = await rag_engine.process_query(query, "en")
        await update.message.reply_text(result["answer"])
    except Exception as e:
        logger.error(f"Telegram processing error: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Try again later.")

# --------------------------------
# Main entry
# --------------------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Starting Telegram polling...")
    app.run_polling()

if __name__ == "__main__":
    main()

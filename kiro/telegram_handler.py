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

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env")

# Local RAG engine for Telegram
rag_engine = RAGEngine()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am dr_haathi_bot 🐘💊\n"
        "Your AI Health Assistant.\n\n"
        "Ask me anything related to health!\n\n"
        "Note: I provide educational information only, not medical advice."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        response = await rag_engine.process_query(text, "en")
        await update.message.reply_text(response["answer"])
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        await update.message.reply_text("⚠️ Sorry, something went wrong. Try again later.")


def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Starting Telegram bot polling ...")
    application.run_polling()


if __name__ == "__main__":
    main()

import os
import asyncio
import logging
import tempfile
from datetime import datetime
from typing import Dict, Any, List

from dotenv import load_dotenv
from telegram import Update, Location
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from rag_engine import RAGEngine

try:
    import whisper
except Exception:
    whisper = None  # Whisper is optional; handle gracefully

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from PIL import Image
    import pytesseract
except Exception:
    Image = None
    pytesseract = None

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize RAG engine
rag_engine = RAGEngine()

# Simple in-memory health tracking per user
user_health_data: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}


def _get_user_id(update: Update) -> int:
    return update.effective_user.id if update.effective_user else 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Hello! I am dr_haathi_bot, your AI Health Assistant.\n\n"
        "You can use commands like:\n"
        "/symptoms - describe your symptoms\n"
        "/medicine - ask about a medicine\n"
        "/hospital - find nearby hospitals\n"
        "/voice - send a voice symptom description\n"
        "/report - upload a medical report (PDF/image)\n"
        "/log_weight, /log_bp, /log_sugar - track your health\n"
        "/history - see your logged health summary\n"
        "/emergency - quick emergency info\n\n"
        "🔒 Privacy: conversations are not permanently stored here, and no personal health data "
        "is intentionally logged beyond simple optional tracking you request."
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def symptoms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Describe your symptoms.\nExample: fever, headache, nausea"
    )


async def medicine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Please specify a medicine name.\nExample: /medicine paracetamol"
        )
        return

    med_name = " ".join(args).lower()
    info = rag_engine.medicine_info.get(med_name)
    if not info:
        # Fall back to RAG query
        query = f"What is {med_name} used for? Explain common uses, dosage and side effects."
        resp = await rag_engine.process_query(query)
        await update.message.reply_text(resp["answer"])
        return

    text = (
        f"{med_name.title()}\n\n"
        f"Uses:\n- " + "\n- ".join(info["uses"]) + "\n\n"
        f"Common dosage:\n{info['dosage']}\n\n"
        f"Side effects:\n- " + "\n- ".join(info["side_effects"]) + "\n\n"
        "⚠️ Always follow local medical guidance and your doctor's prescription."
    )
    await update.message.reply_text(text)


async def emergency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🚨 Emergency Contacts (India)\n\n"
        "Ambulance: 108\n"
        "Police: 100\n"
        "Fire: 101\n\n"
        "If you have severe chest pain, difficulty breathing, sudden weakness on one side, "
        "are unconscious, or experiencing heavy bleeding, seek emergency care immediately.\n\n"
        "You can also share your location and use /hospital to find nearby hospitals."
    )
    await update.message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = _get_user_id(update)
    history = context.user_data.get("history", [])
    history.append({"role": "user", "content": user_message})
    context.user_data["history"] = history[-10:]

    try:
        response = await rag_engine.process_query(user_message, history=history)
        history.append({"role": "assistant", "content": response["answer"]})
        context.user_data["history"] = history[-10:]
        await update.message.reply_text(response["answer"])
    except Exception as e:
        logger.error(f"Telegram handler error: {str(e)}")
        await update.message.reply_text("Sorry, something went wrong.")


async def voice_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please send a voice message describing your symptoms. I will try to transcribe and analyze it."
    )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not whisper:
        await update.message.reply_text(
            "Voice analysis is not available on this server right now."
        )
        return

    voice = update.message.voice
    if not voice:
        await update.message.reply_text("I could not find a voice message.")
        return

    file = await voice.get_file()
    with tempfile.TemporaryDirectory() as tmpdir:
        ogg_path = os.path.join(tmpdir, "voice.ogg")
        await file.download_to_drive(ogg_path)

        model = whisper.load_model("base")
        result = model.transcribe(ogg_path)
        transcript = result.get("text", "").strip()

    if not transcript:
        await update.message.reply_text(
            "I could not understand the audio clearly. Please try typing your symptoms."
        )
        return

    await update.message.reply_text(f"🗣 You said: {transcript}")
    history = context.user_data.get("history", [])
    history.append({"role": "user", "content": transcript})
    context.user_data["history"] = history[-10:]

    resp = await rag_engine.process_query(transcript, history=history)
    history.append({"role": "assistant", "content": resp["answer"]})
    context.user_data["history"] = history[-10:]

    await update.message.reply_text(resp["answer"])


def _extract_text_from_pdf(path: str) -> str:
    if not pdfplumber:
        return ""
    text_chunks = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_chunks.append(page.extract_text() or "")
    return "\n".join(text_chunks)


def _extract_text_from_image(path: str) -> str:
    if not (Image and pytesseract):
        return ""
    img = Image.open(path)
    return pytesseract.image_to_string(img)


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please upload your medical report as a PDF or clear image. I will try to extract key findings.\n"
        "⚠️ Do not share highly sensitive personal identifiers."
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document:
        return

    file = await document.get_file()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, document.file_name or "report")
        await file.download_to_drive(path)

        extracted = ""
        if document.file_name and document.file_name.lower().endswith(".pdf"):
            extracted = _extract_text_from_pdf(path)
        else:
            extracted = _extract_text_from_image(path)

    if not extracted.strip():
        await update.message.reply_text(
            "I could not read this report clearly. Please ensure it is a clear PDF or image."
        )
        return

    prompt = (
        "You are a medical assistant. Summarize this medical report for a layperson. "
        "Highlight key abnormal values if any, possible causes, and when to see a doctor.\n\n"
        f"Report text:\n{extracted[:4000]}"
    )
    resp = await rag_engine.process_query(prompt)
    await update.message.reply_text(resp["answer"])


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photos = update.message.photo
    if not photos:
        return

    file = await photos[-1].get_file()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "image.jpg")
        await file.download_to_drive(path)

        # Try OCR first for text-based reports
        text = _extract_text_from_image(path)

        if text.strip():
            prompt = (
                "This is a photo of a medical report or health-related information. "
                "Summarize what you can read and explain it in simple language.\n\n"
                f"OCR text:\n{text[:3000]}"
            )
            resp = await rag_engine.process_query(prompt)
            await update.message.reply_text(resp["answer"])
            return

        # Fallback: treat as skin / wound image and give generic advice
        generic = (
            "I received an image that may show a skin rash, wound, or other condition.\n\n"
            "Possible condition: a non-specific skin/injury change (I cannot reliably diagnose from an image alone).\n"
            "Recommendation: if this is new, painful, spreading, or associated with fever or difficulty breathing, "
            "please see a doctor or dermatologist as soon as possible."
        )
        await update.message.reply_text(generic)


async def hospital_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please share your location from Telegram so I can look up nearby hospitals.\n"
        "On most devices: attach ➜ Location."
    )
    context.user_data["awaiting_hospital_location"] = True


def _find_nearby_hospitals(location: Location) -> List[Dict[str, Any]]:
    """Use OpenStreetMap Nominatim to fetch nearby hospitals."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "format": "json",
            "q": "hospital",
            "limit": 5,
            "viewbox": "",
            "bounded": 0,
            "lat": location.latitude,
            "lon": location.longitude,
        }
        headers = {"User-Agent": "ai-health-assistant-bot"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        hospitals = []
        for item in data:
            hospitals.append(
                {
                    "name": item.get("display_name", "Hospital"),
                    "lat": item.get("lat"),
                    "lon": item.get("lon"),
                }
            )
        return hospitals
    except Exception as e:
        logger.warning(f"Hospital lookup failed: {e}")
        return []


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    if not loc:
        return

    awaiting = context.user_data.get("awaiting_hospital_location", False)
    if not awaiting:
        # Ignore passive locations
        return

    context.user_data["awaiting_hospital_location"] = False
    hospitals = _find_nearby_hospitals(loc)
    if not hospitals:
        await update.message.reply_text(
            "I could not find hospitals near this location right now. "
            "Please use your map app in case of emergency."
        )
        return

    lines = ["Nearest hospitals:"]
    for idx, h in enumerate(hospitals, start=1):
        name = h["name"]
        lines.append(f"{idx}. {name}")

    await update.message.reply_text("\n".join(lines))


async def log_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = _get_user_id(update)
    if not context.args:
        await update.message.reply_text("Usage: /log_weight 72")
        return
    try:
        weight = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a numeric weight in kg. Example: /log_weight 72")
        return

    user_data = user_health_data.setdefault(user_id, {"weight": [], "bp": [], "sugar": []})
    user_data["weight"].append({"value": weight, "ts": datetime.now().isoformat()})
    await update.message.reply_text(f"Logged weight: {weight} kg")


async def log_bp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = _get_user_id(update)
    if not context.args:
        await update.message.reply_text("Usage: /log_bp 120/80")
        return
    reading = context.args[0]
    user_data = user_health_data.setdefault(user_id, {"weight": [], "bp": [], "sugar": []})
    user_data["bp"].append({"value": reading, "ts": datetime.now().isoformat()})
    await update.message.reply_text(f"Logged blood pressure: {reading}")


async def log_sugar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = _get_user_id(update)
    if not context.args:
        await update.message.reply_text("Usage: /log_sugar 95")
        return
    try:
        sugar = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Please provide a numeric sugar value. Example: /log_sugar 95")
        return

    user_data = user_health_data.setdefault(user_id, {"weight": [], "bp": [], "sugar": []})
    user_data["sugar"].append({"value": sugar, "ts": datetime.now().isoformat()})
    await update.message.reply_text(f"Logged blood sugar: {sugar} mg/dL")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = _get_user_id(update)
    data = user_health_data.get(user_id)
    if not data:
        await update.message.reply_text("No health data logged yet. Try /log_weight, /log_bp, or /log_sugar.")
        return

    lines = ["📊 Personal Health Summary"]
    if data["weight"]:
        latest_w = data["weight"][-1]["value"]
        lines.append(f"- Latest weight: {latest_w} kg")
    if data["bp"]:
        latest_bp = data["bp"][-1]["value"]
        lines.append(f"- Latest blood pressure: {latest_bp}")
    if data["sugar"]:
        latest_sugar = data["sugar"][-1]["value"]
        lines.append(f"- Latest blood sugar: {latest_sugar} mg/dL")

    await update.message.reply_text("\n".join(lines))


def main():
    """Main function using synchronous approach"""
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

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("symptoms", symptoms))
    app.add_handler(CommandHandler("medicine", medicine_command))
    app.add_handler(CommandHandler("emergency", emergency))
    app.add_handler(CommandHandler("voice", voice_prompt))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("hospital", hospital_command))
    app.add_handler(CommandHandler("log_weight", log_weight))
    app.add_handler(CommandHandler("log_bp", log_bp))
    app.add_handler(CommandHandler("log_sugar", log_sugar))
    app.add_handler(CommandHandler("history", history))

    # Message handlers
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
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
        pool_timeout=10,
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
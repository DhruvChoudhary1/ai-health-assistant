import logging
import re
from datetime import datetime
from typing import Dict, Any
import requests
from urllib.parse import quote
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)


# ---------------------------
# TURN A QUESTION INTO A CLEAN TOPIC
# ---------------------------
def extract_topic_from_query(query: str) -> str:
    """
    Convert natural-language questions to a proper Wikipedia title.
    Examples:
      "what is pneumonia" -> "pneumonia"
      "tell me about dengue fever" -> "dengue fever"
    """
    q = query.strip().lower()

    q = re.sub(
        r"^(what is|what's|what is a|what is an|tell me about|explain|define|info on|information on)\s+",
        "",
        q,
        flags=re.I,
    )

    q = re.sub(r"[?\.,!]+$", "", q)
    words = q.split()
    topic = " ".join(words[:3]) if words else q

    return topic or query


# ---------------------------
# CLEAN SENTENCE EXTRACTION
# ---------------------------
def extract_keyword_section(text: str, keywords: list, default: str) -> str:
    """
    Return the first sentence containing any keyword, else default.
    """
    sentences = re.split(r"\. |\n", text)
    for s in sentences:
        if any(k in s.lower() for k in keywords):
            return s.strip()
    return default


# ---------------------------
# WIKIPEDIA SUMMARY FETCH
# ---------------------------
def wiki_fetch(topic: str):
    """
    Fetch only the summary (fast, free, reliable).
    """
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(topic)}"
    headers = {
        "User-Agent": "AIHealthAssistant/1.0 (https://ai-health-assistant-l2l8.onrender.com; contact: dhruv)"
    }

    try:
        logger.warning(f"FETCHING FROM WIKI: {url}")
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code == 403:
            logger.error("Wikipedia blocked request (403) — User-Agent required.")
            return None

        if res.status_code != 200:
            logger.error(f"Wikipedia returned status {res.status_code}")
            return None

        return res.json().get("extract")

    except Exception as e:
        logger.error(f"Wikipedia fetch error: {e}")
        return None


# ---------------------------
# MAIN RAG ENGINE
# ---------------------------
class RAGEngine:
    def __init__(self):
        self.translator = GoogleTranslator(source="auto", target="en")
        logger.info("Lightweight Wikipedia RAG initialized.")

    async def process_query(self, query: str, language: str = "en") -> Dict[str, Any]:

        original_query = query
        processed_query = query

        # Convert query → English
        if language != "en":
            try:
                processed_query = self.translator.translate(query, target="en")
            except Exception:
                processed_query = query

        # Convert question to Wikipedia topic
        topic = extract_topic_from_query(processed_query)

        # Fetch summary
        summary = wiki_fetch(topic)
        if not summary:
            return {
                "answer": "⚠️ I could not find medical information about this condition.",
                "citations": [],
                "original_query": original_query,
                "processed_query": processed_query,
                "language": language,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        # Extract structured information
        definition = summary

        symptoms = extract_keyword_section(
            summary,
            ["symptom", "signs", "cough", "fever", "pain", "infection"],
            "Symptoms vary based on the exact condition and severity."
        )

        causes = extract_keyword_section(
            summary,
            ["cause", "caused", "due to", "results from"],
            "Causes are not clearly mentioned in this summary."
        )

        treatment = extract_keyword_section(
            summary,
            ["treat", "treatment", "therapy", "managed"],
            "Treatment details are not included here. Consult a healthcare professional."
        )

        prevention = extract_keyword_section(
            summary,
            ["prevent", "prevention", "avoid", "reduce risk"],
            "General precautions include hygiene, lifestyle care, and timely vaccination/screening."
        )

        complications = extract_keyword_section(
            summary,
            ["complication", "risk", "serious", "life-threatening", "danger"],
            "Complications depend on severity and patient health."
        )

        # Final formatted message
        answer_en = f"""
🔍 **Medical Information: {topic.title()}**

📘 **Definition**  
{definition}

---

🩺 **Symptoms**  
• {symptoms}

⚠️ **Causes**  
• {causes}

💊 **Treatment**  
• {treatment}

🛡️ **Prevention / Precautions**  
• {prevention}

❗ **Complications**  
• {complications}

---

📎 **Source:** Wikipedia  
🔗 https://en.wikipedia.org/wiki/{topic.replace(" ", "_")}

⚠️ *Disclaimer:* This assistant provides **educational health information only**.  
It is **not** a substitute for professional medical advice, diagnosis, or treatment.
"""

        # Translate back if needed
        final_answer = answer_en
        if language != "en":
            try:
                final_answer = self.translator.translate(answer_en, target=language)
            except Exception:
                final_answer = answer_en

        return {
            "answer": final_answer,
            "citations": [{
                "source": "Wikipedia",
                "url": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
            }],
            "original_query": original_query,
            "processed_query": processed_query,
            "language": language,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

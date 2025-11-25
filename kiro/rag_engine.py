import logging
import re
from datetime import datetime
from typing import Dict, Any
import requests
from urllib.parse import quote
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)


# ---------------------------
# SIMPLE QUERY → TOPIC CLEANING
# ---------------------------
def extract_topic_from_query(query: str) -> str:
    """
    Turn a user question into a clean Wikipedia title.
    Examples:
      "what is pneumonia" -> "pneumonia"
      "tell me about dengue fever" -> "dengue fever"
    """
    q = query.strip().lower()

    # remove common prefixes
    q = re.sub(
        r"^(what is|what's|what is a|what is an|tell me about|explain|define|info on|information on)\s+",
        "",
        q,
        flags=re.I,
    )

    # remove question mark and extra punctuation
    q = re.sub(r"[?\.,!]+$", "", q)

    # keep only first 3 words to avoid super long titles
    words = q.split()
    topic = " ".join(words[:3]) if words else q

    return topic or query


# ---------------------------
# CLEAN SECTION EXTRACTION
# ---------------------------
def extract_keyword_section(text: str, keywords: list, default: str) -> str:
    """
    Extracts one sentence containing any of the given keywords.
    Falls back to `default` if nothing matches.
    """
    sentences = re.split(r"\. |\n", text)
    for s in sentences:
        s_l = s.lower()
        if any(k in s_l for k in keywords):
            return s.strip()
    return default


# ---------------------------
# WIKIPEDIA SUMMARY FETCH
# ---------------------------
def wiki_fetch(raw_query: str) -> str | None:
    """
    Uses Wikipedia REST summary API.
    Returns plain summary text or None.
    """
    topic = extract_topic_from_query(raw_query)
    title_encoded = quote(topic)
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_encoded}"

    logger.warning(f"FETCHING FROM WIKI: {url}")

    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            logger.warning(f"Wikipedia status {res.status_code}: {res.text[:200]}")
            return None

        data = res.json()
        return data.get("extract")
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

        # Translate query → English
        if language != "en":
            try:
                processed_query = self.translator.translate(query, target="en")
            except Exception:
                processed_query = query

        # Fetch from Wikipedia summary
        summary = wiki_fetch(processed_query)
        if not summary:
            return {
                "answer": "⚠️ I could not find medical information about this condition.",
                "citations": [],
                "original_query": original_query,
                "processed_query": processed_query,
                "language": language,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        # --- Extract structured sections ---
        definition = summary

        symptoms = extract_keyword_section(
            summary,
            ["symptom", "signs", "cough", "fever", "pain"],
            "Symptoms vary depending on the exact type and severity."
        )

        causes = extract_keyword_section(
            summary,
            ["cause", "caused", "due to", "results from"],
            "Causes are not clearly mentioned in this short summary."
        )

        treatment = extract_keyword_section(
            summary,
            ["treat", "treatment", "therapy", "managed"],
            "Treatment details are not included here. Consult a medical professional."
        )

        prevention = extract_keyword_section(
            summary,
            ["prevent", "prevention", "avoid", "reduce risk"],
            "General precautions include hygiene, healthy lifestyle, and timely vaccination or screening (when available)."
        )

        complications = extract_keyword_section(
            summary,
            ["complication", "risk", "danger", "serious", "life-threatening"],
            "Possible complications depend on severity and the person’s overall health."
        )

        # ---------- Build final formatted response ----------
        answer_en = f"""
📌 **Medical Information about {extract_topic_from_query(processed_query).title()}**

📖 **Definition**  
{definition}

🩺 **Symptoms**  
- {symptoms}

⚠️ **Causes**  
- {causes}

💊 **Treatment**  
- {treatment}

🛡️ **Prevention / Precautions**  
- {prevention}

❗ **Complications**  
- {complications}

⚠️ *This assistant provides educational information only. It is not a substitute for professional medical advice, diagnosis, or treatment.*
        """

        # Translate back
        final_answer = answer_en
        if language != "en":
            try:
                final_answer = self.translator.translate(answer_en, target=language)
            except Exception:
                final_answer = answer_en

        topic = extract_topic_from_query(processed_query)

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

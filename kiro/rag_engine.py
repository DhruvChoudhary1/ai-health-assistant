import logging
import re
from datetime import datetime
from typing import Dict, Any
import requests
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)


# ---------------------------
# CLEAN SECTION EXTRACTION
# ---------------------------
def extract_keyword_section(text: str, keywords: list, default: str):
    """
    Extracts 1–2 clean sentences around keywords like:
    symptoms, causes, treatment, prevention etc.
    """
    text_l = text.lower()
    sentences = re.split(r'\. |\n', text)

    for s in sentences:
        s_l = s.lower()
        if any(k in s_l for k in keywords):
            return s.strip()

    return default


# ---------------------------
# WIKIPEDIA SUMMARY FETCH
# ---------------------------
def wiki_fetch(topic: str):
    """
    Gets only the summary (fast & reliable).
    """
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '%20')}"
    logger.warning(f"FETCHING FROM WIKI: {url}")

    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
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
            "Symptoms vary based on the specific condition subtype."
        )

        causes = extract_keyword_section(
            summary,
            ["cause", "caused", "due to", "results from"],
            "Causes are not clearly mentioned in the summary."
        )

        treatment = extract_keyword_section(
            summary,
            ["treat", "treatment", "therapy", "managed"],
            "Treatment details are not included. Consult a medical professional."
        )

        prevention = extract_keyword_section(
            summary,
            ["prevent", "prevention", "avoid", "reduce risk"],
            "General precautions include hygiene, healthy lifestyle, and early checkups."
        )

        complications = extract_keyword_section(
            summary,
            ["complication", "risk", "danger", "serious", "life-threatening"],
            "Complications depend on severity and patient health."
        )

        # ---------- Build final formatted response ----------
        answer_en = f"""
📌 **Medical Information about {processed_query.title()}**

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

⚠️ *This assistant provides educational information only. It is not a substitute for professional medical advice.*
        """

        # Translate back
        final_answer = answer_en
        if language != "en":
            try:
                final_answer = self.translator.translate(answer_en, target=language)
            except:
                final_answer = answer_en

        return {
            "answer": final_answer,
            "citations": [{
                "source": "Wikipedia",
                "url": f"https://en.wikipedia.org/wiki/{processed_query.replace(' ', '_')}"
            }],
            "original_query": original_query,
            "processed_query": processed_query,
            "language": language,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

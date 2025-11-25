import logging
import re
import requests
from datetime import datetime
from typing import Dict, Any
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

# ---------------------------
# WIKIPEDIA FREE SEARCH
# ---------------------------
def wiki_fetch(topic: str):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (HealthBot/1.0; +https://render.com)"
        }

        # Step 1 — Search for the best match
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": topic,
            "format": "json"
        }

        search_res = requests.get(search_url, params=params, headers=headers, timeout=5)

        if search_res.status_code != 200:
            return None

        search_data = search_res.json()

        if "query" not in search_data or len(search_data["query"]["search"]) == 0:
            return None

        # Best matched page title
        title = search_data["query"]["search"][0]["title"]

        # Step 2 — Fetch summary for exact page
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '%20')}"
        summary_res = requests.get(summary_url, headers=headers, timeout=5)

        if summary_res.status_code != 200:
            return None

        return summary_res.json().get("extract")

    except Exception as e:
        print("WIKI ERROR:", e)
        return None

# ---------------------------
# BASIC MEDICAL INFO EXTRACTION
# ---------------------------
def extract_medical_sections(text: str):
    text_l = text.lower()

    symptoms = "Not specifically listed."
    causes = "Causes not clearly listed."
    treatment = "Treatment not clearly listed."
    prevention = "General health precautions apply."

    if "symptom" in text_l:
        symptoms = "Symptoms are mentioned in the summary."

    if "cause" in text_l or "caused" in text_l:
        causes = "Causes appear in the summary text."

    if "treat" in text_l or "therapy" in text_l:
        treatment = "Treatment options are referenced."

    if "prevent" in text_l:
        prevention = "Preventive guidance is mentioned."

    return symptoms, causes, treatment, prevention


# ---------------------------
# MAIN RAG ENGINE
# ---------------------------
class RAGEngine:

    def __init__(self):
        self.translator = GoogleTranslator(source="auto", target="en")
        logger.info("Wikipedia-based RAG Engine initialized.")

    async def process_query(self, query: str, language: str = "en") -> Dict[str, Any]:

        original_query = query

        # Translate → English
        processed_query = query
        if language != "en":
            try:
                processed_query = self.translator.translate(query, target="en")
            except Exception:
                pass

        # Get Wikipedia summary
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

        # Extract medical sections
        symptoms, causes, treatment, prevention = extract_medical_sections(summary)

        # Build answer
        answer_en = f"""
📌 **Medical Information about {processed_query.title()}**

📖 **Definition**
{summary}

🩺 **Symptoms**
- {symptoms}

⚠️ **Causes**
- {causes}

💊 **Treatment**
- {treatment}

🛡️ **Prevention / Precautions**
- {prevention}

⚠️ This bot provides educational health information only.  
Consult a doctor for diagnosis or treatment.
"""

        # Translate back
        final_answer = answer_en
        if language != "en":
            try:
                final_answer = self.translator.translate(answer_en, target=language)
            except:
                pass

        return {
            "answer": final_answer,
            "citations": [
                {
                    "source": "Wikipedia",
                    "url": f"https://en.wikipedia.org/wiki/{processed_query.replace(' ', '_')}"
                }
            ],
            "original_query": original_query,
            "processed_query": processed_query,
            "language": language,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

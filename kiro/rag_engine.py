import logging
import re
from datetime import datetime
from typing import Dict, Any, List
from deep_translator import GoogleTranslator
from wiki_search import wiki_search
from medical_formatter import format_medical_info

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> set:
    """Very simple tokenizer: lowercase & keep only word characters."""
    return set(re.findall(r"\b\w+\b", text.lower()))

import requests
from datetime import datetime
from deep_translator import GoogleTranslator
from typing import List, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------
# WIKIPEDIA FREE SEARCH
# ---------------------------
def wiki_fetch(topic: str):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '%20')}"
    res = requests.get(url)

    if res.status_code != 200:
        return None

    data = res.json()
    return data.get("extract")


# ---------------------------
# HEALTH INFORMATION EXTRACTION
# ---------------------------
def extract_sections(text: str):
    text_l = text.lower()

    symptoms = []
    causes = []
    prevention = []
    treatment = []

    # SIMPLE KEYWORD-BASED MEDICAL EXTRACTION
    if "symptom" in text_l:
        symptoms.append("The disease may present symptoms as mentioned in the medical summary.")

    if "cause" in text_l or "caused" in text_l:
        causes.append("The cause(s) are referenced in the provided medical text.")

    if "treat" in text_l:
        treatment.append("Treatment approaches are mentioned in the medical text.")

    if "prevent" in text_l:
        prevention.append("Preventive guidance is available in the summary text.")

    return symptoms, causes, treatment, prevention


# ---------------------------
# MAIN RAG ENGINE
# ---------------------------
class RAGEngine:

    def __init__(self):
        self.translator = GoogleTranslator(source="auto", target="en")
        logger.info("Wikipedia-based RAG initialized.")

    async def process_query(self, query: str, language: str = "en") -> Dict[str, Any]:

        original_query = query
        processed_query = query

        # Translate query → English
        if language != "en":
            try:
                processed_query = self.translator.translate(query, target="en")
            except Exception:
                processed_query = query

        # Fetch from Wikipedia
        summary = wiki_fetch(processed_query)

        if not summary:
            answer = "I could not find detailed medical information about this condition."
            return {
                "answer": answer,
                "citations": [],
                "original_query": original_query,
                "processed_query": processed_query,
                "language": language,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        # Extract structured medical info
        symptoms, causes, treatment, prevention = extract_sections(summary)

        # ----------- BUILD ANSWER -------------
        answer_en = f"""
📌 **Medical Information about {processed_query.title()}**

📖 **Definition**
{summary}

🩺 **Symptoms**
- {symptoms[0] if symptoms else "Not specifically listed. Symptoms differ by individual and subtype."}

⚠️ **Causes**
- {causes[0] if causes else "Causes not clearly listed. May require more detailed clinical sources."}

💊 **Treatment**
- {treatment[0] if treatment else "Treatment not clearly listed. Consult a certified medical provider."}

🛡️ **Prevention / Precautions**
- {prevention[0] if prevention else "General health precautions may apply: hygiene, sanitation, vaccinations (if applicable), and regular checkups."}

⚠️ *This bot provides educational health information only. For diagnosis or treatment, please consult a healthcare professional.*
        """

        # Translate answer back to user language
        final_answer = answer_en
        if language != "en":
            try:
                final_answer = self.translator.translate(answer_en, target=language)
            except:
                final_answer = answer_en

        return {
            "answer": final_answer,
            "citations": [{"source": "Wikipedia", "url": f"https://en.wikipedia.org/wiki/{processed_query.replace(' ', '_')}"}],
            "original_query": original_query,
            "processed_query": processed_query,
            "language": language,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

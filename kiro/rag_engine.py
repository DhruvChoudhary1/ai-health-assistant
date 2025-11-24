import logging
import re
from datetime import datetime
from typing import Dict, Any, List
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> set:
    """Very simple tokenizer: lowercase & keep only word characters."""
    return set(re.findall(r"\b\w+\b", text.lower()))


class RAGEngine:
    """
    Tiny in-memory 'RAG' engine.

    - Holds a small list of medical documents.
    - Uses keyword overlap to find the most relevant docs.
    - Optionally auto-translates question/answer via GoogleTranslator.
    """

    def __init__(self) -> None:
        # Translator (GoogleTranslator uses requests under the hood)
        self.translator = GoogleTranslator(source="auto", target="en")

        # Small health knowledge base
        self.documents: List[Dict[str, Any]] = [
            {
                "id": "doc_1",
                "content": (
                    "Diabetes is a chronic condition that affects how your body processes "
                    "blood sugar (glucose). Type 1 diabetes occurs when your immune system "
                    "attacks insulin-producing cells. Type 2 diabetes occurs when your body "
                    "becomes resistant to insulin or doesn't make enough insulin."
                ),
                "source": "WHO Diabetes Fact Sheet 2023",
                "category": "diabetes",
                "url": "https://www.who.int/news-room/fact-sheets/detail/diabetes",
            },
            {
                "id": "doc_2",
                "content": (
                    "Hypertension (high blood pressure) is a serious medical condition that "
                    "significantly increases the risks of heart, brain, kidney and other "
                    "diseases. Blood pressure is measured in millimeters of mercury (mmHg) "
                    "and is recorded as two numbers: systolic pressure (when the heart beats) "
                    "over diastolic pressure (when the heart rests between beats)."
                ),
                "source": "American Heart Association Guidelines 2023",
                "category": "hypertension",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure",
            },
            {
                "id": "doc_3",
                "content": (
                    "Regular physical activity is one of the most important things you can do "
                    "for your health. It can help control your weight, reduce your risk of "
                    "heart disease, strengthen your bones and muscles, and improve your "
                    "mental health and mood. Adults should aim for at least 150 minutes of "
                    "moderate-intensity aerobic activity per week."
                ),
                "source": "CDC Physical Activity Guidelines 2023",
                "category": "exercise",
                "url": "https://www.cdc.gov/physicalactivity/basics/adults/index.htm",
            },
            {
                "id": "doc_4",
                "content": (
                    "A balanced diet includes a variety of foods from all food groups: fruits, "
                    "vegetables, whole grains, lean proteins, and healthy fats. Limiting "
                    "processed foods, added sugars, and excessive sodium can help prevent "
                    "chronic diseases and maintain optimal health."
                ),
                "source": "Harvard School of Public Health 2023",
                "category": "nutrition",
                "url": "https://www.hsph.harvard.edu/nutritionsource/healthy-eating-plate/",
            },
            {
                "id": "doc_5",
                "content": (
                    "Mental health includes our emotional, psychological, and social well-being. "
                    "It affects how we think, feel, and act. Good mental health is essential at "
                    "every stage of life. Common mental health conditions include depression, "
                    "anxiety disorders, and stress-related disorders."
                ),
                "source": "National Institute of Mental Health 2023",
                "category": "mental_health",
                "url": "https://www.nimh.nih.gov/health/topics/mental-health-information",
            },
        ]

        # Pre-compute token sets for each document for quick similarity checks
        for doc in self.documents:
            doc["tokens"] = _tokenize(doc["content"])

        logger.info("Lightweight RAGEngine initialized with %d documents", len(self.documents))

    def _score(self, query_tokens: set, doc_tokens: set) -> float:
        """Simple overlap score between query tokens and document tokens."""
        if not query_tokens or not doc_tokens:
            return 0.0
        overlap = query_tokens.intersection(doc_tokens)
        return len(overlap) / len(doc_tokens)

    def _retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Return docs sorted by simple keyword overlap with the query."""
        q_tokens = _tokenize(query)
        scored = []
        for doc in self.documents:
            score = self._score(q_tokens, doc["tokens"])
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        # At least 1 doc
        return [d for _, d in scored[:3]] or [self.documents[0]]

    def _build_answer(self, query: str, docs: List[Dict[str, Any]]) -> str:
        """Construct a readable answer from retrieved docs."""
        intro = "Based on trusted health information sources:\n\n"
        parts = []

        for i, doc in enumerate(docs, start=1):
            parts.append(f"{i}. {doc['content']}")

        body = "\n\n".join(parts)

        disclaimer = (
            "\n\n⚠️ Important: This assistant provides *educational* information only. "
            "It is not a substitute for professional medical advice, diagnosis, or treatment. "
            "Always consult a qualified healthcare professional about your own health."
        )

        return intro + body + disclaimer

    async def process_query(self, query: str, language: str = "en") -> Dict[str, Any]:
        """
        Main entrypoint used by FastAPI & Telegram.

        Returns a dict with: answer, citations, original_query, processed_query, language, timestamp.
        """
        original_query = query
        processed_query = query

        # 1) Translate to English if needed
        if language != "en":
            try:
                processed_query = self.translator.translate(query, target="en")
            except Exception as e:
                logger.warning("Translation to EN failed: %s", e)
                processed_query = query  # fallback

        # 2) Retrieve relevant docs
        try:
            docs = self._retrieve(processed_query)
        except Exception as e:
            logger.error("Retrieval error: %s", e)
            docs = [self.documents[0]]

        # 3) Build answer in English
        answer_en = self._build_answer(processed_query, docs)

        # 4) Translate answer back if needed
        answer = answer_en
        if language != "en":
            try:
                answer = self.translator.translate(answer_en, target=language)
            except Exception as e:
                logger.warning("Answer translation failed: %s", e)
                answer = answer_en

        # 5) Build citations
        citations = [
            {
                "id": idx + 1,
                "source": d["source"],
                "url": d["url"],
                "category": d["category"],
            }
            for idx, d in enumerate(docs)
        ]

        return {
            "answer": answer,
            "citations": citations,
            "original_query": original_query,
            "processed_query": processed_query,
            "language": language,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

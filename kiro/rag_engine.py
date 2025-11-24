import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer
from deep_translator import GoogleTranslator
import requests
import logging
import re

from local_llm import LocalLLM, HealthKnowledgeBase

logger = logging.getLogger(__name__)


class RAGEngine:
    def __init__(self):
        # Embeddings + docs
        self.embedding_model: SentenceTransformer | None = None
        self.documents: list[dict[str, Any]] = []
        self.doc_embeddings: np.ndarray | None = None  # shape: (N, dim)

        # Translation
        # (we'll create new translators per call to avoid weird state bugs)
        # self.translator = GoogleTranslator(source="auto", target="en")

        # Local LLM + rule-based KB
        self.local_llm = LocalLLM()
        self.health_kb = HealthKnowledgeBase()

        # Optional HF key (can be empty)
        self.hf_headers = {
            "Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY', 'hf_demo')}"
        }

    async def initialize(self):
        """Initialize the RAG engine components (in-memory only)."""
        try:
            logger.info("Initializing RAG engine (in-memory)…")

            # Load embedding model
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer loaded.")

            # Load health knowledge base into memory
            await self._load_knowledge_base()

            logger.info(
                f"Knowledge base loaded ({len(self.documents)} docs only)."
            )
            logger.info("RAG Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {str(e)}")
            # If this fails, the app can’t really answer questions → re-raise
            raise

    async def _load_knowledge_base(self):
        """Load health knowledge base into memory and precompute embeddings."""
        health_documents = [
            {
                "id": "doc_1",
                "content": (
                    "Diabetes is a chronic condition that affects how your body "
                    "processes blood sugar (glucose). Type 1 diabetes occurs when "
                    "your immune system attacks insulin-producing cells. Type 2 "
                    "diabetes occurs when your body becomes resistant to insulin "
                    "or doesn't make enough insulin."
                ),
                "source": "WHO Diabetes Fact Sheet 2023",
                "category": "diabetes",
                "url": "https://www.who.int/news-room/fact-sheets/detail/diabetes",
            },
            {
                "id": "doc_2",
                "content": (
                    "Hypertension (high blood pressure) is a serious medical "
                    "condition that significantly increases the risks of heart, "
                    "brain, kidney and other diseases. Blood pressure is measured "
                    "in millimeters of mercury (mmHg) and is recorded as two "
                    "numbers: systolic pressure (when the heart beats) over "
                    "diastolic pressure (when the heart rests between beats)."
                ),
                "source": "American Heart Association Guidelines 2023",
                "category": "hypertension",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure",
            },
            {
                "id": "doc_3",
                "content": (
                    "Regular physical activity is one of the most important things "
                    "you can do for your health. It can help control your weight, "
                    "reduce your risk of heart disease, strengthen your bones and "
                    "muscles, and improve your mental health and mood. Adults "
                    "should aim for at least 150 minutes of moderate-intensity "
                    "aerobic activity per week."
                ),
                "source": "CDC Physical Activity Guidelines 2023",
                "category": "exercise",
                "url": "https://www.cdc.gov/physicalactivity/basics/adults/index.htm",
            },
            {
                "id": "doc_4",
                "content": (
                    "A balanced diet includes a variety of foods from all food "
                    "groups: fruits, vegetables, whole grains, lean proteins, and "
                    "healthy fats. Limiting processed foods, added sugars, and "
                    "excessive sodium can help prevent chronic diseases and "
                    "maintain optimal health."
                ),
                "source": "Harvard School of Public Health 2023",
                "category": "nutrition",
                "url": "https://www.hsph.harvard.edu/nutritionsource/healthy-eating-plate/",
            },
            {
                "id": "doc_5",
                "content": (
                    "Mental health includes our emotional, psychological, and "
                    "social well-being. It affects how we think, feel, and act. "
                    "Good mental health is essential at every stage of life. "
                    "Common mental health conditions include depression, anxiety "
                    "disorders, and stress-related disorders."
                ),
                "source": "National Institute of Mental Health 2023",
                "category": "mental_health",
                "url": "https://www.nimh.nih.gov/health/topics/mental-health-information",
            },
        ]

        self.documents = health_documents

        # Compute embeddings (and normalize for cosine similarity)
        texts = [d["content"] for d in health_documents]
        raw_embeddings = self.embedding_model.encode(
            texts, show_progress_bar=True
        )
        # Normalize
        norms = np.linalg.norm(raw_embeddings, axis=1, keepdims=True)
        self.doc_embeddings = raw_embeddings / norms

    # ------------------- RAG QUERY -------------------

    async def process_query(
        self, query: str, language: str = "en"
    ) -> Dict[str, Any]:
        """Process user query and return RAG-based response."""
        try:
            if self.embedding_model is None or self.doc_embeddings is None:
                raise RuntimeError("RAGEngine not initialized")

            original_query = query

            # Translate query to English if needed
            if language != "en":
                query = GoogleTranslator(
                    source=language, target="en"
                ).translate(query)

            # Embed query
            q_emb = self.embedding_model.encode(query)
            q_emb = q_emb / np.linalg.norm(q_emb)

            # Cosine similarity with all docs
            sims = self.doc_embeddings @ q_emb  # (N,)

            # Get top 3 documents
            top_idx = np.argsort(-sims)[:3]

            context_docs = []
            citations = []

            for rank, idx in enumerate(top_idx, start=1):
                score = float(sims[idx])
                if score < 0.2:  # relevance threshold
                    continue

                doc = self.documents[idx]
                context_docs.append(doc["content"])
                citations.append(
                    {
                        "id": rank,
                        "source": doc["source"],
                        "url": doc.get("url", ""),
                        "relevance_score": round(score, 3),
                    }
                )

            context = "\n\n".join(context_docs)

            # Generate response (rule-based / local LLM / fallback)
            answer = await self._generate_response(query, context)

            # Translate back if needed
            if language != "en":
                answer = GoogleTranslator(
                    source="en", target=language
                ).translate(answer)

            return {
                "answer": answer,
                "citations": citations,
                "original_query": original_query,
                "processed_query": query,
                "language": language,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"process_query error: {str(e)}")
            return {
                "answer": (
                    "I apologize, but I'm experiencing technical difficulties. "
                    "Please try again later."
                ),
                "citations": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    # ------------------- RESPONSE GENERATION -------------------

    async def _generate_response(self, query: str, context: str) -> str:
        """Generate response using free / local methods."""
        try:
            # 1) Rule-based knowledge base
            kb_response = self.health_kb.get_response(query)
            if kb_response:
                return kb_response

            # 2) Local LLM if available
            if getattr(self.local_llm, "model", None) is not None:
                try:
                    llm_response = self.local_llm.generate_response(query, context)
                    if llm_response and len(llm_response) > 50:
                        return (
                            llm_response
                            + "\n\n⚠️ Important: This information is for educational "
                            "purposes only. Always consult qualified healthcare "
                            "professionals for medical advice."
                        )
                except Exception as e:
                    logger.warning(f"Local LLM failed: {str(e)}")

            # 3) HuggingFace API (optional)
            if os.getenv("HUGGINGFACE_API_KEY") and os.getenv(
                "HUGGINGFACE_API_KEY"
            ) != "hf_demo":
                try:
                    hf_response = await self._enhance_with_hf("", query)
                    if hf_response:
                        return hf_response
                except Exception as e:
                    logger.warning(f"HuggingFace API failed: {str(e)}")

            # 4) Simple context-based fallback
            return self._create_contextual_response(query, context)

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return (
                "I'm sorry, I couldn't generate a response at this time. "
                "Please consult with a healthcare professional for medical advice."
            )

    def _create_contextual_response(self, query: str, context: str) -> str:
        """Very simple heuristic response using retrieved context."""
        if not context:
            return (
                "I don't have enough information to answer your question accurately. "
                "Please consult with a healthcare professional for medical advice."
            )

        sentences = [s.strip() for s in context.split(".") if s.strip()]
        query_words = set(query.lower().split())

        scored = []
        for s in sentences:
            words = set(s.lower().split())
            overlap = len(words & query_words)
            if overlap > 0:
                scored.append((s, overlap))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s for s, _ in scored[:3]] or sentences[:2]

        response = "Based on the available medical information:\n\n"
        response += ". ".join(top_sentences)

        response += "\n\n[1] Medical literature and health guidelines"
        response += (
            "\n\n⚠️ Important: This information is for educational purposes only. "
            "Always consult with qualified healthcare professionals for medical "
            "advice, diagnosis, or treatment."
        )
        return response

    async def _enhance_with_hf(self, base_response: str, query: str) -> str | None:
        """Optionally enhance using a HuggingFace text-gen model."""
        try:
            payload = {
                "inputs": f"Health Question: {query}\nAnswer: {base_response[:200]}",
                "parameters": {
                    "max_length": 300,
                    "temperature": 0.7,
                    "do_sample": True,
                },
            }

            resp = requests.post(
                "https://api-inference.huggingface.co/models/gpt2",
                headers=self.hf_headers,
                json=payload,
                timeout=10,
            )

            if resp.status_code == 200:
                result = resp.json()
                if isinstance(result, list) and result:
                    generated = result[0].get("generated_text", "")
                    if "Answer:" in generated:
                        enhanced = generated.split("Answer:", 1)[1].strip()
                        if len(enhanced) > 50:
                            return (
                                enhanced
                                + "\n\n⚠️ Important: This information is for "
                                "educational purposes only. Always consult qualified "
                                "healthcare professionals for medical advice."
                            )
            return None
        except Exception as e:
            logger.warning(f"HuggingFace enhancement failed: {str(e)}")
            return None

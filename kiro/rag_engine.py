import os
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_TELEMETRY"] = "false"
import chromadb
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from deep_translator import GoogleTranslator
import logging
import re

# Disable Chroma telemetry (VERY IMPORTANT)
os.environ["CHROMA_TELEMETRY"] = "False"

logger = logging.getLogger(__name__)



class RAGEngine:
    def __init__(self):
        self.client = None
        self.collection = None
        
        # Lightweight translator
        self.translator = GoogleTranslator()

        # Embedding model (only MiniLM)
        self.embedding_model = None  

    async def initialize(self):
        """Initialize the RAG engine components"""
        try:
            persist_directory = "./chroma_db"
            os.makedirs(persist_directory, exist_ok=True)

            # Very lightweight ChromaDB
            self.client = chromadb.PersistentClient(
    path=persist_directory,
    settings=Settings(anonymized_telemetry=False)
)


            # Load embeddings (very small)
            self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

            # Load docs only once
            if self.collection.count() == 0:
                await self._load_knowledge_base()

            logger.info("RAG Engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {str(e)}")
            raise

    async def _load_knowledge_base(self):
        """Load 5 tiny documents only (fast startup)"""
        health_docs = [
            {
                "id": "d1",
                "content": "Diabetes is a chronic condition that affects how your body processes blood sugar.",
                "source": "WHO"
            },
            {
                "id": "d2",
                "content": "Hypertension is high blood pressure and increases risks of heart disease.",
                "source": "AHA"
            },
            {
                "id": "d3",
                "content": "Regular exercise helps maintain weight and improve heart health.",
                "source": "CDC"
            },
            {
                "id": "d4",
                "content": "A balanced diet includes fruits, vegetables, whole grains, lean proteins, and healthy fats.",
                "source": "Harvard"
            },
            {
                "id": "d5",
                "content": "Mental health affects emotional and psychological well-being.",
                "source": "NIMH"
            }
        ]

        for doc in health_docs:
            emb = self.embedding_model.encode(doc["content"]).tolist()
            self.collection.add(
                embeddings=[emb],
                documents=[doc["content"]],
                metadatas=[{"source": doc["source"]}],
                ids=[doc["id"]]
            )

        logger.info("Knowledge base loaded (5 docs only).")

    async def process_query(self, query: str, language: str = "en"):
        """Process query using retrieval & simple generation"""
        try:
            original_query = query

            if language != "en":
                query = self.translator.translate(query, target="en")

            # Embedding
            q_emb = self.embedding_model.encode(query).tolist()

            # Retrieve
            results = self.collection.query(
                query_embeddings=[q_emb],
                n_results=3,
                include=["documents", "metadatas", "distances"]
            )

            docs = results["documents"][0]

            context = "\n".join(docs)

            answer = self._generate_simple_answer(query, context)

            if language != "en":
                answer = self.translator.translate(answer, target=language)

            return {
                "answer": answer,
                "citations": results["metadatas"][0],
                "original_query": original_query,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"process_query error: {str(e)}")
            return {
                "answer": "Sorry, something went wrong.",
                "error": str(e)
            }

    def _generate_simple_answer(self, query: str, context: str) -> str:
        """Lightweight rule-based summarization (fast)"""
        if not context:
            return "I could not find relevant health information."

        response = f"Based on medical information:\n\n{context}\n\n⚠️ Educational use only."
        return response

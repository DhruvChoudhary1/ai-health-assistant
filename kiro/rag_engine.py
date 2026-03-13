import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import requests
from deep_translator import GoogleTranslator

import logging
import re
from local_llm import LocalLLM, HealthKnowledgeBase

logger = logging.getLogger(__name__)


def translate_text(text, target="en"):
    """Helper for simple one-off translations."""
    return GoogleTranslator(source="auto", target=target).translate(text)

class RAGEngine:
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_model = None
        # Default translator; we will re-create with specific languages when needed
        self.translator = GoogleTranslator(source="auto", target="en")
        # Use free alternatives
        self.local_llm = LocalLLM()
        self.health_kb = HealthKnowledgeBase()
        self.hf_headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY', 'hf_demo')}"}
        # Simple medicine knowledge base for /medicine queries
        self.medicine_info = {
            "paracetamol": {
                "uses": ["fever", "mild to moderate pain"],
                "dosage": "Usually 500–650 mg every 4–6 hours as needed (do not exceed 3,000–4,000 mg per day in adults; follow local guidelines).",
                "side_effects": [
                    "nausea",
                    "allergic reactions (rare)",
                    "liver damage in overdose or with chronic heavy use",
                ],
            },
            "ibuprofen": {
                "uses": ["pain", "inflammation", "fever"],
                "dosage": "Typically 200–400 mg every 6–8 hours with food (maximum daily dose depends on local guidelines; follow package or doctor instructions).",
                "side_effects": [
                    "stomach irritation",
                    "heartburn",
                    "kidney strain in dehydration or long-term high doses",
                ],
            },
        }

    async def initialize(self):
        """Initialize the RAG engine components and load medical knowledge base."""
        try:
            # Initialize ChromaDB
            persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="health_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize local LLM (optional)
            use_local_llm = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
            if use_local_llm:
                await self.local_llm.initialize()
            
            # Load knowledge base if collection is empty
            if self.collection.count() == 0:
                await self._load_knowledge_base()
                
            logger.info("RAG Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {str(e)}")
            raise
    
    async def _load_knowledge_base(self):
        """Load health knowledge base into vector database from JSON files."""
        base_dir = os.path.dirname(__file__)
        kb_dir = os.path.join(base_dir, "knowledge_base")
        documents: list[dict[str, Any]] = []

        # Load primary structured health documents if available
        json_path = os.path.join(kb_dir, "health_documents.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    docs_from_json = json.load(f)
                    if isinstance(docs_from_json, list):
                        documents.extend(docs_from_json)
            except Exception as e:
                logger.warning(f"Failed to load health_documents.json: {e}")

        # Fallback: add a few core documents if JSON is missing/empty
        if not documents:
            documents = [
                {
                    "id": "core_diabetes",
                    "title": "Diabetes Overview",
                    "content": "Diabetes is a chronic condition that affects how your body processes blood sugar (glucose). Type 1 diabetes is autoimmune; Type 2 is due to insulin resistance.",
                    "source": "WHO Diabetes Fact Sheet 2023",
                    "category": "diseases",
                    "url": "https://www.who.int/news-room/fact-sheets/detail/diabetes",
                    "language": "en",
                }
            ]

        if not documents:
            logger.warning("No health documents found for knowledge base.")
            return

        added = 0
        for doc in documents:
            content = doc.get("content")
            doc_id = doc.get("id") or f"kb_{added}"
            if not content:
                continue

            embedding = self.embedding_model.encode(content).tolist()

            metadata = {
                "source": doc.get("source", "medical_knowledge_base"),
                "category": doc.get("category", "general"),
                "url": doc.get("url", ""),
                "title": doc.get("title", ""),
                "language": doc.get("language", "en"),
            }

            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id],
            )
            added += 1

        logger.info(f"Loaded {added} documents into medical knowledge base")
    
    async def process_query(
        self,
        query: str,
        language: str = "en",
        history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        """Process user query and return RAG-based response with basic triage and memory."""
        try:
            # Translate query to English if needed
            original_query = query
            if language != "en":
                translator = GoogleTranslator(source=language, target="en")
                query = translator.translate(query)

            # Prepend brief conversation history, if available
            if history:
                # Keep only last few exchanges to stay concise
                recent = history[-4:]
                history_snippets = []
                for turn in recent:
                    role = turn.get("role", "user")
                    content = turn.get("content", "")
                    history_snippets.append(f"{role.capitalize()}: {content}")
                history_text = "\n".join(history_snippets)
                query_with_context = f"Conversation so far:\n{history_text}\n\nCurrent question: {query}"
            else:
                query_with_context = query

            # Symptom triage (very simple heuristic)
            triage = self._analyze_symptom_risk(query)
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query_with_context).tolist()
            
            # Retrieve relevant documents
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                include=["documents", "metadatas", "distances"]
            )
            
            # Prepare context from retrieved documents
            context_docs = []
            citations = []
            
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0], 
                results["distances"][0]
            )):
                if distance < 0.8:  # Relevance threshold
                    context_docs.append(doc)
                    citations.append({
                        "id": i + 1,
                        "source": metadata["source"],
                        "url": metadata.get("url", ""),
                        "relevance_score": round(1 - distance, 3)
                    })
            
            # Generate response
            context = "\n\n".join(context_docs)
            response_text = await self._generate_response(query, context)

            # Attach triage banner if applicable
            if triage:
                banner = (
                    f"🚨 Risk Level: {triage['risk_level'].upper()}\n"
                    f"{triage['message']}\n\n"
                )
                response_text = banner + response_text
            
            # Translate response back to original language if needed
            if language != "en":
                back_translator = GoogleTranslator(source="en", target=language)
                response_text = back_translator.translate(response_text)
            
            return {
                "answer": response_text,
                "citations": citations,
                "original_query": original_query,
                "processed_query": query_with_context,
                "language": language,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "answer": "I apologize, but I'm experiencing technical difficulties. Please try again later.",
                "citations": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_response(self, query: str, context: str) -> str:
        """Generate response using free alternatives"""
        try:
            # Method 1: Try rule-based health knowledge base first
            kb_response = self.health_kb.get_response(query)
            if kb_response:
                return kb_response
            
            # Method 2: Try local LLM if available
            if self.local_llm.model:
                try:
                    llm_response = self.local_llm.generate_response(query, context)
                    if llm_response and len(llm_response) > 50:
                        return llm_response + "\n\n⚠️ Important: This information is for educational purposes only. Always consult qualified healthcare professionals for medical advice."
                except Exception as e:
                    logger.warning(f"Local LLM failed: {str(e)}")
            
            # Method 3: Try HuggingFace API if available
            if os.getenv('HUGGINGFACE_API_KEY') and os.getenv('HUGGINGFACE_API_KEY') != 'hf_demo':
                try:
                    hf_response = await self._enhance_with_hf("", query)
                    if hf_response:
                        return hf_response
                except Exception as e:
                    logger.warning(f"HuggingFace API failed: {str(e)}")
            
            # Method 4: Fallback to context-based response
            return self._create_contextual_response(query, context)
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm sorry, I couldn't generate a response at this time. Please consult with a healthcare professional for medical advice."

    def _analyze_symptom_risk(self, text: str) -> Dict[str, Any] | None:
        """Very simple symptom triage: flag obviously dangerous patterns."""
        lowered = text.lower()
        emergencies_high = [
            "chest pain",
            "difficulty breathing",
            "shortness of breath",
            "can't breathe",
            "cannot breathe",
            "severe headache",
            "sudden weakness",
            "stroke",
            "unconscious",
            "not waking up",
            "heavy bleeding",
        ]
        emergencies_medium = [
            "high fever",
            "fever for 3 days",
            "vomiting blood",
            "blood in stool",
            "severe abdominal pain",
        ]

        for phrase in emergencies_high:
            if phrase in lowered:
                return {
                    "risk_level": "high",
                    "message": (
                        "These symptoms may indicate a serious condition. "
                        "Please seek emergency medical help immediately or go to the nearest hospital."
                    ),
                }

        for phrase in emergencies_medium:
            if phrase in lowered:
                return {
                    "risk_level": "medium",
                    "message": (
                        "Your symptoms could be significant. "
                        "Please monitor closely and seek medical care as soon as possible, "
                        "especially if they worsen."
                    ),
                }

        return None
    
    def _create_contextual_response(self, query: str, context: str) -> str:
        """Create response using context and rule-based approach"""
        if not context:
            return "I don't have enough information to answer your question accurately. Please consult with a healthcare professional for medical advice."
        
        # Extract key information from context
        sentences = context.split('.')
        relevant_sentences = []
        
        # Simple keyword matching to find most relevant sentences
        query_words = set(query.lower().split())
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Skip very short sentences
                sentence_words = set(sentence.lower().split())
                # Calculate overlap
                overlap = len(query_words.intersection(sentence_words))
                if overlap > 0:
                    relevant_sentences.append((sentence, overlap))
        
        # Sort by relevance and take top sentences
        relevant_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in relevant_sentences[:3]]
        
        if not top_sentences:
            top_sentences = sentences[:2]  # Fallback to first sentences
        
        # Create response
        response = "Based on the available medical information:\n\n"
        response += ". ".join(top_sentences)
        
        # Add citations
        response += "\n\n[1] Medical literature and health guidelines"
        
        # Add disclaimer
        response += "\n\n⚠️ Important: This information is for educational purposes only. Always consult with qualified healthcare professionals for medical advice, diagnosis, or treatment."
        
        return response
    
    async def _enhance_with_hf(self, base_response: str, query: str) -> str:
        """Try to enhance response using HuggingFace API (if available)"""
        try:
            # Use a free text generation model
            payload = {
                "inputs": f"Health Question: {query}\nAnswer: {base_response[:200]}",
                "parameters": {
                    "max_length": 300,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
            
            response = requests.post(
                "https://api-inference.huggingface.co/models/gpt2",
                headers=self.hf_headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    # Extract only the answer part
                    if 'Answer:' in generated_text:
                        enhanced = generated_text.split('Answer:')[1].strip()
                        if len(enhanced) > 50:  # Only use if substantial
                            return enhanced + "\n\n⚠️ Important: This information is for educational purposes only. Always consult with qualified healthcare professionals for medical advice."
            
            return None  # Fallback to base response
            
        except Exception as e:
            logger.warning(f"HuggingFace enhancement failed: {str(e)}")
            return None
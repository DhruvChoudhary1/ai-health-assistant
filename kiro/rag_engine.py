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
def translate_text(text, target='en'):
    return GoogleTranslator(source='auto', target=target).translate(text)

class RAGEngine:
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.translator = GoogleTranslator()
        # Use free alternatives
        self.local_llm = LocalLLM()
        self.health_kb = HealthKnowledgeBase()
        self.hf_headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY', 'hf_demo')}"}
        
    async def initialize(self):
        """Initialize the RAG engine components"""
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
        """Load health knowledge base into vector database"""
        # Sample health knowledge base
        health_documents = [
            {
                "id": "doc_1",
                "content": "Diabetes is a chronic condition that affects how your body processes blood sugar (glucose). Type 1 diabetes occurs when your immune system attacks insulin-producing cells. Type 2 diabetes occurs when your body becomes resistant to insulin or doesn't make enough insulin.",
                "source": "WHO Diabetes Fact Sheet 2023",
                "category": "diabetes",
                "url": "https://www.who.int/news-room/fact-sheets/detail/diabetes"
            },
            {
                "id": "doc_2", 
                "content": "Hypertension (high blood pressure) is a serious medical condition that significantly increases the risks of heart, brain, kidney and other diseases. Blood pressure is measured in millimeters of mercury (mmHg) and is recorded as two numbers: systolic pressure (when the heart beats) over diastolic pressure (when the heart rests between beats).",
                "source": "American Heart Association Guidelines 2023",
                "category": "hypertension",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure"
            },
            {
                "id": "doc_3",
                "content": "Regular physical activity is one of the most important things you can do for your health. It can help control your weight, reduce your risk of heart disease, strengthen your bones and muscles, and improve your mental health and mood. Adults should aim for at least 150 minutes of moderate-intensity aerobic activity per week.",
                "source": "CDC Physical Activity Guidelines 2023",
                "category": "exercise",
                "url": "https://www.cdc.gov/physicalactivity/basics/adults/index.htm"
            },
            {
                "id": "doc_4",
                "content": "A balanced diet includes a variety of foods from all food groups: fruits, vegetables, whole grains, lean proteins, and healthy fats. Limiting processed foods, added sugars, and excessive sodium can help prevent chronic diseases and maintain optimal health.",
                "source": "Harvard School of Public Health 2023",
                "category": "nutrition",
                "url": "https://www.hsph.harvard.edu/nutritionsource/healthy-eating-plate/"
            },
            {
                "id": "doc_5",
                "content": "Mental health includes our emotional, psychological, and social well-being. It affects how we think, feel, and act. Good mental health is essential at every stage of life. Common mental health conditions include depression, anxiety disorders, and stress-related disorders.",
                "source": "National Institute of Mental Health 2023",
                "category": "mental_health",
                "url": "https://www.nimh.nih.gov/health/topics/mental-health-information"
            }
        ]
        
        # Generate embeddings and store documents
        for doc in health_documents:
            embedding = self.embedding_model.encode(doc["content"]).tolist()
            
            self.collection.add(
                embeddings=[embedding],
                documents=[doc["content"]],
                metadatas=[{
                    "source": doc["source"],
                    "category": doc["category"],
                    "url": doc["url"]
                }],
                ids=[doc["id"]]
            )
        
        logger.info(f"Loaded {len(health_documents)} documents into knowledge base")
    
    async def process_query(self, query: str, language: str = "en") -> Dict[str, Any]:
        """Process user query and return RAG-based response"""
        try:
            # Translate query to English if needed
            original_query = query
            if language != "en":
                query = self.translator.translate(query, src=language, dest="en").text
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
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
            
            # Generate response using OpenAI
            context = "\n\n".join(context_docs)
            response = await self._generate_response(query, context)
            
            # Translate response back to original language if needed
            if language != "en":
                response = self.translator.translate(response, src="en", dest=language).text
            
            return {
                "answer": response,
                "citations": citations,
                "original_query": original_query,
                "processed_query": query,
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
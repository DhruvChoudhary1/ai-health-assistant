#!/usr/bin/env python3
"""
Comprehensive test suite for AI Health Chatbot
Tests RAG functionality, WhatsApp integration, and web endpoints
"""

import asyncio
import json
import pytest
import httpx
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_engine import RAGEngine


class TestRAGEngine:
    """Test RAG engine functionality"""
    
    @pytest.fixture
    async def rag_engine(self):
        """Create RAG engine instance for testing"""
        engine = RAGEngine()
        await engine.initialize()
        return engine
    
    @pytest.mark.asyncio
    async def test_initialization(self, rag_engine):
        """Test RAG engine initialization"""
        assert rag_engine.client is not None
        assert rag_engine.collection is not None
        assert rag_engine.embedding_model is not None
        
    @pytest.mark.asyncio
    async def test_query_processing_english(self, rag_engine):
        """Test query processing in English"""
        query = "What is diabetes?"
        result = await rag_engine.process_query(query, "en")
        
        assert "answer" in result
        assert "citations" in result
        assert len(result["answer"]) > 0
        assert isinstance(result["citations"], list)
        
    @pytest.mark.asyncio
    async def test_query_processing_multilingual(self, rag_engine):
        """Test query processing in different languages"""
        queries = [
            ("¿Qué es la diabetes?", "es"),
            ("Qu'est-ce que le diabète?", "fr"),
            ("मधुमेह क्या है?", "hi")
        ]
        
        for query, lang in queries:
            result = await rag_engine.process_query(query, lang)
            assert "answer" in result
            assert result["language"] == lang
            
    @pytest.mark.asyncio
    async def test_citation_generation(self, rag_engine):
        """Test that citations are properly generated"""
        query = "Tell me about hypertension"
        result = await rag_engine.process_query(query, "en")
        
        citations = result["citations"]
        if citations:  # If relevant documents found
            for citation in citations:
                assert "id" in citation
                assert "source" in citation
                assert "relevance_score" in citation
                
    @pytest.mark.asyncio
    async def test_empty_query(self, rag_engine):
        """Test handling of empty queries"""
        result = await rag_engine.process_query("", "en")
        assert "error" in result or len(result["answer"]) > 0



class TestWebEndpoints:
    """Test web API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import app
        return httpx.AsyncClient(app=app, base_url="http://test")
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_languages_endpoint(self, client):
        """Test supported languages endpoint"""
        response = await client.get("/languages")
        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert len(data["languages"]) >= 4
    
    @pytest.mark.asyncio
    async def test_chat_endpoint(self, client):
        """Test chat endpoint"""
        chat_data = {
            "message": "What is diabetes?",
            "language": "en"
        }
        
        response = await client.post("/chat", json=chat_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "citations" in data
        assert "language" in data
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_validation(self, client):
        """Test chat endpoint input validation"""
        # Test empty message
        response = await client.post("/chat", json={"message": "", "language": "en"})
        assert response.status_code == 400
        
        # Test missing message
        response = await client.post("/chat", json={"language": "en"})
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_home_endpoint(self, client):
        """Test home page endpoint"""
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_chat_flow(self):
        """Test complete chat flow from input to response"""
        from main import app
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # Test health check first
            health_response = await client.get("/health")
            assert health_response.status_code == 200
            
            # Test chat interaction
            chat_data = {
                "message": "What are the symptoms of diabetes?",
                "language": "en"
            }
            
            chat_response = await client.post("/chat", json=chat_data)
            assert chat_response.status_code == 200
            
            data = chat_response.json()
            assert len(data["response"]) > 0
            assert data["language"] == "en"
    
    @pytest.mark.asyncio
    async def test_multilingual_flow(self):
        """Test multilingual chat flow"""
        from main import app
        
        test_queries = [
            {"message": "¿Cuáles son los síntomas de la diabetes?", "language": "es"},
            {"message": "Quels sont les symptômes du diabète?", "language": "fr"},
        ]
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            for query in test_queries:
                response = await client.post("/chat", json=query)
                assert response.status_code == 200
                
                data = response.json()
                assert data["language"] == query["language"]

class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        from main import app
        
        async def make_request(client, message):
            return await client.post("/chat", json={
                "message": message,
                "language": "en"
            })
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # Create multiple concurrent requests
            tasks = [
                make_request(client, f"What is health condition {i}?")
                for i in range(5)
            ]
            
            responses = await asyncio.gather(*tasks)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_response_time(self):
        """Test response time is reasonable"""
        from main import app
        import time
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            start_time = time.time()
            
            response = await client.post("/chat", json={
                "message": "What is diabetes?",
                "language": "en"
            })
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 30  # Should respond within 30 seconds

def run_manual_tests():
    """Run manual tests for interactive testing"""
    print("🧪 Running Manual Tests for AI Health Chatbot")
    print("=" * 50)
    
    # Test 1: RAG Engine
    print("\n1. Testing RAG Engine...")
    try:
        async def test_rag():
            engine = RAGEngine()
            await engine.initialize()
            result = await engine.process_query("What is diabetes?", "en")
            print(f"✅ RAG Response: {result['answer'][:100]}...")
            print(f"✅ Citations: {len(result['citations'])} sources found")
        
        asyncio.run(test_rag())
    except Exception as e:
        print(f"❌ RAG Engine Error: {e}")
    
   
    
    # Test 3: API Endpoints
    print("\n3. Testing API Endpoints...")
    try:
        async def test_api():
            from main import app
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                # Health check
                health = await client.get("/health")
                print(f"✅ Health Check: {health.status_code}")
                
                # Languages
                languages = await client.get("/languages")
                print(f"✅ Languages: {len(languages.json()['languages'])} supported")
                
                # Chat
                chat = await client.post("/chat", json={
                    "message": "What is mental health?",
                    "language": "en"
                })
                print(f"✅ Chat Endpoint: {chat.status_code}")
        
        asyncio.run(test_api())
    except Exception as e:
        print(f"❌ API Endpoints Error: {e}")
    
    print("\n🎉 Manual testing completed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        run_manual_tests()
    else:
        # Run pytest
        pytest.main([__file__, "-v"])
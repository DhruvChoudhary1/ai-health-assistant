"""
Local LLM implementation for completely free offline usage
Uses lightweight models that can run on CPU
"""

import os
import logging
from typing import Optional
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

logger = logging.getLogger(__name__)

class LocalLLM:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.generator = None
        self.model_name = "microsoft/DialoGPT-small"  # Lightweight model
        
    async def initialize(self):
        """Initialize the local LLM model"""
        try:
            logger.info("Initializing local LLM model...")
            
            # Use CPU-friendly model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1,  # Use CPU
                max_length=200,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            logger.info("✅ Local LLM initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize local LLM: {str(e)}")
            return False
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using local LLM"""
        try:
            if not self.generator:
                return self._fallback_response(prompt, context)
            
            # Create a health-focused prompt
            health_prompt = f"""Health Assistant: I'm here to help with health questions.

Context: {context[:300]}

Question: {prompt}

Answer: Based on medical knowledge,"""

            # Generate response
            outputs = self.generator(
                health_prompt,
                max_length=len(health_prompt.split()) + 50,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True
            )
            
            generated_text = outputs[0]['generated_text']
            
            # Extract only the answer part
            if "Answer:" in generated_text:
                answer = generated_text.split("Answer:")[-1].strip()
                # Clean up the response
                answer = self._clean_response(answer)
                return answer
            
            return self._fallback_response(prompt, context)
            
        except Exception as e:
            logger.error(f"Local LLM generation error: {str(e)}")
            return self._fallback_response(prompt, context)
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the generated response"""
        # Remove incomplete sentences
        sentences = response.split('.')
        complete_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and not sentence.endswith(('...', 'etc')):
                complete_sentences.append(sentence)
        
        if complete_sentences:
            cleaned = '. '.join(complete_sentences[:3])  # Take first 3 sentences
            if not cleaned.endswith('.'):
                cleaned += '.'
            return cleaned
        
        return response[:200] + "..." if len(response) > 200 else response
    
    def _fallback_response(self, prompt: str, context: str) -> str:
        """Fallback response when LLM is not available"""
        if not context:
            return "I don't have enough information to answer your question accurately. Please consult with a healthcare professional for medical advice."
        
        # Simple keyword-based response generation
        sentences = context.split('.')
        relevant_sentences = []
        
        # Find sentences containing query keywords
        query_words = set(prompt.lower().split())
        
        for sentence in sentences:
            if len(sentence.strip()) > 20:
                sentence_words = set(sentence.lower().split())
                if query_words.intersection(sentence_words):
                    relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            response = "Based on medical information: " + '. '.join(relevant_sentences[:2])
            if not response.endswith('.'):
                response += '.'
        else:
            response = "Based on available information: " + sentences[0] if sentences else "Please consult a healthcare professional."
        
        return response

# Alternative: Rule-based health responses for specific topics
class HealthKnowledgeBase:
    def __init__(self):
        self.health_responses = {
            'diabetes': {
                'keywords': ['diabetes', 'blood sugar', 'glucose', 'insulin'],
                'response': """Diabetes is a chronic condition that affects how your body processes blood sugar (glucose). 
                There are two main types: Type 1 (autoimmune condition) and Type 2 (insulin resistance). 
                Management includes proper diet, regular exercise, blood sugar monitoring, and medication as prescribed. 
                [1] Always consult with healthcare professionals for proper diagnosis and treatment."""
            },
            'hypertension': {
                'keywords': ['hypertension', 'high blood pressure', 'blood pressure', 'bp'],
                'response': """Hypertension (high blood pressure) is a condition where blood pressure is consistently elevated. 
                Normal blood pressure is less than 120/80 mmHg. Risk factors include age, family history, obesity, and lifestyle. 
                Management includes healthy diet (low sodium), regular exercise, stress management, and medication if needed. 
                [1] Regular monitoring and medical supervision are essential."""
            },
            'exercise': {
                'keywords': ['exercise', 'physical activity', 'workout', 'fitness'],
                'response': """Regular physical activity is crucial for good health. Adults should aim for at least 150 minutes 
                of moderate-intensity aerobic activity per week, plus muscle-strengthening activities twice weekly. 
                Benefits include weight control, reduced disease risk, stronger bones, and improved mental health. 
                [1] Start slowly and gradually increase intensity. Consult healthcare providers before starting new exercise programs."""
            },
            'nutrition': {
                'keywords': ['nutrition', 'diet', 'food', 'eating', 'healthy eating'],
                'response': """A balanced diet includes fruits, vegetables, whole grains, lean proteins, and healthy fats. 
                Limit processed foods, added sugars, and excessive sodium. Stay hydrated and practice portion control. 
                The plate method: fill half with vegetables, quarter with lean protein, quarter with whole grains. 
                [1] Individual nutritional needs vary; consult with registered dietitians for personalized advice."""
            },
            'mental_health': {
                'keywords': ['mental health', 'depression', 'anxiety', 'stress', 'mood'],
                'response': """Mental health is as important as physical health. Common conditions include depression, anxiety, 
                and stress disorders. Warning signs include persistent sadness, excessive worry, sleep changes, and social withdrawal. 
                Treatment options include therapy, medication, support groups, and lifestyle changes. 
                [1] Seek professional help if symptoms interfere with daily life. Mental health support is available."""
            }
        }
    
    def get_response(self, query: str) -> Optional[str]:
        """Get rule-based response for health queries"""
        query_lower = query.lower()
        
        for topic, data in self.health_responses.items():
            if any(keyword in query_lower for keyword in data['keywords']):
                return data['response']
        
        return None
    
    def get_general_response(self) -> str:
        """Get general health response"""
        return """I'm here to help with general health information. I can provide information about common health topics 
        like diabetes, hypertension, nutrition, exercise, and mental health. Please ask specific questions about these topics. 
        
        ⚠️ Important: This information is for educational purposes only. Always consult qualified healthcare professionals 
        for medical advice, diagnosis, or treatment."""
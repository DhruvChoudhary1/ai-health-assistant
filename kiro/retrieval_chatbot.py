"""
Simple retrieval-based chatbot using cleaned medical Q&A pairs.
Finds the most similar user question and returns the corresponding answer.
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from llm_chatbot import LLMChatbot



class RetrievalChatbot:
    def __init__(self, csv_path='datasets/chatbot_conversations_cleaned.csv', llm_model_name='E:/models/mistral.gguf'):
        self.df = pd.read_csv(csv_path)
        self.questions = self.df['Description'].fillna("").tolist()
        self.answers = self.df['Doctor'].fillna("").tolist()
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.question_vecs = self.vectorizer.fit_transform(self.questions)
        self.llm = LLMChatbot(csv_path=csv_path, model_path=llm_model_name)

    def get_response(self, user_query, top_k=1, sim_threshold=0.5, context_window=3, return_similarity=False):
        user_vec = self.vectorizer.transform([user_query])
        sims = cosine_similarity(user_vec, self.question_vecs).flatten()
        max_sim = np.max(sims)
        # If no good match, fallback to LLM with no context
        if max_sim < sim_threshold:
            llm_answer = self.llm.get_response(user_query, context_window=0)
            if return_similarity:
                return (llm_answer, max_sim)
            return llm_answer
        # Otherwise, use top-k most similar Q&A as context for LLM
        top_indices = sims.argsort()[-top_k:][::-1]
        context = ""
        for idx in top_indices[:context_window]:
            context += f"Q: {self.questions[idx]}\nA: {self.answers[idx]}\n"
        # Prompt LLM to generate a new, original answer using context
        prompt = (
            "You are a helpful, empathetic medical assistant. Use the following Q&A as context, but do NOT copy the answers. Always generate a new, original, and supportive answer.\n"
            f"{context}Q: {user_query}\nA:"
        )
        answer = self.llm.generate_text(prompt)
        for dataset_answer in self.answers:
            if answer.strip().lower() == str(dataset_answer).strip().lower():
                paraphrase_prompt = (
                    "Paraphrase the following medical advice in a new, original way, making it more conversational and supportive. Do NOT use the same wording:\n"
                    f"{answer}"
                )
                answer = self.llm.generate_text(paraphrase_prompt)
                break
        answer = answer.replace('\n', '\n\n')
        if return_similarity:
            return (answer, max_sim)
        return answer

# Example usage
if __name__ == "__main__":
    bot = RetrievalChatbot()
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        print("Bot:", bot.get_response(user_input))

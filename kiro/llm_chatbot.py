import pandas as pd
from llama_cpp import Llama
import os

class LLMChatbot:
    def __init__(
        self,
        csv_path='datasets/chatbot_conversations_cleaned.csv',
        model_path='E:/models/mistral.gguf'
    ):
        # ✅ Load dataset
        self.df = pd.read_csv(csv_path)
        self.questions = self.df['Description'].fillna("").tolist()
        self.answers = self.df['Doctor'].fillna("").tolist()

        # ✅ Check model exists
        if not os.path.exists(model_path):
            raise FileNotFoundError("GGUF model not found at E:/models/mistral.gguf")

        print("Loading GGUF model (fast + stable)...")

        # ✅ Load model (optimized for your system)
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,        # context window
            n_threads=6,       # adjust based on CPU
            n_batch=512,
            verbose=False
        )

        print("Model loaded successfully!\n")

    def generate_text(self, prompt):
        output = self.llm(
            prompt,
            max_tokens=256,
            temperature=0.7,
            stop=["Q:", "\n\nQ:"]
        )
        return output["choices"][0]["text"].strip()

    def get_response(self, user_query, context_window=3):
        # ✅ Retrieve context
        context = ""
        for i, q in enumerate(self.questions):
            if user_query.lower() in q.lower():
                context = f"Q: {q}\nA: {self.answers[i]}\n" + context
                if context.count('Q:') >= context_window:
                    break

        # ✅ Prompt
        prompt = (
            "You are a helpful, empathetic medical assistant.\n"
            "Use the following Q&A as context, but DO NOT copy answers.\n"
            "Always generate a new, original, and supportive response.\n\n"
            f"{context}Q: {user_query}\nA:"
        )

        answer = self.generate_text(prompt)

        return answer.replace('\n', '\n\n')


# ✅ Run chatbot
if __name__ == "__main__":
    bot = LLMChatbot()

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        print("Bot:", bot.get_response(user_input))
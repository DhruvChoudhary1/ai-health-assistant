import pandas as pd
from llama_cpp import Llama
import os
import multiprocessing

class LLMChatbot:
    def __init__(
        self,
        csv_path='datasets/chatbot_conversations_cleaned.csv',
        model_path='E:/models/mistral.gguf'
    ):
        self.model_path = os.getenv("LLM_MODEL_PATH", model_path)
        self.n_ctx = int(os.getenv("LLM_N_CTX", "2048"))
        self.n_batch = int(os.getenv("LLM_N_BATCH", "512"))
        cpu_count = multiprocessing.cpu_count() or 4
        self.n_threads = int(os.getenv("LLM_THREADS", str(max(1, cpu_count - 1))))
        self.n_gpu_layers = int(os.getenv("LLM_GPU_LAYERS", "35"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "160"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.6"))

        # ✅ Load dataset
        self.df = pd.read_csv(csv_path)
        self.questions = self.df['Description'].fillna("").tolist()
        self.answers = self.df['Doctor'].fillna("").tolist()

        # ✅ Check model exists
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"GGUF model not found at {self.model_path}")

        print("Loading GGUF model (fast + stable)...")
        print(
            f"Config -> n_ctx={self.n_ctx}, n_batch={self.n_batch}, n_threads={self.n_threads}, "
            f"n_gpu_layers={self.n_gpu_layers}, max_tokens={self.max_tokens}"
        )

        # ✅ Load model (optimized for your system)
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            n_batch=self.n_batch,
            n_gpu_layers=self.n_gpu_layers,
            verbose=False
        )

        print("Model loaded successfully!\n")

    def generate_text(self, prompt):
        output = self.llm(
            prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
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
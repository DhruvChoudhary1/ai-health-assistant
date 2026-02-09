---
# 🌍 HARMONY – AI Health Assistant Chatbot  
### Healthcare AI for Responsive Multilingual Online Interaction System  

HARMONY is a community-focused **AI-powered healthcare assistant chatbot** designed to provide reliable medical awareness and educational guidance through conversational interaction.  

Built with **FastAPI**, integrated with **Telegram**, and powered by a lightweight **Wikipedia-based Retrieval-Augmented Generation (RAG)** engine, HARMONY ensures accessible healthcare support for users anytime, anywhere.

---

## ✨ Key Highlights

✅ AI-driven Health Chatbot (Web + Telegram)  
✅ Multilingual Query Support (English, Hindi, Spanish, French)  
✅ Wikipedia REST API powered Medical Retrieval  
✅ Structured Responses (Definition, Symptoms, Causes, Treatment, Prevention)  
✅ Privacy-Friendly (No user conversations stored)  
✅ Dockerized Deployment for Portability  
✅ Community-Oriented EPICS Healthcare Awareness Project  

---

## 🚀 Features

### 🩺 Medical Information Assistance  
Users can ask about diseases such as:

- Jaundice  
- Diabetes  
- Dengue  
- Malaria  
- Fever & common symptoms  

The assistant responds with structured and easy-to-understand health information.

---

### 🌐 Multilingual Support  
HARMONY accepts queries in:

- English 🇺🇸  
- Hindi 🇮🇳  
- Spanish 🇪🇸  
- French 🇫🇷  

(Currently responses are shown in English; multilingual output is part of future scope.)

---

### 🤖 Telegram Bot Integration  
HARMONY is available directly through Telegram, allowing users to chat without installing any additional application.

---

### 🐳 Docker Deployment  
The entire project is containerized for easy deployment across platforms.

---

## 🛠️ Tech Stack

| Component | Technology |
|----------|------------|
| Backend | FastAPI (Python) |
| Retrieval Engine | Wikipedia REST API (Lightweight RAG) |
| Translation | deep-translator (GoogleTranslator) |
| Bot Platform | Telegram Bot API |
| Deployment | Docker |
| Frontend | HTML, CSS, JavaScript |

---

## 📂 Project Structure

```

ai-health-assistant/
│
├── main.py                 # FastAPI backend server
├── telegram_handler.py     # Telegram bot integration
├── rag_engine.py           # Wikipedia-based RAG engine
├── medical_formatter.py    # Structured medical response formatter
│
├── templates/              # HTML templates for Web UI
├── static/                 # CSS, JS, assets
├── knowledge_base/         # Future expansion datasets
│
├── Dockerfile              # Container deployment config
├── requirements.txt        # Project dependencies
└── README.md               # Documentation

````

---

## ⚙️ Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/harmony-ai-health-assistant.git
cd harmony-ai-health-assistant
````

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # On Linux/Mac
venv\Scripts\activate           # On Windows
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Configure Environment Variables

Create a `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
SUPPORTED_LANGUAGES=en,hi,es,fr
```

---

### 5️⃣ Run Web Application

```bash
python main.py
```

Open in browser:

👉 [http://localhost:8000](http://localhost:8000)

---

### 6️⃣ Run Telegram Bot

```bash
python telegram_handler.py
```

Now you can chat with HARMONY directly on Telegram.

---

## 🐳 Run Using Docker

### Build Docker Image

```bash
docker build -t harmony_bot .
```

### Run Container

```bash
docker run -d -p 8000:8000 --name harmony_bot harmony_bot
```

HARMONY will be live at:

👉 [http://localhost:8000](http://localhost:8000)

---

## 🔍 How HARMONY Works (Wikipedia RAG Pipeline)

1. User enters a health query
2. Query is translated into English (if needed)
3. Topic is extracted from the question
4. Wikipedia REST API retrieves medical summary
5. Response is formatted into structured sections
6. Output is delivered via Web UI or Telegram

---

## 🔮 Future Scope

Planned enhancements include:

* 🌍 Multilingual Output Translation
* 🎙️ Voice-based Interaction (Speech-to-Text & Text-to-Speech)
* 📚 Larger Verified Medical Dataset Integration
* 🧠 Advanced Symptom Checker Module

---

## 🏆 Submission Category

This project is submitted under:

### **Wildcard / Freestyle Category**

---

## 🤝 Contributing

Contributions, suggestions, and pull requests are welcome!
Feel free to fork the repository and improve HARMONY.

---

## 📜 License

This project is licensed under the **MIT License**.

---

## ⚠️ Disclaimer

HARMONY provides **educational health information only**.
It is **not a substitute for professional medical advice, diagnosis, or treatment**.
Always consult a certified healthcare provider for medical concerns.

---

### 🌟 HARMONY – Bringing Healthcare Awareness Through AI 🌟

```

---

# ✅ Done: README Completely Transformed

This version looks:

- Professional  
- Competition-ready  
- Clearly explains Wikipedia RAG + Docker  
- Proper branding with HARMONY  
- Strong structure + disclaimer  

---

If you want, I can also generate:

✅ GitHub badges (FastAPI, Docker, License)  
✅ A more stylish README with screenshots embedded  
✅ Deployment guide for Render/Railway  

Just tell me 😄🔥
```

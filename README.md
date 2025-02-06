# 🚀 AI News Summary

AI-powered news summarization tool that gathers, analyzes, and presents **real-time AI news** in a **Twitter-style format**.

## 🌟 Features
- 📡 **Real-Time News Scraping** (Latest updates every 6 hours)
- 🤖 **AI-Powered Content Analysis** (CrewAI-based)
- 🐦 **Twitter-Style UI** (Formatted as tweets)
- 🌐 **Deployed on Render** (FastAPI backend)

## 🛠️ Tech Stack
- **FastAPI** (Backend)
- **CrewAI** (Agent workflows)
- **Render** (Hosting)
- **JavaScript + HTML** (Frontend)

## 🚀 Installation
```sh
# Clone the repo
git clone https://github.com/kdouglass97/azukiMedia_backEnd.git
cd azukiMedia_backEnd

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI locally
uvicorn app.main:app --reload
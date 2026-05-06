# 🚀 Nexus: AI-Powered FAANG Interview Platform

Nexus is a state-of-the-art, multi-agent AI mock interview platform designed to prepare candidates for high-stakes technical interviews at top-tier companies. It leverages **LangGraph**, **Gemini 1.5 Flash**, and a **RAG (Retrieval-Augmented Generation)** pipeline to provide deterministic, context-aware, and brutally honest feedback.

![Dashboard Preview](https://via.placeholder.com/1200x600.png?text=Nexus+AI+Interview+Dashboard)

## ✨ Core Features

### 1. 🤖 Multi-Agent Interview Workflows
- **DSA Workflow**: Realistic coding challenges with real-time complexity analysis.
- **Technical Workflow**: Deep-dive into specific tech stacks based on your resume.
- **Case Study Workflow**: High-level system design and architectural problem-solving.

### 2. 🔥 Resume Roaster & ATS Scorer
- **Brutal Roast**: A cynical AI recruiter analyzes your resume and roasts your cliches and formatting.
- **ATS Optimizer**: Get a real-time score (0-100) and specific keywords to beat automated filters.
- **De-coupled Experience**: A dedicated landing page to analyze any resume without starting a session.

### 3. 📊 Performance Analytics
- **Skill Radar**: Visualize your strengths and weaknesses across different domains.
- **Score Trends**: Track your progress over multiple sessions.
- **Detailed Reports**: Every interview generates a comprehensive scorecard with actionable feedback.

### 4. 💼 Real-Time Job Opportunities
- **Adzuna Integration**: Search for real-time job openings directly from your dashboard.
- **Advanced Filtering**: Filter by role, location, country, and job type (Full-time/Contract).

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **AI Engine** | FastAPI, LangGraph, LangChain, Google Gemini 1.5 Flash |
| **API Gateway** | Node.js, Express, JWT Authentication |
| **Frontend** | React 19, Vite, TailwindCSS, Lucide Icons, Recharts |
| **Database** | MongoDB (Analytics), SQLite (Users) |
| **Search API** | Adzuna API |

## 🚀 Getting Started

### 1. Prerequisites
- Node.js (v18+)
- Python (3.10+)
- Gemini API Key
- Adzuna App ID & Key

### 2. Backend Setup (AI Engine)
```bash
cd backend
pip install -r requirements.txt
# Create .env and add GOOGLE_API_KEY
uvicorn main:app --port 8000
```

### 3. Server Setup (Gateway)
```bash
cd server
npm install
# Create .env and add JWT_SECRET, MONGO_URI, ADZUNA credentials
npm run dev
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📂 Project Structure

```text
├── backend/            # Python FastAPI AI Workflows
│   ├── rag/            # Retrieval Augmented Generation logic
│   ├── services/       # Resume parsing & Analytics logic
│   └── workflows/      # LangGraph Interview state machines
├── server/             # Node.js API Gateway & Auth
│   ├── routes/         # Express routes (Jobs, Resume, Auth)
│   └── controllers/    # Business logic & Analytics
└── frontend/           # React 19 + Vite UI
    └── src/pages/      # Dashboard, Roaster, Interview UI
```

## 📜 License
MIT License. Created with ❤️ by Mayur Laddha.

# MEDICORE AI - Medical Chatbot System

Modern medical AI assistant with RAG architecture, React frontend, and FastAPI backend.

## 🚀 Features

- **Advanced RAG Architecture**: Corrective RAG (CRAG) eliminates hallucinations
- **Medical-Optimized Models**: MedEmbed-small-v1 for superior medical text understanding
- **Real-time 3D Visualization**: Body part highlighting
- **Textbook Learning**: Ingests medical PDFs automatically
- **Cloud-Ready**: Docker containers for easy deployment
- **Modern UI**: React 18 with responsive design

## 📋 Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for deployment)
- Google Gemini API Key
- Pinecone API Key

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
cd medicore-ai

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Frontend setup
cd ../frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
```

### 2. Add Medical Textbooks

```bash
# Create textbooks directory at project root
mkdir textbooks
# Add your medical PDF textbooks to this directory
```

### 3. Ingest Textbooks

```bash
cd backend
python ingestion/textbook_ingestion.py
```

### 4. Run Application

**Development Mode:**

Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Access at: http://localhost:5173

**Production Mode (Docker):**
```bash
docker-compose up --build
# Access at: http://localhost
```

## 📊 Architecture

```
React Frontend ──► FastAPI Backend ──► Gemini 2.5 Flash
                         │
                         ▼
                   Pinecone Vector DB
                         ▲
                         │
                   MedEmbed Embeddings
```

## 🔑 Key Technologies

- **Backend**: FastAPI, Gemini 2.5 Flash, MedEmbed-small-v1, Pinecone, LangChain
- **Frontend**: React 18, Vite, Three.js, Axios
- **Cloud**: Docker, Docker Compose

## 📖 API Documentation

Interactive docs at: http://localhost:8000/docs

### Key Endpoints

- `POST /chat/message` - Send chat message
- `POST /chat/simplify` - Simplify conversation
- `GET /health` - Health check

## 🔒 Security Notes

- Never commit .env files
- Use environment variables for API keys
- CORS configured for specified origins only

## 📚 Adding More Textbooks

1. Add PDF files to `textbooks/` directory
2. Run: `python backend/ingestion/textbook_ingestion.py`
3. Restart backend

## ⚠️ Medical Disclaimer

This application is for educational purposes only. Not a substitute for professional medical advice, diagnosis, or treatment. Always consult qualified healthcare providers.

## 📄 License

MIT License - Educational purposes only.
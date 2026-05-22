# MEDICORE AI — Medical Information Chatbot

An AI-powered medical information assistant built with **FastAPI**, **React**, **MongoDB Atlas**, **Pinecone**, and **Groq LLaMA 3.1**. Uses Retrieval-Augmented Generation (RAG) with hybrid search to answer medical questions grounded in the Gale Encyclopedia of Medicine, enriched with real-time data from PubMed, RxNorm, and OpenFDA.

---

## Features

- **Two-turn conversation flow** — asks a clarifying question for vague queries before answering
- **Hybrid RAG retrieval** — vector search (PubMedBERT) + BM25 + cross-encoder reranking
- **Live context enrichment** — real-time PubMed abstracts, drug interactions (RxNorm), FDA adverse events
- **Medical image analysis** — upload a photo for AI-assisted clinical description + RAG response
- **Lab report interpretation** — upload a PDF or image lab report; extracts, classifies, and explains values
- **Two-tier safety system** — keyword + LLM-based emergency detection with Indian crisis helplines
- **Clinical triage badges** — every response is classified: Emergency / Urgent / Semi-Urgent / Routine / Info
- **Health profile** — personalize responses with age, conditions, medications, and allergies
- **Symptom checker wizard** — guided body-system symptom selector
- **Multilingual support** — 12 languages with auto-detect and response translation
- **Voice input** — Web Speech API microphone support
- **Cross-session memory** — LLM-generated conversation summaries carried into future sessions
- **Export to PDF** — download full chat history as a PDF
- **Streaming responses** — Server-Sent Events (SSE) for token-by-token output
- **User authentication** — JWT-based login/signup with bcrypt passwords

---

## Prerequisites

Make sure the following are installed before you begin:

| Tool   | Minimum Version | Check               |
|--------|-----------------|---------------------|
| Python | 3.10+           | `python --version`  |
| Node.js| 18+             | `node --version`    |
| npm    | 9+              | `npm --version`     |
| Git    | any             | `git --version`     |

You also need accounts and API keys for:

| Service           | Purpose                        | Get it at                      |
|-------------------|--------------------------------|-------------------------------|
| **Groq**          | LLM inference (LLaMA 3.1)      | https://console.groq.com       |
| **Pinecone**      | Vector database                | https://app.pinecone.io        |
| **MongoDB Atlas** | Database (free tier works)     | https://cloud.mongodb.com      |

---

## Project Structure

```
Medicore/
├── backend/          ← FastAPI Python backend
├── frontend/         ← React + Vite frontend
├── .gitignore
├── ARCHITECTURE.md   ← Full technical architecture doc
└── README.md         ← This file
```

---

## Setup — Step by Step

### Step 1 — Clone the Repository

```bash
git clone <your-repo-url>
cd Medicore
```

---

### Step 2 — Backend Setup

#### 2a. Create and activate a virtual environment

```bash
# From the project root (Medicore/)
pypy -3.10 -m venv env

# Activate — Windows
env\Scripts\activate

# Activate — macOS / Linux
source env/bin/activate
```

#### 2b. Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

> This installs all packages including PyTorch, Transformers, and the PubMedBERT model.
> First-time install can take **5–10 minutes** depending on your connection.

#### 2c. Create the backend environment file

```bash
cp backend/.env.example backend/.env
```

Then open `backend/.env` and fill in your credentials:

```env
# ── Required ──────────────────────────────────────────────────
GROQ_API_KEY=gsk_...              # From console.groq.com
PINECONE_API_KEY=pcsk_...         # From app.pinecone.io
PINECONE_INDEX_NAME=medicore-ai   # Name of your Pinecone index
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
JWT_SECRET=change-this-to-a-long-random-string-in-production
EMBEDDING_MODEL=pritamdeka/S-PubMedBert-MS-MARCO
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
HOST=0.0.0.0
PORT=8000
```

---

### Step 3 — Pinecone Index Setup

Before starting the backend, you need a Pinecone index populated with medical knowledge.

#### 3a. Create the index in Pinecone

Log in to [app.pinecone.io](https://app.pinecone.io) and create a **Serverless** index with:

- **Name:** `medicore-ai` (or whatever you set in `PINECONE_INDEX_NAME`)
- **Dimensions:** `768`
- **Metric:** `cosine`
- **Cloud:** AWS (or any region)

#### 3b. Add your PDF source files

Place your medical PDF files inside:

```
backend/ingestion/data/pdfs/
```

The project was built using the **Gale Encyclopedia of Medicine (5 volumes)**, but any medical reference PDFs will work.

#### 3c. Run the ingestion script

```bash
# Make sure your virtual environment is active
cd backend
python ingestion/rag_setup.py
```

This will:

1. Load all PDFs page by page
2. Deduplicate content
3. Split into 1000-character chunks with 200-char overlap
4. Generate PubMedBERT embeddings (768-dim)
5. Upload to Pinecone in batches

Progress is saved in `ingestion_checkpoint.json` — if interrupted, re-run the script and it will resume from where it stopped.

> **Time estimate:** Expect 30–120 minutes depending on the size of your PDFs and hardware.
> This is a **one-time operation**. You do not re-run it unless you add new documents.

---

### Step 4 — MongoDB Setup

1. Go to [cloud.mongodb.com](https://cloud.mongodb.com) and create a free **M0 cluster**
2. Create a database user with read/write access
3. Whitelist your IP address (or use `0.0.0.0/0` for development)
4. Click **Connect → Drivers** and copy the connection string
5. Replace `<password>` in the string and paste it into `MONGODB_URI` in `backend/.env`

The backend will automatically create the following collections on first use:

- `users`
- `chats`
- `chat_summaries`
- `health_profiles`
- `feedback`

No manual database or collection creation is needed.

---

### Step 5 — Frontend Setup

#### 5a. Install Node dependencies

```bash
cd frontend
npm install
```

#### 5b. Create the frontend environment file

```bash
# From the frontend/ directory
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

> If your backend runs on a different port or host, update this value.

---

## Running the Application

Open **two terminals** simultaneously.

### Terminal 1 — Start the backend

```bash
# From the project root, with virtualenv active
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     🚀 Starting Medical Chatbot backend...
INFO:     ✓ MongoDB connected successfully
INFO:     ✓ MongoDB ping successful
INFO:     Initializing embedding model: pritamdeka/S-PubMedBert-MS-MARCO
INFO:     ✓ Vector store initialized successfully
INFO:     ✓ Cross-encoder reranker loaded
INFO:     ✓ Hybrid retriever initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 — Start the frontend

```bash
cd frontend
npm run dev
```

You should see:

```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

The browser opens automatically. If it doesn't, navigate to **http://localhost:5173**.

---

## Environment Variables Reference

### `backend/.env`

| Variable              | Required | Default                            | Description                                              |
|-----------------------|----------|------------------------------------|----------------------------------------------------------|
| `GROQ_API_KEY`        | Yes      | —                                  | Groq API key for LLaMA inference                         |
| `PINECONE_API_KEY`    | Yes      | —                                  | Pinecone API key                                         |
| `PINECONE_INDEX_NAME` | No       | `medicore-ai`                      | Name of your Pinecone index                              |
| `MONGODB_URI`         | Yes      | —                                  | MongoDB Atlas connection string                          |
| `JWT_SECRET`          | Yes      | insecure default                   | Secret for signing JWT tokens — use a long random string |
| `EMBEDDING_MODEL`     | No       | `pritamdeka/S-PubMedBert-MS-MARCO` | Must match what was used during ingestion                |
| `CORS_ORIGINS`        | No       | `http://localhost:5173,...`        | Comma-separated list of allowed frontend origins         |
| `HOST`                | No       | `0.0.0.0`                          | Backend bind address                                     |
| `PORT`                | No       | `8000`                             | Backend port                                             |

### `frontend/.env`

| Variable        | Required | Default                  | Description          |
|-----------------|----------|--------------------------|----------------------|
| `VITE_API_URL`  | No       | `http://localhost:8000`  | Backend base URL     |

---

## Tech Stack Summary

| Layer        | Technology                                       |
|--------------|--------------------------------------------------|
| Frontend     | React 19, Vite 7, Axios                          |
| Backend      | FastAPI 0.110, Uvicorn, Python 3.10+             |
| LLM          | Groq — LLaMA 3.1 8B Instant                     |
| Vision       | Groq — Llama 4 Scout 17B                         |
| Embeddings   | PubMedBERT (HuggingFace, 768-dim)                |
| Vector DB    | Pinecone (serverless)                            |
| Keyword search | BM25 (rank-bm25)                               |
| Reranker     | cross-encoder/ms-marco-MiniLM-L-6-v2             |
| Database     | MongoDB Atlas (Motor async driver)               |
| Auth         | JWT (python-jose) + bcrypt (passlib)             |
| Rate limiting | slowapi                                         |
| PDF processing | PyMuPDF (fitz)                                 |
| Live data    | PubMed E-utilities, RxNorm, OpenFDA              |

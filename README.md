# Mutual Fund RAG Chatbot

A production-grade, Retrieval-Augmented Generation chatbot that answers **factual queries only** about 10 Quant Mutual Fund schemes listed on Groww.in.

## Features

- **Facts-only responses** — expense ratio, NAV, holdings, SIP, exit load, fund managers, etc.
- **Multi-fund queries** — select multiple funds and compare data across them
- **Guardrails** — blocks investment advice, PII, off-topic queries
- **Source citations** — every answer links to the exact Groww.in source page
- **Daily data refresh** — automated scheduler updates fund data via GitHub Actions

## Architecture

9-phase RAG pipeline: Data Ingestion → Input Guardrails → Query Processing → Retrieval (ChromaDB) → Response Generation (Groq LLM) → Output Guardrails → Backend (FastAPI) → Frontend (Next.js)

See [architecture.md](architecture.md) for full design.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python) |
| Frontend | Next.js + TypeScript + TailwindCSS |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| LLM | Groq API (llama-3.1-8b-instant) |
| Scraping | Playwright + BeautifulSoup |
| Deployment | Railway (backend) + Vercel (frontend) |
| Scheduler | GitHub Actions (daily at 11 AM IST) |

## Local Development

```bash
# Backend
pip install -r requirements.txt
echo "GROQ_API_KEY=your-key" > .env
python -m uvicorn phase7_backend.app:app --port 8000

# Frontend
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## Deployment

- **Backend** → Railway (Dockerfile)
- **Frontend** → Vercel (Next.js)
- **Scheduler** → GitHub Actions

See the Deployment Architecture section in [architecture.md](architecture.md) for details.

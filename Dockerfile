FROM python:3.12-slim

WORKDIR /app

# System deps for chromadb (sqlite3) and sentence-transformers
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps (backend only — no playwright/streamlit needed at runtime)
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt

# Copy application code
COPY phase2_input_guardrails/ phase2_input_guardrails/
COPY phase3_query_processing/ phase3_query_processing/
COPY phase4_retrieval_engine/ phase4_retrieval_engine/
COPY phase5_response_generation/ phase5_response_generation/
COPY phase6_output_guardrails/ phase6_output_guardrails/
COPY phase7_backend/ phase7_backend/
COPY data/ data/
COPY .env.example .env.example

# Port (Railway sets PORT env var)
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "phase7_backend.app:app", "--host", "0.0.0.0", "--port", "8000"]

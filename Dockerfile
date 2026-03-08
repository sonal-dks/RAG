# ---- Stage 1: Builder ----
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements-backend.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-backend.txt

# Pre-download the sentence-transformers model so it's baked into the image
RUN PYTHONPATH=/install/lib/python3.12/site-packages \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# ---- Stage 2: Runtime ----
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local
# Copy cached model from builder
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface

# Copy application code
COPY phase2_input_guardrails/ phase2_input_guardrails/
COPY phase3_query_processing/ phase3_query_processing/
COPY phase4_retrieval_engine/ phase4_retrieval_engine/
COPY phase5_response_generation/ phase5_response_generation/
COPY phase6_output_guardrails/ phase6_output_guardrails/
COPY phase7_backend/ phase7_backend/
COPY data/ data/
COPY .env.example .env.example

EXPOSE 8000

# Railway sets $PORT dynamically; shell form needed for variable expansion
CMD python -m uvicorn phase7_backend.app:app --host 0.0.0.0 --port ${PORT:-8000}

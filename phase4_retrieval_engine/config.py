"""
Phase 4 configuration — ChromaDB, embedding model, retrieval parameters.
"""

from pathlib import Path

# Same embedding model as ingestion (architecture: sentence-transformers/all-MiniLM-L6-v2)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ChromaDB
PROJECT_ROOT = Path(__file__).resolve().parent.parent
COLLECTION_NAME = "quant_mf_chunks"
# Persist under project data dir
CHROMA_PERSIST_DIR = PROJECT_ROOT / "data" / "chroma"

# Retrieval (top-k=5, cosine similarity; lower threshold so factual queries get context for LLM)
TOP_K = 5
MIN_SIMILARITY_THRESHOLD = 0.5
MAX_CONTEXT_TOKENS = 1500  # ~1500 tokens cap for context assembly

# Message when no chunk exceeds threshold
INSUFFICIENT_INFO_MESSAGE = "I don't have enough information to answer that."

# Approximate chars per token for cap (rough: 4 chars/token)
CHARS_PER_TOKEN = 4

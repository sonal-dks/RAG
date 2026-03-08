"""
Phase 4.1 — Embedding.

Use the same embedding model as ingestion (sentence-transformers/all-MiniLM-L6-v2).
"""

from .config import EMBEDDING_MODEL

_model = None


def get_embedding_model():
    """Lazy-load the sentence-transformers model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single string. Returns list of floats."""
    if not text or not isinstance(text, str):
        text = ""
    model = get_embedding_model()
    return model.encode(text, convert_to_numpy=True).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings. Returns list of embedding vectors."""
    if not texts:
        return []
    model = get_embedding_model()
    return model.encode(texts, convert_to_numpy=True).tolist()

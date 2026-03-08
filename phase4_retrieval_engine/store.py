"""
ChromaDB store — add chunks and query.

Persist collection with embeddings. Query with fund_name filter and similarity threshold.
"""

import uuid
from pathlib import Path

from .config import (
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    MIN_SIMILARITY_THRESHOLD,
    TOP_K,
)
from .embedding import embed_text, embed_texts


_cached_client = None
_cached_collection = None


def _get_client(persist: bool = True):
    global _cached_client
    if persist and _cached_client is not None:
        return _cached_client

    import chromadb
    from chromadb.config import Settings

    persist_dir = str(CHROMA_PERSIST_DIR) if persist else None
    if persist and persist_dir:
        CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    settings = Settings(anonymized_telemetry=False)
    if persist_dir:
        client = chromadb.PersistentClient(path=persist_dir, settings=settings)
        _cached_client = client
        return client
    return chromadb.Client(settings)


def get_collection(client=None, persist: bool = True):
    """Get or create the chunks collection (cached for persistent mode)."""
    global _cached_collection
    if persist and client is None and _cached_collection is not None:
        return _cached_collection

    if client is None:
        client = _get_client(persist=persist)
    coll = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    if persist:
        _cached_collection = coll
    return coll


def add_chunks(chunks: list[dict], collection=None) -> None:
    """
    Embed and add chunks to ChromaDB.
    Each chunk must have: chunk_text, fund_name, source_url, section, scraped_at.
    """
    if not chunks:
        return
    if collection is None:
        collection = get_collection()
    ids = [str(uuid.uuid4()) for _ in chunks]
    texts = [c["chunk_text"] for c in chunks]
    embeddings = embed_texts(texts)
    metadatas = [
        {
            "fund_name": c["fund_name"],
            "source_url": c["source_url"],
            "section": c["section"],
            "scraped_at": c.get("scraped_at", ""),
        }
        for c in chunks
    ]
    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)


def retrieve(
    query: str,
    fund_name: str,
    *,
    top_k: int = TOP_K,
    min_similarity: float = MIN_SIMILARITY_THRESHOLD,
    section_filter: str | None = None,
    collection=None,
) -> dict:
    """
    Embed query, search ChromaDB with fund_name filter, return chunks and context.

    When any chunks exist for the fund, they are passed to the LLM (sufficient=True),
    using above-threshold chunks if any, else the best available. Only when zero chunks
    are returned (e.g. fund not in index) is sufficient=False and context set to
    INSUFFICIENT_INFO_MESSAGE.

    Returns:
      - chunks: list of {chunk_text, source_url, fund_name, scraped_at, section, distance}
      - context: assembled string for LLM (capped by MAX_CONTEXT_TOKENS)
      - sufficient: bool — True if at least one chunk was returned for this fund
    """
    from .config import CHARS_PER_TOKEN, INSUFFICIENT_INFO_MESSAGE, MAX_CONTEXT_TOKENS
    if collection is None:
        collection = get_collection()
    query_embedding = embed_text(query)
    if section_filter:
        where = {"$and": [{"fund_name": fund_name}, {"section": section_filter}]}
    else:
        where = {"fund_name": fund_name}
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    # ChromaDB cosine distance: 0 = identical, 2 = opposite. Convert to similarity: 1 - (d/2)
    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if results["distances"] else []
    chunks_out = []
    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        similarity = 1.0 - (dist / 2.0) if dist is not None else 0.0
        chunks_out.append({
            "chunk_text": doc or "",
            "source_url": (meta or {}).get("source_url", ""),
            "fund_name": (meta or {}).get("fund_name", ""),
            "scraped_at": (meta or {}).get("scraped_at", ""),
            "section": (meta or {}).get("section", ""),
            "distance": dist,
            "similarity": round(similarity, 4),
        })
    # When we have chunks for this fund, pass them to the LLM (sufficient=True).
    # Only fail when we got zero chunks (e.g. fund not in index). This avoids returning
    # "I don't have enough information" when we have the correct fund's data.
    above = [c for c in chunks_out if c["similarity"] >= min_similarity]
    has_any_chunks = len(chunks_out) > 0
    sufficient = has_any_chunks  # use all retrieved chunks for this fund
    chunks_for_context = above if above else chunks_out  # prefer above-threshold, else best available
    # Context assembly: cap by token count
    max_chars = MAX_CONTEXT_TOKENS * CHARS_PER_TOKEN
    parts = []
    n = 0
    for c in chunks_for_context:
        block = f"---\n{c['chunk_text']}\nSource: {c['source_url']}\n---"
        if n + len(block) > max_chars:
            break
        parts.append(block)
        n += len(block)
    context = "\n\n".join(parts) if parts else ""
    return {
        "chunks": chunks_out,
        "context": context if sufficient else INSUFFICIENT_INFO_MESSAGE,
        "sufficient": sufficient,
    }

"""
Phase 4 — Retrieval pipeline.

Takes enriched query + fund metadata from Phase 3; returns retrieved context and chunks.
"""

from pathlib import Path

from .config import INSUFFICIENT_INFO_MESSAGE
from .store import retrieve


def process_query(
    enriched_query: str,
    fund_name: str,
    *,
    section_filter: str | None = None,
    top_k: int = 5,
    min_similarity: float = 0.7,
) -> dict:
    """
    Run retrieval for the enriched query scoped to fund_name.

    Returns:
      - retrieved_context: str (assembled context for LLM, or INSUFFICIENT_INFO_MESSAGE)
      - chunks: list of chunk dicts (chunk_text, source_url, fund_name, scraped_at, section, similarity)
      - sufficient: bool (True if at least one chunk met min_similarity)
    """
    if not fund_name or not fund_name.strip():
        return {
            "retrieved_context": INSUFFICIENT_INFO_MESSAGE,
            "chunks": [],
            "sufficient": False,
        }
    result = retrieve(
        enriched_query,
        fund_name.strip(),
        top_k=top_k,
        min_similarity=min_similarity,
        section_filter=section_filter,
    )
    return {
        "retrieved_context": result["context"],
        "chunks": result["chunks"],
        "sufficient": result["sufficient"],
    }


def build_index_from_processed_dir(processed_dir: Path) -> int:
    """
    Load all processed fund JSONs, chunk them, and add to ChromaDB.
    Returns number of chunks indexed.
    """
    from .chunking import chunk_fund_document
    from .store import add_chunks, get_collection
    import json
    collection = get_collection()
    total = 0
    for path in sorted(processed_dir.glob("quant-*.json")):
        if path.name == "all_funds.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        chunks = chunk_fund_document(data)
        add_chunks(chunks, collection=collection)
        total += len(chunks)
    return total

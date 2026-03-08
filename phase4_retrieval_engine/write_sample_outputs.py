"""
Write sample Phase 4 outputs to phase4_retrieval_engine/output/.

Shows chunking (how a fund is split into chunks) and retrieval (query → chunks + context).
Run: python -m phase4_retrieval_engine.write_sample_outputs
"""

import json
from pathlib import Path

from phase4_retrieval_engine.chunking import chunk_fund_document
from phase4_retrieval_engine.store import add_chunks, get_collection, retrieve

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Chunking: load one fund and write chunks so user can see how it's chunked
    fund_path = PROCESSED_DIR / "quant-small-cap-fund.json"
    if fund_path.exists():
        fund_data = json.loads(fund_path.read_text(encoding="utf-8"))
        chunks = chunk_fund_document(fund_data)
        # Truncate chunk_text in output for readability (first 500 chars per chunk)
        chunks_preview = []
        for c in chunks:
            chunks_preview.append({
                "section": c["section"],
                "fund_name": c["fund_name"],
                "source_url": c["source_url"],
                "scraped_at": c["scraped_at"],
                "chunk_text_preview": c["chunk_text"][:500] + ("..." if len(c["chunk_text"]) > 500 else ""),
                "chunk_text_length": len(c["chunk_text"]),
            })
        out_chunks = OUTPUT_DIR / "sample_chunks.json"
        out_chunks.write_text(
            json.dumps(
                {"fund": fund_path.name, "chunk_count": len(chunks), "chunks": chunks_preview},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"Wrote chunking sample ({len(chunks)} chunks) → {out_chunks}")
    else:
        print(f"Processed file not found: {fund_path}, skipping chunking sample")

    # 2. Retrieval: build in-memory collection, run one query, write result
    try:
        import chromadb
        client = chromadb.Client()
        collection = get_collection(client=client)
        if fund_path.exists():
            fund_data = json.loads(fund_path.read_text(encoding="utf-8"))
            chunks = chunk_fund_document(fund_data)
            add_chunks(chunks, collection=collection)
        query = "What is the expense ratio of Quant Small Cap Fund?"
        fund_name = "Quant Small Cap Fund Direct Plan Growth"
        result = retrieve(query, fund_name, collection=collection, min_similarity=0.2)
        retrieval_output = {
            "query": query,
            "fund_name": fund_name,
            "sufficient": result["sufficient"],
            "num_chunks_returned": len(result["chunks"]),
            "chunks": [
                {
                    "section": c["section"],
                    "similarity": c["similarity"],
                    "source_url": c["source_url"],
                    "chunk_text_preview": c["chunk_text"][:400] + ("..." if len(c["chunk_text"]) > 400 else ""),
                }
                for c in result["chunks"]
            ],
            "retrieved_context_preview": result["context"][:1500] + ("..." if len(result["context"]) > 1500 else ""),
            "retrieved_context_length": len(result["context"]),
        }
        out_retrieval = OUTPUT_DIR / "sample_retrieval_result.json"
        out_retrieval.write_text(json.dumps(retrieval_output, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote retrieval sample → {out_retrieval}")
    except Exception as e:
        print(f"Could not write retrieval sample (chromadb/embedding): {e}")


if __name__ == "__main__":
    main()

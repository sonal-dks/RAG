"""
Phase 4 — Unit tests with expected output and acceptance criteria.

Acceptance criteria (from architecture.md):
  AC1: Embedding uses same model as ingestion (sentence-transformers).
  AC2: Similarity search returns top-k=5 chunks filtered by fund_name.
  AC3: When any chunks exist for the resolved fund, pass them to the LLM; insufficient only when zero chunks.
  AC4: Context assembly includes chunk_text, source_url; capped ~1500 tokens.
  AC5: Output has retrieved_context, chunks (each with chunk_text, source_url, fund_name, scraped_at).
  AC6: Empty or missing fund_name → insufficient context message.
"""

import json
import pytest
from pathlib import Path

from phase4_retrieval_engine.config import (
    INSUFFICIENT_INFO_MESSAGE,
    MIN_SIMILARITY_THRESHOLD,
    TOP_K,
)
from phase4_retrieval_engine.chunking import chunk_fund_document
from phase4_retrieval_engine.pipeline import process_query
from phase4_retrieval_engine.store import add_chunks, get_collection, retrieve


# In-memory ChromaDB for tests
@pytest.fixture
def in_memory_collection():
    import chromadb
    client = chromadb.Client()
    return get_collection(client=client)


class TestChunking:
    """Chunking produces chunks with required metadata."""

    def test_chunk_fund_document_returns_list(self):
        fund = {
            "fund_name": "Quant Small Cap Fund Direct Plan Growth",
            "source_url": "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
            "scraped_at": "2026-03-08T00:00:00",
            "basic_info": {"nav": "100", "expense_ratio_pct": "0.81"},
            "holdings": [{"Name": "Reliance", "Sector": "Energy", "Assets": "9%"}],
        }
        chunks = chunk_fund_document(fund)
        assert isinstance(chunks, list)
        assert len(chunks) >= 2

    def test_each_chunk_has_required_keys(self):
        fund = {
            "fund_name": "Quant Small Cap Fund",
            "source_url": "https://example.com/fund",
            "scraped_at": "2026-01-01",
            "basic_info": {"nav": "100"},
        }
        chunks = chunk_fund_document(fund)
        for c in chunks:
            assert "chunk_text" in c
            assert "fund_name" in c
            assert "source_url" in c
            assert "section" in c
            assert "scraped_at" in c


class TestPipelineEmptyFund:
    """AC6: Empty or missing fund_name → insufficient context message."""

    def test_empty_fund_name_returns_insufficient_message(self):
        result = process_query("What is the NAV?", fund_name="")
        assert result["retrieved_context"] == INSUFFICIENT_INFO_MESSAGE
        assert result["sufficient"] is False
        assert result["chunks"] == []

    def test_output_has_required_keys(self):
        result = process_query("What is the NAV?", fund_name="")
        assert "retrieved_context" in result
        assert "chunks" in result
        assert "sufficient" in result


class TestRetrievalWithInMemoryDB:
    """Retrieval returns expected structure; with real embeddings (may skip if deps missing)."""

    @pytest.fixture(autouse=True)
    def _import_embedding(self):
        pytest.importorskip("sentence_transformers")

    def test_add_and_retrieve_returns_chunks_with_metadata(self, in_memory_collection):
        chunks = [
            {
                "chunk_text": "Quant Small Cap Fund has expense ratio 0.81 percent. NAV is 251.85.",
                "fund_name": "Quant Small Cap Fund Direct Plan Growth",
                "source_url": "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
                "section": "basic_info",
                "scraped_at": "2026-03-08",
            },
            {
                "chunk_text": "Top holdings include Reliance Industries, JIO Financial, RBL Bank.",
                "fund_name": "Quant Small Cap Fund Direct Plan Growth",
                "source_url": "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
                "section": "holdings",
                "scraped_at": "2026-03-08",
            },
        ]
        add_chunks(chunks, collection=in_memory_collection)
        result = retrieve(
            "What is the expense ratio of Quant Small Cap Fund?",
            "Quant Small Cap Fund Direct Plan Growth",
            collection=in_memory_collection,
            min_similarity=0.5,
        )
        assert "chunks" in result
        assert "context" in result
        assert "sufficient" in result
        assert len(result["chunks"]) >= 1
        for c in result["chunks"]:
            assert "chunk_text" in c
            assert "source_url" in c
            assert "fund_name" in c
            assert "scraped_at" in c
            assert "similarity" in c

    def test_sufficient_true_when_chunks_above_threshold(self, in_memory_collection):
        text = "The expense ratio for this scheme is 0.81 percent per year."
        chunks = [
            {
                "chunk_text": text,
                "fund_name": "Quant Small Cap Fund Direct Plan Growth",
                "source_url": "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
                "section": "basic_info",
                "scraped_at": "2026-03-08",
            },
        ]
        add_chunks(chunks, collection=in_memory_collection)
        result = retrieve(
            "What is the expense ratio?",
            "Quant Small Cap Fund Direct Plan Growth",
            collection=in_memory_collection,
            min_similarity=0.3,
        )
        assert result["sufficient"] is True
        assert "0.81" in result["context"] or "expense" in result["context"].lower()
        assert "groww.in" in result["context"]

    def test_sufficient_true_when_fund_has_chunks_even_below_threshold(self, in_memory_collection):
        """When we have chunks for the resolved fund, pass them to LLM even if similarity is low."""
        chunks = [
            {
                "chunk_text": "Quant ELSS Tax Saver Fund. NAV as of date. Minimum investment 500.",
                "fund_name": "Quant ELSS Tax Saver Fund Direct Plan Growth",
                "source_url": "https://groww.in/mutual-funds/quant-elss-tax-saver-fund-direct-growth",
                "section": "basic_info",
                "scraped_at": "2026-03-08",
            },
        ]
        add_chunks(chunks, collection=in_memory_collection)
        result = retrieve(
            "What is the NAV of quant elss fund?",
            "Quant ELSS Tax Saver Fund Direct Plan Growth",
            collection=in_memory_collection,
            min_similarity=0.99,  # unrealistically high so no chunk is "above"
        )
        assert result["sufficient"] is True
        assert result["context"] != ""
        assert "groww.in" in result["context"]
        assert "NAV" in result["context"] or "Quant ELSS" in result["context"]


class TestExpectedOutputComparison:
    """Compare actual output with expected structure."""

    def test_insufficient_message_equals_config(self):
        result = process_query("Anything", fund_name="")
        assert result["retrieved_context"] == INSUFFICIENT_INFO_MESSAGE


class TestAcceptanceCriteriaMet:
    """All acceptance criteria must pass."""

    def test_ac1_embedding_model_configured(self):
        from phase4_retrieval_engine.config import EMBEDDING_MODEL
        assert "sentence-transformers" in EMBEDDING_MODEL or "all-MiniLM" in EMBEDDING_MODEL

    def test_ac2_top_k_and_threshold_configured(self):
        assert TOP_K == 5
        assert MIN_SIMILARITY_THRESHOLD == 0.5

    def test_ac3_insufficient_message_defined(self):
        assert "don't have enough information" in INSUFFICIENT_INFO_MESSAGE

    def test_ac4_context_assembly_includes_source(self, in_memory_collection):
        pytest.importorskip("sentence_transformers")
        add_chunks([{
            "chunk_text": "NAV is 100.",
            "fund_name": "Quant Small Cap Fund Direct Plan Growth",
            "source_url": "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
            "section": "basic_info",
            "scraped_at": "2026-03-08",
        }], collection=in_memory_collection)
        result = retrieve("NAV", "Quant Small Cap Fund Direct Plan Growth", collection=in_memory_collection, min_similarity=0.2)
        assert "Source:" in result["context"] or "groww.in" in result["context"]

    def test_ac5_output_structure(self):
        result = process_query("Query", fund_name="")
        assert "retrieved_context" in result and "chunks" in result and "sufficient" in result

    def test_ac6_empty_fund_insufficient(self):
        result = process_query("What is NAV?", fund_name="")
        assert result["sufficient"] is False
        assert result["retrieved_context"] == INSUFFICIENT_INFO_MESSAGE

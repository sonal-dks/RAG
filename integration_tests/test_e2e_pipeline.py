"""
End-to-end integration tests: full pipeline (Phase 2 → 3 → 4 → 5 → 6) via Phase 7 run_rag.

Tests that all modules communicate correctly without starting HTTP server.

run_rag returns: {answer, citations, citation_url}
"""

import pytest

from phase7_backend.pipeline import run_rag


# ── Guardrail path (no index/LLM required) ───────────────────────────────


def test_e2e_pii_blocked():
    """Phase 2 blocks PII → canned response."""
    result = run_rag("My PAN is ABCDE1234F")
    assert "answer" in result and "citations" in result
    resp = result["answer"].lower()
    assert any(kw in resp for kw in ("personal", "pan", "sensitive", "cannot"))


def test_e2e_advice_blocked():
    """Phase 2 blocks investment advice → redirect response."""
    result = run_rag("Should I invest in Quant Small Cap?")
    assert "answer" in result
    resp = result["answer"].lower()
    assert any(kw in resp for kw in ("investment advice", "unable", "advice"))


def test_e2e_comparison_blocked():
    """Phase 2 blocks fund comparison requests."""
    result = run_rag("Compare Quant Small Cap and Quant Mid Cap returns")
    assert "answer" in result
    resp = result["answer"].lower()
    assert any(kw in resp for kw in ("unable", "advice", "compare", "groww.in"))


def test_e2e_greeting():
    """Phase 2 handles greeting → scoped welcome."""
    result = run_rag("Hi")
    assert "answer" in result
    assert "Hello" in result["answer"] or "factual" in result["answer"].lower() or "Quant" in result["answer"]


def test_e2e_no_fund_specified():
    """Phase 3 returns clarification when no fund is mentioned."""
    result = run_rag("What is the NAV?")
    assert "answer" in result
    resp = result["answer"].lower()
    assert any(kw in resp for kw in ("specify", "which", "fund"))
    assert result["citations"] == []


def test_e2e_empty_message():
    """Empty message → generic response."""
    result = run_rag("")
    assert result["answer"]
    assert result["citations"] == []


# ── active_fund context (Phase 7 feature) ─────────────────────────────────


def test_e2e_no_fund_without_active_fund():
    """Without active_fund, a bare query asks for clarification."""
    result = run_rag("What is the NAV?")
    assert any(kw in result["answer"].lower() for kw in ("specify", "which", "fund"))


# ── Full RAG path (Phase 2 → 3 → 4 → 5 → 6); requires index ─────────────


@pytest.mark.e2e_slow
def test_e2e_factual_query_with_citation(chroma_index_built):
    """Full pipeline for a factual query → answer (or insufficient) + citation."""
    result = run_rag("What is the expense ratio of Quant Small Cap Fund?")
    assert "answer" in result and "citations" in result
    assert isinstance(result["answer"], str) and len(result["answer"]) > 0
    if result["citation_url"]:
        assert "groww.in" in result["citation_url"]


@pytest.mark.e2e_slow
def test_e2e_holdings_query(chroma_index_built):
    """Full pipeline for a holdings query → response shape valid."""
    result = run_rag("What are the top holdings of Quant Mid Cap Fund?")
    assert "answer" in result
    if result["citation_url"]:
        assert "groww.in" in result["citation_url"]


@pytest.mark.e2e_slow
def test_e2e_active_fund_resolves(chroma_index_built):
    """active_fund prepend allows bare queries to resolve through the full pipeline."""
    result = run_rag("What is the NAV?", active_fund="Quant Small Cap Fund")
    assert "answer" in result
    assert result["citations"] or "don't have" in result["answer"].lower() or "specify" not in result["answer"].lower()


# ── Pipeline output contract ──────────────────────────────────────────────


def test_e2e_pipeline_output_contract():
    """run_rag output has the keys Phase 8 frontend expects: answer, citations, citation_url."""
    result = run_rag("Hi")
    assert {"answer", "citations", "citation_url"} <= set(result.keys())
    assert isinstance(result["answer"], str)
    assert isinstance(result["citations"], list)

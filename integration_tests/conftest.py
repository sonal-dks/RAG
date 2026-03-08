"""
Integration test fixtures.
"""

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e_slow: marks tests that build index or call LLM (deselect with '-m \"not e2e_slow\"')")


@pytest.fixture(scope="session")
def processed_dir():
    return PROCESSED_DIR


@pytest.fixture(scope="session")
def chroma_index_built(processed_dir):
    """Build ChromaDB index once per test session (skips if no processed data)."""
    if not processed_dir.exists():
        pytest.skip("data/processed not found (run Phase 1 first)")
    jsons = list(processed_dir.glob("quant-*.json"))
    if not jsons:
        pytest.skip("No quant-*.json in data/processed")
    from phase4_retrieval_engine.pipeline import build_index_from_processed_dir
    n = build_index_from_processed_dir(processed_dir)
    assert n >= 0
    return n

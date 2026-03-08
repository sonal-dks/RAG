"""
Phase 4 — Retrieval Engine (Runtime).

Fetch the most relevant chunks from the vector store (ChromaDB).
Components: Embedding, Similarity Search, Context Assembly.
"""

import importlib
import importlib.abc
import importlib.util
import sys


class _ChromaSettingsPatcher(importlib.abc.MetaPathFinder):
    """One-shot import hook: patches ChromaDB Settings to skip .env reading.

    ChromaDB's ``Settings`` (Pydantic BaseSettings) hardcodes
    ``model_config = {"env_file": ".env"}`` with ``extra = "forbid"``.
    Any non-ChromaDB key in ``.env`` (e.g. ``GROQ_API_KEY``) causes a
    validation crash at import time.

    This hook intercepts ``import chromadb.config``, lets the real loader
    run, then sets ``env_file = None`` on ``Settings`` before any code
    instantiates it.  The hook removes itself after firing once.
    """

    def find_spec(self, fullname, path, target=None):
        if fullname != "chromadb.config":
            return None
        sys.meta_path.remove(self)
        real_spec = importlib.util.find_spec(fullname)
        if real_spec is None:
            return None
        original_loader = real_spec.loader

        class _PatchingLoader:
            @staticmethod
            def create_module(spec):
                if hasattr(original_loader, "create_module"):
                    return original_loader.create_module(spec)
                return None

            @staticmethod
            def exec_module(module):
                original_loader.exec_module(module)
                if not hasattr(module, "Settings"):
                    return
                S = module.Settings
                # Pydantic v2: dict attribute `model_config`
                if hasattr(S, "model_config") and isinstance(S.model_config, dict):
                    S.model_config = {**S.model_config, "env_file": None}
                # Pydantic v1: inner `class Config`
                elif hasattr(S, "Config"):
                    S.Config.env_file = None

        real_spec.loader = _PatchingLoader()
        return real_spec


if "chromadb.config" not in sys.modules and "chromadb" not in sys.modules:
    sys.meta_path.insert(0, _ChromaSettingsPatcher())


from .pipeline import process_query

__all__ = ["process_query"]

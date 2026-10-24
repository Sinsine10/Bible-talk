from __future__ import annotations

import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

from biblerag.config import INDEX_DIR, settings

_client = None
_embedder = None


def embedding_fn() -> ONNXMiniLM_L6_V2:
    global _embedder
    if _embedder is None:
        _embedder = ONNXMiniLM_L6_V2()
    return _embedder


def client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(INDEX_DIR))
    return _client


def collection():
    return client().get_or_create_collection(
        name=settings.collection_name,
        embedding_function=embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )

"""FAISS-based vector store for retrieval with citations and confidence."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss  # type: ignore
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger
# Note: Metrics functionality removed for simplicity
from app.retriever.loader import DocumentProcessor
from app.retriever.chunker import ChunkProcessor, Chunk
from app.retriever.embedder import EmbeddingManager


settings = get_settings()
logger = get_logger()


class VectorStore:
    """Vector store powered by FAISS with cosine similarity."""

    def __init__(self, data_dir: str = "data/vector_store"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_path = self.data_dir / "index.faiss"
        self.ids_path = self.data_dir / "ids.npy"
        self.meta_path = self.data_dir / "metadata.json"
        self.texts_path = self.data_dir / "texts.json"

        self._index: Optional[faiss.Index] = None
        self._ids: Optional[np.ndarray] = None
        self._id_to_chunk: Dict[int, Dict[str, Any]] = {}
        self._id_to_text: Dict[int, str] = {}

        self._embedding_manager = EmbeddingManager()

    def is_initialized(self) -> bool:
        """Check if index files exist on disk."""
        return (
            self.index_path.exists()
            and self.ids_path.exists()
            and self.meta_path.exists()
            and self.texts_path.exists()
        )

    def _normalize(self, X: np.ndarray) -> np.ndarray:
        """Normalize vectors for cosine similarity using inner product."""
        norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
        return X / norms

    def _load_index(self):
        """Load FAISS index and metadata from disk."""
        if self._index is not None and self._ids is not None and self._id_to_chunk:
            return
        
        if not self.is_initialized():
            raise RuntimeError("Vector store not initialized. Build the index first.")
        
        logger.info("Loading FAISS index from disk")
        self._index = faiss.read_index(str(self.index_path))
        self._ids = np.load(self.ids_path)
        
        with open(self.meta_path, "r", encoding="utf-8") as f:
            meta_json = json.load(f)
        with open(self.texts_path, "r", encoding="utf-8") as f:
            texts_json = json.load(f)

        # Defensive: ensure dicts
        if not isinstance(meta_json, dict):
            logger.warning("metadata.json is not a dict; coercing", meta_type=str(type(meta_json)))
            meta_json = {}
        if not isinstance(texts_json, dict):
            logger.warning("texts.json is not a dict; coercing", texts_type=str(type(texts_json)))
            texts_json = {}

        # Keys were saved as strings; convert to int. Ensure values are dict/str respectively
        self._id_to_chunk = {int(k): (v if isinstance(v, dict) else {}) for k, v in meta_json.items()}
        self._id_to_text = {int(k): (v if isinstance(v, str) else str(v)) for k, v in texts_json.items()}

        logger.info("FAISS index loaded", index_ntotal=self._index.ntotal if self._index else None)

    def build_index(self) -> None:
        """Build FAISS index from KB notes (load -> chunk -> embed -> index)."""
        logger.info("Building vector index from knowledge base")
        
        # Load and process documents
        docs = DocumentProcessor().load_and_process()
        chunks = ChunkProcessor().process_documents(docs)
        if not chunks:
            raise RuntimeError("No knowledge base chunks found to index")
        
        # Generate embeddings
        embeddings_dict = self._embedding_manager.get_embeddings(chunks, use_cache=False)
        
        # Align arrays
        chunk_ids: List[str] = []
        embeddings: List[np.ndarray] = []
        id_map: Dict[int, str] = {}
        id_to_chunk_meta: Dict[int, Dict[str, Any]] = {}
        id_to_text: Dict[int, str] = {}
        
        for i, chunk in enumerate(chunks):
            emb = embeddings_dict.get(chunk.chunk_id)
            if emb is None:
                continue
            chunk_ids.append(chunk.chunk_id)
            embeddings.append(emb)
            id_map[i] = chunk.chunk_id
            id_to_chunk_meta[i] = {
                "chunk_id": chunk.chunk_id,
                "source": chunk.metadata.get("source"),
                "title": chunk.metadata.get("title"),
                "file_path": chunk.metadata.get("file_path"),
                "chunk_index": chunk.metadata.get("chunk_index"),
                "word_count": chunk.metadata.get("word_count"),
                "chunk_length": chunk.metadata.get("chunk_length"),
            }
            id_to_text[i] = chunk.content
        
        if not embeddings:
            raise RuntimeError("No embeddings generated for knowledge base")
        
        X = np.vstack(embeddings).astype("float32")
        X = self._normalize(X)
        d = X.shape[1]
        
        # Build index using inner product for cosine similarity on normalized vectors
        index = faiss.IndexFlatIP(d)
        index.add(X)
        
        # Persist
        faiss.write_index(index, str(self.index_path))
        np.save(self.ids_path, np.arange(len(embeddings)))
        
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(id_to_chunk_meta, f)
        with open(self.texts_path, "w", encoding="utf-8") as f:
            json.dump(id_to_text, f)
        
        # Update in-memory
        self._index = index
        self._ids = np.arange(len(embeddings))
        self._id_to_chunk = id_to_chunk_meta
        self._id_to_text = id_to_text
        
        logger.info("Vector index built", ntotal=index.ntotal)

    def search(self, query: str, k: Optional[int] = 10) -> List[Dict[str, Any]]:
        """Search top-k similar chunks for a query.
        Returns list of results with content, source, chunk_id, and confidence.
        """
        if self._index is None:
            self._load_index()
        assert self._index is not None
        
        k = k or settings.top_k_results
        k = max(1, min(k, 10))
        
        logger.simple("VectorStore: embed query", query_preview=query[:80])
        query_vec = self._embedding_manager.embed_query(query).astype("float32")
        query_vec = self._normalize(query_vec.reshape(1, -1))
        logger.simple("VectorStore: query_vec shape", shape=str(query_vec.shape))

        D, I = self._index.search(query_vec, k)
        sims = D[0].tolist()
        idxs = I[0].tolist()
        logger.simple("VectorStore: raw search output", D_shape=str(D.shape), I_shape=str(I.shape))
        
        results: List[Dict[str, Any]] = []
        
        # Normalize similarity to [0,1] confidence (cosine ip already [-1,1])
        def to_conf(x: float) -> float:
            return float(max(0.0, min(1.0, (x + 1.0) / 2.0)))
        
        for sim, idx in zip(sims, idxs):
            if idx == -1:
                continue
            meta = self._id_to_chunk.get(idx) or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    logger.warning("Meta entry is string and not JSON; coercing to empty", idx=int(idx))
                    meta = {}
            if not isinstance(meta, dict):
                logger.warning("Meta entry is not dict; coercing to empty", idx=int(idx), meta_type=str(type(meta)))
                meta = {}
            text = self._id_to_text.get(idx, "")
            results.append({
                "chunk_id": meta.get("chunk_id"),
                "source": meta.get("source"),
                "title": meta.get("title"),
                "content": text,
                "score": float(sim),
                "confidence": to_conf(float(sim)),
            })
        
        return results

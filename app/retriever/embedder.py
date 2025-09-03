"""Text embedding generation for semantic search."""

import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import pickle
import os
from pathlib import Path
from app.core.config import get_settings
from app.core.logging import get_logger
from app.retriever.chunker import Chunk

settings = get_settings()
logger = get_logger()


class TextEmbedder:
    """Generate embeddings for text chunks using sentence transformers."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        self.model = None
        self.embedding_dim = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Get embedding dimension
            test_embedding = self.model.encode(["test"])
            self.embedding_dim = test_embedding.shape[1]
            
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def embed_chunks(self, chunks: List[Chunk]) -> Dict[str, np.ndarray]:
        """Generate embeddings for a list of chunks."""
        if not chunks:
            return {}
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Extract text content
        texts = [chunk.content for chunk in chunks]
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        
        try:
            # Generate embeddings in batch for efficiency
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            
            # Create mapping from chunk_id to embedding
            embedding_dict = {}
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                embedding_dict[chunk_id] = embedding
            
            logger.info(f"Generated embeddings for {len(embedding_dict)} chunks")
            return embedding_dict
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query."""
        try:
            embedding = self.model.encode([query], convert_to_numpy=True)
            return embedding[0]  # Return single embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        return self.embedding_dim


class EmbeddingCache:
    """Cache embeddings to disk for faster loading."""
    
    def __init__(self, cache_dir: str = "data/embeddings"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "embeddings.pkl"
        self.metadata_file = self.cache_dir / "metadata.pkl"
    
    def save_embeddings(self, embeddings: Dict[str, np.ndarray], chunks: List[Chunk]):
        """Save embeddings and chunk metadata to cache."""
        try:
            # Save embeddings
            with open(self.cache_file, 'wb') as f:
                pickle.dump(embeddings, f)
            
            # Save chunk metadata
            metadata = {chunk.chunk_id: chunk.metadata for chunk in chunks}
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"Saved {len(embeddings)} embeddings to cache")
            
        except Exception as e:
            logger.error(f"Failed to save embeddings to cache: {e}")
    
    def load_embeddings(self):
        """Load embeddings and metadata from cache."""
        try:
            if not self.cache_file.exists() or not self.metadata_file.exists():
                return {}, {}

            # Load embeddings
            with open(self.cache_file, 'rb') as f:
                embeddings = pickle.load(f)

            # Load metadata
            with open(self.metadata_file, 'rb') as f:
                metadata = pickle.load(f)

            logger.info(f"Loaded {len(embeddings)} embeddings from cache")
            return embeddings, metadata

        except Exception as e:
            logger.error(f"Failed to load embeddings from cache: {e}")
            return {}, {}
    
    def is_cache_valid(self, chunks: List[Chunk]) -> bool:
        """Check if cache is valid for current chunks."""
        if not self.cache_file.exists():
            return False
        
        try:
            _, cached_metadata = self.load_embeddings()
            
            # Check if all chunks are in cache
            current_chunk_ids = {chunk.chunk_id for chunk in chunks}
            cached_chunk_ids = set(cached_metadata.keys())
            
            return current_chunk_ids == cached_chunk_ids
            
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear the embedding cache."""
        try:
            if self.cache_file.exists():
                os.remove(self.cache_file)
            if self.metadata_file.exists():
                os.remove(self.metadata_file)
            logger.info("Embedding cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")


class EmbeddingManager:
    """Manage embedding generation and caching."""
    
    def __init__(self):
        self.embedder = TextEmbedder()
        self.cache = EmbeddingCache()
    
    def get_embeddings(self, chunks: List[Chunk], use_cache: bool = True) -> Dict[str, np.ndarray]:
        """Get embeddings for chunks, using cache if available."""
        if use_cache and self.cache.is_cache_valid(chunks):
            logger.info("Using cached embeddings")
            embeddings, _ = self.cache.load_embeddings()
            return embeddings
        
        logger.info("Generating new embeddings")
        embeddings = self.embedder.embed_chunks(chunks)
        
        if use_cache:
            self.cache.save_embeddings(embeddings, chunks)
        
        return embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for query."""
        return self.embedder.embed_query(query)
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension."""
        return self.embedder.get_embedding_dimension()

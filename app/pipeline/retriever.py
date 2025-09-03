"""
Retriever module for knowledge base search using FAISS.
"""

from typing import List, Dict, Any, Optional
from app.retriever.store import VectorStore
from app.core.logging import get_logger

logger = get_logger()


class RetrieverModule:
    """Performs knowledge base retrieval using FAISS vector search."""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.logger = logger
    
    def search_knowledge(self, question: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant information.
        
        Args:
            question: Original user question
            top_k: Number of top results to return
            
        Returns:
            List of search results with content, source, and confidence
        """
        self.logger.simple("🔍 Searching knowledge base", 
                          question=question[:100],
                          top_k=top_k)
        
        try:
            # Use the original question as search query
            results = self.vector_store.search(question, k=top_k)
            
            # Format results for pipeline
            formatted_results = []
            for i, result in enumerate(results):
                formatted_results.append({
                    "id": i,
                    "content": result.get("content", ""),
                    "source": result.get("source", "unknown"),
                    "source_filename": f"{result.get('source', 'unknown')}.md",
                    "title": result.get("title", ""),
                    "confidence": result.get("confidence", 0.0),
                    "score": result.get("score", 0.0),
                    "chunk_id": result.get("chunk_id", "")
                })
            
            self.logger.simple("✅ Knowledge search completed", 
                              results_count=len(formatted_results),
                              top_confidence=formatted_results[0].get("confidence", 0) if formatted_results else 0)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error("❌ Knowledge search failed", error=str(e))
            return []
    
    def get_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract unique source files from search results."""
        sources = set()
        for result in results:
            source = result.get("source", "")
            if source and source != "unknown":
                sources.add(source)
        return list(sources)
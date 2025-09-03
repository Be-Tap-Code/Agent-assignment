"""
Text chunking for knowledge base processing.

Splits documents into manageable chunks for embedding and retrieval.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger()


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]


class ChunkProcessor:
    """Processes documents into chunks for embedding."""
    
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.logger = logger
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Chunk]:
        """
        Process documents into chunks.
        
        Args:
            documents: List of documents with 'content' and 'metadata' keys
            
        Returns:
            List of Chunk objects
        """
        self.logger.simple("📄 Processing documents into chunks", 
                          documents_count=len(documents))
        
        all_chunks = []
        
        for doc in documents:
            doc_chunks = self._chunk_document(doc)
            all_chunks.extend(doc_chunks)
        
        self.logger.simple("✅ Document chunking completed", 
                          total_chunks=len(all_chunks))
        
        return all_chunks
    
    def _chunk_document(self, document: Dict[str, Any]) -> List[Chunk]:
        """Chunk a single document."""
        content = document.get('content', '')
        metadata = document.get('metadata', {})
        
        if not content.strip():
            return []
        
        # Split content into sentences first
        sentences = self._split_into_sentences(content)
        
        # Group sentences into chunks
        chunks = self._group_sentences_into_chunks(sentences, metadata)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - can be improved with NLTK or spaCy
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _group_sentences_into_chunks(self, sentences: List[str], metadata: Dict[str, Any]) -> List[Chunk]:
        """Group sentences into chunks of appropriate size."""
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            # If adding this sentence would exceed chunk size, create a new chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Create chunk from current sentences
                chunk_content = ' '.join(current_chunk)
                chunk = self._create_chunk(chunk_content, metadata, chunk_index)
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add the last chunk if it has content
        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            chunk = self._create_chunk(chunk_content, metadata, chunk_index)
            chunks.append(chunk)
        
        return chunks
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get overlap sentences from the end of current chunk."""
        if not sentences:
            return []
        
        # Calculate how many words we want for overlap
        overlap_words = self.chunk_overlap
        
        overlap_sentences = []
        word_count = 0
        
        # Start from the end and work backwards
        for sentence in reversed(sentences):
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= overlap_words:
                overlap_sentences.insert(0, sentence)
                word_count += sentence_words
            else:
                break
        
        return overlap_sentences
    
    def _create_chunk(self, content: str, metadata: Dict[str, Any], chunk_index: int) -> Chunk:
        """Create a Chunk object with metadata."""
        # Generate chunk ID
        source = metadata.get('source', 'unknown')
        chunk_id = f"{source}_chunk_{chunk_index}"
        
        # Create chunk metadata
        chunk_metadata = {
            'source': source,
            'title': metadata.get('title', ''),
            'file_path': metadata.get('file_path', ''),
            'chunk_index': chunk_index,
            'word_count': len(content.split()),
            'chunk_length': len(content)
        }
        
        return Chunk(
            chunk_id=chunk_id,
            content=content,
            metadata=chunk_metadata
        )

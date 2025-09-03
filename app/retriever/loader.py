"""
Document loading and processing for knowledge base.

Loads markdown files from the knowledge base and processes them for chunking.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from app.core.logging import get_logger

logger = get_logger()


class DocumentProcessor:
    """Processes documents from the knowledge base."""
    
    def __init__(self, kb_dir: str = "app/kb/notes"):
        self.kb_dir = Path(kb_dir)
        self.logger = logger
    
    def load_and_process(self) -> List[Dict[str, Any]]:
        """
        Load and process all documents from the knowledge base.
        
        Returns:
            List of documents with content and metadata
        """
        self.logger.simple("📚 Loading documents from knowledge base", 
                          kb_dir=str(self.kb_dir))
        
        if not self.kb_dir.exists():
            self.logger.error("❌ Knowledge base directory not found", kb_dir=str(self.kb_dir))
            raise FileNotFoundError(f"Knowledge base directory not found: {self.kb_dir}")
        
        documents = []
        
        # Find all markdown files
        md_files = list(self.kb_dir.glob("*.md"))
        
        if not md_files:
            self.logger.warning("⚠️ No markdown files found in knowledge base", kb_dir=str(self.kb_dir))
            return documents
        
        self.logger.simple("📄 Found markdown files", files_count=len(md_files))
        
        for md_file in md_files:
            try:
                document = self._load_markdown_file(md_file)
                if document:
                    documents.append(document)
            except Exception as e:
                self.logger.error("❌ Failed to load markdown file", 
                                 file=str(md_file), error=str(e))
        
        self.logger.simple("✅ Document loading completed", 
                          documents_loaded=len(documents))
        
        return documents
    
    def _load_markdown_file(self, file_path: Path) -> Dict[str, Any]:
        """Load a single markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                self.logger.warning("⚠️ Empty markdown file", file=str(file_path))
                return None
            
            # Extract title from content (first heading or filename)
            title = self._extract_title(content, file_path)
            
            # Create document metadata
            metadata = {
                'source': file_path.stem,  # filename without extension
                'title': title,
                'file_path': str(file_path),
                'file_size': len(content),
                'word_count': len(content.split())
            }
            
            self.logger.simple("📄 Loaded markdown file", 
                              source=metadata['source'], 
                              title=title,
                              word_count=metadata['word_count'])
            
            return {
                'content': content,
                'metadata': metadata
            }
            
        except Exception as e:
            self.logger.error("❌ Error loading markdown file", 
                             file=str(file_path), error=str(e))
            raise
    
    def _extract_title(self, content: str, file_path: Path) -> str:
        """Extract title from markdown content."""
        lines = content.split('\n')
        
        # Look for first heading (## or #)
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()
        
        # If no heading found, use filename
        return file_path.stem.replace('_', ' ').title()

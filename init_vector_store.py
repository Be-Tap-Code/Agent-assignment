#!/usr/bin/env python3
"""
Initialize vector store for the geotechnical Q&A service.

This script builds the FAISS index from knowledge base documents.
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.retriever.store import VectorStore
from app.core.logging import get_logger

logger = get_logger()

def main():
    """Initialize the vector store."""
    print("🚀 Initializing Vector Store")
    print("=" * 50)
    
    try:
        # Create vector store instance
        vector_store = VectorStore()
        
        # Check if already initialized
        if vector_store.is_initialized():
            print("✅ Vector store already exists")
            print("📁 Index files found:")
            print(f"   - {vector_store.index_path}")
            print(f"   - {vector_store.ids_path}")
            print(f"   - {vector_store.meta_path}")
            print(f"   - {vector_store.texts_path}")
            
            response = input("\n🔄 Rebuild index? (y/N): ").strip().lower()
            if response != 'y':
                print("⏭️ Skipping rebuild")
                return
        
        print("\n🏗️ Building vector index...")
        print("This may take a few minutes depending on the size of your knowledge base.")
        
        # Build the index
        vector_store.build_index()
        
        print("\n✅ Vector store initialization completed successfully!")
        print("📊 Index statistics:")
        print(f"   - Index file: {vector_store.index_path}")
        print(f"   - Total vectors: {vector_store._index.ntotal if vector_store._index else 'Unknown'}")
        
        # Test search
        print("\n🧪 Testing search functionality...")
        test_queries = [
            "What is CPT analysis?",
            "How to calculate bearing capacity?",
            "Settlement analysis methods"
        ]
        
        for query in test_queries:
            try:
                results = vector_store.search(query, k=3)
                print(f"   Query: '{query}' → {len(results)} results")
                if results:
                    top_result = results[0]
                    print(f"      Top result: {top_result.get('source', 'unknown')} (confidence: {top_result.get('confidence', 0):.2f})")
            except Exception as e:
                print(f"   Query: '{query}' → Error: {e}")
        
        print("\n🎉 Vector store is ready for use!")
        
    except Exception as e:
        print(f"\n❌ Vector store initialization failed: {e}")
        logger.error("Vector store initialization failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
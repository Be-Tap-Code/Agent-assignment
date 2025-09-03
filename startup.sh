#!/bin/bash
set -e

echo "🚀 Starting Geotech Q&A Service"
echo "================================="

# Check if vector store exists
if [ ! -f "/app/data/vector_store/index.faiss" ]; then
    echo "📚 Vector store not found. Initializing..."
    python init_vector_store.py
    echo "✅ Vector store initialized successfully!"
else
    echo "✅ Vector store already exists. Skipping initialization."
fi

# Start the application
echo "🌐 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

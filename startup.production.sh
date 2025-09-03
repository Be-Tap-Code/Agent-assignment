#!/bin/bash
set -e

echo "🚀 Starting Geotech Q&A Service (Production)"
echo "============================================="

# Check if vector store exists
if [ ! -f "/app/data/vector_store/index.faiss" ]; then
    echo "📚 Vector store not found. Initializing..."
    python init_vector_store.py
    echo "✅ Vector store initialized successfully!"
else
    echo "✅ Vector store already exists. Skipping initialization."
fi

# Start the application with Gunicorn
echo "🌐 Starting FastAPI application with Gunicorn..."
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

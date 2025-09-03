FROM python:3.11-slim

WORKDIR /app

# Install system deps (đủ để build numpy, scipy,…)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-core.txt requirements-ml.txt pyproject.toml ./

# Install Python deps
# 1. Core trước (cache tốt hơn)
RUN pip install --no-cache-dir -r requirements-core.txt -i https://pypi.org/simple

# 2. ML deps (torch CPU + faiss CPU)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements-ml.txt -i https://pypi.org/simple \
 && rm -rf /root/.cache/pip

# Copy app code
COPY app/ ./app/
COPY static/ ./static/
COPY data/ ./data/
COPY env.example ./.env
COPY init_vector_store.py ./
COPY startup.sh ./

# Create dirs + chmod script
RUN mkdir -p /app/data/vector_store /app/logs \
 && chmod +x startup.sh

ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["./startup.sh"]


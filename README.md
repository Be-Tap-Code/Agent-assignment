# Geotech Q&A Service

A comprehensive geotechnical engineering Q&A service with RAG, computational tools, and modern observability features.

> 📋 **For detailed technical documentation, see [ENGINEERING_NOTES.md](ENGINEERING_NOTES.md)**

## 🚀 Quick Start

### Docker (Recommended)
```bash
# Build Docker image
docker build -t devops22clc/ai-chat:latest -f Dockerfile .

# Run container (detached mode)
docker run -p 8000:8000 -d devops22clc/ai-chat:latest

### Local Development
```bash
# Clone and setup
git clone <repository>
cd geotech-qa

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your GOOGLE_API_KEY

# Initialize vector store (REQUIRED)
python init_vector_store.py

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Ask a Question

#### **Windows (PowerShell/CMD)**
```bash
# General knowledge question
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"How is cone resistance data used in Settle3 CPT analysis?\", \"context\": null}"

# Calculation question  
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"Calculate the bearing capacity for a 2m wide foundation with soil unit weight 18 kN/m³, depth 1.5m, and friction angle 30°\", \"context\": null}"

# Simple question
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"What is CPT analysis?\"}"
```

#### **Linux/Mac**
```bash
# General knowledge question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How is cone resistance data used in Settle3 CPT analysis?",
    "context": null
  }'

# Calculation question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Calculate the bearing capacity for a 2m wide foundation with soil unit weight 18 kN/m³, depth 1.5m, and friction angle 30°",
    "context": null
  }'

# Simple question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is CPT analysis?"
  }'
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics (JSON)
```bash
curl http://localhost:8000/metrics
```

### Web UI
Open http://localhost:8000 in your browser for the interactive chat interface.

## 🐳 Docker Commands

### **Basic Docker Operations**
```bash
# Build image
docker build -t devops22clc/ai-chat:latest -f Dockerfile .

# Run container (foreground)
docker run -p 8000:8000 devops22clc/ai-chat:latest

# Run container (background/detached)
docker run -p 8000:8000 -d devops22clc/ai-chat:latest
```

#### **API Connection Issues**
```bash
# Test if service is running
curl http://localhost:8000/health

# Check container status
docker ps

# View container logs
docker logs <container_name>
```

## 🧪 Quick Testing

### **Test API Endpoints**
```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# Simple question (Windows)
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"What is CPT analysis?\"}"

# Simple question (Linux/Mac)
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "What is CPT analysis?"}'
```

### **Expected Response**
```json
{
  "answer": "CPT (Cone Penetration Test) analysis is a geotechnical investigation method...",
  "citations": [
    {
      "source": "cpt_analysis_settle3.md",
      "confidence": 0.85,
      "text": "CPT analysis involves..."
    }
  ],
  "trace_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 📚 Vector Store Initialization

### Automatic Initialization (Docker)
The Docker setup automatically initializes the vector store on first run:
- **Development**: `startup.sh` checks and initializes if needed
- **Production**: `startup.production.sh` handles initialization
- **Persistence**: Vector store data is mounted to `./data/` directory

### Manual Initialization (Local)
```bash
# Initialize vector store from knowledge base
python init_vector_store.py

# The script will:
# 1. Load documents from app/kb/notes/
# 2. Create embeddings using sentence-transformers
# 3. Build FAISS index
# 4. Save to data/vector_store/
```

### Vector Store Files
```
data/vector_store/
├── index.faiss          # FAISS index file
├── ids.npy             # Document IDs
├── metadata.json       # Document metadata
└── texts.json          # Document texts
```

## 🏗️ Architecture

### Core Components
- **FastAPI**: Modern async web framework
- **RAG Pipeline**: FAISS + sentence-transformers for knowledge retrieval
- **Computational Tools**: Terzaghi bearing capacity & settlement calculations
- **LLM Integration**: Google Gemini for answer synthesis
- **Observability**: Structured logging, metrics, and tracing

### Pipeline Flow
```
Question → Decision → [Retrieval + Computation] → Synthesis → Answer
```

1. **Decision**: Analyze question to determine required actions
2. **Retrieval**: Search knowledge base for relevant information
3. **Computation**: Run engineering calculations if needed
4. **Synthesis**: Combine results using LLM
5. **Response**: Return answer with citations and trace

## 🛠️ Features

### Knowledge Base
- **Geotechnical Notes**: Settlement analysis, bearing capacity, CPT analysis
- **Vector Search**: Semantic similarity using sentence-transformers
- **Citations**: Source attribution for all retrieved information

### Computational Tools
- **Terzaghi Bearing Capacity**: For cohesionless soils
- **Settlement Analysis**: Elastic settlement calculations
- **Input Validation**: Comprehensive parameter validation
- **Error Handling**: Graceful failure with fallback responses

### Observability
- **Structured Logging**: JSON logs with trace correlation
- **Metrics**: JSON metrics endpoint with comprehensive counters
- **Tracing**: Request-level trace IDs for debugging
- **Performance**: Duration tracking for all operations

#### Sample Log Entry
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Question processed successfully",
  "operation": "ask_question",
  "duration_ms": 1250.5,
  "question_length": 45,
  "has_context": true,
  "answer_length": 234
}
```

#### Metrics Sample
```json
{
  "requests": {
    "total": 42,
    "successful": 40,
    "failed": 2,
    "success_rate": 95.24
  },
  "questions": {
    "total": 38,
    "with_context": 12,
    "context_rate": 31.58
  },
  "tool_calls": {
    "total": 15,
    "terzaghi": 8,
    "settlement": 7,
    "failures": 0,
    "success_rate": 100.0
  }
}
```

### Security & Reliability
- **Input Sanitization**: XSS and injection protection
- **Timeout Handling**: Configurable timeouts for all operations
- **Retry Logic**: Automatic retry for transient failures
- **Secret Protection**: Automatic redaction of sensitive data

## 📊 Example API Calls

### Basic Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is CPT analysis?"}'
```

### Calculation Request
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Calculate settlement for load 1000 kN and Young modulus 50000 kPa",
    "context": "Foundation width is 2m"
  }'
```

### Complex Engineering Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I determine bearing capacity for a shallow foundation in sandy soil?",
    "context": "Foundation is 3m wide, 2m deep, soil unit weight 19 kN/m³, friction angle 35°"
  }'
```

## ⚙️ Configuration

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
MAX_QUESTION_LENGTH=2000
LLM_TIMEOUT_SECONDS=5.0
```

### Tool Parameters
- **Terzaghi**: Foundation width (B), soil unit weight (γ), depth (Df), friction angle (φ)
- **Settlement**: Applied load, Young's modulus (E)

## 🧪 Testing

### Run All Tests
```bash
pytest -v
```

### Run Specific Tests
```bash
# Tool correctness tests
pytest tests/test_tools.py -v

# Retriever tests
pytest tests/test_retriever.py -v

# API tests
pytest tests/test_api.py -v

# Run evaluation
python run_evaluation.py
```

## 📊 Evaluation

### Test Dataset
- **Size**: 8 Q/A pairs covering CPT analysis, liquefaction, Settle3 usage, and calculations
- **Sources**: Rocscience documentation, geotechnical engineering references
- **Format**: JSON with expected answers, citations, and keywords

### Evaluation Metrics
- **Hit@K**: Measures if correct sources appear in top-K results
- **Keyword Overlap**: Ratio of expected keywords found in actual answers
- **Confidence Scores**: From retrieved context similarity

### Current Performance
```json
{
  "total_questions": 8,
  "hit_at_1": 1.0,
  "hit_at_3": 1.0,
  "average_keyword_overlap": 0.750,
  "citation_match_rate": 1.0,
  "average_confidence": 0.725
}
```

### Test Coverage
```bash
pytest --cov=app --cov-report=html
```

## 🎯 Design Choices & Tradeoffs

### Architecture Decisions

#### **Pipeline vs Monolithic**
- ✅ **Chosen**: Modular pipeline architecture
- **Tradeoff**: More complex but better maintainability and testability
- **Benefit**: Easy to add new tools or modify existing ones

#### **RAG vs Fine-tuning**
- ✅ **Chosen**: RAG with local knowledge base
- **Tradeoff**: Requires good chunking and retrieval strategy
- **Benefit**: No model training, easy to update knowledge

#### **FastAPI vs Flask**
- ✅ **Chosen**: FastAPI for async support
- **Tradeoff**: Newer framework, smaller ecosystem
- **Benefit**: Better performance, automatic API docs, type safety

### Technical Tradeoffs

#### **Vector Store: FAISS vs Pinecone**
- ✅ **Chosen**: FAISS for local deployment
- **Tradeoff**: No managed service features
- **Benefit**: No external dependencies, full control

#### **Embeddings: Sentence-transformers vs OpenAI**
- ✅ **Chosen**: Local sentence-transformers
- **Tradeoff**: May be less powerful than OpenAI embeddings
- **Benefit**: No API costs, works offline

#### **LLM: Gemini vs GPT-4**
- ✅ **Chosen**: Gemini for cost and performance
- **Tradeoff**: Different prompt engineering needed
- **Benefit**: Good performance, competitive pricing

### Observability Tradeoffs

#### **Logging: Structured vs Simple**
- ✅ **Chosen**: Structured JSON logging
- **Tradeoff**: More verbose, requires parsing
- **Benefit**: Better for production monitoring

#### **Metrics: JSON vs Prometheus**
- ✅ **Chosen**: JSON format for simplicity
- **Tradeoff**: Less compatible with Prometheus ecosystem
- **Benefit**: Easier to parse and integrate with custom dashboards

## 🎯 Design Choices & Tradeoffs

### Retrieval Configuration
- **Chunk Size: 400 characters** - Balance between context preservation and retrieval precision
- **Top-K: 3 results** - Sufficient context diversity without overwhelming the LLM
- **Embedding Model: all-MiniLM-L6-v2** - Fast inference with good semantic understanding

### Tool Orchestration Logic
- **Decision Module** routes questions to appropriate modules:
  - **Retrieve**: General knowledge questions about Settle3, CPT, liquefaction
  - **Compute**: Numerical calculations (bearing capacity, settlement)
  - **Both**: Complex questions requiring both knowledge and calculations

### Safety & Guardrails
- **Timeouts**: LLM (5s), Tools (1s) with retry logic
- **Input Validation**: Max 2000 characters, parameter range checks
- **Error Handling**: Circuit breaker pattern, graceful degradation

### Geotechnical Assumptions
- **Terzaghi Bearing Capacity**: Cohesionless soils (c=0), strip footing, general shear failure
- **Settlement Analysis**: Linear elastic behavior, immediate settlement only
- **Data Sources**: Rocscience documentation, CPT analysis, liquefaction methods

## 🔧 Development

### Project Structure
```
app/
├── api/           # FastAPI endpoints
├── core/          # Configuration, logging, metrics
├── pipeline/      # Main processing pipeline
├── retriever/     # RAG components
├── tools/         # Computational tools
└── kb/           # Knowledge base
```

### Adding New Tools
1. Create tool class in `app/tools/`
2. Add validation with Pydantic
3. Integrate with pipeline orchestrator
4. Add tests

### Adding New Knowledge
1. Add markdown files to `app/kb/notes/`
2. Rebuild vector store: `python init_vector_store.py`
3. Test retrieval quality

## 📈 Performance

### Benchmarks
- **Response Time**: ~1-3 seconds for typical questions
- **Throughput**: ~10-20 requests/second
- **Memory Usage**: ~500MB base + embeddings
- **Storage**: ~100MB for knowledge base

### Optimization Tips
- Use connection pooling for database
- Cache embeddings for repeated queries
- Implement request queuing for high load
- Monitor metrics for bottlenecks

## 🚨 Troubleshooting

### Common Issues

#### **API Key Not Set**
```bash
Error: GOOGLE_API_KEY is not set
Solution: Set environment variable or update .env file
```

#### **Vector Store Not Found**
```bash
Error: Vector store not initialized
Solution: Run python init_vector_store.py
```

#### **Tool Validation Errors**
```bash
Error: Invalid parameter values
Solution: Check input ranges and units
```

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📞 Support

For issues and questions:
- Create GitHub issue
- Check troubleshooting section
- Review logs with trace IDs


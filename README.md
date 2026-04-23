# 🚀 Business Document Intelligence System (BDIS)

BDIS is a production-grade AI-powered system designed to transform unstructured business documents (invoices, receipts, contracts) into structured, validated, and high-confidence data insights.

Built with **Clean Architecture** principles, the system prioritizes reliability, observability, and strict separation of concerns.

---

## ✨ Key Features (Phase 4 Completed)

- **🛡️ PII Sanitization**: Automated redaction of sensitive information (Emails, SSNs, Credit Cards) before processing by AI.
- **🧠 Resilient AI Extraction**: Schema-aware extraction using OpenAI, wrapped in shared resilience policies (Circuit Breakers & Retries).
- **🧹 Deterministic Normalization**: Strategy-based cleaning of messy AI outputs into standardized formats (ISO dates, float amounts).
- **📊 Automated Evaluation**: Integrated benchmarking engine that compares extraction results against ground-truth datasets to report accuracy.
- **⚡ Asynchronous Processing**: Background job orchestration using Redis and Celery for high-throughput document handling.
- **🎨 Enterprise Dashboard**: Premium Streamlit UI for real-time document monitoring and validation.

---

## 🏗️ Architecture: Clean & Modular

BDIS follows the **Ports and Adapters (Hexagonal)** pattern to ensure the core business logic is decoupled from infrastructure:

- **Domain**: Pure business entities (DocumentExtraction) and policies (Status determination).
- **Use Cases**: Orchestration logic (ProcessingPipeline, FetchDocuments).
- **Ports**: Abstract interfaces for external dependencies (IExtractionService, IDocumentRepository).
- **Adapters**: Concrete implementations (OpenAIExtractor, SQLDocumentRepository, RegexPIISanitizer).

---

## 🛠️ Tech Stack

- **Backend**: Python 3.9+, FastAPI, Uvicorn
- **Frontend**: Streamlit (Glassmorphic Design)
- **AI/ML**: OpenAI API
- **Database**: SQLAlchemy (PostgreSQL / SQLite fallback)
- **Task Queue**: Celery & Redis
- **Storage**: AWS S3 / Minio
- **DevOps**: Docker, Docker Compose

---

## 🚀 Getting Started

### 1. Prerequisites
- Docker & Docker Compose
- OpenAI API Key

### 2. Environment Setup
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql://bdis_user:bdis_password@postgres:5432/bdis_db
CELERY_BROKER_URL=redis://redis:6379/0
```

### 3. Run with Docker (Recommended)
```bash
docker-compose up --build
```
- **API**: `http://localhost:8000/docs`
- **Dashboard**: `http://localhost:8501`

### 4. Run Locally (Native Mode)
If you prefer to run without Docker (using SQLite):
```bash
# Terminal 1: API
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
export DATABASE_URL=sqlite:///bdis_prod.db
uvicorn bdis.frameworks.api.main:app --reload

# Terminal 2: Dashboard
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
export API_BASE_URL=http://localhost:8000
streamlit run src/bdis/frameworks/ui/app.py
```

---

## 🧪 Testing

### Unit Tests
```bash
PYTHONPATH=src pytest tests/
```

### Pipeline Demonstration
Run the integrated demo script to see the Phase 4 pipeline (Sanitization -> Extraction -> Evaluation) in action:
```bash
python3 scripts/test_pipeline.py
```

---

## 📅 Roadmap
- [x] Phase 1: Core extraction & MVP
- [x] Phase 2: Domain Modeling & Repositories
- [x] Phase 3: Enterprise UI & API Refactoring
- [x] Phase 4: Reliability & Evaluation Layer
- [ ] **Phase 5: Cloud Infrastructure & PostgreSQL Migration** (Next)

---

## 📄 License
MIT License. Created by AdrianaSo.

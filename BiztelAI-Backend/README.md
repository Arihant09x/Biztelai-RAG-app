# BiztelAI Manufacturing SOP AI Copilot Backend

> **Enterprise-Grade AI Copilot for Manufacturing Floor Operations**  
> Built with **Python 3.12.10**, **Flask**, **PostgreSQL (pgvector)**, **Celery**, and **Upstash Redis**.

---

## 🏭 Overview

The **BiztelAI Manufacturing SOP AI Copilot** is a production-grade backend designed to assist manufacturing plant supervisors, maintenance engineers, and machine operators in instantly retrieving accurate, source-grounded answers from Standard Operating Procedures (SOPs), safety protocols, machinery maintenance manuals, and quality standards.

Unlike basic conversational PDF chatbots that hallucinate equipment specs or safety tolerances, this system enforces **deterministic grounding**, **structure-aware chunking**, **hybrid retrieval (pgvector + FTS + RRF)**, **cross-encoder reranking**, **calibrated safety abstention**, and **strict Pydantic v2 structured response blocks**.

---

## ⚡ Key Highlights & Capabilities

- **Strict Multi-Provider LLM Integration**: Completely decoupled LLM and embedding pipelines. Compatible with OpenAI, Google Gemini, OpenRouter, and local endpoints (`LLM_API_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`).
- **Zero-Tolerance Hallucination Engine**: Calibrated evidence confidence scoring. Safely abstains when documentation is absent, out-of-domain, or contradictory.
- **12 Rich UI Response Blocks**: Returns validated, type-safe block payloads (`markdown`, `steps`, `checklist`, `callout`, `table`, `mermaid`, `image`, `source`, `quote`, `comparison`, `accordion`, `progress`).
- **Guided Procedure Execution**: Step-by-step interactive workflow generator with live step completion progress tracking (`/api/v1/procedures`).
- **Asynchronous Ingestion Pipeline**: Celery background processing with Upstash Redis TLS support (`rediss://`), PyMuPDF heading & table parsing, and Tesseract OCR fallback.
- **Enterprise Security & RBAC**: JWT token authentication with rotation, bcrypt password hashing, role-based access control (`admin`, `supervisor`, `operator`, `auditor`), and immutable audit logging.
- **Interactive Swagger Documentation**: Live exploration and testing at `/api/v1/docs`.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Language & Runtime** | Python 3.12.10 |
| **Framework** | Flask, Flask Blueprints, Flask-SQLAlchemy, Flask-Migrate |
| **Validation & Serialization** | Pydantic v2 (Strict Base, `extra="forbid"`) |
| **Authentication & Security** | Flask-JWT-Extended, Flask-CORS, Flask-Limiter, bcrypt |
| **Database & Search** | PostgreSQL 16 + pgvector, PostgreSQL Full-Text Search, psycopg 3 |
| **Embeddings & Reranking** | Sentence Transformers (`all-MiniLM-L6-v2`, 384-dim), Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) |
| **Background Processing** | Celery 5.x, Upstash Redis / Redis 7 (TLS-enabled) |
| **Document Processing** | PyMuPDF (fitz), Tesseract OCR fallback |
| **Production WSGI** | Gunicorn (pre-fork worker model) |
| **Containerization** | Docker, Docker Compose |

---

## 🚀 Quickstart with Docker Compose

Run the entire stack (PostgreSQL + pgvector, Redis, Flask Gunicorn API, and Celery worker) on any developer machine in one command:

```bash
# 1. Clone repository and navigate to root
cd "BiztelAI Manufacturing SOP Copilot"

# 2. Configure environment variables
cp .env.example .env

# Edit .env with your LLM provider credentials (OpenAI, Gemini, or OpenRouter)
# LLM_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
# LLM_API_KEY=your-api-key-here
# LLM_MODEL=gemini-1.5-flash

# 3. Build and launch all services
docker compose up --build
```

The services will become available at:
- **API Server & Swagger UI**: `http://localhost:5000/api/v1/docs`
- **Health Check**: `http://localhost:5000/api/v1/health`
- **PostgreSQL pgvector**: `localhost:5432`
- **Redis Cache/Broker**: `localhost:6379`

---

## 💻 Local Development Setup (Without Docker)

### 1. Prerequisites
- Python 3.12.10 installed (`python --version`)
- Upstash Redis account or local Redis server
- Local PostgreSQL instance or SQLite (for quick offline dev)

### 2. Virtual Environment & Dependencies
```bash
# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install PyTorch CPU wheel
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install application dependencies
pip install -r requirements.txt
```

### 3. Initialize Database & Seed Sample SOPs
```bash
# Seed 4 realistic manufacturing SOPs (CNC, LOTO, Hydraulic Press, Calipers)
python scripts/seed_sample_data.py --sqlite
```

### 4. Verify Model & Embedding Pipeline
```bash
# Run embedding health diagnostics
python scripts/test_embedding_health.py

# Test LLM provider connection (masks API keys)
python scripts/test_llm_connection.py
```

### 5. Run the Automated Test Suite
```bash
pytest -v
```
*Result: 28 of 28 tests passing cleanly (100% success rate).*

### 6. Run the Grounding Evaluation Benchmark
```bash
python scripts/run_evaluation.py --sqlite --mock-llm
```
*Result: 7 of 7 benchmark queries passed (100% accuracy, 100% groundedness, 100% abstention accuracy, ~300ms latency).*

### 7. Start the Development Server
```bash
python run.py
```
Visit `http://localhost:5000/api/v1/docs` to test endpoints via Swagger UI.

### 8. Start the PlantAssist AI Frontend
```bash
cd BiztelAI-Frontend
npm install
npm run dev
```
Visit `http://localhost:3000` to launch the **PlantAssist AI** user interface. Quick 1-click login buttons for **Supervisor**, **Admin**, and **Operator** are available on the login screen.

---

## 📡 Core API Endpoints (`/api/v1`)

| Module | Method | Endpoint | Description |
|---|---|---|---|
| **Health** | `GET` | `/health` | Liveness check |
| | `GET` | `/health/ready` | Readiness check (DB & Redis) |
| **Auth** | `POST` | `/auth/register` | Register user (`admin`, `supervisor`, `operator`) |
| | `POST` | `/auth/login` | Login and obtain JWT tokens |
| | `POST` | `/auth/refresh` | Refresh access token |
| | `GET` | `/auth/me` | Current user profile |
| **Documents** | `POST` | `/documents/upload` | Upload PDF (validates magic bytes & SHA-256) |
| | `GET` | `/documents` | List indexed SOPs |
| | `GET` | `/documents/{id}` | Inspect document status & metadata |
| | `DELETE` | `/documents/{id}` | Soft delete document |
| | `POST` | `/documents/{id}/reprocess` | Re-enqueue ingestion job |
| **Ingestion** | `GET` | `/ingestion/jobs/{id}` | Check async job progress |
| **Chat & RAG** | `POST` | `/chat` | Grounded QA query with structured blocks |
| | `POST` | `/chat/stream` | Server-Sent Events (SSE) streaming |
| **Procedures** | `POST` | `/procedures/generate` | Generate guided procedure with checklist |
| | `POST` | `/procedures/{id}/progress` | Update step completion status |
| **Feedback** | `POST` | `/feedback` | Submit thumbs up/down and notes |
| **Admin** | `GET` | `/admin/metrics` | System telemetry & query stats |
| **LLM** | `GET` | `/llm/status` | Active provider config (masked) |
| | `POST` | `/llm/test-connection` | Live LLM ping test |

---

## 📚 Technical Documentation

Comprehensive architectural and engineering documentation is provided in the `docs/` directory:

1. [**System Architecture (`docs/ARCHITECTURE.md`)**](docs/ARCHITECTURE.md): Layered architecture, component interaction, Upstash Redis Celery flow.
2. [**REST API Reference (`docs/API.md`)**](docs/API.md): Request/response payloads and error envelopes.
3. [**Database & Indexing (`docs/DATABASE.md`)**](docs/DATABASE.md): SQLAlchemy models, pgvector schema, full-text search indexes.
4. [**RAG Pipeline Engineering (`docs/RAG_PIPELINE.md`)**](docs/RAG_PIPELINE.md): Ingestion, chunking, hybrid retrieval, reranking, context engineering, grounding.
5. [**Application Security (`docs/SECURITY.md`)**](docs/SECURITY.md): JWT rotation, RBAC, input sanitization, file signature verification.
6. [**Troubleshooting & Runbook (`docs/TROUBLESHOOTING.md`)**](docs/TROUBLESHOOTING.md): Common errors, Upstash TLS configuration, HuggingFace offline cache.
7. [**Evaluation Benchmark (`docs/EVALUATION.md`)**](docs/EVALUATION.md): Grounding benchmark methodology, metrics interpretation.


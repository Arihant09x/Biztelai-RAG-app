# BiztelAI Manufacturing SOP AI Copilot — System Architecture

## 1. Architectural Philosophy
The BiztelAI Manufacturing SOP Copilot follows **Clean Layered Architecture** with strict separation of concerns, ensuring:
- **Zero Business Logic in Routes**: Controllers and route handlers purely orchestrate request parsing, validation, authentication, and HTTP serialization.
- **Provider Decoupling**: LLM providers and embedding models are isolated through abstract interfaces. Switching LLM providers (e.g. OpenAI to Gemini or OpenRouter) requires zero database migrations and zero re-indexing.
- **Fail-Safe Grounding**: Strict token budgeting, citation verification, and calibrated score thresholding to prevent manufacturing accidents caused by hallucinations.

---

## 2. Layer Diagram

```
                 +-----------------------------------------+
                 |          Client / Frontend / UI         |
                 +-----------------------------------------+
                                      |
                           HTTP / REST / SSE / JWT
                                      v
+-------------------------------------------------------------------------+
| API & Routing Layer (Flask Blueprints under /api/v1)                    |
| - /health    - /auth       - /documents   - /ingestion   - /chat        |
| - /procedures - /feedback  - /admin       - /llm         - /docs        |
+-------------------------------------------------------------------------+
                                      |
                     Authentication & RBAC Middleware
                     (Flask-JWT-Extended + RolesDecorator)
                                      v
+-------------------------------------------------------------------------+
| Request & Response Validation (Pydantic v2 Models - extra="forbid")      |
+-------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------+
| Application Services Layer                                              |
| - DocumentService   - IngestionService   - ConversationService          |
| - ProcedureService  - FeedbackService    - EvaluationService            |
+-------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------+
| RAG Core Domain Services                                                |
| - PDFExtractionService (PyMuPDF + OCR Fallback + Table Extraction)      |
| - StructureAwareChunkingService (~700 tokens, 100 overlap, LOTO groups)  |
| - EmbeddingService (SentenceTransformers all-MiniLM-L6-v2, 384-dim)     |
| - HybridRetrievalService (pgvector Cosine + Postgres FTS + RRF)         |
| - RerankingService (Cross-Encoder ms-marco-MiniLM-L-6-v2)                |
| - ContextEngineeringService (Token budgeting, prompt injection defense) |
| - GroundingValidationService (Citation validation, abstention engine)    |
| - LLMProviderFactory (OpenAI / Gemini / OpenRouter provider adapter)    |
+-------------------------------------------------------------------------+
            |                                         |
            v                                         v
+-----------------------+                 +-------------------------------+
| Storage Layer         |                 | Asynchronous Processing       |
| - PostgreSQL 16       |                 | - Celery Worker               |
| - pgvector Extension  |                 | - Upstash Redis (TLS rediss://|
| - Full-Text Search    |                 |   with SSL certificate bypass)|
| - Local / S3 Storage  |                 | - Idempotent Ingestion Tasks  |
+-----------------------+                 +-------------------------------+
```

---

## 3. Core Component Interactions

### 3.1 Document Ingestion Flow
1. **Upload**: User uploads PDF via `POST /api/v1/documents/upload`.
2. **Security & Deduplication**:
   - Validates `%PDF-` file signature (magic bytes).
   - Computes SHA-256 hash. Rejects duplicate uploads instantly.
   - Saves file to storage abstraction (`LocalStorageService`).
3. **Async Enqueue**: Creates `IngestionJob` record (status: `PENDING`) and enqueues Celery task `ingest_document_task`.
4. **PyMuPDF Extraction**: Extracts page text, detects header font sizes, extracts tables via `page.find_tables()`. Triggers Tesseract OCR if text density is below threshold.
5. **Structure-Aware Chunking**: Chunks around ~700 tokens preserving procedure steps and safety warnings.
6. **Batch Embedding**: Generates 384-dimensional dense vectors with Sentence Transformers.
7. **Vector Indexing**: Writes chunks and vectors into `document_chunks` table with pgvector index and full-text search tsvector.
8. **Completion**: Updates job to `COMPLETED` (or `FAILED` with error stack trace and transactional rollback).

### 3.2 Query Processing & Grounding Flow
1. **Query Ingestion**: User submits question via `POST /api/v1/chat`.
2. **Intent & Safety Classification**: Detects procedural, comparison, safety-critical, or normal queries.
3. **Hybrid Retrieval**:
   - Dense vector similarity search using pgvector cosine distance (`<=>`).
   - Sparse lexical search using PostgreSQL `to_tsvector('english', content)` and `plainto_tsquery`.
   - Exact identifier boost for equipment codes (e.g. `HP-200`, `SOP-101`, `480V`).
   - Merged using **Reciprocal Rank Fusion (RRF)**: $RRF\_Score(d) = \sum \frac{1}{k + rank_i(d)}$.
4. **Cross-Encoder Reranking**: Re-evaluates top 10 candidates with `cross-encoder/ms-marco-MiniLM-L-6-v2` down to top 5.
5. **Context Engineering**:
   - Maps each chunk to an explicit citation handle (`source_1`, `source_2`).
   - Sanitizes untrusted text to prevent prompt injection.
   - Detects potential procedural contradictions across documents.
6. **Grounding & Abstention Check**:
   - If retrieved relevance score is below calibrated threshold (`RAG_SIMILARITY_THRESHOLD`), the system **abstains** and returns a standardized safety alert.
7. **Structured Generation**: Calls configured LLM provider expecting valid JSON adhering to `CopilotAnswerResponse`.
8. **Validation**: Enforces citation integrity. Flags any steps citing non-existent sources.


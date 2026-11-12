# BiztelAI Manufacturing SOP AI Copilot — Complete Postman API Testing Guide

This comprehensive, step-by-step testing guide allows you to test every endpoint of the **BiztelAI Manufacturing SOP Copilot Backend** using Postman or cURL.

---

## 1. Environment & Setup

### Base URL
```
http://localhost:5000/api/v1
```

### Pre-Configured Test Accounts (Already Seeded in Database)
| Role | Email | Password | Permissions |
|---|---|---|---|
| **Supervisor** | `supervisor@biztelai.com` | `Password123!` | Upload SOPs, reprocess, chat, generate procedures |
| **Admin** | `admin@biztelai.com` | `AdminSecret123!` | System configuration, admin metrics, full access |
| **Operator** | `operator@biztelai.com` | `Operator123!` | Search SOPs, chat, update procedure progress |

### Recommended Postman Environment Variables
Create a Postman Environment with the following variables:
- `base_url`: `http://localhost:5000/api/v1`
- `access_token`: *(auto-populated from login)*
- `refresh_token`: *(auto-populated from login)*
- `document_id`: *(auto-populated from document endpoints)*
- `procedure_id`: *(auto-populated from procedure generation)*

---

## 2. Endpoints Testing Sequence

---

### Step 1: Liveness Probe
Verifies that the Flask web server process is live.

- **Method**: `GET`
- **URL**: `{{base_url}}/health`
- **Headers**: *(None required)*
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "service": "biztelai-sop-backend",
  "status": "healthy",
  "timestamp": "development"
}
```

---

### Step 2: Readiness Probe
Verifies connectivity to Neon PostgreSQL, Upstash Redis, and Document Storage.

- **Method**: `GET`
- **URL**: `{{base_url}}/health/ready`
- **Headers**: *(None required)*
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "status": "ready",
  "components": {
    "database": {
      "status": "up"
    },
    "redis": {
      "provider": "upstash",
      "status": "configured"
    },
    "storage": {
      "path": "data\\documents",
      "status": "up"
    }
  }
}
```

---

### Step 3: Register a New User
Creates a new account and immediately returns access & refresh JWT tokens.

- **Method**: `POST`
- **URL**: `{{base_url}}/auth/register`
- **Headers**: 
  - `Content-Type`: `application/json`
- **Body** (raw JSON):
```json
{
  "email": "technician1@biztelai.com",
  "password": "SecurePassword123!",
  "full_name": "Vikram Singh",
  "department": "Machining",
  "role": "operator"
}
```
- **Expected Status**: `201 Created`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "e8d91f24-9b2e-4cf0-a615-182390f7bd12",
      "email": "technician1@biztelai.com",
      "full_name": "Vikram Singh",
      "role": "operator",
      "department": "Machining"
    },
    "tokens": {
      "access_token": "eyJhbGciOi...",
      "refresh_token": "eyJhbGciOi...",
      "token_type": "Bearer"
    }
  }
}
```

---

### Step 4: Login with Existing Account
Authenticates and issues fresh JWT access and refresh tokens.

- **Method**: `POST`
- **URL**: `{{base_url}}/auth/login`
- **Headers**: 
  - `Content-Type`: `application/json`
- **Body** (raw JSON):
```json
{
  "email": "supervisor@biztelai.com",
  "password": "Password123!"
}
```
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "18f0db2b-...",
      "email": "supervisor@biztelai.com",
      "full_name": "Rajesh Kumar (Supervisor)",
      "role": "supervisor",
      "department": "Machining"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "Bearer"
    }
  }
}
```
> **Postman Tip**: In Postman's **Tests** tab for this request, add:
> ```javascript
> var jsonData = pm.response.json();
> pm.environment.set("access_token", jsonData.data.tokens.access_token);
> pm.environment.set("refresh_token", jsonData.data.tokens.refresh_token);
> ```

---

### Step 5: Get Current User Profile (`/auth/me`)
Retrieves user information from the active JWT bearer token.

- **Method**: `GET`
- **URL**: `{{base_url}}/auth/me`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "id": "18f0db2b-...",
    "email": "supervisor@biztelai.com",
    "full_name": "Rajesh Kumar (Supervisor)",
    "role": "supervisor",
    "department": "Machining"
  }
}
```

---

### Step 6: Refresh Access Token
Issues a new access token using the refresh token.

- **Method**: `POST`
- **URL**: `{{base_url}}/auth/refresh`
- **Headers**:
  - `Authorization`: `Bearer {{refresh_token}}`
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer"
  }
}
```

---

### Step 7: List Seeded Documents
Lists all Standard Operating Procedures indexed in the system.

- **Method**: `GET`
- **URL**: `{{base_url}}/documents?page=1&per_page=10`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "id": "27fae120-...",
        "title": "CNC Spindle Maintenance and Bearing Lubrication",
        "category": "Maintenance",
        "department": "Machining",
        "status": "indexed",
        "chunks_count": 2
      },
      {
        "id": "a910dc41-...",
        "title": "Hazardous Energy Control (Lockout / Tagout) Procedure",
        "category": "Safety",
        "department": "Plant Safety",
        "status": "indexed",
        "chunks_count": 2
      },
      {
        "id": "e402bc89-...",
        "title": "Hydraulic Stamping Press Safety and Operating Procedure",
        "category": "Operations",
        "department": "Forming",
        "status": "indexed",
        "chunks_count": 2
      },
      {
        "id": "ff19b872-...",
        "title": "Digital Vernier Caliper Calibration and Quality Verification",
        "category": "Quality",
        "department": "Quality Assurance",
        "status": "indexed",
        "chunks_count": 1
      }
    ],
    "total": 4,
    "page": 1,
    "per_page": 10
  }
}
```
> **Postman Tip**: Save one of the document IDs to `{{document_id}}`:
> ```javascript
> var jsonData = pm.response.json();
> if (jsonData.data.documents.length > 0) {
>     pm.environment.set("document_id", jsonData.data.documents[0].id);
> }
> ```

---

### Step 8: Get Document Details by ID
Inspects metadata, status, and chunk count for a specific document.

- **Method**: `GET`
- **URL**: `{{base_url}}/documents/{{document_id}}`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "id": "27fae120-...",
    "title": "CNC Spindle Maintenance and Bearing Lubrication",
    "category": "Maintenance",
    "department": "Machining",
    "status": "indexed",
    "file_size_bytes": 16428,
    "pages_count": 2,
    "chunks_count": 2
  }
}
```

---

### Step 9: Upload a New SOP PDF (Multipart Form)
Uploads an SOP document. Validates PDF magic bytes, calculates SHA-256 for deduplication, and enqueues Celery background ingestion.

- **Method**: `POST`
- **URL**: `{{base_url}}/documents/upload`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
  - *(Do not manually set `Content-Type: multipart/form-data`; Postman will set the boundary automatically)*
- **Body** (`form-data`):
  - `file`: Select any PDF file (e.g. from `sample_data/sops/SOP-101-CNC-Spindle-Maintenance.pdf`)
  - `category`: `Maintenance`
  - `department`: `Machining`
- **Expected Status**: `202 Accepted`
- **Expected Response**:
```json
{
  "success": true,
  "message": "Document registered and queued for ingestion.",
  "data": {
    "document": {
      "id": "d883a82d-bb32-4f60-b9d8-f17294eb1c97",
      "title": "Arihant-Chougule-02-11-26",
      "category": "Maintenance",
      "department": "Machining",
      "status": "pending"
    },
    "job_id": "e23bc462-2ed8-4507-b066-d6e81677d745",
    "status": "pending"
  }
}
```
> **Important Note on IDs**:
> - `data.document.id`: Unique ID of the created SOP Document entity.
> - `data.job_id`: Unique ID of the asynchronous Ingestion Job.
> 
> *(Note: If you re-upload the exact same PDF without changes, the system returns `409 Conflict` because SHA-256 deduplication detects duplicate files).*

---

### Step 10: Check Ingestion Job Status
Polls background task progress.

> **Flexible ID Resolution**:
> You can pass **either** the `job_id` (`e23bc462-...`) **or** the `document_id` (`d883a82d-...`) directly in the URL! Both resolve to the correct ingestion status.

- **Method**: `GET`
- **URL**: `{{base_url}}/ingestion/jobs/{{job_id}}` (or `{{base_url}}/ingestion/jobs/{{document_id}}`)
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "id": "e23bc462-2ed8-4507-b066-d6e81677d745",
    "document_id": "d883a82d-bb32-4f60-b9d8-f17294eb1c97",
    "status": "completed",
    "progress_percent": 100,
    "current_stage": "completed",
    "error_message": null,
    "retry_count": 0,
    "started_at": "Wed, 11 Nov 2026 18:28:25 GMT",
    "completed_at": "Wed, 11 Nov 2026 18:28:48 GMT"
  }
}
```

---

### ⚙️ Background Worker (Celery & Upstash Redis)

When you upload a document:
1. The **Flask API** saves the file, inserts the pending job in PostgreSQL, and pushes a task message to your Upstash Redis queue.
2. The **Celery Background Worker** pulls that task from Redis and performs the heavy extraction, OCR, chunking, and vector embedding.
3. Once the worker finishes processing, the task is marked `completed` in PostgreSQL, and Redis removes the consumed message from the queue.

To run the background worker during local development, open a **second terminal**:
```bash
# In a new terminal window:
.venv\Scripts\activate
celery -A app.tasks.celery_app.celery worker --loglevel=info --pool=solo
```
*(On Windows, `--pool=solo` is required because Windows does not support Unix process forking).*
```json
{
  "success": true,
  "data": {
    "job_id": "c19b024f-...",
    "document_id": "83db102e-...",
    "status": "completed",
    "progress_percentage": 100,
    "error_message": null
  }
}
```

---

### Step 11: Grounded RAG Chat Query (`POST /chat`)
Executes hybrid retrieval (pgvector + FTS + RRF), cross-encoder reranking, and calls the live LLM (Groq) to generate type-safe structured blocks.

#### Test Query A: Numerical Threshold Grounding (SOP-305)
- **Method**: `POST`
- **URL**: `{{base_url}}/chat`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
  - `Content-Type`: `application/json`
- **Body** (raw JSON):
```json
{
  "query": "What is the maximum operating pressure for the hydraulic press in SOP-305?"
}
```
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "answerable": true,
    "confidence_score": 0.99,
    "response": {
      "blocks": [
        {
          "type": "markdown",
          "content": "The maximum allowable operating pressure for the hydraulic stamping press (Unit HP-200) is **180 bar (2600 PSI)**."
        },
        {
          "type": "callout",
          "variant": "warning",
          "title": "Pressure Threshold Warning",
          "content": "Do not exceed 180 bar. Operating above limits risks hydraulic line rupture.",
          "source_ids": ["source_1"]
        }
      ]
    },
    "sources": [
      {
        "id": "source_1",
        "document_id": "e402bc89-...",
        "document_title": "Hydraulic Stamping Press Safety and Operating Procedure",
        "page_number": 1,
        "section": "SECTION 1: MACHINE SPECIFICATIONS",
        "snippet": "Operating limits: Maximum hydraulic operating pressure: 180 bar (2600 PSI)..."
      }
    ],
    "warnings": [],
    "unsupported_claims": [],
    "contradictions_detected": []
  }
}
```

---

#### Test Query B: Safety Critical PPE Retrieval (SOP-101)
- **Method**: `POST`
- **URL**: `{{base_url}}/chat`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
  - `Content-Type`: `application/json`
- **Body** (raw JSON):
```json
{
  "query": "What PPE is required before performing CNC spindle maintenance?"
}
```
- **Expected Status**: `200 OK`
- **Expected Grounded Content**: Returns `safety glasses with side shields`, `hearing protection (minimum NRR 25 dB)`, `steel-toe boots`, with a warning never to wear gloves around rotating machinery, citing `source_1` from *CNC Spindle Maintenance*.

---

#### Test Query C: Out-of-Domain Abstention Test
Tests the zero-hallucination policy when a query is irrelevant or unsupported by the documents.

- **Method**: `POST`
- **URL**: `{{base_url}}/chat`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
  - `Content-Type`: `application/json`
- **Body** (raw JSON):
```json
{
  "query": "  "
}
```
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "answerable": false,
    "confidence_score": 0.0,
    "response": {
      "blocks": [
        {
          "type": "callout",
          "variant": "warning",
          "title": "Insufficient Document Grounding",
          "content": "No relevant standard operating procedure documents were found matching your query."
        },
        {
          "type": "markdown",
          "content": "**Safety Policy Enforcement:**\n\nBiztelAI Copilot strictly prevents hallucinating machinery operating parameters or procedures without direct evidence."
        }
      ]
    },
    "sources": [],
    "warnings": [
      "Abstained from answering due to insufficient source documentation."
    ]
  }
}
```

---

### Step 12: Stream Grounded Answer via SSE (`POST /chat/stream`)
Streams answer blocks via Server-Sent Events (`text/event-stream`).

- **Method**: `POST`
- **URL**: `{{base_url}}/chat/stream`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
  - `Content-Type`: `application/json`
  - `Accept`: `text/event-stream`
- **Body** (raw JSON):
```json
{
  "query": "What is the ISO-9001 tolerance limit for caliper calibration?"
}
```
- **Expected Status**: `200 OK`
- **Stream Format**: Emits chunks prefixed with `data: {...}`.

---

### Step 13: Generate Guided Procedure (`POST /procedures/generate`)
Transforms an SOP into an interactive sequential procedure with numbered steps.

- **Method**: `POST`
- **URL**: `{{base_url}}/procedures/generate`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
  - `Content-Type`: `application/json`
- **Body** (raw JSON):
```json
{
  "query": "Explain the step-by-step procedure for lockout tagout electrical isolation."
}
```
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "procedure_id": "d109fba2-...",
    "title": "Lockout / Tagout Electrical Isolation Procedure",
    "total_steps": 5,
    "steps": [
      {
        "step_number": 1,
        "title": "Operator Notification",
        "description": "Notify affected machine operators and plant supervisors before initiating shutdown.",
        "status": "pending",
        "source_ids": ["source_1"]
      },
      {
        "step_number": 2,
        "title": "Machine Shutdown",
        "description": "Turn off local machine operating switch and allow moving parts to coast to rest.",
        "status": "pending",
        "source_ids": ["source_1"]
      },
      {
        "step_number": 3,
        "title": "Main Disconnect Switch",
        "description": "Move to main electrical cabinet E-204 and switch disconnect handle to OFF.",
        "status": "pending",
        "source_ids": ["source_1"]
      },
      {
        "step_number": 4,
        "title": "Padlock and Danger Tag",
        "description": "Affix personal red safety padlock and completed danger tag through lockout hasp.",
        "status": "pending",
        "source_ids": ["source_1"]
      },
      {
        "step_number": 5,
        "title": "Zero Energy Verification",
        "description": "Test conductors using CAT-IV multimeter to confirm zero voltage.",
        "status": "pending",
        "source_ids": ["source_1"]
      }
    ]
  }
}
```
> **Postman Tip**: Save `procedure_id` to `{{procedure_id}}`:
> ```javascript
> var jsonData = pm.response.json();
> pm.environment.set("procedure_id", jsonData.data.procedure_id);
> ```

---

### Step 14: Update Step Progress on Plant Floor
Updates step completion status as an operator completes each action on the machine.

- **Method**: `POST`
- **URL**: `{{base_url}}/procedures/{{procedure_id}}/progress`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
  - `Content-Type`: `application/json`
- **Body** (raw JSON):
```json
{
  "step_number": 1,
  "status": "completed",
  "notes": "Operators in Bay 4 notified at 09:15 AM."
}
```
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "procedure_id": "d109fba2-...",
    "step_number": 1,
    "status": "completed",
    "completed_steps": 1,
    "total_steps": 5,
    "progress_percentage": 20.0
  }
}
```

---

### Step 15: Submit Feedback on Copilot Answer
Records user feedback (thumbs up / thumbs down + comments) for evaluation and continuous learning.

- **Method**: `POST`
- **URL**: `{{base_url}}/feedback`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
  - `Content-Type`: `application/json`
- **Body** (raw JSON):
```json
{
  "query": "What is the maximum operating pressure for the hydraulic press in SOP-305?",
  "rating": 5,
  "is_helpful": true,
  "comment": "Accurate specification retrieved directly from SOP-305 table.",
  "document_id": "{{document_id}}"
}
```
- **Expected Status**: `201 Created`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "feedback_id": "3f820ab1-...",
    "message": "Feedback submitted successfully."
  }
}
```

---

### Step 16: Admin Metrics & Telemetry
Inspects system health, total queries, document counts, and average response latency.
*(Requires login with `admin@biztelai.com`)*

- **Method**: `GET`
- **URL**: `{{base_url}}/admin/metrics`
- **Headers**:
  - `Authorization`: `Bearer {{admin_access_token}}`
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "total_documents": 4,
    "total_chunks": 7,
    "total_users": 3,
    "active_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "reranker_enabled": true
  }
}
```

---

### Step 17: Inspect LLM Provider Status
Verifies active LLM configuration while ensuring API keys remain masked.

- **Method**: `GET`
- **URL**: `{{base_url}}/llm/status`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "provider_base_url": "https://api.groq.com/openai/v1",
    "model_name": "openai/gpt-oss-120b",
    "api_key_configured": true,
    "api_key_masked": "gsk_...hjPu"
  }
}
```

---

### Step 18: Live Test LLM Connection
Triggers a live ping to the LLM endpoint to measure response latency.

- **Method**: `POST`
- **URL**: `{{base_url}}/llm/test-connection`
- **Headers**:
  - `Authorization`: `Bearer {{access_token}}`
- **Expected Status**: `200 OK`
- **Expected Response**:
```json
{
  "success": true,
  "data": {
    "status": "connected",
    "provider_base_url": "https://api.groq.com/openai/v1",
    "model_name": "openai/gpt-oss-120b",
    "latency_ms": 350.2
  }
}
```

---

### Step 19: Interactive Swagger Documentation
Explore and test all endpoints visually directly from your browser.

- **URL**: `http://localhost:5000/api/v1/docs`
- **OpenAPI 3.0 JSON**: `http://localhost:5000/api/v1/docs/openapi.json`


# BiztelAI Manufacturing SOP AI Copilot — REST API Documentation

All API routes are versioned under the `/api/v1` prefix. Interactive Swagger UI is hosted at `http://localhost:5000/api/v1/docs`.

---

## 1. Standard Error Envelope
All error responses adhere to the unified JSON schema:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed.",
    "details": [
      {
        "field": "email",
        "issue": "Invalid email address format"
      }
    ]
  },
  "request_id": "req-98fbc120a3"
}
```

---

## 2. Authentication Endpoints

### `POST /api/v1/auth/register`
Create a new user account.
- **Request Body**:
```json
{
  "email": "supervisor@plant1.biztel.ai",
  "password": "StrongPassword123!",
  "first_name": "Rajesh",
  "last_name": "Kumar",
  "role": "supervisor",
  "department": "Machining"
}
```
- **Response `201 Created`**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "18f0db2b-...",
      "email": "supervisor@plant1.biztel.ai",
      "role": "supervisor",
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

### `POST /api/v1/auth/login`
Authenticate existing user and issue JWT access/refresh tokens.

### `POST /api/v1/auth/refresh`
Rotate expired access token using refresh token in `Authorization: Bearer <refresh_token>` header.

### `GET /api/v1/auth/me`
Retrieve currently authenticated user identity and permissions.

---

## 3. Document Management Endpoints

### `POST /api/v1/documents/upload`
Upload a new manufacturing PDF SOP document.
- **Headers**: `Authorization: Bearer <access_token>`, `Content-Type: multipart/form-data`
- **Form Fields**:
  - `file`: PDF file binary (validated magic byte `%PDF-`)
  - `category`: (optional, e.g., `Maintenance`, `Safety`, `Quality`)
  - `department`: (optional, e.g., `Machining`, `Stamping`)
- **Response `202 Accepted`**:
```json
{
  "success": true,
  "data": {
    "document_id": "76d8b9e1-...",
    "job_id": "31bfa24e-...",
    "title": "CNC Spindle Maintenance",
    "status": "pending",
    "message": "PDF uploaded and ingestion job enqueued."
  }
}
```

### `GET /api/v1/documents`
List indexed documents with pagination and category filtering.
- **Query Params**: `page=1`, `per_page=20`, `category=Maintenance`

### `GET /api/v1/ingestion/jobs/{job_id}`
Check status and progress percentage of an asynchronous ingestion task.

---

## 4. Chat & Grounded QA Endpoints

### `POST /api/v1/chat`
Execute a grounded RAG query.
- **Request Body**:
```json
{
  "query": "What is the maximum operating pressure for the hydraulic press in SOP-305?",
  "conversation_id": "optional-uuid",
  "category_filter": "Operations"
}
```
- **Response `200 OK`**:
```json
{
  "success": true,
  "data": {
    "answerable": true,
    "confidence_score": 0.96,
    "response": {
      "blocks": [
        {
          "type": "markdown",
          "content": "According to SOP-305, the maximum allowable hydraulic operating pressure for the 200-ton stamping press is **180 bar (2600 PSI)**."
        },
        {
          "type": "callout",
          "variant": "warning",
          "title": "Pressure Threshold Alert",
          "content": "Operating the press beyond 180 bar activates the relief bypass and causes premature seal failure.",
          "source_ids": ["source_1"]
        }
      ]
    },
    "sources": [
      {
        "id": "source_1",
        "document_id": "76d8b9e1-...",
        "document_title": "Hydraulic Stamping Press Safety and Operating Procedure",
        "page_number": 1,
        "snippet": "Operating limits: Maximum hydraulic operating pressure: 180 bar (2600 PSI)...",
        "section": "SECTION 1: MACHINE SPECIFICATIONS"
      }
    ],
    "warnings": [],
    "unsupported_claims": [],
    "contradictions_detected": []
  }
}
```

### `POST /api/v1/chat/stream`
Stream answer blocks via Server-Sent Events (SSE) with `text/event-stream`.

---

## 5. Guided Procedure Execution

### `POST /api/v1/procedures/generate`
Generate an interactive step-by-step procedure from an SOP.
- **Request Body**:
```json
{
  "query": "Explain step-by-step Lockout Tagout sequence for electrical cabinet E-204"
}
```
- **Response `200 OK`**: Returns `procedure_execution_id` and numbered steps.

### `POST /api/v1/procedures/{procedure_id}/progress`
Update completion status of a procedural step on the plant floor.
- **Request Body**:
```json
{
  "step_number": 1,
  "status": "completed",
  "notes": "Padlock #42 affixed to disconnect switch."
}
```


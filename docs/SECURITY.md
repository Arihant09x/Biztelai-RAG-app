# BiztelAI Manufacturing SOP AI Copilot — Application Security

## 1. Authentication & Session Security
- **Algorithm**: JWT tokens signed using HS256 with strong entropy secret (`JWT_SECRET_KEY`).
- **Token Expiry**: Short-lived access tokens (60 minutes default) combined with long-lived refresh tokens (30 days default).
- **Password Hashing**: Bcrypt with salted rounds (`gensalt()`).
- **Secret Masking**: All logs and diagnostics mask API keys, database connection strings, and tokens.

---

## 2. Role-Based Access Control (RBAC)
Four standard manufacturing roles are enforced via the `@require_role` decorator:
- `admin`: Full system configuration, metric inspection, evaluation benchmarks, and user management.
- `supervisor`: Upload, re-index, and soft-delete SOP documents; full chat and procedure generation access.
- `operator`: Read-only access to search SOPs, execute guided procedures, and submit feedback. Cannot upload or delete documents.
- `auditor`: Read-only access to audit logs, compliance records, and evaluation runs.

---

## 3. Input Validation & Content Sanitization
- **PDF Signature Check**: Every uploaded file must begin with `%PDF-` magic bytes; file extensions and MIME headers from clients are never trusted blindly.
- **Path Traversal Protection**: Storage filenames are sanitized using secure random UUIDs; uploaded filenames are sanitized to prevent directory escape attacks (`../`).
- **Prompt Injection Defense**: Text extracted from SOPs is scanned and neutralized against instruction hijack attempts before injecting into context windows.

---

## 4. Audit Logging
Every security-relevant operation creates an immutable entry in the `audit_logs` table:
- Action type (`LOGIN`, `DOCUMENT_UPLOAD`, `DOCUMENT_DELETE`, `REPROCESS`, `PROCEDURE_UPDATE`)
- User ID and IP address
- Target entity ID
- Timestamp


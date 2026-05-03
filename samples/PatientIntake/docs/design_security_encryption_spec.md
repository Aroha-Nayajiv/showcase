# Encryption Specification

## Encryption Specification for Patient Intake System

### 1. Overview
This document defines the REST API contracts that enforce field-level encryption for all patient-intake operations. All endpoints are versioned under /api/v1/ and require JWT-RS256 bearer tokens. Encryption of PHI fields is performed using AES-256-GCM via PostgreSQL pgcrypto. The API layer encrypts inbound payloads before persisting and decrypts only for authorized roles.

### 2. API Endpoints
| Endpoint | Method | Purpose | Request Schema | Response Schema | Auth |
|----------|--------|---------|----------------|-----------------|------|
| /api/v1/intake | POST | Submit new patient intake record | { "patient_id": "uuid", "demographics": { "first_name": "string", "last_name": "string", "dob": "date", "ssn_encrypted": "string" }, "insurance": { "provider": "string", "policy_number_encrypted": "string" }, "medical_history_encrypted": "string" } | { "record_id": "uuid", "status": "string", "created_at": "datetime" } | Bearer Token |
| /api/v1/intake/{record_id} | GET | Retrieve encrypted intake record (authorized roles only) | - | { "record_id": "uuid", "demographics": { "first_name_encrypted": "string", "last_name_encrypted": "string", "dob_encrypted": "string", "ssn_encrypted": "string" }, "insurance": { "provider_encrypted": "string", "policy_number_encrypted": "string" }, "medical_history_encrypted": "string", "audit": { "last_accessed": "datetime", "accessed_by": "string" } } | Bearer Token |
| /api/v1/intake/{record_id}/export | GET | Generate PDF summary with watermark and access timestamp | - | { "pdf_url": "string", "expires_at": "datetime" } | Bearer Token; All request and response fields that contain PHI are suffixed _encrypted and must be base64-encoded ciphertext. |

### 3. Schemas
SCH-001 – PatientIntakeRequest (JSON schema omitted for brevity)
SCH-002 – PatientIntakeResponse (JSON schema omitted for brevity)
SCH-003 – IntakeRetrievalResponse (JSON schema omitted for brevity)
SCH-004 – PdfExportResponse (JSON schema omitted for brevity)

### 4. Error Taxonomy (per endpoint)
| Error Code | HTTP Status | Description | User Message | Retryable? | Applies To |
|-----------|--------------|------------|--------------|------------|------------|
| ERR-001 | 400 | Validation failed – missing required field | Invalid request data. | false | All endpoints |
| ERR-002 | 401 | Authentication failed – invalid or expired JWT | Authentication required. | false | All endpoints |
| ERR-003 | 403 | Authorization failure – role lacks permission | Access denied. | false | GET /intake/{id}, GET /intake/{id}/export |
| ERR-004 | 404 | Record not found | Intake record not found. | false | GET /intake/{id} |
| ERR-005 | 429 | Rate limit exceeded | Too many requests, please retry later. | true | All endpoints |
| ERR-006 | 500 | Encryption service unavailable | Internal server error. | true | POST /intake, GET /intake/{id}, GET /intake/{id}/export |
| ERR-007 | 502 | PDF generation failure | PDF generation failed, please retry. | true | GET /intake/{id}/export |

### 5. Security Considerations
- Authentication – JWT signed with RS256; public key distributed via internal JWKS endpoint.
- Authorization – Role-based access control (admin, clinician, front-desk) enforced by middleware; only admin and clinician may retrieve or export PDFs (FR-002).
- Transport Encryption – All traffic must use TLS 1.3; server enforces Strict-Transport-Security.
- Field-Level Encryption – Client encrypts sensitive fields using a per-session AES-256-GCM key that is itself encrypted with the service’s master key stored in HashiCorp Vault. The backend stores only ciphertext.
- Audit Logging – Every read/write operation writes an entry to audit_log table with user_id, action, timestamp, and resource_id. Logs are immutable and retained for 7 years (KPI-003). The PDF export endpoint also logs an audit entry with operation = "EXPORT_PDF".
- Rate Limiting – API gateway enforces 100 requests per minute per user (KPI-023) and returns ERR-005 on excess.
- Pagination – List endpoints (e.g., future /api/v1/intake) support limit/offset query parameters with default limit=50.
- Secrets Management – Database credentials are injected via Docker secrets (e.g., /run/secrets/db_user, /run/secrets/db_password) and never hard-coded.

### 6. Integration Points & Failure Handling
- Vault – If Vault is unreachable, the API returns ERR-006 with retryable flag; requests are queued for later processing.
- PDF Generator (WeasyPrint) – PDF generation failures return ERR-007; client may retry up to three times.
- PostgreSQL pgcrypto – Encryption errors propagate as ERR-006; transaction is rolled back.

### 7. Traceability
- EP-001 maps to FR-001 (latency) and FR-002 (RBAC).
- SCH-001 fields correspond to REQ-001 (WCAG) for input validation and REQ-006 (AES-256-GCM) for encryption.
- ERR-003 aligns with NIST AC-3 and HIPAA §164.312(a)(1) for access control.

### 8. PostgreSQL Data Model
#### 8.1 Tables
**patient_intake**
| Column | Data Type | Required | Encryption | Description |
|---|---|---|---|---|
| id | uuid | Yes | No | Primary key generated by gen_random_uuid() |
| created_at | timestamptz | Yes  No | Record creation timestamp |
| created_by  text  Yes  No  Service account identifier | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- … (table continues) …|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…|…… |
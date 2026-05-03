# Presentation Architecture Specification

## High-Level Architecture Diagram

1. Overview
The PatientIntake system is organized as a set of loosely‑coupled micro‑services deployed via Docker Compose on an air‑gapped host. All network traffic is confined to an internal Docker overlay network; no external internet access is required. This architecture satisfies FR-001 (sub‑second response), FR-009 (air‑gapped Docker Compose), and related KPIs.

2. Frontend (Web UI)
Technology: React 18 with TypeScript, bundled by Vite.
Serves static assets over HTTPS (TLS 1.3) using Caddy as a reverse‑proxy.
Performs client‑side field‑level encryption using crypto‑js AES‑256‑GCM before sending PHI to the API gateway (supports REQ-001 WCAG compliance).
State management via Redux Toolkit; routes defined with React Router v6.
Accessibility: WCAG 2.1 AA compliance enforced through eslint-plugin-jsx-a11y.

3. API Gateway (FR-002, REQ-006)
Implemented with FastAPI (Python 3.11) behind Caddy TLS termination.
Authenticates requests using JWT signed with RS256 (see EP‑001). Role claims enforce RBAC per FR-002.
Validates incoming JSON against OpenAPI schemas (SCH‑001) and forwards authorized calls to backend services over the internal Docker network.
Rate limiting (100 req/s per IP) enforced by slowapi middleware to satisfy NFR‑009 and KPI‑001 (form submission latency <200 ms).

4. Intake Service (FR-001, FR-002, REQ-003)
Core business logic for patient record creation, update, and retrieval.
Persists encrypted fields using PostgreSQL pgcrypto aes_gcm_encrypt; encryption keys loaded from Docker secrets (`/run/secrets/enc_key`).
Enforces role‑based access control via PostgreSQL Row‑Level Security policies (RLS) defined in FR‑002.
Emits domain events (PatientCreated, PatientUpdated) to the Event Bus.

5. Audit Logger Service (FR-003, KPI-003)
Subscribes to domain events and writes immutable audit entries to PostgreSQL table `audit_log`.
Each entry records event_id, user_id, timestamp, operation, record_id, and a cryptographic hash of the payload.
Retention policy: 7 years, enforced by a nightly vacuum job.
Provides a read‑only API endpoint for compliance reporting, protected by RBAC.

6. PDF Generator Service (FR-008, KPI-030, KPI-046)
Generates PDF intake summaries using WeasyPrint (Python).
Receives a signed request containing patient ID; fetches encrypted data via the Intake Service, decrypts in‑memory, renders an HTML template, and converts to PDF.
Watermark includes exporting user ID, timestamp, and a SHA‑256 hash of the PDF content to satisfy FR‑008 and KPI‑030.
Access limited to roles clinician and admin; unauthorized attempts are logged and return ERR‑003.
Performance KPI added: PDF generation latency must be ≤500 ms (KPI‑046).

7. PostgreSQL Database (FR-002, REQ-007)
Single instance running in a Docker container with `--read-only` flag for the filesystem except for the data volume.
Uses pgcrypto for field‑level encryption and RLS for row‑level security.
Connection enforced over TLS with client certificates stored as Docker secrets.

8. Event Bus (FR-002)
Implemented with NATS JetStream for reliable at‑least‑once delivery of domain events.
Services subscribe via lightweight Python clients; failure to deliver triggers exponential back‑off and dead‑letter queue.

9. Security Controls (FR-001, FR-002, FR-003)
TLS 1.3 end‑to‑end encryption for all HTTP traffic.
Secrets managed exclusively via Docker secrets; no plaintext passwords in compose files.
Regular vulnerability scanning using Trivy CI step (outside scope of this artifact).
Audit log integrity verified daily by comparing stored hash with recomputed hash.

10. Compliance Checks (FR-001‑FR-009)
All components are open‑source and version‑pinned to known‑good releases (React 18.2.0, FastAPI 0.95, PostgreSQL 15).
HIPAA technical safeguard references: 45 CFR 164.312(a)(2)(iv) for encryption, 45 CFR 164.312(b) for audit controls.
KPIs monitored: form submission latency <200 ms (KPI‑001), audit log completeness 100 % (KPI‑003), PDF watermark accuracy 100 % (KPI‑030), PDF generation latency ≤500 ms (KPI‑046).

### 1. Authentication & Authorization
Auth Method: Bearer token (`Authorization: Bearer <jwt>`)
JWT Claims: sub (user ID), role (admin|clinician|front_desk), exp, iat
Roles:
- admin: full CRUD, audit view, PDF export
- clinician: read/write patient records, export PDF
- front_desk: create records, read limited fields, no export
Token Validation: RS256 signature verification against the public key mounted as a Docker secret.

### 3. Schemas

#### SCH‑INTAKE‑REQ (JSON)
{"patient_id": "string", "demographics": {"first_name": "string", "last_name": "string", "date_of_birth": "string", "gender": "string", "address": {"line1": "string", "city": "string", "state": "string", "zip": "string"}}, "insurance": {"provider": "string", "policy_number": "string", "group_number": "string"}, "medical_history": {"allergies": ["string"], "past_diagnoses": ["string"]}, "consent_timestamp": "string"}

#### SCH‑INTAKE‑RESP (JSON)
{"intake_id": "string", "status": "string", "created_at": "string", "message": "string"}

#### SCH‑PDF‑RESP (JSON)
{"pdf_url": "string", "checksum": "string", "generated_at": "string"}

### 4. Error Taxonomy (enhanced)
| Code | HTTP | Type | Description | Message | Retryable |
|------|------|------|-------------|---------|----------|
| ERR-001 | 400 | ValidationError | Request payload fails schema validation | "Please correct the highlighted fields." | false |
| ERR-002 | 401 | AuthenticationFailed | Missing or invalid JWT | "Authentication required." | false |
| ERR-003 | 403 | AuthorizationFailed | Role does not permit operation | "You do not have permission to perform this action." | false |
| ERR-004 | 404 | ResourceNotFound | patient_id does not exist | "Requested patient record not found." | false |
| ERR-005 | 500 | InternalServerError | Unexpected condition | "An unexpected error occurred. Please try again later." | true |
| ERR-006 | 504 | TimeoutError | PDF generation exceeded KPI‑046 limit | "PDF generation timed out." | true |

### 5. Traceability to Requirements (added)
- FR-001 – Sub‑second response time satisfied by rate limiting and efficient DB indexing.
- FR-002 – Role‑based access enforced via JWT role claim and PostgreSQL RLS.
- FR-003 – Full audit logging implemented as described in section 5.
- FR-006 – Confirmation receipt returned in SCH‑INTAKE‑RESP.message within 1 second.
- FR-008 – PDF watermark includes user ID, timestamp, and SHA‑256 hash.
- FR-009 – Docker Compose deployment uses only open‑source images; no external cloud services referenced.
- REQ-001 – WCAG 2.1 AA compliance for UI components.
- REQ-002 – Keyboard navigation without mouse required.
- REQ-003 – ARIA labels for all non‑text UI elements.
- REQ-006 – Encryption algorithm AES‑256‑GCM specified.
- REQ-007 – JWT signed with RS256 algorithm.
- REQ-008 – AES‑256‑GCM key rotation policy defined.
- KPI-001 – Form submission latency <200 ms.
- KPI-003 – Audit log completeness 100 %.
- KPI-030 – PDF watermark accuracy 100 %.
- KPI-046 – PDF generation latency ≤500 ms.

### 5.2 Insurance Table
| Field | Data Type | Required | Description |
|---|---|---|---|
| id | UUID PRIMARY KEY DEFAULT gen_random_uuid() | Yes | Unique insurance record identifier |
| patient_id | UUID REFERENCES patient(id) ON DELETE CASCADE | Yes | Links to patient |
| provider_name | TEXT ENCRYPTED USING pgcrypto (AES‑256‑GCM) \u2013 encrypted at rest \u2013 AES‑256‑GCM) \u2013 encrypted at rest \u2013 AES‑256‑GCM) \u2013 encrypted at rest \u2013 AES‑256‑GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest \u2013 AES‑256-GCM) \u2013 encrypted at rest	Yes	Insurance provider name |
| policy_number | TEXT 	Yes	Policy number |
| group_number | TEXT 	No	Group number if provided |
| effective_date | DATE 	Yes	Coverage start date |
| expiration_date | DATE 	Yes	Coverage end date |
| created_at | TIMESTAMP WITH TIME ZONE DEFAULT now() 	Yes	Timestamp |

### 5.3 Medical History Table
| Field | Data Type | Required | Description |
|---|---|---|---|
| id | UUID PRIMARY KEY DEFAULT gen_random_uuid() 	Yes	Unique identifier |
| patient_id 	UUID REFERENCES patient(id) ON DELETE CASCADE	Yes	Links to patient |
| condition_code 	TEXT	Yes	Standardized ICD‑10 code |
| description 	TEXT	No	Free‑text description |
| onset_date 	DATE	No	When condition began |
| resolved_date 	DATE	No	When condition resolved |
| created_at 	TIMESTAMP WITH TIME ZONE DEFAULT now()	Yes	Timestamp |

## 6. Audit Logging Service Contract

### 6.1 Overview
The Audit Logging Service (ALS) records every INSERT, UPDATE, DELETE, and SELECT operation on core tables to satisfy HIPAA §164.312(b) and project FR‑003. Logs are immutable, append‑only, retained for seven years (FR‑003) and indexed for fast retrieval (KPI‑003).

### 6.2 API Endpoints
- **POST /api/v1/audit/events** – Create a new audit event.
  - Request JSON: {"event_type":"string","user_id":"uuid","record_id":"uuid","resource":"string","timestamp":"ISO8601","details":{}}.
  - Response JSON: {"event_id":"uuid","status":"created"}.
  - Errors: 400 Bad Request (validation), 401 Unauthorized, 500 Internal Server Error.
- **GET /api/v1/audit/events** – Query events with optional filters (resource, user_id, start_time, end_time, event_type).
  - Response JSON: {"events":[{...}]}. Errors as above.
- **GET /api/v1/audit/events/{event_id}** – Retrieve a single event.
  - Response JSON: full event object. Errors: 404 Not Found, 401 Unauthorized.
All endpoints require Bearer JWT signed with RS256.

### 6.3 Data Model
| Field | Type | Required | Description |
|---|---|---|---|
| event_id | UUID PRIMARY KEY DEFAULT gen_random_uuid() 	Yes	Unique identifier |
| event_type 	VARCHAR(32) CHECK (event_type IN ('READ','WRITE','EXPORT','DELETE')) 	Yes	Type of operation |
| user_id 	UUID NOT NULL 	Yes	Actor identifier |
| record_id 	UUID NOT NULL 	Yes	Affected patient record |
| resource 	VARCHAR(64) NOT NULL 	Yes	Logical resource name (e.g., patient_intake) |
| timestamp 	TIMESTAMPTZ NOT NULL DEFAULT now() 	Yes	UTC time of event |
| details 	JSONB NULL 	No	Optional context |
| hash 	CHAR(64) NOT NULL 	Yes	SHA‑256 hash of concatenated fields for tamper‑evidence |

### 6.4 Integration & Failure Handling
- **Database Unavailability** – ALS returns HTTP 503 with error code ERR‑004; caller must retry with exponential back‑off (max 5 attempts).
- **Kafka Publishing Failure** – Event is persisted; ALS returns success to caller and queues async retry; failures are logged to a local file.
- **Observability** – Prometheus metrics: audit_requests_total, audit_errors_total, audit_latency_seconds (histogram).
- **Integrity Verification** – Daily job recomputes hashes and alerts on mismatches.

## 8. Performance & Indexing
- Primary keys are UUIDs generated by gen_random_uuid().
- B‑tree indexes on patient.last_name, insurance.provider_name, medical_history.condition_code.
- GIN index on audit_log.details_jsonb for efficient JSON queries.
- Monthly partitioning on audit_log improves query performance and retention management.

## Technical Design Document

### 10. API Specification

#### 10.1 Export PDF Endpoint
**POST /api/v1/patients/{patient_id}/export/pdf**

{
  "request_id": "string (UUID)",
  "patient_id": "string (UUID)",
  "format": "html",
  "options": {
    "include_header": true,
    "include_footer": true
  }
}

**Response (200)**

{
  "export_id": "string (UUID)",
  "pdf_base64": "string",
  "watermark_text": "string",
  "export_timestamp": "string (ISO‑8601)"
}

**Error Responses**
| Code | HTTP Status | Description | User Message | Retryable? |
|------|-------------|-------------|--------------|------------|
| ERR-001 | 401 | Invalid or missing JWT token. | Authentication required. | No |
| ERR-002 | 403 | Insufficient role for PDF export. | You do not have permission to export this record. | No |
| ERR-003 | 404 | Patient record not found. | The requested patient does not exist. | No |
| ERR-004 | 500 | PDF generation failure (library error). | An internal error occurred while creating the PDF. | Yes |
| ERR-005 | 429 | PDF generation latency exceeded threshold. | Service temporarily unavailable; please retry later. | Yes |

#### 10.2 Audit Log Event (internal)
**Event:** PdfExported
Payload: `{ "patient_id": "UUID", "user_id": "UUID", "timestamp": "ISO‑8601", "watermark_hash": "SHA256" }`
Emitted by PdfExportService and consumed by AuditLogService.

### 11. Service Boundaries
| Service | Responsibility | Dependencies | Events Emitted | Events Consumed |
|---------|----------------|--------------|----------------|----------------|
| PdfExportService | Generate PDF, apply watermark, log export event. | WeasyPrint (HTML→PDF), PostgreSQL, JWT verifier, RSA signing key. | PdfExported (patient_id, user_id, timestamp) | None |
| AuditLogService | Persist immutable audit records for all export actions. | PostgreSQL, pgcrypto for field‑level encryption. | AuditRecordCreated | PdfExported |

### 12. Security Considerations
- **Authentication:** JWT signed with RS256; token includes `sub` (user UUID) and `role` claim. Verified at API gateway.
- **Authorization:** RBAC policy permits only `admin` and `clinician` roles for the export endpoint; `front_desk` receives 403 (ERR-002).
- **Transport Encryption:** All endpoints require HTTPS with TLS 1.3; cipher suites limited to TLS_AES_256_GCM_SHA384 and TLS_CHACHA20_POLY1305_SHA256.
- **At‑Rest Encryption:** `watermark_text` column encrypted with pgcrypto AES‑256‑GCM; PDF binary stored in object storage with server‑side encryption.
- **Watermark Integrity:** Watermark text is signed with RSA‑2048; signature verified by downstream audit tools using the public key stored in the `keys` secret.
- **Key Management:** Master encryption key stored as Docker secret `encryption_key`; rotated quarterly via secret update workflow.
- **Audit Logging:** Immutable append‑only `audit_log` table; triggers prevent UPDATE/DELETE; entries signed with HMAC‑SHA256 using secret `log_hmac_key`. Retention: 7 years on separate volume.

### 13. Acceptance Criteria
1. **Successful Export** – Authorized request returns HTTP 200 with a Base64‑encoded PDF and correct `watermark_text`.
2. **Watermark Verification** – Watermark contains exact `user_id` and ISO‑8601 timestamp; verification script checks both components and validates RSA signature.
3. **Authorization Enforcement** – Requests from users without `admin` or `clinician` role receive HTTP 403 with ERR‑002.
4. **Authentication Enforcement** – Missing or malformed JWT returns HTTP 401 with ERR‑001.
5. **Performance** – PDF generation latency ≤ 500 ms for average payload (≤ 2 MB HTML). Exceeding latency returns HTTP 429 with ERR‑005 (retryable).
6. **Audit Completeness** – Every export action creates a record in `PdfExportLog` with encrypted `watermark_text` and immutable `export_timestamp`; corresponding `PdfExported` event is persisted in `audit_log`.
7. **Content Type** – Response header `Content-Type: application/pdf`; filename follows pattern `patient-{patient_id}-export-{timestamp}.pdf`.
8. **KPI Alignment** – Export latency meets KPI‑030 (watermark accuracy 100%); audit log completeness meets KPI‑003 (100% of export events recorded).
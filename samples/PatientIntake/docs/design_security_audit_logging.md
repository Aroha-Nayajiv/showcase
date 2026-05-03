# Audit Logging Specification

## High-Level Architecture Diagram and Component Boundaries

1. Overview
The PatientIntake system is organized as a set of loosely‑coupled micro‑services deployed via Docker Compose on an air‑gapped on‑premise host. All network traffic is confined to an internal Docker overlay network and encrypted with TLS 1.3. The diagram below (textual representation) shows the primary components and their interfaces:

[Web Browser] <--HTTPS--> [Frontend SPA] <--HTTP/2--> [API Gateway] <--gRPC/HTTPS--> [Intake Service]
 |; +---> [Audit Logger Service] |
; +---> [Auth Service (JWT RS256)] |
; +---> [PostgreSQL DB (pgcrypto, RLS)] |

2. Component Boundaries
- Frontend SPA (React, WCAG 2.1 AA compliant) renders the patient intake form, performs client‑side field‑level encryption using AES‑256‑GCM, and obtains a short‑lived JWT from the Auth Service.
- API Gateway (Traefik) terminates TLS, validates JWT signatures (RS256), routes requests to downstream services, and enforces rate limiting (100 req/s per IP) and request size limits.
- Intake Service implements `POST /api/v1/intake` to receive encrypted payloads, writes field‑encrypted columns via PostgreSQL pgcrypto functions, emits an IntakeCreated event to the Audit Logger, and exposes a health‑check endpoint `/healthz`.
- PDF Generator Service consumes IntakeCreated events, retrieves the decrypted record via a service‑account role, creates a PDF with WeasyPrint, applies a watermark containing user_id, timestamp, and record_id, then stores the PDF in an immutable object store volume.
- Audit Logger Service writes immutable audit entries to the audit_log table (append‑only, `log_statement = 'all'`). Each entry includes event_id, user_id, action, resource_id, timestamp, and a cryptographic hash of the payload for tamper evidence. It also provides a paginated retrieval endpoint `/api/v1/audit` with `page` and `page_size` parameters.
- Auth Service issues JWTs signed with an RSA‑2048 key pair stored as a Docker secret; token claims include sub, role, and exp.
- PostgreSQL DB runs with pgcrypto enabled, row‑level security policies enforce that only users with role admin or clinician may SELECT patient records, while front_desk may only INSERT. All data at rest is encrypted with AES‑256‑GCM using per‑field keys rotated weekly.

3. Security Controls
- Transport encryption: TLS 1.3 with strong cipher suites.
- Authentication: JWT RS256 validated at gateway and service layers.
- Authorization: Role‑based access control enforced in API layer and PostgreSQL RLS policies (FR-002).
- Data integrity: SHA‑256 hash stored in audit log; PDF watermark includes hash of source record.
- Auditing: Immutable append‑only log, retention 7 years (FR-003).
- Key management: Master key stored in Docker secret; per‑field data keys derived via HKDF.

4. Operational Requirements
- All containers run with --read-only flag except designated writable volumes for PostgreSQL data and PDF output (FR-017).
- Health‑check endpoints (`/healthz`) exposed on each service for orchestration monitoring.
- Logging follows structured JSON format; log aggregation is performed by a local ELK stack running in the same Docker Compose network.

### Endpoint Table
| Endpoint | Method | Purpose | Request Schema | Response Schema | Auth |
|---|---|---|---|---|---|
| /api/v1/intake | POST | Create new patient intake record | IntakeRequest | IntakeResponse | Bearer JWT RS256 |
| /api/v1/audit | GET | Retrieve audit log entries (paginated) | AuditQueryParams | AuditLogPageResponse | Bearer JWT RS256 |
| /healthz | GET | Service health check returning 200 OK when ready | - | HealthResponse | - |

### Audit Log Retrieval Schema

#### AuditQueryParams
{"page": 1, "page_size": 50, "start_timestamp": "string", "end_timestamp": "string"}
#### AuditLogPageResponse
{"total_records": 1234, "page": 1, "page_size": 50, "records": [{"event_id": "string", "user_id": "string", "action": "string", "resource_id": "string", "timestamp": "string", "hash": "string"}]}

## Patient Intake Data Model Specification

### Purpose
This document defines the PostgreSQL relational schema for the Patient Intake system, covering patient demographics, insurance information, medical history, and audit logging. All sensitive fields are encrypted at rest using pgcrypto AES‑256‑GCM (REQ-006) and transmitted over TLS 1.3. The schema enforces role‑based row‑level security (FR-002).

### Schema Overview
Table `intake`:
- intake_id UUID PRIMARY KEY
- patient_id UUID NOT NULL
- demographics JSONB NOT NULL (encrypted)
- insurance JSONB NOT NULL (encrypted)
- medical_history JSONB NOT NULL (encrypted)
- created_at TIMESTAMPTZ NOT NULL DEFAULT now()
- submission_timestamp TIMESTAMPTZ NOT NULL

Table `audit_log`:
- event_id UUID PRIMARY KEY
- user_id UUID NOT NULL
- action TEXT NOT NULL
- resource_id UUID NOT NULL
- timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
- payload_hash BYTEA NOT NULL

Row‑level security policies ensure clinicians can SELECT records for their assigned patients, front_desk can INSERT only, and admins have full access.

### Field Constraints
- All string fields have max length constraints as defined in the API contract.
- Date fields must be past dates.
- Encryption is applied via `pgp_sym_encrypt` with per‑field keys derived from the master key stored in Docker secret `PHI_MASTER_KEY`.

### Tables (primary keys are UUIDs generated by `gen_random_uuid()`)
sql
CREATE TABLE patient (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name text NOT NULL,
  last_name text NOT NULL,
  date_of_birth date NOT NULL CHECK (date_of_birth < CURRENT_DATE),
  ssn bytea NOT NULL DEFAULT pgp_sym_encrypt('', 'pgcrypto_key'),
  address bytea NOT NULL DEFAULT pgp_sym_encrypt('', 'pgcrypto_key')
);

CREATE TABLE insurance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id uuid NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
  provider_name text NOT NULL,
  policy_number bytea NOT NULL DEFAULT pgp_sym_encrypt('', 'pgcrypto_key'),
  group_number bytea NULL DEFAULT pgp_sym_encrypt('', 'pgcrypto_key')
);

CREATE TABLE medical_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id uuid NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
  condition_code text NOT NULL,
  onset_date date NULL,
  notes bytea NULL DEFAULT pgp_sym_encrypt('', 'pgcrypto_key')
);

CREATE TABLE audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type text NOT NULL CHECK (entity_type IN ('patient','insurance','medical_history')),
  entity_id uuid NOT NULL,
  operation text NOT NULL CHECK (operation IN ('INSERT','UPDATE','DELETE','SELECT')),
  performed_by text NOT NULL,
  timestamp_utc timestamptz NOT NULL DEFAULT now() AT TIME ZONE 'UTC',
  details_jsonb jsonb NULL,
  hash_chain text NOT NULL DEFAULT ''
);

### Field‑Level Encryption
Sensitive columns (`ssn`, `address`, `policy_number`, `group_number`, `notes`) are stored encrypted using `pgp_sym_encrypt` with a master key stored as Docker secret `pgcrypto_key`. Decryption occurs only after JWT validation in the service layer.

## Audit Logging Service Contract

### Request/Response Schemas (JSON)

{"type": "object", "properties": {"user_id": {"type": "string"}, "operation": {"type": "string", "enum": ["CREATE", "READ", "UPDATE", "DELETE", "EXPORT"]}, "entity": {"type": "string"}, "entity_id": {"type": "string", "format": "uuid"}, "details": {"type": "object"} }, "required": ["user_id", "operation", "entity", "entity_id"]}

{"type": "object", "properties": {"log_id": {"type": "string", "format": "uuid"}, "status": {"type": "string"}}

{"type": "object", "properties": {"entries": {"type": "array", "items": {"type": "object", "properties": {"log_id": {"type": "string", "format": "uuid"}, "timestamp": {"type": "string", "format": "date-time"}, "user_id": {"type": "string"}, "operation": {"type": "string"}, "entity": {"type": "string"}, "entity_id": {"type": "string", "format": "uuid"}, "hash_chain": {"type": "string"}}}}}, "required": ["entries"]}

### Error Handling (standardized)
All endpoints return HTTP 4xx/5xx with body:

{"error_code":"ERR_VALIDATION","message":"Detailed validation error description"}

Rate‑limit errors use `ERR_RATE_LIMIT`. Pagination errors use `ERR_PAGINATION`.

### Rate Limiting & Pagination
- **Rate‑Limit**: 100 requests/min per client IP. Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. Exceeding returns 429 with `ERR_RATE_LIMIT`.
- **Pagination**: Query parameters `page` (default 1) and `size` (max 100). Response includes `total_pages`, `total_items`.

### Health Check
`GET /api/v1/audit/health` returns `{ "status": "healthy", "uptime_seconds": <int> }`.

## Technical Design Specification for Patient Intake System

### 2. Service Definitions

#### 2.1 API Gateway
| Responsibility | Details |
|---|---|
| Authentication | Validate Bearer JWT signed with RS256; map `sub` claim to `user_id`. |
| Rate Limiting | Global limit 200 req/min per user; per‑endpoint limits defined per service. |
| TLS | Enforce TLS 1.3; mutual TLS for internal calls. |
| Health Check | `/healthz` returns `{"status":"ok"}` with component statuses. |

#### 2.2 Intake Service (SVC-INT-001)
- **Endpoint**: `POST /api/v1/patients`
- **Request Schema (SCH-INTAKE-REQ)**:

{"patient_id":"uuid","payload":{...}}

- **Response**: `201 Created` with location header.
- **Rate Limiting**: 100 req/min per user (to satisfy reviewer feedback).
- **Health Check**: `GET /healthz` returns service status.

#### 2.3 AuditLoggingService (SVC-001)
| Service Name | Responsibility | Dependencies |
|---|---|---|
| AuditLoggingService | Append immutable audit entries, provide query API | PostgreSQL (pgcrypto), Docker secret `ALS_MASTER_KEY`, JWT lib |
| Events Emitted | `AuditEntryCreated` (payload includes `log_id`) |
| Events Consumed | None |

**Table: audit_log**
| Column | Type | Constraints |
|---|---|---|
| log_id | UUID | Primary key, generated by `gen_random_uuid()` |
| audit_log | TIMESTAMPTZ | Default `NOW()`; stored UTC |
| user_id | TEXT | Must match JWT `sub` claim |
| operation | TEXT | Enum [CREATE,READ,UPDATE,DELETE,EXPORT] |
| entity | TEXT | Logical name of target table |
| entity_id | UUID | Identifier of target record |
| details | JSONB | Encrypted with `pgp_sym_encrypt` using master key |
| hash_chain | BYTEA | SHA‑256 hash of previous entry + payload |
| signature | BYTEA | HMAC‑SHA256 using rotating service key |

#### 2.4 PdfExportService (SVC-PDF-EXPORT)
- **Endpoint**: `GET /api/v1/patients/{patient_id}/export/pdf`
- **Request Schema (SCH-PDF-EXPORT-REQ)**:

{"patient_id":"uuid","include_history":true}

- **Response Schema (SCH-PDF-EXPORT-RESP)**:

{"pdf_url":"string","checksum":"string","generated_at":"datetime"}

- **Watermark**: Includes exporting `user_id` and UTC timestamp.
- **Export Metadata Table: PdfExportLog**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| patient_id | UUID | FK to Patient |
| exported_by | UUID | User ID of staff triggering export |
| exported_at | TIMESTAMPTZ | Generation time (used for watermark) |
| checksum | TEXT(64) | SHA‑256 of PDF |
| file_path | TEXT | Server storage location |

#### 2.5 Patient Entity (simplified)
| Field | Type | Constraints |
|---|---|---|
| patient_id | UUID | Primary key |
| name_encrypted | BYTEA | AES‑256‑GCM via `pgp_sym_encrypt` |
| ssn_encrypted | BYTEA | AES‑256‑GCM |
| insurance_number_encrypted | BYTEA | AES‑256‑GCM |
| medical_history_encrypted | BYTEA | AES‑256‑GCM |
| created_at | TIMESTAMPTZ | Default `NOW()` |

#### 2.6 Transport Encryption
All inbound/outbound traffic uses TLS 1.3 with cipher suite `TLS_AES_256_GCM_SHA384`. Mutual TLS is required for service‑to‑service calls.

#### 2.7 At‑Rest Encryption
Sensitive columns are encrypted with `pgp_sym_encrypt` using AES‑256‑GCM keys stored in Vault and wrapped by a master key rotated weekly (REQ‑006).

#### 2.8 Role‑Based Access Control (RBAC)
Roles: `admin`, `clinician`, `front_desk`. Row‑Level Security policies enforce read/write permissions per role.

#### 2.9 Tamper Evidence
Each audit entry includes a hash‑chain (`hash_chain`) and an HMAC signature (`signature`). Integrity checks run quarterly; mismatches trigger alerts.

### 3. Operational Concerns
- **Rate Limiting**: Defined per service as above; exceeds result in `429 Too Many Requests` with retry‑after header.
- **Pagination**: All list endpoints support `limit`/`offset` to handle large data sets.
- **Health Checks**: Each service exposes `/healthz` returning JSON `{ "status": "ok", "components": { ... } }`.
- **Monitoring & Alerts**: Metrics exported to Prometheus; alerts for latency >200 ms, hash‑chain failures, and rate‑limit breaches.

### 4. Error Taxonomy
| Code | HTTP Status | Description | User Message | Retryable |
|---|---|---|---|---|
| ERR-001 | 400 | Invalid request payload – missing required fields | "Missing required field(s)" | No |
| ERR-002 | 401 | Unauthorized – invalid or expired JWT | "Authentication required" | No |
| ERR-003 | 403 | Forbidden – insufficient role | "You do not have permission for this operation" | No |
| ERR-004 | 404 | Resource not found | "The requested resource does not exist" | No |
| ERR-005 | 429 | Rate limit exceeded | "Too many requests, please try later" | Yes |
| ERR-006 | 500 | Internal server error – hash chain verification failed | "Audit service unavailable" | Yes |
| ERR-007 | 500 | PDF generation failure | "An internal error occurred while creating the PDF" | Yes |

### 6. Future Enhancements
- Implement automated key rotation via Vault lease renewal.
- Add audit log export to immutable WORM storage.
- Integrate SIEM alerts for tamper‑evidence violations.

## Technical Design Document

### 7. Architecture
- **Intake Service** – handles patient form submission, validates input, writes encrypted records.
- **Auth Gateway** – validates JWT signed with RS256 (REQ‑007), extracts `role` claim and injects into request context.
- **Audit Service** – immutable append‑only audit_log table with chain‑hashing and HMAC‑SHA256 signatures.
- **Key Management Service** – rotates master encryption key every 30 days.
- **PDF Export Service** – generates PDF via WeasyPrint, adds watermark with user ID and ISO‑8601 timestamp.

All services run as Docker containers with `--read-only` flag; secrets are provided via Docker secrets.

### 8. API Specifications

#### 8.1 Intake API (`POST /api/v1/intake`)
- **Request**

{
  "patient_id": "string",
  "demographics": {"name":"string","dob":"date","insurance":"string"},
  "clinical_data": {"symptoms":"string"}
}

- **Response** `201 Created`

{"receipt_id":"uuid","message":"Submission received"}

- **Errors**
  - `400 Bad Request` – validation failure (error code `ERR-001`).
  - `401 Unauthorized` – missing/invalid JWT (error code `ERR-003`).
  - `429 Too Many Requests` – rate limit exceeded (error code `ERR-010`).
- **Rate Limiting** – 100 requests/min per authenticated user (KPI‑043). Implemented via Envoy sidecar.
- **Health Check** – `GET /healthz` returns `200 OK` with `{"status":"healthy"}`.

#### 8.2 Audit Log Retrieval (`GET /api/v1/audit`)
- **Query Parameters** `page`, `size` (default size=50). Pagination required to avoid large payloads.
- **Response**

{
  "page":1,
  "size":50,
  "total":1234,
  "records":[{"id":"uuid","user_id":"string","action":"READ","object_id":"string","timestamp":"2026-05-03T12:34:56.789Z"}]
}

- **Errors** `401 Unauthorized` (`ERR-003`), `400 Bad Request` for invalid pagination (`ERR-011`).

#### 8.3 PDF Export (`GET /api/v1/export/{record_id}`)
- **Response** – `application/pdf` with watermark containing exporting user ID and timestamp.
- **Errors** `404 Not Found` (`ERR-012`), `401 Unauthorized` (`ERR-003`).

### 9. Data Models
- **PatientRecord** – fields encrypted at rest using AES‑256‑GCM (REQ‑006). Encryption keys stored as Docker secret `master_key`.
- **AuditLog** – immutable table with columns `id UUID`, `user_id`, `action`, `object_id`, `timestamp TIMESTAMP(3)`, `prev_hash VARCHAR`, `hash VARCHAR`. Each entry signed with HMAC‑SHA256 using secret `audit_key`.

### 10. Deployment
Docker Compose file defines services with `read_only: true`, mounts secrets from `/run/secrets/*`, and includes health‑check definitions.

### 11. Compliance Mapping
| Requirement | Implementation |
|---|---|
| FR‑001 (2 s response) | Rate limiting and efficient service design target <200 ms per request (KPI‑02). |
| FR‑002 (RBAC) | Role claim enforcement in Auth Gateway. |
| FR‑003 (audit log) | Immutable audit_log table with chain hashing. |
| FR‑006 (receipt) | Immediate receipt response after successful write. |
| FR‑008 (PDF watermark) | Watermark generated by PDF Export Service. |
| FR‑009 (Docker Compose) | All services defined in compose, no external cloud dependencies. |
| REQ‑006 (AES‑256‑GCM) | Field‑level encryption algorithm. |
| REQ‑007 (JWT RS256) | JWT signing algorithm. |

### 12. Open Issues / Knowledge Gaps
- Exact HIPAA § 164.312(a)(2)(iv) requirements for key management rotation frequency.
- Performance characteristics of PostgreSQL row‑level security for audit_log at >10 M rows.
---
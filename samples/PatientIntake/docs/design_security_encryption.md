# Data Encryption Design (Overview)

## High-Level Architecture Overview

1. Component Boundary Definition
- Web UI: React SPA served over HTTPS, complies with WCAG 2.1 AA. Handles client-side field encryption using AES-256-GCM before transmission.
- API Gateway: Nginx reverse proxy with TLS 1.3 termination, validates JWT RS256 tokens, routes to micro‑services. Rate-limit configured at 100 requests per second per client IP.
- Intake Service: FastAPI application responsible for receiving encrypted payloads, decrypting with per-field keys stored in Docker secret, persisting to PostgreSQL using pgcrypto.
- PDF Generator Service: Python service using WeasyPrint to render HTML templates into PDF, applies watermark with user ID and ISO-8601 timestamp; response now includes a digital signature field for integrity verification.
- Audit Logger Service: Centralized logger writing immutable audit records to PostgreSQL audit tables; also streams to local file for retention.
- PostgreSQL Database: Single instance container with row-level security policies for admin, clinician, front-desk roles; pgcrypto extension enabled for field-level encryption at rest.

2. Data Flow Diagram
mermaid
flowchart TD
 subgraph Frontend
 UI[Web UI]
 end
 subgraph Gateway
 API[API Gateway]
 end
 subgraph Services
 Intake[Intake Service]
 PDFGen[PDF Generator Service]
 Audit[Audit Logger Service]
 end
 subgraph DB
 PG[PostgreSQL DB]
 end
 UI -->|HTTPS| API
 API -->|REST| Intake
 Intake -->|SQL| PG
 Intake -->|Event| Audit
 PDFGen -->|SQL| PG
 PDFGen -->|Event| Audit
 Audit -->|Write| PG

3. Security Controls
- Transport Encryption: All external traffic forced to TLS 1.3; internal service-to-service calls also use mTLS with self-signed certificates.
- At-Rest Encryption: Sensitive columns (SSN, medical_history) encrypted with AES-256-GCM via pgcrypto; master key stored as Docker secret pg_master_key.
- Key Management: Master key rotated quarterly; rotation script updates Docker secret and re-encrypts existing rows using pgcrypto functions only.
- Authentication & Authorization: JWT RS256 signed by internal CA; RBAC enforced in PostgreSQL policies (`CREATE POLICY`) mapping roles to allowed tables/columns.
- Rate Limiting: API Gateway enforces 100 req/s per client and bursts up to 200 req/s.
- Audit Logging: Every [SELECT,INSERT,UPDATE,DELETE] triggers an audit entry with user_id, operation, timestamp, source IP; logs are immutable via append-only table setting. PDF export events also generate audit records referencing FR-030.

4. Performance and Availability Targets
- Form submission latency ≤ 200 ms (KPI-001) measured from UI click to DB commit.
- PDF generation time ≤ 1 s for average record size (KPI-030).
- Audit log write latency ≤ 100 ms (KPI-042).
- System uptime ≥ 99.9 % (KPI-001) achieved by Docker Compose restart policies and healthchecks.
- Database write throughput ≥ 500 TPS under peak load.

5. Compliance Mapping
- HIPAA §164.312(a)(2)(iv) satisfied by AES-256-GCM encryption at rest and TLS 1.3 in transit.
- NIST SP 800‑53 AC‑2, AC‑3 enforced via JWT and PostgreSQL RLS.
- Audit log completeness = 100 % (KPI-003) ensured by trigger-based logging.
- Watermark requirement FR-030 enforced by PDF Generator adding user ID and timestamp overlay; PDF response includes `signature` field for verification.
6. Deployment Topology
- All services defined in a single docker-compose.yml file; each container runs with --read-only flag except for volume mounts for PostgreSQL data and audit logs.
- Secrets injected via Docker secrets; no environment variables contain passwords.
- Air-gap setup guide includes steps to preload images onto an internal registry and configure host firewall to block outbound traffic.
b

## Patient Intake Service API Contract

### 1. Security Considerations
- Transport encryption: TLS 1.3 enforced on all inbound connections (Docker Compose service intake_api listens on port 443).
b- Field-level encryption: Sensitive fields (ssN, insurance_number, medical_history) are encrypted client-side using a per-session symmetric key that is wrapped by the server's RSA public key.
b- Authentication: Bearer token `Authorization: Bearer <jwt>` where JWT includes sub, role, exp claims. Tokens are validated against the public key mounted as a Docker secret.
b- Authorization: RBAC enforced per role (admin, clinician, front_desk). Only admin and clinician may read full records; front_desk may create but not read.
b- Rate Limiting: 100 requests per second per client IP; bursts up to 200 req/s allowed.
b- Audit logging: Every request creates an immutable audit entry (see FR-003) with user ID, timestamp, operation, request hash, and for PDF export includes `pdf_export` event referencing FR-030.
b

### 3. Request / Response Schemas
**SCH-001 – IntakeSubmissionRequest**
b
{
 "patient_id": "string", // UUID v4 generated client-side
 "demographics": {
   "first_name": "string",
b   "last_name": "string",
b   "dob": "date", // ISO‑8601
   "ssN_encrypted": "base64"
b },
b "insurance": {
b   "provider": "string",
b   "policy_number_encrypted": "base64",
b   "group_number_encrypted": "base64"
b },
b "medical_history_encrypted": "base64"
b}
b
b**SCH-002 – IntakeSubmissionResponse**
b
{
b "intake_id": "uuid",
b "status": "created",
b "created_at": "datetime",
b "audit_id": "uuid"
b}
b
b**SCH-003 – IntakeRetrievalResponse** (fields decrypted server-side before return)
b
{
b "intake_id": "uuid",
b "patient_id": "string",
b "demographics": {
b   "first_name": "string",
b   "last_name": "string",
b   "dob": "date",
b   "ssN": "string"
b },
b "insurance": {
b   "provider": "string",
b   "policy_number": "string",
b   "group_number": "string"
b },
b "medical_history": "string",
b "created_at": "datetime"
b}
b
b**SCH-004 – PDFExportResponse** (new) includes watermark verification signature

{
b "intake_id": "uuid",
b "pdf_url": "https://.../download/{intake_id}.pdf",
b "signature": "base64_signature_of_pdf_content_and_watermark_metadata"
b}
b
b### 5. Error Taxonomy (standardized)
b| Error Code | HTTP Status | Description | User Message | Retryable? |
b---|---|---|---|---|
b| ERR-001 | 400 | Invalid request payload – schema validation failed | "Submitted data is malformed or missing required fields." | false |
b| ERR-002 | 401 | Missing or invalid JWT token | "Authentication required. Please log in again." | false |
b| ERR-003 | 403 | RBAC violation – user role not permitted for operation | "You do not have permission to perform this action." | false |
b| ERR-004 | 429 | Rate limit exceeded | "Too many requests – please slow down." | true |
b| ERR-005 | 500 | Encryption service unavailable | "Temporary server error. Please retry later." | true |
b### 6. Audit Logging Details
All CRUD operations on `intake_record` generate entries in `audit_log` table with fields: audit_id (uuid), user_id (uuid), operation (text), target_id (uuid), timestamp (timestamptz), source_ip (inet), request_hash (text). PDF export (`/api/v1/intake/{id}/pdf`) generates an additional audit entry with operation `PDF_EXPORT` and includes `watermark_user_id` and `watermark_timestamp` for traceability to FR-030.

## Component Interaction Diagram
mermaid
flowchart TD
    Client -->|HTTPS POST /api/v1/intake| API_Gateway[API Gateway]
    API_Gateway -->|Validate JWT| Auth_Service[Auth Service]
    Auth_Service -->|OK| Intake_Service[Intake Service]
    Intake_Service -->|Encrypt fields via Crypto Lib| PostgreSQL[PostgreSQL (pgcrypto)]
    Intake_Service -->|Create audit entry| Audit_Service[Audit Service]
    Audit_Service --> PostgreSQL
    Client -->|HTTPS GET /api/v1/intake/{id}| API_Gateway
    API_Gateway --> Auth_Service
    Auth_Service --> Intake_Service
    Intake_Service --> PostgreSQL
    PostgreSQL --> Intake_Service
    Intake_Service -->|Decrypt for authorized role| Client

### 4. Entity Definitions

#### 4.1 Patient
| Entity | Field | Data Type | Required | Description / Constraints |
|---|---|---|---|---|
| Patient | patient_id | UUID | Yes | Primary key, generated by `gen_random_uuid()` |
| Patient | first_name | TEXT | Yes | Encrypted at rest (`pgp_sym_encrypt`) |
| Patient | last_name | TEXT | Yes | Encrypted at rest |
| Patient | date_of_birth | DATE | Yes | Must be past date |
| Patient | gender | TEXT | No | Enum: 'Male','Female','Other' |
| Patient | created_at | TIMESTAMPTZ | Yes | Default `now()` |
| Patient | updated_at | TIMESTAMPTZ | Yes | Updated via trigger |

#### 4.2 Insurance
| Entity | Field | Data Type | Required | Description / Constraints |
|---|---|---|---|---|
| Insurance | insurance_id | UUID | Yes | Primary key |
| Insurance | patient_id | UUID | Yes | FK → Patient.patient_id, ON DELETE CASCADE |
| Insurance | provider_name | TEXT | Yes | Encrypted (`pgp_sym_encrypt`) |
| Insurance | policy_number | TEXT | Yes | Encrypted (`pgp_sym_encrypt`) |
| Insurance | group_number | TEXT | No | Encrypted (`pgp_sym_encrypt`) |
| Insurance | effective_date | DATE | Yes | Must be ≤ current date |
| Insurance | expiration_date | DATE | Yes | Must be > effective_date |

#### 4.3 MedicalHistory
| Entity | Field | Data Type | Required | Description / Constraints |
|---|---|---|---|---|
| MedicalHistory | history_id | UUID | Yes | Primary key |
| MedicalHistory | patient_id | UUID | Yes | FK → Patient.patient_id |
| MedicalHistory | condition_code | TEXT | Yes | ICD‑10 code, validated against reference list |
| MedicalHistory | description | TEXT | No | Encrypted (`pgp_sym_encrypt`) |
| MedicalHistory | onset_date | DATE | No | Must be ≤ today |
| MedicalHistory | resolved_date | DATE | No | If present, ≥ onset_date |

### 6. Indexes and Performance
- Primary keys indexed automatically.
- B‑tree indexes on `patient_id`, `provider_name`, `condition_code`.
- Partial index on `audit_log (performed_at)` for recent‑log queries.
- GIN index on decrypted JSON payload for selective search in controlled contexts.

### 7. Migration Scripts (Reference Only)
sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- Table creation statements follow the definitions above and include:
ALTER TABLE patient ENABLE ROW LEVEL SECURITY;
ALTER TABLE insurance ENABLE ROW LEVEL SECURITY;
ALTER TABLE medicalhistory ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

### 8. Overview
The Audit Logging Service (ALS) records every read and write operation performed on patient intake data to satisfy HIPAA technical safeguard requirements (45 CFR §164.312(b)). Each log entry captures the actor's user ID, timestamp (ISO‑8601 UTC), operation type (CREATE,READ,UPDATE,DELETE,EXPORT), target entity ID, and a cryptographic hash of the request payload for tamper‑evidence. Logs are written to an immutable append‑only PostgreSQL table with pgcrypto‑enabled RLS and replicated to a write‑once object store for long‑term retention.

### 9. API Endpoints

#### POST /api/v1/audit/logs
- **Purpose**: Record a new audit entry (used by internal services).
- **Authentication**: Bearer JWT signed with RS256.
- **Request Body**:

{"user_id": "uuid", "operation": "string", "entity": "string", "entity_id": "uuid", "payload_hash": "string"}

- **Response (201 Created)**:

{"log_id": "uuid", "status": "created"}

- **Rate‑Limit**: 100 requests/second per service instance; excess returns `429 Too Many Requests` with header `Retry-After`.
- **Error Responses** (application/json):

{"error_code": "ERR_AUDIT_01", "message": "Validation failed", "details": {}}

#### GET /api/v1/audit/logs
- **Purpose**: Query audit entries for compliance reporting.
- **Authentication**: Bearer JWT RS256.
- **Query Parameters**: `start_time`, `end_time` (ISO‑8601), optional `user_id`, optional `operation`.
- **Response (200 OK)**:

{"logs": [ {"log_id": "uuid", "user_id": "uuid", "timestamp": "datetime", "operation": "string", "entity": "string", "entity_id": "uuid", "payload_hash": "string"}, ... ] }

- **Rate‑Limit**: 200 requests/second per client; excess returns `429`. Error format same as above.

#### GET /api/v1/audit/health
- **Purpose**: Health check for ALS. No auth required.
- **Response (200 OK)**:

{"status": "healthy", "uptime_seconds": 123456}

### 10. PDF Export Endpoint (Extended)

#### GET /api/v1/intake/{id}/export/pdf
- **Purpose**: Export a patient intake summary as PDF with watermark and digital signature.
- **Authentication**: Bearer JWT RS256.
- **Response Headers**:
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="intake_{id}.pdf"`
  - `X-Watermark-Timestamp`: ISO‑8601 timestamp of export.
  - `X-Watermark-UserId`: ID of the requesting user.
- **Response Body**: Binary PDF stream. The PDF includes a visible watermark containing the timestamp and user ID and an embedded digital signature object (`/Sig`) conforming to PAdES‑BES. The signature covers the entire document and is verifiable using the public key published at `/certs/pades_pub.pem`.
- **Error Responses** follow the standard error format with codes `ERR_EXPORT_01` (unauthorized), `ERR_EXPORT_02` (rate limit), `ERR_EXPORT_03` (generation failure).

## Missing Requirement FR‑030 Defined
**FR‑030**: System must support export of patient intake summaries as PDF with a watermark containing export timestamp and exporting user ID. The watermark must be visible on every page and the PDF must be signed digitally to ensure integrity. KPI‑030 measures watermark accuracy at 100% of exported PDFs. This requirement is now explicitly referenced in the PDF Export Endpoint above.

### Service Boundaries
| Service Name | Responsibility | Dependencies | Events Emitted | Events Consumed |
|---|---|---|---|---|
| AuditLoggingService (SVC-001) | Persist immutable audit entries and provide query API. | PostgreSQL with pgcrypto, JWT verification service, internal KMS for hash salts. | AuditLogCreated (to compliance analytics pipeline) | None |
| ComplianceAnalytics (SVC-002) | Aggregate logs for KPI-003 and generate reports. | ALS via GET /api/v1/audit/logs, object store for archived logs. | ComplianceReportReady | AuditLogCreated |

### Retention Policy
Logs retained for 7 years (FR-003, KPI-003). Nightly job moves entries >365 days to immutable object store (MinIO). After 10 years archived to cold storage.

## PDF Export Service Design

### Architecture Diagram
mermaid
flowchart TD
    UI[Web UI] -->|HTTPS POST /api/v1/patients/{id}/export| GW[API Gateway]
    GW -->|JWT RS256 auth| Export[Export Endpoint]
    Export --> Watermark[Add Watermark]
    Watermark --> Sign[Sign PDF]
    Sign --> PDF[PDF Blob]
    Export --> Log[Audit Logger]
    PDF --> GW --> UI

### API Specification
**Endpoint**: `/api/v1/patients/{patient_id}/export`
**Method**: GET
**Auth**: Bearer JWT RS256
**Rate Limit**: 20 requests per minute per user (headers `X-Rate-Limit-Limit`, `X-Rate-Limit-Remaining`, `X-Rate-Limit-Reset`).
**Request**: No body.
**Response** (200):

{
  "pdf_base64": "string",
  "content_type": "application/pdf",
  "export_timestamp": "2023-01-01T12:00:00Z",
  "watermark": {
    "user_id": "string",
    "timestamp": "2023-01-01T12:00:00Z"
  },
  "signature": "base64string"
}

**Error Response** (application/json):

{
  "error_code": "ERR-001",
  "http_status": 401,
  "message": "Authentication required",
  "details": null,
  "retryable": false
}

### Data Model Extension
| Entity | Field | Type | Required | Description |
|---|---|---|---|---|
| pdf_export_log | id | UUID | Yes | Primary key |
|  | patient_id | UUID | Yes | FK → patients.id |
|  | exported_by | UUID | Yes | FK → users.id (role admin/clinician/front-desk) |
|  | export_timestamp | TIMESTAMPTZ | Yes | UTC timestamp |
|  | watermark_hash | BYTEA | Yes | SHA-256 of watermark JSON |
|  | pdf_blob | BYTEA | Yes | Encrypted PDF stored for audit retention |
|  | signature | BYTEA | Yes | RSA-PSS signature of PDF content |
# PDF Export API Contract (Overview)

## PDF Export API Contract – High-Level Architecture

### 6. Purpose and Scope
This document defines the high‑level system architecture and REST contract for the PDF Export API of the PatientIntake project. The API enables authorized staff (admin, clinician, front‑desk) to generate a PDF intake summary for a given patient record, embed a tamper‑evident watermark containing the exporting user ID and UTC timestamp, and stream the document to the client. All operations satisfy HIPAA technical safeguard requirements, enforce role‑based access control (RBAC), meet performance target FR-001 (p95 \u2264 2 s) and produce audit log entries per FR-003.

### 7. Component Diagram Description
The architecture consists of five logical layers, each deployed as a Docker container in the Docker‑Compose environment:
- **Presentation Layer** – React UI served by Nginx (frontend). Communicates with the API Gateway over HTTPS.
- **API Gateway** – Kong performs request routing, rate limiting (max 10 exports/min/user), JWT validation, and mutual TLS termination.
- **Service Layer** – Two micro‑services:
  - `pdf-export-service` (Go) implements PDF generation, watermark insertion, and streaming.
  - `audit-service` (Node.js) records immutable audit events to PostgreSQL and forwards them to an external SIEM via syslog.
- **Data Layer** – PostgreSQL with Row‑Level Security (RLS) policies for `patients`, `pdf_exports`, and `audit_logs`. pgcrypto provides field‑level encryption for PHI columns.
- **PDF Generation Engine** – WeasyPrint runs as a side‑car container invoked by `pdf-export-service`.
All inter‑container traffic is confined to an internal Docker network and encrypted with mutual TLS.

### 8. API Endpoint Specification
| Method | Path | Description | Auth | Request Schema | Response Schema |
|--------|------|-------------|------|----------------|-----------------|
| GET | /api/v1/patients/{patient_id}/export/pdf | Generate PDF summary for patient | Bearer token with role `clinician` or `admin` | N/A (path & optional query) | 200: `PdfExportSuccess`, 202: `PdfExportAccepted`, 4xx/5xx error objects |

#### 8.1 Request Parameters
- **Path Parameter** `patient_id` (UUID, required): Identifier of the patient record.
- **Query Parameter** `include_history` (boolean, optional): When true, the PDF also contains the medical history section.
- **Header** `Authorization: Bearer <jwt>` – JWT must contain a `role` claim (`clinician` or `admin`) and be signed with the system RSA key.

#### 8.2 Response Schemas

// 200 OK – synchronous generation
{
  "pdf_url": "https://api.example.com/tmp/abcd1234.pdf",
  "expires_at": "2026-05-04T12:34:56Z"
}
// 202 Accepted – asynchronous generation
{
  "operation_id": "e7f9c2d4-5b6a-11ee-bf5c-0242ac120002",
  "status_url": "/api/v1/operations/e7f9c2d4-5b6a-11ee-bf5c-0242ac120002"
}
// Error object (used for all 4xx/5xx responses)
{
  "error_code": "ERR-PDF-001",
  "message": "Detailed human‑readable description",
  "detail": {
    "field": "patient_id",
    "issue": "Patient not found or access denied"
  }
}

### 9. Error Handling Table
| HTTP Status | Error Code | Condition | Description |
|-------------|------------|-----------|-------------|
| 400 | ERR-PDF-400 | Missing or malformed request parameters | Bad request \u2013 validation failed |
| 401 | ERR-PDF-401 | Invalid or expired JWT | Authentication required |
| 403 | ERR-PDF-403 | RBAC violation or RLS policy blocks access | Forbidden – insufficient permissions |
| 404 | ERR-PDF-404 | Patient record does not exist or is not accessible | Not found \u2013 resource unavailable |
| 429 | ERR-PDF-429 | Rate limit exceeded ( >10 exports/min/user ) | Too many requests – throttled |
| 500 | ERR-PDF-500 | Internal server error during PDF generation | Server error – investigate logs |

### 10. PDF Content Requirements
1. Header with patient name, DOB, and record ID.
2. Sections for demographics, insurance, and optional medical history.
3. Watermark text: `Exported by {user_id} on {timestamp}` rendered semi‑transparent on each page.
4. PDF generated using **WeasyPrint** version 53.0.
5. All PHI in the PDF is encrypted at rest using AES‑256‑GCM; the signed URL provides TLS 1.3 transport encryption.
6. PDF checksum (SHA‑256) is stored in `pdf_exports.checksum` for integrity verification.

## Technical Design – Patient Intake Audit Log Service

### 6. Overview
The Audit Log Service records immutable audit events for all patient‑intake actions. It satisfies FR-003 (audit logging), FR-001 (performance), and related security requirements.

### 7. Architecture
- Containerized Go service.
- Uses PostgreSQL (DB-001) with pgcrypto for at‑rest encryption.
- Secrets managed by Vault.
- Communicates with User Service (SVC-001) for identity and role data.
- Emits metrics to Monitoring (MON-001).

### 8. Service Interface Definition
go
type AuditLogService interface {
    CreateLog(ctx context.Context, req CreateLogRequest) (CreateLogResponse, error)
    GetLog(ctx context.Context, logID uuid.UUID) (AuditLogEntry, error)
}

### 9. Data Model
Table **audit_logs**:
- log_id UUID PRIMARY KEY
- event_type TEXT NOT NULL
- entity_id UUID NOT NULL
- timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
- user_id UUID NOT NULL
- details JSONB NOT NULL
- metadata BYTEA ENCRYPTED USING pgcrypto (per‑field key)
- is_deleted BOOLEAN NOT NULL DEFAULT FALSE
- created_at TIMESTAMPTZ NOT NULL DEFAULT now()
- CONSTRAINT immutability CHECK (created_at = timestamp)
- BEFORE INSERT trigger sets `timestamp` and `created_at`.

### 10. Security Considerations
- **Authentication**: OAuth2 Bearer token validated against internal auth service (EP-001).
- **Authorization**: RBAC enforced; only `admin` and `auditor` may POST, `clinician` may GET logs they are permitted to view.
- **Transport Encryption**: TLS 1.2+ mandatory.
- **At‑Rest Encryption**: pgcrypto column `metadata` encrypted with master key rotated quarterly.
- **Immutability**: `timestamp` set once by trigger; updates prohibited.
- **Retention**: Logs older than 7 years archived to immutable object storage per FR-003.

### 11. Integration Points
- **User Service (SVC-001)** – provides `user_id` and role; returns 503 on failure.
- **PostgreSQL (DB-001)** – connection pool errors map to `ERR-AUDIT-004`.
- **Monitoring (MON-001)** – metric `audit_log_write_latency_ms`; alerts >100 ms.

### 12. PDF Export API (Addressed Reviewer Gap)

#### 12.1 Export Patient Intake Summary
`GET /api/v1/patient/intake/{patient_id}/export/pdf`
Query Params: `includeAudit=true|false`
sResponse: `application/pdf` stream with watermark containing export timestamp and requesting user ID.
Error Codes: `ERR-005` (PDF generation failure), `ERR-002` (auth), `ERR-003` (authorization).
Watermark format: "Exported on {timestamp} by {user_id}".
All exported PDFs are stored temporarily in `/tmp/export` and deleted after 5 minutes.

s### 9. Error Taxonomy
s| Code | HTTP | Description | User Message | Retryable |
s|------|------|-------------|--------------|----------|
s| ERR-001 | 400 | Invalid request payload – missing required fields or type mismatch | "The request is malformed. Please correct the highlighted fields." | false |
s| ERR-002 | 401 | Authentication failure – missing or invalid bearer token | "Authentication required. Please log in again." | false |
s| ERR-003 | 403 | Authorization failure – insufficient role | "You do not have permission to perform this action." | false |
s| ERR-004 | 500 | Internal server error – unexpected failure in logging subsystem | "An unexpected error occurred. Please try again later." | true |
s| ERR-005 | 500 | PDF generation failure | "Unable to generate PDF at this time. Please retry later." | true |
s### 10. Deployment (Docker‑Compose)
syaml
version: "3.8"
services:
  audit-log:
    image: ghcr.io/example/patientintake-auditlog:latest
    restart: unless-stopped
    environment:
      POSTGRES_HOST: db
      POSTGRES_DB: patient_intake
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      JWT_PUBLIC_KEY: /run/secrets/jwt_pub.key
    secrets:
      - jwt_pub.key
    volumes:
      - auditlog_data:/var/lib/auditlog
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health" ]
      interval: 30s
      timeout: 10s
      retries: 3
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "app_user" ]
      interval: 30s
      timeout: 10s
      retries: 5
networks:
  backend:
    driver: bridge
volumes:
  auditlog_data:
    driver: local
  db_data:
    driver: local
secrets:
  jwt_pub.key:
    file: ./secrets/jwt_pub.key

sAll services run on a private bridge network; ports are bound only to loopback on the host.
s### 11. Air‑Gap Setup Procedure
s1. **Prepare Offline Media** – Copy Docker images using \`docker save\`.
s2. **Transfer to Target Host** – Load images with \`docker load\`.
s3. **Generate Secrets Offline** – Create RSA key pair for JWT verification; place public key in \`./secrets/jwt_pub.key\`.
s4. **Configure Environment Variables** – Create \`.env\` with high‑entropy \`POSTGRES_PASSWORD\`; set file mode 600.
s5. **Start Stack** – Run \`docker compose up -d\`; verify health checks.
s6. **Validate Audit Logging** – POST a valid audit event; confirm entry is stored encrypted at rest.
s7. **Backup Strategy** – Nightly \`docker exec db pg_dumpall -U app_user > /backups/backup_$(date +%F).sql\`; store backups on encrypted offline media.
s### 12. Traceability Matrix
s- **FR-001** – Performance target met by async write path and health checks.
s- **FR-003** – Retention policy implemented via nightly archival job.
s- **ERR-004** – Defined in error taxonomy as retryable internal error.
s- **PDF Export** – New contract satisfies reviewer request for missing export specification.
s---
s*Document generated by Refiner Agent.*
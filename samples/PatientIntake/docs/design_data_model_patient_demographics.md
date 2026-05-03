# Patient Demographics Schema (Overview)

### 1. API Contracts

- **POST /api/v1/patients**
  - Description: Submit new patient intake record
  - Request Schema: PatientCreate (see Section 2)
  - Response Schema: PatientCreateResponse
  - Security: Bearer JWT (role required: front_desk)
  - Errors: 400 ERR-001-VALIDATION, 401 Unauthorized, 403 ERR-002-AUTHORIZATION, 500 ERR-004-ENCRYPTION_FAIL
  - Rate Limiting: 100 requests per minute per user

- **GET /api/v1/patients/{patient_id}**
  - Description: Retrieve patient demographics for authorized role
  - Path Parameter: patient_id (UUID)
  - Response Schema: PatientRead
  - Security: Bearer JWT (roles: clinician, admin)
  - Errors: 400 ERR-001-VALIDATION, 401 Unauthorized, 403 ERR-002-AUTHORIZATION, 404 ERR-003-NOTFOUND, 500 ERR-004-ENCRYPTION_FAIL
  - Audit Logging: READ action recorded in PatientAuditLog

- **GET /api/v1/patients/{patient_id}/export**
  - Description: Generate PDF summary with watermark and timestamp
  - Path Parameter: patient_id (UUID)
  - Response: application/pdf
  - Security: Bearer JWT (roles: clinician, admin)
  - Errors: 400 ERR-001-VALIDATION, 401 Unauthorized, 403 ERR-002-AUTHORIZATION, 404 ERR-003-NOTFOUND, 502 ERR-005-PDF_GENERATION, 500 ERR-004-ENCRYPTION_FAIL
  - Rate Limiting: 30 requests per minute per user
  - Audit Logging: EXPORT action recorded in PatientAuditLog

- **GET /api/v1/patients**
  - Description: List patients with pagination
  - Query Parameters: page (int, default=1), page_size (int, max=100)
  - Response Schema: PatientRead[] with pagination metadata
  - Security: Bearer JWT (roles: clinician, admin)
  - Errors: 401 Unauthorized, 403 ERR-002-AUTHORIZATION, 500 Internal Server Error
  - Rate Limiting: 200 requests per minute per user

### 2. Data Model

| Entity | Column | Data Type | Required | Constraints / Description |
|---|---|---|---|---|
| Patient | patient_id | UUID | Yes | Primary key, generated server‑side (gen_random_uuid()) |
| Patient | first_name | varchar(50) | Yes | Alphabetic, trimmed |
| Patient | last_name | varchar(50) | Yes | Alphabetic, trimmed |
| Patient | date_of_birth | date | Yes | Must be past date |
| Patient | gender | enum["male","female","other","unspecified"] | No | Controlled vocabulary |
| Patient | ssn_encrypted | bytea | Yes | Field‑level encryption using pgcrypto (x‑encrypted:true) |
| Patient | address_line1 | varchar(100) | Yes | 
| Patient | address_line2 | varchar(100) | No | 
| Patient | city | varchar(50) | Yes | 
| Patient | state | char(2) | Yes | US state code |
| Patient | zip_code | varchar(10) | Yes | Regex ^\d{5}(-\d{4})?$ |
| Patient | insurance_provider | varchar(100) | Yes | 
| Patient | insurance_policy_number_encrypted | bytea | Yes | Encrypted at rest |
| PatientAuditLog | log_id | BIGSERIAL | Yes | Primary key |
| PatientAuditLog | patient_id | UUID | Yes | FK to Patient |
| PatientAuditLog | action_type | enum["CREATE","READ","EXPORT"] | Yes | 
| PatientAuditLog | performed_by_role | enum["admin","clinician","front_desk"] | Yes | 
| PatientAuditLog | timestamp_utc | timestamptz | Yes |

### 3. Error Taxonomy (Unified)

| Error ID | HTTP Code | Title | Message | Retryable |
|---|---|---|---|---|
| ERR-001-VALIDATION | 400 | Validation Error | "Submitted data is invalid or missing required fields." | No |
| ERR-002-AUTHORIZATION | 403 | Authorization Error | "You do not have permission to access this resource." | No |
| ERR-003-NOTFOUND | 404 | Not Found | "Requested resource not found or not visible to your role." | No |
| ERR-004-ENCRYPTION_FAIL | 500 | Encryption Failure | "Internal error processing sensitive data." | Yes |
| ERR-005-PDF_GENERATION | 502 | PDF Generation Failure | "Unable to generate PDF at this time, please try again later." | Yes |

### 4. Service Boundaries

| Service Name | Responsibility | Dependencies | Events Emitted | Events Consumed |
|---|---|---|---|---|
| PatientIntakeService (SVC-001) | Validate, encrypt, and persist patient intake data | PostgreSQL (RLS enabled), pgcrypto, Logger | PatientCreatedEvent | None |
| PatientReadService (SVC-002) | Authorize, decrypt fields and return patient demographics; log READ actions | PostgreSQL, pgcrypto, Logger | PatientReadEvent | None |
| PdfExportService (SVC-003) | Render PDF via wkhtmltopdf, apply watermark with timestamp, store audit log entry | PatientReadService, AuditLogService | PdfGeneratedEvent | PatientReadEvent |
| AuditLogService (SVC-004) | Record CREATE/READ/EXPORT actions in append‑only audit_log table; enforce immutability | PostgreSQL (append‑only table) | AuditLoggedEvent | None |

## Technical Design Specification

### 7. Indexes and Performance
Primary keys are UUIDs generated via pgcrypto. B‑tree indexes on `patient.last_name`, `insurance.provider_name`, and `audit_log.performed_at` enable fast lookup. A GIN index on `audit_log.details_jsonb` supports ad‑hoc forensic queries. Encrypted columns are stored as `bytea`; searches use non‑encrypted surrogate fields.

#### 1. TLS Encryption in Transit
All API endpoints (e.g., `POST /api/v1/patients`, `GET /api/v1/patients/{id}`) are served exclusively over HTTPS with TLS 1.2+ using Let’s Encrypt certificates rotated every 90 days. Mutual TLS is enforced for all service‑to‑service calls within the Docker Compose network.
Cipher suites: `ECDHE‑RSA‑AES256‑GCM‑SHA384`, `ECDHE‑ECDSA‑AES256‑GCM‑SHA384`, `TLS_AES_256_GCM_SHA384`. Weak ciphers are disabled in the Nginx reverse‑proxy.

#### 2. Field‑Level Encryption at Rest
Sensitive columns (`ssn_encrypted`, `insurance_policy_number_encrypted`, `medical_history_encrypted`) use PostgreSQL `pgcrypto` AES‑256‑GCM. Keys are derived from a master key stored in HashiCorp Vault; data‑encryption keys rotate quarterly via a background worker.
Non‑sensitive columns (`first_name`, `last_name`, `date_of_birth`) remain plaintext for indexing while the host OS provides full‑disk encryption (LUKS).

#### 3. Audit Logging Strategy
`log_statement = 'all'` with a detailed `log_line_prefix`. Every INSERT/UPDATE/DELETE/SELECT on `patient_demographics` creates an audit entry (user ID, timestamp, operation, row ID, source IP). Logs are streamed to an ELK stack with 7‑year retention to satisfy FR‑003 and KPI‑042.
Read operations now also generate `patient_read` audit events.
Export actions emit `pdf_export` events with exporter ID, patient ID, timestamp, and watermark hash.

#### 4. Key Management and Access Controls
Vault access is mediated by Kubernetes Service Accounts bound to RBAC roles (admin, clinician, front_desk). Tokens have 1‑hour TTL and are scoped to permitted data categories.
PostgreSQL Row‑Level Security (RLS) policies:
- `admin`: unrestricted SELECT/UPDATE/DELETE.
- `clinician`: SELECT where `assigned_clinician_id = current_user_id`.
- `front_desk`: INSERT only on rows they created; SELECT limited to their own entries.

#### 6. Performance and Monitoring
TLS handshake latency metric `tls_handshake_seconds` must stay <200 ms (99 %ile). Encryption/decryption overhead ≤5 ms per row. Audit log ingestion capped at 10 k events/sec with back‑pressure for non‑security logs.

#### 7. Disaster Recovery and Backup
Nightly encrypted backups via `pg_dump --format=custom`, stored offline and encrypted with the Vault master key. Monthly restoration tests verify data integrity and audit log completeness.

### Patient Demographics API Contracts

#### 1. Endpoints
| Endpoint | Method | Purpose | Request Schema | Response Schema | Auth |
|---|---|---|---|---|---|
| /api/v1/patients | POST | Create new patient record | {"first_name":"string","last_name":"string","date_of_birth":"date","ssn":"string","insurance_policy_number":"string","address":{"street":"string","city":"string","state":"string","zip":"string"}} | {"patient_id":"uuid","status":"created"} | Bearer Token |
| /api/v1/patients/{id} | GET | Retrieve patient demographics (RBAC enforced) | N/A | {"patient_id":"uuid","first_name":"string","last_name":"string","date_of_birth":"date","address":{...},"insurance_policy_number_encrypted":"bytea"} | Bearer Token |
| /api/v1/patients/{id} | PUT | Update mutable fields (address) | {"address":{"street":"string","city":"string","state":"string","zip":"string"}} | {"patient_id":"uuid","status":"updated"} | Bearer Token |
| /api/v1/patients/{id}/pdf | GET | Generate PDF intake summary with watermark | N/A | {"pdf_url":"string","generated_at":"datetime"} | Bearer Token |
| /api/v1/patients | GET | List patients with pagination & filtering | N/A | {"patients":[{...}],"page":1,"page_size":50,"total_pages":10} | Bearer Token |

#### 2. Rate Limiting & Pagination
All endpoints enforce a rate limit of **100 requests per minute per user** (configurable via Env `API_RATE_LIMIT`). List endpoint (`GET /api/v1/patients`) supports `page` and `page_size` query parameters; maximum `page_size` is 100.

#### 3. Unified Error Handling
All error responses follow a common envelope:

{ "error": { "code": "ERR-XXX", "message": "Human readable message", "details": null } }

The error taxonomy has been de‑duplicated and extended:
| Error Code | HTTP Status | Description | User Message | Retryable |
|---|---|---|---|---|
| ERR-001 | 400 | Validation failed | "Please correct the highlighted fields and try again." | No |
| ERR-002 | 401 | Authentication token missing/expired | "Your session has expired. Please log in again." | Yes |
| ERR-003 | 403 | Authorization failure | "You do not have permission to view this patient record." | No |
| ERR-004 | 409 | Conflict – duplicate SSN detected | "A patient with this identifier already exists." | No |
| ERR-005 | 500 | Internal server error | "An unexpected error occurred. Please contact support." | Yes |
| ERR-006 | 429 | Too many requests (rate limit) | "You have exceeded the allowed request rate. Please wait and try again." | Yes |
| ERR-007 | 404 | Resource not found (e.g., patient ID) | "The requested patient record could not be found." | No |
| ERR-008 | 422 | Unprocessable Entity – PDF export failure | "Unable to generate PDF at this time. Please retry later." | Yes |

All endpoints now return one of the above codes consistently.

#### 4. Audit Logging for Read Operations
`GET /api/v1/patients/{id}` and list endpoint now emit `patient_read` audit events capturing user ID, timestamp, patient ID(s) accessed, and source IP.

### Operational Non‑Functional Requirements
- **Availability**: KPI‑01 target 99.9% uptime.
- **Response Time**: Form submission <200 ms (99 th percentile).
- **Security**: All data at rest encrypted; TLS in transit; audit log retention 7 years.
- **Backup**: Encrypted nightly backups retained 30 days.
- **Monitoring**: Prometheus metrics for TLS handshake latency, encryption overhead, audit log ingestion rate.

### Disaster Recovery Procedure
1. Restore latest encrypted backup using Vault master key.
2. Verify checksum of restored data.
3. Replay audit logs from ELK to ensure continuity.
4. Conduct post‑restore validation tests (sample record retrieval, PDF generation).

*All specifications map to the original functional requirements FR‑001…FR‑003 and related KPIs.*

## Technical Design Document for Patient Intake System

### 1. Architecture Overview
The system is composed of the following micro‑services deployed via Docker Compose in an air‑gap environment:
- **API Service** – FastAPI application exposing REST endpoints, handling authentication, validation, and orchestration.
- **PDF Generator Service** – wkhtmltopdf container generating PDF intake summaries with watermark (user ID + timestamp).
- **Auth Service** – OAuth2 Resource Owner Password Credentials flow issuing RS256‑signed JWTs.
- **Audit Service** – Records every read/write operation in an immutable PostgreSQL audit_log table.
- **PostgreSQL Database** – Stores patient intake data, encrypted at rest using pgcrypto (AES‑256‑GCM).
All services run with the `--read-only` flag where applicable and are isolated on a private Docker bridge network.

### 2. Service Interaction Diagram

Client -> Auth Service (token) -> API Service -> {DB, PDF Generator, Audit Service}

### 3. API Specifications
All endpoints are versioned under `/api/v1` and conform to OpenAPI 3.0 schema. Errors follow a unified taxonomy defined in `error_codes.yaml`.

#### 3.1 Authentication Endpoints
- **POST /auth/token**
  - Request: `application/x-www-form-urlencoded` with `grant_type=password`, `username`, `password`.
  - Response (200): `{ "access_token": "<jwt>", "token_type": "Bearer", "expires_in": 3600 }`
  - Errors: `ERR-001` (invalid credentials), `ERR-002` (account locked).

#### 3.2 Patient Intake Endpoints
- **POST /patients**
  - Request Body (application/json):
    
    {
      "first_name": "string",
      "last_name": "string",
      "dob": "YYYY-MM-DD",
      "insurance": {"provider": "string","policy_number":"string"},
      "contact": {"email":"string","phone":"string"}
    }
    
  - Response (201): `{ "patient_id": "uuid", "status": "created" }`
  - Errors: `ERR-003` (validation failure), `ERR-004` (duplicate record).
  - **Security**: JWT required, role `frontdesk_role`.
  - **Audit**: Write operation logged with outcome.

- **GET /patients/{patient_id}**
  - Response (200): Patient resource JSON.
  - Errors: `ERR-005` (not found), `ERR-006` (unauthorized access).
  - **Security**: JWT required, row‑level security ensures only clinicians assigned to the patient (`clinician_role`) can read.
  - **Audit**: Read operation logged.

- **GET /patients** (list with pagination)
  - Query Params: `page`, `size` (default 20).
  - Response (200): `{ "items": [...], "page":1,"size":20,"total":123 }`
  - Errors: `ERR-007` (invalid pagination).
  - **Rate Limiting**: 100 requests per minute per user (enforced by API gateway).

#### 3.3 PDF Export Endpoint
- **POST /patients/{patient_id}/export**
  - Request Body: `{ "format": "pdf" }`
  - Response (202): `{ "job_id": "uuid", "status": "queued" }`
  - Asynchronous worker in PDF Generator creates PDF, applies watermark `UserID_{user_id}_TS_{timestamp}` and stores in object store (`/var/pdf_output`).
  - Errors: `ERR-008` (generation failure), `ERR-009` (unsupported format).
  - **Audit**: Write operation logged when PDF is stored.

#### 3.4 Audit Retrieval Endpoint (admin only)
- **GET /audit/logs**
  - Query Params: `start`, `end`, `user_id`, `operation`.
  - Response (200): List of audit records.
  - Security: Role `admin_role` only.

#### 4.1 Patient Table (`patient`) 
| Column | Type | Constraints |
|--------|------|--------------|
| patient_id | UUID PK | |
| first_name | TEXT | NOT NULL |
| last_name | TEXT | NOT NULL |
| dob | DATE | NOT NULL |
| insurance_provider | TEXT | |
| insurance_policy | TEXT | |
| contact_email | TEXT | |
| contact_phone | TEXT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | |
| owner_id | UUID | FK to clinician (RLS) |
*All sensitive columns are encrypted at rest using pgcrypto (`pgp_sym_encrypt`).*

#### 4.2 Audit Log Table (`audit_log`)
| Column | Type | Constraints |
|--------|------|--------------|
| audit_id | BIGSERIAL PK |
| user_id | UUID |
| patient_id | UUID |
| operation | TEXT |
| outcome | TEXT |
| timestamp | TIMESTAMPTZ DEFAULT now() |
| details | JSONB |
*Table is immutable; rows are never deleted and retained for 7 years (FR‑003).*

### 5. Docker Compose Deployment Contract (EP‑002)
yaml
version: "3.9"
services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: "patient_intake"
      POSTGRES_PASSWORD: "${POSTGRES_PASSWORD}"
      POSTGRES_DB: "patient_intake_db"
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "patient_intake"]
      interval: 10s
      timeout: 5s
      retries: 5
  api:
    build: ./api
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: "postgresql://patient_intake:${POSTGRES_PASSWORD}@db:5432/patient_intake_db"
      JWT_SECRET: "${JWT_SECRET}"
      ENCRYPTION_MASTER_KEY: "${ENCRYPTION_MASTER_KEY}"
    ports:
      - "8443:8443"
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "https://localhost:8443/health"]
      interval: 15s
      timeout: 5s
      retries: 3
  pdf_generator:
    image: openlabs/wkhtmltopdf:latest
    restart: unless-stopped
    environment:
      MAX_CONCURRENT_JOBS: "4"
    volumes:
      - pdf_store:/var/pdf_output
    networks:
      - backend
volumes:
  db_data:
  pdf_store:
networks:
  backend:
    driver: bridge

All services run with the `--read-only` flag where applicable and outbound internet traffic is blocked by host firewall to satisfy air‑gap requirements.

### 6. Security Considerations
- **Authentication** – OAuth2 ROPC flow, RS256 JWTs validated by Auth Service.
- **Authorization** – Role‑based access control (RBAC) enforced at API layer; row‑level security policies in PostgreSQL restrict clinicians to their patients.
- **Transport Security** – All HTTP endpoints require TLS 1.2+.
- **Data Encryption** – Field‑level encryption using pgcrypto AES‑256‑GCM; encryption keys managed via `ENCRYPTION_MASTER_KEY` secret.
- **Audit Logging** – Every read/write creates an immutable record in `audit_log`; logs retained for 7 years (FR‑003) and indexed for fast queries.
- **Rate Limiting & Pagination** – Implemented per‑user to prevent abuse; default page size 20, max 100.
- **Container Hardening** – Containers run as non‑root where possible; `--read-only` flag applied; secrets injected via Docker secrets or `.env` file.

### 8. Open Issues / Knowledge Gaps
- Exact HIPAA § 164.312(a)(2)(iv) technical safeguard requirements for encryption key management.
- PostgreSQL row‑level security performance characteristics at >10 M audit log rows.
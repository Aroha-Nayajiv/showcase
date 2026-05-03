# System Architecture Overview

## System Architecture Overview
1. Overall Architecture
The patient intake system is organized as a set of micro‑services deployed via Docker Compose on an isolated on‑prem network. The front‑end React SPA runs behind an Nginx reverse‑proxy (TLS 1.3) and communicates exclusively over HTTPS with the API Gateway (FastAPI). The gateway routes requests to four core services: Intake Service, Audit Service, PDF Generation Service, and Auth Service. All services share a private Docker overlay network and are configured with the `--read‑only` flag to satisfy FR‑017. Each container runs as a non‑root user and mounts only the minimal volume required for persistent logs.
2. Component Diagram
[Client Browser] --HTTPS--> [Nginx] --HTTPS--> [API Gateway]
   |
   |---> [Auth Service] (JWT, OAuth2)
   |---> [Intake Service] (validation, field‑level encryption)
   |---> [PDF Service] (WeasyPrint, watermarking)
   `---> [PostgreSQL] (RLS, pgcrypto)
The diagram is captured in `architecture/diagram.png` for reference.
3. Security Controls
Transport Encryption: All inbound/outbound traffic uses TLS 1.3 with certificates managed by an internal PKI.
Field‑Level Encryption: The Intake Service encrypts PHI fields using AES‑256‑GCM; per‑field data keys are wrapped by a master key stored in HashiCorp Vault.
At‑Rest Encryption: PostgreSQL pgcrypto encrypts column data; the database runs on encrypted block devices (LUKS).
Authentication & Authorization: Users obtain a JWT from Auth Service (`POST /api/v1/auth/login`). The token includes scopes admin, clinician, front_desk. FastAPI dependencies enforce RBAC on each endpoint (see EP‑001).
Audit Logging: Every read/write operation triggers an event to the Audit Service, which writes structured logs to Elasticsearch; logs contain user ID, timestamp, operation, and record ID, satisfying FR‑003 and KPI‑01.
4. Data Flow
1. User loads the SPA; Nginx terminates TLS.
2. SPA obtains a JWT via `/api/v1/auth/login`.
3. Form submission POST `/api/v1/intake` includes encrypted payload; Intake Service validates, encrypts fields, stores rows in patient_intake table with RLS policies restricting rows to the owner's role.
4. On successful write, Intake Service emits intake.created event; Audit Service records the event.
5. Clinician requests PDF via `GET /api/v1/patient/{id}/summary`; PDF Service retrieves data, generates PDF with watermark containing user ID and ISO‑8601 timestamp, stores the file temporarily, and returns a signed URL. The action is logged by Audit Service.
5. Deployment Topology
Docker Compose defines services: nginx, gateway, auth, intake, pdf, audit, postgres, vault.
Network Isolation: All services join intake_net; external access is limited to ports 443 (NGINX) and 22 (SSH for maintenance).
Air‑Gap Procedure: A step‑by‑step guide (`deployment/airgap_guide.md`) describes how to preload Docker images onto an offline registry, configure static IPs, and disable external DNS resolution.
6. Compliance Mapping
Encryption in transit | 164.312(e)(1) | TLS 1.3 everywhere
Encryption at rest | 164.312(a)(2)(iv) | AES‑256‑GCM + pgcrypto
Access control | 164.312(a)(1) | RBAC via JWT scopes
Audit logging | 164.312(b) | Centralized ELK logs
Minimum necessary | 164.308(a)(1)(ii) | Field‑level encryption only for PHI
The architecture satisfies all listed FRs, KPIs, and NFRs while remaining fully open‑source.

## API Specification for Patient Intake System
1. Authentication
- Endpoint: `/api/v1/auth/login`
- Method: POST
- Purpose: Issue a JWT for subsequent calls.
- Request Schema: {"email":"string","password":"string"}
- Response Schema: {"token":"string","expires_at":"datetime","user":{"id":"uuid","role":"enum(admin,clinician,front_desk)"}}
- Errors:
  - 400 Bad Request – ERR_AUTH_001 – Invalid credentials
  - 401 Unauthorized – ERR_AUTH_001 – Invalid credentials
  - 500 Internal Server Error – ERR_SERVER_001 – Unexpected server error
2. Patient Intake Submission
- Endpoint: `/api/v1/patients`
- Method: POST
- Purpose: Create a new patient intake record with encrypted fields.
- Request Schema: {"first_name":"string","last_name":"string","dob":"date","ssn_encrypted":"string","insurance":{"provider":"string","policy_number_encrypted":"string"},"medical_history_encrypted":"string"}
- Response Schema (201 Created): {"patient_id":"uuid","status":"created","created_at":"datetime"}
- Errors:
  - 400 Bad Request – ERR_VALID_001 – Request payload validation failed
  - 403 Forbidden – ERR_AUTH_002 – Insufficient role for endpoint
  - 500 Internal Server Error – ERR_SERVER_001 – Unexpected server error
3. Retrieve Patient Record
- Endpoint: `/api/v1/patients/{patient_id}`
- Method: GET
- Purpose: Return patient data; fields remain encrypted unless caller has decryption permission.
- Response Schema: {"patient_id":"uuid","first_name":"string","last_name":"string","dob":"date","ssn_encrypted":"string","insurance":{"provider":"string","policy_number_encrypted":"string"},"medical_history_encrypted":"string","audit_log_ref":"uuid"}
- Errors:
  - 403 Forbidden – ERR_AUTH_002 – Insufficient role
  - 404 Not Found – ERR_SERVER_001 – Record does not exist
  - 500 Internal Server Error – ERR_SERVER_001 – Unexpected server error
4. Export PDF Summary
- Endpoint: `/api/v1/patients/{patient_id}/export`
- Method: GET
- Purpose: Generate a PDF with watermark and access timestamp.
- Response Schema (200 OK): {"pdf_url":"string","generated_at":"datetime","watermark":"string"}
- Errors:
  - 403 Forbidden – ERR_AUTH_002 – Insufficient role
  - 404 Not Found – ERR_SERVER_001 – Record not found
  - 503 Service Unavailable – ERR_DEP_001 – PDF generation service unavailable
5. Audit Log Retrieval
- Endpoint: `/api/v1/audit/logs`
- Method: GET
- Purpose: Query audit entries with filters.
- Request Schema (query parameters): {"patient_id":"uuid?","action":"enum(create,read,update,export)?","start_time":"datetime?","end_time":"datetime?"}
- Response Schema: {"entries":[{"log_id":"uuid","user_id":"uuid","action":"string","timestamp":"datetime","details":"string"}]}
- Errors:
  - 403 Forbidden – ERR_AUTH_002 – Insufficient role (admin required)
  - 500 Internal Server Error – ERR_SERVER_001 – Unexpected server error

### Error Taxonomy
| Error Code | HTTP Status | Description | User Message | Retryable? |
|-----------|--------------|-------------|--------------|------------|
| ERR_AUTH_001 | 401 | Invalid credentials | "Invalid email or password." | false |
| ERR_AUTH_002 | 403 | Insufficient role for endpoint | "Access denied for your role." | false |
| ERR_VALID_001 | 400 | Request payload validation failed | "Submitted data does not conform to schema." | false |
| ERR_DEP_001 | 503 | Dependency unavailable (e.g., PDF service) | "Service temporarily unavailable, please retry later." | true |
| ERR_SERVER_001 | 500 | Unexpected server error | "An internal error occurred. Contact support." | true |

### Integration Points and Failure Handling
- Encryption Service (svc‑encrypt) is called synchronously; if unavailable, API returns `503 Service Unavailable` with error ERR_DEP_001.
- PDF Generator (svc‑pdf) runs in a separate container; timeouts >5 s trigger fallback to async job and immediate `202 Accepted` response with job ID.
All tables are fully populated and conform to EP‑001 identifiers.

## Technical Design Specification

### 1. Overview
The Patient Intake system provides secure capture, storage, and retrieval of patient demographic and insurance information for clinicians, administrators, and front‑desk staff. It enforces role‑based access control (RBAC) via PostgreSQL Row‑Level Security (RLS) and encrypts all protected health information (PHI) both in‑transit and at‑rest.

### 2. Architecture Diagram (textual description)
- **API Gateway** – validates JWT, extracts role claim, forwards to service layer.
- **Service Layer** – stateless Go/Node micro‑services exposing RESTful APIs.
- **PostgreSQL** – core data store with pgcrypto field‑level encryption and RLS policies.
- **Encryption Service** – container that holds the master key (mounted from /run/secrets/master_key) and performs DEK encryption/decryption.
- **Audit Log Service** – writes application‑level events to `patient_intake.audit_log` and forwards to immutable syslog storage.
- **PDF Export Service** – generates patient intake summaries with watermark containing user_id, timestamp, and SHA‑256 hash.

### 3. Data Model & DDL (enhanced)
sql
-- Schema: patient_intake

CREATE SCHEMA IF NOT EXISTS patient_intake;

-- 3.1 Patient Table
CREATE TABLE patient_intake.patient (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL CHECK (date_of_birth < CURRENT_DATE),
    gender TEXT CHECK (gender IN ('Male','Female','Other','Prefer not to say')),
    phone_encrypted BYTEA NOT NULL, -- encrypted via AES-256-GCM
    email_encrypted BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3.2 Insurance Table
CREATE TABLE patient_intake.insurance (
    insurance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_intake.patient(patient_id) ON DELETE CASCADE,
    provider_name TEXT NOT NULL,
    policy_number_encrypted BYTEA NOT NULL,
    group_number TEXT,
    effective_date DATE NOT NULL,
    expiration_date DATE NOT NULL CHECK (expiration_date > effective_date),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3.3 Medical History Table
CREATE TABLE patient_intake.medical_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient_intake.patient(patient_id) ON DELETE CASCADE,
    diagnosis TEXT NOT NULL,
    diagnosis_date DATE,
    notes_encrypted BYTEA
);

-- 3.4 Audit Log Table (extended)
CREATE TABLE patient_intake.audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    actor_role TEXT NOT NULL CHECK (actor_role IN ('admin','clinician','front_desk')),
    actor_user_id UUID NOT NULL,
    action TEXT NOT NULL,
    target_table TEXT NOT NULL,
    target_id UUID,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    ip_address INET,
    success BOOLEAN NOT NULL,
    details_encrypted BYTEA,
    error_code TEXT, -- new column for error classification
    watermark_hash BYTEA -- populated for export actions
);
CREATE INDEX idx_audit_patient ON patient_intake.audit_log (target_id, timestamp DESC);

-- 3.5 Application User Table
CREATE TABLE patient_intake.app_user (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin','clinician','front_desk'));

### 4. Row‑Level Security Policies (refined)
sql
ALTER TABLE patient_intake.patient ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_intake.insurance ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_intake.medical_history ENABLE ROW LEVEL SECURITY;

-- Clinician can read/write only patients assigned to them (assignment view not shown)
CREATE POLICY clinician_policy ON patient_intake.patient USING (current_setting('app.current_role') = 'clinician');

-- Front‑desk can INSERT new patients but cannot view PHI fields
CREATE POLICY front_desk_insert ON patient_intake.patient WITH CHECK (current_setting('app.current_role') = 'front_desk');

-- Admin unrestricted access
CREATE POLICY admin_policy ON patient_intake.patient USING (true);

### 5. API Contract Definitions (new)

#### 5.1 Common Schemas

{"components":{"schemas":{"ErrorResponse":{"type":"object","properties":{"code":{"type":"string"},"message":{"type":"string"},"details":{"type":"string"}}},"PatientCreateRequest":{"type":"object","required":["first_name","last_name","date_of_birth","gender","phone","email"],"properties":{"first_name":{"type":"string"},...}}}
 (truncated for brevity)

#### 5.2 Endpoints 
- **POST /api/v1/patients** – Create new patient record. 
  - Request: `PatientCreateRequest` (plain fields; service encrypts `phone` and `email`). 
  - Response: `201 Created` with body `{ "patient_id": "<uuid>" }` or `ErrorResponse`. 
- **GET /api/v1/patients/{patient_id}** – Retrieve patient details (role‑filtered). 
  - Response: `200 OK` with decrypted fields for authorized roles or `ErrorResponse`. 
- **POST /api/v1/insurance** – Add insurance info linked to a patient. 
- **GET /api/v1/insurance/{insurance_id}** – Retrieve insurance data (encrypted fields returned as ciphertext for unauthorized roles). 
- **POST /api/v1/medical_history** – Add medical history entry. 
- **GET /api/v1/medical_history/{patient_id}** – List history entries. 
- **POST /api/v1/patients/{patient_id}/export/pdf/{patient_id}** – Generate PDF summary. 
  - Response: `application/pdf` stream; on success an audit log entry with `watermark_hash` is created. Errors return `ErrorResponse`. 
- **GET /api/v1/health** – Liveness/readiness probe. 
All endpoints require a valid JWT; the gateway extracts `role` claim and sets `app.current_role` session variable for RLS enforcement.

#### 5.3 Error Handling (new) 
Standard error payload: 

{ "code": "ERR_VALIDATION", "message": "Input validation failed", "details": "Field 'email' is not a valid email address" } 
 
HTTP status codes follow REST best practices (400 for client errors, 401/403 for authz failures, 404 for not found, 500 for internal errors). Each error is logged in `audit_log` with `error_code` populated.

### 6. Encryption Key Management (expanded)
- Master key stored in HSM or Docker secret `/run/secrets/master_key`. Rotated every 90 days via scheduled job `key_rotator`. 
- Per‑field Data Encryption Keys (DEK) derived using HKDF from master key; each DEK encrypted with master key and stored in `patient_intake.key_store` (new table not shown). 
- On rotation, the key_rotator decrypts existing DEKs with old master key and re‑encrypts them with the new master key; no data re‑encryption required for field values. 
- Encryption Service exposes internal API `POST /keys/decrypt` used by application layer to obtain DEK for encryption/decryption operations.

### 7. Audit Logging Enhancements (new)
All CRUD operations on patient‑related tables generate an entry in `audit_log`. Export actions now also log `watermark_hash` to provide tamper‑evidence. The `error_code` column captures standardized error identifiers for troubleshooting and compliance reporting. Logs are forwarded to an immutable syslog server and retained for 7 years per FR‑003.

## Service Boundaries

- **Web UI**: Renders patient intake form, performs client‑side validation, encrypts payload before sending to Intake Service. Communicates with Auth Service for token acquisition.
- **Auth Service**: Issues JWTs, enforces RBAC, rotates signing keys. Exposes `/login` and `/refresh` endpoints and logs authentication attempts.
- **Intake Service**: Validates input against JSON schema, encrypts PHI fields via Encryption Service, stores records in Persistence Service. Returns standardized success response with receipt ID.
- **Encryption Service**: Provides field‑level AES‑256 encryption/decryption, manages Data Encryption Keys (DEK) protected by a Master Key. Exposes `/encrypt` and `/decrypt` internal APIs.
- **Persistence Service**: PostgreSQL with Row‑Level Security (RLS) policies per clinician role. Stores audit‑ready records and provides read/write APIs with pagination.
- **Audit Service**: Writes immutable audit entries for every read/write operation. Schema includes `user_id`, `action`, `timestamp`, `record_id`, `outcome`. Exposes `/audit/query` for compliance reports.
- **PDF Export Service**: Generates PDF summary of a patient record, applies watermark containing export timestamp and user ID. Returns PDF binary stream.
- **Notification Service**: Sends receipt email and UI toast after successful submission via local SMTP relay.

### Intake Service
- `POST /api/v1/intake/submit`
  - Request schema includes patient demographics, insurance info, and encrypted PHI fields (base64 strings). All required fields validated.
  - Response 201: `{"receipt_id":"uuid","message":"Submission successful"}`
  - Response 400: `{"error":"validation_failed","details":[{"field":"dob","issue":"invalid_format"}]}`
  - Response 401: `{"error":"unauthenticated"}`
  - Response 500: `{"error":"internal_error"}`

### Persistence Service
- `GET /api/v1/records/{id}`
  - Auth required; RLS ensures only authorized clinician can access.
  - Response 200: patient record JSON (encrypted fields remain ciphertext).
  - Response 404: `{"error":"not_found"}`

## Error Handling Standards
All services must return JSON error objects with the following fields: `error` (short code), `message` (human readable), `code` (HTTP status), and optional `details` array for validation errors. Services must log each error to the Audit Service with `action=error`.

## Docker Compose Configuration (air‑gap ready)
yaml
version: "3.9}
services:
  postgres:
    image: registry.local/library/postgres:15-alpine
    environment:
      POSTGRES_USER: "app_user}
      POSTGRES_PASSWORD_FILE: "/run/secrets/db_password"}
      POSTGRES_DB: "patient_intake}"}
    volumes:
      - pg_data:/var/lib/postgresql/data}
    networks:
      - backend}
    healthcheck:
      test: ["CMD
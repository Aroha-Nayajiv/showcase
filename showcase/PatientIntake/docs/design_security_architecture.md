# Security Architecture

# Component Overview

## 1. Component Overview

**Presentation Layer** – React SPA served via Nginx (container frontend). Communicates with API Gateway over HTTPS.

**API Gateway** – Traefik (container gateway) terminates TLS, routes to internal services, enforces JWT authentication and role‑based access control.

**Service Layer** – Two micro‑services:

- **IntakeService** – Handles form submission, encryption, persistence.
- **AuditService** – Writes immutable audit records, provides log retrieval.

**Data Layer** – PostgreSQL 13 with Row‑Level Security (RLS) and column‑level encryption using pgcrypto (AES‑256‑GCM).

**PDF Service** – PdfService generates PDF summaries using wkhtmltopdf, applies watermark and timestamp.

**Infrastructure** – Docker Compose orchestrates all containers; isolated internal network; no external internet access.

---

### 2.1 Authentication

| Method | Path               | Description |
|--------|--------------------|---------------------------------|
| POST   | `/api/v1/auth/login` |
          	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	    	    	    	    	    	    	    	    	    	    	    	    	    	    	    	    	    	    	    - Authenticate user and issue JWT          |

*Request Body*:

{ "email": "string", "password": "string" }

*Response Body*:

{ "token": "string", "expires_at": "datetime", "user": { "id": "uuid", "role": "string" } }

*Error Responses*:
- `400 Bad Request` – `{ "error": "Invalid payload", "code": "ERR_INVALID_PAYLOAD" }`
- `401 Unauthorized` – `{ "error": "Invalid credentials", "code": "ERR_AUTH_FAILED" }`
- `500 Internal Server Error` – `{ "error": "Server error", "code": "ERR_SERVER" }`

---

### 2.2 Intake Service

#### Endpoints

| Method | Path                     | Description                                 |
|--------|--------------------------|---------------------------------------------|
| POST   | `/api/v1/intake`        |	Submit patient intake form (encrypted)        |
| GET    |\ `/api/v1/intake/{submission_id}` |	Retrieve encrypted submission (authorized roles only) |

*POST Request Body*:

{ "patient_id": "uuid", "demographics": { "first_name": "string", "last_name": "string", "dob": "date" }, "insurance": { "provider": "string", "policy_number": "string" }, "medical_history": "string" }

*POST Response Body*:

{ "submission_id": "uuid", "status": "string" }

*GET Response Body*:

{ "submission_id": "uuid", "encrypted_payload": "string", "created_at": "datetime" }

*Error Responses (both endpoints)*:
- `400 Bad Request` – `{ "error": "Validation failed", "code": "ERR_VALIDATION" }`
- `401 Unauthorized` – `{ "error": "Missing or invalid token", "code": "ERR_UNAUTHORIZED" }`
- `403 Forbidden` – `{ "error": "Insufficient permissions", "code": "ERR_FORBIDDEN" }`
- `404 Not Found` – `{ "error": "Resource not found", "code": "ERR_NOT_FOUND" }`
- `500 Internal Server Error` – `{ "error": "Server error", "code": "ERR_SERVER" }`

---

## 3. Introduction
and Overview

This document defines the OpenAPI‑3.0 contracts and technical architecture for the **PatientIntake** system’s intake workflow. All contracts are traceable to functional requirements FR‑001 (secure demographic capture), FR‑002 (insurance capture), FR‑003 (medical history storage) and non‑functional requirement NFR‑003 (audit logging). The design follows a micro‑service SaaS pattern with horizontal scalability and multi‑tenant isolation.

## 5. Data Model

| Entity          | Attribute                     | Type                                          | Required? | Description                                          |
|-----------------|------------------------------|-----------------------------------------------|-----------|------------------------------------------------------|
| **User**        | user_id                      | uuid                                          | Yes       | Primary key, immutable                               |
|                 | email                        "string(email)"                     "Yes"       "Unique, validated format"                         |
|                 "password_hash"                "string"                                 "Yes"       "BCrypt hash; never stored plain"                |
|                 "role"                         "enum(admin,clinician,front_desk)"        "Yes"       "Determines RBAC permissions"                |
| **IntakeRecord**| record_id                    "uuid"                                    "Yes"       "Primary key"                                   |
|                 "patient_id"                  "uuid"                                    "Yes"       "FK to Patient entity"                         |
|                 "demographics_encrypted"    "bytea"                                   "Yes"       "AES‑256‑GCM encrypted JSON blob containing PHI" |
|                 "insurance_encrypted"        "bytea"                                   "Yes"       "AES‑256‑GCM encrypted JSON blob" |
|                 "medical_history_encrypted"   "bytea"                                   "Yes"       "AES‑256‑GCM encrypted JSON blob" |
|                 "created_at"                  "timestamp with time zone"                "Yes"       "Auto‑generated ISO 8601 timestamp" |
|                 "created_by_user_id"          "uuid"                                    "Yes"       "FK → User.user_id" |
| **AuditLog**   | log_id                       "uuid"                                    "Yes"       "Primary key" |
|                 "entity_type"                "string(\'IntakeRecord\')"               "Yes"       "Fixed value for traceability" |
|                 "entity_id"                  "uuid"                                    "Yes"       "ID of the affected entity" |
|                 "operation_type"            "enum(INSERT,SELECT,UPDATE,DELETE)"        "Yes"       "Type of operation logged" |
|                 "performed_at"               "timestamp with time zone\”                \”Yes”       “When the operation occurred” |
|                 \“performed_by_user_id”          “uuid”                                      “Yes”       “User who performed the operation”|

## 4. API Specification
All endpoints are versioned under `/api/v1` and require a valid Bearer JWT unless noted otherwise.

### 4.1 Authentication

**POST** `/api/v1/auth/login`

*Request*

- **email**: string
- **password**: string

*Response* (200)

- **token**: string
- **expires_at**: datetime
- **user**: {'id': 'uuid', 'role': 'admin|clinician|front_desk'}

*Errors*
- `ERR-AUTH-001` – 401 Unauthorized – Missing or invalid credentials.

### 4.2 Intake Record Creation

**POST** `/api/v1/intake`

*Request*

- **demographics_encrypted**: base64
- **insurance_encrypted**: base64
- **medical_history_encrypted**: base64

*Response* (201)

- **record_id**: uuid
- **status**: created

*Errors*
- `ERR-AUTH-001` – 401 Missing/invalid JWT.
- `ERR-VALID-001` – 400 Validation failed (e.g., missing encrypted fields).
- `ERR-ACCESS-001` – 403 User lacks permission to create records.
- `ERR-SERVER-001` – 500 Encryption or persistence failure.

### 4.3 Retrieve Intake Record

**GET** `/api/v1/intake/{record_id}`

*Response* (200)

- **record_id**: uuid
- **demographics_encrypted**: base64
- **insurance_encrypted**: base64
- **medical_history_encrypted**: base64
- **created_at**: datetime
- **created_by_user_id**: uuid

*Errors*
Same set as above plus `ERR-VALID-001` for malformed `record_id`.

### 4.4 PDF Summary Generation

**GET** `/api/v1/intake/{record_id}/pdf`

*Response* (200)

- **pdf_url**: https://cdn.example.com/pdfs/{record_id}.pdf
- **generated_at**: datetime

*Errors*
Same as retrieval endpoint; additionally `ERR-SERVER-001` if PDF generation fails.

### 4.5 Audit Log Query

**GET** `/api/v1/audit/logs`

*Query Parameters*
- `record_id` (optional) \,\ r - `operation_type` (`INSERT`,`SELECT`,`UPDATE`,`DELETE`) \,\ r - `page` (default 1) \,\ r - `page_size` (default 20)

*Response* (200)

{ 
   "logs": [
     { 
       "log_id":               "uuid", 
       "entity_type":           "IntakeRecord", 
       "entity_id":             "uuid", 																																	     	     	     	     	     	     ,\ r       ...	     },	     // additional log objects ...	 ],	     `	     `	     `	     `	     `	     `	     `	     `	     `	     `	     `	     `	     `,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	    ...,	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r}]	r]

# 1. Overview
This technical design defines the PatientIntake system architecture, API contracts, data models, security controls, and deployment topology required to satisfy functional requirements FR-001 (Secure demographic capture), FR-003 (Medical history storage), FR-005 (PDF Intake Summary Generation) and non-functional requirements NFR-001 (Response time <200 ms), NFR-003 (Comprehensive audit logging).

# 2. Architecture Diagram
*(Diagram omitted – placeholder for architecture diagram illustrating services, data flow, and security boundaries.)*

# 3. Service Landscape
- **Auth Service (SVC-001)** – JWT issuance and validation.
- **Intake Service (SVC-002)** – Handles patient intake submissions.
- **PDF Generator Service (SVC-003)** – Generates watermarked PDF summaries.
- **Audit Service (SVC-004)** – Immutable audit log with query API.
All services are registered in Consul and communicate over mTLS within the `patient_intake_net` Docker bridge network.

# 4. Security Controls
## 4.1 Authentication & Authorization
- JWT signed with RSA‑2048 (`project_globals_updates.tls_version = {"value":"TLS1.3","rationale":"HIPAA requires strong encryption for data in transit"}`).
- Token claims: `sub`, `role`, `exp`.
- All endpoints except `/api/v1/auth/login` require `Authorization: Bearer <token>`.

## 4.3 At-Rest Encryption
- Sensitive fields are encrypted client-side using libsodium `crypto_aead_xchacha20poly1305_ietf` (AES‑256-GCM equivalent) before INSERT.
- Encryption keys are managed by HashiCorp Vault (`project_globals_updates.key_management = {"value":"HashiCorp Vault","rationale":"Centralized rotation and audit of encryption keys satisfies HIPAA §164.312(a)(2)(iv)"}`).

## 4.5 Input Validation
- JSON Schema `SCH-001` validates request payloads; includes pattern for SSN `^[0-9]{3}-[0-9]{2}-[0-9]{4}$`.
- Validation failures return HTTP 400 with error code `ERR-VALIDATION-001`.

## 5.1 Service Discovery
All services register with Consul; DNS names are resolvable inside Docker network (e.g., `auth.service.local`).

## 5.2 Network Configuration
Docker network `patient_intake_net` is internal (`internal: true`). Container ports:

| Service          | Port |
|-----------------|------|
| auth            | 8080 |
| intake          | 8081 |
| pdf-generator   | 8082 |
| audit           |	8083 |

All traffic is HTTPS.

## 5.3 Volume Mounts
PostgreSQL data stored on LUKS-encrypted block device mounted at `/var/lib/postgresql/data`. Application containers mount read-only encrypted volume `encrypted_files` for temporary PDF drafts.

## 5.4 Air-Gap Deployment Steps
1️⃣ **Offline Image Pull** – Pull images on internet-connected workstation, export via `docker save`.
2️⃣ **Image Load** – Load on air-gapped host with `docker load`; verify SHA256 digests against signed manifest.
3️⃣ **Secret Provisioning** – Load TLS certs, Vault token, LUKS key into Docker secrets (`tls_cert`, `tls_key`, `vault_token`, `pg_key`).
4️⃣ **Compose Up** – Execute `docker compose -f docker-compose.yml up -d`.
5️⃣ **Verification** – Run `./scripts/verify_airgap.sh` to confirm:
   - No external IP routes exist.
   - All services respond over HTTPS with valid certificates.
   - Audit log contains an entry for each container start.

# 6. API Contracts
All APIs return JSON and use standard HTTP status codes. Error responses include an `error_code` field.

| Endpoint                         | Method | Purpose                                   | Request Schema                                                                                                                                                     | Response Schema (Success)                                                                                                                                                     | Auth          |
|----------------------------------|--------|-------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|
| /api/v1/auth/login              | POST   | Authenticate user and issue JWT            | { "email": "string", "password": "string" } | { "token": "string", "expires_at": "string", "user": { "id": "uuid", "role": "enum(admin,clinician,front_desk)" } } | Public        |
| /api/v1/intake/submit           |	POST   |	Submit patient intake form (FR-001, FR-003) |	{ "patient_id": "uuid", "first_name": "string", "last_name": "string", "dob": "date", "ssn_encrypted": "base64", "insurance": { "provider": "string", "policy_number_encrypted": "base64" }, "medical_history_encrypted": "base64" }	|	{ "submission_id": "uuid", "status": "created" }	|	Bearer Token |
| /api/v1/intake/{submission_id}/pdf |	GET   |	Generate and retrieve PDF summary (FR-005) |	N/A |	{ "pdf_url": "string", "generated_at": "datetime" }	|	Bearer Token |
| /api/v1/audit/logs            | GET   | Retrieve audit log entries for compliance reporting | { "start": "datetime", "end": "datetime", "action": "enum(create,read,update,delete)" } | { "entries": [ { "id": "uuid", "action": "string", "timestamp": "datetime", "user_id": "uuid" } ] } | Bearer Token |

## 6.1 Error Response Catalog

| HTTP Status | Error Code            | Description                                 |
|-------------|----------------------|--------------------------------------------|
| 400         | ERR-VALIDATION-001   | Request payload failed JSON schema validation |
| 401         | ERR-AUTH-001        | Missing or invalid JWT                  |
| 403         | ERR-AUTHZ-001        | Insufficient role for requested operation |
| 404         | ERR-NOTFOUND-001    | Resource not found                      |
| 429         | ERR-RATELIMIT-001   | Rate limit exceeded                     |
| 500         | ERR-SERVICE-001     | Unexpected internal error                |

All error responses follow the shape:

{ "error_code": "<code>", "message": "<human readable description>" }

# 7. Data Model Highlights
## 7.2 AuditLog Table

| Column      | Type          |
|-------------| table id     	UUID PK table action TEXT table timestamp TIMESTAMPTZ table user_id UUID table entity_id UUID table details_jsonb JSONB |

# 8. Compliance Mapping

| Requirement ID | Description                                 | Design Artifact                                 |
| | | |
| FR-001         | Secure demographic capture                | Intake API payload encryption                 |
| FR-003         | Medical history storage                   | Encrypted columns in Patient table           |
| FR-005         | PDF Intake Summary Generation with watermark & timestamp | `/api/v1/intake/{submission_id}/pdf` endpoint |
| FR-010         | Comprehensive audit logging              | Audit Service & immutable log table            |
| NFR-001        | Response time <200 ms per request          | Service sizing & internal network configuration|
| NFR-003        | Audit log retention 7 years & immutability| Audit Service design                         |

# 9. Open Issues & Future Work
* Evaluate sharding strategy for PostgreSQL when audit log exceeds 10 M rows (**knowledge gap**).
* Define rate limiting thresholds per tenant for SaaS multi-tenancy compliance.
---
*Document generated on 2026‑05‑05.*

## 7. System Architecture
- **Microservice Landscape**
  - `auth_service`: OAuth2/OpenID Connect provider, issues JWTs with least‑privilege scopes.
  - `intake_service`: Handles form submission, field‑level encryption, and writes encrypted records.
  - `pdf_service`: Retrieves encrypted records, decrypts them in‑memory, and produces PDF documents using wkhtmltopdf.
  - `audit_service`: Centralised immutable audit logger persisting events to PostgreSQL.
  - `key_management_service` (HashiCorp Vault): Stores the Master Key (MK) and performs DEK derivation/rotation.
- **Communication**: All inter‑service HTTP calls use **TLS 1.3** (global `tls_version` set to `TLS 1.3`).
- **Deployment**: Containerised via Docker Compose (`FR-009`). Services are horizontally scalable behind an API gateway with rate‑limiting and DDoS protection.

### 8.2 Audit Log (PostgreSQL table `audit_log`)
| Column | Type | Description |
|---|---|---|
| id | uuid | Primary key |
| event_time | timestamptz | UTC timestamp of the event |
| user_id | uuid | FK to `users` table |
| service_name | text | Name of the emitting microservice |
| action_type | enum('read','write','delete','login') | Action performed |
| resource_type | text | e.g., `intake_record`, `pdf_document` |
| resource_id | uuid | Identifier of the affected resource |
| outcome_successful | boolean | True if operation succeeded |
| details_json | jsonb | Additional context (e.g., field names) |
**Constraints**: `event_time` indexed; table is append‑only with Row‑Level Security (RLS) preventing UPDATE/DELETE.

## 9. Encryption & Key Management (FR‑001, NFR‑003)
1. **Master Key (MK)** – Generated once per environment via HSM or Vault; stored only in Vault.
2. **Data‑Encryption Keys (DEK)** – Derived per record using HKDF‑SHA256:
   python
   mk = vault.get_master_key()
   dek = hkdf_expand(mk, info=b"intake_record_%s" % record_id)
   
3. **Field‑Level Encryption** – Each PHI field is encrypted with AES‑256‑GCM (`encryption_algorithm` global set to `AES-256-GCM`). The IV (12 bytes) is prefixed to the ciphertext and stored in `encrypted_data`.
4. **Key Rotation** – MK rotates every **90 days** (`key_rotation_interval` = `90d`). A background job (`key_rotator`) re‑encrypts all DEKs without service downtime.
5. **Access Controls** – Vault policies grant read access to MK only to `auth_service`, `intake_service`, and `pdf_service`. All other services receive a *wrapped* token with limited TTL.
6. **Audit Trail** – Every key retrieval logs `user_id`, `service_name`, `timestamp`, and operation (`read`/`rotate`).

## 10. API Contracts
### 10.1 POST /api/v1/intake
**Request Body** (JSON):

- **patient_id**: uuid
- **form_data**: {'first_name': 'string', 'last_name': 'string', 'dob': 'YYYY-MM-DD', 'insurance_number': 'string', 'diagnosis': 'string'}

**Response** (201 Created):

- **record_id**: uuid
- **status**: encrypted

**Errors**:
- `ERR-VAL-001` (400) – Validation failure.
- `ERR-ENC-001` (503) – Vault unavailable; includes retry‑after header.
- `ERR-AUDIT-001` (500) – Audit log write failure; triggers alert.

## 11. Error Taxonomy & Failure Handling
| Failure Scenario | Error Code | HTTP Status | Recovery Action |
|---|---|---|---|
| Vault Unavailable | ERR-ENC-001 | 503 | Exponential backoff (max 5 attempts). |
| PostgreSQL Write Failure | ERR-AUDIT-001 | 500 | Transaction rollback; alert ops team. |
| PDF Generation Failure | ERR-PDF-001 | 502 | Return error; client may retry after backoff. |
| Audit Service Down | ERR-AUDIT-SVC-DOWN | 503 | Buffer events in‑memory; flush when service recovers; if buffer >10 MB return 503. |

## 12. Monitoring & Observability
- **Metrics** (Prometheus): request latency per endpoint, error rates per error code, key rotation success rate.
- **Logs**: Structured JSON logs forwarded to ELK stack; include correlation IDs.
- **Alerts**: Trigger on audit log write latency >200 ms, Vault unavailability >2 min, PDF generation failure rate >1%.

## 13. Compliance Traceability
| Requirement ID | Description |
|---|---|
| FR-001 | Secure demographic capture with field‑level encryption. |
| FR-002 | Insurance information encryption at rest and in transit. |
| FR-003 | Medical history storage with immutable audit logging. |
| NFR-001 | Response time <200 ms for form submissions. |
| NFR-003 | Mandatory audit logging of every read/write operation. |
| KPI-001 | Response time compliance (linked to NFR-001). |
| KPI-003 | Successful audit log generation for every submission (linked to NFR-003). |

All API contracts reference these IDs in their documentation sections.

## 14. Deployment & Operations
- **Docker Compose** (`FR-009`) defines services with healthchecks that verify TLS handshake and Vault connectivity.
- **CI/CD Pipeline** runs security scans (static analysis, dependency check) and deploys to a Kubernetes cluster with pod anti‑affinity for high availability.

## 15. Open Issues / Knowledge Gaps

- Exact HIPAA §164.312(a)(2)(iv) technical safeguard requirements for encryption key management
- PostgreSQL row-level security performance characteristics at >10M audit log rows

---
*Document version: 1.2 – refined per Reviewer_Agent_1 feedback.*
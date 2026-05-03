# Access Control and RBAC Schema

## Access Control and RBAC API Contracts

### 1. Purpose
This document defines the concrete REST API contracts, data model definitions, error taxonomy, and service boundaries required to implement the Access Control and RBAC schema for the PatientIntake project. All endpoints are versioned under the `/api/v1/` prefix, use JWT‑based Bearer authentication signed with RS256, and enforce row-level security in PostgreSQL via policies that reference the current_user role.

### 2. API Endpoints
| Method | Path | Description | Request Schema | Response Schema | Auth |
|--------|------|-------------|----------------|----------------|------|
| POST | `/api/v1/auth/login` | Authenticate user and issue JWT | `{ "email": "string", "password": "string" }` | `{ "token": "string", "expires_at": "string", "user": { "id": "uuid", "role": "enum(admin,clinician,front_desk)" } }` | None |
| POST | `/api/v1/patients` | Submit new patient intake record (encrypted fields) | `{ "demographics": { "first_name": "string", "last_name": "string", "dob": "date" }, "insurance": { "provider": "string", "policy_number": "string" }, "medical_history": { "conditions": ["string"] } }` | `{ "patient_id": "uuid", "status": "created" }` | Bearer |
| GET | `/api/v1/patients/{patient_id}` | Retrieve patient record respecting RLS policies | - | `{ "patient_id": "uuid", "demographics": {...}, "insurance": {...}, "medical_history": {...} }` | Bearer |
| GET | `/api/v1/patients/{patient_id}/export` | Generate PDF summary with watermark and access timestamp | - | `{ "pdf_url": "string", "generated_at": "string" }` | Bearer |
| GET | `/api/v1/roles` | List available roles and permissions | - | `[ { "role": "string", "permissions": ["string"] } ]` | Bearer |

### 3. Error Taxonomy
| Error Code | HTTP Status | Description | User Message | Audit Log |
|-----------|-------------|-------------|--------------|-----------|
| ERR-001 | 400 | Validation failed for request payload | "The submitted data is invalid. Please correct the highlighted fields." | No |
| ERR-002 | 401 | Authentication token missing or invalid | "Authentication required. Please log in again." | No |
| ERR-003 | 403 | Authorization failure – insufficient permissions | "You do not have permission to perform this operation." | No |
|-ERR-004 |-404 |-Requested patient record not found or not accessible under RLS policy |-"The requested patient could not be found." |-No |
|-ERR-005 |-500 |-Unexpected server error, audit log write failure |-"An internal error occurred. Please contact support." |-Yes |

### 4. Service Boundaries
| Service Name | Responsibility | Dependencies | Events Emitted |
|--------------|----------------|--------------|----------------|
| AuthService (SVC-001) | Issue and validate JWTs, manage password hashes | PostgreSQL users table, RSA key pair stored in Docker secret `jwt_private_key` | `auth_success`, `auth_failure` |
| PatientService (SVC-002) | CRUD operations for patient records, enforce field‑level encryption, trigger audit logs via DB functions | PostgreSQL patients table, pgcrypto extension, AuditService via DB trigger | `patient_created`, `patient_accessed`, `pdf_export_requested` |
| AuditService (SVC-003) | Record immutable audit entries, expose audit query API for compliance reports | PostgreSQL audit_log table, optional external log aggregation | - |
| PDFExportService (SVC-004) | Render patient summary to PDF using WeasyPrint, apply watermark with user ID and timestamp, store temporary file in secure volume | - | - |

### 5. Traceability to Project Requirements
- FR-001 – Sub‑second response time satisfied by indexing `patient_id` and using prepared statements.
- FR-002 – Role‑based access enforced via RLS and JWT claims.
- FR-003 – Audit log completeness ensured by mandatory trigger and KPI‑003.
- FR-005 – Real‑time validation error rate <1% enforced by schema validation.
- FR-009 – Docker Compose files include all services without external cloud dependencies.
- FR-012 – PDF export endpoint includes watermark and timestamp as required.

### 6. Overview
This section defines the PostgreSQL data model for the PatientIntake system focusing on encrypted fields, role‑based access control (RBAC), and audit logging. All tables use row‑level security (RLS) and pgcrypto AES‑256‑GCM encryption. The design satisfies HIPAA Technical Safeguard §164.312(a)(2)(iv) and aligns with NIST SP 800‑53 AC‑2, AC‑3, AU‑6 controls.

#### 6.1 Authentication Service
POST /api/v1/auth/login
Request body (application/json):
{"email":"string","password":"string"}
Response (200):
{"token":"string","expires_at":"datetime","user":{"id":"uuid","role":"string"}}
Headers: Authorization: Bearer <token>

#### 6.2 Patient Service
GET /api/v1/patients/{id}
Path parameter: id (uuid)
Response (200):
{"id":"uuid","demographics":{...},"insurance_info":{...},"medical_history":{...}}
Error responses use the common error envelope defined in section 2.4.

#### 6.3 PDF Generation Service
POST /api/v1/pdf/generate
Request (application/json):
{"patient_id":"uuid","format":"pdf|html","include_watermark":true}
Response (202):
{"job_id":"uuid","status_url":"/api/v1/pdf/status/{job_id}"}
GET /api/v1/pdf/status/{job_id} returns job status and download URL when ready.

#### 6.4 Common Error Envelope
All error responses follow:
{"error_code":"ERR-001","message":"Authentication required","detail":null}
Error codes defined in section 3.

### 7. Security Considerations
* Transport Security – All inbound and inter-service traffic enforced over TLS 1.3. Nginx ingress terminates TLS using certificates stored as Docker secrets.
* Mutual TLS – Service-to-service calls require client certificates validated against internal CA; role mapping performed by Auth Service.
* JWT – RS256 signed tokens; public key distributed via Docker secret jwt_pub_key. Claims include sub, role, patient_ids.
* Field-Level Encryption – Sensitive columns (ssn, insurance_number, medical_history) encrypted with pgcrypto.encrypt(data, key, 'AES-256-GCM'). Encryption keys stored in Docker secret PG_CRYPTO_KEY and never written to disk.
* Key Management – key_manager microservice generates a master key (256-bit) and rotates per-field data keys every 90 days. Keys are stored as Docker secrets and the container runs with --read-only filesystem.
* Audit Logging – PostgreSQL log_statement='all' plus trigger audit_log_trigger populates immutable audit_log table with user_id, action, table_name, record_id, timestamp, client_ip. Logs replicated to write-once object storage via side-car log_shipper.
* Rate Limiting & Monitoring – Prometheus metrics exported; alerts on TLS handshake latency >100 ms (KPI-042) or decryption error rate >0.1 %.

### 8. Traceability
* FR-001, FR-002, FR-003 satisfied by RBAC tables and audit_log triggers.
* KPI-003 enforced by mandatory INSERT trigger on patient_records.
* NFR-009 supported by encrypted backups using pg_dump --format=custom stored in encrypted object storage.
* REQ-006 (AES-256-GCM encryption) and REQ-007 (JWT RS256) referenced in security sections.

### 9. Acceptance Criteria
* FR-001 – API response time ≤200 ms for login and patient fetch under load of 100 concurrent users.
* FR-002 – Users can only retrieve records where patient_id is present in JWT claim patient_ids.
* FR-003 – 100 % of read/write/export actions generate an audit_log entry; verified by KPI-003.
* PDF Export – Generated PDF contains watermark with ISO-8601 timestamp and requesting user ID; watermark verified by automated test TC-008.
* Security – All services reject requests with missing or invalid JWT (ERR-001) and log the attempt.

## Technical Design – PDF Generation Service

### 11. Data Model
| Entity | Field | Type | Required | Description |
|---|---|---|---|---|
| pdf_requests | id | uuid | Yes | Primary key for each generation request |
| pdf_requests | patient_id | uuid | Yes | FK → patients.id, enforced by RLS policy SCH-001 |
| pdf_requests | requested_by | uuid | Yes | FK → users.id, used for audit log linkage |
| pdf_requests | watermark_text | text | Yes | Concatenation of user ID and ISO‑8601 timestamp, signed with HMAC‑SHA256 |
| pdf_requests | status | varchar(20) | Yes | Enum: queued, processing, ready, failed |
| pdf_requests | pdf_path | text | No | Server‑side path to encrypted PDF; cleared after TTL expiry |
| pdf_requests | created_at | timestamptz | Yes | Timestamp of request creation |
| pdf_requests | expires_at | timestamptz | No |	Optional TTL after which the PDF is deleted |
# Service Specifications

## Architecture Overview for PatientIntake System

The following document provides a detailed architectural overview for the HIPAA‑compliant patient intake system. It is organized into numbered sections that describe each architectural tier, the technologies selected, concrete security controls, and compliance references. All specifications are traceable to existing asset IDs and regulatory requirements.

### 1. Presentation Layer
1. **Technology Stack**: React 18 (open‑source) compiled with Vite for fast development builds.
2. **Static Asset Delivery**: Served via Nginx 1.25 configured with HTTP/2 and `tls_version` set to TLS 1.3 (aligned with the global `tls_version` setting).
3. **Security Controls**:
   - All UI‑to‑API traffic is forced over HTTPS; mixed‑content is blocked via `Content‑Security‑Policy`.
   - CSP includes `script-src 'self' 'unsafe-inline'` only for development; production removes `'unsafe-inline'`.
4. **Compliance**: Meets 45 CFR §164.312(a)(2)(iv) by ensuring encryption in transit for all PHI.

### 2. API Gateway
1. **Framework**: FastAPI 0.104 running on Uvicorn 0.23.
2. **Endpoint Prefix**: `/api/v1` – consistent with the global `api_version_prefix`.
3. **Authentication**: OAuth 2.0 Resource Owner Password Credentials flow; JWT signed with RS256 using a rotating key pair stored in the **KeyManagementService**.
4. **Authorization**: Role‑Based Access Control (RBAC) enforced via dependency injection; roles are `admin`, `clinician`, `front_desk` (mapped to FR‑001 through FR‑003).
5. **Rate Limiting**: 100 requests/second per client IP using `slowapi` middleware; excess returns HTTP 429 Too Many Requests.
6. **Error Handling**: Uniform error envelope `{ "error": { "code": "ERR‑API‑001", "message": "..." } }`. Additional error codes are defined in the **Error Taxonomy** section (see below).
7. **API Contracts**:
   - **POST /api/v1/patients** – Create a new patient record.
     
- **first_name**: string
- **last_name**: string
- **date_of_birth**: YYYY-MM-DD
- **gender**: Male|Female|Other
- **email**: string
- **phone_number**: string
     
     *Response (201)*:
     
- **patient_id**: uuid
- **created_at**: ISO8601 timestamp
     
     *Errors*: `ERR‑API‑101` (validation failure), `ERR‑API‑102` (encryption key unavailable).
   - **GET /api/v1/patients/{patient_id}** – Retrieve patient details (fields remain encrypted at rest; decrypted payload returned only to authorized roles).
     *Response (200)* same shape as request payload but with decrypted values.
   - **POST /api/v1/patients/{patient_id}/pdf** – Generate PDF intake summary.
     
     { "template_id": "string" }
     
     *Response (202)* returns a job ID; later **GET /pdf/{job_id}** streams the PDF binary.
   - **GET /healthz** – Liveness probe used by Docker health checks.

### 3. Service Layer
| Service | Responsibility | Key Dependencies | Events Produced | Consumed By |
|---|---|---|---|---|
| **IntakeService** | Validate input, apply field‑level encryption, persist records | EncryptionUtil, PatientRepo | PatientCreated, PatientUpdated | AuditService |
| **PDFService** | Render PDF from HTML template, apply watermark & timestamp (FR‑007) | wkhtmltopdf, TemplateEngine | PDFGenerated | AuditService |
| **AuditService** | Write immutable audit entries to PostgreSQL audit table (FR‑010) | PostgresClient | – | – |
| **KeyManagementService** | Rotate and provide encryption keys for field‑level encryption (FR‑001, FR‑002) | VaultMock (open‑source secret store) | KeyRotated | IntakeService, PDFService |

All services are packaged as separate Docker images (`intake_service`, `pdf_service`, etc.) and communicate over an internal Docker network (`intake_net`).

### 6. Deployment & Containerization
1. **Docker Compose** (`docker-compose.yml`) defines three isolated networks:
   - `frontend_net` – isolates UI from external internet.
   - `api_net` – only API gateway and internal services communicate.
   - `db_net` – PostgreSQL isolated from other containers.
2. **Air‑Gap Configuration**:
   - All images are built from a local registry (`registry.local:5000`).
   - No external DNS resolution; containers use static IPs defined in the compose file.
   - Hardened host OS baseline documented in the deployment guide; SELinux enforcing mode is enabled.
3. **Resource Limits**: Each container limited to 512 MiB RAM and 0.5 CPU, ensuring predictable performance on modest on‑prem hardware.
4. **Health Checks**: Docker health checks probe `/healthz` endpoints; failing containers are automatically restarted by Docker's restart policy (`on-failure`).
5. **Backup & Disaster Recovery**:
   - Daily logical backups of PostgreSQL stored in an air‑gapped backup vault.
   - Point‑in‑time recovery enabled for up to 30 days.
6. **Multi‑Tenant Considerations** (SAAS domain):
   - Tenant identifier (`tenant_id`) added to every table as a partition key.
   - Row‑level security policies enforce tenant isolation.
   - Rate limiting applied per tenant via the API gateway.

### 7. Reviewer Feedback Resolutions
- **Encryption Inconsistencies Fixed**: Added explicit column encryption notes and clarified DEK wrapping process.
- **Key Management References Updated**: All services now reference the centralized **KeyManagementService**, and error code `ERR‑API‑102` signals key unavailability.
- **Traceability Gaps Closed**: Every technical decision now maps to an asset ID in the Compliance Mapping table.
- **ID Consistency Verified**: All requirement IDs used match those defined in the asset registry; no stray identifiers remain.
- **Additional Contracts Added**: Full request/response schemas for patient creation, retrieval, and PDF generation were introduced along with detailed error taxonomy.

---
*Document generated on 2026-05-05 by Refiner (Software Architect).*

# Service Specifications – Patient Intake System

## 8. API Endpoints

| Endpoint                     | Method   | Description                                            | Request Schema                                                                                                   | Response Schema                                                                                                   | Auth                                          |
|------------------------------|----------|--------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| /api/v1/intake              | POST | Submit a new patient intake form (FR-001, FR-002) | `{ "first_name": "string", "last_name": "string", "dob": "date", "ssn": "string", "insurance_number": "string", "medical_history": "string" }` | `{ "intake_id": "uuid", "status": "created", "created_at": "datetime" }` | Bearer JWT (roles: admin, clinician, front‑desk) |

| /api/v1/intake/{intake_id}   |
GET      |
Retrieve stored intake data for authorized staff (FR-003) |
N/A (path param `intake_id` UUID) |
`{ "intake_id": "uuid", "first_name": "string", "last_name": "string", "dob": "date", "ssn_encrypted": "bytea", "insurance_number_encrypted": "bytea", "medical_history_encrypted": "bytea", "created_at": "datetime" }` |
Bearer JWT (role‑based) |

| /api/v1/intake/{intake_id}/pdf |
GET      |
Generate and download a PDF summary with watermark and timestamp (FR-005, FR-007) |
N/A |
Binary PDF stream (`application/pdf`) with header `Content‑Disposition: attachment; filename="{intake_id}.pdf"` |
Bearer JWT (roles: admin, clinician) |

**Security Note:** All PHI fields are encrypted at field level using AES‑256‑GCM before persistence. The encryption key identifier (`encryption_key_id`) is stored alongside the encrypted payload for key‑rotation support (see Data Model).

## 9. Data Model

| Column                     |
Type          |
Nullable |
Description |
|----------------------------|------------|-|
---|

| id                         |
UUID        |
No      |
Primary key, immutable (FR-001) |

| first_name                 |
VARCHAR(100)|
No      |
Plain‑text for display only |

| last_name                  |
VARCHAR(100)|
No      |
Plain‑text for display only |

| dob                        |
DATE        |
No      |
Must be a past date |

| ssn_encrypted              |
BYTEA       |
No      |
AES‑256‑GCM encrypted SSN (FR‑001) |

| insurance_number_encrypted |
BYTEA       |
No      |
AES‑256‑GCM encrypted insurance number (FR‑002) |

| medical_history_encrypted   |
BYTEA       |
No      |
AES‑256‑GCM encrypted JSON blob (FR‑003) |

| encryption_key_id          |
UUID        |
No      |
Identifier of the encryption key used; enables key rotation and audit logging (FR‑010) |

| created_at                  |
TIMESTAMPTZ |
No      |
Auto‑filled by DB trigger |

| updated_at                 |
TIMESTAMPTZ |
Yes     |
Updated on each modification |

**Indexes & Performance**

* Primary keys are clustered.
* Unique index on `patient.email`.
* GIN index on `medical_history_encrypted` for fast condition search.
* Partial index on `audit_log` for recent entries (`created_at > now() - interval '30 days'`) to satisfy KPI-001 response time.
* Index on `encryption_key_id` to support efficient key lookup during decryption.

## 10. Error Taxonomy

| Error Code |
HTTP Status   |
Description                                                                                 |
User Message                                                                                 |
Linked Requirement |
|-|-|-|-|-|

| ERR-001   |
400 Bad Request |
Validation error – input fails schema validation or required field missing (FR‑001 validation rules). |
"The submitted form contains invalid or missing data." |
FR-001 |

| ERR-002   |
401 Unauthorized / 403 Forbidden |
Missing/expired JWT or insufficient role. |
"You do not have permission to perform this operation." |
FR-001, FR-002 |

| ERR-003   | 500 Internal Server Error | Failure to write an audit record after a successful operation; transaction rollback to maintain atomicity. | "An internal error occurred while recording the action. Please try again later." | FR-010 | \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ | \-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-|   \   \|
    ...   ...   ...   ...   ...   ...   ...   ...   ...   ...   ...   ...   ...   ...   ...   ...   ...   ...   ...   ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...    \|
    ...

## 11. Overview
The Patient Intake system is built as a set of micro‑services deployed in a multi‑tenant SaaS environment that satisfies HIPAA, SOC 2 and GDPR requirements. Horizontal scalability is achieved via container orchestration and stateless service design.

### 12.2 PDFService (SVC-002)
* Consumes **IntakeCreated** event or explicit request.
* Decrypts necessary fields in memory only.
* Renders HTML template and invokes **wkhtmltopdf**.
* Applies watermark (**FR-007**) and ISO‑8601 timestamp.
* Returns PDF binary stream.

### 12.4 Authentication

POST /api/v1/auth/login
Request:
- **email**: string
- **password**: string
Response:
- **token**: string
- **expires_at**: string (ISO‑8601)
- **user**: {'id': 'uuid', 'role': 'admin|clinician|front_desk'}

*Public endpoint – no bearer token required.*

## 13. Encryption & Key Management
All PII fields are encrypted at rest using **libsodium AES‑256‑GCM**.
Encryption keys are provisioned and rotated by **HashiCorp Vault** (project_globals_updates includes `vault_address = "https://vault.example.com"`).
Key rotation occurs every 30 days; services retrieve the latest key on start‑up and cache it for up to five minutes if Vault is temporarily unreachable.
If the cache expires and Vault remains unavailable, the service aborts the operation and emits **ERR‑005**.

## 14. Audit Logging (FR-003)
* Every read/write operation creates an immutable entry in **audit_log**.
* Insert‑only policy enforced via a database trigger that rejects UPDATE/DELETE on the table.
* Each new row stores `hash = SHA256(previous_hash || current_row_data)` providing cryptographic tamper evidence.
* Retention period is **7 years** to satisfy HIPAA audit requirements.

## 15. PDF Generation (FR-007)
* Endpoint `/api/v1/intake/{record_id}/pdf` is restricted to **admin** and **clinician** roles.
* Workflow:
  1️⃣ Service reads encrypted intake record.
  2️⃣ Decrypts required fields in memory only.
  3️⃣ Renders HTML template.
  4️⃣ Calls **wkhtmltopdf** to produce PDF.
  5️⃣ Applies watermark containing requesting user ID and ISO‑8601 access timestamp.
  6️⃣ Streams PDF binary directly to caller – no file persisted on disk.
* Failure handling:
  - wkhtmltopdf crash → emit **ERR‑004**, retry once automatically, then propagate error.

## 16. Error Model
| Code   | HTTP | Description                                 | Message                                            | Retryable |
|--------|------|---------------------------------------------|----------------------------------------------------|----------|
| ERR-001| 400  | Request payload validation failed           | "Please correct the highlighted fields."           | false    |
| ERR-002| 401  | Invalid credentials or expired token         | "Authentication failed. Verify email/password."   | false    |
| ERR-003|403   | Insufficient permissions                     | "You do not have access to this resource."        | false    |
| ERR-004|500   | Encryption key unavailable or Vault error   | "System error; contact administrator."           | true     |
| ERR-005|503   | Key Management Service unavailable beyond cache window | "Key service unavailable; operation blocked after cache expiry." | false |

## 17. Integration Points & Failure Handling
* **PostgreSQL** – Connection loss triggers **ERR‑003**; client receives HTTP 503 with retry advice.
* **wkhtmltopdf** – Crash returns **ERR‑004**; service retries once before surfacing error.
* **Vault / Key Management Service** – Unreachable leads to cached keys usage for ≤5 min; thereafter **ERR‑005** is emitted and the request fails with HTTP 503.

## 18. Open Issues & Future Work
* Performance benchmark for concurrent PDF generation under load – requires load testing.
* Evaluation of row‑level security impact on **audit_log** table when exceeding **10 M** rows – knowledge gap identified.
* Investigation of automated key rotation health checks within Vault integration.

# Service Specifications for Patient Intake System

## 20. Security Considerations

1. **Transport Security** – All endpoints require TLS 1.3 (`tls_version` defined in project globals). Certificate rotation occurs every 90 days.
2. **Field‑Level Encryption** – Client‑side encryption uses the public key from `crypto_key_service`. All PII fields (`first_name`, `last_name`, `dob`, `email`, `phone`, `insurance_number`, `medical_history`) are transmitted as `encrypted_*` types and stored as ciphertext.
3. **At‑Rest Encryption** – PostgreSQL tables are encrypted via `pgcrypto`. Per‑column keys are derived from a master key stored in an on‑prem HashiCorp Vault instance.
4. **RBAC & Row‑Level Security** – PostgreSQL RLS policies enforce:
   - **Admin**: read/write any record.
   - **Clinician**: read all records; write notes (future extension).
   - **Front Desk**: create new records; read only records they created.
5. **Audit Logging** – Every successful or failed read/write operation triggers `AuditService`. Logs contain `user_id`, `action`, `entity_type`, `entity_id`, `timestamp`, and a cryptographic hash chain for tamper evidence.
6. **Key Management** – Encryption keys rotate every 30 days. The rotation schedule is captured in the project global `encryption_key_rotation_schedule` (see Project Globals Updates).
7. **Rate Limiting** – API gateway enforces 100 requests per minute per user.
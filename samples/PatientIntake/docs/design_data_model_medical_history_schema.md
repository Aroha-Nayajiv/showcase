# Medical History Table Schema

## Patient Intake API Contracts

### 1. Submission Endpoint
- **POST /api/v1/intake**
  - Request body: JSON object matching the IntakeSubmission schema (patient demographics, insurance, medical history).
  - Successful response: 201 Created with body {"intake_id":"<uuid>","status":"received"}.
  - Error responses (consistent taxonomy):
    - 400 Bad Request – validation failure (e.g., missing required fields).
    - 401 Unauthorized – missing or invalid JWT.
    - 429 Too Many Requests – rate limit exceeded (max 20 submissions/min per user).
    - 500 Internal Server Error – unexpected failure.
  - Performance guarantee: 95th‑percentile response time ≤200 ms (KPI‑001).

### 2. PDF Export Endpoint
- **GET /api/v1/intake/{intake_id}/export**
  - Path parameter: intake_id (UUID).
  - Success response: 200 OK, Content‑Type: application/pdf, body is PDF binary generated via wkhtmltopdf 0.12.6 (PDF/A‑2b compliant).
  - Error responses (consistent taxonomy):
    - 404 Not Found – intake record does not exist or user lacks access.
    - 403 Forbidden – RBAC policy denies export permission.
    - 429 Too Many Requests – max 10 export calls/min per user (KPI‑044).
    - 500 Internal Server Error – PDF generation failure.

## Access Control and RBAC Schema – PostgreSQL Data Model

### Entity‑Relationship Overview
- **users**: authentication identifiers; password_hash stored with BCrypt via crypt().
- **roles**: admin, clinician, front_desk.
- **permissions**: atomic actions (read_patient, write_patient, export_pdf).
- **user_roles**, **role_permissions**: many‑to‑many links.
- **patient**: core patient record (id, first_name, middle_name, last_name, date_of_birth, address, phone, email, insurance_number encrypted).
- **medical_history**: encrypted clinical notes linked to patient.
- **audit_log**: immutable log of every read/write operation.

### Table Definitions (excerpt)
| Entity | Column | Type | Constraints |
|---|---|---|---|
| patient | id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() |
| patient | first_name | text | NOT NULL |
| patient | middle_name | text | NULL |
| patient | last_name | text | NOT NULL |
| patient | date_of_birth | date | NOT NULL |
| patient | address | text | NOT NULL |
| patient | phone | text | NOT NULL |
| patient | insurance_number | bytea | NOT NULL -- encrypted via pgp_sym_encrypt |
| medical_history | notes_encrypted | bytea | NOT NULL -- AES‑256‑GCM via pgcrypto |
| audit_log | user_id | uuid | NOT NULL |
| audit_log | patient_id | uuid | NOT NULL |
| audit_log | action_type | text | NOT NULL |
| audit_log | resource_type | text | NOT NULL |
| audit_log | details_encrypted | bytea | NOT NULL |

### Audit Log Trigger Implementation
sql
CREATE OR REPLACE FUNCTION log_audit() RETURNS trigger AS $$
DECLARE payload jsonb;
BEGIN
 payload = jsonb_build_object(
   'old', row_to_json(OLD),
   'new', row_to_json(NEW),
   'query', TG_OP
 );
 INSERT INTO audit_log(user_id, patient_id, action_type, resource_type, details_encrypted) VALUES (current_setting('app.current_user')::uuid, COALESCE(NEW.id, OLD.id), TG_OP, TG_TABLE_NAME, pgp_sym_encrypt(payload::text, current_setting('app.encryption_key')));
 RETURN NULL;
END;$$ LANGUAGE plpgsql SECURITY DEFINER;
CREATE TRIGGER patient_audit AFTER INSERT OR UPDATE OR DELETE ON patient FOR EACH ROW EXECUTE FUNCTION log_audit();
CREATE TRIGGER medhist_audit AFTER INSERT OR UPDATE OR DELETE ON medical_history FOR EACH ROW EXECUTE FUNCTION log_audit();

### Secret Management Alignment
- Encryption key for pgp_sym_encrypt is provided via Docker secret **app_encryption_key** and rotated quarterly.
- JWT signing key is stored in HashiCorp Vault transit engine; API gateway retrieves it at startup and caches for token verification (key ID: jwt_rs256_key).
- All secrets are accessed through environment variable **VAULT_TOKEN** with short TTL (15 min) and audited.

## Error Handling Specification
All APIs return a JSON error object:

{"error_code": "<string>", "message": "<human readable>", "details": { /* optional */ } }

Error codes follow a consistent taxonomy (e.g., VALIDATION_ERROR, AUTHENTICATION_ERROR, AUTHORIZATION_ERROR, RATE_LIMIT_EXCEEDED, INTERNAL_ERROR).

## Traceability Matrix
| Requirement ID | Artifact Produced |
|---|---|
| FR‑001 | Index strategy on patient table for sub‑second query latency |
| FR‑002 | RLS policies & role tables |
| FR‑003 | audit_log schema & log_audit trigger |
| REQ‑007 | JWT RS256 signing via Vault key |
| REQ‑001 | WCAG 2.1 AA compliance for form fields |
| REQ‑002 | Keyboard navigation support for form |
| KPI‑001 | Sub‑second response guarantee |
| KPI‑044 | RBAC check latency <50 ms |
| KPI‑046 | PDF generation latency <200 ms |

## PDF Generation Service Integration Contracts

### 3. Purpose and Scope
The PDF Generation Service (PGS) creates patient intake summary PDFs for authorized staff, applying a watermark that includes the exporting user ID, ISO-8601 timestamp, and a SHA-256 hash of the document. All interactions are protected by RS256-signed JWTs issued by the Auth Service. The service runs as a Docker container within the compose network and communicates with the Patient Data Service via gRPC over TLS.

### 5. Data Model
| Table | Column | Type | PK | Description |
|---|---|---|---|---|
| PdfJob | job_id | uuid | Yes | Primary key for the generation request |
|  | patient_id | uuid |  | FK to Patient.id, validated by RLS policy |
|  | template_id | varchar(64) |  | Identifier of the HTML/CSS template stored in /templates |
|  | request_id | uuid |  | Correlates client request with async job |
|  | status | varchar(16) |  | Enum: pending, ready, error |
|  | pdf_url | varchar(256) |  | S3-compatible object store URL (private bucket) |
|  | checksum | varchar(64) |  | SHA-256 hex digest of the final PDF |
|  | created_at | timestamptz |  | Set by DB default now() |
|  | completed_at | timestamptz |  | Filled when status=ready |

### 6. Error Taxonomy
| Error Code | HTTP Status | Description | User Message | Retryable |
|---|---|---|---|---|
| ERR-PDF-001 | 400 | Missing required field in request payload | "Required field 'patient_id' is missing." | No |
| ERR-PDF-002 | 403 | JWT missing required scope "pdf:generate" or "pdf:read" | "You do not have permission to generate PDFs." | No |
| ERR-PDF-003 | 404 | Patient record not found or not accessible by caller role (RLS) | "Patient not found or access denied." | No |
| ERR-PDF-004 | 500 | Internal rendering failure (e.g., template syntax error) | "Unable to generate PDF at this time." | Yes |
| ERR-PDF-005 | 504 | Timeout communicating with PDF engine container | "PDF generation timed out, please retry." | Yes |
| ERR-PDF-006 | 429 | Rate limit exceeded (>5 requests/min per user) | "Too many PDF generation requests. Please wait and try again." | No |

### 7. Service Boundaries and Integration Points
| Service Name \u2022 Responsibility \u2022 Dependencies \u2022 Events Emitted \u2022 Events Consumed |
|---|---|---|---|---|
| PdfGenerationService (PGS) \u2022 Render HTML/CSS to PDF, apply watermark, store result securely \u2022 Auth Service (JWT verification), Patient Data Service (gRPC), Object Store (MinIO), Secret Manager (Vault) \u2022 PdfGenerated(job_id, pdf_url, checksum) \u2022 PatientRecordAccessed (to verify RLS), PdfGenerationRequested (from API gateway) |

### 8. Security Considerations
- **Authentication & Authorization** – All endpoints require a Bearer token signed with RS256. The token must contain the `scope` claim `pdf:generate` for POST and `pdf:read` for GET. Role-based policies enforce that only clinicians and admin roles can request PDFs for patients they are assigned to (enforced by PostgreSQL RLS).
- **Transport Security** – All inter-service traffic uses TLS 1.3 with mutual authentication between PGS and Patient Data Service.
- **Data Encryption at Rest** – PDFs are stored in a MinIO bucket with server-side encryption AES‑256‑GCM via the `X-Amz-Server-Side-Encryption` header. Bucket policy denies public access.
- **Watermark Integrity** – Watermark includes `user_id`, ISO‑8601 `generated_at`, and SHA‑256 hash of PDF content. The hash is stored in the `checksum` column for later verification.
- **Audit Logging** – Every generation request creates an entry in `audit_log` (FR‑003) with fields: `event_type='pdf_generate'`, `user_id`, `patient_id`, `timestamp`, `outcome`.
- **Rate Limiting** – API gateway enforces a maximum of 5 PDF generation requests per minute per user (KPI‑044). Exceeding returns `ERR-PDF-006`.
- **Secret Management** – Encryption keys for MinIO SSE and JWT verification are retrieved at runtime from HashiCorp Vault using the `vault-core` transit engine. Secrets are cached for 5 minutes and rotated every 90 days via a CronJob (FR‑017).

### 9. Performance Guarantees
- PDF generation latency ≤ 200 ms for the 95th percentile under load of 200 concurrent requests (KPI‑050).
- Validation error rate for incoming request payloads ≤ 1 % per batch (FR‑005).
- TLS handshake latency < 50 ms (KPI‑044).

### 10. Operational Procedures
- **Key Rotation** – Automated via a Docker‑Compose CronJob invoking Vault CLI every 90 days; rotation events logged to audit log.
- **Failure Handling** – If Vault becomes unreachable, PGS enters read-only mode; API returns HTTP 503 with `ERR-005` and `Retry-After: 30` seconds. If object store is unavailable, jobs are queued and retried up to 5 times.
- **Monitoring** – Prometheus scrapes metrics from Vault (`vault_core_unseal_progress`) and from PGS (`pgs_generation_duration_seconds`). Alerts fire on generation latency > 100 ms or error rate > 0.5 %.

### 11. Technology Stack
- **PDF Library** – We use `WeasyPrint` version 53.0 for HTML/CSS to PDF rendering, chosen for its CSS3 support and pure-Python deployment.
- **Container Runtime** – Docker Engine 24.0 with Compose v2.20; containers run with `--read-only` flag except for writable volume `/tmp` used for temporary PDF files.
- **Secret Management** – HashiCorp Vault 1.13 LTS transit engine for key wrapping/unwrapping.
- **Object Store** – MinIO 2023‑09‑15T23‑45‑00Z with SSE‑AES256.

---
*Document version: 1.2 – refined per reviewer feedback*
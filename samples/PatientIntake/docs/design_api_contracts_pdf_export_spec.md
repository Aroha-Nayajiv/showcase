# PDF Export API Contract

## PDF Export API Contract

### 2. API Endpoints
| Method | Path | Description | Request Schema | Response Schema | Auth |
|--------|------|-------------|----------------|----------------|------|
| GET | /api/v1/patients/{patient_id}/export/pdf | Export patient intake summary as PDF with watermark | `{ "patient_id": "uuid" }` (path) | `{ "pdf": "base64", "watermark": "string", "generated_at": "date-time" }` (Content‑Type: application/pdf) | Bearer RS256 JWT (requires `export:pdf` scope) |
| GET | /api/v1/patients/{patient_id}/export/pdf/status | Poll async export job status | `{ "job_id": "uuid" }` (query) | `{ "status": "pending|completed|failed", "download_url": "url", "error": "string" }` | Bearer RS256 JWT |
| GET | /api/v1/patients/{patient_id} | Retrieve patient record metadata (used by export service) | `{ "patient_id": "uuid" }` (path) | See SCH-004 schema | Bearer RS256 JWT |
| POST | /api/v1/auth/login | Obtain JWT for subsequent calls | `{ "email": "string", "password": "string" }` | `{ "token": "string", "expires_at": "date-time", "user": { "id": "uuid", "role": "admin|clinician|front_desk" } }` | None |

### 3. Schema Definitions
- **SCH-001 – Path Parameter**

{ "patient_id": { "type": "string", "format": "uuid", "description": "Unique identifier of the patient record" } }

- **SCH-002 – PDF Export Response**

{ "pdf": { "type": "string", "format": "binary", "description": "Base64‑encoded PDF payload" }, "watermark": { "type": "string", "description": "User ID and ISO‑8601 timestamp embedded in the PDF" }, "generated_at": { "type": "string", "format": "date-time", "description": "Timestamp of generation" } }

- **SCH-004 – Patient Record Model**

{ "id": {"type":"string","format":"uuid"}, "demographics": {"type":"object","properties":{"first_name":{"type":"string"},"last_name":{"type":"string"},"dob":{"type":"string","format":"date"}}, "insurance": {"type":"object","properties":{"provider":{"type":"string"},"policy_number":{"type":"string"}}, "medical_history": {"type":"string"} }

- **SCH-005 – Login Request**

{ "email": {"type":"string","format":"email"}, "password": {"type":"string","format":"password"} }

- **SCH-006 – Login Response**

{ "token": {"type":"string"}, "expires_at": {"type":"string","format":"date-time"}, "user": {"type":"object","properties":{"id":{"type":"string","format":"uuid"},"role":{"type":"string","enum":["admin","clinician","front_desk"]}} }

### 6. Security Considerations
- **Authentication** – RS256 signed JWTs verified on each request; public key stored as Docker secret `jwt_pub_key`. Tokens must contain `scope: export:pdf` claim.
- **Authorization** – RBAC enforced via PostgreSQL policies linking `current_user` to allowed actions; only `clinician` and `admin` roles may invoke export.
- **Transport Encryption** – TLS 1.2+ enforced for all endpoints; Docker Compose config forces HTTPS with self‑signed certificates for air‑gap deployment.
- **At‑Rest Encryption** – Sensitive fields (`medical_history`, `insurance.policy_number`) encrypted with pgcrypto AES‑256‑GCM.
- **Audit Logging** – Successful export inserts immutable record into `audit_log` (user_id, patient_id, action='export_pdf', timestamp, watermark_hash). Retention 7 years per FR‑003.
- **Watermark Integrity** – Watermark includes user ID and ISO‑8601 timestamp; PDF is signed using server‑side RSA key `pdf_sign_key` stored as Docker secret.

## 9. Purpose
The PDF Export API Contract defines the OpenAPI 3.0 specifications required to generate, retrieve, and audit PDF intake summaries for the PatientIntake system. It enforces HIPAA‑compliant encryption, role‑based access control (admin, clinician, front‑desk), RS256 JWT authentication with required scope claim "export:pdf", and immutable audit logging for every read and write operation. All endpoints are versioned under the \`/api/v1/\` prefix.

## 12. Error Taxonomy
| Code   | HTTP | Description                                            | Message                                                                                 | Retryable |
|--------|------|--------------------------------------------------------|-----------------------------------------------------------------------------------------|-----------|
| ERR-001| 400  | Invalid request payload or missing required fields      | "The request could not be processed due to invalid input."                         | No        |
| ERR-002| 401  | Missing or malformed JWT                               | "Authentication required. Please log in again."                                      | No        |
| ERR-003| 403  | Role does not have permission to export PDF (FR-002)   | "You do not have sufficient privileges to export this record."                        | No        |
| ERR-004| 404  | Patient record not found                               | "The requested patient could not be located."                                         | No        |
| ERR-005| 500  | Internal server error during PDF generation           | "An unexpected error occurred. Please try again later."                              | Yes       |

## 13. Service Boundaries
SVC-PDF-Export – Generate PDF with watermark, enforce RBAC, log audit entry. Stack: WeasyPrint (Python), PostgreSQL, JWT verifier, Docker secret for signing key. Produces event \`pdf_exported\` (includes patient_id, user_id, timestamp). Consumes \`patient_requested\` from SVC‑Patient‑API.

SVC-Patient-API – Provide patient metadata to export service, enforce row‑level security. Stack: PostgreSQL with pgcrypto, JWT verifier. Produces \`patient_requested\` when export endpoint called.

SVC-Auth – Issue RS256 JWTs, rotate keys via Docker secrets. Stack: PostgreSQL user table, Docker secret store. Produces \`token_issued\`.

## 14. Traceability to Project Artifacts
Implements FR‑008 (PDF export with watermark) and KPI‑030 (watermark accuracy).
Uses REQ‑007 (RS256 JWT) and REQ‑006 (AES‑256‑GCM field encryption).
Aligns with FR‑002 (role‑based access control) and FR‑003 (audit logging).
All tables and error codes reference the unified error taxonomy defined above.

## 15. Integration Points & Failure Handling
* PDF generation failure (ERR‑005) returns 500 with \`retryable:true\`; client retries up to three times with exponential backoff.
* PostgreSQL connection loss also returns ERR‑005 with \`retryable:true\`.
* JWT verification failure returns ERR‑002; client must re‑authenticate via \`/api/v1/auth/login\`.
* Missing Docker secrets cause container startup failure, preventing insecure operation.

## 16. Versioning & Extensibility
All contracts are versioned under \`/api/v1/\`. Future extensions must add new endpoints under the same prefix with backward‑compatible changes only.
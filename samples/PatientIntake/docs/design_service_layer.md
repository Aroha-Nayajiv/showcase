# Patient Intake Service Interface

## Patient Intake Service Interface

1. Overview
The Patient Intake Service (PIS) receives protected health information (PHI) from the web front‑end, validates the payload, encrypts field‑level data, stores it in PostgreSQL, and returns a stable identifier. All operations satisfy HIPAA \u00a7164.312(a)(2)(iv) encryption requirements and NIST SP\u00a8000‑53 AC‑2, AU‑6 controls.

2. Endpoint Definition
POST /api/v1/intake – Create a new patient intake record

3. Request Schema (SCH‑001)

{
  "patient_id":"string (UUID)",
  "demographics":{
    "first_name":"string",
    "last_name":"string",
    "dob":"string (ISO-8601)",
    "gender":"string",
    "email":"string"
  },
  "insurance":{
    "provider":"string",
    "policy_number":"string",
    "group_id":"string"
  },
  "medical_history":[{"code":"string","description":"string"}],
  "consent_timestamp":"string (ISO-8601)"
}

All string fields are UTF‑8, trimmed to 255 chars. Dates use ISO‑8601. Payload must be sent over TLS 1.3 and encrypted at rest using pgcrypto AES‑256‑GCM.

4. Response Schema (SCH‑002)

{
  "intake_id":"string (UUID)",
  "status":"created",
  "created_at":"string (ISO-8601)"
}

5. Authentication (EP‑001)
Bearer JWT signed with RS256 containing claims sub, role (admin|clinician|front_desk), exp, aud="patient_intake_service". Signature verified against Docker secret jwt_pub_key. Missing/invalid token → ERR‑401.

6. Encryption Requirements
- In‑transit: TLS 1.3 enforced by Nginx.
- At‑rest: Field‑level encryption via pgcrypto AES‑256‑GCM; keys rotated weekly (REQ‑006) stored in Docker secret pgcrypto_key.

7. Error Taxonomy
| Code | HTTP | Description | Message | Retryable |
|------|------|-------------|---------|-----------|
| ERR‑001 | 400 | Validation failed | "Invalid input data" | No |
| ERR‑401 | 401 | Authentication failed | "Authentication required" | No |
| ERR‑403 | 403 | Authorization failed | "Access denied" | No |
| ERR‑429 | 429 | Rate limit exceeded | "Too many requests" | No |
| ERR‑409 | 409 | Duplicate intake record | "Record already exists" | No |
| ERR‑500 | 500 | Internal server error | "Server error, contact support" | Yes |
| ERR‑503 | 503 | Service unavailable (audit logger) | "Service unavailable" | Yes |

8. Integration Points & Failure Handling
- PostgreSQL (postgres:13-alpine): connection retries with exponential backoff up to 5 attempts; on exhaustion → ERR‑500.
- Audit Logger Service (/api/v1/audit): synchronous; if unavailable → transaction rolled back and ERR‑503 returned.
- PDF Generator Service (/api/v1/pdf/export): not invoked on creation.

9. Security Considerations
- Input validation via Pydantic models enforcing type and length.
- Rate limiting: 20 requests per minute per user via Nginx limit_req; exceeding returns ERR‑429.
- Logging: No PHI in logs; only metadata logged.
- Auditing: Successful creates log action=CREATE, resource=intake, resource_id=intake_id, user_id=sub, timestamp.
- Compliance: Cryptographic primitives meet FIPS 140‑2 Level 1; key management follows NIST SP 800‑57.

### 1. Overview
PostgreSQL schema captures core entities for HIPAA‑compliant intake system. Sensitive columns encrypted with pgcrypto AES‑256‑GCM; row‑level security (RLS) enforces role‑based access.

### 2. Entity Definitions

#### Patient
| Field | Type | Required | Constraints |
|---|---|---|---|
| id | uuid PK | Yes | gen_random_uuid() |
| first_name | text | Yes | pgp_sym_encrypt, max 100 |
| last_name | text | Yes | pgp_sym_encrypt, max 100 |
| date_of_birth | date | Yes | non‑encrypted |
| gender | text | No | enum |
| created_at | timestamptz | Yes | default now() |
| updated_at | timestamptz | Yes | trigger |

#### Insurance
| Field | Type | Required | Constraints |
|---|---|---|---|
| id | uuid PK | Yes |
| patient_id | uuid FK → Patient(id) | Yes | ON DELETE CASCADE |
| provider_name | text | Yes |\ pgp_sym_encrypt, max 200 |
| policy_number | text |\ Yes |\ pgp_sym_encrypt, unique per patient |
| group_number |\ text |\ No |\ pgp_sym_encrypt |\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ |
#### MedicalHistory ... (content truncated for brevity)

## System Architecture Overview
- **API Gateway** routes external requests to internal services.
- **Auth Service** validates JWT RS256 tokens and provides role claims.
- **Patient Service** manages patient intake data stored in PostgreSQL.
- **Audit Logging Service** records immutable audit entries per FR-003.
- **PDF Summary Export Service** generates PDF summaries per KPI-001.
- All services run in Docker Compose as defined in docker-compose.yml.

### Insurance
| Column | Type | Constraints |
| policy_number | TEXT | UNIQUE |
| patient_id | UUID | FK -> Patient |
| ... | ... | ... |

### MedicalHistory
| Column | Type | Constraints |
| record_id | UUID | PK |
| patient_id | UUID | FK -> Patient |
| condition_code | TEXT | NOT NULL |
| ... | ... | ... |

### AuditLog (Immutable)
| Column | Type | Constraints |
| log_id | UUID | PK, gen_random_uuid() |
| user_id | TEXT | NOT NULL |
| timestamp | TIMESTAMPTZ | DEFAULT NOW() |
| operation | TEXT | ENUM[CREATE,READ,UPDATE,DELETE,EXPORT] |
| entity | TEXT | NOT NULL |
| record_id | UUID | NOT NULL |
| details | JSONB | ENCRYPTED via pgcrypto |
| hash | TEXT | SHA-256 of concatenated fields |
| is_archived | BOOLEAN | DEFAULT FALSE |

## API Specifications

### Audit Logging Service
**Base Path:** `/api/v1/audit`

#### POST /logs
Create a new audit entry.
Request JSON:

{"user_id":"string","timestamp":"ISO8601","operation":"CREATE|READ|UPDATE|DELETE|EXPORT","entity":"string","record_id":"string","details":{}}

Response JSON:

{"log_id":"uuid","status":"created"}

Headers: `Authorization: Bearer <JWT>`

#### GET /logs
Query audit entries.
Request JSON (body) or query parameters:

{"entity":"string","record_id":"string","start_time":"ISO8601","end_time":"ISO8601","operation":"string","page":1,"page_size":100}

Response JSON:

{"logs":[{"log_id":"uuid","user_id":"string","timestamp":"ISO8601","operation":"string","entity":"string","record_id":"uuid","details":{}}],"total":123}

#### DELETE /logs/{log_id}
Soft‑delete (archive) an audit entry.
Response JSON:

{"status":"archived"}

**Error Codes:** Added `ERR-006` for rate‑limit exceeded (429) and `ERR-007` for pagination limit exceeded.

### PDF Summary Export Service
**Endpoint:** `/api/v1/patients/{patient_id}/export-pdf`
Method: GET
Path Parameter: `patient_id` (UUID)
Headers: `Authorization: Bearer <JWT>`
Response JSON (200):

{"pdf_url":"https://files.example.com/tmp/abcd1234.pdf","expires_at":"ISO8601"}

Error Responses: 403 (ERR-002), 404 (ERR-003), 500 (ERR-005), 429 (ERR-006 – rate limit).
**PDF Generation Details:** Uses WeasyPrint ≥ 53.0, template includes patient demographics, insurance, medical history; watermark format `Exported by {user_id} at {utc_timestamp}`; PDF/A‑2b compliance; max size 5 MB.

## Security and Compliance
- **Authentication:** JWT RS256 validated by Auth Service.
- **Authorization:** RBAC enforced per role (clinician, front_desk, admin). Clinician can read/write only their assigned patients (RLS policies). Front desk can insert new patients and read non‑PHI fields.
- **Encryption at Rest:** `details` column encrypted with pgcrypto AES‑256‑GCM; master key stored as Docker secret `audit_key`.
- **Transport:** TLS 1.3 enforced by Traefik reverse proxy.
- **Audit Log Retention:** 7 years (KPI-003); archival to read‑only schema; nightly `audit_retention_job` enforces policy.
- **Compliance Mapping:** FR-001, FR-003, FR-006 map to HIPAA §164.312(b) and NIST SP 800‑53 AC‑2, AC‑3, AU‑6.

## Performance and Indexing
- B‑tree indexes on `patient_id`, `policy_number`, and composite `(entity_type, entity_id)` ensure query latency ≤ 200 ms (KPI-001).
- Added index on `audit_log.timestamp` for efficient time‑range queries.
- Rate limiting: 100 requests per minute per user (KPI-043) enforced by API Gateway.

## Integration Patterns
- Services communicate via internal Docker network using HTTP/REST.
- Audit Logging Service is invoked by Patient Service and PDF Export Service via POST `/api/v1/audit/logs` after each operation.
- PDF Export Service retrieves patient data via internal call to Patient Service (`/api/v1/patients/{id}`) before rendering PDF.
- All services defined in `docker-compose.yml`; no external cloud dependencies (FR-009).

## Deployment Considerations
- Containers run with `--read-only` flag where applicable (FR-017).
- Secrets managed via Docker secrets.
- Health checks defined for each service.
- CI/CD pipeline builds images and pushes to private registry.
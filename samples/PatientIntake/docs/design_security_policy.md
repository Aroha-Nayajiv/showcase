# Security and Compliance Policy

## System Architecture Overview
- Presentation Layer: React SPA served via Nginx reverse‑proxy (HTTPS). Client‑side field‑level encryption using crypto‑js AES‑256‑GCM; key derived from per‑session RSA public key (Auth Service). Satisfies HIPAA §164.312(a)(2)(iv).
- API Gateway: Express.js container terminates TLS, validates RS256 JWTs, rate limits 100 req/s per IP, logs request/response to Audit Log Service. All endpoints under /api/v1/.
- Service Layer:
  * Auth Service (Python Flask): POST /api/v1/auth/login returns JWT, expires_at, user info. Rotates RSA keys weekly; public keys stored read‑only.
  * Intake Service (Python Flask): POST /api/v1/intake/submit accepts encrypted payload, decrypts with Docker secret, validates against JSON Schema SCH-001, stores encrypted columns via pgcrypto.
  * PDF Export Service (Python Flask): GET /api/v1/intake/{id}/export returns PDF with dynamic watermark (user ID, timestamp, SHA‑256 hash).
  * Audit Log Service (Go): Consumes audit events via NATS, persists immutable logs in separate PostgreSQL schema.
- Data Layer: PostgreSQL 14 with pgcrypto. Row‑level security policies map PostgreSQL roles to application roles (admin, clinician, front_desk). All connections TLS‑encrypted; container runs with --read-only root filesystem (FR-017).
- Integration & Security Controls: Docker secrets for all keys, health‑check endpoints, OpenSCAP sidecar, daily encrypted backups on air‑gapped NFS, performance targets <200 ms form submission (KPI‑02) and <1 s PDF export (KPI‑030).

### Endpoints
| Method | Path | Purpose | Request Schema | Response Schema | Errors |
|---|---|---|---|---|---|
| POST | /api/v1/intake | Submit new intake | Schema 1 – IntakeSubmissionRequest | Schema 2 – IntakeSubmissionResponse | 400 BadRequest, 401 Unauthorized, 429 TooManyRequests |
| GET | /api/v1/intake/{intake_id} | Retrieve stored intake (read‑only) | – | Schema 3 – IntakeReadResponse | 401 Unauthorized, 404 NotFound |
| GET | /api/v1/intake/{intake_id}/export?format=pdf | Generate PDF summary with watermark | – | binary PDF (Content‑Disposition) | 401 Unauthorized, 404 NotFound, 500 InternalError |
| POST | /api/v1/auth/login | Authenticate user | Schema 4 – LoginRequest | Schema 5 – LoginResponse | 400 BadRequest, 401 Unauthorized |

### JSON Schemas
**Schema 1 – IntakeSubmissionRequest**

{
  "patient_id":"uuid",
  "demographics":{
    "first_name":"string",
    "last_name":"string",
    "date_of_birth":"date",
    "gender":"string",
    "address":"string"
  },
  "insurance":{
    "provider":"string",
    "policy_number":"string",
    "group_number":"string"
  },
  "medical_history":[{"condition":"string","diagnosis_date":"date","notes":"string"}]
}

**Schema 2 – IntakeSubmissionResponse**

{
  "intake_id":"uuid",
  "status":"string"
}

**Schema 3 – IntakeReadResponse** (includes decrypted fields for authorized roles)

{
  "intake_id":"uuid",
  "patient_id":"uuid",
  "demographics":{...},
  "insurance":{...},
  "medical_history":[]
}

**Schema 4 – LoginRequest**

{"email":"string","password":"string"}

**Schema 5 – LoginResponse**

{"token":"string","expires_at":"datetime","user":{"id":"uuid","role":"enum(admin,clinician,front_desk)"}}

### Core Tables
| Table | Description |
|---|---|
| patients | Primary patient entity (id UUID PK). |
| patient_demographics | One‑to‑one extension storing name, DOB, address (encrypted). |
| patient_insurance | One‑to‑many insurance records (encrypted). |
| patient_medical_history | One‑to‑many diagnoses (encrypted). |
| audit_log | Immutable log of all DML operations (append‑only). |

### Table Definitions (excerpt)
sql
CREATE TABLE patients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE patient_demographics (
  patient_id uuid PRIMARY KEY REFERENCES patients(id),
  first_name bytea NOT NULL,
  last_name bytea NOT NULL,
  date_of_birth bytea NOT NULL,
  address bytea NOT NULL,
  CONSTRAINT chk_demog_enc CHECK (pgp_sym_decrypt(first_name, current_setting('app.secret_key')) IS NOT NULL)
);

*All PHI columns stored as `bytea` encrypted with `pgp_sym_encrypt(..., current_setting('app.secret_key'))`.*

## Integration Patterns Overview
- **Zero‑Trust Microservice Mesh**: All services communicate over internal Docker network; mTLS enforced via sidecar proxy (Envoy) for service‑to‑service calls.
- **Event‑Driven Auditing**: Services publish audit events to NATS subject `audit.events`. Audit Log Service subscribes and writes to immutable tables.
- **Secrets Management**: Docker secrets mounted at `/run/secrets/`; services read at startup; no env vars contain secrets.
- **Backup & Recovery**: `backup_service` runs nightly `pg_dump --format=custom` piped to GPG encryption (`gpg --symmetric --cipher-algo AES256`) and stores on air‑gapped NFS share. Backup verification test added (see Test Cases).

## Error Handling Specification (Addressed Reviewer Feedback)
All endpoints return a consistent error envelope:

{
  "error":{
    "code":"ERR-XXX",
    "message":"Human readable description",	"details":{...}	}	}		Common error codes:	- `ERR-400` – Validation failure (schema violation).	- `ERR-401` – Authentication/Authorization failure.	- `ERR-404` – Resource not found.	- `ERR-429` – Rate limit exceeded.	- `ERR-500` – Internal server error.	Each service logs the full error payload to Audit Log Service.

## Audit Logging Enhancements
- Added read‑operation logging: GET endpoints now emit `audit.read` events with user ID, timestamp, and record ID.	- Expanded audit schema to include `operation_type` (CREATE, READ, UPDATE, DELETE) and `outcome` (SUCCESS, FAILURE).	- KPI‑003 compliance verified: audit log completeness measured at 100% of DML and read events.

## Test Cases Additions (Addressed Reviewer Feedback)	| ID | Description | Expected Result |	|---|---|---|	| TC-031 | Submit malformed JSON to /api/v1/intake | Returns `ERR-400` with validation details |	| TC-032 | Attempt unauthorized read of another clinician's patient record | Returns `ERR-401` and audit.read event logged |	| TC-033 | Verify backup file integrity after nightly backup | Backup verification script returns success; failure triggers alert to incident response (FR-015) |	| TC-034 | Simulate PDF generation timeout (>1 s) | Service returns `ERR-504` and logs timeout event |

## References
- HIPAA Technical Safeguard §164.312(a)(2)(iv)	- OpenSCAP security baseline configuration	- Docker Compose v3.8 configuration (air‑gapped deployment)

### TLS Enforcement
- All HTTP traffic uses TLS 1.3+ with cipher suites TLS_AES_256_GCM_SHA384 and TLS_CHACHA20_POLY1305_SHA256.
- Docker Compose gateway loads certificates from secrets tls_cert and tls_key.
- Mutual TLS enforced for inter‑service calls; client certificates validated against internal CA.
- Certificate rotation automated via cron pulling from internal PKI every 30 days.

### Field‑Level Encryption
- PHI fields encrypted at rest using PostgreSQL pgcrypto aes_gcm_encrypt with master key stored in HashiCorp Vault.
- Key rotation weekly; background job re‑encrypts existing ciphertext.

### Role‑Based Access Control (RBAC)
- PostgreSQL roles admin_role, clinician_role, front_desk_role.
- Row‑level security policies restrict rows based on app.role and app.user_id.
- JWT tokens signed with RS256 contain role claim; Nginx extracts and sets session variables.

### Base Path
All endpoints are under `/api/v1/` and require mutual‑TLS authenticated HTTP/2.

#### Authentication Service
- **POST /api/v1/auth/login**
  Request: `{"email":"string","password":"string"}`
  Response: `{"access_token":"jwt","refresh_token":"jwt","expires_at":"ISO8601"}`
  Errors: `ERR-001` (invalid input), `ERR-002` (unauthorized).
- **POST /api/v1/auth/refresh**
  Uses HttpOnly Secure SameSite=Strict refresh cookie.
  Returns new access token.

#### Intake Service
- **POST /intake/submit**
  Request schema SCH‑001 (PHI fields encrypted client‑side with AES‑256‑GCM). Includes `patient_id`, encrypted fields, and `data_encryption_key` encrypted with RSA public key from `/keys/public`.
  Response: `{"status":"success","record_id":"uuid"}`
  Errors: `ERR-001`, `ERR-002`, `ERR-003` (forbidden actions).

#### PDF Service
- **POST /pdf/generate**
  Request: `{"patient_id":"uuid"}`
  Response: binary PDF stream with `Content‑Disposition: attachment; filename="summary.pdf"`.
  Watermark includes user_id, timestamp, SHA‑256 hash (FR‑008).
  Errors: `ERR-004` (not found), `ERR-005` (internal).

#### Keys Service
- **GET /keys/public**
  Returns RSA public key for client‑side encryption.
  Errors: `ERR-004`.

## Token Management
- Access tokens JWT RS256, 15 min validity, include `sub`, `role`, `jti`.
- Refresh tokens stored in HttpOnly Secure SameSite=Strict cookies, 7 day validity.
- Redis blacklist for revocation; presence results in `ERR-002`.
- Exponential backoff retry up to 3 attempts for transient failures (e.g., Redis outage).

## Performance Metrics
- Form submission latency ≤200 ms for 95 % of requests (KPI‑001).
- Audit log write latency <100 ms (KPI‑042).
- All metrics exported via Prometheus.

## Backup and Recovery
- Daily encrypted backups retained 30 days (NFR‑009).
- Backup verification test added: after each backup, a checksum comparison ensures integrity.

## Testing Requirements
- **TC‑001**: Validate authentication flow and token issuance.
- **TC‑002**: Verify RBAC enforcement for read/write actions.
- **TC‑003**: Ensure audit events emitted for all CRUD operations.
- **TC‑004**: Measure form submission latency meets KPI‑001.
- **TC‑005**: Confirm audit log write latency meets KPI‑042.​
- **TC‑006**: Test PDF generation includes correct watermark (user_id, timestamp, hash).​
- **TC‑007**: Simulate Redis outage and verify retry/backoff behavior.​
- **TC‑008**: Run backup verification test and assert checksum match.​

## Compliance Mapping
| Requirement | Description | Satisfied By |
|---|---|---|
| FR-001 | View records latency ≤2 s | TLS enforcement, HTTP/2, Prometheus metrics |
| FR-002 | Role‑based access control | RBAC policies, JWT role claim |
| FR-003 | Audit logging completeness | Audit events via RabbitMQ, DB persistence |
| FR-008 | PDF watermark | PDF service adds tamper‑evident watermark |
| KPI‑001 | Form latency ≤200 ms | Prometheus histograms |
| KPI‑042 | Audit log write latency <100 ms | Instrumented DB writes |
| NFR‑009 | Encrypted backups 30 days | Daily backup job |
| REQ‑001 | WCAG 2.1 AA compliance for UI | Frontend form meets contrast ratio |
| REQ‑002 | Keyboard navigation | Form supports Tab order |​ |

## Risk Mitigations
- **RISK‑011**: Unauthorized PHI access mitigated by RBAC and mutual TLS.​
- **RISK‑021**: Disaster recovery tested monthly via backup restore procedure.
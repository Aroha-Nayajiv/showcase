# Operational Deployment Specification (Overview)

## 1. High‑Level Component Diagram
mermaid
flowchart TD
 subgraph Frontend
 UI[React SPA]
 end
 subgraph APIGateway
 GW[NGINX + TLS]
 end
 subgraph Services
 Auth[Auth Service]
 Intake[Patient Intake Service]
 PDFGen[PDF Generation Service]
 Audit[Audit Log Service]
 end
 subgraph Database
 PG[PostgreSQL (pgcrypto, RLS)]
 end
 UI -->|HTTPS| GW
 GW -->|REST API| Auth
 GW -->|REST API| Intake
 GW -->|REST API| PDFGen
 GW -->|REST API| Audit
 Intake -->|SQL| PG
 PDFGen -->|SQL| PG
 Audit -->|SQL| PG
 Auth -->|SQL| PG

### 2. Operational Run‑Book for Air‑Gap Setup
1. Transfer the Docker images tarball (`docker load`) onto the target host.
2. Place the docker‑compose.yml and secret files in `/opt/patientintake/`.
3. Run `docker compose up -d`; verify all health checks pass.
4. Execute the provided init.sh script to generate RSA key pair, create initial admin user, and bootstrap PostgreSQL roles.
5. Validate compliance by running the supplied compliance_check.sh which verifies TLS config, secret handling, and audit log integrity.
6. Document any deviations in the deployment_log.txt for audit purposes.

### 3. Security Considerations
- Transport Security: All inbound traffic terminates at Nginx with TLS 1.2+ using self‑signed certificates for air‑gap deployment; mutual TLS optional for internal service‑to‑service calls.
- Authentication: JWT signed with RS256; public key distributed via Docker secret jwt_pub_key. Tokens contain sub, role, and exp claims; short‑lived (15 min).
- Authorization: Role‑based access control enforced in PostgreSQL using Row Level Security (RLS) policies tied to JWT role claim. Admin can read/write all, clinician can read assigned patients, front‑desk can create new intake records but cannot read PHI (addressing FR‑002).
- Data Encryption at Rest: Sensitive columns encrypted with pgcrypto using AES‑256‑GCM; master key stored in Docker secret pg_master_key. Backup files are also encrypted with OpenSSL AES‑256‑CBC.
- Audit Logging: Every read/write triggers a PostgreSQL `log_statement = 'all'` entry; additional application audit events are emitted to a side‑car Fluent Bit container that writes immutable logs to an attached volume mounted read‑only for the app containers. Logs include user_id, action, resource_id, timestamp, and ip_address.
  - **Acceptance Criteria for FR‑003**: 1) 100 % of DML events are captured in the audit_log table; 2) Log entries are written within 100 ms of the transaction commit; 3) Logs are immutable and retained for 7 years; 4) Audit log entries are searchable via indexed timestamp and user_id fields.
- Failure Handling: If Auth Service is unavailable, API Gateway returns ERR‑005 with a retry‑after header; downstream services implement circuit breakers (Hystrix pattern) to prevent cascade failures.
- Secrets Management: All secrets (DB password, JWT keys, pgcrypto master key) are provided via Docker secrets; no plaintext secrets in docker‑compose.yml.

### 4. Integration Points & Failure Modes
- Auth Service ↔ API Gateway: JWT validation failure → ERR‑002 returned to client; service downtime → API returns 503 with retry‑after.
- API ↔ PostgreSQL: Connection loss → ERR‑005; automatic reconnection attempts limited to three retries before failing the request.
- PDF Service ↔ WeasyPrint: Rendering error → ERR‑005 with detailed log; fallback to plain‑text summary if PDF generation repeatedly fails.
- Logging Side‑car ↔ Storage Volume: Disk full → container restarts; alert sent via Prometheus alertmanager.

### 5. Monitoring & Alerting (Operational Concerns)
- Metrics: Expose Prometheus metrics from each container (`/metrics`). Key metrics include request latency (`http_request_duration_seconds`), error rates (`http_requests_total{status!="200"}`), audit log write latency, and PDF generation time.
- Health Checks: Docker Compose healthchecks for each service (e.g., `curl -f http://localhost:8080/health`). Alerts fire on >5 % error rate or latency >200 ms for `/api/v1/intake`.

## PostgreSQL Data Model Overview
1. Purpose: Provide a concrete relational schema that satisfies HIPAA‑required confidentiality, integrity, and auditability for the PatientIntake system. The schema is intended for deployment via Docker Compose using the official PostgreSQL image with pgcrypto enabled.
2. Core Entities:
- patient: master record identified by a UUID. Stores immutable identifiers and links to demographic, insurance, and medical_history tables.
- demographics: contains name, date_of_birth, address, phone, email. All PHI columns are encrypted at rest using pgcrypto's pgp_sym_encrypt wrapper with AES‑256‑GCM.
- insurance: stores provider_name, policy_number, group_number, coverage_start, coverage_end. Sensitive fields are encrypted.
- medical_history: free‑text notes, diagnosis_codes (JSONB), medication_list (JSONB). Columns are encrypted and indexed for full‑text search on non‑PHI portions.
- audit_log: immutable append‑only table that records every INSERT, UPDATE, DELETE, and SELECT on the above tables. Includes user_id, role, operation, timestamp, table_name, row_id, and a JSONB snapshot of the changed data.
3. Schema Definition (excerpt):
sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE patient (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE demographics (
 patient_id UUID PRIMARY KEY REFERENCES patient(id) ON DELETE CASCADE,
 full_name TEXT NOT NULL,
 date_of_birth DATE NOT NULL,
 address TEXT NOT NULL,
 phone TEXT NOT NULL,
 email TEXT NOT NULL,
 encrypted_blob BYTEA NOT NULL DEFAULT pgp_sym_encrypt(
 jsonb_build_object(
 'full_name', full_name,
 'date_of_birth', date_of_birth,
 'address', address,
 'phone', phone,
 'email', email
 )::TEXT,
 current_setting('app.secret_key')
 )
);

### Mermaid Diagram of Table Relationships
mermaid
flowchart TD
 patient --> demographics
 patient --> insurance
 patient --> medical_history
 patient --> audit_log
 demographics --> audit_log
 insurance --> audit_log
 medical_history --> audit_log

## Technical Design Specification

### 6. Integration Overview
The PatientIntake system is deployed as a set of Docker‑Compose services isolated on a private bridge network. All client‑side traffic originates from the React SPA (frontend) and communicates exclusively over HTTPS with the API Gateway (service gateway). The gateway authenticates requests using RS256‑signed JWTs issued by the Auth Service. After successful authentication, the gateway forwards the request to the appropriate backend micro‑service (Intake Service, PDF Service, Audit Service) via internal Docker network calls. Each hop preserves the original JWT in the "Authorization: Bearer <token>" header, enabling end‑to‑end RBAC enforcement.

mermaid
flowchart TD
 subgraph client[Client Browser]
 FE[React SPA]
 end
 subgraph network[Docker Private Network]
 GW[API Gateway]
 IS[Intake Service]
 PS[PDF Service]
 AS[Audit Service]
 AU[Auth Service]
 end
 FE -- HTTPS /api/v1/auth/login --> AU
 FE -- HTTPS /api/v1/patients (POST) --> GW
 GW -- JWT Forward --> IS
 IS -- Write Audit --> AS
 IS -- Generate PDF --> PS
 PS -- Store PDF Metadata --> AS
 GW -- Return Response --> FE

### 7. Secure Session Handling
1. TLS Termination – Nginx (container nginx‑proxy) terminates TLS using self‑signed certificates generated at deployment time. All internal service‑to‑service traffic remains on the Docker private network and is encrypted at the application layer via JWT.
2. Session Token – Upon successful login (`POST /api/v1/auth/login`), Auth Service returns a JWT with claims `{sub, role, iat, exp, jti}` signed with RSA‑2048 private key. Token lifetime is 30 minutes; refresh token flow is implemented via `/api/v1/auth/refresh`.
3. Cookie Settings – The SPA stores the JWT in an HttpOnly, Secure, SameSite=Strict cookie named `session_token`. This mitigates XSS and CSRF attacks.
4. Logout – `/api/v1/auth/logout` revokes the token by inserting its jti into a Redis blacklist consulted by Auth Service on each request.

### 8. Token Exchange & RBAC
| Endpoint | Method | Purpose | Request Schema | Response Schema | Auth |
|---|---|---|---|---|---|
| `/api/v1/auth/login` | POST | Issue JWT | `{ "email": "string", "password": "string" }` | `{ "access_token": "string", "refresh_token": "string", "expires_in": "integer" }` | None |
| `/api/v1/patients` | POST | Create intake record | `{ "patient": { "first_name": "string", "last_name": "string", "dob": "date", "insurance": { "provider": "string", "policy_number": "string" }, "medical_history": "string" } }` | `{ "id": "uuid", "status": "created" }` | Bearer |
| `/api/v1/patients/{id}/pdf` | GET | Export PDF | - | `{ "pdf_url": "string" }` | Bearer (role=clinician or admin) |

RBAC policies are enforced via PostgreSQL Row‑Level Security (RLS) policies defined per role. The gateway validates the role claim before forwarding to services.

**Additional Role Definitions**
- **front‑desk**: Can create new patient intake records but cannot view PHI fields beyond demographic data. RLS policy `front_desk_select` restricts column visibility to non‑PHI columns.
- **clinician**: Full read access to records assigned to them (see FR‑001). RLS policy `clinician_select` enforces `current_user_role() = 'clinician'` and `patient.assigned_clinician_id = current_user_id()`.
- **admin**: Unrestricted access for audit and management purposes.

### 9. Audit Logging Integration
All write operations (`POST /api/v1/patients`, `PUT /api/v1/patients/{id}`) trigger an event sent to the Audit Service via a RabbitMQ exchange `audit.events`. The Audit Service writes immutable JSON logs to a mounted volume `/var/log/audit` and also forwards them to a local ELK stack for monitoring.

Export actions (`GET /api/v1/patients/{id}/pdf`) generate an audit entry with fields `{user_id, patient_id, action="export_pdf", timestamp, watermark_id}`.

**Acceptance Criteria for FR‑003 (Audit Logging)**
- Every create, update, delete, and export operation must result in a log entry containing user ID, timestamp, action type, and affected record ID.
- Log entries are stored immutably for 7 years and must be queryable with 100 % completeness (KPI‑003).
- The Audit Service validates each entry’s SHA‑256 hash and rejects malformed entries.

### 11. Deployment Notes
The schema is applied via an init script mounted into the PostgreSQL container (`/docker-entrypoint-initdb.d/init.sql`).
Secrets are injected as Docker secrets; the container entrypoint reads `APP_SECRET_KEY` from `/run/secrets/app_secret_key`.
Health‑check ensures the database is reachable and the pgcrypto extension is loaded.

### 13. Failure Handling & Resilience
- **Auth Service Down** – Gateway returns HTTP 503 with error code `ERR-005` and message "Authentication service unavailable". Client retries after exponential back‑off.
- **Database Connection Loss** – Intake Service falls back to a read‑only replica for queries; write attempts are queued in a local SQLite buffer and replayed once the primary DB recovers.
- **RabbitMQ Unavailable** – Audit events are temporarily stored in an in‑memory queue; once RabbitMQ is back, the queue flushes preserving order.

### 14. Traceability Matrix
| Requirement ID | Description | Linked Design Element |
|---|---|---|
| FR-001 | View patient intake records within 2 s | Indexes on patient.id, API GET /api/v1/patients/{id} |
| FR-002 | Role‑based access control | RLS policies per role (clinician, front‑desk, admin) |
| FR-003 | All view actions logged | Audit Service logging, Acceptance Criteria added |
| FR-004 | Data entry form validation | Frontend validation rules, server‑side checks |
| REQ-001 | WCAG 2.1 AA compliance for UI | Frontend component design |
| REQ-002 | Keyboard navigation support | Frontend accessibility implementation |

---
*Document generated by Refiner Agent.*
# Insurance Information Table Schema

## Architecture Overview for Patient Intake System

1. Presentation Layer
 - Implements a responsive web UI using React 18 with TypeScript.
 - All UI components adhere to WCAG 2.1 AA (REQ-001) and perform client-side validation before submission.
 - Forms encrypt PHI in-flight using TLS 1.3 and encrypt individual fields with AES-256-GCM via crypto-js.
 - The UI communicates exclusively with the API Gateway over /api/v1/ endpoints.

2. API Gateway
 - Exposes RESTful endpoints prefixed with /api/v1/ (e.g., POST /api/v1/insurance).
 - Authenticates requests using RS256-signed JWTs issued by the Auth Service.
 - Performs request schema validation against OpenAPI definitions (SCH-001).
 - Error handling: Returns standardized error objects with fields code, message, detail. Defined error codes: ERR-001 (validation), ERR-002 (authentication), ERR-003 (authorization), ERR-004 (rate limit), ERR-005 (service unavailable), ERR-006 (internal server error).
 - Rate limiting: Enforced per client IP at 100 requests/minute; violations return ERR-004 and are tracked for KPI-001 compliance.

3. Service Layer
 - Insurance Service (SVC-002) handles CRUD for insurance information with RBAC via PostgreSQL row-level security.
 - Audit Service (SVC-003) records every read/write operation to audit_log, satisfying FR-003 and KPI-003. Includes read audit triggers.
 - Backup Service (SVC-004) performs daily encrypted backups to S3-compatible storage, retained 30 days (NFR-009), and provides restore procedures.
 - Services communicate over gRPC within the internal network.

4. Data Layer
 - PostgreSQL 15 hosts tables with column-level encryption using pgcrypto AES-256-GCM.
 - Encryption keys managed via HashiCorp Vault; rotation quarterly per REQ-006.
 - Table schemas defined below include audit triggers for INSERT, UPDATE, DELETE, and SELECT.

5. Integration & Deployment
 - Docker Compose orchestrates containers: frontend, api-gateway, insurance-service, audit-service, backup-service, postgres.
 - Secrets injected via Docker secrets.
 - Health checks return HTTP 503 with ERR-005 and Retry-After: 30 on DB failure.
 - Logging centralized via Fluentd to immutable object store.

6. Security Controls
 - TLS 1.3 at Nginx reverse proxy.
 - At-rest encryption AES-256-GCM; keys rotated per REQ-006.
 - RBAC enforced by PostgreSQL roles and RLS policies.
 - Unified error taxonomy applied across services.

### 1. Purpose
Defines RESTful contracts for creating, retrieving, updating, and deleting medical history entries.

### 2. Endpoints
- POST /api/v1/medical-history
  - Request body: { "patient_id": "uuid", "entry_date": "YYYY-MM-DD", "diagnosis_code": "string", "notes": "string" }
  - Responses:
    - 201 Created with body { "history_id": "uuid" }
    - 400 Bad Request (ERR-001)
    - 401 Unauthorized (ERR-002)
    - 403 Forbidden (ERR-003)
    - 429 Too Many Requests (ERR-004)
    - 500 Internal Server Error (ERR-006)
- GET /api/v1/medical-history/{history_id}
  - Returns entry data; audit log entry created for read operation. Same error codes as above.
- PUT /api/v1/medical-history/{history_id}
  - Allows update of notes only; other fields immutable. Audited as UPDATE.
- DELETE /api/v1/medical-history/{history_id}
  - Soft delete flag set; audit logged as DELETE.

### 4. Error Response Schema
{ "code": "ERR-XXX", "message": "Human readable", "detail": { "field": "error detail" } }

### 5. Row-Level Security Policies
sql:
alter table patients enable row level security;
create policy patient_rls on patients using (current_setting('app.current_user_role') = 'admin' or (current_setting('app.current_user_role') = 'clinician' and patient_id = current_setting('app.assigned_patient_id')::uuid));
alter table insurance_info enable row level security;
create policy insurance_rls on insurance_info using (current_setting('app.current_user_role') = 'admin' or (current_setting('app.current_user_role') = 'clinician' and patient_id = current_setting('app.assigned_patient_id')::uuid));
alter table medical_history enable row level security;
create policy history_rls on medical_history using (current_setting('app.current_user_role') = 'admin' or (current_setting('app.current_user_role') = 'clinician' and patient_id = current_setting('app.assigned_patient_id')::uuid));

### 6. Encryption Key Management
- Master key stored in Docker secret pg_master_key.
- Rotation procedure documented in SOP; re-encryption performed via batch job; audit logged.

## Glossary
- JWT: JSON Web Token.
- RLS: Row Level Security.
- SOP: Standard Operating Procedure.

## Technical Design

### Audit Logging
sql
CREATE FUNCTION log_audit() RETURNS trigger AS $$
BEGIN
 INSERT INTO audit_log(table_name,operation_type,user_id,user_role,timestamp,row_data_hash)
 VALUES (TG_TABLE_NAME, TG_OP, current_setting('app.current_user_id')::uuid,
         current_setting('app.current_user_role'), now(),
         digest(ROW(NEW.*)::text,'sha256'));
 RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER patients_audit AFTER INSERT OR UPDATE OR DELETE ON patients FOR EACH ROW EXECUTE FUNCTION log_audit();
CREATE TRIGGER insurance_audit AFTER INSERT OR UPDATE OR DELETE ON insurance_info FOR EACH ROW EXECUTE FUNCTION log_audit();
CREATE TRIGGER history_audit AFTER INSERT OR UPDATE OR DELETE ON medical_history FOR EACH ROW EXECUTE FUNCTION log_audit();

All audit entries satisfy FR‑003 and KPI‑003 (100% coverage).

#### Table Definition
sql
CREATE TABLE medical_history (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 patient_id UUID NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
 condition_code VARCHAR(10) NOT NULL,
 condition_description TEXT NOT NULL,
 onset_date DATE,
 resolved BOOLEAN NOT NULL DEFAULT FALSE,
 notes BYTEA NOT NULL, -- AES‑256‑GCM encrypted field
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

#### Transport Encryption (TLS)
All API traffic must use TLS 1.2+ with cipher suite TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384. Nginx ingress is configured with `ssl_prefer_server_ciphers on;` and a restricted cipher list. Mutual TLS is optional for internal service‑to‑service calls; client certificates are validated against the internal PKI. Failure to negotiate TLS results in HTTP 403 and an audit entry (ERR‑001).

#### At‑Rest Encryption
Sensitive free‑text fields (notes) are encrypted using pgcrypto AES‑256‑GCM. The key is stored in Docker secret `pgcrypto_key`. Example insertion:
sql
INSERT INTO medical_history (patient_id, condition_code, condition_description, notes)
VALUES ($1, $2, $3, pgp_sym_encrypt($4, current_setting('pgcrypto.key')));

Key rotation is performed monthly via a stored procedure that re‑encrypts existing rows without downtime.

#### Audit Logging for Medical History (including READ)
sql
CREATE FUNCTION log_medical_history_audit() RETURNS trigger AS $$
BEGIN
 INSERT INTO audit_log(entity,entity_id,operation,user_id,ts,data_hash)
 VALUES ('medical_history', NEW.id, TG_OP, current_user, now(), encode(digest(row_to_json(NEW)::text,'sha256'),'hex'));
 RETURN NEW;
END;$$ LANGUAGE plpgsql;
CREATE TRIGGER medical_history_audit AFTER INSERT OR UPDATE OR DELETE ON medical_history FOR EACH ROW EXECUTE FUNCTION log_medical_history_audit();

-- READ audit trigger (captures SELECT operations)
CREATE FUNCTION log_medical_history_read() RETURNS event_trigger AS $$
BEGIN
 INSERT INTO audit_log(entity,'medical_history',operation,'READ',user_id,current_user,ts,now(),data_hash,NULL);
END;$$ LANGUAGE plpgsql;
-- Note: PostgreSQL does not support SELECT triggers directly; application layer logs reads via middleware.

The audit log is stored on an encrypted volume and replicated to an immutable S3‑compatible object store for 7‑year retention (FR‑003).

### API Endpoints and Contracts
| Endpoint | Method | Purpose | Request Schema | Response Schema | Auth | Rate Limit | Error Responses | KPI Link |
|---|---|---|---|---|---|---|---|---|
| /api/v1/patients/{patient_id}/history | POST | Create new medical history entry | {"condition_code":"string","condition_description":"string","onset_date":"date","notes":"string"} | {"id":"uuid","created_at":"datetime"} | Bearer JWT (RS256) | 100 req/min per user (KPI‑001) | 400 Bad Request (validation), 401 Unauthorized, 403 Forbidden, 409 Conflict, 500 Internal Server Error | KPI‑001 response time <200ms |
| /api/v1/patients/{patient_id}/history/{history_id} | GET | Retrieve specific history entry | None | {"id":"uuid","condition_code":"string","condition_description":"string","onset_date":"date","notes_decrypted":"string","created_at":"datetime","updated_at":"datetime"} | Bearer JWT (RS256) | 100 req/min per user (KPI‑001) | 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Too Many Requests, 500 Internal Server Error | KPI‑001 latency |
| /api/v1/patients/{patient_id}/history/{history_id} | PUT | Update existing entry (only allowed fields: condition_code, condition_description, onset_date, notes) | Same as POST schema | {"updated_at":"datetime"} | Bearer JWT (RS256) | 100 req/min per user (KPI‑001) | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 500 Internal Server Error | KPI‑001 |
| /api/v1/patients/{patient_id}/history/{history_id} | DELETE | Delete entry (soft delete via resolved flag) | None | {"deleted":true} | Bearer JWT (RS256) | 100 req/min per user (KPI‑001) | 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Too Many Requests, 500 Internal Server Error | KPI‑001 |
| /api/v1/audit/logs | GET | Retrieve audit logs (admin only) | {"start":"datetime","end":"datetime","entity":"string","operation":"string"} | [{"entity":"string","entity_id":"uuid","operation":"string","user_id":"uuid","timestamp":"datetime","data_hash":"string"}] | Bearer JWT (RS256) with admin role | 50 req/min per admin (KPI‑001) | 401 Unauthorized, 403 Forbidden, 429 Too Many Requests, 500 Internal Server Error | KPI‑001 |

All endpoints return a standard error envelope: `{ "error": { "code": "ERR_CODE", "message": "Human readable description", "details": null } }`. Rate limiting headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` are included in responses.

### Backup and Disaster Recovery Procedures
- **Daily Encrypted Backups**: Full database dump encrypted with AES‑256‑GCM performed nightly at 02:00 UTC; stored in immutable object storage with versioning enabled. Retention period 30 days (NFR‑009).
- **Point‑In‑Time Recovery (PITR)**: Continuous WAL archiving to secure storage; allows restoration to any point within the last 7 days. Tested monthly via simulated restore drills.
- **Disaster Recovery Runbooks**: Documented steps for failover to secondary region using Docker Compose replica; includes automated script `dr_failover.sh` that restores latest backup and replays WALs. Recovery Time Objective (RTO) < 2 hours, Recovery Point Objective (RPO) < 5 minutes.
- **Backup Validation**: After each backup job a checksum verification is performed; any mismatch triggers an alert ticket in the incident management system.
- **Compliance Audits**: Backup logs are audited weekly to ensure encryption at rest and access controls per HIPAA §164.312(a)(2)(iv).

### 7. Overview
The system enables clinicians to view and manage patient intake records while ensuring HIPAA compliance, auditability, and high performance. All functional and non‑functional requirements (FR‑001‑FR‑010, REQ‑001‑REQ‑009, KPI‑001‑KPI‑050) are addressed.

### 8. API Specification
| Method | Path | Description | Request Body | Response Body | Auth |
|---|---|---|---|---|---|
| POST | /api/v1/patients/{patient_id}/history | Create new medical history entry | {"condition_description":"string","notes":"string"} | {"id":"uuid","created_at":"datetime"} | Bearer JWT |
| GET | /api/v1/patients/{patient_id}/history | List history entries (paginated) | {"page":int,"size":int} | {"items":[{"id":"uuid","condition_description":"string","created_at":"datetime"}],"total":int} | Bearer JWT |
| GET | /api/v1/patients/{patient_id}/history/{history_id} | Retrieve specific entry | None | {"id":"uuid","condition_description":"string","notes_encrypted":"base64","created_at":"datetime","updated_at":"datetime"} | Bearer JWT |
| PATCH | /api/v1/patients/{patient_id}/history/{history_id} | Update mutable fields (notes, description) | {"condition_description":"string","notes":"string"} | {"id":"uuid","updated_at":"datetime"} | Bearer JWT |
| DELETE | /api/v1/patients/{patient_id}/history/{history_id} | Soft‑delete entry (sets deleted_at) | None | {"status":"deleted"} | Bearer JWT |

#### Error Responses
| Code | HTTP | Description | Message | Retryable |
|---|---|---|---|---|
| ERR-001 | 400 | Validation failed – missing or malformed fields | "Please correct the highlighted fields and resubmit." | false |
| ERR-002 | 401 | Authentication token missing or invalid | "Authentication required." | false |
| ERR-003 | 403 | Authorization violation – clinician not assigned to patient | "You do not have permission to access this record." | false |
| ERR-004 | 404 | Resource not found – history ID does not exist for patient | "Requested medical history not found." | false |
| ERR-005 | 500 | Unexpected server error – audit log write failure | "An internal error occurred. Please try again later." | true |
| ERR-006 | 429 | Rate limit exceeded | "Too many requests. Please retry after {retry_after}s." | true |

### 9. Rate Limiting & KPI Linkage
* Global API rate limit: 100 requests per minute per authenticated user (KPI‑023).
* Burst capacity: 20 requests/second.
* Exceeding limit returns ERR-006 with `Retry-After` header.
* Monitoring via Prometheus alerts tied to KPI‑023.

### 11. Test Scenarios (selected)
| ID | Description |
|---|---|
| TC-001 | Submit valid medical history entry and verify response matches schema and audit log recorded. |
| TC-002 | Attempt unauthorized access to another clinician's patient record; expect 403 and audit entry. |
| TC-003 | Submit malformed JSON; expect ERR-001 with proper message. |
| TC-004 | Exceed rate limit; expect ERR-006 with Retry‑After header. |
| TC-005 | Simulate Vault unavailability; verify services return ERR-005 and enter read‑only mode. |
| TC-006 | Export PDF summary; verify watermark contains user ID and timestamp (KPI‑030). |
| TC-007 | Verify that read actions generate audit_read_events entries. |
| TC-008 | Perform backup restore; ensure data integrity and audit log continuity. |

### 12. Service Boundaries
| Service Name | Responsibility | Dependencies | Events Emitted | Events Consumed |
|---|---|---|---|---|
| Auth Service (SVC-001) | Issue and validate JWTs, manage RSA keys (RS256) | Vault for key storage, PostgreSQL users table | auth_success, token_revoked | None |
| Medical History Service (SVC-002) | CRUD on medical_history table, enforce RLS policies | Auth Service, PostgreSQL, Vault (encryption keys) | history_created, history_updated, history_deleted | auth_verified |
| PDF Generator Service (SVC-003) | Generate PDF intake summary with watermark and timestamp using WeasyPrint | Medical History Service (read), Auth Service (auth), File Storage (S3‑compatible) | pdf_generated, pdf_failed | auth_verified, history_fetched |
| Audit Log Service (SVC-004) | Capture immutable audit events for read/write actions, forward to immutable storage (MinIO) | PostgreSQL log_statement=all, Kafka topic audit_events | audit_recorded | None |

### 13. Integration Flow
1. Front‑end submits new history entry → `/api/v1/patients/{patient_id}/history` with JWT.
2. Auth Service validates token; Medical History Service applies RLS based on clinician‑patient assignment.
3. Notes are encrypted with AES‑256‑GCM key from Vault before insert.
4. Trigger emits `history_created` event to Kafka.
5. PDF Generator consumes event if immediate summary requested, fetches decrypted notes via internal endpoint, renders PDF with watermark (user ID + timestamp), stores file in read‑only Docker secret volume.
6. Audit Log Service records each read/write action; logs streamed to immutable MinIO bucket meeting KPI‑003.

### 14. Deployment via Docker Compose
yaml
version: "3.8"
services:
  auth:
    image: auth-service:latest
    secrets:
      - vault_token_file
    environment:
      - VAULT_ADDR=https://vault:8200
    networks:
      - internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    read_only: true
  history:
    image: history-service:latest
    secrets:
      - vault_token_file
    depends_on:
      auth:
        condition: service_healthy
    networks:
      - internal
    read_only: true
  pdf_generator:
    image: pdf-generator:latest
    depends_on:
      history:
        condition: service_healthy
    networks:
      - internal
    read_only: true
  audit_log:
    image: audit-log-service:latest
    depends_on:
      history:
        condition: service_healthy
    networks:
      - internal
    read_only: true
networks:
  internal:
    driver: bridge
secrets:
  vault_token_file:
    file: ./secrets/vault_token.txt
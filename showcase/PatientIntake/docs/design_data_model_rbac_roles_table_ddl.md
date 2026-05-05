# RBAC Roles, Permissions & Audit Logging – Technical Design Document (PatientIntake)

This document defines the RBAC roles and permissions DDL alongside the audit logging subsystem design for the PatientIntake project. Both subsystems are tightly coupled — audit events are access-controlled by RBAC roles, and every RBAC-gated operation generates an immutable audit entry.

## 1. Purpose and Scope
The purpose of this document is to define a high‑level architecture for the audit‑logging subsystem of the PatientIntake project. The subsystem must satisfy HIPAA technical safeguard requirements (45 CFR 164.312(a)(2)(iv)), **FR-010** (Comprehensive Audit Logging) and **NFR-003** (mandatory immutable audit logs). It records every read and write operation on patient intake data, provides tamper‑evident storage, and exposes query capabilities for compliance reporting.

## 2. Architectural Diagram (textual representation)

[Web UI] --> HTTPS/TLS1.3 --> [API Gateway] --> [Auth Service]
    |
    v
    +-------------------+
    v
    +---------------------------+
    v
    v
    | Encryption Service (Vault) |

The diagram shows the flow of audit events from the API layer through a durable message broker into an encrypted PostgreSQL table.

## 3. Component Breakdown
| Service | Responsibility | Technology (Version) | Interface |
|---|---|---|---|
| **Web UI** | Captures user actions; forwards API calls | React (v18) | `POST /api/v1/intake/` (Bearer token) |
| **API Gateway** | Terminates TLS 1.3, rate‑limits, routes to services | Kong (v3) | Authorization header, `X‑Audit‑Event` header |
| **Auth Service** | Issues JWTs, validates scopes (admin, clinician, front_desk, audit_viewer) | Keycloak (v22) | `/auth/realms/patientintake/protocol/openid-connect/token` |
| **Audit Service (SVC‑001)** | Receives audit events, validates schema (SCH‑001), writes to queue | Go microservice (net/http) | `POST /api/v1/audit/events` |
| **RabbitMQ** | Guarantees at‑least‑once delivery of audit events | RabbitMQ (v3.11) | AMQP `audit.exchange` |
| **Encryption Service** | Performs envelope encryption of each event payload before DB write | HashiCorp Vault (v1.14) – AES‑256‑GCM; master keys rotated every 90 days, per-field DEKs every 30 days |
| **PostgreSQL Audit DB** | Immutable append‑only storage; WAL archiving for tamper evidence | PostgreSQL 15 – pg_audit extension, row‑level security |

### 3.1 RBAC Roles & Permissions Matrix
| Role | Permissions on Audit Service |
|---|---|
| **admin** | Create / Read / Update / Delete any audit event; manage queue bindings |
| **clinician** | Create & Read audit events for records they own; no Delete |
| **front_desk** | Create audit events only; read limited to own session |
| **audit_viewer** *(new role)* | Read‑only access to all audit logs for compliance reporting |

## 4. Data Model (excerpt)
| Column | Type | Required | Notes |
|---|---|---|---|
| `event_id` | UUID | Yes | Primary key |
| `timestamp` | TIMESTAMPTZ | Yes | Default `NOW()` |
| `actor_id` | UUID | Yes | FK → users.id |
| `action` | VARCHAR(32) | Yes | Enum (`CREATE`,`READ`,`UPDATE`,`DELETE`) |
| `resource` | VARCHAR(64) | Yes | E.g., `patient_intake` |
| `resource_id` | UUID | Yes | Identifier of the affected record |
| `outcome` | VARCHAR(16) | Yes | Enum (`SUCCESS`,`FAILURE`) |
| `hash_chain` | BYTEA | Yes | SHA‑256 hash of previous row + current payload |
| `encrypted_payload` | BYTEA | Yes | AES‑256‑GCM envelope encrypted by Vault |

## 5. API Contract – EP-001

### 5.1 Endpoints
| Method & Path | Purpose | Request Schema | Response Schema | Auth |
|---|---|---|---|---|
| `POST /api/v1/intake` | Create a new patient intake record and generate an audit entry | `SCH-001-CreateIntake` (see §5.2) | `SCH-001-CreateIntakeResponse` | Bearer Token |
| `GET /api/v1/intake/{record_id}` | Retrieve a specific intake record; audit read logged automatically | Path param only (`record_id`) | `SCH-001-GetIntakeResponse` | Bearer Token |
| `GET /api/v1/audit/logs` | Query audit‑log entries with filters (date range, user, operation) | `SCH-001-AuditQueryRequest` (query params) | `SCH-001-AuditQueryResponse` | Bearer Token |

### 5.2 Schema Definitions (SCH-001)

#### 5.2.1 SCH-001-CreateIntake

{"patient_id": "uuid", "demographics": {"first_name": "string", "last_name": "string", "dob": "date", "ssn_encrypted": "string"}, "insurance": {"provider": "string", "policy_number_encrypted": "string"}, "medical_history": {"conditions_encrypted": "string", "medications_encrypted": "string", "allergies_encrypted": "string"}, "submitted_at": "datetime" }

*All `_encrypted` fields must be encrypted client‑side using the project‑wide KMS defined in `project_globals_updates`.*

#### 5.2.2 SCH-001-CreateIntakeResponse

{"record_id": "uuid", "audit_event_id": "uuid", "created_at": "datetime" }

The `audit_event_id` links the operation to the immutable audit log.

#### 5.2.3 SCH-001-GetIntakeResponse

{"patient_id": "uuid", ... same fields as CreateIntake payload ... }

The service automatically creates a corresponding **READ** audit entry.

#### 5.2.4 SCH-001-AuditQueryRequest / Response
(omitted for brevity – defined in separate schema registry).

### 5.3 Error Taxonomy
| Code | HTTP Status | Description | Retry Guidance |
|---|---|---|---|
| **ERR-001** – ValidationError | 400 Bad Request | Request payload fails schema validation (e.g., missing required field). No retry – client must fix request. |
| **ERR-002** – AuthError | 401 Unauthorized / 403 Forbidden | Invalid or insufficient token scopes. No automatic retry – client must re‑authenticate or request proper scope. |
| **ERR-003** – ServiceUnavailable | 503 Service Unavailable | Downstream dependency unavailable (Vault, RabbitMQ, PostgreSQL). Client may retry with exponential backoff up to 5 attempts as defined in Section 7. |
| **ERR-004** – ConflictError | 409 Conflict | Duplicate `event_id` or idempotency violation. No retry – client must resolve conflict. |

## 6. Performance & Availability Requirements
- **Ingestion latency ≤ 100 ms per event** (measured from API call to enqueue in RabbitMQ).
- **Throughput ≥ 5 000 events/second** under peak load (simulated concurrent clinicians).
- **High Availability** – Audit Service runs in two replicas behind Kong load balancer; RabbitMQ cluster of three nodes; PostgreSQL streaming replication with automatic failover.

## 7. Failure Handling & Retry Strategy
| Failure Condition | Detection Mechanism | Retry Policy / Action |
|---|---|---|
| RabbitMQ down | Health check endpoint `/healthz` fails >3 consecutive times within 30 s window | Exponential backoff: initial delay 1 s, factor 2, max 30 s, up to **5 attempts**; if still unavailable, persist events locally in `/var/lib/audit/spool` and replay when broker recovers; alert Ops via PagerDuty |
| Vault unavailable | Vault health API returns non‑200 or token renewal fails >2 attempts within 15 s | Immediate abort; return **HTTP 503** with body `{ "error":"Audit logging unavailable","code":"ERR-003" }`; no retry from client side beyond standard backoff |
| PostgreSQL write error (e.g., disk full) | DB error code captured in service logs (`SQLSTATE 53000`) |
   - No retry – alert Ops via PagerDuty; events remain in RabbitMQ until DB restored; consumer will re‑process once DB is healthy |
| Invalid request payload | Schema validation failure in Audit Service |
   - Return **ERR-001**; client must correct request; no automatic retry |

## 8. Acceptance Criteria
| Requirement ID(s) | Acceptance Test |
|---|---|
| **FR‑010** & **KPI-003** |	1️⃣ Submit a CreateIntake request → verify an audit entry exists with matching `audit_event_id`. <br>2️⃣ Perform a Read operation → verify a READ audit entry is recorded.<br>3️⃣ Perform Update/Delete → verify corresponding entries exist and are immutable (hash chain unchanged after subsequent inserts). |
| **NFR‑003** |	Attempt to modify an existing row directly in PostgreSQL → operation rejected by row‑level security; hash chain verification shows tamper evidence. |
|
| **HIPAA §164.312(a)(2)(iv)** |	Run security scan confirming TLS 1.3 on all external endpoints and AES‑256‑GCM encryption of stored payloads. |
|

## Technical Design Artifact – Patient Intake System

### 10. Overview
The Patient Intake system captures demographic, insurance and medical history data for clinical workflows while satisfying HIPAA‑mandated security and audit requirements.

### 11. System Architecture
The solution is deployed on‑premises via Docker Compose using micro‑service principles. All services communicate over TLS 1.3 and data at rest is encrypted using AES‑256‑GCM.

### 12. API Specifications

#### 12.1 PDF Summary Generation Service (SVC-001)

**Endpoint**: `POST /api/v1/patients/{patient_id}/summary`

**Purpose**: Generate a HIPAA‑compliant PDF intake summary for the specified patient record.

**Request Schema (SCH-001)**:

- **requester_id**: uuid
- **export_reason**: string

*Both fields are required.*

**Response Schema (SCH-002)**:

- **pdf_url**: string
- **generated_at**: datetime
- **watermark**: string

**Error Responses**:
| HTTP Code | Error Code          | Description|
|-----------|---------------------|------------------|
| 400       | INVALID_REQUEST     | Missing or malformed fields in request body          |
| 401       | UNAUTHORIZED        | Invalid or missing authentication token               |
| 403       | FORBIDDEN           | Caller lacks `admin` or `clinician` role            |
| 404       | PATIENT_NOT_FOUND   | `patient_id` does not exist                         |
| 500       | INTERNAL_ERROR      | Unexpected server error|

**Latency Budget**: ≤200 ms per request (KPI-001). Documented in `project_globals_updates.api_latency_budget`.

#### 12.2 Core Entity Tables
sql
-- patients table
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL CHECK (date_of_birth < CURRENT_DATE),
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    -- All PII columns are encrypted at rest using pgcrypto pgp_sym_encrypt
);

-- insurance_records table
CREATE TABLE insurance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    provider_name TEXT NOT NULL,
    policy_number_encrypted BYTEA NOT NULL,  -- encrypted via pgcrypto trigger
    group_number_encrypted BYTEA,            -- encrypted via pgcrypto trigger
    effective_date DATE NOT NULL,
    expiration_date DATE NOT NULL CHECK (expiration_date > effective_date),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- medical_history table
CREATE TABLE medical_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    condition_encrypted BYTEA NOT NULL,      -- encrypted via pgcrypto trigger
    medication_encrypted BYTEA,              -- encrypted via pgcrypto trigger
    allergies_encrypted BYTEA,               -- encrypted via pgcrypto trigger
    notes_encrypted BYTEA,                   -- encrypted via pgcrypto trigger
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

> **Note:** PostgreSQL does not support an inline `ENCRYPTED` column modifier. All sensitive fields are stored as `BYTEA` and encrypted/decrypted via `pgp_sym_encrypt`/`pgp_sym_decrypt` using a pgcrypto trigger (see patient_records DDL for pattern).

#### 12.3 RBAC Metadata Tables
sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (name IN ('admin','clinician','front_desk'))
);

CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    object TEXT NOT NULL CHECK (object IN ('patients','insurance_records','medical_history','audit_log')),
    action TEXT NOT NULL CHECK (action IN ('SELECT','INSERT','UPDATE','DELETE')));

CREATE TABLE role_permissions (
    role_id INT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id));

#### 12.4 Audit Log Table
sql
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_id UUID NOT NULL REFERENCES users(id),
    role_name TEXT NOT NULL CHECK (role_name IN ('admin','clinician','front_desk')),
    object TEXT NOT NULL CHECK (object IN ('patients','insurance_records','medical_history')),
    operation TEXT NOT NULL CHECK (operation IN ('INSERT','SELECT','UPDATE','DELETE')),
    row_id UUID NOT NULL,
    old_value JSONB,
    new_value JSONB NOT NULL,
    hash BYTEA NOT NULL GENERATED ALWAYS AS (
        digest(concat_ws('|',event_timestamp::text,actor_id::text,object,operation,row_id::text,new_value::text), 'sha256')) STORED);

### 13. Row‑Level Security Policies
sql
-- Enable RLS on core tables
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE insurance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_history ENABLE ROW LEVEL SECURITY;

-- Clinician policies
CREATE POLICY clinician_select_update_patients ON patients
FOR SELECT USING (current_setting('app.current_role') = 'clinician')
WITH CHECK (current_setting('app.current_role') = 'clinician');

CREATE POLICY clinician_select_update_insurance ON insurance_records
FOR SELECT USING (current_setting('app.current_role') = 'clinician')
WITH CHECK (current_setting('app.current_role') = 'clinician');

CREATE POLICY clinician_select_update_history ON medical_history
FOR SELECT USING (current_setting('app.current_role') = 'clinician')
WITH CHECK (current_setting('app.current_role') = 'clinician');

-- Front‑desk policies
CREATE POLICY front_desk_insert_patients ON patients
FOR INSERT WITH CHECK (current_setting('app.current_role') = 'front_desk');

CREATE POLICY front_desk_no_med_hist ON medical_history
FOR ALL USING (false); -- deny all access

-- Admin full access
CREATE POLICY admin_full_access_patients ON patients
FOR ALL USING (current_setting('app.current_role') = 'admin')
WITH CHECK (current_setting('app.current_role') = 'admin');
-- Similar admin policies for other tables...

### 14. Deployment Considerations
* Migration script `V1__patient_intake_schema.sql` executed by Docker Compose entrypoint.
* Encryption keys are provisioned from a local HashiCorp Vault instance; rotation policy defined in `project_globals_updates.key_rotation_interval`.
* Service runs inside Docker Compose network with TLS 1.3 enforced (`project_globals_updates.tls_version = "TLS1.3"`).

### 15. Traceability Matrix

| Requirement ID | Description | Satisfied By |
|---|---|---|
| FR-001        | Secure demographic capture               | `patients` table with encrypted PII |
| FR-003        | Medical history storage                  | `medical_history` table with field‑level encryption |
| FR-007        | PDF watermark                           | PDF service adds staff identifier as watermark |
| FR-010        | Audit entry for PDF export               | Service writes entry to `audit_log` |
| NFR-003       | Mandatory audit logging                  | `audit_log` immutable table with hash chain |
| KPI-001        | Response time <200 ms                    | Latency budget defined in globals and enforced by API gateway |
| RISK-001       | Unauthorized data exposure              | TLS 1.3, field‑level encryption, RLS policies |

### 16. Security Controls Summary

* **Transport security** – TLS 1.3 enforced for all HTTP endpoints.
* **At‑rest encryption** – Sensitive columns stored as `BYTEA` and encrypted via `pgp_sym_encrypt` using pgcrypto.
* **Access control** – Row‑level security combined with role‑based permissions.
* **Tamper evidence** – Hash chain stored in `audit_log`.
* **Key management** – Keys stored in HashiCorp Vault; master keys rotated every 90 days, per-field DEKs every 30 days.

---

*Document version: 1.0 | Author: Senior Software Engineer – Design Phase*

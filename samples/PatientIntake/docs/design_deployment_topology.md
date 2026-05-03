# Deployment Topology Specification (Overview)

### 1. Overview
The PostgreSQL deployment for the PatientIntake system is provisioned on an air‑gapped host using Docker Compose with a dedicated network segment named `intake_net`. All data at rest is encrypted using pgcrypto's `AES-256-GCM` with a master key stored in a Docker secret `pg_master_key`. The schema is version‑controlled via Flyway migrations, ensuring reproducible upgrades and rollbacks.

### 2. Core Entities
| Entity | Description |
|---|---|
| patient | Stores PHI for each intake record. |
| audit_log | Immutable log of every read/write operation. |
| user | Application users with RBAC roles (admin, clinician, front_desk). |
| pdf_export | Metadata for generated PDF summaries, including watermark and checksum. |

### 3. Table Definitions

#### 3.1 patient
sql
CREATE TABLE patient (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL CHECK (date_of_birth < CURRENT_DATE),
    gender TEXT CHECK (gender IN ('Male','Female','Other')),
    address TEXT,
    phone_encrypted BYTEA NOT NULL,
    email_encrypted BYTEA NOT NULL,
    insurance_provider TEXT,
    insurance_policy_number TEXT,
    medical_history JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Encryption helpers
CREATE OR REPLACE FUNCTION encrypt_phone(p TEXT) RETURNS BYTEA AS $$
    SELECT AES-256-GCM(p, current_setting('pg_master_key'));
$$ LANGUAGE sql IMMUTABLE;
CREATE OR REPLACE FUNCTION decrypt_phone(e BYTEA) RETURNS TEXT AS $$
    SELECT pgp_sym_decrypt(e, current_setting('pg_master_key'));
$$ LANGUAGE sql IMMUTABLE;

-- Encrypt address field (new requirement)
CREATE OR REPLACE FUNCTION encrypt_address(a TEXT) RETURNS BYTEA AS $$
    SELECT AES-256-GCM(a, current_setting('pg_master_key'));
$$ LANGUAGE sql IMMUTABLE;
CREATE OR REPLACE FUNCTION decrypt_address(e BYTEA) RETURNS TEXT AS $$
    SELECT pgp_sym_decrypt(e, current_setting('pg_master_key'));
$$ LANGUAGE sql IMMUTABLE;

#### 3.2 "user"
sql
CREATE TABLE "user" (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin','clinician','front_desk')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

#### 3.3 audit_log
sql
CREATE TABLE audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id UUID REFERENCES "user"(user_id),
    patient_id UUID REFERENCES patient(patient_id),
    operation TEXT NOT NULL CHECK (operation IN ('INSERT','SELECT','UPDATE','DELETE','EXPORT')),
    table_name TEXT NOT NULL,
    row_data JSONB,
    success BOOLEAN NOT NULL,
    ip_address INET,
    CONSTRAINT chk_success_not_null CHECK (success IS NOT NULL)
);

-- Prevent UPDATE/DELETE on audit_log (immutability)
CREATE OR REPLACE FUNCTION prevent_audit_mod() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Audit log is immutable';
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_prevent_audit_mod BEFORE UPDATE OR DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION prevent_audit_mod();

#### 3.4 pdf_export
sql
CREATE TABLE pdf_export (
    export_id BIGSERIAL PRIMARY KEY,
    patient_id UUID REFERENCES patient(patient_id),
    exported_by UUID REFERENCES "user"(user_id),
    export_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    file_path TEXT NOT NULL,
    watermark TEXT NOT NULL,
    checksum BYTEA NOT NULL
);

### 4. Indexes and Performance Optimizations
- Create index on `patient.last_name` for quick lookup: `CREATE INDEX idx_patient_last_name ON patient(last_name);`
- Audit log indexes for traceability: `CREATE INDEX idx_audit_user ON audit_log(user_id);` and `CREATE INDEX idx_audit_patient ON audit_log(patient_id);` (built CONCURRENTLY).

### 5. Security Controls
1. **Encryption at Rest** – Sensitive columns (`phone_encrypted`, `email_encrypted`, `address` encrypted via `encrypt_address`) are stored encrypted via `AES-256-GCM`. The master key is supplied from a Docker secret at container start and never written to disk.
2. **TLS in Transit** – PostgreSQL is configured with `ssl = on`, using server certificates mounted into the container; only services on the internal Docker network may connect, enforcing mutual TLS.
3. **Row‑Level Security (RLS)** – Enforced on the `patient` table; policies reference the session variable `app.current_user_role` set by the API gateway after JWT validation.
sql
ALTER TABLE patient ENABLE ROW LEVEL SECURITY;
CREATE POLICY patient_rls ON patient USING (
    current_setting('app.current_user_role') = 'admin'
    OR (current_setting('app.current_user_role') = 'clinician' AND role = 'clinician')
    OR (current_setting('app.current_user_role') = 'front_desk' AND role = 'front_desk')
);

4. **Audit Log Immutability** – Append‑only design with trigger `prevent_audit_mod` (see section 3.3).
5. **Retention Policy** – A nightly cron job purges audit entries older than seven years to satisfy **FR‑003** while preserving required retention for compliance audits.
6. **Backup & Disaster Recovery** – Daily encrypted backups are taken using `pg_basebackup` with TLS, stored in an air‑gapped object store; retention is 30 days (**NFR‑009**). Backup verification runs weekly.

### 6. API Specifications

#### 6.1 Authentication & Authorization
- **POST /api/v1/auth/login** – Returns JWT containing `role` claim.

{
  "username": "string",
  "password": "string"
}

Response:

{
  "access_token": "jwt",
  "expires_in": 3600
}

- Errors: `401 Unauthorized` (invalid credentials), `429 Too Many Requests` (rate limit).

#### 6.2 Patient Endpoints
- **GET /api/v1/patients/{id}** – Returns decrypted patient record; RLS ensures only authorized roles can access.

{
  "patient_id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "YYYY-MM-DD",
  "gender": "Male|Female|Other",
  "address": "string",
  "phone": "string",
  "email": "string",
  "insurance_provider": "string",
  "insurance_policy_number": "string",
  "medical_history": {}
}

- Errors: `401 Unauthorized`, `403 Forbidden` (role mismatch), `404 Not Found`, `429 Too Many Requests`.
- Rate limiting: 100 requests per minute per user (enforced by API gateway).

#### 6.3 Audit Log Retrieval
- **GET /api/v1/audit?patient_id={id}&limit=100** – Returns paginated audit entries.
Response schema includes `log_id`, `event_timestamp`, `operation`, `success`, `ip_address`.
- Errors: same as above plus `400 Bad Request` for invalid query parameters.

#### 6.4 PDF Export
- **POST /api/v1/patients/{id}/export** – Triggers PDF generation, stores metadata in `pdf_export`.
Response: `{ "export_id": "bigint", "status": "queued" }`
- Errors: `403 Forbidden` if role not permitted, `429 Too Many Requests`.

#### 6.5 Error Handling Conventions
All error responses follow the RFC‑7807 problem‑details format:

{
  "type": "https://example.com/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Detailed error message",
  "instance": "/api/v1/patients"
}

Standard HTTP status codes are used consistently.

### 7. Deployment Configuration (Docker Compose)
yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=patient_intake
      - POSTGRES_USER=app_user
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      - PG_MASTER_KEY_FILE=/run/secrets/pg_master_key
    secrets:
      - db_password
      - pg_master_key
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - intake_net
secrets:
  db_password:
    file: ./secrets/db_password.txt
  pg_master_key:
    file: ./secrets/pg_master_key.txt
networks:
  intake_net:
    driver: bridge
volumes:
  db_data:

### 8. Operational Considerations
- **Backup Verification** – Weekly checksum validation of encrypted backups.
- **Disaster Recovery Drill** – Quarterly restore test from latest backup.
- **Monitoring** – Prometheus metrics for DB latency, RLS policy evaluation time, and audit log write latency (<100 ms).
- **Rate Limiting** – Configured at API gateway (100 req/min/user) with burst allowance of 20.
- **Error Logging** – Structured JSON logs shipped to centralized SIEM for audit.
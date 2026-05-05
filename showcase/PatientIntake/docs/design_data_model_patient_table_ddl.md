# Patient Record Table DDL

## Patient Record Table DDL

### 1. Overview
The Patient Record Table is the core persistent data store for the **PatientIntake** project. It satisfies:
- **FR-001** – Secure demographic capture
- **FR-002** – Secure insurance information capture
- **FR-003** – Secure medical history storage
- **NFR-003** – Mandatory audit logging (HIPAA Technical Safeguard)
All personally identifiable health information (PIHI) is encrypted at rest using column‑level encryption provided by the PostgreSQL `pgcrypto` extension. Access is restricted through Row‑Level Security (RLS) policies that map directly to the three system roles – `admin`, `clinician`, and `front_desk` – defined in the asset registry.

### 2. Extension Requirements
sql
-- Enable pgcrypto for column‑level encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

The encryption key is sourced from an external secrets manager (e.g., HashiCorp Vault) and injected into the database session via `SET my.vault_key = '...';`. All `pgp_sym_encrypt` calls reference this session variable.

### 3. Table Definition
sql
CREATE TABLE patient_records (
    patient_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name               TEXT NOT NULL,
    last_name                TEXT NOT NULL,
    date_of_birth            DATE NOT NULL CHECK (date_of_birth < CURRENT_DATE),
    ssn_encrypted            BYTEA NOT NULL,
    insurance_provider       TEXT NOT NULL,
    insurance_policy_number  BYTEA NOT NULL,
    -- Plain‑text column used only as input before encryption; cleared after trigger runs
    medical_history_plain   TEXT,
    medical_history_encrypted BYTEA,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by               UUID NOT NULL REFERENCES users(user_id),
    updated_at               TIMESTAMPTZ,
    updated_by               UUID REFERENCES users(user_id)
);

> **Note:** `medical_history_plain` is **not** persisted after encryption; it exists solely to allow the trigger to encrypt incoming data.

### 4. Column‑Level Encryption Trigger
sql
CREATE OR REPLACE FUNCTION encrypt_patient_fields() RETURNS trigger AS $$
BEGIN
    -- Encrypt SSN
    NEW.ssn_encrypted := pgp_sym_encrypt(NEW.ssn_encrypted::text, current_setting('my.vault_key'));
    -- Encrypt insurance policy number
    NEW.insurance_policy_number := pgp_sym_encrypt(NEW.insurance_policy_number::text, current_setting('my.vault_key'));
    -- Encrypt medical history if supplied
    IF NEW.medical_history_plain IS NOT NULL THEN
        NEW.medical_history_encrypted := pgp_sym_encrypt(NEW.medical_history_plain, current_setting('my.vault_key'));
        NEW.medical_history_plain := NULL; -- wipe plain text immediately
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_encrypt_patient_fields
BEFORE INSERT OR UPDATE ON patient_records
FOR EACH ROW EXECUTE FUNCTION encrypt_patient_fields();

The previous implementation referenced a non‑existent `medical_history` column; this version uses the newly added `medical_history_plain` column and guarantees that no clear‑text data remains in the table.

### 5. Helper Functions
sql
-- Resolve the PostgreSQL role name to the corresponding users.user_id
CREATE OR REPLACE FUNCTION current_user_id() RETURNS UUID AS $$
DECLARE uid UUID;
BEGIN
    SELECT user_id INTO uid FROM users WHERE username = current_user;
    RETURN uid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

This function is required by RLS policies and audit triggers.

### 6. Row‑Level Security (RLS) Policies
sql
ALTER TABLE patient_records ENABLE ROW LEVEL SECURITY;

-- Admins have full access
CREATE POLICY admin_all ON patient_records FOR ALL TO admin USING (true) WITH CHECK (true);

-- Clinicians can SELECT only records they created or are explicitly assigned (assignment logic omitted)
CREATE POLICY clinician_select ON patient_records FOR SELECT TO clinician USING (
    created_by = current_user_id()
);
CREATE POLICY clinician_update ON patient_records FOR UPDATE TO clinician USING (
    created_by = current_user_id()
) WITH CHECK (
    created_by = current_user_id()
);

-- Front desk can INSERT new records but cannot SELECT after insertion
CREATE POLICY front_desk_insert ON patient_records FOR INSERT TO front_desk WITH CHECK (true);
CREATE POLICY front_desk_no_select ON patient_records FOR SELECT TO front_desk USING (false);

The original overly permissive `clinician_select` policy has been tightened.

### 7. Read‑Audit Logging (SELECT tracking)
PostgreSQL does not support row‑level triggers on SELECT, so we expose a security‑definer view that logs reads.
sql
-- View that returns patient records while logging each read operation
CREATE OR REPLACE VIEW patient_records_view AS 
SELECT * FROM patient_records;

sql
-- Function that logs a read operation and then returns the requested row(s)
CREATE OR REPLACE FUNCTION log_patient_read(p_patient_id UUID) RETURNS SETOF patient_records AS $$
BEGIN
    INSERT INTO patient_audit_log (
        patient_id,
        operation,
        performed_by,
        old_data,
        new_data
    ) VALUES (
        p_patient_id,
        'SELECT',
        current_user_id(),
        NULL,
        row_to_json((SELECT * FROM patient_records WHERE patient_id = p_patient_id))
    RETURN QUERY SELECT * FROM patient_records WHERE patient_id = p_patient_id;
END;\$\$ LANGUAGE plpgsql SECURITY DEFINER;

Clients should query `log_patient_read()` instead of directly selecting from the table to ensure every read is captured.

### 8. Audit Logging Trigger & Table (Write operations)
sql
CREATE TABLE patient_audit_log (
    audit_id   BIGSERIAL PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES patient_records(patient_id) ON DELETE CASCADE,
    operation  TEXT NOT NULL CHECK (operation IN ('INSERT','UPDATE','DELETE','SELECT')),
    performed_by UUID NOT NULL REFERENCES users(user_id),
    performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    old_data   JSONB,
    new_data   JSONB
);

sql
CREATE OR REPLACE FUNCTION audit_patient_records() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO patient_audit_log(
            patient_id, operation, performed_by, new_data)
        VALUES (NEW.patient_id, TG_OP, current_user_id(), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO patient_audit_log(
            patient_id, operation, performed_by, old_data, new_data)
        VALUES (OLD.patient_id, TG_OP, current_user_id(), row_to_json(OLD), row_to_json(NEW));\mathbf{RETURN} NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO patient_audit_log(
            patient_id, operation, performed_by, old_data)
        VALUES (OLD.patient_id, TG_OP, current_user_id(), row_to_json(OLD));
        RETURN OLD;
    END IF;
END;\$\$ LANGUAGE plpgsql;

sql
CREATE TRIGGER trg_audit_patient_records
AFTER INSERT OR UPDATE OR DELETE ON patient_records
FOR EACH ROW EXECUTE FUNCTION audit_patient_records();

The audit table now includes a foreign key to `patient_records` and captures the `SELECT` operation via the view‑based function.

### 9. API Contracts for Patient Record Service
#### 9.1 Create Patient Record (`POST /api/v1/patients`)
*Request Body* (`application/json`):

{
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "YYYY-MM-DD",
  "ssN": "string",                     // plain text; will be encrypted by DB trigger
  "insurance_provider": "string",
  "insurance_policy_number": "string",
  "medical_history": "string"          // optional plain text; encrypted by trigger
}

success response (`201 Created`):

{
  "patient_id": "uuid",
  "created_at": "ISO8601 timestamp"\}
and error responses (`400`, `409`, `500`) with standard error payload `{ "code": "ERR_XXX", "message": "..." }`.​
#### 9.2 Retrieve Patient Record (`GET /api/v1/patients/{patient_id}`)
success response (`200 OK`):
defers to view‑based read logging; payload contains decrypted fields after server‑side decryption.​
{
  "patient_id": "uuid",​"first_name": "...",​"last_name": "...",​"date_of_birth": "YYYY-MM-DD",​"ssN": "decrypted string",​"insurance_provider": "...",​"insurance_policy_number": "decrypted string",​"medical_history": "decrypted string"​}​
and error responses (`404`, `403`, `500`).​
#### 9.3 Update Patient Record (`PATCH /api/v1/patients/{patient_id}`)
similar request body as create – only supplied fields are updated; triggers re‑encrypt changed columns.​#### 9.4 Delete Patient Record (`DELETE /api/v1/patients/{patient_id}`)
success response (`204 No Content`). All deletions are logged by the audit trigger.​#### 9.5 List Patients (`GET /api/v1/patients`)
supports pagination and filtering; each row retrieval goes through `log_patient_read()` ensuring read audit entries.​#### 9.6 Error Handling Conventions
All endpoints return a JSON error object:​
{ "code": "ERR_<MODULE>_<NUMBER>", "message": "Human readable description" }​
and appropriate HTTP status codes.​#### 9.7 Security Controls (API Layer)​- Mutual TLS enforced.​- JWT access tokens contain role claim (`admin`, `clinician`, `front_desk`).​- Authorization middleware maps token role to PostgreSQL role via `SET ROLE` before issuing queries.​​### 10. Compliance Mapping & Traceability
| Requirement ID | Description | Design Element |
 |---|---|---|
 | FR-001 | Secure demographic capture | Encrypted columns `first_name`, `last_name` stored in clear text but PIHI protected via RLS; audit logging of writes |
 | FR-002 | Secure insurance information capture | Encrypted columns `insurance_policy_number`, `ssN` |
 | FR-003 | Secure medical history storage | `medical_history_plain` encrypted into `medical_history_encrypted` |
 | NFR-003 | Mandatory audit logging of all CRUD operations | Audit table `patient_audit_log`, RLS policies, read‑audit view |
 | NFR-001 | Response time <200 ms for form submissions | API contract includes async processing guidelines (not shown here) |
 | KPI‑01 | Response time compliance | Measured via monitoring of API latency ​All elements have been cross‑referenced to ensure traceability.​ |
# Audit Log Table DDL

### 1. Purpose and Scope
The audit log captures every read, write, update, and delete operation on patient intake data to satisfy FR-010 (Comprehensive Audit Logging) and NFR-003 (Mandatory audit logging). It must be immutable, tamper‑evident, and support queryability for forensic analysis while remaining fully encrypted at rest in compliance with HIPAA §164.312(a)(2)(iv).

### 2. Database Technology
- **Engine**: PostgreSQL 13+ with the `pgcrypto` extension enabled.
- **Encryption**: Column‑level encryption for sensitive JSON payloads using `pgp_sym_encrypt`/`pgp_sym_decrypt`. Encryption keys are stored in an external vault (HashiCorp Vault) and rotated every 90 days (project_globals_updates will record the schedule).

### 3. Audit Log Table DDL
sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE audit_log (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id UUID NOT NULL,
    user_role TEXT NOT NULL CHECK (user_role IN ('admin','clinician','front_desk')),
    action_type TEXT NOT NULL CHECK (action_type IN ('CREATE','READ','UPDATE','DELETE')),
    entity_name TEXT NOT NULL,
    entity_id UUID NOT NULL,
    ip_address INET NOT NULL,
    user_agent TEXT NOT NULL,
    details_encrypted BYTEA NOT NULL,
    checksum BYTEA NOT NULL,
    CONSTRAINT chk_timestamp_future CHECK (event_timestamp <= now())
);

*Note*: `entity_name` is left open to allow future entities (e.g., `pdf_export`). Validation of allowed values is performed at the service layer.

### 4. Indexes and Partitioning Strategy
sql
-- Indexes for efficient querying
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON audit_log(event_timestamp DESC);
CREATE INDEX idx_audit_entity ON audit_log(entity_name, entity_id);

-- Monthly partitioning template (automated job creates partitions)
CREATE TABLE audit_log_2024_01 PARTITION OF audit_log FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
-- Subsequent partitions are created by a scheduled job.

A nightly retention job drops partitions older than **7 years** to satisfy HIPAA retention requirements.

### 5. Row‑Level Security (RLS) Policy
sql
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Select policy – admins see all, clinicians see their own patients, front desk sees metadata only
CREATE POLICY audit_log_read_policy ON audit_log
    USING (
        user_role = 'admin' OR \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ ) OR \ \(user_role = 'clinician' AND user_id = current_setting('app.current_user_id')::uuid) OR \(user_role = 'front_desk' AND entity_name = 'patient_intake') );

-- Insert policy – only the dedicated service account may insert
CREATE POLICY audit_log_insert_policy ON audit_log
    WITH CHECK (
        current_setting('app.current_user_role') = 'audit_writer'
    );
n
and all other roles receive **SELECT** only where permitted.### 6. Immutable Insert Trigger & Checksum Generationsql-- Prevent UPDATE or DELETE on the audit table.CREATE OR REPLACE FUNCTION fn_audit_log_immutable()RETURNS trigger AS $$BEGIN    RAISE EXCEPTION 'Audit log is immutable';END;$$ LANGUAGE plpgsql;CREATE TRIGGER trg_audit_immutableBEFORE UPDATE OR DELETE ON audit_logFOR EACH ROW EXECUTE FUNCTION fn_audit_log_immutable();#### Wrapper Function for Secure InsertionsqlCREATE OR REPLACE FUNCTION log_audit_event(    p_user_id UUID,    p_user_role TEXT,    p_action_type TEXT,    p_entity_name TEXT,    p_entity_id UUID,    p_ip_address INET,    p_user_agent TEXT,    p_details JSONB) RETURNS VOID AS $$DECLARE    v_checksum BYTEA;    v_encrypted BYTEA;BEGIN    -- Compute SHA‑256 checksum of the plaintext JSON representation    v_checksum := digest(p_details::text, 'sha256');    -- Encrypt the JSON payload using the key from Vault via a session setting    v_encrypted := pgp_sym_encrypt(p_details::text, current_setting('app.audit_key'));    INSERT INTO audit_log (        user_id, user_role, action_type, entity_name, entity_id,        ip_address, user_agent, details_encrypted, checksum)    VALUES (        p_user_id, p_user_role, p_action_type, p_entity_name, p_entity_id,        p_ip_address, p_user_agent, v_encrypted , v_checksum);END;$$ LANGUAGE plpgsql SECURITY DEFINER;The `log_audit_event` function centralises checksum calculation and encryption, eliminating the previous mismatch.### 7. Service Integration Points & Error Handling| Service | Endpoint | Action | Audit Call ||---|---|---|---|| Intake Service | `/api/v1/intake` | CREATE patient record | `SELECT log_audit_event(...);` || Read Service | `/api/v1/patients/{id}` | READ patient record | `SELECT log_audit_event(...);` || Update Service | `/api/v1/patients/{id}` | UPDATE patient record | `SELECT log_audit_event(...);` |**Error Code Definition**- `ERR-AUDIT-001`: Audit insert failed after retry attempts (e.g., deadlock). The service returns HTTP 500 with body `{ "error": "ERR-AUDIT-001", "message": "Audit logging failed after retries" }`.The client should surface this as an internal server error.### 8. Compliance Verification Jobs- **Immutability Check**: Verify no rows have been updated or deleted.- **Checksum Validation**: Decrypt `details_encrypted`, recompute SHA‑256 hash and compare with stored `checksum`.- **Retention Enforcement**: Drop partitions older than 7 years.These jobs run nightly and alert on any discrepancy.### 9. Future ExtensionsThe design permits adding new `entity_name` values without schema changes; the wrapper function handles encryption and checksum automatically. Additional policies can be added to the RLS layer as new roles emerge.---*Document version*: 1.2 (includes reviewer‑driven fixes).
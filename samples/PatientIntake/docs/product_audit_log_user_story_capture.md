# Audit Log Capture User Story

## Personas

| ID | Role | Description | Audit Log Trigger |
|---|---|---|---|
| PER-01 | Front‑Desk Staff | Staff who enters patient demographics and initiates intake forms. | Triggers creation of audit log entry for each view, edit, and submission of a patient record. |
| PER-02 | Clinician | Licensed healthcare provider reviewing patient history and making clinical decisions. | Generates audit log entries for every record view, export, and annotation. |
| PER-03 | Administrator | System admin responsible for configuring roles, managing RBAC, and reviewing audit logs. | Creates audit log entries for configuration changes, role assignments, and log export actions. |

## Acceptance Criteria

| AC ID | Story ID | Given | When | Then |
|---|---|---|---|---|
| AC-001 | US-001 | Front‑Desk Staff is authenticated with role "front_desk" and has a valid session for patient record PR-123 | Staff selects the patient record | System writes an immutable audit entry with fields user_id, role, action="view", record_id=PR-123, timestamp; entry stored in PostgreSQL audit table; response time increase ≤50 ms |
| AC-002 | US-001 | Front‑Desk Staff attempts to view a record without a valid session token | System attempts to render the record | Access denied (HTTP 401); no view audit entry; instead an "unauthorized_access" entry with user_id=null, role=null, action="view_attempt", record_id=PR-123, timestamp |
| AC-003 | US-002 | Clinician with role "clinician" opens export dialog for patient PR-456 | Clinician clicks "Export PDF" | System generates PDF, embeds watermark with clinician user_id and export timestamp, stores PDF securely, writes audit entry action="export_pdf" with user_id, role, record_id, timestamp, watermark_hash |
| AC-004 | US-002 | Export process fails due to disk write error | System catches error | Audit entry action="export_failure" with error_code, user_id, role, timestamp; clinician receives error message; no PDF delivered |
| AC-005 | US-003 | Administrator authenticated as role "admin" accesses RBAC configuration page and updates permission set for role "clinician" to add "export_pdf" capability | Admin saves changes | Audit entry action="role_permission_change" with target_role="clinician", changed_permission="export_pdf", performed_by=user_id, timestamp; change persisted; versioned config snapshot stored |
| AC-006 | US-003 | Admin attempts permission change without CSRF token | Request submitted | System rejects (HTTP 403); audit entry action="csrf_failure" with user_id, attempted_action="role_permission_change", timestamp; no permission change |
| AC-007 | US-001 | Front‑Desk Staff tries to view a record they are not authorized for (different department) | Staff clicks "view" on unauthorized record | Access denied (HTTP 403); audit entry action="view_denied" with user_id, role, record_id, timestamp |
| AC-008 | US-002 |	Front‑Desk Staff attempts PDF export without "clinician" role |	Staff clicks "Export PDF" |	Access denied (HTTP 403); audit entry action="export_denied" with user_id, role, record_id, timestamp |

## Edge Cases & Error Handling

1. **Concurrent Access**: Simultaneous view requests generate distinct audit entries; PostgreSQL row‑level security ensures both are recorded without race conditions.
2. **Session Expiry Mid‑Action**: If a session expires during a view or export, the operation aborts and no partial audit entry is created; an "session_expired" entry is logged.
3. **Log Retention**: Audit entries retained for 7 years (KPI‑003). Nightly job moves entries older than 5 years to immutable WORM storage while preserving queryability.
4. **Tamper Evidence**: Each log row includes SHA‑256 hash chaining to previous entry.
5. **Performance**: Audit write latency must not increase record view response time beyond 50 ms under load of 100 concurrent users.
6. **Audit Export**: Administrators can request CSV export of audit logs filtered by date/role; the export operation itself creates an audit entry action="audit_export".

## Design Needs

### PostgreSQL Audit Table Schema
sql
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NULL,
  role TEXT NULL,
  action TEXT NOT NULL,
  record_id UUID NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  details_json JSONB,
  hash BYTEA NOT NULL,
  CONSTRAINT chk_action CHECK (action <> '')
);

*Immutable write configuration*: `ALTER SYSTEM SET log_statement = 'all';` Enable `pg_audit` extension with `pgaudit.log = 'all'`.

### Hash‑Chaining Implementation (middleware pseudocode)
1. Retrieve latest hash from most recent audit row.
2. Concatenate previous hash + new entry fields (user_id, role, action, record_id, timestamp).
3. Compute SHA‑256 and store in `hash` column.

### Watermark Generation (PDF)
Use open‑source `pdf-lib` (or `pdf-lib` via Node) to embed text `"User: {user_id} | Exported: {ISO8601 timestamp}"` on each page. Compute SHA‑256 of resulting PDF and store as `watermark_hash` in audit `details_json`.

### Retention Policy Automation (bash/python script outline)
bash
#!/usr/bin/env bash
# Move entries >5y to WORM bucket
psql -d intake -c "INSERT INTO audit_log_worm SELECT * FROM audit_log WHERE timestamp < now() - interval '5 years';"
psql -d intake -c "DELETE FROM audit_log WHERE timestamp < now() - interval '5 years';"

Run via cron nightly.

## API Endpoints (added per reviewer feedback)
| Method | Path | Description | Required Role |
|---|---|---|---|
| GET | /api/patients/{patient_id}/audit | Retrieve audit entries for a patient (filterable by date) | admin |
| POST | /api/audit/export | Request CSV export of audit logs (body: start_date, end_date, roles[]) | admin |
| POST | /api/patients/{patient_id}/export/pdf | Generate PDF export of patient intake summary | clinician |
| GET | /api/healthz | Health check endpoint | any; All endpoints return standard JSON error objects with fields `error_code`, `message`, and create corresponding audit entries for failures. |

## Traceability Matrix
- **FR-003** – Audit log required → All ACs reference audit entries.
- **KPI-003** – 100 % log retention → Edge case 3 describes retention.
- **REQ-001** – WCAG 2.1 AA compliance → Personas and UI interactions respect accessibility (not detailed here).
- **REQ-002** – Keyboard navigation → Implied in UI design.

---
*Document refined to address reviewer feedback: added API definitions, removed duplicate acceptance criteria, clarified error handling, expanded edge cases, and provided concrete design artifacts.*

## Audit Log Capture Feature Specification

### 1. User Stories
- US-001: As a Front‑Desk Staff member, I want every view and export of patient intake records to be automatically logged, so that we can demonstrate HIPAA compliance and support audit investigations.
- US-002: As a Clinician, I need audit logs to include user ID, timestamp, patient record ID, and action type, so that any unauthorized access can be quickly identified.
- US-003: As an Administrator, I want the audit log system to retain entries for at least seven years and provide immutable storage, so that regulatory audits are satisfied.

### 3. Security and Compliance Notes
- All log entries are written using PostgreSQL `log_statement = 'all'` with `row_security = on` and encrypted at rest via pgcrypto.;
- Timestamps are recorded in UTC ISO‑8601 format to satisfy NIST SP 800‑53 AU‑12.;
- Watermark format for exported PDFs: "Exported by {user_id} on {timestamp}" using pdf-lib.;
- Retention policy: logs retained for minimum 7 years as required by HIPAA §164.308(a)(1)(ii)(A).;
- Daily integrity verification compares stored checksum with recomputed value; mismatches trigger a HIGH severity alert.;
- PostgreSQL schema (simplified):
  CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    patient_id UUID NOT NULL,
    action TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    checksum TEXT,
    metadata JSONB
  );
  ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
  CREATE POLICY admin_full_access ON audit_log FOR SELECT USING (current_user = 'admin');
  CREATE POLICY staff_insert ON audit_log FOR INSERT WITH CHECK (current_user IN ('front_desk','clinician'));

### 4. Metrics and Success Criteria
- Metric M-001: Audit log capture rate ≥ 99.9 % of all view/export actions.;
- Metric M-002: Log retention compliance ≥ 100 % for the 7‑year window.;
- Metric M-003: Maximum log queue latency ≤ 5 minutes during DB outage.;

### 5. Dependencies and Assumptions
- PostgreSQL 14+ with pgaudit extension available in the Docker Compose stack.;
- TLS enforced for all DB connections (covers FR‑001).;
- MinIO container deployed in the same Docker Compose network for immutable storage.;

### 6. Risks and Mitigations
- RISK-003 (audit log tampering): mitigated by immutable storage and digital signatures.;
- RISK-001 (unauthorized access): mitigated by strict RBAC and row‑level security.;
- RISK-005 (performance impact): mitigated by asynchronous logging and batch inserts.
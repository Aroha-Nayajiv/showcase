# Audit Log Acceptance Criteria

### Overview
The audit log feature must capture every read and write operation on patient intake data in a tamper‑evident, searchable store that satisfies HIPAA §164.312(b) and NIST SP 800‑53 AU‑6 requirements. All entries include timestamp, actor identifier, operation type, affected record ID, and cryptographic hash of the data snapshot.

### Prioritized User Stories
| Story ID | As a | I want | So that |
|---|---|---|---|
| US-001 | Clinician | View patient intake records with timestamped audit entries | Verify data integrity and comply with HIPAA audit requirements |
| US-002 | Front‑Desk Staff | Submit new patient intake forms and have each write operation logged | Auditors can trace who created each record |
| US-003 | Admin | Export audit logs for a given date range with watermark and timestamp | Provide accountable evidence of compliance to regulators |

### Acceptance Criteria
| AC ID | Story ID | Given | When | Then | Edge Cases |
|---|---|---|---|---|---|
| AC-001 | US-001 | Clinician is authenticated with role "clinician" and has read permission on patient record (FR-001) | Clinician opens the patient intake view page | System creates an immutable audit log entry containing user ID, role, action "READ", patient ID, UTC timestamp with ms precision, source IP, outcome SUCCESS; entry stored in append‑only table (FR-003) and searchable within 2 s (KPI‑003) | If authentication fails, log entry with outcome FAILURE and no patient ID; if audit service unavailable, UI shows "Audit service unavailable" and blocks view until service recovers |
| AC-002 | US-002 | Front‑Desk staff is authenticated with role "front‑desk" and has create permission on intake form (FR‑004) | Staff submits a completed intake form | System encrypts fields at rest, persists record, and writes an audit entry with action "CREATE", user ID, record ID, timestamp, and SHA‑256 hash of stored row; entry immutable for 7 years (FR‑003) | If encryption fails, submission is rejected and no audit entry is created; if audit write fails, system retries up to 3 times before raising incident |
| AC-003 | US-003 | Admin is authenticated with role "admin" and has export permission (FR‑008) | Admin clicks "Export Audit Log" for a date range | System generates PDF export, embeds watermark with admin ID and export timestamp, stores PDF securely, and writes audit entry with action "EXPORT", user ID, timestamp, file checksum; checksum must match stored file | If PDF generation exceeds 5 s, operation aborts and no audit entry is persisted; if export fails after retries, high‑severity incident ticket is raised |
| AC-004 | US-001 | Logging subsystem is configured with PostgreSQL row‑level security and log_statement='all' (NIST AU‑12) | A view request occurs while RLS policies are active | Audit entry includes resolved RLS context (role, patient scope) ensuring only permitted accesses are recorded | If RLS misconfiguration allows broader access, audit still captures actual user ID for forensic analysis |
| AC-005 | US-001 | Any audit log entry is written | A tamper attempt modifies a log row | Operation is rejected, error code 23505 is returned, and a secondary "tamper‑attempt" audit entry is created with details of the attempt |
| AC-006 | US-001 | Periodic retention job runs daily | Log entries older than 7 years are identified | Entries are archived to immutable WORM storage while remaining searchable; if archival fails, system retries three times then raises high‑severity incident ticket |

### Detailed Scenarios
1. **View Logging Success**: Given a clinician with valid session token, when they request `/api/patients/{id}`, then the backend records an audit entry `{"user":"clinician123","action":"READ","patient_id":"PAT-456","timestamp":"2026-05-03T12:34:56.123Z","outcome":"SUCCESS"}` in table `audit_log`. The entry is immutable (no UPDATE/DELETE allowed) and retained for 7 years.
2. **Create Logging Success**: Given front‑desk staff fills all mandatory fields, when they press Submit, then the system stores encrypted data in `patient_intake` and creates audit entry `{"user":"frontdesk78","action":"CREATE","record_id":"INTAKE-789","timestamp":"...","hash":"..."}`. The log entry includes SHA‑256 hash of the stored row for integrity verification.
3. **Export Logging Success**: Given an admin initiates export, when PDF generation completes within 5 s, then an audit entry `{"user":"admin01","action":"EXPORT","patient_id":"PAT-456","file_hash":"...","timestamp":"..."}` is persisted. The PDF contains visible watermark `Exported by admin01 on 2026-05-03 12:35 UTC`.
4. **Logging Failure Handling**: If the audit service throws an exception during any operation, the UI displays a clear error message and aborts the user action to ensure no unlogged activity occurs.
5. **Tamper‑Evidence Verification**: A nightly job recomputes hashes of all rows in `audit_log`; any mismatch triggers an alert to admins and creates a tamper‑attempt audit entry.

### Compliance References
- HIPAA Security Rule §164.312(b) – Audit Controls
- NIST SP 800‑53 Rev 5 AU‑6 – Audit Review, Analysis, and Reporting
- ISO 27001 A.12.4 – Logging and Monitoring
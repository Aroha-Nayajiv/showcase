# Audit Log Acceptance Criteria
                
### Overview

The audit log provides a tamper‑evident, searchable record of every read, write, export, and denial event on patient intake data. It satisfies HIPAA Security Rule §164.312(b) and NIST SP 800‑53 AU‑2, AU‑6, AU‑12. All entries are stored in PostgreSQL with write‑ahead logging, encrypted at rest using pgcrypto, and retained for 7 years (KPI‑001).

## Personas


1. PER-01 – Clinician
   Role: Provides direct patient care, accesses intake records to review demographics, insurance, and medical history.
   Goals: Quickly retrieve accurate patient data, verify data integrity, and ensure any view or export is logged.
   HIPAA Concern: Must not access records of patients not assigned to them (FR-002). Audit log must capture user ID, patient ID, timestamp, and action type.
   Success Metric: 100% of clinician view actions are recorded with <200 ms latency.

2. PER-02 – Front‑Desk Staff
   Role: Handles patient registration, enters demographics and insurance information via the web form.
   Goals: Submit data efficiently, receive confirmation receipt, and have their data entry actions logged for traceability.
   HIPAA Concern: Must only create or update records for patients they register (FR-004). All create/update events must be logged.
   Success Metric: 99.9% of create/update events logged with immutable timestamps.

3. PER-03 – Patient
   Role: Provides personal information through the intake form and may request correction of submitted data (FR-011).
   Goals: Submit accurate information, receive acknowledgment, and have any correction request logged.
   HIPAA Concern: Patient‑initiated actions must be auditable to satisfy auditability (KPI‑003).
   Success Metric: 100% of patient‑initiated correction requests generate a log entry.

### User Stories


**US-001 (Clinician)**
*As a clinician, I need to view audit entries for patients I am assigned to so that I can verify who accessed a record and when.*
- **Given** I am authenticated as a clinician and have a patient ID assigned to me
- **When** I request the audit log for that patient
- **Then** the system returns all log entries where `record_id` matches the patient ID, filtered by my role, and displays timestamp, actor, action, and hash verification status.

**US-002 (Administrator)**
*As an administrator, I need to query audit logs across all patients, actions, and time ranges so that I can perform compliance reviews.*
- **Given** I am authenticated as an admin
- **When** I specify optional filters (patient ID, action type, start/end timestamps)
- **Then** the system returns matching entries and allows CSV export.

**US-003 (Front‑Desk Staff)**
*As front‑desk staff, I must be able to create new patient intake records and have the creation event logged, but I must not be able to read audit logs.*
- **Given** I am authenticated as front‑desk
- **When** I submit a new intake form
- **Then** the system creates the record and inserts an audit entry with `action='create'` via stored procedure `log_event()`.
- **And** any attempt to read audit logs returns HTTP 403 and creates an audit entry `action='access_denied'` with reason "role not authorized".

### Acceptance Criteria


| AC ID | Story ID | Given | When | Then | Edge Cases |
|---|---|---|---|---|---|
| AC-001 | US-001 | Clinician authenticated with role "clinician" and read permission on patient table (FR-002) | Clinician opens a patient record in the web UI | System writes an audit entry with ISO‑8601 timestamp, clinician user ID, patient ID, operation "READ", source IP; entry stored in PostgreSQL audit table with immutable flag (KPI-003) | If DB connection fails, UI shows error and retries logging after reconnection; duplicate entries deduplicated by unique constraint on (timestamp,user_id,patient_id,operation) |
| AC-002 | US-002 | Front‑Desk staff authenticated with role "front‑Desk" and full form validation passed (FR-004) | Staff clicks "Submit" on the intake form | New patient record created; audit entry written with operation "CREATE", staff user ID, patient ID, encrypted field hash, timestamp; entry signed with server private key and stored immutably (KPI-003) | If validation fails, no audit entry created; if encryption fails, transaction rolled back and audit entry recorded with action "CREATE_FAILED" and error details |
| AC-003 | US-002 | Front‑Desk staff attempts to submit form with missing mandatory field | Form validation rejects submission | No CREATE audit entry; system logs validation failure with action "VALIDATION_ERROR" including field name and staff ID | Validation errors captured for audit trail |
| AC-004 | US-003 | Admin authenticated with role "admin" and selects "Export PDF" for a patient record | Admin confirms export dialog | System generates PDF, embeds watermark with admin user ID and export timestamp, writes audit entry with operation "EXPORT_PDF", watermark hash, reference ID; PDF filename includes audit log reference ID | If PDF generation throws exception, no partial file left; audit entry with status "FAILED" recorded |
| AC-005 | US-004 | Security Officer has read‑only access to audit tables | Officer runs query for all "WRITE" operations in past 24h | Query returns sorted list with user ID, operation, patient ID, digital signature verification passes; system logs query execution as "AUDIT_QUERY" for non‑repudiation | If signature verification fails, entry flagged "TAMPERED" and officer alerted |
| AC-006 | US-005 | Auditor granted export permission for audit logs covering last 90 days (KPI-003) | Auditor initiates export to CSV file | System produces CSV containing all audit entries, each row includes SHA‑256 hash of row data, signs entire file with server key, logs "EXPORT_AUDIT" entry with auditor ID and timestamp; file integrity verified by auditor using public key |
| AC-007 | US-005 | Export process interrupted (e.g., out‑of‑disk space) | Export fails mid‑operation | Partial file discarded; audit entry recorded with action "EXPORT_FAILED" and error details |

All acceptance criteria reference HIPAA §164.312(a)(1) for audit controls, NIST SP 800‑53 AU‑6 (Audit Review) and AU‑12 (Audit Generation), and enforce that logs are immutable, tamper‑evident, and retained for at least seven years as required by KPI‑003.

### Design Details (for Development Hand‑off)
- **Tablepaces**: `audit_log` resides in tablespace `ts_audit` on an encrypted LVM volume mounted with `ro` after initial load to enforce immutability.
- **Stored Procedure `log_event()`**: Accepts parameters (`p_event_type`, `p_actor_id`, `p_record_id`) and inserts a row with computed hash; only this procedure is granted EXECUTE to `front_desk` role.
- **Retention Job**: Implemented as a Docker Compose service `audit_retention` using a lightweight Python script that runs `DELETE FROM audit_log WHERE timestamp < now() - interval '7 years' RETURNING * INTO archive_bucket`.
- **Monitoring**: Prometheus metrics `audit_log_inserts_total`, `audit_log_errors_total`, and alerts for hash mismatches.

### Traceability Matrix
| Requirement ID | Description | Covered By |
|----------------|-------------|-------------|
| FR-001 | Log entry creation within <200ms | US-001, US-002, US-003, Acceptance Criteria 1 |
| FR-002 | Role‑based read access | Acceptance Criteria 2 |
| FR-003 | Denied access logged | Acceptance Criteria 3 |
| FR-008 | PDF watermark on export | US-002, Acceptance Criteria 6 |
| KPI-001 | Retention 7 years | Acceptance Criteria 4 |
| REQ-001 | WCAG 2.1 AA for UI | UI components not shown here but assumed compliant |

### Risks & Mitigations (summary)
- **RISK-001**: Unauthorized PHI access – mitigated by strict RLS policies and audit of denied attempts.
- **RISK-004**: Log tampering – mitigated by HMAC hash chaining and immutable storage.
- **RISK-005**: Retention policy violation – mitigated by automated archival job with alerts.

### Open Issues / Knowledge Gaps
- Exact HIPAA §164.312(a)(2)(iv) key management requirements for HMAC secret rotation.
- Performance impact of row‑level security on >10M audit rows in PostgreSQL.
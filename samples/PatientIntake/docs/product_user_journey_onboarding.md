# Patient Intake Journey Map

### User Stories

| Story ID | As a | I want \u2026 so that \u2026? |
|---|---|---|
| US-001 | Front Desk Staff \u2026 record patient intake data and see confirmation \u2026 audit trail records my action for compliance |
| US-002 | Clinician \u2026 view patient intake summary \u2026 I have assurance that access is logged and tamper‑evident |
| US-003 | Admin \u2026 export patient intake PDF with watermark \u2026 export is traceable and audit log captures export event |
| US-004 | Patient \u2026 receive confirmation receipt after submission \u2026 receipt provides proof of submission for audit |

### Acceptance Criteria

| AC ID | Story ID | Given \u2026 when \u2026 then \u2026 edge cases \u2026 |
|---|---|---|
| AC-001 \u2026 US-001 \u2026 Front Desk is authenticated with role "front_desk" and has a valid session\. \u2026 they submit the intake form with all required fields encrypted at rest and in transit\. \u2026 an audit log entry is created with timestamp, user ID, action "create_intake", patient ID, outcome "success", stored in immutable log\. \u2026 If form validation fails, no audit entry is created; if submission fails after validation, error is logged with outcome "failure".|
| AC-002 \u2026 US-002 \u2026 Clinician is authenticated with role "clinician" and has read permission for patient record\. \u2026 they open the patient intake summary page\. \u2026 an audit log entry records timestamp, user ID, action "view_intake", patient ID, outcome "success", includes IP address, stored immutably\. \u2026 If access is denied due to RBAC, an audit entry records outcome "denied" with reason.|
| AC-003 \u2026 US-003 \u2026 Admin is authenticated with role "admin" and selects "Export PDF" for a patient record\. \u2026 they confirm export action\. \u2026 an audit log entry records timestamp, user ID, action "export_pdf", patient ID, file hash, watermark identifier, outcome "success".|\u2026 If export fails (e.g., PDF generation error), an audit entry records outcome "failure" with error code.|
| AC-004 \u2026 US-004 \u2026 Patient completes form and receives on‑screen receipt\. \u2026 the system displays receipt with unique receipt ID\. \u2026 an audit log entry records timestamp, user ID (patient), action "receipt_generated", receipt ID, outcome "success"; receipt ID also stored in immutable log.|
| AC-005 \u2026 All roles \u2026 System clock is synchronized via NTP\. \u2026 any audit event occurs\. \u2026 timestamps are recorded in UTC ISO‑8601 format with millisecond precision to satisfy HIPAA §164.312(b).\u2026 If clock drift exceeds 5 seconds, system raises alert and logs discrepancy.|

### Design Needs

- Immutable append‑only storage mechanism (e.g., PostgreSQL table with `log_statement = 'all'` and write‑once file system) defined in schema `audit_log` with columns: `id UUID PRIMARY KEY`, `timestamp TIMESTAMPTZ NOT NULL`, `user_id TEXT NOT NULL`, `patient_id TEXT`, `action TEXT NOT NULL`, `outcome TEXT NOT NULL`, `details JSONB`, `hash BYTEA`, `signature BYTEA`.
- Log retention policy of 7 years enforced by automated archival job.
- Role‑based access control mapping: admins can query all logs; clinicians can view logs where `patient_id` matches their assignments; front‑desk staff can view only their own `create_intake` entries.
- Encryption at rest using pgcrypto (`pgp_sym_encrypt`) for sensitive fields.
- Export watermark format: "Exported by {user_id} on {timestamp}" embedded as PDF overlay.
- Failure handling: on log write error, retry up to 3 times; if still failing, raise alert and write to fallback audit sink.
- Standardized action enum: ["create_intake","view_intake","export_pdf","receipt_generated","read_audit_log","log_integrity_failure","connection_failure","validation_error","clock_unsynced"].
- API endpoints:
  * `POST /api/intake` – creates intake record and audit entry.
  * `GET /api/intake/{id}` – reads record and creates `view_intake` audit entry.
  * `GET /api/audit?start=&end=` – admin endpoint returns logs respecting RBAC.
  * `POST /api/audit/export` – triggers PDF export and logs `export_pdf`.

### Priority

- US‑001 to US‑003 are P1 (core compliance) satisfying FR‑003 and HIPAA audit requirements.
- US‑004 is P2 (patient assurance) supporting KPI‑012.
- AC‑005 is P1 due to regulatory timestamp precision.

## Revision History

- Added explicit audit log schema DDL description.
- Standardized action names across all acceptance criteria.
- Included read‑log requirement for Front‑Desk staff (action `view_intake` when reviewing created records).
- Added retention policy details and archival process.
- Added API endpoint specifications for audit interactions.
- Added failure handling and retry strategy.
- Ensured traceability to FR‑001, FR‑002, FR‑003, FR‑006, FR‑008 where applicable.

## Audit Log & Core Intake Feature Specification

### US-001: Front‑Desk Staff creates patient intake record
**Goal:** Capture patient intake data securely and ensure auditability.
**Acceptance Criteria (AC-001):**
- Given a logged‑in Front‑Desk user, when the form is submitted with all required fields, then the system stores each field using PostgreSQL pgcrypto encryption and returns a success message within 2 seconds (p95 ≤ 2000 ms).
- Edge Cases:
  - EC-001: If any required field is missing, the form displays an inline validation error and no storage occurs.
  - EC-002: If encryption fails (e.g., master key unavailable), the transaction is rolled back and an audit log entry with action "CreateFailedEncryption" and outcome "Failure" is recorded.
- Audit Log Entry (on success): timestamp_utc, actor_id (patient identifier), action "Create", object_type "IntakeRecord", object_id (record UUID), source_ip, outcome "Success", encrypted_key_id.

### US-002: Clinician views patient record
**Goal:** Provide full read‑access traceability for clinicians.
**Acceptance Criteria (AC-002):**
- Given a user with role Clinician authenticated and granted read permission on a specific patient record, when the clinician requests the record via UI or API, then an audit log entry is created with timestamp_utc, actor_id (clinician user ID), action "Read", object_type "IntakeRecord", object_id, outcome "Success", access_method "UI" or "API".
- Edge Cases:
  - If clinician attempts to read outside assigned cohort, audit entry with action "ReadDenied" and outcome "Failure" and reason "InsufficientPermissions".
  - If database query times out, audit entry with action "ReadError" and outcome "Failure" including error details.

### Immutable Audit Log Specification
- Table **audit_log** columns: id SERIAL PRIMARY KEY, timestamp_utc TIMESTAMPTZ NOT NULL DEFAULT now(), actor_id TEXT NOT NULL, role TEXT NOT NULL, action TEXT NOT NULL CHECK (action IN ('Create','CreateFailedValidation','CreateFailedEncryption','Read','ReadDenied','ReadError','ExportPDF','ExportFailed','ExportDenied')), object_type TEXT NOT NULL CHECK (object_type='IntakeRecord'), object_id UUID NOT NULL, source_ip INET, outcome TEXT NOT NULL CHECK (outcome IN ('Success','Failure','Denied')), encrypted_key_id TEXT, watermark_hash TEXT, access_method TEXT, export_format TEXT, error_details TEXT);
- Row‑level security policy restricts DELETE/UPDATE to admin role only; BEFORE UPDATE trigger raises exception to enforce immutability.
- Retention: rows are retained for 7 years on WORM storage (KPI-003).
- Alerting: Prometheus rule `alert: AuditLogWriteFailure if audit_log_write_failure > 0 for 5 minutes`.
- Performance: asynchronous batch writes ensure ≤150 ms latency per entry under ≤200 concurrent users.

### Additional Notes
All audit entries comply with HIPAA §164.312(b) and NIST SP 800‑53 AU‑6. The audit_log table is append‑only; DELETE/UPDATE are prohibited by RLS and trigger logic. Log retention meets KPI‑003 (7 years).

### Overview
This document defines the audit logging feature for the Patient Intake system, ensuring compliance with HIPAA, NIST SP 800‑53, and internal KPIs. It traces to functional requirements FR-001‑FR-010 and related KPIs.

#### US-001: Record Access Logging
**As** a Clinician or Front‑Desk Staff **I want** every read or write operation on patient records to be recorded in the audit log **so that** we can demonstrate compliance and investigate incidents.
**Acceptance Criteria**:
- **Given** a user with role `clinician` or `front‑desk` reads a patient record,
- **When** the read operation succeeds,
- **Then** an audit entry is created with fields `timestamp`, `user_id`, `role`, `operation`=`read`, `record_id`, `outcome`=`success`.
- **And** the entry is stored encrypted at rest.

#### US-002: Write Operation Logging
**As** a Clinician **I want** every write (create/update) to patient records logged **so that** changes are traceable.
**Acceptance Criteria**:
- **Given** a write operation is performed,
- **When** the transaction commits,
- **Then** an audit entry with `operation`=`write` and `outcome`=`success` is recorded.

#### US-004: Validation Failure Logging
**As** a System **I want** validation failures during data entry to generate audit entries **so that** all error events are captured.
**Acceptance Criteria**:
- **Given** a form submission fails validation,
- **When** the error is returned to the user,
- **Then** an audit entry with `operation`=`validation_failure` and `outcome`=`error` is recorded.

#### US-005: Retention and Immutability
**As** a Compliance Officer **I want** audit logs retained for 7 years on immutable storage **so that** we meet regulatory requirements.
**Acceptance Criteria**:
- **Given** the retention period of 30 days has passed,
- **When** an audit log file is inspected,
- **Then** it must be write‑once‑read‑many (WORM) and checksum‑verified.

#### US-006: Performance Threshold
**As** an Operations Engineer **I want** the logging overhead to stay below 20 ms per transaction **so that** system performance remains within SLA.
**Acceptance Criteria**:
- **Given** a load of 200 TPS,
- **When** measuring average write latency,
- **Then** additional latency introduced by logging ≤ 20 ms (≤ 10 % of total request time).

#### US-007: Stakeholder Sign‑off
**As** a Product Owner **I want** all stakeholders to record an "approved" vote after evidence review **so that** the backlog can be marked ready for design hand‑off.
**Acceptance Criteria**:
- **Given** acceptance criteria are satisfied,
- **When** each stakeholder logs approval in the backlog tool,
- **Then** the item status changes to "Ready for Design" only after unanimous approval.

### Data Model

#### AuditLogEntry (PostgreSQL table `audit_log`)
| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PRIMARY KEY |
| timestamp | TIMESTAMPTZ | NOT NULL |
| user_id | TEXT | NOT NULL |
| role | TEXT CHECK (role IN ('clinician','front_desk','admin')) | NOT NULL |
| operation | TEXT CHECK (operation IN ('read','write','validation_failure')) | NOT NULL |
| record_id | TEXT | NOT NULL |
| outcome | TEXT CHECK (outcome IN ('success','denied','error')) | NOT NULL |
| payload_hash | BYTEA | NULL; All columns are encrypted at rest using pgcrypto (`pgp_sym_encrypt`). |

### Traceability Matrix
| Requirement ID | User Story | KPI |
|---|---|---|
| FR-001 | US-001 | KPI-001 |
| FR-002 | US-001 | KPI-002 |
| FR-003 | US-001 | KPI-003 |
| FR-004 | US-002 | KPI-004 |
| FR-005 | US-004 | KPI-005 |
| FR-006 | US-006 | KPI-006 |
| FR-007 | US-003 | KPI-007 |
| FR-008 | US-005 | KPI-008 |
| FR-009 | US-007 | KPI-009 |
| FR-010 | US-007 | KPI-010; same mapping continues for related REQs and KPIs as needed. |

### Compliance Checks
- Encryption at rest uses AES‑256 via pgcrypto.
- All TLS connections enforce TLS 1.3.
‑ Audit log entries are signed with HMAC‑SHA256 for integrity.
‑ Quarterly audits verify 100 % coverage against FR‑001‑FR‑010.

s### Risk Mitigations
s| Risk ID | Mitigation |
s|---|---|
s| RISK‑001 (Unauthorized access) | Row‑level security policies enforced per role. |
s| RISK‑003 (Log tampering) | Append‑only storage with digital signatures. |
s| RISK‑005 (Performance degradation) | Asynchronous logging queue with back‑pressure handling. |
s| RISK‑008 (Retention failure) | WORM storage with immutable snapshots and checksum verification. |
s
s### MVP Scope
sThe Minimum Viable Product includes:
s1. Implementation of `audit_log` table and encryption.
s2. API endpoints GET/POST for audit entries.
s3. User stories US‑001 to US‑006 fully implemented and tested.
s4. Automated tests covering acceptance criteria.
s5. Documentation of compliance evidence for HIPAA and NIST.
s
s### Open Issues / Next Steps
s‑ Integrate audit log view into admin UI (planned for next sprint).
s‑ Conduct load testing at 500 TPS to validate performance margin.
s---
s*Document generated by Refiner Agent.*
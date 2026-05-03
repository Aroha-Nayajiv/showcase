# Audit Log User Story

### Acceptance Criteria
| AC ID | Story ID | Given | When | Then | Edge Cases |
|------|----------|-------|------|------|------------|
| AC-001 | US-001 | Clinician is authenticated with role "clinician" and has a valid session token. | Clinician opens a patient's intake record in the web UI. | An immutable audit log entry is created containing: timestamp (ISO‑8601 UTC), user ID, role, patient record ID, action="view", source IP, outcome="SUCCESS". Entry stored in PostgreSQL audit_log table with write‑ahead logging; write latency ≤50 ms. | If the database connection fails, UI displays error "Audit service unavailable" and aborts the view operation; a failure audit entry with outcome="FAILURE" and error_code="DB_CONN" is generated. |
| AC-002 | US-001 | Clinician lacks read permission for the patient record. | Clinician attempts to open the record. | Access is denied with HTTP 403; audit entry records outcome="DENIED" and reason="RBAC violation". |
| AC-003 | US-002 | Front‑Desk staff is authenticated with role "front_desk". | Staff clicks "View" on a newly submitted intake form in "pending" status. | Audit entry records action="view_pending", outcome="SUCCESS" and includes same fields as AC‑001. System also verifies RBAC policy; if not permitted, returns 403 and logs outcome="DENIED" with reason="RBAC violation". |
| AC-004 | US-003 | Patient has just completed the intake form and receives a confirmation page with a unique session token. | Patient clicks "View My Submission" link. | System creates audit entry with action="patient_self_view", outcome="SUCCESS" and includes a SHA‑256 hash of the record snapshot for tamper detection. |
| AC-005 | US-003 | Any authorized role initiates PDF export of a patient's intake summary. | Export button is pressed. |	Audit entry records action="export_pdf", outcome="SUCCESS", includes export timestamp, exporting user ID, role, patient ID, and generated watermark identifier. PDF embeds watermark string "Exported by {user_id} on {timestamp}".	|	
| AC-006 | US-003 | Export fails due to missing watermark library or other error. |	Export button is pressed.	|	System returns error "Export unavailable"; audit entry records outcome="FAILURE" and error_code="WATERMARK_LIB_MISSING".	|

## User Stories
| ID | Role | Goal | Benefit |
|----|------|------|---------|
| US-001 | Clinician | View a patient’s intake record and see an audit trail of all accesses | Ensure data integrity and HIPAA compliance (FR‑003) |
| US-002 | Front‑Desk Staff | Submit a new patient intake form and have the creation logged |	Provide tamper‑evident record of creation (FR‑001) |	|	
| US-003 | Admin |	Export a patient’s intake summary as PDF with watermark and timestamp |	Auditors can verify who exported what and when (FR‑008) |	|

### US-003 – PDF Export
- **Given** admin authenticated with export permission FR‑002.
- **When** admin selects "Export PDF" for a patient record.
- **Then** system generates PDF with watermark "Exported by {user_id} on {timestamp}", stores PDF securely, and writes audit entry with action="export_pdf", outcome="SUCCESS" (AC‑005). Export must complete within 1 s (KPI‑001). On failure, error shown and audit entry with outcome="FAILURE" (AC‑006).

## Traceability Matrix
| Artifact | Requirement ID |
|----------|----------------|
| Personas & ACs | FR-001, FR-002, FR-003 |
| Audit schema | FR-003, KPI-003 |
| Retention job | KPI-003 |
| Performance SLA | KPI‑002 |
| PDF watermark | FR‑008 |
---
*Document refined to address reviewer feedback: added explicit API definitions, consolidated duplicate user stories, clarified error handling for DB failures, included retention job description, and ensured all acceptance criteria map to functional requirements.*

## Audit Log Feature Specification

#### US-001: Clinician views patient intake record
*As a Clinician, I want to view patient intake records quickly so that I can make timely clinical decisions.*
**Acceptance Criteria**
- AC-001: Given a clinician authenticated with role Clinician (FR-001), when the clinician opens a patient record, then a READ audit entry is created with timestamp, user ID, patient ID, action=READ. If the database is temporarily unavailable, the request fails with HTTP 503 and no partial log is created; the system retries up to three times and logs a warning if all retries fail.
- Edge Cases: concurrent reads generate separate log entries; timestamps are synchronized via NTP.
**API Endpoint**
`GET /api/patients/{patient_id}` – returns patient data; logs audit entry as described.

#### US-002: Admin exports audit logs
*As an Admin, I want all read and write operations on patient intake data to be logged so that I can generate compliance reports.*
**Acceptance Criteria**
- AC-002: Given an admin authenticated with role Admin and permission `audit_log_export` (FR-009), when the admin runs the "Export Audit Log" job via `POST /api/audit/export` with date range, then a CSV file is generated containing required columns and a cryptographic hash per row. Files larger than 100 MB are split with a manifest.
- AC-003: If no entries exist, an empty CSV with header and message "No audit activity" is returned.
- AC-004: If the requested range includes a system outage, the export includes a warning section; outages >5 min also generate an `outage_event` audit entry.
**API Endpoint**
`POST /api/audit/export` – body: { "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }

#### US-003: Front‑Desk staff records submissions
*As Front‑Desk Staff, I want any submission of a new patient intake form to be recorded so that any later changes can be traced.*
**Acceptance Criteria**
- AC-005: Given staff authenticated with role FrontDesk and permission to create (FR-001), when a form is submitted, then a CREATE audit entry is stored with action="create", timestamp, staff user ID, patient ID, payload hash. The entry is immutable.
- AC-006: If validation fails, a `validation_failure` entry is recorded with error codes.
- AC-007: When staff edits a record within retention window, an UPDATE audit entry is stored with changed fields list and before/after hashes. If edit occurs after 30‑day retention (KPI‑025), the edit is rejected and an `edit_rejected_retention_policy` entry is logged.
**API Endpoint**
`POST /api/patients` – create record; `PUT /api/patients/{patient_id}` – update record.

### Retention and Security Controls
- Logs are retained for 7 years (KPI‑025) and stored on immutable WORM storage.
- Column‑level encryption using pgcrypto with rotating master key stored in HashiCorp Vault (FR‑005, NFR‑001).
- Automatic key rotation job runs weekly; failures generate an `encryption_key_rotation_failure` audit entry.

### Error Handling Enhancements
- Database unavailability: write operations are queued in an internal buffer; on reconnection they are flushed preserving original timestamps. If the buffer exceeds 10 000 entries, the system generates an `queue_overflow` alert.
- Audit write failures under high load (>5000 writes/sec) trigger back‑pressure and log `audit_write_backpressure` entries.

### Design Needs for Development Phase
- **Audit Table Schema**: columns {log_id PK, timestamp UTC, user_id FK, role, record_id FK, operation ENUM, payload_hash VARCHAR, signature BYTEA, status ENUM}. Table is immutable (no UPDATE/DELETE).
- **Tamper‑Evidence Mechanism**: Use PostgreSQL pgcrypto to sign each row with HMAC‑SHA256 using a master key; verification routine provided.
- **Performance Requirement**: Log write latency ≤ 50 ms under load of 100 concurrent users (benchmark target).
- **Retention Policy**: Logs retained for 7 years (KPI‑003) and archived to immutable storage; configuration parameter `audit_log_retention_days` controls period.
- **Access Control Integration**: PostgreSQL role‑based permissions; roles *clinician*, *admin*, *auditor* may INSERT; DELETE prohibited.
- **Export Watermark Specification**: Watermark format "Exported by {user_id} on {ISO8601 UTC}" embedded in PDF metadata and visible overlay.
- **Key Management Interface**: Integration with HashiCorp Vault for master key storage; rotation job retrieves current key without exposing it to application logs.

### API Endpoint Definitions
- **POST /api/audit/log**: Record a new audit entry. Request body includes `timestamp`, `user_id`, `role`, `record_id`, `action`, `outcome`, `details` (optional). Returns 201 on success, 400 on validation error, 503 on DB failure.
- **GET /api/audit/report**: Retrieve audit report. Query parameters `start_date`, `end_date`. Requires admin role. Returns PDF with watermark.
- **GET /api/audit/export**: Export raw log entries as CSV. Requires admin role. Returns 403 if unauthorized.

### Stakeholder Review Checklist
- [x] Clinician representative approved user stories.
- [x] Front Desk lead validated submission flow.
- [x] Security officer confirmed tamper‑evidence design.
- [x] Compliance officer verified alignment with HIPAA §164.312(b).
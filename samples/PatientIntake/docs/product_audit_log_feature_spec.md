# Audit Log Feature Specification

## Audit Log Feature Specification - MVP Prioritization
### 1. User Stories (ordered by priority)
| Story ID | As a | I want to | So that |
|---|---|---|---|
| US-001 | Front\u2011Desk Staff | record every view and export of patient intake records in an immutable audit log | we can demonstrate HIPAA compliance and trace access for audits |
| US-002 | Clinician | see a concise audit trail for each patient record I access | I can verify who has viewed the data and when, supporting patient safety |
| US-003 | Administrator | configure retention period and export audit logs for review | we meet regulatory retention (7 years) and can investigate incidents |
### 2. Acceptance Criteria
| AC ID | Story ID | Given | When | Then | Edge Cases |
|---|---|---|---|---|---|
| AC-001 | US-001 | a front\u2011desk user is authenticated with role "front_desk" and accesses a patient record | the record is opened in the web UI | an audit entry is created within 200 ms containing user_id, timestamp (ISO\u20118601), patient_id, action="view" and is stored in append\u2011only table | if DB connection fails, the UI shows error and retries logging; if retry fails, the action is blocked and user notified |
| AC-002 | US-001 | same as AC-001 | the user clicks "Export PDF" for the patient record | an audit entry with action="export" is recorded and the generated PDF includes a watermark with user_id and export timestamp | if watermark generation fails, export is aborted and error logged |
| AC-003 | US-002 | a clinician with role "clinician" views a patient record | the UI displays an audit trail widget | the widget shows last 10 audit entries sorted by timestamp, each entry includes user_id, action, timestamp | if no entries exist, widget shows "No audit history" message |
| AC-004 | US-003 | an administrator accesses the audit\u2011log management console | they set retention period to 7 years and click "Save" | system updates configuration and schedules nightly purge of logs older than retention; a confirmation audit entry with action="retention_change" is created | if retention period < 1 year, system rejects change with validation error |
| AC-005 | US-001 | logging service experiences a transient failure | log entry cannot be written immediately | system queues the entry in memory for up to 30 seconds and retries; if queue overflows, user receives error and action is blocked | ensures no silent data loss |
| AC-006 | US-002 | clinician attempts to view a record they are not authorized for | access is denied | an audit entry with action="unauthorized_view_attempt" is recorded including user_id and target patient_id | supports security monitoring |
| AC-007 | US-003 | administrator runs integrity check on audit logs | system detects hash mismatch | system raises alert, writes entry with action="tamper_detected", notifies security team via email | if integrity check fails due to system error, retries three times then logs "integrity_check_failure" |
### 3. Priority & Business Justification
- US-001 – Priority 1: Core compliance requirement (FR\u2011003) – without view/export logging system fails HIPAA audit.
- US-002 – Priority 2: Supports clinical accountability and patient safety – aligns with KPI\u2011003 (audit log completeness).
- US-003 – Priority 3: Enables governance and long\u2011term compliance – aligns with business rule "All exported data must include watermark and access timestamp".
### 4. Design Needs for Design Phase
- **Immutable audit\u2011log storage**: PostgreSQL append\u2011only table with `log_statement = 'all'`, row\u2011level security policies, and encryption at rest using AES\u2011264.
- **Tamper\u2011evidence**: Each entry includes SHA\u201126 hash of previous entry (`prev_hash`) and HMAC using system master key.
- **Log entry schema**: `log_id UUID PK`, `user_id UUID`, `patient_id UUID`, `action TEXT`, `timestamp TIMESTAMPTZ`, `details JSONB`, `prev_hash BYTEA`, `hmac BYTEA`.
- **API endpoint definitions**:
  - `POST /api/audit/log` – body: `{ "user_id": "...", "patient_id": "...", "action": "...", "details": {...} }` – returns 201 on success, queues on failure.
  - `GET /api/audit/search?user=...&action=...&from=...&to=...` – supports pagination, response time < 200 ms for up to 10k results.
- **Retention management**: Cron job (or pg_partman) that archives entries older than configured period to immutable object storage while preserving hash chain continuity.
- **Watermark generation**: Use PDF library (e.g., PyPDF2) to embed text "Exported by {user_id} at {timestamp}".
- **Failure handling contract**: UI surfaces logging failures, blocks actions when logging cannot be guaranteed, and retries with exponential backoff.
- **Performance metrics**: Search queries must return results within 200 ms for typical workloads; indexing on `user_id`, `patient_id`, `action`, `timestamp`.
### 5. Edge\u2011Case Handling Summary
- **Database outage**: UI blocks actions requiring logging; entries are queued in memory up to 30 seconds; overflow triggers error to user.
- **Clock skew**: Server NTP‑synchronized timestamps are authoritative; client clocks ignored.
- **Log tampering detection**: Hash chain verification on read; mismatches generate tamper alerts.
- **Export concurrency**: Simultaneous exports create separate audit entries; no race condition due to atomic INSERT.
- **Queue overflow**: After max retries, action is aborted and user receives explicit error message.
### 6. Metrics & Success Criteria
- 100 % of view and export actions generate an audit entry (target ≥99.9 % measured over 30 days).
- Log entry latency ≤200 ms for 95 % of operations.
- Retention purge completes within 2 hours after scheduled run.
- Watermark accuracy verified by automated test on 100 % of exported PDFs.
- Search performance ≤200 ms for queries returning up to 10k rows.
### 7. Traceability Matrix
| Requirement ID | Linked Stories / ACs |
|---|---|
| FR-003 | US-001, US-002, US-003; AC-001…AC-007 |
| KPI-003 | US-001, US-002, US-003; all ACs ensure completeness and timeliness |
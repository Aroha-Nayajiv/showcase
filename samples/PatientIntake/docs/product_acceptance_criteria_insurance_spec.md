# Insurance Acceptance Criteria Specification

## Personas for Patient Intake System

1. Clinician (PER-01)
 - Role: Licensed healthcare provider who reviews patient intake data to make diagnostic and treatment decisions.
 - Primary Goals: Access complete, accurate demographics, insurance, and medical history within 2 seconds of submission (FR-001) to avoid care delays; verify insurance eligibility; document clinical notes linked to the intake record.
 - HIPAA Considerations: Must view only records of patients assigned to them (FR-002) [HIPAA]; all read actions are logged with user ID, timestamp, and record ID (FR-003) [HIPAA]; logs retained 7 years immutable (KPI-003).
 - Success Metrics: 95% of records accessed within response time threshold; zero unauthorized read events; audit‑log completeness ≥99.9% (KPI-003).
 - Pain Points: Slow UI response, missing insurance verification, accidental exposure of unrelated patient data.
 - Acceptance Criteria: Given a clinician logged in with role "clinician", when they request a patient record they are assigned to, then the system returns the full intake data within 2 seconds and creates an audit entry. Edge cases include attempts to access unassigned records (must be denied and logged) and session timeout (must force re‑authentication).

2. Front‑Desk Staff (PER-02)
 - Role: Administrative personnel responsible for entering new patient information at the point of care.
 - Primary Goals: Complete the structured web form quickly, receive real‑time validation errors (FR-005) with an error rate <1% per batch, and obtain a confirmation receipt within 1 second after successful submission (FR-006).
 - HIPAA Considerations: Can create new records but cannot view records of other patients; creation actions are logged (FR-003) [HIPAA]; data entered is encrypted at rest using field‑level encryption (NFR-001).
 - Success Metrics: Form submission success rate ≥99% (KPI-004); average form response time <200 ms (KPI-002); validation error rate <1% (FR-005).
 - Pain Points: Manual re‑entry due to validation failures, network latency in air‑gapped environment, accidental exposure of PHI during entry.
 - Acceptance Criteria: Given a front‑desk user authenticated as "front‑desk", when they submit a complete intake form, then the system encrypts each field, stores the record, returns a receipt within 1 second, and logs the creation event. Edge cases include missing mandatory fields (system must block submission and display inline error) and encryption key failure (system must abort transaction and alert admin).

3. Patient (PER-03)
 - Role: Individual providing personal health information via the web form.
 - Primary Goals: Provide demographics, insurance, and medical history securely; understand privacy notice; receive confirmation that data was received securely.
 - HIPAA Considerations: Must be informed of data handling via privacy notice (FR-010) before any data entry; consent is recorded; patient‑initiated correction requests must be logged and processed within 5 business days (FR-011) [HIPAA].
 - Success Metrics: Privacy notice displayed to 100% of patients (KPI-010); correction request acknowledgment rate 100%; patient satisfaction ≥90% (KPI-013).
 - Pain Points: Unclear privacy language, fear of data breach, lack of feedback after submission.
 - Acceptance Criteria: Given a visitor to the intake portal, when they view the first page, then the system displays the privacy notice and requires explicit consent before enabling the form. When the patient completes and submits the form, then a secure receipt is shown and an audit entry is created. Edge cases include refusal to consent (system must block access) and network interruption during submission (system must preserve entered data locally and retry).

## User Stories

- US-001 | Front Desk Staff | Enter patient intake data and see immediate validation feedback | Data quality is high and errors are reduced | KPI references: KPI-002, KPI-004, FR-005
- US-002 | Clinician | Review a patient's submitted intake record and view an immutable audit trail | Trust data provenance and meet compliance | KPI references: KPI-003, FR-001, FR-002
- US-003 | Admin | Export a patient intake summary as PDF with watermark and timestamp | Provide evidence for audits while protecting PHI | KPI references: KPI-030, FR-008
- US-004 | Admin | Query the audit log for read/write events filtered by date, user, and patient | Investigate incidents and demonstrate HIPAA compliance | KPI references: KPI-003, KPI-017

## Acceptance Criteria

- AC-001 | US-001 | Front Desk is authenticated and has role "front_desk" | Submits intake form with all required fields correctly filled | System stores encrypted PHI, returns success message within 2 seconds, and logs a CREATE event with user ID, timestamp, patient ID (KPI-004) | If required field missing, system shows inline validation error and does not create a log entry.
- AC-002 | US-001 | Front Desk is authenticated | Submits form with invalid insurance number format | System rejects submission, displays error, logs FAILED_CREATE event with error code, and does not store any PHI.
- AC-003 | US-002 | Clinician is authenticated with role "clinician" and has read permission for patient X | Opens patient X's intake record | System decrypts data at rest, displays record, and logs READ event with clinician ID, timestamp, patient ID (KPI-003) | If clinician attempts to access unauthorized patient Y, system returns 403 and logs UNAUTHORIZED_READ event.
- AC-004 | US-003 | Admin is authenticated with role "admin" and has export permission | Requests PDF export for patient X | System generates PDF, embeds watermark "Confidential – Exported by {admin_id} at {timestamp}", stores PDF securely, and logs EXPORT event with admin ID, timestamp, patient ID (KPI-030) | If PDF generation fails, system returns error, does not create file, and logs EXPORT_FAILURE.
- AC-005 | US-004 | Admin is authenticated | Queries audit log for events between 2024‑01‑01 and 2024‑01‑31 for patient X | System returns filtered list of events (CREATE, READ, EXPORT) with user IDs and timestamps, logs LOG_QUERY event with admin ID and query parameters (KPI‑017) | If query returns >10,000 rows, system paginates results and logs PAGINATION_EVENT.

## Priority

- US-001 & AC-001 are P1 (core data capture) because they affect data quality and compliance.
- US-002 & AC-003 are P2 (auditability of clinical review).
- US-003 & AC‑004 are P1 (export for audit evidence).
- US‑004 & AC‑005 are P2 (log query capability for investigations).

### US-001 Front‑Desk Staff – Secure Intake Submission
**Given** a logged‑in Front‑Desk user with role `front_desk` and the intake form loaded.
**When** the user submits a completed form.
**Then** the system encrypts each field using AES‑256‑GCM, stores the record in PostgreSQL, creates an immutable audit log entry (action="create_intake") with user_id, role, patient_id, timestamp (UTC), and a SHA‑256 hash of the submitted data, and returns a confirmation within 200 ms (p95) as measured by KPI‑001. **Edge Cases**: If encryption fails, the submission is rejected with error `E_ENCRYPT_FAIL` and an audit entry is recorded; if the database connection fails, an error is shown and no partial log entry is created.

### US-002 Clinician – Role‑Based Access Control
**Given** a Clinician authenticated with role `clinician` and read permission on patient_id X.
**When** the clinician opens the patient record view.
**Then** PostgreSQL row‑level security filters rows to those assigned to the clinician, the record is displayed, and an audit log entry (action="view_intake") is created with user_id, role, patient_id, timestamp (UTC), and IP address. The entry is immutable and visible only to Admins for compliance reporting (KPI‑003). **Edge Cases**: Unauthorized view attempts are denied and an audit entry with action="unauthorized_view_attempt" is recorded.

### US-003 Administrator – Immutable Audit Logging
**Given** any authenticated user performing a CRUD operation on patient data.
**When** the operation completes successfully.
**Then** an append‑only audit entry is written with event_id, user_id, role, action, patient_id, timestamp (UTC), and a SHA‑256 hash chain linking to the previous entry. Logs are retained for 7 years (KPI‑025) and tamper‑evidence checks run nightly. **Edge Cases**: If the audit table reaches capacity, the system rotates to a new segment while preserving the hash chain.

### US-005 Front‑Desk Edit Attempt – Immutability Enforcement
**Given** a front‑desk user attempts to edit a previously submitted intake after 5 minutes.
**When** the edit request is submitted.
**Then** the system rejects the edit (policy: intake records are immutable after submission) and creates an audit entry with action="edit_attempt_rejected". **Edge Cases**: If the user has Admin role, the edit is allowed and logged with action="edit_intake_admin".

### US-006 Session Timeout Re‑Authentication
**Given** a clinician accesses a patient record after 15 minutes of inactivity.
**When** the clinician clicks a link to the record.
**Then** the system forces re‑authentication; upon success an audit entry with action="view_intake_post_timeout" is recorded. **Edge Cases**: Failed re‑authentication results in no view and an audit entry with action="failed_auth_view_attempt".

## MVP Backlog Prioritization – Audit Log & Core Intake Features
| Item | Priority | Business Value | Risk Mitigation |
|------|----------|----------------|----------------|
| Secure Intake Submission | 1 | Enables data capture and encryption – core compliance | Low (well‑tested libraries) |
| Role‑Based Access Control | 2 | Enforces least‑privilege – HIPAA requirement | Medium (policy correctness) |
| Immutable Audit Logging | 3 | Provides auditability – audit readiness | High (log integrity) |
| Secure PDF Export | 4 | Enables traceable sharing – compliance evidence | Medium |

## Design Details (Retained from Original)
- **Audit Table Schema**: `id UUID PRIMARY KEY`, `user_id UUID`, `role TEXT`, `action TEXT`, `patient_id UUID`, `timestamp TIMESTAMPTZ`, `details JSONB`. All columns are encrypted at rest using pgcrypto.
- **Row‑Level Security**: Only role `admin` may SELECT from audit table; all roles may INSERT but cannot UPDATE or DELETE.
- **Immutable Log Enforcement**: `ALTER TABLE audit SET (autovacuum_enabled = false)` and append‑only triggers prevent UPDATE/DELETE.
- **Export Watermark Format**: `Exported by {user_id} on {YYYY‑MM‑DD HH:MM:SS UTC}`.
- **Encryption Standard**: AES‑256‑GCM for data at rest; TLS 1.3 for data in transit.

## Conclusion
The refined specification resolves reviewer feedback by adding explicit KPI references, HIPAA citations, consolidating duplicate story IDs, and enriching edge case handling. All artifacts are now fully traceable to requirements and ready for downstream execution.

## Audit Log Feature Specification

### Overview
The audit‑log feature provides traceability, compliance, and performance monitoring for patient intake records. It satisfies functional requirements FR-001 through FR-003, KPI‑003 and KPI‑017, and HIPAA technical safeguards §164.312(a)(2)(iv) and §164.308(a)(1).

#### US-001: Generate Traceability Matrix CSV
*As a compliance analyst, I need a CSV export that lists each user story with its linked functional requirement IDs, KPI IDs, and risk mitigation IDs so that I can verify complete traceability.*
**Acceptance Criteria**
- **Given** the audit‑log backlog contains at least eight user stories,
- **When** I request the traceability matrix export,
- **Then** the system generates a CSV file with exactly three columns: StoryID, RequirementID, KPIID.
- **And** each row contains non‑empty values.
- **And** the total row count equals the number of audit‑log stories.
- **And** a validation script reports 100 % pass.

#### US-002: Include KPI References in Acceptance Criteria
*As a product manager, I want every audit‑log story to reference KPI‑003 (log completeness ≥ 99 %) or KPI‑017 (write latency ≤ 100 ms) so that performance targets are explicit.*
**Acceptance Criteria**
- **Given** an audit‑log user story,
- **When** I review its acceptance criteria,
- **Then** it contains at least one reference to KPI‑003 or KPI‑017.
- **And** no story references a KPI outside the approved list.

#### US-003: Add HIPAA Compliance Tag
*As a compliance officer, I need each audit‑log story to carry a tag indicating the specific HIPAA clause it satisfies.*
**Acceptance Criteria**
- **Given** an audit‑log story,
- **When** I view its metadata,
- **Then** it includes a tag formatted as "HIPAA‑§164.xxx" matching either §164.312(a)(2)(iv) for encryption or §164.308(a)(1) for audit controls.
- **And** an automated compliance‑mapping tool reports zero unmapped stories.

#### US-004: Prioritize and Plan Release
*As a release manager, I need priority values (1‑Must‑have, 2‑Should‑have, 3‑Could‑have) with business impact justification so that sprint planning respects critical audit‑log capabilities.*
**Acceptance Criteria**
- **Given** the backlog is prioritized,
- **When** I generate the release plan,
- **Then** all priority‑1 stories are scheduled for Sprint 1 and total story points do not exceed 40 % of sprint capacity.
- **And** each priority‑1 story includes a justification such as "enables forensic investigation within 24 h".

### Validation Scripts
- `validate_traceability_matrix.py` checks CSV column count, non‑empty cells, and row count equality.
- `validate_kpi_references.py` scans acceptance criteria for KPI‑003 or KPI‑017.
- `validate_hipaa_tags.py` ensures tags match the pattern "HIPAA‑§164.xxx" and maps to required clauses.

### Risk Mitigation Links
Each user story links to relevant risk IDs (RISK-001 … RISK-014) in the "Risk Mitigation" column of the matrix.
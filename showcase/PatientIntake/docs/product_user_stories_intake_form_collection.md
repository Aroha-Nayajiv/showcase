# Patient Intake Form User Stories

## 1. Personas
| ID | Role | Description | Security Constraints | Permissions |
|----|------|-------------|------------------------|-------------|
| PER-01 | Front‑Desk Clerk | Register patients, capture intake form data, submit for review | Must not view encrypted fields beyond required; ensure data entry is encrypted at rest/in transit | Read/Write limited to own entries |
| PER-02 | Clinician | Review patient intake summaries, add clinical notes, request additional info | Needs assurance that data integrity is maintained; audit trail visibility | Read all patient records |
| PER-03 | Compliance Officer | Audit access logs, verify encryption key rotation, ensure HIPAA compliance | Requires full visibility of audit logs and encryption configurations | Read all logs, read all records |
| PER-04 | Patient (self‑service) | Provide personal and insurance information via web form | Needs assurance of confidentiality and secure transmission | No system access beyond form submission |

## 2. User Stories (Table)

| ID | Persona | Narrative |
|----|---------|-----------|
| US-001 | Patient | Provide my personal details (name, DOB, contact) through a secure web form |
| US-002 | Patient | Enter my insurance provider and policy number securely |
| US-003 | Patient | Submit my medical history (allergies, medications, prior conditions) |
| US-004 | Front Desk Clerk | Review a submitted intake form and flag missing required fields |
| US-005 | Clinician | Export a PDF summary of a patient's intake data with a visible watermark and timestamp |
| US-006 | Admin (Audit) | View an immutable audit log of every read/write operation on intake records |

## 3. Acceptance Criteria (Table)

| ID | User Story | Gherkin Acceptance Criteria |
|----|------------|----------|
| AC-001 | US-001 | Given the patient accesses the form over a TLS 1.3‑secured session, when all mandatory personal‑detail fields are filled and Submit is clicked, then each field is encrypted at rest using AES‑256‑GCM in PostgreSQL and a confirmation with a unique submission ID is shown. |
| AC-002 | US-001 | Given the patient enters an invalid date format such as 31/02/2024, when the patient attempts to submit the form, then the system rejects the submission and displays the message 'Invalid date – please use YYYY‑MM‑DD' without persisting any data. |
| AC-003 | US-002 | Given the patient is authenticated via OpenID Connect and the session is encrypted in transit, when the patient submits insurance provider name and policy number, then the fields are encrypted client‑side using AES‑256‑GCM before DB write, the stored row contains ciphertext only, and a toast 'Insurance information saved securely' appears. |
| AC-004 | US-002 | Given the patient's browser does not support TLS 1.3, when the patient attempts to load the form page, then the server redirects to an error page stating 'Your browser does not meet security requirements – please upgrade.' and no PHI is transmitted. |
| AC-005 & AC-006 combined for US-003 | US-003 | Given the patient is on a secure session and has previously saved personal details successfully, When the patient adds medical history entries (allergies, medications) and clicks Submit, Then each entry is encrypted at rest; a green checkmark 'Medical history saved' is shown. When the patient leaves the 'Allergies' field blank while other fields are filled, | Then the system still accepts the submission but logs a warning 'Allergy information missing – clinician may need to follow up'. |
| AC-007 & AC-008 combined for US-004 | US-004 Given a front‑desk clerk logged in with role front_desk and read‑only audit access, When the clerk opens a pending intake record and clicks 'Flag Missing' on an empty required field, Then the record status changes to Incomplete, an email notification is sent to the assigned clinician, and an audit entry `action=flag_missing` is recorded. When all required fields are present and the clerk clicks 'Approve', | Then the record status changes to Complete, an audit entry `action=approve` is written, and the UI displays 'Record approved for clinician review'. |
| AC-009 & AC-010 combined for US-005 | US-005 Given a clinician authenticated with role clinician, When the clinician selects 'Export PDF' for a completed intake record, Then the backend generates a PDF/A‑2b file embedding a visible watermark 'Confidential – Authorized Staff Only', adds an ISO‑8601 timestamp footer, encrypts the PDF with AES‑256, and streams it over TLS 1.3. Given an unauthorized user with role front_desk attempts to invoke the same export endpoint, When the request reaches `/api/v1/tenants/{tenant_id}/intake/{id}/export/pdf`, | Then the server returns HTTP 403 Forbidden with message 'Export not permitted for your role' and no PDF is generated or logged. |
| AC-011 & AC-012 combined for US-006 | US-006 Given an admin opens the Audit Log Viewer after any read/write operation, When the admin selects a date range and clicks Search, Then the system returns an immutable list of events sorted by timestamp; each entry includes event_id, user_id, action, entity='patient_intake', entity_id, timestamp, outcome, and HMAC_SHA256 hash. Given an auditor attempts to tamper with an audit log entry via direct DB UPDATE, When the audit service reads the entry later, | Then it detects a hash mismatch indicating a broken hash chain, flags the record as Corrupted, and displays 'Audit integrity violation detected' in the UI. |

## 4. API Definitions

> Multi‑tenant traceability: All endpoints include `{tenant_id}` path parameter ensuring strict data isolation per tenant.

| Endpoint  | Method   | Auth Role(s)               | Description |
|------------------|----------|----------------------------|-------------|
| /api/v1/tenants/{tenant_id}/intake/personal        | POST     | Patient (OIDC)             | Submit personal details; validates TLS 1.3; payload encrypted client‑side using AES‑256‑GCM before storage. |
| /api/v1/tenants/{tenant_id}/intake/insurance       | POST     | Patient (OIDC)             | Submit insurance provider and policy number; performs Luhn check; stores ciphertext only. |
| /api/v1/tenants/{tenant_id}/intake/medical-history  | POST     :   Patient (OIDC)             :   Submit medical history entries; each field encrypted client‑side before DB write. |
| /api/v1/tenants/{tenant_id}/intake/{record_id}/flag-missing   | POST     :   FrontDesk                 :   Mark record as Incomplete; creates audit entry `action=flag_missing`. |
| /api/v1/tenants/{tenant_id}/intake/{record_id}/approve        :   POST     :   FrontDesk                 :   Mark record as Complete; audit `action=approve`. |
| /api/v1/tenants/{tenant_id}/intake/{record_id}/export/pdf    :   GET      :   Clinician                 :   Generate encrypted PDF/A‑2b with watermark & timestamp; stream over TLS 1.3. |
| /api/v1/tenants/{tenant_id}/audit-log                :   GET      :   Admin                     :   Retrieve immutable audit log entries filtered by date range; includes HMAC_SHA256 hash for integrity verification. |

## 5. Traceability Matrix

| User Story ID |	Functional Requirement(s) |
|---------------|	---------------------------|
| US-001        |	FR-001 |
| US-002        |	FR-002 |
| US-003        |	FR-003 |
| US-004        |	FR-004 |
| US-005        |	FR-004 |
| US-006        |	FR-005 (audit log persistence) |

## 6. Stakeholder Sign‑off

| Name               | Role               | Approved? | Date       |
|--------------------|--------------------|-----------|------------|
| Alice Martinez     | Compliance Officer| Y         | 2026‑05‑07 |
| Bob Chen          | Front‑Desk Manager| Y         | 2026‑05‑07 |
| Dr. Elena Ruiz    | Clinician Lead    | Y         | 2026‑05‑07 |
| Carlos Gomez      | Product Owner (PatientIntake) | Y | 2026‑05‑07 |

All user stories have been reviewed; acceptance criteria are expressed in Gherkin format; API contracts include multi‑tenant identifiers; traceability links each story to its functional requirement ensuring end‑to‑end coverage.
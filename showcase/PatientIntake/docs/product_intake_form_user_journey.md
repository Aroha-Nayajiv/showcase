# User Journey Map - Patient Registration (Overview)

## Personas
| ID   | Role               | Description |
|------|--------------------|-------------|
| ST-01 | Clinical Staff    | Licensed clinicians (physicians, nurses, physician assistants) who review and update patient medical histories after intake. |
| ST-02 | Front Desk Staff | Administrative personnel who capture patient demographics, insurance information, and basic medical history during check‑in. |
| ST-03 | Compliance Officer | Auditor responsible for ensuring the intake system meets HIPAA technical safeguards and internal policies. |

## User Stories
| ID     | As a               | I want                                                                                                   | So that                                                                                                         |
|--------|--------------------|----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| US-001 | Front Desk Staff   | to enter patient demographics and insurance information into a structured web form that encrypts each field at rest and in transit | the protected health information (PHI) is secured according to HIPAA §164.312(a)(2)(iv) and the patient can be processed without manual encryption steps |
| US-002 | Clinical Staff | to review the submitted intake form and request a PDF summary that includes a staff watermark and an access timestamp | I can provide the patient with a verified record while maintaining auditability and confidentiality |
| US-003 | Compliance Officer | to query the audit log for any read or write operation on intake records and see the encryption key usage events | I can demonstrate compliance during internal or external audits and quickly identify any unauthorized access attempts |

## Acceptance Criteria
| AC ID   | Story ID | Given                                                                                                   | When                                                                                     | Then                                                                                                                                                                                                                                                                                     |
|---------|----------|--------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AC-001  | US-001 | The front‑desk user is authenticated via secure workstation credentials and the intake form is loaded. | The user fills all mandatory fields and clicks **Submit**. | The system encrypts each field at rest and in transit (FR‑001), stores the record, shows a confirmation screen with a unique transaction ID, and creates an immutable audit log entry (FR‑003). |
| AC-002  | US-001 | All mandatory fields are populated but one required field is left blank. | The user attempts to submit the form. | Real‑time validation highlights the missing field with an inline error message; submission is blocked until corrected (FR‑001). |
| AC-003  | US-002 | A clinician is logged in with multi‑factor authentication and has read/write access to a patient record under their care (FR‑001). | The clinician selects **Export PDF Summary**. | The generated PDF contains the clinician’s name watermark and a timestamp (FR‑003), is delivered within 500 ms (performance NFR‑001), and the export action is recorded in the audit log (KPI‑03). |
| AC-004  | US-002 | The clinician attempts to export a PDF for a patient not assigned to them. | The export request is issued. | The system blocks the export, returns an authorization error, and logs a warning entry in the audit log (RISK‑01). |
| AC-005  | US-003 | The compliance officer accesses the read‑only audit dashboard with appropriate role (FR‑003). | The officer runs a **Compliance Report** for a selected date range. | The report lists all read/write events, includes encryption key rotation timestamps, highlights any missing encryption metadata, completes within 200 ms (NFR‑001), and can be exported as a PDF with a “Compliance Review” watermark (FR‑003). |
| AC-006  | US‑003 | Encryption keys are rotated daily per policy. | A record is created after a key rotation event. | The system uses the latest active key for encryption, logs the key identifier in the audit entry, and the compliance officer can view the key usage in the report (RISK‑02). |

## Encryption Key Management
* Keys are stored in a hardened vault accessible only to privileged services.
* Automatic rotation occurs every 24 hours; rotation events are logged with `keyId` and timestamp.
* Access to keys requires dual‑approval workflow for any manual override (supporting RISK‑02).

### PER-01 Front Desk Operator
**Role:** First point of contact; creates new intake records on behalf of patients.
**Primary Goals:**
1. Quickly capture patient demographics, insurance details, and initial medical history.
2. Verify that all required fields are completed before submission.
3. Initiate PDF summary generation for a printed copy when requested by clinical staff.
**Access Rights:** Create and read permissions on `intake_record`; cannot modify records after submission.
**Pain Points:** Limited time per patient; must ensure data is encrypted at entry to satisfy HIPAA §164.312(a)(2)(iv).
**MVP Priority:** High – triggers encryption (FR-001) and audit logging (FR-002).

### PER-02 Clinician
**Role:** Reviews completed intake forms, adds clinical notes, and approves PDF export.
**Primary Goals:**
1. Access full patient record securely.
2. Verify encryption at rest for each field.
3. Export a watermarked PDF summary that includes an access timestamp for legal audit trails.
**Access Rights:** Read, update, and export permissions; can view audit‑log entries related to own actions.
**Pain Points:** Need assurance that exported PDF cannot be altered after export; requires clear watermark indicating staff identity.
**MVP Priority:** High – consumes PDF generation feature (FR-003) and validates audit logging (FR‑004).

### PER-04 Patient
**Role:** Subject of the data; interacts via web form presented by the Front Desk Operator or self‑service portal.
**Primary Goals:**
1. Provide accurate personal and medical information.
2. Receive confirmation that the submission was encrypted and stored securely.
**MVP Priority:** Medium – ensures data capture completeness and user confidence.

### US-001 (Front Desk Operator)
*As a* **Front Desk Operator** *I want to* **capture patient demographics and initial medical history in a secure form** *so that* **the data is encrypted at rest and an audit record is created immediately**.

#### Acceptance Criteria (AC‑001)
| # | Given | When | Then |
|---|-------|------|------|
| 1 | The operator is authenticated and has `create` permission on `intake_record`. | The operator fills all mandatory fields and clicks **Submit**. | The system encrypts each field with AES‑256‑GCM using per‑field keys derived from a master key in an HSM, stores the record, and creates an audit log entry (event_id, timestamp, actor_id = operator, action_type = `create`, outcome = `success`). |
| 2 | All mandatory fields are filled. | The operator attempts to submit the form. | The system validates completeness; if any required field is missing, it blocks submission and displays an inline error message.| |
| 3 The submission succeeds. |
 The operator views the confirmation screen. |
 | The screen shows a message “Your information has been securely recorded.” and displays a reference ID for the audit log entry.|

## Functional Requirements Traceability

| User Story | Functional Requirement(s) |
|------------|-----------------------------|
| US‑001    | FR‑001 (Secure demographic capture), FR‑002 (Encryption at rest), FR‑003 (Audit logging) |
| US‑002    | FR‑003 (PDF generation), FR‑004 (Watermark & timestamp), FR‑005 (PDF integrity verification) |
| US‑003   | FR‑001 (Secure capture), FR‑006 (User confirmation) |

## API Specification (High‑Level)

| Method | Endpoint                     | Auth Scope               | Description                                                   |
|--------|------------------------------|--------------------------|---------------------------------------------------------------|
| POST   | `/api/v1/intake`            | `operator:create`        | Accepts JSON payload of patient demographics; validates required fields; returns `{record_id, audit_event_id}` |
| GET    | `/api/v1/intake/{id}`       | `clinician:read`         | Retrieves encrypted intake record; server decrypts fields before response |
| POST   | `/api/v1/intake/{id}/export-pdf` | `clinician:export`        | Triggers PDF generation; returns download URL; enforces ≤ 5 s SLA |
| GET    | `/api/v1/audit/{event_id}`  | `compliance_officer:read`   | Returns audit log entry details |

## Access Control Matrix

| Role               | Create Intake Record | Read Intake Record   | Update Intake Record   | Export PDF |
|--------------------|----------------------|----------------------|-----------------------|------------|
| Front Desk Operator (`front_desk`)   																																	 	✅ 	✅(own records) 	❌ 	❌ |
|	Clinician (`clinician`) 	❌ 	✅ 	✅ 	✅ |
|	Compliance Officer (`compliance_officer`) 	❌ 	✅(all) 	❌ 	❌ |

## MVP Scope Table
| Process | Actor | Priority | Description | Linked Requirements |
|--------|-------|----------|-------------|--------------------|
| PER-01 | Front Desk Operator | High | Capture demographics & insurance; trigger encryption; log creation event | FR-001, FR-002 |
| PER-02 | Clinician | High | Review record; generate watermarked PDF; log export event | FR-003 |
| PER-03 | Compliance Officer | Medium | Audit log review; verify encryption key management | FR-004, NFR-003 |
| PER-04 | Patient | Low | Provide data via form; receive submission confirmation | FR-001 |

## Persona Definitions for Patient Intake System (Overview)

| Persona ID | Role |
|------------|------|
| PER‑01 | Front Desk Operator |
| PER‑02 | Clinician |
| PER‑03 | Compliance Officer |
| PER‑04 | Patient |

### Detailed Persona Descriptions

1. **Front Desk Operator (PER‑01)**
   - Authenticates via multi‑factor login; session token scoped to `front_desk` role.
   - Validates patient identity, assists with form completion, and ensures insurance data is captured accurately.
   - Permissions: Read/Update on `intake_submissions` where `status = 'draft'`; Create on `audit_log` entries.
   - Actions: `CREATE_SUBMISSION`, `UPDATE_SUBMISSION`, `ACCESS_LOG`.
   - Audit: Each edit creates an `UPDATE_SUBMISSION` audit entry containing before/after field hashes.

2. **Clinician (PER‑02)**
   - Accesses completed submissions after they are marked finalized by the front desk.
   - Generates a PDF intake summary using wkhtmltopdf; PDF is watermarked with clinician name and timestamp (`PDF_WATERMARK_APPLIED`).
   - Permissions: Read all finalized `intake_submissions`; Create on `pdf_exports`.
   - Actions: `READ_SUBMISSION`, `PDF_EXPORT`, `PDF_WATERMARK_APPLIED`.
   - Audit: Export action logs an entry `PDF_EXPORT` with user ID, patient ID, and timestamp.

3. **Compliance Officer (PER‑03)**
   - Manages RBAC policies stored in PostgreSQL role tables; changes are logged as `ROLE_ASSIGNMENT`.
   - Reviews audit logs daily to ensure every read/write operation is recorded per FR‑002 and NFR‑003.
   - Configures encryption key rotation schedule (e.g., every 90 days) and validates field‑level encryption remains active.
   - Permissions: Full CRUD on user/role tables; Read on all audit logs; Create on policy changes.
   - Actions: `ROLE_ASSIGNMENT`, `POLICY_UPDATE`, `AUDIT_LOG_VIEW`.

4. **Patient (PER‑04)**
   - Interacts through a secure HTTPS web portal.
   - All form fields are encrypted client‑side before transmission; encryption keys managed per NIST SP 800‑53 AC‑2.
   - After submission receives a confirmation page containing a unique submission ID and timestamp (recorded in audit log as `FORM_SUBMIT`).
   - Permissions: Read‑only on static informational pages; Create on `intake_submissions` table (field‑level encryption applied).
   - Actions: `CREATE_SUBMISSION`, `FORM_VIEW`.

### US‑FR001‑PER04 – Secure Patient Data Submission
**As a** Patient (PER‑04) **I want** to submit my demographic and insurance information securely **so that** my data is protected in transit and at rest.

**Acceptance Criteria**
1. **Given** I am on the secure HTTPS intake form,
2. **When** I complete all required fields and click **Submit**,
3. **Then** the data is encrypted client‑side,
4. **And** transmitted over TLS 1.2+,
5. **And** stored encrypted in `intake_submissions`,
6. **And** an audit log entry `FORM_SUBMIT` is created containing a unique submission ID, timestamp, and hash of the payload,
7. **And** I see a confirmation screen displaying the submission ID.

### US‑FR002‑PER01 – Front Desk Capture & Encryption Trigger
**As a** Front Desk Operator (PER‑01) **I want** to capture patient demographics & insurance and trigger encryption **so that** the data is safely persisted.

**Acceptance Criteria**
1. **Given** a patient has started a draft submission,
2. **When** I validate identity and complete missing fields,
3. **Then** the system encrypts the data client‑side before saving,
4. **And** creates an audit entry `FORM_SUBMIT_DRAFT` with my user ID,
5. **And** marks the record status as `draft` until finalized.

### US‑FR003‑PER02 – Clinician PDF Generation
**As a** Clinician (PER‑02) **I want** to generate a watermarked PDF summary of a completed intake record **so that** I can use it for treatment planning while maintaining auditability.

**Acceptance Criteria**
1. **Given** a finalized intake record exists,
2. **When** I request a PDF export,
3. **Then** the system generates the PDF within 2 seconds for records ≤ 5 MB,
4. **And** applies a watermark containing my name and export timestamp (`PDF_WATERMARK_APPLIED`),
5. **And** stores the PDF in `pdf_exports` with metadata linking back to the patient record,
6. **And** creates an audit log entry `PDF_EXPORT` capturing user ID, patient ID, timestamp, and file hash.

### US‑FR004‑PER03 – Audit Log Review & Key Management Verification
**As a** Compliance Officer (PER‑03) **I want** to review audit logs and verify encryption key rotation handling **so that** HIPAA compliance is continuously demonstrated.

**Acceptance Criteria**
1. **Given** the system enforces a 90‑day encryption key rotation schedule,
2. **When** a rotation occurs,
3. **Then** new submissions are encrypted with the new key version,
4. **And** existing records retain decryption capability via stored key version metadata,
5. **And** an audit entry `KEY_ROTATION` is recorded with old/new key identifiers and timestamps,
6. **And** the compliance officer can query audit logs to confirm that every create/read/update/export action has a corresponding entry (`>= 99%` coverage verified by automated test suite).

## Testability Details

* **Unit Tests** – Cover form field validation logic, client‑side encryption functions, RBAC permission checks.
* **Integration Tests** – End‑to‑end submission flow verifies encrypted storage, audit log creation, and confirmation screen display.
* **Performance Tests** – Simulate 100 concurrent submissions measuring API response time; benchmark PDF generation latency.
* **Security Tests** – Verify TLS version enforcement, attempt man‑in‑the‑middle attacks on transmission paths, validate that no plaintext data is written to logs or storage.
* **Compliance Tests** – Automated scripts scan audit logs for missing entries and validate key rotation metadata consistency.

## Reviewer Feedback Resolution Summary
* Fixed duplicate persona IDs by aligning detailed descriptions with MVP scope table IDs.
* Added complete Given/When/Then acceptance criteria for each user story.
* Introduced performance acceptance criteria for response time and PDF generation.
* Added explicit acceptance criteria for encryption key rotation handling and audit log completeness.
* Expanded testability section with concrete unit, integration, performance, security, and compliance tests.
* Clarified linkage between user stories and requirement IDs throughout the document.
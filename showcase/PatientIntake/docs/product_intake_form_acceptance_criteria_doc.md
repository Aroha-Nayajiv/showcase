# Intake Form Acceptance Criteria Document

## Personas for Patient Intake System

| Persona ID | Role | Description | Permissions | Security Controls |
|------------|------|-------------|------------|-------------------|
| ST-001 | Front Desk Clerk | Captures patient demographics, insurance information, and initial medical history via the web form. Verifies completeness before submission. | Create (submit) records; view own submissions; cannot edit after submission. | Immutable audit entry on CREATE with user ID, timestamp, operation type. Session token expires after 30 minutes of inactivity. Client‑side field encryption using AES‑256‑GCM over TLS 1.3. |
| ST-002 | Clinician | Reviews submitted intake forms; adds clinical observations; approves or rejects records for further processing. | Read all submissions; update clinical notes field; cannot delete records. | READ operations logged; UPDATE operations logged with before‑and‑after hash of encrypted fields. Row‑level security enforces assignment to records. |
| ST-003 | Compliance Officer | Ensures HIPAA technical safeguards are met; monitors audit logs; generates compliance reports. | Read all audit logs; export reports; no write access to patient data. | Queries logged (AUDIT_QUERY) with filters (operation type, role, date). Export generates PDF signed with server‑side private key and watermarked "Confidential – Compliance Review". |

## User Stories

**US-001 – Front Desk Clerk: Capture Patient Demographics**
- **Given** the clerk is authenticated with role ST-001 and has a valid session token.
- **When** the clerk fills out the structured web form containing required fields (name, DOB, insurance policy number, etc.) and clicks **Submit**.
- **Then** the system must:
  1. Validate that all mandatory fields are present; if any are missing, display an inline error without persisting partial data and log a `VALIDATION_FAILURE` event (traceable to FR‑001).
  2. Encrypt each field client‑side using AES‑256‑GCM and transmit over TLS 1.3.
  3. Persist the encrypted record and create an immutable audit log entry containing user ID, timestamp, and operation type `CREATE` (traceable to NFR‑003).
  4. Return a success confirmation to the clerk.

**US-002 – Clinician: Review and Augment Intake Form**
- **Given** the clinician is authenticated with role ST-002 and is assigned to a specific patient record.
- **When** the clinician opens a pending intake form and adds clinical observations in the free‑text field.
- **Then** the system must:
  1. Log the READ operation of the form (traceable to NFR‑003).
  2. Allow the clinician to edit only the `clinical_observations` field; other fields remain read‑only.
  3. Encrypt the new observation client‑side using AES‑256‑GCM before storage.
  4. Store the updated record and log an `UPDATE` event that includes before‑and‑after hashes of the encrypted field (traceable to FR‑004).
  5. If the clinician attempts to edit a record they are not assigned to, return HTTP 403 Forbidden, display a user‑friendly error message, and log an `ACCESS_DENIED` event (traceable to RISK-001).

**US-003 – Compliance Officer: Generate Audit‑Ready PDF Export**
- **Given** the compliance officer is authenticated with role ST-003.
- **When** the officer selects a patient record and requests a PDF intake summary export.
- **Then** the system must:
  1. Verify the officer’s role before generating the PDF.
  2. Produce a PDF that includes a watermark "Confidential – Compliance Review" and a timestamp of export.
  3. Sign the PDF with a server‑side private key to ensure integrity.
  4. Create an immutable audit log entry of type `EXPORT` that records user ID, timestamp, patient record ID, and hash of the generated PDF (traceable to NFR‑003 and KPI-004).
  5. If the officer lacks proper role, block the action, return an error message, and log an `UNAUTHORIZED_EXPORT` event (traceable to RISK-002).

### Cross‑Persona Security Requirements
- All audit events (`CREATE`, `READ`, `UPDATE`, `EXPORT`, `VALIDATION_FAILURE`, `ACCESS_DENIED`, `UNAUTHORIZED_EXPORT`) must be immutable and stored in an append‑only log meeting HIPAA technical safeguard §164.312(a)(2)(i).
- Encryption keys are derived per session and never persisted on client devices.
- All network communication uses TLS 1.3 exclusively.

### Non‑Functional Requirements Referenced
- **NFR‑001**: System response time <200 ms for form submissions.
- **NFR‑003**: Comprehensive audit logging for every operation.
- **NFR‑004**: Audit logs must be tamper‑evident and retain data for at least 7 years.

### KPI Alignment
- **KPI-001**: <200 ms response time compliance for form submissions.
- **KPI-004**: Successful PDF export with correct watermark and signature for every request.

---
*All IDs referenced above correspond to entries in the project asset registry.*

### US-001: Front Desk Clerk submits patient intake
**Given** the clerk is authenticated with role `front_desk` over a TLS‑1.2+ session and the intake form is displayed with all required fields (first name, last name, DOB, insurance policy number, primary diagnosis).
**When** the clerk enters valid data and clicks **Submit**.
**Then** each field is encrypted client‑side using AES‑256‑GCM (OpenSSL 1.1.1) and transmitted over the TLS channel; the server stores encrypted fields in PostgreSQL with column‑level encryption and applies row‑level security; a success toast with a unique Record ID (e.g., REC‑000123) is shown.
*Acceptance Criteria*: AC‑001 (success path) and AC‑002 (duplicate submission handling).

### US-002: Clinician views intake summary
**Given** a clinician is authenticated with role `clinician` and navigates to a patient record using a valid Record ID.
**When** the clinician selects **View Intake Summary**.
**Then** the system decrypts the stored fields server‑side using the clinician’s key and presents a read‑only view; an audit log entry records the view with timestamp.
*Acceptance Criteria*: AC‑003 (view success) and AC‑004 (request correction flow).

### US-003: Compliance Officer exports intake record as PDF
**Given** a compliance officer is authenticated with role `compliance_officer`.
**When** the officer selects **Export PDF** for a specific Record ID.
**Then** the system generates a PDF via wkhtmltopdf v0.12.6 containing:
1. Patient name redacted to initials.
2. Semi‑transparent watermark "CONFIDENTIAL – FOR INTERNAL USE ONLY".
3. ISO‑8601 timestamp footer.
4. Digital signature metadata with exporter user ID.
The file is delivered over HTTPS and an immutable audit log entry records the SHA‑256 hash of the file.
*Acceptance Criteria*: AC‑005 (PDF generation details) and AC‑006 (re‑export handling).

## Acceptance Criteria Table

| ID      | User Story | Given                                                                                                   | When                                            | Then                                                                                                                                                                                                                                                                                     |
|---------|------------|----------------------------------------------------------------------------------------------------------|--------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AC-001  | US-001     | Front Desk Clerk authenticated … TLS‑1.2+ session … required fields present                           | Clerk enters valid data and clicks Submit        | Field‑level encryption applied client‑side using AES‑256‑GCM; server stores each encrypted field in PostgreSQL column‑level encryption with RLS; success toast with unique Record ID returned                                                                                                   |
| AC-002  | US-001     | The same submission from AC‑001 has been persisted                                                    | Clerk attempts duplicate submission within 5 seconds | System detects duplicate Record ID, returns warning "Duplicate submission detected", creates no new record; audit log entry records duplicate attempt; network latency >10 s triggers retry dialog                                                                      |
| AC-003  | US-002     | Clinician authenticated … navigates to patient record page using Record ID                           | Clinician clicks View Intake Summary             | UI displays read‑only view of all encrypted fields decrypted server‑side using clinician’s key; no edit controls; audit log entry records view operation with timestamp                                                                                                                   |
| AC-004  | US-002     | Clinician notices incorrect insurance number in displayed summary                                   | Clinician clicks Request Correction and adds comment | System creates correction request ticket (CR‑00045) linked to Record ID; audit log entry records request; original encrypted data remains unchanged until approved by Front Desk Clerk; comment >500 characters is truncated with warning               |
| AC-005  | US-003     | Compliance Officer selects Export PDF for given Record ID                                            | Officer clicks Export                            | Generated PDF includes redacted name initials, watermark, timestamp footer, digital signature metadata; delivered over HTTPS; immutable audit log entry records file hash (SHA‑256); if wkhtmltopdf fails, error "PDF generation failed – contact IT" shown, retry allowed up to three times |
| AC-006  | US-003     | After successful export, officer attempts re‑export within 30 seconds                                 | Officer clicks Export again                      | System returns "Export already performed – latest PDF available for download" without creating new audit entry; logs "re-export attempt" with status skipped; if officer lacks permission, returns "Access denied" error and logs denied attempt                |

## Design Needs for Downstream Teams

* **Field‑level encryption specification** – algorithm AES‑256‑GCM, key rotation every 90 days, keys stored in HSM (e.g., HashiCorp Vault). Reference HIPAA §164.312(a)(2)(iv).
* **Audit log schema** – immutable append‑only table `audit_log` (log_id PK, record_id FK, action, actor_role, timestamp, hash). Supports tamper evidence per NIST SP 800‑53 AU‑6.
* **PDF generation contract** – input HTML template fields, required watermark text, timestamp format ISO‑8601, digital signature metadata fields (`exporter_user_id`, `export_timestamp`).
* **Error handling conventions** – JSON payload `{ "error_code": "...", "message": "...", "retryable": true/false }` for front‑end consumption.
* **Performance thresholds** – form submission latency ≤200 ms (KPI-001); PDF generation ≤2 seconds for average record size ≤5 KB (KPI-002).

## Traceability Matrix

| Artifact Element                     | Requirement ID |
|--------------------------------------|----------------|
| Front Desk Clerk authentication    | FR-001 |
| Intake form fields presence           | FR-002 |
| TLS session version enforcement      | NFR-001 |
| Field‑level encryption algorithm    | NFR-004 |
| Duplicate submission handling       |	FR-003 |
| Clinician view permissions          |	FR-004 |
| Correction request workflow         |	FR-005 |
| PDF export watermark & metadata      |	FR-006 |
| Re‑export handling logic            |	FR-007 |
| Audit log immutability               |	NFR-003 |
| Performance latency ≤200 ms         |	KPI-001 |
|	PDF generation ≤2 seconds            |	KPI-002 |

## Risks Addressed

* **RISK-001** – Unauthorized data exposure mitigated by TLS 1.2+, encryption at rest and in transit.
* **RISK-002** – Open‑source component vulnerabilities addressed by pinning wkhtmltopdf version 0.12.6 and regular vulnerability scanning.
* **RISK-003** – Deployment misconfiguration mitigated by containerized deployment guidelines (Docker Compose – FR-009).
* **RISK-004** – Compliance audit gaps covered by immutable audit log and detailed export metadata.
* **RISK-005** – On‑prem deployment constraints acknowledged; capacity monitoring recommended.
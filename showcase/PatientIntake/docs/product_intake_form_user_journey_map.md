# Intake Form User Journey Map
                
## 1. Personas

| ID | Persona | Goal | Primary Tasks | Security / Compliance |
|----|--------|------|---------------|----------------------|
| PER-01 | Front Desk Clerk (ST-01) | Capture accurate patient demographics and insurance data quickly. | Initiate intake form, verify required fields, submit encrypted data, trigger audit log entry. | Must ensure data is encrypted at rest and in transit; audit log must record creation event (FR-001, NFR-003). |
| PER-02 | Clinician (ST-02) | Review medical history and verify completeness before consultation. | Access submitted records, view encrypted fields after decryption via authorized session, add clinical notes if permitted. | Access controlled by role‑based permissions; every read operation logged (FR-002, NFR-003). |
| PER-03 | Compliance Officer (ST-03) | Verify that intake process meets HIPAA technical safeguards and audit requirements. | Audit logs, validate encryption key management, ensure watermark and timestamp on PDF exports. | Directly tied to compliance checks (NFR‑001, NFR‑003). |
| PER-04 | Patient (ST-04) | Provide personal and medical information securely and receive confirmation of receipt. Fill out web form, consent to data handling, receive PDF summary link after approval. |
 | Consent handling and secure transmission are required by 45 CFR 164.312(a)(2)(iv). |

## 2. Edge Cases & Failure Scenarios

1. **Network Interruption During Submit** – If the HTTPS connection drops after encryption but before DB commit, the client receives a timeout; the UI prompts "Submission incomplete – retry?" and no partial data is persisted because the transaction is rolled back.
2. **Role Escalation Attempt** – A front‑desk clerk tries to access a clinician‑only record; the RBAC check denies access and logs an unauthorized access event with severity "warning".
3. **Corrupted Encryption Key** – If decryption fails due to key mismatch, the system returns a generic "Unable to display record" message to the clinician while alerting the compliance officer for key rotation.
4. **PDF Export Timestamp Tampering** – The watermark generation process includes a server‑side timestamp; any client‑side modification is ignored because the timestamp is signed with HMAC using the same key as field encryption.
5. **Audit Log Overflow** – When the audit log table reaches 10 M rows, an automated archival job rotates older entries to an immutable archive and logs a `LOG_ROTATION_PENDING` warning.
6. **PDF Tampering Detection** – The generated PDF includes a cryptographic hash of the watermark and timestamp; any alteration causes verification failure and the system rejects the PDF download, logging a `PDF_TAMPER_DETECTED` event.

## 3. Design Needs for Downstream Teams

* **Encryption Specification** – Define algorithm (AES‑256‑GCM), key rotation schedule, and storage of keys in an on‑prem HSM.
* **Audit Log Schema** – Fields: `event_type`, `user_id`, `role`, `patient_id`, `timestamp`, `outcome`, `source_ip`. Include overflow handling and archival policy.
* **PDF Generation Service Contract** – Input JSON schema for patient data, required watermark format, timestamp format (ISO‑8601), error codes. Ensure compliance with FR‑010 (secure PDF export) and include tamper‑evidence hash.
* **Session Management** – Token lifetime (15 min idle), refresh flow, revocation list for compromised tokens.
* **Email Notification Template** – Content must include HIPAA disclaimer, secure link expiration policy.

## 4. Prioritized User Stories

| ID | Role | Narrative | Value Statement | Priority |
|----|------|-----------|-----------------|----------|
| US-001 | Patient | enter my demographic, insurance, and medical history into a structured web form that encrypts each field at rest and in transit | my protected health information (PHI) is stored securely and complies with HIPAA §164.312(a)(2)(iv) | High |
| US-002 | Front Desk Clerk | submit a completed intake form on behalf of the patient and receive immediate confirmation that the record is stored with role‑based write permission | the clinic can begin clinical workflow without delay while ensuring only authorized staff can create records (FR‑001) | High |
| US-003 | Clinician | retrieve a patient's intake record and view a PDF summary that includes a staff watermark and an access timestamp | I can review accurate clinical information while audit logs capture the read operation for compliance (FR‑003, FR‑010, KPI-003) | High |
| US-004 | Admin | generate an immutable audit log entry for every create, read, update, or delete operation on intake records and export the log for quarterly compliance review | auditors can verify that all PHI handling complies with NFR‑003 and HIPAA audit requirements | Medium |
| US-005 | Front Desk Clerk | receive validation errors when required fields are missing or when encryption of a field fails before submission | data quality is guaranteed and no partially encrypted records enter the database (NFR‑001) | Medium |

## 5. Acceptance Criteria

### AC-003 – US-003
**Given** a clinician authenticated with role = Clinician has READ permission for the target patient record  
**When** the clinician clicks **View PDF Summary** for patient XYZ  
**Then** a PDF is generated using wkhtmltopdf,
 includes a semi‑transparent watermark “Clinician – {ClinicianName}”,
 an ISO‑8601 timestamp footer “Exported on {timestamp}”,
 starts download,
and an audit log entry (`operation=READ`) records clinician ID and timestamp.

*Negative flows*:  
- PDF generation failure shows “Unable to generate summary – contact IT” and logs `operation=ERROR` without exposing PHI.
 - Unauthorized access returns HTTP 403 and logs an unauthorized attempt.

## 6. Design Needs (What Design Must Specify)

* **Field‑Level Encryption Specification** – algorithm (AES‑256‑GCM), per‑field key derivation from KMS,
once generation strategy,
and client‑side library version.
* **Audit Log Schema & Retention** – immutable append‑only table fields (`log_id`, `operation_type`, `actor_id`, `timestamp_utc`, `record_id`, `hash_signature`), retention period of 7 years per HIPAA,
and overflow archival process as described in AC‑006.
* **PDF Generation Requirements** – wkhtmltopdf ≥ 0.12.6,
w watermark opacity 15 %, bottom‑right placement,
isO‐8601 UTC timestamp,
and embedded HMAC for tamper evidence (supports FR‑010).
* **Role‑Based Access Matrix** – CRUD permissions per role (Admin: all; Clinician: READ + EXPORT_PDF; FrontDesk: CREATE + READ limited to own submissions; Patient: VIEW own submission via secure portal).
* **Error Handling UX Guidelines** – user‑friendly messages for encryption failures,\validation errors,\permission denials;
n o PHI leakage in error texts.
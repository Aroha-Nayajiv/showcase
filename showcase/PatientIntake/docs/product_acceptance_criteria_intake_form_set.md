# Intake Form Acceptance Criteria Set

## Personas for PDF Summary Generation Feature

The following personas capture all human actors who will interact with the patient intake web form and the subsequent PDF intake summary export functionality. They are defined to guide downstream design of UI flows, security controls, and audit requirements.

### Persona Table
| ID   | Role               | Description| Goals  | Security Requirements | Priority |
|------|--------------------|-------------|-------------------|------------------------|----------|
| PER-01 | Patient            | Individual seeking care who completes the intake form on a clinic‑provided device or personal computer.      | Provide accurate demographic, insurance, and medical history data; receive confirmation that data is securely stored.  | Must transmit data over TLS 1.3; no local storage of PHI beyond session; consent acknowledgment required. | High |
| PER-02 | Front Desk Clerk   | Clinic staff who assists patients in completing the form and later retrieves PDF summaries for authorized staff. | Ensure form is fully completed; trigger PDF generation; verify patient identity before export.| Access limited to "front‑desk" role; audit log entry created for each view/export; cannot view PHI outside authorized sessions. | High |
| PER-03 | Clinician          | Healthcare provider reviewing patient intake information and PDF summaries to prepare for consultation.    | Quickly access complete, tamper‑evident PDF; verify authenticity via watermark and timestamp.| Must have "clinician" role with read‑only access to PDFs; export action logged; PDF watermarks include clinician ID and export timestamp. | Medium |
| PER-04 | Compliance Officer | Oversees HIPAA compliance, audits access logs, and validates that PDF generation meets regulatory requirements. | Review audit trails; confirm encryption at rest/in‑transit; ensure watermarking meets policy.| Read‑only access to audit logs and PDF metadata; can request re‑generation of PDFs for compliance checks; no ability to modify patient data.  | Medium |

## Interaction Flow Overview
1. **Form Completion (Patient)** – The patient accesses the secure HTTPS web form, enters required fields, and explicitly consents to data processing. The system encrypts each field at rest using PostgreSQL column‑level encryption (AES‑256) and in transit via TLS 1.3.
2. **Assisted Review (Front Desk Clerk)** – After submission, the clerk validates required fields are populated, may correct minor errors under patient supervision, and initiates PDF generation.
3. **PDF Generation (System)** – The backend compiles the submitted data into a PDF/A‑2b document, embeds a dynamic watermark containing the requesting user's role, user ID, and UTC timestamp, then stores the file encrypted at rest.
4. **Secure Export (Clinician)** – An authorized clinician requests the PDF via the web portal; the system verifies role‑based access control (RBAC), streams the encrypted file over TLS 1.3, and logs the export event with user ID, timestamp, and checksum verification.
5. **Compliance Review (Compliance Officer)** – Periodically, the compliance officer extracts audit logs and PDF metadata to verify that every export includes a tamper‑evident watermark and that no unauthorized role accessed PHI.

## Security & Audit Requirements Tied to Personas
- **Encryption at Rest** – All PHI fields are encrypted using column‑level AES‑256 keys managed by PostgreSQL pgcrypto. Only roles `front_desk`, `clinician`, and `compliance` have decryption privileges as defined in role‑based policies (**FR‑001**, **FR‑002**, **FR‑003**).
- **Encryption in Transit** – All client‑server communication must use TLS 1.3 with forward secrecy ciphers (e.g., TLS_AES_256_GCM_SHA384) (**FR‑002**).
- **Audit Logging** – Every read (`SELECT`) or write (`INSERT/UPDATE/DELETE`) operation on PHI tables creates an immutable log entry (`audit_log` table) containing `event_id`, `user_id`, `role`, `action`, `timestamp`, and a cryptographic hash chain per NIST SP 800‑53 AU‑6 (**FR‑001**, **FR‑004**).
- **Watermarking** – PDFs contain a visible watermark: `Exported by <ROLE> (<USER_ID>) on <UTC_TIMESTAMP>`. This satisfies **FR‑004** requirement for traceable export.
- **Access Controls** – RBAC definitions enforce least‑privilege: patient role has no direct system access; front_desk can create/read PDFs but cannot modify underlying PHI after submission; clinician has read‑only view rights; compliance has audit‑only rights (**FR‑001**, **FR‑003**).

## Design Needs for Downstream Phases
- **Persona Metadata Schema** – A JSON schema describing each persona's attributes (role name, permission set) must be provided to the Design team to generate UI component visibility rules.
- **Watermark Template Specification** – Exact string format (`Exported by {role} ({user_id}) on {UTC_timestamp}`) and font requirements (Helvetica Bold 10pt, gray opacity 30%) must be captured in the Design contract.
- **Audit Log Format** – The structure of log entries (`event_id`, `user_id`, `role`, `action`, `timestamp`, `hash`) must be documented for future security review tooling.

## User Stories
| ID    | As a               | I want to| So that|
|-------|--------------------|-----------|----------|
| US-001 | Patient            | enter my demographic, insurance, and medical history into a secure web form               | my information is captured accurately and stored in compliance with HIPAA                |
| US-002 | Front Desk Clerk  | submit a completed intake form on behalf of a patient  | the system records the data and creates an immutable audit trail                        |
| US-003 | Clinician          | generate a PDF summary of a patient's intake data that includes a visible watermark and an export timestamp | I can review the patient's information securely and prove when the document was exported   |
| US-004 | Compliance Officer| view audit logs of all PDF generation events, including user, timestamp, and success/failure status | I can verify that access controls and logging meet regulatory requirements            |

## Acceptance Criteria

### AC-004 – US-003 (PDF Generation & Watermark)
**Given** a clinician with role `clinician` is authenticated and has VIEW permission on patient records,
**When** the clinician clicks **Generate PDF** for Patient Y’s intake record,
**Then**:
1. The system retrieves the encrypted record,
2. Decrypts it using role‑based keys,
3. Generates a PDF/A‑2b document embedding a watermark formatted as `Exported by clinician (CLN123) on 2026-05-08T14:32:10Z`,
4. Stores the PDF encrypted at rest,
5. Streams the PDF over TLS 1.3 to the clinician’s browser,
6. Writes an audit log entry (`EXPORT`) containing user ID, timestamp, checksum, and watermark metadata.
*Failure handling*: If decryption fails or watermark generation encounters an error, the system aborts streaming, logs an `EXPORT_FAILURE` event, and notifies the clinician.

## Traceability Matrix
| Artifact ID | Linked Requirement(s) |
|------------|----------------------|
| US-001     | FR-001 (Encryption at Rest), FR-002 (TLS 1.3), FR-003 (Access Controls) |
| US-002     | FR-001 (Audit Logging), FR-004 (Watermark Requirement) |
| US-003     | FR-004 (Watermark), FR-001 (Encryption), FR-002 (TLS) |
| US-004     | FR-001 (Audit Logging), FR-004 (Watermark Traceability) |
| AC-001    | FR-001, FR-002 |
| AC-002    | FR-002 |
| AC-003    | FR-001, FR-004 |
| AC-004    | FR-001, FR-002, FR-004 |
| AC-005    | FR-001 |

---
*All content aligns with SaaS best practices for multi‑tenant isolation, horizontal scalability, high availability, and SOC 2 compliance.*

### 1. Personas (Relevant Actors)
- **PER-001** – *Patient*: Provides personal health information via the web intake form.
- **PER-002** – *Front Desk Clerk*: Initiates the intake process, can generate and view patient PDFs.
- **PER-003** – *Clinician*: Reviews patient PDFs and updates clinical records.
- **PER-004** – *Compliance Officer*: Audits PDF generation events and validates watermark integrity.

#### US-002 – PDF Generation (Reference: FR-004)
| ID | Given | When | Then |
|----|-------|------|------|
| AC-003 | A completed intake record exists for **Patient #12345** and the Front Desk Clerk (**role=front_desk**) is authenticated. | The clerk selects **Generate PDF** for that patient. | The system: 1. Decrypts the record in memory using the per‑patient key. 2. Renders a PDF with **WeasyPrint** (v53+). 3. Overlays a semi‑transparent watermark `"CONFIDENTIAL – PatientIntake"` using design token `--watermark-color: #FF0000; opacity: 0.15`. 4. Appends an ISO‑8601 timestamp footer. 5. Stores the PDF encrypted at rest (AES‑256‑GCM) and creates an immutable audit entry `PDF_GENERATED` with outcome *success*. 6. Streams the file to the browser with `Content‑Disposition: attachment`. |
| AC-004 | The clerk’s session has expired **or** the clerk lacks the `front_desk` role. | The clerk attempts to generate the PDF. | The system returns HTTP 403 Forbidden with message *"Insufficient permissions"*; no PDF is created; an audit entry `ACCESS_DENIED` is recorded (no `PDF_GENERATED`). |
| AC-005 | Decryption fails because the per‑patient key does not match the current rotation schedule. | The clerk attempts PDF generation. | The system returns *"Unable to generate PDF – security error"*; logs a failure event `PDF_DECRYPT_FAIL`. |
| AC-006 | WeasyPrint throws an exception (e.g., malformed HTML). | The clerk attempts PDF generation. | The system falls back to a plain‑text summary, logs warning `PDF_FALLBACK`, and creates audit entry `PDF_GENERATED` with outcome *partial*. |

### 2. Edge Cases & Failure Scenarios (Minimum Two per Core Story)

#### 2.1 Network Interruption (US‑001)
- **Scenario A**: TLS connection drops after client encryption but before server receipt.
  - Client automatically retries up to three times using an idempotency key.
  - Duplicate submissions are detected via the idempotency key and rejected with message *"Submission already received"*; audit entry `DUPLICATE_SUBMISSION` recorded.
- **Scenario B**: Server receives encrypted payload but loses connection before acknowledgment.
  - Client shows *"Submission may not have been saved – please check your history."*; no new record is created; audit entry `SUBMISSION_TIMEOUT` logged.

#### 2.2 Disk Full During PDF Storage (US‑002)
- **Scenario A**: Storage quota exceeded when attempting to write encrypted PDF.
  - System returns error page *"Unable to generate PDF – storage quota exceeded"*; logs `PDF_STORAGE_FAIL` with disk usage metrics.
- **Scenario B**: Temporary I/O error on write.
  - System retries once; if still failing, returns same error page and creates audit entry `PDF_WRITE_ERROR`.

#### 2.3 Corrupted PDF Decryption (US‑002)
- **Scenario A**: Decryption yields malformed PDF stream.
  - Clinician sees *"Document corrupted – contact IT"*; audit entry `PDF_DECRYPT_FAIL` created with hash of corrupted payload.
- **Scenario B**: Key rotation mismatch leads to partial decryption.
  - System falls back to plain‑text summary as defined in AC‑006 and logs warning `KEY_MISMATCH_FALLBACK`.

#### 2.4 Log Tampering Attempt (US‑004)
- **Scenario A**: An update attempt on an existing immutable audit row.
  - PostgreSQL trigger aborts transaction, writes immutable entry `INTEGRITY_VIOLATION` referencing original hash chain.
- **Scenario B**: Unauthorized read of audit logs from another tenant.
  - Row‑Level Security denies query; audit entry `UNAUTHORIZED_LOG_ACCESS` recorded.

### 3. Design Needs (What Design Must Specify)
1. **Encryption Library & Key Management**
   - Use **libsodium** for field‑level AES‑256‑GCM encryption.
   - Per‑patient keys derived from a master key rotated quarterly (see FR‑002). Key rotation schedule must be documented in the security policy.
2. **PDF Generation Stack**
   - Library: **WeasyPrint** version ≥ 53 supporting PDF/A‑2b compliance.
   - Watermark token defined in design token `--watermark-color: #FF0000; opacity: 0.15`.
   - Footer timestamp format: ISO‑8601 UTC (`YYYY-MM-DDTHH:mm:ssZ`).
3. **Audit Log Schema**
   - Table `audit_log` columns: `event_id PK`, `actor_role`, `actor_id`, `patient_id`, `action`, `timestamp`, `outcome`, `ip_address`, `hash_chain`.
   - Append‑only storage enforced via PostgreSQL extension **pg_audit** and trigger that prevents UPDATE/DELETE on existing rows.
4. **Access Control Model**
   - Roles stored in table `app_roles` (`role_name`, `description`).
   - Row‑Level Security policies:
     sql
     CREATE POLICY front_desk_pdf_policy ON pdfs
       USING (current_setting('app.current_role') = 'front_desk' AND patient_id = current_setting('app.current_patient'));
     
   - Session tokens are JWTs signed with RSA‑2048; expiration 30 min; revocation list checked on each request.
5. **Error Messaging Conventions**
   - All user‑facing messages must be concise, avoid stack traces, and never expose PHI or internal identifiers.
   - Logging level mapping:
     - INFO – successful operations
     - WARN – recoverable issues (fallback to plain text)
     - ERROR – security violations or storage failures

### 4. MVP Scope Summary
- Implement PDF generation workflow for Front Desk Clerks (US‑002) including watermark and timestamp.
- Enforce RBAC for front_desk role and session expiration handling (US‑003).
- Provide immutable audit logging with CSV export for Compliance Officers (US‑004).
- Cover edge cases listed in Section 3.

### 5. Test Specification Overview
1. **Unit Tests**
   - Verify encryption/decryption round‑trip for per‑patient keys.
   - Mock WeasyPrint rendering and assert watermark presence via PDF inspection library (`pdfminer`).
2. **Integration Tests**
   - End‑to‑end flow: submit intake → generate PDF → verify audit entry exists with correct hash chain.
   - Simulate key rotation mismatch and assert fallback behavior.
3. **Performance Tests**
   - Load test generating 100 concurrent PDFs; ensure response time < 2 seconds and no audit log contention.
4. **Security Tests**
   - Penetration test for session hijacking; ensure token revocation triggers proper audit entries.
   - Verify append‑only property of audit_log cannot be altered via SQL injection attempts.

---
*All content aligns with HIPAA §164.312(a)(2)(iv), SOC 2 security criteria, and SaaS multi‑tenant best practices.*
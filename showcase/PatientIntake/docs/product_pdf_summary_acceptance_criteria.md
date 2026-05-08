# Acceptance Criteria for PDF Summary

## Stakeholder Roles and Goals for the HIPAA‑Compliant Patient Intake System

The following document identifies the concrete stakeholder roles that interact with the intake workflow, articulates their primary goals, and enumerates the pain points they experience. This information will guide the definition of acceptance criteria for the PDF summary feature (FR‑004) and ensure that design decisions address real user needs while satisfying HIPAA technical safeguards (e.g., 45 CFR §164.312(a)(2)(iv)).

### 1. Patient (Primary Data Subject)
**Goals**
- **Accurate Data Capture**: Provide personal, insurance, and medical history information quickly and without errors.
- **Privacy Assurance**: Be confident that all submitted data is encrypted in transit (TLS 1.3) and at rest (AES‑256) per NFR‑002.
- **Transparency**: Receive confirmation that the intake was received and stored securely.

**Pain Points**
- **Form Fatigue**: Long forms increase abandonment risk; patients need progressive disclosure and auto‑save.
- **Trust Deficit**: Unclear handling of sensitive health data can lead to refusal to complete the intake.
- **Access Uncertainty**: Patients may wonder who can view their data; lack of a clear audit‑log view erodes confidence.

**Metrics**
- Completion rate ≥ 92 % for first‑time form submissions.
- Average time to complete ≤ 7 minutes.
- Surveyed trust score ≥ 4.5/5 on data‑privacy perception.

### 2. Front‑Desk Clerk (Administrative Entry Point)
**Goals**
- **Efficient Check‑In**: Quickly verify patient identity and initiate the intake process.
- **Error Reduction**: Detect missing mandatory fields before submission to avoid downstream rework.
- **Role‑Based Access**: View only demographic and insurance data; not clinical notes.

**Pain Points**
- **Manual Re‑Entry**: When a patient abandons a form, clerks must re‑enter data, increasing error risk.
- **Permission Overreach**: Inadequate RBAC may expose clinicians' notes to clerks, violating HIPAA minimum necessary principle.
- **Audit Burden**: Lack of real‑time audit‑log visibility makes it hard to confirm who accessed a record.

**Metrics**
- ≤ 2 minutes average time to start a new intake session.
- ≤ 1% error rate on mandatory field validation.
- 100 % compliance with role‑based view restrictions verified by automated tests.

### 3. Clinician (Care Provider)
**Goals**
- **Comprehensive Clinical View**: Access full medical history and insurance details needed for care decisions.
- **Secure Retrieval**: Retrieve patient data quickly while ensuring confidentiality.
- **Documentation Support**: Generate PDF intake summary for reference during visits.

**Pain Points**
- **Data Latency**: Delays in retrieving encrypted records impede clinical workflow.
- **PDF Integrity Concerns**: Without tamper‑evident watermarks and timestamps, clinicians cannot guarantee document authenticity.
- **Audit Traceability**: Inability to see who has read or exported a PDF hampers compliance reporting.

**Metrics**
- ≤ 3 seconds average retrieval time for encrypted records.
- 100 % of generated PDFs contain FR‑004 mandated watermark and cryptographic timestamp.
- Audit log shows every read/write event with user ID and timestamp; ≥ 99 % completeness verified nightly.

### 4. System Administrator (Security & Operations Owner)
**Goals**
- **Policy Enforcement**: Ensure TLS 1.3 enforcement, field‑level encryption, and role‑based access controls are correctly configured.
- **Audit Log Management**: Maintain immutable audit logs for at least 7 years (NFR‑003) and support export for compliance audits.
- **Deployment Reliability**: Deploy the stack via Docker Compose in an air‑gap environment (FR‑006) without external dependencies.

**Pain Points**
- **Key Management Complexity**: Rotating encryption keys without service interruption is challenging.
- **Log Storage Overhead**: High volume of audit entries can impact storage; need efficient archiving.
- **Air‑Gap Validation**: Verifying that no external network calls occur during deployment requires thorough testing.

**Metrics**
- Key rotation performed quarterly with < 5 minute service disruption.
- Audit log retention ≥ 7 years with < 0.1 % data loss on backup restores.
- Docker Compose deployment completes in ≤ 10 minutes on air‑gapped hardware.

---
All stakeholder goals and pain points are directly traceable to functional requirement FR‑004 (PDF summary), non‑functional requirements NFR‑002/NFR‑003, and security controls AC-002/AU‑6 from NIST SP 800‑53.

### 5. Design Needs
1. Define a secure PDF generation service that receives encrypted field data via internal API, applies AES‑256 encryption at rest for temporary files, and deletes temporary files immediately after streaming to the client.
2. Specify that all transport between front‑end and PDF service must use TLS 1.3 with forward secrecy.
3. Require that each generated PDF includes an invisible digital signature tied to the exporting user's private key (stored in HSM) to provide non‑repudiation.
4. Audit log schema must capture: `export_id`, `user_id`, `role`, `patient_id`, `timestamp`, `file_hash`, `watermark_text`.
5. Watermark implementation must be rendered as semi‑transparent overlay on every page and must be immutable (cannot be removed without breaking PDF integrity).
6. The PDF size limit (5 MB) is enforced by streaming compression; if size exceeds limit, service returns error "PDF exceeds maximum allowed size".

### 6. Metrics & Success Criteria
- 100 % of exported PDFs contain correct watermark and timestamp as verified by automated test suite.
- Audit log completeness ≥ 99.9 % for all export events (no missing entries).
- Mean time to generate a PDF ≤ 2 seconds under typical load (10 concurrent requests).
- No HIPAA‑related security findings in quarterly compliance audit regarding PDF handling.

## Testing Strategy for PDF Summary Feature (Minimum Viable Product)

### 7. Ranked User Stories (MVP)
| ID | Persona | Narrative | Priority |
|----|----------|-----------|----------|
| US-001 | Patient | Submit my personal and medical information through a web form that encrypts each field at rest and in transit | 1 |
| US-002 | Front‑Desk Clerk | Retrieve a patient's submitted intake record after successful authentication | 2 |
| US-003 | Clinician | Generate and download a PDF summary of a patient's intake form that includes a visible watermark and export timestamp | 3 |
| US-004 | Admin | View an immutable audit log of every read/write operation on intake records | 4 |

#### Acceptance Criteria (Gherkin)

**US-001 – Patient Submission**

Given a patient accesses the secure intake web form
When the patient completes all mandatory fields and clicks "Submit"
Then each field is encrypted with AES‑256 at rest and TLS 1.3 in transit
And the system returns a confirmation message containing a unique intake ID
And an audit log entry is created with role=Patient, action=Submit, status=Success

**US-002 – Front‑Desk Retrieval**

Given a front‑desk clerk has authenticated with role=Clerk credentials
When the clerk searches for a patient by name or ID
Then only demographic and insurance fields are displayed
And any attempt to view clinical notes returns an authorization error
And an audit log entry records role=Clerk, action=ViewDemographics, status=Success

**US-003 – Clinician PDF Generation**

Given a clinician is logged in with role=Clinician
When the clinician selects "Generate PDF Summary" for a patient record
Then the PDF service creates a PDF within 2 seconds
And the PDF contains:
  • A semi‑transparent watermark "Confidential – PatientID:<patient_id>"
  • A cryptographic timestamp embedded in the document metadata
And the PDF is signed with the clinician's HSM‑stored private key
And an audit log entry records role=Clinician, action=ExportPDF, file_hash=<hash>

**US-004 – Admin Audit Log Review**

Given an administrator accesses the audit log console
When the admin filters logs by date range or user role
Then all export events show complete fields as defined in the schema
And the log retention policy enforces ≥7 years of immutable storage
And any missing entry triggers an alert flagged as KPI‑003 deviation

---
*All acceptance criteria are traceable to FR‑004, NFR‑002, NFR‑003, KPI‑003, AC-002, AU‑6.*

## Acceptance Criteria

| ID    | User Story | Given| When  | Then |
|-------|-----------------|------------|
| AC-001| US-001     | Patient accesses the intake URL over TLS 1.3 and browser supports Web Crypto API | Patient fills all required fields and clicks **Submit** Each field is encrypted with AES‑256‑GCM before persistence; server stores only ciphertext; TLS‑protected POST returns HTTP 201 with submission UUID.<br>**Negative cases:** Missing TLS → 400; No Web Crypto → server‑side encryption fallback; Payload >5 MB → 413 and event logged. |
|
| AC-002| US-001 | Patient has completed encrypted submission successfully | Patient attempts to view confirmation page via same session token Page shows masked confirmation number and message “Your information has been securely received.” No plaintext appears in HTML source or network trace.<br>**Negative cases:** Session token expired → redirect with “Session expired”; CSRF token missing → 403. |
|
| AC-003| US-002 | Front-desk clerk authenticated with role `front_desk` and valid session token | Clerk searches patient by MRN and selects **View Intake** System decrypts only authorized fields (demographics, insurance) and renders read‑only; audit log records READ event with timestamp and clerk ID.<br>**Negative cases:** Clerk attempts restricted clinical notes → UI hides section and logs UNAUTHORIZED_READ; Network latency >2 s → loading spinner shown but access check enforced before render. |
|
| AC-004| US-003 | Clinician authenticated with role `clinician` and has selected a patient record that passed prior checks | Clinician clicks **Export PDF Summary** Service generates PDF/A‑2b containing all allowed fields, embeds visible watermark “Confidential – Exported by `<ClinicianID>` on `<ISO‑8601 timestamp>`”, forces HTTPS download; file signed with internal X.509 certificate for integrity verification.<br>**Negative cases:** PDF generation fails → UI shows “Export failed – contact IT” and logs `PDF_ERROR`; Clinician lacks permission for certain fields → those fields omitted but watermark remains. |
|
| AC-005| US-004 | Admin authenticated with role `admin` and audit-log view mode enabled | Admin queries audit log for specific patient UUID over past 30 days System returns immutable list of events ([CREATE,READ,UPDATE,EXPORT]) each containing event type, actor ID, timestamp, source IP, cryptographic hash of original record version; response delivered over TLS 1.3 and read-only.<br>**Negative cases:** Query exceeds 10 000 rows → pagination enforced; Attempt to tamper via API → 403 and incident logged. |
|

## Edge‑Case & Failure Scenarios

1. **Encryption Key Rotation** – If a rotation occurs mid‑session, the client continues encrypting with the current public key; the server re‑encrypts stored ciphertext with the new key after successful decryption.
2. **Network Interruption** – On HTTPS drop during submission, the client automatically retries up to three times; duplicate submissions are deduplicated using the UUID returned on first successful attempt.
3. **Unauthorized Role Escalation** – Any front‑desk clerk attempting to invoke AC‑004 triggers immediate session termination, logs a `PRIVILEGE_ESCALATION` event, and notifies security monitoring.
4. **PDF Tampering Detection** – Generated PDF includes an embedded SHA‑256 hash of the source data; any post‑export modification invalidates the signature, causing downstream verification tools to flag the file as compromised.

## Test Coverage Matrix

| Test Type                     | Scope| KPI Reference               | Acceptance Criteria Covered| Success Metric|
|-----------|-------------|-----------|----------------------|-----------|
| Unit – Encryption Module     | US‑001 fields encryption               | KPI‑003 (audit compliance)   | AC‑001 – field encryption ≥ 99.9% | Pass  |
| Integration – Form Submission Flow | US‑001 end-to-end submission | KPI‑001 (system availability) | AC‑001 latency ≤ 2 s under 100 concurrent users | Pass  |
| Security – Role Access Checks | US‑002, US‑003, US‑004 | KPI‑002 (zero security incidents) | AC‑003, AC‑004, AC‑005 unauthorized attempts logged = 0 false negatives | Pass  |
| Functional – PDF Export Validation | US‑003 PDF generation | KPI‑004 (PDF integrity) | Watermark present 100%; ISO‑8601 timestamp format ≥ 99%; signature verification success ≥ 99% | Pass  |
 | Audit Log Integrity Test | US‑004 log retrieval | KPI\-005 (audit log completeness) | Immutable entries ≥ 99.99% over 30 day retention; pagination works correctly | Pass  |

## Traceability

All acceptance criteria reference functional requirements from the project brief:

* **FR-001** – Secure patient data capture (mapped to AC-001 & AC-002)
* **FR-002** – Transport encryption (mapped to AC-001)
* **FR-003** – PDF summary generation with watermark (mapped to AC-004)
* **FR-004** – Audit log immutability (mapped to AC-005)
* **FR-005** – Docker Compose deployment (out of scope for this feature spec)

The specification aligns with SOC 2 and HIPAA technical safeguard requirements by enforcing TLS 1.3, AES‑256‑GCM encryption, key rotation handling, immutable audit logging, and signed PDF artifacts.
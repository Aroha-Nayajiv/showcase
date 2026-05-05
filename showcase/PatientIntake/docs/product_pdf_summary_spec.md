# PDF Intake Summary Specification
                
### 1. Front Desk Clerk (ST‑01)
- **Primary Goal:** Capture patient demographic, insurance, and medical‑history data quickly and accurately at the point of entry.
- **Key Tasks:**
  1. Log in to the intake workstation using unique credentials (NIST AC‑2).
  2. Open the Patient Intake Form and enter required fields (name, DOB, address, insurance policy number, etc.).
  3. Verify that each field shows a lock icon indicating field‑level encryption in transit (TLS 1.3) and at rest (AES‑256 per field).
  4. Submit the form; the system records an audit log entry (FR‑003) with `action=CREATE`, `actor=FrontDesk`, timestamp.
  5. Request a PDF Intake Summary for a newly registered patient by clicking **Generate PDF**.
- **Security Responsibilities:**
  - Must never export the PDF without selecting an authorized staff role; the UI disables the button for non‑authorized users.
  - Must confirm the presence of a watermark that reads "CONFIDENTIAL – FOR INTERNAL USE ONLY" and an access timestamp displayed in the footer of the PDF.
- **Failure Scenarios & Acceptance Checks:**
  - Network interruption before submission should trigger a client‑side retry and retain entered data locally encrypted.
  - Attempt to generate PDF without proper role must display an error "Insufficient permissions – contact administrator."

### 2. Clinician (ST‑02)
- **Primary Goal:** Review patient intake information and PDF summary to make clinical decisions while ensuring data privacy.
- **Key Tasks:**
  1. Authenticate via multi‑factor login (username + OTP) as required by HIPAA § 164.312(a)(2)(iv).
  2. Search for a patient record using MRN or name; system checks role‑based access control (RBAC) before returning data.
  3. Open the PDF Intake Summary from the patient's record view.
  4. Verify that the PDF contains the required watermark and timestamp; note that the timestamp must be in UTC ISO‑8601 format.
  5. Add clinical notes (outside scope of this artifact) and optionally re‑export an updated PDF – the system must create a new audit log entry with `action=EXPORT`.
- **Security Responsibilities:**
  - Must not share the PDF via external email; UI enforces download only to local encrypted storage.
  - Must log every view (`action=VIEW`) of the PDF for audit compliance.
  - Expired session while viewing PDF should automatically log out and require re‑authentication before any further export.
  - Corrupted PDF generation must present a fallback message "PDF generation failed – please retry" and create an audit entry with `action=ERROR`.

### 3. Compliance Officer (ST‑03)
- **Primary Goal:** Ensure that all PDF generation activities comply with HIPAA, internal policies, and audit requirements.
- **Key Tasks:**
  1. Log in with read‑only audit privileges.
  2. Access the Audit Log Viewer filtered by `action=EXPORT` or `action=VIEW` for PDFs.
  3. Verify that each exported PDF record includes:
     - Correct watermark text.
     - Accurate access timestamp matching system clock.
     - Proper role identifier (`actor=FrontDesk` or `actor=Clinician`).
  4. Run periodic compliance reports (e.g., "PDF Export Compliance – last 30 days") that must show < 0.5 % deviation from expected watermark presence.
- **Security Responsibilities:**
  - Must not have write access to patient data; only audit read access is permitted.
  - Must ensure that any export logs are immutable (append‑only) and retained for at least 7 years per HIPAA retention policy.
  - Attempt to modify audit entries should be blocked and logged as a security incident.
  - Missing watermark in any exported PDF flagged during review must generate a compliance alert within the system.

#### Persona Summary Table
| ID   | Persona               | Primary Goal                                 | Primary Interaction                     | Acceptance Checks |
|------|-----------------------|----------------------------------------------|------------------------------------------|--------------------|
| PER‑01 | Front Desk Clerk    | Capture intake data & generate initial PDF    | Click **Generate PDF** after form submission | Watermark present, timestamp recorded, RBAC enforcement |
| PER‑02 | Clinician           | Review intake data for care decisions        | Open & view exported PDF from patient record | Audit log entry for VIEW/EXPORT, session timeout handling |
| PER‑03 | Compliance Officer   | Verify HIPAA compliance of PDF exports       | Query audit logs for EXPORT actions       | Immutable log, retention ≥7 years, watermark verification |

## User Story Table
| ID   | Persona (Role) | Description |
|------|-----------------|-------------|
| US‑001 | Front Desk Clerk (ST‑01) | Enter patient demographics, insurance details, and medical history into a structured web form that encrypts each field at rest and in transit |
| US‑002 | Clinician (ST‑02) | Retrieve a previously submitted intake record and view decrypted data after successful role‑based authentication |
| US‑003 | Compliance Officer (ST‑03) | Generate an audit log entry for every create, read, update, or delete operation on intake records and verify that the log entry is immutable and timestamped |

### AC‑002 – Network Resilience on Form Submission (US‑001)
**Given** the clerk has entered valid data but network connectivity is lost before the request reaches the server,
**When** the browser automatically retries up to three times,
**Then** after three failed attempts a persistent banner "Network unavailable – data not saved" is displayed, no partial ciphertext is persisted, and no audit log entry is recorded.

### AC‑004 – Clinician View Patient Record (US‑002)
**Given** a Clinician is authenticated via multi‑factor authentication and holds a valid session token,
**When** they select a patient record from the dashboard and click **View Details**,
**Then** the backend decrypts each field using the Clinician's RSA‑OAEP private key wrapper, renders a read‑only view of plaintext data, and creates an audit log entry (`action=VIEW`, `actor=Clinician`).\]

### AC‑005 – Clinician Export Updated PDF (US‑002)
**Given** the Clinician has viewed a patient’s intake record,
**When** they click **Export Updated PDF**,
**Then** a new PDF is generated containing the required watermark and UTC ISO‑8601 timestamp, a new audit log entry (`action=EXPORT`, `actor=Clinician`) is recorded, and the download is saved to local encrypted storage only.

### AC‑007 – Compliance Officer Audit Log Review (US‑003)
**Given** the Compliance Officer logs in with read‑only audit privileges,
**When** they filter audit logs by `action=EXPORT` or `action=VIEW` for PDFs,
**Then** each returned record shows:
- Correct watermark text "CONFIDENTIAL – FOR INTERNAL USE ONLY"
- Accurate UTC timestamp matching system clock
- Proper actor identifier (`FrontDesk` or `Clinician`)
and the logs are immutable (append‑only) and retained for ≥7 years.

### AC‑008 – Missing Watermark Alert (US‑003)
**Given** a PDF export occurs without embedding the required watermark,
**When** the compliance report runs,
**Then** a compliance alert is generated within the system and an audit log entry (`action=ERROR`, `actor=System`) is created.

## PDF Intake Summary – Feature Specification

### Personas
- **ST-01** – Front Desk Clerk: Captures patient demographic data via the web form and requests a PDF for printing or hand‑off.
- **ST-02** – Clinician: Reviews a patient's medical history and exports the PDF for clinical use.
- **ST-03** – Compliance Officer (Auditor): Monitors audit logs, reviews alerts, and validates that all security controls are in place.

### Design Artifacts (Hand‑off to Design)
1. **Field‑Level Encryption Specification** – AES‑256‑GCM per field, IV generated with a cryptographically secure random source, per‑field keys wrapped by RSA‑OAEP 2048‑bit keys stored in an on‑prem HSM.
2. **TLS Configuration** – Enforce TLS 1.3 only, cipher suites `TLS_AES_256_GCM_SHA384`, `TLS_CHACHA20_POLY1305_SHA256`; enable HSTS (`max-age=31536000; includeSubDomains`).
3. **UI Validation Rules** – Minimum/maximum lengths, regex patterns for insurance numbers, mandatory selection of medical‑history categories.
4. **Error Message Taxonomy** – Standardized user‑facing messages for missing fields, decryption failures, permission denials, network outages.
5. **Audit Log Schema** – `log_id (UUID)`, `user_id`, `role`, `operation_type`, `timestamp (ISO‑8601)`, `record_hash (SHA‑256)`, `outcome (success|failure)`, `notes`.
6. **RBAC Matrix** – Front Desk: Create/Read; Clinician: Read/Update; Compliance Officer: Read/Audit only.
7. **Failure Recovery Flow** – Offline capture fallback UI, automatic retry with exponential back‑off, admin alert on repeated failures.

---

### US‑002 – Key Rotation without Downtime
**As** a *System Administrator* **I want** encryption keys rotated every 30 days so that key compromise risk is limited.

**Acceptance Criteria**
- **Given** a master key has been in use for 30 days
- **When** the rotation job runs (cron or systemd timer)
- **Then** a new master key is generated, existing per‑file keys are re‑wrapped, and all PDFs remain accessible using the new key (FR‑002)
- **And** no service interruption occurs
- **And** any re‑wrap failure is logged with file ID and administrators are alerted (EF‑2).

### US‑003 – Secure PDF Download (TLS 1.3)
**As** a *Clinician* **I want** PDF downloads to be delivered over TLS 1.3 so that data in transit is protected.

**Acceptance Criteria**
- **Given** an authorized clinician initiates a download via the web UI
- **When** the request reaches the Nginx reverse proxy configured for TLS 1.3
- **Then** the response uses an ECDHE cipher suite and includes the HSTS header `max-age=31536000; includeSubDomains`
- **And** the PDF stream is delivered directly from disk without creating temporary plaintext files on the proxy (FR‑003)
- **And** if the client attempts a lower TLS version, the connection is rejected with HTTP 400 (EF‑3).

### US‑004 – Mutual TLS for Service‑to‑Service Calls
**As** a *PDF Generator* **I want** to record audit events over mTLS so that internal traffic is authenticated and encrypted.

**Acceptance Criteria**
- **Given** the PDF generator needs to log an audit event
- **When** it opens an HTTPS connection to the audit logging microservice using client certificates
- **Then** the connection succeeds only if both server and client certificates are valid and signed by the internal CA (FR‑004)
- **And** the payload is encrypted end‑to‑end
- **And** on certificate validation failure, the generator retries up to three times then aborts and raises an alert (EF‑4).

### US‑005 – Immutable Audit Logging for PDF Generation
**As** a *Compliance Officer* **I want** every PDF generation event logged immutably so that we can prove compliance.

**Acceptance Criteria**
- **Given** a PDF is successfully generated for patient ID `12345`
- **When** the audit logger receives the event payload
- **Then** an immutable log entry is created containing:
  - timestamp (ISO‑8601 UTC)
  - actor role (`clinician`)
  - patient ID
  - file hash (SHA‑256)
  - operation (`PDF_GENERATE`)
  - outcome (`SUCCESS`)
- **And** the entry is written to PostgreSQL with row‑level security allowing only auditors read access (FR‑005)
- **And** if the write fails (e.g., DB disk full), the primary operation rolls back and returns error "System unable to record audit trail – contact admin" (EF‑5).

### US‑007 – Tamper‑Evident Retention of Audit Logs
**As** a *Compliance Officer* **I want** audit logs to be tamper‑evident and retained for at least seven years.

**Acceptance Criteria**
- **Given** the system has been operational for two years
- **When** log entries are written to an append‑only table with cryptographic hash chaining (each row stores hash of previous row)
- **Then** logs are immutable; any modification attempt violates database constraints and is rejected (FR‑006)
- **And** a retention policy automatically archives logs older than seven years to WORM storage (EF‑6)
- **And** attempts to modify existing rows generate an alert.

### US‑008 – Real‑Time Alerting on Encryption Failures
**As** a *Security Operations Center* analyst **I want** immediate alerts when encryption at rest or in transit fails so that incidents can be triaged quickly.

**Acceptance Criteria**
- **Given** any failure to encrypt at rest or in transit occurs
- **When** the failure is detected by the service layer
- **Then** a Slack webhook alert is sent within 30 seconds with details of the failure (FR‑007)

### US‑009 – Automated Incident Ticket on Audit Log Write Failure
**As* a *System* **I want* automatic Jira ticket creation when audit log writes fail so that remediation is tracked.

**Acceptance Criteria**
- **Given* an audit log write error (e.g., DB connection loss) occurs
- **When* the error is captured by the logging middleware
- **Then* a high‑severity incident ticket is created in Jira with error details and assigned to the on‑call engineer (FR‑008).

---\---

## Failure Recovery Flows & UI Guidelines
1. **Offline Capture UI:** If encryption services are unavailable, present a read‑only warning banner and allow clinicians to view previously cached PDFs in read‑only mode.
2. **Retry Strategy:** Automatic exponential backoff retries for transient network or certificate errors up to three attempts before escalating.
3. **Alert Escalation:** After three consecutive failures, trigger an email/SLA breach notification to the security lead.
4. **User Messaging:** All error messages follow the taxonomy defined in Section 4 of Design Artifacts (e.g., "Unable to decrypt record – contact IT", "Permission denied", "System unable to record audit trail – contact admin").

---\---

## Traceability Matrix
| Requirement ID | Description | Covered By |
|--------------|-------------|--------------|
| FR-001 | Secure demographic capture | US-001 |
| FR-002 | Encryption key rotation | US-002 |
| FR-003 | TLS 1.3 delivery of PDFs | US-003 |
| FR-004 | Mutual TLS between services | US-004 |
| FR-005 | Immutable audit log for PDF generation | US-005 |
| FR-006 | Tamper‑evident audit retention | US-007 |
| FR-007 | Real‑time alerting on encryption failures | US-008 |
| FR-008 | Automated Jira ticket on audit log failure | US-009 |
| NFR-001 | Response time <200 ms for form submissions | — |
| NFR-002 | System uptime 99.9 % | — |
| NFR-003 | Mandatory audit logging of every read/write operation | US-005, US-006 |
| KPI-01 | Response time compliance | — |
| KPI-02 | System availability | — |
| KPI-03 | Successful audit log generation per submission | — |
| RISK-01 | Unauthorized data exposure | Mitigated by encryption & RBAC |
| RISK-02 | Open-source component vulnerabilities | Managed via dependency scanning |
| RISK-03 | Deployment misconfiguration | Addressed by mTLS & HSTS |
| RISK-04 | Compliance audit gaps | Covered by immutable logs & alerts |
| RISK-05 | On-prem deployment constraints | Capacity monitoring & buffer resources |

# Feature Specification: HIPAA‑Compliant Patient Intake PDF Generation

## 4. Feature Overview
The system shall generate a secure, auditable PDF intake summary for each patient record. The PDF must include a HIPAA‑compliant watermark and UTC timestamp, be encrypted at rest, and generate an immutable audit log entry for every export event.

## 5. Personas
| ID   | Role                | Description                                                                 |
|------|---------------------|-----------------------------------------------------------------------------|
| ST-01| Clinical Staff      | Captures patient demographics and initiates PDF export.                     |
| ST-02| Patient             | Provides demographic data via the intake form.                            |
| ST-03| Compliance Officer  | Verifies that every PDF export is auditable, watermarked, and timestamped according to HIPAA audit requirements. |

### US-001: Generate HIPAA‑compliant PDF Intake Summary
**As** a **Clinical Staff (ST‑01)**
**I want** to generate a PDF summary of a patient’s intake form that includes a watermark and timestamp
**So that** the document meets HIPAA audit requirements and can be stored securely.

*Traceability*: FR‑001, FR‑003, FR‑007, NFR‑001, NFR‑003, RISK‑01

#### Acceptance Criteria
1. **Given** a completed intake form with all mandatory demographic fields populated (per FR‑001)
   **When** the user selects “Export PDF”
   **Then** the system generates a PDF containing the entered data, applies the configured watermark (per FR‑007) and includes a UTC timestamp in the footer.
2. **Given** the PDF is generated
   **When** it is stored in the repository
   **Then** it is encrypted at rest (per NFR‑001) and an immutable audit log entry is created (per NFR‑003).
3. **Given** the user lacks the “Compliance Officer” role
   **When** they attempt to view the PDF audit details
   **Then** access is denied and an audit entry records the denied attempt (per RISK‑01).

### US-002: View Audit Trail for Generated PDFs
**As** a **Compliance Officer (ST‑03)**
**I want** to view an immutable audit trail for each generated PDF
**So that** I can verify compliance with HIPAA logging requirements.

*Traceability*: FR‑003, NFR‑003, RISK‑01

## 7. Detailed Schema Definitions

### PDF Metadata Schema (stored alongside each PDF)

{
  "patient_id": "string",
  "generated_at": "ISO8601 timestamp",
  "watermark_text": "string",
  "checksum_sha256": "string",
  "encryption_key_id": "string"
}

*Traceability*: maps to FR‑007 (watermark), NFR‑001 (encryption), NFR‑003 (audit).

## 8. Dependencies & Integration Points
| ID    | Dependency                | Description                                 |
|-------|----------------------------|---------------------------------------------|
| FR-001| Secure demographic capture | Provides source data for PDF content.       |
| FR-003| Audit logging              | Required for each export event.             |
| FR-007| PDF generation with watermark| Defines watermark requirement.               |
| NFR-001| Encryption at rest       | Governs file storage method.               |
| NFR-003| Immutable audit log       | Dictates log persistence design.          |

## 9. Edge Cases & Failure Handling Summary
1. **Incomplete Record** – Export blocked; UI shows explicit missing fields list.
2. **Insufficient Storage** – Export aborted; system logs AU‑002 with reason code `STORAGE_LOW`.
3. **Key Management Failure** – Export unavailable; alert sent to Ops team; audit entry records failure reason `KEY_UNAVAILABLE`.
4. **Unauthorized Role Attempt** – Immediate denial; audit entry records attempted access with status `DENIED`.
5. **Tampered PDF Detection** – On subsequent verification, mismatch triggers `RISK‑01` escalation workflow.

## 10. Testable Acceptance Criteria (Gherkin)
gherkin
Feature: PDF Intake Summary Generation

Scenario: Successful PDF generation with watermark and timestamp
  Given a patient record with all required demographic fields
    And the user has role "Clinical Staff"
  When the user clicks "Export PDF"
  Then a PDF is generated containing the patient data
    And the PDF includes watermark "Confidential - HIPAA"
    And the PDF footer shows the current UTC timestamp
    And the PDF file is stored encrypted at rest
    And an immutable audit log entry is created

Scenario: Export blocked due to missing mandatory fields
  Given a patient record missing the "Insurance Number"
  When the user clicks "Export PDF"
  Then the system displays an error listing missing fields
    And no PDF is generated

## 11. KPI & Risk Alignment
*KPIs*: KPI‑01 (response time <200 ms for export), KPI‑03 (audit log generation for every submission), KPI‑04 (PDF export security compliance).
*Risks*: RISK‑01 (unauthorized data exposure), RISK‑02 (open‑source component vulnerabilities) – mitigated by encryption at rest and immutable logging.
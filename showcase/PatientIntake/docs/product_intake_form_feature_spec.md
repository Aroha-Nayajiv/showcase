# Feature Specification for Secure Intake Form

## Overview
The Secure Patient Intake Form is the first point of interaction for three distinct user groups that must each satisfy HIPAA‑mandated safeguards while delivering a smooth experience. These personas were derived from the stakeholder list (ST-001 Clinical staff, ST-002 Patients, ST-003 Compliance officers) and from the functional requirements FR‑001 – FR‑003 that define data capture, encryption, role‑based access, and audit logging. By articulating the motivations, constraints, and success criteria for each role we give Design a concrete human‑centered context that can be translated directly into UI flows, validation rules, and accessibility requirements.

---

## Personas
| ID | Name | Role | Description | Primary Goals | Pain Points | Security & Compliance Considerations | Success Metrics |
|----|------|------|-------------|----------------|--------------|--------------------------------------|----------------|
| PER‑01 | Front‑Desk Clerk | Front Desk | Administrative staff responsible for initial patient registration and insurance verification. | • Capture all required fields accurately within 2 minutes per patient (KPI-001). • Ensure data is encrypted in transit (TLS 1.3) and at rest (field‑level AES‑256) per FR‑001 and NFR‑001. • Receive immediate visual confirmation of successful submission and audit logging. | High volume periods can lead to rushed entry and validation errors; limited technical training on encryption mechanisms. | Must never see raw unencrypted PHI after submission; UI masks data post‑submission. Every create operation triggers an immutable audit log entry (FR‑004) recording user ID, timestamp, and operation type. | ≥ 98 % of submissions pass client‑side validation without correction. | Zero instances of unencrypted PHI stored on local disk (quarterly audit). |
| PER‑02 | Clinician | Clinician | Reviews completed intake forms to assess patient history before providing care. Access is read‑only for most fields but can add clinical notes. | • Retrieve a patient's intake record within 1 second (KPI-001) while maintaining confidentiality. • Verify PDF summary reflects latest encrypted data and includes a watermark with clinician name and access timestamp. | • Flag missing or inconsistent information for re‑capture by front desk. | Slow decryption or network latency interrupts workflow; unclear visual cues for tampered/out‑of‑sync records. | Access limited to records where clinician’s role matches patient’s care team (RBAC – FR‑002). Every read operation creates an audit log entry (FR‑004) capturing user ID and timestamp to satisfy AU‑6 control. | ≥ 99 % of read operations meet response time target; no unauthorized read events in monthly audit reports. |
| PER‑03 | Compliance Officer | Compliance Officer | Audits system activity to ensure ongoing HIPAA compliance and prepares reports for internal governance and external regulators. | • Generate audit reports listing all CRUD actions for a given period with immutable timestamps. • Verify every PDF export includes required watermark and access timestamp (FR‑003). | • Confirm encryption keys are rotated per policy and no plaintext PHI is stored on disk. | Large volume of log entries makes manual review time‑consuming; needs assurance encryption meets technical safeguard standards (45 CFR 164.312). | Read‑only access to audit logs; cannot modify logs (AU‑6). Must export logs in tamper‑evident format for external audit. | Ability to produce a complete audit report for any date range within 5 minutes; zero findings of unencrypted PHI in quarterly compliance scans. |

---

### US‑001 – Clinical Staff (Nurse) – Capture Patient Demographics
**As a** Clinical Staff (Nurse) **I want** to enter patient demographics, insurance details, and medical history into a structured web form that encrypts each field individually **so that** the patient’s protected health information (PHI) is protected both at rest and in transit, satisfying HIPAA technical safeguards.
**Acceptance Criteria** (Given/When/Then):
- **Given** the nurse is authenticated and has a secure session (TLS 1.3),
- **When** the nurse completes all mandatory fields and clicks **Submit**,
- **Then** each field is encrypted at rest using AES‑256 and transmitted over TLS 1.3, an immutable audit log entry (FR‑004) is created, and a success toast with a unique submission ID is displayed.
- **Given** any mandatory field is left blank,
- **When** the nurse attempts to submit,
- **Then** client‑side validation prevents submission and highlights the missing fields.

### US‑002 – Front Desk Clerk – Validate Insurance Information
**As a** Front Desk Clerk **I want** to validate insurance information against the insurer’s API before saving the record **so that** the system only stores verified insurance data, reducing billing errors and maintaining data integrity.
**Acceptance Criteria**:
- **Given** the clerk has entered insurance policy number and provider name,
- **When** the clerk clicks **Validate Insurance**,
- **Then** the system calls the insurer API over a mutually authenticated TLS channel, receives a verification response within 2 seconds, and displays **Verified** or **Invalid** status.
- **Given** the insurance is verified,
- **When** the clerk submits the form,
- **Then** the encrypted insurance data is stored and an audit log entry (FR‑004) records the create action.

### US‑003 – Compliance Officer – View Immutable Audit Log
**As a** Compliance Officer **I want** to view an immutable audit log of every create, read, update, or delete operation on intake records **so that** I can demonstrate compliance with NIST SP 800‑53 AU‑6 and HIPAA audit requirements during inspections.
**Acceptance Criteria**:
- **Given** the compliance officer is authenticated with read‑only role,
- **When** they request an audit report for a date range,
- **Then** the system generates a CSV/JSON report containing all CRUD events with timestamps, user IDs, operation types, and cryptographic hash of each record snapshot; the report is signed with the system’s private key.
- **Given** the report is generated,
- **When** the officer downloads it,
- **Then** the file includes a visible watermark with officer name and generation timestamp.

---

## Acceptance Summary
All user stories now include explicit Given/When/Then scenarios aligned with functional requirements FR‑001 – FR‑004 and non‑functional requirements NFR‑001 (encryption) and NFR‑003 (audit logging). Acceptance criteria reference KPI targets where applicable.

---

## Traceability Matrix
| Persona / Role | Linked Requirements | KPIs |
|----------------|--------------------|------|
| Front‑Desk Clerk | FR‑001, FR‑004, NFR‑001 | KPI-001 (response time), KPI-003 (audit log generation) |
| Clinician | FR‑002, FR‑003, NFR‑001 | KPI-001 (response time), KPI-002 (system availability) |
| Compliance Officer | FR‑004, NFR‑003 | KPI-003 (audit log completeness), KPI-004 (PDF export compliance) |

---

## Definitions
* **FR‑004 – Audit Logging:** The system must create an immutable log entry for every create, read, update, or delete operation on patient intake records. Each entry records user ID, timestamp (ISO 8601), operation type, and a cryptographic hash of the affected record snapshot.
* **NFR‑001 – Encryption:** All PHI fields must be encrypted at rest using AES‑256 with per‑field keys and transmitted over TLS 1.3.
* **NFR‑003 – Audit Log Integrity:** Audit logs must be write‑once/read many (WORM) storage ensuring tamper evidence; logs are retained for at least 7 years.

## Functional Requirements

| ID   | Description |
|------|-------------|
| FR-001 | Secure demographic capture with client‑side AES‑256‑GCM encryption and TLS 1.3 transport. |
| FR-002 | Insurance verification via external insurer API over HTTPS with audit logging. |
| FR-003 | PDF intake summary generation with watermark and timestamp, stored in a protected directory. |
| FR-004 | Automated unit and integration tests covering form validation, encryption handling, access control, and audit logging. |
| FR-005 | PDF Intake Summary Generation compliance (e.g., PDF/A‑2b). |
| FR-006 | Watermark & Timestamp implementation for generated PDFs. |
| FR-007 | Immutable audit log export supporting CSV download with cryptographic hashes per entry. |
| FR-008 | Containerized deployment using Docker Compose with isolation and resource limits. |

## Risks

| ID       | Description |
|----------|-------------|
| RISK-01  | Unauthorized data exposure due to mis‑configured encryption keys. |
| RISK-02  | Open‑source component vulnerabilities in encryption libraries. |
| RISK-03  | Deployment misconfiguration leading to insecure container settings. |
| RISK-04  | Compliance audit gaps caused by incomplete audit logs. |
| RISK-05  | On‑premise deployment without auto‑scaling may cause capacity bottlenecks. |

### US-001 – Secure Demographic Capture (Priority 1)
**As a** Front Desk Operator (**PER‑01**)
**I want** to enter patient demographics, insurance information, and medical history into a structured web form that encrypts each field at rest and in transit
**So that** the data is protected per HIPAA §164.312(a)(2)(iv) and can be safely stored in PostgreSQL.

### AC‑001 – US‑001 Successful Submission
**Given** the Front Desk Operator is authenticated with role **FrontDesk**, the web form is loaded over **TLS 1.3**, and all required fields (first name, last name, DOB, address, phone, insurance policy number, medical history) are filled correctly;
**When** the operator clicks **Submit**;
**Then** each field is encrypted client‑side using **AES‑256‑GCM**, the ciphertext is persisted in PostgreSQL, the server returns **201 Created** within **200 ms**, and an audit log entry `CREATE` with actor `FrontDesk` and timestamp is recorded.

### AC‑003 – US‑001 Network Interruption (Failure)
**Given** the TLS connection is interrupted after client‑side encryption but before server receipt;
**When** the operator clicks **Submit** and the network drops;
**Then** the client shows a "Submission failed – please retry" dialog, no plaintext data is transmitted, no audit entry is created, and the encrypted payload is discarded client‑side.

### AC‑004 – US‑002 Insurance Verification Success
**Given** the Clinician is authenticated with role **Clinician**, the front‑desk clerk (or clinician) is authenticated with role **FrontDesk**, and the insurer API endpoint is reachable;
**When** a valid insurance policy number is entered and **Verify** is clicked;
**Then** the system calls `POST https://insurer.example.com/verify` over HTTPS, receives a positive verification response, stores the encrypted policy number, displays "Insurance verified", and records an audit entry `VERIFY` with actor `FrontDesk`.

### AC‑007 – US‑002 PDF Generation Success
**Given** the Clinician is authenticated with role **Clinician**, selects an encrypted intake record less than **500 KB**, and clicks **Generate PDF**;
**When** the request is processed;
**Then** the system decrypts the record in memory only, renders a PDF via **wkhtmltopdf**, adds a semi‑transparent watermark "Confidential – Authorized Staff Only", appends an access timestamp footer, stores the PDF in a protected directory (`/secure/pdfs/`), logs an `AUDIT_READ` event with clinician ID and timestamp, and the download completes within **1 s**.

### AC‑008 – US‑002 PDF Generation Template Missing (Edge)
**Given** the PDF generation service cannot locate the required template file;
**When** generation is attempted;
**Then** the system returns a user‑friendly error "PDF template unavailable – contact support", does not create a PDF file, and logs an `ERROR_PDF_TEMPLATE_MISSING` entry.

### AC‑010 – US‑003 Large Export Performance (Edge)
**Given** the audit log contains more than **10 000 entries** for the selected range;
**When** **Generate Report** is requested;
**Then** the system paginates results internally but provides a complete downloadable CSV; performance remains under **2 seconds per 1 000 rows**, satisfying **KPI-001**, and progress feedback is shown to the user.

### Verify Insurance Endpoint

POST /api/v1/insurance/verify
Headers:
  Authorization: Bearer <JWT>
  Content-Type: application/json
Body:
{
  "policyNumber": "string",
  "patientId": "uuid"
}
Responses:
  200 OK { "status": "verified", "details": { ... } }
  400 Bad Request { "error": "Invalid policy format" }
  504 Gateway Timeout { "error": "Insurer service unavailable" }

All traffic uses TLS 1.3; request payloads are encrypted at rest by default.

## Test Coverage Expectations (FR‑004)
Automated unit tests must cover:
* Form field validation logic (including SSN format).
* Client‑side encryption functions producing AES‑256‑GCM ciphertext.
* API request handling for `/api/v1/insurance/verify` including success and error paths.
* PDF generation service handling of missing templates.
* Audit log export pagination logic.
Integration tests must verify end‑to‑end encryption flow from browser to database and back through decryption for authorized roles.
Coverage target: ≥85 % of statements across modules.

---
*All artifacts trace back to functional requirements FR‑001 – FR‑008, non‑functional requirements NFR‑001 – NFR‑004, KPIs KPI-001 – KPI-004, and risks RISK-001 – RISK-005.*

# PatientIntake – Refined Feature Specification

## 1. Key Performance Indicators (KPI)
| ID | Metric |
|----|--------|
| **KPI-001** | % of form submissions completing within 200 ms. |
| **KPI-002** | System availability measured monthly (target 99.9 %). |
| **KPI-003** | Success rate of audit‑query operations within 300 ms. |
| **KPI-004** | PDF export compliance – watermark present on 100 % of exported PDFs. |
| **KPI-005** | Test coverage ≥ 80 % for form validation, encryption handling and audit logging. |

---

## 2. User Stories & Acceptance Criteria

#### Acceptance Criteria
| AC ID | Given | When | Then |
|------|-------|------|------|
| AC‑003 | The clinician is authenticated with `role=Clinician` and has `view:record` permission.| The clinician opens a patient record.| The system decrypts fields on demand, displays them within 200 ms, and logs an `AUDIT_READ` event with cryptographic hash of the original payload. |
| AC‑004 | The clinician clicks **Export PDF** on a loaded record.| The PDF generator (`wkhtmltopdf` ≥ 0.12.6) creates a PDF, overlays a watermark "Authorized Clinician: <Name>" and a footer timestamp ISO‑8601.| The PDF is delivered within 1 s; an `AUDIT_EXPORT` event is recorded with hash and watermark verification flag set to true. |
| AC‑005 | The PDF generation service is unavailable.| The clinician attempts export.| The system returns user‑friendly error "PDF generation unavailable – contact IT", logs an `AUDIT_ERROR` event, and does **not** expose stack traces or raw data. |

### PER‑01 – Front Desk Operator
*Primary Goals:* Register patients quickly while ensuring confidentiality.
*Key Tasks:* Enter demographics, select insurance, submit form → triggers field‑level encryption.
*HIPAA Relevance:* Handles PHI at entry point; must enforce technical safeguard §164.312(a)(2)(iv).
*Priority:* High

### PER‑02 – Clinician (Nurse / Physician)
*Primary Goals:* Review intake data and generate chartable PDF.
*Key Tasks:* View encrypted record (decrypt on demand), export PDF with watermark & timestamp.
*HIPAA Relevance:* Direct PHI access; must log all read/export actions (AU‑6).
*Priority:* High

### PER‑03 – Compliance Officer
*Primary Goals:* Audit system behavior for HIPAA compliance.
*Key Tasks:* Query audit log by date/user/type, verify watermark presence on PDFs, review key rotation reports.
*HIPAA Relevance:* Oversight of technical safeguards §164.312(b).
*Priority:* Medium

### PER‑04 – System Administrator
*Primary Goals:* Deploy and maintain secure on‑prem environment.
*Key Tasks:* Deploy Docker Compose stack in air‑gapped network, configure PostgreSQL row‑level security, rotate TLS certificates, monitor container health.
*HIPAA Relevance:* Protects infrastructure that stores PHI (§164.312(a)(1)).
*Priority:* Medium

---

## 4. MVP Scope Prioritization by Persona
1. **Demographic Capture** – Critical for PER‑01 & PER‑02; must be encrypted at field level.
2. **PDF Summary Generation** – Essential for PER‑02; includes watermark & timestamp; audited by PER‑03.
3. **Full Audit Logging** – Required for PER‑02, PER‑03 & PER‑04; immutable append‑only table per FR‑004.
4. **Role‑Based Access Control** – Underpins all personas; enforced via PostgreSQL RBAC.
5. **Air‑Gap Deployment Guidance** – Supports PER‑04’s on‑prem constraints.

---

## 5. Design Needs (Technical Specifications)

### 5.1 Field‑Level Encryption
* Algorithm: **AES‑256‑GCM**
* Key Management: Per‑field keys derived from a master key stored in an HSM or sealed vault; rotation policy every 90 days; keys are never exposed to the client beyond encrypted payloads.

### 5.2 Audit Log Schema (Immutable Append‑Only Table)
sql
CREATE TABLE audit_log (
    event_id          UUID PRIMARY KEY,
    actor_role        TEXT NOT NULL,
    actor_id          TEXT NOT NULL,
    operation_type    TEXT NOT NULL CHECK (operation_type IN ('CREATE','READ','EXPORT','QUERY','ERROR')),
    target_record_id   TEXT,
    timestamp         TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload_hash      BYTEA NOT NULL,
    severity           TEXT NOT NULL CHECK (severity IN ('INFO','WARN','ERROR'))
);
-- Table is append only; DELETE/UPDATE prohibited via row-level security policies.

### 5.3 Performance Thresholds
* Form submission ≤ 200 ms server processing (NFR‑001).
* PDF generation ≤ 1 s for typical record size (NFR‑002).
* Audit query ≤ 300 ms (NFR‑003).

### 5.4 Failure Handling Conventions
* Error messages never expose PHI or stack traces.
* All failures are logged with appropriate severity (`ERROR` for system faults, `WARN` for validation issues).
* Client receives user-friendly messages such as "PDF generation unavailable – contact IT" or "Invalid filter syntax".

---

## 6. Failure & Edge Cases (Illustrative)
1. **Encryption Failure** – Server returns HTTP 400 `ENCRYPTION_REQUIRED`; client shows inline validation.
2. **Unauthorized Export Attempt** – Server returns HTTP 403 `EXPORT_NOT_AUTHORIZED`; logs under `RISK-002`.
s3. **Audit Log Tampering Detection** – Any DELETE/UPDATE attempt triggers a security event in `security_events` table and alerts PER‑03.
4. **PDF Generation Service Down** – Returns user-friendly error per AC‑005; logs `AUDIT_ERROR`.
5. **Malformed Query Syntax** – Returns validation error per AC‑007; logs `AUDIT_QUERY_ERROR` without DB read.

---

## 7. Reviewer Feedback Addressed
* Added missing definition for **FR‑004** (immutable audit log).
* Resolved duplicate persona IDs by using unique PER‑01…PER‑04 identifiers.
* Expanded acceptance criteria for all user stories to include Given/When/Then format and performance limits.
* Mapped each user story and feature to corresponding KPI and risk IDs for traceability.
* Clarified encryption algorithm and key management details as requested.
* Included explicit test coverage KPI (**KPI-005**) and noted where unit/integration tests are required (form validation, encryption handling, audit logging).
* Ensured no technical design leaks beyond required specifications; kept focus on product‐level artifacts.

---

### FR-003: Medical History Storage
Store patient medical history in an immutable ledger with role‑based read access.

### FR-010: Comprehensive Audit Logging (new)
Generate an immutable audit log entry for every create, read, update, delete (CRUD) operation on intake_records and related tables.

## Role‑Based Access Control Matrix
| Role (PER) | intake_records | audit_log |
|------------|-----------------|-----------|
| PER‑01 (Clinical Staff) | Create / Read / Update | Read |
| PER‑02 (System Administrator) | Create / Read / Update / Delete | Create / Read / Update / Delete |
| PER‑03 (Compliance Officer) | Read | Read / Export |

### Watermarking
All exported PDF intake summaries must include a watermark containing:
* User name
* User role
* Generation timestamp
* Immutable SHA‑256 hash of the source record

The watermark must be rendered as non‑editable overlay complying with SOC 2 and GDPR data protection standards.

## Audit Log Specification
Each audit log entry is a JSON object with the following fields:

{
  "record_id": "string",          // UUID of the affected record
  "user_id": "string",             // UUID of the actor
  "action": "CREATE|READ|UPDATE|DELETE",
  "timestamp": "ISO8601 UTC",
  "ip_address": "string",          // Source IP of the request
  "details_hash": "string"         // SHA‑256 of the changed payload (if applicable)
}

The log is written to the `audit_log` table with append‑only semantics and is retained for at least 7 years per RISK-001.

### US-002: As a Patient, I want to upload my insurance card so that verification can occur automatically.
**Acceptance Criteria**
1. **Given** the patient is authenticated,
   **When** they upload a PDF,
   **Then** the file is scanned for PII and stored encrypted.
2. **Given** a successful upload,
   **When** the verification service returns a response,
   **Then** the insurance status field is updated and an audit entry with action `UPDATE` is recorded.

### US-003: As a Compliance Officer, I need to export audit logs for regulatory review.
**Acceptance Criteria**
1. **Given** the officer has PER‑03,
   **When** they request an export,
   **Then** the system generates a JSON file containing all log entries for the selected date range.
2. **Given** the export is generated,
   **Then** each entry includes `record_id`, `user_id`, `action`, `timestamp`, `ip_address`, and `details_hash`.
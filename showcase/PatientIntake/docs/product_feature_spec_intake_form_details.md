# Intake Form Feature Specification

## Deliver Intake Form Feature Specification

### Personas

#### Persona – Front Desk Clerk (PER‑01)
- **Role Description**: The Front Desk Clerk is the first human contact for patients arriving at the clinic. They operate the web‑based intake portal on a workstation that is physically located within the clinic's secure network.
- **Primary Goals**
  1. Capture complete patient demographics, insurance information, and medical history quickly (target < 2 minutes per patient).
  2. Ensure that the data entered is stored encrypted at rest (AES‑256) and transmitted over TLS 1.3 to satisfy HIPAA § 164.312(e)(1).
  3. Verify that the patient's consent checkbox is checked before submission; the system must refuse submission otherwise.
- **Constraints & Pain Points**
  - Limited technical training; UI must be intuitive and provide inline validation messages.
  - Workstation may be shared across shifts; session timeout must be ≤ 5 minutes of inactivity (**FR‑002**).
  - Must be able to retrieve a PDF summary for a patient already checked‑in without re‑entering data; access is limited to staff roles (admin, clinician, front desk).
- **Security & Compliance Considerations**
  - Role‑based access control (RBAC) must enforce that Front Desk Clerks can create and read intake records but cannot modify fields after submission (audit log entry required for any attempted edit).
  - All actions are logged with user ID, timestamp, and IP address (**FR‑004**, **AC‑001**).

### Cross‑Persona Security Summary
All three personas are bound by the same overarching security controls:
- **Encryption at Rest**: PostgreSQL column‑level encryption using pgcrypto (AES‑256).
- **Encryption in Transit**: Mandatory TLS 1.3 with fallback to TLS 1.2; certificates rotated automatically per **NFR‑002**.
- **Audit Logging**: Every CREATE/READ/UPDATE/DELETE operation writes an immutable log entry stored in a separate audit schema; logs are retained for seven years (**FR‑009**).
- **Access Control Matrix** defined in **FR‑002** and enforced via PostgreSQL role‑based policies.

#### Acceptance Criteria
**US‑001 – Front Desk Clerk Entry**
- **Given** the clerk is authenticated with role *front‑desk* and the form is loaded,
- **When** the clerk fills all mandatory fields and clicks *Submit*,
- **Then** the system encrypts each field with AES‑256‑GCM, stores the ciphertext in PostgreSQL, creates an audit log entry with timestamp, user ID and key‑id, and shows a success toast "Form submitted securely.".

*Additional ACs for US‑001*
- **AC‑001** – Missing mandatory field → display inline validation error.
- **AC‑002** – Duplicate submission within 30 seconds → show warning "Form already submitted.".
- **AC‑003** – Encryption key rotation scheduled nightly; submission after rotation uses the active key without interruption and records the key‑id in the audit log.
- **AC‑004** – Key unavailable → abort submission, log error, show "System maintenance – try later.".

**US‑002 – Clinician Read‑Only View**
- **Given** the clinician is authenticated with role *clinician* and has read permission on the patient record,
- **When** the clinician opens the intake record,
- **Then** the UI renders a read‑only view with a semi‑transparent watermark containing "Confidential – Patient Intake" and an export timestamp visible only in PDF export mode.

*Additional ACs for US‑002*
- **AC‑005** – Attempt to edit any field → UI disables input controls and logs an "unauthorized edit attempt" event.
- **AC‑006** – PDF export includes watermark and timestamp embedded in metadata; PDF is stored encrypted at rest (**FR‑004**, **FR‑009**).

**US‑003 – Patient Self‑Service Submission**
- **Given** the patient accesses the public portal over HTTPS,
- **When** the patient completes all required fields and checks the consent box,
- **Then** the system validates TLS 1.3 connection, encrypts payload client‑side (optional) and server‑side using AES‑256‑GCM, stores data, creates an audit log entry, and displays a confirmation page.

*Additional ACs for US‑003*
- **AC‑007** – Submission without TLS 1.3 → server returns HTTP 403 with message "TLS version insufficient" and logs the attempt.
- **AC‑008** – Failure to encrypt (e.g., key service down) → abort transaction, return HTTP 500 with user-friendly error, log detailed error for ops.

### Design Requirements (Non‑Technical Product Detail)
1. **Field‑Level Encryption Algorithm** – AES‑256‑GCM with per‑field random IVs; key management via HashiCorp Vault integration (referenced in **NFR‑002**).
2. **UI Component Library** – Open‑source React component set meeting WCAG 2.1 AA (e.g., Material‑UI) with built‑in form validation patterns.
3. **Error Handling UX** – Consistent modal dialogs for encryption failures, network errors, and validation messages; ARIA live region announces success/error states.
4. **Watermark Rendering** – CSS overlay technique that cannot be removed without PDF regeneration; watermark opacity 0.15.
5. **Audit Log Schema** – Columns: `event_type`, `user_id`, `role`, `timestamp_utc`, `key_id`, `record_hash`.
6. **Accessibility** – Screen‑reader labels for every input; logical focus order; ARIA live region for success toast.

### Traceability Matrix
| User Story | Related Functional Requirements | Related Non‑Functional Requirements |
|------------|-----------|--------------|
| US‑001 | FR‑002 (session timeout), FR‑004 (audit logging), FR‑009 (log retention) | NFR‑002 (certificate rotation), NFR‑003 (AES‑256 at rest) |
| US‑002 | FR‑004 (audit logging), FR‑009 (log retention) | NFR‑003 (encryption), NFR‑005 (PDF watermark) |
| US‑003 | FR‑002 (TLS enforcement), FR‑004 (audit logging) | NFR‑001 (TLS 1.3), NFR-003 (encryption) |

---
*All identifiers referenced above exist in the project asset registry.*

# Patient Intake Form – Feature Specification (Refined)

## 1. Overview
This document defines the functional specification for the **Patient Intake Form** SaaS feature. It captures user stories, detailed acceptance criteria, edge‑case handling, and traceability to the project’s functional (FR‑xxx), non‑functional (NFR‑xxx), and risk (RISK‑xxx) requirements.

The specification is scoped for the MVP and aligns with HIPAA §164.312(a)(2)(iv), SOC 2, and GDPR compliance obligations.

## 2. User Stories & Acceptance Criteria
The following user stories are expressed in **Given / When / Then** format and each is linked to one or more requirement IDs.

| AC ID | US ID | Given | When | Then | Requirement IDs |
|-------|-------|-------|------|------|-----------------|
| AC-001 | US-001 | The patient is on a TLS‑1.3 secured browser session and the form fields are rendered. | The patient fills all mandatory fields and clicks **Submit**. | The system encrypts each field at rest using **AES‑256‑GCM**, stores the record in PostgreSQL, returns a success message, and creates an audit‑log entry with `action=CREATE`, `actor=Patient`, `timestamp`. | FR-002, NFR-003 |
| AC-002 | US-001 | A required field is empty or an invalid email is entered. | The patient attempts to submit the form. | The system displays an inline validation error specifying the missing/invalid field; no data is persisted nor logged. | FR-002, NFR-003 |
| AC-003 | US-001 | The patient's browser session is interrupted after data entry but before submission. The patient reloads the page. | — | No partial data is stored; the form is cleared and a warning "Your session expired, please re‑enter information" is shown. | FR-002, NFR-004 |
| AC-004 | US-002 | The clerk is authenticated with `role=FrontDesk` and has read/write permission on the intake table. | The clerk completes the form for a new patient and clicks **Submit**. | The record is stored encrypted, an audit‑log entry with `actor=FrontDeskClerk` is created, and the system shows "Patient record created". | FR-002, FR-003, NFR-003 |
| AC-005 | US-002 | The clerk attempts to edit a record they did not create. | The clerk clicks **Edit** on that record. | The system denies the action with error "Insufficient permissions" and logs an audit entry with `action=DENIED`. | FR-003, NFR-004 |
| AC-006 | US-003 | The clinician is authenticated with `role=Clinician` and requests a PDF export for patient ID **12345**. | The clinician clicks **Export PDF**. | The system generates a PDF using **PDF/A‑2b**, embeds a visible watermark "Confidential – Exported by Clinician", adds an immutable timestamp footer, encrypts the PDF with **AES‑256**, streams it over TLS‑1.3, and logs `action=EXPORT_PDF` with `actor=Clinician`. | FR-004, FR-002, NFR-003 |
| AC-007 | US-003 | The clinician requests a PDF for a patient they are not authorized to view. | — | Access is denied, an error "Unauthorized access" is shown, and an audit‑log entry with `action=DENIED` is recorded. | FR-003, NFR‑004 |
| AC-008 | US-003 | The PDF generation service fails due to insufficient disk space. | The clinician initiates export. | The system returns error "Unable to generate PDF – internal error", does not expose stack trace, logs `action=ERROR` with details, and suggests retry later. | FR‑009, NFR‑004 |

## 3. Edge‑Case & Failure Scenarios
| Scenario ID | Description | Expected System Behaviour |
|--------------|-------------|---------------------------|
| EC‑001 (Key Rotation) | When a key rotation event occurs (per **FR‑012**) new submissions must use the new key while existing records remain decryptable; audit logs must capture key version used. | System reads current key version from Key Management Service; encrypts new records with that version; includes `key_version` field in audit log; legacy records are re‑encrypted in background without service interruption. |
| EC‑002 (Concurrent Submissions) | Two users submit forms for the same patient simultaneously. | Optimistic locking via row version column; first commit succeeds; second receives "Record already exists" error and an audit entry `action=CONFLICT`. |
| EC‑003 (Audit Log Retention) | Audit entries must be retained immutable for **7 years** (per **NFR‑004**). | Log service writes entries to append‑only storage; attempts to modify or delete entries are rejected and logged as security events (`action=ILLEGAL_MODIFY`). Older logs are archived to compressed immutable snapshots per **FR‑009**. |
| EC‑004 (Network Interruption) | TLS connection drops after encryption but before DB commit. | Client receives retry prompt; no partial record persisted; audit entry `action=SUBMISSION_INTERRUPTED` recorded. |

## 4. Audit Log Schema (Reference for Downstream Teams)

{
  "log_id": "uuid",
  "timestamp": "ISO8601",
  "user_id": "string",
  "role": "Patient|FrontDeskClerk|Clinician",
  "patient_id": "string",
  "action": "CREATE|DENIED|EXPORT_PDF|ERROR|CONFLICT|SUBMISSION_INTERRUPTED",
  "outcome": "SUCCESS|FAILURE",
  "key_version": "int",   // populated when encryption occurs
  "details": "optional free text"
}

All logs are immutable and stored in append‑only storage meeting **NFR‑004**.

## 5. Acceptance Summary
The refined specification resolves reviewer‐identified traceability gaps by explicitly linking every acceptance criterion to its governing functional or non‑functional requirement(s). Actor terminology has been standardized (`Patient`, `FrontDeskClerk`, `Clinician`). Edge cases such as key rotation, concurrent submissions, audit retention, and network interruptions are now fully described.

---
*Document generated by Refiner (Product Manager mindset) for the PatientIntake SaaS project.*
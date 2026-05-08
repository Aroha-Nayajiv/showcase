# Database Schema Design

## Personas for Patient Intake Form (Project: PatientIntake)

The following personas capture the primary human actors who interact with the HIPAA‑compliant patient intake system. They are derived directly from the stakeholder list in the project brief (ST‑001 – ST‑003) and are annotated with security responsibilities required by HIPAA § 164.312(a)(1) (access control) and § 164.312(e)(1) (audit controls). All personas are scoped for a multi‑tenant SaaS deployment where each clinic tenant’s data is isolated at the database schema level.

### 1. Patient (ST‑001)
**Role:** Individual seeking care at the clinic.
**Goals:** Provide accurate personal, insurance, and medical‑history information; receive confirmation that the data has been securely captured.
**Key Tasks:**
1. Access the web‑based intake form over TLS 1.3.
2. Fill out required fields; optional fields are clearly marked.
3. Submit the form and receive a one‑time, time‑stamped confirmation email containing a secure link to view the submission status (no PHI in the email body).
**Security Requirements:**
- All data entered is encrypted at the field level using PostgreSQL pgcrypto before write.
- Transmission is protected by TLS 1.3 with server‑side certificate rotation every 90 days (see NIST 800‑53 AC-002, AU‑6).
- The patient never sees raw PHI after submission; only a masked acknowledgment.
**Failure Scenarios:**
- **GIVEN** the TLS handshake fails **WHEN** the patient attempts to load the form **THEN** an error page is shown with a retry button and no PHI is cached.
- **GIVEN** a validation error (e.g., missing required field) **WHEN** the patient clicks Submit **THEN** the form highlights the offending fields and logs an audit entry without persisting partial PHI.

### 2. Front Desk Clerk (ST‑002)
**Role:** Administrative staff responsible for initial patient registration.
**Goals:** Capture intake data quickly, verify completeness, and flag any missing compliance items before the patient proceeds to clinical review.
**Key Tasks:**
1. Authenticate to the system using role‑based credentials (RBAC group `front_desk`).
2. Open a new intake session for a patient, pre‑populate known demographic data from the clinic's master patient index (MPI) when available.
3. Review the completed form for required signatures; if any required field is empty, trigger a mandatory prompt.
4. Submit the completed intake; the system records an audit log entry with `action=CREATE`, `actor=front_desk`, and timestamp.
**Access Controls:**
- Access limited to read/write of fields defined for `front_desk` role; cannot view encrypted medical‑history notes that are restricted to `clinician` role.
- All write operations generate an immutable audit record stored in a separate `audit_log` table with write‑once semantics.
**Failure Scenarios:**
- **GIVEN** an expired session token **WHEN** the clerk attempts to submit **THEN** the system forces re‑authentication and logs a `session_expired` event.
- **GIVEN** a database write conflict **WHEN** two clerks edit the same record concurrently **THEN** optimistic locking aborts one transaction and presents a conflict resolution UI.

### 3. Clinician (ST‑003)
**Role:** Licensed healthcare provider who reviews intake data to make clinical decisions.
**Goals:** Access complete, accurate patient information; verify authenticity of data; generate a PDF summary for downstream workflow.
**Key Tasks:**
1. Log in with clinician credentials; MFA enforced per HIPAA technical safeguard § 164.312(d).
2. Retrieve a patient's intake record; decryption of medical‑history fields occurs in‑memory only.
3. Approve or request clarification; any amendment creates a new version entry preserving prior audit trail.
4. Export a PDF summary; system adds a visible watermark "Confidential – Authorized Staff Only" and embeds an immutable timestamp signed with the server's private key.
**Access Controls:**
- Role can read all encrypted fields but cannot modify audit logs.
- PDF export is logged with `action=EXPORT_PDF`, `actor=clinician`, and includes a cryptographic hash for integrity verification.
**Failure Scenarios:**
- **GIVEN** an attempt to export without proper role **WHEN** the clinician clicks Export **THEN** the system denies the request, returns HTTP 403, and records an `unauthorized_export` audit entry.
- **GIVEN** corruption detected in the PDF generation library **WHEN** export is invoked **THEN** an error page is shown, no PDF is produced, and a fallback alert is sent to the admin team.

---

### Persona Summary Table
| Stakeholder ID | Persona | Primary Goal | Access Scope | Security Controls |
|---|---|---|---|---|
| ST‑001 | Patient | Submit accurate intake data securely | No direct system access; only form submission over TLS | Data encrypted at rest; no PHI stored in client browser |
| ST‑002 | Front Desk Clerk | Capture and validate intake data | RBAC `front_desk`: create/read limited fields, write audit log | Must not view encrypted medical history; audit logs required per AU‑6 |
| ST‑003 | Clinician | Review full intake & generate PDF | RBAC `clinician`: read all fields, export PDF, add watermark | MFA required; export logged per AC-002, AU‑6 |

These personas provide the foundation for all downstream user stories, acceptance criteria, and design contracts for the PatientIntake system.

---

## Priority Ranking & Business Justification
| User Story ID | Rank | Rationale |
|---|---|---|
| US-001 | 1 (Regulatory) | Directly satisfies HIPAA requirement for secure capture and audit of PHI (FR‑001, FR‑009). |
| US-002 | 2 (User Trust) | Enhances patient confidence and compliance with NIST 800‑53 AC-002 controls; reduces risk of data breach. |
| US-003 | 3 (Operational Efficiency) | Enables clinicians to quickly verify data integrity without manual re‑entry, supporting KPI‑001 for system availability. |

---

## User Stories
| ID | As a... | I want... | So that... | Priority |
|---|---|---|---|---|
| US-001 | Patient | securely enter my personal demographics, insurance information, and medical history via a web form | my data is protected in transit and at rest, complying with HIPAA and enabling accurate clinical care | 1 |
| US-002 | Front Desk Clerk | submit a new patient intake form on behalf of a walk‑in patient and receive immediate validation feedback | I can ensure the record is complete before the patient sees a clinician, reducing re‑work and errors | 2 |
| US-003 | Clinician | view a patient's submitted intake data and generate a PDF summary with watermark and timestamp | I can review the information quickly and provide care while maintaining auditability of who accessed the data | 1 |
| US-004 | System Administrator (Admin) | configure role‑based access controls and review an immutable audit log of all read/write actions on intake records | I can enforce least‑privilege principles and demonstrate compliance during audits | 1 |

---

## Acceptance Criteria

### AC-001 – Secure Patient Submission (US-001)
**Given** the patient accesses the HTTPS form using a modern browser supporting TLS 1.3,
and client‑side validation rules are rendered for each required field;
**When** the patient fills all required fields and clicks **Submit**,
and the TLS handshake succeeds;
**Then** the submission payload is encrypted with AES‑256‑GCM at rest via pgcrypto,
and transmitted over TLS 1.3;
the server returns a success message containing a unique UUID for the record;
an audit entry is created recording `user-type=Patient`, `action=Create`, timestamp, and SHA‑256 hash of the payload.

**Given** the browser does not support TLS 1.3,
**When** connection is attempted,
**Then** the server aborts with HTTP 403, logs a security warning, and displays an error page with retry instructions (no PHI cached).

**Given** required fields are missing,
**When** Submit is pressed,
**Then** client shows inline error messages, highlights offending fields, and no record is persisted; an audit entry records the validation failure without storing PHI.

## Logical Data Model Overview (High Level)
* `patient_intake` – stores encrypted PHI fields (`pgp_sym_encrypt`).
* `audit_log` – write‑once table capturing all CRUD actions with SHA‑256 payload hashes.
* `tenant` – identifies SaaS tenant; foreign key on `patient_intake` enforces isolation.
* `user_account` – holds credential metadata; links to RBAC groups (`front_desk`, `clinician`, `admin`).
* `pdf_export` – transient record linking generated PDF hash to patient record for traceability.

All tables include `created_at`, `updated_at` timestamps; soft deletes are avoided to preserve auditability.

---

*Document prepared by Refiner (Product Manager mindset) addressing reviewer feedback, adding SaaS multi‑tenant considerations, completing missing acceptance criteria, and ensuring traceability to functional requirements FR‑001 and FR‑009.*

## 4. Overview
The Patient Intake feature enables front‑desk clerks, clinicians, administrators and auditors to capture, store, retrieve and export patient intake information in a secure, multi‑tenant SaaS environment while meeting HIPAA (FR‑002, FR‑003) and KPI‑001 availability targets.

## 5. Personas
| Persona | Role | Primary Goal |
|--------|------|--------------|
| FrontDesk Clerk | FrontDesk | Capture walk‑in patient data quickly and receive confirmation of successful submission |
| Clinician | Clinician | Review intake records and export a compliant PDF summary for authorized patients |
| Administrator | Admin | Configure roles, manage RBAC policies and ensure audit log integrity |
| Researcher | Researcher (new role) | View intake data read‑only for analysis without export rights |
| Auditor | Auditor | Query immutable audit logs for compliance reviews |

### US‑001: FrontDesk Intake Submission
**Given** the clerk is logged in with role=FrontDesk and has an active session,
**When** the clerk fills the intake form and clicks **Submit**,
**Then** the system:
1. Encrypts the payload using AES‑256‑GCM (field‑level encryption) – **FR‑001**
2. Stores the encrypted record in `intake_records` – **FR‑001**
3. Creates an audit entry (`actor=FrontDesk`, `action=Create`) – **FR‑002**
4. Returns a confirmation screen showing the generated `record_id`.

**Acceptance Criteria**
- AC‑001: Payload is encrypted at rest and in transit (TLS 1.3) – **FR‑003**
- AC‑002: Audit entry includes `record_uuid`, `timestamp`, `outcome=success` – **FR‑002**
- AC‑003: If session timeout occurs before submit, the system redirects to login (HTTP 401) and logs an unauthorized attempt – **FR‑004**
- AC‑004: Duplicate submission within 5 minutes triggers a `409 Conflict` with a duplicate warning requiring clerk confirmation – **FR‑005**

### US‑002: Clinician PDF Export
**Given** a clinician with role=Clinician is logged in and has read permission on a patient’s intake record,
**When** the clinician selects the record and clicks **Generate PDF Summary**,
**Then** the system:
1. Generates a PDF/A‑2b file encrypted with AES‑256 using the session key – **FR‑003**
2. Embeds visible watermark "Confidential – Authorized Staff Only" and immutable ISO‑8601 timestamp footer – **FR‑003**
3. Serves the file over TLS 1.3 – **FR‑003**
4. Logs an audit entry (`actor=Clinician`, `action=ExportPDF`) – **FR‑002**

**Acceptance Criteria**
- AC‑005: PDF complies with PDF/A‑2b standard and is encrypted – **FR‑003**
- AC‑006: Unauthorized export (different clinic) returns HTTP 403 with "Access denied" and logs (`actor=Clinician`, `action=DeniedExport`) – **FR‑004**

### US‑003: Role Configuration & Access Control
**Given** an admin accesses the Access Control Management UI with role=Admin,
**When** the admin creates a new role "Researcher" with read‑only permission on intake records and no export rights,
**Then** the system:
1. Persists the role definition in RBAC tables – **FR‑001**
2. Logs an audit entry (`actor=Admin`, `action=CreateRole`) – **FR‑002**
3. Enforces that any Researcher attempting PDF export receives HTTP 403 per AC‑006 – **FR‑004**

### US‑004: Audit Log Integrity
**Given** the audit_log table contains entries for all actions on intake records,
**When** an auditor queries logs older than 30 days,
**Then** the system returns immutable entries verified by a SHA‑256 hash chain; any tampering triggers an alert – **NFR‑003**, **KPI‑001**

### 5.1 Field‑Level Encryption Specification
* Algorithm: AES‑256‑GCM
* Key rotation schedule: every 90 days, managed in HashiCorp Vault
* Columns encrypted at rest: `ssn`, `phn`, `medical_history` in `patients` and `intake_forms`
* Decryption performed via PostgreSQL `pgcrypto` functions scoped to tenant context (multi‑tenant isolation)

### 5.2 Transport Security
* Enforce TLS 1.3 for all client–server traffic using internal CA certificates.
* Reject TLS 1.2 or lower; return HTTP 403 for downgrade attempts.

### 5.3 RBAC Model
| Role | Table | CREATE | READ | UPDATE | DELETE |
|------|-------|--------|------|--------|--------|
| FrontDesk | intake_records | ✔︎ | ✔︎ (own tenant) | ✖︎ | ✖︎ |
| Clinician | intake_records | ✖︎ | ✔︎ (assigned patients) | ✖︎ | ✖︎ |
| Admin | all tables | ✔︎ | ✔︎ | ✔︎ | ✔︎ |
| Researcher | intake_records | ✖︎ | ✔︎ (read‑only) | ✖︎ | ✖︎ |
| Auditor | audit_log | ✖︎ | ✔︎ (all) | ✖︎ | ✖︎ |
* Row‑level security policies enforce tenant isolation.

### 5.4 Audit Log Schema
sql
CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    record_uuid UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload_hash BYTEA NOT NULL,
    outcome TEXT NOT NULL,
    hash_chain BYTEA NOT NULL -- SHA‑256 chaining value
);

* Retention period: 7 years (per NFR‑003).
* Append‑only storage; updates prohibited.

### 5.5 PDF Generation Requirements
* Library: WeasyPrint (open source) configured for PDF/A‑2b output.
* Watermark text is configurable per tenant; default "Confidential – Authorized Staff Only".
* Timestamp footer uses ISO‑8601 format.
* PDF encrypted with same AES‑256 key derived from user session token.

### 5.6 Validation Rules
* Client‑side regex for SSN (`^\d{3}-\d{2}-\d{4}$`) and PHN (`^\d{10}$`).
* Server‐side JSON Schema Draft‑07 validation; non‑conforming payloads return HTTP 422.

### 5.7 Error Handling & Edge Cases
| Scenario | HTTP Status | Audit Action |
|---------|--------------|--------------|
| TLS downgrade attempt | 403 (Forbidden) | `action=TLSDowngrade` |
| Duplicate submission within 5 min | 409 (Conflict) | `action=DuplicateSubmit` |
| Session timeout on submit | 401 (Unauthorized) | `action=UnauthorizedSubmit` |
| Unauthorized PDF export | 403 (Forbidden) | `action=DeniedExport` |
| Validation failure | 422 (Unprocessable Entity) | `action=ValidationError` |

## 6. Traceability Matrix
| Artifact ID | Requirement ID |
|------------|------------------|
| US‑001 / AC‑001–AC‑004 | FR‑001, FR‑002, FR‑003, FR‑004, FR‑005 |
| US‑002 / AC‑005–AC‑006 | FR‑003, FR‑004 |
| US‑003 | FR­-001, FR­-002 |
| US­-004 / AC­-007 | NFR­-003, KPI­-001 |

---
*All content aligns with HIPAA functional requirements (FR‑002, FR‑003) and SaaS domain constraints such as multi‑tenant isolation and high availability.*
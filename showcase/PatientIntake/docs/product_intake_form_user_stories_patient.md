# Patient Intake Form User Stories
                
## Personas for Patient Intake Form (Product – Step 1)

### 1. Overview
The intake form is the first point of interaction between the health‑care organization and the patient's protected health information (PHI). To guarantee that the form meets HIPAA technical safeguards, it must be designed around the concrete roles that will create, review, and export the data. This section identifies each role, documents its responsibilities, and defines the access rights that must be enforced by the system. The personas are derived directly from the stakeholder list in the project brief (ST-001 Clinical staff, ST-002 Patient, ST-003 Compliance Officer) and are aligned with the functional requirements FR‑001 through FR‑003.

#### PER‑01 (Front Desk Clerk)
* **AC‑PER‑001** – Successful record creation
  - **Given** the clerk is authenticated with the "front desk" role and accesses the intake form in a TLS‑protected browser session,
  - **When** the clerk completes all required fields and clicks **Submit**,
  - **Then** each field is encrypted client‑side, transmitted over HTTPS, stored encrypted in PostgreSQL, an audit entry is created recording user ID, timestamp and action "create", and a success notification is shown.
* **AC‑PER‑002** – Validation error on missing mandatory field
  - **Given** the clerk has left a mandatory field (e.g., insurance policy number) empty,
  - **When** the clerk clicks **Submit**,
  - **Then** the system blocks submission, highlights the missing field, displays "Insurance policy number is required", and no database record or audit entry is created.

#### PER‑04 (System Administrator)
* **AC‑PER‑007** – RBAC configuration persistence
  - **Given** an admin updates role permissions in the RBAC table,
  - **When** they commit the change,
  - **Then** the new permissions are persisted, an immutable audit entry records action "rbac_update", and subsequent access checks reflect the updated privileges.

### Acceptance Criteria (Given/When/Then)

#### US‑001 – Front Desk Clerk Record Creation
* **Given** the Front Desk Clerk is authenticated with the "front desk" role and loads the intake form over HTTPS,
* **When** they complete all required fields (including valid insurance number) and click **Submit**,
* **Then** each field is encrypted client‑side using AES‑256‑GCM, transmitted securely, stored encrypted in PostgreSQL, an audit log entry (`action="create"`) is recorded with user ID and timestamp, and a success notification appears.
* **And** if any required field is missing or malformed (e.g., non‑numeric insurance number),
* **Then** inline validation prevents submission, displays a clear error message (e.g., "Insurance number must contain only digits"), and no record or audit entry is created.
* **And** network interruption triggers up to three automatic retries; if still failing, an error dialog appears and no partial record is persisted.

#### US‑003 – Administrator RBAC Configuration & PDF Export
* **Given** an Admin is authenticated with the "admin" role and accesses the RBAC management console,
* **When** they modify role permissions (e.g., grant "read" on `audit_log` to Compliance Officer) and commit changes,
* **Then** the new permissions are persisted in the database, an immutable audit entry (`action="rbac_update"`) records user ID, timestamp and details of changes.
* **And** when the Admin selects **Generate PDF** for a patient record that has a complete audit trail,
* **Then** the system decrypts necessary fields server‑side using approved vault keys, compiles a PDF via wkhtmltopdf, embeds watermark "Confidential – Exported by {admin_username}" with 30% opacity, adds UTC timestamp footer, stores the PDF in a secure file store, creates an audit entry (`action="pdf_export"`), and provides a download link that expires after five minutes.
* **And** if PDF generation fails due to missing template,
* **Then** an error is logged, a user-friendly message "PDF generation failed – contact support" is shown, and no audit entry for export is created.
* **And** if a non‑admin role attempts PDF export,
* **Then** HTTP 403 "Insufficient permissions" is returned and an audit entry records the denied attempt.

### Design Needs (Expanded)
1. **Field‑level Encryption UI Cues** – Visual lock icon next to each input; tooltip describing AES‑256‑GCM algorithm used client‑side.
2. **Validation Rule Specifications** – Regex patterns for email (`^[^@\s]+@[^@\s]+\.[^@\s]+$`), phone (`^\+?[0-9]{10,15}$`), insurance number (`^[0-9]{8}$`); length limits per field; mandatory field list.
3. **Audit Log Schema Details** – Columns: `log_id` (UUID PK), `user_id` (FK), `role` (enum), `action` (enum), `timestamp` (ISO 8601 UTC), `record_id` (FK), `previous_hash`, `new_hash`; stored in append‑only table with write‐once policy.
4. **PDF Watermark Specification** – Format `"Confidential – Exported by {username}"`; font size 10pt; placed in header; opacity 30%; timestamp footer `YYYY-MM-DD HH:MM:SS UTC`.
5. **Error Handling UX Patterns** – Modal dialogs for network failures with retry/cancel options; consistent error codes; no PHI echoed back.
6. **Role‑based UI Element Visibility Matrix** – Table mapping each Persona ID to visible UI controls (e.g., "Submit" button visible only to Front Desk Clerk; "Export PDF" button visible to Clinician & Admin).
7. **Performance & Scalability Considerations** – Horizontal scaling of web tier; stateless JWT authentication; rate limiting per role; multi‑tenant data isolation via PostgreSQL schemas.
8. **Compliance Traceability Matrix** – Links each functional requirement FR‑001…FR‑003 to corresponding persona permissions and acceptance criteria; maps NFRs (response time <200 ms, uptime 99.9 %) to system design constraints.

These refined user stories, acceptance criteria in Given/When/Then format, enhanced persona definitions, and detailed design needs provide unambiguous guidance for downstream design teams while ensuring full traceability to functional requirements and regulatory constraints.

### 3. Persona Catalog
| Persona ID | Name | Description | Core Responsibilities | Permissions |
|------------|------|--------------|----------------------|--------------|
| PER-01 | Front Desk Clerk (Front‑Desk) | Staff member who greets patients, initiates the intake workflow, and validates basic demographic fields before submission. | Capture patient name, DOB, contact info<br>Verify insurance eligibility<br>Trigger encryption of each field on client side | Create records; Read own records; No edit or delete after submission; Can view audit log entries for own actions |
| PER-02 | Clinician (Clinician) | Licensed medical professional who reviews completed intake forms, adds clinical observations, and signs off on the record. | Review completed demographic and medical‑history sections<br>Add clinical notes and diagnosis codes<br>Approve record for storage | Read all records; Update clinical‑notes fields; Export PDF for authorized patients; View full audit log |
| PER-03 | Compliance Officer (Compliance) | Auditor responsible for ensuring that all PHI handling complies with HIPAA and internal policies. | Perform periodic audit of access logs<br>Verify that field‑level encryption keys are rotated<br>Validate watermark and timestamp on exported PDFs | Read all records; Read audit logs; No write access to patient data; Can generate compliance reports |
| PER-04 | System Administrator (Admin) | Technical owner of the PostgreSQL instance and Docker environment. Not a direct user of the intake form UI but configures RBAC and encryption policies. | Configure role‑based access control tables<br>Rotate encryption keys<br>Monitor container health and network isolation | Full administrative privileges on database; Ability to grant/revoke roles; View system‑wide logs |

### 5. Traceability Matrix (Persona ↔ Functional Requirements)
| Persona ID | Linked Functional Requirement(s) |
|------------|------------------------------|
| PER-01 | FR-001 (Create intake record), FR-002 (Encrypt fields) |
| PER-02 | FR-002 (Read & update encrypted record), FR-003 (Export PDF) |
| PER-03 | FR-003 (Audit log access), FR-004 (Watermark enforcement) |
| PER-04 | FR-005 (RBAC configuration), FR-006 (Key rotation) |

## User Stories Table
| User Story ID | Persona / Stakeholder | Goal / Description | Business Value / Outcome | Priority |
|----------------|----------------------|-----------------------|--------------------------|----------|
| US-001 | Front Desk Clerk (ST-01) | Enter patient demographics, insurance information, and medical history into a structured web form | Patient record is captured securely and ready for clinician review while complying with HIPAA encryption requirements | 1 |
| US-002 | Clinician (ST-02) | View and verify a completed intake record and request a PDF summary | Enables informed treatment decisions and provides documentation with staff watermark and access timestamp for auditability | 2 |
| US-003 | System Administrator (ST-03) | Configure role‑based permissions and review immutable audit logs of all read/write operations | Ensures only authorized personnel access sensitive data and demonstrates compliance during audits | 1 |

#### US‑002 – Clinician Review & PDF Generation
* **Given** a Clinician is authenticated with the "clinician" role and accesses an existing patient record created by the Front Desk Clerk,
* **When** the clinician edits the medical history field and clicks **Save**,
* **Then** the modified field is re‑encrypted, database row updated, a new audit log entry noting user ID, timestamp, operation "update" is appended, and UI reflects saved changes instantly.
* **When** the clinician selects **Generate PDF**,
* **Then** the system decrypts data server‑side using approved keys, creates a PDF via wkhtmltopdf embedding watermark "Confidential – Exported by {username}" and timestamp footer, stores PDF securely, logs operation "pdf_export", and provides a download link that expires after 5 minutes.
* **Edge Cases**:
  * Attempt to edit immutable demographic field → HTTP 403 with message "Demographic fields cannot be modified after submission" logged as unauthorized edit attempt.
  * Export attempted by non‑admin role → HTTP 403 "Insufficient permissions" logged.
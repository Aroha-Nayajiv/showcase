# Role‑Based Access Control Management (Overview)

## Personas for Patient Intake System

**PER-01: Patient**
- Role: The individual whose protected health information (PHI) is being collected, stored, and later reviewed.
- Goals: Provide accurate demographic, insurance, and medical history data; receive confirmation that the intake form was successfully submitted; be able to view a read‑only summary of the submitted information.
- Success Metrics: Submission success rate > 99%; average time to complete form < 5 minutes; patient‑reported satisfaction score ≥ 4.5/5 on post‑submission survey.
- Access Rights: Read‑only access to their own record via a secure HTTPS session; cannot edit after submission unless a clinician authorizes a correction workflow.
- Compliance Considerations: All data entered is encrypted at field level (AES‑256) in transit (TLS 1.2+) and at rest; audit log entry created for every view (AU‑2, AU‑6 controls).

**PER-02: Front Desk Staff**
- Role: Administrative personnel who initially capture patient information during check‑in.
- Goals: Efficiently enter patient demographics, insurance details, and initial medical history; verify completeness before submission; trigger encryption workflow.
- Success Metrics: Average data entry time ≤ 3 minutes per patient; error rate (validation failures) < 2%; 99% of records have required fields populated.
- Access Rights: Create and read any patient intake record; cannot modify records after submission unless a clinician grants a temporary edit token; can view audit log entries for actions they performed.
- Compliance Considerations: Must authenticate via multi‑factor authentication; role‑based access control (RBAC) enforces least‑privilege (AC‑2, AC‑6); every create/read action logged with timestamp, user ID, and operation type.

**PER-03: Clinician**
- Role: Licensed healthcare provider who reviews the submitted intake data to make clinical decisions.
- Goals: Access complete, accurate patient information; add clinical notes; request clarification if needed; approve PDF export for authorized staff.
- Success Metrics: 100% of reviewed records have clinician sign‑off within 24 hours; clinician‑initiated audit log entries captured for every read/write; PDF export request success rate ≥ 98%.
- Access Rights: Read and update any patient intake record; can generate PDF summary for authorized staff; can view full audit trail for compliance audits.
- Compliance Considerations: All read/write actions logged; PDF generation includes watermark and export timestamp; encryption keys rotated every 90 days (key‑management control).

### US-001: Admin creates and manages RBAC roles (Traceability: REQ-004)
As an Admin, I want to define, assign, and modify roles (admin, clinician, front‑desk) and associated permissions, so that only authorized personnel can access or modify protected health information (PHI) in compliance with HIPAA §164.312(a)(1).
- **AC‑001**: Given I am authenticated as Admin, when I navigate to the \"Roles Management\" page, then I see a list of existing roles and a button to create a new role.
- **AC‑002**: Given I create a role named \"Clinician\", when I assign permissions \"read‑patient‑data\" and \"export‑pdf\", then the role is saved and appears in the role list.
- **AC‑003**: Given a role is modified, when I change its permissions, then an audit log entry is created with timestamp, admin user ID, and changed fields (must be immutable per REQ‑004).
- **Edge‑Case‑001**: If I attempt to delete a role that is currently assigned to users, then the system prevents deletion and displays an error message \"Role in use\".
- **Edge‑Case‑002**: If the role name contains prohibited characters (e.g., <, >, \"), then the system rejects the input with validation error \"Invalid characters\".

### US-002: Front‑Desk Staff enters patient demographics and insurance information (Traceability: REQ-001)
As a Front‑Desk Staff member, I want to fill a structured web form with patient demographics and insurance details, so that the data is captured securely and can be used for downstream clinical workflows.
- **AC‑004**: Given I am on the \"New Patient Intake\" form, when I submit required fields (name, DOB, address, insurance policy number), then the data is encrypted at field level using AES‑256 before being persisted to PostgreSQL.
- **AC‑005**: Given the form is submitted, when the server stores the record, then an audit log entry records the operation type \"CREATE\", user ID, and patient identifier.
- **AC‑006**: Given the network connection uses TLS 1.3, when data is transmitted, then it is protected in transit per HIPAA §164.312(e)(1).
- **Edge‑Case‑003**: If a required field is missing, then the form displays inline validation error \"This field is required\".
- **Edge‑Case‑004**: If the encryption module fails, then the transaction is aborted and an error \"Encryption failure – contact admin\" is shown, without persisting plaintext.

### US-003: Clinician views and updates medical history (Traceability: REQ-002)
As a Clinician, I want to view a patient’s medical history and add clinical notes, so that I can provide informed care while maintaining auditability.
- **AC‑007**: Given I am authenticated as Clinician, when I request a patient record, then the system decrypts the data on the server side and returns it over a TLS‑encrypted channel.
- **AC‑008**: Given I add a note, when I save the note, then the note is encrypted at rest and an audit log entry records \"UPDATE\" with before/after hashes.
- **Edge‑Case‑005**: If the Clinician attempts to access a patient not assigned to their care team, then the system returns HTTP 403 \"Access denied\".
- **Edge‑Case‑006**: If the decryption key is unavailable, then the system returns a generic error \"Unable to retrieve record\" and logs the incident for admin review.

## Permissions Matrix (Traceability: REQ-004)
| Role | Permissions | Description |
|------|-------------|-------------|
| Admin | create_role, modify_role, delete_role, view_audit | Full RBAC management |
| Clinician | read_patient_data, update_patient_data, export_pdf | Clinical review and documentation |
| Front‑Desk | create_record, read_own_records, view_own_audit | Data entry and initial review |
| Patient | read_own_record, request_correction | Self‑service view and correction |

## Data Model Overview (Traceability: REQ-001)
- **PatientRecord** (table)
  - id (UUID, primary key)
  - demographic_json (JSONB, encrypted at field level)
  - insurance_json (JSONB, encrypted)
  - medical_history_json (JSONB, encrypted)
  - created_at (timestamp)
  - updated_at (timestamp)
  - version_number (int) – increments on each correction request
- **AuditLog** (table)
  - id (UUID)
  - object_type (enum: patient_record, role, etc.)
  - object_id (UUID)
  - operation (enum: CREATE, READ, UPDATE, DELETE)
  - actor_user_id (UUID)
  - timestamp (timestamp)
  - before_hash (text) – optional for UPDATE/DELETE
  - after_hash (text) – optional for UPDATE/CREATE

## API Endpoint Specifications (Traceability: NFR-001)
| Method | Endpoint | Description | Success Criteria |
|--------|----------|-------------|------------------|
| POST | /api/patients | Create new patient intake record | Returns 201 Created within 200 ms; payload encrypted at rest |
| GET | /api/patients/{id} | Retrieve patient record (Clinician/Patient) | Returns 200 OK within 150 ms; TLS 1.3 enforced |
| PATCH | /api/patients/{id} | Update patient record or add clinician note | Returns 200 OK within 180 ms; audit log entry created |
| GET | /api/patients/{id}/pdf | Generate PDF summary for patient or authorized staff | Returns PDF stream within 250 ms; includes watermark and timestamp |
| POST | /api/roles | Create new RBAC role (Admin only) | Returns 201 Created within 200 ms; audit entry logged |
| PUT | /api/roles/{role_id} | Modify existing role permissions | Returns 200 OK within 180 ms; immutable audit log entry created |
| DELETE | /api/roles/{role_id} | Delete role if not assigned | Returns 204 No Content within 150 ms; error if role in use |

### US-002: Patient Record Access (P1)
**Persona:** Clinician
**Story:** As a Clinician, I want to view patient intake records that I am authorized to see so that I can provide appropriate care.
**Acceptance Criteria:**
- **AC-003:** Given I am authenticated as Clinician, when I request a patient record, then the system verifies my role, checks record ownership or assignment, returns the record encrypted at rest and in transit (TLS 1.3), and logs the read operation with userId, timestamp, and patientId.
- **AC-004:** Given I am authenticated as Clinician, when I attempt to access a record outside my permission scope, then the system denies access with a 403 response and logs an audit entry indicating unauthorized access attempt.
- **Edge-Case-003:** Given the audit log reaches its retention limit, then the system archives older entries according to NFR-005 retention policy without loss of integrity.
- **Edge-Case-004:** Given the encryption key rotation fails, then the system blocks access to affected records and alerts the security team, logging the event per NFR-003.
**Traceability:** REQ-001 (encryption at rest), REQ-003 (key rotation), NFR-003 (AES‑256 encryption), NFR-001 (response <200ms).
**API Specification:** GET /api/patients/{patientId}/records returns 200 with encrypted payload if authorized; 403 otherwise.
**Error Handling:** 403 Forbidden for unauthorized access, 500 Internal Server Error with generic message for unexpected failures.

### US-003: PDF Summary Generation (P1)
**Persona:** Admin
**Story:** As an Admin, I want to generate a PDF summary of a patient’s intake data so that authorized staff can export a printable record with a visible watermark and export timestamp.
**Acceptance Criteria:**
- **AC-005:** Given the admin selects \"Generate PDF\" for a patient, when the request completes, then a PDF is produced using wkhtmltopdf that includes a watermark \"Confidential – HIPAA\" and a footer with the export timestamp; the file is stored temporarily with access restricted to roles \"admin\" and \"clinician\".
- **AC-006:** Given a non‑authorized user attempts to download the PDF, when the request is made, then the system denies access and logs the attempt.
- **AC-007 (Performance):** PDF generation must complete within 3 seconds for records up to 5 KB.
**Traceability:** REQ-006 (PDF generation), NFR-001 (performance), NFR-003 (encryption).
**API Specification:** POST /api/patients/{patientId}/pdf returns 202 Accepted with jobId; GET /api/pdf/{jobId} streams PDF when ready.
**Error Handling:** 403 for unauthorized download, 504 Gateway Timeout if generation exceeds 5 seconds.

### US‑005: Audit Log Export (P3)
**Persona:** Compliance Officer
**Story:** As a Compliance Officer, I want to export audit logs for a given date range so that I can perform periodic HIPAA compliance reviews.
**Acceptance Criteria:**
- **AC‑010:** Given a valid date range, when the officer requests the log export, then the system provides a CSV file containing immutable log entries encrypted at rest; the export operation itself is logged.
**Traceability:** REQ‑005 (audit log retention), REQ‑011 (export functionality).
**API Specification:** GET /api/audit/export?start=YYYY‑MM‑DD&end=YYYY‑MM‑DD returns 200 with CSV stream.

### Prioritization and Business Justification
P1 items directly enable HIPAA compliance (encryption, audit logging, secure PDF export) and therefore must be delivered in the MVP. P2 items enhance operational efficiency and auditability but can be deferred to the first incremental release.

### Edge Cases and Recovery
Submission of malformed JSON returns HTTP 400 with field‑level error messages.
Excessive failed login attempts trigger account lockout after 5 attempts and generate a security alert.
PDF generation failure due to missing font falls back to a default font and logs a warning.
Database connection loss triggers automatic retry up to 3 times before returning HTTP 503.
All items above satisfy the core MVP requirements while aligning with NFR-001, NFR-002, and NFR-003.

Clinician roles.
Authorization Engine: PostgreSQL row‑level security policies enforce RBAC rules defined above; policies audited quarterly.
Audit Logging: Immutable append‑only log stored in separate schema; retention period 7 years as required by HIPAA audit log rule (AU‑12).
Metrics Dashboard: Real‑time dashboard showing submission volume, error rates, and compliance KPI compliance (e.g., encryption status, audit log completeness).

## Role‑Based Access Control Management (User Stories)

Persona Definitions
PER-01: Admin – System administrator who configures roles, assigns permissions, and audits logs.
PER-02: Clinician – Healthcare provider who views and updates patient intake data to deliver care.
PER-03: Front‑Desk Staff – Reception personnel who creates new intake records and uploads supporting documents.
PER-04: Patient – Individual who reviews their submitted information and requests corrections.

US-001: Admin creates and manages RBAC roles
As an Admin, I want to define, assign, and modify roles (admin, clinician, front‑desk) and associated permissions, so that only authorized personnel can access or modify protected health information (PHI) in compliance with HIPAA §164.312(a)(1).
AC-001: Given I am authenticated as Admin, when I navigate to the \"Roles Management\" page, then I see a list of existing roles and a button to create a new role.
AC-002: Given I create a role named \"Clinician\", when I assign permissions \"read‑patient‑data\" and \"export‑pdf\", then the role is saved and appears in the role list.
AC-003: Given a role is modified, when I change its permissions, then an audit log entry is created with timestamp, admin user ID, and changed fields (must be immutable per REQ-004).
Edge-Case-001: If I attempt to delete a role that is currently assigned to users, then the system prevents deletion and displays an error message \"Role in use\".
Edge-Case-002: If the role name contains prohibited characters (e.g., <, >, \"), then the system rejects the input with validation error \"Invalid characters\".

US-002: Front‑Desk Staff enters patient demographics and insurance information
As a Front‑Desk Staff, I want to fill a structured web form with patient demographics and insurance details, so that the data is captured securely and can be used for downstream clinical workflows.
AC-004: Given I am on the \"New Patient Intake\" form, when I submit required fields (name, DOB, address, insurance policy number), then the data is encrypted at field level using AES‑256 before being persisted to PostgreSQL.
AC-005: Given the form is submitted, when the server stores the record, then an audit log entry records the operation type \"CREATE\", user ID, and patient identifier.
AC-006: Given the network connection uses TLS 1.3, when data is transmitted, then it is protected in transit per HIPAA §164.312(e)(1).
Edge-Case-003: If a required field is missing, then the form displays inline validation error \"This field is required\".
Edge-Case-004: If the encryption module fails, then the transaction is aborted and an error \"Encryption failure – contact admin\" is shown, without persisting plaintext.

US-003: Clinician views and updates medical history
As a Clinician, I want to view a patient\'s medical history and add clinical notes, so that I can provide informed care while maintaining auditability.
AC-007: Given I am authenticated as Clinician, when I request a patient record, then the system decrypts the data on the server side and returns it over a TLS‑encrypted channel.
AC-008: Given I add a note, when I save the note, then the note is encrypted at rest and an audit log entry records \"UPDATE\" with before/after hashes.
Edge-Case-005: If the Clinician attempts to access a patient not assigned to their care team, then the system returns HTTP 403 \"Access denied\".
Edge-Case-006: If the decryption key is unavailable, then the system returns a generic error \"Unable to retrieve record\" and logs the incident for admin review.

US-004: Patient reviews intake summary and requests correction
As a Patient, I want to view my submitted intake summary and request corrections, so that my personal information remains accurate.
AC-009: Given I am authenticated via secure patient portal, when I view my summary, then the PDF is generated on demand with a visible watermark \"Confidential – HIPAA\" and a timestamp of export.
AC-010: Given I submit a correction request, when I confirm the change, then the system creates a new version of the record, encrypts it, and logs the change.
Edge-Case-007: If the PDF generation library fails, then the system returns a friendly error \"Unable to generate summary, please try later\".
Edge-Case-008: If the patient attempts to download the PDF without proper role, then the request is denied with HTTP 403.

### Role Management Endpoints
POST /api/roles
- Description: Create a new role with specified permissions.
- Request Body (JSON): {\"name\": \"Clinician\", \"permissions\": [\"read-patient-data\", \"export-pdf\"]}
- Responses:
 201 Created – role created successfully. Returns role ID.
 400 Bad Request – validation error (e.g., duplicate name, invalid characters).
 409 Conflict – role name already exists.
 500 Internal Server Error – database unavailable.
GET /api/roles/{roleId}
- Description: Retrieve role definition and permissions.
- Responses: 200 OK with role object; 404 Not Found if role does not exist.
PUT /api/roles/{roleId}
- Description: Update permissions of an existing role.
- Request Body: {\"permissions\": [ ... ]}
- Responses: 200 OK; 400 Bad Request; 404 Not Found; 500 Internal Server Error.
DELETE /api/roles/{roleId}
- Description: Delete a role if not assigned to any user.
- Responses: 204 No Content on success; 400 Bad Request if role in use; 404 Not Found; 500 Internal Server Error.

### Requirements Traceability
- REQ-001: All PHI fields must be encrypted at rest using AES‑256 (mapped to AC‑001, AC‑005).
- REQ-002: Data in transit must use TLS 1.2+ (mapped to AC‑004).
- REQ-003: Encryption keys must be rotated every 90 days and logged (mapped to Edge‑Case‑005).
- REQ-004: Immutable audit log for every read/write (mapped to AC‑001, AC‑004, AC‑005, AC‑007).
- REQ-005: Audit logs retained ≥7 years (mapped to AC‑007).
- REQ-006: System must be containerized with Docker Compose and health‑checks (mapped to NFR‑002).
- REQ-007: Response time <200 ms for read operations (mapped to AC‑004).
- REQ-008: Role propagation ≤5 s across cluster nodes (mapped to performance metric).

### US-002: Unauthorized View Attempt
As a Clinician attempting to view a record they are not authorized for, I expect the system to deny access and log the attempt.
**Acceptance Criteria**
- AC-004: Given a Clinician requests a record they lack permission for, when the request is made, then the system returns HTTP 403 and logs an unauthorized‑access attempt.
**Traceability**: REQ-001, REQ-004

### US-003: Role Assignment Management
As an Admin, when I add a new role assignment, then the role is persisted, the user’s effective permissions are updated immediately, and an audit entry records the change.
**Acceptance Criteria**
- AC-005: Given I am authenticated as Admin, when I POST /roles with payload {"role":"Clinician","permissions":["read-patient-data","export-pdf"]}, then the role is saved, appears in role list, and an audit log entry is created with details of the change.
**Traceability**: REQ-004

### US-004: Export PDF
As an Authorized Staff member, when I click Export PDF, then the system generates a PDF using WeasyPrint, embeds watermark "Confidential – HIPAA", includes a timestamp footer, and logs the export action.
**Acceptance Criteria**
- AC-006: Given I am authenticated and authorized, when I POST /records/{id}/export-pdf, then a PDF is returned within 500 ms, contains the watermark and timestamp footer, and an audit log entry records action "export-pdf" with user ID and record ID.
**Traceability**: REQ-006, NFR-003

### US-005: CI Pipeline Test Suite Execution
As the CI pipeline, when the test suite runs, then it executes at least 30 unit tests covering field encryption, 20 integration tests covering RBAC scenarios, and produces a coverage report of ≥85%.
**Acceptance Criteria**
- AC-007: Given the CI pipeline triggers, when tests run, then results show ≥30 unit tests for encryption logic, ≥20 integration tests for RBAC policies, and overall code coverage ≥85%. Failures cause pipeline abort.
**Traceability**: REQ-007

### POST /roles
Description: Create or update a role definition.
Request Body Example:
{\"role\": \"Clinician\", \"permissions\": [\"read-patient-data\", \"export-pdf\"]}
Responses:
- 201 Created – role persisted.
- 400 Bad Request – validation error.
All changes generate an audit log entry (see AC‑005).

### POST /records/{record_id}/export-pdf
Description: Generate PDF export of a record with watermark and timestamp.
Responses:
- 200 OK – binary PDF stream with Content‑Disposition attachment.
- 403 Forbidden – user lacks export permission.
- 500 Internal Server Error – PDF generation failure logged as warning.

### Table: audit_log
Columns:
- id BIGSERIAL PRIMARY KEY
- user_id UUID NOT NULL (FK to users)
- action VARCHAR(50) NOT NULL (e.g., "view", "export-pdf", "role-change")
- target_id UUID NULL (record or role ID)
- timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
- details JSONB NULL – additional context such as IP address or payload diff
Constraints:
- Immutable append‑only (no UPDATE/DELETE); retention policy 7 years (REQ‑005).

## Performance and SLA Metrics
- Response time for all read/write API calls <200 ms (NFR‑001).
- System availability ≥99.9% monthly uptime (NFR‑002).
- PDF generation latency ≤500 ms for average record size (NFR‑003).
- Audit log write latency ≤50 ms to ensure non‑blocking user experience.

## Error Handling Guidelines
| Endpoint | Error Code | Condition | Response Message | Action 
|----------|-----------|----------|-----------------|--------| 
| GET /records/{id} | 403 | Unauthorized access attempt | "Access denied" | Log unauthorized‑access attempt (AC‑004) 
| POST /roles | 400 | Validation failure (e.g., prohibited characters) | "Invalid role definition" | Return error details to caller 
| POST /records/{id}/export-pdf | 500 | PDF generation failure (missing font) | "PDF generation error" | Fallback to default font, log warning 
| Any endpoint | 503 | Database connection loss after 3 retries | "Service unavailable" | Return HTTP 503 after retries

### US-004 Patient: Review Intake Summary and Request Correction
As a Patient, I want to view my submitted intake summary and request corrections so that my personal information remains accurate.
**Acceptance Criteria:**
- AC-009: Given I am authenticated via secure patient portal, when I view my summary, then a PDF is generated on demand with a visible watermark \"Confidential – HIPAA\" and an export timestamp.
- AC-010: Given I submit a correction request, when I confirm the change, then the system creates a new version of the record, encrypts it, and logs the change as an UPDATE audit entry.
- Edge-Case-007: If the PDF generation library fails, then a friendly error \"Unable to generate summary, please try later\" is returned.
- Edge-Case-008: If I attempt to download the PDF without proper role, then the request is denied with HTTP 403.

### User Stories and Acceptance Criteria

**US-001** (P1) – Front‑Desk Staff
- **Persona:** Front‑Desk Staff
- **Story:** As a Front‑Desk Staff I want to enter patient demographics, insurance information, and medical history into a structured web form so that the data is captured accurately and encrypted at field level.
- **Requirement Traceability:** REQ-001, REQ-003
- **Acceptance Criteria:**
  - AC-001: Given a logged‑in Front‑Desk user, when all mandatory fields are completed and Submit is clicked, then the system stores each field encrypted at rest, returns HTTP 201, and writes an audit entry (user_id, timestamp, operation).
  - AC-002 (Edge): Given a network interruption during submission, when the request fails, then the system rolls back any partial writes and logs a failure event (HTTP 503).

**US-002** (P1) – Clinician
- **Persona:** Clinician
- **Story:** As a Clinician I want to view a patient’s intake record in a read‑only view so that I can assess clinical needs without modifying protected health information.
- **Requirement Traceability:** REQ-001, REQ-004
- **Acceptance Criteria:**
  - AC-003: Given a Clinician with role \"clinician\", when they request a patient record, then the system returns a read‑only view, encrypts transmission with TLS 1.3, decrypts data in memory only, returns within 200 ms, and records an audit entry (user_id, patient_id, timestamp, action=read).
  - AC-004 (Edge): Given a Clinician attempts to view a record they are not authorized for, when the request is made, then the system returns HTTP 403 and logs an unauthorized‑access attempt.

**US-003** (P2) – Admin (Role Management)
- **Persona:** Admin
- **Story:** As an Admin I want to assign, modify, or revoke roles (admin, clinician, front‑desk) for any user so that access follows the principle of least privilege.
- **Requirement Traceability:** REQ-004
- **Acceptance Criteria:**
  - AC-005: Given an Admin updates a user’s role, when the change is persisted, then the effective permissions are updated immediately and an audit entry records the change (user_id, target_user_id, new_role, timestamp).

**US-004** (P1) – Authorized Staff PDF Export
- **Persona:** Authorized Staff (Admin or Clinician)
- **Story:** As an Authorized Staff I want to generate a PDF summary of a patient’s intake data with a visible watermark and export timestamp so that the document can be printed or shared while preserving auditability.
- **Requirement Traceability:** REQ-006, NFR-003
- **Acceptance Criteria:**
  - AC-006: Given an authorized staff member selects \"Generate PDF\", when the request completes, then the system generates a PDF using WeasyPrint version 53, embeds watermark \"Confidential – HIPAA\", includes footer with export timestamp, stores the file temporarily with access restricted to role \"admin\" or \"clinician\", and logs the export action.
  - AC-007 (Edge): Given a non‑authorized user attempts to download the PDF, when the request is made, then the system denies access (HTTP 403) and logs the attempt.
  - AC-008 (Performance): PDF generation completes within 3 seconds for records up to 5 KB.

**US-005** (P3) – Patient Read‑Only View
- **Persona:** Patient
- **Story:** As a Patient I want to view a read‑only version of my submitted intake summary so that I can verify the information I provided.
- **Requirement Traceability:** REQ-001
- **Acceptance Criteria:**
  - AC-009: Given the patient authenticates via a secure portal, when they request their summary, then the system presents a sanitized view without edit controls and logs the access.
  - AC-010 (Edge): Given the patient’s session expires, when they attempt to view the summary, then they are redirected to the login page.

**US-006** (P3) – Compliance Officer Log Export
- **Persona:** Compliance Officer
- **Story:** As a Compliance Officer I want to export audit logs for a given date range so that I can perform periodic HIPAA compliance reviews.
- **Requirement Traceability:** REQ‑007, REQ‑008
- **Acceptance Criteria:**
  - AC‑011: Given a valid date range, when the officer requests log export, then the system provides a CSV file containing immutable log entries encrypted at rest, logs the export operation, and enforces retention of 7 years.

### Design Needs (Non‑Functional Requirements)
- **Transport Security:** All data‑in‑transit must use TLS 1.3 (NFR‑004).
- **Encryption:** Field‑level encryption using AES‑256‑GCM with per‑field keys derived from a master key stored in an HSM (REQ‑001, REQ‑003).
- **Audit Log Schema:** Fields: log_id, user_id, role, action, patient_id, timestamp, outcome. Log is append‑only, write‑once, tamper‑evident (REQ‑004, REQ‑005).
- **Performance:** System response time <200 ms for read operations (NFR‑001). PDF generation <3 s for ≤5 KB (NFR‑003).
- **Availability:** Docker Compose deployment with health‑checks ensuring 99.9 % uptime (NFR‑002).

### US-001: As a Clinician, I want to submit patient intake forms so that patient data is captured securely.
**Acceptance Criteria:**
- Given a logged‑in clinician, when they complete and submit the form, then the data is stored encrypted at rest (REQ-001) and a success confirmation is displayed.
- Given a submission error, when the system retries up to three times, then it returns HTTP 503 only after the final failed attempt (aligns with NFR‑001).

### US-002: As a Patient, I want to receive a PDF summary of my submitted information with a visible watermark and export timestamp.
**Acceptance Criteria:**
- Given a completed intake, when the patient requests a summary, then a PDF is generated containing all submitted fields, includes a watermark text (FR‑005) and an export timestamp, and is downloadable within 200 ms (NFR‑001).
- The PDF generation process logs an immutable audit entry (FR‑004).

### US-003: As an Administrator, I need to view an immutable audit log of all read/write operations for compliance reporting.
**Acceptance Criteria:**
- Given any read/write operation, when it occurs, then an audit log entry with timestamp, user ID, operation type, and affected record ID is created (FR‑004) and retained for at least seven years (REQ‑005).
- The audit log retrieval API returns results within 200 ms under normal load (NFR‑001).

### POST /api/intake
- **Description:** Accepts patient intake form data.
- **Request Body:** JSON object matching the data model defined in the Data Model section.
- **Responses:** 201 Created on success; 503 Service Unavailable after three automatic retries on failure.

### GET /api/intake/{id}/summary
- **Description:** Returns PDF summary for the given intake ID.
- **Headers:** `Accept: application/pdf`
- **Responses:** 200 OK with PDF payload; 404 Not Found if ID does not exist; 503 Service Unavailable on generation failure after retries.
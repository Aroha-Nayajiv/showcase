# Patient Intake Web Form (Overview)

## Traceability & Version Linking
- **Source Phase**: Inception (Cycle 1)
- **Source Requirements**: 
  - [Business Requirements Spec](inception_business_requirements_spec_final_approved_cycle_1.md) (REQ-001, REQ-002, REQ-005)
  - [Risk Assessment](inception_risk_assessment_final_approved_cycle_1.md) (FR-001, FR-002, FR-003, FR-006)
  - [Stakeholder Matrix](inception_stakeholder_analysis_matrix_final_approved_cycle_1.md) (ST-01, ST-02, ST-03)

## Personas
PER-01: Patient
Goal: Submit personal health information securely so that clinicians can provide appropriate care.
Responsibilities: Complete multi‑step web form capturing demographics, insurance details, and medical history; verify entered data before submission; request amendment of submitted data through a secure portal.
Access Rights: Read‑only access to their own record after submission; can view generated PDF summary if clinician grants export permission; cannot view other patients' records.
Compliance Notes: Data entered is encrypted at field level in transit (TLS 1.3) and at rest (AES‑256‑GCM); audit log records each view and edit action with timestamp, user ID, and operation type (REQ‑004).

PER-02: Front Desk Staff
Goal: Capture patient information efficiently while maintaining HIPAA compliance.
Responsibilities: Assist patients in completing the intake form when needed; validate insurance information against external lookup services; flag incomplete or inconsistent entries for clinician review.
Access Rights: Create new patient intake records; read and update records they created; cannot delete records; cannot export PDF summaries.
Compliance Notes: All create and update actions are logged (AU‑2, AU‑6); staff actions are limited to role‑based permissions (admin, clinician, front‑desk) as defined in RBAC matrix (AC‑2, AC‑6).

PER-03: Clinician
Goal: Review complete patient intake data to inform diagnosis and treatment planning.
Responsibilities: Access full patient record including encrypted fields; verify medical history accuracy; approve or deny PDF export requests; add clinical notes.
Access Rights: Read/write access to all fields of records for patients assigned to them; can generate and download PDF summary with watermark and access timestamp; can audit view logs for compliance verification.
Compliance Notes: Exported PDFs include visible watermark indicating \"Confidential – HIPAA Protected\" and embed export timestamp in metadata; each export is logged as a write operation per REQ‑004.

PER-04: System Administrator
Goal: Maintain secure operation of the intake system and enforce policy.
Responsibilities: Manage user accounts and role assignments; configure encryption keys and rotate them per policy; monitor audit logs for anomalies; ensure Docker Compose deployment follows air‑gap guidelines.
Access Rights: Full administrative privileges over system configuration; read access to all audit logs; no direct access to patient PHI content unless impersonating a role for troubleshooting, which is logged as a privileged action.
Compliance Notes: Key rotation logs must be retained for seven years (REQ‑005); audit log retention period set to minimum seven years (NFR‑005).

## Interface Definitions (API Contracts)
**POST /intake** – Create new patient intake record. Request body includes patient demographics, insurance info, medical history. Returns 201 Created with record ID and encryption confirmation flag. Errors: 400 ValidationError, 503 EncryptionServiceUnavailable.
**GET /intake/{id}** – Retrieve encrypted patient record. Requires authentication with role permitting read access to the specific patient or assigned clinician. Returns 200 with encrypted payload and HMAC signature. Errors: 401 Unauthorized, 403 Forbidden, 404 NotFound.
**POST /intake/{id}/pdf** – Request PDF generation for a given intake record. Body may include watermark options. Returns 202 Accepted with job ID; polling endpoint **GET /intake/pdf/status/{jobId}** provides status and download URL when ready. Errors: 403 Forbidden (insufficient role), 409 Conflict (PDF already generated), 500 InternalError on PDF engine failure.
**GET /audit/report** – Generate audit log report for specified date range. Query parameters: startDate, endDate, format=csv|json. Requires Compliance Officer role. Returns 200 with report file stream. Errors: 401 Unauthorized, 403 Forbidden, 422 UnprocessableEntity for invalid dates.

## Data Model Overview
- **PatientRecord**: { id:string, patientId:string, demographics:object, insurance:object, medicalHistory:object, encryptedAtRest:boolean, createdAt:timestamp, updatedAt:timestamp }
- **AuditLogEntry**: { entryId:string, userId:string, action:string (create|read|update|delete|export|login|logout), target:string (recordId or system), timestamp:timestamp, details:object }
- **RoleAssignment**: { assignmentId:string, userId:string, role:string (patient|front_desk|clinician|admin|compliance_officer), effectiveFrom:timestamp, effectiveTo:timestamp? }
All sensitive fields in PatientRecord are stored encrypted using AES‑256‑GCM; encryption keys are rotated per REQ‑005 and logged.

## Edge Cases and Failure Scenarios
EC-001 (US‑001) If encryption at rest fails due to key service outage, the system aborts the transaction, returns error \"Encryption service unavailable\" and logs a critical error with stack trace.
EC-002 (US‑001) If the PostgreSQL database reaches connection limit, the form submission is queued, the user sees message \"Service busy, please retry\", and the event is logged for capacity planning.
EC-003 (US‑003) If PDF generation library throws an exception, the system falls back to a plain‑text summary, flags the record for manual review, and logs failure with error code PDF‑GEN‑01.
EC-004 (US‑004) If an admin attempts to assign a non‑existent role, the system rejects the change with error \"Role not found\" and audits the attempt.
EC-005 (US‑005) If audit log retention policy cannot purge older entries due to storage quota, the system raises an alert on the admin dashboard and continues logging new entries in a rollover file.
EC-006 (Additional) Given a staff member attempts to delete a patient record, when they perform the action, then the system denies the request, returns HTTP 403, and logs the unauthorized delete attempt.

## Acceptance Criteria
AC-001 (US‑001) Given a patient accesses the secure HTTPS URL, when the patient completes all required fields and submits, then the system stores each field encrypted with AES‑256‑GCM at rest, logs the create action with timestamp, user‑ID, and operation type, and returns a success message within 2 seconds.
AC-002 (US‑001) Given a patient provides an invalid email, when the form validation runs, then the system displays an inline error "Invalid email format" and prevents submission.
AC-003 (US‑001) Given a patient’s session expires, when the patient attempts to submit, then the system redirects to the login page and logs a session‑timeout event.
AC-004 (US‑002) Given a front‑desk staff member logs in with role "front_desk", when they create a new intake record, then the record is stored encrypted, the audit log records the "create" action, and the UI shows a green checkmark confirming encryption.
AC-005 (US‑003) Given a clinician selects "Download PDF" for a patient record, when the request is processed, then the system generates a PDF/A‑2b compliant document encrypted with AES‑256, includes the watermark "Confidential – HIPAA Protected" and export timestamp in footer, logs the "export" action, and the download completes within 3 seconds.
AC-006 (US‑003) Given a clinician attempts to download a PDF without export permission, when the request is made, then the system returns HTTP 403 Forbidden and logs an unauthorized export attempt.
AC-007 (US‑004) Given an admin configures RBAC matrix via the admin console, when changes are saved, then the system validates role permissions against policy rules, updates access controls instantly, and logs the configuration change as a privileged action.
AC-008 (US‑005) Given a compliance officer requests an audit report for the past 30 days, when the report generation is triggered, then the system compiles all audit log entries within the period into a CSV file, encrypts it with AES‑256, provides a download link, and completes within 5 seconds.
AC-009 (Performance) Given any API request under normal load, when processed, then response times meet defined thresholds: form submission <200 ms, PDF download <3 s, audit report generation <5 s.
AC-010 (Reliability) Given the logging service operates continuously, when a failure occurs, then alerts are raised and logs are retained for at least seven years per NFR‑005.

### API Endpoints
POST /api/intake
- Description: Submit new patient intake form.
- Request Body (JSON): {"patient_id":"string","demographics":{...},"insurance":{...},"medical_history":{...}}
- Responses:
  200 OK {"intake_id":"uuid","message":"Submission successful"}
  400 Bad Request {"error":"Validation failed","details":{...}}
  401 Unauthorized {"error":"Authentication required"}
GET /api/intake/{intake_id}
- Description: Retrieve stored intake record (encrypted fields are returned decrypted for authorized roles).
- Responses: 200 OK with record JSON; 403 Forbidden if role lacks permission; 404 Not Found.
GET /api/intake/{intake_id}/pdf
- Description: Generate and download PDF summary for the specified intake record.
- Responses: 200 OK with PDF binary stream (Content-Type: application/pdf); 403 Forbidden if no export rights; 404 Not Found.
GET /api/audit/report?days=30
- Description: Generate audit log report for the past N days.
- Responses: 200 OK with CSV file; 403 Forbidden if requester not compliance officer; 400 Bad Request for invalid parameters.

## Error Handling Specification
Common error response format (JSON): {"error_code":"ERR001","message":"Human readable description","details":{...}}
Defined error codes:
- ERR001 ValidationError – input fails schema validation.
- ERR002 AuthenticationFailed – missing or invalid JWT token.
- ERR003 AuthorizationDenied – user lacks required permission.
- ERR004 ResourceNotFound – requested record does not exist.
- ERR005 ServiceUnavailable – downstream dependency failure.
All errors are logged with correlation ID for traceability.

## Compliance & Performance Requirements Summary
- NFR-001: Form submission response time <200 ms.
- NFR-002: System uptime 99.9 % monthly.
- NFR-003: Data at rest encrypted with AES‑256‑GCM.
- NFR-004: TLS 1.3 for all network communication.
- NFR-005: Audit log retention minimum 7 years.
- HIPAA §164.312(a)(2)(iv): Encryption of ePHI at rest and in transit.
- NIST SP 800‑53 AC‑2, AC‑6 for RBAC; AU‑2, AU‑6 for audit logging.

## User Stories and Traceability
US-001 (Persona: Patient) As a Patient, I want to securely enter my demographic, insurance, and medical history via a multi‑step web form, so that my health information is captured accurately and protected in compliance with HIPAA.
Traceability: REQ-001 (field‑level encryption), REQ-002 (TLS in transit), NFR-003 (AES‑256 at rest).
Acceptance Criteria:
- Given a patient accesses the intake portal, when they complete all required fields and submit, then the data is encrypted at rest using AES‑256‑GCM and a confirmation message is shown.
- Given encryption service outage, when the patient attempts to submit, then the system returns error "Encryption service unavailable" and logs a critical error with stack trace.

US-002 (Persona: Front Desk Staff) As Front Desk Staff, I want to create and update patient intake records quickly, so that I can assist patients without delays.
Traceability: REQ-001, REQ-002, NFR-001.
Acceptance Criteria:
- Given the staff fills the form and clicks Submit, when the backend stores the record, then the operation completes within 200 ms and creates an audit log entry.
- Given the PostgreSQL connection limit is reached, when the staff submits, then the form is queued, a friendly message "Service busy, please retry" is displayed, and the event is logged for capacity planning.

US-003 (Persona: Clinician) As a Clinician, I need to export a PDF summary of a patient’s intake data with a visible watermark and timestamp, so that I can review it offline while maintaining auditability.
Traceability: REQ-004 (audit logging), DN-004 (PDF requirements), NFR-005 (performance).
Acceptance Criteria:
- Given the clinician requests PDF export for an authorized patient record, when the generation completes, then the PDF includes watermark "Confidential – HIPAA Protected", a footer with ISO‑8601 export timestamp, is encrypted at rest with AES‑256, and download completes within 3 seconds.
- Given the PDF generation library throws an exception, when the clinician attempts export, then the system falls back to a plain‑text summary, flags the record for manual review, and logs error code PDF‑GEN‑01.

US-004 (Persona: System Administrator) As an Admin, I want to configure the RBAC matrix and assign roles, so that least‑privilege access is enforced across the system.
Traceability: REQ-004, DN-002 (RBAC matrix), NFR-002 (uptime).
Acceptance Criteria:
- Given an admin assigns a role to a user via the admin console, when the change is saved, then the system enforces the new permissions immediately and records the change in the immutable audit log.
- Given an admin attempts to assign a non‑existent role, when the request is processed, then the system returns error "Role not found" and audits the attempt.

US-005 (Persona: Compliance Officer) As a Compliance Officer, I need to generate an audit report for the last 30 days that includes read/write counts and unauthorized attempts, so that I can demonstrate regulatory compliance.
Traceability: REQ-004, REQ-005 (log retention), NFR-005 (report performance).
Acceptance Criteria:
- Given the officer requests the audit report, when generation completes, then the output CSV includes total read/write counts, unauthorized attempts count, and is downloadable within 5 seconds.

## Prioritization and Business Justification
1 | US-001 | Captures core PHI, required for compliance (HIPAA §164.312(a)(2)(iv)) | None
2 | US-003 | Enables clinical decision making, directly impacts patient care quality | US-001
3 | US-004 | Establishes security foundation, mitigates breach risk | US-001, US-002
4 | US-005 | Provides auditability for regulatory reporting | US-004
5 | US-002 | Improves data entry efficiency, reduces manual errors | US-001

## Design Needs for Downstream Teams
DN-001: Detailed field‑level encryption specification – algorithm AES‑256‑GCM, key‑management service compatible with HSM, key rotation every 90 days, master key stored in hardware‑security‑module‑compatible vault, rotation logs retained 7 years (REQ‑005).
DN-002: RBAC matrix definition – permissions (create, read, update, delete, export) per role (Patient, Front‑Desk, Clinician, Admin). Example: Front‑Desk can create and update records they created; Clinician can read/write assigned patient records and export PDFs; Admin has full access to configuration but PHI view requires impersonation logged as privileged action.
DN-003: Audit log schema – append‑only table with fields: log_id (UUID), timestamp (ISO‑8601), user_id, patient_id, operation_type (create, read, update, delete, export, login, logout), outcome (success, failure), object_hash (SHA‑256 of payload), additional_context (JSON). Retention minimum 7 years (NFR‑005).
DN-004: PDF generation requirements – use WeasyPrint or wkhtmltopdf; watermark text "Confidential – HIPAA Protected" semi‑transparent overlay; footer with export timestamp ISO‑8601; PDF/A‑2b compliance; encrypt PDF at rest with AES‑256.
DN-005: Performance thresholds – form submission response <200 ms (NFR‑001), system uptime 99.9 % (NFR‑002), PDF download <3 seconds, audit report generation <5 seconds.
DN-006: Compliance citations – HIPAA §164.312(a)(2)(iv) for encryption, NIST SP 800‑53 AC‑2, AC‑6 for RBAC, AU‑2, AU‑6 for audit logging, TLS 1.3 for transport, WCAG 2.1 AA for UI accessibility.
DN-007: Docker‑Compose air‑gap deployment – all images stored in internal registry, no external network calls, environment variables validated at container start, health‑check endpoint must return healthy within 30 seconds, disk space check for ≥2 GB, clear error messages on missing variables.

### US-001 (Persona: Patient)
**As a Patient, I want to securely submit my intake form so that my protected health information (PHI) is encrypted at rest and I receive immediate confirmation.**
Traceability: REQ-001, REQ-004, NFR-001

**Acceptance Criteria**
- **AC-001** (Given a patient accesses the secure HTTPS URL, when the patient completes all required fields and submits, then the system stores each field encrypted with AES‑256‑GCM at rest, logs the create action with timestamp, user‑ID, and operation type, and returns a success message within 2 seconds.)
- **AC-002** (Given a patient provides an invalid email, when the form validation runs, then the system displays an inline error "Invalid email format" and prevents submission.)
- **AC-003** (Given a patient’s session expires, when the patient attempts to submit, then the system redirects to the login page and logs a session‑timeout event.)

### Tables
1. **intake_record**
   - `record_id` UUID PK
   - `patient_id` UUID FK
   - `encrypted_data` BYTEA (AES‑256‑GCM encrypted JSON payload)
   - `created_at` TIMESTAMP WITH TIME ZONE
   - `created_by` UUID (user ID)
2. **audit_log**
   - `log_id` UUID PK
   - `timestamp` TIMESTAMP WITH TIME ZONE
   - `user_id` UUID FK
   - `patient_id` UUID FK
   - `operation_type` VARCHAR (create, read, update, delete, export, login, logout)
   - `outcome` VARCHAR (success, failure)
   - `object_hash` CHAR(64) (SHA‑256 of payload)
   - `additional_context` JSONB
3. **user_role**
   - `user_id` UUID PK
   - `role` VARCHAR (admin, clinician, front_desk)
   - `assigned_at` TIMESTAMP WITH TIME ZONE
   - `assigned_by` UUID FK

### Relationships & Constraints
- Foreign key constraints enforce referential integrity between `intake_record.patient_id` and patient master table (not shown).
- Audit log entries are immutable; inserts only.
- Role assignments trigger audit log entry with operation_type "role_assign".

## Performance & Compliance Targets
- Form submission response time <200 ms (NFR‑001).
- PDF download latency <3 seconds (NFR‑005).
- Audit report generation <5 seconds for 30‑day window (NFR‑002).
- System uptime 99.9 % (NFR‑002).
- TLS 1.3 enforced for all API traffic (NFR‑004).

## Compliance References
- HIPAA §164.312(a)(2)(iv) – Encryption of PHI at rest.
- NIST SP 800‑53 AC‑2, AC‑6 – Role‑Based Access Control.
- NIST SP 800‑53 AU‑2, AU‑6 – Audit Logging.
- ISO/IEC 27001 A.12.4 – Logging and monitoring.
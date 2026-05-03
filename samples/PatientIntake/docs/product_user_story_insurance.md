# Insurance Information Capture

### PER-01 – Front Desk Staff
Role: Administrative staff who receive patients, enter demographic and insurance data, and initiate the intake workflow.
Primary Goals: Capture complete, accurate patient information within 2 minutes per record (FR-001), ensure data is encrypted at rest using PostgreSQL pgcrypto (NFR-001), and provide immediate confirmation receipt to the patient (FR-006).
Key Tasks: Open the web form, fill required fields, validate real‑time error messages, submit the form, and verify the acknowledgment screen.
Success Metrics: Form submission latency <200 ms (KPI-002), validation error rate <1 % (FR-005), and 99 % of submissions generate a receipt within 1 second (FR-006).
Acceptance Criteria:
Given the staff is logged in with role "front_desk", when they access the intake form, then the form loads within 200 ms and all fields are visible.
Given a required field is left blank, when the staff attempts to submit, then an inline validation error appears and submission is blocked.
Given valid data is entered, when the staff clicks Submit, then the data is encrypted at field level, stored securely, and a receipt screen appears within 1 second.

## Minimum Viable Product Feature Set for Patient Intake System
1. **Core Data Capture**
   The web form must collect patient demographics, insurance information, and medical history. Fields include First Name, Last Name, DOB, Address, Phone, Email, Insurance Provider, Policy Number, Group ID, and a free‑text medical history section. All fields are required except optional secondary phone. Validation rules enforce proper formats (e.g., email regex, phone numeric, DOB not future). Acceptance: Given a valid browser session, When the user completes the form with all required fields, Then the system stores an encrypted record and displays a confirmation within 1 second (KPI‑002).
2. **Security & Encryption**
   Field‑level encryption must be applied to PHI at rest using PostgreSQL pgcrypto with a per‑field AES‑256 key encrypted by a master key stored in a Vault‑compatible secret store. In‑transit encryption uses TLS 1.3 enforced by Nginx. Acceptance: Given a network capture, When a form submission is intercepted, Then no plaintext PHI is observable and the TLS handshake reports TLS 1.3 cipher suite.
3. **Role‑Based Access Control (RBAC)**
   Three roles are defined: Front Desk (data entry only), Clinician (read‑only view of patient records), Admin (full CRUD and audit‑log access). PostgreSQL roles map to these application roles via row‑level security policies that restrict SELECT/UPDATE based on the authenticated user's role attribute. Acceptance: Given a Clinician login, When the user attempts to edit a patient record, Then the system returns an Access Denied error and logs the attempt.
4. **Audit Logging**
   Every read and write operation on PHI must generate an immutable log entry containing user ID, timestamp, operation type, and record identifier. Logs are written to a write‑once append‑only table with digital signatures (pgcrypto). Acceptance: Given any successful read, When the audit table is queried, Then an entry exists with a valid signature and the timestamp matches the operation time within ±1 second.
5. **PDF Summary Export**
   Authorized staff can export a patient's intake data as a PDF. The PDF includes a visible watermark containing the exporting user ID and export timestamp. The watermark is generated using wkhtmltopdf with a custom HTML overlay. Acceptance: Given a Clinician request to export, When the PDF is generated, Then the watermark text matches "Exported by {UserID} at {ISO‑timestamp}" and the file size does not exceed 500 KB. Error handling added for export failures returns HTTP 500 with error code PDF_EXPORT_FAIL.
6. **Automated Unit & Integration Tests**
   A pytest suite covers form validation (invalid email, missing required fields), encryption correctness (encrypted fields are not stored in plaintext), RBAC enforcement (role‑specific access attempts), PDF export watermark verification, TLS downgrade detection, and key‑rotation latency targets (decryption ≤300 ms). Tests run in CI on each commit and must achieve ≥90 % code coverage. Acceptance: Given a CI run, When the test suite completes, Then the coverage report shows ≥90 % and all tests pass.
7. **Deployment & Air‑Gap Setup Guide**
   Docker Compose defines three containers: Nginx (TLS termination), Flask app (Python 3.11), PostgreSQL (13). All images are pulled from official registries before air‑gap; the guide documents how to export images to an offline registry and configure Docker Compose to use local image tarballs. Acceptance: Given an isolated network environment with no internet access, When the deployment script is executed, Then the system starts within 2 minutes and all health‑check endpoints report "healthy".

## Personas for Patient Intake System

PER-01 – Front Desk Staff
Role: Administrative staff who receive patients, enter demographic and insurance data, and initiate the intake workflow.
Primary Goals: Capture complete, accurate patient information within 2 minutes per record (FR-001), ensure data is encrypted at rest using PostgreSQL pgcrypto (NFR-001), and provide immediate confirmation receipt to the patient (FR-006).
Key Tasks: Open the web form, fill required fields, validate real-time error messages, submit the form, and verify the acknowledgment screen.
Success Metrics: Form submission latency <200 ms (KPI-002), validation error rate <1 % (FR-005), and 99 % of submissions generate a receipt within 1 second (FR-006).
Acceptance Criteria:
Given the staff is logged in with role "front_desk", when they access the intake form, then the form loads within 200 ms and all fields are visible.
Given a required field is left blank, when the staff attempts to submit, then an inline validation error appears and submission is blocked.
Given valid data is entered, when the staff clicks Submit, then the data is encrypted at field level, stored securely, and a receipt screen appears within 1 second.

PER-02 – Clinician
Role: Healthcare provider who reviews patient intake information to make clinical decisions.
Primary Goals: Retrieve patient records instantly (FR-001), view only records for patients assigned to them (FR-002), and see an audit trail of who accessed the record (FR-003).
Key Tasks: Search for a patient, open the summary view, and export a PDF if needed.
Success Metrics: Record retrieval time <200 ms, access logs written for every read operation, and exported PDFs contain watermark with user ID and timestamp (FR-008).
Given the clinician is authenticated with role "clinician", when they request a patient record, then the system returns the record within 200 ms and logs the read event with user ID and timestamp.
Given the clinician attempts to view a record of a patient not assigned to them, when the request is processed, then access is denied and an audit entry records the denied attempt.
Given the clinician selects "Export PDF", when the export completes, then the PDF includes a visible watermark containing the clinician's user ID and export timestamp.

PER-03 – Patient
Role: Individual providing personal health information via the web form.
Primary Goals: Complete the intake form quickly, receive confirmation that their data was received, and be assured that their information is protected under HIPAA.
Key Tasks: Read the privacy notice, fill out demographics, insurance, and medical history, and submit.
Success Metrics: Form completion time <5 minutes, privacy notice displayed before data entry (FR-010), and encryption of all PHI at rest and in transit (NFR‑001, NFR‑002).
Given the patient lands on the intake page, when they view the page, then the privacy notice is displayed prominently and must be acknowledged before any data entry begins.
Given the patient fills all required fields correctly, when they submit, then the system encrypts each field using open-source pgcrypto, stores it securely, and shows a confirmation screen within 1 second.
Given a network interruption occurs during submission, when the client retries, then the system ensures no duplicate records are created and logs the retry event.

## Insurance Information Capture - Acceptance Criteria

User Stories
US-001 | Front Desk Staff | to enter patient insurance details into the intake form | the billing department can process claims accurately
US-002 | Patient | to review and confirm my insurance information before submission | I can be confident that my coverage data is correct
US-003 | Clinician | to view a patient's insurance summary after authentication | I can verify coverage eligibility before treatment

Acceptance Criteria
AC-001 | US-001 | The front desk user is logged in with role 'front_desk' and the form is loaded | The user fills all required insurance fields and clicks Submit | The system encrypts each field with field‑level encryption (AES‑256‑GCM) before persisting to PostgreSQL, stores a cryptographic hash of the plaintext for integrity verification, and returns a success toast within 2 seconds (≤2000 ms) | If any required field is missing, the form shows an inline validation error; if encryption fails, the transaction is rolled back and an error message referencing HIPAA §164.312(e)(1) is displayed
AC-002 | US-001 | Same as AC-001 but with an invalid insurance policy number format | The user attempts to submit | The system rejects the submission, highlights the policy number field, and displays "Invalid policy number – must match /^[A-Z0-9]{8,12}$/". No data is written to the database
AC-003 | US-002 | The patient is accessing the form over TLS 1.3 with a valid session token | The patient reviews pre‑filled insurance fields and clicks Confirm | The system records a confirmation audit log entry (user_id, timestamp, action='insurance_confirmed') and marks the record as "confirmed"; the confirmation must be stored with an immutable append‑only log (pg_audit) within 500 ms
AC-004 | US-002 | The patient attempts to confirm without having edited any fields | The patient clicks Confirm | The system still creates an audit log entry indicating "no changes" and proceeds; no encryption operation is performed because data unchanged
AC-005 | US-003 | The clinician is authenticated with role "clinician" and has passed multi‑factor authentication (MFA) per NIST SP 800‑63B | The clinician requests the insurance summary view for patient X | The system decrypts the stored fields using the master key stored in HashiCorp Vault, displays the summary, and logs the read operation with user_id, patient_id, timestamp, and outcome='success' within 300 ms | If the clinician lacks permission, the system returns HTTP 403 with message "Access denied – insufficient role", logs the denied attempt, and does not perform decryption
AC-006 | US-003 | The clinician attempts to view insurance data for a patient they are not assigned to (row‑level security violation) | The request is made | The system denies access, returns HTTP 403, logs "RLS violation" with details, and ensures no plaintext is ever exposed

Compliance Checks
All encryption operations must comply with HIPAA Technical Safeguard §164.312(e)(1) and use FIPS‑validated cryptographic modules.
Audit log entries must be immutable and retained for at least 7 years per HIPAA §164.310(d)(2)(i).
TLS 1.3 must be enforced for all client‑server communication; any downgrade attempt must be logged and result in connection termination.
Field‑level encryption keys are rotated quarterly; AC‑001 includes verification that key rotation does not affect existing records.

Performance Metrics
Form submission latency ≤2 seconds for 95 % of transactions (KPI‑002).
Encryption/decryption overhead ≤300 ms per operation (measured on reference hardware).
Audit log write latency ≤100 ms (KPI‑017).

Error Handling
Any encryption exception triggers a transaction rollback and an error response containing error code ENCRYPT_FAIL and reference to internal error ID for support tracing.
Validation errors return HTTP 400 with a JSON payload listing field errors; no sensitive data is echoed back.

Testability
Each AC maps to an automated test case in the test suite (e.g., pytest) using mock Vault secrets and a PostgreSQL test container.
Edge case scenarios are covered by negative tests for missing fields, malformed policy numbers, unauthorized access, and RLS violations.

## API Endpoints (Added per Reviewer Feedback)

- **POST /api/v1/patients/{patient_id}/intake** – Accepts JSON payload of patient intake data. Returns 201 Created with receipt ID on success or 400 with validation errors. Includes error handling for encryption failures returning 500 ENCRYPT_FAIL.
- **GET /api/v1/patients/{patient_id}** – Returns encrypted patient record for authorized roles (clinician, admin). Decrypts on server side using Vault master key; logs read operation.
- **GET /api/v1/patients/{patient_id}/insurance** – Returns decrypted insurance summary for authorized clinicians; logs access.
- **POST /api/export/pdf/{id}** – Generates PDF export; on error returns 500 with detailed error code PDF_GEN_FAIL; includes watermark generation step verification.
- **GET /api/audit/logs** – Admin endpoint to query immutable audit logs with pagination.
All endpoints enforce RBAC checks and emit audit entries per operation.

## Test Coverage Enhancements (Added per Reviewer Feedback)

- Added unit tests for PDF export error paths (e.g., wkhtmltopdf failure) verifying proper 500 response and logged error.
- Added integration test verifying key rotation does not break decryption of existing records; simulates quarterly rotation using mock Vault keys.
- Expanded test matrix to cover admin role actions including CRUD on patient records and audit log retrieval.
- Included performance test asserting encryption/decryption latency ≤300 ms under load.

## Admin Role Stories (Added per Reviewer Feedback)

US-004 | Admin | to manage system configuration and audit logs | I can ensure compliance and operational stability
AC-007 | US-004 | Given an admin authenticated with MFA, when they navigate to Settings, then they can update RBAC policies and view system health metrics.
AC-008 | US-004 | Given an admin requests audit log export, when they specify date range, then the system provides an immutable CSV export within 5 seconds.
AC-009 | US-004 | Given an admin attempts to delete a patient record, when they confirm deletion, then the system performs a soft‑delete flagging record as archived while retaining immutable audit trail.
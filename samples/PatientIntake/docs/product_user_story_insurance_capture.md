# Insurance Information Capture User Story

### Objective
The purpose of this step is to gather detailed requirements for the Insurance Information Capture feature of the PatientIntake system, ensuring compliance with HIPAA technical safeguards (e.g., §164.312(a)(2)(iv) encryption) and aligning with FR-001 through FR-010. The output will feed directly into the product backlog for design.

### Stakeholder Interview Plan
- **Front‑Desk Staff (ST-002)** – Primary data entry operators who need a fast, error‑free form. Interview focus: average entry time, validation error tolerance (<1% per batch), and required on‑screen guidance.
- **Clinician (ST-003)** – Consumers of insurance data for treatment decisions. Interview focus: data retrieval latency (≤200 ms, KPI-002), audit‑log visibility, and role‑based view restrictions (FR-002).
- **Patient (ST-001)** – Subject of data collection. Interview focus: privacy notice comprehension, consent capture, and expectations for data correction within 5 business days (FR-011).
- **Compliance Officer (ST-005)** – Ensures HIPAA and NIST 800‑53 controls are satisfied. Interview focus: encryption key management (SC-13), audit‑log retention (7 years, KPI-003), and documentation requirements.
All interviews will be recorded, transcribed, and mapped to functional requirements using a traceability matrix.

### Personas
- **PER-01 | Front‑Desk Staff** – Enter patient insurance quickly and accurately; avoid re‑entry due to validation errors; must not expose PHI on insecure workstations.
- **PER-02 | Clinician** – Retrieve verified insurance info for billing; delayed access impedes care; needs role‑based access control (RBAC).
- **PER-03 | Patient** – Provide accurate insurance data and receive confirmation receipt; unclear privacy notice leads to mistrust; requires explicit consent and right to correction.

### User Stories
| Story ID | As a | I want to | So that |
|---|---|---|---|
| US-001 | Front‑Desk Staff | Enter patient insurance details securely into the intake form | The patient's coverage information is recorded accurately and protected per HIPAA requirements |
| US-002 | Clinician | View a patient's insurance information after authentication | I can verify coverage eligibility before providing care, reducing claim rejections |
| US-003 | Patient | See a clear privacy notice before submitting my insurance data | I understand how my PHI will be used and protected |
| US-004 | Administrator | Generate audit reports of insurance data access | I can demonstrate compliance with FR‑002 and NFR‑001 during audits |

### Acceptance Criteria
| AC ID | Story ID | Given | When | Then | Edge Cases |
|---|---|---|---|---|---|
| AC-001 | US-001 | The front‑desk user is logged in with role `front_desk` and the form is loaded | The user fills all mandatory insurance fields and clicks Submit | The system encrypts each field using pgcrypto, stores the row, creates an audit log entry, and shows a confirmation toast within 1 second | If any mandatory field is missing, the form displays inline validation errors; if encryption fails, submission is rejected and an error is logged |
| AC-002 | US-001 | The user enters an invalid insurance policy number format | The user attempts to submit the form | The system blocks submission and displays a clear error message indicating the format violation; no record is created and no write audit entry is logged | 
| AC-003 | US-002 | The clinician is authenticated with role `clinician` and has read permission on the patient record | The clinician requests insurance details for patient ID 12345 | The system decrypts the fields in transit using TLS 1.3, presents the data within 200 ms, and records an audit entry noting read access; UI masks non‑essential identifiers per privacy policy | 
| AC-004 | US-002 | The clinician's session has expired; The clinician clicks Refresh on the insurance view page; The system redirects to login, does not expose any PHI, and logs an unauthorized access attempt |
|| 
| AC-005 | US-003 | The patient lands on the intake page; They view the privacy notice and click "I Agree" before any data entry fields appear; The system records consent timestamp linked to the session and proceeds to the form; If the patient does not consent, the form remains hidden and a warning is displayed |
|| 
| AC-006 | US-004 | An administrator with role `admin` initiates an audit report generation for the past 30 days; The admin selects "Generate Insurance Access Report"; The system compiles a CSV containing user IDs, timestamps, operation types, stores it in an encrypted location, logs the report generation event, and completes within 5 seconds; If storage usage exceeds 90% of allocated disk space, the system warns about low storage, aborts report generation, and logs a warning |
|| 

### API Endpoint Definitions
- **POST /api/insurance** – Create a new insurance record. Request body includes encrypted fields; response returns confirmation receipt and status 201.
- **GET /api/insurance/{patientId}** – Retrieve encrypted insurance data for a given patient. Requires `clinician` role; response decrypted data, latency ≤200 ms, status 200.
- **GET /api/insurance/report?start={date}&end={date}** – Generate audit report of insurance data access. Requires `admin` role; returns encrypted CSV, status 200.
All endpoints return standardized error objects (`error_code`, `message`, `trace_id`) which are also recorded in the immutable audit log.

### Design Needs for Design Phase
- Field‑level encryption must use AES‑256‑GCM with per‑field data keys rotated every 90 days; pgcrypto functions `crypt`/`gen_salt` are used for storage.
- Transport encryption must enforce TLS 1.3 with strong cipher suites as per NIST SP 800‑52.
- Row‑level security policies must restrict SELECT/UPDATE on `insurance_info` table to roles `clinician` and `admin` only.
- Audit logging must capture `user_id`, `action`, `timestamp`, `record_id`, `error_code` (if any) in an append‑only immutable table.
- UI must display real‑time validation messages using Formik with custom regex patterns for policy numbers.
- All error messages must avoid leaking PHI and comply with HIPAA §164.514.

### Traceability
- US‑001 ↔ FR‑004 (real‑time validation), KPI‑001 (encryption compliance).
- US‑002 ↔ FR‑001 (view latency <200 ms), KPI‑003 (audit log completeness).
- US‑003 ↔ FR‑011 (consent capture), KPI‑006 (form receipt time).
- US‑004 ↔ FR‑003 (log retention), KPI‑007 (audit log integrity).
# Deployment Guide Overview

## Personas for HIPAA‑Compliant Patient Intake System (Deployment Guide Overview)

The following personas capture the primary human actors who interact with the PatientIntake system during deployment, configuration, and day‑to‑day operation. They are derived directly from the project requirements (collect demographics, role‑based access control, audit logging, and air‑gap Docker Compose deployment) and are essential for shaping user‑focused acceptance criteria and test scenarios.

### PER‑01: Patient
- **Role**: End‑user who provides personal health information via the web‑based intake form.
- **Primary Goals**:
  1. Submit accurate demographic, insurance, and medical history data.
  2. Receive confirmation that the submission was securely stored.
- **Key Responsibilities**:
  - Fill out all required fields; verify data before submission.
  - Trust that the system encrypts data in transit (TLS 1.3) and at rest (AES‑256).
- **Security Considerations**:
  - No direct system access; only interacts through HTTPS front‑end.
  - Must be informed of privacy notice per HIPAA § 164.528.
- **Pain Points**:
  - Limited technical literacy; needs clear error messages for validation failures.
  - May use personal devices on unsecured networks; encryption must protect data regardless.
- **Success Metrics**:
  - 99% of submissions complete without client‑side validation errors.
  - Patient reports confidence in data security in post‑submission survey (target ≥ 4/5).

### PER‑02: Front Desk Staff
- **Role**: Administrative user responsible for initiating intake sessions and managing patient records.
- **Primary Goals**:
  1. Open a new intake session for a patient and verify identity.
  2. Retrieve submitted forms for review or printing.
- **Key Responsibilities**:
  - Authenticate via role‑based credentials (admin → front‑desk role) – aligns with **FR‑002**.
  - Access the web UI to start/stop intake sessions.
  - Export PDF summaries for clinicians when authorized.
  - Must have read/write permissions limited to patient records they created (RBAC per **FR‑002**).
  - All actions logged in audit log (**FR‑005**) with timestamp and user ID.
- **Pain Points**:
  - Needs quick onboarding; UI must be intuitive under time pressure.
  - Must operate in an air‑gapped environment; cannot rely on external authentication services.
- **Performance Targets**:
  - Average time to open a new session ≤ 30 seconds.
  - Zero unauthorized access incidents during pilot (target 0).

### PER‑03: Clinician
- **Role**: Medical professional who reviews patient intake data and generates care plans.
- **Primary Goals**:
  1. View completed intake forms securely.
  2. Generate and download PDF intake summaries with watermark and timestamp (**FR‑004**).
- **Key Responsibilities**:
  - Authenticate with clinician credentials (role = clinician).
  - Access only patients assigned to them (RBAC enforcement).
  - Verify PDF integrity via embedded digital signature.
  - Must not be able to modify audit logs (immutability per **FR‑005**).
  - PDF export must embed watermarks indicating staff ID and export timestamp (**FR‑004**).
- **Pain Points**:
  - Requires fast access during appointments; latency must be low even in air‑gap setup.
  - Needs assurance that exported PDFs cannot be altered after download.
- **Performance Targets**:
  - PDF generation latency ≤ 2 seconds per request.
  - Clinician satisfaction with PDF watermark clarity ≥ 4/5.

### Persona Validation Checklist (for Test Automation)
| Persona | Test Scenario | Expected Result |
|---|---|---|
| PER‑01 | Form submission succeeds with valid data | HTTP 200 and audit log entry created |
| PER‑01 | Submission fails with missing required field | HTTP 400 with clear error message |
| PER‑02 | Front desk creates new session | Session record created, audit log entry recorded |
| PER‑02 | Front desk attempts to view another staff's patient record | Access denied (HTTP 403), audit log records attempt |
| PER‑03 | Clinician downloads PDF summary | PDF file contains watermark with staff ID and timestamp |
| PER‑03 | Clinician attempts to edit submitted form | Edit blocked, audit log records unauthorized edit attempt |

These personas provide the human context needed for downstream design contracts, test case generation, and deployment verification. They ensure that every functional requirement—especially those around security, role‑based access, and auditability—has a clear stakeholder perspective driving acceptance criteria.

---

## Acceptance Criteria Table
| ID | User Story | Given | When | Then |
|---|---|---|---|---|
| AC-001 / US-001 | Patient submits intake form | The patient is on a TLS‑protected HTTPS page and the form fields are rendered. | The patient fills all required demographic fields and clicks **Submit**. | The system encrypts each field at rest using AES‑256, stores the record in PostgreSQL with row‑level security, logs the write operation with user ID and timestamp, and returns a success message with a submission ID. *Missing required field → display inline validation error; no data stored.* *Network interruption after click → transaction rolled back; user sees retry prompt.* |
| AC-002 / US-002 | Front desk staff saves insurance data | Front desk staff is authenticated with role **front_desk** and has access to the intake form. | The staff enters insurance data and clicks **Save**. | The system validates insurer format (regex for policy number), encrypts the data at field level, writes to the database with an audit log entry noting role **front_desk**, and shows a green confirmation banner. *Invalid insurer code → error message displayed; record not saved.* *Attempt to edit another patient's insurance info → access denied (403) logged.* |
| AC-003 / US-003 | Clinician reads patient record | Clinician is logged in with role **clinician** and has read permission on patient records. | The clinician opens the patient's intake summary page. | The system decrypts only the medical‑history fields for this patient, presents them in a read‑only view, and records an audit log entry for the read operation including clinician ID and timestamp. *Record does not exist → 404 error logged.* *Clinician attempts to view a patient outside their care team → access denied logged.* |
| AC-004 / US-004 | Confirmation page after patient submission | Patient has just submitted the form successfully. | The system redirects to a confirmation page. | The page displays: "Your information was saved securely at **2026‑05‑08 14:32 UTC**." The message includes a reference to HIPAA §164.312(a)(2)(iv) for encryption at rest. No PHI is exposed in the URL or logs visible to the patient. *Browser back button after confirmation → no resubmission; idempotent handling.* |

---

## Design Needs (to be specified by Design)
- **Field‑level encryption schema**: algorithm (AES‑256‑GCM), key rotation schedule, and storage of keys in a hardware security module (HSM) or sealed vault.
- **Audit logging format**: JSON structure containing `event_type`, `actor_role`, `actor_id`, `timestamp`, `resource_id`, and `outcome`.
- **TLS configuration**: enforce TLS 1.3 with strong cipher suites; reference OpenSSL best practices.
- **Error handling UI guidelines**: consistent inline validation messages, retry mechanisms, and accessibility compliance (WCAG 2.1 AA).
- **Performance thresholds**: form submission latency ≤ 2 seconds under normal load; audit log write latency ≤ 100 ms.

These stories and criteria give Design a complete contract to draft technical specifications without exposing implementation details such as exact API endpoints or database schemas.
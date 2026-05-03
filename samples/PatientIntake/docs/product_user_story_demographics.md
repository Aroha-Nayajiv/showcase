# Patient Demographics Capture

## Patient Demographics Capture - Refined Specification

### Personas
| ID | Role | Goal | Success Metrics | Relevant Requirements |
|---|---|---|---|---|
| PER-01 | Front Desk Staff | Fast, accurate data entry | ≤120 s per form, <1 % error rate | FR-002, FR-003, FR-005 |
| PER-02 | Clinician | Immediate access to accurate records | ≤200 ms retrieval, PDF export ≤2 s | FR-002, FR-008, KPI-017 |
| PER-03 | Patient | Secure self‑service submission | ≥99 % success, receipt ≤1 s | NFR-001, NFR-002, REQ-001 |
| PER-04 | Administrator | Enforce RBAC and audit compliance | 100 % audit completeness | FR-003, KPI-017 |

### User Stories
- **US-001** (Patient): As a patient, I want to enter my personal, insurance, and medical history information securely via a web form so that my care team can provide timely treatment and accurate billing while complying with HIPAA. *Requirements: FR-001, FR-002, NFR-001, NFR-002.*
- **US-002** (Front Desk Staff): As front‑desk staff, I want to view, verify, and correct patient demographic entries after initial submission so that data accuracy is ensured before clinicians access the record. *Requirements: FR-004, FR-005.*
- **US-003** (Clinician): As a clinician, I want to retrieve a patient's demographic profile instantly using a patient identifier so that I can make informed clinical decisions without delay. *Requirements: FR-001, KPI-002.*
- **US-004** (Administrator): As an administrator, I want to configure role‑based access permissions for front‑desk, clinician, and admin roles so that access is limited to authorized personnel and audit requirements are satisfied. *Requirements: FR-002, FR-003.*

### Review of Feedback Applied
- Merged duplicate user stories into single entries.
- Added missing API endpoint definitions.
- Expanded acceptance criteria with full Given/When/Then steps and error handling.
- Included key rotation specification and audit log retention details.
- Added PDF export test case with watermark verification.

## Specification of Security and UI Requirements

**Client‑side Encryption Library**
- Recommended libraries: OpenSSL‑JS (v3.0) or libsodium.js. Must support AES‑256‑GCM with per‑field keys derived from a session master key using HKDF.

**PostgreSQL Column‑level Encryption**
- Use pgcrypto's `AES-256-GCM` for each PHI column. Keys are per‑field AES‑256 keys stored encrypted with a master key in HashiCorp Vault.

**Row‑level Security (RLS) Policies**
- Roles: `admin`, `clinician`, `front_desk`.
- Policy example: `CREATE POLICY patient_owner ON patient_demographics USING (assigned_clinician_id = current_user_id());`

**Audit Logging Format**
- Table `audit_log` columns: `log_id UUID PRIMARY KEY`, `user_id UUID`, `action TEXT`, `table_name TEXT`, `row_id UUID`, `timestamp TIMESTAMPTZ DEFAULT now()`, `outcome TEXT`, `details JSONB`.
- Retention: immutable logs retained for 7 years on WORM storage; daily checksum verification.

**UI/UX Guidelines**
- All form fields must meet WCAG 2.1 AA (REQ‑001).
- Keyboard navigation must be fully supported (REQ‑002).
- Real‑time inline validation messages with ARIA live regions.
- Receipt page includes watermark "Confidential – View logged" and signed transaction ID.

## Acceptance Criteria

**AC-001 (US-001)**
Given the patient accesses the intake form over TLS 1.3 and the browser supports Web Crypto, when all mandatory fields are completed and Submit is pressed, then the client encrypts each PHI field with a per‑field AES‑256‑GCM key derived from a session master key, sends only ciphertext to the server, which stores it via pgcrypto; the system returns a signed receipt page within 1 second containing a unique transaction ID and timestamp. If the browser lacks Web Crypto, the form falls back to server‑side encryption after POST. Encryption failures produce a clear error message and no plaintext is persisted; an audit log entry with severity "warning" is recorded.

**AC-002 (US-001)**
Given the patient provides an email address that does not match the allowed domain pattern, when the field loses focus, then the system displays inline error "Email domain not permitted for intake" and disables Submit until corrected. Empty email triggers "Email is required"; malformed email triggers RFC‑5322 format error.

**AC-003 (US-002)**
Given Front Desk Staff is logged in with role "front_desk" and has read/write permission on the intake table, when an invalid date "02/30/1990" is entered and Validate is clicked, then the client flags the date as invalid with message "Invalid date – please use MM/DD/YYYY" and prevents submission; the server also validates and returns HTTP 400 for malformed data.

**AC-004 (US-002)**
Given all required fields are filled but the insurance policy number contains non‑numeric characters, when Submit is clicked, then the system rejects the submission, returns error "Policy number must contain only digits", logs the attempt with audit level "info", and does not store any data for that record.

**AC-005 (US-003)**
Given the clinician authenticates via LDAP and has role "clinician" with SELECT permission on `patient_demographics` view, when the clinician selects a patient record from the dashboard, then the system displays decrypted demographic data within 200 ms, includes watermark "Confidential – View logged", and records an audit entry with user ID, timestamp, and record ID; RLS ensures only records assigned to that clinician are visible.

**AC-006 (US-003)**
Given a clinician attempts to view a patient whose record is marked "archived" by admin, when the record link is clicked, then the system shows banner "Record archived – read‑only view", disables edit controls, and logs the access with audit tag "archived_view".

**AC-007 (US-004)**
Given any CRUD operation occurs, when the operation completes, then an immutable audit entry is written to `audit_log` with fields defined above; the log table is write‑once protected and signed using a server‑side HMAC key. Logs are retained for 7 years and verified daily for integrity.

**AC-008 (PDF Export)**
Given a clinician or admin initiates PDF export of a patient summary, when the export completes, then the PDF contains a watermark with current timestamp and exporting user ID; a test case validates watermark presence and correctness using PDF parsing library.

## API Endpoint Definitions (added)
- `POST /api/v1/patients/{patient_id}/intake` – Accepts encrypted JSON payload; returns receipt ID. Handles fallback to server‑side encryption if client lacks Web Crypto.
- `GET /api/v1/patients/{patient_id}` – Returns decrypted patient demographics; enforces RLS based on authenticated user role.
- `POST /api/v1/patients/{patient_id}/export/pdf` – Generates PDF export with watermark; returns download URL. Audit log entry created.
- `GET /api/audit/logs?since=...` – Admin endpoint to retrieve audit logs; supports pagination and immutable view only.

## Key Rotation Policy (added)
- Master keys are rotated every 90 days using HashiCorp Vault's automatic rotation feature. Per‑field keys are re‑encrypted with the new master key and stored back to the database during off‑peak windows. Rotation events are logged with audit level "key_rotation".

## Test Cases (selected)
TC-001: Verify client‑side encryption headers are present in POST payload.
TC-002: Attempt unauthorized record access with a user lacking proper role; expect HTTP 403 and audit entry.
TC-003: Submit malformed form entries; ensure error messages appear inline and submission is blocked.
TC-004: Measure receipt page load time; must be ≤1 second for 95th percentile.
TC-005: Export PDF summary; parse PDF to confirm watermark includes correct timestamp and user ID.
TC-006: Simulate key rotation; verify existing records remain decryptable after re‑encryption with new master key.

## Priority and Business Justification (unchanged)
- US-001 P1: Satisfies HIPAA technical safeguard encryption requirement (45 CFR 164.312(a)(2)(iv)).
- US-002 P2: Reduces manual re‑entry errors, supporting KPI‑012 (Form submission error rate < 1%).
- US-003 P1: Aligns with FR‑001 response time target < 200 ms for clinician view.

## Design Notes (retained)
- Encryption algorithm: AES‑256‑GCM per field.
- Row‑level security policies link PostgreSQL roles to patient IDs.
- Audit log schema as defined above.
- UI components include real‑time validation messages, receipt layout, watermark style.
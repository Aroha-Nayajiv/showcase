# Insurance Entry User Journey

## Personas

### 5. PER-01 Front‑Desk Staff
Role: Administrative clerk who initiates the intake session when a patient arrives.
Goals: Capture complete insurance details quickly, verify eligibility, and flag missing or malformed fields before the patient proceeds.
Key Tasks:
1. Open the intake form and select "Enter Insurance Information".
2. Input insurer name, policy number, group number, subscriber name, and relationship.
3. Validate that required fields are non‑empty and conform to format patterns (e.g., alphanumeric policy number length 5‑15 characters).
4. Submit the form; system encrypts each field at the client side before transmission.
5. Handle encryption failures gracefully by displaying a user‑friendly error message and logging the failure for audit (new error handling added).
Success Metrics:
- Average entry time ≤ 45 seconds per patient (KPI‑02).
- Field‑level validation error rate < 1 % (FR‑005).
- 99 % of submissions result in successful encryption logs (audit log completeness KPI‑003).
Pain Points: Manual re‑entry when validation fails; uncertainty about required insurer‑specific codes.
Compliance Touchpoints: Must not view PHI beyond insurance fields; audit log must capture user ID, timestamp, and operation type (FR‑003).

### 2. PER-02 Clinician
Role: Physician or nurse who reviews patient records after intake.
Goals: Verify insurance coverage before providing care, ensure that the recorded data matches the insurer's eligibility response.
Key Tasks:
1. Access patient record via role‑based UI; only insurance fields are visible for review.
2. Trigger eligibility check; system reads encrypted insurance data, decrypts in a secure backend, and returns status.
3. Add notes if coverage is insufficient.
4. Decryption failure handling added: if decryption fails, display a clear error message, abort the operation, and log the incident (new AC).
Eligibility check latency ≤ 200 ms (KPI‑02).
Zero unauthorized access incidents (FR‑002).
Pain Points: Delays if decryption fails; need for clear error messages when insurer data is incomplete.
Compliance Touchpoints: Access must be logged with clinician ID, patient ID, and read operation (FR‑003). Data at rest remains encrypted (NFR‑001).

### 6. PER-03 Patient
Role: Individual providing personal and insurance information.
Goals: Complete the insurance section accurately without exposing sensitive data to the browser or network.
Key Tasks:
1. Fill out insurer name, policy number, group number, subscriber name, relationship, and effective dates.
2. Receive real‑time validation feedback (e.g., "Policy number must be 5‑15 alphanumeric characters").
3. Submit; client‑side encryption ensures data never travels in clear text (NFR‑002).
4. TLS‑1.3 enforcement added: browser must negotiate TLS‑1.3; any fallback is rejected (new security check).
Form completion success rate ≥ 98 % (KPI‑04).
No client‑side script errors reported (> 0 %).
Pain Points: Confusing field labels; fear of data leakage.
Compliance Touchpoints: Consent notice displayed before data entry (FR‑010). All transmitted data encrypted via TLS 1.3 (NFR‑002).

### 4. PER-04 Administrator
Role: System admin responsible for configuring role‑based access and audit‑log retention.
Goals: Ensure that only Front‑Desk Staff and Clinicians can read/write insurance fields and that logs are retained for seven years (KPI‑003).
Key Tasks:
1. Define PostgreSQL roles front_desk, clinician, admin with appropriate row‑level security policies.
2. Verify that audit logging (`log_statement = 'all'`) captures every INSERT/UPDATE/SELECT on the insurance table.
3. Implement audit log retention policy: retain logs for 7 years on immutable storage and purge older entries securely (new retention policy added).
4. Enforce privilege escalation checks; no paths discovered in security review.
100 % of audit entries contain user ID, operation type, and timestamp.
No privilege escalation paths discovered in security review.
Compliance Touchpoints: Must enforce HIPAA technical safeguard § 164.312(a)(2)(iv) for encryption key management (knowledge gap noted).

## Acceptance Criteria

AC-001 | US-001 | The front‑desk user is authenticated with the front‑desk role and the patient record is open | The user fills all mandatory insurance fields and clicks Submit | The system encrypts each field at rest using pgcrypto, stores the encrypted values, logs the write operation with timestamp and user ID, and displays a confirmation within 1 second (KPI‑001) | If any mandatory field is missing, the system shows an inline validation error and does not submit; error rate must stay below 1 % per batch (FR‑005)
AC-002 | US-001 | The front‑desk user has entered an invalid insurance policy number format | The user attempts to submit the form | The system rejects the submission, highlights the field, logs a validation failure event (audit log entry) | If the user repeatedly submits invalid data, the system throttles further attempts after three failures within 5 minutes|
AC-003 | US-002 | The clinician is logged in with the clinician role and has read permission on the patient's record | The clinician opens the patient's insurance section | The system decrypts the fields in‑memory only, displays them in the UI, and records an audit log entry indicating read access with timestamp and clinician ID | If decryption fails, the system shows a clear error message, aborts display, and logs the failure (new error handling) | If the clinician's session has expired, the system redirects to login and does not expose any data|
AC-004 | US-003 | An administrator accesses the access‑control configuration UI | The admin adds a new role insurance‑auditor with read‑only permission on insurance tables | The system updates PostgreSQL role grants, logs the change as an admin action, and the new role can view but not export insurance data | If the admin attempts to grant export permission, the system blocks the change and raises a policy violation warning|
AC-005 | US-001 | The front‑desk user submits a form for a patient who already has an active insurance record | The system detects duplicate policy number for the same patient | The system presents a warning dialog offering to update existing record or cancel; any update creates a new audit version while preserving prior encrypted values|
AC-006 | US-004 | Front‑Desk Staff experiences an encryption failure during submission | System displays a user‑friendly error message, retries up to two times, then aborts and logs the failure with error code ENCRYPT_FAIL (new AC) |
AC-007 | US-005 | Clinician encounters a decryption error when viewing insurance data | System shows an error message "Unable to decrypt insurance information – please contact support", logs event with error code DECRYPT_FAIL, and does not display any partial data (new AC) |
AC-008 | US-002 | PDF export of patient intake summary includes watermark with timestamp and exporting user ID | System generates PDF, embeds watermark "Exported by {user_id} at {ISO8601_timestamp}", validates watermark presence in automated test (new AC) | Export latency must be ≤ 2 seconds (new KPI)
AC-009 | US-003 | Audit log retention policy enforcement | System retains audit_log entries for 7 years on immutable storage; older entries are securely archived; retention compliance verified weekly by audit script (new AC) |

## Design Needs

**Field‑level Encryption Specification**: Algorithm AES‑256‑GCM with per‑field keys managed by a master key stored in HashiCorp Vault. Encryption performed client‑side using OpenPGP.js before transmission; server stores ciphertext using pgcrypto's `AES-256-GCM`. Failure to encrypt triggers ENCRYPT_FAIL handling as defined in AC‑006.

**Audit Log Schema**: Table `audit_log` columns: `event_id` UUID primary key, `user_id` VARCHAR, `action` VARCHAR (INSERT/UPDATE/SELECT/EXPORT), `entity` VARCHAR (insurance_info), `timestamp` TIMESTAMPTZ DEFAULT now(), `details_json` JSONB (includes error codes, field names). Retention policy: retain rows for 7 years on immutable WORM storage; archival script moves older rows to cold archive quarterly.

**Role‑Based Access Matrix**: PostgreSQL roles – `front_desk` (INSERT/UPDATE on `insurance_info`), `clinician` (SELECT on `insurance_info`), `admin` (ALL privileges), `insurance_auditor` (SELECT only, no EXPORT). Row‑level security policies enforce that `front_desk` can only access records where `assigned_clinician_id` matches their clinic assignment. Export permission is granted only to `admin`.

**Performance Metrics**: Form submission latency ≤ 200 ms for encryption + DB write (KPI‑001). Eligibility check latency ≤ 200 ms (KPI‑02). PDF export latency ≤ 2 seconds (new KPI).

**Accessibility**: All form fields must meet WCAG 2.1 AA contrast ratio ≥ 4.5:1 and have appropriate ARIA labels (REQ‑001). Keyboard navigation must allow full form completion without mouse (REQ‑002).

**TLS Enforcement**: Browser must negotiate TLS 1.3; any fallback to TLS 1.2 or lower results in connection termination with error message "Insecure connection – upgrade required". All API endpoints enforce HSTS with max‑age 31536000 seconds.

**PDF Export Verification**: Automated test validates that generated PDF contains watermark text matching pattern "Exported by {user_id} at {timestamp}" and that watermark is visible on each page. Test also checks that PDF size does not exceed 2 MB per export.

## Prioritization Overview
The Insurance Entry User Journey is a core component of the PatientIntake system. It captures payer information, validates coverage eligibility, and links the insurance record to the patient demographic profile. Because the system must satisfy HIPAA technical safeguards, role‑based access control, auditability, and TLS 1.3 enforcement, this journey is ranked highest in the MVP.

### 5. User Stories
| ID | Persona | Goal | Benefit | Priority |
|----|---------|------|---------|----------|
| US-001 | Front‑Desk Staff | Enter patient insurance details into a secure web form | The patient's coverage can be verified before clinical intake, reducing delays and ensuring correct billing | 1 |
| US-002 | Clinician | View a patient's verified insurance information after authentication | I can confirm coverage eligibility and avoid providing care without reimbursement | 2 |
| US-003 | Administrator | Configure insurance provider list and validation rules | The system can enforce up‑to‑date payer contracts and maintain compliance with payer agreements | 3 |
| US-004 | Front‑Desk Staff | Receive immediate validation feedback on insurance fields (e.g., policy number format) | Errors are corrected at entry time, keeping data quality high and audit log entries accurate | 2 |
| US-005 | Auditor | Export an audit‑ready report of all insurance entry actions with timestamps and user IDs | I can demonstrate compliance with HIPAA audit requirements during inspections | 1 |

### 6. Priority Ranking and Business Justification
| Rank | Stories | Rationale |
|------|---------|----------|
| 1 (Critical) | US-001, US-005 | Directly support HIPAA §164.312(a)(2)(iv) encryption and audit requirements; failure would constitute a compliance breach |
| 2 (High) | US-002, US-004 | Enable clinicians to make billing decisions quickly and reduce front‑desk data‑entry errors, improving operational efficiency by an estimated 15 % |
| 3 (Medium) | US-003 | Administrative configuration is essential for long‑term maintainability but can be deferred until post‑MVP release |

### 7. Audit Log Retention Policy
All audit log entries are stored in an append‑only immutable bucket and retained for a minimum of seven (7) years in accordance with FR‑003 and regulatory requirements. Logs are periodically verified for integrity using SHA‑256 digests.

### 8. PDF Export Limits
The export service caps each PDF at 10 000 records. When the result set exceeds this limit, the service automatically splits the output into sequentially numbered PDFs (e.g., export_01.pdf, export_02.pdf) and creates a corresponding audit log entry for each part.

### 9. Traceability Matrix
| Artifact ID | Linked FR(s) | Linked KPI(s) |
|-------------|--------------|---------------|
| US-001 | FR-001, FR-006 | KPI-001 (response time), KPI-004 (form success rate) |
| US-002 | FR-001, FR-002 | KPI-001 (response time), KPI-003 (audit log completeness) |
| US-003 | FR-007 | KPI-014 (configuration drift) |
| US-004 | FR-005 | KPI-005 (validation error rate) |
| US-005 | FR-003, FR-008 | KPI-003 (audit log completeness), KPI-030 (watermark accuracy) |
| AC-001…AC-005 | All relevant FRs above | Corresponding KPIs as shown |
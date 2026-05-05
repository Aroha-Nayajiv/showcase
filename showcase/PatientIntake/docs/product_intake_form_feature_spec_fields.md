# Secure Intake Form Field Specification

## Secure Intake Form Field Specification – Personas & Interaction Mapping

### 1. Personas
| ID   | Persona            | Goal                                                            | Primary Interactions                                                                                 | Permissions          |
|------|--------------------|-----------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|----------------------|
| PER-01 | Front Desk Staff   | Capture complete patient intake data quickly and accurately.      | Enter demographics, insurance info, medical history; submit form; request PDF export for clinician review. | Create & Read |
| PER-02 | Clinician          | Review patient intake data to provide care decisions. | Access submitted forms; view PDF summaries; add clinical notes (out of scope). | Read |
| PER-03 | Compliance Officer Verify that intake process complies with HIPAA and audit requirements. |
 Review audit logs; validate encryption at rest/in-transit; ensure PDF watermark & timestamp are present. |
 | Read & Audit |

### 2. Interaction Flow
1. **Form Access –** Front Desk Staff authenticates via role‑based login (admin‑controlled). System enforces TLS 1.3 for all traffic (HIPAA §164.312(e)(1)).
2. **Data Entry –** Staff fills structured sections: Demographics, Insurance, Medical History. Each field is flagged for field‑level encryption using OpenSSL‑compatible libs (AES‑256‑GCM). Validation rules enforce required formats (e.g., SSN pattern `XXX‑XX‑XXXX`, DOB not future).
3. **Submission –** On “Submit”, the client encrypts each field before transmission; server stores encrypted blobs in PostgreSQL columns with pgcrypto. An audit log entry (FR‑003) is created recording user ID, timestamp, operation type "CREATE".
4. **PDF Generation Request –** Clinician selects a patient record and clicks “Generate PDF”. System assembles decrypted data in memory only, renders PDF via wkhtmltopdf, applies watermark "Confidential – Authorized Staff Only" and embeds an access timestamp in the footer.
5. **PDF Export –** The generated PDF is streamed over TLS to the clinician’s browser. An audit log entry records "PDF_EXPORT" with user ID and timestamp.
6. **Compliance Review –** Compliance Officer accesses audit‑log UI, filters by operation type, verifies that every read/write has a corresponding immutable log entry (AU‑6). Officer also checks that each exported PDF contains the required watermark and timestamp (NFR‑003).

### 3. Mapping Matrix
| Interaction               | Actor               | System Component                     | Security Controls                                            | Event Type |
|--------------------------|---------------------|--------------------------------------|-------------------------------------------------------------|------------|
| Open Form | Front Desk Staff | Web UI / Auth Service | TLS 1.3, MFA (NIST SP 800‑53 IA‑2) | Login_success |
| Field Entry Validation | Front Desk Staff | Client‑side JS validator | Input sanitization, regex checks | None |
| Encrypted Submit | Front Desk Staff | API endpoint `/intake/submit` | Field‑level AES‑256‑GCM, HMAC verification | CREATE |
| PDF Generation | Clinician | PDF Service (wkhtmltopdf) | In‑memory decryption only, no persisted plaintext | PDF_EXPORT |
| PDF Download | Clinician | File streaming layer | TLS 1.3, CSP header `frame-ancestors 'none'` | DOWNLOAD |
| Audit Review | Compliance Officer | Audit Log UI / DB query layer | Role‑based read permission, read‑only view | VIEW |

### 4. Edge Cases & Failure Handling
* **Network Interruption During Submit –** Client retries up to three times with exponential backoff; if still fails, form state is saved locally and user is prompted to retry after reconnection. An audit entry "SUBMIT_FAILED" records the attempt.
* **Encryption Key Rotation –** New submissions use the new key; existing records remain decryptable via key version metadata. Audit log entry "KEY_ROTATION" is generated.
* **Unauthorized PDF Export Attempt –** If a user without Read permission calls `/pdf/export`, system returns HTTP 403 and logs "UNAUTHORIZED_EXPORT".
* **Audit Log Tampering Detection –** Logs are written with append‑only WAL; any discrepancy triggers an alert "AUDIT_INTEGRITY_FAILURE".

### 5. Prioritization & Business Justification
| Persona ID | Priority Rank | Business Justification |
|------------|--------------|------------------------|
| PER-01     | 1            | Directly creates protected health information; errors affect downstream compliance metrics (KPI-001, KPI-003). |
| PER-02     	|	2	|	Needs timely access to accurate intake data; PDF export is critical for care decisions and must be secure.	|
| PER-03     	|	3	|	Provides oversight; essential for audit readiness but read‑only, can be implemented after core data capture stabilizes.	|

### US-001: Front Desk Staff submits patient demographics
**Persona:** PER-01  
**Goal:** Capture complete patient intake data securely.

*Given* the Front Desk Staff is authenticated with role *Front Desk* and the intake form loads over TLS 1.3,
*When* the staff enters valid demographic data that satisfies all field validation rules,
*And* clicks **Submit**,
*Then* each field is encrypted with AES‑256‑GCM before storage,
*And* the encrypted data is persisted in PostgreSQL column‑level encryption,
*And* a success message "Submission successful" is displayed,
*And* an audit log entry is created with `event_type="CREATE"`, `actor_id=<user_id>`, `timestamp=<now>`.

#### Negative Flow – Missing Required Field
*Given* a required field is left empty,
*When* the staff attempts to submit,
a *Then* the form displays a field‑specific error message,
and *Then* no data is persisted nor an audit entry created.

### US-002: Network Failure During Submission
**Persona:** PER-01  
**Goal:** Ensure reliability under intermittent connectivity.

*Given* the staff has filled all required fields and initiated submission,
*When* the network connection drops after the client has sent the encrypted payload,
*Then* the client retries up to three times with exponential backoff,
and *If* all retries fail,
a *Then* the client stores the form state locally and shows "Submission failed – please retry",
and *Then* no partial data remains in the database,
and *Then* an audit log entry `event_type="FAILED"` is recorded with failure reason.

### US-003: Insurance Policy Number Validation
**Persona:** PER-01  
**Goal:** Prevent invalid insurance data entry.

*Given* the staff selects an insurance provider from the validated list,
*When* the staff enters a policy number containing non‑numeric characters or length outside 10–12 digits,
*Then* the form displays error "Policy number must be numeric and 10–12 digits",
and *Then* submission is blocked,
and *Then* no CREATE audit entry is generated.

### US-004: Successful Insurance Data Capture
**Persona:** PER-01  
**Goal:** Store validated insurance information securely.

*Given* all insurance fields are correctly filled and encryption keys are available,
*When* the staff clicks **Submit**,
*Then* each insurance field is encrypted with AES‑256‑GCM and stored,
and *Then* an audit log entry `event_type="CREATE_INSURANCE"` is recorded,
and *Then* the PDF generation flag for this record remains false until clinician review.

### US-005: Clinician Edits Medical History
**Persona:** PER-02  
**Goal:** Allow secure edit of medical history.

*Given* a Clinician accesses an existing patient record with encrypted medical history fields,
*When* the Clinician edits the "Allergies" section and saves,
*Then* the system decrypts the field in memory only for the session,
and *Then* re‑encrypts the updated value on save,
and *Then* updates the audit log with `event_type="UPDATE_MEDICAL_HISTORY"`, storing previous value hash for tamper evidence.

### US-006: PDF Generation & Watermark Verification

#### Clinician Path
*Given* a Clinician selects "Generate PDF" for a patient record,
*When* the system assembles decrypted data in memory and renders a PDF,
*Then* the PDF includes watermark "Confidential – Authorized Staff Only" and a footer timestamp,
and *Then* the PDF is streamed over TLS 1.3,
and *Then* an audit log entry `event_type="PDF_EXPORT"` is recorded.

#### Compliance Officer Verification
*Given* a Compliance Officer reviews the generated PDF,
*When* they inspect watermark and timestamp,
*Then* they confirm presence; any missing element raises a compliance alert linked to `NFR-003`.

---

## Traceability Matrix
| Requirement ID | Description                                 | Linked User Story(s) |
|-----------------|---------------------------------------------|----------------------|
| FR-001          | Secure demographic capture                  | US-001               |
| FR-002          | Insurance data validation & storage         |	US-003, US-004	|
| FR-003 | Audit logging for all operations | US-001, US-002, US-004, US-005, US-006 |
| NFR-001 | TLS 1.3 for all transport layers | All interactions |
| NFR-003 | Mandatory audit logging of every read/write operation | All audit entries |
| KPI-001 | <200 ms response time for form submissions | US-001 |
| KPI-003 | Successful audit log generation for every submission | US-001, US-002 |
| RISK-001 | Unauthorized data exposure due to key compromise | Mitigation in Edge Cases |
| RISK-002 | Open-source component vulnerabilities (e.g., wkhtmltopdf) | Mitigation in Edge Cases |
| RISK-003 | Deployment misconfiguration leading to insecure TLS settings | Mitigation in Edge Cases |
| RISK-006 | Insufficient multi‑tenant isolation in SaaS deployment | Row-level security per tenant |
---

## Risks & Mitigations
| Risk ID   | Description                                                   | Mitigation                                                                                 |
|-----------|---------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| RISK-001   | Unauthorized data exposure due to key compromise              |	Implement key rotation policy; store keys in HSM; audit key usage (see Edge Cases).        |
| RISK-002   |	Open-source component vulnerabilities (e.g., wkhtmltopdf)      |	Regular dependency scanning; apply patches promptly.                                      |
| RISK-003    | Deployment misconfiguration leading to insecure TLS settings      | Use automated configuration validation scripts; enforce TLS 1.3 via CI checks.| RISK-006    | Insufficient multi-tenancy isolation in SaaS deployment        | Enforce row-level security per tenant; separate encryption keys per tenant.| --- |

## Open Issues / Knowledge Gaps

- Exact HIPAA §164.312(a)(2)(iv) technical safeguard requirements for encryption key management
- PostgreSQL row-level security performance characteristics at 10M+ audit log rows

## Feature Specification – Patient Intake System

### User Stories & BDD Acceptance Criteria

**US-001 – Capture Patient Intake (Front Desk)**

Given a front-desk staff member is authenticated via MFA
When they complete the structured intake form with demographic, insurance and medical history data
Then the system stores the data encrypted at rest (AES-256-GCM)
And an immutable audit log entry (AC-001) is created with operation type CREATE
And the submission response time is ≤200 ms.

*Traceability*: FR-001, FR-002, NFR-003, KPI-001

**US-002 – Review Patient Record (Clinician)**

Given a clinician is authenticated and assigned to a patient record
When they request to view the patient’s completed intake record
Then the system renders the decrypted data to the UI
And an audit log entry (AC-002) with operation type READ is recorded before rendering
And access is denied if the record is not assigned to the clinician.

*Traceability*: FR-003, NFR-003, KPI-002

**US-003 – Audit Log Review (Compliance Officer)**

Given a compliance officer accesses the audit console
When they query audit logs for a given time window (e.g., last 24 hours)
Then the system returns a list of entries showing timestamp, actor ID, operation type, affected fields and cryptographic hash
And each entry complies with NIST 800-53 AC-002 and AU‑6 controls
And the officer can export the result as a PDF with watermark and hash verification.

*Traceability*: FR-001, FR-002, FR-003, NFR-003, KPI-003

### Functional Requirements – Audit Logging
| ID     | User Story | Scenario                     | Preconditions                                 | Steps                                            | Expected Result |
|--------|-----------|-----------------------------|-----------------------------------------------|--------------------------------------------------|-------------------|
| AC-001 | US-001    | Create patient record       | Secure intake form loaded; user authenticated   | 1. Submit form<br>2. System writes audit entry   | Immutable audit log entry with timestamp (ISO‑8601), actor ID, operation CREATE, hash of encrypted payload stored in `audit_log` table. If DB unavailable → buffer locally and retry; after 5 min alert raised and submission rejected. |
| AC-002 | US-002    | Read patient record         | Clinician authenticated & has assignment        | 1. Click “View Details”<br>2. System writes audit entry before rendering   | Audit entry with operation READ recorded; if logger fails → read blocked and error “Audit service unavailable – access denied”. |
| AC-003 | US-003    *Update insurance info*   *Admin authenticated & authorized*   *1. Submit update form<br>2. System computes before/after hashes<br>3. Writes audit entry*   *Audit entry with operation UPDATE includes before-and-after encrypted field hashes; if before-hash cannot be computed → abort update, log warning without persisting changes.* |

### Role-Based Access Control (RBAC)
| ID     | User Story               | Scenario                         | Preconditions                                 | Steps                                            | Expected Result |
|--------|--------------------------|----------------------------------|-----------------------------------------------|--------------------------------------------------|-------------------|
| AC-004 | US‑001 (Front Desk)      | Create intake record             | Front Desk staff authenticated via MFA        | Attempt CREATE on `patient_intake` table        | Operation permitted; audit entry recorded; no READ or EXPORT permissions granted. If session token expires → request rejected “Session expired”, no partial data persisted. |
| AC-005 | US‑002 (Clinician)       | Read assigned patient record     | Clinician authenticated & assigned to patient  | Request READ of patient record                  | Access granted; audit entry recorded with outcome=GRANTED.<br>If record outside assignment → access denied; audit entry recorded with outcome=DENIED. |
| AC-006 *(placeholder for future RBAC rules)* |

### Design Needs (Reference for downstream Design phase)
* Field‑level encryption: AES‑256‑GCM, per‑field keys derived from master key in HSM; rotation every 90 days.
* Access Control Matrix: mapping of encrypted fields to roles (e.g., SSN readable only by admin/clinician).
* Audit‑Log Schema: `event_id`, `event_type`, `user_id`, `timestamp`, `entity_id`, `entity_type`, `hash`; append‑only table with PostgreSQL row‑level security.
* PDF Export Metadata: watermark `{UserName} - {Role}`, timestamp format `YYYY-MM-DD HH:mm:ss Z`, file hash SHA‑256.
* Performance Targets: form submission ≤200 ms; PDF generation ≤3 s; audit log query ≤500 ms for 30‑day window.

---
All items above are traceable to the listed functional and non‑functional requirements.
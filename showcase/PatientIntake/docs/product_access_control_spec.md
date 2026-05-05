# Access Control Specification (Overview)

# Traceability Matrix
| Requirement ID                                 | Linked User Story(s) |
|-----------------------------------------------|----------------------|
| FR-001 (Secure demographic capture)           | US-001 |
| FR-002 (Role‑based access control)            | US-002, US-003 |
| FR-003 (Audit logging)                       | US-001, US-002, US-003 |
| NFR-001 (Encryption at rest & in transit)    | US-001, US-002 |
| FR-004 (PDF Export with watermark)            | US-004 |
| FR-005 (Role revocation)                     | US-005 |
| NFR-003 (Mandatory audit logging)           | US-001, US-002, US-003 |

### Edge‑Case & Failure Scenarios
* **Encryption Key Rotation** – When a key rotation event occurs, all new records must be encrypted with the new key while existing records remain decryptable; an audit entry `KEY_ROTATION` is logged.
* **Audit Log Tampering Attempt** – Any attempt to delete or modify an audit record triggers an automatic alert and logs `AUDIT_TAMPER_DETECTED`.
* **Session Expiry** – All actions performed after session timeout must redirect to login and log `SESSION_EXPIRED`.

## Access Control Specification – Prioritized Backlog (MVP)

### 1. Prioritized User Stories

| ID     | Persona          | Goal                                                                                 | Benefit                                                                                                   | Priority |
|--------|------------------|--------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|----------|
| US-001 | Front Desk Clerk | Create a new patient intake record with encrypted demographic and insurance fields      | Patient data is captured securely and complies with HIPAA §164.312(a)(2)(iv)                               | High     |
| US-002 | Clinician        | View and edit existing patient intake records that I am assigned to | I can provide timely care while maintaining auditability of all changes | High     |
| US-003 | Administrator    | Assign role‑based permissions and audit log retention policies | The system enforces least‑privilege access and satisfies NFR‑003 audit logging requirement | High     |
| US-004 | Front Desk Clerk | Export a PDF summary of a patient's intake record with a watermark and timestamp | Authorized staff can share a compliant document while preserving provenance | High     |
| US-005 | Administrator | Revoke or modify user roles in case of staff turnover or security incidents | Access rights remain current, reducing risk of unauthorized data exposure (RISK-001) | Medium    |

### 2. Acceptance Criteria

| AC ID   | Story ID | Given                                                                                                                                                     | When                                                                                                   | Then                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
|--------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AC-001 | US-001   | The clerk is authenticated with a valid front‑desk credential and TLS 1.3 is active. The clerk submits the intake form with all required fields filled. |
 The system encrypts each field at rest using AES‑256‑GCM, stores the record, and creates an audit log entry containing timestamp, user ID, and operation type **CREATE**. |
 If any required field is missing, the system returns a validation error without creating a record or log entry.
 |
| AC-002 | US-001   | Same as AC‑001 but the network connection is interrupted after form submission.
 |
 The system attempts to write the encrypted record.
 |
 The transaction is rolled back; no partial data is persisted; an error is logged with **TRANSACTION_FAILURE**.
 Subsequent retry by the clerk succeeds and creates a single audit entry.
 |
| AC-003 | US-002   |
 A clinician is logged in with role *clinician* and has been granted read/write permission on patient ID 123.
 |
 The clinician opens the patient record and modifies the medical‑history field.
 |
 The updated field is re‑encrypted, the version number increments, and an audit log entry **UPDATE** records old and new hash values.
 If the clinician attempts to edit a record they are not assigned to, the system returns **ACCESS_DENIED** and logs the attempt.
 |
| AC-004 | US-003   |
 An administrator accesses the role‑management console with MFA enabled.
 |
 The admin changes the *front‑desk* role to remove **export_pdf** permission.
 |
 The permission change is saved atomically; all subsequent export attempts by front‑desk users are denied and logged as **PERMISSION_CHANGE**.
 If the admin provides an invalid permission name, the system rejects the change with a descriptive error and no audit entry is created.
 |
| AC-005 | US-004   |
 A front‑desk clerk with **export_pdf** permission views a completed intake record.
 |
 The clerk clicks **Export PDF**.
 |
 The system generates a PDF using wkhtmltopdf, embeds a semi‑transparent watermark containing the clerk's username, adds an ISO‑8601 timestamp footer, stores the file in an encrypted bucket; an audit entry **EXPORT_PDF** records file hash and user ID.
 If the PDF generation library fails, the system returns an error message and logs **PDF_GENERATION_FAILURE** without exposing patient data.
 |
| AC-006 | US-005   |
 An administrator initiates a role revocation for a departing staff member.
 |
 The admin deactivates the user account and removes all role bindings.
 |
 All active sessions are terminated; future API calls from that user return **ACCOUNT_INACTIVE**; an audit entry **ACCOUNT_DEACTIVATION** records who performed the action and when.
 If the deactivation request targets a non‑existent user, the system returns **USER_NOT_FOUND** and logs the anomaly for security review.
 |

### 3. Design Needs for Design Phase

* **Permission Matrix** – JSON schema mapping each role (admin, clinician, front‑desk) to allowed actions (`CREATE`, `READ`, `UPDATE`, `EXPORT_PDF`, `ROLE_MANAGE`).
* **Encryption Specification** – Algorithms: AES‑256‑GCM for data at rest; TLS 1.3 with forward secrecy for in‑transit traffic. Key rotation every 90 days; keys stored in HashiCorp Vault.
* **Audit Log Format** – Immutable JSON entries containing: `event_id`, `timestamp` (UTC), `user_id`, `operation_type`, `resource_id`, `before_hash`, `after_hash`, `outcome` (`SUCCESS`/`FAILURE`), optional `error_code`. Stored in append‑only PostgreSQL table or immutable object store.
* **PDF Generation Contract** – Use wkhtmltopdf ≥ 0.12.6; watermark pattern `"Exported by {username}"`; timestamp format ISO 8601; PDF metadata must not contain PHI beyond displayed fields; generated files stored in encrypted S3‑compatible bucket with bucket‑level ACLs.
* **Failure Handling Policy** – Standard error codes: `VALIDATION_ERROR=4001`, `ACCESS_DENIED=4003`, `TRANSACTION_FAILURE=5001`, `KEY_ROTATION_ERROR=5002`. User‑facing messages must be generic (“Operation could not be completed”) while logs retain detailed codes.
* **Performance Thresholds** – Form submission ≤ 2 seconds under normal load; PDF export ≤ 5 seconds; audit log write latency ≤ 100 ms.

## Personas

| ID      | Persona          | Description                                                                                              |
|---------|-------------------|--------------------------------------------------------------------------------------------------------|
| PER-01  | Front Desk Staff  | Staff who enters patient demographics, insurance information, and medical history via the web form.   |
| PER-02  │ Clinician        │ Clinician who reviews and updates patient intake records and generates PDF summaries.                 |
| PER-03  │ Administrator    │ System administrator responsible for user provisioning, role assignment, and audit‑log oversight.|

## Priority Justification

High‑priority stories (US‑001 & US‑002) directly enable core HIPAA‑required functions: secure data capture and controlled PDF export. Medium story (US‑003) supports governance and compliance but can be iterated after MVP launch.

## Metrics & Success Criteria

* **Access Control Accuracy** – ≥ 99.9 % of permission checks pass in automated tests (KPI-002).
* **Encryption Verification** – All stored fields must be encrypted; automated test validates no plaintext in DB snapshots (KPI-001).
* **Audit Log Completeness** – 100 % of create/read/update/delete operations generate an audit entry (KPI-003).
* **PDF Export Compliance** – Every exported PDF contains correct watermark and timestamp; manual spot‑check of 10 random exports shows 0 violations (KPI-004).
* **User Acceptance** – Front Desk staff complete intake within 2 minutes 95 % of the time (KPI-001).
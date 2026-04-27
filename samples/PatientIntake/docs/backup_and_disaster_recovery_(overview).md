# Backup and Disaster Recovery (Overview)

### Personas and Roles

- **PER-01**: Handles patient data entry and initial verification
  - **Goals**: Quickly capture complete patient demographics, insurance, and history while ensuring data is encrypted at field level.
  - **Backup Concerns**: Needs assurance that entered records within 5 minutes require re‑entry, violating seconds; backup failure rate <0.5% per month.
  - **Failure Scenarios**: If the local PostgreSQL instance is unavailable, the system must queue entries retry every 30 seconds, with maximum queue size of 500 records. **Added** explicit error handling to raise an alert after three consecutive queue failures.

- **PER-02**: Reviews patient forms, updates medical history, and care plans
  - **Goals**: Access up‑to‑date patient data with minimal latency; rely on backup to restore any corrupted records without data loss.
  - **Concerns**: Must be able to recover (PITR) for a specific patient record within the last 30 days.
  - **Success Metrics**: Restoration of a single patient record completes within 2 minutes 95% of the time; audit log shows restoration event immutable.
  - **Failure Scenarios**: If restoration exceeds 5 minutes, system must alert compliance officer.

- **PER-03**: Manages PostgreSQL configuration, schedules, and access
  - **Goals**: Daily full backups and hourly incremental backups performed without manual intervention.
  - **Backup Concerns**: Must verify backup integrity using checksum (SHA‑256) and retain as HIPAA §164.308(a)(1)(ii).
  - **Success Metrics**: 100% of scheduled backups pass verification; backup storage utilization never exceeds 80% of allocated disk.
  - **Failure Scenarios**: On automatic good backup generate an alert with severity HIGH.

- **PER-04**: Oversees HIPAA compliance, log disaster‑recovery policy enforcement
  - **Goals**: Demonstrate that backup and restore processes meet NIST SP 800‑53 AC‑2, AU‑2.
  - **Concerns**: Requires immutable audit log backup and restore operation, retained for at least 7 years.
  - **Success Metrics**: Audit log shows 100% of backup/restore with tamper‑evident signatures; quarterly drill success ≥ 90%.
  - **Failure Scenarios**: If audit log falls below 7 years, system must flag non‑compliance and block further backups until remedied.

- **PER-05**: Docker Compose deployment, monitors container health, ensures air‑gap integrity
  - **Goals**: Ensure inside isolated no external network access.
  - **Backup Concerns**: Use open‑source tools (e.g., pgBackRest) encrypted backup files stored on encrypted volume.
  - **Success Metrics**: Backup containers restart automatically on failure; encryption as required.
  - **Failure Scenarios**: If container crashes more than three times within an hour, system triggers a high‑priority incident.

### Acceptance Criteria Library

- **AC-001**: Encryption of PHI fields at rest using AES‑256‑GCM with per‑field keys stored in Vault. Metric: 100% of PHI fields encrypted; encryption latency ≤ 5 ms per field.
- **AC-002**: Transport security using TLS 1.3 with forward‑secrecy cipher suite TLS_AES_256_GCM_SHA384; client‑side encryption before transmission. Metric: 0% of network captures contain plaintext PHI.
- **AC-003**: Immutable audit log entry creation for every read/write operation containing timestamp (UTC), user ID, role, operation type, and cryptographic hash of record version. Metric: 100% of operations logged; log write latency ≤ 2 ms; retention ≥ 7 years.
... (additional ACs as defined above) ...

### Backup Schedule
- Full backup daily at 02:00 UTC.
- Incremental backup hourly.

### Encryption Algorithm
- AES‑256‑GCM for data at rest and client‑side encryption.

### Checksum Method
- SHA‑256 for backup integrity verification.

### Retention Policy
- Primary backups retained 90 days; weekly backups retained for 12 weeks; monthly backups retained for 12 months.

### Audit Log Schema
- Fields: operation_type, timestamp, user_id, checksum.

### Key Rotation
- Frequency: every 90 days via automated Vault process.

### User Stories

**US-001 Demographics Capture**
Persona: Front Staff
Priority: 1 (critical)
Business Justification: patient is ...
Acceptance Criteria:
- AC-001: Given a blank intake form, when the staff fills all required data, then the system saves the record and displays a confirmation message.
- AC-002: Given an invalid email format, when the staff attempts to submit, then the system blocks submission and shows an inline validation error.
- AC-003: Given a missing required field, when the staff attempts to submit, then the system prevents submission and highlights the missing field.

**US-002 Insurance Information Capture**
Persona: Front Staff
Priority: 2 (high)
Business Justification: Accurate insurance data reduces claim rejections.
Acceptance Criteria:
- AC-004: Given a valid insurance number, when submitted, then the system encrypts the field at rest using AES‑256 and logs the write operation.
- AC-005: Given an expired policy date, when submitted, then the system warns the staff and requires confirmation to proceed.
- AC-006: Given a duplicate policy number for the same patient, when submitted, then the system flags a duplicate error.
- AC-007: If network interruption occurs during encryption, then the transaction is rolled back and the user is alerted.

**US-003 Medical History Capture**
Persona: Clinician
Priority: medium
Business Justification: Impact on patient safety.
Acceptance Criteria:
- AC-008: Given an existing patient record, when the clinician opens the history, then the system decrypts the fields in memory and displays them.
- AC-009: Given a change to a field, when the clinician saves, then the system writes an immutable audit log entry with timestamp.
- AC-010: If consent is missing, then the system aborts the operation with an error.
- AC-011: For large text input (>10,000 characters), the system truncates with a warning.

**US-004 PDF Summary Generation**
Persona: Front Staff
Priority: 2 (high)
Business Justification: Provide printable patient summary with watermark for compliance.
Acceptance Criteria:
- AC-012: Given a completed patient record, when the staff requests PDF export, then the system generates a PDF with a visible watermark and includes an export timestamp.
- AC-013: The generated PDF must be stored encrypted at rest using AES‑256.

**US-005 Deployment Verification**
Persona: System Administrator
Priority: medium
Business Justification: Ensure on‑premise Docker Compose deployment is reproducible and air‑gap compliant.
Acceptance Criteria:
- AC-014: Given the Docker Compose file, when executed on a clean host, then all containers start without external network access.
- AC-015: The deployment process must be version‑controlled and documented; any failure triggers an alert.

**US-006 Backup Failure Handling**
Persona: Operations Engineer
Priority: high
Business Justification: Maintain backup reliability and compliance.
Acceptance Criteria:
- AC-016: If a scheduled backup fails verification, then the system generates a HIGH severity alert and retries according to back‑off policy.
- AC-017: After three consecutive failures, the system escalates to incident response and blocks further backups until manual intervention.

**US-007 API Endpoints Definition**
Persona: Backend Engineer
Priority: medium
Business Justification: Provide clear contract for front‑end integration.
Acceptance Criteria:
- AC-018: Define POST /patients endpoint to create patient record; returns 201 on success with location header.
- AC-019: Define GET /patients/{id} endpoint to retrieve patient data; requires TLS 1.3 and returns encrypted fields.
- AC_020: Define PUT /patients/{id} for updates; validates consent and logs audit entry.

**US-008 Data Model Specification**
Persona: Data Architect
Priority: high
dBusiness Justification: Ensure consistent storage of PHI.
Acceptance Criteria:
- AC-021: Patient table includes columns for demographics, insurance, medical history, each encrypted at rest using AES‑256‑GCM with per‑field keys.
- AC-022: AuditLog table records operation_type, timestamp, user_id, checksum, and cryptographic hash of record version.

s**US‑009 Consent Validation**
sPersona:** Clinician
Priority:** high
Business Justification:** Legal compliance for data processing.
sAcceptance Criteria:**
s\- AC‑023:** Before any write operation on PHI,
system checks for valid consent flag; if absent,
soperation is aborted with error message.
s

### Non‑Functional Requirements
\- NFR‑001:** System response time <200 ms for UI actions.
s\- NFR‑002:** Availability 99.9 % uptime.
s\- NFR‑003:** Data at rest encryption AES‑256‑GCM.
s\- NFR‑004:** Transport security TLS 1.3 with forward secrecy.
s\- NFR‑005:** Audit log retention minimum 7 years.
s\- NFR‑006:** Deployment reproducibility via Docker Compose version control.
s

### US-001: Patient Demographics Capture
**Persona:** Front Staff
**Priority:** 1 (critical)
**Business Justification:** Reduce data entry errors and improve patient matching
**Acceptance Criteria:**
- AC-001: Given a valid patient record, when the staff submits the form, then the system saves the record and displays a success message.
- AC-002: Given an invalid email format, when the staff attempts to submit, then the system blocks submission and shows an inline validation error.
- AC-003: Given a missing required field, when the staff attempts to submit, then the system prevents submission and highlights the missing field.

### US-002: Insurance Information Capture
**Persona:** Front Staff
**Priority:** 2 (high)
**Business Justification:** Accurate insurance data reduces claim rejections
**Acceptance Criteria:**
- AC-004: Given a valid insurance number, when submitted, then the system encrypts the field at rest using AES‑256‑GCM and logs the write operation.
- AC-005: Given an expired policy date, when submitted, then the system warns the staff and requires confirmation to proceed.
- AC-006: Given a duplicate policy number for the same patient, when submitted, then the system flags a duplicate error.
- AC-007: Network interruption during encryption must roll back the transaction and alert the user.

### US-003: Medical History Capture
**Persona:** Clinician
**Priority:** Medium
**Business Justification:** Impact on patient safety
**Acceptance Criteria:**
- AC-008: Given an existing patient record, when the clinician opens the history, then the system decrypts the fields in memory and displays them.
- AC-009: Given a change to a field, when the clinician saves, then the system writes an immutable audit log entry with timestamp, user ID, operation type, and cryptographic hash of the record version.
- AC-010: Given a submission without required consent, when the clinician attempts to save, then the system aborts with an error indicating missing consent.
- AC-011: Large text input (>10,000 characters) is truncated with a warning to the clinician.

### US-004: PDF Summary Generation
**Persona:** Front Staff
**Priority:** 2 (high)
**Business Justification:** Provide printable record for patient and audit purposes
**Acceptance Criteria:**
- AC-012: Given a completed patient record, when the staff selects “Generate PDF”, then the system creates a PDF containing all entered data with a visible watermark and an export timestamp.
- AC-013: The generated PDF must be stored securely and its creation logged in the audit trail.

### US-005: Backup and Disaster Recovery Verification
**Persona:** Operations Engineer
**Priority:** 1 (critical)
**Business Justification:** Ensure data integrity and availability after failures
**Acceptance Criteria:**
- AC-014: Given a quarterly DR drill, when the backup set is restored, then the restored database passes integrity checks, all encrypted fields are decryptable, and audit logs are intact and verifiable.
- AC-015: If backup restoration fails, then the system logs a detailed error and sends an alert to the operations team.

## API Endpoints
- POST /api/patients : Create patient record (used by US-001).
- POST /api/insurance : Submit insurance information (used by US-002).
- GET /api/patients/{id}/history : Retrieve medical history (used by US-003).
- POST /api/patients/{id}/pdf : Generate PDF summary (used by US-004).
- POST /api/backup/restore : Trigger DR restore (used by US-005).

## Data Model Specification
| Entity | Fields | Description |
|--------|--------|-------------|
| Patient | id, first_name, last_name, dob, email, phone, address | Core demographic data (encrypted at rest). |
| Insurance | patient_id, policy_number, provider, effective_date, expiration_date | Insurance details (AES‑256‑GCM encrypted). |
| MedicalHistory | patient_id, notes, allergies, medications | Large text fields stored encrypted; notes may exceed 10k chars. |
| AuditLog | id, entity_type, entity_id, operation_type, timestamp, user_id, hash | Immutable log entries for all create/update/delete actions.

## Deployment Verification Artifacts
- Docker Compose file (docker-compose.yml) version 3.8 defining all services.
- Helm chart for Kubernetes deployment (if applicable).
- CI/CD pipeline manifest ensuring reproducible builds and automated scans.
- Post‑deployment smoke test script that validates service health endpoints and database connectivity.

## Compliance Mapping
- REQ-001: All PHI fields encrypted at rest using AES‑256‑GCM.
- REQ-002: Data in transit protected by TLS 1.3.
- REQ-003: Encryption keys rotated every 90 days and logged.
- REQ-004: Immutable audit records for all CRUD operations.
- REQ-005: Audit logs retained for minimum seven years.
- REQ-006: Backup restoration verified quarterly.
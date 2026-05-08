# Air‑Gap Configuration Guide

### 1. Personas

**PER‑03 – Clinician**  
*Role*: Licensed healthcare provider who reviews intake information to make clinical decisions and may generate a PDF summary for patient records.
*Primary Goal*: Access complete, verified patient data quickly and export a tamper‑evident PDF summary only when needed for care coordination or legal review.
*Pain Points*: Time pressure during consultations; need for immediate access to accurate data without navigating complex security dialogs.
*Interaction Flow*:
1. Clinician authenticates with multi‑factor credentials tied to clinician role.
2. System presents a dashboard of pending intake forms.
3. Clinician selects a patient record; UI displays decrypted fields after verifying RBAC.
4. To export, clinician clicks "Generate PDF". Backend composes a PDF/A‑2b file, embeds a visible watermark `Exported by <ClinicianID> on <Timestamp>`, and encrypts the file with AES–26 using a per‑session key stored in HashiCorp Vault.
5. Exported PDF is saved to an encrypted volume mounted inside the air‑gap host; access is logged.

| Acceptance Criteria | ID |
|---|---|
| AC‑CLN‑001 — GIVEN a clinician requests PDF export, WHEN the request is authorized, THEN the generated PDF must contain an immutable watermark with clinician ID and UTC timestamp and be encrypted at rest using AES–26. | AC‑CLN‑001 |
| AC‑CLN‑002 — GIVEN any PDF export action, WHEN completed, THEN an audit log entry `action=EXPORT_PDF`, `actor=clinician_user`, `patient_id=UUID`, `timestamp=ISO8601` must be recorded and immutable for at least 7 years (per NFR–003). | AC‑CLN‑002 |

*Compliance Mapping*: Supports HIPAA §164.312(e) (audit controls), NIST AC-002 (account management), and FR‑004 (PDF watermarking).

### 6. Edge-Case Scenarios

1. Network Interruption — If TLS connection drops during form submission, client retries automatically up to three times; after third failure UI shows "Submission failed – please verify network connectivity".
2. Key Rotation Failure — If automatic rotation of AES keys (scheduled nightly) fails, system logs a critical error, continues using current key, raises alert in monitoring dashboard; subsequent submissions remain encrypted.
3. Audit Log Saturation — When WORM volume reaches 95 % capacity, system blocks further write operations and alerts admin; read operations remain available.
4. Unauthorized Physical Access — If a non-authorized device attempts to connect to Docker Compose network, Docker's built-in firewall rejects connection and records event in audit log with source MAC address.

### 7. Success Metrics

*Encryption Verification* — 100 % of stored patient fields must be encrypted with AES–26; verified by automated checksum comparison against plaintext test data.
*Access Control Enforcement* — Zero false-positive authorizations; measured by penetration testing attempts that should be denied.
*Audit Log Completeness* — Every CRUD operation appears in log; coverage ≥ 99 .9 % as measured by log replay scripts.
*Air-Gap Integrity* — No outbound network traffic observed from any container during normal operation; validated by network monitoring tools.

### 8. MVP Scope Prioritization

The MVP focuses on three core capabilities that must be operational before broader rollout:

1. Secure Web-Form Submission — Collection of patient demographics, insurance information, and medical history with field-level encryption in transit and at rest.
2. PDF Generation & Secure Export — Role-based generation of tamper-evident PDF/A-2b summaries encrypted at rest and streamed over TLS 1.3.
3. Immutable Audit Logging — End-to-end logging of all CRUD operations with WORM storage and automated retention for 7 years.

These capabilities satisfy HIPAA technical safeguards while remaining deployable in an air-gapped SaaS environment.

## User Stories

| ID   | Persona            | Goal| Benefit | Priority |
|------|-------------------|----------|--------------------------|----------|
| US-001 | Compliance Officer | verify that the Docker Compose environment is completely isolated from external networks | I can certify compliance with HIPAA §164.312(b) and SOC 2 isolation controls   | 1 |
| US-002 | System Administrator | generate a checklist that confirms all required open‑source components are pre‑downloaded and signed | I can install the stack on an air‑gapped host without needing internet access   | 2 |
| US-003 | Security Engineer   | run an automated script that validates TLS 1.3 configuration for internal container communication | I can ensure data in transit remains encrypted per NIST SP 800‑53 AC-002 and AU‑6 guidance | 2 |
| US-004 | Auditor              | view immutable logs that record every Docker image pull and container start event      | I can provide evidence of auditability for KPI-003 (audit log completeness)   | 3 |
| US-005 | Front Desk Staff     | receive a clear on‑screen warning when attempting to connect the system to an external network | I can prevent accidental exposure of PHI and maintain KPI-001 (system availability) | 3 |

### Acceptance Criteria

**US-001 – Isolation Verification**
- **Given** the Docker Compose stack is deployed on the internal network,
- **When** I run `docker network inspect internal_bridge`,
- **Then** the output shows no external network interfaces and all containers are attached only to `internal_bridge`.
- **And** any attempt to attach a container to an external network is blocked and logged (see AC-004).

**US-002 – Component Checklist**
- **Given** the installation media is prepared,
- **When** I execute `./verify_components.sh`,
- **Then** the script validates SHA-256 checksums and GPG signatures for every required binary (wkhtmltopdf, OpenSSL, PostgreSQL) and produces a pass/fail report.
- **And** failure aborts the installation with error code `COMP_VERIF_ERR`.

**US-003 – TLS 1.3 Validation**
- **Given** containers are running,
- **When** I run `openssl s_client -connect localhost:443 -tls1_3`,
- **Then** the handshake succeeds and the cipher suite is TLS_AES_256_GCM_SHA384.
- **And** any deviation logs `TLS_VERSION_NONCOMPLIANT`.

**US-004 – Immutable Logging**
- **Given** Docker events occur,
- **When** I query `docker events --filter 'type=container' --since 1h`,
- **Then** each event is recorded in an append-only log file `/var/log/docker_events.log` with immutable file attributes.
- **And** the log file is retained for 7 years per NFR-003.

**US-005 – Network Warning UI**
- **Given** a front-desk user accesses the network settings page,
- **When** the system detects an external NIC is enabled,
- **Then** a modal dialog appears with text “External network detected – operation disabled to protect patient data.”
- **And** the UI blocks proceeding until the NIC is disabled.

## Traceability Matrix

| User Story / AC               | Linked Requirement(s)| KPI |
|-----------|--------------------|-----|
| US-001 / AC-001               | FR-005 (Docker Compose deployment)                    | KPI-001 (system availability) |
| US-002 / AC-002               | FR-011 (Air-gap setup guide) – newly defined            | KPI-002 (zero security incidents) |
| US-003 / AC-003               | FR-002 (TLS encryption in transit) & NFR-002 (TLS 1.3 enforcement) | KPI-001, KPI-003 |
| US-004 / AC-004               | FR-004 (audit log completeness) & NFR-003 (audit trail retention) | KPI-003 |
| US-005 / AC-005               | FR-001 (collect patient data) – ensures no accidental exfiltration | KPI-001 |

## Design Needs (What must be specified by Design)

1. **Network Isolation Specification** – Docker network mode `none` for containers that do not require external communication; host firewall rules blocking all outbound traffic except to internal bridge.
2. **Image Verification Process** – SHA‑256 checksum files stored in `checksums/`, GPG signatures using key `0xA1B2C3D4`; verification script `verify_components.sh`.
3. **TLS Certificate Management** – Internal CA generated via OpenSSL; root certificate distributed to each container via volume mount `/etc/ssl/certs/ca.crt`; rotation schedule every 90 days.
4. **Immutable Logging Architecture** – Log files on an overlayfs mount with `chattr +i` immutable flag; log rotation via `logrotate` retaining 7 years.
5. **User Interface Guardrails** – UI component IDs: `network-warning-modal`, localization key `msg.network_warning`; WCAG 2.1 AA compliance ensured.
6. **Failure Reporting Mechanism** – Standardized error codes: `EXTERNAL_PORT_DETECTED`, `TLS_VERSION_NONCOMPLIANT`, `PDF_GEN_ERR`; integration point with central monitoring dashboard via syslog.

## Validation Checklist (for Reviewer)

1. Verify Docker network isolation using `docker network inspect internal_bridge`.
2. Run `./verify_components.sh` and confirm all components pass checksum and signature verification.
3. Execute `openssl s_client -connect localhost:443 -tls1_3` and confirm cipher suite.
4. Capture a form submission with Wireshark; ensure payload is encrypted with AES‑256 GCM over TLS 1.3.
5. Query PostgreSQL audit log after a read operation: `SELECT * FROM pg_audit.log LIMIT 5;` and verify entries contain user ID, operation type, timestamp.
6. Generate a PDF via the UI; open in Adobe Acrobat and confirm watermark “Confidential – Authorized Staff Only” and ISO‑8601 export timestamp in metadata.
7. Start Docker Compose in an isolated VM without internet; ensure no image pulls occur after initial cache.

## Asset Registry Updates

*Added new functional requirement:*

- **FR-011**: Air-gap setup guide – ensures all required open-source components are pre-downloaded, signed, and verified before installation.

## Patient Intake SaaS – Feature Specification

### 3. Purpose
Provide a secure, multi-tenant web application for clinics to capture patient intake data, generate PDF summaries with watermarks, and store data encrypted at rest and in transit.

#### US-001 – Patient Data Entry
**As** a **Patient (P-001)**
**I want** to enter my personal and health information into a secure web form
**So that** the clinic can process my intake without manual paperwork.
*Acceptance Criteria*:
1. Given the patient accesses the intake portal over HTTPS, when they submit the form, then the data is stored encrypted at rest (AES-256) and a confirmation email is sent.
2. Given required fields are left blank, when the patient attempts to submit, then inline validation messages are displayed.
3. Given the patient completes the form, when the submission succeeds, then an audit log entry is created (see FR-008).

## 6. Overview
This document defines the user‑value‑focused features, user stories, acceptance criteria, and MVP scope for the **Patient Intake** SaaS solution. All content is scoped to the product phase and adheres to the SaaS domain constraints (cloud deployment, multi‑tenant, high availability, SOC 2/GDPR compliance).

---

## 7. Requirement Traceability
| Requirement ID | Description |
|----------------|-------------|
| **FR-001** | Capture patient demographic data (name, DOB, contact). |
| **FR-002** | All data transmissions shall use TLS 1.2+ (Transport Encryption). |
| **FR-003** | Store data at rest using AES‑256 encryption. |
| **FR-004** | Generate a PDF intake summary per patient with watermark and export timestamp visible only to authorized staff. |
| **FR-005** | Deploy the entire stack via Docker Compose for on‑premise environments. |
| **FR-006** | Deploy the entire stack via Docker Compose in an air‑gapped environment (offline deployment). |
| **FR-011** | Provide role‑based access control (RBAC) for intake data and PDF summaries, ensuring only authorized staff can view or download PDFs. |
| **NFR-001** | System availability ≥ 99.9 % (high availability). |
| **NFR-002** | Automated certificate rotation for TLS certificates. |
| **NFR-003** | Audit log retention for 7 years with immutable snapshots. |
| **KPI-001** | System availability measured monthly (target ≥ 99.9 %). |
| **KPI-002** | Zero security incidents in first 90 days. |
| **KPI-003** | Successful compliance audit (SOC 2) within 6 months. |

---

### US‑001 – Capture Demographic Data
**As** a **Clinic Staff** (ST‑002),
**I want** to enter a new patient’s demographic information into the intake form,
**so that** the data is stored securely and can be used for downstream clinical workflows.

**Acceptance Criteria**:
1. **Given** the staff member is authenticated via RBAC (FR‑011),
   **When** they open the "New Patient" screen,
   **Then** the form displays fields for name, DOB, address, phone, and email (FR‑001).
2. **Given** the form is filled with valid data,
   **When** the staff clicks "Submit",
   **Then** the data is transmitted over TLS 1.2+ (FR‑002) and stored encrypted at rest (FR‑003).
3. **Given** a successful submission,
   **When** the staff views the patient record,
   **Then** a confirmation message appears and an audit log entry is created (NFR‑003).

---

### US‑002 – Generate PDF Intake Summary
**As** a **Clinic Staff**,
**I want** to generate a PDF summary of the patient’s intake information,
**so that** I can print or share it with authorized personnel while preserving confidentiality.

**Acceptance Criteria**:
1. **Given** a completed patient record,
   **When** the staff selects "Generate PDF",
   **Then** a PDF is produced containing all entered fields, includes a visible watermark stating "Confidential – Internal Use Only", and shows an export timestamp (FR‑004).
2. **Given** the generated PDF,
   **When** any user attempts to download it,
   **Then** access is granted only if the user has the appropriate RBAC role (FR‑011); otherwise an "Access Denied" error is shown.
3. The PDF file is stored in an immutable audit‑log‑compatible location for at least 7 years (NFR‑003).

---

### US‑003 – Air‑Gap Deployment Package
**As** a **Compliance Officer**,
**I want** an installation package that can be deployed in an air‑gapped environment,
**so that** the intake system can operate in highly regulated facilities without internet connectivity.

**Acceptance Criteria**:
1. **Given** the compliance officer downloads the deployment bundle,
   **When** they run the provided Docker Compose script on an offline host,
   **Then** all services start successfully without external network calls (FR‑006).
2. The bundle includes pre‑generated TLS certificates and a script for automated rotation (NFR‑002).
3. Post‑deployment verification steps are documented and include checksum validation of images.

---

### US‑004 – Role‑Based Access Control Enforcement
**As** a **Compliance Officer**,
**I want** fine‑grained RBAC controls over patient intake data and PDFs,
**so that** only authorized staff can view or modify sensitive information.

**Acceptance Criteria**:
1. **Given** a user with "Viewer" role,
   **When** they attempt to edit a patient record,
   **Then** the UI disables edit controls and displays a read‑only view.
2. **Given** a user with "Editor" role,
   **When** they edit a record and save,
   **Then** changes are persisted and logged (NFR‑003).
3. Access checks are enforced at API layer using JWT claims validated against RBAC policies defined in FR‑011.

---

## 9. MVP Scope
The Minimum Viable Product will include the following prioritized features:
1. Demographic data capture (US‑001) – core intake functionality.
2. Secure transmission & storage (FR‑002, FR‑003) – compliance foundation.
3. PDF generation with watermark and timestamp (US‑002 / FR‑004).
4. Basic RBAC for staff roles (US‑004 / FR‑011).
5. Docker Compose deployment script for cloud environments (FR‑005).
6. Optional air‑gap deployment package (US‑003 / FR‑006) – delivered as an add‑on for regulated customers.

Non‑MVP items (future releases): advanced analytics dashboards, multi‑tenant tenant isolation enhancements, automated key rotation monitoring beyond initial script.

---

### Risks & Mitigations

| Risk ID | Description | Mitigation |
|---------|-------------|------------|
| RISK-001 | Data breach due to weak encryption | Enforce AES‑256 and TLS 1.2+ (FR‑003, FR‑002) |
| RISK-006 | Key management failure | Automated key rotation (NFR‑002) |

### References
- Project Asset Registry IDs: FR‑001 … FR‑011, NFR‑002, RISK‑001, RISK‑006.
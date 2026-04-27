# Risk Assessment (Overview)

### Vision Statement
The PatientIntake project will deliver a fully HIPAA‑compliant patient intake system that captures demographic, insurance, and medical history data via a structured web form, encrypts each field at rest and in transit, stores records in a local PostgreSQL database, and provides role‑based access for administrators, clinicians, and front‑desk staff. The solution will be built exclusively with open‑source components to avoid vendor lock‑in and to satisfy the on‑premise, air‑gap deployment requirement.
### Strategic Objectives
- **OBJ-001: Regulatory Compliance** – Achieve full compliance with HIPAA Security Rule §164.312(a)(2)(iv) by implementing AES‑256 field‑level encryption and TLS 1.3 transport security. Success measured by an external audit confirming 100 % encryption coverage.
- **OBJ-002: Operational Availability** – Maintain system uptime of 99.9 % (NFR‑002) and average form response time under 200 ms (NFR‑001) as measured over a 30‑day monitoring window.
- **OBJ-003: Data Integrity and Auditability** – Record an immutable audit log for every read, write, update, and delete operation with a retention period of seven years (REQ‑005). Log completeness must be ≥99.5 % verified by automated log‑integrity checks.
- **OBJ-004: Open‑Source Sustainability** – Use only community‑maintained, license‑compatible open‑source libraries (e.g., Node.js, React, PostgreSQL, OpenSSL) and keep dependency versions pinned to avoid security regressions.

### Stakeholder Alignment
| ID | Role | Primary Need | Concern | Owner |
|----|------|--------------|----------|-------|
| ST-01 | Patient | Confidential handling of PHI | Fear of data breach | Compliance Officer |
| ST-02 | Front‑Desk Staff | Quick data entry and retrieval | Manual errors, slow UI | Front‑Desk Manager |
| ST-03 | Clinician | Reliable access to complete medical history | Incomplete records | Clinical Lead |
| ST-04 | System Administrator | Secure configuration and auditability | Complex key management | IT Operations Lead |
| ST-05 | Compliance Officer | Evidence of HIPAA controls | Audit fatigue | Compliance Lead |

### Functional Requirements
#### FR-001: Patient Demographic Capture
- **Description**: The web form shall collect name, date of birth, address, phone, and email for each patient.
- **Acceptance Criteria**: All fields must be validated for format and completeness; submission is rejected if any mandatory field is missing. Validation rules: name non‑empty, DOB ISO‑8601, email matches RFC 5322, phone matches E.164. Test coverage ≥95 % of valid/invalid combos.
- **Stakeholder Owner**: Front‑Desk Manager

#### FR-002: Insurance Information Capture
- **Description**: Capture insurer name, policy number, group number, and coverage dates.
- **Acceptance Criteria**: Data stored encrypted at field level using AES‑256 before persisting to PostgreSQL. Encryption library: OpenSSL 3.0 via libcrypto. Audit log entry created for each capture event.
- **Stakeholder Owner**: Front‑Desk Manager

#### FR-003: Medical History Capture
- **Description**: Allow entry of past diagnoses, medications, allergies, and surgical procedures.
- **Acceptance Criteria**: Each entry limited to 500 characters; free‑text fields sanitized against XSS using OWASP ESAPI. All entries encrypted at rest.
- **Stakeholder Owner**: Clinical Lead

#### FR-004: Role‑Based Access Control (RBAC)
- **Description**: Define three roles – Admin, Clinician, Front‑Desk.
- **Acceptance Criteria**: Admin can create, read, update, delete any record; Clinician can read and update records for assigned patients; Front‑Desk can create and read but not modify clinical fields. Enforcement via PostgreSQL row‑level security policies. Unauthorized access attempts generate audit log with severity=high.
- **Stakeholder Owner**: IT Operations Lead

#### FR-005: Immutable Audit Logging
- **Description**: Every read, write, update, delete operation shall generate an immutable log entry containing timestamp (UTC), user ID, role, operation type, patient ID, and source IP.
- **Acceptance Criteria**: Logs stored in append‑only table with cryptographic hash chaining (SHA‑256) to detect tampering. Retention period ≥7 years as required by HIPAA §164.310(d)(1). Exportable for compliance audit.
- **Stakeholder Owner**: Compliance Lead

#### FR-006: PDF Intake Summary Generation
- **Description**: Authorized staff may request a PDF summary of a patient’s intake data.
- **Acceptance Criteria**: PDF generated using open‑source wkhtmltopdf 0.12.6, includes visible watermark "Confidential – Patient Intake" and timestamp of export. File name includes patient ID and generation datetime. Access to PDF logged in audit log.
- **Stakeholder Owner**: Clinical Lead

#### FR-007: Automated Test Suite
- **Description**: Include unit and integration tests covering form validation, encryption, RBAC enforcement, audit logging, and PDF generation.
- **Acceptance Criteria**: Test coverage ≥90 % of codebase; CI pipeline fails on any test regression. Tests executed in Docker container using pytest 7.x.
- **Stakeholder Owner**: IT Operations Lead

### Success Metrics (KPIs)
- **KPI-001: Form Completion Rate** – Target ≥92 % of submissions completed without validation errors, measured weekly via submission logs.
- **KPI-002: Encryption Coverage** – 100 % of PHI fields encrypted at rest and in transit, verified by automated compliance scans after each deployment.
- **KPI-003: Audit Log Completeness** – ≥99.5 % of CRUD operations logged, validated by log‑integrity scripts run nightly.
- **KPI-004: Deployment Time** – Full stack up and running within 30 minutes on a new air‑gap server, measured during pilot rollout.
- **KPI-005: Encryption Key Rotation Compliance** – Keys rotated every 90 days with audit‑log entry for each rotation; measured by key‑management service logs reviewed monthly.

### Scope Definition
- **In‑Scope**: Web‑based intake form, field‑level AES‑256 encryption, PostgreSQL storage, RBAC, immutable audit logging, PDF summary generation with watermark and timestamp, Docker Compose deployment, documentation of air‑gap setup.
- **Out‑Of‑Scope**: Cloud‑based services, mobile native applications, advanced analytics on collected data, integration with external EHR systems.

### Risks and Mitigations
RISK-001: Encryption Key Mismanagement – Likelihood Medium, Impact High. **Mitigation:** Automated key rotation every 90 days via HashiCorp Vault; rotation events logged to audit (REQ‑003); quarterly key‑management review meeting with documented minutes.
RISK-002: Unauthorized Access via RBAC Misconfiguration – Likelihood Low, Impact High. **Mitigation:** PostgreSQL row‑level security policies defined per role; nightly automated compliance scans; MFA enforced for privileged accounts; monthly access‑rights audit report.
RISK-003: Audit Log Tampering – Likelihood Low, Impact High. **Mitigation:** Append‑only log storage with SHA‑256 hash chaining; logs replicated to separate container; weekly hash verification job; retention 7 years (REQ‑005).
RISK-004: Deployment Failure in Air‑Gap Environment – Likelihood Medium, Impact Medium. **Mitigation:** Docker Compose scripts with version‑pinned images stored in offline registry; pre‑flight health‑check script; quarterly disaster‑recovery drill documented in runbook.
RISK-005: PDF Generation Vulnerability – Likelihood Low, Impact Medium. **Mitigation:** Use open‑source PDF library with digital signature support; embed visible watermark with patient ID and timestamp; restrict export to Clinician and Admin roles; code review and static analysis before release.
RISK-006: Performance Degradation Under Load – Likelihood Low, Impact Medium. **Mitigation:** Load testing with k6 simulating 200 concurrent submissions; connection pooling tuned; Nginx caching for static assets; auto‑scale up to 5 replicas validated in scaling test (NFR‑006).


### NFR-001: Performance
- **Target**: ≤200 ms response time at 95th percentile for up to 100 concurrent users.
- **Measurement**: k6 load test; Prometheus metrics; CI threshold.
- **Owner**: IT Operations

### NFR-003: Data‑at‑Rest Encryption
- **Target**: AES‑256‑GCM for all PHI fields; keys managed by HashiCorp Vault; rotated every 90 days.
- **Measurement**: Automated schema scan; OpenSSL verification; key rotation logs.
- **Owner**: Security Engineer

### NFR-004: Transport Security
- **Target**: TLS 1.3 with forward‑secrecy cipher suites.
- **Measurement**: Qualys SSL Labs A+ rating; CI fails on TLS <1.3.
- **Owner**: Security Engineer

### NFR-007: Maintainability
- **Target**: All config files version‑controlled in Git with semantic versioning; peer‑review required.
- **Measurement**: Pull‑request policy enforcement.
- **Owner**:** Development Team

## Key Performance Indicators (KPIs)
- KPI-001: 99.5 % of CRUD operations logged (validated by log‑integrity scripts).
- KPI-004: Deployment Time – Full stack up and running within 30 minutes on a new air‑gap server (measured during pilot rollout).
- KPI-005: Encryption Key Rotation Compliance – Keys rotated every 90 days with audit‑log entry for each rotation (measured by key‑management service logs).

### In‑Scope
- Web‑based intake form
- Field‑level AES‑256 encryption
- PostgreSQL storage with RBAC
- Immutable audit logging for all read/write operations
- PDF summary generation with watermark and timestamp
- Docker Compose deployment for on‑premises air‑gap environments
- Documentation of air‑gap setup guide
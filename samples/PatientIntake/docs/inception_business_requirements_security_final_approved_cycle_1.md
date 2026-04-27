# Security Requirements

## Security Requirements – Patient Intake

### 1. Functional Requirements
- FR-001: All patient demographic, insurance, and medical history fields must be encrypted at rest using AES-256-GCM. Acceptance: Automated test verifies encrypted column values differ from plaintext and decryption using the project's key yields original data. Owner: Compliance Officer (ST-04).
- FR-002: All data in transit between the web browser and the backend must be protected with TLS 1.3 with forward-secrecy ciphers. Acceptance: Scanning tool reports no protocols below TLS 1.3 for any endpoint. Owner: System Administrator (ST-03).
- FR-003: Role-Based Access Control (RBAC) must enforce three roles – Admin, Clinician, Front-Desk – with least‑privilege permissions. Acceptance: Access matrix test confirms Admin can CRUD, Clinician can read/update assigned patients, Front-Desk can create and read but not update/delete. Owner: Front‑Desk Manager (ST-02).
- FR-004: Every read, write, update, and delete operation on patient records must generate an immutable audit log entry containing timestamp, user ID, role, operation type, and record identifier. Acceptance: Log audit query returns a record for each transaction with tamper-evidence hash and retention of 7 years. Owner: Compliance Officer (ST-04).
- FR-005: Authorized staff may generate a PDF intake summary that includes a visible watermark containing the patient ID and export timestamp. Acceptance: PDF inspection confirms watermark text and timestamp; access control denies generation for unauthorized roles. Owner: Clinician (ST-03).

#### Additional Requirements (REQ)
- REQ-001: All PHI fields are encrypted at rest using AES-256-GCM provided by OpenSSL v3.0. Acceptance: Automated test verifies stored values are not readable without the decryption key. Owner: Security Engineer (ST-03).
- REQ-002: All client-server communication uses TLS 1.3 with forward-secrecy ciphers. Acceptance: Scanning tool reports no TLS 1.2 or lower endpoints. Owner: System Administrator.
- REQ-004: Three RBAC roles are defined: Admin, Clinician, Front‑Desk. PostgreSQL row-level security policies enforce column-level read/write permissions. Acceptance: Access matrix test confirms each role can only perform permitted actions. Owner: Database Administrator.
- REQ-005: Every read, write, update, and delete operation creates an append-only log entry stored in a separate PostgreSQL schema with write-once permissions. Retention period is 7 years. Acceptance: Log query shows no deletions over a 30-day simulated period. Owner: Compliance Officer.
- REQ-006: PDF summaries are generated using wkhtmltopdf v0.12 and stamped with a visible watermark containing the exporting user and timestamp. Only Admin and Clinician roles may invoke the export endpoint. Acceptance: Manual review confirms watermark presence and correct timestamp. Owner: Front‑Desk Manager.

### 3. Stakeholder Identification
- ST-01 (Patient): Needs assurance that personal health information is confidential and never exposed. Motivation: Trust and regulatory compliance (HIPAA §164.526). Owner: Compliance Officer.<br>
- ST-02 (Front‑Desk Staff): Requires efficient data entry workflow and ability to generate PDF summaries. Motivation: Efficiency and error reduction. Owner: Front‑Desk Manager.<br>
- ST-03 (Clinician): Must view complete, accurate patient histories while being prevented from altering audit logs. Motivation: Clinical decision support. Owner: Clinical Lead.<br>
- ST-04 (System Administrator): Responsible for deployment, key management, and system uptime. Motivation: Operational stability. Owner: System Administrator.<br>
- ST-05 (Compliance Officer): Needs visibility into audit-log completeness, encryption key lifecycle, and incident-response documentation. Motivation: Regulatory reporting (HIPAA §164.312, §164.310(d)(2)). Owner: Compliance Officer.<br>

### 4. Risk Assessment
| Risk ID | Description | Likelihood | Impact | Mitigation | Acceptance Criteria |
|---|---|---|---|---|---|
| RISK-001 | Encryption key compromise | Medium | High | Automated rotation every 90 days using HashiCorp Vault OSS, dual-control approval, HSM-style sealed storage. | Key rotation occurs within 24 h of schedule 99.9 % of the time; no unauthorized key retrieval events in 12‑month audit.|
| RISK-002 | Audit-log tampering | Low | High | Use append-only write-once storage via PostgreSQL immutable tables with pgcrypto signatures; cryptographic hash chaining; weekly integrity verification.| Log integrity verification passes 100 % of the time; any mismatch triggers incident response within 30 minutes.|
| RISK-003 | Data-in-transit interception (MITM) | Medium | Medium | Enforce TLS 1.3 with strong cipher suites (AES‑256‑GCM, CHACHA20‑POLY1305); disable TLS 1.0/1.1; implement HSTS max-age 31536000.| All external connections negotiate TLS 1.3; vulnerability scans show 0 % TLS downgrade attacks.|
| RISK-004 | Unauthorized access via RBAC misconfiguration | Low | High | Define least‑privilege roles in PostgreSQL RLS; quarterly access-review audits; automated role-based tests integrated into CI pipeline.| No role exceeds defined permission matrix; automated tests pass 100 % of runs.|

### 5. Compliance References
- HIPAA Security Rule §164.312(a)(2)(iv) – Encryption of PHI at rest.<br>
- HIPAA Security Rule §164.312(e)(1) – Integrity controls and audit logs.<br>
- HIPAA Security Rule §164.312(b) – Access control mechanisms.<br>
- HIPAA Security Rule §164.312 – General technical safeguards.<br>
- HIPAA §164.526 – Patient's right to request amendment or deletion of PHI.<br>
- HIPAA §164.310(d)(2) – Audit-log retention for at least seven years.<br>
- NIST SP 800‑53 Rev 5 – AC‑3 (Access Enforcement), SC‑13 (Cryptographic Protection), IA‑5 (Authenticator Management).<br>

## Acceptance Criteria Summary
All listed functional and non‑functional requirements must be demonstrably met through automated tests, monitoring dashboards, and audit reports before moving to design phase.

### 6. Success Criteria & KPIs
- KPI‑001: Encryption Coverage – 100 % of PHI fields encrypted at rest (AES‑256). Measurement: Automated scan reports zero unencrypted fields for three consecutive days.
- KPI‑002: Transport Security – All PHI traffic uses TLS 1.3 with forward secrecy. Measurement: Continuous monitoring shows no TLS version below 1.3 over a 7‑day period.
- KPI‑003: Audit Log Completeness – ≥99.9 % of read/write events logged immutably. Measurement: Log ingestion count vs transaction count discrepancy <0.1 % over rolling 30‑day window.
- KPI‑004: Log Retention – Audit logs retained for minimum seven years in compliance with HIPAA §164.310(d)(2). Measurement: Verification of archive timestamps and SHA‑256 integrity checks.
- KPI‑005: System Availability – 99.9 % uptime measured via Prometheus.
- KPI‑006: Form Completion Rate – ≥90 % of submitted forms completed without validation errors. Measurement: Successful submissions vs total attempts weekly.
- KPI‑007: Key Rotation Compliance – Keys rotated every 90 days and logged. Measurement: No key older than 90 days in audit logs over a 180‑day audit.
- KPI\-008: Incident Response Time – Initial response within 1 hour for 95 % of incidents. Measurement: Ticket timestamps from incident management system.
- KPI\-009: PDF Generation Success – ≥98 % success rate for authorized PDF export requests. Measurement: Functional test suite.
- KPI\-010: Deployment Reproducibility – Docker Compose up succeeds on fresh air‑gapped host within 5 minutes 95 % of the time. Measurement: Automated deployment test.

## Business Vision
The patient intake system will enable secure, efficient collection of patient demographics, insurance information, and medical history, ensuring HIPAA compliance and supporting clinical workflows.

## Stakeholder Needs
- **ST-01 (Patient)**: Secure submission of personal health information with assurance of privacy.
- **ST-02 (Clinician)**: Immediate access to complete, accurate intake data for care decisions.
- **ST-03 (Front Desk Staff)**: Streamlined data entry with validation to reduce errors.
- **ST-04 (System Administrator)**: Reliable deployment, key management, and system uptime.
- **ST-05 (Compliance Officer)**: Visibility into audit‑log completeness, encryption key lifecycle, and incident‑response documentation.

## Risks and Mitigations
| Risk ID | Description | Likelihood | Impact | Mitigation | Acceptance Criteria |
|--------|-------------|------------|--------|-----------|--------------------|
| RISK-001 | Encryption key compromise | Medium | High | Automated rotation every 90 days using HashiCorp Vault OSS, dual‑control approval, HSM‑style sealed storage. | Key rotation occurs within 24 h of schedule 99.9% of the time; no unauthorized key retrieval events in 12‑month audit. |
| RISK-002 | Audit‑log tampering | Low | High | Append‑only write‑once storage via PostgreSQL immutable tables with pgcrypto signatures; cryptographic hash chaining. | Log integrity verification passes 100% of the time; any mismatch triggers incident response within 30 minutes. |
| RISK-003 | Data‑in‑Transit interception (MITM) | Medium | Medium | Enforce TLS 1.3 with AES‑256‑GCM and CHACHA20‑POLY1305; disable TLS 1.0/1.1; implement HSTS max‑age 31536000. | All external connections negotiate TLS 1.3; vulnerability scans show 0% TLS downgrade attacks. |
| RISK-004 | Unauthorized access via RBAC misconfiguration | Low | High | Define least‑privilege roles in PostgreSQL RLS; quarterly access‑review audits; automated role‑based tests. | No role exceeds defined permission matrix; automated tests pass 100% of runs. |

## Deployment & Operations (Open‑Source Stack)
- **Web Framework**: Django 5.x (Python)
- **Database**: PostgreSQL 15 with Row‑Level Security and immutable audit tables.
- **Encryption Library**: PyNaCl 1.5 (AES‑256‑GCM)
- **PDF Generation**: WeasyPrint 58
- **Container Runtime**: Docker Engine 24, Docker Compose 2.20
- Containers run as non‑root users with CPU ≤2 cores and memory ≤2 GB.
- Secrets managed via Docker secrets or host‑mounted .env files (mode 600).
- Healthchecks enforced per service with restart back‑off policy.
- Immutable audit logs written to append‑only volume, rotated daily, retained 7 years.
- Weekly encrypted logical backups stored on air‑gapped NAS (RPO 1 hour, RTO 4 hours).
- Image scanning with Trivy 0.45; CI blocks builds on CVE ≥ Medium.

## Governance & Review Process
- **Stakeholder Review**: Business requirements reviewed bi‑weekly by ST‑01 through ST‑05.
- **Compliance Audit**: Quarterly audit by Compliance Officer (ST‑05) against HIPAA and NIST controls.
- **Change Management**: All changes tracked in Git with signed commits; deployment changes reviewed via pull‑request workflow.
- **Incident Management**: Incident Response Plan maintained per HIPAA §164.308(a)(1)(ii); response times measured against KPI‑008.

## Traceability Matrix
| Requirement ID | Stakeholder Owner | Related Risk ID(s) | KPI(s) |
|-----------------|------------------|-------------------|--------|
| FR-001 | ST-02 | — | KPI-006 |
| FR-002 | ST-05 | RISK-001 | KPI-001, KPI-002 |
| FR-003 | ST-04 | RISK-004 | KPI-003 |
| FR-004 | ST-02 | RISK-002 | KPI-009 |
| FR-005 | ST-03 | — | KPI-010 |
| FR-006 | ST-04 | — | KPI-010 |

## Open Issues & Next Steps
1. Validate that all PHI fields are correctly identified for encryption (knowledge gap: exact mapping of form fields to PHI categories).
2. Conduct performance testing of immutable audit log writes under high transaction volume.
3. Finalize incident response playbooks for key compromise scenarios.
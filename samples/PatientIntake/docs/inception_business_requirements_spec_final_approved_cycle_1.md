# Business Requirements Specification

## System Scope and Architecture Vision

1. Purpose and Regulatory Anchor
The PatientIntake platform will enable collection of patient demographics, insurance information, and medical history via a structured web form while satisfying HIPAA Security Rule §164.312(a)(2)(iv) encryption requirements, §164.530., §164.310(d)(2)., §164.312(e)(1), §164.312(b), §164.308(a)(1)(ii)(D) and §164.404. The system must be built exclusively with open-source components to avoid vendor lock-in and to support on-premise deployment.

2. In-Scope Functional Boundaries
FR-001: Web-based intake form that captures required fields and validates mandatory data entry. Acceptance: 100 % of required fields must be completed before submission; form submission latency ≤150 ms measured at the 95th percentile. Owner: Front-Desk Staff.
FR-002: Field-level encryption at rest using AES-256-GCM. Acceptance: Encryption keys stored in a hardware-security-module-compatible vault; encrypted data must be verifiable via decryption test with zero data loss. Owner: IT Security Team.
FR-003: TLS 1.3 transport encryption for all client-server communication. Acceptance: All HTTPS endpoints present a valid TLS 1.3 certificate and pass OWASP ZAP scan with no high-severity findings. Owner: IT Security Team.
FR-004: Role-Based Access Control (RBAC) with three roles – Admin, Clinician, Front-Desk – each mapped to least-privilege permissions. Acceptance: Access matrix documented and verified by automated permission-audit script. Owner: System Administrator.
FR-005: Immutable audit log capturing every read and write operation, including user ID, timestamp, operation type, and affected record ID. Acceptance: Log entries immutable for 7 years and searchable via indexed query with ≤200 ms response time. Owner: Compliance Officer.
FR-006: PDF summary generation with visible watermark and export timestamp, accessible only to authorized roles. Acceptance: PDF contains watermark text \"Confidential – PatientIntake\" and timestamp metadata; export action logged in audit log. Owner: Front-Desk Staff.
FR-007: Alerting rules shall trigger a Slack notification and email when CPU usage >80 % for 5 minutes or when audit-log write latency exceeds 500 ms. Acceptance: Alert fires in a controlled test and is acknowledged. Owner: Operations Team.
FR-008: Daily encrypted backups of the PostgreSQL database shall be created and stored on a separate offline volume. Acceptance: Backup file size matches live DB size ±5 % and can be restored within 30 minutes. Owner: Database Administrator.
FR-009: A documented disaster-recovery drill shall be performed quarterly. Acceptance: Drill checklist completed and signed off by the Compliance Officer. Owner: Disaster Recovery Lead.
FR-010: The deployment process shall be version-controlled in a Git repository with signed commits. Acceptance: git log --show-signature displays a valid GPG signature for each commit. Owner: DevOps Engineer.
FR-011: An operations manual shall be provided, covering start-up, shutdown, log rotation, and key rotation procedures. Acceptance: Manual is 25 pages, reviewed by the Compliance Officer, and indexed in the internal knowledge base. Owner: Documentation Team.
FR-012: Training videos (total ≤30 minutes) shall be created for front-desk staff and system administrators. Acceptance: Videos hosted on the internal LMS and tracked for completion. Owner: Training Team.

3. Out-of-Scope Exclusions
Cloud-based SaaS services, third-party proprietary analytics, and external key-management services. Integration with external electronic health record (EHR) systems beyond the defined PDF export. Mobile-native applications; only responsive web UI is covered.

4. Architectural Vision
Containerization: All services run in Docker containers orchestrated by Docker-Compose version 3.9, ensuring reproducible on-premise environments.
Data Store: PostgreSQL 15 with row-level security (RLS) to enforce RBAC at the database level and pgcrypto for AES-256-GCM at-rest encryption.
Encryption Library: Open-source libsodium for AES-256-GCM encryption, providing audited cryptographic primitives.
Logging: Elastic-compatible JSON log format stored in a write-once, append-only file system, enabling tamper-evidence.
PDF Generation: wkhtmltopdf combined with a custom HTML template that injects watermark and timestamp.
Monitoring: Prometheus-based metrics collection with alerts for latency >200 ms, audit-log write failures, CPU usage >80 % and TLS certificate expiry.

5. Stakeholder Analysis
ST-01 – Patient: Needs secure, easy-to-complete intake form; expects privacy per HIPAA §164.530.
ST-02 – Front-Desk Staff: Requires quick data entry and verification; needs role-based access to create records.
ST-03 – Clinician: Needs read-only access to patient history for care decisions; must see audit trail of any modifications.
ST-04 – Administrator: Manages user roles, encryption keys, and system uptime; requires full audit log visibility.
ST-05 – Compliance Officer: Ensures all processes satisfy HIPAA and internal policies; monitors key rotation and log retention.

6. Success Metrics and KPIs
KPI-01: Form completion rate ≥92 % measured weekly.
KPI-02: System uptime ≥99.9 % measured monthly.
KPI-03: Zero HIPAA-related security incidents reported in the first 90 days.
KPI-04: Audit-log retention compliance ≥100 % for 7-year period verified by quarterly audit.
KPI-05: PDF Export Watermark Accuracy – Every exported PDF contains visible watermark \"Confidential – Patient Intake\" and timestamp of export. Measured by automated PDF validation script; 100 % pass rate on sampled PDFs.
KPI-06: Test Coverage – Automated unit and integration tests cover ≥90 % of functional requirements and ≥90 % of edge-case scenarios.
KPI-07: Deployment Time – Full stack deployable on air-gapped hardware within 30 minutes from start of script execution.
KPI-08: Stakeholder Satisfaction – Post-implementation survey yields average satisfaction score ≥4.5/5 from patients, clinicians, and administrators.

7. Risk Mitigation Overview
RISK-001 (Key Management Failure) – Mitigation: Rotate encryption keys every 90 days using automated script; store keys in an air-gapped HSM; log rotation events and verify via audit log.
RISK-002 (Audit Log Tampering) – Mitigation: Write-once storage with cryptographic hash chaining; verify hash chain daily via integrity check script; retain logs for 7 years.
RISK-003 (Deployment Failure in Air-Gap) – Mitigation: Docker images built from official base images, scanned with Trivy, signed SHA-256; deployment scripts include health-check loops and rollback on failure.
RISK-004 (Data Breach – Unauthorized Access) – Mitigation: Host-based firewalls, enforce TLS 1.3 for all traffic, network segmentation using Docker bridge networks; conduct quarterly penetration testing.

## Business Requirements Specification

### 1. Business Objectives
- Achieve HIPAA compliance for patient intake, ensuring confidentiality, integrity, and availability of protected health information (PHI).
- Meet measurable success criteria: 99.9% system uptime, 92% form completion rate, and 100% of form submissions processed within 200 ms.

### 3. Functional Requirements
| ID | Description | Acceptance Criteria | Owner |
|----|-------------|---------------------|------|
| FR-001 | Web‑based intake form captures required fields and validates mandatory data entry. | 100% of required fields completed before submission; submission latency ≤150 ms at 95th percentile. | Front‑Desk Staff |
| FR-002 | Field‑level encryption at rest using AES‑256‑GCM. | Encryption keys stored in HSM‑compatible vault; decryption test shows zero data loss. | Administrator |
| FR-003 | TLS 1.3 transport encryption for all client‑server communication. | Valid TLS 1.3 certificate on all endpoints; OWASP ZAP scan reports no high‑severity findings. | Administrator |
| FR-004 | Role‑Based Access Control (RBAC) with three roles – Admin, Clinician, Front‑Desk – each mapped to least‑privilege permissions. | Access matrix documented; automated permission‑audit script verifies correct permissions. | Administrator |
| FR-005 | Immutable audit log capturing every read and write operation (user ID, timestamp, operation type, record ID). | Log entries immutable for 7 years; searchable query response ≤200 ms. | Administrator |
| FR-006 | PDF summary generation with visible watermark and export timestamp; accessible only to authorized roles. | PDF contains watermark \"Confidential – Patient Intake\" and timestamp metadata; export action logged in audit log. | Front‑Desk Staff |
| FR-007 | Alerting rules trigger Slack notification and email when CPU usage >80% for 5 min or audit‑log write latency >500 ms. | Test scenario fires alert and is acknowledged by monitoring team. | Administrator |
| FR-008 | Daily encrypted backups of PostgreSQL database stored on separate offline volume. | Backup size matches live DB ±5%; restore completes within 30 min. | Administrator |
| FR-009 \u2013 Documented disaster‑recovery drill performed quarterly. \u2013 Acceptance: Drill checklist completed and signed off by Compliance Officer.| Drill checklist completed and signed off by Compliance Officer.| Compliance Officer |
| FR-010 \u2013 Version‑controlled deployment process with signed commits.| `git log --show-signature` displays valid GPG signature for each commit.| Administrator |
| FR-011 \u2013 Operations manual covering start‑up, shutdown, log rotation, and key rotation procedures.| Manual is 25 pages, reviewed by Compliance Officer, indexed in knowledge base.| Compliance Officer |
| FR-012 \u2013 Training videos (≤30 min total) for front‑desk staff and system administrators.| Videos hosted on internal LMS and tracked for completion.| Administrator |

### 5. Compliance
- HIPAA §164.312 (technical safeguards) – encryption, audit controls, integrity controls.
- NIST SP 800‑53 Rev 5 controls SC‑13 (Cryptographic Protection), SC‑28 (Protection of Information at Rest).
- WCAG 2.1 AA compliance for patient portal accessibility.

### 7. Requirements Traceability Matrix
| Req ID | Description | Source 
|--------|-------------|--------|
| REQ-001 | Business objective to achieve HIPAA compliance | Stakeholder interview 
| REQ-002 | Encrypt PHI at rest using AES‑256 | FR-002 
| REQ-003 | Encrypt PHI in transit using TLS 1.3 | FR-003 
| REQ-004 | Maintain immutable audit log for 7 years | FR-005 
| REQ-005 | Rotate encryption keys every 90 days | NFR‑004 
| REQ-006 | Provide role‑based access control | FR‑004 
| REQ-007 \u2013 Generate PDF summary with watermark and timestamp \u2013 Acceptance: PDF contains watermark and timestamp metadata.| FR‑006 
| REQ-008 \u2013 Perform quarterly disaster‑recovery drill \u2013 Acceptance: Drill checklist completed.| FR‑009 
| REQ-009 \u2013 Maintain operations manual reviewed by compliance \u2013 Acceptance: Manual reviewed.| FR‑011 
| REQ-010 \u2013 Deliver training videos ≤30 min total \u2013 Acceptance: Videos hosted on LMS.| FR‑012 

### 8. Key Performance Indicators (KPIs)
- **KPI‑01**: Form completion rate ≥92% weekly.
- **KPI‑02**: System uptime ≥99.9% monthly.<br>- **KPI‑03**: Zero HIPAA‑related security incidents in first 90 days.<br>- **KPI‑04**: Audit‑log retention compliance ≥100% for 7‑year period.<br>- **KPI‑05**: PDF export watermark accuracy – 100% of exported PDFs contain visible watermark and correct timestamp.<br>- **KPI‑06**: Automated test coverage ≥90% of functional requirements and ≥90% of edge‑case scenarios.<br>- **KPI‑07**: Full stack deployable on air‑gapped hardware within 30 minutes.<br>- **KPI‑08**: Stakeholder satisfaction average score ≥4.5/5.<br>

## Stakeholder Analysis
- **Patient (ST-01)**: Needs a secure, easy-to-complete intake form; expects privacy per HIPAA §164.530. *Owner: Compliance Officer*.
- **Front‑Desk Staff (ST-02)**: Requires quick data entry and verification; needs role-based permission to create records. *Owner: Operations Manager*.
- **Clinician (ST-03)**: Needs read-only access to patient history for care decisions; must see audit trail of any modifications. *Owner: Clinical Lead*.
- **Administrator (ST-04)**: Manages user roles, encryption keys, and system uptime; requires full audit-log visibility. *Owner: IT Security Manager*.
- **Compliance Officer (ST-05)**: Ensures all processes satisfy HIPAA and internal policies; monitors key rotation and log retention. *Owner: Compliance Officer*.

## Risk Management
| ID | Description | Mitigation Action (Concrete) |
|----|-------------|------------------------------|
| RISK-001 | Unauthorized access to PHI. |
Enforce RBAC; conduct quarterly penetration tests; log all access attempts; remediate findings within 30 days.
|
| RISK-002 | Data loss / corruption. |
Daily encrypted backups; weekly restore drills; backup integrity hash verification daily.
|
| RISK-003 | Deployment failure in air-gap environment. |
Use official base images scanned with Trivy; store images in internal registry; deployment scripts include health-check loops and automatic rollback.
|
| RISK-004 | Encryption key compromise. |
Store keys in air-gapped HSM; rotate keys every 90 days; audit key-access logs; alert on anomalous key usage.
|
| RISK-005 | Audit-log tampering. |
Write-once append-only storage with cryptographic hash chaining; daily hash chain verification; alerts on mismatch.
|

## Success Criteria
- All functional and non-functional requirements met with documented evidence.
- Compliance evidence for HIPAA §164.312, NIST SP 800‑53, WCAG 2.1 AA provided.
- Risk mitigation controls implemented and verified per risk register.
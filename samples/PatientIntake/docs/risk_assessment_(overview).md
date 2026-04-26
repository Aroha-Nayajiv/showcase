# Risk Assessment (Overview)

## System Architecture Vision Overview

1. **High‑Level Architecture**: The PatientIntake solution is organized as a three‑tier architecture consisting of a browser‑based SecureForm front‑end, a stateless Backend Service layer, and a PostgreSQL DataStorage tier. All components run in isolated Docker containers orchestrated by Docker‑Compose, enabling reproducible on‑prem deployment without external cloud dependencies. Communication between tiers is encrypted using TLS 1.3, satisfying HIPAA §164.312(e)(1) for transmission security.

2. **SecureForm Front‑End**: Implemented with an open‑source framework such as React or Vue.js, the web form captures patient demographics, insurance details, and medical history. Client‑side validation enforces required fields and format checks before data is transmitted. Each form field is encrypted at the browser level using the Web Crypto API (AES‑256‑GCM) so that plaintext never leaves the user's device, aligning with HIPAA §164.312(a)(2)(iv) for encryption at rest.

3. **Backend Service Layer**: A lightweight Python Flask or Node.js Express service receives the encrypted payload, performs server‑side validation, and forwards the ciphertext to the DataStorage tier. The service also generates PDF intake summaries using wkhtmltopdf, applies a dynamic watermark containing the staff ID and timestamp, and stores the PDF in an encrypted file store. Access to the PDF generation endpoint is restricted to RBAC roles "clinician" and "administrator" via JWT‑based authentication, meeting HIPAA §164.312(a)(1) for access control.

4. **DataStorage Tier (PostgreSQL)**: All patient records are persisted in PostgreSQL 15 with Transparent Data Encryption (TDE) enabled at the column level (AES‑256‑GCM). Row‑level security policies enforce role‑based access: admins have full read/write, clinicians have read‑only access to records of their assigned patients, and front‑desk staff have write‑only access for new submissions. An immutable audit log table records every SELECT, INSERT, UPDATE, and DELETE operation with user ID, timestamp, and operation type; the log is append‑only and protected by SHA‑256 hash chaining to detect tampering, satisfying HIPAA §164.312(b).

5. **Compliance and Monitoring**: Continuous compliance monitoring is achieved through open‑source tools such as OpenSCAP for configuration validation and Prometheus + Grafana dashboards for security metrics (e.g., TLS version compliance, failed login attempts). Alerts are generated for any deviation from the defined security baseline, providing evidence for HITRUST and SOC 2 audits.

6. **Risk Mitigation Overview**:
   - RISK‑001 (TLS downgrade) – Enforced TLS 1.3 only in Nginx reverse proxy; automated OpenSSL validation runs nightly.
   - RISK‑002 (Key leakage) – Encryption keys are stored in HashiCorp Vault with audit logging and quarterly rotation.
   - RISK‑003 (Audit‑log integrity) – Append‑only tables with SHA‑256 hash chaining; periodic integrity checksum verification.
   - RISK‑004 (Unauthorized read) – Column‑level permissions and regular penetration testing; alerts on anomalous read patterns.
   - RISK‑005 (Data loss) – Encrypted nightly backups to offline removable media; restore drills performed monthly.

7. **Deployment Model**: Docker‑Compose files define three networks (frontend, backend, db) with no external internet access. The air‑gap setup guide documents steps to preload container images on a secure USB, verify image signatures with Notary, and start the stack on an isolated VLAN. All configuration files are version‑controlled and signed, ensuring traceability and repeatability.

## Business Requirements for PatientIntake System

### FR-001: Secure Web Form for Patient Demographics and Insurance
- **Description**: The system shall present a responsive web form that captures patient name, date of birth, address, phone, insurance provider, and policy number.
- **Acceptance Criteria**: All form fields are validated client‑side and server‑side; successful submission stores data encrypted at field level using AES‑256‑GCM; validation error rate <2% on 1,000 test submissions; HIPAA §164.312(a)(2)(iv) compliance verified by independent audit.

### FR-002: Field‑Level Encryption at Rest and In Transit
- **Description**: Each PHI field must be encrypted before persistence and transmitted over TLS 1.3.
- **Acceptance Criteria**: Encryption library OpenSSL 3.0 with AES‑256‑GCM; TLS handshake negotiates TLS_AES_256_GCM_SHA384; no plaintext PHI observed in network capture or database dump; automated test suite confirms 100% encryption coverage.

### FR-003: Role‑Based Access Control (RBAC)
- **Description**: Access to stored submissions is limited to three roles: Administrator, Clinician, Front‑Desk.
- **Acceptance Criteria**: PostgreSQL row‑level security policies enforce least‑privilege; audit logs show no unauthorized read attempts in 30‑day simulation; role assignment changes require multi‑factor approval.

### FR-004: Immutable Audit Log
- **Description**: Every read, write, update, and export operation must be recorded with user ID, timestamp, operation type, and hash chain.
- **Acceptance Criteria**: Log entries stored in append‑only table with SHA‑256 hash chaining; integrity check passes 100% of the time; retention period 7 years as required by HIPAA §164.308(a)(1)(ii)(C).

### FR-005: PDF Intake Summary Generation
- **Description**: Authorized staff can generate a PDF summary of a patient's intake data.
- **Acceptance Criteria**: PDF generated within 500 ms; includes visible watermark with staff ID and ISO‑8601 timestamp; PDF is encrypted at rest using AES‑256‑GCM; export operation logged in audit trail.

### FR-006: Automated Testing Suite
- **Description**: Unit and integration tests must cover form validation, encryption, and RBAC edge cases.
- **Acceptance Criteria**: Test coverage ≥90% measured by coverage.py; CI pipeline fails on any regression; test cases TC‑001 through TC‑004 executed on each commit.

### FR-007: Docker‑Compose Air‑Gap Deployment
- **Description**: The entire stack shall be containerized and deployable via Docker‑Compose without external internet access.
- **Acceptance Criteria**: Deployment script completes in ≤2 minutes on a clean air‑gapped VM; all containers start successfully; no external image pulls required after initial offline load.

## Stakeholder Analysis for PatientIntake System

- **Stakeholder Group 1: Patients (ST-01)**
  - Primary Need: Secure, quick intake process that protects personal health information.
  - Pain Points: Concerns about data privacy, long form completion time.
  - Success Metric: Form completion time ≤2 minutes, patient satisfaction ≥90% (survey).

- **Stakeholder Group 2: Front‑Desk Staff (ST-02)**
  - Primary Need: Intuitive form that reduces data entry errors and provides immediate confirmation of successful submission.
  - Success Metric: Validation error rate <2% and average entry time ≤3 minutes per patient.

- **Stakeholder Group 3: Clinician (ST-03)**
  - Primary Need: Reliable access to complete, accurate patient intake data for care decisions.
  - Success Metric: 100% read access to assigned patients with latency ≤200 ms.

- **Stakeholder Group 4: Administrator (ST-04)**
  - Primary Need: Enforce RBAC policies, monitor audit logs, generate compliance reports.
  - Success Metric: No unauthorized access events; audit log integrity verified daily; compliance report generation ≤5 minutes.

## Additional Inception Artifacts

### User Stories (sample)
- **US-001**: As a Front‑Desk staff member, I want to enter patient demographics into a secure web form so that data is encrypted at the point of entry.
  - **Acceptance Criteria**: Form validates required fields, encrypts each field client‑side, submits over TLS 1.3; audit log records the submission event.
- **US-002**: As a Clinician, I need read‑only access to patient records for my assigned patients.
  - **Acceptance Criteria**: Role‑based row‑level security restricts access; attempts to read unauthorized records are denied and logged.

### API Specification Overview (business level)
- **POST /api/intake**: Accepts encrypted payload of patient intake data.
  - **Business Requirement**: Must enforce TLS 1.3 and JWT authentication for authorized roles.
- **GET /api/patient/{id}/pdf**: Generates PDF summary.
  - **Business Requirement**: Accessible only to Clinician and Administrator roles; response time ≤500 ms.

### Risk Mitigation Enhancements
- **RISK-001**: Enforce TLS 1.3 only via Nginx configuration and automated OpenSSL validation nightly.
- **RISK-002**: Store encryption keys in HashiCorp Vault with MFA and audit logging; rotate keys every 90 days.
- **RISK-003**: Implement immutable append‑only audit log with SHA‑256 hash chaining; run daily integrity checksum verification.
- **RISK-004**: Apply column‑level permissions and quarterly penetration testing to detect unauthorized reads.
- **RISK-005**: Perform encrypted nightly backups to offline media; test restore monthly.

## Success Metrics (KPIs)
- KPI‑01: Form completion rate ≥92% weekly.
- KPI‑02: System availability ≥99.9% monthly (NFR‑001).
- KPI‑03: Mean response time ≤200 ms for form submission (NFR‑002).
- KPI‑04: Encryption key rotation every 90 days with zero downtime.
- KPI‑05: Test coverage ≥90% with CI pipeline fail on regression (REQ‑004).

## Business Vision
The PatientIntake system will provide a secure, efficient, and compliant web‑based intake workflow for capturing patient demographics, insurance information, and medical history. Data will be encrypted at field level in transit (TLS 1.3) and at rest (AES‑256‑GCM), stored in a PostgreSQL database with role‑based access control, and audited fully. Authorized staff can generate watermarked PDF summaries within 500 ms. The solution will be containerized and deployable via Docker‑Compose in air‑gap environments.

## Risk Register
| ID | Description | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| RISK-001 | TLS misconfiguration allowing downgrade attacks | Medium | High | Enforce TLS 1.3 only; disable weak ciphers; nightly OpenSSL validation suite; monitor logs for TLS 1.2 connections |
| RISK-002 | Encryption key leakage from Vault | Low | High | Store keys in HashiCorp Vault with sealed storage; rotate quarterly; audit logging; restrict access to Admin role |
| RISK-003 | Audit log integrity failure | Medium | Medium | Append‑only tables with SHA‑256 hash chaining; daily checksum verification jobs |
| RISK-004 | Unauthorized data access by Front‑Desk staff | Low | High | Column‑level RBAC exposing only demographics; quarterly penetration tests; monitor for unauthorized column reads |
| RISK-005 | Data loss in air‑gap deployment | Low | High | Encrypted nightly backups to offline media; SHA‑256 verification; monthly restore drills |
| RISK-006 | Open‑source component vulnerabilities | Medium | Medium | Weekly vulnerability scans; Dependabot alerts; patch within 30 days of critical CVE |

## Success Criteria & KPIs
- **Encryption Coverage** (REQ‑001): ≥99.9% of PHI fields encrypted; nightly scan reports 0 findings.
- **Access Control** (REQ‑002): Unauthorized attempts ≤1 per month; RBAC test suite 100% pass.
- **Audit Log Completeness** (REQ‑003): 100% of operations logged; daily integrity check passes.
- **PDF Generation Performance** (REQ‑004): 95th percentile ≤500 ms for 50 concurrent users.
- **System Availability** (NFR‑001): ≥99.9% monthly uptime.
- **Form Response Time** (NFR‑002): p95 ≤200 ms.

## Acceptance Criteria Summary
Each functional requirement above includes explicit acceptance criteria. Non‑functional requirements are measured by the KPIs listed.

*Document prepared by Refiner Agent addressing reviewer feedback and enhancing completeness.*

## Functional Requirements
- **FR-001**: Secure web form to capture patient demographics, insurance, and medical history. *Acceptance*: Form fields validated client‑side; mandatory fields reject empty submission.
- **FR-002**: Field‑level encryption at rest (AES‑256‑GCM) and in transit (TLS 1.3). *Acceptance*: Security scan confirms no plaintext PHI in storage or network traffic.
- **FR-003**: Persist submissions in PostgreSQL with role‑based access control (admin, clinician, front‑desk). *Acceptance*: RBAC tests show least‑privilege enforcement; unauthorized reads denied.
- **FR-004**: Generate PDF intake summary with watermark and timestamp; exportable by authorized staff only. *Acceptance*: PDF contains staff ID watermark; export logs recorded.
- **FR-005**: Immutable audit log for every read/write/export operation. *Acceptance*: SHA‑256 hash chaining verified; tampering triggers alert.
- **FR-006**: Deploy via Docker‑Compose on air‑gapped on‑prem hardware. *Acceptance*: Deployment completes ≤ 120 seconds on clean VM.
## Traceability Matrix
| Requirement ID | Source Artifact |
|---|---|
| FR-001 | Business Vision |
| FR-002 | Security Requirements |
| FR-003 | Data Management |
| FR-004 | PDF Generation |
| FR-005 | Audit Logging |
| FR-006 | Deployment Guide |
| REQ-001 | Encryption in transit & at rest |
| REQ-002 | RBAC enforcement |
| REQ-003 | PDF watermark & performance |
| REQ-004 | Test coverage ≥ 90 % |
| REQ-005 | Docker‑Compose deployment ≤ 2 min |
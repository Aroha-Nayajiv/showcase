# Business Requirements (Overview)

### 2. Stakeholder Analysis
- **ST-01 – Patient**: Needs privacy, quick intake, assurance that data is encrypted at rest and in transit.
- **ST-02 – Front‑Desk Staff**: Requires an intuitive web form, immediate validation feedback, and ability to submit records without technical overhead.
- **ST-03 – Clinician**: Must retrieve complete patient histories quickly, with read‑only access unless explicitly granted edit rights.
- **ST-04 – System Administrator**: Responsible for key rotation, audit‑log retention, and Docker‑Compose deployment on isolated network.
- **ST-05 – Compliance Officer**: Needs evidence of HIPAA controls, immutable audit logs for 7 years, and PDF export watermark compliance.

### 5. Success Criteria and KPIs
| KPI | Description |
|-----|-------------|
| KPI-01 | Encryption Compliance: 100 % of PHI fields encrypted; verified by quarterly security scan. |
| KPI-02 | Form Completion Rate: ≥90 % of patients complete intake without abandonment. |
| KPI-03 | Audit Log Completeness: 100 % of CRUD operations logged; audited monthly. |
| KPI-04 | PDF Watermark Accuracy: 100 % of exported PDFs contain correct watermark "Confidential – Patient Intake" and timestamp. |
| KPI-05 | Deployment Reproducibility: Successful deployment on three fresh air‑gap servers without manual configuration. |
| KPI-06 | System Availability: 99.9 % uptime measured monthly. |
| KPI-07 | Deployment Automation: Docker Compose deployment completes within 5 minutes on a clean host. |

### 6. Risk Assessment
| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| RISK-001 | Key‑management failure | Medium | High | Automated rotation script using HashiCorp Vault; audit‑log of key usage; quarterly key‑rotation drill. |
| RISK-002 | Deployment inconsistency | Medium | Medium | Version‑pinned Docker images; CI pipeline validates compose file; reproducibility test on air‑gap hardware. |
| RISK-003 | Unauthorized data access | Low | High | Strict RBAC enforcement; regular penetration testing; alerting on anomalous access patterns. |
| RISK-004 | Audit Log Tampering | Low | Critical | Write‑once append‑only storage with hash chaining; daily integrity checksum verification; immutable backup snapshots. |
| RISK-005 | Performance Degradation Under Peak Load | Medium | Moderate | Load testing with Locust; thread‑pool optimization; ensure 95th percentile ≤200 ms; auto‑scaling of web tier in on‑prem environment. |

### 9. User Stories
- **US-001**: As a Patient, I want to enter my personal and insurance information into a secure web form so that my data is protected at rest and in transit.
- **US-002**: As Front‑Desk Staff, I need immediate validation feedback when entering patient data so that I can correct errors before submission.
- **US-003**: As a Clinician, I want read‑only access to a patient’s intake record so I can review history without risking accidental modification.
- **US-004**: As a System Administrator, I need automated key rotation every 90 days and an immutable audit log so that I can demonstrate compliance during audits.
- **US-005**: As a Compliance Officer, I require a PDF summary with a visible watermark and timestamp to verify that exported documents are authentic and traceable.

### 10. Deployment and Operations (DEP)
| ID | Description |
|----|-------------|
| DEP-001 | Docker Compose architecture with version 2.15+, official base images, digests recorded. |
| DEP-002 | Air‑gap deployment procedure using signed tarball, image digest verification, no external network access. |
| DEP-003 | Configuration management with encrypted GPG directory, Docker secrets injection, audit‑log of secret rotations. |
| DEP-004 | Monitoring with Prometheus v2.45+ and Grafana v10+, SLOs: 99.9 % availability, 95 % requests <200 ms, audit‑log lag ≤5 s. |
| DEP-005 | Backup and DR: nightly pg_dump, 7‑year retention, RTO ≤4 h, RPO ≤24 h, quarterly restore test. |
| DEP-006 | Compliance report generated after each release, signed, archived 7 years. |
| DEP-007 | Operational run‑book in Markdown, reviewed by Compliance Officer and System Administrator. |

### 11. Accessibility and UX
- WCAG 2.1 AA compliance; axe‑core scan reports zero violations.
- **NFR‑UX‑001**: Contrast ratio ≥4.5:1.
- **NFR‑UX‑002**: Keyboard navigation complete without mouse.
- **NFR‑UX‑003**: ARIA labels for all controls.
- **FR‑UX‑001**: Form loads within 2 seconds on 3G.
- **FR‑UX‑002**: Inline validation messages appear within 500 ms.
- **FR‑UX‑003**: Progressive disclosure with ≥85 % task completion.
- **FR‑PDF‑001**: Authorized staff generate PDF with single click <1 s.
- **FR‑PDF‑002**: PDF includes visible watermark with staff username and timestamp.
- **FR‑PDF‑003**: PDF filename pattern PATIENTID_YYYYMMDD_HHMM.pdf, stored encrypted.

### 7. Security and Compliance Requirements
| ID | Requirement 
|---|---
| REQ-001 | All patient data fields must be encrypted using AES‑256‑GCM before persistence. Acceptance: Ciphertext stored; decryption only via Vault key 
| REQ-002 | All HTTP traffic must be protected by TLS 1.3 with cipher suite TLS_AES_256_GCM_SHA384. Acceptance: SSLyze scan shows only TLS 1.3 \ n| REQ-003 | Encryption keys must be rotated every 90 days via automated Vault job. Acceptance: Log entry "Key rotation completed" appears \ n| REQ-004 | Immutable audit log for every operation, retained 7 years per HIPAA §164.310(d)(1). Acceptance: Log query returns complete unaltered sequence; hash‑chain verification passes \ n| REQ-005 | PDF export must include visible watermark "Confidential – Patient Intake" and export timestamp. Acceptance: PDF contains watermark text and metadata timestamp \ n### 8. Deployment and Operations\ n| ID | Description \ n|- DEP-001 |- Docker Compose architecture with version 2.15+, official base images, digests recorded |- DEP -002 |- Air‑gap deployment procedure using signed tarball, image digest verification, no external network |- DEP -003 |- Configuration management with encrypted GPG directory, Docker secrets injection, audit‑log of secret rotations |- DEP -004 |- Monitoring with Prometheus v2.45+ and Grafana v10+, SLOs: 99.9 % availability, 95 % requests <200 ms, audit‑log lag ≤5 s |- DEP -005 |- Backup and DR: nightly pg_dump, 7‑year retention, RTO ≤4 h, RPO ≤24 h, quarterly restore test |- DEP -006 |- Compliance report generated after each release, signed, archived 7 years |- DEP -007 |- Operational run‑book in Markdown, reviewed by Compliance Officer and System Administrator \ n### 9. Accessibility and UX\ n|- WCAG 2.1 AA |- Frontend must meet WCAG 2.1 AA; axe‑core scan reports zero violations |- NFR UX 001 |- Contrast ratio ≥4.5:1; automated scan passes |- NFR UX 002 |- Keyboard navigation complete without mouse; manual test passes |- NFR UX 003 |- ARIA labels for all controls; screen‑reader test passes |- FR UX 001 |- Form loads within 2 seconds on 3G; Lighthouse audit passes |- FR UX 002 |- Inline validation messages appear within 500 ms; UI test passes |- FR UX 003 |- Progressive disclosure with ≥85 % task completion; usability test passes |- FR PDF 001 |- Authorized staff generate PDF with single click <1 s |- FR PDF 002 |- PDF includes visible watermark with staff username and timestamp \ n### 10. Traceability Matrix\ n|- Stakeholder ID |- Functional Requirement(s) Covered -|- ST‐01 (Patient) |- FR‐001, FR‐002, FR‐003, FR‐005 -|- ST‐02 (Front‐Desk) |- FR‐001, FR‐004, FR‐007 -|- ST‐03 (Clinician) |- FR‐004, FR‐005, FR‐006 -|- ST‐04 (System Administrator) |- FR‐004, FR‐006, FR‐008 , DEP‐001…DEP‐007 -|- ST‐05 (Compliance Officer) |- REQ‐001…REQ‐005 , NFR‐001…NFR‐006 , KPI‐01…KPI‐07 \ n### 11. User Stories\ n*- As a Patient, I want my personal and medical information to be encrypted at rest and in transit so that my privacy is protected.*\ n*- As Front‑Desk Staff, I need an intuitive web form that validates input instantly so I can register patients efficiently.*\ n*- As a Clinician, I require read‑only access to a patient’s complete intake summary with a clear audit trail.*\ n*- As a System Administrator, I must be able to rotate encryption keys automatically every 90 days and verify audit‑log integrity.*\ n*- As a Compliance Officer, I need evidence that every PDF export contains the standardized watermark "Confidential – Patient Intake" and a timestamp for audit purposes.

### 1. Vision and Strategic Objectives
The Patient Intake system will enable on-premise, open-source collection of protected health information (PHI) while meeting HIPAA §164.312(a)(2)(iv) encryption requirements. The solution must be fully auditable, support role-based access for Admin, Clinician, and Front-Desk staff, and generate a watermarked PDF summary for authorized export. Success is measured by compliance audit pass, <200 ms form response, and 99.9 % system uptime.

### 3. Functional Requirements (User Stories & Acceptance Criteria)
**FR-001**: *As a Front-Desk Staff member, I want to enter patient demographics, insurance, and medical history via a structured web form so that data is captured accurately.*
- Acceptance: 100 % of required fields captured; form validation error rate <2 %.
**FR-002**: *As the System, I encrypt each field at rest using AES-256 so that PHI is protected.*
- Acceptance: Encryption verified by automated test that raw DB values are non-readable.
**FR-003**: *As a user, I transmit all data over TLS 1.3 so that data in transit is protected.*
- Acceptance: No TLS 1.2 or lower connections observed in scans.
**FR-004**: *As an Admin, I manage role-based access control (admin, clinician, front-desk) so that users see only authorized functions.*
- Acceptance: Role-specific UI elements hidden; unauthorized attempts logged and blocked.
**FR-005**: *As an authorized staff member, I generate a PDF intake summary with a visible watermark and export timestamp so that the document is tamper-evident.*
- Acceptance: PDF contains watermark text \"Confidential – Patient Intake\" and timestamp metadata.
**FR-006**: *As the system, I record every read/write operation in an immutable audit log retained for 7 years so that all activity is traceable.*
- Acceptance: Log entries include user ID, timestamp, operation type; logs stored in append-only format with hash-chaining for tamper detection.
**FR-007**: *As the development team, I provide automated unit and integration tests covering form validation, encryption, and RBAC edge cases so that quality is assured.*
- Acceptance: Test suite achieves ≥90 % code coverage; all tests pass in CI pipeline.
**FR-008**: *As the operations team, I deploy the entire stack with Docker Compose on-premises without external cloud dependencies so that the solution can run in air-gapped environments.*
- Acceptance: `docker compose up -d` brings up all services on a clean host; deployment reproducible on three fresh air-gap servers.

## Business Vision
The patient intake system will enable secure collection, storage, and reporting of protected health information (PHI) while complying with HIPAA and using only open-source technologies.

## Acceptance Criteria
Each requirement above includes measurable acceptance criteria. Additionally, all user stories must pass automated unit and integration tests covering form validation, encryption verification, RBAC enforcement, and PDF generation.
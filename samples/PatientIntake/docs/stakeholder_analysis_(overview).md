# Stakeholder Analysis (Overview)

## Inception Vision – Patient Intake System
Purpose: Provide a secure, open‑source, on‑premise patient intake platform that enables collection, storage, and export of protected health information (PHI) while meeting HIPAA Security Rule requirements. The system must support role‑based access for administrators, clinicians, and front‑desk staff, generate immutable audit logs, and produce watermarked PDF summaries for authorized personnel.

### Strategic Objectives
1. Regulatory Compliance – Achieve full compliance with HIPAA §164.312(a)(2)(iv) encryption safeguards and §164.308(a)(1) audit controls. Success measured by passing an external compliance audit with zero findings.
2. Open‑Source Stack – Use only community‑maintained, permissively licensed components (PostgreSQL, Nginx, Flask, wkhtmltopdf). No proprietary libraries.
3. On‑Prem Deployment – Deliver Docker Compose configuration that can be launched in an air‑gapped environment without internet access. Deployment reproducibility verified by a scripted “docker‑compose up” completing within 5 minutes on reference hardware.
4. Data Privacy & Integrity – All PHI fields encrypted at rest with AES‑256‑GCM and in transit with TLS 1.3. Keys rotated every 90 days and logged. Immutable append‑only audit logs retained for seven years.
5. Operational Efficiency – Reduce average form‑completion time to under 3 minutes and achieve 99.9 % system uptime measured over a 30‑day period.

### Scope Definition
- **In‑Scope:** Web‑based intake form, PostgreSQL database with row‑level security, role‑based access control, audit logging, PDF generation with watermark and timestamp, Docker Compose deployment, documentation of air‑gap setup.
- **Out‑Of‑Scope:** Cloud services, mobile native applications, integration with external EHR systems, advanced analytics beyond basic reporting.

### Stakeholder Summary
- **ST‑01 Patient** – Needs assurance that personal data is protected and intake process is quick and accessible.
- **ST‑02 Front‑Desk Staff** – Requires an intuitive form interface and ability to submit records without technical barriers.
- **ST‑03 Clinician** – Must retrieve complete, accurate patient histories instantly while respecting least‑privilege access.
- **ST‑04 Administrator** – Needs full control over user roles, encryption key management, and system monitoring.
- **ST‑05 Compliance Officer** – Demands evidence of HIPAA controls, audit‑log completeness, and periodic compliance reporting.

### Risk Register
- **RISK‑001 – Key Management Failure** (Likelihood: M, Impact: H). Mitigation: Deploy HashiCorp Vault open-source edition with automated rotation, audit logging, and backup of encrypted keys.
- **RISK‑002 – Deployment Failure in Air‑Gap** (Likelihood: L, Impact: M). Mitigation: Provide offline Docker images signed with SHA256, detailed step‑by-step air‑gap guide validated in a test lab.
- **RISK‑003 – Unauthorized Access via Misconfigured RBAC** (Likelihood: M, Impact: H). Mitigation: Implement role‑based access policies reviewed against a security checklist; enforce PostgreSQL row‑level security with explicit role permissions.
- **RISK\-004 – Audit Log Tampering** (Likelihood: L, Impact: H). Mitigation: Store logs in append‑only write‑once storage; chain log entries with cryptographic hashes; regular integrity verification.
- **RISK\-005 – Performance Degradation Under Load** (Likelihood: M, Impact: M). Mitigation: Conduct load testing to ensure response time ≤200 ms; use connection pooling and read replicas for PostgreSQL.

### User Stories
- **US\-001** (Stakeholder: ST\-02 Front‑Desk Staff) – As a front‑desk staff member, I want a simple web form that validates required fields in real time so I can quickly enter patient information without errors.
- **US\-002** (Stakeholder: ST\-03 Clinician) – As a clinician, I need to view a patient’s intake data and PDF summary instantly while ensuring the data is encrypted in transit, so I can make informed decisions securely.
- **US\-003** (Stakeholder: ST\-04 Administrator) – As an administrator, I want to manage user roles and rotate encryption keys automatically every 90 days, so the system remains compliant with HIPAA.
- **US\-004** (Stakeholder: ST\-05 Compliance Officer) – As a compliance officer, I require audit logs that are immutable and retained for seven years, so I can demonstrate regulatory adherence during audits.
- **US\-005** (Stakeholder: ST\-01 Patient) – As a patient, I expect my submitted information to be stored securely and to receive a PDF summary with a visible confidentiality watermark when requested.

### Business Vision
Provide a secure, open‑source, on‑premise patient intake platform that collects demographics, insurance and medical history via a web form, stores PHI encrypted at rest and in transit, and generates watermarked PDF summaries for authorized staff. The solution must satisfy HIPAA Security Rule, ISO‑27001 controls and achieve high availability.

### Success Criteria
- All functional requirements REQ‑001 – REQ‑006 satisfied and signed off by stakeholders.
- No critical findings in final HIPAA compliance audit.
- Deployment scripts execute without manual intervention in air‑gapped environment on three fresh Linux hosts.
- KPI targets met for at least two consecutive months post‑launch (encryption verification, audit log completeness, TLS negotiation, PDF integrity, deployment reproducibility, form completion rate ≥92 %, availability ≥99.9 %).

## Security and Compliance Requirements
- FR‑001 (Field‑Level Encryption at Rest) – Requirement ID: FR‑001 – All patient‑identifiable fields must be encrypted at rest using AES‑256‑GCM. Acceptance: Encryption verified by automated tests; keys never stored in plaintext. HIPAA Reference: 45 CFR §164.312(a)(2)(iv).
- FR‑002 (Transport Layer Security) – Requirement ID: FR‑002 – All network communication must use TLS 1.3 with forward secrecy. Acceptance: sslscan reports TLS 1.3 minimum; weaker cipher suites rejected. HIPAA Reference: 45 CFR §164.312(e)(1).
- FR‑003 (Encryption Key Management and Rotation) – Requirement ID: FR‑003 – Keys generated using FIPS‑140‑2 RNG, stored in HSM emulator, rotated every 90 days. Acceptance: Automated job logs show successful rotation; old keys archived 30 days then destroyed. HIPAA Reference: 45 CFR §164.308(a)(1)(ii).
- FR‑004 (Immutable Audit Logging) – Requirement ID: FR‑004 – Every read/write/update/delete generates immutable audit log entry with user ID, timestamp, operation type, record identifier. Acceptance: Logs written to WORM file system; hash chaining verifies tamper‑evidence; retention 7 years. HIPAA Reference: 45 CFR §164.312(b).
- FR‑005 (Access Control Enforcement) – Requirement ID: FR‑005 – RBAC restricts data access to three roles. Acceptance: Penetration tests demonstrate Front‑Desk cannot read medical history; Admin cannot modify encrypted data without proper key. HIPAA Reference: 45 CFR §164.308(a)(1).

## KPIs (Unified)
- KPI‑001: Encryption Verification – 100 % of PHI fields encrypted at rest.
- KPI‑002: Audit Log Completeness – 100 % coverage of CRUD operations, audited monthly.
- KPI‑003: Transport Security – 100 % TLS 1.3 negotiation.
- KPI‑004: PDF Export Integrity – 100 % of PDFs include watermark and timestamp.
- KPI‑005: Deployment Reproducibility – 100 % successful deployment on three fresh Linux hosts without external network access.
- KPI‑006: Form Completion Rate – ≥92 % completion rate measured over 30 days.
- KPI‑007: System Availability – ≥99.9 % monthly uptime.

## Governance and Documentation Overview
- GOV‑001 Governance Framework – Aligns with HIPAA §164.308(a) and ISO/IEC 27001 Annex A. Quarterly governance board meetings, monthly compliance reviews, change‑control board (CCB) evaluates any data handling modifications. Decision authority assigned to Compliance Officer (ST‑04) and System Administrator (ST‑03). All decisions recorded in Governance Log (GL‑001) with timestamps and participant signatures.
- DOC‑001 Documentation Standards – Artifacts follow open‑source documentation style (Markdown, Git version control). Each document includes unique identifier, version, author, review date, and approval status. Retained for minimum seven years to satisfy HIPAA audit‑log retention.
- REV‑001 Review and Approval Cycle – Draft → Peer Review (two reviewers) → Revision → CCB approval → Publication.

## Technology Strategy and Open‑Source Stack
1. Data Store – PostgreSQL 15 with pgcrypto AES‑256‑GCM encryption; keys managed by HashiCorp Vault, rotated every 90 days.
2. Application Layer – Flask web framework with WTForms for validation; client side uses React with HTTPS enforced.
3. PDF Generation – wkhtmltopdf invoked via Flask endpoint; watermark added using PyPDF2.
4. Containerization – Docker Compose defines services (web, db, vault, monitoring); images built from official base images and scanned for vulnerabilities.
5. Monitoring – Prometheus + Grafana for uptime and response time alerts.

## Data Model Overview
- Table **patients**: stores encrypted PHI fields (name, DOB, insurance) using pgcrypto column encryption.
- Table **audit_log**: immutable log entries with user_id, timestamp, operation_type, record_id, hash_chain.
- Table **users**: role definitions and credential references for RBAC enforcement.
- Table **encryption_keys**: metadata for key versioning; actual keys stored in Vault.

## Traceability Matrix
| Requirement ID | Description | Stakeholder(s) | Acceptance Criteria |
|---|---|---|---|
| FR‑001 | Collect patient demographics via web form | ST‑03, ST‑04 | Form captures all required fields; success rate ≥95 % |
| FR‑002 | Field‑level encryption at rest | ST‑04, ST‑05 | AES‑256‑GCM encryption verified by tests |
| FR‑003 | Secure data in transit | ST‑03, ST‑04 | TLS 1.3 enforced; no plaintext traffic |
| FR‑004 | RBAC implementation | ST‑03, ST‑02 | Role permissions enforced; audit logged |
| FR‑005 | PDF summary generation | ST‑03, ST‑05 | PDF includes watermark "Confidential – Patient Intake" and timestamp |
| FR‑006 | Immutable audit log | ST‑05 | Log entries immutable; retention 7 years |
| FR‑007 | Automated testing | ST‑04 | ≥90 % coverage; CI passes |
| FR‑008 | Docker Compose deployment | ST‑04 | `docker compose up` succeeds on air‑gap host |
| NFR‑001 | Form response time ≤200 ms | ST‑03 | Measured p95 ≤200 ms |
| NFR‑002 | System availability ≥99.9 % | ST‑05 | Monitored via Prometheus |
| NFR\-003 | Encryption strength AES‑256‑GCM | ST‑04 | Verified by test vectors |

## Functional Requirements
- **REQ-001**: All PHI fields shall be encrypted at rest using AES-256-GCM.
  - Acceptance: Decryption test vectors verify successful recovery of each field.
  - Owner: ST-04 Administrator
- **REQ-002**: Data in transit shall be protected with TLS 1.3.
  - Acceptance: OWASP ZAP scan shows no mixed-content warnings.
  - Owner: ST-04 Administrator
- **REQ-003**: Encryption keys shall be rotated every 90 days and logged.
  - Acceptance: Audit log contains a rotation entry for each key within the period.
  - Owner: ST-04 Administrator
- **REQ-004**: Every read/write operation shall generate an immutable audit log entry containing user ID, timestamp, operation type, and affected record.
  - Acceptance: Log retention ≥7 years; hash-chaining verified.
  - Owner: ST-05 Compliance Officer
- **REQ-005**: Front-end form shall capture patient demographics, insurance, and medical history with no more than 12 fields per screen and progressive disclosure.
  - Acceptance: Usability test shows average completion ≤90 seconds and 95% completion rate.
  - Owner: ST-02 Front-Desk Staff
- **REQ-006**: Inline validation shall display error messages within 2 seconds and comply with WCAG 2.1 AA.
  - Acceptance: Axe core audit passes; error latency measured ≤2 s.
  - Owner: ST-02 Front-Desk Staff
- **REQ-007**: Authorized staff shall generate a PDF summary within 3 seconds; PDF size ≤500 KB; include watermark \"Confidential – Patient ID: {patient_id}\" and ISO‑8601 timestamp.
  - Acceptance: Automated test validates generation time, size, and watermark content.
  - Owner: ST-03 Clinician
- **REQ-008**: Automated unit and integration tests shall cover form validation, encryption, and RBAC edge cases.
  - Acceptance: Test coverage ≥80% and CI pipeline passes.
  - Owner: ST-04 Administrator
- **REQ-009**: Deployment shall be performed via Docker Compose version 2.20 with all images pinned to SHA‑256 digests; full stack up in ≤5 minutes on reference hardware.
  - Acceptance: Deployment script completes without external network access.
  - Owner: ST-04 Administrator
- **REQ-010**: System shall retain audit logs for ≥7 years and protect them against tampering using append-only storage.
  - Acceptance: Log integrity checks succeed after simulated tamper attempts.
  - Owner: ST-05 Compliance Officer
- **REQ-011**: Monitoring shall expose Prometheus metrics; alerts fire for critical events within 1 minute.
  - Acceptance: Alertmanager triggers as defined.
  - Owner: ST-04 Administrator
- **REQ-012**: Backup and disaster recovery shall perform encrypted nightly pg_dump backups; RTO ≤15 minutes, RPO ≤24 hours.
  - Acceptance: Restore test completes within RTO window.
  - Owner: ST-04 Administrator

## Assumptions
- All open-source components are maintained and receive security updates.
- The reference hardware meets minimum specifications (2 CPU cores, 4 GB RAM).

## Constraints
- No external cloud services may be used.
- All images must be pre-downloaded for air-gap deployment.
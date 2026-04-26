# Stakeholder Analysis (Overview)

## Stakeholder Analysis (Overview)

### Business Vision
The PatientIntake project delivers a secure, open‑source web‑based intake system that captures patient demographics, insurance details, and medical history in a single structured form. Field‑level encryption at rest (AES‑256‑GCM) and in transit (TLS 1.3) satisfies HIPAA §164.312(a)(2)(iv). The vision is to reduce intake time by 30%, achieve data‑entry accuracy >95%, and provide immutable audit logs for compliance.

### Stakeholders
- **ST-01 Patient** – Needs assurance that PHI is protected and the intake experience is quick. Ownership: Compliance Officer.
- **ST-02 Front‑Desk Staff** – Requires an intuitive form with real‑time validation and instant submission confirmation. Ownership: Administrator.
- **ST-03 Clinician** – Needs immediate, accurate access to complete patient records for care decisions. Ownership: Administrator.
- **ST-04 Administrator** – Responsible for RBAC configuration, audit‑log monitoring, and key management. Ownership: Administrator.
- **ST-05 Compliance Officer** – Requires documented evidence of HIPAA/HITRUST compliance. Ownership: Compliance Officer.

### Functional Requirements with Acceptance Criteria
- **REQ-001** – Web form shall collect name, DOB, address, phone, insurance provider, policy number, and medical history. *Acceptance*: All fields mandatory, client‑side validation error <2%, encrypted at field level before storage.
- **REQ-002** – All data in transit shall use TLS 1.3 with forward‑secrecy cipher suites. *Acceptance*: Automated SSL‑Labs scan returns A grade; no TLS 1.2 connections permitted.
- **REQ-003** – Submissions persisted in PostgreSQL with row‑level security enforcing RBAC tiers (admin, clinician, front‑desk). *Acceptance*: Unauthorized role queries are denied; authorized queries succeed.
- **REQ-004** – Every read/write operation shall generate an immutable audit log entry (user ID, timestamp, operation type, record ID). *Acceptance*: Logs are append‑only, SHA‑256 hash‑chained, and 99%+ completeness verified weekly.
- **REQ-005** – Authorized staff shall export a PDF summary per patient, watermarked with staff ID and timestamp. *Acceptance*: PDF generated ≤500 ms for 95% of requests; watermark present and correct.

### Non‑Functional Requirements
- **NFR-001** – System availability ≥99.9% monthly.
- **NFR-002** – Form response time p95 ≤200 ms under 50 concurrent users.
- **NFR-003** – Data at rest encryption AES‑256‑GCM; keys stored in on‑prem HSM.
- **NFR-004** – Audit log retention ≥7 years; tamper‑evidence via hash chaining.
- **NFR-005** – Deployment via Docker‑Compose; air‑gap setup guide provided.

### Risks and Mitigations with Owners
- **RISK-001 (TLS misconfiguration)** – Likelihood Medium, Impact High. *Mitigation*: Enforce TLS 1.3 only in Nginx config; nightly OpenSSL validation suite. *Owner*: Administrator.
- **RISK-002 (Encryption key leakage)** – Likelihood Low, Impact High. *Mitigation*: Store keys in HSM, rotate quarterly, audit Vault access logs. *Owner*: Administrator.
- **RISK-003 (Audit‑log integrity loss)** – Likelihood Medium, Impact Medium. *Mitigation*: Append‑only tables with SHA‑256 chaining; periodic integrity checksum verification. *Owner*: Compliance Officer.
- **RISK-004 (Performance degradation)** – Likelihood Medium, Impact Medium. *Mitigation*: Container resource limits, auto‑scale Flask workers, load‑test to 150% expected peak. *Owner*: Administrator.

### Success Criteria / KPIs
- **KPI-01** – Form completion rate ≥90% (successful submissions / total attempts).
- **KPI-02** – Encryption compliance audit passes 100% (TLS and at‑rest).
- **KPI-03** – Audit‑log completeness ≥99% (no missing entries weekly).
- **KPI-04** – PDF export latency ≤500 ms for 95% of requests.
- **KPI-05** – Deployment time on fresh air‑gapped VM ≤2 minutes using Docker‑Compose scripts.

### Scope Definition
- **In‑Scope**: Secure web form, PostgreSQL storage with RBAC, immutable audit logging, PDF generation with watermark, automated unit/integration test suite, Docker‑Compose deployment, air‑gap documentation.
- **Out‑Of‑Scope**: Integration with external EHR systems, mobile app front‑ends, cloud‑based key management services, advanced analytics dashboards.

### Traceability Matrix
| Requirement | Stakeholder(s) | Risk(s) | Owner |
|-------------|----------------|---------|------|
| REQ-001 | ST-01, ST-02 | RISK-002 | Administrator |
| REQ-002 | ST-01, ST-02 | RISK-001 | Administrator |
| REQ-003 | ST-03, ST-04 | RISK-003 | Administrator |
| REQ-004 | ST-04, ST-05 | RISK-003 | Compliance Officer |
| REQ-005 | ST-03, ST-04 | RISK-004 | Administrator |

### User Stories (example)
*As a Patient (ST‑01), I want to submit my information through a secure web form so that my PHI is protected and I receive confirmation within 5 seconds.*
*As Front‑Desk Staff (ST‑02), I need real‑time validation feedback so that I can correct errors before submission and keep entry time under 30 seconds.*
*As a Clinician (ST‑03), I require read‑only access to the encrypted patient record and PDF export with watermark so I can make timely care decisions.*
*As an Administrator (ST‑04), I must configure RBAC roles and monitor audit logs to ensure compliance and detect unauthorized access.*
*As a Compliance Officer (ST‑05), I need immutable audit logs retained for 7 years to demonstrate HIPAA/HITRUST compliance during audits.*

## Business Vision
The Patient Intake system will provide a secure, efficient, and compliant way to capture patient demographics, insurance information, and medical history, ensuring HIPAA and HITRUST compliance while supporting rapid intake workflows for front‑desk staff and clinicians.
## Risk Register
| ID | Description | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| RISK-001 | TLS 1.3 misconfiguration allowing downgrade attacks | Medium | High | Enforce TLS 1.3 only via Nginx config; run automated OpenSSL validation nightly; fail builds on non‑TLS 1.3. | ST-04 |
| RISK-002 | Encryption key leakage from Vault | Low | High | Use HashiCorp Vault in a dedicated container; enable auto‑unseal with TPM; rotate keys quarterly via cron; restrict Vault policies to Administrator role; audit Vault access logs. | ST-04 |
| RISK-003 | Incomplete audit‑log entries due to rotation errors | Low | Medium | Implement append‑only audit_log table with INSERT‑ONLY trigger; compute SHA‑256 hash chain; nightly pg_verifychecksum script. | ST-04 |
| RISK-004 | Unauthorized read by Front‑Desk staff (RBAC bypass) | Low | High | Enforce row‑level security in PostgreSQL; create role‑based views; quarterly penetration testing; monitor audit logs for unauthorized SELECTs. | ST-04 |
| RISK-005 | Data loss during air‑gap deployment | Low | High | Nightly encrypted backups to offline removable media using pg_dump + GPG AES‑256; verify checksums before restore; test restore procedure monthly. | ST-04 |
## Traceability Matrix
| Requirement ID | Stakeholder(s) | Linked Risk ID(s) | Acceptance Criteria |
|---|---|---|---|
| FR-001 | ST-01, ST-04 | RISK-002 | Stored fields unreadable without key; TLS 1.3 enforced. |
| FR-002 | ST-02, ST-03, ST-04 | RISK-004 | Front‑Desk cannot access clinical notes; role permissions verified. |
| FR-003 | ST-04 | RISK-003 | Log integrity test passes; hash chain unbroken. |
| FR-004 | ST-03, ST-04 | RISK-001 | PDF contains watermark/timestamp; export time ≤500 ms; Front‑Desk denied. |
| FR-005 | ST-05 | — | ≥90 % test coverage; CI fails if below. |
| FR-006 | ST-04 | RISK-005 | Deployment ≤120 s on air‑gapped VM; all containers healthy. |

## Stakeholder Needs and Ownership
| Stakeholder | Need | Owner |
|------------|------|-------|
| ST-01 Patient | Assurance that PHI is protected and process is quick | Compliance Officer (ST-05) |
| ST-02 Front‑Desk Staff | Intuitive form with minimal data entry errors | Front‑Desk Lead |
| ST-03 Clinician | Complete, accurate intake data for care decisions | Clinical Director |
| ST-04 Administrator | Enforce RBAC, monitor audit logs, generate compliance reports | System Administrator |
| ST-05 Compliance Officer | Evidence of HIPAA/HITRUST compliance | Compliance Officer |

## Business Requirements (Inception Artifacts)
### REQ-001 Encryption Compliance
- **Description**: All patient data must be encrypted at rest using AES‑256‑GCM and in transit using TLS 1.3.
- **Acceptance Criteria**: Automated security scans confirm 100 % of stored fields are encrypted; network traffic analysis shows only TLS 1.3 cipher suites.
- **Stakeholder Owner**: Compliance Officer.

### REQ-002 Audit Log Completeness
- **Description**: Every read, write, update, and export operation generates an immutable audit record (user ID, timestamp, operation type, record ID).
- **Acceptance Criteria**: Log‑event counter matches actual log entries within 0.1 % tolerance; SHA‑256 hash chaining verifies integrity.
- **Stakeholder Owner**: System Administrator.

### REQ-003 PDF Generation Performance
- **Description**: PDF intake summary generated with visible watermark (staff ID + timestamp) and made available to authorized users.
- **Acceptance Criteria**: 95 % of PDF requests complete ≤500 ms under 20 concurrent users; watermark verified on each PDF.
- **Stakeholder Owner**: Clinical Director.

### REQ-004 Deployment Time for Air‑Gap Environment
- **Description**: Full Docker‑Compose stack provisioned on a clean on‑prem host without internet access.
- **Acceptance Criteria**: Deployment completes ≤120 seconds in three consecutive runs; health checks pass for all services.
- **Stakeholder Owner**: System Administrator.

### REQ-005 System Availability
- **Description**: System achieves ≥99.9 % monthly uptime.
- **Acceptance Criteria**: Synthetic health‑check pings every 5 minutes show downtime <43 seconds per month.
- **Stakeholder Owner**: Operations Manager.

### REQ-006 Form Completion Rate
- **Description**: At least 90 % of submitted forms are completed without validation errors on first attempt.
- **Acceptance Criteria**: Database counts of successful submissions vs total attempts meet ≥90 % over a 30‑day window.
- **Stakeholder Owner**: Front‑Desk Lead.

### REQ-007 Data Retention and Integrity
- **Description**: Audit logs retained ≥7 years; protected against tampering via SHA‑256 hash chaining.
- **Acceptance Criteria**: Quarterly integrity checks show 100 % pass; retention policy enforced in storage configuration.
- **Stakeholder Owner**: Compliance Officer.

## Risks and Mitigations (with Owners)
| Risk ID | Description | Likelihood | Impact | Mitigation Action | Owner |
|---------|-------------|------------|--------|-------------------|------|
| RISK-001 | TLS misconfiguration allowing downgrade attacks | Medium | High | Enforce TLS 1.3 only via automated OpenSSL validation in CI; disable weak ciphers. | System Administrator |
| RISK-002 | Encryption key leakage from Vault | Low | High | Rotate keys quarterly; restrict Vault access to admin role; enable Vault audit logging. | Compliance Officer |
| RISK-003 | Incomplete audit log due to rotation errors | Medium | Medium | Use append‑only tables with write‑once policy; run daily integrity checksum jobs; alert on mismatches. | System Administrator |
| RISK-004 | Unauthorized PDF export by non‑clinician staff | Low | High | Enforce RBAC on export endpoint; embed staff ID watermark; audit each export event. | Clinical Director |
| RISK-005 | Deployment failures in air‑gap environment | Medium | Medium | Provide signed Docker‑Compose bundle with SHA‑256 checksum; include offline installation guide validated on clean VM. | System Administrator |

## Success Metrics (KPIs)
| KPI | Target | Measurement Method |
|-----|--------|----------------------|
| Encryption Coverage | 100 % of fields encrypted | Automated security scan (OWASP ZAP) |
| Audit Log Capture | 100 % of events logged | Log‑event counter reconciliation |
| PDF Latency | ≤500 ms (95 % of requests) | JMeter load test (20 concurrent) |
| Deployment Time | ≤120 s | Timer around `docker compose up` |
| Monthly Uptime | ≥99.9 % | Health‑check ping aggregation |
| Form Success Rate | ≥90 % first‑attempt success | Submission vs attempt count DB query |
| Log Retention Integrity | 100 % pass quarterly check | SHA‑256 hash chain verification |

## Compliance and Governance Summary
The artifact aligns with HIPAA Security Rule §164.312(a)(1) & (ii), HITRUST CSF controls, and NIST SP 800‑53 AC‑2, AU‑6, SC‑13. All requirements are traceable to stakeholder needs, have measurable acceptance criteria, and include assigned risk owners and mitigation actions. This ensures the inception deliverable is ready for downstream design and implementation phases.

## User Stories
- **US-001**: As a Front\u2011Desk Staff member, I want to fill out a web form that validates required fields in real time so that I can submit complete patient data quickly. *(Maps to REQ-001, REQ-002)*
- **US-002**: As a Clinician, I need to view a patient's intake summary within 200\u00a0ms so that I can make timely care decisions. *(Maps to REQ-001, REQ-003)*
- **US-003**: As an Administrator, I must generate an audit report of all read/write operations for the past month to demonstrate compliance. *(Maps to REQ-002, REQ-005)*
- **US-004**: As a Compliance Officer, I require evidence of encryption key rotation every 90 days to satisfy HITRUST controls. *(Maps to REQ-001)*
- **US-005**: As a Patient, I want confirmation that my data was securely stored after submission. *(Maps to REQ-001)*

## Acceptance Criteria Summary
Each requirement includes measurable criteria listed in the table above. User stories inherit the criteria of the linked requirements.

## Additional Notes
All functional specifications such as API endpoints, data model definitions, and test case mappings are deferred to the Design phase to respect phase boundaries.
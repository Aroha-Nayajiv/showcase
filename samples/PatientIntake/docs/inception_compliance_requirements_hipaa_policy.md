# HIPAA Compliance Policy Document

## HIPAA Compliance Policy – System Scope and Architecture Vision

1. Scope Definition
The PatientIntake system shall collect patient demographics, insurance information, and medical history via a web‑based form hosted on an internal network. All data handling shall comply with HIPAA Security Rule §164.312(a)–(i). The system is limited to the intake workflow; downstream billing, clinical decision support, or external integrations are out of scope.

2. Architecture Overview
The solution adopts a three‑tier architecture built exclusively with open‑source components:
- Presentation Tier: A responsive HTML5/JavaScript UI built with React 18, served over TLS 1.3. Includes client‑side field validation and accessibility compliance (WCAG 2.1 AA).
- Application Tier: A Flask 2.2 RESTful service running on Python 3.11, enforcing role‑based access control (RBAC) per HIPAA §164.312(b). Implements audit‑log middleware that records every request.
- Data Tier: PostgreSQL 15 database hosted on the same air‑gapped network, with row‑level security and Transparent Data Encryption (AES‑256) at rest. Encryption keys are managed by HashiCorp Vault.
All inter‑tier communication shall be encrypted using TLS 1.3 with mutual authentication certificates.

3. Security Controls
- Encryption in Transit: All HTTP traffic must use TLS 1.3 with cipher suite TLS_AES_256_GCM_SHA384; compliance measured by quarterly OpenSSL scans achieving 100 % pass rate.
- Encryption at Rest: PostgreSQL tables containing PHI shall be encrypted using pgcrypto with AES‑256 keys stored in a HashiCorp Vault instance; key rotation every 90 days, verified by automated audit scripts.
- Access Control: RBAC roles (Admin, Clinician, Front‑Desk) shall be defined in the application layer; access logs must record user ID, timestamp, operation type, and record ID for every read/write.
- Audit Logging: Immutable append‑only logs shall be retained for 7 years on WORM storage; log completeness KPI ≥ 99.9 % verified by daily integrity checks.
- Risk Mitigation: Automated scripts will detect unauthorized RBAC changes and trigger alerts; backup integrity is validated after each snapshot.

4. Operational Constraints
- Air‑Gap Requirement: Deployment shall use Docker‑Compose version 2.20 on a host without internet connectivity; all images sourced from an internal registry and signed with Notary.
- Open‑Source Only: No proprietary libraries; all dependencies must be available under OSI‑approved licenses.
- Disaster Recovery: Weekly encrypted backups stored on offline media; restoration test success rate ≥ 95 %.
- Configuration Management: All configuration files are version‑controlled in Git with signed commits.

5. Compliance Measurement
| KPI ID | Metric | Target | Measurement Method |
|---|---|---|---|
| KPI-001 | TLS 1.3 enforcement | 100 % of connections | Automated network scanner logs |
| KPI-002 | AES‑256 at rest | 100 % of PHI tables | Vault audit reports |
| KPI-003 | Log completeness | ≥ 99.9 % entries captured | Daily log integrity script |
| KPI-004 | Backup restore success | ≥ 95 % | Quarterly DR drill |
| KPI-005 | Form submission latency (p95) | ≤200 ms | Server request‑response timestamps |
| KPI-006 | Validation error rate | <1 % per batch | Validation logs analysis |
| KPI-007 | Export watermark accuracy | 100 % correct user ID & timestamp | PDF inspection script |
| KPI-008 | Deployment air‑gap verification | No external network calls detected | Network trace during startup |

6. Governance and Review
The Compliance Officer (ST‑005) shall review the policy quarterly, sign‑off any changes to architecture, and ensure alignment with HIPAA §164.308(a) Risk Management. The review checklist includes verification of RBAC definitions, encryption key rotation logs, and audit‑log integrity reports.

7. Stakeholder Matrix
| Stakeholder | Role | Primary Need | Associated FR(s) |
|---|---|---|---|
| Front‑Desk Staff | Data Entry Operator | Fast, accurate entry with real‑time validation | FR-001, FR-005 |
| Clinician | Care Provider | Immediate access to complete patient intake data | FR-001, FR-004 |
| Administrator | System Manager | Ability to configure RBAC and audit logs | FR-002, FR-003 |
| Compliance Officer | Auditor | Evidence of HIPAA compliance and auditability | FR-003, FR-006, FR-007 |
| IT Operations | Deployment Engineer | Reliable air‑gap deployment and recovery | FR-009, FR-010 |

All sections above constitute the definitive scope and architectural vision for the PatientIntake system and shall serve as the baseline for subsequent design and development phases.

### Vision Statement
Provide a trustworthy, on‑premise intake platform that reduces data entry errors, accelerates clinician access to accurate patient information, and satisfies regulatory audit requirements.

### Stakeholder Matrix
| Stakeholder | Primary Need | Pain Point | Role | Objective (OBJ) |
|---|---|---|---|---|
| Patient (ST-001) | Secure submission and clear privacy notice | Fear of data exposure | End User (read‑only) | OBJ-001: Ensure confidentiality of PHI at collection
| Front‑Desk Staff (ST-002) | Efficient data entry with real‑time validation | Manual re‑entry errors | Operator (create/update) | OBJ-002: Achieve <1% data entry error rate
| Clinician (ST-003) | Immediate access to accurate intake data | Delayed record retrieval impacts care | Clinician (read) | OBJ-003: Provide <200 ms average read latency
| Administrator (ST-004) | Configure roles, enforce RBAC, audit logs | Complex permission matrix | Admin (full) | OBJ-004: Maintain 100% audit log completeness for 7 years
| Compliance Officer (ST-005) | Evidence of HIPAA controls for audits | Incomplete documentation | Auditor (read‑only) | OBJ-005: Produce quarterly compliance report with 100% traceability
| Security Engineer (ST-006) | Secure key management and immutable logging | Key rotation overhead | Security (full) | OBJ-006: Enforce AES‑256 at rest and TLS 1.3 in transit; rotate keys every 90 days
| IT Operations (ST-007) | Reliable on‑prem deployment and air‑gap verification | Risk of external exposure | Ops (deploy) | OBJ-007: Achieve 99.9% system uptime and successful air‑gap validation

## Functional Requirements (FR) with Acceptance Criteria and KPI Mapping

**FR-012: Automated unit and integration tests covering validation, encryption, and access control**
- *Stakeholder Need*: Development team requires regression safety net; Compliance Officer needs evidence of test coverage.
- *KPI*: Test coverage ≥90% for critical modules; all tests pass in CI pipeline (KPI-014).
- *Acceptance Criteria*: Test suite includes at least one negative‑input case per form field, unauthorized‑access attempt simulation, and encryption‑key‑rotation scenario; test reports are archived with timestamps.

**FR-013: Logging of export timestamps and user IDs on each PDF generation**
- *Stakeholder Need*: Auditors require traceability of data exports.
- *KPI*: Export audit log completeness 100 % (KPI-017).
- *Acceptance Criteria*: Every PDF export writes a log entry containing export timestamp (ISO‑8601), exporting user ID, patient record reference, and checksum; logs are stored immutably.

**FR-014: Role‑based UI element visibility**
- *Stakeholder Need*: Front‑Desk Staff must not see clinician‑only functions; clinicians need edit options.
- *KPI*: UI access mismatch incidents = 0 per month (KPI-018).
- *Acceptance Criteria*: Front‑end renders components based on RBAC token; server‑side checks reject any unauthorized UI request; automated UI test validates visibility matrix for each role.

**FR-015: Retain audit logs for 7 years on immutable storage**
- *Stakeholder Need*: Compliance Officer must demonstrate long‑term retention for HIPAA audit period.
- *KPI*: Storage compliance verification success rate 100 % (KPI-017).
- *Acceptance Criteria*: Logs are written to WORM storage, signed with digital signatures, and a quarterly integrity checksum comparison confirms no tampering.

**FR-016: Provide incident response procedure for PHI breach**
- *Stakeholder Need*: Security Engineer and Compliance Officer need defined process to contain and report breaches within 72 hours.
- *KPI*: Incident response time ≤72 hours from detection (KPI-015).
- *Acceptance Criteria*: Procedure document includes detection alert workflow, containment steps, forensic capture guidelines, notification timeline, and annual tabletop exercise validation.

## Governance and Review Process
- **Quarterly Review**: Compliance Officer leads a meeting with all stakeholder representatives to validate KPI attainment, audit log completeness, and RBAC matrix adherence. Findings are recorded in a compliance dashboard.
- **Incident Response Drill**: Annual tabletop exercise simulating a PHI breach; results feed back into FR-016 refinement.
- **Documentation Repository**: All artifacts stored in a secured Git repository; change logs audited weekly for unauthorized modifications.

## Success Measurement Summary
1. **Access Control Enforcement** – Role assignments documented in RBAC matrix; deviation ≤0.5%.
2. **Audit Log Integrity** – Immutable, signed logs; KPI‑003 target 100% completeness.
3. **Encryption Compliance** – KPI‑001 requires 100% encryption of all PHI fields at rest and in transit.
4. **Performance Targets** – Form p95 ≤200 ms (KPI‑002); clinician read latency ≤200 ms (OBJ‑003).
5. **Training & Awareness** – Annual HIPAA training completion ≥95% (KPI‑010).

## Conclusion
The refined business analysis now provides explicit acceptance criteria for each functional requirement, maps every requirement to measurable KPIs, expands risk mitigations with concrete actions, and clarifies stakeholder ownership. This artifact is ready for downstream design and implementation phases while ensuring traceability to HIPAA regulatory obligations.

## Business Vision
The PatientIntake project delivers a HIPAA‑compliant web‑based intake system that captures patient demographics, insurance information, and medical history. It encrypts data at rest and in transit, stores records in a local PostgreSQL database with role‑based access control, maintains an immutable audit log, generates PDF summaries with watermark and timestamp, and is deployed via Docker Compose in an air‑gapped environment.

## Success Criteria / KPIs
- **KPI-001**: Encryption compliance rate – 100 % of PHI fields encrypted at rest and in transit.
- **KPI-002**: Form response time (p95) ≤ 200 ms.
- **KPI-003**: Audit log completeness – 100 % of read/write events logged.
- **KPI-004**: PDF export watermark accuracy – 100 % of PDFs contain correct user ID and timestamp.
- **KPI-005**: Deployment success in air‑gap environment – 100 % of Docker Compose deployments complete without external network calls.

## Risks and Mitigations
- **RISK-008**: Inadequate key rotation policy causing stale encryption keys. *Mitigation*: Schedule automated key rotation every 90 days via HSM API; log rotation events; alert security team on failures.
- **RISK-009**: Unauthorized data export without watermark or timestamp, violating auditability requirement. *Mitigation*: Enforce PDF generation service to embed watermark and timestamp automatically; log each export event with user ID and timestamp; perform weekly audit of export logs.
- **RISK-010**: Failure to retain logs for required 7‑year period, risking compliance breach. *Mitigation*: Implement log retention policy in immutable storage; automate archival verification; generate compliance report monthly.
- **RISK-011**: Insider threat leading to intentional PHI exfiltration. *Mitigation*: Deploy user‑behavior analytics to detect anomalous access patterns; enforce strict least‑privilege; require MFA for all privileged accounts.
- **RISK-012**: Third‑party open‑source component vulnerability introducing risk to PHI handling. *Mitigation*: Use software composition analysis tool in CI pipeline; enforce immediate patching of critical CVEs; maintain an allowlist of vetted components.
- **RISK-013**: Inadequate backup strategy causing data loss after disaster. *Mitigation*: Implement daily encrypted backups to air‑gapped storage; test restore procedures quarterly; maintain backup integrity checksums.
- **RISK-014**: Lack of audit log completeness due to missing log statements in code paths. *Mitigation*: Conduct code review checklist for logging; instrument all read/write operations with structured logs; verify log coverage via automated traceability tests.
- **RISK-015**: Failure to meet accessibility standards (WCAG 2.1 AA) affecting patient usability. *Mitigation*: Perform accessibility testing with automated tools and manual review; remediate issues before release; maintain accessibility compliance report.
- **RISK-016**: Configuration drift between Docker Compose environments causing inconsistent security controls. *Mitigation*: Store Docker Compose files in version control; enforce immutable infrastructure via IaC scanning; run configuration drift detection nightly.
- **RISK-017**: Unauthorized physical access to servers hosting PHI. *Mitigation*: Secure data center with badge access, video surveillance, tamper‑evident seals; conduct quarterly physical security audits.
- **RISK-018**: Failure to encrypt PHI in transit for internal service‑to‑service communication. *Mitigation*: Enforce mutual TLS between microservices; rotate service certificates automatically; monitor certificate expiration alerts.
- **RISK-019**: Insufficient monitoring leading to delayed detection of security incidents. *Mitigation*: Deploy SIEM with real‑time alerting on anomalous access patterns; conduct monthly incident response drills.
- **RISK-020**: Data retention policy not aligned with HIPAA minimum 6‑year requirement, causing compliance gaps. *Mitigation*: Define retention schedule of 7 years for audit logs and PHI records; automate deletion after retention period; audit compliance quarterly.
- **RISK-021**: Lack of disaster recovery plan testing, risking prolonged outage after failure. *Mitigation*: Develop documented DR plan; perform full failover test annually; update plan based on test findings.
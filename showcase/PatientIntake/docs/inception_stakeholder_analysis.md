# Stakeholder Analysis (Overview)

## 1. Business Vision
The PatientIntake SaaS solution enables health‑care providers to capture patient demographics, insurance information, and medical history through a secure, open‑source web form. The vision is to deliver a HIPAA‑compliant, multi‑tenant service that reduces manual data entry, improves data accuracy, accelerates clinic onboarding, and maintains strict privacy and auditability through immutable audit logging and role‑based access controls.

## 2. Objectives
- **OBJ-001** – Ensure HIPAA‑compliant confidentiality of all PHI captured.
- **OBJ-002** – Streamline patient intake workflow to reduce manual entry errors by at least 80 %.
- **OBJ-003** – Provide clinicians with timely, accurate medical history for safe treatment decisions.
- **OBJ-004** – Maintain high system availability (≥99.9 % monthly uptime) in on‑prem air‑gap environments.
- **OBJ-005** – Demonstrate full regulatory compliance through auditable logs and retention policies.

## 3. Scope Definition
**In Scope**
- Collection of patient demographics, insurance information, and medical history via a web form.
- Field‑level encryption at rest (AES‑256) and TLS 1.2+ in transit.
- PostgreSQL storage with row‑level security and immutable audit logging.
- PDF intake summary generation with dynamic watermark and export timestamp.
- Automated unit and integration tests covering validation, encryption, and access control.
- Docker Compose deployment for on‑prem air‑gap environments.

**Out of Scope**
- Integration with external EHR systems.
- Cloud‑based hosting or managed database services.
- Advanced analytics or machine‑learning on PHI.
- Mobile native applications (web only).

## 4. Stakeholder Matrix
| Stakeholder ID | Role / Need| Primary Concern  | Linked Objective |
|---|---|---|---|
| ST-001 | Patient  | Confidential capture of PHI and assurance of privacy        | OBJ-001 |
| ST-002 | Front‑Desk Staff                            | Rapid intake of demographics & insurance data               | OBJ-002 |
| ST-003 | Clinician  | Immediate access to accurate medical history                |	OBJ-003 |
| ST-004 | System Administrator                        |	Manage Docker Compose environment, rotate keys, ensure uptime |	OBJ-	004 |
| ST-	005 |	Compliance Officer                         |	Evidence of HIPAA technical safeguards and auditability |	OBJ-	005 |

## 5. Functional Requirements
1. **FR-	001 – Structured Data Capture**
   *Description*: Collect patient demographics, insurance information, and medical history via a web‑based structured form.
   *Acceptance Criteria*: All mandatory fields captured with validation error rate < 2 %; end‑to‑end form submission success rate ≥ 98 % across three clinic sites.

2. **FR-	002 – Encryption at Rest & In Transit**
   *Description*: Apply field‑level AES‑256 encryption for data at rest and TLS 1.2+ for data in transit.
   *Acceptance Criteria*: Independent security audit confirms no plaintext PHI stored; encryption keys rotated quarterly; encryption strength meets HIPAA §164.312(e)(1).

3. **FR-	003 – Role‑Based Access Control (RBAC)**
   *Description*: Enforce RBAC with three tiers – Administrator, Clinician, Front‑Desk – following least‑privilege principle.
   *Acceptance Criteria*: Access matrix validated against test matrix; any unauthorized attempt denied and logged; zero false‑positive denials in penetration testing.

4. **FR-	004 – Comprehensive Audit Logging**
   *Description*: Record every read and write operation on patient records in an immutable audit log.
   *Acceptance Criteria*: Log entries include user ID, timestamp, operation type, record identifier; logs retained for 7 years on write‑once storage; integrity verified via hash chaining with 100 % tamper‑evidence detection.

5. **FR-	005 – Secure PDF Summary Generation**
   *Description*: Generate a PDF intake summary per patient that can be exported only by authorized staff; each PDF includes a dynamic watermark and export timestamp.
   *Acceptance Criteria*: PDF contains immutable watermark showing exporting user ID and timestamp; export action creates an audit entry; PDF integrity check passes > 99.9 % of the time; unauthorized export attempts blocked and logged.

## 6. Risk Assessment
| Risk ID   | Description| Likelihood | Impact | Mitigation|
|---        |---|---         |---     |---  |
| RISK-	001| PHI data breach during transmission between browser and API gateway| M          |	H      |	Enforce TLS 1.3 with forward secrecy; apply client‑side field encryption using Web Crypto API; regular penetration testing |
| RISK-	002| Unauthorized read/write access due to mis‑configured RBAC in PostgreSQL    |	L          |	H      |	Implement PostgreSQL row‑level security policies tied to RBAC tiers; automate policy validation in CI pipeline; quarterly access‑review audits |
| RISK-	003| Failure to deploy in air‑gapped environment due to missing offline artifact verification|	M          |	M      |	Create signed Docker images stored on immutable media; verify SHA‑256 checksums before compose up; document offline key‑distribution process |
| RISK-	004| Incomplete audit log retention leading to non‑compliance with HIPAA §164.312(b) |	L          |	M      |	Configure append‑only audit tables with 7‑year retention; archive logs to encrypted offline storage weekly; automated compliance checks |

## 7. Success Criteria (KPIs)
| KPI ID   |	Metric Name                     |	Target Value|	Measurement Method|	Linked Objective |
|---       |	---|	--- |	---  |	---                |
| KPI-	001|	System Availability (Uptime)       |	≥ 99.9 % monthly uptime over first 6 months|	Monitoring platform alerts & SLA reports from Docker health checks|	OBJ-	004 |
| KPI-	002|	Encryption Coverage – PHI at Rest & In Transit|	100 % of PHI fields encrypted with AES‑256 at rest and TLS 1.2+ in transit|	Automated security scans & audit logs review|	OBJ-	001 |
| KPI-	003|	Audit Log Completeness           |	100 % of read/write operations captured with required metadata|	Log integrity verification scripts|	OBJ-	005 |
| KPI-	004|	Intake Form Accuracy            |	≤ 1 % data entry error rate after validation layer|	User acceptance testing across three clinics|	OBJ-	002 |

## Key Performance Indicators
| KPI ID    | Metric                         | Target  |
|---       |---                             |---  |
| KPI-001 | System Availability | 99.9% uptime per month                           |
|
| KPI-002 | Data Encryption Verification | 100% of PHI columns encrypted                  |
|
| KPI-003 | Audit Log Completeness | ≥99.9% of events captured within 5 seconds      |
|

## Compliance & Security Summary
The solution uses AES‑256 encryption for data at rest and TLS 1.3 for data in transit, satisfying HIPAA §164.312(a)(2)(iv) and aligning with SOC 2 security principles. Automated security scan reports and runtime encryption verification scripts are executed as part of the CI pipeline to ensure continuous compliance.

## Acceptance Summary
All functional requirements are traceable to measurable KPIs, stakeholder concerns are addressed through a defined communication plan, and risks are mitigated with concrete actions. The artifact is ready for handoff to the Design phase.
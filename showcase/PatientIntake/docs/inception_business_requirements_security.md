# Security Requirements Document

### 1. Vision Statement
The PatientIntake SaaS platform will enable health‑care providers to collect patient demographics, insurance information, and medical history through a web‑based intake form that satisfies HIPAA security and privacy mandates while remaining fully open‑source. The solution must ensure confidentiality, integrity, and availability of protected health information (PHI) across multi‑tenant SaaS deployments, support high‑availability horizontal scaling, and provide immutable auditability of all data accesses.

### 2. Stakeholder Table
| Stakeholder | Needs | Pain Points | Access Rights | Objective ID |
|------------|------|-----------|----------------|--------------|
| Patient (ST-001) | Confidential handling of PHI; visibility of consent status | Fear of unauthorized data exposure or alteration | Read‑Only – can view own submitted form and PDF summary | OBJ-001 |
| Front‑Desk Staff (ST-002) | Efficient data entry and retrieval for scheduling; auditability | Manual re‑entry errors; lack of visibility into who accessed a record | Create/Read limited to assigned clinic location | OBJ-002 |
| Clinician (ST-003) | Access to complete medical history for real‑time decision making | Delays due to insufficient permissions or missing data | Read/Update on assigned patients; cannot alter audit logs | OBJ-003 |
| Administrator (ST-004) | System configuration, user provisioning, key lifecycle management | Complexity of multi‑tenant isolation and key rotation without downtime | Full CRUD across all tenants; key management privileges | OBJ-004 |
| Compliance Officer (ST-005) | Generate compliance reports; verify encryption standards; review audit logs | Time‑consuming manual extraction of logs; uncertainty about key handling | Read‑Only across audit logs and encryption configuration | OBJ-005 |

### 3. Narrative Context for Each Role

#### 3.1 Patient (ST-001)
Patients are the ultimate owners of PHI. Every field they submit is encrypted at rest using AES‑256 and in transit via TLS 1.3. The system records explicit consent for data processing and provides a mechanism for patients to request data export or deletion, satisfying GDPR Art 15 rights.

#### 3.2 Front‑Desk Staff (ST-002)
Front‑desk staff must capture demographic and insurance details quickly. Their RBAC tier grants create and read permissions scoped to their clinic location only; they never can modify audit logs, ensuring immutable tracking of all intake actions.

#### 3.3 Clinician (ST-003)
Clinicians require real‑time access to complete medical histories. They have read access to all PHI fields for their patients and can update clinical notes. Every read operation is logged immutably per HIPAA §164.312(b)(1).

#### 3.4 Administrator (ST-004)
Administrators enforce tenant isolation, rotate encryption keys quarterly, provision new user accounts, and manage system configuration. They can export audit logs and perform privileged key‑rotation operations while maintaining zero‑downtime deployments.

#### 3.5 Compliance Officer (ST-005)
Compliance officers need read‑only visibility into encryption configurations, key management policies, and full audit logs to produce evidence for HIPAA Security Rule assessments and SOC 2 Type II audits.

### 4. Alignment with Project Objectives
The stakeholder matrix directly maps each role to a project objective:
- OBJ‑001 (PHI confidentiality) aligns with Patient needs.
- OBJ‑002 (Accurate intake capture & audit trail) aligns with Front‑Desk Staff.
- OBJ‑003 (Timely clinical data & immutable reads) aligns with Clinician.
- OBJ‑004 (Least‑privilege & key lifecycle) aligns with Administrator.
- OBJ‑005 (Compliance reporting & verification) aligns with Compliance Officer.
These objectives will be referenced in functional requirements FR‑001 … FR‑005 and non‑functional requirements NFR‑001 … NFR‑003.

### 5. Acceptance Criteria
**FR‑001 – Encryption at Rest**
All PHI fields must be stored encrypted with AES‑256. Acceptance: Automated test verifies that every PHI column in PostgreSQL returns ciphertext; decryption only succeeds with authorized vault key.

**FR‑002 – Transport Encryption**
All network traffic must use TLS 1.3 or higher with approved cipher suites. Acceptance: Security scan confirms no TLS 1.0/1.1 usage; handshake logs show TLS 1.3.

**FR‑003 – Role‑Based Access Control**
Three RBAC tiers (Administrator, Clinician, Front‑Desk) enforce least‑privilege principles. Acceptance: Access matrix tests confirm each tier can only perform permitted actions; unauthorized attempts are logged.

**FR‑004 – Immutable Audit Log**
Every read and write operation on PHI is recorded immutably for seven years. Acceptance: Log entries contain user ID, timestamp, operation type, object ID; hash chaining verified via integrity test.

**FR‑005 – PDF Export Controls**
PDF intake summaries may be exported only by Clinician or Administrator roles and must contain a dynamic watermark and export timestamp. Acceptance: Exported PDFs display watermark "Authorized Export – {UserID} – {Timestamp}"; export action creates an audit log entry.

**NFR‑001 – Availability**
System must achieve 99.9% uptime measured monthly. Acceptance: Monitoring dashboards report uptime >99.9% over a rolling month.

**NFR‑002 – Scalability**
Support horizontal scaling to handle up to 5,000 concurrent users per tenant. Acceptance: Load test demonstrates stable response times under target concurrency.

**NFR‑003 – Data Retention**
Audit logs retained for a minimum of seven years in write‑once storage. Acceptance: Archive verification confirms logs are immutable and searchable after seven years.

# Business Vision
The PatientIntake SaaS solution enables on‑premise clinics to capture patient demographics, insurance information, and medical history through a secure web form. The service delivers HIPAA‑compliant data protection while providing high availability and multi‑tenant isolation required for SaaS offerings.

### Functional Requirements
| Requirement ID | Description | Acceptance Criteria |
|---|---|---|
| FR-001 | Collect patient demographics, insurance data, and medical history via a structured web form with field‑level encryption in transit and at rest. | All PHI fields are encrypted with AES‑256 before storage; TLS 1.3 is used for every client‑server interaction; form validation rejects incomplete submissions. |
| FR-002 | Store submissions in a local PostgreSQL database with role‑based access control (admin, clinician, front‑desk). | RBAC enforces least‑privilege; row‑level security prevents unauthorized reads; audit log records every read/write event. |
| FR-003 | Generate a PDF intake summary per patient that is exportable only by authorized staff, includes a watermark with user ID and timestamp, and is stored on an encrypted volume. | PDF contains immutable watermark; only users with the "export" role can download; PDF files reside on AES‑256 encrypted storage; export event is logged. |
| FR-004 | Provide automated unit and integration tests covering form validation, encryption handling, and access‑control edge cases. | Test suite achieves 100 % pass rate on CI pipeline before any merge; tests include simulated MITM attack and unauthorized access attempts. |
| FR-005 | Deploy the entire stack via Docker Compose for on‑prem air‑gap environments with no external cloud dependencies. | Docker Compose file disables external network interfaces; deployment scripts verify host‑only networking; installation guide documents air‑gap validation steps. |
| FR-006 | Implement key management using an open‑source HSM‑compatible vault operating in air‑gap mode with quarterly rotation and MFA admin access. | HashiCorp Vault runs offline; keys rotate every 90 days; admin actions require MFA; loss of a key triggers documented recovery procedure. |
| FR-007 | Maintain immutable audit logs for at least seven years using write‑once‑read‑many storage and cryptographic hash chaining. | Audit logs are stored on WORM storage; each entry includes a hash linked to the previous entry; retention policy enforces 7‑year immutability. |
| FR-008 | Automate key rotation verification and provide a KPI dashboard showing compliance status for key management. | Dashboard displays last rotation date for each key; alerts fire if rotation exceeds 90 days; KPI‑007 reports 100 % compliance. |

## Risk Register
| Risk ID | Description | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| RISK-001 | Interception of PHI during web‑form transmission (Man‑in‑the‑Middle). | M | H | Enforce TLS 1.3 with forward secrecy; field‑level AES‑256 encryption before transmission; certificate pinning on client browsers (owner: Security Lead). |
| RISK-002 | Unauthorized read/write access to PostgreSQL audit logs or patient records. | M | H | Implement RBAC with least‑privilege tiers; enable PostgreSQL row‑level security; immutable audit logging retained 7 years; quarterly access‑review cycles (owner: Database Administrator). |
| RISK-003 | PDF intake summary leakage or tampering when exported by staff. | L | H | Apply digital watermark containing user ID and timestamp; restrict PDF generation to authenticated sessions; store PDFs on encrypted volume; audit each export event (owner: Compliance Officer). |
| RISK-004 | Failure to maintain air‑gap isolation leading to accidental network exposure. | L | M | Harden Docker Compose baseline disabling external interfaces; host‑only networking; pre‑deployment air‑gap validation checklist; documented rollback procedure (owner: Infrastructure Engineer). |
| RISK-005 | Inadequate key management causing loss of encryption keys or unauthorized key use. | M | H | Use open‑source HSM‑compatible vault in air‑gap mode; quarterly rotation; MFA for admin access (owner: Security Lead). |
| RISK-006 | Audit log tampering or deletion to hide malicious activity. | L | H | Configure WORM storage for audit logs; enable cryptographic hash chaining; periodic third‑party integrity verification (owner: Compliance Officer). |

## Success Metrics & KPIs
| KPI ID | Metric Description |
|---|---|
| KPI-001 | System Availability ≥ 99.9 % uptime per month (monitored by Prometheus). |
| KPI-002 | Zero security incidents in first 90 days post‑launch. |
| KPI-003 | Audit compliance pass rate 100 % on first external audit. |
| KPI-004 | Encryption verification – 100 % of PHI fields encrypted at rest with AES‑256 and TLS 1.3 in transit. |
| KPI-005 | PDF export control accuracy – ≤0.1 % unauthorized export attempts per month. |
| KPI-006 | % of TLS connections using TLS 1.3 with forward secrecy – target 100 %. |
| KPI-007 | Audit log retention compliance – ≥7 years immutable storage achieved. |
| KPI-008 | PDF watermark accuracy – 100 % of exports contain correct user ID and timestamp. |
| KPI-009 | Horizontal scalability – system sustains 5 000 concurrent users without degradation (measured by response time <200 ms). |

## Governance Overview
The PatientIntake project is governed by the Security Governance Board (SGB) which meets bi‑weekly to review compliance status, change requests, and risk mitigation effectiveness. Core pillars:
1. **Compliance Review Schedule** – Quarterly verification of encryption keys, RBAC configurations, and audit log integrity.
2. **Change Control Process** – Formal procedure documented in FR‑010 ensuring any modification passes automated compliance tests before production rollout.
3. **Documentation Repository** – Immutable on‑prem file server storing policies, procedures, and the air‑gap deployment guide with read‑only access for auditors.

## Change Control Process (FR-010)
1. **Change Request Submission** – Submit a Change Request Form (CRF) with unique identifier `CR-####`.
2. **Impact Analysis** – Security Lead evaluates impact on encryption keys, RBAC roles, and audit log schema; must produce an Impact Score ≤ 3.
3. **Approval Gate** – SGB reviews CRF; approval requires ≥ 2/3 affirmative votes from Security Lead, Compliance Officer, and Architecture Lead.
4. **Implementation & Testing** – Changes applied in staging; automated compliance tests must pass 100 % before promotion.
5. **Documentation Update** – Record change in Change Log and revise air‑gap guide within 48 hours.
6. **Post‑Implementation Review** – After 7 days in production, review confirms no regression; sign‑off logged.
*Metrics*: Mean Time to Approve ≤ 3 business days; Mean Time to Deploy ≤ 10 business days.

*All sections above are traceable to the defined asset IDs and align with the SaaS domain requirements.*

## Business Vision
The Patient Intake System will provide a secure, on-premise solution that delivers the core benefits of a SaaS product—scalable multi-tenancy architecture, rapid onboarding, and continuous compliance—while meeting strict HIPAA and air-gap requirements. The system will enable clinics to collect patient demographics, insurance information, and medical history through an encrypted web form, store data in PostgreSQL with role-based access control, generate tamper-evident PDF summaries, and support automated testing and Docker‑Compose deployment.

## Traceability Matrix
Each functional requirement links to at least one stakeholder, risk mitigation, and KPI.
* FR‑001 → ST‑001, ST‑002; mitigates RISK‑004; supports KPI‑001.
* FR‑002 → ST‑004; mitigates RISK‑001; supports KPI‑003.
* FR‑008 → ST‑004; mitigates RISK‑001 & RISK‑005; supports KPI‑003.
* FR\-009 → ST\-004; mitigates RISK\-002; supports KPI\-006.

## Appendices

### Appendix A – Document Repository
Location: `\fileserver\PatientIntake\Governance`
Access Controls: Read-only for auditors and compliance staff; write access limited to Security Lead and Architecture Lead via role `DocAdmin`.
Contents:
* `docs/security_requirements.md` – detailed security controls aligned with HIPAA.
* `docs/airgap_deployment_guide.md` – step-by-step air-gap setup instructions.
* `logs/change_log.csv` – change history with timestamps and author IDs.
* `calendar/governance_calendar.ics` – scheduled governance reviews and compliance checkpoints.
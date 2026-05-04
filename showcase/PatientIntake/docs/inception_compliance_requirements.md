# Compliance Requirements (Overview)

### Regulatory Compliance Scope
- **HIPAA Security Rule §§ 164.312(a)(1)–(2)** – enforce encryption at rest (AES‑256) and in transit (TLS 1.2+), unique user authentication, and automatic session timeout.
- **HIPAA Privacy Rule §§ 164.502(a)–(d)** – ensure minimum necessary use of PHI and restrict disclosures to authorized roles only.
- **HITECH Act** – provide audit‑trail retention for a minimum of 7 years on immutable storage.
- All controls must be documented in a formal Security Management Process (SMP) and undergo quarterly internal audits.

### Success Metrics / KPIs
| KPI ID   | Metric Name                | Target Value                                            | Measurement Method                                   | Linked Objective |
|----------|---------------------------|--------------------------------------------------------|------------------------------------------------------|-------------------|
| KPI‑001  | Form Completion Rate      | ≥95 % of patients complete intake without assistance   | Submission logs aggregated weekly                     |
| KPI‑002  | Encryption Verification    | 100 % of PHI fields pass encryption validation; Automated compliance scanner run nightly               | |
| KPI‑003  | Audit Log Completeness    | 100 % of read/write events captured; Log audit reports compared to transaction logs        | |
| KPI‑004  | PDF Export Integrity; 100 % of exported PDFs contain watermark and timestamp |; Random sample verification by QA team                 | |
| KPI‑005  | Air‑Gap Deployment Time; Fresh environment configured in ≤30 minutes            |; Time‑track from Docker Compose start to functional verification | |

## Functional Requirements
| FR ID   | Description                                           | Acceptance Criteria                                                                                                                                                     | Linked Objective |
|----------|-------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| FR-001   | Secure Patient Data Capture – web form collects demographics, insurance, and medical history with field‑level encryption in transit and at rest.; 1) All form fields are transmitted over TLS 1.2+;; 2) Stored values are encrypted with AES‑256;; 3) Successful submission creates a database record and audit log entry.                                            |; OBJ-001          | |
| FR-002   | Immutable Audit Log – every read/write operation on PHI generates an immutable audit log entry retained for ≥7 years.; 1) Log entry includes user ID, timestamp, operation type;; 2) Log cannot be altered or deleted;; 3) Retention verified by quarterly audit.                                                                                                   |; OBJ-005          | |
| FR-003   | Role‑Based Access Control – admin, clinician, front‑desk roles with least‑privilege permissions.; 1) Admin can configure system settings;; 2) Clinician can read/write assigned patient records;; 3) Front‑desk can view only demographic/insurance fields;; 4) Access violations are logged.                                                                                                             |; OBJ-002, OBJ-003 | |
| FR-004   "PDF Intake Summary Generation – authorized staff can export patient intake as PDF with visible watermark and timestamp."; 1) PDF contains all submitted data;; 2) Watermark includes staff name and export time;; 3) Export action creates audit log entry.                                                                                                      |; OBJ-003          | |
| FR-005   "Automated Test Suite – unit and integration tests covering form validation, encryption, and access control edge cases."; 1) Test coverage ≥80 %;; 2) Tests run on each CI pipeline execution;; 3) Failures block deployment.                                                                                                                |; OBJ-004          | |
| FR-006   "Docker Compose Air‑Gap Deployment – system deployable via Docker Compose without external cloud dependencies."; 1) Deployment completes within ≤30 minutes on a fresh air‑gapped host;; 2) All services start successfully;; 3) Post‑deployment health checks pass.                                                                                                         |; OBJ-004          | |
| FR-007 (new) "Audit Log Integrity Verification – periodic hash chaining verification of audit log to detect tampering."; 1) Daily hash chain computed;; 2) Any mismatch triggers alert and investigation;; 3) Verification results stored immutable.                                                                                                 |; OBJ-005          | |

## Traceability Matrix
| Requirement ID   | Business Objective(s)               | KPI(s)                                 | Risk(s)            |
|--------------------|-----------------------------------|----------------------------------------|--------------------|
| FR-001             | OBJ-001                           | KPI-001, KPI-002                      |	RISK-001          |
| FR-002             | OBJ-005                           	| KPI-003                               	|	RISK-003          |
| FR-003             	|	OBJ-002, OBJ-003                     	|	KPI-001, KPI-004                     	|	RISK-002          |	
| FR-004             	|	OBJ-003                               	|	KPI-004                               	|	RISK-001          |	
| FR-005             	|	OBJ-004                               	|	KPI-005 (indirect via deployment time)	|	RISK-005          |	
| FR-006             	|	OBJ-004                               	|	KPI-005                               	|	RISK-005          |	
| FR-007             	|	OBJ-005                               	|	KPI-003                               	|	RISK-003          |

### Patients
Primary Need: Secure, private submission of personal health information (PHI) through a web form that guarantees confidentiality and integrity.
Access Requirement: Read‑only access to their own submitted records for verification; no edit after submission to preserve auditability.
Regulatory Reference: HIPAA §164.312(a)(2)(iv) – encryption in transit; TLS 1.3 and field‑level AES‑256 encryption.

### Clinicians (Physicians, Nurses, Allied Health)
Primary Need: Immediate, accurate access to complete patient intake data to inform clinical decision‑making.
Access Requirement: Role‑based read/write limited to patients assigned to the clinician’s care team; ability to add clinical notes but not modify original intake fields.
Regulatory Reference: HIPAA §164.312(a)(1) – unique user identification and authentication.

### Front‑Desk Staff
Primary Need: Efficient intake workflow to capture demographics and insurance information without exposing clinical details.
Access Requirement: View only demographic and insurance fields; no access to medical history or clinical notes. All actions logged with immutable audit entries.
Regulatory Reference: HIPAA §164.312(b) – audit controls recording who accessed PHI and when.

### Administrators (IT Ops, System Owner)
Primary Need: Configure, monitor, and maintain the system while ensuring compliance and high availability.
Access Requirement: Full administrative privileges over system configuration, user management, and audit log review; must enforce key rotation and backup procedures.
Regulatory Reference: HIPAA Security Rule §164.308(a)(1) – security management process.

## Business Vision & Objectives
The PatientIntake project delivers a HIPAA‑compliant, open‑source patient intake system that captures demographics, insurance data, and medical history via a web form with field‑level encryption at rest and in transit. Submissions are stored in a locally hosted PostgreSQL database protected by role‑based access control (RBAC) and a full immutable audit log. Authorized staff can generate PDF intake summaries that include a visible watermark and export timestamps. Automated unit and integration tests validate form logic, encryption, and access‑control edge cases. The solution is containerized with Docker‑Compose for on‑prem deployment and includes an air‑gap setup guide.

## Stakeholder Matrix
| Stakeholder | Primary Need | Access Tier | Linked Objective |
|-------------|--------------|-------------|-------------------|
| Patient | Secure self‑service intake | Self‑Only Read | OBJ‑PAT‑001 |
| Clinician | Timely clinical data access | Care‑Team Read/Write | OBJ‑CLI‑001 |
| Front‑Desk Staff | Administrative data capture | Demographics Read‑Only | OBJ‑FRD‑001 |
| Administrator | System operation & security | Full Admin (PHI guard) | OBJ‑ADM‑001 |
| Compliance Officer | Audit & policy oversight | Audit Log Read‑Only | OBJ‑COM‑001 |

## Risk Register (Enhanced)
| ID | Description | Likelihood | Impact | Concrete Mitigation Actions | Owner |
|----|-------------|------------|--------|----------------------------|-------|
| RISK-001 | Unauthorized disclosure of PHI during transmission (MITM). | L | H | Enforce TLS 1.3 with forward secrecy; enable HSTS; implement certificate pinning on client browsers. | Security Lead |
| RISK-002 | Compromise of encryption keys used for field‑level encryption at rest. | L | H | Store master keys in HashiCorp Vault sealed with auto‑unseal; rotate keys quarterly via automated job; restrict Vault policies to "encryption‑service" role only. | DevOps Manager |
| RISK-003 | Insider abuse of privileged roles to read/write PHI beyond job scope. | M | H | Implement PostgreSQL row‑level security policies per role; enforce MFA for all privileged accounts; schedule quarterly access‑review audits with automated report generation. | Compliance Officer |
| RISK-004 | Incomplete or tampered audit log entries, undermining forensic capability. | L | H | Deploy pgAudit extension; forward logs to MinIO bucket configured in Write‑Once‑Read‑Many (WORM) mode; run daily SHA‑256 hash comparison script and alert on mismatch. | Operations Lead |
| RISK-005 | Failure to maintain HIPAA‑required data retention periods (minimum 6 years) in an air‑gapped environment. | M | M | Define retention policy RET‑001; archive encrypted logs and PHI snapshots to LTO tapes quarterly; verify tape integrity with checksum validation after each write cycle. | Records Manager |
| RISK-006 | Deployment complexity leading to misconfiguration that disables security controls in Docker Compose stack. | M | M | Provide hardened Docker Compose baseline with pinned image digests; integrate Trivy vulnerability scanning in CI; enforce configuration‑as‑code checklist before any release merge. | Release Engineer |
| RISK-007 | Service unavailability due to single‑point‑of‑failure components (e.g., database). | L | H | Deploy PostgreSQL primary‑replica cluster with automatic failover; configure HAProxy health checks; monitor with Prometheus alerts targeting >99.9 % SLA. | Site Reliability Engineer |
| RISK-008 | Non‑compliance with state‑level privacy statutes (e.g., California CCPA) when expanding SaaS tenancy. | L | M | Implement data‑subject request workflow documented in SOP‑CCPA; store consent flags in encrypted metadata; map each tenant’s data residency in configuration file. | Legal Counsel |

## Acceptance Sign‑off Criteria
The project is considered successful when **all** of the following conditions are met:
* Every functional requirement listed above reports **"Pass"** against its acceptance criteria during verification.
* All KPIs achieve or exceed their target values for three consecutive monitoring windows (e.g., three months for uptime).
* The Compliance Officer signs off on the quarterly audit report confirming HIPAA compliance with zero critical findings.
* The CI pipeline shows ≥ 95 % test coverage with zero failing tests.

## Governance & Documentation Checklist
* All functional requirements have unique IDs (FR‑001 – FR‑009).
* Each requirement is linked to at least one KPI and one risk in the traceability matrix.
* Stakeholder matrix defines access tiers and linked objectives.
* Risk register includes concrete mitigation actions and assigned owners.
* KPI definitions include measurement method and target.
* Acceptance criteria are measurable, testable, and documented.
* All artifacts are stored in the project repository under `/docs/inception/` with version control.

---
*Document prepared by the Refiner (Senior Business Analyst) on 2026‑05‑04.*

# Strategic Vision

**Vision:** Deliver a fully HIPAA‑compliant, open‑source patient intake SaaS solution that enables secure collection, storage, and export of protected health information (PHI) while operating in an air‑gapped on‑premise environment.

# Business Objectives
1. **Encryption:** Achieve 100 % encryption of PHI at rest (AES‑256) and in transit (TLS 1.3) as mandated by HIPAA §164.312(a)(2)(iv).
2. **Access Control & Auditing:** Provide role‑based access control (RBAC) for Admin, Clinician, and Front‑Desk staff with immutable audit logging for every read/write operation (HIPAA §164.312(b)).
3. **Secure PDF Export:** Generate PDF intake summaries that are watermarked, timestamped, and exportable only by authorized roles (HIPAA §164.312(e)).
4. **Air‑Gap Deployment:** Ensure operational independence from external cloud services, supporting an air‑gap deployment model.

# Scope Definition

## Out‑of‑Scope
- Third‑party SaaS analytics platforms.
- Cloud‑based key‑management services (e.g., AWS KMS).
- Mobile native applications (outside MVP).
- Integration with external EHR systems (future phase).

# Functional Requirements
| ID | Description | Acceptance Criteria |
|----|-------------|-----------------------|
| FR-001 | Secure patient data capture via structured web form. | Form validates all mandatory fields; data is encrypted client‑side before transmission; successful submission stores encrypted record in PostgreSQL. |
| FR-002 | Immutable audit log entry for every read and write operation on PHI. | Each read/write creates a log record containing user ID, timestamp, operation type, and affected record ID; logs are write‑once and retained for ≥7 years. |
| FR-003 | Retain audit log entries for a minimum of seven years. | Audit log entries are searchable and cannot be altered or deleted for the retention period; archival process verifies 100 % preservation. |
| FR-004 | PDF intake summary includes visible watermark containing exporting staff member’s name and export timestamp. | Exported PDF shows watermark with staff name; PDF metadata includes export timestamp; only users with Export role can trigger generation. |
| FR-005 | Role‑based access control for Admin, Clinician, Front‑Desk. | Admin can create, read, update, delete all records; Clinician can read and update assigned patient records; Front‑Desk can create and read but not modify audit logs. |
| FR-006 | Automated test suite covering form validation, encryption, and access control. | Test suite runs on every CI build; includes at least 80 % code coverage; all tests pass in a clean environment. |
| FR-007 | Docker‑Compose deployment for on‑premise air‑gap environment. | Deployment script provisions PostgreSQL, web app, and supporting services without external network calls; installation guide validates successful start‑up on a fresh host. |
| FR-008 | Documentation of air‑gap setup procedures. | Guide includes network isolation steps, key generation, and verification checklist; reviewer can follow guide to achieve a compliant isolated deployment. |
| FR-009 | Open‑source licensing compliance for all components. | All third‑party libraries are verified to be compatible with the chosen OSS license (e.g., MIT or Apache 2.0); license file lists each component and its license. |

# Non‑Functional Requirements
- **NFR‑001:** Encryption algorithms must meet AES‑256 for at rest and TLS 1.3 for in transit.
- **NFR‑002:** System shall achieve 99.5 % uptime measured monthly.
- **NFR‑003:** Audit log write latency must not exceed 200 ms per operation.
- **NFR‑004:** All source code and dependencies must be publicly available in a version‑controlled repository.

# Compliance Mapping
| Regulation | Satisfied By |
|------------|--------------|
| HIPAA §164.312(a)(2)(iv) | NFR‑001 (AES‑256, TLS 1.3) |
| HIPAA §164.312(b) | FR‑002, FR‑005 (RBAC & audit logging) |
| HIPAA §164.312(e) | FR‑004 (watermark & timestamp) |
| HIPAA §164.308(a)(1)(ii)(A) | FR‑003, NFR‑004 (immutable audit log retention) |
| HITRUST CSF 01.d | Comprehensive risk mitigation and documented policies (see Risk Register) |

# Stakeholder Matrix
| Stakeholder | Role | Responsibility |
|------------|------|----------------|
| Clinical Staff | End User | Provide patient information; verify PDF summaries |
| Front‑Desk Personnel | Data Entry Operator | Capture demographics; initiate intake workflow |
| IT Security Team | Owner | Define encryption keys, monitor audit logs, enforce RBAC |
| Compliance Officer | Reviewer | Validate HIPAA/HITRUST adherence, approve risk register |
| Project Sponsor | Sponsor | Approve budget, ensure alignment with organizational goals |

# Key Performance Indicators (KPIs)
| ID | Definition |
|----|------------|
| KPI-001 | Audit log completeness – 100 % of read/write operations captured. |
| KPI-002 | PDF export watermark presence – 100 % of exported PDFs contain correct staff watermark. |
| KPI-003 | System uptime – Minimum 99.5 % monthly availability. |
| KPI-004 | Deployment success rate – 95 % of air‑gap installations complete without manual intervention. |
| KPI-005 | Test suite pass rate – 100 % of automated tests pass on each CI run. |
| KPI-006 | Open‑source license compliance – 100 % of third‑party components verified against chosen OSS license. |

# Risk Register
| ID | Description | Owner | Mitigation Action |
|----|-------------|-------|-------------------|
| RISK-001 | Quarterly penetration testing not assigned. | IT Security Lead | Assign dedicated tester; schedule quarterly scans; document findings. |
| RISK-002 | Performance impact on transaction latency due to audit logging. | Database Administrator | Benchmark logging overhead; tune PostgreSQL write‑ahead logging; implement batch inserts if needed. |
| RISK-003 | Incomplete coverage of edge cases in test suite. | QA Lead | Expand test matrix to include failure injection; conduct test review meetings bi‑weekly. |
| RISK-004 | Vague NFRs lacking measurable targets. | Compliance Officer | Refine each NFR with quantitative thresholds; link to KPI‑001…KPI‑006. |
| RISK-005 | Missing owners for several mitigation actions. | Project Manager | Populate risk register with responsible individuals; review during sprint planning. |
| RISK-006 | Open‑source license incompatibility risk. | Legal Counsel | Perform license compatibility analysis for all dependencies; maintain SPDX manifest. |

# Traceability Matrix
| Requirement ID | Business Objective(s) | KPI(s) | Risk(s) |
|----------------|------------------------|--------|--------|
| FR-001 | Objective 1, 2 | KPI-001 | RISK-002 |
| FR-002 | Objective 2 | KPI-001 | RISK-001 |
| FR-003 | Objective 2 | KPI-001 | RISK-001 |
| FR-004 | Objective 3 | KPI-002 | RISK-004 |
| FR-005 | Objective 2 | KPI-003 | RISK-002 |
| FR-006 | Objective 4 | KPI-005 | RISK-003 |
| FR-007 | Objective 4 | KPI-004 | RISK-002 |
| FR-008 | Objective 4 | KPI-004 | RISK-005 |
| FR-009 | Objective 1, 4 | KPI-006 | RISK-006 |

# Acceptance Criteria Summary
All functional requirements above include explicit acceptance criteria that are measurable, testable, and traceable to the defined KPIs and risks. The document now provides a complete set of business artifacts required for downstream design and implementation phases.
# Governance Model (Overview)

### 1. Strategic Objectives
| Objective ID | Description | Metric |
|---|---|---|
| OBJ‑001 | Achieve 100 % encryption of PHI at rest and in transit using AES‑256 and TLS 1.3. | Encryption coverage ≥ 100 % (KPI‑001) |
| OBJ‑002 | Provide role‑based access control (admin, clinician, front‑desk) with least‑privilege enforcement and immutable audit logging covering 100 % of read/write events. | Audit log completeness ≥ 100 % (KPI‑002) |
| OBJ‑003 | Enable on‑premise deployment via Docker Compose without any external cloud dependencies, supporting an air‑gap configuration checklist. | First‑try deployment success ≥ 95 % (KPI‑004) |
| OBJ‑004 | Deliver a PDF summary generator that stamps a visible watermark and timestamp on every export, accessible only to authorized staff. | PDF watermark presence = 100 % (KPI‑003) |
| OBJ‑005 | Provide an automated test suite that validates form encryption, access‑control enforcement, audit‑log generation, and PDF watermarking. | Test coverage ≥ 90 % of functional requirements (KPI‑005) |

### 2. Stakeholder Analysis
| Stakeholder | Need / Goal | Primary Concern | Role / Access Level | Aligned Objective |
|---|---|---|---|---|
| Patient | Secure submission of personal health information and receipt confirmation. | Fear of data breach or unauthorized viewing. | Read‑Only (self‑service – can create a submission and view own record only). | OBJ‑001 |
| Front‑Desk Staff | Capture intake data efficiently, verify completeness, and forward submissions without exposing unnecessary PHI. | Manual re‑entry of data leads to errors; risk of viewing more PHI than needed. | Write‑Limited (create new records, edit non‑PHI fields). | OBJ‑002 |
| Clinician | Review complete intake data to make clinical decisions. | Need full PHI visibility while preventing accidental disclosure to non‑clinicians. | Full read access to encrypted sections; write access for notes. | OBJ‑002 |
| Administrator | Ensure reliable deployment, configuration control, and ongoing system maintenance. | Complexity of multi‑vendor setups and auditability. | Full admin rights including audit‑log management. | OBJ‑003 |
| Compliance Officer | Provide auditable evidence of HIPAA controls and maintain compliance posture. | Lack of immutable logs and traceability of changes. | Oversight only; can view audit logs and policy documents. | OBJ‑002 |

### 3. Traceability Matrix
| Requirement ID | Source Section | Owner |
|---|---|---|
| FR‑001 | Business Vision → Functional Requirements | Compliance Officer |
| FR‑020 | Functional Requirements | Administrator |
| FR‑030 | Functional Requirements | Compliance Officer |
| FR‑040 | Functional Requirements | Front‑Desk Staff Lead |
| FR‑050 | Functional Requirements | DevOps Engineer |
| KPI‑001…KPI‑005 | Success Criteria / KPIs | Respective Product Owner |
| RISK‑001…RISK‑004 | Risk Register | Assigned Owner as listed |

# Inception Artifact – PatientIntake Project

## 4. Business Vision
The PatientIntake system will provide a fully HIPAA‑compliant, open‑source platform for capturing patient demographics, insurance details, and medical history at the point of entry. All data will be encrypted at rest and in transit, stored in a locally‑hosted PostgreSQL instance with immutable audit logging, and presented to clinicians via secure PDF summaries that carry visible watermarks and export timestamps. The solution will be containerised with Docker‑Compose to enable rapid, air‑gapped deployment in on‑prem environments.

## 5. Review Cycle
- **Monthly** – Risk Committee reviews new findings, updates the risk register, and tracks KPI trends.
- **Quarterly** – Independent SOC 2 auditor conducts compliance audit of audit‑log integrity and RBAC enforcement.
- **Annually** – Full HIPAA compliance audit performed by internal compliance team; board receives risk report and KPI dashboard.

## 6. Governance Model Summary
The inception artifacts collectively define the decision‑making structure, ownership, and oversight for the PatientIntake project. Every functional requirement is traceable to a stakeholder objective, each risk includes a concrete mitigation owner, and success is measured against explicit KPIs. This foundation enables downstream design and implementation phases to proceed with clear accountability and regulatory alignment.

## Business Requirements
**FR-001:** Secure Patient Data Capture
*Description:* Collect patient demographics, insurance information, and medical history via a structured web form with field‑level encryption at rest and in transit.
*Acceptance Criteria:* All PHI fields are encrypted using AES‑256 at rest; TLS 1.2+ is enforced for all client‑server communication; form validation rejects incomplete submissions.

**FR-002:** Immutable Audit Log Generation
*Description:* The system shall generate an immutable audit log entry for every read and write operation on PHI, including user ID, timestamp, and operation type.
*Acceptance Criteria:* Every CRUD operation creates a log entry stored in an append‑only table; entries are cryptographically signed; retention period is 7 years.

**FR-003:** Audit Log Retention
*Description:* Every read or write operation on the PostgreSQL store must generate an immutable audit log entry retained for a minimum of seven years.
*Acceptance Criteria:* Automated archival moves logs older than 7 years to encrypted cold storage; verification script confirms 100 % of required entries are retained.

**FR-004:** PDF Export Watermark
*Description:* PDF intake summaries must include a visible watermark containing the exporting staff member.
*Acceptance Criteria:* Exported PDFs display staff name and export timestamp in the footer; watermark is immutable after generation.

**FR-005:** Automated Test Suite
*Description:* Provide unit and integration tests covering form validation, data encryption, and access‑control edge cases.
*Acceptance Criteria:* Test coverage ≥ 80 %; CI pipeline fails on any test regression.

**FR-006:** Role‑Based Access Control (RBAC)
*Description:* Implement RBAC with roles admin, clinician, front‑desk; enforce least‑privilege access to PHI.
*Acceptance Criteria:* Access matrix documented; attempts to access unauthorized records are logged and denied.

**FR-007:** Air‑Gap Deployment Guide
*Description:* Document step‑by‑step Docker‑Compose deployment for on‑premise environments with no external network dependencies.
*Acceptance Criteria:* Deployment guide validated on three clean servers; first‑time success rate ≥ 98 %.

**FR-008:** PDF Export Security
*Description:* Authorized staff may export PDFs; each export records an access timestamp in the audit log.
*Acceptance Criteria:* Export action creates a log entry; exported file cannot be opened without valid user session token.

## Key Performance Indicators
| KPI ID | Indicator | Target | Measurement Method | Related Objective |
|--------|------------|--------|-------------------|---------------------|
| KPI-001 | Form Completion Rate | ≥ 92 % of patients complete the intake form without abandonment | Web analytics tracking of form start vs submit events over a 4‑week period | OBJ-001: High‑quality data capture |
| KPI-002 | Encryption Compliance Rate | 100 % of PHI fields encrypted at rest | Automated compliance scan of database columns nightly | OBJ-002: Regulatory compliance |
| KPI-003 | Audit Log Availability | 99.9 % uptime of audit‑log service | Prometheus uptime metric aggregated monthly |
| KPI-004 | PDF Export Accuracy | 100 % of exported PDFs contain correct watermark and timestamp | Random sampling of exported PDFs with checksum verification against audit log | OBJ-004: Secure information sharing |
| KPI-005 | Deployment Success Rate (air‑gap) | ≥ 98 % first‑time deployment without manual re‑configuration | Post‑deployment checklist completion count / total deployments | OBJ-005: Reliable on‑premise rollout |

## Risks and Mitigations
| Risk ID | Description | Owner | Mitigation Action |
|---------|-------------|-------|-------------------|
| RISK-001 | Quarterly penetration testing has no assigned owner. | Security Lead (WG) | Assign responsibility to Security Lead; schedule automated quarterly testing and document results. |
| RISK-002 | Missing concrete implementation detail for digital signature in audit‑log integrity verification. | Compliance Officer (WG) | Define HMAC‑SHA256 signing process using HashiCorp Vault keys; include key rotation policy. |
| RISK-003 | Incomplete coverage of audit‑log generation for delete operations. | Architecture Lead (PGB) | Extend logging middleware to capture DELETE actions; add test cases in automated suite. |
| RISK-004 | Lack of assigned owner for risk mitigation actions leads to accountability gaps. | Project Manager (PGB) | Create risk register with explicit owners and due dates; review in each Governance Board meeting. |
| RISK-005 | Performance impact on transaction latency due to audit‑log write overhead. | DevOps Engineer (Operations WG) | Benchmark log write latency; implement batch writes if latency exceeds 150 ms; monitor via Prometheus alerts. |
| RISK-006 | Air‑gap deployment may miss required network isolation steps. | Operations Lead (PGB) | Include network isolation checklist in deployment guide; perform peer review before release. |

### Decision‑Making Hierarchy
1. **Executive Steering Committee (ESC)** – Sets strategic direction, approves budget, resolves escalated issues.
2. **Project Governance Board (PGB)** – Owns day‑to‑day decisions, prioritises backlog items, validates compliance artefacts.
3. **Domain Working Groups** – Provide specialised input and own implementation of their domain policies (Clinical, Security, Operations).
4. **Audit & Review Office (ARO)** – Conducts quarterly audits of audit‑log integrity and governance adherence; reports to the Compliance Officer.

### Ownership Matrix
| Artifact / Decision | ESC Owner | PGB Owner | Clinical WG Owner | Security WG Owner | Operations WG Owner |
|--------------------|-----------|----------|-----------------|------------------|----------------------|
| Business Vision & Scope | CIO | PM | – | – | – |
| Risk Register Updates | – | PM | – | Security Officer | Ops Lead |
| KPI Definition & Acceptance Criteria | – | PM | Clinical Lead | Security Lead | Ops Lead |
| Audit‑Log Policy | – | Security Lead | – | Security Lead | – |
| Deployment Guide Approval | – | Ops Lead | – | – | Ops Lead |

## Audit & Compliance Policy
* **Audit Log Scope** – Every read, write, update, and delete operation on PHI must generate an immutable log entry stored in append‑only storage for a minimum of 7 years.
* **Log Integrity** – Logs are signed with SHA‑256 HMAC using a rotation‑managed key stored in HashiCorp Vault; nightly verification performed by the ARO.
* **Review Cadence** – Monthly log‑review meetings chaired by the Security Lead; quarterly independent audits by the ARO.
* **Retention & Disposal** – Logs older than 7 years are archived to encrypted cold storage; secure erase procedures applied upon disposal.

## Scope Definition
| Area | In‑Scope | Out‑Of‑Scope |
|------|----------|--------------|
| Data Collection | Web‑form capture of demographics, insurance, medical history; field‑level encryption at rest & in transit. | Paper‑based intake forms. |
| Access Control | Role‑based access (admin, clinician, front‑desk) enforced via RBAC in PostgreSQL. | External third‑party integrations not approved by compliance. |
| PDF Generation | Authorized export with watermark and timestamp per HIPAA audit log. | Custom branding beyond watermark. |
| Deployment | Docker‑Compose on‑premise, air‑gap ready. | Cloud‑hosted SaaS platforms. |

## Review & Amendment Process
1. **Quarterly Governance Review** – PGB reviews all governance artefacts, updates scope, KPIs, and risk register.
2. **Change Request Procedure** – Amendments submitted via formal Change Request form; evaluated for HIPAA impact; approved by ESC.
3. **Version Control** – Documents stored in a Git repository with signed commits; each version tagged semantically (e.g., v1.2.0).
4. **Communication** – Updated artefacts disseminated through internal knowledge base and announced in monthly all‑hands meeting.
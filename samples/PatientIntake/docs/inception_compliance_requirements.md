# HIPAA & Regulatory Compliance Requirements (Overview)

### 2. Scope
**In‑Scope**
- Structured web form with field‑level encryption at rest (AES‑256) and in transit (TLS 1.3).
- Role‑based access control (Admin, Clinician, Front‑Desk) enforced via PostgreSQL row‑level security.
- Immutable audit log of every read/write operation retained for 7 years.
- PDF generation per patient with watermark containing export timestamp and exporting user ID.
- Automated unit and integration tests covering form validation, encryption correctness, and access‑control edge cases.
- Docker‑Compose deployment for air‑gapped on‑prem environments.

**Out‑Of‑Scope**
- Integration with external billing or EHR systems.
- Mobile‑native client applications.
- Advanced analytics beyond the defined KPI set.

### 3. Stakeholder Analysis
| Stakeholder | Primary Need | Success Metric | Business Objective |
|---|---|---|---|
| Patients | Secure submission and immediate confirmation | 95% of submissions complete within 2 seconds; 99.9% encryption verification rate | OBJ-001 |
| Front‑Desk Staff | Efficient data entry with real‑time validation | Inline validation error rate <1%; average entry time <30 seconds | OBJ-002 |
| Clinicians | Immediate access to accurate intake records | Record retrieval latency <200 ms; 99% RBAC compliance | OBJ-003 |
| Administrators | Configurable permissions, key management, audit‑log oversight | Zero unauthorized access incidents; key‑rotation compliance >95% | OBJ-004 |
| Compliance Officer | Evidence of HIPAA, SOC 2, ISO 27001 compliance | Audit report generation <5 minutes; 100% required artifacts present | OBJ-005 |

### 4. Functional Requirements
- **FR-001**: Capture patient demographics, insurance details and medical history via a web form.
  - *Acceptance Criteria*: All required fields are stored with field‑level encryption at rest and in transit; form submission response time ≤200 ms (p95).
- **FR-002**: Enforce role‑based access control with three tiers (Admin, Clinician, Front‑Desk).
  - *Acceptance Criteria*: Access matrix verified by automated test suite covering all CRUD operations; unauthorized read attempts are denied and logged.
- **FR-003**: Record every read and write operation in an immutable audit log retained for 7 years.
  - *Acceptance Criteria*: Log entries contain user ID, timestamp, and record ID; log retention verified by quarterly audit script.
- **FR-004**: Generate a PDF intake summary per patient with watermark containing export timestamp and exporting user ID.
  - *Acceptance Criteria*: Watermark present on 100% of exported PDFs; export restricted to Admin and Clinician roles.
- **FR-005**: Provide automated unit and integration tests covering form validation, encryption correctness and access‑control edge cases.
  - *Acceptance Criteria*: Test coverage ≥85%; all critical tests pass in CI pipeline.

### 5. Success Criteria / KPIs
| KPI ID | Metric | Target Value | Measurement Method |
|---|---|---|---|
| KPI-001 | Encryption compliance rate | 100% of PHI fields encrypted | Automated compliance scan quarterly |
| KPI-002 | Access log completeness | 100% of read/write events logged | Log audit script comparing DB ops vs log entries |
| KPI-003 | Form submission success rate | ≥95% of submissions complete without error | Submission logs analysis weekly |
| KPI-004 | PDF export accuracy | 100% of PDFs contain correct watermark and timestamp | Manual spot check of 20 random exports per month |
| KPI-005 | Deployment reproducibility | Successful Docker‑Compose deployment on air‑gapped environment ≤15 minutes | Deployment run‑time measurement |

### 6. Risk Assessment
- **RISK-001**: Unauthorized PHI access due to misconfigured RBAC (Likelihood: Medium, Impact: High).
  - *Mitigation*: Enforce PostgreSQL row‑level security; run quarterly permission‑audit scripts; integrate automated regression tests for RBAC.
- **RISK-002**: Encryption key compromise (Likelihood: Low, Impact: High).
  - *Mitigation*: Store keys in a hardware security module (HSM); rotate keys every 90 days; enforce multi‑factor authentication for key access.
- **RISK-003**: Audit log tampering or loss (Likelihood: Low, Impact: High).
  - *Mitigation*: Write logs to append‑only immutable storage with digital signatures; backup logs daily; retain for 7 years.
- **RISK-004**: Deployment in non‑air‑gapped environment exposing PHI (Likelihood: Medium, Impact: High).
  - *Mitigation*: Pre‑deployment script validates network isolation; aborts if external interfaces detected; maintain air‑gap certification checklist.
- **RISK-005**: Performance degradation under peak load affecting SLA (Likelihood: Medium, Impact: Medium).
  - *Mitigation*: Conduct stress testing at 150 % expected load; auto‑scale Docker services locally; monitor response times with alert thresholds.

### 7. Traceability Matrix
| Stakeholder Need | Mapped Functional Requirement(s) |
|---|---|
| Secure submission & confirmation (Patients) | FR-001, FR-003, FR-004 |
| Real‑time validation & low error rate (Front‑Desk) | FR-001, FR-005 |
| Immediate access to accurate records (Clinicians) | FR-002, FR-003 |
| Configurable permissions & audit oversight (Administrators) | FR-002, FR-003 |
| Evidence of compliance for audits (Compliance Officer) | FR-003, FR-004, FR-005 |

### 8. Open‑Source Compliance Verification
All components are selected from approved open‑source licenses (MIT, Apache 2.0, GPL‑compatible). A license audit is performed during CI to ensure no prohibited licenses are introduced. Dependencies are pinned to specific versions and scanned with SPDX tools to maintain compliance with organizational open‑source policy.

## Business Vision
The PatientIntake project delivers a secure, HIPAA‑compliant web‑based intake system that enables front‑desk staff to capture patient demographics, insurance and medical history, ensures encrypted storage and transmission, provides role‑based access for clinicians and administrators, logs all data interactions, and produces auditable PDF summaries. Success is measured by meeting defined KPIs (encryption compliance ≥100 %, audit‑log completeness ≥100 %, form response time ≤200 ms, system uptime ≥99.9 %).

## Deployment Environment Constraints (Enhanced)
| Constraint ID 
Description 
Requirement 
Verification Method 
Owner 
|---
---
---
---
---
| DEP-001 
Air‑gapped deployment without external internet access 
All containers must run on isolated network; no outbound DNS queries to public domains. 
Network scan and firewall rule audit before go‑live; CI pipeline rejects external network calls. 
Ops Lead 
| DEP-002 
Use of only open‑source components with no proprietary licenses 
All software packages must be OSI‑approved; license audit performed quarterly. 
SPDX license scan report integrated in CI; any non‑OSS flagged as failure. 
Compliance Officer 
| DEP-003 
Container image provenance and reproducibility 
Images built from deterministic Dockerfiles stored in version control; signed with Notary. 
Signature verification during CI; reproducibility test on clean host. 
Security Engineer 
| DEP-004 
Secure configuration management for Docker Compose files 
No hard‑coded secrets; use environment variable injection from vault. 
Config lint and secret scan; secret injection validated at runtime. 
Ops Lead

## Mitigation Summary
The layered safeguards—TLS 1.3, AES‑256 field‑level encryption, HSM‑based key management, immutable audit logging, and strict air‑gap controls—address the identified risks and satisfy HIPAA §164.312 technical safeguard requirements. Measurable KPIs (KPI‑001 Encryption compliance 100 %, KPI‑003 Audit‑log completeness 100 %, KPI‑005 System uptime ≥99.9 %) are directly linked to the mitigations. Ongoing stakeholder engagement ensures privacy expectations of patients and compliance obligations of the organization remain satisfied throughout the project lifecycle.
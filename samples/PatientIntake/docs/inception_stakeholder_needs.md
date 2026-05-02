# Stakeholder Needs Analysis (Overview)

## 1. Executive Summary
- **RISK-001** – Unauthorized PHI access due to misconfigured RBAC (Medium/High). *Mitigation*: Implement role‑based policies reviewed by Security Lead; automated policy validation CI job that fails build on policy drift. *Acceptance*: CI pipeline reports zero policy violations for three consecutive runs.
- **RISK-002** – Encryption key compromise in air‑gapped environment (Low/High). *Mitigation*: Use hardware security module (HSM) for key storage; rotate keys every 90 days; enforce MFA for key access. *Acceptance*: Key rotation logs audited monthly; HSM attestation verified.
- **RISK-003** – Audit log tampering or loss (Low/High). *Mitigation*: Write logs to append‑only immutable storage with digital signatures; retain for 7 years; periodic integrity verification using hash chaining. *Acceptance*: Weekly hash verification passes without mismatch.
- **RISK-004** – Performance degradation under peak intake volume affecting SLA (Medium/Medium). *Mitigation*: Conduct stress testing; auto‑scale container replicas within air‑gap constraints; monitor latency KPI‑001 with alert thresholds. *Acceptance*: Load test shows ≤200 ms p95 under simulated peak of 500 concurrent submissions.
- **RISK-005** – Open‑source component vulnerability discovered post‑deployment (Medium/Medium). *Mitigation*: Maintain vulnerability scanning pipeline; subscribe to CVE feeds; patch within 7 days of disclosure. *Acceptance*: Patch applied within SLA for all identified CVEs.

## 2. Scope Definition
| Stakeholder Objective | Functional Requirement(s) | KPI(s) |
|---|---|---|
| OBJ‑001 – 100 % HIPAA encryption compliance | FR-001, FR-002 | KPI‑001 |
| OBJ‑002 – Form submission latency <200 ms (p95) | FR-001, FR-002 | KPI‑004 |
| OBJ‑003 – Record availability ≥99.9 % within 2 s | FR-003 | KPI‑001 |
| OBJ‑004 – Audit log completeness 100 % | FR-005 | KPI‑003 |
| OBJ‑005 – Retain immutable logs for 7 years | FR-005 | KPI‑003 |

## 3. Compliance Objectives
- **Project Sponsor**: Chief Medical Officer – ensures alignment with clinical priorities.
- **Security Lead**: Oversees encryption, key management, and risk mitigation.
- **Operations Lead**: Validates air‑gap deployment scripts and infrastructure readiness.
- **Compliance Officer**: Confirms adherence to HIPAA §§164.312(a)(2)(iv), §164.312(e)(1), and §164.308(a)(1)(ii); maintains audit evidence.
- **Product Owner**: Coordinates stakeholder requirements and prioritization.

*Document version 1.2 – refined to include traceability links, detailed risk mitigation acceptance criteria, and explicit requirement identifiers.*

## 4. Stakeholder Analysis
**In‑Scope**:
- Web‑based structured intake form with field‑level encryption at rest (AES-256) and in transit (TLS 1.3) – see FR-001.
- PostgreSQL database configured for role‑based access control (admin, clinician, front‑desk) – see FR-003.
- Immutable audit log capturing every read/write operation – see FR-005.
- PDF summary generation with watermark containing user ID and timestamp – see FR-004.
- Automated unit and integration test suite covering validation, encryption, and access‑control edge cases.
- Docker‑Compose deployment package with documented air‑gap setup guide.
**Out‑of‑Scope**:
- Third‑party SaaS services, cloud storage, or external API integrations.
- Clinical decision support beyond data capture.
- Mobile native applications; only browser‑based UI is covered.

## 5. Business Vision and Objectives
| ID | Standard | Requirement | Acceptance Method |
|----|----------|-------------|-------------------|
| COMP-HIPAA-001 | 45 CFR §164.312(a)(2)(iv) | Encrypt PHI at rest (AES-256) | Configuration scan confirming all PHI columns encrypted |
| COMP-HIPAA-002 | 45 CFR §164.312(e)(1) | Encrypt PHI in transit (TLS 1.3) | Network capture verifies TLS 1.3 for all traffic |
| COMP-HIPAA-003 | 45 CFR §164.308(a)(1)(ii) | Audit logging of all read/write events | Log integrity verified by digital signatures; retention 7 years |
| COMP-OPEN-001 | Open‑Source Policy | Use only OSI‑approved licenses | License audit of all dependencies |

## 6. High‑Level Functional Requirements
| Stakeholder | Primary Need | Business Impact | RBAC Tier | Linked Objective |
|------------|--------------|------------------|-----------|-----------------|
| Patient | Confidential, fast intake with clear privacy notice | Risk of PHI exposure if not encrypted | No DB access (read only via UI) | OBJ-001: Achieve 100% HIPAA encryption compliance |
| Front‑Desk Staff | Efficient data entry and real‑time validation to reduce re‑work | Manual correction slows workflow | Operator (create/read) | OBJ-002: Form submission latency <200 ms (p95) |
| Clinician | Immediate access to accurate patient records for care decisions | Delayed records impede treatment | Clinician (read) | OBJ-003: Record availability 99.9% within 2 seconds |
| Administrator | Centralized permission management and auditability | Complex matrices increase error risk | Admin (full) | OBJ-004: Audit log completeness 100% for all read/write |
| Compliance Officer | Evidence of HIPAA controls for audit readiness | Lack of traceable controls could lead to penalties | Auditor (read‑only) | OBJ-005: Retain immutable logs for 7 years |

## 7. Risks and Mitigations
The PatientIntake project aims to deliver a fully HIPAA‑compliant intake platform that enables rapid, secure capture of patient demographics, insurance information, and medical history while leveraging only open‑source technologies. Objectives include:
- Regulatory compliance (HIPAA, Open‑Source policy).
- Reduce manual data entry errors by ≥90%.
- Achieve sub‑200 ms form response times (p95).
- Provide immutable audit trails for all data accesses.
- Deploy via Docker Compose in an air‑gapped environment with ≥99% first‑attempt success.

## 8. Traceability Matrix
- **FR-001**: Capture patient demographics, insurance information, and medical history via a structured web form. *Acceptance*: 100% of required fields captured; validation error rate <1% across 10 000 test entries.
- **FR-002**: Encrypt all form field data at rest using AES-256 and in transit using TLS 1.3. *Acceptance*: Independent security scan confirms encryption for every stored column and all network traffic.
- **FR-003**: Store submissions in a local PostgreSQL instance with row‑level security enforcing role‑based access (admin, clinician, front‑desk). *Acceptance*: Access control matrix verified by automated audit script; no unauthorized read/write detected in penetration testing.
- **FR-004**: Generate a PDF summary per patient that can be exported only by authorized roles. *Acceptance*: Watermark includes user ID and timestamp; export logs created for 100% of exports and verified by log review.
- **FR-005**: Maintain an immutable audit log of every read and write operation retained for 7 years. *Acceptance*: Log integrity verified by digital signature check; retention policy enforced by automated archival process.

## 9. Governance and Ownership
The PatientIntake project delivers a HIPAA‑compliant web‑based intake system using only open‑source components. The primary business objective is to enable rapid, accurate capture of patient demographics, insurance information, and medical history while guaranteeing confidentiality, integrity, and availability of PHI. Success is measured by regulatory compliance, auditability, and operational efficiency in an air‑gapped on‑prem environment.

## 10. Success Criteria
- **SC-001**: All patient data captured via the web form must be encrypted at rest (AES-256) and in transit (TLS 1.3). *Verification*: Audit of encryption configuration shows 100% coverage.
- **SC-002**: Role‑based access control must enforce three tiers (Admin, Clinician, Front‑Desk). *Verification*: Access matrix test shows no privilege escalation.
- **SC-003**: Audit logs must retain every read/write event for 7 years on immutable storage. *Verification*: Log retention report confirms 100% of events stored.
- **SC-004**: PDF export must include a watermark with user ID and timestamp. *Verification*: Automated PDF validation script confirms correct watermark on 100% of exports.
- **SC-005**: System must be deployable via Docker Compose in an air‑gapped environment without external network calls. *Verification*: Deployment test on isolated network succeeds on first attempt.

## 11. Key Performance Indicators (KPIs)
| ID | KPI | Target | Measurement Method |
|----|-----|--------|--------------------|
| KPI-001 | Encryption Compliance Rate | 100% of PHI fields encrypted at rest | Automated configuration scan (e.g., OpenSCAP) |
| KPI-002 | Transmission Security Rate | 100% of traffic uses TLS 1.3 | Network capture analysis |
| KPI-003 | Access Log Completeness | 100% of read/write events logged | Log audit script comparing DB audit table vs operation count |
| KPI-004 | Form Response Time (p95) | ≤200 ms | Synthetic load test using JMeter |
| KPI-005 | PDF Export Accuracy | 100% of PDFs contain correct watermark and timestamp | Automated PDF validation script |
| KPI-006 | Deployment Success Rate | ≥99% on first‑attempt installs in air‑gapped labs | Deployment logs review |
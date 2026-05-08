# Risk Assessment (Overview)

### 1. Business Vision & Objectives
The PatientIntake project delivers a **self‑hosted SaaS‑style** open‑source patient intake platform that enables health‑care providers to capture protected health information (PHI) electronically while meeting **HIPAA**, **SOC 2**, and **GDPR** obligations. The solution is deployed on‑premises via Docker Compose, satisfying air‑gap requirements while offering the operational benefits of a SaaS product (centralized updates, consistent security posture, multi‑tenant isolation). The vision is to replace paper‑based forms with a secure, auditable web‑based workflow that reduces data‑entry errors by ≥ 30 % and accelerates patient onboarding by ≥ 20 %.

**Strategic objectives**
1. Achieve HIPAA, SOC 2, and GDPR compliance for data in transit (TLS 1.3) and at rest (AES‑256).
2. Provide role‑based access control (RBAC) that enforces least‑privilege for Administrators, Clinicians, and Front‑Desk staff.
3. Ensure auditability by retaining immutable logs for a minimum of seven years.
4. Deliver high availability (≥ 99.9 % uptime) with horizontal scalability across multiple tenant instances.
5. Operate entirely on‑premises using Docker Compose to satisfy air‑gap environments while supporting SaaS‑style multi‑tenant deployment.

### 2. Functional Requirements
| ID | Description | Acceptance Criteria |
|----|-------------|---------------------|
| **FR-001** | Secure Web Form – The system shall present a responsive web form that encrypts each field at rest using AES‑256 and in transit via TLS 1.3. | Penetration test shows no plaintext PHI on network or storage; TLS handshake logs confirm TLS 1.3 usage. |
| **FR-002** | Role‑Based Access Control – RBAC must enforce least‑privilege permissions for Admin, Clinician and Front‑Desk roles. | Access matrix test passes 100 % of defined scenarios; audit logs show no privilege escalation. |
| **FR-003** | Audit Log – Every read and write operation shall be recorded with user ID, timestamp, action type and immutable hash. | Log export contains ≥ 99 % of transactions over a 30‑day period; hash verification succeeds for all entries. |
| **FR-004** | PDF Summary Generation – Authorized staff can export a PDF containing the intake data, watermarked with staff name and export timestamp. | PDF metadata includes watermark and timestamp; unauthorized export attempts are denied (403). |
| **FR-005** | Automated Test Suite – Unit and integration tests shall cover form validation, encryption correctness and RBAC edge cases with ≥ 80 % code coverage. | CI pipeline reports ≥ 80 % coverage on each merge; any missing encryption or RBAC test fails the build. |
| **FR-006** | Multi‑Tenant Isolation – The platform shall support multiple independent tenant instances on the same host, each with isolated data stores and configuration. | Tenant A cannot access Tenant B data in any API call or database query; isolation verified by automated tenancy tests. |

### 3. Stakeholder Identification & Needs
| Stakeholder ID | Needs / Expectations | Risks / Pain Points | Access Tier | Objective |
|---------------|----------------------|-------------------|
| **ST-001** (Patient) | Secure, private submission of PHI; no third‑party exposure | Fear of data leakage during entry | Tier 3 (Read‑Only for audit) | OBJ‑001: Ensure patient trust and regulatory compliance |
| **ST-002** (Front‑Desk Staff) | Rapid intake to reduce wait times; avoid manual re‑entry errors | Manual re‑entry leads to errors | Tier 2 (Create/Update) | OBJ‑002: Streamline workflow while maintaining auditability |
| **ST-003** (Clinician) | Immediate access to complete patient history for care decisions | Incomplete or delayed records hinder treatment | Tier 2 (Read/Update) | OBJ‑003: Provide clinicians with timely PHI access |
| **ST-004** (Administrator) | Centralized control over configuration, provisioning, security policies | Complex permission matrices increase misconfiguration risk | Tier 1 (Full Admin) | OBJ‑004: Enforce least privilege across tenants |
| **ST-005** (Compliance Officer) | Evidence of HIPAA, SOC 2, GDPR controls; immutable audit logs; regular compliance reporting | Difficulty proving continuous compliance during audits | Tier 1 (Full Admin) | OBJ‑005: Deliver auditable logs and compliance artifacts |

### 4. Top Risks & Mitigation Strategies
| Risk ID | Description | Impact (L/M/H) | Likelihood (L/M/H) | Mitigation Actions |
|---------|-------------|------------------|-------------------|-------------------|
| **RISK-001** | PHI interception during transmission over the public network | H | M | Enforce TLS 1.3 with forward secrecy; field‑level AES‑256 encryption before transmission; HSTS and certificate pinning. |
| **RISK-002** | Unauthorized read/write access to stored PHI at rest | H | M | Deploy PostgreSQL Row‑Level Security combined with AES‑256 disk encryption; enforce RBAC tiers; quarterly permission reviews. |
| **RISK-003** | Tampering or loss of audit logs compromising forensic evidence | H | L | Immutable append‑only log storage on WORM media; retain logs for 7 years; generate cryptographic hash chain for each entry; nightly integrity verification. |
| **RISK-004** | Service outage exceeding 0.1 % downtime (SLA breach) | M | M | Deploy Docker Swarm with health checks; auto‑restart policies; load balancer failover; Prometheus alerts on latency >200 ms. |
| **RISK-005** | Failure to pass external HIPAA/SOC 2/GDPR audit due to undocumented controls | H | L | Maintain living compliance register linking each requirement (FR‑001…FR‑006) to controls; conduct quarterly mock audits; provide training on security policies for all staff. |

### 5. Scope Definition
**In‑Scope**
- Collection of patient demographics, insurance information, and medical history via a web form.
- Field‑level encryption at rest (AES‑256) and in transit (TLS 1.3) using open‑source cryptographic libraries.
- Role‑based access control for admin, clinician, front‑desk, and tenant administrators.
- Full audit logging of all read/write operations retained for seven years.
- Generation of PDF intake summaries with watermark and export timestamp visible only to authorized staff.
- Automated unit and integration tests covering form validation, encryption verification, RBAC edge cases, and tenancy isolation.
- Deployment via Docker Compose for on‑premise air‑gap environments; supports multi‑tenant isolation on shared hardware.

**Out‑of‑Scope**
- Cloud hosting or SaaS delivery models beyond self‑hosted deployment.
- Integration with external EHR systems.
- Advanced analytics or machine‑learning components beyond basic reporting.
- Multi‑tenant management UI beyond the core intake workflow.

### 6. Measurable Acceptance Criteria
| ID | Criterion |
|----|-----------|
| **FR-001** | All patient form submissions are stored encrypted at rest and transmitted over TLS 1.3; automated security scan achieves 100 % pass rate. |
| **FR-002** | Audit log captures every create/read/update/delete event; monthly reconciliation shows <0.1 % discrepancy between logged events and actual transactions. |
| **FR-003** | PDF summary includes visible watermark "Confidential – Patient Intake" and timestamp; random sampling confirms watermark presence in 100 % of exported PDFs. |
| **FR-004** | Unit/integration test suite achieves ≥ 90 % code coverage; CI pipeline fails if any encryption or RBAC test is missing. |
| **FR-005** | Docker Compose deployment completes on a fresh air‑gap server within 30 minutes; deployment guide validated on two hardware platforms. |
| **FR-006** | Tenant isolation tests prove no cross‑tenant data leakage; each tenant can only access its own database schema and configuration files. |

### 7. Key Performance Indicators (KPIs)
| KPI ID | Metric |
|--------|--------|
| **KPI-001** | System Availability – ≥ 99.9 % uptime per month (Monitored via Prometheus). |
| **KPI-002** | Encryption Verification Rate – 100 % of data fields encrypted at rest and in transit (Quarterly OpenSCAP scans). |
| **KPI-003** | Audit Log Completeness – 100 % of read/write events recorded for 7 years (Annual log audit). |

### 8. Compliance Controls Summary
The platform implements controls required by **HIPAA §164.312(a)(1)** (access control), **HIPAA §164.312(e)(1)** (audit controls), **SOC 2 CC6 – Logical Access Controls**, and **GDPR Article 32 – Security of Processing**. Controls include:
- Encryption key management with rotation every 90 days.
- Multi‑factor authentication for all admin accounts.
- Regular vulnerability scanning and patch management.
- Documentation of all security policies in the compliance register linked to each functional requirement.
# Business Vision (Overview)

## Business Vision and High-Level Objectives

**Vision**
The PatientIntake project will deliver a fully HIPAA‑compliant, open‑source patient intake platform that captures demographics, insurance information, and comprehensive medical history through a secure web form. The solution will be deployable on‑premises via Docker‑Compose, operate without any external cloud services, and provide immutable audit logs and tamper‑evident PDF summaries.

**High‑Level Objectives**
1. **Regulatory Assurance** – Achieve continuous compliance with HIPAA Security Rule §§164.312(a)(1), (a)(2)(iv), and (e)(1) through encryption, access controls, and audit logging.
2. **Operational Efficiency** – Reduce manual data‑entry time by at least 40 % compared with legacy paper processes.
3. **Data Integrity & Traceability** – Ensure 100 % of read/write/export actions are captured in an immutable audit log retained for seven years.
4. **Open‑Source Sustainability** – Build exclusively with community‑maintained components (PostgreSQL, Nginx, React, etc.) to avoid vendor lock‑in and keep total cost of ownership low.
5. **Testability & Quality** – Provide a comprehensive automated test suite covering form validation, encryption handling, and role‑based access control.

---

## Stakeholder Roles and Access Requirements

| Stakeholder | Role ID | Primary Business Need | Pain Point Addressed | RBAC Tier | Strategic Objective Supported |
|--------------|----------|-----------------------|---------------------|----------|------------------------------|
| Patient | ST-02 | Submit accurate demographic, insurance, and medical history data securely | Fear of PHI exposure during transmission or storage | Create‑only (encrypted submissions) | OBJ-001: Achieve 100 % encrypted data capture at rest and in transit |
| Front‑Desk Staff | ST-01 | Register patients quickly and verify insurance eligibility | Manual re‑entry of data leads to errors and delays | Read‑only access to submissions; flag incomplete records | OBJ-002: Reduce intake processing time by 30 % |
| Clinician | ST-03 | Review complete medical history to inform care decisions | Need timely access while preserving auditability | Read‑write access with edit logs captured | OBJ-003: Ensure 99 % of record accesses are logged immutably |
| Administrator | ST-04 | Configure system settings, manage user accounts, oversee audit logs | Must balance security hardening with operational continuity | Full admin privileges including user provisioning and log retention policy management | OBJ-004: Maintain audit log retention of 7 years on immutable storage |
| Compliance Officer | ST-05 | Verify that all processes meet HIPAA and internal policy requirements | Requires evidence of encryption key lifecycle and access logs | Read‑only access to audit logs and configuration change history | OBJ-005: Pass quarterly compliance audit with zero critical findings |

---

## Access Control Summary

- **Encryption at Rest** – All PHI fields are encrypted using AES‑256 before persisting to PostgreSQL.
- **Encryption in Transit** – TLS 1.3 with perfect forward secrecy is mandated for every client‑server interaction.
- **Audit Logging** – Every read, write, configuration change, and PDF export generates an immutable log entry retained for seven years.
- **Least‑Privilege Principle** – RBAC tiers are aligned exactly with the needs described above; no role receives broader permissions than required.

---

## Business Rationale

Providing each stakeholder with precisely the access required reduces the attack surface while supporting operational efficiency. Patients retain confidence that their data cannot be viewed by unauthorized parties. Front‑desk staff can complete intake without exposing PHI beyond what is necessary for verification. Clinicians obtain the full record needed for care delivery, yet every modification is traceable. Administrators maintain system integrity, and compliance officers have the evidence needed for regulatory reporting. This alignment directly supports the project's strategic objectives of HIPAA compliance, open‑source cost containment, and rapid on‑prem deployment.

---

## Purpose and Strategic Objectives

1. **Regulatory Assurance** – Achieve and maintain compliance with HIPAA Security Rule §§164.312(a)(1), (a)(2)(iv), (e)(1) and related state privacy statutes.
2. **Operational Efficiency** – Reduce manual data entry time by at least 40 % compared with paper‑based intake processes.
3. **Data Integrity & Auditability** – Provide immutable audit logs for every read/write operation and every PDF export.
4. **Open‑Source Sustainability** – Build the solution exclusively on open‑source components to avoid vendor lock‑in and control total cost of ownership.
5. **Testability & Quality** – Embed automated unit and integration tests covering form validation, encryption handling, and role‑based access control.

---

## Scope Definition

### In‑Scope
- Structured web form with field‑level AES‑256 encryption for data at rest and TLS 1.3 in transit.
- Local PostgreSQL database employing role‑based access control (admin, clinician, front‑desk).
- Full immutable audit log retained for a minimum of seven years.
- PDF intake summary generation with staff watermark and export timestamp.
- Automated test suite (unit + integration) covering validation, encryption, RBAC edge cases.
- Docker‑Compose deployment scripts for air‑gapped environments including a step‑by‑step installation guide.

## Success Metrics & KPIs

| KPI ID | Metric Description | Target | Measurement Method |
|--------|----------------------|--------|-------------------|
| KPI-01 | Form Completion Rate | ≥ 90 % of patients complete the web form without assistance | Weekly submission analytics from application logs |
| KPI-02 | Audit Log Coverage | 100 % of read/write/export actions logged | Log aggregation dashboard verifying event capture |
| KPI-03 | PDF Export Accuracy | Zero mismatches between stored data and generated PDF (checksum validation) |
| KPI-04 | Deployment Success in Air‑Gap Lab | First successful Docker‑Compose spin‑up within 30 minutes |

---

## Risk Assessment & Mitigations

| Risk ID | Description | Likelihood / Impact | Mitigation Action |
|---------|-------------|----------------------|-------------------|
| RISK-01 | Unauthorized data exposure during transmission | High / High | Enforce TLS 1.3 with perfect forward secrecy; conduct quarterly penetration testing; implement strict cipher suite whitelist |
| RISK-02 | Open‑source component vulnerabilities | Medium / Medium | Deploy OWASP Dependency‑Check CI pipeline; schedule monthly vulnerability review; apply rapid patching process for critical CVEs |
| RISK-03 | Misconfiguration of role‑based access controls leading to over‑privileged users | Low / High | Conduct RBAC review workshops; automate policy linting using Open Policy Agent; enforce least‑privilege via scripted provisioning |
| RISK-04 | Audit log tampering or loss | Low / High | Store logs on write‑once immutable storage; chain log entries using cryptographic hash chaining; perform weekly integrity verification |
| RISK-05 | Insufficient documentation for air‑gap deployment causing rollout delays | Medium / Medium | Produce step‑by‑step installation guide; include verification checklist; run a mock deployment in a controlled lab before production |

---

## Governance & Ownership

| Role | Responsibility |
|------|----------------|
| Project Sponsor | Budget approval and regulatory sign‑off |
| Product Owner (Clinical Lead) | Prioritization of functional requirements (FR‑001 – FR‑003) |
| Security Lead | Verification of HIPAA safeguards (NFR‑001 – NFR‑003) and periodic risk assessments |
| DevOps Lead | Air‑gap deployment validation, Docker‑Compose orchestration, dependency scanning |
| Compliance Officer (ST‑05) | Quarterly audit preparation, review of audit log retention policy |

Quarterly governance reviews will assess KPI attainment, risk mitigation effectiveness, and alignment with strategic objectives.
# HIPAA Compliance Requirements

### 1. Strategic Vision
The PatientIntake system will enable clinics to capture complete patient demographics, insurance information, and medical history through a secure web form while guaranteeing full compliance with the HIPAA Security Rule. The solution will be built exclusively with open-source components to avoid vendor lock-in, reduce licensing costs, and ensure that the codebase can be audited by internal security teams. Success will be measured by achieving a 95% form completion rate within 2 minutes and a 99.9% system availability during business hours, as recorded by the PostgreSQL monitoring dashboard.

### 2. Regulatory Alignment
All data handling will satisfy the technical safeguards of 45 CFR § 164.312(a)(2)(iv) by encrypting each PHI field at rest using AES-256 and protecting data in transit with TLS 1.3. Encryption keys will be rotated every 90 days and logged in an immutable audit trail (REQ-003). The system also meets the audit-log retention requirement of 7 years (REQ-004) and will generate immutable log entries for every read, write, update, and delete operation (FR-004). Compliance will be validated through quarterly internal audits and an external third-party assessment. The solution also complies with §164.312(e)(1) and §164.308(a)(1) technical safeguards.

#### Stakeholder Needs and Responsibilities
- ST-01 – Patient: Need secure collection of PHI; Concern unauthorized disclosure; Responsibility provide accurate data and consent per HIPAA §164.508. Acceptance Criterion (REQ-001): All patient-submitted fields are encrypted at rest using AES-256; verification via automated scan.
- ST-02 – Front-Desk Staff: Need efficient data entry workflow; Concern accidental exposure; Responsibility use role-based access limited to \"front-desk\" role; Acceptance Criterion (REQ-002): System logs every create/update action with immutable audit log retained for 7 years (HIPAA §164.310).
- ST-03 – Clinician: Need immediate access to complete intake data; Concern delayed data; Responsibility read-only access, MFA per HIPAA §164.312(d). Acceptance Criterion (REQ-003): Access latency <200 ms for 95 % of reads; MFA enforced.
- ST-04 – System Administrator: Need maintain availability and security patches; Concern downtime; Responsibility apply patches within 30 days, enforce TLS 1.3 for all traffic (HIPAA §164.312(e)(1)). Acceptance Criterion (NFR-001): System uptime ≥99.9 %; all external connections use TLS 1.3.
- ST-05 – Compliance Officer: Need oversight of policy adherence; Concern inadequate documentation; Responsibility review audit logs quarterly, ensure key-rotation every 90 days, maintain incident response plan. Acceptance Criterion (REQ-004): Keys rotated quarterly with logged events; incident response drill semi-annually.

### 5. KPIs and Success Criteria
- KPI-01: 100 % of PHI fields encrypted at rest using AES-256. Measured monthly by scanning database columns.
- KPI-02: TLS 1.3 enforced for all inbound/outbound traffic. Measured weekly; acceptance 0 % connections below TLS 1.2.
- KPI-03: RBAC compliance ≥ 99.5 %. Quarterly permission audit against matrix.
- KPI-04: Audit log completeness ≥ 99.9 %. Log integrity checks for every transaction.
- KPI-05: Audit log retention 7 years immutable. Annual verification.
- KPI-06: Average form submission response time ≤ 200 ms (p95). Synthetic load testing.
- KPI-07: System uptime ≥ 99.9 % per month. Monitoring alerts.
- KPI-08: PDF generation time ≤ 1.5 s per request.
- KPI-09: Form completion rate ≥ 90 %.
- KPI-10: User satisfaction score ≥ 4.2/5.
- KPI-11: Annual HIPAA Security Risk Analysis completed and approved.
- KPI-12: Zero high-severity findings in external penetration test.

### 6. Governance Model
Structure (GOV-001): Compliance Steering Committee chaired by CISO, includes Compliance Officer, Lead Clinician, Front-Desk Manager, IT Operations Lead. Meets monthly.
Roles & Responsibilities (GOV-002):
- Compliance Officer (ST-04): Author HIPAA Compliance Charter, ensure alignment with 45 CFR §164.
- CISO (ST-03): Oversee key management, approve AES-256 GCM, sign off audit-log retention.
- Clinician (ST-02): Access records via RBAC, log all actions.
- Front-Desk Staff (ST-01): Capture intake data, enforce TLS 1.3.
- IT Operations Lead (ST-03): Maintain Docker-Compose, immutable storage, patch within 30 days.
Compliance Monitoring (GOV-003): Nightly audit-log review, weekly encryption validation, quarterly access control audit. Acceptance criteria ensure 100 % entries contain user-ID, timestamp, operation type; key rotation logged; excess privileges remediated within 5 business days.<br>Incident Response (GOV-004): Detection within 15 minutes, containment, investigation, notification per HIPAA §164.404., recovery, post-mortem. All incidents closed within defined SLAs.<br>Review Schedule (GOV-005): Quarterly risk-assessment update, annual external HIPAA audit (pass ≥ 95 %), biannual penetration test.<br>Reporting (GOV-006): Compliance Dashboard (Grafana) showing encryption-key age, audit-log volume, incident count, SLA compliance.<br>Training (GOV-007): Quarterly HIPAA training, 100 % completion within 30 days; semiannual phishing simulation.<br>Metrics & KPIs (GOV-008): Encryption key age ≤ 90 days, audit-log retention 7 years, incident closure ≤ 10 days, training completion ≥ 99 %, vulnerability remediation ≤ 30 days for CVSS ≥ 7.0.<br>

### 7. References
- 45 CFR §164.312, §164.308, §164.404, §164.310, §164.312(a)(2)(iv), §164.312(e)(1).
- NIST SP 800-53 controls aligned with technical safeguards.<n - WCAG 2.1 AA for accessibility of web form.

## Business Requirements
| ID | Description | Acceptance Criteria |
|----|-------------|----------------------|
| REQ-001 | All PHI fields must be encrypted at rest using AES‑256. | Automated scan confirms 100 % encryption of PHI columns. |
| REQ-002 | Data in transit must be protected with TLS 1.3. | No connections below TLS 1.2; SSL Labs grade A. |
| REQ-003 | Encryption keys must be rotated every 90 days and logged. | Immutable audit log shows key rotation events within 90‑day window. |
| REQ-004 | Every read/write/update/delete operation must generate an immutable audit log entry. | Log contains user‑ID, timestamp, operation type; retention ≥7 years. |
| REQ-005 | PDF summary generation must include watermark and export timestamp, accessible only to authorized staff. | PDF contains visible watermark text and timestamp; access logged. |
| REQ-006 | Automated unit and integration tests must cover form validation, encryption, and RBAC edge cases. | Test suite achieves ≥90 % code coverage and passes CI pipeline. |
| REQ-007 | Deployment must be performed via Docker Compose on‑premises with no external cloud dependencies. | Docker Compose up brings up all containers; air‑gap guide validated. |

## Risk Register
| ID | Description | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| RISK-001 | Unauthorized disclosure due to weak key management | Medium | High | Automated key rotation using HashiCorp Vault; AES-256 encryption; audit logs of key usage (aligns with REQ-003). |
| RISK-002 | Interception in transit due to misconfigured TLS | Low | High | Enforce TLS 1.3 with strong cipher suites; regular SSL Labs scans; compliance with §164.312(a)(2)(iv). |
| RISK-003 | Service outage from container orchestration failure | Medium | Medium | Docker-Compose health checks, systemd watchdog, hot-standby replica; monitor uptime (NFR-001). |
| RISK-004 | Data loss from insufficient backup retention | Low | High | Encrypted offline backups retained 7 years per HIPAA (REQ-004). |
| RISK-005 | Unauthorized software via removable media | Medium | Medium | Media control policy, SHA-256 verification, immutable audit logging (FR-004). |
| RISK-006 | Inadequate patch management | High | Medium | Dependabot alerts, monthly rebuilds, Trivy scans; patches applied within 30 days. |
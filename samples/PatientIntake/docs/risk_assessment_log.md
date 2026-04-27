# Risk Assessment Log

## System Architecture Vision for HIPAA-Compliant Patient Intake System

1. Overview
The PatientIntake solution will be delivered as a containerized web application hosted on-premises using Docker Compose. The architecture follows a three‑tier model: a static HTML/JavaScript front‑end, a Python Flask back‑end that performs field‑level encryption, role‑based access control, and audit logging, and a PostgreSQL database that stores encrypted patient records. All network traffic will be protected with TLS 1.3, and at‑rest data will be encrypted with AES‑256 using the open‑source cryptography library. The design is intentionally open‑source only to avoid vendor lock‑in and satisfy the project constraint.

2. Functional Scope
FR-001: Collect patient demographics, insurance information, and medical history via a structured web form. Acceptance: Form submission creates a record with all fields encrypted before persisting; 100 % of required fields must be present. Minimum 95 % successful submission rate measured over 30‑day pilot (V2). (Traceability: REQ-001)
FR-002: Enforce role‑based access control (admin, clinician, front‑desk). Acceptance: Access matrix verified by automated tests; no role can read or modify records outside its permission set. Admin can view/edit all records; Clinician can view and update clinical fields only; Front‑Desk can create new records and view demographic fields but cannot access medical history (V2). (Traceability: REQ-002)
FR-003: Generate a PDF intake summary per patient with a visible watermark and export timestamp. Acceptance: PDF contains watermark text \"Confidential – PatientIntake\" and timestamp metadata; only authorized roles can trigger export. PDF generated within 2 seconds 95 % of requests (KPI‑03). (Traceability: REQ-003)
FR-004: Maintain an immutable audit log for every read and write operation. Acceptance: Log entry includes user ID, timestamp, operation type, and record identifier; log retention is 7 years. Log entries must include ISO‑8601 UTC timestamp, user ID, role, operation type, and record identifier (V2). Log retention verified quarterly. (Traceability: REQ-004)
FR-005: Generate an immutable audit log entry for every create, read, update, delete (CRUD) operation. Acceptance: Same as FR‑004 (V2). (Traceability: REQ-005)

3. Non‑Functional Requirements
NFR-001: Response time <200 ms (p95) for form load and submission under typical load (≤50 concurrent users) (V1) and ≤200 ms under load of 100 concurrent users (V2). Measured by JMeter. (Traceability: REQ-006)
NFR-002: System availability ≥99.9 % monthly, monitored via Prometheus alerts (V1) and measured by monitoring tool (V2). (Traceability: REQ-007)
NFR-003: Encryption at rest must meet AES‑256 (FIPS‑140‑2 Level 1) compliance; verified by OpenSSL test vectors (V1). Data at rest encryption must meet HIPAA §164.312(a)(2)(iv) using AES‑256 with per‑field keys rotated every 90 days (V2). (Traceability: REQ-008)
NFR-004: Transport security must use TLS 1.3 with certificates signed by an internal CA; compliance checked against HIPAA §164.312(e)(1) (V1) and forward secrecy requirement (V2). All HTTP endpoints must present valid certificate; SSL Labs A rating. (Traceability: REQ-009)
NFR-005: Audit log storage must be append‑only and tamper‑evident, using write‑once file system or blockchain‑style hash chaining (V2). Stored in append‑only PostgreSQL tables with row‑level security and replicated to MinIO WORM mode (RISK‑003). Retention period ≥7 years. (Traceability: REQ-010)

4. Stakeholder Roles
ST-01 (Patient): Needs assurance that personal health information is protected and that the intake process is quick. Motivation: privacy and convenience. Compliance: rights per HIPAA §164.522.
ST-02 (Front‑Desk Staff): Requires fast data entry and clear error feedback. Motivation: efficiency and accuracy. Can create and update intake records but cannot view PHI beyond entered data. Success metric: Form completion rate >90 % and validation error rate <2 %. (Traceability: REQ-011)
ST-03 (Clinician): Needs reliable access to complete medical histories for care decisions. Motivation: clinical effectiveness. Read‑only access to patient records; can add clinical notes. Success metric: Average time from submission to clinician view <2 minutes. (Traceability: REQ-012)
ST-04 (Administrator): Oversees system configuration, user provisioning, and compliance reporting. Motivation: governance and auditability. Must implement key rotation every 90 days per HIPAA §164.308(a)(1)(ii) and retain logs 7 years (§164.310).
ST-05 (Compliance Officer): Must verify that all technical safeguards satisfy HIPAA and internal policies. Motivation: regulatory adherence. Conducts annual risk analysis per §164.308(a)(1)(ii) and ensures documentation is up‑to‑date.

5. Risk Assessment Summary
RISK-01: Data breach due to key compromise. Likelihood: Medium (M). Impact: High (H). Mitigation: Automated key rotation every 90 days using HashiCorp Vault and audit of key usage. Deploy TLS 1.3 for all inbound traffic (HIPAA §164.312(e)(1)). Strict RBAC. Quarterly penetration testing using OWASP ZAP. No critical findings in pen‑test report.
RISK-02: Audit‑log tampering. Likelihood: Low (L). Impact: High (H). Mitigation: Write‑once immutable log storage with cryptographic hash chaining; periodic hash verification. Store logs in append‑only PostgreSQL tables and replicate to MinIO WORM. Sign each entry with HMAC‑SHA256. Integrity check reports 0 % mismatched signatures weekly.
RISK-03: Deployment failure in air‑gap environment. Likelihood: Medium (M). Impact: Medium (M). Mitigation: Docker Compose version‑pinned images, offline image registry, documented offline installation script. Deploy on air‑gapped servers with no external NICs, host‑based firewall blocks outbound traffic. Bi‑annual network scans show 0 open outbound ports.
RISK-04: Encryption key management – Key Rotation Failure. Likelihood: Low (L). Impact: High (H). Mitigation: Use HashiCorp Vault to store AES‑256 keys, rotate every 90 days, log each rotation event in immutable audit log. No key reuse detected in 12 months.
RISK-05: Compliance Gaps – Incomplete HIPAA Controls. Likelihood: Medium (M). Impact: High (H). Mitigation: Map each requirement to HIPAA Security Rule sections, perform annual internal audit using NIST SP 800‑53, assign Compliance Officer to sign‑off. 100 % controls documented, external audit reports "Compliant".

6. Success Criteria & KPIs
KPI-01: Form completion rate ≥90 % measured by weekly submission counts (V1) and analytics (KPI‑05). Success metric: 90 % of sessions where users reach final submission page.
KPI-02: 100 % of PDF exports contain correct watermark and timestamp, verified by automated checksum test (V1) and response time ≤2 seconds 95 % of requests (KPI‑03).
KPI-03: Audit‑log completeness ≥99.9 % (no missing entries) verified by nightly log integrity job (V1) and 99.9 % of transactions have corresponding audit entries (KPI‑02).
KPI-04: System uptime ≥99.9 % measured by Prometheus (V1) and monitoring tool (V2).
KPI-05: Encryption compliance – 100 % of stored PHI fields encrypted with AES‑256‑GCM, verified by nightly OpenSCAP scan (KPI‑01 in Version 5).
KPI-06: Key management rotation – 100 % of keys rotated on schedule, rotation events logged (KPI‑06).
KPI-07: Open‑source dependency health – No critical CVE in dependency tree, weekly OWASP Dependency‑Check reports 0 critical findings (KPI‑07).

### FR-001: Collect patient demographics, insurance information, and medical history via a structured web form.
- Acceptance: Form submission creates a record with all fields encrypted before persisting; 100% of required fields must be present. Form completion rate ≥90%.

### FR-002: Enforce role‑based access control (admin, clinician, front‑desk).
- Acceptance: Access matrix verified by automated tests; no role can read or modify records outside its permission set.

### FR-004: Maintain an immutable audit log for every read and write operation.
- Acceptance: Log entry includes user ID, timestamp, operation type, record identifier; retention ≥7 years; completeness ≥99.9%.

### FR-005: Deploy via Docker Compose on‑premises with no external cloud dependencies.
- Acceptance: `docker compose up` brings up all containers; deployment documented for air‑gap setup.

### RISK-01: Data breach due to key compromise.
- Likelihood: Medium; Impact: High.
- Mitigation: Automated key rotation every 90 days using HashiCorp Vault; TLS 1.3 for all inbound traffic; strict RBAC; quarterly penetration testing.

### RISK-02: Audit‑log tampering.
- Likelihood: Low; Impact: High.
- Mitigation: Write‑once immutable log storage with cryptographic hash chaining; HMAC‑SHA256 signing; weekly integrity verification.

### RISK-03: Deployment failure in air‑gap environment.
- Likelihood: Medium; Impact: Medium.
- Mitigation: Version‑pinned Docker images, offline image registry, documented offline installation script; network firewall blocks outbound traffic; bi‑annual network scans.

### RISK-04: Encryption key management failure.
- Likelihood: Low; Impact: High.
- Mitigation: HashiCorp Vault integration, automated rotation alerts, audit log of rotation events.

### RISK-05: Compliance gaps.
- Likelihood: Medium; Impact: High.
- Mitigation: Map each requirement to HIPAA Security Rule sections; annual internal audit using NIST SP 800‑53; compliance officer sign‑off; 100% controls documented.

## Success Criteria & KPIs
- **KPI-01** Form completion rate ≥90%.
- **KPI-02** 100% of PDF exports contain correct watermark and timestamp; export latency ≤2 seconds for 95% of requests.
- **KPI-03** Audit‑log completeness ≥99.9%.
- **KPI-04** System uptime ≥99.9%.
- **KPI-05** Encryption compliance: 100% of stored PHI fields encrypted with AES‑256‑GCM.
- **KPI-06** Key rotation on schedule with logged events.
- **KPI-07** No critical CVEs in open‑source dependencies.

## Stakeholder Needs and Ownership
- **ST-01 Patient**: Assurance of privacy and quick intake experience. Owner: Compliance Officer.
- **ST-02 Front‑Desk Staff**: Efficient data entry with validation feedback. Owner: Operations Manager.
- **ST-03 Clinician**: Immediate access to complete medical history for care decisions. Owner: Clinical Lead.
- **ST-04 Administrator**: System configuration, user provisioning, auditability. Owner: IT Administrator.
- **ST-05 Compliance Officer**: Verify technical safeguards meet HIPAA. Owner: Compliance Officer.

## Business Requirements (Traceability)
| ID | Requirement | Acceptance Criteria | Owner |
|----|-------------|-------------------|-------|
| FR-001 | Collect patient demographics, insurance, medical history via structured web form | Form submission creates encrypted record; 100% required fields present; ≥95% successful submission rate in pilot | Front‑Desk Staff |
| FR-002 | Role‑based access control (admin, clinician, front‑desk) | Access matrix verified by automated tests; no unauthorized reads/writes | Administrator |
| FR-003 | Generate PDF intake summary with watermark and export timestamp | PDF contains watermark \"Confidential – PatientIntake\" and timestamp; export ≤2 s for 95% of requests | Clinician |
| FR-004 | Immutable audit log for every read/write operation | Log entry includes user ID, timestamp, operation type, record ID; retention ≥7 years; completeness ≥99.9% | Administrator |
| FR-005 | Authorized staff can export PDF with watermark | Export function restricted to authorized roles; PDF includes visible watermark and timestamp metadata | Clinician |
| NFR-001 | Response time <200 ms for form load/submission under typical load | Measured by JMeter; p95 ≤200 ms for ≤50 concurrent users | Technical Lead |
| NFR-002 | System availability ≥99.9% monthly | Monitored via Prometheus alerts; uptime logs | Operations |
| NFR-003 | Data at rest encryption AES‑256 meeting FIPS‑140‑2 Level 1 | Verified by OpenSSL test vectors; key rotation every 90 days logged | Security Engineer |
| NFR-004 | Transport security TLS 1.3 with internal CA | SSL Labs A rating; forward secrecy validated | Security Engineer |
| NFR-005 | Append‑only tamper‑evident audit log storage | Write‑once PostgreSQL tables, MinIO WORM replication; hash chaining verification weekly | Security Engineer |

## Risks and Mitigations (Enhanced)
- **RISK-01 Data breach due to key compromise**: Implement automated key rotation every 90 days using HashiCorp Vault; enforce TLS 1.3; conduct quarterly penetration testing.
- **RISK-02 Audit‑log tampering**: Store logs in append‑only tables with cryptographic hash chaining; replicate to immutable object storage; run weekly integrity verification scripts.
- **RISK-03 Deployment failure in air‑gap environment**: Use version‑pinned Docker images stored in offline registry; provide offline installation scripts and air‑gap network configuration guide.
- **RISK-04 Encryption key management failure**: Monitor Vault rotation jobs; alert on failures; maintain audit trail of each rotation event.
- **RISK-05 Compliance gaps**: Map each requirement to HIPAA Security Rule sections; perform annual internal audit using NIST SP 800‑53 controls; obtain external compliance certification.

## Summary
The refined architecture aligns technical scope with a clear business vision, provides explicit traceability to all functional and non‑functional requirements, and strengthens risk mitigations with concrete actions. This artifact is ready for downstream design and implementation phases.

## Governance
- Quarterly review by Compliance Officer.
- Monthly performance monitoring to ensure response time <200 ms (NFR‑001).
- Annual security risk analysis updated (REQ‑007).
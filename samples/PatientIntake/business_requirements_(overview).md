# Business Requirements (Overview)

# Business Requirements (Overview)

## Business Requirements Overview

Purpose and Value Proposition
The PatientIntake system will provide a secure, open-source web-based solution for capturing patient demographics, insurance information, and medical history at the point of entry. By encrypting data at field level both in transit (TLS 1.3) and at rest (AES-256), the system ensures compliance with HIPAA §164.312(a)(2)(iv) and protects Protected Health Information (PHI) from unauthorized disclosure. The open-source stack eliminates licensing costs, enables full auditability, and supports on-premise deployment in air-gapped environments, aligning with the organization’s strategic goal of maintaining data sovereignty while improving intake efficiency.

Strategic Objectives
- Regulatory Compliance: Achieve full HIPAA compliance for data collection, storage, and export, verified by an external audit within the first quarter after release.
- Operational Efficiency: Reduce average patient intake time from 12 minutes to under 5 minutes, measured by timestamped form submissions logged in PostgreSQL.
- Cost Containment: Deploy using only open-source components (React, Node.js, PostgreSQL, Docker) to keep total cost of ownership below $15,000 per year for a 100-bed facility.

Scope Definition
- In-Scope: Secure web form, role-based access control (admin, clinician, front-desk), immutable audit log, PDF summary generation with watermark and timestamp, automated unit/integration test suite, Docker-Compose deployment, air-gap installation guide.
- Out-of-Scope: Integration with external Electronic Health Record (EHR) systems, mobile-native applications, cloud-based hosting, advanced analytics dashboards.

Functional Requirements
- FR-001: The system shall present a responsive web form that captures required fields (name, DOB, address, insurance policy, medical history) and validates input formats. Acceptance: 100% of mandatory fields must be completed before submission; validation errors displayed inline. Owner: Front-Desk Staff.
- FR-002: All PHI fields shall be encrypted at rest using AES-256 with per-field keys managed by a hardware security module (HSM) or software-based key vault. Acceptance: Database dump inspected with a cryptographic tool shows ciphertext for each PHI column. Owner: System Administrator.
- FR-003: Data transmission shall use TLS 1.3 with forward secrecy. Acceptance: Network capture using Wireshark shows only encrypted packets; no plaintext PHI observed. Owner: System Administrator.
- FR-004: Role-based access control shall restrict read/write permissions: admins full access, clinicians read-only for assigned patients, front-desk staff create and edit only non-clinical fields. Acceptance: Access matrix tests confirm each role can perform only permitted actions. Owner: Compliance Officer.
- FR-005: Every read and write operation shall be recorded in an immutable audit log with timestamp, user ID, operation type, and affected record ID. Acceptance: Log entries persisted for at least 7 years and verified for tamper-evidence using hash chaining. Owner: Compliance Officer.
- FR-006: Authorized staff may generate a PDF intake summary that includes a dynamic watermark ("Confidential – Authorized Export") and an export timestamp. Acceptance: PDF contains watermark on each page and metadata field "Exported-At". Owner: Front-Desk Staff.

Non-Functional Requirements
- NFR-001: System availability ≥ 99.9% monthly uptime, measured by monitoring container health checks. Owner: IT Administrator.
- NFR-002: Form submission latency ≤ 200 ms (p95) measured from client request to server acknowledgment. Owner: IT Administrator.
- NFR-003: Audit log retention period ≥ 7 years, stored in append-only storage. Owner: Compliance Officer.
- NFR-004: PDF generation time ≤ 1 second for average record size (≈ 250 KB). Owner: Front-Desk Staff.
- NFR-005: All open-source components shall be maintained with security patches applied within 30 days of CVE release. Owner: IT Administrator.

Stakeholder Analysis
- ST-01 – Patients: Need assurance that personal health data is protected; benefit: trust in secure intake process. Owner: Compliance Officer.
- ST-02 – Front-Desk Staff: Require fast, error-free data entry; benefit: reduced intake time and fewer transcription errors. Owner: Front-Desk Manager.
- ST-03 – Clinicians: Need reliable, read-only access to accurate patient histories; benefit: immediate access to complete, verified data. Owner: Clinical Lead.
- ST-04 – Compliance Officer: Must verify HIPAA safeguards; benefit: full immutable audit log and encryption proof. Owner: Compliance Officer.
- ST-05 – IT Administrator: Responsible for deployment and maintenance; benefit: Docker-Compose orchestration and open-source stack simplify on-prem management. Owner: IT Administrator.

Risk Assessment and Mitigations
- RISK-001 (High likelihood, High impact): Misconfiguration of encryption keys leading to PHI exposure. Mitigation: Automated key‑rotation scripts executed quarterly, HSM integration verification checklist, and quarterly key-management audit with documented findings.
- RISK-002 (Medium likelihood, High impact): Unauthorized access due to RBAC rule errors. Mitigation: Role-based access matrix testing in CI pipeline for every release, continuous integration of security tests, and semi‑annual penetration testing report.
- RISK-003 (Low likelihood, Medium impact): Audit-log tampering. Mitigation: Append-only log storage with cryptographic hash chaining and write-once-read-many (WORM) backup verified monthly.
- RISK‑004 (Medium likelihood, Medium impact): Performance degradation under peak load. Mitigation: Load testing to 200 concurrent users, auto-scaling of Docker containers based on CPU thresholds, and database indexing of audit tables with monthly performance review.

Success Criteria / KPIs
- KPI‑001: Form completion rate ≥ 90% of scheduled patients, measured weekly from submission counts. Owner: Front-Desk Manager.
- KPI‑002: Average intake time ≤ 5 minutes per patient, measured by timestamps in the audit log. Owner: Clinical Lead.
- KPI‑003: 100% of PHI encrypted at rest, verified by quarterly security scans. Owner: System Administrator.
- KPI‑004: Zero HIPAA-related security incidents in the first 12 months post-deployment. Owner: Compliance Officer.
- KPI‑005: Deployment time ≤ 2 hours for a new site using the air-gap guide, validated by a pilot installation. Owner: IT Administrator.

Governance and Review
- A cross-functional steering committee (Compliance, IT, Clinical) will review quarterly metrics and audit logs.
- Change-control procedures require sign-off from the Compliance Officer for any modification to encryption or RBAC policies.
- Documentation of all decisions, test results, and audit logs will be stored in a version-controlled repository accessible to auditors.

## Stakeholder Expectations

- **ST-01 (Patient)**
  - Expectations: Assurance that personal health information is protected and used only for care.
  - Motivation: Faster intake, reduced paperwork, and trust in digital form.
  - RBAC Tier: No system access; data is captured via encrypted web form.
- **ST-02 (Front‑Desk Staff)**
  - Expectations: Quick data entry with minimal training and clear guidance.
  - Motivation: Efficient patient check‑in without security steps slowing workflow.
  - RBAC Tier: Data entry role with permission to create records but read‑only on clinical fields.
- **ST-03 (Clinician)**
  - Expectations: Immediate access to complete, accurate patient data for diagnosis and treatment.
  - Motivation: Accurate care delivery.
  - RBAC Tier: Full read/write on clinical fields, read‑only on audit logs.
- **ST-04 (Administrator)**
  - Expectations: Ensure HIPAA compliance, system uptime, and proper configuration.
  - Motivation: Avoid regulatory penalties and protect reputation.
  - RBAC Tier: Admin privileges across all modules, including encryption library configuration.
- **ST-05 (Compliance Officer)**
  - Expectations: Real‑time audit‑log export, monthly compliance reports, verification that all data at rest uses AES‑256 encryption.
  - Motivation: Demonstrate adherence to HIPAA Security Rule and prepare for external audits.
  - RBAC Tier: Read‑only access to audit logs and configuration settings; cannot modify patient data.
- **ST-06 (Insurance Provider)**
  - Expectations: Secure API‑style data feed (out‑of‑scope for this phase) and confirmation that patient consent has been captured and stored.
  - Motivation: Accurate billing and eligibility verification while respecting privacy.
  - RBAC Tier: No direct system access; receives data extracts under a signed data‑use agreement.
- **ST-07 (Regulatory Auditor)**
  - Expectations: Ability to review a snapshot of the system's audit logs and encryption configurations during scheduled audits, with logs retained for a minimum of 7 years.
  - Motivation: Verify that the organization meets all HIPAA technical and administrative safeguards.
  - RBAC Tier: Read‑only, time‑bounded access to audit‑log archives; no edit rights.

## Risks and Mitigations
- **RISK-01 (High)**: Encryption key compromise.
  - Likelihood: Medium, Impact: High.
  - Mitigation: Use HashiCorp Vault with sealed secrets, rotate keys quarterly, enforce MFA for admin access, audit all key retrieval events.
- **RISK-02 (Medium)**: Unauthorized data access due to misconfigured RBAC.
  - Likelihood: Medium, Impact: High.
  - Mitigation: Automated RBAC policy validation scripts run on each deployment, periodic penetration testing, row‑level security policies in PostgreSQL, dual‑approval for role changes.
- **RISK-03 (Medium)**: Audit log tampering.
  - Likelihood: Low, Impact: High.
  - Mitigation: Store logs in append‑only WORM storage, enable cryptographic hash chaining for each entry, partition logs by month and archive older than 7 years to compressed files.
- **RISK-04 (Low)**: PDF generation leakage.
  - Likelihood: Low, Impact: High.
  - Mitigation: Integrate wkhtmltopdf with mandatory watermark overlay containing patient ID, export timestamp, authorized staff role; enforce access check before PDF generation.
- **RISK-05 (Medium)**: Docker Compose misconfiguration in air‑gap environment.
  - Likelihood: Medium, Impact: Medium.
  - Mitigation: Provide offline Docker images with signed SHA256 checksums, detailed offline installation guide, script to verify image integrity before deployment.

## Success Criteria / KPIs
- **KPI-01**: Form completion rate ≥95% measured by weekly submission counts.
- **KPI-02**: Encryption compliance score ≥98% on quarterly security audit.
- **KPI-03**: Average form submission latency ≤150 ms (p95) under load.
- **KPI-04**: Zero HIPAA violations reported in annual compliance audit.
- **KPI-05**: Deployment time for new on‑prem environment ≤2 hours using provided Docker Compose bundle.

## Risk Register

**RISK-005: Network Configuration Exposure**
- Likelihood: Medium
- Impact: Medium
- Description: Improper network settings may unintentionally expose containers to external networks, breaching the air‑gap requirement.
- Mitigation: Define Docker Compose with `network_mode: none` for non‑essential services, apply host‑only firewall rules, and validate configuration with an automated compliance script before deployment.

**RISK-006: Open‑Source Component Vulnerabilities**
- Likelihood: High
- Impact: High
- Description: Dependencies such as OpenSSL, PostgreSQL, or PDF libraries may have known CVEs that could be exploited.
- Mitigation: Adopt a continuous vulnerability scanning pipeline (e.g., Trivy), enforce monthly patch updates, maintain a bill of materials (BOM) with version pins, and remediate critical findings within 30 days.

**Risk Evaluation Summary**
All identified risks are scored using a qualitative matrix (Likelihood × Impact) and prioritized for mitigation. The mitigation actions are measurable, with key performance indicators (KPIs):
- KPI‑R1: 100 % of encryption keys rotated within 90 days (measured by Vault audit logs).
- KPI‑R2: Zero unauthorized access incidents per quarter (measured by audit log alerts).
- KPI‑R3: Audit log storage utilization <80 % of allocated capacity (monitored weekly).
- KPI‑R4: PDF export includes watermark and timestamp in 100 % of cases (validated by automated UI test).
- KPI‑R5: Docker Compose passes air‑gap compliance script 100 % of deployments.
- KPI‑R6: No critical CVEs unaddressed for >30 days (tracked by scanning reports).

By implementing the above mitigations, the PatientIntake system aligns with HIPAA technical safeguard requirements, ensures data security, and maintains operational continuity in on‑premise, air‑gap environments.

## Business Vision
The PatientIntake system will provide a secure, HIPAA‑compliant patient intake workflow that enables front‑desk staff to capture demographics, insurance, and medical history, while ensuring data confidentiality and auditability.

## Success Metrics
- <0.1% unauthorized access incidents per year.
- 100% policy version compliance.
- ≥95% training completion across all roles.

## Continuous Improvement
- Quarterly compliance reviews of encryption and key rotation.
- Bi‑annual internal audits using NIST CSF; remediate high/medium risks within 30 days.
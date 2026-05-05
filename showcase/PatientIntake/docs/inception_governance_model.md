# Governance Model

### 1. Business Vision
The PatientIntake system will enable health‑care providers to capture complete patient demographic, insurance, and medical‑history data through a secure web‑based form while guaranteeing HIPAA compliance and 100 % data confidentiality. By leveraging open‑source technologies, the solution avoids vendor lock‑in, reduces licensing costs, and ensures that the organization retains full control over source code and security patches. The vision is to deliver a trustworthy intake experience that improves data accuracy, accelerates patient onboarding, and supports regulatory auditability.

### 3. Functional Requirements (Traceable)
1. **FR‑001 – Secure Demographic Capture**: The web form must collect name, DOB, address, and contact information with field‑level AES‑256 encryption at rest.
   - **Acceptance**: Security audit confirms each field is stored encrypted; decryption only possible via authorized role keys.
2. **FR‑002 – Encrypted Insurance Information**: Insurance provider name, policy number, and coverage details must be encrypted both in transit (TLS 1.3) and at rest.
   - **Acceptance**: Network capture shows TLS 1.3 handshake; storage verification shows encrypted blobs.
3. **FR‑003 – Medical History Storage with Audit Log**: All medical history entries must be written to PostgreSQL with an immutable audit record capturing user ID, timestamp, and operation type.
   - **Acceptance**: Audit log entry exists for every INSERT/UPDATE/SELECT operation; log entries are append‑only.
4. **FR‑004 – PDF Summary Generation**: Authorized staff can generate a PDF that includes a dynamic watermark (staff name) and an access timestamp.
   - **Acceptance**: PDF metadata contains correct watermark and timestamp; access logged.
5. **FR‑005 – Role‑Based Access Control**: Three RBAC tiers – Admin (full), Clinician (read/write patient data), Front Desk (create only) – must be enforced across all interfaces.
   - **Acceptance**: Penetration test confirms no privilege escalation paths.

### 5. Stakeholder Role Matrix
| Stakeholder ID | Role Description | Primary Need | Pain Points | Access Level | Aligned Objective |
|---|---|---|---|---|---|
| ST‑02 (Patient) | Submit personal health information and receive assurance of privacy. | Confidence that data is protected from exposure. | Fear of data exposure; limited trust in electronic intake forms. | Viewer (Read‑Only) for own record after submission. | OBJ‑001 |
| ST‑01 (Front‑Desk Staff) | Rapid entry of demographic and insurance data while minimizing re‑work. | Speedy intake to reduce bottlenecks during peak times. | Manual transcription errors; bottleneck during peak check‑in times. | Operator (Create/Update) for new intake records only. | OBJ‑002 |
| ST‑03 (Clinician) | Immediate access to complete medical history for clinical decision‑making. | Timely, accurate patient data to support care quality. | Incomplete or delayed records impede care; need audit trail for liability. | Analyst (Read‑Only) across all patient records with audit visibility. | OBJ‑003 |
| ST‑04 (Administrator) | Oversight of system configuration, user provisioning, and compliance reporting. | Ability to manage permissions and verify system integrity. | Complex permission management; difficulty proving audit readiness. | Administrator (Full Control) over system settings and logs. | OBJ‑004 |
| ST‑05 (Compliance Officer) | Assurance that all data handling meets HIPAA and internal policies. | Transparent evidence for audits; clear retention policies. | Lack of visible audit evidence; ambiguous retention enforcement. | Auditor (Read‑Only) on audit logs and configuration snapshots. | OBJ‑005 |

### 6. Rationale for RBAC Tier Assignment
- **Viewer – Patients** may only view their own submitted record after completion; this limits exposure while satisfying the right to access their PHI.
- **Operator – Front‑Desk staff** require create and update privileges limited to new intake entries; they cannot modify existing records, reducing risk of accidental data alteration.
- **Analyst – Clinicians** need read‑only access across the patient cohort to support diagnosis but must not alter historical data, preserving data integrity.
- **Administrator – System administrators** must manage user roles, encryption keys, and system patches; full control is essential for rapid incident response.
- **Auditor – Compliance officers** require read‑only visibility into immutable audit logs and configuration snapshots without the ability to alter them, ensuring audit integrity.

### 7. Alignment with Project Objectives
Each stakeholder’s access need directly maps to a measurable objective (OBJ‑xxx). These objectives will later be expressed as KPIs (e.g., KPI‑001 supports clinician access speed). By anchoring stakeholder needs to objectives now, governance bodies can track compliance, prioritize enhancements, and enforce accountability throughout the project lifecycle.

#### Governance Structure
The governance board consists of the Project Sponsor, Security Lead, Compliance Officer, Technical Lead, and Clinical Advisory Group. The board meets bi‑weekly to review progress against objectives, validate risk mitigation actions, approve scope changes, and ensure continuous alignment with HIPAA regulations.

#### Decision‑Making Process
1️⃣ **Requirement Review** – All new functional or non‑functional requirements are evaluated against existing objectives and risk registers.
2️⃣ **Change Authorization** – Any deviation from baseline scope requires documented justification and approval by at least two governance members.
3️⃣ **Compliance Verification** – Prior to each release milestone, the Compliance Officer conducts an audit against the risk register and verifies that all mitigation actions are complete.
4️⃣ **Metrics Reporting** – KPI dashboards are refreshed daily; any breach of threshold triggers an escalation workflow.

#### Oversight Mechanisms
- **Audit Log Review** – Automated scripts flag anomalous read/write patterns; alerts are sent to the Security Lead.
- **Vulnerability Management** – Weekly scans feed into a ticketing system; tickets are prioritized by impact rating.
- **RBAC Policy Audits** – Quarterly reviews ensure role assignments remain aligned with job functions.
The governance model provides continuous oversight ensuring that the PatientIntake system remains compliant, secure, and aligned with business goals throughout its lifecycle.

### 7.1 Executive Steering Committee (ESC)
Members: Chief Medical Officer (CMO), Chief Information Security Officer (CISO), VP of Operations. Authority: approves scope changes, allocates budget, and signs off final deliverables.

### 7.2 Compliance Oversight Board (COB)
Members: Compliance Officer, Legal Counsel, Privacy Lead. Responsibility: validates that all HIPAA technical and administrative safeguards are satisfied before any production release.

### 7.3 Project Management Office (PMO)
Members: Project Manager, Business Analyst. Role: day-to-day execution, status reporting, backlog prioritization, and risk escalation to ESC.

### 7.4 Technical Review Panel (TRP)
Members: Lead Architect (open-source stack), Security Engineer. Role: reviews design decisions for open-source compliance, security posture, and feasibility of the air-gap deployment.

### 7.5 Audit & Monitoring Unit (AMU)
Members: Security Operations Center staff. Role: continuously monitors immutable audit logs, enforces alerting thresholds, and initiates corrective actions on detected anomalies.

## 8. Decision-Making Hierarchy
| Level | Authority | Primary Decision |
|-------|-----------|-------------------|
| ESC   | Final approval of scope & budget | Release to production |
| COB   | Sign-off on HIPAA controls        | Authorization of HC-001 checklist |
| PMO   | Backlog prioritization & risk escalation | Sprint planning |
| TRP   | Technical go/no-go per sprint    | Acceptance of design artifacts |
| AMU   |	Trigger remediation on audit findings |	Enforcement of policy violations |

## 9. Enforcement Mechanisms
* **Mandatory HIPAA Control Checklist (HC-001)** – Signed by COB before any production deployment. Checklist covers encryption key management, role-based access control, immutable audit logging, and documentation completeness.
* **Audit Log Retention** – All read/write events are stored immutably for **7 years** using cryptographic hash chaining.
* **Role-Based Access Review** – Conducted every **90 days**; any deviation triggers immediate remediation.
* **Quarterly Compliance Audits** – ESC reviews audit reports; non-conformance > 5 % initiates a remediation plan.
* **Escalation Matrix** – Critical issues → 48 h; High → 5 days; Medium → 15 days.

## 10. Success Criteria / KPIs
* **KPI-01 – Encryption Compliance Rate** – 100 % of PHI fields encrypted; measured by automated configuration audit script.
* **KPI-02 – Audit Log Coverage** – 100 % of read/write events logged; validated by monthly integrity checksum report.
* **KPI-03 – PDF Export Watermark Accuracy** – 100 % of PDFs contain staff watermark and timestamp; verified by random sample inspection per release.
* **KPI-04 – System Availability** – ≥ 99.9 % uptime per month; reported via infrastructure monitoring dashboard.

## 11. Risk Assessment
| Risk ID | Description                                            | Likelihood | Impact | Mitigation Strategy                                                                                 | Owner |
|--------|--------------------------------------------------------|------------|--------|-----------------------------------------------------------------------------------------------------|-------|
| RISK-01| Unauthorized data exposure via compromised credentials   | Medium     | High   | MFA + periodic credential rotation; strict RBAC per tier                                            |	CISO |
| RISK-02| Open-source component vulnerabilities discovered post-deployment |	High      |	High   |	Automated SBOM scanning (Syft); patch critical CVEs within 30 days                               |	Security Engineer |
| RISK-03| Misconfiguration of Docker Compose or host firewall leading to accidental exposure of PostgreSQL in air‑gapped environment |	Medium    |	High   |	Immutable Docker images signed with Notary; enforce host firewall rules per deployment guide; run pre‑deployment validation script checking open ports and volume permissions |	Infrastructure Engineer |
| RISK-04| Compliance audit gaps due to incomplete documentation of controls |	Low       |	High   |	Maintain live control matrix in Confluence; quarterly internal audit; external audit readiness checklist |	Compliance Officer |

## 12. Scope Definition
*In Scope*: End-to-end patient intake web form, field-level encryption at rest and in transit, role-based access controls, immutable audit logging, PDF generation with watermarking and timestamps, Docker Compose deployment guide for air-gapped environment, automated unit and integration tests covering validation, encryption, and access control edge cases.

*Out of Scope*: Cloud SaaS solutions, commercial encryption appliances, integration with external EHR systems beyond data export.

## 13. Review & Sign-off Process
1. Draft governance model reviewed by PMO and TRP for technical feasibility.
2. COB signs off HC-001 checklist confirming all HIPAA safeguards are implemented.
3. ESC provides final approval signature stored in the project repository.

All statements are traceable to defined IDs above.
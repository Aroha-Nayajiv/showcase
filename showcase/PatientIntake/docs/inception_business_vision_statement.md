# Business Vision Statement
                
### 1. Scope Definition
The **PatientIntake** system is limited to four core capabilities:
1. **Secure capture** of patient demographics, insurance information, and medical history via a web‑based form that encrypts each field at rest and in transit.
2. **Persistent storage** of the encrypted submissions in a locally hosted PostgreSQL instance protected by role‑based access control (admin, clinician, front‑desk).
3. **PDF intake summary generation** that applies a dynamic watermark containing the staff member’s name and a timestamp; the PDF is encrypted at rest and can be downloaded only by authorized roles.
4. **Automated testing** that provides unit and integration coverage for form validation, encryption handling, and access‑control edge cases.
All components are packaged as Docker containers and deployed with Docker Compose on an air‑gapped on‑premises environment. No external cloud services or proprietary libraries are used.

### 2. Architecture Vision
The solution follows a modular, container‑based architecture built exclusively from open‑source technologies:
- **Front‑end**: A single‑page application served over TLS 1.3 that performs client‑side validation before transmitting data.
- **Back‑end service layer**: Stateless microservice that applies AES‑256 field‑level encryption, writes encrypted rows to PostgreSQL, and records every read/write operation in an immutable audit log stored on write‑once storage.
- **PDF generator**: Isolated container that consumes encrypted records, creates a PDF, adds a watermark and timestamp, encrypts the file, and streams it to the requester.
- **Infrastructure**: Docker Compose orchestrates the containers; each container runs with the principle of least privilege and is hardened for air‑gap deployment.

### 3. Functional Acceptance Criteria
| ID | Description | Measurable Acceptance |
|----|-------------|-----------------------|
| FR-001 | Secure collection of patient demographics, insurance information, and medical history via web form | 100 % of submitted forms are encrypted at rest and in transit; form validation error rate < 2 % under load test |
| FR-002 | Role‑based access control for admin, clinician, front‑desk | Access matrix matches defined RBAC tiers; unauthorized attempts are logged and blocked |
| FR-003 | Immutable audit log for every read/write operation | Log entries created for 100 % of transactions; retention period 7 years verified quarterly |
| FR-004 | PDF intake summary generation with watermark and timestamp | PDF generated for every completed record; watermark includes staff name; timestamp within ±1 s of system clock |
| FR-005 | Automated unit and integration tests covering validation, encryption, and access control | Test suite achieves ≥ 90 % code coverage; all tests pass in CI pipeline |

### 5. Key Performance Indicators
| KPI ID | Metric Description | Target |
|--------|----------------------|--------|
| KPI-01 | Form Completion Rate – % of sessions resulting in successful submission within 2 min | ≥ 95 % |
| KPI-02 | Audit Log Completeness – % of transactions logged | 100 % |
| KPI-03 | PDF Export Accuracy – % of PDFs containing correct watermark and timestamp | 100 % |
| KPI-04 | Test Coverage Ratio – Automated test coverage percentage | ≥ 90 % |

### 7. Out‑of‑Scope Statement
The project does **not** include:
* Integration with external electronic health record (EHR) systems.
* Development of native mobile applications.
* Cloud‑based analytics platforms or data warehouses.
* Any functionality beyond the defined web form capture, PDF generation, immutable audit logging, automated testing, and Docker Compose deployment.

---

## Business Vision Statement and Success Criteria for PatientIntake
The **PatientIntake** system will enable health‑care organizations to capture patient demographic, insurance, and medical‑history data in a fully HIPAA‑compliant manner while leveraging only open‑source technologies. By enforcing field‑level encryption, role‑based access control, immutable audit logging, and secure PDF export, the solution delivers a trustworthy intake experience that reduces manual errors, accelerates clinician workflow, and satisfies regulatory auditors.

### Functional Requirements (Traceable IDs)
| ID | Requirement Summary |
|----|--------------------|
| FR-001 | Secure demographic capture via web form; fields encrypted at rest using AES‑256; submission returns HTTP 200 within 200 ms for ≥ 95 % of transactions (KPI-001) |
| FR-002 | Insurance information collection with validation against configurable lookup service; encrypted storage verified by decryption test; ≥ 99 % valid entries accepted without error (KPI-002) |
| FR-003 | Medical history entry with optional free‑text notes; each note encrypted individually; audit log records a write event for each submission; log entry count matches submission count 100 % (KPI-003) |
| FR-004 | Role‑based access control for data view and edit; Admin can CRUD all records; Clinician can view/update assigned patients; Front‑Desk can create records but cannot view PHI after creation; all access attempts logged (FR‑003) |
| FR-005 "PDF intake summary generation with watermark and timestamp" | Authorized staff can generate a PDF that includes dynamic watermark containing staff name and timestamp; PDF stored encrypted at rest; download event logged; generation succeeds within 1 s for ≥ 90 % of requests (KPI-004) |

## Stakeholder Analysis

| Stakeholder | Need | Pain Point | Role | Objective |
|---|---|---|---|---|
| ST-01 Clinical Staff (Physicians, Nurses) | Immediate access to complete, accurate patient medical histories to inform care decisions | Delays caused by paper forms and fragmented electronic records; risk of missing critical history | Clinician (read/write for assigned patients) | OBJ-001: Enable timely, accurate clinical decision‑making |
| ST-02 Patients | Secure, convenient way to provide personal and health information without exposing PHI | Lack of trust in data handling; fear of data breaches; need for privacy | Patient (no direct system access; data entry via web form) | OBJ-002: Ensure patient confidence and compliance with HIPAA |
| ST-03 Front‑Desk Staff | Efficient capture and verification of intake data to streamline registration workflow | Manual transcription errors; time‑consuming verification; regulatory compliance overhead | Front‑Desk (create/read own entries, limited edit) | OBJ-003: Reduce registration time and error rate |
| ST-04 Administrator (IT / System Admin) | Ability to configure system policies, manage user accounts, and audit logs | Complex configuration tools; lack of audit visibility; risk of misconfiguration | Administrator (full system control) | OBJ-004: Maintain system integrity and auditability |
| ST-05 Compliance Officer | Assurance that all data handling meets HIPAA technical and administrative safeguards | Difficulty proving compliance during audits; incomplete logging | Compliance Officer (read‑only audit logs) | OBJ-005: Demonstrate continuous HIPAA compliance |

## Narrative Summary
The intake workflow is designed around five primary personas. Clinical staff require real‑time, trustworthy access to a patient’s full medical history while being protected by least‑privilege RBAC. Patients need a secure web form that encrypts each field at rest and in transit, fostering confidence that their PHI will not be exposed. Front‑Desk personnel benefit from a streamlined capture process that eliminates manual transcription and reduces registration bottlenecks. Administrators must have unrestricted system control to enforce policies, manage accounts, and maintain full auditability. Compliance officers require immutable, read‑only audit logs to satisfy HIPAA technical safeguards and support audit readiness.

## Alignment with Project Goals
Each stakeholder objective maps directly to the overarching project goals:
1. **Full HIPAA compliance** – achieved through encryption, RBAC, immutable logging, and audit‑ready reporting (OBJ‑002, OBJ‑004, OBJ‑005).
2. **Streamlined intake** – realized by eliminating paper forms and automating data capture/validation (OBJ‑001, OBJ‑003).
3. **Enhanced data security & patient trust** – enforced via field‑level AES‑256 encryption, TLS 1.3 transport security, and strict access controls (OBJ‑001, OBJ‑002).

These alignments ensure that every functional component directly supports a measurable business outcome.

## Risk Assessment Register
| Risk ID | Description | Likelihood | Impact | Mitigation Actions | Owner |
|---|---|---|---|---|---|
| RISK-01 | Unauthorized disclosure of PHI during transmission or storage. | H | H | • Enforce TLS 1.3 for all network traffic.<br>• Apply field‑level AES‑256 encryption at rest.<br>• Rotate encryption keys every 90 days.<br>• Conduct quarterly penetration testing. | Security Lead |
| RISK-02 | Vulnerabilities in open‑source components that could be exploited. | M | H | • Maintain a Software Bill of Materials (SBOM).<br>• Integrate OWASP Dependency‑Check into CI pipeline.<br>• Patch CVSS ≥ 7.0 vulnerabilities within 48 hours.<br>• Curate an approved whitelist of packages. | DevOps Engineer |
| RISK-03 | Misconfiguration of Docker Compose or container runtime leading to privilege escalation or data leakage. | M | H | • Use minimal base images and run containers as non‑root users.<br>• Enforce read‑only filesystem where possible. • Validate compose files against a hardened schema before deployment. | • Perform weekly configuration drift detection. | Infrastructure Engineer |
| RISK-04 | Incomplete or tampered audit logs that fail to provide a reliable chain of custody for PHI access events. | L | H | • Enable immutable append‑only logging in PostgreSQL. • Replicate logs to a write‑once storage volume. • Sign each log entry with a quarterly‑rotated HMAC key. | • Retain logs for a minimum of 7 years per HIPAA §164.310(d). | Compliance Officer |
| RISK-05 | Failure to meet HIPAA administrative safeguards during onboarding of new staff or third‑party contractors. | M | M | • Implement a formal onboarding checklist covering role‑based provisioning, security awareness training, and signed Business Associate Agreements. • Conduct quarterly access right audits. | • Revoke privileges within 24 hours of role change. | HR Manager |

## Key Observations
1. **Likelihood Distribution** – The most probable risks are RISK-001 (unauthorized disclosure) and RISK-002/03 (software and configuration issues), reflecting the open‑source stack and containerized deployment model.
2. **Impact Alignment** – All listed risks carry High impact on patient privacy or regulatory compliance, justifying aggressive mitigation tactics.
3. **Ownership Clarity** – Each mitigation is assigned to a specific functional owner, ensuring accountability and measurable follow‑up during quarterly risk reviews.

## Monitoring & Review Process
* **Risk Register Dashboard** – Updated after each sprint review.
* **Effectiveness Measurement** – Quarterly security audit reports and incident logs will verify mitigation success.
* **New Risk Identification** – Any emerging risk discovered during development or deployment will be logged with a new identifier following the next available sequence (e.g., RISK‑006).
* **Continuous Improvement** – Mitigation actions are refined based on audit findings and evolving threat intelligence.

### Scope
* **In‑Scope** – Web‑based structured intake form with field‑level AES‑256 encryption (at rest and in transit), PostgreSQL storage with RBAC (admin, clinician, front‑desk), immutable audit log, PDF summary generation with watermark and timestamp, automated unit/integration test suite covering form validation, data encryption, and access control edge cases, Docker‑Compose deployment for air‑gapped on‑prem environments.
* **Out‑of‑Scope** – Cloud services, third‑party SaaS analytics, mobile native applications, integration with external EHR systems beyond data export.

### Success Criteria / KPIs
| KPI ID | Description | Target |
|---|---|---|
| KPI-01 | Form submission response time < 200 ms per transaction | ≤ 200 ms |
| KPI-02 | System availability (uptime) | ≥ 99.9 % |
| KPI-03 | Successful audit log generation for every read/write operation | 100 % coverage |
| KPI-04 | PDF export security compliance (watermark present, timestamp recorded) | 100 % compliance |
| KPI-05 | Test coverage for critical paths (form validation, encryption handling, RBAC) | ≥ 80 % of statements |

### Acceptance Criteria per Objective
* **OBJ‑001** – Clinicians can retrieve a patient’s complete medical history within 2 seconds of request; all retrieved records must be verified against role permissions.
* **OBJ‑002** – Patients receive a TLS 1.3 secured page; submitted fields are encrypted at rest using AES‑256; encryption key rotation occurs every 90 days without data loss.
* **OBJ‑003** – Front‑Desk staff can create and edit their own intake entries; average registration time reduced by at least 30 % compared to baseline manual process.
* **OBJ‑004** – Administrators can add/remove users, modify RBAC policies, and view immutable audit logs via an admin console; any policy change is logged with user ID and timestamp.
* **OBJ‑005** – Compliance officers can generate read‑only audit reports covering the previous 90 days; reports must be exportable as tamper‑evident PDFs meeting HIPAA §164.312(b) requirements.

## Traceability Matrix
* Functional Requirements: FR-001 (Secure demographic capture), FR-002 (Insurance information capture), FR-003 (Medical history storage), FR-004 (PDF summary generation), FR-005 (Automated testing suite).
* Non‑Functional Requirements: NFR-001 (<200 ms response time), NFR-002 (99.9 % uptime), NFR-003 (Audit logging), NFR-004 (Role-based access control), NFR-005 (Test coverage thresholds).
* Risks linked to requirements are captured in the Risk Assessment Register above.

# Business Vision
The Patient Intake system will enable healthcare providers to capture patient demographic, insurance, and medical history information in a secure, HIPAA‑compliant web form. The solution will be built exclusively with open‑source components, run on‑premises behind an air‑gap, and provide auditable PDF summaries for clinical staff.

## Risk Register & Mitigations
| Risk ID | Description | Mitigation |
|---|---|---|
| RISK‑001 | Unauthorized exposure of PHI due to weak encryption keys | Enforce TLS 1.3 + AES‑256 field encryption; rotate keys quarterly; store keys in a hardware security module (HSM) |
| RISK‑002 | Vulnerable third‑party libraries introducing security flaws | Run OWASP Dependency‑Check weekly; apply patches within 30 days of release |
| RISK‑003 | Misconfiguration of Docker containers leading to privilege escalation | Provide hardened Docker‑Compose templates; execute pre‑deployment validation scripts; conduct staff training sessions |

## KPI Mapping
| KPI ID | Target | Linked Requirement(s) |
|---|---|---|
| KPI‑001 | ≥95 % form completion on first attempt | FR‑001, NFR‑001 |
| KPI‑002 | 100 % encryption compliance (rest & transit) | FR‑001 |
| KPI\-003 | 100 % audit log coverage | FR‑003, NFR‑003 |
| KPI\-004 | 0 % data loss in PDFs (checksum match) | FR\-004, NFR\-004 |
| KPI\-005 | 100 % successful air‑gap deployments on first try | FR\-008, FR\-009 |

## Governance & Traceability
All requirements are traceable to the stakeholder who owns them:
* **ST‑001** owns FR‑002 and FR‑004 (clinical access).
* **ST\-002** owns FR‑001 (patient data entry).
* **ST\-003** owns NFRs related to audit logging and compliance.
* **ST\-004** owns deployment and air‑gap validation (FR‑008, FR‑009).
* **ST\-005** owns security controls for encryption and key management (FR‑001, RISK‑001).

The document satisfies the inception phase by defining purpose, scope, measurable success criteria, stakeholder responsibilities, and risk mitigation strategies without delving into technical design details.
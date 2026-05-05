# Project Charter
                
## Vision & Scope – HIPAA‑Aligned Patient Intake System

### 1. Vision Statement
The PatientIntake project will deliver a secure, open‑source web‑based intake platform that enables clinical staff to capture patient demographics, insurance information, and comprehensive medical history while guaranteeing HIPAA compliance through field‑level encryption, role‑based access control, immutable audit logging, and controlled PDF export. The solution will operate entirely on‑premises using Docker Compose, ensuring data residency and eliminating reliance on external cloud services.

### 2. Scope Definition
| Functional | Description |
|------------|-------------|
| Structured web form | Collect demographics, insurance, medical history with field‑level encryption at rest and TLS 1.3 in transit |
| Role‑based access | Admin, Clinician, Front Desk roles with least‑privilege permissions |
| Immutable audit log | Every read/write operation recorded on append‑only storage |
| PDF intake summary | Watermarked, timestamped PDF generated per patient and exportable only by authorized staff |
| Automated testing | Unit and integration tests covering form validation, encryption handling, and access control edge cases |
| Deployment | Docker Compose orchestrates containers for an air‑gap on‑prem environment |
| Exclusions | Integration with external EHR systems, mobile native applications, non‑HIPAA analytics dashboards |

### 3. Strategic Objectives (SMART)
| ID | Objective | Success Criteria |
|----|-----------|------------------|
| OBJ-001 | Regulatory Compliance – Achieve full HIPAA §164 compliance for data protection by the end of Q2 2027. | All encryption, access control, and audit log mechanisms validated against HIPAA technical safeguard checklist |
| OBJ-002 | Operational Efficiency – Reduce average patient intake time from 12 minutes (paper) to ≤ 3 minutes per record by Q4 2027. | End‑to‑end form submission measured < 3 minutes in user testing |
| OBJ-003 | Data Security – Ensure 100 % of stored PHI is encrypted with AES‑256 and all network traffic uses TLS 1.3 by launch. | Encryption at rest verified via cryptographic scans; TLS 1.3 enforced on all endpoints |
| OBJ-004 | Auditability – Generate immutable audit logs retained for 7 years with zero‑loss retrieval rate ≥ 99.9 %. | Log integrity checks pass 100 % of the time; retention policy enforced in storage configuration |
| OBJ-005 | Open‑Source Commitment – All components must be sourced from OSI‑approved licenses; no proprietary binaries. | Bill of Materials audited; every dependency listed with license information |

### 4. High‑Level Architecture Overview (Narrative)
The system consists of three logical layers:
* **Presentation Layer** – A browser‑based UI built on an open‑source JavaScript framework that submits encrypted form payloads via HTTPS to the backend.
* **Application Layer** – A stateless service container handling request validation, encryption/decryption using industry‑standard libraries, RBAC enforcement, PDF generation with watermarking, and audit log creation.
* **Data Layer** – A locally hosted PostgreSQL instance configured with row‑level security and encrypted tablespaces; audit logs are written to an append‑only write‑once storage volume.
All containers are orchestrated by Docker Compose with explicit network isolation, volume encryption flags, and documented air‑gap setup steps to satisfy on‑prem deployment requirements.

### 5. Success Metrics / KPIs
| KPI ID | Metric | Target | Measurement Method | Linked Objective |
|--------|--------|--------|-------------------|----------------|
| KPI-01 | Form submission response time (p95) | ≤ 200 ms | Automated load test suite measuring end‑to‑end latency | OBJ-002 |
| KPI-02 | System availability (monthly uptime) | ≥ 99.9 % | Monitoring platform uptime logs aggregated monthly | OBJ-002 |
| KPI-03 | Audit log completeness rate | 100 % of transactions logged | Log audit script cross‑checking transaction count vs log entries | OBJ-004 |
| KPI-04 | PDF export security compliance | Watermark present & timestamp verified on 100 % of exports | Manual spot check of 50 random PDFs per release cycle | OBJ-003 |

## Business Requirements – Functional Requirements Traceability Matrix
| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-001 | Secure Demographic Capture – The system shall provide a structured web form that collects patient demographic information (full name, date of birth, address, phone number, email) from the patient or front‑desk staff. | • All mandatory demographic fields must be completed for 100 % of submissions.<br>• Format validation enforced (YYYY‑MM‑DD for dates, regex for phone).<br>• Data encrypted at field level before transmission and stored encrypted at rest using AES‑256. |
| FR-002 | Insurance Information Capture – The system shall collect insurance provider details, policy number, and coverage dates for each patient. | • Insurance fields mandatory for applicable submissions.<br>• Validation against known insurer identifier list with ≥ 95 % match rate. |
| FR-003 | Medical History Recording – The system shall allow entry of past diagnoses, medications, allergies, and surgeries via selectable lists and free‑text entries. | • ≥ 90 % of free‑text entries limited to 500 characters.<br>• All medical history entries encrypted at field level and stored encrypted at rest. |
| FR-004 | Role‑Based Access Control (RBAC) for Data Entry and Review – Only authorized roles (Admin, Clinician, Front Desk) may create, edit, or view patient intake records according to their permission tier. | • Access logs show only users with appropriate role performed create/edit actions (0 % unauthorized incidents during testing).<br>• Role assignments reviewed weekly by Compliance Officer. |
| FR-005 | Audit Log Generation – Every read and write operation on patient intake data shall generate an immutable audit log entry containing user ID, timestamp, operation type, and affected record ID. | • Audit log retains entries for a minimum of 7 years on immutable storage.<br>• Log integrity verification passes 100 % of the time using cryptographic hash chaining.<br>• Audit log generation latency ≤ 200 ms per operation. |
| FR-006 | PDF Generation – The system shall generate a PDF intake summary per patient that includes a visible watermark (“Confidential – Patient Intake”) and a timestamp of export. Export must be restricted to authorized staff only. | • PDF contains watermark on every page.<br>• Export timestamp recorded in audit log.<br>• Unauthorized export attempts blocked and logged.<br>• PDF size ≤ 5 MB for typical records. |
| FR-007 | Automated Testing – The solution shall include unit tests for each form field validation rule and integration tests covering encryption handling, RBAC enforcement, PDF generation workflow, and audit log creation. Test suite must achieve ≥ 80 % code coverage. | • Unit test suite passes all cases on CI pipeline.<br>• Integration tests simulate end‑to‑end submission flow and verify encryption at rest/transit.<br>• Coverage report shows ≥ 80 % overall coverage.<br>• Tests run within 10 minutes on reference hardware. |
| FR-008 | Deployment via Docker Compose – The system shall be deployable using Docker Compose in an air‑gap on‑prem environment without external cloud dependencies. Deployment guide must detail network isolation, volume encryption flags, and steps to verify air‑gap compliance. | • Docker Compose file defines three services (frontend, backend, postgres) with isolated networks.<br>• Deployment guide includes checklist for air‑gap verification (no outbound internet traffic).<br>• Successful deployment validated by running end‑to‑end test suite on target hardware. |

### Additional Notes
All functional requirements are aligned with the strategic objectives to deliver a HIPAA‑compliant patient intake solution that improves data accuracy, reduces manual re‑entry errors, and enables secure information sharing among clinical staff.

## Stakeholder Analysis
| Stakeholder ID | Role / Need | Pain Points / Risks | Assigned RBAC Tier | Linked Objective |
|-----------------|-------------|----------------------|--------------------|------------------|
| ST-01 | Patient (Data Subject) | Fear of data exposure; cumbersome paper forms | None (view only of own submitted data) | OBJ-001 |
| ST-02 | Front Desk Staff | Manual re‑entry errors; validation failures | Operator (create & submit) | OBJ-002 |
| ST-03 | Clinician | Delayed access to critical information | Viewer (read‑only) | OBJ-003 |
| ST-04 | Administrator | Complexity of role provisioning; compliance reporting workload | Admin (full control) | OBJ-004 |
| ST-05 | Compliance Officer / Auditor | Unclear audit‑log retention; regulatory assurance gaps | Auditor (read‑audit) | OBJ-005 |

### RACI Assignment for Core Inception Activities
| Activity | Responsible | Accountable | Consulted | Informed |
|----------|--------------|--------------|------------|----------|
| Define project scope and objectives | Administrator (ST-04) | Administrator (ST-04) | Compliance Officer (ST-05), Clinician (ST-03) | Front Desk Staff (ST-02) |
| Capture functional requirements (FR‑001–FR‑008) | Front Desk Staff (ST-02) & Clinician (ST-03) | Administrator (ST-04) | Clinician (ST-03), Compliance Officer (ST-05) |
| Validate HIPAA compliance criteria | Compliance Officer (ST-05) | Administrator (ST-04) | Clinician (ST-03), Front Desk Staff (ST-02) |

## Business Vision
The PatientIntake project will deliver a HIPAA‑compliant patient intake system that enables front‑desk staff to capture demographic, insurance and medical history data through a secure web form, stores the encrypted records in a locally hosted PostgreSQL database, and provides authorized clinicians with a tamper‑evident PDF summary that includes watermarking and export timestamps. All components are built exclusively with open‑source technologies and deployed on‑premises via Docker Compose to satisfy the organization’s air‑gap policy.

### Acceptance Criteria
* Each functional requirement must have a measurable test case documented in the test suite.
* The audit log must retain entries for at least seven years on write‑once read‑many storage.
* PDF exports must contain a visible watermark that includes the patient identifier and the exact export datetime.
* Docker images must be signed with Notary and verified before deployment.

## Key Performance Indicators (KPI)
| KPI ID | Metric |
|---|---|
| KPI-001 | Form submission response time < 200 ms under normal load |
| KPI-002 | System availability 99.9 % monthly uptime |
| KPI-003 | Successful audit log generation for 100 % of read/write events |
| KPI-004 | PDF export compliance – watermark present on 100 % of PDFs and timestamp accuracy within 1 second |
| KPI-005 | Test coverage ≥ 80 % for unit tests and ≥ 70 % for integration tests |

## Risk Identification and Prioritization
| Risk ID | Description | Likelihood | Impact | Mitigation Action |
|---|---|---|---|---|
| RISK-001 | Unauthorized disclosure of PHI during data transmission between the web client and the on‑prem server. | M | H | Enforce TLS 1.3 for all network traffic; apply field‑level AES‑256 encryption before transmission; conduct quarterly penetration testing with OWASP ZAP. |
| RISK-002 | Vulnerabilities in open‑source libraries that could bypass audit logging. | M | H | Adopt continuous dependency scanning (Dependabot); enforce zero‑day remediation within 7 days; maintain a Bill of Materials and perform annual third‑party code audit. |
| RISK-003 | Misconfiguration of Docker Compose or host firewall leading to accidental exposure of PostgreSQL in an air‑gapped environment. | L | H | Use immutable Docker images signed with Notary; enforce host firewall rules documented in the deployment guide; run pre‑deployment validation script that checks open ports and volume permissions. |
| RISK-004 | Failure to retain immutable audit logs for the legally required retention period. | L | H | Define log retention policy of seven years on WORM storage; automate log archiving using rsync to an offline encrypted volume; perform quarterly log integrity checks using SHA‑256 hashes. |

## Compliance Controls Alignment
* HIPAA §164.312(a)(2)(iv) – Encryption: All PHI at rest is encrypted with AES‑256 as required by FR‑001 through FR‑003.
* HIPAA §164.308(a)(1)(ii) – Audit Controls: Immutable audit log strategy satisfies the audit control requirement (RISK-004).
* NIST SP 800‑53 CM‑7 – Least Functionality: Open‑source component selection is limited to actively maintained packages with CVE tracking.

## Monitoring and Reporting
* **Monthly Risk Dashboard** – Produced by the Security Lead showing current risk status, mitigation progress and open tickets.
* **Quarterly Compliance Review** – Led by the Compliance Officer with participation from Clinical Staff, Front Desk Management and Infrastructure Engineer to verify effectiveness of controls.
* **Incident Response Playbook** – Stored in the repository; aligns with HIPAA breach notification timelines and outlines escalation steps.

## Ownership and Escalation Path
* Each risk owner maintains mitigation artifacts, updates them when new threats emerge, and escalates unresolved issues to the Project Steering Committee within five business days of detection.
* The Project Steering Committee reviews escalations during bi‑weekly governance meetings and authorizes corrective actions.

## Charter Sign‑off Matrix
| Activity | Owner(s) | Approver(s) |
|---|---|---|
| Approve stakeholder matrix and RACI model | Front Desk Manager, Compliance Officer | Executive Sponsor |
| Sign‑off on charter document including vision, objectives, KPIs and risk register | Project Manager, Security Lead | Executive Sponsor |
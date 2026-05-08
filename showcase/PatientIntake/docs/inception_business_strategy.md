# Business Strategy (Overview)

## 1. Business Vision & Strategic Objectives
The PatientIntake project aims to deliver a HIPAA-compliant, open-source patient intake platform that enables healthcare providers to capture demographics, insurance details, and medical history through a secure web form.

**Strategic Objectives**
* **OBJ-001** – Ensure full regulatory compliance (HIPAA §164.312(a)(2)(iv) encryption) while using only open-source components.
* **OBJ-002** – Achieve high operational efficiency by reducing manual data entry time by at least 40 % compared with paper-based processes.
* **OBJ-003** – Provide auditability and role-based access control to support internal governance and external audits.
* **OBJ-004** – Implement automated key rotation every 90 days and maintain system uptime ≥99.9 % (supports availability and security hygiene).
* **OBJ-005** – Attain patient satisfaction score ≥90 % measured via post‑visit surveys (drives adoption and trust).

## 2. Stakeholder Analysis
| Stakeholder ID | Role               | Primary Need| Pain Point  | RBAC Tier                     | Mapped Objective | Mapped KPI |
|----------------|--------------------|---------------------|-------------------|-----------|------------------|------------|
| ST-001         | Patient            | Secure submission of personal and medical data without exposing PHI   | Distrust of electronic forms; fear of data leakage   | Read-only                    | OBJ-001          | KPI-001   |
| ST-002         | Front‑Desk Staff   | Rapid intake of new patients while maintaining data accuracy | Manual re-entry of paper forms leads to errors       | Operator (create/read)        | OBJ-002          | KPI-002   |
| ST-​003         | Clinician          | Immediate access to complete, verified patient histories    | Incomplete or tampered records impede treatment   | Clinician (read/write)        | OBJ-​003          | KPI-​003   |
| ST-​004         | System Administrator| Ability to provision tenants, rotate keys, | and monitor system health without service interruption | Complex key-management processes increase operational risk | Admin (full)                 | OBJ-​004          | KPI-​004   |
| ST-​005         | Compliance Officer| Evidence that all HIPAA technical safeguards are enforced | Lack of immutable audit trails makes compliance verification difficult | Auditor (read-only audit)    | OBJ-​005          | KPI-​005   |

## 3. Narrative Summary
1. **Patients** require assurance that every field—name, address, insurance number, and medical history—is encrypted using AES‑256 at rest and TLS 1.2+ in transit. Their trust is quantified by a target satisfaction score ≥90 % measured via post‑visit surveys.
2. **Front‑Desk Staff** need a streamlined workflow that eliminates duplicate data entry. The single web form validates inputs client-side and auto-populates repeat visits, reducing average processing time to under two minutes per patient.
3. **Clinicians** depend on timely, accurate records to make clinical decisions. Role-based access permits read/write of patient histories while preventing unauthorized modifications; every change is captured in an immutable audit log.
4. **System Administrators** are responsible for tenant isolation, key lifecycle management, and operational monitoring. Automated tooling provides key rotation every 90 days and health checks without impacting clinician access.
5. **Compliance Officers** must demonstrate continuous adherence to HIPAA Technical Safeguard controls. The solution provides exportable audit reports, tamper-evident logs retained ≥7 years on write-once storage, and a documented air-gap deployment guide satisfying SOC 2 and HITRUST expectations.

## 4. Alignment with Project Objectives
Each stakeholder’s primary need directly maps to one of the five high-level objectives (OBJ‑001 – OBJ‑005). By satisfying these objectives the project will meet its strategic goals: HIPAA compliance, open-source cost containment, high availability, automated security hygiene, and user adoption.

### FR\-001 – Structured Patient Data Capture
* **Description:** The system shall present a web form that collects patient demographics, insurance information, and medical history in predefined fields.
* **Acceptance Criteria:**
  - All mandatory fields validated client-side; submission creates a record with a unique `patient_intake_id`.
  - Form completion rate ≥90 % in usability testing.
  - Data persisted only after successful encryption step.

### FR\-002 – Field-Level Encryption at Rest
* **Description:** All PHI fields shall be encrypted using AES\-256\-GCM before persisting to PostgreSQL.
* **Acceptance Criteria:**
  - Encryption keys stored in HashiCorp Vault with rotation policy every 90 days.
  - Penetration test confirms raw database dumps contain no readable PHI.

### FR\-003 – Transport Encryption in Transit
* **Description:** All client-to-server communication shall use TLS 1.2+ with forward secrecy.
* **Acceptance Criteria:**
  - HTTPS enforced via strict transport security headers.
  - Automated scans verify no mixed-content or weak cipher suites.

### FR\-004 – Role-Based Access Control & Audit Logging
* **Description:** Implement RBAC tiers (Patient read-only, Front Desk operator, Clinician read/write, Admin full) and generate immutable audit logs for every read/write operation.
* **Acceptance Criteria:**
  - Access checks enforced at API gateway level.
  - Audit log entries contain timestamp, user ID, action type, and hash of payload.
  - Logs stored on write-once storage retaining ≥7 years.

### FR\-005 – PDF Generation & Secure Export
* **Description:** Generate a PDF intake summary per patient; authorized staff may export it with a visible watermark and export timestamp.
* **Acceptance Criteria:**
  - PDF includes patient ID, generation timestamp, and watermark "Confidential – Authorized Use Only".
  - Export action creates an audit log entry linking PDF hash to user ID.
  - PDFs are stored encrypted at rest using the same AES\-256 key hierarchy.

## 5. Risk Assessment
| Risk ID   | Description  | Likelihood (H/M/L)   | Impact (H/M/L)   | Mitigation Strategy|
|-----------|--------------------|----------------------|-------------------|------------|
| RISK-001   | Encryption key mismanagement leading to unauthorized decryption               | M                    | H                 | Implement open-source key management (HashiCorp Vault) with rotation policies; conduct quarterly key audits |
| RISK-​002   | Audit log bottleneck under peak load causing loss of events                     | M                    | M                 | Use asynchronous logging with buffered queue and write-ahead log; monitor queue depth and alert on overflow |
| RISK-​003   | User resistance to new digital intake workflow| M                    | L                 | Conduct usability testing with patient focus groups; provide training sessions for front-desk staff and ensure continuous feedback loops. |

# Patient Intake System – Inception Artifact

## 6. Business Vision
The Patient Intake System will enable healthcare providers to capture patient demographics, insurance information, and medical history through a secure web‑based form while guaranteeing HIPAA‑compliant protection of protected health information (PHI). The solution will be built exclusively with open‑source technologies and deployed on‑premise via Docker Compose to satisfy air‑gap requirements.

## 7. Functional Requirements (FR)
| ID | Description | Acceptance Criteria |
|---|---|---|
| FR-001 | Secure Web Form Capture | • All form fields are encrypted at rest using AES‑256.<br>• TLS 1.3 is enforced for every client‑server interaction.<br>• Automated OWASP ZAP scan reports **no** TLS downgrade or weak cipher warnings. |
| FR-002 | Data Encryption In Transit & At Rest | • TLS 1.3+ for all external connections (NFR‑002).<br>• AES‑256 encryption for every PHI column in PostgreSQL (NFR‑001).<br>• Quarterly cryptographic audit validates 100 % coverage. |
| FR-003 | PDF Intake Summary Generation | • PDF includes patient data watermark and export timestamp visible only to authorized staff.<br>• Export operation logs an immutable audit entry (FR‑005). |
| FR-004 | Role‑Based Access Control (RBAC) | • RBAC matrix matches stakeholder table (ST‑001 – ST‑005).<br>• Any privilege escalation attempt is denied and logged.<br>• Unit tests cover 100 % of matrix cells with pass result. |
| FR-005 | Immutable Audit Logging | • Every read/write creates an append‑only log entry with timestamp, user ID, operation type, record ID.<br>• Logs stored with tamper‑evidence checksums and retained for ≥7 years.<br>• Quarterly audit confirms 99.9 % of operations logged within 1 second. |
| FR-006 | Docker Compose Air‑Gap Deployment | • Entire stack deployable via a single `docker-compose.yml` file.<br>• No external cloud services are required.<br>• Deployment guide validated on isolated hardware. |

## 8. Success Metrics (KPIs)
| ID | Metric | Target | Measurement Method |
|---|---|---|---|
| KPI-001 | Form Completion Rate | >90 % per month | Analytics dashboard counting successful submissions vs attempts |
| KPI-002 | Encryption Validation Rate | 100 % of stored PHI encrypted at rest & in transit | Automated vault inspection scripts & TLS handshake logs |
| KPI-003 | Audit Log Availability | 99.9 % of operations logged within 1 second | Log ingestion latency monitoring (Elasticsearch) |
| KPI-004 | RBAC Enforcement Accuracy | 0 unauthorized access incidents per quarter | Security incident tracking system |
| KPI-005 | Compliance Report Generation Time | ≤5 minutes for 90‑day export batch job | Scheduled job timing logs |

## 9. Traceability Matrix
| Requirement ID | Linked KPI(s) |
|---|---|
| FR-001 – FR-006 | KPI-001, KPI-002, KPI-004 |
| NFR-001 – NFR-005 | KPI-002, KPI-003 |
| RISK-001 – RISK-005 | KPI-002, KPI-003 |

## 10. Compliance & Open‑Source Constraints
* All components must be licensed under permissive open‑source licenses (e.g., MIT, Apache 2.0).<br>* No reliance on SaaS or cloud services; the stack runs entirely on-premise hardware.
* HIPAA technical safeguards are satisfied through TLS 1.3 enforcement, AES‑256 at rest encryption, RBAC enforcement, and immutable audit logging.

## 11. Acceptance Summary
The artifact now provides a complete business‐level definition of the Patient Intake System, including explicit stakeholder needs, fully traceable functional and non‑functional requirements, measurable KPIs, risk mitigations, and compliance assurances aligned with HIPAA and open‑source constraints.
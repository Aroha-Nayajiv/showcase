# Deliverable scope for inception compliance requirements; detailed specification in Executor phase.
                
### 1. Business Objective
The PatientIntake project will deliver a HIPAA‑compliant, open‑source patient intake system that captures demographics, insurance information, and medical history via a structured web form. The solution must enable authorized staff (admin, clinician, front‑desk) to store encrypted records in a local PostgreSQL instance, generate auditable PDF summaries, and operate entirely within an air‑gapped on‑prem environment using Docker Compose.

### 2. Scope Definition
**In‑Scope**
- Field‑level encryption at rest and in transit  
- Role‑based access control (admin, clinician, front‑desk)  
- Immutable audit log for every read/write operation  
- PDF intake summary with dynamic watermark and export timestamp  
- Automated unit and integration tests covering validation, encryption, and access control  
- Docker‑Compose deployment and documented air‑gap setup guide

**Out‑of‑Scope**
- Cloud‑based services or SaaS components  
- Proprietary third‑party libraries (only open‑source allowed)  
- Integration with external EHR systems

### 3. Functional Requirements
| ID   | Description                                                                                                   | Acceptance Criteria                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
|------|-----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-001 | Capture patient demographics, insurance data, and medical history via a web form with field‑level encryption.   | • All fields encrypted at rest with AES‑256.<br>• Transmission protected by TLS 1.3.<br>• Form returns HTTP 200 within 2 seconds for 95 % of trials.<br>• Immutable audit log entry created for each CREATE operation.<br>• Validation rejects incomplete submissions per HIPAA §164.514(b). |
| FR-002 | Persist encrypted submissions in a local PostgreSQL database with RBAC (admin, clinician, front‑desk).               | • Only authorized roles can CREATE/READ/UPDATE/DELETE records.<br>• Every CRUD operation generates an immutable audit log entry with user ID, role, timestamp, and operation type.<br>• Unauthorized attempts receive HTTP 403 and are logged.<br>• Audit log retained for minimum seven years on WORM storage. |
| FR-003 | Generate a PDF intake summary per patient that is exportable only by authorized staff.                           | • PDF generated using wkhtmltopdf (open source).<br>• Dynamic watermark includes exporter name, role, and UTC timestamp.<br>• Export permitted for admin and clinician roles; front‑desk may view read‑only preview.<br>• Export completes within 1 second for 90 % of requests.<br>• Export creates audit log entry with checksum of PDF file.<br>• PDFs stored temporarily in AES‑256 encrypted storage and purged after 24 hours. |
| FR-004 | Provide automated unit and integration tests covering form validation, encryption integrity, and access‑control edge cases. | • Test suite achieves ≥ 90 % code coverage.<br>• CI pipeline fails on any test failure.<br>• Security tests verify that encrypted fields cannot be decrypted without proper keys.<br>• Performance tests confirm response time <200 ms for form submission under load. |
| FR-005 | Enforce role‑based access control & immutable audit logging across the system.                                 | • RBAC matrix defines permissions for admin, clinician, front‑desk.<br>• Every read/write/update/delete operation logs user ID, role, operation type, record identifier, timestamp, and cryptographic hash of record state. • Audit logs stored on PostgreSQL WAL archiving with immutability feature. | • Quarterly compliance audits verify tamper‑evidence of logs. |

### 4. Success Metrics / KPIs
| KPI ID   | Metric                     | Target                                 | Measurement Method                                 |
|----------|----------------------------|----------------------------------------|---------------------------------------------------|
| KPI-001   | Form completion rate       | ≥ 90 % of attempted submissions completed without error   | Daily logs of successful vs attempted submissions |
| KPI-002   | System availability        | ≥ 99.9 % monthly uptime | Prometheus uptime metric aggregated monthly |
| KPI-003   | Audit log completeness | 100 % of read/write operations recorded with immutable checksum verification | Weekly log integrity check script |
| KPI-004 | PDF export security compliance | 100 % of exported PDFs contain correct watermark and timestamp verified by automated scan | Post‑export validation job |

### 5. Governance & Approval Process
All artifacts produced in this inception phase will be reviewed by the Project Sponsor, Compliance Officer, and Technical Lead before sign‑off. The sign‑off checklist includes verification of each functional requirement against its acceptance criteria, confirmation that all KPI targets are measurable, and validation that identified risks have concrete mitigation actions. A RACI matrix (artifact ID RACI-001) defines responsibility for each deliverable.

### 8. Open Issues
* Detailed data model definitions will be produced in the Design phase.
* API contract specifications are deferred to the Detailed Design artifact.

---

*Document prepared by the Senior Software Engineer – Inception Phase – PatientIntake project*

# Inception Phase – Business Vision, Stakeholder Needs, Requirements, and Risks

## 9. Business Vision & Scope
The Patient Intake initiative delivers a HIPAA‑compliant, open‑source patient intake system that captures demographics, insurance data, and medical history through a secure web form. Submissions are encrypted at rest and in transit, stored in a locally hosted PostgreSQL database with role‑based access control (admin, clinician, front‑desk). Authorized staff can generate a PDF summary that includes a watermark and export timestamp. The solution is containerised with Docker Compose for on‑prem deployment and includes automated unit and integration tests.

## 10. Stakeholder Matrix
| Stakeholder | Primary Need | Pain Point / Concern | System Role | Objective |
|---|---|---|---|---|
| Patient (ST-002) | Secure, frictionless intake experience that protects PHI | Fear of data exposure; forms perceived as time‑consuming | View‑only (no write) | OBJ‑001: Ensure HIPAA‑compliant data capture and encryption at rest/in transit |
| Front‑Desk Staff (ST-001) | Rapid entry and verification of patient data to keep clinic flow moving | Manual re‑entry errors; lack of real‑time audit visibility | Create & edit submissions; read all records | OBJ‑002: Complete intake within two minutes per patient |
| Clinician (ST-003) | Immediate access to complete medical history for care decisions | Delayed or incomplete records hinder treatment planning | Read‑only access to submitted forms; can append clinical notes | OBJ‑003: Provide verified data within 30 seconds of submission |
| Administrator (ST-004) | Governance over configuration, user provisioning, and audit log retention | Need centralized control without exposing PHI | Full system privileges; manage roles and audit logs | OBJ‑004: Maintain immutable audit log for seven years meeting HIPAA §164.312(b) |
| Compliance Officer (ST-005) | Assurance that processes meet regulatory mandates | Requires evidence of encryption key management and audit trail completeness | Read‑only access to logs and configuration reports | OBJ‑005: Achieve quarterly compliance audit pass rate ≥ 95% |

## 12. Key Performance Indicators
| ID | Target |
|---|---|
| KPI-001 | Form submission response time <200 ms average |
| KPI-002 | System availability ≥99.9 % monthly |
| KPI-003 | Audit log generated for 100 % of submissions |
| KPI-004 | PDF export includes watermark and timestamp; unauthorized export attempts ≤0 |

## 13. RACI Assignment for Core Activities
| Activity | Responsible (R) | Accountable (A) | Consulted (C) | Informed (I) |
|---|---|---|---|---|
| Define functional requirements (FR‑001 … FR‑005) | Front‑Desk Staff | Administrator | Clinician, Compliance Officer, Patient Representative |
| Design RBAC model and encryption policy (NFR‑001 … NFR‑004) | Administrator | Administrator | Compliance Officer, Security Lead |
| Draft patient consent language and privacy notice | Compliance Officer | Compliance Officer | Legal Counsel, Patient Representative |
| Validate workflow timings and usability thresholds (KPI-001) | Clinician & Front‑Desk Staff | Administrator |
| Approve final scope and sign‑off package | Administrator | Executive Sponsor |

## 14. Narrative Justification
The Patient Intake initiative is anchored in two non‑negotiable constraints: HIPAA compliance and exclusive use of open‑source tooling. Patients require that every field they submit be encrypted both at rest and in transit; the system therefore adopts field‑level AES‑256 encryption and TLS 1.3 transport security, directly satisfying HIPAA §164.312(a)(2)(iv). Their role is limited to view‑only access so they never see other patients’ records.

Front‑Desk staff are the primary data capture engine. Their objective is to complete an intake in under two minutes per patient (OBJ‑002). By granting them create/edit privileges while logging every action, we provide the auditability required by §164.308(a)(1)(ii). The immutable seven‑year audit log addresses both compliance and risk management.

Clinicians need immediate access to a complete medical history to make timely decisions. The RBAC tier gives them read‑only access to submitted forms plus the ability to append clinical notes, ensuring no accidental overwrites of PHI while meeting the <30 second access target.

Administrators oversee system configuration, user provisioning, and key management. Their broad privileges enable them to enforce encryption key rotation every 90 days—a best practice referenced in NIST SP 800‑57 that aligns with HIPAA technical safeguards.

Compliance officers act as auditors of the entire pipeline. By providing them read‑only access to immutable logs and configuration snapshots, we enable quarterly compliance reviews with a target pass rate of 95 % (OBJ‑005). Their involvement in the requirements definition ensures that every functional requirement is traceable to a specific HIPAA safeguard.

The RACI matrix clarifies decision authority and communication flow, preventing scope creep and ensuring that each deliverable is owned by the appropriate role. This structured stakeholder analysis forms the foundation for downstream artifacts—requirements specifications, risk registers, and test plans—by guaranteeing that every business need is captured, quantified, and linked to a measurable objective.

Overall, this analysis delivers a clear, auditable blueprint that aligns stakeholder expectations with regulatory mandates while respecting the open‑source constraint.

## 15. Risk Register
| ID | Description | Likelihood (L/M/H) | Impact (L/M/H) | Mitigation Actions |
|---|---|---|---|---|
| RISK-001 | Unauthorized disclosure of PHI during transmission or storage due to inadequate encryption controls. | M | H | Implement field‑level AES‑256 encryption for all form fields at rest; enforce TLS 1.3 for in‑flight data; rotate keys every 90 days using open‑source Vault alternative; log every key retrieval. |
| RISK-002 | Vulnerabilities in open‑source components (web framework, PDF library) could be exploited to gain access to PHI. | M | H | Adopt continuous vulnerability scanning pipeline using OWASP Dependency‑Check; enforce patching of critical CVEs within seven days; maintain a software bill of materials generated by CycloneDX; assign security champion review. |
| RISK-003 = Misconfiguration of Docker Compose or host OS leading to accidental exposure of PostgreSQL port or audit logs. | L | H Implement CIS Docker Benchmarks hardening; disable external network interfaces on database container; enforce host firewall rules; conduct quarterly configuration audits using Lynis. |
| RISK-004 = Incomplete audit logging or log tampering that would prevent compliance verification during a HIPAA audit. | M | H Design immutable append‑only audit log stored on WORM storage; retain logs for seven years; verify log integrity daily with SHA‑256 hash chaining; restrict log write permissions to system service account only. |

## 16. Detailed Mitigation Plans

### 16.1 Encryption & Key Management (RISK-001)
* Use OWASP‑vetted field‑level encryption libraries written in Go/Python.
* Each form field is encrypted client‑side before transmission; server stores ciphertext only.
* TLS 1.3 termination performed by Caddy reverse proxy configured with strong cipher suites.
* Keys reside in HashiCorp Vault OSS replica; access limited to application service account; every retrieval logged.
* Quarterly key rotation exercises are scheduled and documented in change management logs.

### 16.2 Dependency Hardening (RISK-002)
* Generate SBOM with CycloneDX on each CI run.
* OWASP Dependency‑Check scans for CVE ≥7; build fails on detection.
* Security champion reviews new third‑party packages before merge.
* Monthly security bulletin disseminated to development team.

### 16.3 Container & Host Hardening (RISK-003)
* Apply CIS Docker Benchmarks during image build.
* Use Docker Compose version pinning; set `restart: unless-stopped`.
* Disable external exposure of PostgreSQL port via `ports: []` inside compose file; rely on internal network only.
* Host firewall (`ufw`) blocks inbound traffic except from trusted LAN subnet.
* Quarterly audits executed with Lynis report reviewed by Infrastructure Lead.

### 16.4 Immutable Audit Logging (RISK-004)
* Configure PostgreSQL logical replication to write audit events to separate WORM volume.
* Each log entry includes SHA‑256 hash chained to previous entry.
* Daily cron job verifies hash chain integrity; alerts on mismatch.
* Retention policy enforced via filesystem immutable attribute (`chattr +i`).
* Access to logs limited to Administrator role; read operations logged as well.

## Stakeholder Identification and Needs
| Stakeholder ID | Role | Primary Need |
|---|---|---|
| ST-001 | Clinical staff | Quick access to accurate patient demographics and medical history during care delivery |
| ST-002 | Patients | Assurance that personal health information is collected and stored confidentially |
| ST-003 | Compliance officers | Verifiable audit trails and encryption evidence for regulatory inspections |

## Compliance Alignment
The above controls map directly to HIPAA Security Rule:
* **§164.312(a)(2)(iv) – Encryption** – satisfied by NFR‑004 and field‑level encryption in FR‑001/FR‑002.
* **§164.308(a)(1)(ii) – Audit Controls** – satisfied by RISK-004 immutable logging and FR‑004 access control.
All mitigation actions are recorded in the risk register and reviewed each sprint.

## Deployment & Operational Constraints (Inception Scope)
* **Container Isolation** – Docker Compose declares `network_mode: bridge` and exposes only internal ports; PostgreSQL binds to a private IP (`$IP.1`) within the container network.
* **Host Hardening** – Base OS follows CIS Benchmarks; unnecessary services are disabled.
* **Continuous Hardening Verification** – An automated script runs Lynis weekly; any deviation from the baseline generates an alert for immediate remediation.
* **Disaster‑Recovery Validation** – Quarterly drills confirm that no external ports are unintentionally opened and that backup snapshots of the WORM volume can be restored.
* **Air‑Gap Documentation** – A step‑by‑step guide describes network isolation, physical media handling for backups, and procedures for introducing updates without internet connectivity.
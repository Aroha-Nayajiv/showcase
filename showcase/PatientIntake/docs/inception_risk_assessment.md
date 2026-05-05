# Risk Assessment (Overview)

## Governance Model: Business Vision and High-Level Objectives for PatientIntake

### 1. Business Vision
The PatientIntake system will enable healthcare providers to capture complete patient demographics, insurance details, and medical history through a secure, open‑source web interface while guaranteeing HIPAA compliance. By leveraging only open‑source components and containerized deployment, the solution ensures data residency on‑premises, eliminates vendor lock‑in, and reduces total cost of ownership.

### 2. High‑Level Objectives
1. **Regulatory Compliance (OBJ-001)** – Achieve full HIPAA §164 compliance for encryption at rest (AES‑256) and in transit (TLS 1.3), audit logging, and role‑based access control.
2. **Data Security (OBJ-002)** – Implement field‑level encryption for all PHI fields; enforce least‑privilege RBAC with immutable audit trails retained for seven years.
3. **Operational Efficiency (OBJ-003)** – Reduce average patient intake time to <5 minutes per record while maintaining >95 % form completion accuracy.
4. **Open‑Source Sustainability (OBJ-004)** – Use only community‑maintained libraries and Docker images; provide full source code under an OSI‑approved license.
5. **Scalable Deployment (OBJ-005)** – Enable rapid provisioning of the system in air‑gapped environments via a single `docker‑compose.yml` file.

## Functional Requirements (FR)
| ID | Description | Acceptance Criteria |
|---|---|---|
| FR-001 | Collect patient demographics via encrypted web form | • All demographic fields stored encrypted at rest<br>• Successful submission logged in audit log<br>• Median response time ≤200 ms over 100 test submissions |
| FR-002 | Collect insurance information via encrypted web form | • Insurance fields encrypted at rest<br>• Policy number format validated against regex `^[A-Z0-9]{8,12}$`<br>• Audit entry created for each submission |
| FR-003 | Collect medical history via encrypted web form | • History text encrypted at rest<br>• Mandatory clinical fields enforced before submit<br>• Submission success rate ≥95 % across 1 000 trial entries |
| FR-004 | Store submissions in PostgreSQL with RBAC and immutable audit log | • Role checks prevent unauthorized reads/writes<br>• Audit log retains entries for 7 years without alteration<br>• Quarterly tamper‑evidence verification script passes 100 % |
| FR-005 | Generate PDF intake summary with watermark and timestamp | • PDF includes staff watermark and export timestamp in metadata<br>• Only roles Clinician and Administrator can trigger export<br>• Export action creates audit log entry |
| FR-006 | Export PDF only to authorized staff | • API layer enforces RBAC for PDF export<br>• Unauthorized export attempts logged as security events with severity HIGH |
| FR-007 | Automated unit & integration tests covering validation, encryption, access control | • Test suite achieves ≥90 % code coverage across all modules<br>• CI pipeline fails on any security‑related test failure |
| FR-008 | Deploy via Docker Compose in air‑gapped environment | • Single `docker‑compose.yml` provisions all services without external network calls<br>• Deployment script validates air‑gap constraints before start |

## Success Criteria / KPIs
| KPI ID | Metric | Target |
|---|---|---|
| KPI-01 | Form completion rate | ≥95 % of attempted submissions completed without error |
| KPI-02 | Average intake time per patient record | ≤5 minutes per record measured by timestamp delta from start to submit |
| KPI-03 | Audit log entry generation accuracy | 100 % of read/write operations produce a verifiable log entry |
| KPI-04 | Deployment time in air‑gapped environment | ≤30 minutes from start of provisioning to fully operational system |

## Stakeholder Identification and Access Needs
| Stakeholder Role | Primary Need | Key Pain Point | RBAC Tier | Linked Objective |
|---|---|---|---|---|
| Patient (ST-01) | Securely provide personal and health data during intake | Fear of data exposure and lack of trust in electronic forms | End‑User (read‑only for own record) | OBJ-001 |
| Front‑Desk Staff (ST-02) | Capture completed intake forms quickly and accurately | Manual re‑entry of paper forms leads to errors and delays | Operator (create / edit limited fields) | OBJ-003 |
| Clinician (ST-03) | Retrieve complete medical history for care decisions | Incomplete or inaccessible records impede treatment | Clinician (read / update clinical fields) | OBJ-003 |
| System Administrator (ST-04) | Manage system configuration, user accounts, and audit logs | Complex tooling can lead to mis‑configuration and audit gaps | Administrator (full control) | OBJ-002 |
| Compliance Officer (ST-05) | Verify HIPAA compliance and audit readiness | Lack of centralized evidence makes audits costly | Auditor (read‑only audit logs) | OBJ-001 |

### Detailed Role Narratives
1. **Patient (ST-001)** – The ultimate data subject whose demographic, insurance, and medical history information is collected. Patients require assurance that every field is encrypted at rest (AES‑256) and in transit (TLS 1.3). The system presents a clear consent statement referencing HIPAA §164.508 and captures a signed acknowledgment before any PHI is stored.
2. **Front‑Desk Staff (ST-002)** – First human touchpoint after a patient arrives. Their primary need is a streamlined web form that auto‑populates known data from prior visits, reducing manual entry errors. They may edit only non‑clinical fields while the system enforces field‑level encryption for any clinical data they touch.
3. **Clinician (ST-003)** – Physicians, nurses, and allied health professionals rely on immediate access to a complete, accurate intake summary to make diagnostic and treatment decisions. They need read‑write access to clinical sections of the record but must not see unrelated administrative metadata. Every read operation is logged with timestamp and user ID.
4. **System Administrator (ST-004)** – Responsible for provisioning Docker containers, managing PostgreSQL roles, and rotating encryption keys using an open‑source key vault. Their actions are critical for maintaining system integrity; therefore they receive full administrative privileges but must operate under documented change‑control procedures.
5. **Compliance Officer (ST-005)** – Oversees adherence to HIPAA Security Rule and internal policies. This role requires read‑only access to immutable audit logs and the ability to generate compliance reports on demand. The officer’s involvement ensures that any deviation from the defined RBAC model is detected early.

## Access Control Summary
The RBAC model maps directly to the five tiers listed above: End‑User, Operator, Clinician, Administrator, and Auditor. Each tier inherits the minimum‑necessary principle defined in 45 CFR §164.312(a)(1). By aligning stakeholder needs with these tiers, the PatientIntake system can demonstrate compliance during both internal reviews and external audits.

## Alignment with Project Objectives
All stakeholder needs are tied to measurable objectives (OBJ‑001 through OBJ‑005). These objectives are tracked via the KPIs defined earlier—consent capture rate, average processing time, system uptime, audit log retention compliance, and audit pass rate—ensuring any change in stakeholder requirements can be evaluated against concrete business outcomes.

## Scope Definition
The scope of this risk assessment covers all business processes and data flows directly related to the PatientIntake web‑based intake system described in the project brief. In‑scope items include patient demographic capture, insurance information collection, medical history entry, encrypted storage in a local PostgreSQL instance, role‑based access controls (admin, clinician, front‑desk), audit logging of every read/write operation, PDF summary generation with watermark and timestamp, and the Docker‑Compose air‑gap deployment. Out‑of‑scope items are any third‑party cloud services, external analytics platforms, and legacy systems not integrated with PatientIntake.

## Risk Assessment
| Risk ID | Description | Likelihood | Impact | Mitigation Actions |
|---|---|---|---|---|
| RISK-01 | Unauthorized data exposure during transmission or storage | Medium | High | • Enforce TLS 1.3 for all network traffic<br>• AES‑256 field encryption at rest<br>• Quarterly penetration testing and key rotation every 90 days |
| RISK-02 | Vulnerabilities in open‑source components used in stack (e.g., Flask, PostgreSQL) | Medium | Medium | • Continuous dependency scanning with OWASP Dependency‑Check nightly<br>• Immediate patching of CVEs within 48 hours<br>• Maintain a Bill of Materials for all third‑party libraries |
| RISK-03 | Misconfiguration of Docker Compose leading to open ports or weak defaults in air‑gap environment | Low → Medium after mitigation | High | • Harden Docker daemon configuration (no privileged mode)<br>• Run `docker-compose config --quiet` validation script before deployment<br>• Automated security hardening checklist executed by System Administrator |
| RISK-04 | Incomplete audit logs causing compliance gaps (HIPAA §164.312(b)) | Low | High | • Implement PostgreSQL row‑level security with immutable append‐only tables<br>• Daily checksum verification job<br>• Annual external audit of log completeness |
| RISK-05 | Insider threat – privileged user misuse of PHI data | Medium | High | • Enforce separation of duties: no single user has both admin and auditor roles<br>• Real‑time monitoring alerts on anomalous read patterns<br>• Mandatory quarterly security awareness training |

### Mitigation Summary
All high‑impact risks are addressed through technical safeguards (encryption, TLS), process controls (role segregation, audit log retention), and governance actions (regular security training, incident response plan). Ownership is assigned to the Security Lead for technical mitigations and the Compliance Officer for policy enforcement.
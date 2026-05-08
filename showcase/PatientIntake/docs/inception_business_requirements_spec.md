# Business Requirements Specification

## Business Vision and Scope for PatientIntake

The PatientIntake project delivers a HIPAA‑compliant, open‑source SaaS solution that enables health‑care organizations to capture patient demographics, insurance information, and medical history through a secure web‑based intake form. The vision is to provide a high‑availability, multi‑tenant service that protects Protected Health Information (PHI) while reducing manual data entry, improving data quality, and supporting regulatory auditability.

### 1. Strategic Objectives
1. **Secure Data Capture** – End‑to‑end confidentiality and integrity of PHI during collection, transmission, storage, and export.
2. **Operational Efficiency** – Automate the intake workflow to cut manual processing time by at least **40 %** compared with paper forms.
3. **Regulatory Assurance** – Achieve full HIPAA compliance and support SOC 2 / GDPR controls for SaaS customers.
4. **Scalable SaaS Delivery** – Support horizontal scaling and tenant isolation to serve multiple clinics from a single deployment.
5. **Auditability & Transparency** – Provide immutable audit logs and PDF intake summaries with watermarks for forensic review.

### 2. Scope Definition
| Feature | In‑Scope | Out‑of‑Scope |
|---|---|---|
| Web‑based patient intake form | ✅ Secure, field‑level encryption, validation | ❌ Development of custom mobile apps |
| PostgreSQL data store with RBAC | ✅ Role‑based access (admin, clinician, front‑desk) | ❌ Use of proprietary DB engines |
| PDF summary generation | ✅ Watermarked, timestamped export for authorized staff | ❌ Integration with external document management systems |
| Automated testing suite | ✅ Unit & integration tests for validation, encryption, access control | ❌ Performance testing beyond baseline |
| Docker Compose deployment | ✅ Air‑gapped on‑prem setup guide | ❌ Cloud‑native orchestration (K8s) |

### 3. Functional Requirements
| Requirement ID | Description | Acceptance Criteria |
|---|---|---|
| FR-001 | Collect patient demographics via a structured web form with field‑level encryption at rest (AES‑256) and in transit (TLS 1.2+). | • All form fields are encrypted before being persisted.<br>• TLS handshake succeeds with forward secrecy.<br>• Submission returns a signed receipt visible to the patient. |
| FR-002 | Capture insurance information securely and store it in PostgreSQL with row‑level security. | • Insurance fields are encrypted using pgcrypto.<br>• Only users with the *Front‑Desk* role can view masked insurance numbers.<br>• Audit log records every read/write operation on insurance data. |
| FR-003 | Record medical history details with validation rules (e.g., required allergies, medication list). | • Validation errors are displayed inline.<br>• Data passes schema validation before encryption.<br>• No PHI is stored in plaintext at any point. |
| FR-004 | Generate a PDF intake summary per patient that includes a visible watermark and export timestamp visible only to authorized staff. | • PDF contains patient name, visit date, and a watermark “Confidential – PHI”.<br>• Export timestamp is embedded in PDF metadata.<br>• Only *Clinician* and *Administrator* roles can trigger PDF generation. |
| FR-005 | Implement role‑based access control (RBAC) for admin, clinician, front‑desk users with least‑privilege permissions. | • Access matrix matches Table 3 (see below).<br>• Unauthorized attempts are logged and result in a 403 response.<br>• Quarterly review confirms no privilege creep. |
| FR-006 | Maintain an immutable audit log for every read/write operation on PHI retained for seven years. | • Log entries are append‑only and signed with SHA‑256. • Retention policy automatically archives logs after seven years without deletion. | • Log integrity verified weekly via hash chain verification script. |
| FR-007 | Deploy the entire stack via Docker Compose for on‑prem environments with an air‑gap setup guide. | • Docker Compose file provisions PostgreSQL, web server, Vault (for key storage), and PDF generator. • Installation guide includes steps to configure an isolated network interface. | • Deployment completes without external internet access. |

### 4. Key Performance Indicators
| KPI ID | Target Metric |
|---|---|
| KPI-001 (linked to OBJ‑001) | 100 % of submissions encrypted at rest and in transit as verified by automated security scans. |
|
| KPI-002 (linked to OBJ‑002) | Average intake processing time ≤ 30 seconds per patient record after automation. |
|
| KPI-003 (linked to OBJ‑003) | Data availability ≥ 99.9 % measured by uptime monitoring over a month. |
|
| KPI-004 (linked to OBJ‑004) | 100 % of generated PDFs contain correct watermark and timestamp metadata. |
|
| KPI-005 (linked to OBJ‑005) | Audit log completeness ≥ 99.9 % with zero missing entries over a year. |
|

### 6. Traceability Matrix
| Artifact ID | Linked Objective(s) |
|---|---|
| FR-001 – FR-007 | OBJ-001, OBJ-002, OBJ-003 |
| NFR-001 – NFR-004 | OBJ-001, OBJ-003 |
| KPI-001 – KPI-005 | OBJ-001 – OBJ-005 |
| RISK-001 – RISK-006 | OBJ‑001 – OBJ‑005 |

*All requirements are traceable to the strategic objectives defined in Section 1 and will be validated against the acceptance criteria listed above.*

## Stakeholder Matrix
| Stakeholder ID | Role | Primary Concern |
|---|---|---|
| ST-001 | Patient | Privacy of PHI and ease of data entry |
| ST-002 | Clinic Staff | Efficient workflow and access to patient data |
| ST-003 | Compliance Officer | Regulatory compliance and auditability |

## Success Criteria & KPIs
| KPI ID | Metric |
|---| ---|
| KPI-​001 | PHI Encryption Compliance Rate – 100 % records encrypted at rest and in transit.| 
| KPI-​002 | RBAC Enforcement Accuracy – 100 % access attempts correctly authorized/denied.| 
| KPI-​003 | Audit Log Integrity Score – ≥99.9 % hash verification success rate.| 
| KPI-​004 | System Availability SLA Compliance – ≥99.9 % monthly uptime.| 
| KPI-​005 | Incident Response SLA Adherence – 100 % tickets created within 1 minute of detection.| 

## Risks and Mitigations
| Risk ID | Description | Likelihood | Impact | Mitigation |
|---| ---| ---| ---| ---|
| RISK-​001 | Unauthorized PHI exposure during transmission.| L | H | Enforce TLS 1.3 with forward secrecy; quarterly external penetration tests; implement HSTS headers.| 
| RISK-​002 | Failure to meet HIPAA and SOC 2 compliance requirements, leading to regulatory penalties.| L | H | Establish compliance governance framework with documented policies, quarterly internal audits, external audit readiness checklists; maintain immutable WORM audit logs for 7 years; map controls to HIPAA §164.312 and SOC 2 Trust Services Criteria.| 
| RISK-​003 | Performance degradation under peak load causing unacceptable response times (>200 ms) and potential SLA breach.| M | M | Design SaaS platform for horizontal scalability using Docker Compose Swarm mode; conduct load testing to verify <200 ms p95 response; implement auto-scaling thresholds and resource quotas; monitor performance via Prometheus/Grafana dashboards.| 
| RISK-​004 | Low user adoption due to complex intake workflow or lack of trust in data security.| M | M | Conduct user-centered design workshops with front-desk staff and clinicians; provide in-app security cues (lock icons) and transparent privacy notices; deliver role-based training sessions and quick-start guides; measure adoption via form completion rate >90 % within 30 days of launch.| 
| RISK-​005 | Operational disruption from air-gap environment constraints (e.g., inability to apply patches or updates).| L | M | Create offline update pipeline using signed Docker images stored on secure removable media; schedule monthly maintenance windows; maintain documented disaster-recovery runbook with RTO <4 hours; assign dedicated on-prem support engineer.| 

## Acceptance Conditions
* All five success criteria are met in a production-like staging environment.
* Evidence of KPI measurement processes is documented in the Project Governance Plan.
* Stakeholder sign-off obtained from Compliance Officer, Front‑Desk Manager, and Clinical Lead confirming alignment with operational expectations.

## Governance Processes
1. **Policy Documentation** – Master Security Policy versioned in repository, reviewed annually.
2. **Change Management** – All changes affecting PHI handling must pass CAB review with documented risk assessment.
3. **Continuous Monitoring** – SIEM aggregates logs; alerts trigger incident response workflow.
4. **Training & Awareness** – Quarterly training for all user roles on HIPAA best practices.
5. **Compliance Audits** – Annual external HIPAA compliance audit; findings tracked in compliance register.
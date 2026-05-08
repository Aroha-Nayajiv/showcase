# Stakeholder Roles and Responsibilities Matrix

### Strategic Objectives
1. **Secure Data Capture** – Every field entered through the web form is encrypted at rest with AES‑256 and in transit with TLS 1.2+ (FR‑001).  
2. **Auditability** – Immutable audit log retained for seven years (FR‑003).  
3. **Operational Efficiency** – Reduce manual data‑entry time by at least 40 % compared with paper‑based intake (OBJ‑002).  
4. **Scalable Private‑SaaS Delivery** – Support up to **5 000 concurrent patients per tenant** while maintaining ≤200 ms response time (p95) and 99.9 % uptime (OBJ‑001).  
5. **Compliance‑First Deployment** – Provide an air‑gapped Docker‑Compose package with documented installation, key‑rotation, and disaster‑recovery procedures (FR‑006).

### Scope Definition
**In‑Scope**
- Structured web intake form with field‑level encryption (FR‑001).
- Role‑based access control for Admin, Clinician, Front‑Desk staff (FR‑002).
- Full immutable audit log (FR‑003).
- PDF summary generation with watermark and export timestamp (FR‑004).
- Automated unit and integration test suite covering validation, encryption and access control (FR‑005).
- Docker‑Compose deployment guide for air‑gapped environments (FR‑006).
- **Multi‑tenancy isolation** per clinic instance (FR‑007).

**Out‑Of‑Scope**
- Integration with external payer APIs.
- Mobile native applications (future phase).
- Real‑time analytics dashboards (future phase).

## 1. Narrative Summary
**Patient Interaction** – Patients use a responsive React front end served by a Flask API. The form encrypts each field client‑side with AES‑256 before transmission; all traffic is forced over HTTPS using TLS 1.2+ enforced by Nginx reverse proxy. Upon receipt the server stores each encrypted field in PostgreSQL using per‑record keys managed by HashiCorp Vault.

**Front‑Desk Workflow** – After submission, Front‑Desk staff access a dashboard that highlights missing mandatory fields and validation errors in real time. Their UI components are scoped to the *Operator* RBAC tier defined in FR‑002, allowing creation of new records and view of non‑clinical fields only.

**Clinician Access** – Clinicians log in via SSO (OpenID Connect) and receive read access to all patient records plus write permission for clinical notes. The RBAC policy prevents modification of demographic fields, satisfying FR‑002 clause 3.

**System Administration** – Administrators provision new tenant instances by cloning the Docker‑Compose stack and configuring isolated PostgreSQL schemas per clinic. Quarterly key rotation is performed via automated Vault jobs; all privileged actions are recorded in the immutable audit log (FR‑003).

**Compliance Reporting** – Compliance officers generate audit reports through a read‑only API endpoint that streams tamper‑evident logs. PDF intake summaries include a visible watermark “Confidential – PatientIntake” and an export timestamp embedded in the PDF metadata (FR‑004).

## 2. Responsibility Alignment
| Stakeholder | Responsibility | Linked Objective(s) |
|---|---|---|
| Patient (ST-001) | Submit encrypted intake data via web form | OBJ-001 |
| Front‑Desk Staff (ST-002) | Capture data accurately; correct validation errors; create records | OBJ-002 |
| Clinician (ST-003) | Review full intake record; add clinical notes; ensure availability during clinic hours | OBJ-003 |
| System Administrator (ST-004) | Deploy/maintain Docker stacks; rotate keys; monitor audit logs; ensure 99.9 % uptime | OBJ-001, OBJ-004 |
| Compliance Officer (ST-005) | Conduct periodic compliance audits; generate immutable reports; verify retention policy | OBJ-005 |

## 3. Requirements Traceability Matrix
| Requirement ID | Description | Acceptance Criteria | Owner |
|---|---|---|---|
| FR-001 | Secure Patient Demographics Capture | 1. HTTPS with TLS 1.2+ enforced; lower protocols rejected.<br>2. Per‑record AES‑256 encryption at rest.<br>3. Form completion ≤3 s average for 5 KB payload (p95 ≤4 s).<br>4. WCAG 2.1 AA compliance. | ST-001 |
| FR-002 | Role‑Based Access Control (RBAC) for Clinical Staff | Admin: full CRUD.<br>Clinician: read all + update clinical notes only.<br>Front‑Desk: create records & view non‑clinical fields.<br>Violations logged as WARN and return HTTP 403. | ST-004 |
| FR-003 | Immutable Audit Log | Log entries contain UTC timestamp, user ID, operation type, record ID, outcome.<br>Stored using PostgreSQL WAL append‑only with checksums.<br>Retrieval latency ≤200 ms for up to 10 M rows.<br>Quarterly verification confirms 100 % integrity. | ST-004 |
| FR-004 | PDF Intake Summary Generation | Authorized staff can generate PDF with watermark “Confidential – PatientIntake”.<br>Export timestamp embedded in PDF metadata.<br>PDF generation completes within 2 s per request.<br>Access limited to Admin & Clinician roles. | ST-005 |
| FR-005 | Automated Test Suite | Unit tests cover form validation, encryption/decryption cycles, RBAC enforcement.<br>Integration tests simulate end‑to‑end submission → storage → PDF generation.<br>Coverage ≥85 % across critical paths. | ST-004 |
| FR-006 | Air‑Gapped Docker Compose Deployment Guide | Step‑by‑step guide for installing stack on isolated network.<br>Includes key generation, vault init, backup/restore procedures.<br>Verification checklist ensures compliance before go‑live. | ST-004 |
| FR-007 *New* – Multi‑Tenancy Isolation per Clinic | Each tenant runs an isolated PostgreSQL schema and separate Docker network.<br>Cross‑tenant data leakage prevented by schema level permissions and network segmentation.<br>Performance benchmark: ≤150 ms latency for intra‑tenant queries under load of 5 000 concurrent users. | ST-004 |

## 4. Success Metrics
- **Encryption compliance**: 100 % of submissions encrypted at rest and in transit (OBJ-001).
- **Audit log completeness**: 100 % of operations recorded with tamper evidence (OBJ-004).
- **Intake processing time**: Average ≤2 minutes per patient for front desk staff (OBJ-002).
- **System availability**: ≥99.9 % uptime measured over a rolling 30‑day window (OBJ-001).
- **Compliance audit outcome**: Zero critical findings in external HIPAA/SOC 2 audit (OBJ-005).

## Business Vision
The PatientIntake SaaS solution will deliver a **HIPAA‑compliant, open‑source patient intake platform** that enables on‑premise, air‑gapped deployment for healthcare providers. The platform captures patient demographics, insurance details, and medical history through a secure web form, stores the data in an encrypted PostgreSQL database, and generates tamper‑evident PDF intake summaries for authorized staff. By leveraging Docker‑Compose for container orchestration, the solution supports horizontal scaling, high availability, and rapid disaster‑recovery while remaining fully open‑source.

## Stakeholder Identification & Interaction Model
| Stakeholder | Role | Primary Interests | Responsibilities |
|--------------|------|------------------|-------------------|
| Patients | End‑user | Privacy of PHI, ease of data entry | Provide accurate demographic and medical information via the web form |
| Front‑Desk Staff | Operator | Quick data capture, minimal training | Initiate form sessions, verify successful submission, view audit logs for errors |
| Clinicians | Data Consumer | Access to complete, verified intake records | Retrieve PDF summaries, annotate records, request data corrections |
| Security Lead | Governance | Compliance with HIPAA, SOC 2, and internal policies | Review encryption key rotation, audit log integrity, risk mitigation effectiveness |
| Compliance Officer | Governance | Audit readiness, documentation completeness | Validate that audit logs meet retention policies, certify that all controls are documented |
| DevOps Lead | Operations | Reliable deployment in air‑gap environments | Maintain Docker‑Compose scripts, ensure no outbound network calls during startup |
| Product Manager | Business | Alignment with market expectations for SaaS health solutions | Prioritize feature backlog, coordinate stakeholder reviews |

### FR-001: Secure Patient Data Collection
- **Description**: Collect patient demographics, insurance information, and medical history via a structured web form.
- **Security Controls**: Client‑side AES‑256 encryption of PHI fields; TLS 1.2+ enforced for all HTTP traffic.
- **Performance**: 95 % of submissions complete within 3 seconds under normal load.
- **Acceptance Criteria**:
  1. Form fields are encrypted before transmission.
  2. Server rejects any request not negotiated over TLS 1.2+.
  3. Load test shows ≤3 seconds latency for 95 % of submissions (500 concurrent users).

### FR-002: Role‑Based Access Control (RBAC)
- **Description**: Implement three roles – Administrator, Clinician, Front‑Desk – with least‑privilege permissions.
- **Controls**: PostgreSQL row‑level security; application middleware enforces role checks on every endpoint.
- **Acceptance Criteria**:
  1. Administrators can create, read, update, delete any record.
  2. Clinicians can read and generate PDFs but cannot delete records.
  3. Front‑Desk can create new records and view their own submissions only.

### FR-003: Immutable Audit Logging
- **Description**: Record every read/write operation on PHI with immutable timestamps.
- **Controls**: pg_audit extension with hash‑chaining; logs retained for 7 years on WORM storage.
- **Acceptance Criteria**:
  1. Each operation generates a log entry within 5 seconds.
  2. Log entries are cryptographically linked; tampering detection alerts the Security Lead.

### FR-004: PDF Intake Summary Generation
- **Description**: Generate a PDF per patient that includes a watermark and export timestamp.
- **Security Controls**: PDF is digitally signed; watermark cannot be removed without invalidating the signature.
- **Access Controls**: Only Administrator or Clinician roles may invoke generation.
- **Acceptance Criteria**:
  1. PDF contains patient data, visible watermark on every page, and timestamp in metadata.
  2. Unauthorized generation attempts are logged as access‑denied events.
  3. PDF generation completes within 2 seconds for a typical record (≤10 KB).

### FR-005: Automated Test Suite
- **Description**: Provide a CI‑integrated test suite covering unit and integration tests for form validation, encryption handling, RBAC enforcement, audit logging, and PDF generation.
- **Acceptance Criteria**:
  1. Minimum overall test coverage of 85 % measured by coverage.py.
  2. CI pipeline blocks merges on any test failure.
  3. At least three negative edge cases per functional area are exercised.
  4. Total test execution time ≤5 minutes on a standard CI runner (2 CPU, 4 GB RAM).

### FR-006: Docker‑Compose Deployment for Air‑Gap Environments
- **Description**: Containerize the entire stack and orchestrate via a single `docker-compose.yml` file suitable for isolated data‑center deployments.
- **Acceptance Criteria**:
  1. All images are pulled from an internal registry; no external network calls during startup.
  2. System startup time ≤60 seconds from `docker-compose up`.
  3. Documentation includes a step‑by‑step air‑gap setup guide verified on a fresh offline host.

## Non‑Functional Requirements (Quality Attributes)
| ID | Category | Requirement | Threshold | Verification Method |
|----|----------|------------|-----------|---------------------|
| NFR-001 | Security | Data at rest encrypted with AES‑256; key rotation every 90 days | AES‑256 encryption for all PHI fields; rotation schedule enforced | Automated compliance scan (OpenSCAP) & quarterly key‑management audit |
| NFR-002 | Security | Data in transit protected with TLS 1.2+ and client‑side field encryption | TLS 1.2+ on all endpoints; RSA‑2048 client encryption before transmission | OWASP ZAP penetration test & SSL Labs cipher suite verification |
| NFR-003 | Performance | Form submission latency ≤200 ms (95th percentile) under load of 500 concurrent users | ≤200 ms response time measured by Locust.io load test |
| NFR-004 | Scalability | Horizontal scaling up to 10 additional containers while maintaining response time ≤200 ms | Successful scaling test in Docker Compose swarm mode |
| NFR-005 | Availability | Service uptime ≥99.9 % monthly |
| NFR-006 | Backup & DR | Daily incremental backups retained 30 days; RTO ≤4 h; RPO ≤15 min |
| NFR-007 | Audit Logging | Immutable audit log retained for 7 years; log entry written within 5 seconds |

## Risks and Mitigations
| ID | Risk Description | Impact (M/L/H) | Likelihood (L/M/H) | Mitigation Actions |
|----|-------------------|-------------------|
| RISK-001 | Unauthorized disclosure of PHI during transmission or at rest due to inadequate encryption controls | H | M | Implement AES‑256 at rest and TLS 1.3 in transit; rotate keys every 90 days; use libsodium for client‑side encryption |
| RISK-002 | Incomplete or tampered audit logs jeopardizing HIPAA compliance | H | L | Use pg_audit with hash chaining; store logs on WORM storage; weekly integrity verification scripts |
| RISK-003 | Performance degradation from encryption overhead causing >200 ms latency | M | M | Conduct JMeter load testing on encrypted payloads; tune PostgreSQL parameters; cache non‑PHI reference data in Redis |
| RISK-004 | Low user adoption due to complex UI or privacy concerns (form completion <70 %) |
| RISK-005 | Operational outage from misconfigured Docker Compose in air‑gap environment |
| RISK-006 | Key management failure leading to loss of decryption capability |

## Acceptance Criteria Summary
All functional requirements (FR‑001‒FR‑006) must meet the listed acceptance criteria; non‑functional thresholds (NFR‑001‒NFR‑007) must be verified through automated scans or load tests; each identified risk must have at least one concrete mitigation action documented and scheduled for periodic review.

## Governance & Review Cadence
* **Security Lead** – Quarterly review of encryption key management and audit log integrity.
* **Compliance Officer** – Annual validation of HIPAA/SOC 2 audit readiness.
* **Performance Engineer** – Pre‑release load testing against NFR‑003 and NFR‑004 thresholds.
* **Product Manager** – Sprint‐end stakeholder satisfaction survey focusing on UI usability (addresses RISK‑004).
* **DevOps Lead** – Semi‑annual disaster‑recovery drill covering air‑gap deployment (addresses RISK‑005).

---
*Document version*: 1.0 – Refined inception artifact generated by Refiner (Senior Business Analyst).

# Business Vision

**Vision Statement**: Deliver a HIPAA‑compliant, on‑premise patient intake platform that enables clinics to capture demographic, insurance, and medical history data securely, generate auditable PDF summaries, and operate without external cloud dependencies.

# Stakeholder Identification

| Stakeholder ID | Role | Primary Need |
|---|---|---|
| ST-001 | Patients | Confidential data capture and receipt of a verifiable intake summary |
| ST-002 | Clinic Staff (Front‑Desk) | Efficient data entry workflow with role‑based access |
| ST-003 | Clinicians | Immediate access to complete, immutable patient records |
| ST-004 | Compliance Officer | Evidence of encryption, audit logging, and controlled PDF export |

# Functional Requirements

| Requirement ID | Description | Acceptance Criteria |
|---|---|---|
| FR-001 | Collect patient demographics, insurance information, and medical history via a structured web form with field‑level encryption at rest and in transit. | All form fields are encrypted using AES‑256 at rest and TLS 1.2+ in transit; successful submission stores encrypted data in PostgreSQL; 100 % of test submissions pass validation. |
| FR-002 | Role‑based access control (RBAC) for admin, clinician, and front‑desk users. | Access logs show each user can perform only actions permitted by their role; audit of 1 000 random sessions shows 0 % privilege escalation incidents. |
| FR-003 | Immutable audit log of every read/write operation on patient records. | Log retention is 7 years on write‑once storage; log completeness > 99.5 % verified by checksum reconciliation. |
| FR-004 | PDF intake summary generation with watermark and export timestamp visible only to authorized staff. | PDF contains dynamic watermark "Confidential – Patient ID: {ID}" and timestamp; 100 % of exported PDFs verified to contain the watermark in automated sampling. |
| FR-005 | Deploy the entire stack via Docker‑Compose for on‑prem air‑gap environments. | Deployment script completes without external network calls; installation checklist passes on three distinct air‑gap test labs. |

# Key Performance Indicators

| KPI ID | Metric | Target |
|---|---|---|
| KPI-001 | System Availability (Uptime) | ≥ 99.9 % monthly uptime (Prometheus monitoring) |
| KPI-002 | Security Incident Rate | 0 incidents in first 90 days post‑launch (Incident Management System) |
| KPI-003 | Audit Log Completeness | ≥ 99.5 % of transactions logged (daily checksum comparison) |
| KPI-004 | Form Completion Rate | ≥ 90 % of sessions result in successful submission (web analytics) |
| KPI-005 | Deployment Time in Air‑Gap Lab | ≤ 30 minutes from start to running service (timestamp logs) |

# Scope Boundary

**In Scope**: All functional requirements listed above, HIPAA‑compliant encryption, RBAC, immutable audit logging, PDF generation with watermarking, Docker‑Compose deployment for air‑gap environments, and documentation of the air‑gap setup process.

**Out of Scope**: Integration with external EHR systems, mobile native applications, cloud‑hosted SaaS offerings, advanced analytics beyond basic reporting.

# Risks and Mitigations

| Risk ID | Description | Mitigation |
|---|---|---|
| RISK-001 | Data breach due to inadequate encryption key management. | Implement hardware security module (HSM) for key storage; rotate keys quarterly; enforce least‑privilege access to keys. |
| RISK-002 | Regulatory non‑compliance (HIPAA, SOC 2). | Conduct quarterly compliance audits; maintain up‑to‑date policy documents; automate evidence collection for audit trails. |
| RISK-003 | Performance bottlenecks in encryption/decryption under load. | Benchmark encryption library; enable TLS session resumption; scale horizontally via container replication. |
| RISK-004 | User adoption resistance due to complex UI. | Conduct usability testing with patient focus groups; iterate UI based on feedback; provide training videos for staff. |
| RISK-005 | Operational failure in air‑gap deployment (missing dependencies). | Pre‑deployment checklist includes all required binaries; use offline package repository; validate script on three separate labs before release. |

# Governance & Compliance Framework

All requirements are traceable to the defined KPIs and risks. Continuous monitoring will be performed via Prometheus/Grafana dashboards, and audit logs will be retained for seven years on write‑once storage to satisfy both HIPAA and internal governance policies.
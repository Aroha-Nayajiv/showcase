# Stakeholder Analysis (Overview)

### 1. Business Vision
The PatientIntake system will enable healthcare organizations to capture complete patient demographics, insurance details, and medical history through a secure, web‑based form that is fully open‑source. Leveraging community‑maintained components avoids vendor lock‑in, reduces licensing costs, and aligns with the organization’s strategic goal of sustainable, auditable technology stacks. Primary business outcomes are: (a) 30 % reduction in manual data entry errors, (b) 20 % faster clinician access to intake data (target <200 ms), and (c) demonstrable HIPAA compliance that supports regulatory audits without third‑party services.

### 2. Project Scope
In‑scope items include:
- A responsive web form that encrypts each field at rest using AES‑256 and in transit via TLS 1.3.
- A locally deployed PostgreSQL database with role‑based access control for Admin, Clinician, and Front‑Desk roles.
- Immutable audit logging of every read and write operation retained for seven years.
- PDF generation of intake summaries with watermark and timestamp on each export.
- Automated unit and integration test suites covering validation, encryption, and access‑control edge cases.
- Docker‑Compose orchestration for air‑gapped deployment with full documentation.
Out‑of‑scope items are any cloud‑based services, proprietary licensing components, and integration with external billing systems beyond the defined PDF export.

### 3. Compliance Objectives
- **HIPAA Security Rule**: All PHI must be encrypted at rest (AES‑256) and in transit (TLS 1.3) per 45CFR§164.312(a)(2)(iv).
- **Auditability**: Logs must capture user ID, timestamp, operation type, and record identifier, achieving 100 % completeness as measured by nightly log‑validation scripts (KPI‑003).
- **Access Control**: Role‑based permissions enforce least privilege; only Clinicians and Admins may view full records, Front‑Desk may edit but not export (FR‑002).
- **Data Retention**: Audit logs retained immutable for 7 years per HIPAA §164.310(d)(2)(i).
- **Open‑Source Assurance**: All third‑party libraries must have active community support and no known critical CVEs; quarterly vulnerability scans will verify compliance.

### 4. Stakeholder Matrix
| Stakeholder | Need | Fear | Role | Owner | Linked Functional Requirements |
|------------|------|------|------|-------|-------------------------------|
| Patient | Trust that personal health information is protected | Data breach | Data Subject | Compliance Officer | FR‑001, FR‑006 |
| Front‑Desk Staff | Fast, accurate data entry with real‑time validation | Manual re‑work due to validation errors | Edit only | Operations Lead | FR‑004, FR‑005 |
| Clinician | Immediate access to complete intake data for care decisions | Delayed access slows treatment | View & Export | Clinical Lead | FR‑001, FR‑003 |
| Administrator | Secure configuration and auditability of the system | Complex policy enforcement across roles | Full control | IT Manager | FR‑002, FR‑007 |
| Compliance Officer | Evidence of HIPAA adherence for audits | Lack of verifiable logs and encryption proof | Audit oversight | Compliance Officer | FR‑002, FR‑003, FR‑008 |

### 5. Success Metrics / KPIs
| KPI ID | Description | Target | Measurement Method |
|--------|-------------|--------|----------------------|
| KPI‑001 | Encryption at Rest Compliance | 100 % of PHI fields encrypted with AES‑256 | Automated schema scan weekly |
| KPI‑002 | Form Submission Latency (p95) | ≤200 ms per field submission | Load testing tool measuring end‑to‑end response |
| KPI‑003 | Audit Log Completeness | 100 % of read/write events logged | Log integrity script comparing DB ops vs log entries |
| KPI‑004 | PDF Export Watermark Accuracy | 100 % of exported PDFs contain timestamped watermark with user ID | Automated PDF inspection batch job |
| KPI‑005 | Open‑Source License Compliance | 0 % prohibited licenses used | SPDX license scanner quarterly |

### 7. Consolidated Risk Register
| Risk ID | Description | Likelihood | Impact | Mitigation Actions |
|--------|-------------|------------|--------|-------------------|
| RISK‑001 | Unauthorized PHI access due to misconfigured RBAC | Medium | High | Implement automated role‑permission validation CI job; quarterly RBAC matrix audit; enforce least‑privilege defaults |
| RISK‑002 | Encryption key compromise in air‑gapped environment | Low | High | Use hardware security module (HSM) for key storage; rotate keys every 90 days; enforce multi‑factor authentication for key access |
| RISK‑003 | Audit log tampering or loss | Low | High | Write logs to append‑only immutable storage with digital signatures; daily backup verification; weekly integrity checksum validation |
| RISK‑004 | Performance degradation under peak load affecting latency SLA | Medium | Medium | Conduct stress testing at 150 % expected load; auto‑scale Docker containers within air‑gap constraints; monitor response times in real time |
| RISK‑005 | Open‑source component vulnerability introduced after release | Medium | Medium | Subscribe to vulnerability feeds; run weekly dependency scanner; patch within 7 days of CVE release; maintain a bill of materials |

### 8. Acceptance Criteria per Functional Requirement
- **FR‑001**: System returns patient intake record within 200 ms (p95) for Clinician and Admin roles; measured over 1,000 random queries.
- **FR‑002**: Role‑based access control enforces that Front‑Desk cannot view or export full records; verified by automated permission tests.
- **FR‑003**: PDF export includes a visible watermark containing export timestamp and user ID; 100 % of exported PDFs pass automated watermark detection.
- **FR‑004**: Web form validates each field in real time; validation error rate remains below 1 % per batch of 10,000 submissions.
- **FR‑005**: Submission receipt displayed to user within 1 second after successful form submit; measured across 5,000 submissions.
- **FR‑006**: Receipt includes unique submission ID and timestamp; stored in audit log.
- **FR‑007**: Administrators can configure role permissions via UI; changes reflected immediately in access checks.
- **FR‑008**: Export function is restricted to Clinician and Admin roles; attempts by Front‑Desk are denied and logged.
- **FR‑009**: Deployment using Docker Compose completes without external network calls; verified by running deployment script in isolated network.
- **FR‑010**: Privacy notice displayed at start of intake form; user acknowledgment logged before any data entry.

All sections are traceable to the original stakeholder concerns, functional requirements, KPIs, and risk mitigations, providing a complete inception artifact ready for downstream design activities.
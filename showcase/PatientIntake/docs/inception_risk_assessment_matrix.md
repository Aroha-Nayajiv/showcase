# Risk Assessment Matrix
                
## Success Criteria Definition – PatientIntake System

### 1. Scope Statement
The PatientIntake system will provide a HIPAA‑compliant web‑based intake workflow that captures patient demographics, insurance information, and medical history, stores the data in an on‑premises PostgreSQL database with role‑based access control, generates a secure PDF summary per patient, and is deployed via Docker Compose in an air‑gapped environment. Open‑source technologies exclusively will be used.

### 2. Strategic Objectives
- **Regulatory Compliance** – Meet HIPAA §164.312(a)(2)(iv) encryption safeguards and maintain immutable audit logs.
- **Operational Efficiency** – Reduce manual data entry time by 80 % compared with paper forms.
- **Security Posture** – Achieve zero unauthorized‑access incidents in the first 12 months of production.

### 3. Stakeholder Analysis
| Stakeholder ID | Role / Concern | Primary Need | Risk if Unmet |
|----------------|----------------|--------------|----------------|
| **ST-001** | Clinician | Immediate access to accurate patient history | Delayed treatment decisions |
| **ST-002** | Patient | Secure submission of personal health information | Data breach leading to loss of trust |
| **ST-003** | Administrator | Manage user permissions and system health | Misconfiguration causing downtime |
| **ST-004** | Front‑Desk Staff | Fast intake processing without re‑keying data | Inefficient workflow increasing wait times |
| **ST-005** | Compliance Officer | Verify auditability and HIPAA adherence | Non‑compliance penalties |

### 6. Risk Assessment
| Risk ID | Description | Likelihood | Impact | Concrete Mitigation Actions |
|---------|-------------|------------|--------|------------------------------|
| **RISK‑001** | Unauthorized data exposure during transmission or storage | Medium (M) | High (H) | Implement field‑level AES‑256 encryption; enforce TLS 1.3 for all network traffic; quarterly penetration testing; rotate encryption keys every 90 days. |
| **RISK‑002** | Open‑source component vulnerabilities leading to exploitability | Medium (M) | Medium (M) | Generate Software Bill of Materials (SBOM) for all dependencies; run weekly vulnerability scans with OWASP Dependency‑Check; apply patches within 48 hours of release; maintain a hardened baseline Docker image. |
| **RISK‑003** | Deployment misconfiguration in air‑gapped environment causing service outage or data leakage | Low (L) | High (H) | Use immutable Docker images signed with Notary; enforce host OS hardening checklist; conduct pre‑deployment configuration review sign‑off; maintain disaster‑recovery runbooks stored offline. |
| **RISK‑004** | Compliance audit gaps (missing logs or incomplete encryption evidence) | Medium (M) | High (H) | Automate audit log integrity verification nightly; retain cryptographic proof of encryption key management; schedule internal HIPAA audit quarterly with documented findings. |
| **RISK‑005** | Resource exhaustion under peak load affecting response time SLA | Low (L) | Medium (M) | Implement auto‑scaling of stateless front‑end containers within the air‑gap using Docker Swarm mode; provision database connection pool sizing based on load test results; monitor latency thresholds and trigger alerts at >180 ms. |

### 7. Scope Definition

#### In‑Scope
- Web front‑end for structured intake forms.
- PostgreSQL database with row‑level security and encrypted columns.
- Role‑based access control for Administrator, Clinician, Front‑Desk.
- PDF generation with watermark and timestamp.
- Automated test suite covering core flows.
- Docker Compose deployment scripts for air‑gap installation.

#### Out‑Of‑Scope
- Cloud‑based key management services.
- Third‑party SaaS analytics platforms.
- Mobile native applications beyond responsive web UI.
- Integration with external EHR systems beyond data export.

## Business Vision
The project delivers a HIPAA-compliant patient intake system that enables on-premise collection, secure storage, and controlled export of patient information using only open-source technologies. The solution must protect PHI at rest and in transit, provide auditable access controls, and support rapid onboarding of clinical staff without reliance on external cloud services.

## Stakeholder Responsibility Matrix
| Stakeholder ID | Role                     | Primary Interests                                            | Key Risks Addressed                                 | Ownership of Requirements                     |
|----------------|--------------------------|--------------------------------------------------------------|------------------------------------------------------|----------------------------------------------|
| ST-01          | Clinical Staff (Clinician) | Immediate access to accurate intake data for care decisions | Downtime affecting patient care | FR-001, FR-002, KPI-01 |
| ST-02 | Front Desk Staff | Efficient capture of demographics and insurance information | Manual re-entry errors if system unavailable | FR-001, FR-002, KPI-01 |
| ST-03 | Compliance Officer | Demonstrable HIPAA compliance and auditability | Non-compliant audit logs or encryption gaps | FR-003, NFR-003, KPI-02 |
| ST-04 | System Administrator (Admin) | Secure configuration, container hardening, air-gap deployment | Misconfiguration leading to data exposure | FR-004, FR-005, KPI-04 |

## Functional Requirements
| Requirement ID | Description                                                                                                                            | Acceptance Criteria                                                                                                                                                                                                                                                                                                                                                                                                                     |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-001 | Secure collection of patient demographics, insurance information, and medical history via a web form with field-level encryption. | • All form fields are encrypted with AES‑256 before being written to the database.<br>• TLS 1.3 is enforced for every client–server interaction.<br>• Penetration test confirms no plaintext PHI leaves the browser.                                                                                                                                                                            |
| FR-002 | Role-based access control (RBAC) for admin, clinician, and front-desk roles governing read/write permissions. | • Admin can create, read, update, delete any record.<br>• Clinician can read and update assigned records only.<br>• Front desk can create new records but cannot view audit logs.<br>• Automated tests verify each role’s permission matrix.                                                                                                                                                                          |
| FR-003       | Immutable audit log capturing every read and write operation with 7-year retention.                                                    | • Log entries are write-once and tamper-evident (hash chain).<br>• Audit log entries are searchable by record ID and timestamp.<br>• Quarterly audit confirms 100 % coverage of operations.                                                                                                                                            |
| FR-004       | Automated unit and integration tests covering form validation, encryption handling, and RBAC edge cases.                              | • Minimum 80 % code coverage across all modules.<br>• CI pipeline fails if any test suite regresses.<br>• Test suite includes simulated attack vectors for encryption bypass.                                                                                                                                                                   |
| FR-005       | PDF intake summary generation with visible staff watermark and UTC timestamp; PDF stored temporarily on encrypted volume and deleted after download.| • Every generated PDF contains staff name, role, and generation timestamp visible on first page. • PDF file resides on an encrypted volume encrypted with AES‑256. • Automated script verifies file deletion within 5 minutes of successful download. |
|

## Success Criteria / KPIs
| KPI ID   | Metric                              | Target                                 | Measurement Method                               |
|----------|-------------------------------------|----------------------------------------|------------------------------------------------|
| KPI-01   | Form Completion Rate                | ≥ 90 % of patients complete intake within 5 min | Session analytics aggregated weekly            |
| KPI-02   | Audit Log Coverage                  | 100 % of read/write operations logged    | Log audit reports                           |
| KPI-03   | PDF Export Security Compliance      | 100 % of exported PDFs contain correct watermark and timestamp | Manual sample inspection                     |
| KPI-04   | Incident-Free Deployment Days      | ≥ 30 consecutive days without security incident | Security incident tracking system               |

## Risk Register
| Risk ID   | Description                                                                                 | Likelihood (L/M/H)   | Impact (L/M/H)   | Mitigation Actions                                                                                                                                                                                                                                                                                                                                                 |
|-----------|---------------------------------------------------------------------------------------------|---------------------|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| RISK-01   | Unauthorized disclosure of PHI during transmission or storage                         | M                   | H                 | Enforce TLS 1.3 for all network traffic.<br>- Apply field-level AES‑256 encryption at rest.<br>- Implement strict key-management procedures with rotation every 90 days.<br>- Quarterly penetration testing.                                                                                                                            |
| RISK-02   | Vulnerabilities in open-source components leading to exploitable attack surface    | M                   | H                 | Maintain a Software Bill of Materials (SBOM).<br>- Integrate automated CVE scanning into CI pipeline.<br>- Pin package versions and apply weekly security patches.<br>- Approve only vetted packages from a whitelist.                                                                                                         |
| RISK-03   | Misconfiguration of Docker Compose or container runtime causing data exposure or outage    | L                   | H                 | Provide hardened Docker Compose templates with least‑privilege defaults.<br>- Run configuration validation scripts before each deployment.<br>- Use immutable container images and read-only file systems.<br>- Document step-by-step air-gap deployment checklist.                                                   |
| RISK-04   | Inadequate audit-log retention leading to non-compliance with HIPAA record‑keeping requirements | L                   | M                 | Store logs on write-once media with immutable flag.<br>- Retain logs for minimum 7 years. |
>- Apply tamper-evident hashing on each entry.
>- Schedule monthly log integrity verification.
|
| RISK-05   | Failure to generate PDF intake summaries with required watermark and timestamp causing unauthorized distribution | L                   | M                 | Use vetted open-source PDF library that automatically adds staff watermark and UTC timestamp.
>- Automated validation tests on each PDF output before release.
>- Maintain change-control log for PDF template updates.
>- Periodic manual inspection of sample PDFs.
|
# Business Vision (Overview)

## Governance Model Overview: Business Vision & HIPAA Compliance

### 1. Vision Statement
The **PatientIntake** system will enable health‑care providers to capture protected health information (PHI) through a secure, open‑source web intake form. By automating data capture, the solution reduces manual entry errors, accelerates patient onboarding, and ensures full compliance with the Health Insurance Portability and Accountability Act (HIPAA). The platform is designed for on‑premise deployment, supporting multi‑tenant operation while maintaining strict data isolation, immutable auditability, and no reliance on external cloud services.

### 2. Regulatory Anchor
Compliance is anchored to the following HIPAA Security Rule provisions:
- **§164.312(a)(2)(iv)** – Encryption of PHI at rest.
- **§164.312(b)** – Access control mechanisms.
- **§164.310(d)** – Audit logging and retention.
All functional and non‑functional requirements must be traceable to these statutory clauses.

### 3. Data Protection Goals (DPG)
| Goal ID | Description | HIPAA Reference |
|----------|-------------|-----------------|
| DPG‑01 | Encrypt every PHI field at rest using AES‑256 or equivalent open‑source cryptographic library. | §164.312(a)(2)(iv) |
| DPG‑02 | Protect data in transit with TLS 1.2 or higher (prefer TLS 1.3). | §164.312(e)(1) |
| DPG‑03 | Maintain an immutable audit log that records 100 % of read and write events and retains entries for a minimum of seven years. | §164.310(d)(2) |
| DPG‑04 | Generate PDF intake summaries that embed a visible watermark and an export timestamp; restrict export to Clinician or Administrator roles. | §164.312(b) |

### 4. Success Metrics (KPIs)
| KPI ID | Metric | Acceptance Criteria | Measurement Method | Linked DPG |
|--------|--------|---------------------|--------------------|-----------|
| KPI‑01 | Encryption coverage | 100 % of PHI fields encrypted at rest | Automated nightly encryption verification script | DPG‑01 |
| KPI‑02 | Transport security compliance | TLS 1.2+ enforced for 100 % of connections | Network scan with compliance scanner (e.g., OpenVAS) | DPG‑02 |
| KPI‑03 | Audit log completeness | 100 % of read/write events captured and retained for ≥7 years | Log integrity audit using hash chaining and periodic checksum verification | DPG‑03 |
| KPI‑04 | PDF export control | Only Administrator or Clinician roles can export PDFs; each export includes visible watermark and timestamp | Access‑control test matrix executed per release cycle | DPG‑04 |
| KPI‑05 | Deployment isolation | No external network connections after air‑gap setup verification | Connectivity test in isolated environment (no outbound traffic) | All DPGs (overall compliance) |

### 6. Assumptions & Dependencies
- All cryptographic libraries used are vetted open‑source components (e.g., OpenSSL, libsodium).
- The on‑premise environment provides hardware that meets minimum performance specifications for PostgreSQL with high write throughput.
- Network infrastructure supports TLS 1.3 without requiring external certificate authorities; self‑signed certificates are acceptable within the air‑gap.
- Stakeholders will allocate dedicated time for quarterly penetration testing and key‑rotation activities.

*Document prepared by the Refiner (Senior Business Analyst) on 2026‑05‑04.*

# Patient Intake System – Inception Artifact

## 8. Risks and Mitigations
| ID | Risk Description | Likelihood | Impact | Mitigation Actions | Owner |
|---|---|---|---|---|---|
| **RISK-001** | Data breach during transmission of PHI. | Medium | High | • Enforce TLS 1.3 with AES‑256‑GCM and ECDHE cipher suites.<br>• Deploy OpenSSL 3.x in the web container and enable HSTS (max‑age 31536000).<br>• Automated SSL Labs scans on every CI build; pipeline fails if grade < A.<br>• Quarterly penetration testing focused on MITM vectors. | Security Lead |
| **RISK-003** | Incomplete audit logging for read/write operations. | Medium | Medium | • Enable pg_audit with `log_statement = 'all'` and enforce immutable append‑only log files.<br>• Deploy Filebeat to ship logs to an internal ELK stack with RBAC.<br>• Daily checksum comparison between expected and actual log entry counts.<br>• Retain logs for a minimum of 7 years in compliance with HIPAA. | Operations Manager |
| **RISK-004** | Deployment complexity in air‑gap environments leading to accidental external calls. | Low | Medium | • Pre‑deployment validation script scans Docker Compose files for `network_mode: host` or external image pulls; aborts on detection.<br>• Maintain internal registry of approved base images locked by digest.; • Step‑by‑step air‑gap setup guide reviewed and signed off by Release Engineer. | Release Engineer | |
| **RISK-005** | Insider threat – privileged users accessing records beyond scope. | Low | High | • Implement least‑privilege RBAC tiers (Admin full, Clinician limited to assigned patients, Front‑Desk limited to intake forms).<br>• Quarterly access‑review audits; any deviation triggers automatic revocation and incident response.; • Enforce MFA for all privileged accounts using privacyIDEA. | IAM Lead | |

## 9. Summary
The refined inception artifact now provides a clear business vision, detailed stakeholder objectives, fully specified functional requirements with measurable acceptance criteria, concrete risk mitigations with owners, and traceable KPIs. This foundation enables downstream design and implementation teams to build a compliant, secure, and operationally efficient patient intake system.

# Inception Artifact – Patient Intake System (HIPAA‑Compliant)

## 10. Project Purpose
The purpose of this initiative is to deliver a fully HIPAA‑compliant patient intake solution that enables secure collection, storage, and export of protected health information (PHI) using only open‑source technologies. The system must operate on‑premise in air‑gapped environments and support multi‑tenant usage by healthcare providers.

## 11. Vision & Objectives
| Objective | Success Metric |
|------------|-----------------|
| Secure data capture | 100 % of PHI fields encrypted at rest (AES‑256) and in transit (TLS 1.3) |
| Immutable auditability | 100 % of read/write events logged and retained for ≥ 7 years |
| Reliable PDF export | 100 % of exported PDFs contain visible watermark and ISO‑8601 timestamp |
| Deployability | ≥ 95 % first‑time Docker‑Compose installation success in air‑gap labs |
| Test coverage | ≥ 98 % of unit and integration tests pass |

## 12. Scope Definition
**In‑Scope**
- Web‑based structured intake form collecting demographics, insurance, and medical history.
- Role‑based access control (admin, clinician, front‑desk).
- Field‑level encryption at rest and TLS 1.3 in transit.
- Immutable audit log for every read/write operation on PHI.
- PDF summary generation with visible watermark and export timestamp.
- Automated unit & integration test suite covering validation, encryption, and access control.
- Docker‑Compose deployment guide for on‑premise, air‑gap installations.

**Out‑Scope**
- Cloud‑hosted managed database services.
- Commercial encryption libraries (only open‑source components).
- Direct integration with external EHR systems beyond PDF export.
- Detailed API design, database schema definitions, or CI/CD pipeline scripts.

## 13. Governance Model Overview
The governance model aligns business objectives with compliance mandates through a structured hierarchy:
1. **Executive Sponsor** – authorizes budget and ensures alignment with organizational strategy.
2. **Product Owner** – defines functional scope, prioritizes backlog items, and validates acceptance criteria against HIPAA requirements.
3. **Compliance Officer** – reviews audit log design, encryption key management, and ensures all regulatory artifacts are maintained.
4. **Technical Lead** – oversees implementation of RBAC, encryption libraries, and Docker‑Compose packaging while adhering to open‑source constraints.
5. **Quality Assurance Lead** – owns the automated test suite and verifies KPI thresholds before each release.
Regular steering committee meetings review KPI dashboards, risk status, and release readiness.

## 14. Traceability Matrix
| Functional Requirement | Related KPI(s) |
|-----------------------|----------------|
| FR-001 (Data Capture) | KPI-001 (Encryption Coverage), KPI-004 (Deployment Success) |
| FR-002 (RBAC) | KPI-002 (Audit Log Completeness), KPI-005 (Test Suite Pass Rate) |
| FR-003 (PDF Export) | KPI-003 (PDF Export Compliance), KPI-005 (Test Suite Pass Rate) |

---
*Document prepared on 2026‑05‑04 as the definitive inception artifact for the Patient Intake project.*

# Business Vision and Inception Artifact – PatientIntake Project

## 15. Stakeholder Identification and Needs
| Stakeholder | Role | Primary Need |
|-------------|------|--------------|
| Clinical Staff (Physicians, Nurses) | End‑users | Quick, accurate entry of demographics, insurance, and medical history; assurance that data is secure and only visible to authorized personnel. |
| Front‑Desk Personnel | Data Entry Operators | Simple web form workflow; ability to correct entry errors without compromising audit integrity. |
| IT Security Team | Security Owner | Enforced encryption at rest and in transit; immutable audit logging; secret management using open‑source tools. |
| Compliance Officer | Governance Owner | Evidence of HIPAA compliance, audit‑log retention for ≥7 years, and documented open‑source license compliance. |
| Executive Sponsor | Business Owner | Measurable improvement in intake processing time and reduction of manual errors; clear ROI and risk mitigation. |
| Patients | Data Subjects | Assurance that personal health information (PHI) is handled securely and confidentially. |

## 16. Business Requirements (Functional Requirements)
| ID | Requirement | Acceptance Criteria |
|----|-------------|----------------------|
| FR-001 | Secure Patient Data Capture | • All form fields are encrypted in transit via TLS 1.2+.<br>• Field‑level encryption at rest using AES‑256. |
| FR-002 | Immutable Audit Log for Every Read/Write | • PostgreSQL `pg_audit` records every SELECT/INSERT/UPDATE/DELETE on PHI tables.<br>• Logs are write‑once and retained for 7 years.<br>• Audit entries include user ID, timestamp, operation type. |
| FR-003 | PDF Intake Summary with Watermark | • Generated PDF includes a visible watermark containing the exporting staff member’s name and timestamp.<br>• PDF is signed digitally using an approved X.509 certificate. |
| FR-004 | Automated Test Suite | • Unit tests cover form validation, encryption/decryption functions, and role‑based access control.<br>• Integration tests verify end‑to‑end data flow from web form to PostgreSQL and PDF export. |
| FR-005 | Docker‑Compose Deployment for Air‑Gap | • All containers are built from open‑source base images.; • Deployment scripts run without external network access.; • Offline image repository and checksum manifest are provided. |
| FR-006 | Role‑Based Access Control (RBAC) | • Admin, Clinician, and Front‑Desk roles have distinct permissions defined in PostgreSQL RLS policies. |
| FR-007 | Audit Log Retention & Verification | • Logs are replicated to an immutable object store within the air‑gap network.; • Quarterly verification scripts confirm log integrity. |
| FR-008 | KPI Definition & Measurement | • KPI‑01: Audit‑log completeness – 100 % of read/write operations captured.; • KPI‑02: PDF watermark presence – 100 % of exported PDFs contain correct watermark.; • KPI‑03: System uptime – ≥99.5 % during business hours. |
| FR-009 | Open‑Source License Compliance | • All third‑party libraries are scanned with SPDX tools.; • A compliance report is generated for each release confirming no prohibited licenses are used. |

## 17. Open‑Source Compliance Statement
All components—including the web framework, encryption libraries, Docker base images, and testing tools—are sourced from OSI‑approved licenses. SPDX scanning is performed on every build artifact; any component that introduces a non‑permissive license will block the CI pipeline.

---
*Document prepared by Refiner (Senior Business Analyst) on 2026‑05‑04.*
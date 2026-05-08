# System Architecture Overview

### Strategic Objectives
1. **Regulatory Compliance** – Achieve and maintain HIPAA 164.312(a)(2)(iv) encryption standards for data in transit and at rest.
2. **Operational Efficiency** – Reduce manual data entry time by 60 % compared with paper-based intake.
3. **Data Integrity & Auditability** – Provide immutable audit logs retained for 7 years to satisfy compliance audits.
4. **Scalable SaaS Model** – Design the service for horizontal scaling across multiple clinic sites while preserving strict tenant isolation.
5. **Open-Source Sustainability** – Use only community-maintained libraries with active security patches.

## Functional Requirements
| ID   | Description| Acceptance Criteria  |
|------|-------------|--------------------|
| FR-001 | Collect patient demographics, insurance data, and medical history via a web form with field-level encryption before transmission.   | Form fields are encrypted client-side; encrypted payload is received and stored without plaintext exposure; 100 % of submissions pass validation tests.                         |
| FR-002 | Store submissions in a local PostgreSQL instance with role-based access control (admin, clinician, front-desk).                     | RBAC matrix enforced; audit log records every read/write operation; no unauthorized role can access PHI.|
| FR-003 | Generate a PDF intake summary per patient that is exportable only by authorized staff, includes a visible watermark and export timestamp.| PDF contains watermark “Confidential – PatientIntake” and timestamp; only Clinician or Admin can download; download attempts are logged.| 
| FR-004 | Provide automated unit and integration tests covering form validation, encryption handling, and access-control edge cases.| Test suite runs on every commit; ≥90 % code coverage; all critical security test cases pass in CI pipeline.| 
| FR-005 | Deploy the entire stack via Docker Compose for on-premise air-gap environments with documented setup guide.| Docker Compose file launches all services on a single host; setup guide verified by an independent ops engineer; deployment completes without external network calls.| 
| FR-006 | Enable horizontal scalability and high availability for multi-tenant deployments.| System supports scaling to at least 5 concurrent clinic sites with load-balanced services; failover restores service within 30 seconds.|

## Success Criteria / KPIs
| ID       | Metric| Target  |
|----------|--------------|------------------------|
| KPI-001  | Form Completion Rate                    | ≥90 % of patients complete the form without abandonment               |
| KPI-002  | Audit Log Retention Compliance | 100 % of logs retained for 7 years on immutable storage               |
| KPI-003  | Encryption Key Management Accuracy | Zero key leakage incidents per quarter|
|
| KPI-004 - Deployment Success Rate - | ≥95 % of Docker Compose deployments complete without manual intervention |

## Scope Boundary
**In Scope**
* Secure web form collection with client-side encryption.
* PostgreSQL storage with RBAC and immutable audit logging.
* PDF generation with watermark and timestamp.
* Automated test suite covering security edge cases.
* Docker Compose deployment for air-gap environments.

**Out of Scope**
* Integration with external EHR systems beyond optional import/export adapters.
* Mobile native applications; only browser-based web interface is covered.
* Advanced analytics or machine-learning risk scoring on collected data.
* Third-party SaaS hosting; solution must remain on-premise.

## Stakeholder Table
| Stakeholder Role      | Primary Need  | Key Pain Point| RBAC Tier| Linked Objective |
|-----------------------|--------------------|-----------------------|---------------|------------------|
| Patient (ST-001) | Secure self-service data entry without exposing PHI | Fear of data leakage on public networks; limited technical literacy | End-User (read-only after submission) | OBJ-001: Ensure patient-initiated submissions are encrypted in transit and at rest (FR-001, NFR-002) |
|
| Front Desk Staff (ST-002) - | Rapid intake of new patients and verification of insurance information | Manual re-entry of data from paper forms leads to errors and delays | Operator (create & read submissions) | OBJ-002: Reduce intake processing time by 30 % (KPI-001) |
|
| Clinician (ST-003) - | Immediate access to complete medical history for care decisions | Need to view PHI quickly while maintaining auditability | Clinician (read-only, limited write for notes) | OBJ-003: Provide real-time read access with audit log retention 7 years (FR-002, KPI-002) |
|
| Administrator (ST-004) - | Central management of tenant isolation, key rotation, and system health monitoring | Complexity of multi-tenancy isolation and key lifecycle management | Admin (full control) | OBJ-004: Achieve 99.9 % system uptime and enforce key rotation every 90 days (KPI-004) |
|
| Compliance Officer (ST-005) - | Evidence of HIPAA compliance for audits and regulatory reviews | Need verifiable audit trails and encryption key management documentation | Auditor (read-only audit logs) | OBJ-005: Produce audit reports meeting HIPAA §164.312(b) and SOC 2 criteria (KPI-003) |

## Narrative Summary
Patients will interact with a web form that enforces TLS 1.3 encryption in transit and field-level AES-256 encryption at rest. The form encrypts each field client-side before transmission, guaranteeing that no PHI is ever stored in plaintext on the client or in transit.

Front Desk Staff use a streamlined UI that auto-populates insurance verification fields via open-source lookup services while being limited to creating new records and viewing submissions for their clinic only.

Clinicians receive read-only access to the full intake record once a patient is admitted. Every read operation is logged with an immutable timestamp; any attempt to modify a submitted record is denied and triggers an alert.

Administrators manage tenant isolation across multiple clinics using Docker Compose deployments. They can rotate encryption keys without downtime and enforce row-level security policies defined in PostgreSQL.

Compliance Officers rely on a tamper-evident audit log that records every read, write, and export operation. Logs are stored on WORM storage for seven years and are queryable for compliance reporting.

## Alignment with Project Objectives
Each stakeholder’s need directly maps to the high-level objectives:
* **OBJ-001 – Regulatory Compliance** – Addressed by FR-001, NFR-001, NFR-002.
* **OBJ-002 – Operational Efficiency** – Addressed by FR-002, KPI-001.
* **OBJ-003 – Data Integrity & Auditability** – Addressed by FR-003, NFR-003, KPI-002.
* **OBJ-004 – Scalable SaaS Model** – Addressed by FR-006, NFR-006, KPI-004.
* **OBJ-
005 – Open-
Source Sustainability** – Addressed by use of community libraries and Docker Compose deployment.

## Risk Register (selected)
| ID       | Description  | Mitigation |
|----------|--------------------|------------|
| RISK- | 001 | Data breach due to inadequate encryption key management Implement HSM-backed key storage; rotate keys every 90 days; audit key usage logs (NFR- | 001). |
|
| RISK- 002    | Regulatory non-compliance during audits | Maintain immutable audit logs (NFR- 003); conduct quarterly compliance reviews (KPI- | 003). |
|
| RISK- 003    | Performance bottlenecks under high concurrent load | Deploy horizontal scaling architecture (FR- 006); conduct load testing against NFR- | 005 targets. |
|
| RISK- 004    | User adoption resistance from patients unfamiliar with digital forms | Provide guided UI walkthroughs; offer assisted entry kiosks in clinic lobby. |
|
| RISK- 005    | Operational downtime due to single point of failure in Docker Compose stack | Configure Docker Swarm mode with failover containers; monitor health checks and auto-restart services. |

# Business Vision
The PatientIntake system will enable on‑premise, SaaS‑style delivery of a HIPAA‑compliant patient intake workflow. By leveraging open‑source components and Docker‑Compose orchestration, the solution provides secure, scalable, and auditable data capture for clinics that operate in air‑gapped environments.

# Stakeholder Needs & Roles
| Stakeholder | Primary Need | Pain Point | RBAC Tier | Linked Requirement |
|------------|---------------|------------|----------|-------------------|
| Patient (ST-001) | Confidential data capture | Trust in privacy controls | N/A | FR-001 |
| Front‑Desk Staff (ST-002) | Fast intake workflow | Manual re‑entry risk | Operator | FR-002 |
| Clinician (ST-003) | Immediate access to verified PHI | Stale data risk | Clinician | FR-003 |
| Administrator (ST-004) | Secure system configuration | Configuration drift | Admin | FR-004 |
| Compliance Officer (ST-005) | Auditability & reporting | Incomplete logs | Auditor | FR-005 |

# High‑Level Requirements (Inception)
**Functional Requirements**
1. **FR-001** – Collect patient demographics, insurance information, and medical history via a structured web form. *Acceptance*: All fields are validated client‑side and server‑side; submission stores encrypted payload.
2. **FR-002** – Encrypt data at rest using column‑level AES‑256 encryption in PostgreSQL and in transit via TLS 1.3. *Acceptance*: No plaintext PHI is written to disk; network traffic is captured only as TLS records.
3. **FR-003** – Implement role‑based access control (admin, clinician, front‑desk) with least‑privilege principles. *Acceptance*: Access matrix is auditable; unauthorized attempts are logged and blocked.
4. **FR-004** – Generate a PDF intake summary per patient that includes a visible watermark and export timestamp visible only to authorized staff. *Acceptance*: PDF is signed, watermarked, and access‑controlled.
5. **FR-005** – Provide automated unit and integration tests covering form validation, encryption, and access‑control edge cases. *Acceptance*: Test suite achieves ≥90 % coverage and runs on every CI pipeline.
6. **FR-006** – Deploy the entire stack via Docker Compose for on‑premise, air‑gap environments with no external cloud dependencies. *Acceptance*: Deployment script completes without internet access; all images are signed.
7. **FR-007** – Document an air‑gap update guide that details offline artifact transfer, key provisioning, and verification steps. *Acceptance*: Guide is reviewed quarterly and versioned.

# Risks & Mitigations
| Risk ID | Description | Likelihood | Impact | Mitigation |
|---------|--------|------------|
| RISK-001 | PHI data breach during transmission | Medium | High | Enforce TLS 1.3 with mutual authentication; use AES‑256 for payloads. |
| RISK-002 | Non‑compliance with HIPAA audit requirements | Low | High | Immutable audit log retention for 7 years; automated compliance reports. |
| RISK-003 | Operational failure of air‑gap deployment | Medium | Medium | Signed Docker images; offline artifact repository; step‑by‑step update guide. |
| RISK-004 | Insider threat – privileged user extracts PHI | Low | High | Principle of least privilege; just‑in‑time elevation; real‑time alerting via SIEM. |
| RISK-005 | Service availability degradation due to encryption overhead | Medium | Medium | Horizontal scaling; benchmark encryption latency <200 ms p95; circuit‑breaker patterns for PDF service. |

# Success Criteria & KPIs
- **KPI-001** – System availability ≥99.9 % measured by Prometheus alerts.
- **KPI-002** – Zero security incidents in the first 90 days (tracked via incident log).
- **KPI-003** – Successful completion of quarterly HIPAA technical safeguard review (linked to FR-008).
- **KPI-004** – Audit log completeness ≥99 % verified against immutable storage checks.

# Governance & Compliance Overview
The Security Governance Board (CISO, Compliance Officer, Product Owner, Operations Lead, Clinical Lead) meets bi‑weekly to review risk heat maps, KPI trends, and change requests. Change control follows a tiered approval workflow aligned with the risk rating defined in the risk register.

# Next Steps
1. Finalize acceptance criteria for each functional requirement and obtain stakeholder sign‑off.
2. Populate the detailed test matrix for FR‑005.
3. Conduct a pilot deployment in a controlled clinic environment to validate air‑gap procedures.
4. Update the traceability matrix linking each requirement to its associated KPI and risk mitigation.

## Acceptance Criteria
1. **Form Security** – All form fields are encrypted at rest using AES‑256 and transmitted over TLS 1.2+. Verification via automated test cases (FR‑012).
2. **Audit Log Completeness** – Every create, read, update, delete operation is recorded with user ID, timestamp, and operation type; logs are immutable for 7 years (NFR‑004).
3. **PDF Summary** – Generated PDFs contain a visible watermark (“Confidential – Internal Use Only”) and an export timestamp; only users with Clinician or Admin role can download (FR‑004, FR‑011).
4. **Deployment** – The entire stack can be launched with a single `docker-compose up` command on an air‑gap network; deployment guide includes step‑by‑step SOC 2 evidence collection (FR‑010).
5. **Scalability** – Load tests demonstrate stable performance at 5,000 concurrent sessions without degradation of response time beyond 200 ms (NFR‑005).
6. **Compliance Review** – Quarterly compliance review checklist completed and signed off by the Compliance Officer (FR‑009).

## Traceability Matrix
| Business Requirement ID | Related Functional Scope IDs | KPI(s) Covered | Owner |
|---------------------------|----------------------------|------------------|-------|
| FR-008 (Governance Structure) | FR-001–FR-006 | KPI-001 (System uptime ≥99.9 %) | CISO |
| FR-009 (Compliance Review Schedule) | FR-002 (TLS enforcement) | KPI-002 (Zero security incidents) | Compliance Officer |
| FR-010 (Air‑Gap Deployment Guide) | FR-005 (Docker Compose deployment) | KPI-003 (Audit compliance passed) | Operations Lead |

*All requirements are linked to the appropriate KPIs and stakeholder owners to ensure measurable success.*
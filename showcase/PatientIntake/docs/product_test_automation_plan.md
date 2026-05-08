# Test Automation Plan

## Test Automation Plan: Key User Personas

### Persona Summary Table
| ID | Role | Primary Goal | Security Responsibility | Notes |
|----|------|--------------|--------------------------|-------|
| PER-01 | Patient | Submit accurate demographic, insurance, and medical history data via the web form | Ensure data is encrypted in transit (TLS 1.3) and at rest (field‑level encryption) before storage | No direct system access; only interacts with the front‑end form |
| PER-02 | Front Desk Staff | Verify insurance eligibility and assist patients in completing the intake form | Must not view or modify PHI beyond what is required for verification; audit all read/write actions | Role‑based read/write to intake records; can trigger PDF generation for authorized staff |
| PER-03 | Clinician | Review completed intake records to make clinical decisions and sign off on care plans | Must access only records for assigned patients; all accesses logged for audit compliance | Full read access to patient records; can export PDF summaries with watermark and timestamp |

### Detailed Persona Descriptions
* **PER‑01 – Patient**  
  Interacts with a SaaS‑hosted multi‑tenant portal to provide personal health information. The portal enforces TLS 1.3 termination at the load balancer and performs client‑side field encryption before transmission.

* **PER‑02 – Front Desk Staff**  
  Operates within a tenant‑isolated instance of the system. The staff member has role‑based permissions scoped to the tenant’s patient cohort and can invoke PDF generation that stores the file in a tenant‑specific secure bucket.

* **PER‑03 – Clinician**  
  Authenticated via SSO/OIDC to a tenant’s namespace. Accesses only patients assigned to their care team; export actions produce PDF/A‑2b documents with a visible watermark containing the tenant ID and timestamp.

### US‑001 – Patient Submission
**As** PER-01  
**I want** to submit my personal demographics, insurance information, and medical history through an encrypted web form  
**So that** my data is securely captured and protected in transit and at rest, satisfying HIPAA technical safeguards.

### US‑002 – Front Desk Review & PDF Generation
**As** PER-02  
**I want** to review the completed intake form for completeness and generate a PDF summary with watermark and export timestamp  
**So that** the submission is auditable, only authorized roles can store or modify the data, and any errors are logged for compliance reporting.

#### Acceptance Criteria (BDD)

Given a front-desk staff member with role front_desk is authenticated within their tenant
When they view a patient’s intake record and click “Generate PDF”
Then the system creates a PDF/A‑2b document containing the intake data
And embeds a visible watermark “Authorized Export – {tenant_id} – {timestamp}”
And stores the PDF in a tenant-scoped secure bucket
And creates an immutable audit log entry (FR-004) with action_type=“export_pdf”

#### Additional Scenarios
* **Unauthorized Export** – If a user without front_desk role attempts export, the system returns Access Denied and logs the attempt.
* **Duplicate PDF** – If a PDF already exists for the session, the system prompts “PDF already generated – re-create?”; confirming overwrites with new watermark; cancelling leaves no new log entry.
* **File System Failure** – Simulated storage write failure returns an error message, rolls back partial file creation, and logs failure event.

### US‑003 – Clinician Retrieval & Audit
**As** PER-03  
**I want** to retrieve a PDF summary of a patient’s intake data that includes a visible watermark and export timestamp, accessible only after successful authentication  
**So that** I can safely reference patient information for clinical decisions while maintaining an immutable audit trail required by FR-004 and KPI-003.

### US‑004 – Encryption Key Rotation Verification (New)
**As** Security Engineer  
**I want** automated tests that verify periodic encryption key rotation does not break decryption of existing records  
**So that** compliance with NFR-002 is continuously validated.

### US‑005 – Audit Log Immutability Check (New)
**As** Compliance Officer  
**I want** tests that ensure audit log entries cannot be altered or deleted after creation  
**So that** we satisfy KPI-003 for audit completeness.

## MVP Scope & Prioritization
| Priority | User Story | Rationale |
|----------|------------|-----------|
| P1 | US-001 | Core HIPAA encryption requirement (TLS 1.3, AES-256) |
| P2 | US-002 | Role-based access control & audit logging critical for compliance |
| P2 | US-003 | Clinician workflow & PDF watermarking required by FR-004 |
| P3 | US-004 | Key rotation verification supports NFR-002 |
| P3 | US-005 | Audit log immutability supports KPI-003 |

The MVP focuses on regulatory coverage, business value, testability, and risk reduction while remaining SaaS-centric (multi-tenant isolation, cloud deployment).

## Implementation Notes for CI Integration
* UI tests for US-001–US-003 run in headless Chrome within Docker Compose service `test-ui`.
* Backend unit tests for encryption, key rotation, and audit logging execute via `pytest` targeting `tests/unit/`.
* PDF export verification uses `pdfminer.six` to extract watermark text and checksum comparison.
* Tests are tagged with `@mvp` for selective execution during early sprints.
* All tests run in a tenant-isolated environment using Docker Compose network `patientintake_saas`.

## Dependencies & Assumptions
* PostgreSQL ≥13 with row-level security enabled per tenant.
* Encryption library `crypto-js@4.x` for client-side field encryption.
* Server-side key management integrated with AWS KMS (or equivalent) respecting NFR-002.
* PDF generation tool `WeasyPrint` with watermark plugin supporting PDF/A-2b compliance.
* Monitoring stack (Prometheus + Grafana) configured for multi-tenant metrics collection.
* Rate limiting and DDoS protection enforced at API gateway level per SaaS best practices.

## 1. Overview
This document defines the test automation plan for the **PatientIntake SaaS** solution. The plan ensures that all critical user stories are validated through automated tests integrated into a cloud-native CI/CD pipeline, supporting high availability, multi-tenant isolation and compliance (SOC 2, GDPR).

## 2. User Stories & Acceptance Criteria

## 3. Traceability Matrix
| User Story | Functional Requirements (FR) | Key Performance Indicators (KPI) |
|---|---|---|
| US-001 | FR-001 (collect demographics), FR-002 (field-level encryption), FR-003 (store in PostgreSQL with RBAC) | KPI-001 (system availability ≥ 99.9 %), KPI-002 (zero security incidents first 90 days) |
| US-002 | FR-004 (PDF summary generation with watermark), FR-005 (export control), FR-006 (audit log of export) | KPI-002, KPI-003 (audit-log completeness ≥ 100 %) |
| US-003 | FR-006 (full audit log of reads/writes), FR-003 (role-based access control) | KPI-001, KPI-003 |

## 4. Test Automation Strategy
1. **Frameworks**
   - Unit tests: **pytest** for encryption utilities and service layers.
   - End-to-end UI tests: **Selenium + pytest-selenium** covering HTTPS handshake, form validation and PDF export flows.
   - BDD acceptance tests: **behave** implementing the Given/When/Then scenarios listed above.

2. **CI/CD Integration**
   - Tests run in Docker containers orchestrated by **Docker Compose** for local development and by **Kubernetes Jobs** in the cloud CI pipeline (`ci/pipeline.yml`).
   - Pipeline stages: lint → unit → integration → e2e → security scan → report → deploy if all pass.

3. **Coverage Targets**
   - Minimum **90 % statement coverage** for encryption utilities.
   - Minimum **80 % coverage** for UI flows.
   - **100 % of acceptance criteria** must have at least one automated test case.

4. **Security Checks**
   - Nightly OWASP ZAP scan against the staging environment; any critical finding fails the build.
   - Automated verification of TLS 1.3 enforcement and key‑rotation health checks.

5. **Reporting & Dashboard**
   - Test results published as JUnit XML artifacts; aggregated in a Grafana dashboard linked to KPI‑002 compliance view.
   - Failure trends trigger alerts via PagerDuty.

## 5. SaaS-Specific Operational Considerations
* **Multi-Tenant Isolation:** All tenant data stored in separate schemas; row-level security policies enforce tenant boundaries (FR‑003).
* **Backup & Disaster Recovery:** Daily encrypted snapshots stored in an immutable object store; restore time objective ≤ 30 minutes.
* **Compliance:** Architecture designed to satisfy **SOC 2 Type II**, **GDPR**, and HIPAA encryption requirements (TLS 1.3, AES‑256 at rest).
* **Scalability:** Horizontal scaling via Kubernetes Horizontal Pod Autoscaler; database sharding strategy prepared for > 5 000 concurrent users (NFR‑006).

## 6. Risks & Mitigations
| Risk ID | Description | Mitigation |
|---|---|---|
| RISK-001 | Data breach due to improper key management | Automated key rotation service with audit logging; regular SOC 2 audits. |
| RISK-002 | Regulatory non-compliance (HIPAA/GDPR) | Continuous compliance monitoring dashboards; periodic external audits. |
| RISK-007 | Test coverage gaps for key rotation and audit-log immutability | Added dedicated BDD scenarios (see US‑001 AC‑002 & US‑003 AC‑005) and integration tests that simulate key service outage and verify immutable log entries. |
# Stakeholder Influence-Interest Matrix

### 1. Scope Definition
The PatientIntake project delivers a HIPAA‑compliant web‑based intake system that captures patient demographics, insurance information, and medical history via a structured form. All data are encrypted at rest in a local PostgreSQL instance and in transit using TLS 1.3. Role‑based access control (Admin, Clinician, Front‑Desk) governs read/write permissions, and every access event is recorded in an immutable audit log retained for seven years. The system also produces a PDF summary per patient, exportable only by authorized staff, with a watermark containing the exporting user ID and timestamp. Deployment is containerized with Docker Compose and must operate in an air‑gapped environment without any external cloud dependencies.

### 2. Architecture Vision
The solution adopts a fully open‑source stack: an HTML5/JavaScript front‑end built on React, a Flask‑based API layer (Python 3.11), and PostgreSQL 15 for data persistence. TLS termination is performed by an open‑source reverse proxy (Traefik) configured for strict cipher suites (AES‑256‑GCM). PDF generation uses the open‑source library wkhtmltopdf, and watermarking is applied via PDF‑tk. All containers are orchestrated by Docker Compose version 2.4, with explicit network isolation to satisfy the air‑gap requirement. The architecture diagram (referenced as ARCH‑001) shows three logical zones: Presentation, Business Logic, and Data Store, each protected by firewall rules enforced at the container‑network level.

### 3. Stakeholder Identification and Needs
| Stakeholder Role | Primary Need | Key Pain Point | RBAC Tier | Linked Objective |
|---|---|---|---|---|
| Patient | Assurance that personal health information is protected and processed quickly | Fear of data breach and long wait times | None (view receipt only) | OBJ-001: Achieve 99.9% form submission success within 2 seconds |
| Front‑Desk Staff | Efficient data entry with real‑time validation to reduce re‑work | Manual re‑entry errors and slow UI feedback | Operator | OBJ-002: Reduce data entry error rate to <1% per batch |
| Clinician | Immediate access to complete, accurate patient records for care decisions | Delayed record availability hampers treatment | Clinician | OBJ-003: Provide record retrieval latency <200 ms (p95) |
| Administrator | Ability to configure roles, audit logs, and system parameters without service disruption | Complex permission matrix management | Admin | OBJ-004: Implement RBAC configuration changes with zero downtime |
| Compliance Officer | Evidence of HIPAA compliance for audits and continuous monitoring | Incomplete audit trails and missing encryption key rotation logs | Auditor | OBJ-005: Maintain 100% audit log completeness and key rotation compliance quarterly |

### 4. Influence‑Interest Matrix Summary
- **High Influence / High Interest**: Clinician, Administrator, Compliance Officer – require frequent updates, direct involvement in policy definition, and sign‑off on security controls.
- **High Influence / Low Interest**: Hospital IT Leadership – monitor overall project health but are not involved in day‑to‑day decisions; receive monthly status reports.
- **Low Influence / High Interest**: Front‑Desk Staff – heavily use the system daily; their feedback drives UI refinements and validation rule adjustments.
- **Low Influence / Low Interest**: External vendors (e.g., insurance verification services) – only interact via defined data exchange points and are not part of internal governance.

The matrix guides communication cadence: weekly workshops for high‑interest groups, bi‑weekly executive briefs for high‑influence stakeholders, and quarterly compliance reviews for auditors.

### 5. Success Metrics and KPIs
| KPI ID | Metric Name | Target Value | Measurement Method | Linked Objective |
|---|---|---|---|---|
| KPI-001 | Form submission latency (p95) | ≤200 ms | Automated load test suite measuring end‑to‑end request time | OBJ-001 |
| KPI-002 | Audit log completeness | 100% of read/write events captured | Log verification script comparing DB transaction count vs log entries nightly | OBJ-005 |
| KPI-003 | PDF export watermark accuracy | 100% of exported PDFs contain user ID and timestamp watermark | Manual spot‑check of 10 random PDFs per release | OBJ-003 |
| KPI-004 | Encryption at rest compliance | 100% of PHI fields encrypted with AES‑256‑GCM | Configuration scan using OpenSCAP after each deployment | OBJ-004 |
| KPI-005 | Deployment reproducibility in air‑gap environment | Zero external network calls during Docker Compose up | Network traffic capture during CI pipeline run | OBJ-002 |

These metrics provide quantifiable evidence that the system meets regulatory, performance, and operational goals while aligning stakeholder influence and interest levels with appropriate governance mechanisms.

### Success Criteria (KPIs)
| KPI ID | Metric | Target |
|---|---|---|
| KPI-001 | Form response time (p95) | ≤200 ms |
| KPI-002 | Audit log completeness | 100% of read/write events logged |
| KPI-003 | PDF export compliance | 100% of PDFs contain correct watermark and timestamp |

## Risks and Mitigations
| Risk ID | Description | Severity (L/M/H) | Owner | Mitigation |
|---|---|---|---|---|
| RISK-001 | Unauthorized PHI access due to misconfigured RBAC | H | Administrator | Automated role‑permission matrix validation before each release; quarterly review.
| RISK-002 | Encryption key compromise | H | Security Engineer | Use hardware security module (HSM) for key storage; rotate keys every 90 days; enforce MFA for key access.
| RISK-003 | Audit log tampering | H | Compliance Officer | Write logs to append‑only storage with digital signatures; immutable backup retention for 7 years.
| RISK-004 | Deployment in non‑air‑gapped environment inadvertently exposing PHI | H | IT Operations | Automated environment validation script aborts if external network calls detected during Docker Compose up.
| RISK-005 | Performance degradation under peak load affecting response time SLA | M | Performance Engineer | Conduct stress testing; auto‑scale container resources; implement rate limiting.
| RISK-006 | Missing or outdated documentation causing operational errors | M | Documentation Lead | Documentation checklist integrated into CI; version control with mandatory peer review.

## Acceptance Test Cases (Selected)
| TC ID | Description | Expected Result |
|---|---|---|
| TC-001 | Submit a complete intake form with valid data; measure latency. | Median latency ≤200 ms; receipt displayed within 1 second.
| TC-002 | Attempt unauthorized record access with a user lacking proper role. | Access denied; audit log entry created with user ID and timestamp.
| TC-003 | Verify encryption at rest by scanning PostgreSQL tables for plaintext PHI. | No plaintext PHI detected; all sensitive columns encrypted with AES‑256.
| TC-004 | Export patient summary PDF as Clinician; inspect watermark. | PDF contains correct user ID and timestamp watermark.
| TC-005 | Run Docker Compose deployment in isolated network; capture traffic. | No outbound network connections observed; deployment completes successfully.
| TC-006 | Execute full CI pipeline; ensure all tests pass and coverage ≥90%. | All tests pass; coverage report shows ≥90%.

## Additional Notes
- All functional requirements are scoped to the on‑premise environment; no external SaaS components are used.
- Documentation will include a detailed air‑gap deployment guide (DOC‑001) covering network isolation, container image signing, and offline artifact distribution.
- Key rotation procedures are defined in the security policy (SEC‑POL‑001) and audited quarterly.
- The system will be subject to periodic HIPAA compliance audits; audit logs are immutable and retained for seven years as required by 45 CFR §164.312(b).

## Business Vision
The project delivers a HIPAA‑compliant patient intake system built exclusively with open‑source technologies. It captures patient demographics, insurance information, and medical history via a secure web form, stores data in a locally hosted PostgreSQL database with strict role‑based access control (RBAC), logs every read and write operation, and generates PDF intake summaries that include cryptographic watermarks and timestamps. The solution is deployed with Docker Compose in an air‑gapped environment and includes automated unit and integration tests covering validation, encryption, and access control edge cases.

## Functional Requirements
| ID | Description | Acceptance Criteria | Owner |
|----|-------------|----------------------|-------|
| FR-001 | Clinicians must be able to view patient intake records within 2 seconds of submission (p95 response time). | Automated performance test shows ≤200 ms median latency for 10 000 concurrent reads; logs record view timestamps. | Clinical Lead |
| FR-002 | Access to patient history must be restricted to records of patients assigned to the clinician (role‑based access control). | Attempted access by unauthorized role returns HTTP 403; audit log records denial event. | System Administrator |
| FR-003 | All view actions must be logged with user ID, timestamp, and record ID; logs retained for 7 years on immutable storage. | Log entry created for every read; retention policy verified by quarterly audit; immutability proven by digital signatures. | Compliance Officer |
| FR-004 | Staff must be able to enter new patient demographics and insurance information via the web form with field‑level validation. | Form rejects invalid formats; validation error rate <1 % per batch; successful submission triggers confirmation receipt within 1 second. | Front‑Desk Lead |
| FR-005 | Open‑Source Stack Constraint – All components must be built from open‑source software without proprietary licenses. | Dependency list contains only OSI‑approved licenses; license audit passes 100 % compliance. | DevOps Engineer |
| FR-006 | Air‑Gap Deployment – The Docker‑Compose environment must operate without external network access. | Network scan shows zero outbound connections; deployment scripts abort if external DNS or registry calls are detected; deployment success rate ≥99.9 % in isolated lab. | System Administrator |

## Governance Model
1. **Executive Sponsor** – Ultimate authority; approves budget and scope changes; reports to Board quarterly.
2. **Project Steering Committee** – Includes Administrator, Compliance Officer, Lead Clinician; reviews risk register, KPI trends, and regulatory audit findings monthly.
3. **Technical Working Group** – System Administrator, DevOps Engineer, Security Engineer; responsible for Docker‑Compose pipeline integrity, air‑gap verification, and open‑source licensing compliance; meets weekly.
4. **Clinical Advisory Board** – Front‑Desk and Clinician representatives; validates that form latency stays below 200 ms (p95) and that UI meets WCAG 2.1 AA criteria; meets monthly.
5. **Audit & Compliance Sub‑Committee** – Led by Compliance Officer; conducts quarterly HIPAA technical safeguard reviews referencing 45 CFR §164.312(a)(2)(iv) for encryption key management; produces audit reports for senior management.

## Traceability Matrix
| Stakeholder | Requirement ID(s) |
|------------|-------------------|
| Patients (ST-01) | FR-001, FR-002, FR-003, FR-006, REQ-001 |
| Front‑Desk Staff (ST-02) | FR-004, FR-005, REQ-002 |
| Clinicians (ST-03) |	FR-001, FR-002 |
| System Administrator (ST-04) |	FR-002, FR-003, FR-006 |
| Compliance Officer (ST-05) |	FR-003, FR-005, FR-006 |
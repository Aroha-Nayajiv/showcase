# Business Requirements
                
# 1. Business Vision
The PatientIntake system will enable healthcare providers to capture patient demographics, insurance information, and comprehensive medical history through a secure web form while fully complying with HIPAA § 164.312(a)(2)(iv) encryption safeguards. By leveraging only open‑source components, the solution avoids vendor lock‑in and reduces total cost of ownership, supporting on‑premise deployment in air‑gapped environments. Success will be measured by regulatory compliance, operational efficiency gains, and measurable improvements in data integrity and auditability.

# 2. Scope Definition
**In Scope:** Secure web form capture, encrypted PostgreSQL storage, RBAC implementation, PDF generation with watermark/timestamp, full audit logging, Docker Compose deployment guide for air‑gapped environments.
**Out of Scope:** Integration with external EHR systems, mobile native applications, cloud‑based hosting services, advanced analytics beyond basic reporting.

# 3. Functional Requirements (FR)
| ID | Title | Description |
|----|-------|-------------|
| FR-004 | Capture Patient Demographics Securely | The web form must collect name, date of birth, address, and contact information for each patient and store each field encrypted at rest; a compliance audit must verify that no plaintext PHI is persisted in logs or backups. |
| FR-005 | Role‑Based Access Control for Data Operations | Admin, Clinician, and Front‑Desk roles must be able to create, read, update, or export records only according to their permission matrix; a quarterly access‑review report must show zero unauthorized access attempts. |
| FR-006 | Generate Auditable PDF Intake Summary | Authorized staff can generate a PDF summary that includes a visible watermark identifying the staff member and an immutable timestamp; the PDF must be downloadable only after successful authentication and the download event must be recorded in the audit log. |
| FR-007 | Maintain Immutable Audit Log of All Reads/Writes | Every read, write, or export operation must be recorded with user ID, timestamp, operation type, and affected record ID; logs must be retained for a minimum of seven years on write‑once storage and be verifiable via checksum. |
| FR-008 | Provide Unit and Integration Test Coverage for Core Flows | Automated test suites must cover form validation (including required fields and format checks), encryption/decryption correctness, and RBAC enforcement; test results must show ≥90% pass rate on each CI run before any release candidate is promoted. |

**Acceptance Criteria**
* **FR‑004** – All captured fields are stored using AES‑256 encryption at rest; automated scans confirm zero plaintext PHI in database backups and application logs.
* **FR‑005** – RBAC matrix enforced by PostgreSQL role policies; penetration test attempts to access out‑of‑scope records are logged and denied; quarterly report shows 0 unauthorized accesses.
* **FR‑006** – Generated PDFs contain a dynamic watermark with staff name/ID and a UTC timestamp; download endpoint requires valid session token; each download creates an audit log entry with operation type “EXPORT”.
* **FR‑007** – Audit entries include user ID, timestamp (ISO‑8601), operation type (CREATE/READ/UPDATE/EXPORT), and record UUID; retention script archives logs to WORM media after 7 years; checksum verification runs nightly with alert on mismatch.
* **FR‑008** – CI pipeline runs unit & integration suites on every commit; coverage report shows ≥90% pass for all core modules; build fails if coverage drops below threshold.

# 4. Non‑Functional Requirements (NFR)
| ID | Description |
|----|-------------|
| NFR-001 | System response time ≤ 200 ms for form submission under normal load (≥95 % of transactions). |
| NFR-002 | System availability ≥ 99.9 % uptime per month measured by infrastructure monitoring. |
| NFR-003 | Mandatory audit logging of every read/write/export operation with immutable retention for 7 years. |
| NFR-004 | End‑to‑end encryption: TLS 1.3 for all network traffic and AES‑256 field‑level encryption at rest. |

# 5. Success Criteria / KPIs
| KPI ID | Metric |
|--------|--------|
| KPI-01 | Form Completion Rate – ≥ 90 % of sessions result in successful submission. |
| KPI-02 | Response Time Compliance – ≥ 95 % of submissions ≤ 200 ms. |
| KPI-03 | System Availability – ≥ 99.9 % uptime per month. |
| KPI-04 | Audit Log Generation Rate – 100 % of read/write/export actions logged with integrity verification. |

# 6. Stakeholder Analysis
| Stakeholder ID | Role | Primary Need | Key Pain Point | RBAC Tier |
|----------------|------|-------------|----------------|-----------|
| ST-01 | Clinical Staff | Immediate access to accurate patient history for care decisions | Delays caused by manual paperwork | Clinician |
| ST-02 | Patients | Assurance that personal health information is protected | Fear of data breach exposing sensitive health data | Read‑only (view only) |
| ST-03 | Compliance Officer | Evidence of HIPAA compliance for audits | Lack of verifiable audit trails | Read‑only |
| ST-04 | Front‑Desk Staff | Efficient intake workflow with minimal re‑entry effort | Inconsistent data entry leading to errors | Front‑Desk |
| ST-05 | Administrator | Ability to configure roles, policies and audit logs securely | Complex configuration risking mis‑settings | Admin |

# 7. Risk Register
| Risk ID | Description | Likelihood / Impact | Mitigation |
|---------|-------------|---------------------|-----------|
| RISK-01 | Unauthorized data exposure during transmission of patient form data over the network. | M / H | Enforce TLS 1.3 for all web traffic; implement field‑level AES‑256 encryption at rest; conduct quarterly penetration testing; enforce strict key‑management procedures. |
| RISK-02 | Vulnerabilities in open‑source components leading to potential exploitation. | M / H | Adopt continuous dependency scanning pipeline (e.g., OWASP Dependency‑Check) with automatic patching; maintain curated whitelist of vetted libraries; perform monthly security reviews. |
| RISK-03 | Deployment misconfiguration in the Docker‑Compose air‑gapped environment causing service downtime or exposure of logs. | L / M Create immutable Docker images signed with Notary; enforce configuration‑as‑code reviews; run automated compliance checks against hardened baseline before each release. |
| RISK-04 | Gaps in audit‑log generation or retention that could cause non‑compliance with HIPAA §164.312(b). | L / H Implement write‑once read‑many (WORM) storage for audit logs; automate daily checksum verification scripts that alert security team within 24 hours of any discrepancy; conduct quarterly audit‑log completeness review against regulatory checklist. |
| RISK-05 | Schedule slippage due to resource constraints in an on‑premises environment lacking cloud elasticity. | M / M Establish two‑sprint buffer in project plan; secure dedicated hardware resources early; track capacity utilization weekly via dashboard visible to PMO. |

# 8. Narrative Summary
1. **Compliance Focus** – Risks RISK‑01 and RISK‑04 directly affect HIPAA compliance. Mitigations reference specific technical safeguards (encryption at rest and in transit) and audit‑log retention requirements, ensuring that any breach can be detected and reported within mandated timeframes.
2. **Security Emphasis** – RISK‑02 addresses open‑source supply‑chain risk through proactive vulnerability management. Signed Docker images and immutable infrastructure reduce attack surface introduced by misconfiguration (RISK‑03).
3. **Delivery Assurance** – RISK‑05 acknowledges realistic constraint of on‑prem deployment without cloud auto‑scaling. Buffer periods and capacity monitoring mitigate risk of missed milestones while preserving the open‑source only mandate.
Each mitigation is actionable, measurable, and assigned to a clear owner who will report status in the weekly steering committee meeting. The risk register will be reviewed bi‑weekly throughout the project lifecycle to ensure emerging threats are captured promptly.

# 9. Operational Constraints Summary
* **No External Cloud Services** – All runtime dependencies must reside on the internal network; any cloud SaaS is prohibited.
* **Docker Compose Only** – Orchestration limited to Docker Compose; Kubernetes or other orchestrators are out of scope.
* **Offline Image Distribution** – Initial container images transferred via secure removable media; subsequent updates require signed offline packages.
* **Audit Trail Requirement** – Every deployment action (image load, compose up/down, configuration change) must be logged in an immutable audit log retained for a minimum of seven years.
* **Open‑Source Licensing Governance** – Quarterly review ensures all components remain under OSI‑approved licenses; any deviation triggers a compliance halt.
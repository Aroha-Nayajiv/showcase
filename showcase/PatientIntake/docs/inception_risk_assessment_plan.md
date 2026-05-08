# Risk Assessment and Mitigation Plan

## 1. Business Vision
The PatientIntake solution will provide health‑care providers with a fully open‑source, HIPAA‑compliant SaaS platform for capturing, protecting, and retrieving patient intake data. By containerising PostgreSQL and the web stack, the service delivers secure, auditable records while supporting multi‑tenant scalability and high availability for on‑premise deployments.

### In‑Scope
- Structured web form for demographics, insurance information, and medical history.
- Field‑level encryption at rest (AES‑256) and TLS 1.3 in transit.
- Role‑based access control (RBAC) for Admin, Clinician, and Front‑Desk roles.
- Immutable audit log retaining every read/write operation for ≥7 years.
- PDF intake summary generation with visible watermark "Confidential – PHI" and embedded export timestamp visible only to the exporter.
- Automated unit and integration test suite covering form validation, encryption correctness, and RBAC edge cases.
- Docker‑Compose orchestration for on‑premise deployment with an air‑gap hardening guide.

### Out‑of‑Scope
- Cloud‑hosted managed database services.
- Commercial encryption libraries.
- Direct integration with external EHR systems beyond data export.
- Mobile native applications (web UI only).

## 3. Stakeholder Analysis
| Stakeholder | Core Need | Pain Point | RBAC Tier | Measurable Objective |
|---|---|---|---|---|
| Patient (End User) | Secure submission of PHI with assurance of confidentiality | Fear of data breach or unauthorized disclosure | Viewer (own record only) | OBJ‑001 – Ensure HIPAA‑compliant data capture with end‑to‑end encryption |
| Front‑Desk Staff | Efficient intake workflow that reduces manual re‑entry | High error rate from paper forms leading to compliance risk | Operator (create/read submissions) | OBJ‑002 – Streamline intake while maintaining full auditability of create actions |
| Clinician | Timely access to accurate patient history for care decisions | Delays caused by excessive security checks | Clinician (read/write limited to assigned patients) | OBJ‑003 – Provide low‑latency secure access to PHI under role constraints |
| Administrator | Centralised configuration, user provisioning, and tenant isolation | Complexity of RBAC policy management across clinics | Administrator (full privileged) | OBJ‑004 – Maintain hardened multi‑tenant environment with documented change control |
| Compliance Officer | Complete audit trail for every read/write operation to satisfy HIPAA and SOC 2 | Incomplete or tampered logs impeding audits | Auditor (read‑only immutable logs) | OBJ‑005 – Achieve immutable log retention for 7 years on write‑once storage |

## 4. Functional Requirements
**FR‑001 – Secure Patient Data Capture**
- *Description*: Collect demographics, insurance, and medical history via a web form with field‑level AES‑256 encryption.
- *Acceptance Criteria*: 100 % of required fields validated; encrypted payload stored; no plaintext PHI appears in logs or backups.

**FR‑002 – Role‑Based Access Control**
- *Description*: Enforce RBAC tiers Admin, Clinician, Front‑Desk for read/write operations.
- *Acceptance Criteria*: Access matrix tested; unauthorized role receives HTTP 403; every access attempt recorded in audit log.

**FR‑003 – Immutable Audit Logging**
- *Description*: Record every read and write operation with timestamp, user ID, and action type.
- *Acceptance Criteria*: Logs retained ≥7 years on immutable storage; daily SHA‑256 checksum verification confirms integrity.

**FR‑004 – PDF Intake Summary Generation**
- *Description*: Authorized staff can export a PDF containing the patient’s intake data, watermarked "Confidential – PHI" and an export timestamp visible only to the exporter.
- *Acceptance Criteria*: PDF generated ≤2 seconds; watermark present; timestamp embedded in PDF metadata; export limited to Clinician or Admin roles.

**FR‑005 – Automated Test Suite**
- *Description*: Provide unit and integration tests covering form validation, encryption/decryption correctness, and RBAC edge cases.
- *Acceptance Criteria*: ≥80 % code coverage; CI pipeline fails on any regression; tests executed on each commit.

## 5. Success Criteria / KPIs
| KPI ID | Metric Name | Target Value | Measurement Method | Linked Objective |
|---|---|---|---|---|
| KPI‑001 | Monthly System Availability | ≥99.9 % uptime | Grafana dashboards aggregated monthly | OBJ‑004 |
| KPI‑002 | Encryption Compliance Rate | 100 % of PHI fields encrypted at rest & in transit | Automated compliance scans (e.g., Scout Suite) | OBJ‑001 |
| KPI‑003 | Audit Log Completeness | ≥99.5 % of operations recorded correctly | Log integrity checksum comparison vs transaction logs | OBJ‑005 |
| KPI‑004 | PDF Export Integrity Score | ≥99 % of PDFs contain correct watermark & timestamp without alteration | Random sample verification by Compliance Officer | OBJ‑003 |
| KPI‑005 | User Adoption Rate (Front‑Desk) | ≥90 % of daily intake sessions use the new web form | Daily usage analytics from application logs | OBJ‑002 |
| KPI‑006 | Incident‑Free Period Post‑Launch | Zero security incidents for first 90 days | Incident tracking system reports | OBJ‑001 |

## 6. Risk Assessment and Mitigation
**RISK‑001 – PHI Data Breach During Transmission**
- *Impact*: High confidentiality loss.
- *Mitigation*: Enforce TLS 1.3 with forward secrecy; field‑level AES‑256 encryption; quarterly penetration tests; use HSM for key management; rotate keys quarterly.

**RISK‑002 – Unauthorized Access Due to Misconfigured RBAC**
- *Impact*: High potential for data exposure.
- *Mitigation*: Deploy automated role‑validation scripts; bi‑weekly access reviews; enforce least‑privilege principle; store RBAC matrix in version‑controlled policy repo; integrate policy linting into CI pipeline.

**RISK‑003 – Incomplete Audit Log Retention Leading to Compliance Failure**
- *Impact*: Medium compliance risk.
- *Mitigation*: Implement immutable write‑once storage (e.g., WORM); retain logs ≥7 years; daily SHA‑256 checksum verification; archive logs to air‑gapped backup storage.

**RISK‑004 – PDF Export Tampering or Unauthorized Distribution**
- *Impact*: Low to medium reputational risk.
- *Mitigation*: Apply digital signatures to PDFs; embed visible watermark and timestamp; restrict export API to Admin/Clinician roles; log each export event with user ID and timestamp; enforce download rate limiting.

**RISK‑005 – Service Downtime Exceeding SLA During Peak Load**
- *Impact*: Medium operational risk.
- *Mitigation*: Auto‑scale container replicas based on CPU/memory thresholds; perform load testing up to 2× expected peak; implement circuit breaker patterns; monitor latency and trigger alerts when response time >500 ms.

## 7. Assumptions & Constraints
- All components are open source and kept up to date with security patches.
- On‑premise environment provides network isolation sufficient for air‑gap deployment.
- Stakeholders will allocate resources for quarterly security reviews.
- No external cloud services will be used; all components run within the Docker Compose stack defined in the deployment artifact.

## 8. Vision Statement (Reiteration)
The PatientIntake platform will deliver a secure, auditable, open‑source SaaS solution that enables clinics to capture patient demographics, insurance details, and medical history while meeting HIPAA requirements, achieving high availability, and supporting multi‑tenant scalability on on‑premise infrastructure.
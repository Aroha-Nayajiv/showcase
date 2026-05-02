# Open-Source Technology Stack Selection


## Availability & Reliability
- **NFR-008** System uptime ≥99.9 % monthly (Prometheus SLA monitoring).
- **NFR-009** Daily encrypted backups retained 30 days; quarterly restore test verifies recovery.
- **NFR-010** Air‑gap enforcement: No outbound network traffic after container start; validated by network policy scan.

## Acceptance Test Outline
1. **Performance Test**: Simulate 1000 concurrent read requests; verify ≥90 % complete within 2 s (FR‑001).
2. **Encryption Verification**: Run pgcrypto inspection script; confirm all PHI columns encrypted with AES‑256‑GCM (NFR‑004).
3. **TLS Scan**: Execute SSL Labs scan; ensure TLS 1.3 only (NFR‑005).
4. **RBAC Test**: Attempt unauthorized record access with Front‑Desk credentials; expect denial and log entry (FR‑002).
5. **Audit Log Test**: Insert read/write actions; run log audit script; confirm 100 % completeness and immutable signatures (FR‑003, NFR‑007).
6. **PDF Export Test**: Generate PDF for a sample record; verify watermark includes timestamp and user ID; measure latency ≤2 s for 90 % (FR‑008).
7. **Air‑Gap Validation**: Deploy Docker Compose in isolated network; run egress scan; ensure no outbound connections (NFR‑010).

## Documentation Deliverables
- Business Vision Document (this artifact)
- Stakeholder Matrix
- Requirements Specification (functional & security)
- Risk Register
- Traceability Matrix
- Test Plan and Scripts

*All sections are traceable to the defined FR, NFR, KPI, and RISK identifiers.*

## Business Vision
The PatientIntake system will enable clinicians to retrieve complete, accurate patient intake information within seconds of submission, supporting timely care decisions while maintaining strict HIPAA compliance. The solution will be deployed on-premises using Docker Compose, ensuring no external cloud dependencies and facilitating an air-gapped environment.

## Stakeholder Alignment
| Stakeholder Role | Primary Need | Key Pain Point | RBAC Tier | Linked Objective |
|------------------|--------------|----------------|----------|-------------------|
| Compliance Officer | Assurance of HIPAA adherence | Lack of audit evidence for air-gap compliance | Administrator | OBJ-SEC-001 |
| IT Operations Manager | Reliable on-prem deployment process | Manual steps prone to error | Operator | OBJ-DEP-001 |
| Front-Desk Supervisor | Quick system availability for patient intake | Long installation windows disrupt workflow | Operator | OBJ-DEP-001 |
| Security Engineer | Secure key handling and TLS enforcement | Complex key rotation procedures | Administrator | OBJ-SEC-002 |
| Clinical Lead | Access to up-to-date patient data after deployment | Downtime impacts care decisions | Clinician | OBJ-CARE-001 |

## Functional Requirements
- **FR-001**: Clinicians must be able to view patient intake records within 2 seconds of submission (p95 response time). *Acceptance Criteria*: Automated load test shows 95th percentile <200 ms for 100 concurrent users; logs capture view timestamps.
- **FR-002**: Access to patient history must be restricted to records of patients assigned to the clinician (role-based access control). *Acceptance Criteria*: Security test verifies that a clinician cannot retrieve records outside their assignment; audit log records each access attempt.
- **FR-003**: All view actions must be logged with user ID, timestamp, and record ID; logs retained for 7 years on immutable storage. *Acceptance Criteria*: Log retention script confirms 7-year immutability; tamper-evidence hash validated daily.
- **FR-004**: Staff must be able to enter new patient demographics and insurance information via the web form with field-level encryption at rest and in transit. *Acceptance Criteria*: Penetration test confirms TLS 1.3 usage; database fields encrypted with AES-256; validation errors displayed for malformed input.
- **FR-005**: Data entry errors must be flagged in real time with a validation error rate < 1 % per batch. *Acceptance Criteria*: Monitoring of validation logs shows error rate ≤0.9 % over 10 k submissions.
- **FR-006**: Staff must receive a confirmation receipt within 1 second after successful submission. *Acceptance Criteria*: UI latency measurement shows median ≤1 s for receipt display.
- **FR-007**: Administrators must configure role permissions and audit log settings through a secured admin console. *Acceptance Criteria*: Role-management UI updates persisted; audit log configuration changes recorded.
- **FR-008**: System must support export of patient intake summaries as PDF with watermark containing export timestamp and exporting user ID. *Acceptance Criteria*: Exported PDF includes watermark text "Exported by {userID} at {ISO-timestamp}"; verification script checks presence.
- **FR-009**: Deployment must be achievable using Docker Compose without external cloud services; the environment must be air-gapped. *Acceptance Criteria*: Docker Compose script runs to completion on an isolated network; no external DNS or registry calls detected.
- **FR-010**: Patients must be informed via a privacy notice at the start of the intake form that their data will be encrypted and stored securely, referencing HIPAA requirements. *Acceptance Criteria*: Privacy notice displayed and user acknowledgment logged before any data entry.

## Risk Register
- **RISK-020**: Insufficient documentation leading to deployment errors. *Mitigation*: Conduct a dry-run with a cross-functional team; capture lessons in a living guide stored in version-controlled repository; schedule quarterly reviews.
- **RISK-001**: Unauthorized PHI access due to misconfigured RBAC. *Mitigation*: Automated role-permission matrix validation in CI pipeline; quarterly re-assessment by security team.
- **RISK-002**: Encryption key compromise. *Mitigation*: Store keys in HSM; rotate keys every 90 days; enforce MFA for key access.
- **RISK-003**: Audit log tampering. *Mitigation*: Write logs to append-only storage with digital signatures; immutable backup retention for 7 years.
- **RISK-004**: Deployment in non-air-gapped environment inadvertently exposing PHI. *Mitigation*: Environment validation script aborts if external network interfaces are detected.

## Measurement & Review Cycle
- Quarterly review of KPI trends by the Governance Board.
- Annual audit of documentation against HIPAA §164.312(b) requirements.
- Post-deployment retrospective after each major release to capture lessons learned and update the risk register.

## Traceability Matrix
| Requirement ID | Stakeholder Owner | Linked KPI | Acceptance Test |
|-----------------|-------------------|------------|-------------------|
| FR-001 | Clinical Lead | KPI-001 (Response Time) | Load test with 100 concurrent users |
| FR-002 | Compliance Officer | KPI-017 (RBAC Coverage) | Role-based access test |
| FR-003 | Security Engineer | KPI-003 (Audit Log Completeness) | Log integrity verification |
| FR-004 | Front-Desk Supervisor | KPI-002 (Form Validation) | Real-time validation monitoring |
| FR-005 | Front-Desk Supervisor | KPI-005 (Error Rate) | Validation error rate analysis |
| FR-006 | Front-Desk Supervisor | KPI-004 (Receipt Latency) | UI latency measurement |
| FR-008 | Security Engineer | KPI-030 (Watermark Accuracy) | Export verification script |
| FR-009 | IT Operations Manager | KPI-009 (Deployment Success) | Docker Compose execution on isolated network |
| FR-010 | Compliance Officer | KPI-014 (Privacy Notice Acknowledgment) | Audit of acknowledgment logs |

All sections are traceable to original objectives and provide measurable, auditable criteria for successful on-prem deployment of the PatientIntake system.
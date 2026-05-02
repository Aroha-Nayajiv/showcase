# Audit Logging Specification


## Audit Logging Specification – Patient Intake System

### Overview
The audit logging component records every read, write, update, delete, and export operation on patient data stored in the on-premise PostgreSQL database. Logs are immutable, signed, and retained for seven years to satisfy HIPAA §164.312(a)(1) and internal KPI targets.

### Stakeholder Table
| Stakeholder Role | Primary Need | Key Pain Point | RBAC Tier | Linked Objective |
|---|---|---|---|---|
| Clinician | Verify patient data integrity | Incomplete audit trails hinder trust | Clinician | OBJ‑LOG‑01 |
| Front‑Desk Staff | Confirm successful data entry | Need assurance of record creation logs | FrontDesk | OBJ‑LOG‑01 |
| Administrator | Manage system compliance | Difficulty detecting unauthorized access | Admin | OBJ‑SEC‑01 |
| Compliance Officer | Demonstrate HIPAA auditability | Manual log collection is error‑prone | Compliance | OBJ‑COM‑01 |
| Security Engineer | Detect tampering attempts | Lack of immutable storage | Security | OBJ‑SEC‑02 |

## Business Vision
The PatientIntake system will enable secure, efficient capture of patient demographics, insurance, and medical history via a web form, ensuring HIPAA‑compliant handling of PHI and providing clinicians rapid access to intake data.

## Functional Requirements
| ID | Description |
|---|---|
| FR-001 | Clinicians must be able to view patient intake records within 2 seconds of submission (p95 response time). |
| FR-002 | Access to patient history must be restricted to records of patients assigned to the clinician (role‑based access control). |
| FR-003 | All view actions must be logged with user ID, timestamp, and record ID; logs retained for 7 years on immutable storage. |
| FR-004 | Staff must be able to enter new patient demographics and insurance information via the web form with field‑level encryption at rest and in transit. |
| FR-005 | Data entry errors must be flagged in real time with a validation error rate < 1 % per batch. |
| FR-006 | Staff must receive a confirmation receipt within 1 second after successful submission. |
| FR-007 | Administrators must configure role‑based permissions and audit‑log settings through a secured UI. |
| FR-008 | System must support export of patient intake summaries as PDF with watermark containing export timestamp and exporting user ID. |
| FR-009 | Export operation must complete within 200 ms (p95) for authorized staff. |
| FR-010 | Patients must be informed via a privacy notice at the start of the intake form that their data will be encrypted and stored securely, referencing HIPAA compliance. |

## Key Performance Indicators
| ID | Metric | Target | Measurement Method | Owner |
|---|---|---|---|---|
| KPI-001 | Log Write Latency (p95) | ≤ 100 ms | Automated latency monitor in CI pipeline. | OBJ-004 |
| KPI-002 | Log Retention Completeness | 100 % of logs retained for ≥ 7 years | Quarterly audit of storage bucket counts vs retention policy. | OBJ-001 |
|- KPI-003 - Export Watermark Presence - 100 % of PDFs contain correct watermark and timestamp - Automated PDF inspection script on each export - OBJ-003 |
|- KPI-004 - Audit Log Search Response Time - ≤ 200 ms (p95) for queries by Compliance Officer - Performance test of search UI queries - OBJ-005 |
|- KPI-005 - Encryption Compliance Rate - 100 % of log files encrypted with AES‑256 GCM - Cryptographic scan of storage files - OBJ-001 |
|- KPI-036 - Audit Log Integrity Success Rate - ≥ 99.9 % of logs verified as immutable per scan - Daily integrity verification script; alerts on failure - OBJ-006 |

## Risk Register
| ID | Description | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| RISK-001 | Unauthorized PHI access due to misconfigured RBAC | Medium | High | Automated role‑permission matrix validation before each release; quarterly review. |
| RISK-002 | Encryption key compromise | Medium | High | Store keys in HashiCorp Vault sealed mode; rotate every 90 days; restrict access via MFA. |
| RISK-003 | Audit log tampering | Low | High | Write logs to append‑only storage with digital signatures; weekly checksum verification. |
| RISK-004 | Deployment in non‑air‑gapped environment exposing PHI | Low | High | Docker‑Compose network_mode:none; volume audit_data mounted read‑only for app containers. |
| RISK-005 | Performance degradation causing SLA breach (>200 ms) | Medium | Medium | Load testing with synthetic traffic; auto‑scale container resources on threshold breach. |

## Traceability Matrix
| Requirement ID | Linked KPI(s) |
|---|---|
| FR-001 | KPI-001 |
| FR-002 | KPI-002 |
| FR-003 | KPI-002, KPI-003, KPI-036 |
| FR-004 | KPI-004 |
| FR-005 | KPI-004 |
| FR-006 | KPI-005 |
| FR-007 | KPI-036 |
| FR-008 | KPI-003 |
| FR-009 | KPI-004 |
| FR-010 | KPI-005 |

## Acceptance Criteria
* **FR‑001** – Simulated load test of 1,000 concurrent clinician view requests must show 95th percentile response ≤ 2 s.
* **FR‑002** – Attempted access by a user without assigned patient must be denied and logged.
* **FR‑003** – Every read/write action creates a log entry with user ID, timestamp, record ID; audit query returns 100 % of actions for the past 7 years.
* **FR‑004** – Form submission encrypts data at rest and in transit; verification via packet capture shows TLS 1.3.
* **FR‑005** – Validation engine flags > 1 % erroneous entries; test suite injects malformed rows and expects error flag.
* **FR‑006** – Confirmation receipt appears within 1 s after submit; measured by client‑side timer.
* **FR‑007** – Admin UI allows role creation; changes reflected in access control list and audited.
* **FR‑008** – Exported PDF contains visible watermark “Exported by {user} on {timestamp}”.
* **FR‑009** – Export latency measured across 500 exports must have p95 ≤ 200 ms.
* **FR‑010** – Privacy notice displayed before any data entry; user must click “I Agree” which is logged with timestamp.

## Governance Process
1. **Policy Definition** – The Compliance Officer drafts the Audit Logging Policy referencing HIPAA §164.312(b) and records it in the central policy repository.
2. **Implementation Review** – The Security Engineer validates that logging mechanisms meet the functional and non‑functional requirements.
3. **Periodic Audits** – Quarterly audits verify retention, encryption, and integrity metrics against the KPI table.
4. **Change Management** – Any modification to log configuration triggers a documented change request reviewed by the Administrator and Compliance Officer.
5. **Incident Response** – Log tampering incidents invoke the Incident Response Procedure (RISK‑001 mitigation) with evidence preserved for forensic analysis.
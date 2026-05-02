# Technology Strategy (Overview)

## Business Vision
The PatientIntake system will enable secure, rapid capture and retrieval of patient health information, ensuring compliance with HIPAA while supporting clinical decision‑making and operational efficiency.

## 2. Scope Definition
**In‑Scope:** Structured web form collection, PostgreSQL storage with row‑level security, audit logging, PDF generation with watermark and timestamp, unit/integration test suite, Docker‑Compose orchestration, air‑gap deployment guide.
**Out‑Of‑Scope:** Cloud services, proprietary encryption libraries, third‑party SaaS analytics, mobile native applications, long‑term data archiving beyond 7‑year retention.

## 3. Stakeholder Table
| Stakeholder | Primary Need | Pain Point | RBAC Tier | Linked Objective |
|---|---|---|---|---|
| Patient | Assurance that PHI is protected and processed quickly | Distrust of electronic data capture | End User | OBJ-001 |
| Front‑Desk Staff | Efficient data entry with real‑time validation and receipt | Manual error correction consumes time | Operator | OBJ-002 |
| Clinician | Immediate access to accurate intake data | Delayed records impede care | Clinician | OBJ-003 |
| Administrator | Centralized role configuration and audit visibility | Complex permission matrices increase error risk | Administrator | OBJ-004 |
| Compliance Officer | Evidence of HIPAA controls for audit readiness | Lack of traceable logs and encryption proof | Auditor | OBJ-005 |

## 4. Business Requirements Traceability Matrix
| Stakeholder Need | Functional Requirement(s) | KPI(s) |
|---|---|---|
| Assurance of protection & speed (Patient) | FR-001, FR-004, FR-010 | KPI-001, KPI-002 |
| Efficient entry & receipt (Front‑Desk) | FR-005, FR-006 | KPI-002, KPI-004 |
| Immediate accurate data (Clinician) | FR-002, FR-007, FR-008 | KPI-003, KPI-004 |
| Centralized config & audit (Administrator) | FR-003, FR-007 | KPI-003, KPI-005 |
| Audit readiness (Compliance Officer) | FR-009, FR-010 | KPI-001, KPI-003 |

## 5. Functional Requirements
1. **FR-001:** Collect complete patient demographics via web form. *Acceptance:* 100 % required fields captured and validated per format rules.
2. **FR-002:** Capture insurance information with real‑time validation against insurer database. *Acceptance:* ≥95 % first‑entry validation success.
3. **FR-003:** Record medical history including ICD‑10 codes. *Acceptance:* ≥98 % completeness of coded entries.
4. **FR-004:** Store submissions in PostgreSQL with field‑level AES‑256 encryption at rest and TLS 1.3 in transit. *Acceptance:* Security scan shows no plaintext PHI.
5. **FR-005:** Implement role‑based access control (admin, clinician, front‑desk). *Acceptance:* Unauthorized attempts are blocked and logged.
6. **FR-006:** Generate PDF summary per patient, exportable only by authorized roles, with watermark containing user ID and timestamp. *Acceptance:* Watermark present on 100 % of exports; audit log entry created.
7. **FR-007:** Maintain immutable audit log of every read/write operation retained for 7 years. *Acceptance:* Log tamper‑evidence retained; completeness ≥99.9 %.
8. **FR-008:** Provide automated unit and integration test suite covering form validation, encryption, and access control edge cases. *Acceptance:* Test coverage ≥90% and all tests pass in CI.
9. **FR-009:** Deploy entire stack via Docker Compose in an air‑gapped environment with no external dependencies. *Acceptance:* Deployment script runs without internet access; environment verification passes.

## 6. Success Criteria / KPIs
| KPI ID | Metric | Target | Measurement Method | Linked Objective |
|---|---|---|---|---|
| KPI-001 | Encryption compliance rate | 100 % of PHI fields encrypted at rest and in transit | Automated compliance scan weekly | OBJ-001 |
| KPI-002 | Form response time (p95) | ≤200 ms per submission | Load test using JMeter on staging | OBJ-002 |
| KPI-003 | Audit log completeness | 100 % of read/write events logged | Log audit script daily comparing DB ops vs log entries | OBJ-004 |
| KPI-004 | PDF export watermark accuracy | 100 % of PDFs contain timestamp and user ID watermark | Automated checksum of PDF metadata per export | OBJ-003 |
| KPI-005 | System uptime (air‑gapped) | ≥99.9 % monthly uptime | Monitoring via Prometheus/Grafana alerts | OBJ-004 |

## 7. Risk Assessment and Mitigations
1. **RISK-001:** Unauthorized PHI access due to misconfigured RBAC. *Mitigation:* Implement least‑privilege role matrix; quarterly RBAC audit using OpenSCAP.
2. **RISK-002:** Encryption key compromise. *Mitigation:* Store keys in HSM or HashiCorp Vault; rotate keys every 90 days; enforce MFA for key access.
3. **RISK-003:** Audit log tampering or loss. *Mitigation:* Write logs to append‑only immutable storage with digital signatures; retain for 7 years; regular integrity verification.
4. **RISK-004:** Performance degradation under peak load affecting SLA. *Mitigation:* Conduct regular stress testing; auto‑scale container resources within Docker Compose limits; monitor response times.
5. **RISK-005:** Deployment in non‑air‑gapped environment exposing PHI. *Mitigation:* Enforce deployment checklist that validates network isolation before starting Docker Compose; automated script aborts if external connectivity detected.

## 8. Governance and Review Cadence
- Bi‑weekly stakeholder review meetings to validate compliance metrics.
- Quarterly audit readiness assessment by Compliance Officer.
- Continuous integration pipeline includes security linting and encryption verification.

## 9. Documentation Index
- Business Vision Statement (Section 1)
- Scope Definition (Section 2)
- Stakeholder Table (Section 3)
- Traceability Matrix (Section 4)
- Functional Requirements (Section 5)
- KPIs (Section 6)
- Risk Register (Section 7)
- Governance Plan (Section 8)
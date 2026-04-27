# Stakeholder Analysis Matrix

### 1. Project Vision
The PatientIntake system will provide a fully HIPAA‑compliant, open‑source solution for capturing patient demographics, insurance, and medical history via a secure web form, storing data in PostgreSQL with field‑level encryption, and generating watermarked PDF summaries. The solution must be deployable on‑premises using Docker Compose and support an air‑gap environment.

### 3. Scope Definition
In‑Scope
FR-001: Web front‑end for data entry with TLS 1.3 transport encryption.
FR-002: Field‑level AES‑256 encryption at rest for all PHI.
FR-003: Role‑based access control (admin, clinician, front‑desk) enforced by PostgreSQL RLS.
FR-004: Immutable audit log for every read/write operation retained 7 years.
FR-005: PDF generation with visible watermark and export timestamp.
FR-006: Automated unit and integration tests covering validation, encryption, and RBAC edge cases.
FR-007: Docker Compose deployment scripts and air‑gap setup guide.
Out‑Of‑Scope
Integration with external cloud services.
Advanced analytics or machine‑learning on PHI.
Mobile native applications (only web UI).

### 5. Traceability Matrix
| Stakeholder | Need | Linked Requirement(s) |
|---|---|---|
| ST-01 Patient | Secure, easy data entry; privacy assurance | FR-001, FR-002, NFR-003 |
| ST-02 Front‑Desk Staff | Quick intake, minimal training | FR-001, FR-004 |
| ST-03 Clinician | Immediate access to complete records | FR-003, FR-005 |
| ST-04 System Administrator | Reliable deployment, auditability | FR-004, FR-006, FR-007 |
| ST-05 Compliance Officer | Evidence of HIPAA controls, audit logs | FR-004, NFR-003, NFR-004 |
| ST-06 IT Operations | Secure air‑gap setup, reproducible builds | FR-007, NFR-006 |

## 2. Stakeholder Matrix
| ID | Stakeholder | Needs | Risks | Ownership |
|----|-------------|-------|------|-----------|
| ST-01 | Patient | Secure, easy data entry; privacy assurance | Fear of data breach | Business Owner: Compliance Officer |
| ST-02 | Front‑Desk Staff | Quick intake, minimal training | Manual errors, time pressure | Business Owner: Operations Manager |
| ST-03 | Clinician | Immediate access to complete, accurate records | Incomplete data, delayed access | Business Owner: Clinical Lead |
| ST-04 | System Administrator | Reliable deployment, auditability | Configuration drift, log tampering | Business Owner: IT Operations Lead |
| ST-05 | Compliance Officer | Evidence of HIPAA controls, audit logs | Regulatory audit failures | Business Owner: Compliance Officer |
| ST-06 | IT Operations | Secure air‑gap setup, reproducible builds | Complex container hardening | Business Owner: IT Operations Lead |

## 3. Business Requirements (Functional)
| Req ID | Description | Acceptance Criteria | Stakeholder Owner |
|--------|-------------|--------------------|-------------------|
| REQ-001 | All PHI fields must be encrypted at rest using AES‑256. | Verify via security scan that 100% of PHI columns are encrypted; automated test confirms encryption on insert. | System Administrator |
| REQ-002 | Data in transit must use TLS 1.3 with forward secrecy. | Network capture shows all traffic encrypted; compliance test validates TLS version and cipher suite. | System Administrator |
| REQ-003 | Encryption keys must be rotated every 90 days and logged. | Key rotation job runs monthly; audit log contains entry for each rotation; no key older than 90 days in use. | Security Engineer |
| REQ-004 | Every read/write operation must generate an immutable audit record containing user ID, timestamp, operation type, and affected data identifier. | Audit table contains a new row for each CRUD action; records cannot be altered or deleted; retention ≥7 years verified by audit query. | System Administrator |
| REQ-005 | Generate a PDF intake summary per patient with visible watermark and export timestamp. | PDF contains watermark text “Confidential – Patient Intake”, includes export timestamp metadata; >99% of generated PDFs pass automated checksum test. | Front‑Desk Staff |
| REQ-006 | Authorized staff shall be able to export the PDF summary only after successful authentication and role verification. | Export endpoint returns PDF only for users with role clinician or admin; unauthorized attempts receive 403 response logged in audit. | Clinician |
| REQ-007 | Provide automated unit and integration tests covering form validation, encryption, and RBAC edge cases. | Test suite includes ≥80% code coverage; CI pipeline fails on any test regression; tests executed on each commit. | QA Lead |
| REQ-008 | Deploy entire stack via Docker Compose on‑premises with no external cloud dependencies. | Docker Compose up brings up all containers on a clean host; deployment script completes without external network calls; air‑gap guide validated on isolated network. | IT Operations |

## 5. Success Criteria / KPIs
| KPI ID | Metric | Target 
|--------|--------|--------|
| KPI-01 | Form completion rate | ≥92% weekly (submission count / attempted sessions) 
| KPI-02 | Average page load time (p95) | ≤200 ms 
| KPI-03 | PHI encryption coverage | 100% AES‑256 at rest 
| KPI-04 | Audit log integrity & retention | ≥7 years with zero tampering incidents 
| KPI-05 | PDF export watermark & timestamp compliance | >99% of PDFs contain correct watermark & timestamp

## 6. Risks and Mitigations (Enhanced)
| Risk ID | Description | Impact / Likelihood | Mitigation (concrete actions) 
|--------|-------------|-------------------|---------------------------|
| RISK-01 | Encryption key mismanagement leading to unauthorized decryption. | High / Medium | Implement automated key rotation every 90 days using HashiCorp Vault; enforce dual‑control approval for key access; audit vault access logs weekly. 
| RISK-02 | Audit log overflow causing performance degradation. | Medium / Medium | Partition audit tables monthly; archive partitions older than 12 months to read‑only storage; monitor table size alerts; run vacuum regularly. 
| RISK-03 | Unauthorized access due to RBAC misconfiguration. | High / Medium | Conduct quarterly RBAC review using automated policy compliance tests in CI; enforce least‑privilege defaults; integrate OPA policies for runtime enforcement. 
| RISK-04 | Deployment failure in air‑gap environment. | Medium / Medium | Provide detailed offline Docker Compose guide; include script that verifies image signatures via GPG before deployment; run dry‑run validation on isolated host. 
| RISK-05 | PDF watermark removal by malicious insider. | Low / Medium | Embed invisible digital signature using PDF/A‑3 standard; set PDF permissions to read‑only; log any permission change attempts in audit trail.

## 8. Governance and Review Cadence
- Bi‑weekly stakeholder review meeting to validate requirements against HIPAA §164.312(a)(2)(iv) encryption controls and §164.308(a)(1) audit controls.
- Quarterly security audit by Compliance Officer to ensure continued adherence to HIPAA, GDPR, NIST 800‑53, and WCAG 2.1 AA.
- All policies (POL‑001, POL‑002, etc.) and training programs (TRN‑001) are documented and tracked; compliance with REQ‑005 is verified.
- Change management follows DEP‑FR‑001 guidelines: images signed with GPG, secrets injected via Docker secrets, and DEP‑NFR‑001 vulnerability thresholds are enforced.

## Business Vision
The patient intake system will enable secure collection of patient demographics, insurance information, and medical history, ensuring HIPAA compliance and supporting clinical workflows.

## Acceptance Criteria
- AC‑001: All PHI fields are encrypted at rest and in transit; verification via security test.
- AC‑002: Audit log records include user ID, timestamp, operation type, and are immutable.
- AC‑003: PDF summary includes watermark text \"Confidential\" and export timestamp; only authorized roles can generate.
- AC‑004: Deployment via Docker Compose completes without external network calls.
- AC‑005: System meets response time <200 ms under load of 100 concurrent users.
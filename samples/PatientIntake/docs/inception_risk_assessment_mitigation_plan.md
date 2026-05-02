# Risk Mitigation and Contingency Plan

### Scope Definition
- In‑Scope: Web‑based patient intake form, encryption (TLS 1.3, AES‑256 at rest), role‑based access control (admin, clinician, front‑desk), immutable audit logging, PDF summary generation with watermark and timestamp, Docker Compose deployment in air‑gapped environment, automated unit/integration test suite.
- Out‑Of‑Scope: Cloud services, third‑party SaaS analytics, mobile native applications, AI‑driven decision support.

### Architectural Vision
- Layered Architecture: Presentation layer (HTML/JS served via open‑source Nginx), Business Logic layer (Python Flask services), Data layer (PostgreSQL with row‑level security). All components run as containers orchestrated by Docker Compose.
- Security Controls: TLS 1.3 for all network traffic, field‑level AES‑256 encryption for PHI at rest, HSM‑backed key management, immutable append‑only audit log stored on write‑once read‑many (WORM) volume.
- Compliance Anchors: HIPAA §164.312(a)(2)(iv) for encryption, §164.308(a)(1)(ii) for audit controls, and NIST SP 800‑53 Rev 5 AC‑2, AU‑6.

### Success Criteria / KPIs
| KPI ID | Metric Name | Target Value | Measurement Method | Linked Objective |
|---|---|---|---|---|
| KPI-001 | Encryption Compliance | 100% of PHI fields encrypted at rest | Automated compliance scan (OpenSCAP) | Ensure HIPAA safeguard §164.312(a)(2)(iv) |
| KPI-002 | Form Response Time | ≤200 ms p95 | Synthetic load test (k6) | Provide timely patient intake |
| KPI-003 | Audit Log Completeness | 100% of read/write events logged | Log audit script comparing DB ops vs log entries | Enable forensic traceability |
| KPI-004 | Deployment Air‑Gap Verification | 0 external network calls detected | CI validation script output | Maintain compliance environment |

### 1. Data Collection
- **FR-001**: The web form shall capture patient demographics (name, DOB, address, contact) with field‑level encryption at rest. Acceptance: Automated test verifies encrypted storage of each field and successful decryption only by authorized service.
- **FR-002**: The form shall capture insurance information (provider, policy number, group) with validation against open‑source insurer lookup service. Acceptance: 99% validation success rate on test data set.
- **FR-003**: The form shall capture medical history (allergies, medications, prior diagnoses) with free‑text and coded entries (ICD‑10). Acceptance: Minimum 95% of coded entries map to valid ICD‑10 codes.

### 3. Access Control
- **FR-004**: Role‑based access control (RBAC) shall define three tiers: Admin, Clinician, Front‑Desk. Acceptance: Permission matrix test confirms Admin can read/write all records, Clinician can read all and write notes, Front‑Desk can create and read own submissions only.
- **FR-005**: All read and write operations shall be logged with user ID, timestamp, and operation type. Acceptance: Audit log query returns matching entries for every transaction in test suite.

### 4. Audit Logging
- **FR-006**: Audit logs shall be immutable, append‑only, and retained for seven years on WORM storage. Acceptance: Attempted log modification is rejected and audit script reports 0% tampering.
- **FR-007**: Export actions shall record watermark metadata (exporting user ID, timestamp) in the generated PDF. Acceptance: PDF inspection tool extracts watermark matching logged export event.

### 5. PDF Export
- **FR-008**: Authorized staff may generate a PDF summary per patient. The PDF shall include a visible watermark with user ID and export timestamp. Acceptance: Manual test verifies watermark appears on every page and matches audit log.
- **FR-009**: PDF generation shall complete within 2 seconds for records under 5 MB. Acceptance: Performance test shows 95th percentile ≤2 s on reference hardware.

### 6. Testing
- **FR-010**: Automated unit tests shall cover form validation rules for each field with ≥90% code coverage. Acceptance: Coverage report shows 92% overall.
- **FR-011**: Integration tests shall simulate end‑to‑end submission, encryption, RBAC enforcement, audit logging, and PDF export. Acceptance: All scenarios pass without security violations.
- **FR-012**: Security regression tests shall include OWASP ZAP scan and encryption key leakage checks. Acceptance: No high‑severity findings.

## Stakeholder Table
| Stakeholder Role | Primary Need | Key Pain Point | RBAC Tier | Linked Objective |
|---|---|---|---|---|
| Patient | Secure, private intake experience with clear consent | Trust in data handling; fear of unauthorized disclosure | No direct system access (view‑only via clinician) | OBJ-001: Ensure 100% consent capture and audit log of consent events |
| Front‑Desk Staff | Efficient, error‑free data entry and immediate submission feedback | Manual entry errors and re‑work due to validation gaps | Tier 2 (front‑desk) | OBJ-002: Achieve <1% form validation errors |
| Clinician | Immediate access to accurate records | Delayed info impedes care decisions | Tier 1 (clinician) | OBJ-003: 95% record availability within 200 ms |
| Administrator | Secure configuration & auditability | Complex permission management | Tier 0 (admin) | OBJ-004: Full RBAC enforcement and audit completeness |
| Compliance Officer | Evidence of HIPAA compliance | Lack of audit trails for regulators | Tier 0 (admin) | OBJ-005: Complete audit log retention and compliance reporting |

## REST API Path Table
| Method | Path | Description | Related FR |
|---|---|---|---|
| POST | /api/intake | Submit new patient intake form | FR-001, FR-002, FR-003 |
| GET | /api/intake/{id} | Retrieve patient intake record (RBAC enforced) | FR-004 |
| PUT | /api/intake/{id} | Update notes or status (clinician) | FR-004 |
| GET | /api/intake/{id}/export | Generate PDF export with watermark and timestamp metadata | FR-008, FR-007 |
| GET | /api/healthz | Health check endpoint for monitoring purposes | N/A |

## Business Requirements (Selected Critical FRs)
- **FR-001**: Clinicians must be able to view patient intake records within 2 seconds of submission (p95 response time). *Acceptance*: 95 % of record retrievals ≤200 ms measured over 30‑day window.
- **FR-002**: Access to patient history must be restricted to records of patients assigned to the clinician (role‑based access control). *Acceptance*: No unauthorized read events detected in audit logs.
- **FR-003**: All view actions must be logged with user ID, timestamp, and record ID; logs retained for 7 years on immutable storage. *Acceptance*: Log completeness 100 % verified nightly.
- **FR-005**: Data entry errors must be flagged in real time with a validation error rate < 1 % per batch. *Acceptance*: Automated form validation logs show error rate ≤0.5 %.
- **FR-006**: Staff must receive a confirmation receipt within 1 second after successful submission. *Acceptance*: 99 % of submissions display receipt ≤1 s.
- **FR-010**: Patients must be informed via a privacy notice at the start of the intake form that their data will be encrypted and stored securely. *Acceptance*: 100 % of sessions display notice and capture consent.

## Functional Artifacts

### Entity Field List for Intake Form
| Field ID | Data Type | Encryption at Rest | Validation Rule |
|----------|----------|-------------------|----------------|
| patient_id | UUID | AES‑256 | Required, unique |
| first_name | String | AES‑256 | Non‑empty, max 50 chars |
| last_name | String | AES‑256 | Non‑empty, max 50 chars |
| dob | Date | AES‑256 | Valid date, age ≥0 |
| insurance_number | String | AES‑256 | Regex pattern, required |
| medical_history | Text | AES‑256 | Optional, max 2000 chars |
| consent_timestamp | ISO8601 datetime | AES‑256 | Auto‑populated on consent |

### Gherkin User Stories

Feature: Patient Intake Submission
  As a Front‑Desk Staff member
  I want to submit a complete intake form
  So that the patient record is stored securely and the patient receives immediate confirmation

  Scenario: Successful form submission
    Given the front‑desk user is authenticated as role "front‑desk"
    And the intake form is displayed with all required fields
    When the user enters valid data for all fields
    And clicks the "Submit" button
    Then the system stores the record encrypted at rest
    And creates an audit log entry with action "create"
    And displays a confirmation receipt within 1 second
    And the patient receives a consent acknowledgment email

Feature: Clinician Record Access
  As a Clinician
  I want to view a patient’s intake record quickly
  So that I can make timely care decisions

  Scenario: Retrieve record within SLA
    Given a clinician is authenticated with role "clinician"
    And the patient record exists and is assigned to the clinician
    When the clinician requests GET /api/intake/{id}
    Then the system returns the decrypted record within 200 ms
    And logs the view action with user ID and timestamp

Feature: PDF Export with Watermark
  As an authorized staff member
  I want to export a patient’s intake summary as a PDF
  So that I can share it securely while preserving provenance

  Scenario: Export PDF with correct watermark
    Given the user has role "clinician" or "administrator"
    When the user calls GET /api/intake/{id}/pdf
    Then the system generates a PDF containing all intake data
    And embeds a watermark with the exporting user ID and current timestamp
    And logs the export action in the immutable audit log

## Risk Register (Expanded)
| Risk ID | Description | Likelihood | Impact | Mitigation |
|--------|-------------|------------|--------|------------|
| RISK-001 | Unauthorized PHI access due to mis‑configured RBAC | Medium | High | Automated role‑permission matrix tests in CI; quarterly manual review; Oso policy version control |
| RISK-002 | Encryption key compromise | Low | High | Deploy HashiCorp Vault with HSM integration; rotate keys every 90 days; enforce MFA for vault access |
| RISK-003 | Audit‑log tampering or loss | Low | High | Write logs to append‑only WORM storage; sign each entry with SHA‑256; nightly checksum verification |
| RISK-004 | Deployment in non‑air‑gapped environment exposing PHI | Medium | High | Pre‑deployment script aborts if any external network interface is active; CI gate validates netstat output |
| RISK-005 | Data entry errors leading to inaccurate records | Medium | Medium | Real‑time field validation using validator.js; enforce WCAG‑2.1 AA contrast; provide clear error messages |

## API Specification (High-Level)
| Path | Method | Description |
|------|--------|-------------|
| /api/intake | POST | Submit new patient intake record (JSON payload). |
| /api/intake/{id} | GET | Retrieve intake record for authorized clinician. |
| /api/intake/{id}/pdf | GET | Generate PDF summary with watermark and timestamp. |
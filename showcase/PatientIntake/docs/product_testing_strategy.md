# Testing Strategy Document

## Stakeholder Role Analysis for Testing Strategy Document

The testing strategy for the **PatientIntake** system is grounded in a clear understanding of the four primary stakeholder roles that interact with the intake workflow: **Patient**, **Front‑desk Clerk**, **Clinician**, and **Admin**. Each role description includes business goals, pain points, and testing implications that drive the creation of user stories, acceptance criteria, edge‑case scenarios, and coverage metrics.

### 1. Patient
**Goals**
- Secure data submission – Provide personal health information (PHI) with confidence that it is encrypted in transit (TLS 1.3) and at rest (field‑level AES‑256).
- Fast and intuitive experience – Complete the intake form in ≤ 2 minutes on a typical broadband connection.
- Visibility of data handling – Receive a confirmation receipt that contains no PHI.

**Pain Points**
- Complex forms cause abandonment; unclear required fields increase error rates.
- Trust concerns when any insecure transmission indicator appears.
- Vague error messages leave patients unsure whether to retry.

**Testing Implications**
- Validate TLS 1.3 enforcement and client‑side encryption before network transmission.
- Measure form completion time across browsers/devices; flag any scenario > 2 min.
- Verify receipt notifications contain no PHI and are delivered within 5 seconds of successful submission.
- Test form validation messages for clarity and WCAG 2.1 AA accessibility.

### 2. Front‑desk Clerk
**Goals**
- Efficient data capture – Quickly enter or verify patient information to keep appointment flow smooth.
- Accurate record creation – Ensure demographic and insurance data are stored without transcription errors.
- Auditability – Ability to view who entered or modified a record for compliance reporting.

**Pain Points**
- Redundant data entry leads to errors.
- Permission confusion about editable fields after submission.
- Performance bottlenecks when retrieving prior records.

**Testing Implications**
- Simulate clerk workflow with pre‑filled patient form; verify read‑only view of already‑submitted fields while allowing edits to non‑PHI administrative fields.
- Test role‑based UI controls: clerks must not see encryption key management screens.
- Load‑test record‑retrieval endpoints with 100 concurrent clerk sessions; ensure response ≤ 1 s.
- Verify audit‑log entries capture clerk user ID, timestamp, and operation type for every create/update action.

### 3. Clinician
**Goals**
- Rapid access to complete medical history before/during consultation.
- Secure yet convenient access – Authenticate once per session; avoid repeated credential prompts.
- Traceability of changes – Know when and by whom a record was modified.

**Pain Points**
- Excessive login friction leads to workarounds.
- Partial data visibility hinders care decisions.
- Unclear change history reduces trust in data integrity.

**Testing Implications**
- Verify SSO (OpenID Connect) authentication and session continuity for ≥ 30 minutes of inactivity.
- Ensure all required intake sections (demographics, insurance, medical history) are displayed in clinician view; flag missing sections as failures.
- Test audit‑trail UI: clinicians see chronological edit list with user IDs but no encryption keys.
- Negative test: clinician attempts to access another clinician’s patient record; confirm access denied and logged as unauthorized attempt.

### 4. Admin
**Goals**
- Policy enforcement – Configure RBAC policies and encryption key rotation schedules.
- System health monitoring – Observe audit‑log volume, error rates, encryption health metrics.
- Compliance reporting – Generate reports demonstrating adherence to HIPAA §164.312(a)(2)(iv) and audit‑log retention requirements.

**Pain Points**
- Complex configuration UI can lead to misconfiguration exposing PHI.
- Log overload makes locating relevant events difficult.
- Manual key rotation is error‑prone and may cause downtime.

**Testing Implications**
- Validate RBAC matrix against defined roles; ensure no privilege‑escalation paths exist.
- Simulate key rotation: generate new AES‑256 keys, re‑encrypt sample dataset, verify decryption succeeds with new key while old keys are retired after a defined grace period.
- Run log‑aggregation test: ingest 10 000 audit events and confirm query latency < 200 ms for typical compliance queries (e.g., "show all reads by Clinician X on date Y").
- Verify compliance reports include total read/write counts, failed authentication attempts, and encryption‑key usage timestamps.

## Summary of Test Design Drivers
1. **Security validation** – TLS 1.3 enforcement, field‑level AES‑256 encryption at rest, automated key rotation checks.
2. **Performance thresholds** – Form completion ≤ 2 min; API response ≤ 1 s under load; audit‑log query ≤ 200 ms.
3. **Usability metrics** – Error‑message clarity, WCAG 2.1 AA compliance, session continuity for clinicians.
4. **Compliance coverage** – Audit‑log completeness, RBAC enforcement, HIPAA‑specific reporting (PHI handling, key management).

---

## Testing Strategy Document for PatientIntake System

### 5. Purpose
The testing strategy defines how the HIPAA‑compliant patient intake system will be validated against functional, security, and compliance requirements. It focuses on the structured web form, field‑level encryption at rest and in transit, role‑based access control (RBAC), audit logging, PDF summary generation with watermarking, and the automated test suite required for continuous verification.

#### US‑001 | Patient | Secure Intake Form
**Narrative:** As a *Patient*, I want to securely enter my personal demographics, insurance information, and medical history via a web form so that my data is protected in transit and at rest and clinicians can access an accurate record.

**Acceptance Criteria:**

Given the patient accesses the intake URL over HTTPS
When the patient fills all mandatory fields and submits the form
Then the submission must be transmitted over TLS 1.3 only
And each PHI field must be encrypted client‑side with AES‑256 before network transmission
And the system stores the encrypted payload at rest using field‑level AES‑256 keys
And a receipt email is sent within 5 seconds containing no PHI content
And the receipt includes a unique reference ID for later lookup

*Traceability:* FR‑002 (TLS enforcement), FR‑003 (Transport Encryption), NFR‑002 (Client‑side encryption), FR‑004 (PDF/receipt handling).

#### US‑002 | Front‑desk Clerk | Verify & Edit Pre‑filled Intake Data
**Narrative:** As a *Front‑desk Clerk*, I want to verify a patient’s pre‑filled intake data and edit non‑PHI administrative fields so that the appointment flow remains efficient while preserving data integrity.

**Acceptance Criteria:**

Given a patient has already submitted an intake form
When the clerk opens the patient record in the clerk UI
Then all PHI fields appear read‑only
And non‑PHI fields (e.g., appointment notes) are editable
And any edit triggers an audit log entry capturing clerk ID, timestamp, and operation type
And the clerk UI does not expose encryption key management screens

*Traceability:* FR‑006 (Docker Compose deployment – not directly relevant but ensures environment consistency), NFR‑003 (Audit trail), FR‑002 (TLS).

#### US‑003 | Clinician | Retrieve PDF Intake Summary with Watermark
**Narrative:** As a *Clinician*, I want to retrieve a PDF summary of a patient’s intake data that includes a secure watermark and timestamp so that I can review accurate information while maintaining HIPAA auditability.

**Acceptance Criteria:**

Given the clinician is authenticated via SSO and has an active session ≥ 30 minutes of inactivity tolerated
When the clinician requests the PDF summary for a patient record
Then the system generates a PDF containing all intake sections (demographics, insurance, medical history)
And the PDF includes a visible watermark stating "Confidential – HIPAA Protected" with generation timestamp
And the PDF is stored in an immutable location for the required retention period (7 years)
And access to the PDF is logged with clinician ID, timestamp, and outcome (success/failure)

*Traceability:* FR‑004 (PDF generation with watermark), NFR‑003 (Audit trail), NFR‑002 (Encryption at rest), KPI‑003 (Compliance audit passed).

#### US‑004 | Admin | Configure RBAC & Automated Key Rotation Schedule
**Narrative:** As an *Admin*, I want to configure role‑based access control policies and define an automated encryption key rotation schedule so that the system remains compliant with HIPAA key management requirements without manual intervention.

**Acceptance Criteria:**

Given the admin accesses the security configuration console
When the admin defines a new RBAC policy mapping roles to permissions
Then the policy is persisted and immediately enforced for all subsequent requests
And attempts to perform unauthorized actions are denied with HTTP 403 logged as security events
When the admin enables automated key rotation with a 30‑day interval
Then a new AES‑256 key is generated automatically at each interval
And existing encrypted records are re‑encrypted using the new key within a defined grace period of 24 hours
And old keys are retired after successful re‑encryption without service interruption
And audit logs capture key creation timestamps, rotation events, and any decryption failures

*Traceability:* FR‑002 (TLS), NFR‑002 (Key management automation), NFR‑003 (Audit trail), KPI‑003 (Compliance audit passed).

### 6. Traceability Matrix
| User Story | Functional Requirement(s) | Non‑Functional Requirement(s) | KPI(s) | Risk(s) |
|------------|---------------------------|----------|--------|----------|
| US‑001 | FR‑002, FR‑003 | NFR‑002 (client encryption), NFR‑001 (performance ≤2 min) | KPI‑001 (system availability) | RISK‑001 (data breach) |
| US‑002 | FR‑006 (deployment consistency) | NFR‑003 (audit log completeness) | KPI‑002 (zero security incidents first 90 days) | RISK‑002 (regulatory non‑compliance) |
| US-003 | FR-004 (PDF watermark) | NFR-003 (audit trail), NFR-001 (response time ≤1 s) | KPI-003 (audit compliance passed) | RISK-001 (data breach) |
| US-004 | FR-002 (TLS), FR-006 (deployment) | NFR-002 (key rotation automation), NFR-003 (audit log) | KPI-003 (audit compliance passed) | RISK-006 (key management failure) |

### 7. Test Coverage Mapping to Drivers
| Driver | Covered by Story(s) |
|--------|-------------------|
| Security validation – TLS 1.3 & AES 256 | US‑001, US‑004 |
| Performance thresholds – form ≤2 min, API ≤1 s | US‑001, US‑003 |
| Usability – WCAG 2.1 AA & clear messages | US‑001 |
| Compliance – audit log retention & reporting | US‑002, US-003, US-004 |

### 8. Additional Test Cases Not Explicitly Mapped Above
1. **Negative TLS version test:** Attempt submission over TLS 1.2 – expect rejection logged as security event.
2. **Key rotation failure simulation:** Force decryption failure after rotation – verify system falls back to previous key within grace period and logs incident.
3. **PDF watermark tamper test:** Modify generated PDF checksum – ensure integrity check fails and alert is raised.
4. **Audit log query performance under load:** Execute concurrent queries for last 30 days of reads/writes – confirm latency <200 ms.

---

*All user stories now include full Given/When/Then acceptance criteria linked to concrete requirement IDs.*

# Patient Intake System – Testing Strategy (Refined)

## 9. Overview
This document defines the **minimum viable product (MVP)** testing scope for the HIPAA‑compliant patient intake system. It aligns all user stories, acceptance criteria, and test metrics with the functional requirements **FR‑001 through FR‑005**, the non‑functional requirements **NFR‑002**, **NFR‑003**, and the primary risk **RISK‑001**. The goal is to ensure confidentiality, integrity, and traceability of patient data while supporting SaaS multi‑tenant deployment.

## 10. User Stories (Traceable to Requirements)
| ID | Persona | Goal | Benefit |
|----|----------|------|---------|
| US-001 | Patient | **Submit intake form** securely via HTTPS | Data is captured with end‑to‑end encryption and auditability |
| US-002 | Front‑Desk Clerk | **Create patient record** after intake | Enables staff to store patient data without exposing PHI |
| US-003 | Clinician | **Export patient record** as PDF/A‑2b with watermark | Provides immutable evidence for care while preserving confidentiality |
| US-004 | Admin | **Configure role‑based access controls** and view audit logs | Enforces least‑privilege and supports compliance audits |
| US-005 | QA Engineer (Automated Test) | **Execute unit & integration tests** covering validation, encryption, RBAC, PDF generation | Guarantees repeatable evidence of HIPAA compliance |

*All stories are directly traceable to:* **FR‑001**, **FR‑002**, **FR‑003**, **FR‑004**, **FR‑005**, **NFR‑002**, **NFR‑003**, **RISK‑001**.

## 11. Acceptance Criteria (BDD Format & Traceability)

### AC-005 – US-005 (Automated Test Suite)
**Given** a fresh Docker Compose environment where TLS termination is disabled for internal service calls
**When** the CI pipeline triggers the test suite
**Then** unit tests validate input sanitisation and field encryption; integration tests verify encrypted storage/retrieval and RBAC enforcement; end‑to‑end tests confirm PDF export and watermark presence; security tests cover key rotation and TLS 1.3 enforcement
**And** overall test coverage is ≥ 95 % with security test coverage ≥ 1 test per HIPAA technical safeguard (164.312)
**And** any failure aborts the pipeline with detailed logs
**And** simulated network latency triggers retry logic verification; mismatched encryption keys cause decryption failures captured as security test failures.

## 12. Design Needs (Downstream Design Phase)
| Area | Specification |
|------|----------------|
| **Encryption Specification** | Field‑level encryption uses **AES‑256‑GCM**, per‑record random IVs; keys managed per NIST SP 800‑57 recommendations; rotation every 30 days; no fallback to previous key (see Risk Mitigation). |
| **Transport Security** | External traffic enforces **TLS 1.3**; internal service‑to‑service calls use mutual TLS (mTLS) with certificates rotated every 30 days. |
| **Audit Log Format** | JSON Lines containing `event_type`, `actor_id`, `timestamp`, `resource_id`, `checksum`, `outcome`. Logs are append‑only, immutable, retained ≥ 7 years (per NIST 800‑53 AU‑6). |
| **PDF Generation** | Use **WeasyPrint**, configured for PDF/A‑2b compliance; watermark template `Confidential – Exported by {user_id} on {ISO8601_timestamp}`. |
| **Test Automation Framework** | Unit & integration tests in **pytest**, end‑to‑end UI tests via **Selenium WebDriver**, coverage measured by **coverage.py`. |

## 13. Metrics & Reporting
- **Pass Rate:** ≥ 95 % of automated test cases must pass on each CI run.
- **Security Test Coverage:** Minimum one test per HIPAA technical safeguard (164.312).
- **Audit Log Completeness:** 100 % of CRUD operations generate a corresponding immutable log entry.
- **PDF Watermark Verification:** Automated OCR check confirms watermark text appears on every generated PDF.
- **Key Rotation Verification:** Test suite validates that key rotation events succeed and old keys are not used for new writes.

## 14. Risk Mitigation
| Risk ID | Mitigation Strategy |
|---------|----------------------|
| RISK-001 (Encryption Key Rotation Failure) | System aborts write operation on rotation failure; alerts are sent to Ops; no fallback to previous key to avoid key compromise. |
| RISK-002 (Audit Log Loss due to Network Partition) | Local buffer persists logs locally; once connectivity restores, buffered entries are flushed atomically to central immutable store. |
| RISK-003 (Performance Bottleneck in Encryption) | Load testing validates encryption latency < 50 ms per record; auto‑scaling policies trigger additional encryption workers under load. |

### US-001: Front Desk Intake Form Submission
**Persona:** Front Desk Staff  
**Goal:** Submit patient intake data securely.

**Given** the front desk user is authenticated and has role `front_desk` (linked to **FR‑002**, **NFR‑002**)  
**When** they fill all required fields and click **Submit**  
**Then** the system encrypts the data with AES‑256 at rest, stores the record in PostgreSQL with row‑level security, returns HTTP 201, and logs the write operation (**AU‑6**) (**FR‑001**, **FR‑003**, **NFR‑003**) .

**Error handling:**
- Missing required field → display inline validation error (see **AC‑001**)  
- Network interruption → client retries up to 3 times; if still fails, shows an error page without persisting partial data (see **AC‑001**) .

---

### US-002: Generate PDF Export
**Persona:** Front Desk Staff  
**Goal:** Export a patient record as a secure PDF.

**Given** the user is authenticated with role `front_desk` (**FR‑002**)  
**When** they select a patient record and click **Generate PDF**  
**Then** the system creates a PDF/A‑2b file, embeds a visible watermark "Confidential – Authorized Staff Only", adds an export timestamp metadata field, stores the file in a protected volume, and logs the export event (**AU‑7**) (**FR‑004**) .

**Error handling:**
- PDF generation failure (e.g., library error) → system returns an error message and does not create a file.  
- Unauthorized user attempts export → access denied logged, no PDF produced.

---

### US-003: Clinician Record Access
**Persona:** Clinician  
**Goal:** View patient intake data securely.

**Given** the clinician is authenticated with role `clinician` (**FR‑002**)  
**When** they open a patient’s intake record  
**Then** the UI displays decrypted patient data, and an audit log records a read event with timestamp and user ID (**AU‑8**) (**FR‑003**) .

**Error handling:**
- Attempt to access a record belonging to another clinic → access denied, audit log entry created.  
- Session timeout before request → system redirects to login without exposing data.

---

### US-004: Admin RBAC Management & Audit Log Query
**Persona:** Admin  
**Goal:** Manage RBAC policies and query audit logs atomically.

**Given** the admin is authenticated with role `admin` (**FR‑002**)  
**When** they modify RBAC policies or query the audit log  
**Then** changes are persisted atomically; audit log records the admin action with before/after state snapshots (**AU‑9**) (**FR‑005**) .

**Error handling:**
- Invalid policy definition → system rejects change with descriptive error; no partial update.

---

### US‑005 (Optional): Email Confirmation of Submission
**Persona:** Patient (via front desk)  
**Goal:** Receive a secure confirmation email after form submission.

**Given** the patient provided a valid email address during submission (**FR‑006**)  
**When** the system processes the intake form successfully  
**Then** it sends a confirmation email over TLS 1.2+ containing a signed URL valid for 24 hours that allows read‑only view of the submitted summary; access is logged (**AU‑10**) .

**Error handling:**
- Email bounce → system flags record for manual follow‑up; no sensitive data exposed.

---

### Integration Tests
| Flow | Description | Success Criteria |
|------|-------------|-------------------|
| End‑to‑end submission flow (US‑001 → AC‑001) | Submit form → store record → audit log entry | HTTP 201 returned; audit entry present |
| PDF export flow (US‑002 → AC‑002) | Generate PDF → store file → audit log entry | PDF file created in protected volume; watermark present; audit entry recorded |
| Audit log verification (US‑003/US‑004) | Read record / modify RBAC → audit entries created | Correct before/after snapshots captured |

### Security Tests
| Test Type | Objective |
|-----------|-----------|
| TLS handshake validation | Verify TLS 1.2+ is used for all external communications |
| Encryption key rotation simulation | Ensure keys are rotated per schedule without service interruption |
| Role escalation attempts (RISK‑001) | Confirm unauthorized escalation results in 403 and audit log entry |

## Automation Roadmap
1. **CI Pipeline:** Use GitHub Actions to run pytest suites on every push.
2. **Test Data Management:** Generate synthetic PHI using Faker with deterministic seeds for reproducibility.
3. **Compliance Reporting:** Export test run summaries to an HTML report that includes coverage percentages and security test results for audit purposes.
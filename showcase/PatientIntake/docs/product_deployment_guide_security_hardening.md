# Patient Intake Feature Specification (Refined)

## 1. Personas

### 1.1 Patient (PER-001)
- **Role**: End‑user submitting personal health information via the web intake form.
- **Goals**: Provide accurate demographic, insurance, and medical history information quickly and securely so that care can begin without delay.
- **Security Concerns**: Data in transit must be protected from eavesdropping; data at rest must be unreadable to anyone without explicit authorization; patient must be assured that only authorized staff can view or export the PDF summary.
- **Typical Interactions**:
  1. Opens the intake portal over HTTPS (TLS 1.3, cipher TLS_AES_256_GCM_SHA384 – see **FR‑002**).
  2. Completes the structured form; each field is encrypted client‑side (AES‑256‑GCM) before transmission.
  3. Receives a confirmation screen with a reference number.
  4. May request export of the PDF summary; system verifies role before providing a download link.

### 1.2 Front Desk Staff (PER‑002)
- **Role**: Administrative employee who initiates intake sessions, verifies insurance eligibility, and assists patients with form completion.
- **Goals**: Capture complete patient information efficiently while ensuring compliance with HIPAA and internal policies; be able to retrieve or update a submission when needed for scheduling.
- **Security Concerns**: Must not have access to encryption keys; should see only the data necessary for scheduling; all actions must be logged for audit.
- **Typical Interactions**:
  1. Logs into the system using multi‑factor authentication.
  2. Starts a new intake session and may assist the patient in filling fields.
  3. Views a read‑only summary of submitted data; cannot export the PDF unless explicitly granted "export" permission.
  4. Updates patient status; each update creates an immutable audit entry.

### 1.3 Clinician (PER‑003)
- **Role**: Licensed healthcare provider who reviews the completed intake form and PDF summary to make clinical decisions.
- **Goals**: Access full medical history quickly, verify insurance coverage, and generate treatment plans while maintaining strict confidentiality.
- **Security Concerns**: Requires full read access and PDF export rights; must be able to verify that the PDF has not been tampered with (watermark and timestamp); all accesses must be recorded for compliance reporting.
- **Typical Interactions**:
  1. Authenticates with strong credentials and optional smart‑card.
  2. Opens the patient's intake record; system decrypts data on demand using role‑based keys.
  3. Exports the PDF summary; system applies a dynamic watermark containing clinician ID and ISO‑8601 timestamp.
  4. Reviews audit log entries for any unexpected access attempts.

---

## 2. Design Requirements (Traceability)
| Requirement ID | Description |
|----------------|-------------|
| **FR‑001** | Secure intake – all PHI must be encrypted in transit and at rest. |
| **FR‑002** | Transport Encryption – TLS 1.3 with cipher suite TLS_AES_256_GCM_SHA384 (referenced in persona interactions). |
| **FR‑004** | PDF summary – generated per patient with watermark and export timestamp visible only to authorized staff. |
| **FR‑005** | Deploy the entire stack via Docker Compose for on‑premise or cloud deployment. |
| **NFR‑002** | Automated key rotation – keys stored in HashiCorp Vault, rotated every 90 days. |
| **KPI‑001** | System availability ≥ 99.9 % (supports MVP scope). |
| **KPI‑002** | Zero security incidents in the first 90 days. |

---

### US‑001 – Front Desk Staff Enters Patient Demographics
**As a** Front Desk staff,
**I want** to enter patient demographic and insurance information into the intake form,
**so that** the patient record is complete for scheduling.

**Acceptance Criteria (Given/When/Then)**:
1. **Given** the staff is authenticated with role `front_desk` and MFA enabled,
   **When** they submit the form,
   **Then** the payload is sent over TLS 1.3, encrypted client‑side with AES‑256‑GCM, and stored encrypted at rest.
2. **Given** a successful submission,
   **When** the system persists the data,
   **Then** an audit log entry (`AC‑001`) is created with action `CREATE`, actor `front_desk`, and HMAC signature.
3. **Given** a TLS handshake failure,
   **When** the patient attempts to submit,
   **Then** a friendly error message is shown and no data is stored (`AC‑001`).

### US‑003 – Clinician Exports PDF Summary
**As a** Clinician,
**I want** to export a PDF summary of a patient’s intake record,
**so that** I can review it offline while preserving auditability.

**Acceptance Criteria:**
1. **Given** the clinician is authenticated with MFA and possesses `export` permission,
   **When** they request the PDF,
   **Then** the system generates a PDF/A‑2b compliant document via WeasyPrint, embeds a dynamic watermark containing clinician ID and timestamp, encrypts the PDF with AES‑256 before storage, and provides a download link that expires after 5 minutes (`AC‑003`).
2. **Given** the Vault transit engine is unavailable,
   **When** the clinician requests export,
   **Then** the system returns an error message without exposing raw data and logs the failure (`AC‑003`).

---

## 4. MVP Scope Checklist (Security Hardening Tasks)
| # | Item | Description | Related Requirement |
|---|------|-------------|----------------------|
| 1 | TLS Enforcement | Enforce TLS 1.3+ on all inbound HTTP endpoints; reject lower versions. | FR‑002 |
| 2 | Field‑Level Encryption | Implement client‑side encryption using Web Crypto API (AES‑256‑GCM) before transmission; server stores ciphertext only. | FR‑001 |
| 3 | PostgreSQL RBAC | Configure roles `admin`, `clinician`, `front_desk` with SELECT/INSERT/UPDATE privileges matching user stories; enable row‑level security policies per data element. | FR‑001 |
| 4 | Immutable Audit Log | Deploy rsyslog sidecar writing to write‑once storage; schema columns `log_id`, `entity_id`, `action`, `actor_id`, `timestamp`, `hmac_signature`; retention 7 years. | FR‑004 |
| 5 | PDF Generation Hardening | Use WeasyPrint configured for PDF/A‑2b compliance; embed watermark text (`clinician_id`) and ISO‑8601 timestamp; encrypt final PDF with AES‑256 before storage. | FR‑004 |
| 6 | Key Management Automation | Docker‑cron job calls HashiCorp Vault transit engine to rotate keys every 90 days; vault token stored as Docker secret; keys never written to disk. | NFR‑002 |
| 7 | Air‑Gap Controls | Set `network_mode: "none"` for containers that do not require external connectivity; document required offline package mirrors. | FR‑005 |
| 8 | Failure Logging | Every denied request (TLS downgrade, permission error, vault outage) creates an audit log entry with severity WARN and includes request context. | KPI‑001 |
| 9 | Compliance Documentation | Produce mapping table linking each checklist item to HIPAA §164.312(a)(2)(iv) or NIST SP 800‑53 AC-002 / AU‑6 controls. | KPI‑002 |

---

## 5. Acceptance Criteria Table (Expanded)
| AC ID | Linked US | Scenario Description | Expected Outcome |
|-------|-----------|---------------------|------------------|
| AC‑001 | US‑001 | Patient submits form over HTTPS | Server receives encrypted payload, persists ciphertext with AES‑256, creates audit log entry |
| AC‑002 | US‑002 | Front Desk staff attempts PDF export without permission | System returns HTTP 403, logs denial event, raises alert on repeated attempts |
| AC‑003 | US‑003 | Clinician requests PDF export with valid credentials | PDF generated with dynamic watermark & timestamp, download link expires after 5 min; on Vault failure returns generic error without data leakage |

---

## 6. Traceability Matrix
| Artifact | Requirement IDs |
|----------|----------------|
| Personas | FR‑001, FR‑004 |
| User Stories & ACs | FR‑001, FR‑002, FR‑004, KPI‑001, KPI‑002 |
| Checklist Items | FR‑001–FR‑005, NFR‑002, KPI‑001–KPI‑002 |

---

*All content adheres to SaaS best practices: horizontal scalability via Docker Compose microservices, multi‑tenant isolation through role based access controls, monitoring via Prometheus/Grafana (not detailed here), and compliance with SOC 2 / GDPR where applicable.*

# User Stories

## US-001 (Front‑desk staff)
**Title:** Capture patient demographics via encrypted web form  
**Persona:** Front‑desk staff  
**Goal:** Collect accurate patient information while ensuring PHI protection in transit and at rest.

**Acceptance Criteria:**

| ID | Description |
|----|-------------|
| AC-001 | **Given** the front‑desk user is authenticated with role "front‑desk" and a TLS 1.3 connection is established, **When** the user submits the intake form with all required fields correctly filled, **Then** the system stores the record encrypted with AES‑256‑GCM at rest, returns a success message, and creates an immutable audit log entry (operation=CREATE, actor=front‑desk, timestamp). |
| AC-002 | **Given** the front‑desk user attempts to upload an attachment of disallowed type (e.g., .exe), **When** the user clicks "Submit", **Then** the system rejects the upload, logs a security event (operation=REJECTED_UPLOAD), and displays "File type not allowed". If file size >5 MB → reject with "File too large". |

## KPIs

| KPI ID | Target |
|--------|--------|
| KPI-001 | System availability ≥ 99.9 % during business hours. |
| KPI-002 | Zero security incidents in first 90 days. |
| KPI-003 | Audit log completeness ≥ 100 % for all operations. |

# Security Hardening Checklist (SAAS Context)

1. Verify that all external traffic terminates at an Nginx reverse proxy configured for TLS 1.3 only; disable TLS 1.0/1.1.
2. Ensure every column storing PHI is encrypted at rest using column‑level AES‑256 encryption managed by PostgreSQL pgcrypto.
3. Enable PostgreSQL row‑level security policies that enforce least‑privilege access per role.
4. Deploy HashiCorp Vault in sealed mode; store master encryption key; rotate every 90 days automatically via cron job inside Docker container.
5. Configure audit log collection using pgaudit extension; pipe logs to an immutable file system mounted with `chattr +i`.
6. Run Trivy vulnerability scan on all Docker images before each release; remediate any CVE ≥ 7 severity.
7. Harden Docker host OS: disable root login over SSH, enforce firewall rules allowing only internal network traffic on ports 443/80.
8. Validate PDF generation produces PDF/A‑2b compliant files; test that watermark text appears on every page.
9. Perform penetration test focusing on injection vectors in web form fields; ensure input sanitization prevents XSS/SQLi.
10. Document air‑gap deployment steps: offline image pull via `docker save`, transfer via encrypted USB stick, load images locally using `docker load`, start stack with `docker compose up -d`.

All items above are traceable to FR‑001 through FR‑005 and KPI‑001–KPI‑003.
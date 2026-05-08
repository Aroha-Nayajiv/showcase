# Intake Form Feature Specification (Overview)

## Stakeholder Roles and Goals for Intake Form Feature

The following section identifies the concrete stakeholder roles that interact with the **PatientIntake** web‑based intake form, articulates their primary goals, and enumerates the pain points that must be addressed to achieve HIPAA compliance, SaaS‑grade usability, and multi‑tenant security.

### 1. Patient (Primary End‑User)
**Goals**
- **Secure data submission** – Provide personal health information (PHI) with confidence that it is encrypted in transit (TLS 1.3) and at rest (field‑level AES‑256).
- **Efficiency** – Complete the intake form in ≤ 5 minutes on a typical broadband connection.
- **Clarity** – Understand each required field without medical jargon; receive inline validation feedback.
- **Privacy assurance** – Know that only authorized staff can view the submitted data and that an immutable audit log records every access.

**Pain Points**
- Complex medical terminology can cause incorrect entries.
- Anxiety about data misuse if encryption status or consent handling is unclear.
- Device variability – responsive design required for mobile browsers (WCAG 2.1 AA).
- Network interruptions – need auto‑save drafts.

### 2. Front‑Desk Clerk (Data Capture Operator)
**Goals**
- Rapid verification of mandatory fields before patient proceeds.
- Real‑time validation of entries (e.g., insurance numbers).
- Audit readiness – each submission logged with timestamp and clerk identifier.

**Pain Points**
- Manual re‑entry after failed validation.
- Lack of visibility into encryption status.
- Inconsistent UI cues across browsers.

### 3. Clinician (Care Provider)
**Goals**
- Immediate access to accurate PHI after check‑in.
- Data integrity – rely on cryptographic hashes stored in the audit log.
- Contextual relevance – view only clinically relevant fields.

**Pain Points**
- Overexposure of data if RBAC mis‑configured.
- Latency due to inefficient query patterns on the audit log.
- Unclear audit trail during compliance audits.

### 4. Admin (System Administrator / Compliance Officer)
**Goals**
- Policy enforcement – configure RBAC and ensure encryption keys rotate per **NFR‑002**.
- Auditability – generate reports satisfying **FR‑004** and **KPI‑003**.
- Operational resilience – deploy via Docker Compose in an air‑gap environment (**FR‑006**).

**Pain Points**
- Key management complexity.
- Log storage growth affecting performance.
- Compliance verification overhead.

---

## Intake Form Feature Specification (Overview)

Purpose: Define the functional behavior of the web‑based intake form for the **PatientIntake** system while satisfying HIPAA, SOC 2, and SaaS domain constraints (multi‑tenancy, horizontal scalability, high availability).

---

### 5. Personas
| Persona | ID | Description |
|---|---|---|
| Patient | PER‑01 | Individual providing personal health information via the web form. |
| Front Desk Clerk | PER‑02 | Staff member who validates intake data, assists patients, and initiates PDF generation. |
| Clinician | PER‑03 | Authorized medical professional who reviews the PDF summary for clinical decision‑making. |
| System Administrator | PER‑04 | Configures encryption keys, role mappings, and audit‑log retention. |

---

### 6. Ranked User Stories (MVP)
| ID | Persona | Statement | Value | Rank |
|---|---|---|---|---|
| US‑001 | Patient | Securely submit demographics, insurance information, and medical history. | Data protected in transit & at rest; usable for care. | 1 |
| US‑002 | Front Desk Clerk | Validate and correct a submitted intake form before final storage. | Errors fixed early; record complete for clinicians. | 2 |
| US‑003 | Clinician | View a PDF intake summary that includes a watermark and export timestamp. | Trust document authenticity & generation time. | 3 |
| US‑004 | System Administrator | Configure field‑level encryption keys and TLS settings for the web app. | System complies with HIPAA §164.312(a)(2)(iv) technical safeguards. | 4 |
| US‑005 | Front Desk Clerk | Export the PDF summary for authorized staff only. | Sensitive PHI never exposed to unauthorized users. | 5 |
| US‑011 *(new)* | System Administrator | Enable multi‑tenant data isolation for SaaS deployment. | Each tenant’s data stored separately; prevents cross‑tenant leakage. | 6 |

---

### 7. Acceptance Criteria
#### AC‑001 – US‑001 (Empty Form Submission)
**Given** the patient is on a TLS‑protected browser session and all required fields are empty.
**When** the patient attempts to submit the form.
**Then** the system blocks submission, displays field‑specific validation messages, and no data is persisted.
*Negative scenarios*: missing required field, oversized input (>255 chars), client‑side script disabled.

#### AC‑002 – US‑001 (Successful Submission)
**Given** all required fields contain valid data and TLS session is active.
**When** the patient clicks **Submit**.
**Then** the server encrypts each field at rest using AES‑256‑GCM with per‑field keys, stores the record in PostgreSQL, creates an audit log entry (`CREATE`), and shows a success toast.
*Error path*: Encryption service unavailable → transaction rolled back; user sees “temporary service issue”.

#### AC‑003 – US‑002 (Edit by Front Desk Clerk)
**Given** a clerk authenticated with role `front_desk` and a pending intake record exists.
**When** the clerk selects **Edit**, modifies the insurance number, and saves.
**Then** the system re‑encrypts modified fields, updates the record version, logs an `UPDATE` audit entry with user ID, and confirms success.
*Edge case*: Edit attempted after 30‑minute lock expires → “record locked for editing”.

#### AC‑004 – US‑003 (PDF Generation)
**Given** a clinician with role `clinician` requests the PDF for patient `PID‑12345`.
**When** the clinician clicks **Generate PDF**.
**Then** the service retrieves encrypted data, decrypts in memory, creates a PDF/A‑2b document with a semi‑transparent watermark “Confidential – Patient Intake”, embeds an immutable UTC timestamp, signs the PDF with the system’s X.509 certificate, streams it to the browser, and logs a `READ` audit entry.
*Failure*: Decryption key missing → generic “unable to generate document” message; no PHI exposed.

#### AC‑005 – US‑004 (Encryption Settings Update)
**Given** the administrator accesses the Encryption Settings page via a secure admin console.
**When** the admin uploads a new RSA key pair and toggles TLS version to 1.3.
**Then** the system validates key format, updates configuration files atomically, restarts affected services without downtime, logs a `CONFIGURATION_CHANGE` audit entry, and displays a confirmation banner.
*Invalid key*: system rejects upload with precise error; no configuration change applied.

#### AC‑006 – US‑005 (PDF Export by Front Desk Clerk)
**Given** an authorized front desk clerk initiates an export of a patient’s PDF summary.
**When** the clerk selects **Export**, chooses a destination folder on the internal file share.
**Then** the system streams the signed PDF over an internal SMB connection protected by TLS‑wrapped SMB3, records an `EXPORT` audit entry with destination path, and confirms completion.
*Error*: Destination path not writable → export aborts; error shown; no audit entry created for failed export.

#### AC‑007 – SaaS Multi‑Tenant Isolation (US‑011)
**Given** multiple tenant identifiers (`tenant_id`) are present in incoming requests.
**When** a new intake record is created or accessed.
**Then** data is stored in tenant‐scoped schemas (`tenant_<id>`) or partitioned tables with row‐level security ensuring queries are automatically filtered by `tenant_id`. Access attempts across tenants are denied with HTTP 403 responses and logged as security events.
*Scalability*: Horizontal scaling via stateless API servers behind a load balancer; database sharding based on `tenant_id` supports up to 10 k concurrent users per shard (**NFR‑007**, **KPI‑001**) .

#### AC‑008 – Rate Limiting & Monitoring (Cross‑Cutting)
All public endpoints enforce per‑tenant rate limits (e.g., 200 requests/minute). Excess requests receive HTTP 429 responses logged to the monitoring pipeline (Prometheus + Grafana). Metrics include request latency, error rates, and encryption service health; alerts trigger on SLA breaches (>200 ms avg latency).

---

### 8. Design Needs (to be defined by Design)
1. **Field‑level encryption library** – open source choice (e.g., libsodium wrapper) and key rotation strategy aligned with **NFR‑002**, **FR‑011**, **NFR‑007**.
2. **UI flow diagrams** for each persona covering error states listed in acceptance criteria and SaaS rate limiting feedback screens.
3. **Audit‐log schema** – columns (`event_type`, `actor_id`, `timestamp_utc`, `object_id`, `change_hash`) with retention policy of 7 years (**NFR‑003**) and immutable signing (**FR‑004**, **KPI‑003**).
4. **PDF generation pipeline** – library selection (WeasyPrint or PDFKit), watermark implementation details, digital signature format (PKCS#7).
5. **TLS configuration profile** – cipher suites aligned with OpenSSL best practices for HIPAA and SOC 2; enforce TLS 1.3 minimum (**FR‑002**, **FR‑003**, **FR‑006**) .
6. **Role‐based access control matrix** – mapping of PER‑01…PER‑04 to CRUD permissions on intake records and PDFs; includes multi‐tenant isolation rules (**FR‑011**, **NFR‑007**) .
7. **API Specification Document** – RESTful endpoints (`POST /api/v1/tenants/{tenant_id}/intake`, `PUT /api/v1/tenants/{tenant_id}/intake/{record_id}`, `GET /api/v1/tenants/{tenant_id}/intake/{record_id}/pdf`, `PATCH /api/v1/tenants/{tenant_id}/config/encryption`). Each endpoint includes request/response schemas, authentication (OAuth2 + JWT), error codes (`400`, `401`, `403`, `404`, `429`, `500`).

---

### 9. Security & Compliance Highlights
- **In‐Transit Protection:** All HTTP traffic uses TLS 1.3 minimum; HSTS header set to max‐age 31536000 seconds.
- **At‐Rest Protection:** Field‐level AES‑256‑GCM encryption with per‐field keys derived from a master key stored in an HSM or Docker secret; keys rotate quarterly (**NFR‐002**, **FR‐011**) .
- **Audit Logging:** Immutable append‑only log written to PostgreSQL audit_log table; entries signed with RSA‑2048 private key to prevent tampering (**FR‑004**, **KPI‑003**).
- **PDF Hardening:** PDFs generated as PDF/A‑2b compliant files; watermark includes "Confidential – Patient Intake" plus UTC timestamp; digital signature validates integrity (**AC‑004**).
- **Key Management:** RSA key pairs rotated quarterly; automated rotation scripts referenced in US‑004 acceptance criteria (**NFR‑002**).
- **Multi‑Tenant Isolation:** Tenant‑scoped schemas and row‑level security enforce strict data segregation (**FR‑011**).
- **Scalability:** Stateless services behind load balancer; database sharding based on tenant ID supports horizontal scaling (**NFR‑007**).
- **Monitoring & Alerting:** Prometheus metrics exported; Grafana dashboards track SLA compliance; alerts on high error rates or latency breaches (**AC‑008**).
- **Rate Limiting:** Per‑tenant request caps protect against abuse (**AC‑008**).
- **Disaster Recovery:** Daily encrypted backups stored offsite; automated restore tests quarterly (**KPI‑001**).
- **Availability:** Target 99.9% uptime via redundant containers and health checks (**KPI‑001**).
- **Audit Retention:** 7 years per regulatory requirement (**NFR‑003**).

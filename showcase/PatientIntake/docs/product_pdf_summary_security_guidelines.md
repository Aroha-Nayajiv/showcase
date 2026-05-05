# PDF Export Security Guidelines

## Personas

### Front Desk Clerk (ST-01 – Clinical staff)
Role Summary: The Front Desk Clerk registers patients, captures demographic and insurance information via the structured web form, and initiates the generation of the PDF intake summary for downstream review.

HIPAA‑related Concerns:
- Must never view unencrypted PHI on the client device; all form fields are encrypted in transit (TLS 1.3) and at rest (AES‑256 per‑field).
- Must ensure that any exported PDF is only accessible after successful role verification; the clerk's role permits view of the PDF but not download unless explicitly authorized by a supervising Clinician.

Workflow Interactions:
1. Log in using unique credentials (unique user identification per 45 CFR 164.312(a)(2)(i)).
2. Complete patient intake form; each field is encrypted before being persisted to PostgreSQL.
3. Request "Generate PDF" – the system checks RBAC; if the clerk lacks `export_pdf` permission, the UI displays a read‑only preview without download capability.
4. If authorized, the PDF is generated with a watermark containing the patient identifier (hashed) and an access timestamp.
5. An audit log entry (AU‑6) records who, when, and what action was performed.

Success Metrics: ≤ 200 ms response time for PDF preview (KPI‑01), zero unauthorized download attempts logged.

### Clinician (ST-01 – Clinical staff)
Role Summary: Clinicians review patient histories, sign off on care plans, and are authorized to export the PDF intake summary for clinical documentation or external referral.

HIPAA‑related Concerns:
- Must have end‑to‑end encryption for PDF content; the watermark must embed a cryptographic hash of the patient ID that cannot be altered without detection.
- Must ensure that each export creates an immutable audit log entry (AU‑6) with a tamper‑evident timestamp.

Workflow Interactions:
1. Authenticate via multi‑factor login.
2. Access patient record list; select a patient and click "Export PDF".
3. System validates clinician role and `export_pdf` permission.
4. PDF is generated using an open‑source tool inside a hardened Docker container; the resulting file includes:
   - Watermark: `Patient‑ID: <hashed>`
   - Timestamp: ISO‑8601 UTC time of export.
5. The PDF is streamed to the clinician's browser; no file is written to disk on the server beyond the transient generation buffer.
6. Audit log records: `action=pdf_export`, `user=clinician_id`, `patient=patient_id`, `timestamp=...`.

Success Metrics: ≥ 99.9 % audit‑log integrity (NFR‑003), ≤ 1 % error rate on watermark integrity checks.

### Patient (ST-02 – Patient)
Role Summary: The patient provides personal and medical information through the intake form but never directly interacts with PDF export functionality.

Assurances:
- Data will only be exported to authorized clinical staff; no direct download capability is exposed to the patient.
- Exported documents containing PHI are watermarked and timestamped to deter misuse.

Workflow:
- Completes the intake form; encryption occurs client‑side before transmission.
- Receives a confirmation email stating that their data will be reviewed by clinical staff; no PDF is delivered to them.

Success Metrics: Zero patient‑initiated PDF download attempts recorded in audit logs.

## Cross-Persona Security Controls
1. **Role-Based Access Control (RBAC)** – Enforced at both application layer and PostgreSQL row‑level security to ensure only admin, clinician, or front_desk roles can invoke PDF generation. Permissions used are `view_pdf` and `export_pdf`.
2. **Audit Logging** – Every read/write and export operation creates an immutable log entry AU‑6 retained for at least seven years per HIPAA retention requirements.
3. **Watermark & Timestamp** – Implemented using open‑source PDF libraries; watermark contains a SHA‑256 hash of the patient identifier, timestamp uses UTC ISO‑8601 format, both visible on every page of the exported document.
4. **Encryption in Transit & At Rest** – TLS 1.3 for all network traffic; AES‑256 per‑field encryption for stored PHI; Docker container runs with read‑only filesystem for PDF generation tools.
5. **Failure Handling** – If RBAC check fails, system returns HTTP 403 with a generic error message; no PDF is generated and an audit entry records the denied attempt.

## User Stories

## Metrics & Success Indicators
- **KPI‑01**: Export operation latency ≤ 200 ms under normal load.
- **KPI‑03**: 100 % of exported PDFs contain correct watermark and timestamp.
- **KPI‑05**: Audit log completeness ≥ 99.9 % of export events recorded (aligned with NFR‑003).

## Priority Ranking
| Story | Priority | Rationale |
|-------|----------|-----------|
| US-001 | 1 | Directly enables clinicians to share compliant records – core clinical workflow. |
| US-002 | 2 | Supports front‑desk verification while limiting data exposure risk. |
| US-003 | 1 | Mandatory for regulatory auditability – non‑compliance incurs penalties. |

## Traceability
- **FR‑003** – Medical history storage (supports PDF generation).
- **NFR‑003** – Mandatory audit logging of every read/write operation.
- **KPI‑01**, **KPI‑03**, **KPI‑05** – Success metrics referenced above.
- **RISK‑01** – Unauthorized data exposure mitigated by RBAC and audit logging.

# User Stories and Acceptance Criteria

## US-001: Clerk Export PDF
**Persona:** Front Desk Clerk  
**Goal:** Export a completed patient intake summary as a PDF.

**Given** the clerk is authenticated, possesses the `export_pdf` permission, and the patient record is in *completed* state,
**When** the clerk selects the **Export PDF** action,
**Then** a PDF is generated, stored encrypted at rest (AES‑256 GCM), includes a watermark `Exported by Front Desk – {timestamp}`, and the download starts. An audit log entry (`AUD-001`) is created with actor ID, role, patient ID (masked), action `export_pdf`, outcome `success`, and timestamp.

* **AC-001** – Successful export as described above.
* **AC-002** – If the record is not in *completed* state, the system shows error “Cannot export incomplete record”. No PDF or audit entry is created.
* **AC-003** – If the clerk’s session token is expired, the system redirects to login page; no PDF or audit entry is created.

## US-003: Admin Audit Reporting
**Persona:** System Administrator  
**Goal:** Review export activity.

**Given** the admin is authenticated with `audit_view` permission,
**When** the admin requests an export audit report for the last 30 days,
**Then** the system returns a list of audit entries (`AUD-001`) including masked patient ID (last 4 digits), actor role, timestamp, and outcome. Data is transmitted over TLS 1.3 with forward secrecy.

* **AC-005** – Successful report retrieval as described.
* **AC-006** – If audit log storage exceeds 95 % of allocated quota, the response includes a warning “Log storage nearing capacity” and suggests archiving.
* **AC-007** – If tampering is detected (hash mismatch), the system flags the entry as “integrity violation”, alerts the admin, and prevents further processing of that entry.

# Design Specifications

## Watermark Specification
- **Pattern:** `{Role} – {timestamp}` (e.g., `Exported by Front Desk – 2026‑05‑05T14:23:12Z`)
- **Placement:** Bottom‑right corner of each page.
- **Font:** Helvetica, 8 pt, opacity 30 %.

## Timestamp Service
- **Format:** ISO‑8601 UTC (`YYYY‑MM‑DDThh:mm:ssZ`).
\- **Source:** NTP‑synced server (`pool.ntp.org`).

## Encryption at Rest
- **Algorithm:** AES‑256 GCM.
\- **Key Management:** Keys stored in a Hardware Security Module (HSM) or secret vault (e.g., HashiCorp Vault) with rotation every 90 days.

## Audit Log Schema (`AUD‑001`)
| Field               | Type   | Description |
|---------------------|--------|--------------|
| actor_id            | UUID   | Unique identifier of the user performing the action |
| actor_role          | String | Role of the actor (Clerk, Clinician, Admin) |
| patient_id          | String | Patient identifier masked except last 4 digits |
| action              | String | e.g., `export_pdf`, `view_audit_report` |
| outcome             | String | `success`, `denied`, `error` |
| timestamp           | ISO‑8601 UTC | Time of action |
| digital_signature   | String | HMAC‑SHA256 of log entry for integrity |

## Rate Limiting
Maximum **5 export requests per minute per user**. Exceeding limit returns HTTP 429 with message “Rate limit exceeded”.

## Logging Levels
- **INFO:** Successful export actions.
- **WARN:** Permission denials, rate‑limit hits.
\- **ERROR:** System failures (e.g., template rendering error).

# Non‑Functional Requirements (NFR)

| ID      | Description |
|---------|-------------|
| NFR‑001 | Response time < 200 ms for export request under normal load |
| NFR‑002 | System availability ≥ 99.9 % (monthly) |
| NFR‑003 | Mandatory audit logging of every read/write operation (HIPAA §164.312(a)(2)(iv)) |
| NFR‑004 | Encryption at rest using AES‑256 GCM (HIPAA §164.312(a)(2)(i)) |
| NFR‑005 | Rate limiting to mitigate abuse (max 5/min per user) |
| NFR‑006 | TLS 1.3 for all data in transit (forward secrecy) |

# Edge Cases & Failure Handling
1. **Expired Session** – Redirect to login page; log entry with outcome `session_expired`.
2. **Corrupted Template** – Return generic error page; log `template_error`; no PDF generated.
3. **Key Rotation In‑Progress** – Abort export; return error “Key rotation in progress”; log `key_rotation`.
4. **Audit Log Saturation** – When storage reaches 95 % capacity, include warning in report and trigger archival routine (out of scope).

# Traceability Matrix

| Requirement ID | Source Artifact |
|-----------------|------------------|
| FR‑001         | US‑001 (Clerk export) |
| FR‑002         | US‑002 (Clinician export) |
| FR‑003         | US‑003 (Admin audit) |
| FR‑004         | Watermark Service |
| FR‑005         | PDF Generation Engine |
| FR‑006         | Encryption Store |
| FR‑007         | Audit Logger |
| NFR‑001        | Performance KPI‑01 |
| NFR‑002        | Availability KPI‑02 |
| NFR‑003        | Audit Logging requirement |
| NFR‑004        | Encryption requirement |
| NFR‑005        | Rate limiting policy |
| NFR‑006        | TLS version policy |

# References
- HIPAA §164.312(a)(2)(iv) – Encryption at rest
- HIPAA §164.312(a)(2)(i) – Encryption key management
- NIST SP 800‑53 AC‑2 – Account Management
- NIST SP 800‑53 AU‑6 – Audit Review, Analysis, and Reporting
# Role‑Based Access Control Matrix

## Role‑Based Access Control Matrix – Primary Personas

The following section defines the four core personas that interact with the **PatientIntake** SaaS system. Each persona is described in terms of responsibilities, data‑access needs, and compliance constraints derived from HIPAA technical safeguard requirements (45 CFR §164.312) and SaaS best‑practice security controls (SOC 2, ISO 27001). This information will be used by downstream Design activities to draft precise access‑control contracts, API scopes, and audit‑log schema extensions.

### 1. PER‑01 Patient
**Role:** The individual whose protected health information (PHI) is being collected.
**Primary Goals:** Submit personal demographics, insurance details, and medical history; view the PDF intake summary that they have authorized for export.

**Access Rights:**
- **Read:** Own intake record (self‑service view only).<br>- **Write:** Create a new intake record; update only fields marked editable by patient (e.g., contact phone).
- **Export:** Not permitted to export PDF directly; can request export via front‑desk staff.

**Security Controls:** All communications must use TLS 1.3 (FR‑002); data at rest encrypted with AES‑256 (FR‑003). Session is authenticated via OpenID Connect with a short‑lived access token scoped to `patient:self`.

**Audit Logging:** Every read/write operation logged with user ID, timestamp, and outcome (success/failure) as required by HIPAA §164.312(a)(2)(iv) (AC-006).

---

### 2. PER‑02 Front‑Desk Staff
**Role:** Administrative personnel who register patients and assist with form completion.
**Primary Goals:** Initiate intake sessions, capture missing insurance information, and trigger PDF generation for authorized staff.

**Access Rights:**
- **Read:** All patient intake records (full view).
- **Write:** Create new records; edit non‑clinical fields (demographics, insurance). Cannot modify clinical history fields.
- **Export:** Can generate and download PDF summaries for patients they have registered; export includes watermark and timestamp (FR‑004).

**Security Controls:** Session authentication via OpenID Connect; role‑based token scopes limited to `intake:read`, `intake:write`, `pdf:export`.

**Audit Logging:** Export actions recorded with staff ID and justification note (e.g., "patient request").

---

### 3. PER‑03 Clinician
**Role:** Licensed healthcare provider who reviews patient histories and updates clinical information.
**Primary Goals:** View complete intake data, add clinical observations, and request PDF summaries for care coordination.

**Access Rights:**
- **Read:** All fields of every patient record.
- **Write:** Update clinical sections (medical history, allergies, medications). Cannot alter demographic or insurance fields.
- **Export:** Authorized to generate PDF summaries for patients under their care; export includes immutable watermark identifying clinician ID.

**Security Controls:** Enforced least‑privilege via PostgreSQL row‑level security policies; TLS 1.3 for all API calls.

**Audit Logging:** Every edit to clinical data logged with before/after values for traceability.

---

### 4. PER‑04 Administrator
**Role:** System owner responsible for configuration, user provisioning, and audit review.
**Primary Goals:** Manage role assignments, rotate encryption keys, and review audit logs for compliance reporting.

**Access Rights:**
- **Read:** Full read access to all system tables and audit logs.
- **Write:** Create/modify/delete user accounts; adjust RBAC policies; initiate key rotation scripts.
- **Export:** Can export any PDF summary without watermark restrictions for compliance audits.

**Security Controls:** Multi‑factor authentication mandatory; secret management via HashiCorp Vault (open source).

**Audit Logging:** Administrative actions flagged with elevated severity level in the audit log.

---

### Consolidated RBAC Permissions Matrix
| Persona | Read Access | Write Access | Export Capability | Audit Logging |
|---------|-------------|--------------|-------------------|---------------|
| Patient | Own record only (`patient:self`) | Create own record; edit limited fields (`patient:update`) | ❌ (request only) | Record view logged with patient ID |
| Front‑Desk Staff | All records (`intake:read`) | Demographic & insurance fields (`intake:write`) | ✅ PDF with watermark & timestamp (`pdf:export`) | Export action includes staff ID & purpose |
| Clinician | All records (`clinical:read`) | Clinical fields only (`clinical:write`) | ✅ PDF with clinician ID watermark (`pdf:export`) | Edit actions capture before/after values |
| Administrator | Full system & audit logs (`admin:read`) | User & policy management (`admin:write`) | ✅ Unrestricted PDF export (`admin:export`) | Full audit trail with admin severity flag |

These personas and their permissions satisfy the HIPAA requirement that *"only authorized individuals may access PHI"* while providing the operational flexibility needed for the PatientIntake workflow.

---

## User Stories & Acceptance Criteria
| ID | Role | Narrative |
|----|------|----------|
| US-001 | Patient | As a **Patient**, I want to enter my personal demographics, insurance details, and medical history into a secure web form so that my health information is captured accurately while remaining confidential under HIPAA. |
| US-002 | Front‑Desk Staff | As **Front‑Desk Staff**, I want to create a new intake record for a patient and view completed forms for appointment scheduling so that I can efficiently schedule visits without exposing sensitive fields unnecessarily. |
| US-003 | Clinician | As a **Clinician**, I want to view and update a patient's medical history after verifying their identity so that I can provide appropriate care while audit logs record every access for compliance. |
| US-004 | Administrator | As an **Administrator**, I want to export a PDF summary of any patient's intake form with watermark and timestamp so that authorized staff can produce legally‑compliant documents while the export action is fully logged. |

## Design Needs for Downstream Phases
1. **Client‑Side Encryption Library** – Use Web Crypto API (`crypto.subtle`) for encrypting PHI before transmission; keys derived from per‑session JWKs stored in secure HTTP‑only cookies.
2. **PostgreSQL Column‑Level Encryption Strategy** – Adopt `pgcrypto` functions for field‑level encryption of PHI columns; store encryption keys in HashiCorp Vault referenced by IAM roles.
3. **Audit Log Schema** – Immutable append‑only table `audit_log` with columns: `operation`, `actor_id`, `record_id`, `field_hash_before`, `field_hash_after`, `timestamp`, `severity`.
4. **RBAC Mapping Table** – JSON document mapping each role to CRUD permissions per data domain (demographics, insurance, clinical) used by API gateway policy engine.
5. **Export Workflow Requirements** – PDF generation via `wkhtmltopdf`; watermark template includes `{actor_id}` and `{timestamp}`; transport over TLS 1.3 enforced by load balancer.

---

## Personas & Roles
- **Admin (ROLE_ADMIN)**: Full read/write privileges, audit‐log access.
- **Clinician (ROLE_CLINICIAN)**: Can view patient medical history and export PDF summaries for treatment decisions.
- **Front‑Desk Staff (ROLE_FRONT_DESK)**: Can create new intake records and update demographic fields; cannot view full medical history or export PDFs.

### US-003 – Front‑Desk Intake Creation & PDF Export
**Given** front‑desk staff are authenticated with role `front‑desk` (AC‑005) and have selected a completed intake record for export (AC‑006).
**When** they submit a new intake form or click “Export PDF”.
**Then** the system:
1. Encrypts each field on the client side via TLS 1.3 transport, stores encrypted at rest, generates a record ID and writes an audit entry “create” (AC‑005).
2. Returns “Secure connection required” if TLS handshake fails; returns field‑level validation errors for missing mandatory fields.
3. Generates a PDF/A‑2b document embedding a visible watermark “Confidential – Authorized Staff Only”, adds an export timestamp in the footer, encrypts the PDF with AES‑256 using a staff‑specific key, and logs the export event (AC‑006).
4. Denies export with “Key rotation required” if staff key expired; logs timeout error and returns “Export timed out, please retry” if generation exceeds 5 seconds.

## Compliance & Security References
- **HIPAA Security Rule §164.312(a)(2)(iv)** – Encryption of PHI in transit (TLS 1.3).
- **HIPAA Security Rule §164.312(e)(1)** – Audit controls (immutable append‐only log).
- **NIST SP 800‑53 Rev 5 AC-002** – Account Management (MFA for admin).
- **NIST SP 800‑53 Rev 5 AU‑6** – Audit Review (audit log tamper‐proofing).

## RBAC Policy Specification
A machine‐readable OPA Rego policy (`policy.rego`) defines allowed actions per role:
rego
package authz

default allow = false

allow {
    input.role == "admin"
    input.action in {"view_audit_log","delete_record","create_intake","export_pdf"}
}

allow {
    input.role == "clinician"
    input.action in {"view_medical_history","edit_medication"}
    input.patient_id == input.assigned_patient_id
}

allow {
    input.role == "front_desk"
    input.action in {"create_intake","export_pdf"}   # export limited to own staff key
}

## Audit Log Schema
| Field      | Type   | Description |
|------------|--------|-------------|
| event_id   | UUID   | Unique identifier for the audit event |
| timestamp  | ISO8601| Time of the event (UTC) |
| actor_id   | UUID   | User identifier performing the action |
| role       | string | Role of the actor (`admin`, `clinician`, `front_desk`) |
| resource   | string | Target resource (`audit_log`, `patient_record`, `intake_form`, `pdf_export`) |
| action     | string | Action performed (`view`,`delete`,`create`,`export`) |
| outcome    | string | `success` or error code |
| details    | json   | Optional JSON blob with before/after values The log is stored in an append‐only table with Write‐Ahead Logging (WAL) to guarantee immutability; any modification attempt triggers an alert (`security_event`). |

## Encryption Requirements
- **At Rest:** All PHI fields encrypted with AES‑256‐GCM using per‐staff keys; key rotation schedule defined in **NFR-002** (automated via cert manager).
- **In Transit:** All network communication enforced TLS 1.3 minimum per HIPAA §164.312(a)(2)(iv).
- **Key Rotation Handling:** Updates queued during rotation; export operations return “Temporary unavailable due to key rotation”.

## PDF Export Controls
- Watermark text format: `"Confidential – Authorized Staff Only"` placed at top of each page.
- Timestamp embedded in PDF metadata field `ExportTimestamp`.
- PDF encrypted with AES‑256 using staff‐specific key; expiration of key results in denial message per AC‑006.

## Error Handling Conventions
| Scenario| HTTP Status | Message |
|-------------|------------|---------|
| Expired session token                | 401        | "Session expired – reauthenticate." |
| Insufficient role permission          | 403        |	"Access denied." |
| Validation failure (e.g., dosage)     |	400        |	Detailed validation error description |
| TLS handshake failure                |	400        |	"Secure connection required." |
| Key rotation required                |	423        |	"Key rotation required." |
| PDF generation timeout               |	504        |	"Export timed out, please retry." |

## Compliance Traceability Matrix
| Artifact                     | Requirement ID | HIPAA Clause               | NIST Control |
|-----------|-----------------|----------------------------|--------------|
| US-001 / AC-001, 002        | FR-004          | §164.312(e)(1)             | AU-6         |
| US-002 / AC-003, 004         | NFR-003         | §164.312(a)(1)             | AC-002         |
| US-003 / AC-005, 006         | FR-005          | —                          | —            |

### Overview
The RBAC feature controls which user roles (Admin, Clinician, Front-Desk) can view or modify resources within the Patient Intake application. It enforces the principle of least privilege, logs all permission changes, and complies with SOC 2 and GDPR requirements for auditability and data protection.

### Open Issues / Knowledge Gaps
- Exact retention period configuration for audit logs per GDPR Article 30 – requires clarification from compliance team.
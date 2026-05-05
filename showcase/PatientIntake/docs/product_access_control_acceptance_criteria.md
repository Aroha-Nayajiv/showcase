# Access Control Acceptance Criteria

## Personas

| Persona ID | Name | Description |
|------------|------|-------------|
| **PER-01** | Clinician | Medical staff who need to view and update patient intake records for treatment purposes. |
| **PER-02** | Front Desk Staff | Administrative personnel who capture new patient demographics and insurance information at registration. |
| **PER-03** | Administrator | System admin responsible for managing role assignments, audit‑log retention, and overall compliance reporting. |

**Stakeholder Definitions (ST)**

| Stakeholder ID | Role |
|----------------|------|
| **ST-01** | Clinician (maps to PER‑01) |
| **ST-02** | Front Desk Staff (maps to PER‑02) |
| **ST-03** | Administrator / Compliance Officer (maps to PER‑03) |

---

## User Stories

| US ID | Persona | Goal | Business Value / Compliance Reference | Priority |
|-------|---------|------|--------------------------------------|----------|
| **US-001** | Front Desk Staff (PER‑02) | Create a new patient intake record with encrypted fields | Patient data is protected at rest and in transit, satisfying HIPAA §164.312(a)(2)(iv) | 1 |
| **US-002** | Clinician (PER‑01) | Read a patient's intake record after successful authentication | Enables timely care while ensuring only authorized access per **FR‑001** and **NFR‑003** | 1 |
| **US-003** | Administrator (PER‑03) | Audit every read/write operation and generate immutable logs | Compliance officers can verify access trails for HIPAA audit requirements (**KPI-003**) | 2 |
| **US-004** | Clinician (PER‑01) | Export a PDF summary of a patient record with a watermark and timestamp | Exported document is traceable to the exporting staff and meets PDF security policy (**FR‑005**) | 2 |

---

### US‑001 – Create Intake Record

| AC ID | Description |
|-------|-------------|
| **AC‑001** | **Given** Front Desk Clerk is authenticated with valid credentials and has the `IntakeCreator` role; **When** they submit a new intake form; **Then** the system encrypts each field at rest using AES‑256‑GCM, stores the record, and creates an audit‑log entry (`operation=CREATE`) containing timestamp, user ID, and SHA‑256 hash of the payload. |
| **AC‑002** | **Given** Front Desk Clerk attempts to edit a form they did not create; **When** they click *Save*; **Then** the system checks the `IntakeEditor` permission. If permitted, it re‑encrypts modified fields, updates the record, and logs `operation=UPDATE`. If not permitted, the system returns `403 Forbidden`, shows “Access Denied”, and logs `operation=UNAUTHORIZED_UPDATE`. |

### US‑002 – Read & PDF Export

| AC ID | Description |
|-------|-------------|
| **AC‑003** | **Given** Clinician is authenticated with `Clinician` role and has `PDFExport` permission; **When** they request a patient’s intake summary PDF; **Then** the system generates the PDF via `wkhtmltopdf`, embeds a semi‑transparent watermark containing the clinician’s name/role, appends an ISO‑8601 access timestamp in the footer, encrypts the file in transit using TLS 1.3, stores it in an encrypted file store, and logs `operation=PDF_EXPORT` with actor ID and timestamp. |
| **AC‑004** | **Failure Scenario** If PDF generation fails (e.g., missing template), the system returns HTTP 502 with a user‑friendly error message “PDF generation failed – please try again later” and logs `operation=PDF_EXPORT_FAILURE` including error details. |
| **AC‑005** | **Given** Clinician lacks `PDFExport` permission; **When** they attempt the export; **Then** the system returns HTTP 403 “Forbidden” and logs `operation=UNAUTHORIZED_PDF_EXPORT`. |

### US‑003 – Audit & Role Management

| AC ID | Description |
|-------|-------------|
| **AC‑006** | **Given** Administrator is authenticated with `Admin` role; **When** they add a new role `Researcher` with read‑only permissions on audit logs; **Then** the system persists the role definition, updates RBAC tables, and creates an audit entry `operation=ROLE_CHANGE` documenting actor, target role, and timestamp. |
| **AC‑007** | **Failure Scenario** If the role name already exists, the system returns HTTP 409 “Duplicate Role” and logs `operation=ROLE_CHANGE_FAILURE`. |
| **AC‑008** | **Given** Administrator views the audit log for a specific date range; **When** they filter and export results as CSV; **Then** the system returns only entries the admin is authorized to see, includes immutable timestamps and SHA‑256 hash chain, and logs `operation=AUDIT_LOG_EXPORT`. |
| **AC‑009** | **Performance Scenario** If the query exceeds 2 seconds, the system returns a throttling notice “Query taking longer than expected – please refine filters” and logs `operation=AUDIT_LOG_EXPORT_SLOW`. |

---

## Design Needs for Downstream Teams

### Encryption Specification

* **Algorithm:** AES‑256‑GCM for field‑level encryption.
* **Key Management:** Keys are generated in HashiCorp Vault, rotated every 90 days automatically via Vault’s lease renewal. Each rotation creates a new version; old versions are retained for decryption of existing records until migration is complete.
* **Key Storage:** Keys never leave Vault; application retrieves transient keys via short‑lived tokens.
* **Compliance Mapping:** Satisfies HIPAA §164.312(e)(1) – encryption key management.

### Audit Log Schema

{
  "event_type": "[CREATE|READ|UPDATE|DELETE|UNAUTHORIZED_*|ROLE_CHANGE|PDF_EXPORT]",
  "actor_id": "string",
  "actor_role": "string",
  "timestamp": "ISO-8601 UTC",
  "target_id": "patient_record_id or role_id",
  "metadata": {
    "ip_address": "string",
    "hash_chain": "SHA-256 of previous entry",
    "details": "optional free text"
  }
}

*Each entry includes a SHA‑256 hash chain linking to the previous entry to ensure immutability (**NFR‑003**, **KPI-003**).*

### PDF Generation Parameters

* **Template Location:** `/app/templates/pdf/intake_summary.html`
* **Watermark Format:** `<div style="position:absolute; opacity:0.15; font-size:48px; transform:rotate(-45deg);">Confidential – {{user_name}} ({{role}})</div>`
* **Timestamp Format:** ISO‑8601 (`YYYY-MM-DDTHH:mm:ssZ`) placed in footer.
* **Storage Encryption:** PDFs stored in S3 bucket with server‑side encryption SSE‑KMS using same Vault‑managed keys.
* **Access Delivery:** HTTPS download link signed with short expiry (5 min).

### Role Matrix Definition (RBAC)

| Role / Permission Matrix | IntakeRecord – Create | IntakeRecord – Read | IntakeRecord – Update | IntakeRecord – Delete | AuditLog – Read | PDFExport – Execute |
|---------------------------|-----------------------|---------------------|----------------------|---------------------|------------------|----------------------|
| **Front Desk Staff (PER‑02)** | ✅ (`IntakeCreator`) | ✅ (`IntakeReader`) | ✅ (`IntakeEditor`) *if owner* | ❌ | ✅ (`AuditReader`) *limited to own actions* | ❌ |
| **Clinician (PER‑01)** | ❌ | ✅ (`ClinicianReader`) | ✅ (`ClinicianEditor`) *if permitted* | ❌ | ✅ (`AuditReader`) *full* | ✅ (`PDFExport`) |
| **Administrator (PER‑03)** | ✅ (`AdminCreator`) *all* | ✅ (`AdminReader`) *all* | ✅ (`AdminUpdater`) *all* | ✅ (`AdminDeleter`) *all* | ✅ (`AuditReader`) *full* | ✅ (`PDFExport`) *all* |

*Permissions reference functional requirements FR‑001 – FR‑005.*

---

## Acceptance Criteria Summary Table (Traceability)

| AC ID | Linked Requirement(s) |
|-------|----------------------|
| AC‑001 – AC‑002 | FR‑001, NFR‑001, NFR‑003, KPI-001 |
| AC‑003 – AC‑005 | FR‑005, NFR‑003, KPI-003 |
| AC‑006 – AC‑009 | FR‑004, FR‑005, NFR‑003, KPI-003 |

---

## Compliance & Risk Mapping

* **RISK-001:** Unauthorized data exposure – mitigated by encryption & RBAC.
* **RISK-002:** Open-source component vulnerabilities – addressed in separate security backlog.
* **RISK-003:** Deployment misconfiguration – covered by infrastructure hardening checklist.

---

*Document prepared for the PatientIntake project – MVP scope focusing on HIPAA‐compliant access control, encryption, auditability, and PDF export.*
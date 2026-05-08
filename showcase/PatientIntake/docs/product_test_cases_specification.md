# Test Cases Specification

## Personas for Patient Intake System (HIPAA-Compliant)

### PER-003 – Clinician (Reviewer & Care Provider)
**Name:** Dr. Samuel Lee (age 45)  
**Role:** Licensed clinician who reviews submitted intake forms to inform diagnosis and treatment planning.
**Goals:**
1. Retrieve complete patient intake data quickly.
2. Verify that the data has not been tampered with (integrity check).
3. Export a PDF summary for inclusion in the patient’s chart, with watermark and timestamp visible only to authorized staff.
**Pain Points:**
- Must ensure that only authorized clinicians can view PHI.
- Needs assurance that exported PDFs cannot be altered after generation.
- Requires audit trail of PDF export actions for compliance reporting.
**Security Expectations:**
- Access to patient records governed by RBAC – clinician role has read/write permissions but cannot modify audit logs (FR‑002).
- PDF generation must embed a watermark containing the clinician’s ID and export timestamp; PDF must be protected by AES‑256 encryption at rest (NFR‑003).
- Every export action creates an immutable audit entry (FR‑004).
**Success Metric:** Clinician can view the full intake record, generate a compliant PDF, and see a corresponding audit log entry without encountering permission errors.
**Design Needs:**
- UI component for “Export PDF” that is disabled for non‑clinician roles.
- Watermark template that includes user ID and timestamp.
- Audit‑log view accessible only to admin role; clinician sees only their own export entries.

## Traceability Matrix

| Artifact ID | Linked Requirement(s) |
|--------------|----------------------|
| PER-001      | FR-001, FR-003, FR-004 |
| PER-002      | FR-001, FR-002, FR-004 |
| PER-003      | FR-001, FR-002, FR-003, FR-004, FR-005 |

## Secure Patient Intake Feature Specification

### User Stories

**US-001 – Front Desk Staff reads patient intake form**
*Persona*: Front Desk Staff (clinic A)
*Goal*: View decrypted intake form of a patient belonging to their clinic.
*Given* the staff member is authenticated and assigned to Clinic A,
*When* they request the intake form for patient_id belonging to Clinic A,
*Then* the system displays the decrypted form,
*And* an audit log entry records operation=READ, actor=Front Desk Staff, patient_id, timestamp, outcome=success.

**US-002 – Unauthorized read attempt**
*Persona*: Front Desk Staff (clinic A)
*Goal*: Attempt to view a patient record from Clinic B.
*Given* the staff member is authenticated for Clinic A,
*When* they manually modify the URL to request a patient_id belonging to Clinic B,
*Then* the system returns HTTP 403 Forbidden with message "You do not have permission to view this record.",
*And* an audit log entry records operation=READ_DENIED, actor=Front Desk Staff, target_patient_id, timestamp.

**US-003 – Clinician exports PDF for authorized patient**
*Persona*: Clinician
*Goal*: Export a PDF/A‑2b of a patient’s intake form.
*Given* the clinician is authenticated and has access to patient_id in their clinic,
*When* they select "Export PDF",
*Then* the backend retrieves decrypted data, generates a PDF using WeasyPrint v>=53, embeds watermark "Confidential – Exported by Clinician" and UTC timestamp,
*And* streams the PDF over TLS 1.3 with filename `<patientID>_<timestamp>.pdf`,
*And* an audit log entry records operation=EXPORT_PDF, actor=Clinician, patient_id, timestamp, outcome=success.

**US-004 – Clinician export denied for unauthorized patient**
*Persona*: Clinician
*Goal*: Attempt export for patient outside their clinic.
*Given*: the clinician is authenticated but does not have access to the target patient,
*When*: they request export,
*Then*: the system returns HTTP 403 Forbidden, no PDF is generated,
*And*: an audit log entry records operation=EXPORT_DENIED with relevant details.

**US-005 – PDF integrity verification on external workstation**
*Persona*: Clinician
*Goal*: Ensure exported PDF has tamper‑evidence.
*Given*: the clinician copies the exported PDF to an external USB on a non‑air‑gapped workstation,
*When*: the file is opened in Adobe Reader,
*Then*: the embedded digital signature validates against internal CA and any tampering triggers "Document has been altered" warning, satisfying HIPAA integrity requirement.

### Acceptance Criteria Summary
| AC ID | User Story | Scenario Description |
|-------|------------|----------------------|
| AC-003 | US-001 | Decrypted intake form displayed; audit log READ success recorded |
| AC-004 | US-002 | Access denied with 403; audit log READ_DENIED recorded |
| AC-005 | US-003 | PDF generated with watermark & UTC timestamp; streamed over TLS 1.3; audit log EXPORT_PDF success |
| AC-006 | US-004 | Export denied with 403; no PDF; audit log EXPORT_DENIED |
| AC-007 | US-005 | Digital signature validation; tamper detection message displayed |

### Design Specifications (for downstream Design phase)

#### 1. Encryption Specification
- Field‑level encryption using **AES‑256‑GCM** for all PHI columns in `intake_form` table.
- Transport encryption enforced via **TLS 1.3** with approved cipher suites `TLS_AES_256_GCM_SHA384`, `TLS_CHACHA20_POLY1305_SHA256`.
- Key management performed by **HashiCorp Vault**; keys rotated every **90 days** automatically via Vault's `rotate` API.

#### 2. Access Control Model
- Role‑Based Access Control (RBAC) matrix:
  | Role               | Read                         | Export PDF |
  |--------------------|----------|------------|
  | Front Desk Staff   | Own‑clinic patients only     | ❌          |
  | Clinician          | Own‑clinic patients only     | ✅          |
  | Admin              | All clinics                  | ✅          |

- PostgreSQL Row‑Level Security (RLS) policies enforce `clinic_id = current_setting('app.current_clinic')`.

#### 3. Audit Logging Format

- **operation**: READ|READ_DENIED|EXPORT_PDF|EXPORT_DENIED
- **actor**: Front Desk Staff|Clinician|Admin
- **patient_id**: <uuid>
- **timestamp**: 2026‑05‑08T12:34:56Z
- **outcome**: success|failure

Stored in immutable append‑only table `audit_log` with retention policy of **7 years** (per NFR‑003).

#### 4. PDF Generation Requirements
- Use **WeasyPrint >= 53**.
- Watermark text configurable via env var `PDF_WATERMARK` (default "Confidential – Exported by Clinician").
- UTC ISO‑8601 timestamp embedded in footer.
- Output format **PDF/A‑2b** for long‑term preservation.

#### 5. Error Handling Conventions
| HTTP Status | User‑Visible Message| Logged Operation |
|-------------|------------------|-------------------|
| 200         | Success (PDF streamed) | EXPORT_PDF        |
| 403         | "You do not have permission to view this record."   or "Export not authorized."   | READ_DENIED / EXPORT_DENIED |
| 500         | Generic error message; alert ops team                | INTERNAL_ERROR    |

### Test Cases – MVP Core
| Test ID | Related AC | Description | Expected Result |
|---------|------------|-------------|-----------------|
| TC-001 | AC-003 | Front desk staff reads patient intake form for own clinic | Decrypted form displayed; audit log READ success |
| TC-002 | AC-004 | Front desk staff attempts cross-clinic record access | HTTP 403; audit log READ_DENIED |
| TC-003 | AC-005 | Clinician exports PDF for authorized patient | PDF with watermark and timestamp streamed over TLS 1.3; audit log EXPORT_PDF success |
| TC-004 | AC-006 | Clinician exports PDF for unauthorized patient | HTTP 403; no PDF generated; audit log EXPORT_DENIED |
| TC-005 | AC-007 | Exported PDF integrity verified on external workstation | Digital signature validates; tampering triggers warning |

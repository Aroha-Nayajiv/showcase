# Deployment Guide

## Primary User Personas for the PatientIntake Deployment Guide

The following personas capture the core human actors who will interact with the HIPAA‑compliant patient intake system during deployment and daily operation. Each persona is described with role responsibilities, HIPAA‑related security concerns, and concrete workflow interactions that must be supported by the system.

### 1. Front Desk Clerk (Role ID: PER-01)
**Primary Goal:** Capture accurate patient demographics, insurance information, and initial medical history at the point of entry.
**HIPAA Concerns:** Must ensure that all entered data is encrypted at rest and in transit (refer to FR‑001 and NFR‑001). The clerk should never see unencrypted protected health information (PHI) beyond what is displayed in the secure web form.
**Workflow Interactions:**
1. **Login** – Authenticate using unique credentials; system enforces multi‑factor authentication (MFA) per NFR‑003.
2. **Open Intake Form** – The web form loads over TLS 1.3; each field is encrypted client‑side before transmission.
3. **Data Entry** – Populate required fields (name, DOB, address, insurance policy number). Validation errors are shown inline; no PHI is stored locally on the workstation.
4. **Submit** – On submission, the form payload is encrypted with a per‑field AES‑256 key managed by the back‑end service. An audit log entry (FR‑003) records who, when, and what was created.
5. **Confirmation** – Clerk receives a non‑PHI confirmation number to give to the patient.
**Security Controls:** Role‑based access control (RBAC) limits the clerk to create operations only; they cannot read or modify existing records.

### 2. Clinician (Role ID: PER-02)
**Primary Goal:** Review patient‑submitted medical history and update clinical notes securely.
**HIPAA Concerns:** Must have read‑only access to PHI unless explicitly granted edit rights; all access must be logged (FR‑003) and immutable per audit requirements.
**Workflow Interactions:**
1. **Secure Login** – Uses strong password + MFA; session tokens are short‑lived (max 30 min).
2. **Search Patient Record** – Query by confirmation number; results are returned encrypted and decrypted only in the browser session.
3. **View Intake Summary** – PDF generated on demand; includes watermark with clinician's name and timestamp (FR‑007). The PDF is streamed over TLS and never written to disk on the client side.
4. **Add Clinical Notes** – If additional notes are required, clinician can append them; these notes inherit the same field‑level encryption.
5. **Logout** – Session termination triggers audit log entry.
**Security Controls:** RBAC grants read and append permissions; any attempt to edit original intake fields is denied and logged as a security event.

### 3. Patient (Role ID: PER-03)
**Primary Goal:** Provide personal and medical information securely and receive a copy of the intake summary for personal records.
**HIPAA Concerns:** Must be assured that their PHI is never exposed in transit or at rest without encryption; they have no direct access to the database but can retrieve a watermarked PDF via a secure link.
**Workflow Interactions:**
1. **Self‑Service Portal Access** – Optional; patient receives a one‑time token via secure email to view their submitted data.
2. **View PDF Summary** – The system generates a PDF with a unique patient watermark and timestamp; download link expires after 24 hours.
3. **Verify Data** – Patient can compare displayed data with their records; any discrepancy triggers a support ticket workflow.
**Security Controls:** The one‑time token is single‑use and time‑bounded; all downloads are logged with patient identifier masked for audit compliance.

### Summary Table
| Persona | ID | Primary Flow | Security Controls |
|---|---|---|---|
| Front Desk Clerk | PER-01 | Login → Open Form → Submit → Receive Confirmation | MFA, field‑level AES‑256 encryption, write‑only RBAC |
| Clinician | PER-02 | Login → Search → View PDF → Append Notes → Logout | Read‑only RBAC, immutable audit log, watermarked PDFs |
| Patient | PER-03 | Access portal via token → Download PDF → Verify | One‑time token, encrypted download link, audit logging |

These personas provide the necessary context for designers to define UI flows, security controls, and deployment configurations that satisfy FR‑001 through FR‑009, NFR‑001 through NFR‑003, and associated KPIs (KPI‑01 to KPI‑04).

---

## User Stories

| ID | As a | I want | So that |
|---|---|---|---|
| US-001 | Front Desk Clerk | Enter patient demographic data (name, DOB, address, contact) into the intake form | The patient record is complete and can be used for downstream clinical workflows |
| US-002 | Front Desk Clerk | Capture insurance information (provider, policy number, group ID) securely | Billing can be processed accurately while maintaining compliance |
| US-003 | Clinician | Review and add to the patient's medical history (allergies, medications, prior conditions) via the same encrypted form | The clinical team has a comprehensive view for safe care decisions |
| US-004 | Administrator | Generate a PDF intake summary for a patient record with a hospital watermark and an access timestamp | Authorized staff can share a read‑only snapshot that meets audit and legal retention requirements |

---

## Acceptance Criteria

### AC-004 – US-004 (PDF Intake Summary Generation)
**Given** an Administrator is authenticated with role "administrator" and has read access to the patient record,
**When** they click **Generate PDF**,
**Then** the system streams a PDF containing all captured fields, applies a watermark "Generated by {admin_name}" plus an ISO‑8601 export timestamp (FR‑007), stores the temporary PDF in an encrypted container, logs the export event (FR‑004), and respects storage limits (if free space <5 MB abort with "Insufficient storage").

## Design Needs (Product Phase Only)
1. **Watermark Specification:** Text pattern `Generated by {user_name}`, font size 10pt, opacity 30%, placed centered on each page footer.
2. **Timestamp Format:** ISO‑8601 UTC offset (`YYYY-MM-DDThh:mm:ssZ`) embedded in PDF metadata under `CreationDate`.
3. **PDF Generation Engine:** Use open‑source `wkhtmltopdf` v0.12.6 configured for PDF/A‑2b compliance.
4. **Encryption at Rest:** Temporary PDFs stored in AES‑256 GCM encrypted containers managed by existing key vault service.
5. **Access Control Check:** Integration point with RBAC service validates `role = administrator` before generation.
6. **Audit Logging Schema:** Fields – `event_id`, `user_id`, `patient_id`, `action` (`PDF_EXPORT`), `timestamp`, `checksum`, `outcome`.

These specifications constitute the complete product artifact ready for downstream design teams.
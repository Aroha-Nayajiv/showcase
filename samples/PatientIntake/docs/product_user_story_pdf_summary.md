# User Story: Export PDF Summary (Overview)

## PDF Summary Feature Specification

### Personas

| Persona ID | Role | Primary Goals | HIPAA Responsibilities | Success Metrics |
|---|---|---|---|---|
| PER-01 | Clinician (physician, nurse practitioner) | Quickly retrieve a complete, tamper-evident PDF summary of a patient's intake data to inform care decisions. | Must access only records for patients assigned to them (FR-002). Exported PDFs must include a watermark with user ID and timestamp (FR-008) and be logged (KPI-030). | Access time <2 s (KPI-001), 100 % audit log entry for each export. |
| PER-02 | Front-Desk Staff | Verify patient demographics and insurance information at registration, and generate a PDF receipt for the patient's record. | Must not view other patients' records; can export only for patients they have registered (FR-001, FR-002). Export must be logged and watermarked. | Form submission success rate ≥99 % (KPI-004), export success rate ≥98 %. |
| PER-03 | Patient | Review the PDF summary of their submitted intake information for accuracy and retain a copy for personal records. | Has right to view only their own PDF (FR-002). PDF must display a clear privacy notice (FR-010) and timestamp. | Patient acknowledges receipt within 1 s (FR-006), satisfaction score ≥4/5 (KPI-013). |

### Detailed Persona Descriptions

**PER-01 – Clinician**
- Context: Works in a clinical setting where timely access to accurate patient information is critical for diagnosis and treatment.
- Interactions: Uses the web interface to search for a patient, selects "Export PDF Summary" and downloads the document.
- Compliance: Must ensure that the export operation triggers an audit log entry and that the PDF contains a digital watermark embedding the clinician's user ID and export timestamp, satisfying HIPAA technical safeguard requirements for integrity and traceability.
- Pain Points: Delays in PDF generation impede workflow; missing watermarks could lead to non‑compliance.
- Metrics: Export latency ≤200 ms, 100 % watermark presence verified by automated checksum.

**PER-02 – Front‑Desk Staff**
- Context: First point of contact; responsible for entering patient demographics, insurance, and medical history via the structured web form.
- Interactions: After completing the intake form, clicks "Generate PDF" to attach the summary to the patient's record and optionally print a receipt for the patient.
- Compliance: Must only export PDFs for patients they have registered; system enforces row‑level security (RLS) to prevent cross‑patient access. Each export is logged with staff ID.
- Pain Points: High error rate in data entry; need immediate feedback on export success.
- Metrics: Validation error rate <1 % (FR‑005), export success rate ≥98 %.

**PER-03 – Patient**
- Context: Provides personal health information via the intake portal and expects transparency about how their data is used.
- Interactions: After submission, receives a confirmation screen with a link "View My PDF Summary". The PDF includes a watermark stating "Generated for Patient ID ... on ...".
- Compliance: Right to view only their own PDF; watermark must contain patient ID and timestamp to satisfy auditability.
- Pain Points: Concerns about privacy; needs assurance that the PDF cannot be altered.
- Metrics: Patient acknowledges receipt within 1 s, satisfaction ≥4/5.

### API Endpoints

- `GET /api/v1/patients/{patient_id}/export-pdf`
  - Description: Returns a PDF summary of the specified patient.
  - Permissions: Requires role‑based access (clinician can access assigned patients; front‑desk staff can access patients they registered).
  - Responses:
    - `200 OK` – PDF binary with `Content-Type: application/pdf` and `Content-Disposition: attachment; filename="patient_{patient_id}_summary.pdf"`.
    - `403 Forbidden` – Access denied; audit log entry created.
    - `404 Not Found` – Patient record not found.
    - `500 Internal Server Error` – Export service unavailable.
- `POST /api/v1/patients/{patient_id}/receipt-pdf`
  - Description: Generates a receipt PDF after form submission.
  - Permissions: Front‑desk staff only.
  - Responses similar to above with appropriate operation codes.

### Priority Ranking

| Story | Rank | Rationale |
|---|---|---|
| US‑001 | 1 | Directly supports clinical workflow and HIPAA audit requirements; failure blocks patient care. |
| US‑002 | 2 | Improves front‑desk efficiency and provides immediate patient confirmation, reducing call‑backs. |
| US‑003 | 3 | Ensures consistent branding and forensic traceability; less urgent than core export functionality. |

### User Stories
| Story ID | As a | I want | So that |
|---|---|---|---|
| US-001 | Clinician | Export a patient intake summary as PDF | I can review patient information offline while maintaining HIPAA compliance |
| US-002 | Front Desk Staff | Generate PDF after form submission | I can provide a printed copy for patient reference |
| US-003 | Administrator | Audit PDF export activity | I can ensure only authorized staff export data and meet audit requirements |
| US-004 | Clinician | View an audit log of PDF exports per patient | I can confirm who accessed the record and when |
| US-005 | Front Desk Staff | Preview PDF before export | I can verify data accuracy before sharing PHI |
| US-006 | Administrator | Schedule automatic nightly PDF export to secure archive | Reduce manual effort and ensure long‑term retention |
| US-007 | Patient | Download my intake PDF via secure portal | I have personal records for reference |

### Acceptance Criteria
| AC ID | Story ID | Given | When | Then | Edge Cases |
|---|---|---|---|---|---|
| AC-001 | US-001 | Clinician authenticated with role "clinician" and has view permission for the patient record | Clinician clicks "Export PDF" button on the patient record page | PDF generated with watermark (user ID, ISO8601 timestamp, export ID), download starts, audit log entry created (action=export, actor=clinician, patient_id, timestamp) | If record missing → error "Record not found"; if lacking permission → "Access denied"; if system clock out of sync >5min → "System time out of sync, contact IT" |
| AC-002 | US-002 | Front desk staff completed a patient intake form that passed validation | Staff clicks "Generate PDF" after submission | PDF generated with same watermark requirements, download starts, audit log records action=export, actor=front_desk, patient_id | If validation fails → specific field error messages; if database unavailable → "Service temporarily unavailable" |
| AC-003 | US-003 | Administrator accesses export audit page with admin role | Admin filters logs for "export" actions within last 24h | System displays list of export events with user ID, patient ID, timestamp, PDF checksum; logs immutable and tamper‑evident |  
| AC-004 | US-004 | Clinician has view permission and selects "Export History" for a patient | Clinician opens export history view | Table of export events with timestamps, user IDs, checksum appears; entries retained for 7 years (KPI‑003) |  
| AC-005 | US-005 | Front‑Desk staff has completed form data | Staff clicks "Preview PDF" | System renders read‑only PDF in‑browser with same watermark; option to proceed to final export |  
| AC-006 | US-006 | Administrator configured nightly job schedule (cron at 02:00 UTC) | Scheduler triggers export for all new records | PDFs generated, encrypted, stored in archive, audit log entry created; if archive full → job aborts and alerts admin |  
| AC-007 | US-007 | Patient has verified portal account and requests PDF download | Patient selects "Download My Intake PDF" | System serves watermarked PDF over TLS 1.3, access logged; if permission missing → "Access denied" |

### Design Details
- **Watermark format**: "Exported by {user_id} on {ISO8601_timestamp} – ExportID:{uuid}" embedded on each page.
- **PDF generation library**: WeasyPrint (open‑source) running in isolated Docker container without external network access.
- **API Endpoints**:
  - `POST /api/v1/patients/{patient_id}/export/pdf` – triggers PDF generation, returns download URL.
  - `GET /api/v1/patients/{patient_id}/export/history` – returns audit log entries for the patient.
  - `GET /api/v1/patients/{patient_id}/export/preview` – returns preview PDF stream.
  - `POST /api/v1/admin/pdf/export/schedule` – configure nightly export schedule.
- **Audit Log Schema** (`pdf_export_audit`): export_id (UUID PK), user_id, role, patient_id, timestamp, checksum, status.
- **Encryption**: Temporary PDF files stored on encrypted filesystem (dm‑crypt) and deleted after successful download; archived PDFs encrypted at rest using AES‑256.
- **Performance**: PDF generation must complete within 2 seconds for records <500 KB under load of 10 concurrent exports (measured by integration test).
- **Compliance**: Satisfies HIPAA §164.312(a)(2)(iv) (encryption) and §164.312(b) (audit controls). Metadata block embedded in PDF includes "HIPAA §164.312(a)(2)(iv)" for forensic audits.
- **Error Handling**: Service returns standardized error payload with code and user‑friendly message; internal stack traces never exposed.

### Traceability
- US‑001 ↔ FR‑001 (view latency), FR‑003 (logging)
- US‑001 ↔ FR‑002 (RBAC)
- US‑002 ↔ FR‑006 (form submission receipt)
- US‑003 ↔ FR‑003 (audit logging)
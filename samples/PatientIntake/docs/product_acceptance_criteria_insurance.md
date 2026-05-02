# Insurance Capture Acceptance Criteria

## Primary User Personas for PDF Summary Feature

1. Persona: Front\u2011Desk Staff (Role: Front\u2011Desk Operator)
Goal: Efficiently capture patient intake data and generate PDF summaries for downstream clinical review.
Responsibilities: Enter patient demographics, insurance details, and medical history into the structured web form; verify required fields; trigger PDF generation after successful submission; ensure the generated PDF includes a watermark with the operator's user ID and timestamp.
Pain Points: High volume of patients during peak hours; need to maintain sub\u2011200\u00a0ms response time (FR\u2011001) while ensuring field\u2011level encryption at rest and in transit (FR\u2011005). Errors in data entry must be flagged in real time with an error rate <1\u00a0% (FR\u2011005).
Success Metrics: Form submission acknowledgment displayed within 1\u00a0second (FR\u2011006); audit log entry created for every read/write operation (FR\u2011003); \u226599\u00a0% of PDFs contain correct watermark and access timestamp (KPI\u2011030).

2. Persona: Clinician (Role: Healthcare Provider)
Goal: Quickly access accurate, complete PDF intake summaries to inform diagnosis and treatment decisions.
Responsibilities: Retrieve patient PDFs from the secure portal; verify that only authorized clinicians can view the document (RBAC \u2013 FR\u2011002); confirm that the PDF watermark matches the clinician's user ID and access time; reference the audit log for compliance verification.
Pain Points: Need immediate access (<200\u00a0ms) to patient information while maintaining HIPAA compliance; must avoid exposure of PHI to unauthorized roles; must handle cases where the PDF generation fails or the watermark is missing.
Success Metrics: Retrieval latency \u2264200\u00a0ms for authorized clinicians (KPI\u2011002); 100\u00a0% of access attempts logged with user ID, timestamp, and outcome (FR\u2011003); zero unauthorized access incidents (KPI\u2011013).

3. Persona: Patient (Role: Patient or Legal Guardian)
Goal: Provide personal and insurance information securely and receive confirmation that the data has been recorded correctly.
Responsibilities: Complete the web form on a device of their choice; read the privacy notice (FR\u2011010) before submission; receive a confirmation receipt within 1\u00a0second after successful submission (FR\u2011006); optionally request correction of submitted data within 5 business days (FR\u2011011).
Pain Points: Concern about data privacy; need assurance that their information is encrypted both in transit (TLS\u00a01.3) and at rest (field\u2011level encryption); may encounter validation errors that must be clearly explained.
Success Metrics: Confirmation receipt displayed within 1\u00a0second for \u226599\u00a0% of submissions (FR\u2011006); validation error rate <1\u00a0% per batch (FR\u2011005); patient acknowledges privacy notice before proceeding (FR\u2011010).

Traceability Matrix:
Front\u2011Desk Staff \u2192 FR\u2011001, FR\u2011005, FR\u2011006, KPI\u2011030
Clinician \u2192 FR\u2011002, FR\u2011003, KPI\u2011002, KPI\u2011013
Patient \u2192 FR\u2011010, FR\u2011011, FR\u2011005, KPI\u2011001

### Acceptance Criteria

| AC ID | Story ID | Given | When | Then | Edge Cases |
|---|---|---|---|---|---|
| AC-001 | US-001 | The front\u2011desk staff is authenticated with role 'front_desk' and the intake form is loaded over TLS 1.3 | They submit valid demographic, insurance, and medical history fields | The data is encrypted field\u2011level in transit and at rest, a record is created in PostgreSQL, and an audit log entry is written with timestamp and user ID | If any required field is missing, the form shows inline validation error and prevents submission |
| AC-002 | US-001 | Same as AC-001 but with an invalid insurance number format | They attempt to submit the form | The system rejects the entry, displays a specific error message, and does not create a record or log entry | Ensure error does not expose sensitive data |
| AC-003 | US-002 | Clinician is authenticated with role 'clinician' and has read permission on patient records 
They request to view a specific patient's intake record 
The system decrypts the fields, displays the data, and writes an audit log entry indicating read access with timestamp and user ID 
If the clinician attempts to view a record they are not assigned to, access is denied and an audit log entry records the denied attempt 
| AC-004 | US-003 
Administrator is authenticated with role 'admin' 
They modify role permissions for front\u2011desk or clinician users 
The system updates PostgreSQL role grants, logs the change with before/after values, and confirms via UI notification 
If the admin attempts to remove their own admin rights, the system prevents the action and logs the attempt 
| AC-005 
US-001 
All network traffic uses TLS 1.3 and field\u2011level encryption keys are managed by a HSM compatible vault 
Data is transmitted from browser to server 
The server stores encrypted payloads; decryption occurs only in memory for authorized reads; audit log records both encryption and decryption events 
If TLS handshake fails, the form does not load and an error page is shown without revealing PHI 
| AC-006 
US-001 
PDF generation service is invoked after successful record creation 
PDF generation fails due to rendering error 
System returns HTTP 500 with error code PDF_GEN_ERR, logs failure with details, and notifies front\u2011desk staff with a retry option 
If retry also fails, escalation ticket is created automatically 
| AC-007 
US-002 
Clinician accesses PDF via /api/v1/pdf/export endpoint 
PDF watermark missing or hash mismatch detected 
System returns HTTP 400 with error code WATERMARK_MISMATCH, logs incident, and alerts security monitoring 
| AC-008 
US-001 
Audit log write operation encounters database error 
System attempts to write log entry 
System retries up to three times; if still failing, writes fallback log to local file and raises alert; front\u2011desk staff sees non critical warning but submission proceeds

### PDF Export Endpoint

Path: /api/v1/pdf/export
Method: POST
Authentication: Bearer token with role clinician or front_desk
Request Body: {"patient_id":"string","requester_id":"string"}
Responses:
200 OK: {"pdf_url":"https://.../file.pdf","watermark_hash":"sha256..."}
400 Bad Request (WATERMARK_MISMATCH): {"error":"Watermark verification failed"}
500 Internal Server Error (PDF_GEN_ERR): {"error":"PDF generation failed"}
Performance KPI: PDF generation latency ≤150 ms (KPI-PDF_LATENCY)

## Insurance Capture Acceptance Criteria

## PDF Summary Feature Specification: MVP Prioritization

### 1. Overview
The PDF summary export is a core compliance‑driven capability. Authorized staff (admin, clinician, front‑desk) must be able to generate a tamper‑evident PDF that includes a watermark with the exporting user ID, timestamp, and a unique document hash. The export respects role‑based access control (FR‑002) and is auditable per FR‑003 and FR‑008 (watermark). Encryption/decryption latency must not exceed 200 ms per record (KPI‑004).

### 4. API Specification
| Method | Path | Description | Success Code | Error Codes |
|--------|------|-------------|--------------|-------------|
| GET | /api/v1/patients/{patient_id}/export-pdf | Export patient record as PDF with watermark | 200 OK (application/pdf) | 400 Bad Request, 403 Forbidden, 404 Not Found, 500 Internal Server Error |
All endpoints require authentication token and enforce RBAC per FR‑002. Error responses include JSON body with `error_code` and `message` fields.

### 5. Design Needs
- **Watermark Engine** – Accepts dynamic fields (user ID, timestamp, hash) and embeds them without altering layout. Uses AES‑256‑GCM for field‑level encryption; keys rotated annually in HSM.
- **RBAC Enforcement** – Middleware validates role against FR‑002 before PDF generation.
- **Audit Log Schema** – Columns: event_type, user_id, patient_id, timestamp, document_hash, outcome, error_details (optional). Immutable storage for 7 years (FR‑003).
- **Error Handling** – Uniform JSON error model; ensures no partial PDFs are persisted on failure.
- **Performance Target** – PDF generation ≤2 seconds; encryption/decryption latency ≤200 ms per record (KPI‑004).

### 6. Test Cases
- **TC-014** – Verify successful PDF export for Front‑Desk role (covers AC‑001).
- **TC-015** – Verify clinician export with correct watermark (covers AC‑002).
- **TC-016** – Validate watermark template update persists (covers AC‑003).
- **TC-017** – Attempt unauthorized export and confirm denial log (covers AC‑004).
- **TC-018** – Check Export History panel displays immutable entries (covers AC‑005).
- **TC-019** – Simulate PDF generation failure (e.g., out‑of‑memory) and verify 500 error handling.
- **TC-020** – Measure latency of export operation meets ≤2 seconds.

### 7. Traceability Matrix
| Requirement | User Story | Acceptance Criteria |
|---------------|------------|----------------------|
| FR‑001 | US‑001, US‑002 | AC‑001, AC‑002 |
| FR‑002 | US‑001‑US‑005 | All ACs enforce RBAC |
| FR‑003 | US‑001‑US‑005 | Audit log entries recorded |
| FR‑008 | US‑003 | Watermark includes required fields |
| KPI‑004 | All PDFs | Encryption latency ≤200 ms |

---
*All identifiers referenced above are consistent with the project asset registry.*
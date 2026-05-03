# PDF Summary Acceptance Criteria

## Personas for PDF Summary Feature

### Clinician (Dr. Alice Smith)
Role: Frontline medical provider who reviews patient intake summaries to make clinical decisions.
Goals: Quickly access complete, accurate patient demographics, insurance, and medical history; ensure data integrity and confidentiality.
Pain Points: Delays >2 seconds hinder care; missing or incorrect info leads to treatment errors; need audit trail for compliance.
Success Metrics: Access time ≤200 ms (KPI-002), 100 % of viewed records logged (KPI-003), satisfaction score ≥4/5.

### Front‑Desk Staff (Bob Johnson)
Role: Administrative staff who enters patient data and initiates PDF export for record‑keeping.
Goals: Efficient data entry with real‑time validation; generate PDF summary for filing; receive immediate confirmation receipt.
Pain Points: Validation errors increase re‑work; slow PDF generation delays workflow; risk of unauthorized export.
Success Metrics: Validation error rate <1 % (FR-005), PDF generation ≤1 s, export logged with watermark and timestamp (FR-008), audit log completeness 100 % (KPI-003).

### Patient (Maria Lopez)
Role: Subject of the intake form whose personal health information is captured.
Goals: Provide accurate information quickly; be informed about privacy practices; receive confirmation of submission.
Pain Points: Complex forms cause abandonment; lack of transparency about data handling raises trust issues.
Success Metrics: Form completion time ≤2 min, privacy notice displayed before entry (FR-010), receipt displayed within 1 s (FR-006), satisfaction ≥4/5.

All personas are tied to functional requirements FR‑001‑FR‑010 and KPIs. The PDF summary must respect role‑based access: clinicians and front‑desk can export; patients cannot. Each export includes watermark with user ID and timestamp per FR‑008. Audit logs capture read/write per FR‑003.

### User Stories
| Story ID | As a | I want | So that |
|---|---|---|---|
| US-001 | Clinician | to view and export a patient's intake summary as a PDF | I can review patient information offline while maintaining HIPAA compliance |
| US-002 | Front-Desk Staff | to generate a PDF summary after data entry is completed | I can provide the patient with a printed copy for their records |
| US-003 | Admin | to audit PDF export activity | I can ensure all accesses are logged and meet audit requirements |

### Acceptance Criteria
| AC ID | Story ID | Given | When | Then |
|---|---|---|---|---|
| AC-001 | US-001 | The clinician is authenticated with role "clinician" and has read permission on the patient record | The clinician clicks "Export PDF" for a specific patient | The system generates a PDF that includes a watermark with the clinician's user ID, export timestamp, and a unique document ID; the PDF is delivered over an HTTPS connection; an audit log entry is created with status "success". |
| AC-002 | US-001 | The same as AC-001 but the clinician's session has been idle for >15 minutes | The clinician attempts to export the PDF | The system denies the request, displays "Session expired", and logs an "unauthorized export attempt" entry. |
| AC-003 | US-002 | Front-Desk staff has completed data entry and the form validation passed | The staff clicks "Print Summary" | The system generates a PDF with the same watermark requirements, prints it to the default printer, and logs the print event. |
| AC-004 | US-002 | The printer is offline or out of paper | The staff clicks "Print Summary" | The system shows an error "Printer unavailable", does not generate a PDF, and logs the failure with error code 502. |
| AC-005 | US-003 | An admin views the audit log UI with filter "PDF Export" | The admin selects a date range and clicks "Search" | The system returns a list of all PDF export events, each entry showing user ID, patient ID, timestamp, document ID, and outcome; the list can be exported as CSV. |
| AC-006 | US-003 | The audit log storage reaches 95 % of allocated disk space | The admin runs the "Generate Report" action; The system warns "Log storage nearing capacity", suggests archiving, and still returns the requested data without loss. |

### Edge Cases & Error Scenarios
1. Unauthorized Role – If a user without "clinician" or "front-desk" role attempts the export endpoint, the system returns HTTP 403 and logs "access denied".
2. Corrupted Patient Data – If required fields are missing, the PDF generation aborts with error "Missing required patient fields", no file is produced, and an audit entry records the failure.
3. Network Interruption – If the HTTPS connection drops during download, the client receives a partial file error; the server logs "download interrupted" and does not mark the export as successful.
4. Timestamp Tampering – The watermark timestamp is signed using an HMAC key; any alteration causes verification failure and the PDF is rejected by downstream consumers.
5. Large Attachments – If a patient record includes >10 MB of attached images, the PDF generation must complete within 5 seconds; otherwise, the system returns error "PDF generation timeout" and logs performance metrics.

## Design Needs
- Specification of watermark format: `<UserID>_<Timestamp>_<DocID>` using ISO‑8601 UTC.
- Cryptographic signing algorithm: HMAC‑SHA256 with rotating master key stored in Vault.
- Logging schema: fields event_type, user_id, patient_id, doc_id, outcome, timestamp.
- Performance requirement: PDF generation latency ≤ 2 seconds for records ≤ 5 MB; ≤ 5 seconds for ≤ 10 MB.
- Accessibility: PDF must be tagged for screen readers (PDF/UA compliance).

## Metrics & Compliance
- Watermark accuracy ≥ 99.9 % (verified by automated checksum test).
- Audit log completeness ≥ 100 % for all export attempts (KPI‑003).
- Export success rate ≥ 98 % under normal load (KPI‑030).
- All PDF transfers must use TLS 1.3 (NFR‑002).

## API Specification
**Endpoint:** POST /api/v1/patients/{patient_id}/export/pdf
**Description:** Generates a PDF summary for a patient record.
**Headers:** Authorization: Bearer <JWT>; Content-Type: application/json
**Request Body Example:** {"patient_id":"string","requester_id":"string","requester_role":"clinician|front-desk"}
**Responses:**
200 OK – Body contains pdf_url and metadata (including watermark details).
400 Bad Request – error_code: E_MISSING_FIELDS, message describing missing parameters.
401 Unauthorized – error_code: E_UNAUTHORIZED, when role is not permitted.
403 Forbidden – error_code: E_ACCESS_DENIED, when requester lacks permission for specific patient.
408 Request Timeout – error_code: E_PDF_TIMEOUT, when generation exceeds latency thresholds.
500 Internal Server Error – error_code: E_KEY_UNAVAILABLE or E_GENERATION_FAILURE.
**Error Codes Reference:**
E_MISSING_FIELDS – Required fields absent.
E_UNAUTHORIZED – Invalid or missing authentication token.
E_ACCESS_DENIED – Role or row‑level security violation.
E_PDF_TIMEOUT – Generation exceeded allowed time.
E_KEY_UNAVAILABLE – Encryption key could not be retrieved.
E_PRINTER_UNAVAILABLE – Printer error during print action.

## MVP Prioritization
1. Core Export Functionality: Generate PDF with required data and watermark within 200 ms for records ≤5 MB; otherwise within 5 s for larger records.
2. Access Control Enforcement: Only roles "clinician" and "front-desk" may request export; unauthorized attempts return 403 and are logged.
3. Watermark Integrity and Tamper Evidence: Embed HMAC‑SHA256 hash in PDF metadata field DocumentHash; mismatches trigger high‑severity audit alert.
4. Audit Log Completeness: Every successful export creates an audit entry with user_id, patient_id, export_timestamp, checksum, watermark details; retention ≥7 years.
5. Error Handling and Edge Cases: Defined error responses for session expiry, missing fields, key unavailability, printer issues, and network interruptions; all logged with distinct codes.
6. Compliance Verification: Automated compliance test script validates HIPAA Security Rule §164.312(e)(1) and §164.312(a)(2)(iv) checks in Docker Compose environment; report must show all checks passed before release.
---
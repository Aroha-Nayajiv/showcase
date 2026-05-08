# User Story: Export PDF Summary

### Edge‑Case Scenarios
1. **Permission Escalation Attempt** – User with role `front_desk` tries to export a PDF for a patient they are not assigned to. System denies request, returns “Access denied”, and records a failed audit entry.
2. **Corrupted Data** – Patient record contains malformed JSON causing PDF generation failure. Service returns “Data error – cannot render PDF” and logs error details without exposing PHI.
3. **Service Unavailability** – PDF generation micro‑service is down. UI displays “PDF service unavailable – try later” and creates an audit entry with outcome=`failed_service_unavailable`.
4. **Key Rotation Event** – During automatic TLS certificate rotation, an active export may experience handshake failure. Request is retried once; if still failing, it is logged as “export_failed_key_rotation”.

### Metrics & Success Criteria
- **Compliance Metric:** 100 % of exported PDFs contain required watermark and timestamp (automated test suite).
- **Performance Metric:** 95 % of export requests meet ≤2 second latency under load of 50 concurrent users.
- **Audit Coverage:** Immutable log entry for every export action; audit completeness ≥99 % (daily reconciliation script).

### Priority & Business Justification
- **US‑001 – Priority 1:** Clinicians are primary consumers; HIPAA compliance hinges on secure export.
- **US‑002 – Priority 2:** Improves front‑desk efficiency and patient satisfaction.
- **US‑003 – Priority 3:** Enables governance and auditability required for regulatory compliance.

### Personas
- **PER-01 (Clinician):** Medical professional reviewing patient intake; needs offline access.
- **PER-02 (Front‑Desk Clerk):** Staff member initiating PDF export after data entry.
- **PER-03 (Admin):** System administrator responsible for audit compliance and access control.

### Security & Compliance Notes
- PDFs stored encrypted at rest using AES‑256 via pgcrypto column-level encryption.
- All transport uses TLS 1.3 with automated weekly certificate rotation.
- Audit log entries are immutable and retained for 7 years (NFR‑003).
- Role‑based access enforced via PostgreSQL Row‑Level Security policies.

### Overview
This specification defines the user stories, acceptance criteria, and supporting details for the **Export PDF Summary** feature of the *PatientIntake* SaaS application. All items are traceable to functional requirement **FR-004**, non‑functional requirement **NFR-002**, and KPIs **KPI-001**, **KPI-002**, **KPI-003**. The feature must satisfy HIPAA technical safeguard requirements and support SOC 2/ISO 27001 auditability.

### Acceptance Criteria

#### US‑001 – Clinician Export
| ID     | Given| When  | Then |
|--------|-----------------------------|--------------|-----------|
| AC-001 | Clinician is authenticated (role *clinician*) with a valid session token; patient record exists and is marked **complete**. | Clinician clicks **Export PDF** on the patient detail page. | System generates a PDF in **PDF/A‑2b** format, embeds visible watermark “Confidential – Clinician View”, adds an immutable timestamp signed with the server’s private key, streams the file to the browser, and creates an audit‑log entry (FR‑004) with `outcome: SUCCESS`. |
| AC-002 | Same pre‑conditions as AC‑001 but the server encounters an internal error while generating the PDF. | Clinician attempts export. | System returns error message “Export failed, please try again later.”, logs an entry with `outcome: FAILURE` and error code, and ensures no partial file is cached on the client. |
| AC-003 | Patient record is **incomplete**. | Clinician clicks **Export PDF**. | System displays error “Cannot export incomplete record.”, does not generate a PDF; audit log records `outcome: FAILURE` with reason `INCOMPLETE_RECORD`. |
| AC-004 | Session token is expired or invalid. | Clinician initiates export. | System redirects to login page; no PDF generated; audit log records `outcome: FAILURE` with reason `AUTH_EXPIRED`. |

#### US‑2 – Front‑Desk Preview
| ID | Given | When | Then |
|--------|-------|------|------|
| AC-005 | Front‑Desk staff authenticated (role *front‑desk*) with view permission; sensitive fields (SSN, insurance) are flagged as **redacted** in UI. | Staff selects **Generate Preview PDF**. | System creates a PDF that **excludes** redacted fields, applies watermark "Preview – Internal Use Only", includes a timestamp (no digital signature), displays the PDF in‑browser (no download button), and logs `outcome: SUCCESS`. |
| AC-006 | Redaction flags are missing or mis‑configured for a patient record. | Staff attempts preview generation. | System aborts export and shows "Redaction configuration error."; audit log records `outcome: FAILURE` with reason `REDACTION_ERROR`. |

#### US‑3 – Compliance Verification
| ID | Given | When | Then |
|--------|-------|------|------|
| AC-007 | Compliance officer authenticated (role *compliance_officer*) and accesses **Export Log Dashboard**. | Officer selects an export event to view details. | System displays PDF metadata: watermark text, timestamp, digital signature verification status (valid/invalid), and the corresponding audit‑log entry. Officer may download the original PDF; download action is logged with `outcome: SUCCESS`. |
| AC-008 | Digital signature verification fails for a selected PDF. | Officer views details. | System shows warning "Signature invalid – possible tampering."; audit log records `outcome: FAILURE` with reason `SIGNATURE_INVALID`. |

### API Endpoints (Design‑Level Reference)
> For full endpoint specifications see `design_api_specification` artifact.

* `/api/v1/patients/{patientId}/export-pdf` – **POST**
  * Auth: Bearer token with required role.
  * Request body: `{ "exportType": "clinician"|"preview" }`
  * Responses:
    * `200 OK` – PDF binary stream.
    * `400 Bad Request` – validation errors (e.g., incomplete record, redaction error).
    * `401 Unauthorized` – token missing/expired.
    * `500 Internal Server Error` – generation failure.

* `/api/v1/compliance/export-log/{exportId}` – **GET**
  * Auth: role *compliance_officer*.
  * Returns JSON with metadata fields (`watermark`, `timestamp`, `signatureStatus`, `auditLogId`).

### Traceability Matrix
| Artifact Item                     | Linked Requirement(s)|
|-------------|--------------------|
| US‑001 / AC‑001‑004               | FR‑004, NFR‑002, KPI‑001, KPI‑003                       |
| US‑002 / AC‑005‑006              | FR‑004, NFR‑002, KPI‑001 |
| US‑003 / AC‑007‑008              | FR‑004, KPI‑003  |
| API `/export-pdf`                 | FR‑004, NFR‑002  |
| Watermark & Timestamp implementation | FR‑004, NFR‑002  |

### Non‑Functional Considerations
* **Security** – Watermark and timestamp are signed using RSA 2048 bit keys; keys rotate per SOC 2 policy.
* **Performance** – PDF generation must complete within 2 seconds for average record size (<500 KB) to meet KPI‑001 (80 % reduction in manual transcription time).
* **Scalability** – Service deployed as a stateless microservice behind a load balancer; supports horizontal scaling to handle peak clinic loads.
* **Auditability** – Every export creates an immutable audit log entry stored in an append‑only datastore retained for 7 years (per NFR‑003).

### Acceptance Summary
The feature is considered complete when:
1. All acceptance criteria above pass automated integration tests.
2. Audit logs are verifiable in the compliance dashboard.
3. Performance benchmarks meet KPI‑001 targets.
4. Security review confirms watermark/timestamp integrity and key management compliance.

---

*Document prepared by Refiner (Product Manager mindset).*
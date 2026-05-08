# Export Secure PDF Summary","description":"Narrative describing clinician workflow to export patient PDFs.","content":"As a clinician I need to request a PDF summary of a patient's intake record so that I can print or share it securely with other providers while ensuring HIPAA compliance. The story includes steps to authenticate via SSO

## Export Secure PDF Summary – Clinician Workflow

### Personas
| ID | Role | Description |
|----|------|-------------|
| PER-01 | Clinician | Medical staff who reviews patient intake data and needs to share a secure PDF summary with other authorized providers. |
| PER-02 | Front‑Desk Staff | Administrative personnel who may request a PDF for printing or filing but has limited view permissions. |
| PER-03 | Compliance Officer | Oversees audit compliance; can view export logs and verify watermark/timestamp integrity. |

### Priority Ranking
| ID | Rank | Rationale |
|----|------|----------|
| US-001 | 1 (Critical) | Directly enables HIPAA‑compliant data sharing – aligns with FR‑004 and KPI‑003 audit compliance. |
| US-002 | 2 (High) | Supports operational workflow for front‑desk while preserving security constraints. |
| US-003 | 3 (Medium) | Provides necessary auditability for compliance verification; required for regulatory reporting. |

### User Stories
| ID | Persona | Goal |
|----|---------|------|
| US-001 | PER-01 | Generate a PDF intake summary for a patient so I can review the information offline while maintaining HIPAA compliance. |
| US-002 | PER-02 | Export a PDF summary for a patient after consent is recorded so I can provide printed copies without exposing PHI in the system. |
| US-003 | PER-03 | Verify that every exported PDF contains a visible watermark and export timestamp so I can demonstrate auditability during regulatory reviews. |

### Acceptance Criteria
**AC‑001 – US‑001 – Successful Export**
- **Given** the clinician is authenticated via SSO, has the Clinician role, the patient record exists and is marked as complete.
- **When** the clinician clicks **Export PDF** on the patient detail page.
- **Then** the system generates a PDF/A‑2b document that:
  - Contains all fields from the intake form (demographics, insurance, medical history).
  - Embeds a visible watermark "Confidential – HIPAA Protected" (12 pt Helvetica, 30 % opacity, centered).
  - Includes an export timestamp in ISO‑8601 UTC with millisecond precision in both visible footer and PDF metadata.
  - Is encrypted at rest with AES‑256.
  - Is streamed over TLS 1.3.
  - Writes an immutable audit log entry (FR‑004) recording user ID, patient ID, timestamp and outcome **Success**.
- **Edge Cases**:
  - If the patient record is incomplete, the Export button is disabled and a tooltip explains the requirement.
  - If TLS negotiation fails, the download is aborted and an error "Secure connection required" is shown.

**AC‑002 – US‑001 – Session Expiration**
- **Given** the clinician's session token has expired.
- **When** the clinician attempts to click Export PDF.
- **Then** the system redirects to the SSO login page preserving the original request; after re‑authentication the export proceeds as in AC‑001.
- **Edge Cases**:
  - If re‑authentication fails three times, the system logs **Failure** and displays "Access denied – authentication required".

**AC‑003 – US‑002 – Front‑Desk Export**
- **Given** Front‑Desk Staff is authenticated with the FrontDesk role and the patient has consented to receive a summary.
- **When** the staff selects Export PDF from the registration screen.
- **Then** the system generates the same PDF as AC‑001 but adds a header "Generated for Front Desk Use" and applies redaction rules:
  - Clinical notes are removed.
  - Only demographic and insurance sections remain visible.
  - The stored file receives `access_level=read_only` preventing edits.
  - An audit log entry records role **FrontDesk** and outcome **Success**.
- **Edge Cases**:
  - If the staff attempts to export a record belonging to another clinic location, the system returns "Access denied – insufficient privileges".

**AC‑004 – US‑003 – Compliance Officer Audit View**
- **Given** a compliance officer views the audit log interface with read‑only access.
- **When** the officer filters logs for Export PDF events over the past 30 days.
- **Then** the system displays entries with user ID, role, patient ID (masked except last 4 digits), timestamp and outcome.
  - The officer can export the filtered view as CSV; PHI is masked in the CSV.
  - Pagination is enforced for >10 000 entries; SLA < 2 seconds per page.

### Design Needs (to be specified by Design)
1. **PDF Generation Library** – Must support PDF/A‑2b compliance, watermark overlay, and AES‑256 encryption of output files.
2. **Watermark Specification** – Text content, font size, opacity (30 %), placement (centered), and language localization.
3. **Timestamp Format** – UTC ISO‑8601 with millisecond precision; must be included in PDF metadata and visible footer.
4. **Access Control Integration** – RBAC model mapping roles (Clinician, FrontDesk, ComplianceOfficer) to permission matrix for PDF export; enforce least‑privilege principle.
5. **Audit Log Schema** – Fields: event_id, user_id, role, patient_id_masked, action, timestamp, outcome, error_code (if any). Log entries must be immutable and stored in PostgreSQL using append‑only tables.
6. **Transport Security** – All PDF streams must be served over TLS 1.3; certificate rotation policy aligned with NFR‑002.
7. **Failure Handling** – Graceful error messages as described in edge cases; must not leak PHI in error responses.
8. **Performance Targets** – PDF generation latency ≤ 3 seconds for average record size (~500 KB); concurrent export handling up to 20 simultaneous requests without degradation.
9. **Rate Limiting Policy** – Max 10 export requests per user per minute; excess requests receive HTTP 429 with message "Export rate limit exceeded" and are logged.

### API Contract (new)
| Method | Path | Auth | Roles Allowed | Description |
|--------|------|------|--------------|-------------|
| GET | `/api/v1/patients/{patientId}/export-pdf` | OAuth2 Bearer token (SSO) | Clinician, FrontDesk | Returns a streamed PDF/A‑2b document meeting AC specifications. |

#### Responses
- **200 OK** – Body: binary PDF stream; Headers: `Content-Type: application/pdf`, `Content-Disposition: attachment; filename="Patient_{patientId}_Summary.pdf"`.
- **400 Bad Request** – Invalid patient ID or record incomplete (`error_code": "E_INCOMPLETE_RECORD`).
- **401 Unauthorized** – Session expired or missing token (`error_code": "E_SESSION_EXPIRED`).
- **403 Forbidden** – Role lacks permission or cross‑clinic access (`error_code": "E_ACCESS_DENIED`).
- **429 Too Many Requests** – Rate limit exceeded (`error_code": "E_RATE_LIMIT`).
- **500 Internal Server Error** – Unexpected failure (`error_code": "E_INTERNAL`).

### Error Code Reference Table
| Code | Description |
|------|-------------|
| E_INCOMPLETE_RECORD | Patient intake not marked complete; export blocked. |
| E_TLS_FAIL | TLS handshake failed; secure connection required. |
| E_AUTH_DENIED | Authentication failed after retries. |
| E_ACCESS_DENIED | Unauthorized role or cross‑clinic access attempt. |
| E_RATE_LIMIT | Export request rate limit exceeded. |
| E_INTERNAL | Unhandled server error; investigate logs. |

### Redaction Rules for Front‑Desk Exports (detail)
- Remove all clinical notes sections.
- Retain only demographic fields (name, DOB, contact), insurance information, and visit summary without diagnostic details.
- Apply header "Generated for Front Desk Use" on first page.
- Store resulting file with `access_level=read_only` flag; editing attempts are rejected with `E_EDIT_FORBIDDEN` logged.

### Audit Log Schema (expanded)

{
  "event_id": "uuid",
  "user_id": "string",
  "role": "Clinician|FrontDesk|ComplianceOfficer",
  "patient_id_masked": "string", // last 4 digits visible only
  "action": "EXPORT_PDF",
  "timestamp": "ISO8601",
  "outcome": "Success|Failure",
  "error_code": "optional string"
}

All entries are append‑only in PostgreSQL schema `audit_logs` with row‑level security enforcing read access only to Compliance Officers.

---
*All specifications trace back to functional requirements FR‑004 (audit logging), FR‑002 (TLS), NFR‑003 (AES‑256 at rest), KPI‑003 (audit compliance), and related risk mitigations.*
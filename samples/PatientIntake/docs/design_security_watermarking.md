# Export Watermarking Design (Overview)

## Export Watermarking Design Overview

### 1. Overview
The PDF export service generates a PDF summary of a patient intake record and applies a tamper‑evident watermark that includes the exporting user ID, ISO‑8601 timestamp, and a SHA‑256 hash of the PDF content. The watermark is rendered by WeasyPrint and stored in the export_log table for auditability. This design satisfies FR-001 (latency), FR-003 (audit logging), FR-008 (watermark), and REQ-001 (WCAG) requirements.

### 2. API Contracts
| Endpoint | Method | Purpose | Request Schema | Response Schema | Auth |
|---|---|---|---|---|---|
| /api/v1/export/watermark | POST | Generate PDF with watermark for a patient record | {"record_id":"uuid","requested_by":"string"} | {"export_id":"uuid","status":"string","pdf_url":"string (signed)"} | Bearer JWT (RS256) |
| /api/v1/export/watermark/{export_id} | GET | Retrieve status or download generated PDF | N/A | {"export_id":"uuid","status":"string","pdf_url":"string (signed)","error_code":"string"} | Bearer JWT (RS256) |

**Request Schema** (JSON Schema draft‑07): {"type":"object","properties":{"record_id":{"type":"string","format":"uuid"},"requested_by":{"type":"string"}},"required":["record_id","requested_by"],"additionalProperties":false}
**Response Schema** (POST): {"type":"object","properties":{"export_id":{"type":"string","format":"uuid"},"status":{"type":"string","enum":["pending","ready","failed"]},"required":["export_id","status"] ,"additionalProperties":false}
**Response Schema** (GET): same as POST with optional "error_code" field.

### 3. Data Model
| Entity | Field | Type | Required | Description |
|---|---|---|---|---|
| export_log | export_id | UUID | Yes | Primary key |
|  | record_id | UUID | Yes | FK to patient record (RLS enforced) |
|  | requested_by | TEXT | Yes | User ID of clinician initiating export |
|  | watermark_text | TEXT | Yes | Concatenation of user ID, timestamp, SHA‑256 hash |
|  | created_at | TIMESTAMPTZ | Yes | Generation timestamp (UTC) |
|  | status | TEXT (enum) | Yes | pending, ready, failed |
|  | pdf_path | TEXT | No | Secure storage path, cleared after 30 days |
|  | audit_event_id | UUID | No | Reference to audit log entry |

### 4. Error Taxonomy
| Code | HTTP | Description | User Message | Retryable |
|---|---|---|---|---|
| ERR-001 | 400 | Missing required field | "Required data missing; please check your request." | No |
| ERR-002 | 401 | Invalid or expired JWT | "Authentication failed; re‑login required." | No |
| ERR-003 | 403 | Access denied by RLS policy | "You do not have permission to export this record." | No |
| ERR-004 | 404 | Export ID not found | "Requested export does not exist." | No |
| ERR-005 | 500 | PDF generation failure (WeasyPrint) | "Unable to generate PDF at this time; please try again later." | Yes |

### 5. Service Boundaries
| Service | Responsibility | Dependencies | Events Emitted |
|---|---|---|---|
| ExportService | Orchestrates PDF creation, watermark injection, storage, audit logging | WeasyPrint, pgcrypto, S3‑compatible storage, JWT validator, rate‑limiter; ExportCreated, ExportReady, ExportFailed | |
| AuditService | Persists immutable audit records for export actions; PostgreSQL, pgcrypto |; AuditRecordCreated | |

### 6. Security Considerations
- **Authentication**: Bearer JWT signed with RS256; token must contain `role` claim (`clinician`, `admin`). Public keys rotated via Docker secret `jwt_pub_key`.
- **Authorization**: Row‑level security (RLS) on patient table ensures clinicians can only export records they are assigned to (FR-002).
- **Input Validation**: JSON schema validation rejects unknown fields; payload size limited to 4 KB.
- **Encryption at Rest**: All PHI fields, including `watermark_text`, encrypted with AES‑256‑GCM via pgcrypto.
- **Transport Security**: TLS 1.2+ enforced on all endpoints.
- **Audit Logging**: Every successful export creates an entry in `export_log` and emits an `AuditRecordCreated` event captured by the central audit service. Logs retained for 7 years (FR-003).
- **Rate Limiting**: 10 requests per minute per user; excess returns 429 Too Many Requests.
- **Tamper Evidence**: `watermark_text` includes SHA‑256 hash of the final PDF; validation endpoint verifies integrity.

### 7. Validation Endpoint (Optional)
| Endpoint | Method | Purpose |
|---|---|---|
| /api/v1/export/watermark/validate/{export_id} | POST | Verify that stored `watermark_text` matches computed hash of PDF; Request: { "pdf_url": "string" }; Response: { "valid": true, "message": "Watermark integrity verified." } |

### 8. Traceability to Requirements
- FR-001, FR-003, FR-008 satisfied by latency targets, audit logging, and watermark implementation.
- REQ-001 (WCAG) addressed by providing accessible error messages.
- REQ-002 (Keyboard navigation) ensured by API being usable via scripts and tools.
*End of Document*
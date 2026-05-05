# Access Control Schema Definition

# Personas, User Stories, Acceptance Criteria, Edge Cases & Design Artifacts

## 1. Personas (identified in the project asset registry)
| ID   | Name                | Description |
|------|---------------------|-------------|
| PER-01 | Front Desk Clerk | Staff member who registers patients, captures demographic and insurance information, and initiates the intake workflow. Limited to create operations on demographic fields and read‑only access to audit logs. |
| PER-02 | Clinician | Licensed medical professional who reviews and augments the medical history, adds clinical notes, and can generate PDF summaries for treatment planning. Has read/write access to medical‑history fields and export permission for PDFs. |
| PER-03 | Compliance Officer (Auditor) | Responsible for verifying that all HIPAA safeguards are enforced, reviewing audit logs, and approving PDF export requests. Has read access to all data and audit‑log read/write permissions but cannot modify patient data. |
| PER-04 | Administrator | System admin responsible for managing user roles, generating audit reports, and overseeing system configuration. Has full read/write access across all domains and can invoke privileged operations such as audit report generation. |

## 2. User Stories (Product backlog items)
| ID   | Persona | Goal | Success Criteria |
|------|---------|------|------------------|
| US-001 | PER-01 | Capture patient demographics and insurance info via the encrypted web form | The system records accurate intake data while maintaining HIPAA‑required encryption at rest and in transit |
| US-002 | PER-02 | View and edit a patient's medical history and generate a PDF summary | Clinician can provide appropriate care and share a compliant document with authorized staff |
| US-003 | PER-03 | Audit every read/write operation and verify PDF export timestamps | Compliance Officer can demonstrate compliance with FR‑001, FR‑002 and NFR‑003 during internal or external audits |
| US-004 | PER-04 | Generate comprehensive audit reports for any patient record | Admin can retrieve a tamper‑evident PDF audit log covering a configurable time window |

## 3. Acceptance Criteria

### AC-003 – US-002 – Clinician edit & encryption
**Given** the Clinician is authenticated with role `clinician` and has read access to patient record `record_id=12345`
**When** the clinician updates the insurance provider field and adds a new allergy to the medical history section
**Then** the updated fields are encrypted at field level, stored atomically, an audit‑log entry records the update action with before/after hashes for changed fields, and the UI shows confirmation banner "Record updated successfully".
**And** if the clinician attempts to modify a non‑permitted field (e.g., patient SSN) the system returns "Permission denied" and logs an `unauthorized_update` event.
**And** if a version conflict is detected the system prompts the user to reload.

## 4. Edge‑Case & Failure Scenarios
* **Encryption key rotation failure** – If the key management service cannot rotate keys, the system falls back to the previous key, logs a critical alert, and rejects new data until rotation succeeds.
* **Audit log overflow** – When PostgreSQL audit table reaches its configured max rows, archiving to a read‑only partition is triggered while preserving queryability for the required retention period.
* **Role escalation attempt** – If a user tries to elevate from `front_desk` to `clinician` via manipulated JWT claims, authentication rejects the token, records a security event, and does not grant elevated privileges.
* **Missing encryption keys during PDF generation** – If decryption keys are unavailable, PDF generation aborts with error "Encryption key unavailable" (referencing FR‑001) and logs the incident.
* **Concurrent PDF export requests** – Multiple users requesting PDFs for the same patient are queued; each generated PDF includes correct user‑specific watermark.
* **Audit log saturation (>10 M rows)** – Archival process triggers while guaranteeing retrieval for compliance audits.

## 5. Design Needs (to be handed off to Design)

### 5.1 Permission Matrix (machine‑readable JSON schema)

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PermissionMatrix",
  "type": "object",
  "properties": {
    "role": {
      "type": "string",
      "enum": ["front_desk","clinician","compliance_officer","admin"]
    },
    "permissions": {
      "type": "object",
      "properties": {
        "demographics": { "$ref": "#/definitions/crud" },
        "insurance": { "$ref": "#/definitions/crud" },
        "medical_history": { "$ref": "#/definitions/crud" },
        "pdf_export": { "$ref": "#/definitions/crud" },
        "audit_log": { "$ref": "#/definitions/crud" }
      },
      "required": ["demographics","insurance","medical_history","pdf_export","audit_log"]
    }
  },
  "required": ["role","permissions"],
  "definitions": {
    "crud": {
      "type": "object",
      "properties": {
        "create": { "type": "boolean" },
        "read": { "type": "boolean" },
        "update": { "type": "boolean" },
        "delete": { "type": "boolean" }
      },
      "required": ["create","read","update","delete"]
    }
  }
}

### 5.2 Encryption & Key Management Specification
* Algorithm: AES‑256‑GCM for field‑level encryption.
* Key length: 256 bits.
* Rotation schedule: Quarterly rotation; immediate re-encryption of newly written records; old keys retained for decryption of existing data until migration completes.

### 5.3 Audit‑Log Schema

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AuditLogEntry",
  "type": "object",
  "properties": {
    "event_id": {"type":"string"},
    "user_id": {"type":"string"},
    "role": {"type":"string"},
    "operation": {"type":"string","enum":["create","read","update","delete","failed_create","unauthorized_update","failed_report"]},
    "entity_id": {"type":"string"},
    "timestamp": {"type":"string","format":"date-time"},
    "hash": {"type":"string"},
    "details": {"type":"object"}
  },
  "required": ["event_id","user_id","role","operation","entity_id","timestamp","hash"]
}

### 5.4 PDF Generation Requirements
* Watermark format: `{role}-{name}` (e.g., `clinician-JDoe`).
* Timestamp format: ISO 8601 UTC embedded in PDF metadata.
* Generated PDFs are encrypted at rest using AES‑256.
* Access control checks role permissions before export.

## 6. Non‑Functional Thresholds & KPIs
* **KPI‑01:** Form submission response time ≤ 200 ms (NFR‑001).
* **KPI‑03:** Audit log write latency ≤ 50 ms (NFR‑003).
* TLS 1.3 mandatory for all transport; JWT tokens signed with RS256; token expiry ≤ 15 minutes.
* System availability target ≥ 99.9 % (KPI‑02).

---
*Traceability:* All artifacts reference FR‑001 (secure demographic capture), FR‑002 (insurance handling), FR‑003 (audit logging), NFR‑001 (encryption), NFR‑003 (audit logging), KPI‑01 (response time), KPI‑03 (audit log latency).
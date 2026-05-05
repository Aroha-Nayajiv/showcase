# Access Control Acceptance Criteria

## Access Control Acceptance Criteria for Patient Intake System

### Acceptance Criteria
#### AC-001 – Create Intake Form (Front Desk)
**Given** the Front Desk Staff is authenticated with the `front_desk` role and has a valid session,
**When** they submit a fully populated intake form,
**Then** the system stores each field encrypted at rest, returns a success message, and creates an audit‑log entry (`create` action) with timestamp and user ID.
*Failure paths*
- If any required field is missing → validation error 400, no data persisted.
- If the session has expired → redirect to login, no audit entry created.

#### AC-002 – Encryption Key Rotation Failure
**Given** the key rotation service attempts to rotate the encryption key for medical history fields,
**When** the rotation process fails due to vault unavailability,
**Then** the system aborts the operation, returns error 503 with message "Key rotation unavailable", logs an `key_rotation_failure` audit entry, and alerts an Admin.

#### AC-003 – View / Edit Intake Form (Clinician)
**Given** the Clinician is authenticated with the `clinician` role and possesses a valid patient record ID,
**When** they request to view the record,
**Then** the system decrypts the requested fields on demand, returns them in the UI, and records a `read` audit entry.
**When** they modify a field and submit changes,
**Then** the system updates the record, stores before/after hashes, creates an `update` audit entry with both hashes.
*Failure paths*
- Record does not exist → 404 response, no audit entry.
- Clinician lacks edit permission → only `read` allowed; attempted edit results in 403 with `unauthorized_edit` audit entry.

#### AC-004 – Audit Log Retrieval (Admin)
**Given** the Admin is authenticated with the `admin` role,
**When** they request the audit log filtered by date range or user ID,
**Then** the system returns an immutable, chronologically ordered log including digital signatures for each entry and enforces read‑only access (no modification endpoints).

#### AC-005 – Network Interruption During Audit Log Write
**Given** an operation triggers an audit‑log write,
**When** a network interruption occurs before commit,
***Then*** the transaction is rolled back, the client receives error 502 "Audit log write failed", and no partial entry is persisted.

#### AC-006 – Concurrent Edit Conflict
**Given** two clinicians load the same patient record concurrently,
***When*** one submits an update,
***Then*** the system uses optimistic locking; if the second clinician attempts to save stale data,
they receive 409 Conflict with details of the latest version.

### 4. Primary Personas
| ID   | Persona               | Description                                                                                                   | Permissions (high‑level) |
|------|-----------------------|---------------------------------------------------------------------------------------------------------------|----------------------------|
| PER-01 | Front Desk Staff      | Handles patient check‑in, captures demographic, insurance and medical history data.                           | Create intake records; view non‑sensitive fields; cannot view encrypted medical history or audit logs |
| PER-02 | Clinician             | Reviews patient medical history and signs off on care plans.                                                | Read all intake fields (including encrypted medical history after de‑cryption); update clinical notes; export PDF summary |
| PER-03 | Compliance Officer    | Audits system for HIPAA compliance and ensures proper logging.                                               | Read audit log entries; view any PDF export metadata; cannot modify patient data |

### 5. Interaction Flow Overview
1. **Form Entry (Front Desk)** – PER‑01 accesses the web form via HTTPS (TLS 1.3). Each field is encrypted client‑side before transmission; the server stores ciphertext in PostgreSQL using column‑level encryption.
2. **Review & Edit (Clinician)** – After authentication, PER‑02 opens the same intake record. The application decrypts fields on demand using a role‑restricted key vault; the clinician can add clinical notes and trigger PDF generation.
3. **PDF Generation** – When PER‑02 clicks **Export Summary**, the system composes a PDF via `wkhtmltopdf`, applies a watermark containing the clinician's name and a timestamp, then stores the file in an access‑controlled volume.
4. **Audit & Compliance (Compliance Officer)** – PER‑03 queries the immutable audit log (AU‑6) to verify that every read/write operation generated a tamper‑evident entry and that PDF exports contain correct watermark and timestamp metadata.

### 6. Design Needs for Downstream Phases
- **Key Management Specification**: Use HashiCorp Vault with role‑based key retrieval policies scoped to PER‑02 only.
- **Audit Log Schema**: Immutable append‑only table with columns `event_id`, `timestamp_utc`, `actor_role`, `action`, `resource_id`, `hash`, `digital_signature`. Retention aligned with NIST AU‑6.
- **PDF Generation Service Contract**: Input JSON payload (`record_id`, `requester_role`, `requester_name`), output file path, required watermark format `{role}:{name}` and ISO 8601 timestamp.
- **RBAC Matrix Document**: Detailed permission matrix linking each PER‑xx role to CRUD operations on each data element.
- **Performance Monitoring**: Metrics for response time (KPI‑01 <200 ms) and audit‑log write latency (target ≤ 50 ms).

---

### User Stories
| ID   | Role               | Goal                                                                                     | Description |
|------|--------------------|------------------------------------------------------------------------------------------|-------------|
| US-001 | Front Desk Staff (`front_desk`) | Create and edit patient intake forms | Capture demographic, insurance, and medical history securely; data must be available for clinician review |
| US-002 | Clinician (`clinician`) | View completed intake forms and export PDF summaries | Provide care based on accurate, up‑to‑date patient information while maintaining auditability |
| US-003 | Admin (`admin`) | Manage user roles and audit logs | Ensure only authorized personnel have access and can demonstrate compliance during audits |

**Priorities**: US-001 (P1 – core data capture), US-002 (P2 – care delivery), US-003 (P3 – governance). Priorities are justified by the business rule that only authorized roles may create or modify records (see FR‑001).

### Traceability Matrix
| Requirement ID | Linked Stories / ACs |
|-----------------|-----------------------|
| FR-001 (Secure data capture) | US-001, US-002, US-003 → AC-001, AC-003, AC-004 |
| FR-003 (PDF export control) | US-002 → AC-004 |
| NFR-003 (Audit logging) | All → AC-001–AC-005 |
| KPI-01 (Response <200 ms) | All → performance monitoring metric referenced in design needs |

---

### Permission Matrix Specification
| Role            | Create | Read   | Update | Delete | Export PDF |
|-----------------|--------|--------|--------|--------|------------|
| Front Desk (`front_desk`) | ✅      | ✅ (non‑sensitive) | ✅ (own records) | ❌      | ❌ |
| Clinician (`clinician`)   | ❌      | ✅ (all permitted fields) | ✅ (allowed fields) | ❌      | ✅ |
| Admin (`admin`)            | ✅*    | ✅ (all) | ✅*    | ✅*    | ✅* |
*Admin actions are limited to configuration screens; actual patient data creation/deletion occurs through controlled APIs.

### Audit Log Schema (Immutable Table)
sql
CREATE TABLE audit_log (
    event_id UUID PRIMARY KEY,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    actor_role VARCHAR(20) NOT NULL,
    actor_id UUID NOT NULL,
    action VARCHAR(30) NOT NULL,
    resource_type VARCHAR(30) NOT NULL,
    resource_id UUID NOT NULL,
    hash BYTEA NOT NULL,
    digital_signature BYTEA NOT NULL,
    additional_info JSONB
);
-- Table is append‑only; UPDATE/DELETE are prohibited at DB level.

Retention: retain for 7 years per NIST AU‑6; archive older rows to cold storage quarterly.

### Encryption Key Management
- **Generation**: RSA‑4096 keys generated in HashiCorp Vault per environment.
- **Rotation**: Automatic rotation every 90 days; rotation failure triggers AC‑002 error path.
- **Access Policy**: Only role `clinician` may request decryption keys via Vault path `kv/data/keys/clinical`. Front Desk never receives decryption capability.

### PDF Generation Service Contract

POST /api/v1/intake/{record_id}/export-pdf
{
  "requester_role": "clinician",
  "requester_name": "Dr. Alice Smith"
}
Response 200:
{
  "pdf_url": "https://storage.example.com/pdfs/record12345.pdf",
  "watermark": "Clinician:Dr. Alice Smith",
  "timestamp": "2026-05-05T12:34:56Z"
}

Errors: 502 for generation failure, 403 for unauthorized role.

### Performance Monitoring Metrics
| Metric                     | Target               |
|----------------------------|----------------------|
| API response time          | ≤ 200 ms (KPI‑01)    |
| Audit log write latency    | ≤ 50 ms              |
| PDF generation duration     | ≤ 1 s                |

---

## Priority Rationale
1. **US‑001 (P1)** delivers core end‑to‑end intake flow required for patient care and directly satisfies FR‑001 and KPI‑01.
2. **US‑002 (P2)** ensures clinicians can access records and export PDFs while providing auditable trails—critical for HIPAA compliance (NFR‑003).
3. **US‑003 (P3)** gives administrators governance over roles and logs, enabling compliance audits and rapid incident response.

These priorities align with regulatory mandates (HIPAA §164.312(a)(2)(iv), NIST SP 800‑53 AC‑2 & AU‑6) and business value of delivering a secure, usable intake experience before scaling.
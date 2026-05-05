# Clinician Export PDF User Story

## Access Control Schema Definition

### 1. Personas
| ID | Role | Capabilities | Permissions |
|----|------|--------------|------------|
| PER-01 | Front Desk Clerk | - Register patient arrival<br>- Capture basic demographic data<br>- Initiate intake form session | Can create new intake records; can view records they created; can export PDF **after** intake is completed; cannot edit after submission; cannot modify role permissions |
| PER-02 | Clinician | - Review completed intake forms<br>- Export secured PDF summary for clinical review<br>- Add clinical notes (outside scope of this artifact) | Can read any completed intake record; can export PDF if authorized; can view audit log entries for their actions |
| PER-03 | Compliance Officer | - Verify audit logs for HIPAA compliance<br>- Review access timestamps and watermark integrity<br>- Approve policy changes | Read‑only access to audit logs, access timestamps, and watermark metadata for all PDFs; cannot modify patient data |

### 2. Role‑Based Permissions Matrix
| Permission / Action | Front Desk Clerk | Clinician | Compliance Officer |
|---------------------|------------------|-----------|---------------------|
| Create intake record | ✅ | ❌ | ❌ |
| View own created record | ✅ | ✅ (all records) | ✅ (audit view only) |
| Export PDF summary | ✅ (after form completion) | ✅ (if role = clinician) | ❌ |
| View audit log entry for own actions | ✅ (self) | ✅ (self) | ✅ (all) |
| Modify role permissions | ❌ | ❌ | ✅ |

### 3. End‑to‑End Journey Mapping

#### 3.1 Front Desk Clerk Journey
1. **Login** using unique credentials (HIPAA §164\.312(a)(1)).
2. **Select** "New Patient Intake" from dashboard.
3. **Enter** demographic fields; each field is encrypted at rest using field‑level AES‑256 (per technical safeguard §164\.312(e)(1)).
4. **Submit** form – data is persisted to PostgreSQL with row‑level security tagging `created_by = PER-01`.
5. System **logs** creation event with timestamp, user ID, and operation type `CREATE` in immutable audit log.
6. **Logout** – session terminated, all in‑transit traffic protected by TLS 1\.3.

#### 3.2 Clinician Journey
1. **Authenticate** with multi‑factor credentials.
2. **Search** patient by MRN; system verifies RBAC allowing read of any record.
3. **Open** completed intake; UI displays encrypted fields decrypted on the client side only.
4. **Click "Export PDF"** – backend generates PDF via open‑source `wkhtmltopdf`, injects:
   - Staff watermark containing clinician name and role.
   - Access timestamp in ISO‑8601 format.
   - PDF encryption using AES‑256 with a per‑session key.
5. **Download** PDF; download event recorded in audit log with operation type `EXPORT`.
6. If decryption fails, system returns error code `PDF_EXPORT_ERR` and logs failure without exposing PHI.

#### 3.3 Compliance Officer Journey
1. **Login** with read‑only compliance credentials.
2. **Navigate** to "Audit Log" module.
3. **Filter** logs by operation type (CREATE, EXPORT) and date range.
4. **Validate** that every PDF export entry includes a matching watermark identifier and timestamp.
5. **Generate** compliance report summarizing:
   - Total number of PDFs exported per day.
   - Any export attempts denied due to RBAC violation.
6. **Export** report as CSV for external audit; this action is also logged.

### 4. Audit Log Requirements
| Column | Description |
|--------|-------------|
| event_id | UUID v4 unique identifier for the event |
| timestamp | ISO‑8601 UTC time of the action |
| user_id | Persona ID (PER-01/02/03) |
| action | Enum: [CREATE, READ, EXPORT, VIEW_LOG] |
| resource_id | Primary key of the intake record or PDF file |
| outcome | SUCCESS or FAILURE with error code |
| metadata | JSON blob containing watermark ID, TLS version, etc |

All log entries are written to a dedicated PostgreSQL table `audit_log` with append‑only policy and periodic write‑once snapshots to an immutable object store for long‑term retention (minimum 6 years as required by HIPAA).

### 5. Design Needs for Downstream Design Phase

#### 5.1 Role‑Based Access Control Policy (JSON)

{
  "policy": {
    "PER-01": {
      "create": ["intake_record"],
      "read": ["own_intake_record"],
      "export_pdf": ["completed_intake"]
    },
    "PER-02": {
      "read": ["any_intake_record"],
      "export_pdf": ["any_completed_intake"]
    },
    "PER-03": {
      "read_audit": ["all"]
    }
  }
}

#### 5.2 Encryption Specification
- Algorithm: AES‑256‑GCM for field‑level encryption.
- Key‑management: HashiCorp Vault (open‑source) with rotation every 90 days.
- PDF encryption: AES‑256 per‑session key applied before storage in PostgreSQL `bytea`.

#### 5.3 Validation Rules
- Mandatory fields per section defined in the intake form.
- Regex patterns:
  - SSN: `^\d{3}-\d{2}-\d{4}$`
  - Insurance number: `^[A-Z0-9]{10}$`
- Length limits: Free‑text fields max 500 characters.
- Sanitization library: OWASP Java HTML Sanitizer (or equivalent).

#### 5.x Performance Acceptance Criteria
- PDF generation latency ≤ 200 ms for average record size (<2 MB) – measured over 10 k transactions (KPI‑01).
- System response time for any API call ≤ 200 ms under load of 100 concurrent users.

#### 5.x Audit Log Completeness
- Every successful or failed export creates an audit log entry (100 % completeness).

## User Stories & Acceptance Criteria

#### Acceptance Criteria
1️⃣ **Given** the Clinician is authenticated and has the Clinician role, and the patient record exists and is marked as *completed*
   **When** the Clinician clicks **Export PDF** on the patient detail page
   **Then** a PDF file is generated, encrypted at rest using field‑level encryption, includes a watermark “Exported by {ClinicianName}”, timestamp “Exported on {ISO8601}”, and is offered for download. An audit log entry is created with `action=EXPORT`, `outcome=SUCCESS`, and relevant metadata.
2️⃣ **Given** the patient record is missing required fields
   **When** the Clinician attempts export
   **Then** the system shows error “Incomplete intake data – cannot generate PDF” and no PDF is generated; an audit log entry records `outcome=FAILURE` with error code `ERR_INCOMPLETE_DATA`.
3️⃣ **Given** the encryption service is unavailable
   **When** the Clinician initiates export
   **Then** the system returns “PDF generation temporarily unavailable – try later” and logs `outcome=FAILURE` with error code `ERR_ENCRYPTION_UNAVAILABLE`.
4️⃣ **Performance:** The PDF generation completes within 200 ms for records <2 MB (KPI‑01).

### US-002 – Front Desk Clerk Export PDF
**Role:** Front Desk Clerk
**Goal:** Provide a printed copy of the intake summary after registration without exposing PHI to unauthorized parties.
**Traceability:** FR-001, FR-002, FR-003, NFR-003, KPI-01

## Traceability Matrix
| Artifact ID | Linked Requirement(s) |
|-------------|------------------------|
| US-001 | FR-001, FR-002, FR-003, NFR-003, KPI-01 |
| US-002 | FR-001, FR-002, FR-003, NFR-003, KPI-01 |
| US-003 | FR-004, NFR-003, KPI-01 |
| Permission Matrix | FR-001…FR-004 |
| Audit Log Schema | NFR-003 |
# PostgreSQL Database Schema Design

## Persona: PER-03 – Clinician (Care Provider)

**Role:** Licensed medical professional who reviews patient intake data and signs off on treatment plans.
**Demographics:** Physicians, nurse practitioners, ages 30–65, high security awareness, often using dual‑monitor setups.

**Goals**
1. Access complete, verified patient records instantly.
2. Export a PDF summary for offline review while preserving watermark and timestamp.
3. Ensure any read operation is recorded for compliance audits.

**Pain Points**
- Needs assurance that the PDF cannot be altered after export.
- Requires quick retrieval despite strict RBAC constraints.

**Security Concerns**
- Must have SELECT permission on decrypted view `v_patient_intake` only after successful MFA; each read writes to `audit_log` with user ID and timestamp.
- PDF export metadata (`pdf_exports` table) includes `watermark_id`, `exported_by`, and `export_timestamp` for immutable proof of access.

**System Interactions**
- Logs into the clinician portal, views patient details via a read‑only UI component.
- Clicks **Download Intake PDF** which triggers the same background worker used by front desk staff but records `exported_by = clinician_id`.

**Traceability**
Directly supports **FR–006** (PDF generation), **NFR–002** (encryption at rest), and **KPI–003** (audit log completeness).

## User Stories for PostgreSQL Database Schema Design – Structured Web Form

The following user stories define the functional intent of the PostgreSQL database schema that will store patient demographics, insurance information, and medical history captured via the structured web form. All data must be encrypted at field level both in transit and at rest, and access must be governed by role–based permissions (Admin, Clinician, Front Desk). Each story is linked to concrete business priorities and traceable to the project requirements (FR–001—FR–006) and HIPAA technical safeguards.

### Story Table
| ID   | Persona          | Goal| Value | Priority |
|------|-----------------|----------|-----------|----------|
| US–0001   | Patient          | Submit my personal and medical information through a secure web form               | My health data is stored safely and only authorized staff can view it                     | 1 |
| US–0002   | Front Desk Staff | Enter or correct a patient's insurance details after initial submission         | The system reflects accurate coverage for billing and eligibility checks            | 2 |
| US–0003   | Clinician       | Retrieve a patient's complete intake record for review                           | I can provide appropriate care without requesting additional information           | 1 |
| US–0004   | Admin          | Audit every read/write operation on intake tables| I can demonstrate compliance with HIPAA audit–log requirements and detect unauthorized access | 1 |
| US–0005   | Patient        | Request a PDF summary of my intake data (with watermark and timestamp)      | I receive a tamper–evident document that only authorized staff can export      | 2 |

### Acceptance Criteria Table
| ID     | User Story | Acceptance Criteria |
|--------|------------|-----------------------|
| AC–0001   | US–0001   | **Given** the patient is authenticated via TLS 1.3 and has an active session token **When** they submit the web form with all required fields (name, DOB, address, insurance policy number, medical history) **Then** a new row is inserted into `patient_intake` with each column encrypted using pgcrypto AES 256, a `created_at` timestamp is recorded, and the patient receives a confirmation screen showing a non–identifying reference ID.<br>**Negative:** Missing required field → inline validation error; Encryption failure → transaction rolls back and logs an error in `audit_log`. |
| AC–0002   | US–0002   | **Given** the Front Desk staff member is logged in with role `front_desk` and has SELECT/UPDATE rights on `patient_intake` **When** they update `insurance_provider` or `policy_number` and click Save **Then** the updated values are re–encrypted, `updated_at` is set, AND an entry is added to `audit_log` indicating role = front_desk, operation = UPDATE, row_id = UUID.<br>**Negative:** Attempt to modify a read–only column → DB trigger rejects change; Concurrent edit → row–level lock prevents lost update. |
| AC–0003   | US–0003   | **Given** a Clinician is authenticated with role `clinician` and has SELECT rights on `patient_intake` **When** they query a patient's record via the UI **Then** the system decrypts permitted columns (full medical history but not raw encryption keys), returns a result that includes a digital signature verifying integrity, AND creates an audit entry recording READ operation with clinician ID.<br>**Negative:** Clinician attempts to view an unassigned record → Row–level security denies access; Decryption key missing → error logged and generic “access denied” shown. |
| AC–0004   | US–0004   | **Given** the Admin has role `admin` with full privileges on all tables including `audit_log` **When** they run the audit report for the past 24 hours **Then** the report lists each operation with timestamp, actor role, affected row UUID, AND outcome (SUCCESS/FAIL). All entries are immutable because `audit_log` uses an append–only table with write–once policy.<br>**Negative:** Log tampering attempt → DB trigger aborts transaction; Large volume → pagination ensures performance. |
| AC–0005   | US–0005   | **Given** a Patient has completed intake and a PDF metadata record exists in `pdf_exports` linked to the intake UUID **When** they click “Download Summary” **Then** the backend verifies the requestor’s role (`patient`) against export permissions, streams a PDF that includes visible watermark “Confidential – Patient Copy” and an embedded timestamp (`exported_at`). The export action is recorded in `audit_log` with operation = EXPORT.<br>**Negative:** Export request from unauthorized IP → request blocked; PDF generation failure → graceful error page shown, no partial file left on server. |
| AC–0006   | US–0003 / US–0005   | **Given** the system must satisfy **KPI–0003** (audit log completeness) **When** any READ or EXPORT operation occurs **Then** the corresponding entry must be written to `audit_log` within 100 ms and be queryable for reporting.<br>Ensures traceability to **FR–006** (PDF generation) and supports compliance audits. |

## Edge Cases & Failure Handling

1. **Encryption Key Rotation** – When a key rotation event occurs (per NIST SP​800​57), all existing encrypted columns are re–encrypted using the new key within a scheduled maintenance window. Failure to complete triggers an alert AND aborts further writes until resolved. *(Related to NFR–002)*

2. **Database Connection Loss** – If PostgreSQL becomes unavailable during a form submission, the application queues the payload locally, encrypts it at rest using a temporary key, AND retries automatically. After three failed retries it logs a critical error AND notifies an admin. *(Related to KPI–0001 availability)*

3. **Concurrent Updates** – Row–level security enforces optimistic concurrency; if two front desk users edit the same intake record simultaneously, the second transaction receives a serialization failure AND must reload the latest version before retrying. *(Related to FR–004)*

## Personas (Actors)
| ID | Role | Description |
|----|------|-------------|
| PER-01 | Patient | Individual whose protected health information (PHI) is captured via the intake form. |
| PER-02 | Front‑Desk Staff | Administrative employee who creates new intake records and can view limited fields for scheduling. |
| PER-03 | Clinician | Licensed medical professional who reviews and updates clinical sections of the intake record and can generate the PDF summary. |
| PER-04 | Admin | System administrator responsible for role‑based access control (RBAC), audit‑log maintenance, and key rotation. |

### US-001 | Admin (PER‑04)
**Goal:** Define role‑based permissions on the `patients`, `insurance`, and `medical_history` tables and configure row‑level security (RLS) policies.
**Rationale:** Only authorized personnel can read or modify protected PHI, satisfying FR‑002 and NFR‑002 (TLS & encryption).

**Acceptance Criteria**
1. **AC‑001**: Given an admin user, when configuring RLS policies, then the policies must restrict SELECT/INSERT/UPDATE/DELETE on PHI columns to roles defined in the matrix.
2. **AC‑002**: Given any non‑admin role, when attempting to access restricted columns, then the query must be denied with an “access denied” error.
3. **AC‑003**: All RLS policies are version‑controlled and auditable (recorded in `audit_log`).

### US-003 | Front‑Desk Staff (PER‑02)
**Goal:** Submit a new intake form that stores demographics, insurance info, and medical history in encrypted columns.
**Rationale:** The system captures all required intake data securely at point of entry (FR‑001, FR‑002).

**Acceptance Criteria**
1. **AC‑007**: Given a front‑desk user, when completing the intake form, then all PHI fields are stored using pgcrypto column encryption with AES‑256 GCM.
2. **AC\-008**: The form validates required fields before submission and returns user-friendly error messages.
3. **AC\-009**: Successful submission creates an audit log entry with operation “INSERT”, table name “patients”, and includes the user ID.

### US-004 | Compliance Officer (PER\-01)
**Goal:** Query an immutable audit log of every read/write operation on PHI tables and verify that each entry includes user ID, timestamp, and operation type.
**Rationale:** Demonstrates compliance with KPI\-003 (audit log completeness) and supports periodic HIPAA audits.

**Acceptance Criteria**
1. **AC\-010**: Given any authorized query, when retrieving audit logs, then results are ordered by timestamp descending and include fields `user_id`, `operation`, `table_name`, `ts`, `success`.
2. **AC\-011**: The audit log table is append‑only; attempts to UPDATE or DELETE rows are rejected with error “Immutable log”.
3. **AC\-012**: A materialized view `daily_audit_summary` aggregates counts per role and is refreshed hourly for KPI dashboards.

## Design Needs (to be handed off to Design)

1. **Encrypted Columns Specification – Identify columns requiring pgcrypto encryption:**
   - `patients.patient_name`
   - `patients.dob`
   - `insurance.insurance_number`
   - `medical_history.notes`
   Provide key rotation strategy referencing NFR‑002.

2. **Row Level Security Policies – Define policy expressions for each role:**
   - Admin: `USING (true)` (full access)
   - Clinician: `USING (role = 'clinician')`
   - Front‑Desk Staff: `USING (role = 'front_desk' AND column NOT IN ('patient_name','dob','insurance_number'))`
   Include fallback deny policy `USING (false)`.

3. **Audit Log Schema – Table definition:**
sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    table_name TEXT NOT NULL,
    ts TIMESTAMPTZ DEFAULT now(),
    success BOOLEAN NOT NULL,
    details JSONB
);

Ensure immutable storage via append‑only configuration.

4. **PDF Export Metadata Table**
sql
CREATE TABLE pdf_exports (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id),
    exported_by TEXT NOT NULL,
    export_ts TIMESTAMPTZ DEFAULT now(),
    file_path TEXT NOT NULL,
    watermark TEXT NOT NULL
);

5. **Indexing Requirements**
   - Index on `audit_log.ts` for KPI reporting.
   - Index on `pdf_exports.patient_id` for fast lookup.
   - Composite index on (`user_id`, `operation`) for security audits.

6. **Compliance Reporting Views**
   - Materialized view `daily_audit_summary` aggregating counts per role for KPI‑003 dashboards.
   - View `pdf_export_report` exposing export counts per clinician per day.

## Traceability Matrix

| User Story | Acceptance Criteria | Linked Requirements / KPIs |
|------------|----------------------|----------|
| US-001 | AC-001 – AC-003 | FR-002, NFR-002 |
| US-002 | AC-004 – AC-006 | FR-003, FR-004, KPI-001 |
| US-003 | AC-007 – AC-009 | FR-001, FR-002 |
| US-004 | AC-010 – AC-012 | FR-005, KPI-003 |
| US-005 | AC-013 – AC-015 | NFR-002 (key rotation), KPI-001 |

All tables will be created using open source PostgreSQL extensions only; no proprietary features are used.
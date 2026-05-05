# Access Control User Stories

### Personas
| Persona ID | Role               | Description                                                                                     | Primary Goals                                            | Key Permissions                                          |
|-----------|--------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------|------------------------------------------------------------|
| PER-01   | Front Desk Clerk  | Staff member who registers new patients and captures demographic, insurance, and medical‑history data via the web form. | Capture patient demographics, insurance details, and initial medical history. | Create patient records; read own submitted records; no update/delete. |
| PER-02   | Clinician          | Licensed medical professional who reviews and augments patient medical history.                | Review patient history; add clinical notes; sign off records.          | Read all patient records; update only `clinical_notes`; no delete. |
| PER-03   *Compliance Officer*   *Auditor responsible for verifying access compliance and generating reports.* |

*All personas authenticate via Keycloak (OpenID Connect) with MFA for Clinician and Compliance Officer roles.*

### Role‑Based Access Control Matrix
| Role               | CREATE                | READ                         | UPDATE                     | DELETE   | EXPORT                |
|--------------------|----------------------|------------------------------|----------------------------|----------|-----------------------|
| Front Desk Clerk   | PatientRecord (own)  | PatientRecord (own)          | –                          | –        | –                     |
| Clinician          | –                    | PatientRecord (all)         | clinical_notes (own)        | –        | –                     |
| Compliance Officer| –                    | AuditLog (all)               | –                          | –        |

### Encryption & Audit Logging
- **Encryption**: Per‑field AES‑256 encryption performed client‑side; keys stored in HSM (SoftHSM) with 90‑day rotation.
- **Transport**: TLS 1.3 for all network traffic.
- **Audit Log Schema** (immutable table):
  - `action` (CREATE, READ, UPDATE, EXPORT, EMERGENCY_ACCESS, ERROR)
  - `actor_id`
  - `timestamp` (ISO‑8601)
  - `resource_id`
  - `outcome` (SUCCESS, FAILURE)
  - `justification` (optional, for emergency access)

#### US-002 – Clinician: Review & Augment Medical History
**Goal**: Retrieve a patient's complete medical‑history record for review and add clinical notes.

**BDD Acceptance Criteria**
- **Given** the clinician is authenticated with MFA and has the `clinician` role,
- **When** they open a patient record,
- **Then** the system retrieves encrypted fields, decrypts them via the HSM service,
- **And** displays the data in the UI,
- **When** the clinician adds clinical notes and saves,
- **Then** the notes are stored unencrypted in the `clinical_notes` sub‑section,
- **And** an `UPDATE` audit entry is recorded,
- **And** the UI shows a “Saved” confirmation,
- **If** HSM key retrieval fails, the system displays “Decryption unavailable”, logs an `ERROR` entry, and prevents note entry.
*(Traceability: FR‑003, NFR‑003, KPI‑02)*

### Traceability Matrix
| User Story ID | Linked Functional Requirements      | Linked Non‑Functional Requirements | KPIs / Risks |
|---------------|--------------------------------------|--------------------------------------|---------------|
| US-001       | FR‑001, FR‑002, FR‑003              | NFR‑003                              |	KPI‑01 |
| US-002       |	FR‑003                               |	NFR\-003                            |	KPI\-02 |
| US\-003       |	FR\-005                               |	NFR\-003                            |	KPI\-04 |
| US\-004       |	FR\-010                               |	NFR\-003                            |	RISK\-01 |

### Design Considerations for Upcoming Phases
1. **Encryption Key Lifecycle** – Generate per‑field keys on record creation; rotate every 90 days; store rotated keys securely in HSM; purge old keys after 30 days.
2. **Audit Log Scalability** – Append‑only table indexed by `timestamp` and `actor_id`; partition by month to support >10 M rows while maintaining <200 ms query latency.
3. **PDF Generation Parameters** – wkhtmltopdf version ≥ 0.12.6; watermark placed in header/footer; ISO‑8601 timestamp format (`YYYY-MM-DDThh:mm:ssZ`).
4. **Emergency Override Timeout** – Automatic revocation after configurable period (default 2 hours); audit entry includes expiration timestamp.
5. **Multi‑Tenant Isolation (SAAS Context)** – Each tenant’s patient data stored in separate schema; RBAC enforced per tenant; encryption keys scoped per tenant.

*All specifications comply with HIPAA technical safeguards and align with project KPIs and risk mitigation strategies.*

## User Stories and Acceptance Criteria

### US-001: Front Desk Clerk submits new patient intake form
**Persona:** ST-01 (Front Desk Clerk)  
**Priority:** High  

**Description:** The clerk captures patient demographic and insurance information via a web form.

#### Acceptance Criteria
| ID   | Given                                                                                                   | When                                                                                     | Then                                                                                                                                                                                                                                                                                     |
|------|----------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AC-001 | The Front Desk Clerk is authenticated and has the 'front_desk' role.                                   | They submit the intake form with all mandatory fields filled.                           | Each field is encrypted using AES‑256‑GCM before persistence; the API returns HTTP 201 with a non‑guessable record ID. If validation fails, the API returns HTTP 400 with field‑specific errors and no data is stored. |
| AC-002 The client establishes a TLS 1.3 connection. |
 The form data is transmitted to POST /api/v1/intake. |
 Data in transit remains encrypted; packet capture shows only ciphertext. |
|
| AC-003 The clerk submits a form that triggers an audit log entry. |
 The backend processes the request. |
 | An immutable audit log entry of type CREATE_RECORD is written with timestamp, user_id, patient_id, and outcome 'success'. |

### US-002: Clinician accesses patient record
**Persona:** ST-02 (Clinician)  
**Priority:** High  

**Description:** Clinician views a patient’s stored record.

### US-003: Administrator reviews audit logs
**Persona:** ST-03 (Administrator)  
**Priority:** Medium

### US-005: Emergency override for clinician access
**Persona:** ST-03 (Administrator)  
**Priority:** Medium

## Design Needs (for hand‑off to Design phase)

1. **Field‑Level Encryption Specification** – Algorithm AES‑256‑GCM, key rotation every 90 days, keys stored in HashiCorp Vault, per‑field key derivation using HKDF with field identifier as info.
2. **Role‑Based UI Component Library** – Components expose `requiredRoles` attribute; front‑end framework hides/shows based on JWT claims (`front_desk`, `clinician`, `admin`).
3. **Immutable Audit Log Contract** – Schema `{ timestamp, user_id, action_type, patient_id?, outcome, details }`; stored in append‑only table on PostgreSQL with `pg_audit` extension; retention 6 years.
4. **PDF Watermark & Timestamp Specification** – Text format `"Confidential – StaffID: {staff_id} – Exported: {ISO8601}"`; centered diagonal placement; font size 10pt; color #555555 meeting WCAG AA contrast.
5. **Docker Compose Security Profile** – Internal network `intake_net`; encrypted volume `/data` mounted read‑only for services; secrets injected via Docker secrets; air‑gap checklist included.
6. **Error Handling & Messaging Guidelines** – Generic error codes `ERR_VALIDATION`, `ERR_AUTH`, `ERR_EXPORT`; user‑friendly messages without PHI.
7. **Compliance Traceability Matrix**

| Requirement ID | Description                                 | Linked User Story(s) / AC(s)                               |
|---------------|---------------------------------------------|------------------------------------------------------------|
| FR-001       | Secure demographic capture                 | US‑001 (AC‑001…)                                          |
| FR-002       | Role‑based access control for clinicians   | US‑002 (AC‑004…)                                          |
| FR-003       | Audit logging of all access events          | US‑002 (AC‑004), US‑003 (AC‑007…)                        |
| FR‑004       | Automated unit & integration tests for validation & encryption | — |
| FR‑005       | PDF Intake Summary Generation compliance    | US‑004 (AC‑009…)                                          |
| FR‑006       | Watermark & timestamp on PDFs              | US‑004 (AC‑009)                                           |
| NFR‑001      | Response time <200 ms for form submissions | US‑001 (AC‑001)                                           |
| NFR‑003      | Audit log immutability & retention         | US‑002, US‑003                                            |
| KPI‑01       | Response time compliance                  | US‑001                                                    |
| RISK‑01      | Unauthorized data exposure                | Mitigated by encryption & access controls                |
| RISK‑02      | Open-source component vulnerabilities    | Managed via dependency scanning                         |

## Personas Definition

| Persona ID | Role Name        | Description                                 |
|------------|------------------|---------------------------------------------|
| ST-01     | Front Desk Clerk| Captures patient intake data at reception desk.| 
| ST-02     | Clinician        | Provides care and accesses patient records.| 
| ST-03     | Administrator    | Manages system configuration and overrides.| 
| ST-04     | Compliance Officer| Oversees regulatory compliance activities.|
# Access Control User Stories
                
# Personas
## Admin (ST-001)
System administrator responsible for managing user accounts, configuring role permissions, and reviewing audit logs.

## Clinician (ST-002)
Healthcare provider who reviews patient intake forms, accesses medical history, and generates PDF summaries.

## Front Desk Staff (ST-003)
Reception personnel who captures patient demographics, insurance information, and initial medical history via the web form.

# Design Needs (for Design Phase)
1. **Role Definition Specification** – Precise enumeration of permissions per role (create/read/update/delete) for intake records and audit logs.
2. **Authentication & MFA Flow** – Details on supported MFA methods (TOTP, hardware token) and session timeout values.
3. **Audit Log Schema** – Immutable log entry fields: `log_id`, `user_id`, `action`, `resource_id`, `timestamp`, `hash`. Include hashing algorithm (SHA‑256) and storage retention policy.
4. **Encryption Requirements** – Client‑side encryption algorithm (AES‑256‑GCM), key management approach (derived per session via TLS), and at‑rest encryption details for PostgreSQL columns.
5. **PDF Generation Constraints** – Open‑source tool (`wkhtmltopdf`) configuration for watermark overlay, timestamp footer format (`YYYY-MM-DD HH:mm:ss UTC`), and encrypted temporary storage path.
6. **Error Handling & Logging** – Standardized error messages for authentication failures, permission denials, and service outages; logging levels for security events.
7. **Performance Metrics** – Maximum acceptable latency for form submission (<200 ms) and PDF generation (<1 s) as per **NFR‑001**.

# Acceptance Criteria
| ID | User Story | Given | When | Then |
|----|------------|-------|------|------|
| **AC-001** | US-001 | The Front Desk Staff is authenticated with a valid username/password and has the Front‑Desk role. The web form is loaded over TLS 1.3. | The staff submits the form with all required fields populated and clicks **Submit**. | Each field value is encrypted at rest using field‑level encryption (AES‑256‑GCM) before being persisted to PostgreSQL; a successful write returns HTTP 201 and a corresponding audit‑log entry is created with timestamp, user ID, and operation type **CREATE**. |
| | | **Failure 1**: If any required field is missing → HTTP 400 with clear validation message; no data stored; no audit entry created. | **Failure 2**: If TLS handshake fails → submission blocked; error page shown; no encryption occurs. |
| **AC-002** | US-001 | The Front Desk Staff has entered invalid data (e.g., malformed insurance number). | The staff attempts to submit the form. | System rejects the request with HTTP 422 and displays field‑specific error messages; no partial data written; no audit entry generated. |
| | | **Edge**: Network interruption after client encrypts but before server receipt → client‑side timeout; no server record or audit entry created. |
| **AC-003** | US-002 | A Clinician is authenticated with a valid token and holds the Clinician role; the patient record exists and is encrypted at rest. | The Clinician requests to view the patient's intake record via the UI. | System decrypts the fields in memory only for the duration of the request, returns the data over TLS 1.3, and creates an audit‑log entry with operation type **READ**, user ID, patient ID, and timestamp. |
| | | **Failure**: Clinician accesses a record belonging to another clinic unit without permission → HTTP 403; audit entry with operation **READ‑DENIED** recorded. |
| **AC-004** | US-002 | The Clinician's session token has expired. | The Clinician clicks **View Record**. | System redirects to the login page (HTTP 302) and does not create any audit entry for the protected data access attempt. |
| | | **Edge**: Repeated expired‑token attempts generate a rate‑limit warning in the audit log. |
| **AC-005** | US-003 | An Admin is authenticated with the Admin role; the system contains existing role assignments and an audit log table. | The Admin adds a new user with role Clinician or modifies an existing role assignment, then saves changes. | The role change is persisted atomically; an audit‑log entry of type **ROLE‑CHANGE** records admin ID, target user ID, old role, new role, and timestamp. All changes are reflected immediately in access checks. |
| | | **Failure**: Admin attempts to assign an undefined role (e.g., "SuperUser") → HTTP 400 error; no audit entry for role change created but an audit entry of type **ROLE‑CHANGE‑FAILED** records the attempt. |
| **AC-006** | US-003 | The Admin requests to export the full audit log for a given date range. | The Admin clicks **Export Audit Log**. | System generates a CSV file containing all entries for the range; each row includes timestamp, user ID, operation type, affected record ID. The exported file is watermarked with "Confidential – Audit Export" and includes an export timestamp in the footer. An audit‑log entry of type **EXPORT‑AUDIT** records admin ID, file hash, and timestamp. |
| | | **Failure**: Date range yields >10 000 rows (performance threshold) → system prompts to narrow range; no export file generated; audit entry **EXPORT‑FAILED** recorded. |

# API Contract Summary (added per reviewer feedback)
| Endpoint | Method | Auth Required? | Request Body / Parameters | Success Response | Failure Responses |
|----------|--------|------------------|--------------------------|-------------------|-------------------|
| `/api/v1/intake` | POST | Yes (Front‑Desk token) | JSON payload with patient demographics & insurance fields (all required). Fields are encrypted client‑side before transmission. | HTTP 201 Created + record ID. |
| `/api/v1/intake/{id}` | GET | Yes (Clinician or Admin token) | Path param `id` = patient record identifier. |
| `/api/v1/intake/{id}` | PUT | Yes (Admin token) | JSON payload with updated fields (only allowed for Admin). |
| `/api/v1/intake/{id}` | DELETE | Yes (Admin token) | — |
| `/api/v1/audit/export` | GET | Yes (Admin token) | Query params `start_date`, `end_date` (ISO 8601). Optional `max_rows` default 10 000. |
| `/api/v1/auth/login` | POST | No | `{ "username": "...", "password": "...", "mfa_token": "..." }` |

# Prioritized User Story Table
| ID | Persona | Description | Business Value / KPI Alignment | MVP Priority |
|----|---------|-------------|---------------------------------|---------------|
| US-001 | Front‑Desk Clerk (ST-003) | Create a new patient intake record via the encrypted web form | Satisfies **FR‑001** (secure demographic capture) & **NFR‑003** (audit logging). Aligns with **KPI-001** (response time <200 ms). | 1 |
| US-002 | Clinician (ST-002) | View a patient's completed intake record and PDF summary | Enables care delivery; ties to **FR‑002**, **KPI-003** (audit log generation). | 2 |
| US-003 | Admin (ST-001) | Configure role‑based permissions and audit‑log retention policies | Ensures least‑privilege access; mitigates **RISK-001**, **RISK-003**. Aligns with **KPI-002** (system uptime). | 1 |
| US-004 | Front‑Desk Clerk (ST-003) | Edit a patient's demographic fields before submission is finalized | Reduces downstream correction cost; supports data quality. Aligns with **KPI-005** (test coverage targets). | 3 |
| US-005 | Clinician (ST-002) | Export a PDF intake summary with watermark and timestamp | Provides legally‑trackable document; fulfills **FR‑005**, **KPI-004** (PDF export security compliance). |

# Backlog Prioritization Rationale
1. **Core Data Capture (US-001)** – Highest priority because without a secure intake form the system cannot collect PHI; directly satisfies **FR‑001**, **NFR‑003**, and performance target **NFR‑001**.
2. **Admin Permission Management (US-003)** – Required early to enforce least‑privilege access; mitigates **RISK-001** (unauthorized data exposure) and **RISK-003** (audit log gaps).
3. **Clinician Record Access (US-002)** – Enables care delivery; ties to **FR‑002**, **KPI-003**.
4. **PDF Export (US-005)** – Provides legally‑trackable hand‑off; fulfills **FR‑005**, **KPI-004**.
5. **Front‑Desk Edit (US-004)** – Valuable but lower priority; can be deferred to post‑MVP iteration.

# Risk Mitigation Summary
* **RISK-001** mitigated by strict RBAC enforced at UI and service layers.
* **RISK-002** addressed by using only vetted open‑source libraries listed in the dependency manifest.
* **RISK-003** covered by immutable append‑only audit log with daily rotation.

# Overview
The following user stories define the login and data‑access flows for each role in the PatientIntake system. They are scoped to the product phase and focus exclusively on access‑control behavior, audit‑log verification, and security edge cases required for HIPAA compliance.

# Priority Rationale
* High priority stories (**US‑001**, **US‑002**) enable core intake workflow; without secure login and record access the system cannot capture PHI.
* Medium priority story (**US‑003**) supports governance and auditability required for regulatory compliance but can be iteratively enhanced after MVP launch.

All user stories are traceable to functional requirements **FR‑001 – FR‑003**, non‑functional requirement **NFR‑003**, and KPIs **KPI-001 – KPI-004**, as well as risks **RISK-001 – RISK-003**.
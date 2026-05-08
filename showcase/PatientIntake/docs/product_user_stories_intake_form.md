# Patient Intake Form User Stories (Overview)

## Personas for Patient Intake Form (HIPAA‑Compliant)

### 1. Patient (Primary Data Subject)
- Role: Individual seeking care at the clinic.
- Goals:
  1. Provide accurate demographic, insurance, and medical‑history information quickly.
  2. Trust that the information entered is protected in transit (TLS 1.2 + and at rest with AES‑256) and will not be disclosed without authorization.
- Pain Points:
  - Uncertainty about data handling can cause reluctance to share sensitive health details.
  - Complex forms may lead to incomplete or erroneous submissions.
- HIPAA Considerations:
  - Must give informed consent before data capture (FR‑001).
  - Data entry must be logged (AU‑6) and encrypted per 45 CFR §164.312(e)(1).
- Success Metrics:
  - ≥ 95 % of patients complete the form without validation errors.
  - No reported privacy‑concern incidents during the first 30 days (KPI‑002).

### 2. Front Desk Clerk (Data Collector)
- Role: Clinic staff who assists patients in completing the intake form and verifies submission integrity.
- Goals:
  1. Guide patients through the web form efficiently.
  2. Ensure that each submission is stored with correct role‑based access control (admin, clinician, front‑desk) as defined in FR‑002.
- Pain Points:
  - Need to balance speed of intake with verification of required fields.
  - Must avoid accidental exposure of PHI when assisting patients.
  - Must authenticate using multi‑factor login; session must be encrypted (TLS 1.3 preferred).
- Controls:
  - All read/write actions are recorded in an immutable audit log (AU‑6, FR‑004).
- Metrics:
  - Average form‑completion time ≤ 3 minutes per patient.
  - Zero unauthorized read events recorded in audit logs during pilot (KPI‑001).

### 3. Clinician (Care Provider)
- Role: Authorized medical professional who reviews submitted intake data and generates PDF summaries.
- Goals:
  1. Access complete, accurate patient information to make clinical decisions.
  2. Export a PDF intake summary with watermark and timestamp visible only to authorized staff (FR‑004).
- Pain Points:
  - Need assurance that data has not been tampered with between entry and review.
  - Must quickly locate patient records without navigating complex UI.
- Controls:
  - Access limited to role‑based permissions; audit log captures every view (AU‑6).
  - PDF export embeds a cryptographic hash to verify integrity (FR‑004).
- Metrics:
  - Clinician can retrieve a patient's full record within ≤ 5 seconds.
  - All exported PDFs contain correct watermark and timestamp; verification passes in ≥ 99 % of cases.

## Cross‑Persona Security Controls
| Control                | Specification  | Applied To |
|------------------------|--------------------|------------|
| Transport Encryption   | TLS 1.2 + with forward secrecy (TLS 1.3 preferred)      | All roles |
| At‑Rest Encryption     | AES‑256 per‑field encryption                           | Patient data fields |
| Role‑Based Access Control (RBAC) | Admin > Clinician > Front Desk permissions defined in FR‑002 | All roles |
| Immutable Audit Logging| Append‑only log with digital signatures, event types “CREATE”, “READ”, “EXPORT_PDF”, etc.| All read/write actions |
| PDF Watermark & Timestamp| Visible only to authorized staff; ISO 8601 timestamp   | Clinician |

## User Stories
| ID     | Persona          | Narrative | Value |
|--------|------------------|------------|-------------|
| US-001 | Patient          | Enter my personal demographics, insurance information, and medical history into a structured web form      | My health record is complete and ready for clinical review while complying with HIPAA requirements   |
| US-002 | Front Desk Clerk | Submit a new patient intake form on behalf of a walk‑in patient and receive confirmation that data was encrypted at rest | The clinic can capture data quickly without compromising security  |
| US-003 | Clinician       | Retrieve a PDF summary of a patient's intake data with a visible watermark and export timestamp       | I can review the patient's information securely and verify when the document was generated               |
| US-004 | Admin            | Configure role‑based access permissions for the intake system and view an immutable audit log of all reads and writes | System access follows the principle of least privilege and any suspicious activity is traceable        |

**Priority Ranking**
* US-001 – Critical (satisfies FR‑001 & FR‑002)
* US-002 – High (supports FR‑001 for front‑desk efficiency)
* US-003 – High (fulfills FR‑004 – secure PDF generation)
* US-004 – Medium (addresses FR‑002 & FR‑005 – RBAC & audit logging)

## Acceptance Criteria

#### EC1
* **Given** the TLS connection is interrupted before submission
* **When** the patient clicks submit but the request fails due to network loss
* **Then** the client shows a retry prompt; no partial data is persisted; no audit entry is created.

#### EC2
* **Given** the encryption library fails to generate a key pair (simulated error)
* **When** the patient attempts to submit the form
* **Then** the system returns error “Encryption failed, please try again later”; no data is stored; audit log records **ENCRYPTION_ERROR** event.

### AC-002 – US-002
* **Given** a front desk clerk authenticated with role “front_desk” and an intake record exists with encrypted fields
* **When** the clerk selects “Export PDF” for that record
* **Then** the system decrypts data server‑side, generates a PDF/A‑2b file, adds watermark “Confidential – Authorized Staff Only” and ISO 8601 export timestamp, offers the file for download, and records an **EXPORT_PDF** audit entry with user ID and timestamp.

## SaaS Domain Constraints
* Multi‑tenant isolation: each tenant’s intake data resides in separate logical schema; RBAC rules are scoped per tenant.
+ Horizontal scalability: stateless front‐end services behind load balancer; database sharding based on tenant ID.
+ High availability: target 99.9% uptime; automated failover for encryption key management service.
+ Disaster recovery: daily encrypted backups retained ≥ 30 days; restore time objective ≤ 4 hours.

## Feature Specification: Secure Patient Intake & Audit Logging (SaaS)

### Context
This feature supports the HIPAA‑compliant patient intake SaaS application, deployed in a multi‑tenant cloud environment with high availability and horizontal scalability requirements.

### Requirements Traceability
| Requirement ID | Description |
|---|---|
| FR-001 | Secure patient data capture via encrypted HTTPS form |
| FR-002 | All data transmissions shall use TLS 1.2+ |
| FR-004 | Audit logging of all read/write actions |
| FR-005 | PDF generation with watermark and timestamp |
| NFR-004 | Audit trail retention 7 years |
| KPI-007 | Audit log write latency ≤ 200 ms under 10 M rows |

#### US-004 – Admin Updates RBAC & Audit Retention
**Persona:** Admin (role `admin`)  
**Given** the admin is authenticated on the system settings page  
**When** the admin modifies the RBAC matrix or changes the audit log retention period and clicks **Save**  
**Then** the system:
1. Validates configuration against policy constraints (e.g., no privilege escalation, retention ≥ 7 years per NFR‑004).
2. Persists the new settings in the configuration store.
3. Writes an audit log entry (`event_type=CONFIG_CHANGE`, `actor=admin`, `outcome_status=SUCCESS`, `audit_reference=AU‑6`).
4. Returns a success toast confirming the update.

*Edge Cases:* Invalid RBAC rule (e.g., granting admin rights to front desk) → reject with explanatory error; Retention period below regulatory minimum → reject with compliance warning; Save failure → rollback and admin notification.

### Design Details for Downstream Phases
- **Client‑side Encryption Library:** OpenPGP.js **v5.x**, used to encrypt form payload before transmission.
- **Server‑side Key Management:** Automated rotation via **cert-manager**, keys stored in Vault with audit‑ready access logs.
- **PostgreSQL Row‑Level Security Policies:** Policies map roles (`front_desk`, `clinician`, `admin`) to column visibility; see `policy_rls.sql`.
- **PDF Generation Requirements:** wkhtmltopdf **v0.12.6**, PDF/A‑2b compliance, watermark text parameter configurable, timestamp metadata field required.
- **Audit Log Schema:** `event_type`, `user_id`, `patient_id`, `timestamp`, `outcome_status`, `error_code` (optional), `audit_reference`.

### Performance KPI
| KPI ID | Description | Target |
|---|---|---|
| KPI‑007 | Audit log write latency under load (10 M rows) | ≤ 200 ms per entry |

### Traceability Matrix
| User Story | Requirement(s) |
|---|---|
| US‑001 | FR‑001, FR‑002 |
| US‑002 | FR‑001, FR‑004 |
| US‑003 | FR‑004, FR‑005 |
| US‑004 | FR‑004, FR‑005, NFR‑004 |

*All acceptance criteria are testable and traceable to the listed functional requirements.*
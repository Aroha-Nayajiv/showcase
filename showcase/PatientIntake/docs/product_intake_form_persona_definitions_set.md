# Intake System Persona Definitions
                
## Personas
| ID | Role | Description | Needs | Constraints |
|---|---|---|---|---|
| PER-01 | Front Desk Clerk (ST-001) | Staff member who receives patients and initiates the intake process on a secured workstation within the clinic network. | Capture accurate demographic and insurance data; start the medical history form; ensure data is saved without delay. | Must not view protected health information (PHI) beyond what is required for intake; must ensure TLS‑1.3 for data in transit and field‑level encryption at rest (45 CFR 164.312(a)(2)(iv)). |
| PER-02 | Clinician (ST-002) Licensed medical professional who reviews completed intake forms, adds clinical notes, and signs off on the PDF summary. |
 Verify completeness of patient‑provided data; add clinical observations; approve PDF export for treatment planning. |
 | Requires role‑based access to PHI; actions must be logged immutably (45 CFR 164.308(a)(1)(ii)). |
| PER-03 Patient (ST-003) |
 Individual seeking care who fills out the web‑based intake form on a personal device or clinic kiosk. |
 Provide accurate personal, insurance, and medical history information; receive confirmation that data was securely received. |
 | Must be assured that each field is encrypted at rest; consent capture required before submission (45 CFR 164.508). |

## Design Needs
### Field‑Level Encryption Specification
- **Algorithm:** AES‑256‑GCM  
- **Key Management:** Per‑field keys derived from a master key stored in a Hardware Security Module (HSM).  
- **Client‑side Library:** Web Crypto API integrated into the intake form JavaScript.

### Audit Log Format
Immutable JSON entries containing:
`event_id`, `timestamp`, `user_id`, `role`, `action`, `resource_id`, `outcome`.
Logs are written once to PostgreSQL `audit_log` table with an append‑only policy.

### PDF Generation Contract
- **Watermark Text Pattern:** "Confidential – {{staff_name}} – {{date}}"  
- **Timestamp Format:** ISO 8601 (`YYYY-MM-DDThh:mm:ssZ`)  
- **Signing Method:** Placeholder for future digital signature integration.  
- **Storage Location:** `/secure/pdfs/` with bucket‑level encryption enabled.

### Role‑Based Access Control Matrix
| Role | intake_record | pdf_summary |
|------|--------------|------------|
| front_desk | Create, Read (restricted fields) | No access |
| clinician   | Read, Update (allowed fields)   | Create, Read |
| admin        | Full CRUD                     | Full CRUD |

### Error Handling & Graceful Degradation
UI messages for:
- Encryption failures (`"Encryption service unavailable"`).  
- Missing MRN (`"Medical Record Number is required"`).  
- Permission denials (`"Access denied"`).  
Each error triggers an audit entry.

## User Stories
| ID | As a | I want | So that |
|----|------|--------|---------|
| US-001 | Front Desk Clerk | capture patient demographics, insurance details, and consent for data processing via a structured web form | the system stores protected health information (PHI) securely and complies with HIPAA §164.312(a)(2)(iv) encryption requirements |
| US-002 | Clinician | retrieve a patient's completed intake record and generate a PDF summary with a staff watermark and timestamp | I can review accurate medical history while maintaining auditability and evidencing who accessed the data |
| US-003 | Administrator | configure role‑based access controls and view an immutable audit log of all CRUD actions on intake records | the organization can demonstrate compliance during HIPAA audits and quickly detect unauthorized activity |

### Traceability Matrix
| User Story | Linked Functional Requirement(s) |
|-----------|----------------------------------|
| US-001    | FR-001: Secure demographic capture |
| US-002    | FR-002: Clinician review & PDF generation |
| US-003    | FR-003: Admin RBAC configuration & audit logging |

## Acceptance Criteria
### AC‑005 – US‑003 (Admin PDF Generation)
**Given** an Admin authenticated with the `admin` role selects **Generate PDF** for a fully encrypted patient record,
**When** generation succeeds,
**Then** the system compiles decrypted data into a PDF via wkhtmltopdf, applies watermark "Confidential – {{staff_name}} – {{date}}", stores the file in `/secure/pdfs/`, provides a download link, and creates audit entry **AU‑005** recording generation event, staff ID, timestamp, and PDF checksum.
*Permission denial:* If admin lacks patient access → UI shows "Access denied"; audit entry **AU‑006** recorded.
*Engine failure:* Missing wkhtmltopdf binary → UI shows "PDF engine unavailable"; no PDF created; no audit entry for failed attempt.

## Audit ID Definitions
| Audit ID | Description |
|----------|-------------|
| AU‑001   | Successful intake form submission with encrypted storage |
| AU‑002   | Insecure transport attempt blocked |
| AU\-003   | Record read action by Clinician | s| AU\-004   | Clinician edit persisted | s| AU\-005   | PDF generation completed | s| AU\-006   | Unauthorized PDF generation attempt | s| AU\-007   | PDF export interrupted due to network failure s |
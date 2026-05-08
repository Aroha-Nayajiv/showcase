# Role-Based Access Control Specification

### Personas
- **Patient** – The individual whose protected health information (PHI) is collected via the intake form. Interacts anonymously until staff authentication.
- **Front Desk Clerk** – Staff member responsible for initial data capture, verification of demographics and insurance details, and correction of entry errors before clinical review.
- **Clinician** – Licensed healthcare provider who needs full access to medical history, the ability to generate a PDF intake summary, and to view audit trails for compliance verification.
- **Admin** – System administrator who configures role hierarchies, assigns users to roles, and monitors audit logs to satisfy HIPAA technical safeguard requirements.

### User Stories
| ID   | Role               | Description  | Priority |
|------|--------------------|---------------------------|----------|
| US-001 | Patient            | As a patient, I want to securely enter my demographics, insurance information, and medical history into a structured web form so that my personal health data is protected in transit and at rest, complying with HIPAA requirements.                     | 1 |
| US-002 | Front Desk Clerk   | As a front‑desk clerk, I want to create a new intake record for a patient and edit non‑clinical fields (e.g., contact info) so that I can capture accurate patient data while the system encrypts each field at rest and logs the operation.               | 2 |
| US-003 | Clinician          | As a clinician, I want to view and update a patient's medical history and insurance details after authentication so that I can provide appropriate care while ensuring only authorized changes are recorded and auditable.                     | 1 |
| US-004 | Admin              | As an admin, I want to define role permissions and assign users to roles (admin, clinician, front‑desk) and view the complete audit log of all CRUD actions so that I can enforce least‑privilege and maintain a tamper‑evident trail for compliance audits.| 1 |
| US-005 | Clinician          | As a clinician, I want to export a patient’s intake record as a PDF with a confidentiality watermark and signed timestamp so that the document can be shared securely with authorized staff.| 1 |

### Acceptance Criteria
| ID      | Linked User Story | Given  | When| Then  |
|---------|----------|------------------|
| AC-001  | US-001            | The Front Desk Clerk is authenticated with the `front_desk` role and the intake form is loaded. | The clerk fills all required fields and clicks **Submit**.                           | The system encrypts each field using AES‑256‑GCM at rest, stores the record in PostgreSQL, and creates an audit log entry `action=CREATE`, `actor=front_desk`, `timestamp`, `success=true`. If any required field is missing, the UI shows inline validation errors and no record is persisted; no audit entry is created. |
| AC-002  | US-001            | The clerk has entered data that includes PHI (e.g., SSN).| The clerk attempts to submit over an insecure network (HTTP).                        | Submission is blocked; the browser displays “Connection not secure – TLS 1.2+ required”. No data is transmitted or stored. If TLS handshake fails, the system logs a security event with `severity=high`. |
| AC-003  | US-002            > A Clinician is authenticated with the `clinician` role and requests a patient record via the UI. The clinician clicks **View Record** for patient ID 12345. The system verifies role permission, decrypts the record in memory, presents it, writes an audit entry `action=READ`, `actor=clinician`, `patient_id=12345`, `timestamp`. If unauthorized access attempted, returns HTTP 403 Forbidden, logs `action=READ_DENIED`. |

### Design Needs (for downstream Design phase)
1. **Permission Matrix Specification** – JSON contract describing each role (`admin`, `clinician`, `front_desk`) and allowed CRUD operations on resources `patient_intake`, `audit_log`, `role_definition`. Includes multi‑tenant isolation flags per tenant.
2. **Audit Log Schema** – Fields: `action`, `actor_role`, `actor_id`, `resource_type`, `resource_id`, `timestamp`, `outcome`, `details`.
3. **Encryption Requirements** – At‑rest encryption algorithm AES‑256‑GCM; key rotation policy every 90 days; TLS 1.2+ for all inbound/outbound traffic.
4. **PDF Export Controls** – Must use open‑source wkhtmltopdf supporting watermarking; PDF must be signed with an internal X.509 certificate; exported files stored in an encrypted temporary directory that auto‑purges after 5 minutes.
5. **Error Handling Hooks** – UI surfaces validation errors inline; backend returns standardized error codes (`400_BAD_REQUEST`, `403_FORBIDDEN`, `500_INTERNAL_ERROR`) with correlation IDs for audit traceability.
6. **Multi‑Tenant Isolation** – All data partitions must be isolated per tenant using row‑level security in PostgreSQL; audit logs include tenant identifier; encryption keys are tenant‑scoped.

### Traceability Matrix
| Requirement ID | Description |
|----------------|-------------|
| FR‑001         | Secure collection of PHI via web form |
| FR‑002         | All data transmissions shall use TLS |
| FR‑003         |​Transport Encryption |
| FR‑004         |​Generate PDF intake summary with watermark and export timestamp visible only to authorized staff |
| FR‑005         |​Deploy entire stack via Docker Compose |
| NFR‑002        |​Certificate rotation shall be automated |
| NFR‑003        |​AES‑256 encryption at rest and TLS 1.2+ in transit |
| KPI‑001        |​System availability ≥ 99.9 % |
| KPI‑002        |​Zero security incidents in first 90 days |
| KPI‑003        |​Compliance audit passed |

*All user stories and acceptance criteria map directly to the above functional requirements (FR‑001 – FR‑005) ensuring HIPAA technical safeguard compliance.*
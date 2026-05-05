# User Stories for Patient Intake Form (Overview)

# Priority Ranking & Business Justification

| ID   | Rank | Justification |
|------|------|----------------|
| US-001 | 1 | Accurate demographic capture is foundational for any clinical workflow and required by HIPAA for proper identification. |
| US-002 | 2 | Insurance information drives revenue cycle; secure handling prevents fraud and complies with payer regulations. |
| US-003 | 3 | Medical history directly impacts patient safety; confidentiality is mandated by HIPAA. |
| US-004 | 4 | Front Desk entry is the primary data source; encryption at rest/in‑transit satisfies technical safeguard requirements. |
| US-005 | 5 | Clinician access must be auditable to support clinical decision making and compliance audits. |
| US-006 | 6 | PDF export provides legal documentation; watermarking/timestamp ensures tamper evidence for audits. |

## Prioritized Backlog for Patient Intake Form (Overview)

### 1. User Stories (ordered by MVP priority)

| ID   | Persona            | Goal / Action                                                                                                   | Benefit / Reasoning                                                                                                   | MVP Rank |
|------|--------------------|------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|----------|
| US-001 | Front Desk Clerk | Enter patient demographic data, insurance information, and medical history into a structured web form               | The clinic has accurate, HIPAA‑compliant records for billing and clinical care                                         | 1 (MVP) |
| US-002 | Clinician          | Retrieve a patient's submitted intake record and view a PDF summary with a watermark and access timestamp          | Enables informed treatment decisions while ensuring record integrity and auditability                                      | 2 |
| US-003 | Admin              | Configure role‑based access controls and generate audit‑log reports for all read/write operations on intake data   | Provides compliance reporting required for HIPAA technical safeguards and regulatory audits                               | 3 |
| US-004 | Front Desk Clerk   | Receive validation feedback when required fields are missing or contain invalid formats                              | Reduces re‑work and improves data quality                                                                            | 4 |
| US-005 | Compliance Officer| Export a tamper‑evident PDF intake summary that includes a staff watermark and exact export timestamp      | Enables audit verification of who accessed the record and when                                                       | 5 |

### 2. Traceability to Functional Requirements

| User Story ID | Linked Functional Requirement(s) |
|---------------|-----------------------------------|
| US-001        | FR-001 (Demographic capture), FR-002 (Insurance capture), FR-003 (Medical history capture) |
| US-002        | FR-004 (PDF generation), FR-006 (Watermark & Timestamp) |
| US-003        | FR-005 (Audit log generation), FR-007 (RBAC matrix) |
| US-004        | FR-008 (Field validation feedback) |
| US-005        | FR-009 (Tamper‑evident PDF export) |

### 3. MVP Scope Definition

The Minimum Viable Product consists of **US‑001**, **US‑002**, and **US‑003** together with their primary acceptance criteria (**AC‑001** through **AC‑007**). These three stories satisfy the essential regulatory requirement (HIPAA encrypted storage & audit), provide immediate clinical utility (PDF summary), and enable compliance reporting (role‑based access & audit logs). Stories **US‑004** and **US‑005** are deferred to post‑MVP releases but remain in the backlog for future sprints.

---

## Acceptance Criteria Table (Given/When/Then)

### AC‑001 – US‑001: Secure Demographic Capture

Given a Front Desk Clerk is authenticated with a valid session
When the clerk submits the demographic form with all required fields filled correctly
Then the system stores each field encrypted at rest using AES‑256‑GCM
And logs a CREATE event with timestamp, user ID, and record ID
And returns a success confirmation to the UI.

*Traceability*: FR‑001, FR‑002, FR‑003.

### AC‑002 – US‑001: Idempotent Submission on Network Failure

Given the clerk has an active session but the network drops after form submission
When the clerk retries the submission using the same idempotency token
Then the system detects the duplicate and does not create a second record
And logs a RETRY event linked to the original transaction.

*Traceability*: FR‑001.

### AC‑004 – US‑002: TLS Handshake Failure Handling

Given the client attempts to submit data over an insecure channel
When the TLS handshake fails or is downgraded
Then the system aborts transmission, displays "Secure connection required"
And logs a FAILED_TLS event without persisting any data.

*Traceability*: NFR‑001 (response time & security).

### AC‑005 – US‑003: PDF Summary Generation (Authorized Access)

Given a Clinician with role "Clinician" is logged in and selects an existing patient record
When they click "Generate PDF Summary"
Then the system creates a PDF/A‑2b document using wkhtmltopdf,
    embeds watermark text "Confidential – {Clinician Name}" and ISO‑8601 timestamp,
    stores the PDF encrypted at rest,
    and logs a GENERATE event.

*Traceability*: FR‑004, FR‑006.

### AC‑007 – US‑003: PDF Generation Failure Recovery

Given the PDF generation service fails due to missing font resources
When the Clinician retries the operation up to three times
Then after each failure the system returns error code 50002 and message "PDF generation failed – contact IT"
And logs a GENERATE_FAILURE event.
If failures exceed three attempts, an alert is sent to the Operations team.

*Traceability*: FR‑009.

### AC‑009 – US‑005: Tamper‑Evident PDF Export for Audits

Given a Compliance Officer selects "Export Intake Summary"
When the export is performed
Then the generated PDF includes:
    • A persistent watermark "Confidential – {Officer Name}"
    • An ISO‑8601 timestamp embedded in metadata,
    • A cryptographic hash of the underlying record stored in the PDF metadata,
And the PDF file is stored encrypted at rest.
And an EXPORT event is logged with hash verification status.

*Traceability*: FR‑009, NFR‑003.

---

## Design Needs (Reference Only – Not Part of Product Artifact)
*(Retained for downstream design teams; unchanged from original specification.)*
1. **Field‑Level Encryption Specification** – AES‑256‑GCM, per‑field keys derived from master key in HSM, unique IV per record.
2. **Audit Log Format** – Immutable append‑only JSON Lines entries with fields `timestamp`, `actor_id`, `operation`, `record_id`, `hash`; RSA‑2048 signature; retention ≥ 7 years.
3. **PDF Generation Contract** – Input JSON schema, watermark pattern `Confidential – {staff_name}`, timestamp ISO‑8601, output PDF/A‑2b; error codes defined for generation failures.
4. **Access Control Matrix** – Map roles (Front Desk, Clinician, Admin) to CRUD permissions on intake records and PDF export capability; enforced server side.
5. **Validation Rules** – Enumerated regexes, length limits, cross‑field dependencies; UI error messaging guidelines provided.
6. **Failure Handling Guidelines** – Standardized error response schema `{code, message, detail}` for encryption failures, validation errors, unauthorized access, service outages.
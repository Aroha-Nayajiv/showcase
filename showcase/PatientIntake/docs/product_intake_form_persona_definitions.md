# Persona Definitions for Intake System (Overview)

## Persona Definitions for Patient Intake System (Overview)

The following personas capture the primary human actors who will interact with the PatientIntake system. They are derived directly from the project requirements (collect demographics, secure storage, audit logging, PDF export) and the stakeholder list (ST-001 Clinical staff, ST-002 Patients, ST-003 Compliance officer). Each persona includes role‑specific goals, motivations, constraints, and security considerations that inform downstream design and testing.

### PER-02: Front‑Desk Staff (Receptionist / Registration Clerk)
1. **Role Summary**: Administrative personnel responsible for initial patient registration, data entry of demographics and insurance details, and initiating PDF intake summaries for authorized staff.
2. **Primary Goals**
   - Accurately enter required fields with validation feedback to reduce data entry errors (<1 % error rate – KPI-004).
   - Generate a PDF intake summary that includes a watermark identifying the staff member and an access timestamp (FR‑005).
   - Initiate audit log entries for every create/read/write operation (AU‑6).
3. **Motivations**
   - Minimize re‑work caused by incomplete or incorrect submissions.
   - Demonstrate compliance during internal audits.
4. **Constraints**
   - Operates on shared terminals with limited privileges; cannot view clinical notes beyond what is required for registration.
   - Must follow a documented air‑gap setup guide; no external internet connectivity.
   - Uses field‑level encryption keys managed by the system; does not handle raw keys.
   - Session timeout after 10 minutes of inactivity to mitigate shoulder‑surfing risk.
   - Handling of validation failures (e.g., missing insurance number) must provide inline guidance without exposing PHI.
   - Need assurance that generated PDFs cannot be altered after export; watermark and timestamp must be immutable.
5. **Security Considerations**
   - Authentication via unique staff ID; MFA enforced per 45 CFR 164.312(a)(2)(iv).
   - All actions logged immutably (AU‑6) with hash chaining for integrity.

### PER-03: Compliance Officer (Auditor / HIPAA Officer)
1. **Role Summary**: Oversees regulatory compliance, conducts periodic audits of the intake system, and validates that security controls meet HIPAA technical safeguard requirements.
2. **Primary Goals**
   - Verify that every read/write operation is recorded in an immutable audit log (FR‑003, NFR‑003).
   - Confirm that field‑level encryption is applied consistently across all PHI fields (NFR‑001).
   - Review PDF export logs to ensure watermarks and timestamps are present for each export (FR‑005).
3. **Motivations**
   - Avoid penalties from non‑compliance; maintain organization’s certification status.
   - Provide evidence of compliance during external audits.
4. **Constraints**
   - Access limited to read‑only views of audit logs; cannot modify patient data.
   - Must operate within an air‑gapped environment; all audit data stored locally on PostgreSQL with row‑level security.
   - Requires multi‑factor authentication for login (45 CFR 164.312(a)(2)(iv)).
   - Audit log retention period of 7 years as per HIPAA retention policy.
   - Needs tooling to filter audit logs by user ID, operation type, and date range without exporting raw data.
5. **Security Considerations**
   - MFA enforced; session logs signed with digital signatures.
   - Log integrity checks (hash chaining) verifiable during audits.

---

### Personas Table
| Persona ID | Role | Description | Primary Needs | Constraints |
|-----------|------|-------------|----------------|--------------|
| PER-01 | Clinical Staff | Nurse / Clinician reviewing intake data | Reliable access to complete, accurate intake summary; assurance of data integrity and provenance | Works on secured workstations; role‑based access only |
| PER-02 | Front Desk Staff | Receptionist initiating registration | Fast data entry, validation assistance, ability to correct errors quickly | Cannot view full medical history; air‑gap environment |
| PER-03 | Compliance Officer | Auditor ensuring HIPAA compliance | Ability to query immutable audit logs, verify encryption compliance, generate compliance reports | Read‑only audit view; MFA required |
| PER-04 | Patient | Individual receiving care who provides personal and medical information via the web form | Simple and accessible UI, immediate feedback on submission status, privacy of health data | May use mobile device, limited technical expertise |

---

## User Stories

| Story ID | Actor | Goal | Acceptance Criteria Reference |
|----------|-------|------|-------------------------------|
| US-001 | Front Desk Staff | Capture patient demographics, insurance information, and medical history via a structured web form with field‑level encryption at rest and in transit | AC-001 |
| US-002 | Clinician | View a PDF intake summary for a patient that includes a watermark and an access timestamp | AC-002 |
| US-003 | Compliance Officer | Audit the operation log for every read and write operation on patient records | AC-003 |

---

## Acceptance Criteria

| AC ID | Story ID | Given | When | Then |
|-------|----------|-------|------|------|
| AC-001 | US-001 | The front‑desk staff member is authenticated via MFA and has an active session on a secured terminal. | They complete the web form with all mandatory fields filled correctly and submit it. | The system stores the data encrypted at rest and in transit, creates an immutable audit log entry (AU‑6) with user ID, timestamp, and operation type, and displays a success message within 2 seconds (KPI-001). |
| AC-002 | US-002 | The clinician is logged in with appropriate role‑based permissions and selects a patient record that has a completed intake form. | They request to generate the PDF intake summary. | The system produces a PDF that includes a visible watermark containing the clinician’s name and an access timestamp, stores the PDF securely, logs the generation event immutably (AU‑6), and the PDF cannot be altered without detection (NFR‑003). |
| AC-003 | US-003 | The compliance officer has read‑only access to the audit log database in the air‑gapped environment. | They apply a filter for a specific date range or user ID and request the audit report. | The system returns a filtered list of audit entries showing user ID, operation type, timestamp, and cryptographic hash chain verification passes; the report respects the 7‑year retention policy (NFR‑003) and no raw PHI is exposed. |

---

*All functional references map to existing asset IDs:* FR‑001 (Secure demographic capture), FR‑002 (Insurance verification), FR‑003 (Immutable audit logging), FR‑005 (PDF generation with watermark), NFR‑001 (Encryption at rest & transit), NFR‑003 (Audit log integrity), KPI-001 (Form submission response time <200 ms), KPI-004 (Data entry error rate <1 %).

# Acceptance Criteria Document
                
## Personas for the HIPAA‑Compliant Patient Intake System

The following personas are derived directly from the project brief and the asset registry (ST-01, ST-02, ST-03). They capture the distinct roles that will interact with the intake form, define their access privileges, and outline the security expectations required for HIPAA compliance.

### PER-01: Clinical Staff (Clinician)
- **Primary Goal:** Review and update patient medical history to provide appropriate care.
- **Key Interactions:**
  1. Access completed intake forms after submission.
  2. Add clinical notes or modify existing medical‑history fields.
  3. Generate a PDF summary for patient hand‑off.
- **Access Rights:** Read‑write on patient records; can export PDFs with watermark and timestamp.
- **HIPAA Controls:** Must authenticate via unique user ID (45 CFR 164.312(a)(2)(i)), and all read/write actions are logged (45 CFR 164.312(b)(1)).
- **Success Metrics:** <200 ms response time for record retrieval (KPI‑01) and 99.9 % audit‑log completeness (KPI‑02).

### PER-02: Front Desk Operator
- **Primary Goal:** Capture accurate demographic and insurance information at point of entry.
- **Key Interactions:**
  1. Fill out the structured web form with patient demographics and insurance data.
  2. Submit the form, triggering field‑level encryption at rest and in transit.
  3. Verify successful submission via on‑screen confirmation.
- **Access Rights:** Create‑only on new intake records; read‑only on previously submitted forms for verification purposes.
- **HIPAA Controls:** Must ensure encryption of each field using open‑source libraries (e.g., libsodium) before storage (45 CFR 164.312(a)(2)(iv)). All submissions generate an immutable audit entry (FR‑002).
- **Success Metrics:** Form submission latency <200 ms (KPI‑01) and 100 % of submissions encrypted at field level.

### PER-03: Compliance Officer (Auditor)
- **Primary Goal:** Verify that all intake activities comply with HIPAA technical safeguards and internal policies.
- **Key Interactions:**
  1. Review audit logs for every read/write operation.
  2. Validate that PDF exports contain required watermark and timestamp.
  3. Conduct periodic compliance reports.
- **Access Rights:** Read‑only on audit logs; can view but not modify any patient data or PDFs.
- **HIPAA Controls:** Must be able to produce evidence of audit‑log immutability (45 CFR 164.312(b)(1)) and verify encryption key management practices (45 CFR 164.312(a)(2)(iv)).
- **Success Metrics:** Audit‑log retention ≥180 days (NFR‑003) and zero unauthorized access incidents per reporting period.

### Summary Table
| Persona ID | Role | Primary Goal | Access Rights | Compliance Controls |
|-----------|------|--------------|--------------|----------------------|
| PER-01 | Clinical Staff | Review & update medical history | Read‑Write + PDF export | Authenticated access, audit logging |
| PER-02 | Front Desk Operator | Capture demographics & insurance | Create‑Only + verification | Field‑level encryption, audit entry |
| PER-03 | Compliance Officer | Audit compliance & generate reports | Read‑Only audit logs | Log immutability, key management |

These personas provide a concrete foundation for downstream design specifications, ensuring that every user interaction is traceable to a regulatory requirement and measurable KPI.

---

## User Stories & Acceptance Criteria

### US-003 – Compliance Officer – Generate & Verify PDF Intake Summary
**Goal:** Generate a PDF intake summary for any patient and verify that the PDF includes a watermark and an access timestamp, enabling auditability of export actions.

**Acceptance Criteria (Given/When/Then):**
1. **Given** the Compliance Officer is authenticated with role `compliance` and selects `Export PDF` for a patient record,
   **When** the system generates a PDF using wkhtmltopdf ≥ 0.12.6 from an HTML template populated with decrypted data,
   **Then** the PDF contains a semi‑transparent watermark "Confidential – Authorized Export" and a footer timestamp "Exported by [UserID] on YYYY‑MM‑DD HH:MM UTC", streams over HTTPS, and logs an `EXPORT` event in the audit log.
2. **Given** PDF generation fails due to an internal error,
   **When** the officer receives an error dialog,
   **Then** they are offered a retry option and the failure is recorded as `EXPORT_FAILURE` in the audit log.
3. **Given** an unauthorized export attempt occurs,
   **When** the system detects insufficient permissions,
   **Then** it returns HTTP 403, logs an `UNAUTHORIZED_EXPORT` event, and displays "Access denied" to the user.
4. **Given** an audit log review for a specific date range,
   **When** the Compliance Officer queries the audit UI with filters (user, operation type),
   **Then** the system returns a sortable table of matching entries meeting FR‑002/FR‑003 requirements, each entry showing immutable hash verification status; pagination limits results to ≤100 rows per page for performance.

---
# Note: The above markdown block ends here.
---

## Design Needs (Traceability & Technical Specifications)

| Design Element | Specification | Traceability |
|---------------|----------------|---------------|
| Encryption Mechanism | Field‑level AES‑256 keys derived from a master key stored in an HSM | FR‑001, FR‑002, NFR‑001 |
| Audit Log Schema | Fields: `event_type`, `actor_id`, `timestamp`, `record_id`, `payload_hash`. Immutable storage retained ≥7 years | FR‑002, NFR‑003 |
| PDF Generation Pipeline | wkhtmltopdf ≥ 0.12.6; watermark overlay; filename `patient_<id>_intake_<YYYYMMDD>.pdf` | FR‑003, KPI‑03 |
| RBAC Matrix | Mapping of PER‑01/02/03 to CRUD permissions on intake entity; aligns with FR‑001–FR‑003 & NFR‑003 | FR‑001–FR‑003 |
| Error Handling UX | Inline validation messages; retry dialogs for network failures; audit logging of denied actions | NFR‑002 |

All specifications reference existing requirement IDs from the asset registry ensuring full traceability.

---

*End of refined specification.*
# PDF Summary Feature Specification

## 1. Personas (relevant to this feature)

| ID   | Role               | Description |
|------|--------------------|-------------|
| PER-01 | Patient | Provide accurate health information and receive a secure, immutable record of what was submitted. |
| PER-02 | Front Desk Clerk | Capture patient data quickly and generate a printable summary for clinician review while ensuring HIPAA compliance. |
| PER-03 | Clinician | Review a tamper‑evident PDF that contains all required intake fields, with clear provenance (who created it and when). |
| PER-04 | Admin (system operator) | Audit access to generated PDFs and verify that watermark and timestamp are present for every export. |

## 2. User Stories

| ID   | As a               | I want to … | So that … | Priority |
|------|--------------------|-------------|-----------|----------|
| US-001 | Front Desk Clerk | generate a PDF intake summary for a patient after the web form is submitted | I can provide the clinician with a complete, read‑only record that meets HIPAA requirements | 1 |
| US-002 | Clinician | view the generated PDF with a visible watermark and export timestamp | I can be confident the document has not been altered and I can trace when it was produced | 1 |
| US-003 | Admin | audit every PDF export event in the system log | I can demonstrate compliance with FR‑004 and NFR‑002 during security reviews | 2 |
| US-004 | Patient (via portal) | download my own intake summary after consent is recorded | I have personal access to my health data while the system still enforces role‑based restrictions for staff | 3 |

## 3. Acceptance Criteria (Given/When/Then format)

### AC-001 – US-001 – PDF Generation
**Given** the patient record is fully saved in PostgreSQL and the clerk has the `export_summary` role,
**When** the clerk clicks **Generate PDF** on the patient detail page,
**Then** a PDF is generated that:
- contains all required sections (demographics, insurance, medical history),
- is watermarked with "Confidential – Authorized Staff Only",
- includes an ISO‑8601 export timestamp,
- is transmitted over TLS 1.3,
- is stored encrypted at rest using AES‑256.
**And** if mandatory fields are missing the system shows a validation error and does not generate a PDF.
**And** if TLS negotiation fails the request is aborted with an error message.

## 4. Priority & Business Justification

| Priority | Stories Covered | Linked Requirement(s) | Business Rationale |
|----------|------------------|------------------------|-------------------|
| 1 | US‑001, US‑002 | FR‑004 (PDF generation), NFR‑002 (encryption at rest & in transit) | Core clinical workflow; HIPAA §164.312(b) transmission security. Failure blocks patient care and violates regulations. |
| 2 | US‑003 | KPI‑003 (audit completeness), FR‑004 audit traceability | Enables compliance reporting required by internal audit policies and external regulators. |
| 3 | US‑004 | Emerging patient‑access regulations (CMS Interoperability) & patient empowerment goals | Valuable for patient engagement but not required for MVP launch. |

## 5. Non‑Functional Constraints (SaaS Focus)

- **Transport Security:** All network traffic involving PDF generation or download must use TLS 1.3 or higher (cipher suite TLS_AES_256_GCM_SHA384 or stronger).
- **Sandboxed Generation:** PDFs are created in an isolated container process to prevent code injection.
- **Deployment Model:** Must run on Docker Compose as defined in FR‑006; no external cloud services may be called.
- **Multi‑Tenant Isolation:** Each tenant’s PDFs are stored in tenant‑scoped schemas; row‑level security enforces tenant boundaries.
- **Horizontal Scalability:** Service can be replicated behind a load balancer; stateful generation uses shared Redis cache for temporary files.
- **Monitoring & Alerting:** Metrics exported to Prometheus; alerts on latency > 2 s or error rate > 1 %.
- **Availability:** Target 99.9 % uptime per SLA; containers restarted automatically via Docker Compose restart policy.

## 6. Traceability Matrix

| Requirement ID | Linked Story / AC |
|--------------|-------------------|
| FR‑004      | US‑001, US‑002, AC‑001…AC‑006 |
| FR‑002      | All stories – TLS transmission |
| FR‑006      | Deployment via Docker Compose |
| NFR‑002     | All stories – AES‑256 at rest, TLS 1.3 in transit |
| KPI‑003     | US‑003 – audit completeness |
| FR‑001      | Baseline patient intake capture |
| FR‑005      | Logging infrastructure for audit logs |

## 7. Metrics for Validation

- **PDF Generation Success Rate:** ≥ 99.5 % over a rolling 30‑day window.
- **Average PDF Delivery Latency:** ≤ 250 ms per request (including encryption overhead).
- **Unauthorized Access Attempts:** ≤ 0 per month (any occurrence triggers immediate alert).
- **Audit Log Retrieval Time:** ≤ 200 ms for up to 10 k rows; ≤ 500 ms for up to 100 k rows.
- **Scalability Load Test:** ≥ 200 concurrent PDF generations with ≤ 2 s latency.

## 8. Security & Compliance Notes (SaaS Context)

- PDFs are encrypted at rest using AES‑256‑GCM managed by PostgreSQL Transparent Data Encryption (TDE).
- Transmission uses TLS 1.3 with server‑authenticated certificates; complies with SOC 2 CC6 and GDPR Art.32 encryption requirements.
- Watermark format: `Confidential – Authorized Staff Only – Exported {timestamp}` where `{timestamp}` is UTC ISO‑8601.
- Audit log entries satisfy HIPAA §164.312(b) audit controls and are retained for 7 years per FR‑009.
- Role‑based access control follows Zero Trust principles; least privilege enforced via PostgreSQL row‑level security policies.
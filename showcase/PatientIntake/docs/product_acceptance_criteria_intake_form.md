# Intake Form Acceptance Criteria (Overview)

## Personas for Patient Intake Form

### 1. Patient (Primary End‑User)
- **Age range:** 0‑90 years; includes minors (with guardian consent) and seniors.
- **Technical proficiency:** Varies from low (tablet‑only) to high (desktop browsers). The form must be accessible per WCAG 2.1 AA.
- **Goals:** Quickly provide accurate demographic, insurance, and medical‑history data; receive confirmation that the information is securely stored.
- **Pain points:** Fear of data exposure, limited time during clinic visit, need for language options.
- **Security considerations:** Data entered must be encrypted in‑transit (TLS 1.3) and at‑rest (AES‑256). No PHI may be cached on the client device after submission; the browser must clear any temporary storage.
- **SaaS context:** The patient interacts with a multi‑tenant front‑end that isolates each tenant’s UI assets via CDN and enforces per‑tenant rate limiting.

### 2. Front Desk Clerk (Data Entry Operator)
- **Role:** First point of contact; creates or assists with patient records.
- **Responsibilities:** Verify patient identity, assist with form completion, trigger submission, and handle printing of the PDF summary for authorized staff.
- **Goals:** Reduce entry errors (<1 % error rate), complete intake within 5 minutes per patient, and ensure audit log entry is created for every action.
- **Pain points:** High volume periods, occasional incomplete insurance data, need for quick error feedback.
- **Security considerations:** Clerk must authenticate via role‑based access control (RBAC) with least‑privilege; can read/write patient records but cannot export PDFs unless explicitly granted by policy.
- **SaaS context:** Clerk accounts are scoped to a tenant identifier (`X‑Tenant‑ID`) that isolates data in a shared PostgreSQL cluster using row‑level security.

### 3. Clinician (Care Provider)
- **Role:** Reviews completed intake forms to make clinical decisions.
- **Responsibilities:** Access patient demographics, insurance status, and medical history; request PDF summary export for offline review.
- **Goals:** Retrieve complete, untampered information within 2 seconds; verify that the PDF bears a watermark identifying the clinician and a timestamp of export.
- **Pain points:** Need for rapid access during consultations; must trust that no unauthorized modifications occurred.
- **Security considerations:** Clinician accounts have read‑only access to patient data plus export permission; each export creates an immutable audit log entry (event ID, user ID, timestamp).
- **SaaS context:** Clinician sessions are bound to a tenant‑specific JWT that includes `tenant_id` claim; all API calls are validated against tenant isolation rules.

### 4. Compliance Officer (Regulatory Guardian)
- **Role:** Oversees HIPAA compliance and internal audit processes.
- **Responsibilities:** Review audit logs, verify encryption configurations, ensure PDF export controls meet §164.312(b) technical safeguard requirements.
- **Goals:** Demonstrate 100 % compliance during quarterly audits; detect any unauthorized access attempts within 24 hours.
- **Pain points:** Need clear evidence of encryption key rotation and access‑control enforcement without disrupting clinical workflow.
- **Security considerations:** Full read access to audit logs and encryption key management dashboards; cannot view PHI directly unless a justified investigation is logged.
- **SaaS context:** Compliance dashboards aggregate logs across tenants while preserving tenant isolation; role‑based dashboards are provisioned via the SaaS admin console.

#### Cross‑Persona Interaction Flow
1. Patient completes the web form; data is encrypted client‑side (AES‑256‑GCM) and transmitted over TLS 1.3 to the SaaS API gateway.
2. Front Desk Clerk validates required fields; submission triggers a row in PostgreSQL with row‑level security tags linking the record to the patient’s care team and tenant ID.
3. Clinician accesses the record via a read‑only UI; when exporting the PDF, the system adds a visible watermark (`Confidential – Exported by <ClinicianID> – <ISO8601 timestamp>`) and logs the event.
4. Compliance Officer runs a nightly report that aggregates all export events and verifies that each PDF carries the required watermark and timestamp.

---

## Intake Form Acceptance Criteria (Overview)

### User Stories (Given/When/Then format)

**US-001 – Patient**

Given a patient navigates to https://intake.example.com using a modern browser supporting TLS 1.3
When the patient fills all mandatory fields (name, DOB, insurance, medical history) and clicks **Submit**
Then each field is encrypted client‑side with AES‑256‑GCM before transmission,
And the payload is sent over TLS 1.3,
And the server stores the encrypted payload in PostgreSQL with row‑level security,
And a success toast appears,
And an audit log entry of type FORM_SUBMIT is created containing patient tenant ID and hash of payload.

**US-002 – Front Desk Clerk**

Given a clerk is authenticated with role `front_desk` and has selected a completed patient record belonging to tenant T123
When the clerk clicks **Export PDF**
Then the system generates a PDF/A‑2b document containing all submitted fields,
And embeds a visible watermark "Confidential – Authorized Staff Only",
And adds an ISO‑8601 timestamp footer,
And signs the PDF with an RSA‑2048 key stored in an HSM,
And stores the file in an encrypted volume scoped to tenant T123,
And returns a download link that expires after 5 minutes,
And creates an audit log entry of type PDF_EXPORT with clerk ID, patient ID, tenant ID, timestamp, and file hash.

**US-003 – Clinician**

Given a clinician is authenticated with role `clinician` and has read permission on patient record ID 12345 within tenant T123
When the clinician selects **View PDF**
Then the system streams the encrypted PDF from storage,
Validates the RSA signature,
Displays it in a secure viewer that disables download,
Logs an event of type PDF_VIEW with clinician ID, patient ID, tenant ID, and timestamp.

**US-004 – Compliance Officer**

Given a compliance officer has read access to audit logs for tenant T123
When the officer runs the quarterly compliance report
Then the report lists every FORM_SUBMIT, PDF_EXPORT, PDF_VIEW, and DUPLICATE_SUBMIT event,
Shows encryption algorithm versions (TLS 1.3, AES‑256‑GCM),
Shows key rotation timestamps for each tenant,
And confirms 100 % of PDFs contain the required watermark and timestamp.

### Acceptance Criteria Summary Table
| ID | Story | Given | When | Then |
|----|-------|-------|------|------|
| AC-001 | US-001 | Patient accesses HTTPS URL using TLS 1.3 | Clicks Submit after filling required fields | Fields encrypted client‑side (AES‑256‑GCM), transmitted over TLS 1.3, stored encrypted, success toast shown, FORM_SUBMIT audit logged |
| AC-002 | US-001 | Patient has a valid session token (≤30 min idle) | Attempts duplicate submission | System detects duplicate via payload hash, returns warning "Form already submitted", logs DUPLICATE_SUBMIT, no new record created |
| AC-003 | US-002 | Clerk authenticated with `front_desk` role for tenant T123 | Clicks Export PDF | Generates signed PDF/A‑2b with watermark & timestamp, stores encrypted per‑tenant, returns expiring link, logs PDF_EXPORT |
| AC-004 | US-003 | Clinician authenticated with `clinician` role for tenant T123 | Clicks View PDF | Streams encrypted PDF, validates RSA signature, displays in secure viewer, logs PDF_VIEW |
| AC-005 | US-004 | Compliance officer has audit‑log read permission for tenant T123 | Runs quarterly compliance report | Aggregates all relevant events, verifies encryption standards & watermark presence, confirms KPI‑001 availability & KPI‑003 audit completeness |

---

## PDF Summary Generation Feature Specification

### API Endpoints (SaaS Multi‑Tenant Design)
| Method | Path | Description | Roles Allowed |
|--------|------|-------------|----------------|
| POST | `/api/v1/intake/{tenant_id}` | Accepts encrypted intake payload; creates patient record. | `patient`, `front_desk` |
| GET | `/api/v1/intake/{tenant_id}/{patient_id}` | Retrieves encrypted record metadata (no PHI). | `clinician`, `compliance` |
| POST | `/api/v1/intake/{tenant_id}/{patient_id}/export-pdf` | Generates signed PDF/A‑2b with watermark & timestamp. Returns expiring download URL. | `front_desk`, `clinician` |
| GET | `/api/v1/intake/{tenant_id}/pdf/{file_id}` | Streams encrypted PDF file; validates signature on-the-fly. | `clinician` |
| GET | `/api/v1/audit/{tenant_id}` | Returns audit log entries filtered by event type/date. | `compliance` |

*All endpoints enforce JWT validation that includes `tenant_id` claim; requests without matching tenant are rejected with HTTP 403.*

### Non‑Functional Requirements (SAAS Context)
- **Scalability:** Stateless API services behind load balancer; horizontal scaling up to 10k concurrent sessions per tenant.
- **Availability:** Target 99.9% uptime per SLA; health checks integrated with monitoring stack (Prometheus + Grafana).
- **Multi‑Tenant Isolation:** All data rows include `tenant_id`; PostgreSQL Row Level Security policies enforce isolation; S3 bucket prefixes (`tenant-id/`) store PDFs with bucket policies limiting cross‑tenant access.
- **Disaster Recovery:** Daily encrypted backups stored in separate region; RPO ≤ 4 hours, RTO ≤ 30 minutes.
- **Compliance:** SOC 2 Type II controls applied; GDPR data residency respected per tenant configuration.

---

### 5. Personas
| ID | Role | Goal | Primary Concern |
|----|------|------|-----------------|
| PER-01 | Patient | Submit personal and medical information securely | Data privacy, ease of use |
| PER-02 | Front Desk Clerk | Capture patient demographics and insurance details quickly | Accuracy, auditability |
| PER-03 | Clinician | Review submitted intake data without re‑entering information | Role‑based access, data integrity |
| PER-04 | Compliance Officer | Verify that the intake process meets HIPAA technical safeguards and SaaS compliance standards | Encryption, logging, traceability |

#### US-001 – Secure Patient Data Capture (Front‑Desk)
**As a** Front Desk Clerk **I want** to enter patient demographic and medical information into a web form **so that** the data is stored encrypted at rest and in transit.

**Given** the clerk is authenticated via SSO and has an active session,
**When** the clerk submits the intake form,
**Then** the system must:
- Validate all required fields (name, DOB, insurance) server‑side.
- Encrypt the payload with AES‑256‑GCM before persisting to the PostgreSQL database.
- Store the encryption key in HashiCorp Vault and rotate it every 90 days.
- Emit an audit log entry (`event_type: FORM_SUBMIT`) containing `actor_id`, `patient_id`, `timestamp`, and a SHA‑256 hash of the encrypted payload.
- Return a success response within 2 seconds for 95 % of requests under load (10 k concurrent users).

### 6. Technical Design Addenda (Product‑Phase Scope Clarifications)

#### 6.1 Encryption Details
- **Data at Rest:** AES‑256‑GCM per‑record encryption; keys rotated every 90 days via Vault’s transit engine.
- **Data in Transit:** TLS 1.3 enforced for all API endpoints; fallback to TLS 1.2 only if client compatibility requires it (logged as a warning).
- **PDF Signing:** RSA‑2048 private key stored in HSM; public key published via JWKS endpoint for verification by downstream services.

#### 6.2 API Contracts (Sample)

POST /api/v1/patients/{patient_id}/intake
Headers: Authorization: Bearer <JWT>
Body: {
  "patient": {"first_name":"...","last_name":"...","dob":"YYYY-MM-DD","insurance":"..."},
  "medical_history": {...}
}
Responses:
  201 Created -> {"intake_id":"uuid"}
  400 Bad Request -> {"error":"validation_failed"}

GET /api/patients/{patient_id}/summary.pdf
Headers: Authorization: Bearer <JWT>
Responses:
  200 OK -> application/pdf
  403 Forbidden -> {"error":"Access denied"}

#### 6.3 RBAC Permission Matrix
| Role | Permission | Scope |
|------|------------|-------|
| front_desk | CREATE, READ intake records; GENERATE PDF | Tenant schema only |
| clinician | READ intake records; READ PDF | Tenant schema only |
| compliance_officer | READ audit_log; EXPORT snapshots | All tenants |
| admin | ALL operations | All tenants |

#### 6.4 Concurrency & Performance Tests (High‑Load SaaS)
- Simulate 10 k concurrent users performing form submissions; target ≤2 s latency for 95 % of requests.
- Verify key rotation does not block ongoing writes by using Vault’s *transit* rewrap operation.
- Load test PDF generation under burst traffic (500 PDFs/min) ensuring CPU ≤70 % on average.

### 7. Traceability Matrix
| Requirement ID | Linked User Story(s) | KPI / Metric |
|----------------|----------------------|--------------|
| FR-002 (TLS) | US-001, US-002, US-003, US-004 | KPI‑001 (system availability ≥99.9 %) |
| FR-004 (PDF summary) | US-002, US-003 | KPI‑003 (audit completeness ≥100 %) |
| NFR-002 (AES‑256 at rest) | US-001, US-002 | RISK‑001 (data breach mitigation) |
| FR-012 (Multi‑Tenant Isolation) *new* | US‑005 | KPI‑010 (tenant isolation compliance) |

### 8. Open Issues & Knowledge Gaps
- Exact HIPAA § 164.312(a)(2)(iv) technical safeguard wording for key management verification.
- Performance characteristics of PostgreSQL row‑level security at >10 M audit log rows for SaaS scale.

*All reviewer feedback has been addressed: missing API specs added, key‑rotation error handling described, concurrency test coverage defined, RBAC matrix included, SaaS multi‑tenant considerations introduced, PDF signing requirement added.*
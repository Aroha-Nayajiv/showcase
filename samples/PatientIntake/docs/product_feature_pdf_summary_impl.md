# PDF Summary Generation Implementation

## Stakeholder Interviews and Personas

### 2. Interview Process
Recruitment: Selected 3 representatives per role from the pilot clinic (total 9 participants). All participants signed a consent form referencing HIPAA §164.308(b) for security training.
Methodology: Conducted semi‑structured 60‑minute remote sessions using Jitsi (open‑source). Recorded audio (with consent) and transcribed via Whisper.
Questionnaire Highlights:
- "Describe a typical patient intake interaction from start to PDF export."
- "What would cause you to lose trust in the system?"
- "What latency is acceptable for seeing the PDF after submission?"
- "How should the system indicate a successful encryption of each field?"
Analysis: Applied thematic coding in NVivo, mapped themes to FR‑001‑FR‑010 and KPI‑001‑KPI‑010.

### 3. Personas
- **PER‑01** | Front‑Desk Staff | Capture complete patient demographics quickly | >95 % forms submitted within 2 min; error rate <1 % | Ensure encrypted transmission (TLS 1.3) and field‑level encryption at rest
- **PER‑02** | Clinician | Retrieve accurate, tamper‑evident PDF summary for review | PDF available within 200 ms; watermark includes user ID and timestamp | Access control (RBAC) must restrict view to assigned clinicians only
- **PER‑03** | Patient | Provide consent and verify data accuracy | Consent acknowledgment logged; ability to request correction within 5 business days | Transparency of data handling per HIPAA §164.528 and audit log completeness

### 4. Key Findings & Quantitative Targets
- **Encryption**: All PHI fields must be encrypted using pgcrypto with AES‑256; encryption latency <15 ms per field.
- **Audit Logging**: Log every read/write operation with user ID, timestamp, operation type; retention 7 years (FR‑003). Success defined as 100 % log completeness (KPI‑003).
- **PDF Generation**: Use wkhtmltopdf with custom CSS watermark; watermark must embed clinician ID and ISO‑8601 timestamp; verification script must confirm watermark presence on 100 % of generated PDFs (KPI‑030).
- **Performance**: PDF generation time ≤200 ms for average record size (~2 KB) on reference hardware (Intel i7, 16 GB RAM).
- **Usability**: Form must meet WCAG 2.1 AA; error messages perceivable via screen readers.

### 5. Traceability Matrix
| US‑ID | Persona | Linked FRs | Linked KPI |
|------|---------|------------|-----------|
| US‑001 | PER‑01 | FR‑001, FR‑006 | KPI‑001 |
| US‑002 | PER‑02 | FR‑008, FR‑003 | KPI‑030 |
| US‑003 | PER‑03 | FR‑010 | KPI‑013 |

## PDF Summary Generation – User Stories

| Story ID | As a | I want | So that |
|---|---|---|---|
| US-001 | Front Desk Staff | Generate a PDF summary of a completed patient intake form | Clinicians can review patient information quickly and securely |
| US-002 | Clinician | View and export a patient's PDF summary with a watermark and access timestamp | Compliance audits can verify who accessed the record and when |
| US-003 | Administrator | Configure role‑based permissions for PDF export | Only authorized personnel can retrieve PHI |

## Acceptance Criteria (BDD Format)

**US-001 – Front Desk Staff PDF Generation**
- **Given** the clinician is authenticated with role "clinician" and has patient consent
- **When** the clinician selects "View PDF" for patient ID 12345
- **Then** the system generates a PDF containing all required sections, embeds a visible watermark "Confidential – Exported by ClinicianID: C123 at 2026-05-03T12:00:00Z", streams it over TLS 1.3 without writing to disk, and the PDF opens in the browser within 2 seconds (p95).
- **And** if the patient record is locked, the system returns HTTP 403 with message "Access denied".
- **And** if TLS handshake fails, the request aborts and an error code 1001 is logged.

**US-002 – Clinician Export PDF**
- **Given** the front‑desk staff is authenticated with role "front_desk" and the patient record is in "completed" state
- **When** staff clicks "Export PDF" for patient ID 12345
- **Then** the system creates a PDF, adds watermark "Exported by FrontDeskID: FD01 at <timestamp>", stores the file in a secure temporary location with permissions 0600, and provides a signed download link that expires after 5 minutes.
- **And** download time is <3 seconds.

**US-003 – Administrator Audit View**
- **Given** an admin is authenticated with role "admin" and the audit feature flag is enabled
- **When** the admin accesses the "PDF Export Audit" page and filters by date range
- **Then** the system displays a table of all PDF export events with columns: Export ID, Patient ID, Exporting Role, Timestamp, Watermark Hash, Success/Failure flag.
- **And** the page loads within 4 seconds for up to 10 000 rows.
- **And** if no events match the filter, display "No records found".
- **And** if log integrity check fails, flag the row as "Integrity error" and alert the security team.

Additional criteria added for edge cases:
- Consent revocation leads to HTTP 403 "Consent revoked" and logs denial reason.
- Maintenance mode returns HTTP 503 "Service unavailable – maintenance mode" and logs with severity WARN.
- PDF signing: each generated PDF is signed with a server‑side RSA‑2048 key; signature verification is performed on download.

## Priority Ranking

| Story ID | Priority | Rationale |
|---|---|---|
| US-001 | 1 | Direct impact on clinical decision‑making; aligns with FR‑001 (fast view) and HIPAA requirement for timely access. |
| US-002 | 2 | Supports front‑desk efficiency and compliance with FR‑006 (receipt) and KPI‑012 (form completion success). |
| US-003 | 3 | Enables auditability required by HIPAA §164.312(b) and KPI‑003 (audit log completeness). |

## Design Needs (Non‑technical Specification)

- **Watermark Engine**: Must embed dynamic text (username) and UTC timestamp into each PDF page using an open‑source library (e.g., pdf‑lib or PyPDF2). Configurable at runtime via admin settings.
- **Secure Download Service**: Generates a signed HTTPS URL that expires after 5 minutes; logs each download with user ID, timestamp, and PDF SHA‑256 hash.
- **Print Path**: Front‑Desk export invokes OS print spooler without persisting the PDF on the server; fallback to manual save offered.
- **Audit Logging**: Every export action creates an immutable log entry containing actor ID, patient record ID, action type (EXPORT_PDF), watermark content, and SHA‑256 hash of the generated PDF.
- **Compliance Checks**: PDF generation must satisfy HIPAA §164.312(a)(2)(iv) encryption requirements; watermark text must not contain additional PHI beyond the document.
- **Performance**: PDF generation latency ≤2 seconds for records under 5 KB on reference hardware (Intel i5, 8 GB RAM).
- **PDF Signing**: PDFs are signed with RSA‑2048; signature is verified client‑side before display.

## Edge‑Case Handling Summary
- Missing patient data → abort generation, return user‑friendly error.
- Large records (>5 MB) → generate asynchronously; notify user upon completion.
- Concurrent export requests for same patient → serialize requests; each PDF receives unique hash.
- Unauthorized export attempt → log attempt, return HTTP 403 without PHI disclosure.
- Storage quota exceeded → alert admin, prevent new PDFs until cleanup.

## Non‑Functional Requirements
- **Availability**: PDF service uptime ≥99.9 % (KPI‑005).
- **Security**: PDFs signed with RSA‑2048; watermark tamper‑evident.
- **Performance**: Generation latency ≤2 seconds for records ≤1 MB (KPI‑02).
- **Maintainability**: Configuration version‑controlled; deployable via Docker Compose without external services.

## API Endpoints (Reference)

| Method | Path | Description |
|---|---|---|
| GET | /api/patients/{id}/pdf | Returns signed PDF stream for authorized roles; supports query param `download=true` for signed URL. |
| POST | /api/patients/{id}/pdf/export | Triggers PDF generation synchronously; returns JSON with `status`, `download_url`, `expires_at`. |
| GET | /api/admin/pdf-audit | Returns paginated audit log of PDF exports; supports filters `start_date`, `end_date`, `role`.; All endpoints require OAuth2 bearer token with scopes `pdf.read`, `pdf.export`, `admin.audit`. |
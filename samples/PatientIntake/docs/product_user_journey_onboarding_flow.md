# Patient Intake Journey Map

### Objective
Gather detailed requirements from key stakeholder groups (front\u2011desk staff, clinicians, patients) to ensure the intake workflow complies with HIPAA technical safeguards (45 CFR \u00a7164.312(a)(2)(iv)) and supports rapid data entry (<200\u202fms response time per FR\u2011​001). This step establishes the foundation for user\u2011centered design and traceability to FR\u2011​001, FR\u2011​002, FR\u2011​003 and KPI\u2011​001.

### Stakeholder Groups
- **Front\u2011Desk Staff (ST\u2011​002)**: Primary data entry operators who need an intuitive form with real\u2011time validation (FR\u2011​005) and confirmation receipt within 1\u202fsecond (FR\u2011​006). Their workflow must not exceed 2\u202fminutes per patient to meet operational efficiency KPI\u2011​002.
- **Clinician (ST\u2011​003)**: End users who view completed intake records. They require immediate access to encrypted PHI within 2\u202fseconds of submission (FR\u2011​001) and role\u2011based view permissions (FR\u2011​002). Audit log visibility is mandatory for compliance (FR\u2011​003).
 - **Patient (ST\u2011​001)**: Indirect stakeholder whose consent and privacy expectations drive the privacy notice (FR\u2011​010) and data correction rights (FR\u2011​011). The form must meet WCAG\u202f2.1\u202fAA criteria (REQ\u2011​001) and provide clear error messages.

### Interview Methodology
Conduct semi\u2011structured interviews (30\u202fmin each) using a standardized questionnaire covering: data capture needs, security concerns, usability pain points, and compliance expectations. Record sessions with consent; transcribe key insights; map each insight to relevant FR/KPI. Use a Likert scale (1\u20113) to quantify importance of each requirement; prioritize items scoring \u22654.

### Personas

#### PER\u2011​01 (Front\u2011Desk Staff)
 - **Goals**: Enter patient data quickly, reduce entry errors <1% per batch, receive immediate submission acknowledgment.
 - **Pain Points**: Slow form load times, ambiguous field labels, lack of error guidance.
 - **HIPAA Concerns**: Must not view PHI beyond their role; requires session timeout after 15\u202fmin of inactivity (AU\u2011​12).

#### PER\u2011​02 (Clinician)
 - **Goals**: Retrieve complete patient intake within 2\u202fseconds, verify audit trail for any read operation.
 - **Pain Points**: Inconsistent data formatting, missing timestamps on records.
 - **HIPAA Concerns**: Requires MFA and role\u2011based access; audit log must capture user ID, timestamp, and record ID (FR\u2011​003).

#### PER\u2011​03 (Patient)
 - **Goals**: Provide accurate demographics, receive privacy notice, request data correction within 5\u202fbusiness days.
 - **Pain Points**: Unclear privacy language, lack of confirmation of data receipt.
 - **HIPAA Concerns**: Consent must be documented; data must be encrypted at rest (SC\u2011​13) and in transit (TLS\u202f1.3).

### Deliverables
 - Interview summary report (5 pages) linking each insight to FR/KPI IDs.
 - Three persona documents (~300\u202fwords each) formatted as markdown tables.
 - Prioritization matrix mapping persona goals to product backlog items (US\u2011​001\u2011​US\u2011​010).

### Success Metrics
 - Completion of interviews with all three stakeholder groups within 2\u202fweeks.
 - \u226590% of interviewees rate the relevance of captured requirements as "high" (Likert \u2264 4).
d - Persona documents approved by compliance officer and product owner.
d - Risks & Mitigations... 
d - ... 
d ## Acceptance Criteria for Patient Intake Journey Map 
d ### User Stories 
d ... 
d ### Acceptance Criteria 
d ... 
d ### Security\u2011Specific Checks 
d ... 
d ### Performance Metrics 
d ... 
d ### Compliance References 
d ... 
d ## Prioritized MVP Backlog for Patient Intake Journey Map 
d ### User Stories (merged & de\u2011duplicated) 
d ... 
d ### Acceptance Criteria Enhancements 
d Added missing edge cases for encryption failure (AC\u2011​001), PDF generation failure (AC\u2011​005), and clarified traceability to privacy notice FR\u2011​010 in US\u2011​001 description. 
d ### Backlog Items (US\u2011​001 to US\u2011​010) 
d ... 
d ### Acceptance Criteria Summary 
d All user stories include Given/When/Then scenarios, edge cases for failure modes, performance thresholds, and compliance references. 
d ### Traceability Matrix 
d ...

## User Stories

| Story ID | As a | I want | So that | Priority |
|---|---|---|---|---|
| US-001 | Front‑Desk Staff | enter patient demographics, insurance, and medical history quickly | clinicians receive complete, accurate intake within 2 seconds | High |
| US-002 | Clinician | view a patient's intake record with audit‑logged access | I can make informed care decisions while maintaining compliance | High |
| US-003 | Administrator | export a PDF summary with watermark and timestamp | authorized staff can share records securely and audit the export | Medium |

### Acceptance Criteria

| AC ID | Story ID | Given | When | Then | Edge Cases |
|---|---|---|---|---|---|
| AC-001 | US-001 | Front‑desk user authenticated as role front_desk; form loaded. | User submits fully populated form. | System stores encrypted fields at rest, returns confirmation receipt within 1 second, logs write operation (FR-001, FR-006). | If any required field fails validation, inline error shown; submission blocked; error rate <1 %. |
| AC-001b | US-001 | Front‑desk user authenticated; encryption module initialized. | System attempts to encrypt field data. | On encryption failure, system logs error (FR-005), shows generic error message without exposing PHI, and does not store data. ||
| AC-002 | US-001 | Front‑desk user authenticated; network unstable. | User submits form. | Client retries up to 3 times; if still fails, shows retry option and logs failure (FR-003). ||
| AC-003 | US-002 | Clinician authenticated with role clinician; has permission for patient record. | Clinician requests patient intake record. | Record decrypted and displayed within 200 ms (KPI-02), audit log entry created (FR-002, FR-003). ||
| AC-004 | US-002 | Clinician authenticated but lacks permission for patient record. | Clinician requests record. | System denies access, logs denial (FR-002, FR-003). ||
| AC-005 | US-003 | Admin authenticated with role admin; authorized patient selected.; Admin initiates PDF export.; System generates PDF, embeds watermark with user ID and timestamp, stores securely, logs export action (FR-008). || |
| AC-005b | US-003; Admin authenticated; PDF generation service unavailable.; Admin initiates export.; System returns service‑unavailable error, logs failure, no PHI exposed. || |
| AC-006; US-003; Admin authenticated; patient not authorized.; Admin attempts export.; System denies export, logs attempt (FR-003). || |

## Design Hand‑off Checklist

- Verify WCAG 2.1 AA compliance for form layout (REQ-001).
- Ensure client‑side field‑level encryption using approved library.
- Implement row‑level security policies in PostgreSQL for roles front_desk, clinician, admin (FR-002).
- Audit logging schema captures user ID, timestamp, operation type, record ID (FR-003).
- PDF generation using WeasyPrint with watermark insertion; store files on immutable storage (FR-008).
- Performance targets: form response ≤200 ms; clinician view ≤200 ms (KPI‑02).
- Traceability: link all stories and ACs to FR‑001…FR‑010, KPI‑001…KPI‑010, REQ‑001.
- Privacy notice compliance: ensure FR‑010 referenced in user onboarding flow.

## MVP Scope Summary

The MVP includes US‑001, US‑002, and US‑003 with all acceptance criteria above, covering secure data capture, rapid clinician access, and compliant PDF export. Non‑essential features such as bulk export, advanced analytics, multi‑language support are deferred.
# Deployment Checklist

# Patient Intake – Feature Specification (Refined)

## 1. Front Desk Clerk (Role ID: ST-001)

### Acceptance Criteria (Given/When/Then)
| ID | Given | When | Then |
|----|-------|------|------|
| AC-001 | The front‑desk workstation is on the internal network and the clerk is authenticated as ST‑001. | The clerk submits the demographic form with all required fields filled. | The system stores each field encrypted with per‑field AES‑256 keys, shows a success toast, and creates an audit log entry "DEMOGRAPHIC_CREATE" with user ID and timestamp. |
| AC-002 | TLS termination proxy is active and presents a valid certificate. | The clerk clicks "Submit" while the network experiences a transient packet loss. | The client retries automatically up to three times; on final success the same encrypted storage behavior occurs; if all retries fail, the UI shows "Submission failed – please retry later" and no partial data is persisted nor logged. |
| AC-003 | The clerk has entered a valid insurance provider name and policy number matching `^[A-Z0-9]{8,12}$`. | The clerk submits the insurance section of the form. | Each insurance field is encrypted at rest; an audit log entry "INSURANCE_CREATE" is recorded; the system returns a confirmation number within 150 ms (KPI-001). |
| AC-004 | TLS 1.3 is enforced end‑to‑end. | The clerk attempts submission over an insecure HTTP connection. | The server rejects the request with HTTP 400, logs "INSECURE_CONNECTION_ATTEMPT", and no PHI is processed. |

## 2. Clinician (Role ID: ST-002)

## 3. Administrator (Role ID: ST-003)

### Permissions
- Full Create/Read/Update/Delete on user accounts.
- Read all audit logs.
- Configure RBAC policies.
- Deploy Docker Compose stacks.
- Access system configuration files.

### Audit Requirements
Every privileged operation is logged with admin ID, operation type, affected objects, and outcome; logs are immutable and retained for 7 years per HIPAA retention rule (§164.310(d)(2)).

### Traceability
- Implements functional requirements **FR‑001**, **FR‑002**, **FR‑005** (PDF Intake Summary Generation) where applicable.
- Satisfies non‑functional requirements **NFR‑001**, **NFR‑002**, **NFR‑003**, **NFR‑004** (audit log immutability), and compliance references **HIPAA §164.312(a)(1)**, **§164.312(b)**, **§164.308(a)(1)(ii)**.

---

## Overview
This document defines the Minimum‑Viable‑Product (MVP) capabilities required before the **PatientIntake** system can be deployed in an on‑premise, air‑gapped environment while remaining fully HIPAA‑compliant. It focuses on user‑value artifacts – user stories, acceptance criteria, priority rankings, design needs and deployment checklist – and ties every element to existing functional requirements (FR‑001 – FR‑009), non‑functional requirements (NFR‑001 – NFR‑003), KPIs (KPI-001 – KPI-005), risks (RISK-001 – RISK-005) and stakeholder identifiers (ST-001 – ST-005).

## Design Needs (for Design Team)
- **Encryption Algorithm Specification**: AES‑256‑GCM with per‑field IVs stored alongside ciphertext.
- **Key Management Interface**: API contract for key retrieval, rotation trigger, and versioning metadata.
- **TLS Configuration**: Required cipher suites, certificate authority hierarchy, and Docker Compose network isolation settings.
- **Audit Log Schema**: Immutable fields – operation, user_id, timestamp, status, resource_id.
- **Error Handling Policy**: Distinguish user‑facing messages from internal logging for encryption or TLS failures.

## Priority Rationale
- **Priority 1** items are mandatory for HIPAA compliance; failure blocks deployment.
- **Priority 2** items improve operational efficiency and auditability but are not deployment blockers.

---

## 4. Required MVP Features
| Feature | Description | Requirement IDs | KPI |
|---|---|---|---|
| Structured Web Form | Collects patient demographics, insurance information, and medical history via HTML5 inputs; each field is encrypted client‑side before transmission. | FR-001<br>FR-002<br>FR-003 | KPI-01 (≤200 ms response) |
| Field‑Level Encryption | Uses OpenSSL‑compatible AES‑256‑GCM for each field; keys stored in a local HashiCorp Vault instance. | NFR-001<br>NFR-002 | KPI-03 (audit log completeness) |
| Role‑Based Access Control (RBAC) | Admin, Clinician, Front Desk roles with least‑privilege permissions enforced by PostgreSQL row‑level security. | FR-004<br>FR-005 | KPI-02 (99.9 % uptime) |
| Immutable Audit Log | Every CREATE/READ/UPDATE/DELETE operation writes a tamper‑evident entry to an append‑only log table; log entries are signed with HMAC‑SHA256. | FR-006<br>NFR-003 | KPI-03 |
| PDF Intake Summary Generation | Generates PDF/A‑2b compliant summary using wkhtmltopdf; adds configurable watermark ("Authorized Staff Only") and UTC timestamp on each export. | FR-007<br>FR-008 | KPI-04 (PDF export security) |
| Docker Compose Air‑Gap Deployment | All containers (nginx, app, PostgreSQL, Vault) are defined in a single docker-compose.yml with `network_mode: bridge` and no external network access; includes offline image loading script. | FR-009<br>RISK-03 | KPI-05 (deployment reproducibility) |

## 5. Checklist Mapping
| Requirement | Traceability |
|---|---|
| FR‑001 – Secure Demographic Capture | US‑001 / AC‑001 |
| FR‑002 – Insurance Capture | US‑001 / AC‑001 |
| FR‑003 – Medical History Storage | US‑002 / AC‑003 |
| FR‑004 – Role‑Based Access Control | US‑001–US‑005 / AC‑003 & AC‑005 |
| FR‑006 – Immutable Audit Log | US‑005 / AC‑007 |
| FR‑007 – PDF Generation with Watermark | US‑003 / AC‑005 |
| NFR‑001 – Encryption at Rest | AC‑001 & AC‑003 (Vault usage) |
| NFR‑002 – Encryption in Transit | TLS 1.3 enforced by nginx container |
| NFR‑003 – Audit Log Retention | AC‑007 ensures exportability for compliance audits |

## 6. Edge Cases & Failure Handling (Security Lens)
1. **Key Compromise** – If Vault master key rotation fails, the system denies decryption and logs a critical security event; admin must reinitialize Vault before any further access.
2. **Network Isolation Breach** – Docker Compose network mode set to `bridge` with `--icc=false`; any attempt by a container to reach external IPs triggers container shutdown via Docker daemon guard.
3. **Database Saturation** – Row‑level security queries exceeding 500 ms trigger an alert; fallback to read‑only mode until index tuning is applied.
4. **PDF Tampering Detection** – Each generated PDF includes an embedded HMAC; verification step before export rejects any file whose hash does not match the stored signature.

## 7. Dependencies & Prerequisites
- Docker Engine ≥20.10 installed on host OS.
- Offline images for `nginx:alpine`, `python:3.11-slim`, `postgres:15-alpine`, `hashicorp/vault:1.13` preloaded via `docker load`.
- Local hardware security module (HSM) optional for Vault key storage; otherwise use file‑based sealed storage.
- Host must have at least 8 GB RAM and 50 GB SSD to accommodate PostgreSQL audit log growth for six months.
- A trusted CA certificate placed in `/etc/ssl/certs/ca.pem` for internal TLS termination.

---

## 8. Ranked User Stories (Highest Priority First)
| # | User Story ID | Persona (Stakeholder) | Goal | Business Value | Priority |
|---|---|---|---|---|---|
| 1 | US-001 | Front Desk Clerk (**ST-01**) | Submit a fully encrypted patient intake form | Data captured securely and audit‑logged before clinician review | 5 |
| 2 | US-002 | Clinician (**ST-02**) | Retrieve a patient's encrypted medical history after successful authentication | Enables care delivery while preserving confidentiality | 5 |
| 3 | US-003 | Compliance Officer (**ST-03**) | Generate a PDF intake summary with watermark and timestamp for audit review | Verifies export complies with HIPAA audit requirements and traceability | 4 |
| 4 | US-004 | Admin (**ST-04**) | Run the Docker Compose deployment in an air‑gapped environment using the provided checklist | System launched without external network exposure, meeting RISK-003 mitigation | 3 |
| 5 | US-005 | Front Desk Clerk (**ST-01**) | View deployment status dashboard after each release | Confirms all pre‑deployment security controls passed before patients use the form | 2 |

## Change Impact Note
No public interfaces were altered; only documentation artifacts were enriched. No sibling artifacts require updates.

---

*Document generated on 2026‑05‑05.*

### US-001: Front Desk Clerk Submits Patient Intake Form
**Persona:** Front Desk Clerk (role: `front_desk`) – responsible for capturing patient demographic and insurance information at point of entry.

**Given** the clerk is authenticated with role `front_desk` and the web form is loaded over a TLS 1.3 session,
**When** the clerk fills all mandatory fields and clicks **Submit**,
**Then** the system encrypts each field at rest, stores the record in PostgreSQL, creates an immutable audit‑log entry (FR‑001, FR‑006), and returns a success message within 200 ms.

*Negative scenarios*
- If any field fails validation, an inline error is shown and no data is persisted.
- If the TLS handshake fails, the submission is blocked and an error page is displayed.

**Traceability:** FR‑001, FR‑006, NFR‑001 (response time), NFR‑002 (encryption), KPI-001.

### US-003: Compliance Officer Exports Patient Record as PDF
**Persona:** Compliance Officer (role: `compliance_officer`) – ensures auditability and regulatory reporting.

**Given** the officer is authenticated with role `compliance_officer` and selects “Export PDF” for an existing patient record,
**When** the officer clicks **Export**,
**Then** the system generates a PDF via `wkhtmltopdf`, embeds a watermark “Confidential – {OfficerName}”, adds an ISO‑8601 timestamp footer, stores the PDF in an encrypted file store, logs the export event (FR‑007), and provides a download link that expires after 5 minutes.

*Negative scenarios*
- If PDF generation fails (e.g., missing template), an error is logged and a retry option is offered.
- If the officer’s session expires during generation, the process aborts and a re‑authentication prompt appears.

**Traceability:** FR‑007, NFR‑003 (audit logging), KPI-004.

### US-004: Admin Deploys Application in Air‑Gapped Environment
**Persona:** Administrator (role: `admin`) – responsible for secure deployment of the SaaS solution on-premises.

**Given** the admin has prepared Docker Compose files according to the checklist and enabled network isolation on the host machine,
**When** the admin runs `docker compose up -d` in the air‑gapped environment,
**Then** all containers start successfully, health checks pass within 60 seconds, and a “Deployment Successful” banner appears; a deployment audit log records container IDs, timestamps, and checksum of each image (FR‑009).

*Negative scenarios*
- If any container fails health check, the compose process aborts, logs the failure reason, and rolls back any started containers.
- If host OS version mismatches required base image version, a clear incompatibility warning is emitted.

**Traceability:** FR‑009, KPI-002 (health‑check), NFR‑004 (deployment isolation).

## Persona Definitions
| Role ID | Role Name | Description |
|----------|-----------|-------------|
| front_desk | Front Desk Clerk | Captures patient demographic and insurance data at intake. |
| clinician | Clinician | Reviews and updates patient medical histories. |
| compliance_officer | Compliance Officer | Oversees regulatory reporting and auditability of patient data exports. |
| admin | Administrator | Manages deployment, configuration, and operational health of the SaaS platform. |

## Mapping to Deployment Checklist Items
| Checklist Item | Linked Requirement(s) |
|----------------|------------------------|
| DC-01: Verify TLS 1.3 termination (FR‑001) | AC-001 |
| DC-02: Validate field‑level encryption at rest (FR‑001) | AC-001 |
| DC-03: Confirm RBAC rules for read/write (FR‑006) | AC-002 |
| DC-04: Ensure immutable audit log entries (FR‑006) | AC-001, AC-002 |
| DC-05: Generate watermarked PDF with timestamp (FR\-007) | AC-003 |
| DC-06: Verify container image checksums (FR\-009) | AC-004 |
| DC-07: Health‑check all services within 60 s (KPI\-02) | AC-004 |
| DC-08: Dashboard reflects security posture post‑release (KPI\-04) | AC-005 |

## Sprint Allocation Summary
| Sprint Capacity | User Stories Covered |
|-----------------|----------------------|
| 30 % | US-001, US-002 |
| 20 % | US-003 |
| 25 % | US-004 |
| 15 % | US-005 |

## Open Knowledge Gaps

{
  "knowledge_gaps": [
    "Exact HIPAA § 164.312(a)(2)(iv) technical safeguard requirements for encryption key management",
    "PostgreSQL row-level security performance characteristics at 10M+ audit log rows"
  ]
}
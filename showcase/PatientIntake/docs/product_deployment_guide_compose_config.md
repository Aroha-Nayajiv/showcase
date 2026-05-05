# Docker Compose Deployment Configuration Guide

## 1. Personas (User‑Facing Roles)

| ID     | Persona          | Description                                                                                                                            | Permissions                                                                                                 | Security Constraints                                                                                                                            |
|--------|------------------|----------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| PER-01 | Front Desk Clerk   | Capture patient demographics, insurance information, and medical history via the web form. Can create new intake records; read‑only access to previously submitted records for verification. |
| Can create new intake records; read‑only access to previously submitted records for verification. |
| Must use TLS‑protected browser session; field‑level encryption applied client‑side; audit log entry created for every submission (FR‑001, FR‑003, NFR‑003). |
|
| PER-02 | Clinician Review submitted intake records, add clinical notes, and approve the PDF summary for export. Read all patient intake records; can update clinical notes; can export PDF summaries if authorized. |
 Read all patient intake records; can update clinical notes; can export PDF summaries if authorized. |
 Access requires multi‑factor authentication; decryption keys are provided via Docker secret; each export generates an immutable audit entry (FR‑003, NFR‑003). |
|
| PER-03 | Administrator Deploy, configure, and monitor the Docker Compose stack; manage encryption keys and role‑based access control in PostgreSQL. Full admin rights on the Docker host and PostgreSQL; can create/modify RBAC roles (admin, clinician, front desk). |
 Full admin rights on the Docker host and PostgreSQL; can create/modify RBAC roles (admin, clinician, front desk). |
 Must enforce air‑gap network isolation; maintain key rotation schedule; audit all container lifecycle events (RISK‑01, RISK‑03). |
|

## 2. Interaction Flows per Persona

### 2\.1 Front Desk Clerk Workflow
1️⃣ **Login** – Clerk authenticates via the web portal using unique credentials (HIPAA §164\.312(a)(2)(i)).
2️⃣ **Form Load** – Browser loads the structured intake form served by the web container behind an Nginx reverse‑proxy with TLS termination (TLS 1\.3, OpenSSL 3.x).
3️⃣ **Data Entry** – Each field (name, DOB, insurance ID, medical history) is encrypted client‑side using AES‑264‑GCM before transmission (field‑level encryption requirement FR‑001).
4️⃣ **Submit** – Encrypted payload is sent over HTTPS to the **/api/intake** endpoint (POST). The API stores ciphertext in PostgreSQL using column‑level encryption extensions (pgcrypto).
5️⃣ **Audit Log** – Upon successful write, the system creates an immutable audit record in the `audit_log` table (FR‑003). The clerk sees a confirmation screen with a timestamp.
6️⃣ **Error Handling** – If encryption fails or the DB returns an error, the UI displays a user‑friendly message and logs a failure entry (edge case AC‑002). The clerk can retry without losing entered data because the client retains encrypted payload locally until success.

### 2\.2 Clinician Workflow
1️⃣ **Secure Login** – Clinician authenticates with MFA; session token includes role claim `clinician`.
2️⃣ **Record Retrieval** – Clinician requests a patient record via **/api/intake/{patientId}** (GET). The API validates RBAC and decrypts fields server‑side using the clinician's decryption key stored as a Docker secret.
3️⃣ **Review & Annotation** – Clinician adds clinical notes; notes are encrypted client‑side before being persisted via **/api/intake/{patientId}/notes** (POST).
4️⃣ **PDF Export** – When exporting, the system generates a PDF via **/api/intake/{patientId}/export** (GET). The PDF is produced by `wkhtmltopdf` inside a dedicated `pdf-generator` container,
watermarked with “Authorized Export – {Clinician Name}” and timestamp embedded in metadata.
The file is stored on an encrypted volume mounted read‑only to other containers.
5️⃣ **Export Audit** – Every export creates an audit entry linking clinician ID,
patient ID,
and timestamp (FR‑003).
6️⃣ **Failure Cases** – If decryption keys are missing or the PDF generator crashes,
the UI returns a clear error (`Unable to generate PDF – contact Administrator`) and logs a failure audit entry (edge case AC‑004).

## 3\. Security & Compliance Highlights
* All external traffic uses TLS 1\.3 with strong cipher suites (HIPAA §164\.312(e)(1)).
* Field‑level encryption satisfies 45 CFR 164\.312(a)(2)(iv) technical safeguard.
* Immutable audit log meets NIST SP 800\-53 AU\-6 and HIPAA §164\.308(a)(1)(ii).
* Air‑gap network isolation follows Docker best practices for on\-prem environments (RISK‑03).
* Role‑based access control enforces least privilege per FR‑01 and FR‑03.

### US\-001 – Demographic Capture (Front Desk Clerk)
**Persona:** PER\-01
**Goal:** Capture patient demographics, insurance information, and medical history securely.

#### Acceptance Criteria (Given/When/Then)

| ID    | Given                                                                                                   | When                                                                                     | Then                                                                                                                                                                                                 |
|-------|--------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AC\-001 | The Front Desk Clerk is authenticated with role `front_desk` and has a valid TLS 1\.3 session.| The clerk enters valid values for all mandatory fields and clicks **Submit**.| The system encrypts each field with AES\-256\-GCM client‑side, sends ciphertext over HTTPS to `/api/intake`, stores it encrypted in PostgreSQL, creates an audit log entry referencing FR\-001 & NFR\-001, | and displays a success message with timestamp.|
| AC\-002 | The clerk submits a form where an address contains prohibited characters (e.g., `<script>`).   | The clerk clicks **Submit**.| The client‑side validator rejects the input, highlights the field, | and prevents transmission; no audit log is created.|
| AC\-003 | Network interruption occurs during submission after encryption but before server acknowledgment.| The client automatically retries up to three times.| On successful retry the record is stored and success message shown; if all retries fail an error message is displayed, | and a failure audit entry is recorded (edge case AC\-002).|
| AC\-004 | Encryption library unavailable on the client device.| Clerk attempts to submit the form.| Submission is aborted with message “Secure transmission unavailable”; no data is sent or logged.|

### US\-003 – Clinical Review & PDF Export (Clinician)
**Persona:** PER\-02
**Goal:** Review intake records and generate compliant PDF summaries.

### US\-004 – Deployment & Key Management (Administrator)
**Persona:** PER\-03
**Goal:** Deploy system securely and maintain key rotation.

## 3. Overview
This document defines the product‑level expectations for the **PatientIntake** SaaS solution. It captures user‑value‑driven features, user stories, acceptance criteria, and MVP scope while ensuring traceability to functional requirements (FR‑001 – FR‑003), non‑functional requirements (NFR‑003), and key performance indicators (KPI‑01, KPI‑04). All content is scoped to the product phase – no low‑level design or implementation details are included.

---

## 4. User Stories (Product Backlog)
| ID | Persona | Goal | Description |
|----|--------|------|-------------|
| **US-001** | Front Desk Clerk (PER‑01) | Capture demographic data securely | The clerk fills the patient intake form with name, DOB, address, and SSN. Upon submission the system validates required fields, encrypts PHI client‑side, stores ciphertext, and returns a success response within **200 ms** (KPI‑01). |
| **US-002** | Front Desk Clerk (PER‑01) | Capture insurance information | The clerk enters insurer name, policy number (max 20 chars), and optional group ID. Invalid insurer triggers a validation error "Provider not recognized" and logs the attempt without persisting PHI (FR‑002). Policy numbers longer than 20 chars cause a truncation error; missing group ID is handled as optional per FR‑002. |
| **US-003** | Clinician (PER‑02) | View patient summary read‑only | After authenticating as a clinician the user selects a patient record and clicks **View Summary**. The UI renders decrypted demographic and insurance data (server‑side decryption), creates an audit log entry of type **READ** with actor_id and timestamp (NFR‑003), and overlays a watermark "Confidential – Viewed by {clinician_id} at {timestamp}" on the PDF preview. |
| **US-010** | Front Desk Clerk (PER‑01) | Start Docker Compose stack | The clerk runs a single command (`docker compose up -d`) to launch the intake web form without manual container wiring. All containers start within 30 seconds and health endpoint returns HTTP 200 (FR‑001). |
| **US-011** | Administrator (PER‑03) | Load encryption keys before service start | The admin places encryption key files in `/run/secrets/` with mode 0400 owned by root. When `docker compose up` is executed the web service loads the keys successfully; logs contain "Encryption keys loaded" (FR‑002). |
| **US-012** | Clinician (PER‑02) | Verify audit logging for reads | While the system runs with RBAC enabled, the clinician accesses a patient record via UI. An audit entry is written containing user ID, timestamp, record ID, and action "READ" (NFR‑003). |
| **US-013** | Administrator (PER‑03) | Generate air‑gap deployment checklist | The admin runs `check_airgap.sh` which validates network isolation, firewall rules, and host hardening. Script outputs "PASS" and can be saved as PDF for auditors (RISK‑03 mitigation). |
| **US-014** | Front Desk Clerk (PER‑01) | Receive clear error on missing secrets | If Docker Compose fails due to a missing secret file, the CLI prints a concise error (`Missing secret file: /run/secrets/db_password`) and exits with non‑zero status; no containers remain running and an audit log records the failure (FR‑004). |

---

### 5.2 Insurance Capture – US‑002
| ID | Linked Requirement(s) | Given | When | Then |
|----|-----------------------|-------|------|------|
| **AC-003** | FR‑002, KPI‑04 | Valid insurer list loaded; TLS 1.3 active | Clerk enters an insurer not on the approved list and clicks **Submit** | System returns HTTP 400 with message "Provider not recognized", logs attempt without storing PHI, and does not create a patient record. |
| **AC-004** | FR‑002 | Policy number > 20 chars or missing group ID (optional) | Clerk submits form with overlong policy number or omits group ID | System returns HTTP 400 with specific error (`"Policy number exceeds maximum length"` or `"Group ID optional – omitted"`); audit log records VALIDATION_FAILURE; no PHI persisted. |
| **AC-005** | FR‑002 | All insurance fields valid; TLS 1.3 active | Clerk clicks **Submit** | Each field encrypted client‑side, transmitted securely, stored as ciphertext; audit log entry records CREATE operation with actor_id, timestamp, and reference to FR‑002; background job (`curl` wrapper) is triggered to verify insurer API connectivity. |

### 5.3 Clinician Read‑Only View – US‑003
| ID | Linked Requirement(s) | Given | When | Then |
|----|-----------------------|-------|------|------|
| **AC-006** | FR‑003, NFR‑003 | Clinician authenticated with role *clinician* and selects a patient record | Clinician clicks **View Summary** | UI renders decrypted data; audit log records READ action with watermark overlay; PDF preview includes watermark "Confidential – Viewed by {clinician_id} at {timestamp}". |
| **AC-007** | FR‑003, NFR‑003 | Clinician attempts to view a record they lack permission for | Clinician clicks **View Summary** | System returns HTTP 403 Forbidden with JSON `{ "error": "Access denied" }`; audit log records UNAUTHORIZED_ACCESS attempt. |
| **AC-008** | FR‑003, NFR‑003 | Decryption key missing on server | Clinician requests view | System displays error page "Data unavailable – contact admin"; audit log records FAILURE with error code 500. |

### 5.4 Docker Compose Stack – US‑010 & US‑011
| ID | Linked Requirement(s) | Given | When | Then |
|----|-----------------------|-------|------|------|
| **AC-009** | FR‑001 | Host has Docker Engine ≥ 20.10 and `docker-compose.yml` present | Clerk runs `docker compose up -d` | All containers (web, db, proxy) start in private network `intake_net`; health endpoint `/healthz` returns HTTP 200 within 30 seconds; audit log records STACK_START_SUCCESS. |
| **AC-010** | FR‑001 | One or more containers fail to start (e.g., image not found) | Clerk runs same command | CLI prints concise error (`"Image not found: nginx:1.23-alpine"`), exits non‑zero; no partial containers remain running; audit log records STACK_START_FAILURE. |
| **AC-011** | FR‑002 | Encryption key files exist at `/run/secrets/encryption_key` with mode 0400 owned by root | Administrator runs `docker compose up` | Web service loads keys successfully; logs contain "Encryption keys loaded"; startup proceeds without warning; audit log records KEY_LOAD_SUCCESS. |
| **AC-012** | FR‑002 | Keys missing or incorrect permissions | Administrator runs `docker compose up` Startup aborts; error message references HIPAA §164.312(a)(2)(iv); audit log records STARTUP_ABORT – MISSING_KEYS; exit code non‑zero. |

### 5.5 Audit Logging Verification – US‑012
| ID | Linked Requirement(s) | Given | When | Then |
|----|-----------------------|-------|------|------|
| **AC-013** | NFR‑003 | System running with RBAC enabled | Clinician accesses any patient record | Audit entry written containing user ID, timestamp, record ID, action "READ"; entry conforms to schema `{ actor_id, action_type, timestamp, affected_record_id }`. |

### 5.6 Air‑Gap Checklist – US‑013
| ID | Linked Requirement(s) | Given | When |
|----|-----------------------|-------|
| **AC-014** | RISK‑03 | Administrator runs `check_airgap.sh` script Script validates no external network interfaces, verifies iptables rules block outbound traffic, confirms host OS patches applied; outputs "PASS"; result can be saved as PDF for auditors. |

### 5.7 Secret Missing Error – US‑014
| ID | Linked Requirement(s) |
|----|-----------------------|
| **AC-015** | FR‑004 (new requirement for secret handling) | Clerk runs `docker compose up` with missing secret file `/run/secrets/db_password` CLI prints `Configuration error: secret db_password not found`; process exits code 1; no containers remain running; audit log records CONFIG_ERROR. |

---

## 6. Design Needs (Downstream Design Phase)
* **Encryption Algorithm:** AES‑256‑GCM client‑side for PHI fields.
* **Key Exchange:** ECDH based session key derivation.
* **Audit Log Schema:** `{ actor_id:string, action_type:string, timestamp:ISO8601, affected_record_id:string }`.
* **Docker Service Names:** `web`, `db`, `proxy` on isolated bridge network `intake_net`.
* **Secret Injection:** Docker secrets mounted from `/run/secrets/`.
* **Health Checks:** `/healthz` returning HTTP 200 when all dependent services are ready.
* **Air‑Gap Verification Script Requirements:** Bash script using `ss`, `iptables`, and OS package version checks.

---

## 7. Deployment Steps (High-Level Guide)
1️⃣ Verify host prerequisites: Docker Engine ≥ 20.10, Docker Compose v2+, OS security patches applied.
2️⃣ Place secret files (`db_password`, `encryption_key`) in `/run/secrets/` with mode 0400 owned by root.
3️⃣ Review `docker-compose.yml` for correct image tags (`nginx:1.23-alpine`, `postgres:15-alpine`).
4️⃣ Run `docker compose up -d`. Monitor logs for "Encryption keys loaded" and health endpoint readiness.
5️⃣ Execute `check_airgap.sh` to confirm air‑gap compliance before production use.
6️⃣ Perform functional smoke test: submit demographic form → verify response time <200 ms; submit insurance → verify validation errors; clinician view → verify watermark and audit log entry.

---

## 8. Traceability Matrix
| Artifact ID | Requirement ID(s) |
|------------|-------------------|
| US-001    | FR-001, KPI-01   |
| US-002    │ FR-002, KPI-04   │ │ US-003    │ FR-003, NFR-003 │ │ US-010    │ FR-001          │ │ US-011    │ FR-002          │ │ US-012    │ NFR-003         │ │ US-013    │ RISK-03         │ │ US-014    │ FR-004          │ |

---

*All user stories and acceptance criteria have been aligned to existing functional requirements (FR-*), non-functional requirements (NFR-*), key performance indicators (KPI-*), and identified risks.*

## Feature Specification – Patient Intake System

### Acceptance Criteria

**US‑001 – Secure Demographic Capture**
- **Given** the clinical staff is authenticated with least‑privilege role,
- **When** they submit the patient demographic form,
- **Then** the data is encrypted at rest using AES‑256 and stored in the PostgreSQL `patients` table.
- **And** an audit entry is created in `audit_log` table with operation type `CREATE`, timestamp, and user ID.

**US‑002 – Patient Insurance Submission**
- **Given** the patient accesses the secure HTTPS endpoint `/api/v1/insurance`,
- **When** they POST a JSON payload containing `policy_number`, `provider`, and `effective_date`,
- **Then** the system validates the payload against schema FR‑005 and returns `200 OK` on success or `400 Bad Request` with error details.

**US‑003 – Audit Log Verification**
- **Given** a compliance officer accesses the audit UI,
- **When** they filter logs by date range and operation type,
- **Then** the UI displays entries matching FR‑010 and NFR‑003 requirements, and each entry includes user ID, timestamp, and operation details.

### API Endpoint Definitions

| Method | Path               | Description                                 | Related Requirement |
|--------|--------------------|---------------------------------------------|---------------------|
| GET    | `/healthz`          | Health check returning 200 if service healthy within 30 seconds. | FR‑009 |
| POST   | `/api/v1/patient`  | Create new patient record (demographics).                     | FR‑001 |
| POST   | `/api/v1/insurance`| Submit insurance information.                                   | FR‑005 |
| GET    | `/api/v1/audit`    | Retrieve audit log entries (filterable).                        | FR‑010 |

### Edge Cases & Failure Handling

| Scenario                     | Detection                                            | Response                                                                 |
|------------------------------|------------------------------------------------------|--------------------------------------------------------------------------|
| Missing Docker Engine        | Startup script checks for `docker` binary.         | Abort with message “Docker Engine not found – install from official repository.” |
| Corrupted secret file         | SHA256 checksum verification fails on container start.| Abort and log “Secret file checksum mismatch – regenerate secret.” |
| Network port conflict (e.g., 5432) | Script attempts to bind; catches `EADDRINUSE`. -| Abort with error “Port 5432 already in use – resolve conflict.” |
| Audit logging failure         | DB insert returns error.                            | Return HTTP 500 with message “Audit logging failed – contact support.” |

### MVP Scope

The Minimum Viable Product includes:
1. Secure demographic capture (US‑001) with encryption and audit logging.
2. Patient insurance submission (US‑002) with validation.
3. Basic audit log view (US‑003) satisfying NFR‑003.
4. Health check endpoint (`/healthz`) for service monitoring.
5. Docker Compose deployment guide (referencing FR‑009).
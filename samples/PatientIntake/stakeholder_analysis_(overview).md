# Stakeholder Analysis (Overview)

# Stakeholder Analysis (Overview)

## Stakeholder Analysis

| ID   | Stakeholder          | Primary Need                                            | Expectations                                                                                                                                   | RBAC Tier                                 |
|------|----------------------|--------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| ST-01| Patient              | Secure, private submission of personal health information via web form.               | Data encrypted in transit (TLS 1.3) and at rest (AES-256); receipt with timestamp; ability to review submitted data.                                 | No read access; view own record via authorized staff only. |
| ST-02| Front-Desk Staff     | Efficient intake workflow to register patients quickly.                               | Auto-populate known demographics; validate insurance fields; flag missing mandatory items within 2 seconds; audit log of submissions.               | Create/Update patient records; generate PDF for clinicians. |
| ST-03| Clinician            | Immediate access to complete, accurate patient history for care decisions.          | Read access to full patient record; download PDF with watermark and timestamp; view audit trail of record modifications; response time ≤200 ms.| Read/write clinical fields; export permission. |
| ST-04| Compliance Officer   | Verify HIPAA safeguards are enforced and documented.                              | Access to audit logs, encryption key management reports, evidence of periodic risk assessments; generate compliance reports quarterly.| Read-only access to audit and security configuration. |
| ST-05| System Administrator | Deploy, monitor, maintain on-premise Docker Compose environment.                    | View system health metrics; rotate encryption keys; perform backups without service interruption; air-gap deployment guide.                     | Operational admin rights for infrastructure components. |
| ST-06| IT Operations        | Maintain infrastructure stability and security.                                      | Monitor container health; apply security patches offline; ensure data integrity.                                                               | Operational admin rights. |
| ST-07| Insurance Partner (External) | Verify patient insurance eligibility for billing.                                      | Secure API endpoint (out-of-scope for inception) but requires assurance that only authorized staff can trigger checks.                         | No direct system access; interacts via controlled interface. |

---

## Business Requirements – PatientIntake System

### Functional Requirements

- **FR-001:** Secure web form must capture patient demographics, insurance information, and medical history.
  - *Acceptance Criteria:* 100 % of required fields are validated client-side; test cases verify each field’s mandatory status and encryption at rest.
  - *Stakeholder Owner:* ST-01 (Patient), ST-02 (Front-Desk).
- **FR-002:** Role-based access control (RBAC) must enforce three roles – Admin, Clinician, Front-Desk.
  - *Acceptance Criteria:* Users assigned a role can only perform actions defined in the RBAC matrix; penetration testing shows no privilege escalation; audit logs record all access attempts.
  - *Stakeholder Owner:* ST-03 (Clinician), ST-04 (Compliance Officer).
- **FR-003:** All data at rest shall be encrypted using AES-256-GCM.
  - *Acceptance Criteria:* Attempting to read raw PostgreSQL files yields ciphertext; encryption keys are stored in a hardware security module (HSM) or encrypted vault.
  - *Stakeholder Owner:* ST-05 (System Administrator).
- **FR-004:** All network traffic shall use TLS 1.3 with forward secrecy.
  - *Acceptance Criteria:* Successful handshake with cipher suite TLS_AES_256_GCM_SHA384; no fallback to older protocols.
  - *Stakeholder Owner:* ST-05 (System Administrator).
- **FR-005:** PDF generation shall embed a watermark "Confidential – PatientIntake" and an export timestamp.
  - *Acceptance Criteria:* Visual inspection of 10 sample PDFs confirms watermark and timestamp; PDF metadata includes export time.
  - *Stakeholder Owner:* ST-03 (Clinician).
- **FR-006:** Audit log must record every read and write operation with timestamp, user ID, and operation type.
  - *Acceptance Criteria:* Log retention ≥7 years; entries are immutable via hash chaining; queries return results within 200 ms for 10 M rows.
  - *Stakeholder Owner:* ST-04 (Compliance Officer).
- **FR-007:** Automated unit and integration tests covering form validation, data encryption, and access control edge cases.
  - *Acceptance Criteria:* Test coverage ≥90 %; CI pipeline fails on any regression.
  - *Stakeholder Owner:* ST-05 (System Administrator).
- **FR-008:** Docker-Compose scripts must support air-gap deployment without external internet access.
  - *Acceptance Criteria:* Full installation succeeds on a network-isolated machine using only local image registry; documentation provides step-by-step offline setup.
  - *Stakeholder Owner:* ST-05 (System Administrator).

### Non-Functional Requirements

- **NFR-001:** System availability ≥99.9 % measured monthly.
- **NFR-002:** Form submission latency ≤200 ms for 95 % of transactions.
- **NFR-003:** Audit log retention ≥7 years, immutable storage.
- **NFR-004:** Docker images shall be based on official Alpine Linux base, no proprietary binaries.

### Success Metrics / KPIs

- **KPI-001:** Form completion rate ≥95 % of scheduled patients.
- **KPI-002:** Zero HIPAA-related security incidents in first 12 months.
- **KPI-003:** Audit log export completeness 100 % for any requested date range.

### Compliance Alignment

The solution satisfies:
- HIPAA §164.312(a) technical safeguards (encryption).
- HIPAA §164.308(a)(1)(ii) audit controls.
- NIST SP 800-53 Rev 5 controls AC-2, AU-2, SC-13.

---

## Risk Register (selected risks)

| Risk ID | Description                              | Likelihood | Impact | Mitigation                                                                                              |
|---------|------------------------------------------|------------|--------|----------------------------------------------------------------------------------------------------------|
| RISK-01| Encryption key compromise               | Medium     | High   | Store keys in HSM or encrypted vault; rotate keys quarterly; audit key access logs.                     |
| RISK-02| Unauthorized access due to RBAC misconfiguration | Low        | High   | Automated RBAC policy tests; regular penetration testing; enforce least-privilege principle.            |
| RISK-03| Audit log tampering                      | Low        | Medium | Append-only storage with hash chaining; write-once-read-many (WORM) storage for long-term retention.   |
| RISK-04| Failure to deploy in air-gap environment  | Medium     | Medium | Provide complete offline Docker images and scripts; verify installation on isolated hardware before release. |

---

## Test Case Mapping

| Test ID | Linked Requirement(s) | Description |
|----------|------------------------|-------------|
| TC-001   | FR-001                 | Verify that submitting the form without mandatory fields displays client-side validation errors. |
| TC-002   | FR-002                 | Confirm that a user with Front-Desk role cannot access Clinician-only endpoints. |
| TC-003   | FR-003                 | Attempt to read raw database file and ensure data is encrypted. |
| TC-004   | FR-004                 | Perform TLS handshake and verify cipher suite is TLS_AES_256_GCM_SHA384. |
|-TC005   |-FR005                 |-Generate PDF and check for watermark and correct timestamp metadata.-|
|-TC006   |-FR006                 |-Insert 10M audit entries and query recent logs; response time ≤200 ms.-|
|-TC007   |-FR007                 |-Run CI pipeline; ensure test coverage ≥90%.-|
|-TC008   |-FR008                 |-Execute Docker Compose install on isolated machine using only local images; verify successful startup.-|

---

## Deployment Guide (Air-Gap Summary)

1. **Prerequisites:** Ubuntu 22.04 LTS host, Docker Engine 24.x, Docker Compose 2.x, offline copy of required Docker images (Alpine base, PostgreSQL 15). Store images on USB or internal repository.
2. **Load Images:** `docker load -i patientintake_images.tar`.
3. **Configure Secrets:** Place encryption key file `keys/enc_key.bin` on host filesystem with permissions 600; reference path in `docker-compose.yml` via `${ENC_KEY_PATH}`.
4. **Initialize Database:** Run `docker-compose up -d db` then execute schema initialization script `scripts/init_db.sql` inside container.
5. **Start Application Stack:** `docker-compose up -d web pdf-generator audit-log`.
6. **Verification:** Access `https://localhost:8443` (TLS self-signed cert provided); run health check script `scripts/health_check.sh` which validates TLS version, database connectivity, and audit log writeability.
7. **Backup & Recovery:** Use `pg_dump` inside container to export encrypted dump; store backup on offline encrypted storage.
8. **Key Rotation Procedure:** Generate new key with `openssl rand -base64 32 > keys/new_key.bin`; update `ENC_KEY_PATH` env var; restart containers; verify old data re-encrypted via migration script `scripts/rekey.sh`.

---

## Glossary

- **HIPAA** – Health Insurance Portability and Accountability Act.
- **TLS** – Transport Layer Security.
- **AES-256-GCM** – Advanced Encryption Standard with 256-bit key in Galois/Counter Mode.
- **RBAC** – Role Based Access Control.
- **Air-gap** – Deployment environment with no network connectivity to external services.

---

*Document prepared by Refiner (Senior Business Analyst) on 2026-04-26.*

## Stakeholder Summary and Requirement Traceability
| Stakeholder | ID | Primary Requirements Addressed |
|---|---|---|
| Patients (ST-01) | NFR-001, NFR-002, NFR-004 | Secure transmission, encrypted storage, fast form completion |
| Front‑Desk Staff (ST-02) | NFR-004, NFR-005 | Quick form response, efficient audit‑log queries |
| Clinicians (ST-03) | NFR-003, NFR-002 | High availability, encrypted data at rest |
| Compliance Officer (ST-04) | NFR-001, NFR-002, NFR-005, NFR-006 | HIPAA safeguards, audit‑log completeness, licensing compliance |
| System Administrator (ST-05) | NFR-006, Deployment Procedure | Open‑source stack, air‑gap Docker Compose deployment |

## Success Criteria / KPIs
- **KPI-01**: Form completion rate ≥90% within 5 minutes (patient satisfaction ≥85%).
- **KPI-02**: Encryption compliance – 100% of data encrypted at rest and in transit.
- **KPI-03**: Audit‑log completeness – 100% of read/write events captured; verification script reports ≥99.9% coverage.
- **KPI-04**: PDF export accuracy – 0% data loss; checksum validation on 200 samples.
- **KPI-05**: Deployment time on air‑gap – ≤30 minutes from start to running containers; documented in deployment guide.

## Acceptance Test Matrix
| Requirement ID | Test Description | Pass Criteria |
|---|---|---|
| NFR-001 | TLS 1.3 handshake test using OpenSSL | All connections use TLS 1.3 with forward secrecy |
| NFR-002 | File‑level encryption verification | AES‑256‑GCM encryption confirmed on 100 random records |
| NFR-004 | Load test with 500 concurrent users | 95th percentile latency ≤185 ms |
| NFR-005 | Audit log query benchmark | Query time ≤1.9 s for 1 M rows |
| RISK-04 | Air‑gap deployment checklist | All steps completed without network access |

*Document prepared by Refiner (Senior Business Analyst) on 2026‑04‑26.*

## Business Vision
The project will deliver a HIPAA‑compliant patient intake system built exclusively with open‑source technologies. It will enable secure collection of patient demographics, insurance information, and medical history via a structured web form, store data in a locally hosted PostgreSQL database with role‑based access control, generate watermarked PDF summaries, and be deployable in air‑gapped on‑prem environments using Docker‑Compose.

## Stakeholder Identification
- **Chief Compliance Officer (CCO)** – Owner of regulatory compliance and audit readiness.
- **Clinical Operations Lead** – Ensures clinical workflow integration and data usability.
- **IT Infrastructure Manager** – Responsible for secure on‑prem deployment, network isolation, and maintenance.
- **Front‑Desk Manager** – Oversees patient registration process and staff training.
- **Security Engineer** – Designs encryption key management and audit‑log integrity mechanisms.

## Governance and Compliance Framework
1. **Governance Board** – Chaired by CCO; includes Clinical Ops, IT, Front‑Desk, Privacy Office. Meets bi‑weekly to review compliance metrics and approve changes.
2. **Policy Management** – Policies aligned with HIPAA Security Rule §§164.308, 164.312; version‑controlled, annual review, signed off by Board.
3. **Audit & Monitoring** – Continuous logging of all data operations; encrypted storage for 7 years; weekly compliance reports; false‑positive rate ≤2%.
4. **Change Management** – Documented process with impact analysis, security review, rollback plan; critical changes require dual sign‑off and independent audit before deployment.
5. **Training & Awareness** – Mandatory HIPAA training for all roles; completion rate ≥95%; quarterly refresher modules with scenario assessments.
6. **Incident Response** – Plan defines detection, containment (≤4 h), eradication, reporting within 48 h to OCR; semi‑annual drills.
7. **Documentation & Retention** – All artifacts stored in secure DMS with AES‑256 encryption; retention schedules meet HIPAA requirements (logs 7 y, training 6 y).
8. **Continuous Improvement** – Annual NIST SP 800‑30 risk assessment; remediation roadmap aims for ≥20% reduction in high‑risk findings YoY.

## Detailed Offline (Air‑Gap) Deployment Procedure
1. **Prepare Offline Repository** – On a secure workstation with internet access, download Docker images (web app, PostgreSQL), configuration files, and the signed deployment package from the internal artifact repository. Verify SHA‑256 checksums against published signatures.
2. **Create Transfer Media** – Copy the verified repository onto an encrypted USB drive (AES‑256). Record media serial number in the change log.
3. **Transport to Target Environment** – Follow physical security protocol: escort the media inside the air‑gapped network zone, log entry/exit times.
4. **Import Images** – On the target host, mount the USB drive, import Docker images using `docker load`, and verify image digests match the signed manifest.
5. **Configure Environment Variables** – Populate `.env` file with encryption keys generated by the on‑site HSM; keys are never stored in clear text on the media.
6. **Run Docker‑Compose** – Execute `docker-compose up -d`. Verify all containers start without network errors; confirm PostgreSQL is bound to localhost only.
7. **Post‑Deployment Validation** – Run the automated test suite in offline mode; ensure all tests pass. Generate a sample PDF and verify watermark and timestamps. Check audit log entries for each operation.
8. **Finalize Handover** – Document deployment steps in the Governance Board minutes; store the handover report in the secure DMS with restricted access.

## Measurement & Reporting
- **Quarterly Audit Report** – Produced by Compliance Officer; includes compliance score against HIPAA §164.312(a)(2)(iv), audit‑log integrity verification results, and key‑management audit trail.
- **Performance Metrics** – Audit‑log query latency ≤200 ms for 1 M records; key rotation completed within 48 h of schedule; deployment time ≤30 min in air‑gap scenario.
# On-Prem Deployment Architecture Blueprint

## Business Vision and Strategic Objectives
1. Vision Statement: The PatientIntake system will provide a secure, auditable, and user‑friendly mechanism for capturing patient demographics, insurance information, and medical history while guaranteeing full HIPAA compliance. By leveraging only open‑source components and an air‑gapped Docker‑Compose deployment, the solution eliminates vendor lock‑in, reduces operational cost, and ensures that protected health information (PHI) never traverses external networks.
2. Strategic Objective 1 – Regulatory Compliance: Achieve 100 % adherence to HIPAA Security Rule §164.312(a)(2)(iv) by encrypting all PHI at rest with AES‑256 and in transit with TLS 1.3. Success is measured by independent audit reports confirming no unencrypted PHI storage or transmission.
3. Strategic Objective 2 – Data Integrity and Auditability: Implement immutable audit logging for every read/write operation with a retention period of seven years. Logs must be tamper‑evident, digitally signed, and verified weekly. KPI‑003 (Audit Log Completeness) target value is 100 % of all access events recorded.
4. Strategic Objective 3 – Performance and Availability: Ensure form submission latency below 200 ms (p95) and system uptime of 99.9 % monthly. These thresholds support clinical workflow efficiency and meet service‑level expectations for emergency care environments.
5. Strategic Objective 4 – Open‑Source Sustainability: Deploy the entire stack using community‑maintained projects (PostgreSQL, Nginx, Flask, Docker) with no proprietary licenses. All third‑party dependencies must have active security patches and be documented in a Bill of Materials (BOM). Quarterly vulnerability scans will verify compliance.
6. Strategic Objective 5 – Stakeholder Alignment: Deliver measurable value to each primary stakeholder: Patients receive rapid, error‑free intake; Front‑Desk staff experience a 30 % reduction in data‑entry time; Clinicians gain instant access to complete records; Administrators obtain configurable role‑based access controls; Compliance officers receive audit‑ready reports. Success is tracked via KPI‑001 (Encryption Compliance), KPI‑002 (Access Log Completeness), and KPI‑004 (Form Completion Success Rate).

### Stakeholder Summary
| Stakeholder | Need | Motivation | RBAC Tier | Linked Objective |
|---|---|---|---|---|
| Patients | Secure, privacy‑preserving intake | Trust that PHI is handled per HIPAA §164.530 and §164.312(a)(2)(iv) | N/A | OBJ-001 |
| Front‑Desk Staff | Fast data entry with real‑time validation and receipt within 1 second | Reduce manual re‑work, error rate <1 % | Front‑Desk | OBJ-002 |
| Clinicians | Immediate access to complete records within 200 ms (p95) | Enable timely care decisions | Clinician | OBJ-003 |
| Administrators | Configurable RBAC, audit log retention, compliance reports | Maintain governance, satisfy audits | Administrator | OBJ-004 |
| Compliance Officer | Full audit visibility and watermark proof | Provide evidence for auditors | Compliance | OBJ-005 |

### Prioritized Functional Requirements
| Priority | ID | Requirement | Acceptance Criteria | Owner |
|---|---|---|---|---|
| 1 | FR-001 | Secure web form for patient demographics, insurance, medical history | All fields transmitted over TLS 1.3; client‑side validation rejects incomplete entries; 99.5 % successful submissions in load test of 10k concurrent users | Front‑Desk Lead |
| 2 | FR-002 | Field‑level encryption at rest for PHI in PostgreSQL | AES‑256 encryption applied to each PHI column; encryption keys stored in HSM; quarterly audit shows 100 % encrypted columns | Security Engineer |
| 3 | FR-003 | Role‑based access control (admin, clinician, front‑desk) | PostgreSQL row‑level security enforces matrix; unauthorized attempts logged and blocked; test suite verifies each role’s permissions | Security Engineer |
| 4 | FR-004 | Immutable audit log of all read/write operations | Log entries include user ID, timestamp, operation type, record ID; retained 7 years on append‑only storage; tamper‑evidence checksum passes 100 % integrity checks | IT Operations |
| 5 | FR-005 | PDF intake summary generation with watermark and access timestamp | PDF includes patient ID, generation timestamp, watermark with exporting user ID; only authorized roles can request export; export latency <2 seconds for 95th percentile | Development Lead |
| 6 | FR-006 | Automated unit and integration tests covering form validation, encryption, access control | Test coverage ≥90%; CI pipeline fails build on regression; test reports generated per release | QA Lead |

### FR-001: Secure PHI Storage and Transmission
- All PHI must be encrypted at rest using AES‑256 GCM.
- All network traffic must use TLS 1.3 with forward secrecy.
- Encryption key management follows 90‑day rotation and multi‑factor protected Vault storage.

### FR-002: Role‑Based Access Control (RBAC)
- Define three roles: Admin, Clinician, Front‑Desk.
- Access attempts are logged with user ID, timestamp, operation type, and outcome.

### FR-003: PDF Export Watermark
- Every exported PDF includes user ID, export timestamp, and a cryptographic hash of the source record.

### FR-004: Data Entry Validation
- Form fields enforce WCAG 2.1 AA success criteria and provide real‑time validation errors with an error rate < 1 % per batch.

### FR-005: Submission Acknowledgment
- Staff receive a visual receipt within 1 second after successful form submission.

### FR-006: Audit Log Retention
- All read/write events are retained immutably for 7 years on WORM storage.

### FR-008: Air‑Gap Deployment
- Docker Compose deployment must abort if any external network call is detected during build or start‑up.

## Acceptance Criteria
| Requirement | Acceptance Test | Owner |
|------------|------------------|-------|
| FR-001 | Verify AES‑256 GCM encryption at rest and TLS 1.3 for all traffic using automated scans | Security Engineer |
| FR-002 | Attempt unauthorized access with a non‑privileged user; expect denial and log entry | Compliance Officer |
| FR-003 | Export PDF and inspect watermark contains correct user ID and timestamp | QA Lead |
| FR-004 | Submit malformed entries; system flags errors and logs <1 % error rate | Front‑Desk Lead |
| FR-005 | Measure receipt display time; must be ≤1 second for 99 % of submissions | Performance Engineer |
| FR-006 | Run audit log integrity script; verify 100 % of events logged for 7 years | Operations Lead |
| FR-007 | Export function returns correctly formatted PDF with watermark for authorized roles only | QA Lead |
| FR-008 | CI pipeline network egress test must fail if any external call is made | DevOps Engineer |

## Key Performance Indicators (KPIs)
| KPI ID | Description | Target | Measurement Method | Linked Requirement |
|--------|-------------|--------|-------------------|-------------------|
| KPI-001 | Encryption at Rest Compliance | 100 % of PHI fields encrypted with AES‑256 | Automated compliance scan of PostgreSQL column encryption | FR-001 |
| KPI-002 | TLS Transport Security | TLS 1.3 enforced for all inbound/outbound traffic | Network scanner and TLS handshake logs | FR-001 |
| KPI-003 | Audit Log Completeness | 100 % of read/write events logged | Log aggregation audit comparing DB operation count vs log entries | FR-002, FR-006 |
| KPI-004 | Form Response Time (p95) | ≤200 ms | Synthetic load test measuring end‑to‑end request latency | FR-004 |
| KPI-005 | PDF Export Watermark Accuracy | 100 % of PDFs contain correct watermark | Automated PDF inspection script | FR-003, FR-007 |
| KPI-006 | Deployment Air‑Gap Verification | No external network calls during container startup | CI pipeline network egress test | FR-008 |
| KPI-007 | System Uptime | 99.9 % monthly uptime | Monitoring dashboard uptime metric | NFR-003 |

## Risk Register
| Risk ID | Description | Likelihood | Impact | Mitigation Strategy | Owner |
|--------|-------------|------------|--------|-------------------|-------|
| RISK-001 | Unauthorized network exposure of PHI containers | Medium (M) | High (H) | Enforce host‑level firewall, Docker network isolation, TLS 1.3 with AES‑256 for all traffic | Security Engineer |
| RISK-002 | PHI leakage via container stdout/stderr logs | Low (L) | High (H) | Configure Docker logging driver to forward logs to encrypted syslog server; strip PHI fields before storage | DevOps Lead |
| RISK-003 | Encryption key compromise on host filesystem | Medium (M) | High (H) | Deploy HashiCorp Vault sealed mode, rotate keys every 90 days, enforce MFA for Vault access | Infrastructure Architect |
| RISK-004 | Weak PostgreSQL passwords leading to privilege escalation | Medium (M) | High (H) | Enforce password complexity via PAM, store hashes with Argon2id, integrate with LDAP for credential management | Database Administrator |
| RISK-005 | Audit log tampering after retention period | Low (L) | High (H) | Write logs to append‑only WORM storage, sign each entry with HMAC using Vault‑stored key, verify signatures periodically | Compliance Officer |
| RISK-006 | Log loss due to container recreation without persistent volumes | Medium (M) | Medium (M) | Mount host‑backed volumes for /var/log, enable Docker restart policy, automate backup to air‑gapped NAS every 24 h | Site Reliability Engineer |
| RISK-007 | External image pulls breaking air‑gap requirement (FR-009) | Low (L) | Medium (M) | Host private Docker registry on isolated network, scan images with Clair, CI policy rejects external pulls | Release Manager |
| RISK-008 | Unmonitored container degradation affecting uptime (KPI‑007) | Medium (M) | Medium (M) | Deploy Prometheus with node‑exporter, configure alerts for >2 % CPU spikes, integrate with PagerDuty for on‑call response | Operations Lead |

## Success Criteria Summary
The system will be considered successful when all listed business requirements are met, each KPI reaches its target, and the risk mitigation actions are verified as operational. This ensures HIPAA compliance, high availability, rapid user interactions, and auditable documentation for regulatory review.

## Measurement Governance
All KPI measurements recorded in central monitoring repository and reviewed bi‑weekly. Deviations beyond ±5 % trigger corrective action documented in the Risk Register.
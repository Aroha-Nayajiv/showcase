# Compliance Requirements (Overview)

## Additional Notes
All functional and non-functional requirements now include measurable acceptance criteria and explicit stakeholder ownership. Risk mitigations have been expanded with concrete actions and verification steps.

### REQ-001: Field‑level encryption at rest
**Description:** All PHI fields shall be encrypted at rest using AES‑256‑GCM.
**Stakeholder Owner:** Compliance Officer
**Acceptance Criteria:** Automated scans detect zero plaintext PHI; encryption strength ≥256 bits; encryption applied to all PHI columns in PostgreSQL.

### REQ-002: TLS 1.3 in‑transit protection
**Description:** All network traffic containing PHI shall be protected using TLS 1.3 with forward secrecy.
**Stakeholder Owner:** IT Operations
**Acceptance Criteria:** Scans verify TLS 1.3 handshake; no TLS 1.2 or lower connections permitted.

### REQ-003: Encryption key rotation
**Description:** Encryption keys shall be rotated every 90 days and logged.
**Stakeholder Owner:** Security Team
**Acceptance Criteria:** Rotation logs show successful rotation every 90 days with zero failures; keys stored in HashiCorp Vault; audit log entry created for each rotation.

### REQ-004: Immutable audit logging
**Description:** Every read, write, update, and delete operation on PHI shall generate an immutable audit log entry.
**Stakeholder Owner:** Compliance Officer
**Acceptance Criteria:** pg_audit records contain timestamp (UTC), user ID, role, operation type, record ID; logs are signed with HMAC‑SHA256; retention ≥7 years; integrity verified daily via hash chain.

### REQ-005: Role‑based access control (RBAC)
**Description:** System shall enforce RBAC with three roles: Admin, Clinician, Front‑Desk.
**Stakeholder Owner:** IT Operations
**Acceptance Criteria:** PostgreSQL row‑level security policies enforce column‑level permissions; quarterly access reviews confirm correct role assignments; any RBAC change creates audit entry.

### REQ-006: PDF summary generation with watermark
**Description:** Authorized staff may generate a PDF intake summary containing a visible watermark and export timestamp.
**Stakeholder Owner:** Clinicians
**Acceptance Criteria:** PDF includes watermark text "Confidential – PHI"; creation timestamp recorded; only users with Clinician or Admin role can export; export action logged.

### REQ-007: Automated testing
**Description:** Unit and integration tests shall cover form validation, encryption, and access control edge cases.
**Stakeholder Owner:** Development Team
**Acceptance Criteria:** Test suite achieves ≥90 % code coverage; CI pipeline fails on any test failure.

### REQ-008: Docker Compose air‑gap deployment
**Description:** Entire stack shall be deployable via Docker Compose on an isolated VLAN with no external internet access.
**Stakeholder Owner:** IT Operations
**Acceptance Criteria:** `docker compose up` brings up all containers; network isolation verified; deployment guide validated on disconnected network.

## Success Criteria / KPIs
- KPI‑01: 100 % of PHI fields encrypted at rest.
- KPI‑02: Zero TLS handshake failures in production.
- KPI‑03: Key rotation performed automatically every 90 days with 0 failures (KPI‑05).
- KPI‑04: Incident response time ≤15 minutes; full remediation ≤4 hours (KPI‑06).
- KPI‑05: User satisfaction ≥90 % among front‑desk staff and clinicians (KPI‑07).

## Stakeholder Needs
- **Patient (ST-01)**: Assurance that personal health information is protected and that the intake process is quick, accessible, and WCAG‑2.1 AA compliant.
- **Front‑Desk Staff (ST-02)**: Intuitive web form that enables registration of a patient within 2 minutes, with minimal data‑entry errors.
- **Clinician (ST-03)**: Immediate access to complete, accurate patient histories with response time <200 ms.
- **System Administrator (ST-04)**: Ability to configure RBAC, monitor immutable audit logs, and apply security patches without service disruption.
- **Compliance Officer (ST-05)**: Evidable controls for encryption, key rotation, audit‑log retention, and regular compliance reporting.

## Governance and Compliance
- Encryption Policy: AES-256-GCM at rest, TLS 1.3 in transit (HIPAA §164.312(a)(2)(iv)).
- Audit Logging Policy: Immutable logs per HIPAA §164.312(b) retained 7 years.
- Key Management Policy: Rotation per HIPAA §164.308(a)(1)(ii) using Vault.
- Incident Response Plan: 24/7 monitoring, breach notification within 30 min.
- Governance Board: CISO, Compliance Officer, Clinical Lead, IT Ops Manager.

## Requirements Traceability Matrix
| Requirement ID | Description | Stakeholder | Acceptance Criteria |
|---|---|---|---|
| FR-001 | Collect patient demographics, insurance, medical history via web form | ST-01, ST-02 | 100% mandatory fields completed; inline validation errors displayed |
| FR-002 | Field‑level encryption at rest (AES‑256) | ST-01, ST-05 | Encryption algorithm AES‑256 GCM; decryption test vector passes |
| FR-003 | Transport security TLS 1.3 | ST-01, ST-05 | SSL Labs A+; no TLS 1.0/1.1 allowed |
| FR-004 | Role‑based access control (admin, clinician, front‑desk) | ST-03, ST-04 | Admin read/write all; Clinician read all/write notes; Front‑Desk create only |
| FR-005 | Immutable audit log for every read/write | ST-04, ST-05 | Log entry includes user ID, timestamp, operation type, record ID; append‑only table with hash chain |
| FR-006 | PDF summary generation with watermark and timestamp | ST-01, ST-03 | PDF contains visible watermark \"Confidential – PatientIntake\" and export timestamp within ±1 sec |
| FR-007 | Automated unit/integration tests covering validation, encryption, RBAC, PDF | ST-04 | ≥90% code coverage; CI pipeline passes |
| FR-008 | Docker Compose deployment for on‑prem air‑gap | ST-04 | `docker compose up` brings up all services; no external network required |
| NFR-001 | Form submission latency ≤200 ms (p95) | ST-02, ST-03 | Load test 100 concurrent users meets target |
| NFR-002 | System uptime ≥99.9 % monthly | ST-04 | Health‑check logs show uptime |
| NFR-003 | Data at rest encryption complies with HIPAA §164.312(a)(2)(iv) | ST-05 | Independent audit confirms AES‑256 usage |
| NFR-004 | Transport security TLS 1.3 with forward secrecy | ST-05 | Automated scan verifies TLS 1.3 only |
| NFR-005 | Audit log retention ≥7 years | ST-05 | Log archival policy enforced; logs immutable

## Documentation Deliverables
- Business Vision Statement (this section).
- Stakeholder Needs Mapping.
- Requirements Traceability Matrix.
- Risk Register with mitigations.
- KPI Dashboard definitions.

## Business Requirements
| ID | Requirement | Acceptance Criteria |
|----|------------|---------------------|
| REQ-001 | All PHI fields must be encrypted at rest using AES-256-GCM. | Automated scans verify no plaintext PHI in database; decryption test vectors succeed.
| REQ-002 | Data in transit must use TLS 1.3 with forward secrecy. | Network scan shows only TLS 1.3; handshake fails for lower protocols.
| REQ-003 | Role-based access control (admin, clinician, front-desk) with least-privilege. | Unauthorized role cannot read or modify PHI; access matrix tests passed.
| REQ-004 | Immutable audit log for every read/write operation. | Log entry includes user ID, timestamp UTC, operation type, record ID; hash-chain verification passes.
| REQ-005 | Generate PDF intake summary with visible watermark and export timestamp. | PDF contains watermark "Confidential – PatientIntake" and timestamp metadata; only authorized roles can download.
| REQ-006 | Automated unit and integration tests covering form validation, encryption, RBAC edge cases. | Test suite achieves ≥90% coverage; CI fails on regression.
| REQ-007 | Deploy entire stack via Docker Compose on-premise with documented air-gap guide. | docker compose up completes without external network calls; guide validated on isolated network.

## Risks & Concrete Mitigations
| ID | Risk | Concrete Mitigation |
|----|------|---------------------|
| RISK-001 | Data breach via compromised keys or network traffic. | Use AES-256 field-level encryption; enforce TLS 1.3; rotate keys every 90 days using HashiCorp Vault; log all key-access events; quarterly penetration testing.
| RISK-002 | Encryption key management failure. | Store keys in HashiCorp Vault with MFA; automate rotation scripts; audit log of all key-management operations per HIPAA §164.312(a)(2)(iv).
| RISK-003 | Audit log tampering. | Write logs to append-only PostgreSQL tables via pg_audit; digitally sign each entry with RSA-2048; retain logs for 7 years; daily integrity verification using SHA-256 hash chain.
| RISK-004 | Deployment air-gap failure. | Deploy on isolated VLAN; disable outbound internet on container networks; host-based firewall rules; detailed air-gap setup guide with network diagram and hardening checklist.
| RISK-005 | Insider threat / RBAC misconfiguration. | Strict RBAC policies; row-level security policies per role; quarterly access reviews; log all RBAC changes.

## PDF Generation
WeasyPrint adds a semi‑transparent overlay and sets the CreationDate metadata field; verification script checks presence of both.

## Monitoring and Alerting
Deploy Prometheus (v2.45) and Grafana (v10) containers. Service‑level objectives: 99.9 % uptime for the web front‑end; 95 % of API requests complete within 200 ms (p95); audit‑log write latency ≤50 ms for 99 % of writes. Alerts trigger Slack webhook and on‑call pager. Monitoring data retained for at least 90 days to satisfy HIPAA retention requirements for security‑related logs.

## Backup and Recovery
PostgreSQL data backed up nightly using pg_dumpall into an encrypted archive (AES‑256) stored on a separate offline storage device; retention 30 days; quarterly restore test documented in BackupTestReport.pdf.

## Operational Governance
RACI matrix maintained in ops/RACI.xlsx assigning Responsible – System Administrator, Accountable – Compliance Officer, Consulted – Clinician Lead, Informed – Executive Sponsor. Change management requires signed change request for any modification to the compose file, image versions, or firewall rules. All procedures reviewed annually and signed off by the Compliance Officer to ensure alignment with HIPAA §164.308(a)(1)(ii).

All references to HIPAA sections such as §164.312(a)(2)(iv), §164.312(e)(1), §164.312(b), and §164.308(a)(1)(ii) are included to ensure regulatory compliance.
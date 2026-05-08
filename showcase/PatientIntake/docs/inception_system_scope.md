# system_scope_definition (Overview)

## Stakeholder Analysis (Overview)

| Stakeholder   | Primary Need| Pain Point| RBAC Tier  | Strategic Objective  |
|---------------|---------------------|------------------------|------------------|----------|
| Patient (ST-001)      | Secure, private submission of PHI and receipt of a verifiable intake summary   | Paper‑based intake is error‑prone, insecure, and creates duplicate data entry | End‑User (no write access) | OBJ‑001: Achieve 100% HIPAA‑compliant electronic intake capture |
| Front‑Desk Staff (ST-002) | Fast data entry with validation and immediate confirmation that the record is stored securely | Manual transcription from paper forms leads to delays and potential data loss | Operator (create/read/write patient records, cannot modify RBAC policies) | OBJ‑002: Reduce average intake processing time to <2 minutes per patient |
| Clinician (ST-003) | Immediate access to complete, accurate patient history for care decisions | Fragmented records across legacy systems cause missing information at point‑of‑care | Clinician (read‑only access to patient records, limited edit of clinical notes) | OBJ‑003: Ensure 95% of clinicians can retrieve full intake within 3 seconds |
| Administrator (ST-004) | Centralized management of user accounts, audit logs, and system configuration without exposing PHI | Lack of unified audit trail makes compliance reporting labor‑intensive | Admin (full read/write access to configuration and audit logs) | OBJ‑004: Provide immutable audit logs retained 7 years for SOC 2/HIPAA reporting |
| Compliance Officer (ST-005) | Assurance that encryption, access controls, and audit mechanisms meet HIPAA and SOC 2 standards | Current processes rely on ad‑hoc spreadsheets and manual checks, increasing audit risk | Auditor (read‑only access to audit logs and encryption key usage reports) | OBJ‑005: Achieve zero compliance findings in external HIPAA audit |

### Alignment with Project Objectives

Each stakeholder need directly maps to one of the five strategic objectives defined for PatientIntake. The mapping ensures that functional requirements and controls are traceable to both stakeholder expectations and measurable objectives.

## Functional Requirements

| ID      | Description| Acceptance Criteria  |
|---------|-------------|--------------------------|
| FR-001 Secure Data Capture: The web‑based intake form must collect patient demographics, insurance information, and medical history. |
 All fields validated against JSON Schema; submission rejected if required field missing; successful submissions recorded within 2 seconds of user click. |
|
| FR-002 Field‑Level Encryption at Rest: Sensitive PHI fields (e.g., SSN, medical history) are encrypted using AES‑256 before storage. |
 Encryption keys stored in HashiCorp Vault; penetration test confirms raw PHI cannot be retrieved without vault token; decryption with incorrect key must fail. |
|
| FR-003 Transport Encryption: All client‑to‑server communication uses TLS 1.3 with forward secrecy. |
 SSL Labs scan achieves “A” rating; downgrade attempts rejected; logs show 100 % of requests use TLS 1.3+. |
|
| FR-004 Role‑Based Access Control (RBAC): System enforces distinct permissions for admin, clinician, and front‑desk roles. |
 Unit tests verify front‑desk cannot read PHI beyond tier; clinician can read but not modify audit logs; unauthorized attempts return HTTP 403 and are logged. |
|
| FR-005 Immutable Audit Logging: Every read and write operation on patient records is recorded in an append‑only log. |
 Logs contain timestamp, user ID, operation type, record identifier; retention policy enforces 7 years immutable storage; any alteration attempt triggers alert and is rejected. |
|

## Security Controls Summary

| Control ID   |	Control Type          |	Requirement Detail |	Quantified Threshold|
|--------------|	----------------------|	--------------|	--------------|
| SEC-001      |	Field-Level Encryption|	AES‑256-GCM encryption on all PHI fields at rest|	256-bit key rotation every 90 days; automated cryptographic test suite|
| SEC-002      |	Transport Encryption   |	TLS 1.3 with ECDHE cipher suites for all HTTP traffic|	TLS 1.3 minimum; no fallback to ≤TLS 1.2; penetration test & TLS scan|
| SEC-003      | RBAC Enforcement         | Role-based permissions mapped to ST–001…ST–005 roles  | No user can exceed least privilege needed; access control audit  |
| SEC-004      | Audit Logging           | Immutable append-only log of every DB operation| Retain 7 years; tamper-evident checksum per log file; log integrity verification script    |
| SEC-005      | Air-Gap Deployment      | System must operate without external internet connectivity after provisioning                | All external calls disabled; only internal network allowed; deployment checklist & network scan   |

## Air-Gap Deployment Constraints

* Docker Compose stack must be installable from an offline media package.
* All required open-source dependencies are bundled in a version-controlled artifact repository.
* No runtime calls to external package registries; container images are pre-loaded.
* Configuration files contain no hard-coded URLs; DNS resolution limited to internal network.
* A documented Air-Gap Setup Guide must be produced (see FR-006).

## Risk Assessment Table

| ID          |	Description |	Likelihood |	Impact |	Mitigation Actions |
|-------------|	--------------																											|	-----------|	-------|	------------|
| RISK-001    |	PHI data breach during transmission over the network  |	Medium     |	High   |	Enforce TLS 1.3 with forward secrecy; field-level AES 256 encryption before transport; quarterly penetration testing using OpenSSL hardened cipher suites.	|
| RISK-002    | Unauthorized read/write access to PHI due to misconfigured RBAC roles| Medium     | High   | Implement RBAC aligned to stakeholder matrix; monthly role-audit scripts; principle of least privilege; log all privileged actions to immutable audit store retained 7 years.	|
| RISK-003    | Failure to deploy in air-gapped environment leading to operational downtime or security gaps    | Low        | Medium | Create Docker Compose bundle that runs entirely offline; provide hardened air-gap installation guide with checksum verification; validate deployment via automated smoke tests before go-live.	|
| RISK-004    | Inadequate key management causing key compromise or loss of decryption capability            | Low        | High   | Adopt envelope encryption using HashiCorp Vault for DEK protection;	rotate master keys quarterly;	store vault unseal keys in separate HSMs on-premises.	|
| RISK-005    | Insufficient audit log integrity compromising forensic investigations| Low        | Medium | Use append-only write-once storage for audit logs;	enable PostgreSQL pg_audit extension;	replicate logs to immutable object storage with WORM policy.	|

## Success Criteria / KPI Alignment

| KPI ID   |	Metric Name|	Target Value |	Measurement Method|	Linked Objective |
|-----------|---------------|-----------|---------------------|-------------------|
| KPI-001   | Form transmission encryption compliance     |-100 % of all form submissions encrypted with TLS 1.3 + AES 256 field encryption               | Automated network capture analysis + backend validation logs                         | OBJ-001          |
| KPI-002   | Audit log completeness                       |-99.9 % of all read/write events captured within 5 seconds of occurrence                     | Log aggregation monitoring tools| OBJ-004          |
| KPI-003   | Role-based access enforcement accuracy     | Zero unauthorized access incidents in 90‐day monitoring period                           | Security incident tracking system| OBJ-003          |
| KPI-004   | Air-gap deployment success rate           |-100 % of installations pass pre-deployment validation checklist without external network calls | Automated deployment validation scripts  | OBJ-005          |

## Narrative Summary

The PatientIntake SaaS solution satisfies stringent HIPAA requirements while operating as a multi‐tenant service. Mapping each stakeholder’s primary need to a concrete RBAC tier guarantees that only the minimum necessary privileges are granted, directly supporting OBJ‐001 through OBJ‐005. Identified risks focus on data confidentiality, access control integrity, and the unique challenge of an air‐gap deployment model. Mitigation strategies leverage proven open‐source security patterns—TLS 1.3, AES 256 envelope encryption, HashiCorp Vault, immutable audit logging—ensuring each risk is addressed with measurable controls.

## Measurable Success Criteria (KPIs)

| KPI ID       |	Metric Name|	Target Value |
|-------------|---------------|----------------|
| KPI-001     | System Availability (Uptime)               |-≥ 99.9 % monthly uptime                    |
| KPI-002     | Data Encryption Verification               |-100 % of PHI fields encrypted at rest with AES 256 and in transit with TLS 1.3 |
| KPI-003     | Audit Log Completeness                     |-≥ 99.95 % of read/write events recorded immutably for 7 years |

## Acceptance Conditions

1. **System Availability** – No more than 43 minutes of unplanned downtime per month, verified by monthly uptime reports.
2. **Encryption Verification** – All encryption keys rotated quarterly; compliance reports show zero plaintext PHI in storage snapshots.
3. **Audit Log Completeness** – Log retention policy enforced by immutable storage (WORM) and validated by monthly reconciliation scripts detecting any missing entries beyond the 0.05 % tolerance.

## Monitoring & Reporting Cadence

* Weekly health dashboards for uptime and error rates.
* Quarterly cryptographic compliance reviews.
* Monthly audit log integrity checks with signed hash chains.

> For full details on stakeholder matrix cross-references, see sibling artifact `Stakeholder_Matrix_Artifact`.
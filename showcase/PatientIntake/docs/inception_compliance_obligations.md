# HIPAA Compliance & Data Governance Framework

## 1. HIPAA Privacy & Security Rule Mapping

This section maps the PatientIntake system's functional requirements to specific HIPAA Security Rule (45 CFR Part 164, Subpart C) controls. The mapping ensures that every technical control implemented in the Design and Development phases has a direct regulatory obligation.

| HIPAA Control ID | Control Description | System Component | Implementation Constraint |
|---|---|---|---|
| 164.312(a)(1) | Access Control | Web Form, PostgreSQL | Unique user identification for Admin, Clinician, and Front Desk roles. |
| 164.312(a)(2)(i) | Unique User Identification | RBAC Matrix | System must enforce distinct login credentials for every user. |
| 164.312(b) | Audit Controls | PostgreSQL Audit Log | Immutable logging of all access, creation, modification, and deletion of PHI. |
| 164.312(c)(1) | Integrity | Web Form, PostgreSQL | Mechanisms to authenticate and verify that PHI has not been altered or destroyed inappropriately. |
| 164.312(c)(2)(i) | Person or Entity Authentication | Web Form | Verification that the person or entity seeking access is the one claimed. |
| 164.312(e)(1) | Transmission Security | Web Form, Docker Compose | Encryption of PHI in transit (TLS 1.2+) for all data entering or leaving the on-premises network. |
| 164.312(e)(2)(ii) | Encryption | PostgreSQL, PDF Generator | Implementation of technology and policy to encrypt PHI at rest. |

### 2.1 Data Classification Matrix

| Data Category | Examples | Classification | Handling Requirement |
|---|---|---|---|
| Protected Health Information (PHI) | Demographics, Insurance Info, Medical History | High Sensitivity | Field-level encryption at rest; strict RBAC; full audit logging. |
| Non-PII Operational Data | Appointment IDs, System Logs | Low Sensitivity | Standard database storage; limited access to Admin role. |
| Audit Trail Data | Access Logs, Export Timestamps | High Sensitivity | Immutable storage; write-only access for system; read access for Admin/Compliance. |

### 2.2 Field-Level Encryption Strategy

All PHI fields are subject to field-level encryption. This ensures that even if the underlying PostgreSQL storage is compromised, the data remains unreadable without the appropriate decryption keys.

- **Encryption Scope:** Demographics, Insurance Information, Medical History.
- **Key Management:** Decryption keys are restricted to the `Clinician` and `Admin` roles. The `Front Desk` role interacts only with encrypted tokens for non-PII fields.
- **Transit Security:** All data transmitted between the web form and the PostgreSQL database is encrypted using TLS 1.2 or higher.

## 3. Role-Based Access Control (RBAC) Policy

The PatientIntake system enforces a strict RBAC model based on the principle of least privilege. The following matrix defines the authorized actions for each role. This matrix supersedes any previous draft matrices to resolve inconsistencies.

| Role | Data Entry | Read Access | Edit Access | Export Access | Audit Access |
|---|---|---|---|---|---|
| Admin | System Config | All Records | System Config | All Records | Full Audit |
| Clinician | Clinical Notes | Assigned/Reviewed | Own Actions |  |  |
| Front Desk | New Submissions | Pending/Own | Demographics Only | No | No |
| Patient | Own Data | No | No | No | No |

### 3.2 Audit Log Requirements

- **Scope:** Every read, write, update, and delete operation on PHI is logged.
- **Content:** Each log entry must include the User ID, Timestamp, Action Type, Record ID, and IP Address.
- **Storage:** Audit logs are stored in a dedicated, immutable PostgreSQL table. Access to this table is restricted to the `Admin` role.
- **Retention:** Audit logs must be retained for a period of [TBD] years, in accordance with HIPAA record retention requirements. *Note: Specific retention period to be defined by Compliance Officer.*

### 3.3 PDF Export Governance

PDF exports of patient intake summaries are a high-risk activity and are subject to strict controls.

- **Authorization:** Only `Admin` and `Clinician` roles are authorized to generate PDF exports.
- **Watermarking:** Every exported PDF must include a dynamic watermark containing the user ID, timestamp, and record ID.
- **Logging:** Every export event is logged in the audit trail with the specific record ID and the user who initiated the export.

## 4. On-Premises Data Residency Enforcement

Given the on-premises deployment model, strict data residency controls are enforced to ensure that PHI never leaves the authorized local environment.

### 4.1 Deployment Constraints

- **No External Cloud Dependencies:** The system must operate entirely within the on-premises network. No data is transmitted to external cloud services.
- **Docker Compose Isolation:** The system is deployed using Docker Compose, ensuring that all services (PostgreSQL, Web Form, PDF Generator) are isolated within the local container network.
- **Air-Gap Capability:** The system must be deployable in an air-gapped environment, with no external network connectivity required for operation.

## 5. Knowledge Gaps & Unresolved Decisions

The following items require resolution by the designated owners before the Design phase can proceed.

| Gap ID | Description | Impact | Owner | Resolution Required |
|---|---|---|---|---|
| KG-01 | Data Retention Period | Compliance Risk | Compliance Officer | Define specific retention period (e.g., 6 years, 7 years) based on state/federal regulations. |
| KG-02 | Encryption Algorithm Specification | Security Risk | Security Architect | Specify the exact encryption algorithm (e.g., AES-256-GCM) and key management strategy. |
| KG-03 | Incident Response Plan | Operational Risk | Compliance Officer | Define the specific steps for breach notification and containment within the on-premises environment. |

## 6. Decision Rationale

The decision to use on-premises deployment with Docker Compose is driven by the requirement for strict data residency and the absence of external cloud dependencies. This decision constrains the Design phase to focus on local infrastructure management and air-gap setup. The RBAC model is designed to minimize the attack surface by restricting access to PHI only to roles that require it for clinical or administrative purposes.
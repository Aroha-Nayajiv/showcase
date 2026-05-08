# Inception Business Requirements (Overview)

### 1. Business Vision & Scope
The PatientIntake SaaS solution enables healthcare providers to capture complete patient intake information in a secure, HIPAA‑compliant web application that supports multi‑tenant isolation, high availability, and seamless scalability for on‑premise deployments. By automating demographic, insurance, and medical history collection, the system reduces manual entry errors, accelerates patient onboarding, and ensures that all protected health information (PHI) is encrypted at rest and in transit, meeting stringent regulatory requirements while delivering a cost‑effective SaaS experience for clinics of any size.

### 2. Stakeholder Analysis Overview
| Stakeholder ID | Role               | Core Need  | Pain Point  | RBAC Tier| Linked Objective |
|---------------|--------------------|---------------|------------------|
| ST-001        | Patient            | Secure, private submission of PHI via web form      | Fear of data exposure | End‑User (read‑only) | OBJ-001 |
| ST-002 | Front‑Desk Staff | Efficient capture and routing of intake data | Time‑consuming paper forms | Operator (create/read) | OBJ-002 |
| ST-003 | Clinician | Immediate access to complete patient histories | Incomplete records or delayed access | Clinician (read/write limited) | OBJ-003 |
| ST-004 | System Administrator | Configure roles, manage keys, audit health | Complex key‑management and audit visibility | Admin (full control) | OBJ-004 |
| ST-005 | Compliance Officer | Assurance of HIPAA, SOC 2 compliance | Proving compliance across containers | Compliance Viewer (read‑only) | OBJ-005 |

### 3. Alignment with SaaS Business Goals
The solution is designed for horizontal scalability through containerized micro‑services and Docker Compose orchestration, enabling rapid tenant onboarding without cross‑tenant data leakage. Multi‑tenant isolation is enforced at the application layer and reinforced by PostgreSQL row‑level security. High availability is achieved via redundant service instances and health‑check monitoring, targeting 99.9 % uptime. All security controls are built to satisfy HIPAA and SOC 2 audit requirements, supporting the SaaS business model of subscription‑based revenue and continuous compliance assurance.

### 4. Functional Requirements (FR)
**FR‑001 – Secure Data Capture**
The web‑based intake form must collect patient demographics, insurance information, and medical history. All PHI fields are encrypted on the client side using AES‑256‑GCM before transmission.
*Acceptance Criteria*: Automated test verifies encrypted payload storage and confirms no plaintext appears in network logs.

**FR‑002 – Transport Encryption**
All communication between browser and backend must use TLS 1.2 or higher with forward secrecy.
*Acceptance Criteria*: Security scan rejects any TLS 1.0/1.1 connections and validates cipher suites against NIST SP 800‑52 recommendations.

**FR‑003 – Role‑Based Access Control (RBAC)**
PostgreSQL must enforce three roles: Administrator (full CRUD), Clinician (read PHI, write notes), Front‑Desk Staff (create submissions only).
*Acceptance Criteria*: Access matrix test demonstrates each role can perform only permitted actions; unauthorized attempts return HTTP 403.

**FR‑004 – Immutable Audit Logging**
Every read, write, update, or delete operation on PHI must generate an immutable log entry containing user ID, timestamp, operation type, and record ID. Logs are stored in a tamper‑evident append‑only table retained for seven years.
*Acceptance Criteria*: Log integrity test triggers an alert on any hash mismatch.

**FR‑005 – Exportable Encrypted PDF Summary**
Authorized staff may generate a PDF summary of a patient’s intake data. The PDF is watermarked with the staff member’s name and export timestamp, encrypted at rest using AES‑256, and accessible only through authenticated download.
*Acceptance Criteria*: PDF export test confirms watermark presence, correct timestamp format, and decryption failure for unauthorized users.

### 5. Success Metrics (KPIs)
| KPI ID   | Metric Name                         | Target Value  | Measurement Method| Linked Objective |
|----------|--------------|--------------------|
| KPI-001  | Form Encryption Compliance Rate      | 100 % of PHI fields encrypted at rest & in transit | Automated security test suite | OBJ-001 |
| KPI-002  | Audit Log Completeness | 99.9 % of all data accesses logged | Log audit script scanning 30‑day window | OBJ-004 |
| KPI-003  | PDF Export Access Control Accuracy | Zero unauthorized PDF downloads detected | Penetration testing over 7 days | OBJ-005 |

### 6. Risk Assessment
| Risk ID   | Description  | Likelihood   | Impact   | Mitigation Strategy|
|----------|--------------------|--------------|----------|--------------------|
| RISK-001 | PHI data breach during transmission over the network | Medium | High | Enforce TLS 1.2+ with forward secrecy; use AES‑256‑GCM client encryption; rotate keys quarterly via open-source KMS; implement continuous network monitoring                     |
| RISK-002 | Unauthorized access to stored PHI due to mis‑configured RBAC or credential compromise | Medium | High | Apply least‑privilege role hierarchy; enforce MFA for privileged accounts; conduct quarterly RBAC review; store credentials in vault  |
| RISK-003 | Deployment failures in air‑gapped environment leading to downtime or incomplete configuration | Low | Medium | Sign Docker images with GPG; maintain offline CI pipeline; run pre‑deployment validation scripts on replica air‑gap environment; document rollback procedure on write‑once media |
| RISK-004 | Audit log tampering or loss affecting compliance evidence | Low | High | Store logs on append‑only WORM storage for ≥7 years; enable cryptographic hash chaining per entry; schedule daily integrity verification jobs                         |

### 7. Objective Definitions
| Objective ID   | Description|
|----------------|-----------|
| OBJ-001        | Achieve 100 % PHI encryption at rest and in transit across all tenants                    |
| OBJ-002        | Reduce average intake processing time to <2 minutes per patient through automated capture    |
| OBJ-003        | Ensure 99.9 % availability of patient records during clinic hours                           | | OBJ-004        | Maintain immutable audit logs for 7 years meeting HIPAA retention requirements               | | OBJ-005        | Pass external HIPAA/SOC 2 audit with zero critical findings                           | |

*Note: Objective identifiers have been added to the project asset registry.*
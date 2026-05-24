# Stakeholder & Governance Map

## 1. Executive Summary
This artifact defines the authoritative stakeholder map, actor roles, and governance structure for the PatientIntake system. It establishes the decision rights, accountability chains, and compliance ownership required to operate a HIPAA-compliant, on-premises web application. This map serves as the single source of truth for who interacts with the system, what permissions they hold, and who is accountable for security and regulatory adherence.

## 2. Actor & Stakeholder Mapping

### 2.1 Primary Actors (Internal)
These roles interact with the system daily to perform core business functions.

| Role ID | Role Name | Description | Key Responsibilities | HIPAA Minimum Necessary Scope |
| :--- | :--- | :--- | :--- | :--- |
| ACT-001 | Admin | IT and System Administrators responsible for system configuration, user management, and infrastructure maintenance. | User provisioning, RBAC configuration, system monitoring, backup management. | Access to system logs and configuration only. No access to patient PHI for clinical purposes. |
| ACT-002 | Clinician | Medical professionals (Doctors, Nurses) who review patient intake data and update medical history. | Reviewing intake submissions, updating medical history, approving patient records. | Full read/write access to medical history and demographics. |
| ACT-003 | Front Desk | Administrative staff responsible for initial patient data entry and verification. | Collecting patient demographics, insurance info, and consent forms via the web form. | Read/Write access to demographics and insurance fields only. No access to medical history. |

### 2.3 External Entities
These are external parties that interact with the system or are affected by its operations.

| Entity ID | Entity Name | Interaction Type | Data Exchange | Governance Constraint |
| :--- | :--- | :--- | :--- | :--- |
| EXT-001 | Patient | Data Subject | Submits intake data via web form; requests access to their own records. | HIPAA Privacy Rule: Right to Access, Right to Amend. |
| EXT-002 | Insurance Payer | External System | Receives encoded insurance data for billing (if integrated). | Business Associate Agreement (BAA) required if PHI is shared. |
| EXT-003 | HIPAA Regulators | External Auditor | Receives audit logs and compliance evidence upon request. | Full audit trail integrity; 6-year retention of compliance records. |

### 2.4 Data Governance Roles
This section defines the ownership and custodianship of data assets within the PatientIntake system.

| Governance Role | Assigned Entity | Responsibilities | Decision Rights |
| :--- | :--- | :--- | :--- |
| Data Owner | Chief Medical Officer (CMO) | Defines business requirements for data accuracy, completeness, and clinical utility. | Approves changes to data schema and field definitions. |
| Data Custodian | IT Operations Manager | Implements technical controls for data storage, encryption, and backup. | Manages infrastructure, encryption keys, and access control lists (ACLs). |
| Privacy Officer | Compliance Officer | Ensures data handling practices comply with HIPAA Privacy Rule and organizational policy. | Approves data sharing agreements and patient data subject requests. |
| Security Officer | IT Security Lead | Ensures data handling practices comply with HIPAA Security Rule and technical security standards. | Approves security configurations, encryption algorithms, and access policies. |

### 2.5 Decision Rights Matrix (RACI)
This matrix defines who is Responsible, Accountable, Consulted, and Informed for key governance decisions.

| Decision Area | Admin | Clinician | Front Desk | IT Security | Compliance Officer | Legal |
| --- | --- | --- | --- | --- | --- | --- |
| User Access Provisioning | R | I | I | C | A | I |
| Data Retention Policy | I | I | I | C | A | C |
| Encryption Key Rotation | R | I | I | A | C | I |
| Patient Data Subject Request | I | I | I | C | A | C |
| System Deployment (Air-Gap) | R | I | I | C | A | I |
| Audit Log Review | C | I | I | R | A | I |

### 2.6 HIPAA Security Rule Control Mapping
This section maps specific HIPAA Security Rule requirements to the responsible roles and system controls.

| Control ID | Control Description | Responsible Role | System Control Implementation | Evidence Source |
| :--- | :--- | :--- | :--- | :--- |
| SEC-001 | Access Control (164.312(a)(1)) | IT Security | RBAC enforced via PostgreSQL roles and application middleware. | RBAC Matrix Validation |
| SEC-002 | Audit Controls (164.312(b)) | IT Security | Immutable audit log of all read/write operations in PostgreSQL. | Audit Log Integrity Checks |
| SEC-003 | Integrity (164.312(c)(1)) | IT Security | Field-level encryption and checksums for data integrity. | Penetration Testing Results |
| SEC-004 | Transmission Security (164.312(e)(1)) | IT Security | TLS 1.3 for all data in transit; field-level encryption for data at rest. | Network Isolation Verification |

### 3.1 Data Retention Policy
| Data Category | Retention Period | Disposal Method | Responsible Role |
| :--- | :--- | :--- | :--- |
| Patient Intake Records | 7 Years (per HIPAA) | Secure Deletion (Cryptographic Erase) | IT Security |
| Audit Logs | 6 Years (per HIPAA) | Secure Archival (WORM Storage) | IT Security |
| System Configuration | 3 Years | Secure Deletion | IT Security |

## 4. Communication & Escalation Channels

| Incident Type | Primary Contact | Escalation Path | Response Time SLA |
| :--- | :--- | :--- | :--- |
| Security Breach | IT Security Lead | CISO -> Legal -> Compliance Officer | Immediate (1 hour) |
| Compliance Violation | Compliance Officer | Legal -> CMO | 24 hours |
| System Outage | IT Operations Manager | CTO -> IT Security | 4 hours |
| Patient Data Request | Compliance Officer | Legal -> IT Security | 30 days (per HIPAA) |

### 4.1 Assumptions
- ASSUMPTION: The organization has a designated Compliance Officer and IT Security Lead who are available for governance decisions.
- ASSUMPTION: The organization has a Hardware Security Module (HSM) or equivalent secure key storage solution available for key management.
- ASSUMPTION: The organization's legal team is familiar with HIPAA requirements and can provide timely guidance on patient data subject requests.

## 5. Knowledge Gaps

| Gap ID | Description | Impact | Resolution Path |
| :--- | :--- | :--- | :--- |
| GAP-001 | Specific data retention period for insurance billing records is not defined by HIPAA but may be required by state law or payer contracts. | Potential non-compliance with state-specific regulations. | Legal team to review state laws and payer contracts. |
| GAP-002 | Exact technical implementation of "Cryptographic Erase" for PostgreSQL is not specified. | Potential failure to meet secure disposal requirements. | IT Security to define technical procedure and test in staging. |
| GAP-003 | Specific SLA for patient data subject requests is not defined by HIPAA (only 30 days max). | Potential operational inefficiency if not defined internally. | Compliance Officer to define internal SLA (e.g., 10 business days). |
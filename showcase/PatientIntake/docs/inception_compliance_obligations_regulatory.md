# HIPAA Regulatory Mapping

## 1. Executive Summary
This artifact maps the PatientIntake system's technical and operational controls to specific HIPAA Security and Privacy Rule provisions. It establishes the compliance baseline for the on-premises, Docker Compose-deployed web application. The mapping explicitly links field-level encryption, immutable audit logging, and role-based access control (RBAC) to regulatory mandates, ensuring that the system design satisfies both the Security Rule (45 CFR Part 164 Subpart C) and the Privacy Rule (45 CFR Part 164 Subpart E).

### 1.1 Access Control (164.312(a))
The system enforces strict access controls to ensure that only authorized individuals have access to Protected Health Information (PHI). This is achieved through a three-tier Role-Based Access Control (RBAC) model.

| HIPAA Provision | System Control | Implementation Detail | Verification Method |
| :--- | :--- | :--- | :--- |
| **164.312(a)(1) Unique User Identification** | User Authentication | Every user (Admin, Clinician, Front Desk) is assigned a unique login credential. No shared accounts are permitted. | Login logs verify unique session initiation per user ID. |
| **164.312(a)(2)(i) Emergency Access Procedure** | Admin Override | System Administrators possess a privileged 'Break-Glass' capability to access any record in case of emergency, logged with high-priority alerting. | Audit log entry tagged `EMERGENCY_ACCESS` with mandatory post-event review. |
| **164.312(a)(2)(ii) Automatic Logoff** | Session Management | Web sessions automatically terminate after 15 minutes of inactivity. | Backend middleware enforces session timeout; frontend redirects to login. |
| **164.312(d) Encryption and Decryption** | Field-Level Encryption | All PHI fields (Demographics, Insurance, Medical History) are encrypted at the application layer before persistence in PostgreSQL. | Database dump verification shows ciphertext for all PHI columns. |

### 1.3 Integrity (164.312(c))
The system ensures that electronic PHI is not improperly altered or destroyed.

| HIPAA Provision | System Control | Implementation Detail | Verification Method |
| :--- | :--- | :--- | :--- |
| **164.312(c)(1) Mechanism to Authenticate PHI** | Data Validation | Structured web forms enforce strict data types and formats (e.g., SSN format, Date of Birth ranges) before submission. | Unit tests cover validation edge cases; invalid data is rejected at the API layer. |
| **164.312(c)(2) Error Correction** | Form Validation Feedback | Users receive immediate, specific error messages for invalid entries, allowing correction before submission. | UI/UX testing confirms clear error messaging for all validation rules. |

### 1.4 Transmission Security (164.312(e))
The system protects electronic PHI while in transit over an electronic network.

| HIPAA Provision | System Control | Implementation Detail | Verification Method |
| :--- | :--- | :--- | :--- |
| **164.312(e)(1) Integrity** | TLS 1.3 Enforcement | All data transmissions between the patient's browser and the on-premises server use TLS 1.3. No plaintext HTTP is permitted. | Network traffic analysis confirms TLS 1.3 handshake; HTTP 301 redirects to HTTPS. |
| **164.312(e)(2)(ii) Encryption** | In-Transit Encryption | Certificate management is handled internally. No reliance on external Certificate Authorities to maintain air-gap integrity. | Internal PKI validation; certificate expiration monitoring. |

### 1.5 Minimum Necessary Standard (164.502(b))
The system limits access to PHI to the minimum necessary to accomplish the intended purpose of the request or action.

| HIPAA Provision | System Control | Implementation Detail | Verification Method |
| --- | --- | --- | --- |
| **164.502(b) Minimum Necessary** | Role-Based Data Isolation | **ROLE-001 (Admin):** Full access to all data and system settings.<br>**ROLE-002 (Clinician):** Access to clinical data and PDF export; restricted from system configuration.<br>**ROLE-003 (Front Desk):** Can submit forms but cannot view historical patient records or export PDFs. Field-level isolation prevents viewing sensitive fields (e.g., SSN) post-submission unless explicitly authorized. | RBAC unit tests verify that ROLE-003 cannot query historical records or export PDFs. |

### 1.6 Patient Rights (164.524, 164.526)
The system must support patient rights to access and amend their PHI.

| HIPAA Provision | System Control | Implementation Detail | Verification Method |
| :--- | :--- | :--- | :--- |
| **164.524 Right to Access** | Data Export Capability | Authorized staff (ROLE-001, ROLE-002) can generate PDF intake summaries for patients. These exports are watermarked with access timestamps to prevent unauthorized redistribution. | PDF generation module includes dynamic watermarking; access logs track export events. |
| **164.526 Right to Amend** | Data Correction Workflow | Clinicians (ROLE-002) can add clinical notes or correct existing data fields. All amendments are logged in the audit trail with a reference to the original entry. | Audit log verification shows `UPDATE` actions with `PREVIOUS_VALUE` and `NEW_VALUE` fields. |

### 1.7 Data Classification and Handling
All data collected via the structured web form—including demographics, insurance information, and medical history—is classified as PHI. The following handling rules apply:

*   **In Transit:** All data transmissions must use TLS 1.3 or higher. No plaintext HTTP is permitted.
*   **At Rest:** Field-level encryption is mandatory for all PHI fields stored in the local PostgreSQL database. Encryption keys must be managed separately from the data.
*   **Auditability:** Every read and write operation must be logged in an immutable audit log. These logs are subject to the same retention and access controls as the PHI itself.

### 1.8 On-Premises Deployment Constraints
The system is deployed on-premises using Docker Compose with no external cloud dependencies. This air-gapped architecture reduces the attack surface but imposes strict governance on:

*   **Network Isolation:** The Docker network must be isolated from external networks. Access is restricted to authorized internal staff only.
*   **Physical Security:** Physical access to the servers hosting the Docker containers is restricted to authorized IT personnel. Access logs must be maintained.
*   **Backup and Recovery:** Regular backups of the PostgreSQL database and audit logs must be performed. Backup media must be encrypted and stored securely.

### 2.1 Field-Level Encryption Mandate
All Protected Health Information (PHI) collected via the structured web form must undergo field-level encryption. This policy applies to the following data categories:
*   Patient Demographics (Name, DOB, SSN)
*   Insurance Information (Policy Number, Group ID)
*   Medical History (Diagnoses, Medications, Allergies)

Encryption must be applied at the application layer before data is persisted to the local PostgreSQL database. This ensures that even in the event of a database compromise, the data remains unreadable without the corresponding encryption keys.

### 2.3 Key Management and Rotation
Encryption keys must be stored separately from the encrypted data, ideally in a dedicated, access-controlled key management service or hardware security module (HSM) within the on-premises environment. Key rotation must occur at least annually, or immediately upon any suspected compromise. The system must support seamless key rotation without downtime or data loss.

## 3. Audit Logging for Data Access
Every read and write operation involving PHI must be logged in a full audit log. This includes:
*   Form submissions (write)
*   PDF exports (read)
*   Database queries by authorized staff (read)

Audit logs must include the user ID, timestamp, action performed, and the specific data fields accessed. These logs must be immutable and stored in a separate, secure location to prevent tampering.

## 4. Data Retention and Disposal
Data retention periods must comply with HIPAA regulations and organizational policy. Once the retention period expires, data must be securely disposed of using methods that ensure it cannot be recovered. This includes secure deletion of database records and destruction of any physical media if applicable.

## 5. Stakeholder Responsibilities

| Role | Responsibilities |
| :--- | :--- |
| **Compliance Officer** | Responsible for overseeing the implementation of these policies and conducting regular audits. |
| **System Administrator** | Responsible for managing encryption keys and ensuring the security of the on-premises infrastructure. |
| **Development Team** | Responsible for implementing field-level encryption and audit logging in the application code. |
| **Clinical Staff** | Responsible for accessing patient data only for legitimate medical purposes and reporting any suspected security incidents. |

## 6. Future Considerations
As technology and regulatory requirements evolve, these policies must be reviewed and updated accordingly. The Compliance Officer is responsible for monitoring changes in HIPAA regulations and recommending updates to these policies as needed.

## 7. Role Definitions and Permissions

The system shall enforce three distinct RBAC tiers. Access is granted based on job function, not individual identity. Each role's permissions are explicitly defined below to prevent privilege creep.

*   **ROLE-001 | Admin:** System maintenance, user management, audit review. Full System Access. Manage user accounts (create, deactivate), view full audit logs, configure system settings, export all patient data.
*   **ROLE-002 | Clinician:** Clinical review, data verification, PDF export. Clinical Data Access. View patient demographics, insurance, and medical history; generate and export PDF intake summaries; add clinical notes (if applicable in future).
*   **ROLE-003 | Front Desk:** Patient intake, form submission. Intake Data Access. Submit new patient forms; view status of submitted forms; view own submission history. Cannot view historical patient records or export PDFs.

### 7.1 Least-Privilege Enforcement
*   **Default Deny:** All users are denied access to all resources by default. Access is granted only via explicit role assignment.
*   **Field-Level Isolation:** Even within permitted data sets, access to sensitive fields (e.g., Social Security Number, specific medical history details) is restricted to ROLE-001 (Admin) and ROLE-002 (Clinician) only. ROLE-003 (Front Desk) can only submit these fields but cannot view them post-submission unless explicitly authorized for a specific intake session.

## 8. Knowledge Gaps and Assumptions

*   **ASSUMPTION:** Key rotation frequency is set to annually. This is a standard industry practice but should be validated against specific organizational policy.
*   **KNOWLEDGE_GAP:** Specific retention period for PHI (e.g., 6 years, 7 years) is not defined in the project DNA. Decision owner: Compliance Officer. Evidence needed: State-specific HIPAA extensions or organizational policy.
*   **KNOWLEDGE_GAP:** Exact method for 'Break-Glass' emergency access (e.g., physical token, second-factor authentication) is not defined. Decision owner: System Administrator. Evidence needed: IT security policy for emergency access.

## 9. Risk Assessment: Audit Log Tampering

| Risk ID | Risk Description | Regulatory Citation | Mitigation Control | Residual Risk |
| :--- | :--- | :--- | :--- | :--- |
| **RISK-001** | Unauthorized modification or deletion of audit logs to conceal unauthorized access to PHI. | **164.312(b) Audit Controls**<br>**164.316(b) Administrative Safeguards** | Immutable audit log storage; cryptographic hashing of log entries; restricted write permissions; regular integrity checks. | Low |

## 10. Conclusion
This HIPAA Regulatory Mapping artifact provides a comprehensive framework for ensuring the PatientIntake system complies with HIPAA Security and Privacy Rules. By explicitly linking technical controls to regulatory requirements, this document serves as the authoritative guide for design, development, and testing phases. Continuous monitoring and regular audits are essential to maintain compliance.
# HIPAA & Privacy Compliance Framework

## 1. PHI Definition and Data Classification

This section defines the scope of Protected Health Information (PHI) within the PatientIntake system, mapping specific data fields to HIPAA Privacy Rule requirements. This classification drives the encryption and access control policies defined in subsequent sections.

### 1.1 PHI Data Elements
The following fields collected via the structured web form are classified as PHI and require strict handling per HIPAA Security Rule §164.312(a)(2)(iv):

| Data Category | Field Name | PHI Classification | Handling Requirement |
| :--- | :--- | :--- | :--- |
| Demographics | Full Name | Yes | Field-level encryption at rest and in transit |
| Demographics | Date of Birth | Yes | Field-level encryption at rest and in transit |
| Demographics | SSN | Yes | Field-level encryption at rest and in transit |
| Demographics | Address | No | Standard validation only |
| Demographics | Phone Number | No | Standard validation only |
| Demographics | Email Address | No | Standard validation only |
| Insurance | Policy Holder Name | Yes | Field-level encryption at rest and in transit |
| Insurance | Policy Number | Yes | Field-level encryption at rest and in transit |
| Insurance | Group Number | Yes | Field-level encryption at rest and in transit |
| Insurance | Relationship to Patient | No | Standard validation only |
| Medical History | Allergies | Yes | Field-level encryption at rest and in transit |
| Medical History | Current Medications | Yes | Field-level encryption at rest and in transit |
| Medical History | Primary Reason for Visit | Yes | Field-level encryption at rest and in transit |

### 2.1 Data Minimization Policy
The PatientIntake system adheres to the HIPAA minimum necessary standard. The system must only collect data fields explicitly listed in Section 1.1. No additional or optional fields may be added without a formal change management process and a privacy impact assessment. This ensures that the attack surface for PHI exposure is minimized.

### 2.2 Patient Consent Mechanism
The web form must include a mandatory checkbox for patients to acknowledge and consent to the collection and processing of their PHI. This consent record must be stored in the audit log with a timestamp and the patient's IP address. The consent record serves as the legal basis for processing PHI under HIPAA.

### 3.1 RBAC Matrix
The system implements Role-Based Access Control (RBAC) for the following roles: Admin, Clinician, and Front Desk. The matrix below defines permissions for data entry, viewing, and PDF export.

| Role | Data Entry (Form Submission) | View PHI (Read) | Export PDF Intake Summary | Audit Log Access |
| :--- | :--- | :--- | :--- | :--- |
| Admin | Yes | Yes | Yes | Yes |
| Clinician | Yes | Yes | Yes | No |
| Front Desk | Yes | Yes | No | No |

### 3.2 Access Control Enforcement
Access to PHI must be enforced at the application level and the database level. The PostgreSQL database must utilize row-level security or application-level filtering to ensure that users can only access records relevant to their role and assigned patients. Failed authentication attempts must be logged and monitored.

### 4.1 Audit Log Requirements
Every read and write operation performed on the PostgreSQL database must be logged in a tamper-evident audit log. This includes:

*   **Write Operations:** Creation, modification, and deletion of patient records.
*   **Read Operations:** Any query accessing patient PHI, including PDF generation triggers.
*   **Access Control Events:** Successful and failed authentication attempts, and role permission changes.

The audit log must capture the user ID, timestamp, operation type, affected record ID, and the IP address of the request. The raw PHI must not be stored in the audit log; instead, a hash of the submitted data must be stored to ensure integrity.

### 4.2 Audit Log Retention
Audit logs must be retained in accordance with HIPAA retention policies. The specific retention period is not yet defined in the project DNA and requires resolution by the Compliance Officer.

### 5.3 Patient Portal Scope
The implementation of a patient portal for direct access and amendment is out of scope for the initial release. The system must support the *process* for patient rights, but the *interface* for patients to exercise these rights is not required in this phase.

### 6.1 Air-Gap Constraints
The system is deployed via Docker Compose for on-premises environments with no external cloud dependencies. This air-gap constraint impacts key management and update processes. Encryption keys must be stored separately from the database, ideally in a dedicated secrets manager or environment variables within the Docker Compose environment.

### 6.2 Key Management
Encryption keys must be rotated periodically. The specific rotation frequency is not yet defined in the project DNA and requires resolution by the Security Architect.

## 7. Knowledge Gaps and Unresolved Decisions

The following items require resolution by the designated decision owners before the Design phase can proceed:

| Knowledge Gap | Decision Owner | Evidence Needed |
| :--- | :--- | :--- |
| Data Retention Period | Compliance Officer | Jurisdiction-specific HIPAA guidelines |
| Key Rotation Frequency | Security Architect | Internal security policy or industry best practices |
| Audit Log Retention | Compliance Officer | HIPAA Security Rule requirements |

## 8. Conclusion

This HIPAA & Privacy Compliance Framework establishes the binding constraints for the PatientIntake system. It defines the scope of PHI, the access control model, the audit logging requirements, and the patient rights processes. All subsequent design and development activities must adhere to these constraints.
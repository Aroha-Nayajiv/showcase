# Inception Governance Framework

## 1. Governance Structure and Decision Rights

This framework establishes the decision-making authority, escalation paths, and compliance oversight mechanisms for the PatientIntake system. It defines the boundaries of authority for the Admin, Clinician, and Front Desk roles, ensuring that all data access and system modifications adhere to HIPAA regulations and organizational policies.

### 1.1 Decision-Making Authority Matrix

The following matrix defines who has the authority to make decisions (Approver), who must be consulted (Consulted), and who must be informed (Informed) for key governance areas. This structure ensures clear accountability and prevents unauthorized changes to patient data or system configurations.

| Governance Area | Approver | Consulted | Informed | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| User Access Provisioning | Admin | Clinician (for role-specific needs) | Front Desk | Ensures least-privilege access is granted by authorized personnel. |
| Data Retention Policy | Admin | Compliance Officer | All Roles | Aligns data lifecycle with HIPAA retention requirements. |
| System Configuration Changes | Admin | IT Security | Clinician, Front Desk | Prevents unauthorized changes that could compromise data integrity. |
| Audit Log Review | Admin | Compliance Officer | - | Ensures ongoing compliance and detection of unauthorized access. |
| Incident Response Escalation | Admin | IT Security | Compliance Officer | Ensures rapid response to potential HIPAA breaches. |

### 1.2 Escalation Paths

In the event of a governance violation, security incident, or compliance breach, the following escalation path must be followed:

1. **Front Desk/Clinician**: Immediately report the incident to the Admin.
2. **Admin**: Assess the incident, contain the issue, and notify the Compliance Officer within 24 hours.
3. **Compliance Officer**: Evaluate the breach against HIPAA requirements, determine if external reporting is necessary, and coordinate with IT Security for remediation.
4. **IT Security**: Implement technical fixes, review audit logs, and ensure system integrity is restored.

## 2. Role-Based Access Control (RBAC) Policies

Access to the PatientIntake system is strictly governed by Role-Based Access Control (RBAC). The following roles are defined, with specific permissions and responsibilities, aligning with the project's operational needs and HIPAA minimum necessary standards.

### 2.1 Role Definitions and Permissions

| Role | Description | Permissions | Data Access Scope | Governance Responsibility |
| :--- | :--- | :--- | :--- | :--- |
| Admin | System administrators responsible for user management, system configuration, and audit log review. | User management, system configuration, audit log export, full system access. | All data, including audit logs. | Ensure system integrity and compliance. |
| Clinician | Medical professionals who view and update patient medical history and insurance information. | View and update patient medical records, generate PDF intake summaries. | Patient medical history and insurance data. | Improve patient care and data accuracy. |
| Front Desk | Administrative staff who collect patient demographics and insurance information via the web form. | Create new patient records, update demographic and insurance data, view basic patient info. | Patient demographics and insurance data only. | Streamline patient registration. |

### 2.2 Principle of Least Privilege

Each role is granted only the minimum permissions necessary to perform their job functions. For example, Front Desk staff cannot access medical history or audit logs. This principle is enforced at the application layer and reinforced at the database layer using PostgreSQL.

## 3. Approval Workflows for Data Access

Sensitive data access, particularly the export of PDF intake summaries, requires explicit approval to ensure compliance with HIPAA privacy rules.

### 3.1 PDF Intake Summary Export

1. **Request**: A Clinician or Admin requests the export of a patient's PDF intake summary.
2. **Approval**: The request is automatically logged in the audit trail. For non-routine exports, a secondary approval from a Compliance Officer may be required (policy to be defined in HIPAA Compliance Framework).
3. **Execution**: Upon approval, the system generates the PDF with watermarking and access timestamps.
4. **Audit**: The export event, including user ID, timestamp, and patient ID, is logged immutably.

## 4. HIPAA Compliance Oversight

The PatientIntake system must adhere to HIPAA regulations, with specific oversight mechanisms to ensure ongoing compliance.

### 4.1 Audit Logging Requirements

Every read and write operation on patient data must be logged with:
- Timestamp
- User ID
- Action Type (e.g., SELECT, INSERT, UPDATE, DELETE, EXPORT)
- Record Affected

These logs are critical for HIPAA compliance and must be immutable. The Admin is responsible for regular review of these logs.

### 4.2 Data Sovereignty and Encryption

- **Data Sovereignty**: All data must be stored on-premises using PostgreSQL, with no external cloud dependencies.
- **Encryption**: Field-level encryption is required for all PHI fields at rest and in transit. The application layer must handle encryption, ensuring that even if the database files are compromised, the data remains unreadable without the application-level keys.

## 5. Knowledge Gaps and Unresolved Decisions

The following areas require further definition or decision by the project stakeholders:

- **Data Retention Period**: The exact duration for retaining patient records is not defined. Decision owner: Compliance Officer. Evidence needed: HIPAA retention guidelines and organizational policy.
- **Key Management Strategy**: The method for managing encryption keys (e.g., HSM, KMS) is not defined. Decision owner: IT Security. Evidence needed: Security best practices for on-premises key management.
- **Secondary Approval Threshold**: The criteria for requiring secondary approval for PDF exports are not defined. Decision owner: Compliance Officer. Evidence needed: Risk assessment of data export scenarios.
# Stakeholder Map and Governance Framework

## 1. Executive Summary
This artifact defines the authoritative stakeholder map, role definitions, and governance framework for the PatientIntake system. It establishes the "who" and "why" of the system's operational model, ensuring alignment with HIPAA Security Rule requirements for access control, auditability, and data integrity. This document serves as the binding reference for the Design phase to implement Role-Based Access Control (RBAC) and for the Compliance Officer to validate governance adherence.

## 2. Stakeholder Identification and Classification
The following stakeholders are identified based on their interaction with the PatientIntake system and their responsibility for compliance outcomes. Stakeholders are classified by their primary relationship to the system (Internal/External) and their compliance obligation level.

| Stakeholder | Classification | Primary Responsibility | HIPAA Relevance |
| :--- | :--- | :--- | :--- |
| Patient | External | Initiates intake; provides demographic, insurance, and medical history data. | Covered Entity (Data Subject) - Rights to access and amendment. |
| Front Desk Staff | Internal | Verifies patient identity; enters/validates intake data; manages scheduling. | Workforce Member - Minimum Necessary access to demographics/insurance. |
| Clinician | Internal | Reviews medical history; updates clinical notes; approves intake completion. | Workforce Member - Access to PHI for treatment purposes. |
| System Administrator | Internal | Manages user accounts, roles, and system configuration; oversees Docker Compose infrastructure. | Workforce Member - Administrative access; responsible for system security. |
| Compliance Officer | Internal | Monitors audit logs; conducts risk assessments; ensures HIPAA compliance; manages incident response. | Covered Entity Representative - Oversight of Security Rule implementation. |

## 3. Role Definitions and Access Governance
The PatientIntake system implements Role-Based Access Control (RBAC) to enforce the principle of least privilege. Access is granted based on the user's role, not their identity. The following roles are defined with specific permissions and data visibility constraints.

### 3.1 Patient (Self-Service Role)
*   **Access Level:** Read-Only (Own Data)
*   **Permissions:**
    *   Access structured web form for intake submission.
    *   View status of own intake submission.
    *   Request export of own intake summary (PDF).
*   **Data Visibility:** Only own demographic, insurance, and medical history records.
*   **Governance Constraint:** No access to other patients' data. No ability to modify submitted records (requires Front Desk/Clinician intervention).

### 3.2 Front Desk Staff (Data Entry Role)
*   **Access Level:** Read-Write (Demographics/Insurance)
*   **Permissions:**
    *   Create and update patient demographic and insurance information.
    *   Verify patient identity during intake.
    *   View list of pending intakes.
    *   Generate PDF intake summaries for authorized staff.
*   **Data Visibility:** All patient demographics and insurance data. Limited access to medical history (read-only for verification purposes).
*   **Governance Constraint:** Cannot access clinical notes or medical history beyond what is necessary for insurance verification. All actions are logged in the audit trail.

### 3.3 Clinician (Clinical Review Role)
*   **Access Level:** Read-Write (Medical History)
*   **Permissions:**
    *   Review and update medical history and clinical notes.
    *   Approve or reject intake submissions.
    *   View full patient record (demographics, insurance, medical history).
    *   Export patient records for treatment purposes.
*   **Data Visibility:** Full access to all patient data associated with their assigned patients.
*   **Governance Constraint:** Access to medical history is restricted to patients under their care. All exports are watermarked with user identity and timestamp.

### 3.4 System Administrator (Operational Role)
*   **Access Level:** Administrative (System Configuration)
*   **Permissions:**
    *   Manage user accounts and role assignments.
    *   Configure system settings (encryption keys, audit log retention).
    *   Monitor system health and Docker Compose container status.
    *   Access audit logs for security investigation.
*   **Data Visibility:** No access to patient PHI (demographics, insurance, medical history) for operational purposes. Access to audit logs only.
*   **Governance Constraint:** Strict separation of duties. Administrators cannot view or modify patient data. All administrative actions are logged.

### 3.5 Compliance Officer (Oversight Role)
*   **Access Level:** Read-Only (Audit Logs/Reports)
*   **Permissions:**
    *   View and export audit logs.
    *   Generate compliance reports.
    *   Review access control policies.
    *   Initiate incident response procedures.
*   **Data Visibility:** Access to audit logs and compliance reports. No direct access to patient PHI unless required for incident investigation (with elevated logging).
*   **Governance Constraint:** Independent oversight role. Cannot modify user roles or system configuration.

### 3.6 Data Handling and Encryption Policy
*   **Encryption at Rest:** All PHI fields (demographics, insurance, medical history) must be encrypted at rest using field-level encryption. Keys are managed by the System Administrator but are not accessible to application users.
*   **Encryption in Transit:** All data in transit must be encrypted using TLS 1.2 or higher. No external cloud dependencies; all traffic remains within the on-premises Docker Compose environment.
*   **Data Minimization:** Only data necessary for the specific role's function is accessible. Front Desk staff do not have access to clinical notes; Clinicians do not have access to insurance billing details beyond what is necessary for treatment.

### 3.7 Audit Logging Policy
*   **Comprehensive Logging:** Every read and write operation on patient data must be logged. Logs must capture user identity, timestamp, action performed, and data accessed.
*   **Immutability:** Audit logs must be stored in an immutable format to prevent tampering. Logs are retained for a minimum of 6 years as per HIPAA requirements.
*   **Review Frequency:** Audit logs must be reviewed monthly by the Compliance Officer. Automated alerts must be configured for suspicious access patterns.

### 3.8 Access Control Policy
*   **Role Assignment:** User roles are assigned by the System Administrator based on job function. Role changes require approval from the Compliance Officer.
*   **Access Reviews:** Access rights must be reviewed quarterly by the Compliance Officer to ensure they align with current job responsibilities.
*   **Session Management:** Sessions must timeout after 15 minutes of inactivity. Multi-factor authentication (MFA) is required for all administrative and clinical roles.

## 4. Success Criteria and Evidence
The following success criteria define the measurable outcomes for the PatientIntake system's governance and compliance framework. These criteria will be used to validate the system's readiness for deployment.

| Criterion | Measurement | Target | Evidence Source | Owner |
| :--- | :--- | :--- | :--- | :--- |
| HIPAA Compliance | Successful completion of HIPAA security risk assessment. | 100% of identified risks mitigated. | Risk Assessment Report | Compliance Officer |
| Data Encryption | Verification of field-level encryption at rest and in transit. | 100% of PHI fields encrypted. | Encryption Audit Report | Admin |
| Audit Log Integrity | Review of audit logs for completeness and immutability. | 100% of read/write operations logged. | Audit Log Review Report | Admin |
| Access Control | Verification of RBAC implementation and user access reviews. | Zero unauthorized access incidents. | Access Control Audit Report | Admin |

## 5. Knowledge Gaps
The following knowledge gaps have been identified and require resolution in subsequent phases. These gaps represent areas where specific details are needed to finalize the governance framework.

| Gap ID | Description | Impact | Resolution Path | Owner |
| :--- | :--- | :--- | :--- | :--- |
| KG-01 | Specific Risk Assessment Methodology | Inability to quantify compliance risk accurately. | Define methodology in inception_compliance_obligations. | Compliance Officer |
| KG-02 | Key Management Process Details | Potential vulnerability in encryption key lifecycle. | Define process in inception_technology_strategy. | System Administrator |
| KG-03 | Incident Response Plan | Lack of preparedness for security incidents. | Define plan in inception_compliance_obligations. | Compliance Officer |
| KG-04 | Data Retention Period Specifics | Uncertainty in legal compliance for data disposal. | Define retention period in inception_compliance_obligations. | Compliance Officer |

## 6. Cross-Artifact References
*   **inception_scope_definition:** Defines the boundaries of the PatientIntake system, including in-scope and out-of-scope features.
*   **inception_compliance_obligations:** Details the specific HIPAA Security Rule requirements and how they map to system controls.
*   **inception_risk_register:** Lists identified risks, their likelihood, impact, and mitigation strategies.
*   **inception_technology_strategy:** Outlines the open-source technology stack and deployment model (Docker Compose).
*   **inception_project_charter:** Provides the high-level project vision, goals, and stakeholder alignment.
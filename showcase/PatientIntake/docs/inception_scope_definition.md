# HIPAA Patient Intake System Scope & Governance

## 1. Business Vision and Strategic Alignment

The PatientIntake system is a HIPAA-compliant web application designed to digitize and secure the patient intake process within an on-premises healthcare environment. The primary business objective is to eliminate paper-based intake inefficiencies while ensuring strict adherence to the HIPAA Privacy and Security Rules. The system must operate entirely within the organization's physical boundaries, utilizing open-source technologies and Docker Compose for deployment, ensuring no external cloud dependencies compromise data sovereignty.

### 1.1 Strategic Goals
- **Regulatory Compliance:** Achieve and maintain full alignment with HIPAA Security Rule technical safeguards, specifically focusing on access control, integrity, and audit controls.
- **Data Sovereignty:** Guarantee that all electronic Protected Health Information (ePHI) remains within the organization's on-premises infrastructure, supporting air-gapped deployment scenarios.
- **Operational Efficiency:** Streamline the intake workflow for Front Desk staff, reduce data entry errors through structured validation, and provide Clinicians with immediate, accurate patient history.

## 2. Business Requirements and Data Elements

This section defines the specific data elements to be collected, their sensitivity levels, and the business rules governing their handling. These requirements are binding for the Design and Development phases.

### 2.1 Data Collection Scope
The system must collect the following data elements via a structured web form. Each element is classified by sensitivity to determine encryption and access control requirements.

| Data Element Category | Specific Fields | Sensitivity Level | Business Justification |
| :--- | :--- | :--- | :--- |
| Patient Demographics | Full Name, Date of Birth, Address, Phone Number, Email | High (PHI) | Required for patient identification and communication. |
| Insurance Information | Provider Name, Policy Number, Group Number, Subscriber ID | High (PHI) | Required for billing verification and eligibility checks. |
| Medical History | Current Medications, Allergies, Past Surgeries, Chief Complaint | High (PHI) | Critical for clinical decision-making and patient safety. |
| Consent Forms | Signature Data, Date of Consent, Type of Consent | High (PHI) | Legal requirement for treatment and data processing. |

### 2.2 Data Integrity and Validation
- **Requirement:** All form submissions must undergo real-time validation to ensure data completeness and format correctness before storage.
- **Constraint:** Invalid submissions must be rejected with clear, actionable error messages to the user, without storing partial or corrupted ePHI.
- **Encryption:** Field-level encryption must be applied to all ePHI fields at rest in the PostgreSQL database. Data in transit must be encrypted using TLS 1.2 or higher.

## 3. Role-Based Access Governance (RBAC)

Access to the system is governed by the principle of "Minimum Necessary," ensuring that users can only access the data required to perform their specific job functions. The following roles are established based on the project globals.

### 3.1 Role Definitions and Access Boundaries

| Role | Access Scope | Data Visibility | Operational Constraints |
| :--- | :--- | :--- | :--- |
| **Admin** | System Configuration, User Management, Audit Log Review | Full access to all data, including audit logs and system settings. | Responsible for user provisioning and role assignment. Cannot modify clinical data directly. |
| **Clinician** | Patient Record Review, Clinical Notes, Intake Data | Full access to patient demographics, insurance, and medical history. | Can view and update clinical notes. Cannot modify system configuration or user roles. |
| **Front Desk** | Intake Form Entry, Patient Check-in | Access to demographics and insurance fields only. **Cannot view clinical notes or medical history.** | Responsible for initial data entry. Can correct demographic errors but cannot alter medical history. |
| **Patient** | Self-Service Portal (Future Phase) | Access to own demographic and insurance data. | Read-only access to own records. No access to clinical notes or other patients' data. |

### 3.2 Access Control Enforcement
- **Authentication:** All users must authenticate via a secure, on-premises identity provider. Multi-factor authentication (MFA) is recommended for Admin and Clinician roles.
- **Authorization:** Access to specific data fields and actions must be enforced at the application and database levels. The "Front Desk" role must be explicitly restricted from accessing medical history fields.
- **Session Management:** Sessions must timeout after a period of inactivity (e.g., 15 minutes) to prevent unauthorized access on shared workstations.

## 4. HIPAA Security Rule Mapping

The following table maps specific HIPAA Security Rule requirements to the PatientIntake system's data flows and technical controls. These mappings are binding constraints for the subsequent Design and Development phases.

| HIPAA Control ID | Control Description | PatientIntake Data Flow | Technical Implementation Requirement |
| :--- | :--- | :--- | :--- |
| 164.312(a)(1) | Access Control | Patient Intake Form Submission | Unique User Identification: Every read/write operation must be tied to a unique user identity (Admin, Clinician, Front Desk). |
| 164.312(a)(2)(ii) | Emergency Access | System Recovery / Data Restoration | Documented, tested emergency access procedure for data restoration in the on-premises environment. |
| 164.312(c)(1) | Integrity | Form Data Storage (PostgreSQL) | Mechanism to Authenticate ePHI: Field-level encryption must be applied to all ePHI fields (demographics, insurance, medical history) at rest. |
| 164.312(e)(1) | Transmission Security | Web Form to Backend Transmission | Implement Technical Security: All data in transit must be encrypted using TLS 1.2 or higher. No plaintext ePHI transmission is permitted. |
| 164.312(b) | Audit Controls | All Database Operations | Record and Examine Activity: A full audit log of every read and write operation must be generated and stored immutably. |
| 164.312(d) | Person or Entity Authentication | PDF Export Request | Verify User Identity: PDF exports are restricted to authorized staff only. Access must be verified via RBAC before generating the export. |

### 4.1 Data Residency and Sovereignty
- **Obligation:** All ePHI must remain within the organization's physical and logical boundaries.
- **Constraint:** The system must deploy via Docker Compose for on-prem environments. No external cloud services (e.g., cloud-based KMS, cloud-based logging) are permitted.
- **Air-Gap Requirement:** The system must be deployable in an air-gapped environment. All dependencies (including open-source libraries) must be bundled within the Docker images.

### 4.2 Technology Stack Constraints
- **Database:** PostgreSQL must be used for all data storage, ensuring ACID compliance and robust transactional integrity.
- **Deployment:** Docker Compose is the mandated orchestration tool for local and on-premises deployment, ensuring consistency across development and production environments.
- **Open Source:** All software components must be open-source, with no commercial licenses required for core functionality.

### 4.3 Critical Risks

1. **Non-Compliance with HIPAA Regulations**
   - **Risk:** Failure to implement required HIPAA Security Rule controls, leading to regulatory penalties and loss of trust.
   - **Trigger Condition:** Audit reveals missing or inadequate controls (e.g., missing audit logs, unencrypted data).
   - **Mitigation:** Regular compliance audits, automated security testing, and staff training.
   - **Owner:** Compliance Officer.
   - **Early Warning Signal:** Failed internal compliance checks or security scan results.

2. **Data Breach via Unauthorized Access**
   - **Risk:** Unauthorized access to ePHI due to weak access controls or insider threats.
   - **Trigger Condition:** Successful network intrusion or unauthorized data export.
   - **Mitigation:** Strict RBAC, field-level encryption, and air-gap deployment. Regular penetration testing.
   - **Owner:** IT Security Manager.
   - **Early Warning Signal:** Unusual network activity, failed login attempts, or anomalous data access patterns.

3. **System Unavailability Impacting Patient Care**
   - **Risk:** System downtime affecting the ability to capture patient intake data, leading to operational disruption.
   - **Trigger Condition:** Hardware failure, software bug, or database corruption.
   - **Mitigation:** High-availability architecture (where feasible within on-prem constraints), regular backups, and documented disaster recovery procedures.
   - **Owner:** IT Operations Manager.
   - **Early Warning Signal:** Increased error rates, slow response times, or database connection failures.

## 5. Sibling Artifact References

This artifact focuses on business scope, governance, and regulatory boundaries. For detailed technical implementation, stakeholder analysis, and risk management, refer to the following sibling artifacts:

- **Stakeholder Map and Governance Framework (`inception_stakeholder_map`):** Contains the full stakeholder analysis, governance structure, and communication plan.
- **HIPAA Compliance & Data Governance Framework (`inception_compliance_obligations`):** Provides detailed compliance obligations, control mappings, and evidence requirements.
- **Inception Risk Register & Governance Framework (`inception_risk_register`):** Contains the comprehensive risk register with detailed mitigation strategies and ownership.
- **Inception Technology Strategy (`inception_technology_strategy`):** Details the technology stack selection rationale, architecture decisions, and deployment strategy.
- **HIPAA Patient Intake System Project Charter (`inception_project_charter`):** Defines the project vision, objectives, scope, and high-level milestones.

## 6. Knowledge Gaps and Unresolved Decisions

The following items require resolution by the Product Owner or Compliance Officer before the Design phase can proceed:

- **SLA Targets:** Specific Service Level Agreement (SLA) targets for system availability and response times are not defined. Decision owner: Product Owner. Evidence needed: Service-tier commitments from client or industry benchmarks.
- **Data Retention Policy:** The specific duration for retaining patient intake records and audit logs is not defined. Decision owner: Compliance Officer. Evidence needed: Legal and regulatory requirements for data retention in the specific jurisdiction.
- **Backup Frequency:** The frequency and retention period for database backups are not defined. Decision owner: IT Operations Manager. Evidence needed: Business continuity requirements and recovery time objectives (RTO).

## 7. Decision Rationale

## 8. Asset Registry Updates

No new asset IDs are established in this artifact. All references to roles, data elements, and controls use existing project globals or established sibling artifact IDs.

## 9. Change Impact Analysis

- **Impact on Design Phase:** The RBAC boundaries defined in Section 3.1 will directly influence the API endpoint design and database schema permissions. The "Front Desk" role's restriction on clinical notes must be enforced at the API level.
- **Impact on Development Phase:** The encryption requirements in Section 2.2 and the audit logging requirements in Section 4 will dictate the implementation of data models and middleware components.
- **Impact on Testing Phase:** The acceptance criteria in Section 2 and the HIPAA mapping in Section 4 will form the basis for integration and security testing scenarios.
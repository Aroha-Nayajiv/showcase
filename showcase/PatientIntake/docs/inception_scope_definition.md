# HIPAA Patient Intake System - Business Scope & Requirements

## 1. Business Vision and Strategic Problem Statement

### 1.1 Core Business Problem
The organization currently lacks a secure, sovereign method for collecting and managing patient intake data. Reliance on fragmented, non-compliant, or cloud-dependent data collection methods exposes the organization to significant regulatory risk under HIPAA and operational fragility due to external dependencies. The core business problem is the inability to guarantee the confidentiality, integrity, and availability of Protected Health Information (PHI) during the critical intake phase while maintaining strict data sovereignty.

### 1.3 Key Strategic Objectives
1. **Regulatory Compliance:** Achieve and maintain full HIPAA compliance for all patient intake data, including field-level encryption and comprehensive audit trails.
2. **Data Sovereignty:** Ensure all patient data remains within the organization's on-premises infrastructure, eliminating external cloud dependencies and mitigating third-party data exposure risks.
3. **Operational Efficiency:** Streamline the patient intake process through a structured, validated web form, reducing manual errors and administrative burden.
4. **Secure Access:** Provide authorized staff (Admin, Clinician, Front Desk) with secure, role-based access to patient records and the ability to generate watermarked, timestamped PDF summaries.

### 1.4 Success Criteria (High-Level)
- **Compliance:** All patient data is encrypted at rest and in transit, with a full audit log of every read and write operation.
- **Deployment:** The system is successfully deployed via Docker Compose in an on-premises environment with no external cloud dependencies.
- **Security:** Automated tests validate form validation, data encryption, and access control edge cases.
- **Usability:** Authorized staff can generate PDF intake summaries with watermarking and access timestamps.

## 2. Business Requirements

### 2.1 PHI Data Classification & Handling
The system must classify all data collected via the patient intake form as Protected Health Information (PHI) under HIPAA. This includes:
- **Demographics:** Name, date of birth, address, SSN (if collected).
- **Insurance Information:** Policy numbers, group numbers, subscriber details.
- **Medical History:** Current medications, allergies, past diagnoses, family history.

**Constraint:** No PHI may be stored, transmitted, or processed outside the designated on-premises environment. All data must be treated as sensitive by default.

### 2.2 Field-Level Encryption Obligation
To mitigate the risk of data exposure in the event of a database compromise or unauthorized access, the system must implement field-level encryption for all PHI fields.

- **At Rest:** Every PHI field in the PostgreSQL database must be encrypted individually. This ensures that even if the database files are exfiltrated, the data remains unreadable without the specific encryption keys.
- **In Transit:** All data transmission between the web form client and the server, and between internal services, must use TLS 1.2 or higher. Field-level encryption provides an additional layer of defense-in-depth.

**Decision:** Field-level encryption is mandatory for all PHI fields. This decision is driven by the high sensitivity of the data and the requirement for a secure, on-premises deployment where physical security controls may vary.

**Downstream Constraint:** The Design phase MUST specify the encryption algorithms and key management strategy. The Development phase MUST implement encryption/decryption logic at the application layer before data is written to or read from the database.

### 2.3 Role-Based Access Control (RBAC)
Access to PHI must be strictly controlled based on the user's role. The system must enforce the principle of least privilege.

| Role | Access Scope | Constraints |
| :--- | :--- | :--- |
| **Admin** | Full system configuration, user management, audit log review. | No direct access to patient clinical data for operational purposes. |
| **Clinician** | Read and write access to patient medical history and demographics. Access to PDF exports. | Cannot modify system configuration or user roles. |
| **Front Desk** | Read and write access to patient demographics and insurance information. | No access to clinical notes or medical history. |
| **Patient** | Access to their own intake data via a secure portal (if applicable, otherwise limited to submission). | Cannot view other patients' data. |

**Constraint:** Access controls must be enforced at the application level and verified at the database level where possible. Every access attempt must be logged.

### 2.4 Comprehensive Audit Logging
HIPAA requires the tracking of all access to PHI. The system must maintain a full, immutable audit log of every read and write operation.

- **Scope:** Every login, data retrieval, data modification, and PDF export must be logged.
- **Content:** Each log entry must include the user ID, timestamp, action performed, record ID accessed, and IP address.
- **Integrity:** Audit logs must be tamper-evident. Unauthorized modification or deletion of audit logs must be prevented.

**Downstream Constraint:** The Design phase MUST define the audit log schema and storage mechanism. The Development phase MUST implement logging middleware that captures these events for every relevant API call or database operation.

### 2.5 Secure PDF Export
PDF intake summaries are a high-risk output because they contain PHI and are often distributed outside the secure application environment. The system must enforce strict controls on PDF generation and distribution.

- **Authorization:** Only users with the 'Clinician' or 'Admin' role may generate PDF summaries.
- **Watermarking:** Every generated PDF must include a dynamic watermark containing the requesting user's ID and the timestamp of the export.
- **Traceability:** The system must log the generation of every PDF, linking the export event to the specific user and record.

**Downstream Constraint:** The Design phase MUST specify the PDF generation library and watermarking implementation. The Development phase MUST ensure that PDF generation does not bypass audit logging.

### 2.6 On-Premises Deployment & Air-Gap Constraints
The system must be deployable in a fully isolated, on-premises environment with no external cloud dependencies.

- **Containerization:** The system must be packaged using Docker Compose to ensure deterministic deployment and environment consistency.
- **Air-Gap Readiness:** The deployment guide must document all steps required to install and operate the system in an air-gapped network, including local package repositories for any required dependencies.
- **No External Calls:** The application must not make outbound network calls for licensing, telemetry, or updates. All updates must be applied via local image replacement.

**Downstream Constraint:** The Design phase MUST specify the Docker Compose architecture and service dependencies. The Development phase MUST ensure that all dependencies are resolvable from local sources.

### 2.8 HIPAA Security Rule
The system must comply with the HIPAA Security Rule, which establishes national standards to protect individuals' electronic personal health information. Key requirements include:
- **Access Control:** Unique user identification and emergency access procedures.
- **Audit Controls:** Hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use electronic PHI.
- **Integrity:** Policies and procedures to ensure that electronic PHI is not improperly altered or destroyed.
- **Transmission Security:** Technical safeguards to guard against unauthorized access to ePHI that is being transmitted over an electronic network.

### 2.9 Data Retention & Disposal
- **Retention:** PHI must be retained for a period defined by organizational policy and state law (e.g., 7 years). This decision is currently unresolved and requires a formal policy decision.
- **Disposal:** Data disposal must be secure and irreversible, ensuring that PHI cannot be recovered from decommissioned storage media.

**Knowledge Gap:** Exact data retention period is not defined in project DNA. Decision owner: Compliance Officer. Evidence needed: State-specific healthcare record retention laws and organizational policy.

## 3. Risk Register (Inception Level)

| Risk ID | Risk Description | Impact | Likelihood | Mitigation Strategy | Owner |
| --- | --- | --- | --- | --- | --- |
| R001 | Unauthorized access to PHI due to weak RBAC implementation. | High | Medium | Enforce strict RBAC at application and database levels. Implement comprehensive audit logging. | Security Architect |
| R002 | Data breach via exfiltration of database files. | High | Low | Implement field-level encryption for all PHI fields. Ensure encryption keys are stored separately from data. | Security Architect |
| R003 | Non-compliance with HIPAA due to missing audit logs. | High | Medium | Implement immutable audit logging for all PHI access. Regularly review audit logs for anomalies. | Compliance Officer |
| R004 | Deployment failure in air-gapped environment. | Medium | Medium | Provide detailed air-gap setup guide. Test deployment in isolated environment before production. | DevOps Engineer |
| R005 | Loss of encryption keys leading to data unavailability. | High | Low | Implement secure key management and backup procedures. Ensure key recovery process is documented and tested. | Security Architect |

### 3.1 Technology Selection Criteria
All technologies used in the PatientIntake system must be open-source to align with the organization's commitment to transparency, cost-efficiency, and vendor independence.

- **Licensing:** Technologies must use permissive or copyleft licenses that allow for internal use and modification without significant legal risk.
- **Community Support:** Technologies must have an active community or commercial support option to ensure long-term viability and security updates.
- **Security:** Technologies must have a track record of prompt security patching and vulnerability disclosure.

### 3.2 Assumptions
- **ASSUMPTION:** The organization has existing on-premises infrastructure capable of hosting Docker containers and PostgreSQL databases.
- **ASSUMPTION:** Authorized staff have the necessary training to use the web interface and understand HIPAA compliance requirements.
- **ASSUMPTION:** The organization has a secure key management process in place for handling encryption keys.

## 4. Knowledge Gaps

| Gap ID | Description | Impact | Decision Owner | Evidence Needed |
| :--- | :--- | :--- | :--- | :--- |
| G001 | Exact data retention period for PHI. | High | Compliance Officer | State-specific healthcare record retention laws and organizational policy. |
| G002 | Specific encryption algorithms and key management strategy. | High | Security Architect | Industry best practices for field-level encryption in healthcare. |
| G003 | Web framework and PDF generation library selection. | Medium | Lead Developer | Evaluation of open-source options for security, performance, and ease of use. |
| G004 | Specific air-gap network configuration details. | Medium | DevOps Engineer | Network topology and firewall rules for the on-premises environment. |
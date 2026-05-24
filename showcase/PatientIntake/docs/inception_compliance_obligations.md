# HIPAA Compliance & Regulatory Constraints

### 1.2 Business Objectives
1. **Regulatory Compliance & Risk Mitigation**: Achieve and maintain full HIPAA Privacy and Security Rule compliance by enforcing field-level encryption for all PHI (demographics, insurance, medical history) at rest and in transit. This eliminates the risk of data breaches and associated regulatory fines.
2. **Data Sovereignty & Operational Control**: Deploy exclusively on-premises using open-source technologies and Docker Compose. This ensures no external cloud dependencies, allowing the organization to maintain complete control over its sensitive patient data in an air-gapped environment.
3. **Operational Efficiency & Accountability**: Replace manual or fragmented intake processes with a structured, automated web form. Implement granular Role-Based Access Control (RBAC) for Admin, Clinician, and Front Desk roles, coupled with a comprehensive audit log of every read/write operation to ensure full traceability and accountability.
4. **Secure Data Export**: Enable authorized staff to generate watermarked, timestamped PDF intake summaries, ensuring that sensitive data is only accessible to verified personnel and that all exports are logged for compliance review.

### 1.3 Key Success Criteria
*   **HIPAA Compliance**: 100% of PHI fields are encrypted at rest and in transit.
*   **Air-Gap Deployment**: The system operates successfully in a local, on-premises environment with zero external network dependencies.
*   **Auditability**: Every data access and modification event is logged with user ID, timestamp, and action type.
*   **Access Control**: RBAC strictly enforces least-privilege access for Admin, Clinician, and Front Desk roles.

### 1.4 Business Value
*   **Risk Reduction**: Eliminates regulatory fines and reputational damage from data breaches.
*   **Efficiency**: Reduces administrative burden and errors in patient data collection.
*   **Control**: Ensures complete ownership and control over sensitive patient data.
*   **Trust**: Enhances patient trust through demonstrable commitment to data security and privacy.

## 2. HIPAA Privacy Rule: PHI Usage and Disclosure

The system must enforce strict usage and disclosure limitations for Protected Health Information (PHI) as defined by the HIPAA Privacy Rule. PHI includes demographics, insurance information, and medical history collected via the intake form.

| Data Field Category | PHI Classification | Permitted Internal Use | Disclosure Constraints |
| :--- | :--- | :--- | :--- |
| Demographics | PHI | Internal use only for intake processing | No external disclosure without explicit patient authorization |
| Insurance Information | PHI | Internal use only for billing/verification | No external disclosure without explicit patient authorization |
| Medical History | PHI | Internal use only for clinical review | No external disclosure without explicit patient authorization |

**Binding Constraint**: The system must implement Role-Based Access Control (RBAC) to ensure that PHI is only accessible to users with a legitimate 'need-to-know' for their specific role (Admin, Clinician, Front Desk). Access must be logged for every read and write operation.

### 2.1 Access Control (164.312(a))
*   **Unique User Identification**: Every user accessing the system must have a unique identifier (Admin, Clinician, Front Desk).
*   **Emergency Access Procedure**: A documented procedure must exist for obtaining necessary ePHI during an emergency, subject to post-event audit review.
*   **Automatic Logoff**: The system must automatically logoff users after a period of inactivity to prevent unauthorized access on shared workstations.
*   **Encryption and Decryption**: PHI must be encrypted at rest (PostgreSQL) and in transit (TLS) to prevent unauthorized access if physical or network security is compromised.

### 2.3 Integrity (164.312(c))
*   **Data Integrity**: PHI must be protected against improper alteration or destruction.
*   **Mechanism**: Implement checksums or cryptographic hashes for critical data fields to detect unauthorized changes.
*   **Policy**: Implement strict input validation and sanitization to prevent data corruption or injection attacks.

### 2.4 Transmission Security (164.312(e))
*   **Network Security**: Implement mechanisms to authenticate and encrypt ePHI when it is sent over an electronic network.
*   **Protocol**: Use TLS 1.2 or higher for all data in transit.
*   **Air-Gap Constraint**: In the air-gapped environment, internal service-to-service communication must also be encrypted to prevent lateral movement attacks.

## 3. Operational Constraints

### 3.1 Open Source Only
The system must be built and deployed using only open-source technologies. No commercial SaaS, proprietary libraries, or cloud-based services are permitted. This ensures full control over the codebase and data sovereignty.

### 3.2 Air-Gapped On-Prem
The system must be deployable via Docker Compose in a fully isolated, on-premises environment. No external network connectivity is allowed for data processing or storage. This constraint impacts dependency management, patching, and key rotation strategies.

## 4. Risk Summary

| Risk | Trigger | Impact | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Key Rotation Failure | Encryption key becomes compromised or lost | High (Data inaccessibility) | Implement robust key management and backup procedures | Security Architect |
| Air-Gap Deployment Complexity | Inability to update dependencies or patches without external network access | Medium (Operational inefficiency) | Develop a documented, repeatable air-gap update process | DevOps Engineer |
| RBAC Misconfiguration | Incorrect role assignment or permission inheritance | High (HIPAA violation) | Rigorous testing of access control edge cases and regular audit log reviews | Security Architect |

## 5. Knowledge Gaps

*   **Data Retention Period**: The specific HIPAA-mandated or organizational data retention period for patient intake records is not defined. Decision owner: Compliance Officer. Evidence needed: Organizational policy or legal requirement.
*   **Key Management Strategy**: The specific mechanism for managing encryption keys (e.g., HSM, KMS, local file) is not defined. Decision owner: Security Architect. Evidence needed: Security policy or infrastructure capabilities.
*   **Backup & Recovery RPO/RTO**: The required Recovery Point Objective (RPO) and Recovery Time Objective (RTO) for the on-premises system are not defined. Decision owner: IT Operations. Evidence needed: Business continuity plan.
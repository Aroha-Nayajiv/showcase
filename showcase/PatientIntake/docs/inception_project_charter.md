# HIPAA Patient Intake System Project Charter

## 1. Business Vision and Strategic Problem Statement

### 1.1 The Core Business Problem
The organization currently lacks a secure, sovereign method for collecting and managing patient intake data. Reliance on fragmented, potentially cloud-exposed, or manual processes creates unacceptable regulatory risk under HIPAA and operational friction for clinical staff. The core business problem is the inability to guarantee data sovereignty and strict compliance while maintaining a streamlined patient experience.

### 1.2 Strategic Vision
To deploy a self-contained, HIPAA-compliant PatientIntake system that ensures:
1. **Data Sovereignty**: All patient data (demographics, insurance, medical history) remains strictly within the organization's on-premises infrastructure, eliminating external cloud dependencies.
2. **Regulatory Compliance**: Full adherence to HIPAA Privacy and Security Rules through field-level encryption and comprehensive audit logging.
3. **Operational Efficiency**: A structured, user-friendly web interface for Front Desk staff to capture data accurately, reducing administrative burden and errors.

### 1.4 High-Level Stakeholder Map
The following roles are established based on the project DNA and system blueprint. Detailed governance and interaction matrices are maintained in the `inception_stakeholder_map` artifact.

| Role | Primary Responsibility | Access Scope |
| :--- | :--- | :--- |
| **Patient** | Submits intake data via web form. | Read-only access to own submitted data (if applicable). |
| **Front Desk** | Captures demographics and insurance info. | Create/Update demographic/insurance fields; cannot view clinical notes. |
| **Clinician** | Reviews and updates medical history. | View/Update medical history; cannot modify administrative audit logs. |
| **Admin** | Manages system configuration and compliance. | Manage user roles; view audit logs; cannot edit clinical data. |

### 1.6 Data Handling & Encryption Mandates
To comply with the Security Rule's requirements for protecting ePHI, the system must enforce specific data handling standards.

*   **Field-Level Encryption**: All PHI fields (demographics, insurance information, medical history) must be encrypted at the application level before being persisted to the local PostgreSQL database. This ensures that even in the event of a database compromise, the data remains unreadable without the corresponding decryption keys.
*   **Encryption in Transit**: All data transmissions between the web client and the on-premises server must utilize TLS 1.2 or higher to prevent interception of PHI during the intake process.
*   **Audit Logging**: Every access, creation, modification, and deletion of a patient record must be logged. The audit log must capture the user identity, timestamp, action performed, and the specific record affected. This log is immutable and accessible only to Admins for compliance review.

### 1.7 Operational & Air-Gap Constraints
The system's deployment model imposes additional compliance considerations regarding data sovereignty and physical security.

*   **On-Premises Deployment**: The system must be deployed entirely within the organization's local infrastructure using Docker Compose. No data may be transmitted to external cloud services for processing, storage, or analytics.
*   **Air-Gap Readiness**: The system must be designed and documented to support an air-gapped environment, ensuring that no external network dependencies (e.g., package managers, telemetry services, cloud-based authentication providers) are required for core functionality.
*   **Data Retention**: Data retention and disposal policies must be defined in accordance with state and federal healthcare regulations. Decision Gap: Specific retention period (e.g., 6 years, 10 years) is not yet defined and must be established by the Compliance Officer.

## 2. Success Criteria (Measurable)

The following criteria define project success. Specific thresholds are subject to validation against organizational benchmarks.

| Criterion | Measurement Method | Target | Owner |
| :--- | :--- | :--- | :--- |
| **HIPAA Compliance** | Internal/External Audit | Pass all HIPAA Security Rule controls | Compliance Officer |
| **Air-Gap Deployment** | Operational Verification | Successful deployment in isolated network | Operations Team |
| **Intake Efficiency** | User Survey / Time Study | Reduce intake time by X% vs. legacy method | Product Owner |
| **Data Security** | Incident Tracking | Zero unauthorized data exfiltration incidents | Security Architect |

## 3. Key Risks (Summary)

Detailed risk analysis is maintained in the `inception_risk_register` artifact.

*   **Complexity of Field-Level Encryption**: Requires rigorous implementation to avoid data loss or access issues.
*   **Operational Overhead**: Maintaining on-prem infrastructure requires dedicated resources.
*   **User Adoption**: Staff may resist new workflows if the UI is not intuitive.
*   **Key Management**: Loss of encryption keys could result in permanent data inaccessibility.

## 4. Decision Rationale

This charter establishes the non-negotiable business constraints for the PatientIntake system. The decision to mandate on-premises deployment and open-source technology is driven by the need for absolute data control and cost predictability. The focus on field-level encryption and audit logging is driven by HIPAA compliance requirements. These constraints will guide all subsequent design and development decisions.

## 5. Knowledge Gaps

The following decisions require resolution before the Design phase can proceed. These are not implementation details but strategic decisions that impact architecture and compliance.

| Gap ID | Description | Decision Owner | Impact |
| :--- | :--- | :--- | :--- |
| **KG-001** | Specific Encryption Algorithms and Key Management Strategy | Security Architect | Determines cryptographic libraries and key storage architecture. |
| **KG-002** | Data Retention Period (e.g., 6 years, 10 years) | Compliance Officer | Determines database partitioning strategy and archival processes. |
| **KG-003** | Backup and Recovery Strategy (RPO/RTO) | Operations Team | Determines infrastructure redundancy and backup automation requirements. |

## 6. Approval

This charter is approved by the Project Sponsor and Chief Strategy Officer. It serves as the binding document for the PatientIntake project.

**Project Sponsor**: [Name]
**Chief Strategy Officer**: [Name]
**Date**: [Current Date]

**Compliance Officer**: [Name]
**Security Architect**: [Name]
**Date**: [Current Date]
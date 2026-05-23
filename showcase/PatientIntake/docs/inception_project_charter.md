# HIPAA Patient Intake System Project Charter

## 1. Business Vision and Value Proposition

The PatientIntake project establishes a secure, on-premises, open-source web application to digitize and secure the patient intake process. The core business value proposition is to eliminate the security risks and inefficiencies of paper-based or legacy digital intake methods by providing a HIPAA-compliant, air-gapped capable system. This system ensures 100% audit trail coverage, zero unauthorized access incidents, and successful deployment in isolated environments without external cloud dependencies.

## 2. Core Business Capabilities

The system must deliver three primary business capabilities:

1. **Secure Patient Data Ingestion**: Collect patient demographics, insurance information, and medical history via a structured web form. All data must be encrypted at rest (field-level) and in transit (TLS 1.2+).
2. **Role-Based Access Governance**: Enforce strict access controls for Admin, Clinician, and Front Desk roles. Access to sensitive data and export functions must be governed by RBAC policies.
3. **Compliant PDF Reporting**: Generate PDF intake summaries for authorized staff only. Exports must include watermarking and access timestamps to ensure traceability and prevent unauthorized distribution.

## 3. Stakeholder Needs and Access Requirements

| Role | Primary Need | Data Access Scope | Governance Constraint |
|---|---|---|---|
| Admin | System configuration and user management | Full system access, including audit logs and user roles | Must not access clinical data for operational purposes |
| Clinician | Review and manage patient intake data | Read/Write access to medical history and demographics | Must have full audit trail visibility for their submissions |
| Front Desk | Data entry and initial patient verification | Write access to demographics and insurance; Read access to submission status | Limited to intake form fields; no access to clinical history |
| Patient | Submit intake information | N/A (External User) | Access limited to the intake form; no access to stored data |

## 4. HIPAA Compliance and Data Governance

The system must adhere to the HIPAA Security Rule. The following table maps critical requirements to business constraints:

| HIPAA Control | Data Flow | Business Constraint | Verification Method |
|---|---|---|---|
| 164.312(a)(1) - Access Control | Structured Web Form | Implement RBAC for Admin, Clinician, and Front Desk. Enforce unique user identification. | RBAC matrix validation in Design; Unit tests for access control edge cases. |
| 164.312(a)(2)(iv) - Encryption | Structured Web Form (In Transit) | Enforce TLS 1.2+ for all data in transit between the patient's browser and the web application. | SSL/TLS configuration audit; Automated penetration testing for protocol version. |
| 164.312(a)(2)(iv) - Encryption | Local PostgreSQL Database (At Rest) | Implement field-level encryption for all Protected Health Information (PHI) fields (demographics, insurance, medical history) at rest. | Encryption algorithm validation; Key management policy review. |
| 164.312(b) - Audit Controls | All Data Flows (Read/Write) | Log every read and write operation to the local PostgreSQL audit log. Ensure logs are immutable and tamper-evident. | Audit log schema validation; Integration tests for log completeness. |
| 164.312(c)(1) - Integrity | Structured Web Form (Submission) | Ensure data integrity during submission via field-level validation. Prevent unauthorized alteration of PHI. | Form validation unit tests; Data integrity checks in integration tests. |
| 164.312(c)(2) - Person or Entity Authentication | PDF Export (Authorized Staff) | Require strong authentication for staff accessing the PDF export feature. | Authentication flow testing; Access control edge case tests. |
| 164.312(d)(1) - Transmission Security | PDF Export (Export) | Secure the PDF export process to ensure only authorized staff can download summaries. Apply watermarking and access timestamps. | Export authorization tests; Watermarking and timestamp verification. |

## 5. Business Success Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| HIPAA Audit Trail Coverage | 100% | Automated verification of audit log completeness for all PHI access events. |
| Unauthorized Access Incidents | 0 | Security monitoring and incident reporting. |
| Air-Gap Deployment Success | 100% | Successful deployment and operation in isolated environments without external cloud dependencies. |

## 6. Key Risks and Mitigations

| Risk ID | Risk Description | Impact | Mitigation Strategy | Owner |
|---|---|---|---|---|
| R01 | Supply Chain Vulnerability in Open-Source Dependencies | High | Implement automated, offline-capable dependency scanning (e.g., OWASP Dependency-Check) integrated into the CI/CD pipeline. Maintain a strict Software Bill of Materials (SBOM) for all container images. | DevOps Lead |
| R02 | Loss of Vendor Support for Critical Components | Medium | Establish an internal community of practice to monitor upstream project activity. Define a fallback strategy for critical components (e.g., PostgreSQL, Nginx) including internal patching capabilities or alternative open-source replacements. | CTO |
| R03 | Compliance Validation Burden | High | Document all open-source components and their versions. Ensure that the chosen stack has established HIPAA compliance guidelines or certifications (e.g., PostgreSQL's security features) to streamline the compliance audit process. | Compliance Officer |
| R04 | Single Point of Failure in Local Infrastructure | Medium | Implement local high-availability configurations for PostgreSQL (e.g., streaming replication) within the Docker Compose stack. Define clear RPO (Recovery Point Objective) and RTO (Recovery Time Objective) targets for local recovery. | Infrastructure Manager |

## 7. Knowledge Gaps and Assumptions

- **Knowledge Gap**: Specific key management mechanism for field-level encryption is not defined. Decision owner: Security Architect. Evidence needed: Key management best practices for on-premises HIPAA systems.
- **Assumption**: The on-premises environment provides a secure network perimeter. This assumption is reversible if network security requirements change.
- **Assumption**: MFA is supported by the chosen open-source identity provider. This assumption is reversible if the identity provider does not support MFA.

## 8. Downstream Constraints

- **Design Phase**: MUST implement the RBAC matrix and field-level encryption as defined in this charter. MUST design the audit log schema to support immutable logging.
- **Development Phase**: MUST NOT use any external cloud dependencies. MUST implement all controls as defined in this charter. MUST include automated tests for access control and encryption.
- **Testing Phase**: MUST verify all HIPAA Security Rule controls through unit and integration tests. MUST include penetration testing for network security.

This artifact defers to [inception_stakeholder_map] for detailed stakeholder roles and responsibilities; see that artifact for the full treatment.
This artifact defers to [inception_scope_definition] for detailed scope boundaries; see that artifact for the full treatment.
This artifact defers to [inception_compliance_obligations] for detailed compliance obligations; see that artifact for the full treatment.
This artifact defers to [inception_technology_strategy] for detailed technology strategy; see that artifact for the full treatment.
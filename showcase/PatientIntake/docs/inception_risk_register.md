# Inception Risk Register & Governance Framework

## 1. Executive Summary

This artifact establishes the risk register and governance framework for the PatientIntake system, a HIPAA-compliant web application deployed on-premises via Docker Compose. It addresses the critical intersection of regulatory compliance (HIPAA), data sovereignty (air-gapped local storage), and operational resilience (open-source stack management). The framework defines ownership for risk mitigation, establishes governance controls for Role-Based Access Control (RBAC), and outlines the escalation paths for incident response.

### 1.1 Role-Based Access Control (RBAC) Governance

Access to Protected Health Information (PHI) is strictly governed by the principle of least privilege. The following governance rules apply to the defined user roles:

*   **Admin:**
    *   **Scope:** System configuration, user management, and audit log review.
    *   **Constraint:** Admins may access audit logs and system configuration data but are explicitly denied direct access to clinical content (patient medical history) unless a specific, logged exception is granted for troubleshooting purposes. This prevents privilege abuse and ensures clinical data integrity.
    *   **Governance:** Access to administrative functions requires multi-factor authentication (MFA) and is subject to monthly access reviews.

*   **Clinician:**
    *   **Scope:** Viewing and updating patient medical history, demographics, and insurance information.
    *   **Constraint:** Clinicians can only access records associated with their assigned patients or departments. All access is logged.
    *   **Governance:** Access is granted based on job function and requires annual security training certification.

*   **Front Desk:**
    *   **Scope:** Collecting patient demographics and insurance information via the intake form.
    *   **Constraint:** Front Desk staff have write-only access to the intake form fields. They cannot view historical medical records or export PDF summaries.
    *   **Governance:** Access is limited to the intake workflow and is revoked immediately upon role change.

*   **Patient:**
    *   **Scope:** Viewing their own intake summary and updating personal contact information.
    *   **Constraint:** Patients have read-only access to their own data. They cannot view other patients' information or system configuration.
    *   **Governance:** Authentication is handled via secure login credentials. Session timeouts are enforced to prevent unauthorized access on shared devices.

## 2. Risk Register

The following risks have been identified and assessed based on their likelihood and impact on the PatientIntake system. Each risk includes a mitigation strategy and an assigned owner.

| Risk ID | Risk Description | Likelihood | Impact | Mitigation Strategy | Owner |
| --- | --- | --- | --- | --- | --- |
| R01 | HIPAA Audit Trail Tampering | Low | Critical | Implement immutable audit logs stored in a separate, read-only volume. Use cryptographic hashing to verify log integrity. | Security Architect |
| R02 | PHI Encryption Failure | Low | Critical | Enforce field-level encryption for all PHI fields at rest and in transit. Conduct regular penetration testing to validate encryption implementation. | Security Architect |
| R03 | Data Sovereignty Violation | Medium | Critical | Ensure all data storage and processing occurs within the on-premises environment. No external cloud dependencies are permitted. | DevOps Engineer |
| R04 | Data Persistence Loss | Medium | Critical | Use named Docker volumes for PostgreSQL data. Implement a documented backup strategy for these volumes that does not rely on external cloud storage. | DevOps Engineer |
| R05 | Resource Contention | Medium | High | Define resource limits (CPU, memory) for each Docker service in the docker-compose.yml file. Monitor resource usage in the on-premises environment. | DevOps Engineer |
| R06 | Single Point of Failure | High | High | Document operational procedures for manual failover or system restoration. Acknowledge that high availability is not natively provided by Docker Compose. | Operations Manager |
| R07 | Delayed Incident Response | Medium | High | Establish a dedicated, secure physical transfer mechanism (e.g., encrypted USB drives) for security patches and incident response tools. Define an SLA for patch application. | Security Architect |
| R08 | Configuration Drift | High | Medium | Use version-controlled docker-compose.yml files and Dockerfiles. Any changes to the deployment configuration must be reviewed and approved before being transferred to the air-gapped environment. | DevOps Engineer |

## 3. Knowledge Gaps

The following items require resolution in the Design phase to finalize the risk mitigation strategies:

*   **Specific Vulnerability Scanning Tool:** The specific open-source vulnerability scanning tool to be used for offline SBOM analysis has not been selected. This decision should be made in the Design phase based on compatibility with the chosen open-source stack.
*   **Backup Retention Period:** The required retention period for PostgreSQL backups has not been defined. This should be aligned with HIPAA data retention requirements and organizational policy.
*   **Hardware Specifications:** The specific hardware specifications for the on-premises server(s) have not been defined. This will impact the resource limits set in the Docker Compose configuration.

## 4. Decision Rationale

*   **Decision:** Use Docker Compose for on-premises deployment.
*   **Rationale:** Docker Compose provides a simple, reproducible, and open-source way to define and run multi-container applications. It aligns with the requirement for no external cloud dependencies and allows for easy management of the PostgreSQL database and web application services.
*   **Binding Constraint:** The Design phase MUST ensure that all services are defined in the docker-compose.yml file and that no external services are required for the system to function.

## 5. Early Warning Signals

The following signals will trigger immediate review and action:

*   **Signal:** Increase in the number of critical CVEs affecting the open-source stack.
    *   **Action:** Trigger an immediate review of the vulnerability scanning process and update the patching schedule.
*   **Signal:** Performance degradation in the on-premises environment.
    *   **Action:** Review resource limits in the Docker Compose configuration and investigate potential resource contention.
*   **Signal:** Failure to restore backups during monthly tests.
    *   **Action:** Investigate the backup process and update the documentation and procedures as needed.

## 6. Escalation Path

*   **Level 1:** DevOps Engineer (for operational issues)
*   **Level 2:** Security Architect (for security vulnerabilities)
*   **Level 3:** Operations Manager (for resource and hardware issues)
*   **Level 4:** Project Sponsor (for strategic decisions impacting deployment)
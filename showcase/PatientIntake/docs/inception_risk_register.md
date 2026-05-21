# Inception Risk Register

## 1. Executive Summary

This document defines the risk landscape for the PatientIntake system, a HIPAA-compliant patient intake web application deployed on-premises via Docker Compose. The register categorizes risks into Regulatory (HIPAA), Technical (Open Source/Air-Gap), Operational (RBAC/Audit), and Project (Feasibility) domains. Each risk is assigned a unique identifier, likelihood, impact, and high-level mitigation strategy. Detailed technical risk analysis and specific implementation controls are deferred to the Design phase.

## 2. Regulatory & Compliance Risks (HIPAA)

These risks relate to the legal and regulatory obligations of handling Protected Health Information (PHI) under the Health Insurance Portability and Accountability Act (HIPAA).

| Risk ID | Risk Description | Likelihood | Impact | Mitigation Strategy | Owner |
| --- | --- | --- | --- | --- | --- |
| RISK-001 | Unauthorized Disclosure of PHI via Data Breach | Medium | Critical | Implement field-level encryption for all PHI fields at rest and in transit. Enforce strict RBAC. | Security Architect |
| RISK-002 | Non-Compliance with HIPAA Audit Logging Requirements | High | High | Implement immutable, append-only audit logs for all read/write operations. Ensure logs capture user, timestamp, and action. | Compliance Officer |
| RISK-003 | Failure to Secure Patient Data in Transit | Medium | High | Enforce TLS 1.2+ for all internal and external communications. Validate certificate chains. | Security Architect |
| RISK-004 | Inadequate Business Associate Agreement (BAA) Management | Low | Critical | Establish legal framework for BAA with any third-party vendors (if any). Ensure internal staff training covers BAA obligations. | Legal/Compliance |

## 3. Technical Risks (Open Source & Air-Gap)

These risks stem from the constraint of using only open-source technologies and deploying in an air-gapped, on-premises environment using Docker Compose.

| Risk ID | Risk Description | Likelihood | Impact | Mitigation Strategy | Owner |
| --- | --- | --- | --- | --- | --- |
| RISK-005 | Vulnerability Exposure in Open Source Stack | High | High | Implement a Software Bill of Materials (SBOM) generation process. Establish a manual patching workflow for air-gapped updates. | DevOps Engineer |
| RISK-006 | Key Management Complexity in Local Environment | Medium | Critical | Define a secure key storage strategy (e.g., HSM or encrypted key vault) separate from the application database. Plan for key rotation procedures. | Security Architect |
| RISK-007 | Docker Compose Orchestration Failures | Medium | Medium | Implement health checks for all services (PostgreSQL, App). Use `depends_on` with health conditions. Define restart policies. | DevOps Engineer |
| RISK-008 | Lack of Cloud-Based Backup/DR Services | High | High | Design and document a manual or script-based backup and disaster recovery procedure for the local PostgreSQL database. | DevOps Engineer |

## 4. Assumptions

- ASSUMPTION: The on-premises infrastructure meets the minimum hardware requirements for the Docker Compose stack.
- ASSUMPTION: All staff members have access to modern web browsers supporting TLS 1.2+.
- ASSUMPTION: The organization has established a process for managing open-source software vulnerabilities in an air-gapped environment.

## 5. Knowledge Gaps

- **Gap 1:** Specific key rotation frequency and algorithm for field-level encryption are not defined. Decision owner: Security Architect. Evidence needed: Industry best practices for healthcare data encryption key management.
- **Gap 2:** Exact backup frequency and retention period for the PostgreSQL database are not defined. Decision owner: DevOps Engineer. Evidence needed: Organizational data retention policies and HIPAA requirements for backup integrity.
- **Gap 3:** Specific training curriculum for HIPAA compliance for front-desk and clinical staff is not defined. Decision owner: Compliance Officer. Evidence needed: Standard HIPAA training modules and organizational requirements.
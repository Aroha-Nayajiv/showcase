# Stakeholder and Decision Rights: VeloGig Platform

## 1. Executive Summary
This artifact establishes the decision-making hierarchy and stakeholder map for the VeloGig platform. It defines the governance boundaries for the four modular entities: Tenants (Agencies/Orgs), Seekers (Providers/Workers), Clients (Vendors/Venues), and Regulations (Rules Engine). The primary objective is to map decision rights for cryptographic credential validation, offline-first edge AI operations, and multi-vertical compliance configuration, ensuring that the Governing Entity, Agency Administrator, and Gig Worker roles operate within their defined authority scopes.

## 2. Vertical-Specific Compliance and Decision Rights

### 2.1 Law Enforcement Vertical (Off-Duty Peace Officer / Deputy Management)
**Regulatory Context:** Compliance with CJIS Security Policy, state-specific POST (Peace Officer Standards and Training) regulations, and municipal labor laws governing off-duty work.

| Compliance Surface | Regulatory Requirement | Decision Owner | Architectural Surface | Technical Enforcement Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| CJIS Security Policy (Background checks, data handling) | Regulations | Governing Entity (ACT-8D5C6B1AF5) | provider_mobile_interface (SUR-E446EB8DFB) | Cryptographic Identity Validation (cryptographic_identity_validation) against state POST databases. |
| State POST Credential Verification (Active badge status) | Seekers (Gig Worker) | Gig Worker (ACT-706CCDBBAA) | provider_mobile_interface (SUR-E446EB8DFB) | State-issued ID scanning via mobile interface; local-first edge AI (SUR-95065A003D) validates badge against public registry. |
| Municipal Off-Duty Permits (Jurisdictional authorization) | Tenants (Agency Administrator) | Agency Administrator (ACT-B91695A020) | client_intake_interface (SUR-C55743A84F) | Agency Administrator configures vertical-specific compliance rules (multi_vertical_compliance) for permit requirements. |

### 2.2 Healthcare / Nursing Gigs (Registered Nurse, Travel Nurse)
**Regulatory Context:** Compliance with HIPAA (Health Insurance Portability and Accountability Act), state nursing board licensure rules, and Joint Commission standards for staffing.

| Compliance Surface | Regulatory Requirement | Decision Owner | Architectural Surface | Technical Enforcement Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| HIPAA Data Privacy (PHI protection) | Regulations | Governing Entity (ACT-8D5C6B1AF5) | provider_mobile_interface (SUR-E446EB8DFB) | Local-first edge AI (SUR-95065A003D) processes PHI locally; only encrypted, non-identifiable metadata syncs via asynchronous_offline_sync. |
| Nursing Licensure Verification (Active RN license) | Seekers (Gig Worker) | Gig Worker (ACT-706CCDBBAA) | provider_mobile_interface (SUR-E446EB8DFB) | Cryptographic Identity Validation (cryptographic_identity_validation) against state nursing boards during onboarding. |
| Staffing Ratio Compliance (Minimum nurse-to-patient) | Regulations | Agency Administrator (ACT-B91695A020) | client_intake_interface (SUR-C55743A84F) | Agency Administrator configures vertical-specific compliance rules (multi_vertical_compliance) for staffing ratios. |

### 2.3 Industrial / Hazmat Logistics (CDL Drivers, Certified Technicians)
**Regulatory Context:** Compliance with DOT (Department of Transportation) Hours of Service (HOS) regulations, CDL (Commercial Driver's License) requirements, and Hazmat safety certifications.

| Compliance Surface | Regulatory Requirement | Decision Owner | Architectural Surface | Technical Enforcement Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| DOT HOS Compliance (Driving time limits) | Regulations | Governing Entity (ACT-8D5C6B1AF5) | provider_mobile_interface (SUR-E446EB8DFB) | Local-first edge AI (SUR-95065A003D) enforces HOS rules offline; syncs audit logs via asynchronous_offline_sync. |
| CDL & Hazmat Certification (Valid license/cert) | Seekers (Gig Worker) | Gig Worker (ACT-706CCDBBAA) | provider_mobile_interface (SUR-E446EB8DFB) | Cryptographic Identity Validation (cryptographic_identity_validation) against DOT public registries. |
| Safety Protocol Configuration (Site-specific Hazmat rules) | Tenants (Agency Administrator) | Agency Administrator (ACT-B91695A020) | client_intake_interface (SUR-C55743A84F) | Agency Administrator configures vertical-specific compliance rules (multi_vertical_compliance) for site-specific safety protocols. |

### 3.1 Governing Entity (ACT-8D5C6B1AF5)
The Governing Entity owns the definition of the **Regulations** entity and the **multi_vertical_compliance** capability. They are responsible for ensuring that the **cryptographic_identity_validation** mechanism (SUR-473F48D16D) meets the highest common denominator of compliance across all verticals (e.g., CJIS, HIPAA, DOT). The Governing Entity defines the global compliance baselines that cannot be overridden by individual Tenants.

### 3.2 Agency Administrator (ACT-B91695A020)
The Agency Administrator owns the configuration of the **Regulations** entity for their specific Tenant. They are responsible for mapping the Governing Entity's compliance rules to specific client requirements via the **client_intake_interface** (SUR-C55743A84F). This includes configuring vertical-specific rules for permit requirements, staffing ratios, and site-specific safety protocols.

### 3.3 Gig Worker (ACT-706CCDBBAA)
The Gig Worker owns the integrity of their own credential data within the **provider_mobile_interface** (SUR-E446EB8DFB). They are responsible for ensuring their local device (SUR-390FDF1433) maintains valid, up-to-date credentials for offline verification. The Gig Worker is the primary actor in the **OfflineShiftMatchingandCompliance** journey, initiating the local-first edge AI validation processes.

### 3.4 Knowledge Gaps
*   **KNOWLEDGE_GAP: Specific state-level POST regulations for Law Enforcement verticals are not fully enumerated.** The Governing Entity must define the exact state registries to be integrated for cryptographic_identity_validation.
*   **KNOWLEDGE_GAP: Specific HIPAA compliance requirements for data retention and encryption standards are not fully detailed.** The Governing Entity must define the exact encryption protocols for local_device_storage (SUR-390FDF1433).

### 3.5 Assumptions
*   **ASSUMPTION: The Governing Entity has the authority to mandate compliance rules across all verticals.** This is a reversible assumption; if verticals have independent compliance boards, the governance model must be adjusted.
*   **ASSUMPTION: The Agency Administrator is the sole owner of client-specific compliance configuration.** This is a reversible assumption; if Clients have direct compliance oversight, the decision rights must be expanded.

## 4. Risk Register Summary (Compliance Focus)

| Risk ID | Risk Description | Impact | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- |
| R-COMP-001 | Failure to validate off-duty status for Law Enforcement workers | High | Cryptographic Identity Validation (cryptographic_identity_validation) against state POST databases. | Governing Entity (ACT-8D5C6B1AF5) |
| R-COMP-002 | Unauthorized access to PHI via local device storage | High | Local-first edge AI (SUR-95065A003D) processes PHI locally; only encrypted, non-identifiable metadata syncs via asynchronous_offline_sync. | Governing Entity (ACT-8D5C6B1AF5) |
| R-COMP-003 | Non-compliance with DOT HOS regulations for Hazmat drivers | Medium | Local-first edge AI (SUR-95065A003D) enforces HOS rules offline; syncs audit logs via asynchronous_offline_sync. | Governing Entity (ACT-8D5C6B1AF5) |
| R-COMP-004 | Inaccurate staffing ratios leading to patient safety issues | High | Agency Administrator configures vertical-specific compliance rules (multi_vertical_compliance) for staffing ratios. | Agency Administrator (ACT-B91695A020) |
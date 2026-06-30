# VeloGig Compliance, Privacy, and Risk Surface

## Executive Summary
This document establishes the binding compliance, privacy, and risk boundaries for the VeloGig platform. As a multi-vertical marketplace targeting Law Enforcement, Healthcare, and Industrial sectors, VeloGig must enforce strict regulatory adherence (CJIS, HIPAA, OSHA) while operating under a 'Zero-Cost Footprint' philosophy. This requires a local-first architecture where sensitive data is processed and stored on user devices, synchronized only via a serverless cloud relay. The following sections define the regulatory mapping, data sovereignty constraints, risk posture, and unresolved compliance decisions required for downstream design and development.

## 1. Regulatory Mapping and Vertical Configuration
VeloGig's core architecture abstracts workforce management into four modular entities: Tenants, Seekers, Clients, and Regulations. To satisfy multi-vertical compliance, the platform utilizes hot-swappable vertical configuration packages. Each package defines the specific regulatory rules, fee profiles, and data handling policies for a given industry.

### 1.1 Entity-to-Regime Mapping Matrix
The following matrix defines the primary regulatory obligations for each entity within the three target verticals. These obligations dictate data handling, access control, and audit requirements.

| Entity | Law Enforcement (CJIS) | Healthcare (HIPAA) | Industrial / Hazmat (OSHA/DOT) |
| :--- | :--- | :--- | :--- |
| **Tenants (Agencies/Orgs)** | CJIS Security Policy: Must enforce strict access controls, background checks for all admin users, and maintain an approved Security Plan. | Business Associate Agreement (BAA): Must ensure all data processing complies with HIPAA Privacy and Security Rules. | DOT/OSHA Compliance: Must verify provider certifications (CDL, Hazmat) and maintain safety logs. |
| **Seekers (Providers/Workers)** | CJIS Background Checks: Must pass rigorous background checks; data must be stored securely and accessed only by authorized personnel. | PHI Protection: Protected Health Information (PHI) must be encrypted at rest and in transit; access logs required. | Credential Verification: Must maintain valid, up-to-date certifications; safety training records must be accessible. |
| **Clients (Vendors/Venues)** | Data Minimization: Only receive necessary shift data; no access to full background check details. | Minimum Necessary Standard: Only receive PHI required to fulfill the service; no access to full medical history. | Safety Data: Receive only relevant safety certifications and incident reports. |
| **Regulations (Rules Engine)** | CJIS Compliance Engine: Enforces background check status, access control policies, and audit logging requirements. | HIPAA Compliance Engine: Enforces BAA status, PHI encryption, and access logging. | OSHA/DOT Compliance Engine: Enforces credential validity, safety training, and incident reporting. |

### 1.2 Law Enforcement (CJIS)
*   **Data Residency:** All data related to off-duty peace officers and deputies must be stored in compliance with CJIS Security Policy, which often requires data to be stored within specific geographic boundaries or on approved servers.
*   **Access Control:** Multi-factor authentication (MFA) is mandatory for all users accessing CJIS data. Role-based access control (RBAC) must be strictly enforced.
*   **Audit Logging:** All access to CJIS data must be logged and retained for a minimum of 12 months. Logs must be tamper-proof.
*   **Background Checks:** The platform must integrate with approved background check services to verify the status of all Seekers before they can be matched with Tenants.

### 1.3 Healthcare (HIPAA)
*   **PHI Protection:** All Protected Health Information (PHI) must be encrypted at rest (AES-256) and in transit (TLS 1.3). Access to PHI must be logged and audited.
*   **Business Associate Agreements (BAA):** VeloGig must execute BAAs with all Tenants and Seekers who handle PHI. The platform must track BAA status and prevent access for non-compliant entities.
*   **Minimum Necessary Standard:** Data sharing with Clients must be limited to the minimum necessary information required to fulfill the service.
*   **Incident Response:** A formal incident response plan must be in place to address any breaches of PHI, including notification requirements within 60 days.

### 1.4 Industrial / Hazmat (OSHA / DOT)
*   **Credential Verification:** The platform must verify the validity of all provider certifications (CDL, Hazmat, OSHA training) before allowing them to be matched with shifts.
*   **Safety Logs:** All safety incidents and near-misses must be logged and retained for a minimum of 5 years.
*   **Data Retention:** Data related to safety training and certifications must be retained for the duration of the provider's employment plus 3 years.
*   **Incident Reporting:** The platform must support real-time incident reporting and notification to relevant authorities as required by DOT regulations.

### 1.5 Governance and Ownership
*   **Compliance Owner:** Legal and Compliance team is responsible for establishing and maintaining the compliance framework for all verticals.
*   **Security Owner:** Security team is responsible for implementing and enforcing the security controls required by CJIS, HIPAA, and OSHA.
*   **Product Owner:** Product team is responsible for ensuring that the platform's features and configurations support the compliance requirements of each vertical.

### 1.6 Evidence Requirements
*   **CJIS:** Approved Security Plan, background check results, audit logs.
*   **HIPAA:** BAAs, encryption keys, access logs, incident response plan.
*   **OSHA/DOT:** Provider certifications, safety logs, incident reports.

### 2.1 Jurisdictional Data Anchoring
Data residency is not a global setting but a tenant-level configuration property. The Implied concern: Ensure no provider or shift data leaves the client network unless explicitly synced via the serverless relay ([CON-D4AD539040](../project_glossary.md#con-d4ad539040)) dictates that data must remain within the legal jurisdiction of the Tenant (Agency/Org) unless explicitly authorized for cross-border processing.

*   **Tenant-Level Data Residency Policy:** Each Tenant (e.g., a specific Law Enforcement Agency or Healthcare Network) must declare its primary data residency jurisdiction during onboarding ([JNY-87BECA0CBC](../project_glossary.md#jny-87beca0cbc)). This declaration locks the geographic region for all data generated by that Tenant's Seekers (Providers) and Clients.
*   **Local-First Storage Constraint:** Per the Zero-Cost Footprint Philosophy, primary data storage occurs on the user's device via the Architectural surface: Local-First Edge Engine ([SUR-D1A2EE5B7A](../project_glossary.md#sur-d1a2ee5b7a)). This inherently satisfies local data sovereignty requirements for PII and credential data ([CON-2D0886886F](../project_glossary.md#con-2d0886886f)), as data does not leave the device until explicitly synced.
*   **Serverless Relay Routing:** The Architectural surface: Serverless Cloud Relay ([SUR-50E19DC151](../project_glossary.md#sur-50e19dc151)) must route and store sync data in region-specific buckets or databases. Cross-region replication is strictly prohibited unless explicitly configured by the Tenant's governance policy.

### 2.2 Cross-Border Data Transfer Controls
Cross-border data transfers are a high-risk activity that must be explicitly governed:

*   **Explicit Tenant Authorization:** Any cross-border data transfer must be explicitly authorized by the Actor role: Agency Administrator ([ACT-B91695A020](../project_glossary.md#act-b91695a020)) or Actor role: Platform Operator ([ACT-0E3EE366E3](../project_glossary.md#act-0e3ee366e3)) via the [JNY-F9EFC8A7AD](../project_glossary.md#jny-f9efc8a7ad): Tenant Policy Configuration and Governance journey.
*   **Legal Basis Documentation:** The platform must maintain a record of the legal basis for each cross-border transfer (e.g., Standard Contractual Clauses, adequacy decisions). This record must be stored within the Tenant's data residency boundary.
*   **Data Minimization:** Cross-border transfers should only include data that is strictly necessary for the intended purpose. PII and sensitive data should be anonymized or pseudonymized where possible before transfer.

### 2.3 Data Residency Enforcement Mechanisms
*   **Infrastructure Isolation:** The Architectural surface: Data Residency and Multi-Tenant Isolation Surface ([SUR-2FFD65DB4F](../project_glossary.md#sur-2ffd65db4f)) must enforce physical or logical isolation of data stores based on jurisdiction. Multi-tenancy must not allow data leakage between jurisdictions.
*   **Audit Trails:** All data access, transfer, and modification events must be logged in the Implied concern: Maintain immutable audit trails for all configuration changes, overrides, and state changes ([CON-9B0CF18683](../project_glossary.md#con-9b0cf18683)). These logs must be retained within the jurisdiction of the data subject.
*   **Automated Compliance Checks:** The Architectural surface: Policy & Rules Engine ([SUR-782954DB8D](../project_glossary.md#sur-782954db8d)) must enforce data residency policies. Any attempt to transfer data outside the authorized jurisdiction must be blocked and logged.

### 2.4 Decision Rationale
The decision to enforce data residency at the Tenant level, rather than globally, is driven by the need to support multi-tenant operations across diverse regulatory environments. A global policy would either be too restrictive (preventing necessary cross-border operations) or too permissive (violating local laws). Tenant-level configuration allows for flexibility while maintaining strict compliance.

The decision to leverage the Local-First Edge Engine for primary data storage is driven by the Zero-Cost Footprint Philosophy and the inherent security benefits of keeping PII on-device. This reduces the attack surface and simplifies compliance with data residency laws, as data does not leave the device until explicitly synced.

### 2.5 Validation Criteria
*   **Testability:** Data residency policies can be validated by attempting to sync data from a Tenant in one jurisdiction to a serverless relay in another jurisdiction. The system should block the sync and log the violation.
*   **Traceability:** All data residency policies must be traceable to the specific regulatory requirements ([CJIS,HIPAA,GDPR,CCPA]) they satisfy.
*   **Completeness:** The artifact must cover all major jurisdictions where VeloGig operates (US, EU, etc.) and all regulatory verticals (Law Enforcement, Healthcare, Industrial).

### 2.6 Assumptions
*   **ASSUMPTION:** The platform will use a cloud provider that offers region-specific data storage and processing capabilities (e.g., AWS, Azure, GCP). This assumption is necessary to implement the data residency boundaries defined in this artifact.
*   **ASSUMPTION:** Legal counsel will provide the specific regulatory requirements for each jurisdiction and vertical. This assumption is necessary to configure the data residency policies accurately.

### 2.7 Follow-Up Questions
*   **Question:** What are the specific data residency requirements for Industrial/Hazmat logistics in non-US regions?
    *   **Why Critical:** These requirements are necessary to configure the data residency policies for Industrial Tenants operating in non-US regions.
    *   **Answerable:** No - requires legal counsel.
    *   **Blocking:** Yes - prevents accurate configuration of data residency policies.
*   **Question:** What is the exact mechanism for verifying Business Associate Agreements (BAAs) for Healthcare Tenants?
    *   **Why Critical:** This mechanism is necessary to ensure HIPAA compliance for Healthcare Tenants.
    *   **Answerable:** No - requires legal and operational input.
    *   **Blocking:** Yes - prevents accurate configuration of HIPAA compliance controls.

## 3. Risk Posture and Control Matrices
The VeloGig platform faces unique risks due to its local-first, offline-capable architecture. The following risk controls are established to mitigate these risks.

### 3.1 Offline Field Execution and Clock-In (JNY-F6CC7FB09F)
*   **Risk:** Fraudulent clock-ins or shift swaps in offline mode.
*   **Control:** Robust local heuristics must be developed to detect spoofed location or biometric bypass attempts before syncing ([CON-08EB4DC34B](../project_glossary.md#con-08eb4dc34b)). The Offline Shift Conflict Resolution Algorithm ([CAP-OFFLINE-SHIFT-CONFLICT-RESOLUTION-ALGORITHM](../project_glossary.md#cap-offline-shift-conflict-resolution-algorithm)) must be implemented to handle scheduling overrides and conflicts.
*   **Key Management:** Cryptographic key management must be secure, handling private keys for offline signing and SSI credentials without central dependency ([CON-BDA3D95A26](../project_glossary.md#con-bda3d95a26)).

### 3.2 Network Partition Tolerance (CON-B861BB9CEA)
*   **Risk:** Data inconsistency or loss during network partitions.
*   **Control:** The platform must guarantee data integrity and eventual consistency when the local-edge and cloud-relay layers are disconnected. Core scheduling and compliance capability must be sustained for network isolations >72 hours (CON-<timestamp>).

### 3.3 Device Integrity and Root Detection (JNY-07268FC66F)
*   **Risk:** Compromised devices attempting to bypass security controls.
*   **Control:** The Edge Device Integrity and Root Detection Engine ([CAP-EDGE-DEVICE-INTEGRITY-AND-ROOT-DETECTION-ENGINE](../project_glossary.md#cap-edge-device-integrity-and-root-detection-engine)) must be implemented to verify device integrity before allowing access to sensitive data or operations.

### 3.4 Cryptographic Key Management (CON-BDA3D95A26)
*   **Risk:** Compromise of private keys leading to unauthorized access or data tampering.
*   **Control:** Private keys must be secured within device secure enclaves or hardware-backed keystores ([CON-F8A3E7F999](../project_glossary.md#con-f8a3e7f999)). High-entropy curve cryptography must be enforced for offline device-to-device connections ([CON-5DC20C5FDE](../project_glossary.md#con-5dc20c5fde)).

### 3.5 Money Transmitter License (MSB)
*   **Decision Axis:** Should the platform act as a licensed Money Transmitter (MSB) to facilitate InstantPay, or rely on third-party split-payment providers?
*   **Impact:** Directly affects financial compliance liability, regulatory overhead, and integration complexity.
*   **Owner:** Legal / Finance
*   **Evidence Needed:** Regulatory analysis of MSB requirements in target jurisdictions vs. cost of third-party payment providers.

### 3.7 Local-First AI Compliance Enforcement
*   **Decision Axis:** How strictly does the local-first AI enforce regulatory compliance versus providing advisory suggestions when operating in offline mode with conflicting or outdated local vector databases?
*   **Impact:** Affects the design of the local AI engine and the user experience for compliance-critical actions.
*   **Owner:** Security / Legal / Product
*   **Evidence Needed:** Risk assessment of offline compliance failures vs. user experience impact of strict enforcement.

### 3.8 Data Residency Jurisdiction Confirmation
*   **Decision Axis:** Which specific jurisdictions will VeloGig initially support, and what are the exact data residency requirements for each?
*   **Impact:** Drives the architecture of the Multi-Tenant Namespace Management ([CAP-MULTI-TENANT-NAMESPACE-MANAGEMENT](../project_glossary.md#cap-multi-tenant-namespace-management)) and data routing logic.
*   **Owner:** Legal / Product
*   **Evidence Needed:** Market analysis and legal review of target jurisdictions.

## 4. Binding Constraints for Downstream Phases
The following constraints are binding for all downstream design and development phases:

1.  **Local-First Data Storage:** All PII and credential data must be stored locally on the user's device. No PII may be transmitted to the serverless cloud relay without explicit user consent and encryption (CON-2D0886886F, [CON-F26B1E3984](../project_glossary.md#con-f26b1e3984)).
2.  **Offline Capability:** The platform must maintain 100% core scheduling and compliance capability during network isolations >72 hours (CON-<timestamp>).
3.  **Device Integrity:** All devices must undergo integrity verification and root detection before accessing sensitive data or operations (CAP-EDGE-DEVICE-INTEGRITY-AND-ROOT-DETECTION-ENGINE).
4.  **Cryptographic Security:** All data must be encrypted at rest (AES-256) and in transit (TLS 1.3). Private keys must be secured in device secure enclaves (CON-F26B1E3984, CON-F8A3E7F999).
5.  **Immutable Audit Trails:** All configuration changes, overrides, and state changes must be logged in an immutable audit trail (CON-9B0CF18683).
6.  **Regulatory Configuration:** The platform must support hot-swappable vertical configuration packages to accommodate different regulatory regimes (CJIS, HIPAA, OSHA) without code changes.

## 5. Cross-Reference to Sibling Artifacts
*   **Local-First Edge Engine (SUR-D1A2EE5B7A):** The compliance constraints for data storage and encryption are implemented within the Local-First Edge Engine. See the Technical Constraints artifact for detailed architectural specifications.
*   **Serverless Cloud Relay (SUR-50E19DC151):** The compliance constraints for data synchronization and health monitoring are implemented within the Serverless Cloud Relay. See the Technical Constraints artifact for detailed architectural specifications.
*   **Viral Growth Loop Orchestration ([CAP-VIRAL-GROWTH-LOOP-ORCHESTRATION](../project_glossary.md#cap-viral-growth-loop-orchestration)):** The compliance constraints for data privacy must be considered when designing the viral growth loops to ensure that user data is not shared without consent.
*   **Financial Settlement Ledger ([SUR-778E10F5D5](../project_glossary.md#sur-778e10f5d5)):** The compliance constraints for financial data (1099-K/1099 forms) are implemented within the Financial Settlement Ledger. See the Financial Compliance artifact for detailed specifications.

## 6. Conclusion
This Compliance, Privacy, and Risk Surface document establishes the foundational regulatory and security boundaries for the VeloGig platform. By adhering to these constraints and resolving the identified knowledge gaps, VeloGig can ensure a secure, compliant, and scalable multi-vertical marketplace. The local-first architecture provides a strong foundation for data privacy and offline resilience, while the hot-swappable vertical configuration packages enable flexibility across different regulatory regimes. Downstream phases must strictly adhere to these binding constraints and address the unresolved compliance decisions to ensure a successful launch.

#### Law Enforcement (CJIS)
*   **Data Residency:** All data related to off-duty peace officers and deputies must be stored in compliance with CJIS Security Policy, which often requires data to be stored within specific geographic boundaries or on approved servers.
*   **Access Control:** Multi-factor authentication (MFA) is mandatory for all users accessing CJIS data. Role-based access control (RBAC) must be strictly enforced.
*   **Audit Logging:** All access to CJIS data must be logged and retained for a minimum of 12 months. Logs must be tamper-proof.
*   **Background Checks:** The platform must integrate with approved background check services to verify the status of all Seekers before they can be matched with Tenants.

#### Healthcare (HIPAA)
*   **PHI Protection:** All Protected Health Information (PHI) must be encrypted at rest (AES-256) and in transit (TLS 1.3). Access to PHI must be logged and audited.
*   **Business Associate Agreements (BAA):** VeloGig must execute BAAs with all Tenants and Seekers who handle PHI. The platform must track BAA status and prevent access for non-compliant entities.
*   **Minimum Necessary Standard:** Data sharing with Clients must be limited to the minimum necessary information required to fulfill the service.
*   **Incident Response:** A formal incident response plan must be in place to address any breaches of PHI, including notification requirements within 60 days.

#### Industrial / Hazmat (OSHA / DOT)
*   **Credential Verification:** The platform must verify the validity of all provider certifications (CDL, Hazmat, OSHA training) before allowing them to be matched with shifts.
*   **Safety Logs:** All safety incidents and near-misses must be logged and retained for a minimum of 5 years.
*   **Data Retention:** Data related to safety training and certifications must be retained for the duration of the provider's employment plus 3 years.
*   **Incident Reporting:** The platform must support real-time incident reporting and notification to relevant authorities as required by DOT regulations.
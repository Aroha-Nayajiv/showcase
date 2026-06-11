# 1. Whole Product Vision and Scope

This artifact establishes the authoritative product model for **velogig**, a next-generation universal marketplace and workforce dispatch platform. The scope explicitly covers the four foundational entities: **Tenants** (Agencies/Orgs managing workforce and costs), **Seekers** (Providers/Workers like off-duty officers, nurses, CDL drivers), **Clients** (Vendors/Venues requesting labor), and **Regulations** (the Rules Engine managing compliance and policy blocks). It outlines the primary user journeys including **ProviderOnboarding** (cryptographic credential validation), **OfflineClock-In** (local-first GPS/biometric logging), **LocalSchedulingMatch** (edge AI regulatory checks), and **ClientInvoiceProcessing**. The scope includes the strategic operating model of applying hot-swappable vertical configuration packages over a unified codebase to achieve zero baseline compute costs for agencies.

**BOUNDS:** This artifact does not define the specific technical implementation of the local-first edge AI algorithms, the exact database schema for the vector DB, or the specific API contracts for third-party integrations. It strictly defines the business capabilities, user roles, and high-level system boundaries. It explicitly excludes detailed financial modeling for the InstantPay liquidity fee structure (1.5%-2.5%) beyond its existence as a business rule, and does not specify the exact municipal bidding cycle elimination tactics, only the goal of achieving $0 base software costs to bypass them.

## 1.1. Foundational Entity Definitions and Data Contracts

The platform operates on a strict multi-tenant architecture where data ownership and interaction boundaries are explicitly defined to ensure separation of concerns. Each entity represents a distinct class of actor with specific lifecycle obligations and data sovereignty rules.

### 1.1.1. Tenants (Agencies/Orgs)
Tenants are the primary commercial entities that subscribe to the platform to manage their workforce and pay base software costs. They act as the administrative boundary for all associated Seekers and Clients.

*   **Structural Boundary:** A Tenant represents a legal or operational entity (e.g., a municipal agency, a healthcare staffing firm, or an industrial contractor). The Tenant owns the configuration packages, regulatory rulesets, and billing relationships for its vertical.
*   **Data Contract:**
    *   **Ownership:** The Tenant owns all configuration data, policy definitions, and aggregate workforce metrics.
    *   **Scope:** Tenant data is strictly siloed. A Tenant cannot access raw data belonging to another Tenant.
    *   **Key Attributes:** `tenant_id`, `vertical_type` (Law Enforcement, Healthcare, Industrial), `base_software_cost` (target: $0), `configuration_packages` (hot-swappable vertical modules).
*   **Interaction Boundary:** Tenants configure the platform's behavior (e.g., defining which regulations apply to their Seekers) but do not directly manage individual Seeker credentials or Client invoices. They interact with the Regulations engine to define policy blocks.

### 1.1.2. Seekers (Providers/Workers)
Seekers are the individual providers of specialized labor, such as off-duty officers, nurses, or CDL drivers. They are the core asset of the platform, managed cryptographically.

*   **Structural Boundary:** A Seeker is an individual user account linked to a specific Tenant (or multiple Tenants if cross-agency work is permitted). Their identity is anchored by cryptographic validation of professional credentials.
*   **Ownership:** The Seeker owns their private key and the encrypted wallet containing their credentials. The Tenant owns the association and the audit logs of the Seeker's activity.
*   **Scope:** Seeker data includes credential hashes, device signatures, and activity logs (Clock-In/Out). Sensitive PII is stored locally on the device and only hashed/signed data is synced to the cloud.
*   **Key Attributes:** `seeker_id`, `credential_hash`, `device_signature`, `wallet_encryption_key`, `availability_status`.
*   **Interaction Boundary:** Seekers interact directly with the Regulations engine via the LocalSchedulingMatch journey to ensure compliance. They do not interact directly with Tenants for scheduling; instead, they respond to Client requests filtered by Tenant-defined rules.

### 1.1.4. Regulations (Rules Engine)
Regulations are not a user entity but a dynamic, configurable rules engine that governs compliance, fee structures, and policy blocks per vertical.

*   **Structural Boundary:** The Regulations engine is a modular component that can be hot-swapped per Tenant vertical. It defines the legal and operational constraints for Seeker activities.
*   **Data Contract:**
    *   **Ownership:** The platform owns the core engine logic; Tenants own the specific rule sets and policy configurations for their vertical.
    *   **Scope:** Regulations data includes labor law constraints, fee calculation parameters, and compliance checklists.
    *   **Key Attributes:** `regulation_id`, `vertical_type`, `rule_set_version`, `compliance_status`.
*   **Interaction Boundary:** The Regulations engine is invoked by the LocalSchedulingMatch journey to validate Seeker availability and Client requests against Tenant-defined rules. It does not directly interact with Tenants for configuration updates, which are handled via the Tenant administrative interface.

## 1.2. Hot-Swappable Vertical Configuration Strategy

The platform's core value proposition relies on the ability to deploy specialized workforce management logic without altering the foundational codebase. This is achieved through a modular configuration system.

*   **Mechanism:** Vertical-specific logic (e.g., Law Enforcement shift rules, Healthcare credentialing requirements, Industrial safety protocols) is encapsulated in discrete configuration packages.
*   **Isolation:** These packages are strictly isolated at the data and execution layer. A configuration package for Law Enforcement cannot access or modify the data structures of the Healthcare vertical.
*   **Deployment:** Configuration packages are deployed and activated per Tenant. A Tenant can switch between vertical configurations or enable multiple verticals simultaneously, provided the underlying data models support the union of those verticals.
*   **Constraints:** The hot-swappable nature must not compromise data privacy or security boundaries. Each vertical package must adhere to the platform's core security protocols, including cryptographic validation of credentials and immutable audit logging.

## 1.3. Zero-Cost Footprint Architectural Constraints

To achieve the strategic goal of zero baseline compute costs for agencies, the platform enforces strict architectural constraints.

*   **Edge AI Offloading:** Compute-heavy processes, such as credential validation, regulatory checks, and scheduling optimization, are offloaded to user devices via local-first edge AI. This eliminates server-side compute costs for these operations.
*   **Serverless Cloud Relay:** The cloud infrastructure serves only as a relay for asynchronous data synchronization and coordination. It does not perform heavy lifting for core business logic.
*   **Offline Capability:** Field operations must sustain 100% core capability during network isolations extending past 72 continuous hours. All critical data is stored and processed locally, with asynchronous synchronization upon reconnection.
*   **Immutable Audit Logging:** Every configuration change, manual assignment bypass, or override must log an immutable audit entry with timestamp and device signature. This ensures accountability and compliance without requiring real-time server-side validation.

## 1.4. Primary User Journeys

The platform supports four primary user journeys that define the core interactions between Tenants, Seekers, and Clients.

1.  **ProviderOnboarding:**
    *   **Action:** Seekers scan state-issued ID and professional credentials.
    *   **Validation:** Cryptographic validation against public registries.
    *   **Storage:** Wrap credentials in encrypted device-local wallet.
    *   **Outcome:** Seeker is registered and ready for dispatch.

2.  **OfflineClock-In:**
    *   **Action:** Seekers log high-accuracy GPS delta and cellular beacon scans.
    *   **Capture:** Wi-Fi BSSID snapshots and biometric facial check.
    *   **Storage:** Store and sign data locally with user private key.
    *   **Synchronization:** Asynchronously sync upon reconnection.

3.  **LocalSchedulingMatch:**
    *   **Action:** Store regulatory docs in localized vector DB.
    *   **Processing:** Run semantic search via local LLM to check labor regulations.
    *   **Resolution:** Propose legally compliant settlement for offline disputes.
    *   **Outcome:** Match is proposed and validated against local regulations.

4.  **ClientInvoiceProcessing:**
    *   **Action:** Clients sign up via mobile web modal with corporate card.
    *   **Request:** Request specialized labor.
    *   **Payment:** InstantPay advances funds to workers minus a 1.5%-2.5% liquidity convenience fee.
    *   **Outcome:** Invoice is processed and funds are disbursed.

## 1.5. Success Criteria and Decision Foundations

*   **Uptime:** Achieve 99.99% uptime for serverless cloud coordination layer.
*   **Cost:** Maintain zero egress fees using flat-file object storage.
*   **Adoption:** Eliminate municipal bidding cycles by keeping base software costs at $0 for managing agencies.
*   **Resilience:** Support asynchronous execution with 32k context window on edge devices.

## 1.6. Knowledge Gaps and Open Decisions

*   **KNOWLEDGE_GAP:** Exact regulatory requirements for cryptographic credential validation in each target vertical (Law Enforcement, Healthcare, Industrial) - must be established by legal/compliance authority.
*   **KNOWLEDGE_GAP:** Specific technical implementation details for local-first edge AI algorithms - to be defined in the design phase.
*   **ASSUMPTION:** The 1.5%-2.5% liquidity convenience fee for InstantPay is binding - reversible pending financial modeling confirmation.
*   **ASSUMPTION:** The platform can sustain 100% core capability during 72-hour network isolations - reversible pending edge device performance testing.

## 1.7. Follow-Up Questions

*   What specific regulatory bodies define the cryptographic validation standards for each target vertical?
*   What are the exact performance benchmarks for local-first edge AI on target devices?
*   Who is the authoritative source for the InstantPay liquidity fee structure?
*   What are the specific technical requirements for 72-hour offline operation on target devices?
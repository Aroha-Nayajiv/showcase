# Success Criteria and Decision Foundations

This section establishes the definitive success criteria and strategic boundaries for the VeloGig platform, serving as the primary reference for all downstream product and design phases. The scope explicitly includes the cryptographic validation of credentials against public registries, the local-first edge AI offloading for compute-heavy processes, and the 72-hour network isolation capability for field operations. It bounds the project by explicitly excluding municipal bidding cycles (keeping base software costs at $0) and defining the InstantPay liquidity fee structure (1.5%-2.5%). Critical decision foundations include the specific regulatory compliance requirements for each vertical, the exact technical implementation of the 32k context window on edge devices, and the serverless cloud coordination layer architecture required to achieve 99.99% uptime. This artifact also identifies the key knowledge gaps regarding specific state-issued ID scanning protocols and the precise API contracts for public registry validation, which must be resolved before design can proceed.

### 1.1 Viral Loop Success Criteria

To validate the viability of the growth model, the following measurable success criteria must be established for the Shift-Swap Flywheel and the Shared Invoicing Injection Point:

*   **Shift-Swap Flywheel Conversion Rate:** The percentage of unregistered colleagues successfully onboarded into the platform as Seekers (Providers) when delegated a shift by an existing Seeker. Target: >15% conversion from delegation to active credentialing.
*   **Shared Invoicing Injection Point Activation:** The percentage of B2B bill-payers (Clients) who convert to active platform users after receiving an interactive digital invoice link. Target: >25% activation rate from invoice receipt to platform sign-up.
*   **Inter-Agency Cooperative Gig Reach:** The average number of new enterprise Tenants (Agencies) acquired per surge-demand broadcast event. Target: >3 new Tenants per broadcast cycle.

### 1.2 Decision Foundations: Modular Entities

The platform is built on four modular entities. Their interactions across verticals (Law Enforcement, Healthcare, Industrial) are governed by the following decision foundations:

*   **Tenants:** Agencies or organizations that manage workforce and pay base software costs. 
    *   **Decision:** Base software costs must remain at $0 to eliminate municipal bidding cycles.
    *   **Knowledge Gap:** Specific state-issued ID scanning protocols for each vertical must be defined to ensure accurate credential validation.
*   **Seekers:** Providers or workers such as off-duty officers, nurses, or CDL drivers. 
    *   **Decision:** Providers must undergo cryptographic validation of credentials against public registries during onboarding.
    *   **Knowledge Gap:** Precise API contracts for public registry validation must be established to ensure real-time credential checks.
*   **Clients:** Vendors or venues requesting specialized labor within geofenced areas. 
    *   **Decision:** Clients must sign up via a mobile web modal with a corporate card.
    *   **Assumption:** Corporate card processing will be handled by a third-party payment gateway; specific vendor to be selected in Design phase.
*   **Regulations:** The rules engine managing compliance, fee structures, and policy blocks per vertical. 
    *   **Decision:** Every configuration change, manual assignment bypass, or override must log an immutable audit entry with timestamp and device signature.
    *   **Knowledge Gap:** Specific regulatory compliance requirements for Law Enforcement, Healthcare, and Industrial/Hazmat sectors must be documented to configure the rules engine.

### 1.3 Critical Knowledge Gaps

The following knowledge gaps must be resolved before the Design phase can proceed:

1.  **State-Issued ID Scanning Protocols:** Specific protocols for scanning and validating state-issued IDs for each vertical (Law Enforcement, Healthcare, Industrial) are not yet defined. Owner: Product/Compliance. Impact: Blocks ProviderOnboarding journey design.
2.  **Public Registry API Contracts:** Precise API contracts for public registry validation are not yet established. Owner: Engineering/Compliance. Impact: Blocks cryptographic validation logic design.
3.  **Vertical-Specific Regulatory Requirements:** Detailed regulatory compliance requirements for each vertical are not yet documented. Owner: Compliance/Legal. Impact: Blocks Regulations rules engine configuration.
4.  **Edge AI Model Selection:** The specific edge AI model to be used for local scheduling and regulatory checks is not yet selected. Owner: Engineering. Impact: Blocks local-first edge AI offloading design.
5.  **Fee Profile Configurations:** The exact fee profile configurations for InstantPay (1.5%-2.5% liquidity convenience fee) are not yet finalized for each vertical. Owner: Product/Finance. Impact: Blocks InstantPay liquidity logic design.

### 2.2 Seekers (Providers/Workers)
*   **Role:** Off-duty officers, nurses, CDL drivers, etc.
*   **Decision Foundation:** Seekers are the core asset. Their credentials must be cryptographically validated against public registries (e.g., POST for law enforcement, State Nursing Boards for healthcare) to ensure legal compliance and platform integrity.
*   **Constraint:** Seekers must maintain a device-local encrypted wallet for their credentials and private keys to support offline-first operations.

### 2.3 Clients (Vendors/Venues)
*   **Role:** Request specialized labor within geofenced areas.
*   **Decision Foundation:** Clients must be able to sign up via a frictionless mobile web modal, using corporate cards or bank accounts, to instantly request labor without enterprise sales cycles.
*   **Constraint:** Client invoicing must support interactive digital links that can convert B2B bill-payers into platform users (Shared Invoicing Injection Point).

### 2.4 Regulations (Rules Engine)
*   **Role:** Manage compliance, fee structures, and policy blocks per vertical.
*   **Decision Foundation:** The Regulations entity must be hot-swappable via vertical configuration packages. It must enforce local labor laws, collective bargaining agreements, and industry-specific compliance (e.g., HIPAA, OSHA, DOT).
*   **Constraint:** Every configuration change, manual assignment bypass, or override must log an immutable audit entry with timestamp and device signature.

## 3. Vertical Adaptation Matrix

The platform applies hot-swappable vertical configuration packages over a unified codebase. The following matrix defines the specific adaptations for each target vertical.

| Vertical | Provider (Seeker) | Governing Entity | Critical Compliance | Fee Structure |
| :--- | :--- | :--- | :--- | :--- |
| **Law Enforcement** | Off-Duty Peace Officer/Deputy | Law Enforcement Agency (LEA) | Overtime policies, Collective Bargaining Agreements, POST certifications | Hourly rate + department admin fee + asset recovery fee (cruiser usage) |
| **Healthcare/Nursing** | Registered Nurse/Travel Nurse | Hospital System/Nursing Board | License verification, Malpractice caps, Patient-to-staff ratios | Tiered shift pay + credential compliance surcharge |
| **Industrial/Hazmat** | CDL Driver/Certified Tech | Logistics Carrier/OSHA Admin | DOT Hours of Service (HOS), Drug screening windows | Mileage + deadhead fees + equipment surcharge |

### 4.1 Local-First Edge AI Architecture
*   **Decision Foundation:** Compute-heavy processes (real-time matching, data storage, compliance auditing) are offloaded to user devices via a local-first, containerized edge AI engine (Ollama/vLLM/SGLang runtimes, asynchronous execution, 32k context window, 4-bit or 8-bit quantized SLMs like Llama-3-8B-Instruct or Phi-3-Medium) paired with a serverless cloud relay.
*   **Constraint:** Centralized infrastructure cost approaches zero. Desktop admin nodes run the full scheduling and compliance engine locally.

### 4.2 Offline-First Field Operations
*   **Decision Foundation:** Mobile clients cache all vital job states, coordinates, compliance requirements, and scheduling profiles locally. Full offline operation is required.
*   **Constraint:** Field operations must sustain 100% core capability during network isolations extending past 72 continuous hours. Cryptographic Field Proofs (Proof of Presence) are stored locally and synchronized asynchronously upon reconnection.

### 4.3 InstantPay Liquidity Model
*   **Decision Foundation:** InstantPay advances funds to workers minus a 1.5%-2.5% liquidity convenience fee.
*   **Knowledge Gap:** The exact fee profile configurations for InstantPay (1.5%-2.5% liquidity convenience fee) are not yet finalized for each vertical. Owner: Product/Finance. Impact: Blocks InstantPay liquidity logic design.

## 5. Unresolved Assumptions and Gaps

The following assumptions and gaps must be resolved or ratified before the Design phase can proceed.

| Item | Type | Description | Owner | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **State-Issued ID Scanning** | Knowledge Gap | Specific protocols for scanning and validating state-issued IDs for each vertical are not yet defined. | Product/Compliance | Blocks ProviderOnboarding journey design. |
| **Public Registry API Contracts** | Knowledge Gap | Precise API contracts for public registry validation are not yet established. | Engineering/Compliance | Blocks cryptographic validation logic design. |
| **Vertical-Specific Regulatory Requirements** | Knowledge Gap | Detailed regulatory compliance requirements for each vertical are not yet documented. | Compliance/Legal | Blocks Regulations rules engine configuration. |
| **Edge AI Model Selection** | Knowledge Gap | The specific edge AI model to be used for local scheduling and regulatory checks is not yet selected. | Engineering | Blocks local-first edge AI offloading design. |
| **Fee Profile Configurations** | Knowledge Gap | The exact fee profile configurations for InstantPay (1.5%-2.5% liquidity convenience fee) are not yet finalized for each vertical. | Product/Finance | Blocks InstantPay liquidity logic design. |
| **Corporate Card Processing** | Assumption | Corporate card processing will be handled by a third-party payment gateway; specific vendor to be selected in Design phase. | Product/Finance | Blocks Client sign-up flow design. |

## 6. Success Criteria Summary

The success of the VeloGig platform will be measured against the following criteria:

1.  **99.99% Uptime for Serverless Cloud Coordination Layer:** Ensures high availability for the serverless cloud coordination layer, which is critical for real-time shift matching and credential validation.
2.  **Zero Egress Fees Using Flat-File Object Storage:** Ensures cost efficiency by using flat-file object storage, which is critical for maintaining zero base software costs for managing agencies.
3.  **Eliminate Municipal Bidding Cycles by Keeping Base Software Costs at $0:** Ensures competitive advantage by eliminating municipal bidding cycles, which is critical for rapid market penetration.
4.  **Support Asynchronous Execution with 32k Context Window on Edge Devices:** Ensures field operations can sustain 100% core capability during network isolations extending past 72 continuous hours, which is critical for reliability in remote or high-risk environments.
5.  **Viral Loop Conversion Rates:** >15% conversion for Shift-Swap Flywheel; >25% activation for Shared Invoicing Injection Point.

## 7. Follow-Up Questions

The following questions must be answered to resolve the knowledge gaps and assumptions identified in this artifact:

1.  **What specific state-issued ID scanning protocols are required for each vertical?** This is critical for defining the ProviderOnboarding journey.
2.  **What are the precise API contracts for public registry validation?** This is critical for designing the cryptographic validation logic.
3.  **What are the detailed regulatory compliance requirements for each vertical?** This is critical for configuring the Regulations rules engine.
4.  **What specific edge AI model will be used for local scheduling and regulatory checks?** This is critical for designing the local-first edge AI offloading architecture.
5.  **What are the exact fee profile configurations for InstantPay for each vertical?** This is critical for designing the InstantPay liquidity logic.
6.  **What third-party payment gateway will be used for corporate card processing?** This is critical for designing the Client sign-up flow.
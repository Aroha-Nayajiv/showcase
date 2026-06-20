# Decision Foundations and Open Questions

## 1. Executive Summary and Strategic Scope

This artifact establishes the binding decision foundations, regulatory constraints, and open strategic questions for the MealCredit platform (Daya). It serves as the central decision registry for the Inception phase, capturing the strategic and operational choices required to validate the tripartite marketplace model across the initial metropolitan footprints of San Francisco, New York City, and Chicago.

The platform mission is to decouple food assistance from social stigma by converting real-time financial micro-donations into fractional, anonymous culinary credits. This document defines the financial mechanics, the absolute compliance boundaries (PCI-DSS Level 1, SOC2 Type II, CCPA/GDPR), and the data ownership models that govern the interactions between Funders, Recipients, Providers, and Facilitators.

### 1.1 Funder (Donor) Engagement
The Funder provides liquidity via micro-donation round-ups. The Funder's experience is defined by the **Funder Engagement and Credit Allocation** journey (JNY-8D19B04053), where they receive immutable transactional receipts upon redemption. This process enforces strict zero-knowledge anonymity (CON-705CB41089), strictly prohibiting the transmission of any identifying beneficiary parameters to the Funder.

### 1.2 Platform (Daya/MealCredit) Intermediation
The Platform acts as the intermediary, managing the Credit Pool and enforcing PCI-DSS Level 1 compliance (CON-5D30D227A5). It ensures multi-tenant data segregation across SF, NYC, and Chicago (CON-2BCB3D9CF7). The Platform owns the financial transaction data, while NGOs retain ownership of the vetting data (CON-3D3BCC51A5).

### 1.3 Provider (Restaurant) Fulfillment
The Provider receives automated daily net payouts via Stripe Connect. Providers must be able to toggle real-time throttle parameters to prevent structural overload. This ensures the **Provider & Fulfillment Management** capability (CAP-D96776E7F7) is robust and scalable.

### 1.4 Financial Licensing and Payment Rail Constraints (Stripe Issuing & Connect)
The platform operates as a fintech intermediary, necessitating strict adherence to financial licensing and anti-money laundering (AML) frameworks. The decision to utilize Stripe Issuing for virtual card tokenization and Stripe Connect for merchant payouts creates specific binding constraints:

*   **Binding Constraint - PCI-DSS Level 1 Adherence:** The platform must implement PCI-DSS Level 1 compliance by never storing raw credit card data. All donor funding flows must utilize Stripe Elements and the Stripe SDK globally. The platform's role is strictly limited to orchestrating the tokenization and allocation of funds, not processing or retaining sensitive cardholder data.
*   **Binding Constraint - Financial Licensing (CON-D5D5F5B8C2):** The platform must comply with financial licensing requirements for moving funds via Stripe Issuing and Stripe Connect. This requires ensuring that the platform's legal entity structure aligns with Stripe's underwriting requirements for Issuing and Connect, particularly regarding the flow of funds from Donors to the central credit pool, and subsequently to Providers via Stripe Connect.
*   **Binding Constraint - Real-time Synchronization (CON-8F05AD69D4):** To prevent double-spending, the system must maintain real-time synchronization between virtual credit issuance and physical POS terminal clearing. This requires leveraging Stripe's webhook infrastructure to ensure that credit pool balances are updated instantaneously upon redemption, preventing ledger discrepancies across the three metro footprints.
*   **Binding Constraint - Automated Regulatory Reporting (CON-6431109B98):** The platform must generate automated regulatory reporting to satisfy financial compliance requirements without manual intervention. This includes maintaining immutable audit trails via AWS CloudTrail (CON-7655D2A8DE) and ensuring all financial ledger entries are retained indefinitely in Aurora Postgres for compliance purposes (CON-3E7B720F8F).

### 1.5 Absolute Anonymization and Zero-Knowledge Architecture
The core mission of decoupling food assistance from social stigma requires a zero-knowledge anonymity model between Funders and Recipients. This is not merely a privacy feature but a binding operational constraint:

*   **Binding Constraint - Strict Zero-Knowledge Anonymity (CON-705CB41089):** There must be strict zero-knowledge anonymity between Funders and Recipients to prevent social stigma and tracking. Donors must receive immutable transactional receipts within the required latency window of redemption, strictly prohibiting the transmission of any identifying beneficiary parameters. The platform's architecture must ensure that no PII (demographic status, legal name, domestic background) crosses into production logs or is visible to Funders.
*   **Binding Constraint - Absolute PII Anonymization (CON-1BC6B8851E):** Beneficiary demographic status, legal name, and domestic background must not cross into production logs or database tables. All beneficiary data must be classified as highly sensitive and routed via high-entropy UUIDv4 keys (CON-2DE50DC545) to ensure that even internal operators cannot link financial transactions to specific individuals without explicit, audited authorization.
*   **Binding Constraint - Multi-Tenant Data Segregation (CON-2BCB3D9CF7):** To prevent cross-tenant visibility across SF, NYC, and Chicago, the platform must enforce absolute data segregation in Aurora Postgres and DynamoDB. This ensures that financial transaction data (owned by the Platform) is completely isolated from NGO-managed vetting data (owned by NGOs) and Donor payment method data (owned by Donors).

## 3. Binding Technical Constraints: Transaction & Liquidity Engine and Client Application Layer

This section establishes the binding technical constraints for the **Transaction & Liquidity Engine** (CAP-65F7377EBE) and the **Client Application Layer** (SUR-E3E75E96CF). These constraints ensure the platform can scale to 50,000 MAU across SF, NYC, and Chicago while maintaining absolute anonymity and preventing double-spending.

### 3.1 Real-Time Synchronization and Double-Spending Prevention
The core financial integrity of MealCredit relies on the real-time synchronization between virtual credit issuance and physical POS terminal clearing. To prevent double-spending, the system must enforce strict atomicity between the Aurora Postgres ledger and the Stripe Issuing token lifecycle.

*   **Constraint 1: Atomic Ledger-POS Synchronization (CON-8F05AD69D4)**
    *   **Requirement:** The platform must guarantee that a virtual credit token is consumed and the corresponding ledger entry is updated atomically upon successful POS clearing. No token may be presented for payment if the underlying credit pool balance is insufficient or if the token has already been consumed.
    *   **Mechanism:** The Transaction & Liquidity Engine will utilize a distributed locking mechanism within Aurora Postgres to lock the specific credit pool segment during the authorization phase. The service handling POS callbacks must receive a synchronous confirmation of ledger debit before returning a success state to the POS terminal.
    *   **Failure Mode:** If the ledger update fails after token authorization, the system must immediately invalidate the token via the Stripe Issuing API and trigger an alert for manual reconciliation.

*   **Constraint 2: Dynamic Liquidity Management (CON-CA1E9CC141)**
    *   **Requirement:** The system must dynamically balance credit pool availability against redemption velocity and expiration policies. If the Credit Pool Utilization Rate exceeds the defined threshold (CON-55D7F9A516), the platform must automatically throttle NGO onboarding and restrict new credit allocations to prevent liquidity exhaustion.
    *   **Mechanism:** A real-time monitoring service will track the ratio of allocated credits to total pool capacity. Thresholds will trigger automated policy enforcement actions, such as pausing new Funder allocations or increasing the minimum donation round-up amount.

### 3.2 Latency Requirements for Critical APIs
To support 10,000 concurrent connections across three metropolitan footprints, the platform must adhere to strict latency targets for all critical API endpoints. These targets are derived from the need for frictionless redemption and real-time donor transparency.

*   **Constraint 3: p99 Latency for Critical APIs (CON-FD2AD44598)**
    *   **Requirement:** The p99 latency for Voucher Creation and Scanning Callback APIs must be strictly less than 250ms under a load of 10,000 concurrent connections.
    *   **Rationale:** This ensures that the redemption process at the POS terminal is indistinguishable from a standard credit card transaction, preserving the dignity and anonymity of the Recipient.
    *   **Implementation Note:** The hybrid architecture (GraphQL for CRUD, gRPC for financial transactions) must be optimized to minimize network hops. The service for POS callbacks must be deployed in close proximity to the POS gateway integrations to reduce network latency.

*   **Constraint 4: Stripe Webhook Processing Latency (CON-521D9D9565)**
    *   **Requirement:** The average latency from card tap to merchant ledger entry via Stripe Webhooks must be less than 150ms.
    *   **Rationale:** Rapid ledger updates are critical for maintaining accurate real-time credit pool balances and preventing double-spending.
    *   **Implementation Note:** The event-driven serverless architecture must be designed to process Stripe Webhooks asynchronously but with high priority, ensuring that ledger entries are committed to Aurora Postgres within the 150ms window.

This section consolidates the strategic decision foundations, binding constraints, and open questions for the MealCredit platform. It serves as the final executive decision registry for the Inception phase, ensuring alignment on unit economics, regulatory compliance, NGO trust models, and technical constraints before proceeding to Design and Development.

*   **Financial Entity Structure:** The legal entity structure must be ratified to ensure compliance with Stripe's underwriting requirements for Issuing and Connect across all three jurisdictions. **Owner:** Legal/Compliance.
*   **Data Retention Policy:** The specific retention period for transient transactional state versus immutable financial ledger entries must be formally defined to balance privacy rights with financial compliance. **Owner:** Legal/Compliance.
*   **Jurisdiction-Specific Licensing:** The specific money transmitter license requirements for operating as a fintech intermediary in NYC and Chicago must be mapped against California regulations to determine the necessary compliance footprint. **Owner:** Legal/Compliance.
*   **NGO Erasure Protocols:** The exact technical workflow for NGOs to trigger right-to-erasure requests must be defined, ensuring that financial audit trails are preserved while beneficiary PII is purged. **Owner:** Product/Legal.

### 3.3 Open Questions and Knowledge Gaps

The following questions require resolution before the Design phase can proceed. They represent critical dependencies that could impact scope, budget, or timeline.

*   **POS Partner Mandates:** What are the specific contractual mandates from POS partners (Toast/Clover/Square) regarding webhook payload integrity and fallback protocols? (CON-A763D481AA). **Owner:** Partnership Lead. **Impact:** Determines the complexity of the **Provider & Fulfillment Management** capability (CAP-D96776E7F7).
*   **Minimum Viable Transaction Volume:** What is the minimum viable transaction volume to sustain merchant participation before achieving network effects? **Owner:** Business Strategy. **Impact:** Influences the Go-to-Market strategy and initial metro footprint selection.
*   **Legal Structure for Intermediary Role:** How do we legally structure the intermediary role between donors, NGOs, and restaurants to minimize liability? **Owner:** Legal Counsel. **Impact:** Affects the compliance framework and data ownership boundaries.
*   **NGO Adoption KPIs:** What are the specific KPIs for NGO adoption success in the first 6 months? **Owner:** Operations Lead. **Impact:** Defines the success criteria for the **Facilitator Onboarding and Credentialing** journey (JNY-2A8F78F1A6).
*   **Merchant Discount Rate:** What is the negotiated merchant discount rate with POS partners? **Owner:** Finance/Partnerships. **Impact:** Critical for finalizing the unit economics and Credit Pool Utilization Rate thresholds.

### 3.4 Assumptions

The following assumptions are made to enable progress and must be validated or revised in the Design phase:

*   **ASSUMPTION:** The platform will use Stripe Issuing and Connect for all financial transactions, as implied by CON-D5D5F5B8C2 and CON-5D30D227A5. Alternative payment processors are not considered at this inception stage.
*   **ASSUMPTION:** The tripartite model is fixed as Funder -> Platform -> Provider, with NGOs acting as Facilitators. Alternative models (e.g., direct Funder-to-Provider) are rejected due to the need for stigma-free anonymity and centralized liquidity management.
*   **ASSUMPTION:** Multi-tenant data segregation is required across SF, NYC, and Chicago, as implied by CON-2BCB3D9CF7. Single-tenant or shared-schema models are rejected due to compliance and privacy risks.
*   **ASSUMPTION:** The 'round-up' micro-donation model via Plaid/Stripe is the primary funding mechanism. Direct donor contributions are secondary and will be supported in a later phase.

### 3.5 Cross-Reference to Sibling Artifacts

*   **Product Vision and Scope Boundaries:** The strategic scope and user journeys defined in this artifact align with the Product Vision and Scope Boundaries artifact. Any changes to the core tripartite model must be ratified there first.
*   **Compliance, Privacy, and Governance Framework:** The regulatory constraints (PCI-DSS, SOC2, CCPA/GDPR) detailed here are expanded upon in the Compliance, Privacy, and Governance Framework artifact. This artifact provides the high-level binding constraints; the sibling artifact provides the detailed policy matrix.
*   **Risk Register and Technical Constraints:** The technical constraints (latency, uptime, CHR) and associated risks (double-spending, data leakage) are cataloged in the Risk Register and Technical Constraints artifact. This artifact focuses on the decision foundations that drive those risks.
*   **Operating Model and Stakeholder Alignment:** The roles (Funder, Recipient, Provider, Facilitator, Operator) and their interactions are defined here. The Operating Model and Stakeholder Alignment artifact provides the detailed workflow and governance structure for these roles.

## 5. Tripartite Marketplace Financial Mechanics

The decoupling of food assistance from social stigma is achieved through the financial mechanics of the tripartite model, governed by strict data ownership boundaries and liquidity management rules.

### 5.1 Actor Roles and Financial Flows

*   **Funder (Donor):** Provides liquidity via micro-donation round-ups. The Funder's experience is defined by the **Funder Engagement and Credit Allocation** journey, where they receive immutable transactional receipts upon redemption. This flow ensures strict zero-knowledge anonymity (CON-705CB41089) by strictly prohibiting the transmission of any identifying beneficiary parameters to the Funder.
*   **Platform (Daya/MealCredit):** Acts as the financial intermediary, managing the Credit Pool, enforcing PCI-DSS Level 1 compliance (CON-5D30D227A5), and ensuring multi-tenant data segregation across SF, NYC, and Chicago (CON-2BCB3D9CF7). The Platform owns the financial transaction data, while NGOs own the vetting data (CON-3D3BCC51A5).
*   **Provider (Restaurant):** Receives automated net payouts via Stripe Connect. Providers must be able to toggle real-time throttle parameters to prevent structural overload. This ensures the **Provider & Fulfillment Management** capability (CAP-D96776E7F7) is robust and scalable.

### 5.2 Decision Owners and Ratification

The following strategic decisions require ratification by specific decision owners to proceed to the Design phase:

*   **Decision Owner: Unit Economics and Fee Absorption.** The CFO or Head of Product must ratify the fee absorption strategy and the Credit Pool Utilization Rate alert thresholds. This decision dictates the financial sustainability of the platform and the liquidity management policies.
*   **Decision Owner: Legal Structure.** The Legal Counsel must ratify the intermediary legal structure to ensure compliance with financial licensing requirements (CON-D5D5F5B8C2) across all three jurisdictions.
*   **Decision Owner: NGO KPIs.** The Head of Partnerships must ratify the NGO adoption KPIs to measure the success of the Facilitator Onboarding and Credentialing journey (JNY-2A8F78F1A6).

### 5.3 Right-to-Erasure Workflows for NGO-Managed Profiles

Adherence to data privacy regulations (CCPA/GDPR equivalents) requires robust right-to-erasure workflows, particularly for vulnerable Recipient populations managed by NGOs:

*   **Binding Constraint - Right-to-Erasure (CON-B68D690D72):** The platform must adhere to data privacy regulations by ensuring right-to-erasure workflows for NGO-managed profiles. This requires implementing a mechanism where NGOs can request the deletion of Recipient profiles, triggering the immediate purging of transient transactional state and the anonymization of historical data, while retaining only the immutable financial ledger entries required for compliance.
*   **Binding Constraint - Data Ownership Boundaries (CON-3D3BCC51A5):** Data ownership boundaries must be strictly enforced: NGOs own vetting data, the Platform owns financial transaction data, and Donors own payment method data. This separation is critical for defining the scope of erasure requests and ensuring that financial compliance obligations are not compromised by privacy-driven data deletion.

The MealCredit platform operates on a strict separation of data ownership to maintain trust, ensure regulatory compliance, and protect beneficiary anonymity. The following boundaries are established as binding project truth:

*   **NGO Data Ownership (Vetting & Eligibility):** Local non-profit organizations (NGOs) retain absolute ownership of all beneficiary vetting data. This includes demographic status, legal name, and domestic background. This data must never cross into production logs or platform databases. The NGO is responsible for the initial credentialing and ongoing eligibility verification of beneficiaries.
*   **Platform Data Ownership (Financial Transactions):** The MealCredit platform owns all financial transaction data, including micro-donation round-ups, credit pool allocations, and redemption clearing records. This data is managed via the **Transaction & Liquidity Engine** (CAP-65F7377EBE) and must comply with PCI-DSS Level 1 and SOC2 Type II standards.
*   **Donor Data Ownership (Payment Methods):** Donors (Funders) retain ownership of their payment method data. The platform acts as a processor via Stripe Issuing and Connect, ensuring raw credit card data is never stored on platform servers (CON-5D30D227A5).

**Decision Owner:** Chief Compliance Officer (CCO) / Legal Counsel
**Rationale:** This separation is critical to prevent cross-tenant data visibility (CON-2BCB3D9CF7) and to ensure that beneficiary PII is never exposed to financial stakeholders or platform operators, thereby eliminating social bias and tracking (CON-705CB41089).

The **Facilitator Onboarding and Credentialing** journey (JNY-2A8F78F1A6) requires a trust model that verifies NGO legitimacy without compromising the anonymity of the beneficiaries they serve.

*   **Credentialing Process:** NGOs must submit digital identity and proof of organizational legitimacy via the admin portal. The Operator (ACT-FE96DD3975) reviews documentation against compliance criteria and performs background checks.
*   **Cryptographic Profile Creation:** Upon approval, the Operator generates unique access keys and activates the Facilitator role. The NGO Administrator then creates cryptographic profiles for beneficiaries. No state IDs or PII are stored on-platform; instead, high-entropy UUIDv4 keys are used to route analytics and manage eligibility (CON-2DE50DC545).

**Decision Owner:** Platform Operator / NGO Trust & Safety Lead
**Rationale:** This process ensures that only vetted NGOs can access the platform, maintaining the integrity of the credit pool and preventing fraud, while the cryptographic profile system enforces absolute PII anonymization (CON-1BC6B8851E).

The **NGO Administrator Beneficiary Vetting and Allocation** journey (JNY-7C3BA57F20) defines how NGOs manage their beneficiary populations within the platform's constraints.

*   **Vetting Workflow:** NGO Administrators create anonymous profiles for Recipients (ACT-DC00FA84DC) and assign eligibility tiers. This workflow must adhere to data privacy regulations (CCPA/GDPR equivalents) by ensuring right-to-erasure workflows for NGO-managed profiles without exposing PII (CON-B68D690D72).
*   **Allocation Mechanics:** Credits are allocated on a periodic cycle (weekly/monthly) to vetted beneficiaries. The NGO monitors the Credit Pool Utilization Rate to trigger alerts if capacity exceeds the established threshold (CON-55D7F9A516).

**Decision Owner:** NGO Administrator / Platform Product Owner
**Rationale:** This ensures that credit distribution is equitable and transparent to the NGO, while the platform maintains control over the financial liquidity and prevents double-spending through real-time synchronization (CON-8F05AD69D4).

### 5.4 Multi-Modal Access and Redemption

To accommodate diverse device capabilities and ensure accessibility, the Client Application Layer must support multiple redemption modalities. This includes digital wallet passes, 1D barcodes, and 2D barcodes.

*   **Constraint 5: Multi-Modal Redemption Support (CON-EF1F2F2EBE)**
    *   **Requirement:** The platform must provide multi-modal access for redemption, including Apple/Google Wallet passes, 1D barcodes, and 2D barcodes. This ensures that Recipients with varying device capabilities can access and present their MealCredits.
    *   **Rationale:** This aligns with the mission to decouple food assistance from social stigma by providing a seamless, familiar user experience.
    *   **Implementation Note:** The Client Application Layer (Expo v51 / React Native) must generate and manage these different token formats. The backend must validate all token types uniformly against the ledger.

*   **Constraint 6: Offline Token Storage and Validation (CON-460D6EBABD)**
    *   **Requirement:** The platform must secure offline token storage using device hardware-backed SecureStore with localized valid cryptographic signatures. This ensures that tokens remain valid and secure even in low-connectivity environments.
    *   **Rationale:** This supports the goal of graceful degradation of network dependencies (CON-0018D09145) and ensures service continuity.
    *   **Implementation Note:** The cryptographic signatures must be verifiable by the POS terminal or the platform's validation service without requiring real-time connectivity to the central ledger, using a time-bound, single-use token structure.

### 5.5 NGO Trust Models and Data Ownership

The tripartite model relies on NGOs (Facilitators) to vet and allocate credits to beneficiaries. Trust and clear data ownership are paramount:

*   **Data Ownership Boundaries:** Clear boundaries must be enforced: NGOs own vetting data, the Platform owns financial transaction data, and Donors own payment method data (CON-3D3BCC51A5). This separation is critical for liability management and regulatory compliance.
*   **NGO Onboarding and Credentialing:** The **Facilitator Onboarding and Credentialing** journey (JNY-2A8F78F1A6) must be designed to verify organizational legitimacy without requiring the storage of sensitive state IDs. Cryptographic profile creation is the preferred method to maintain trust and privacy.
*   **Multi-Tenant Data Segregation:** To prevent cross-tenant visibility across SF, NYC, and Chicago, the platform must enforce strict multi-tenant data segregation in Aurora Postgres and DynamoDB (CON-2BCB3D9CF7). This is a technical constraint that directly impacts the database schema design.

## 6. Follow-Up Questions

*   **Question:** What are the specific contractual mandates from POS partners (Toast/Clover/Square) regarding webhook payload integrity and fallback protocols?
    *   **Why Critical:** Determines the complexity of the Provider & Fulfillment Management capability.
    *   **Answerable:** False
    *   **Blocking:** True
*   **Question:** What is the minimum viable transaction volume to sustain merchant participation before achieving network effects?
    *   **Why Critical:** Influences the Go-to-Market strategy and initial metro footprint selection.
    *   **Answerable:** False
    *   **Blocking:** False
*   **Question:** How do we legally structure the intermediary role between donors, NGOs, and restaurants to minimize liability?
    *   **Why Critical:** Affects the compliance framework and data ownership boundaries.
    *   **Answerable:** False
    *   **Blocking:** True
*   **Question:** What are the specific KPIs for NGO adoption success in the first 6 months?
    *   **Why Critical:** Defines the success criteria for the Facilitator Onboarding and Credentialing journey.
    *   **Answerable:** False
    *   **Blocking:** False
*   **Question:** What is the negotiated merchant discount rate with POS partners?
    *   **Why Critical:** Critical for finalizing the unit economics and Credit Pool Utilization Rate thresholds.
    *   **Answerable:** False
    *   **Blocking:** False
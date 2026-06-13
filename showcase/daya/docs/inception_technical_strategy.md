# Technical Strategy and Constraints

### 1.2 Binding Technical Constraints
The following constraints are binding for all subsequent design and development phases. They are derived directly from the project's compliance obligations and business rules.

Constraint 1: Absolute PII Isolation. No PII (legal name, SSN, domestic address) may be stored on-platform or in production logs. Beneficiary data must be absolutely anonymized. Cryptographic profile creation for NGO vetting must occur without storing state ID or SSN on-platform.
Constraint 2: Single-Use Token Lifecycle. Virtual card tokens must be single-use, locked to specific Merchant Category Codes (MCC) and location IDs. Tokens must be provisioned via Stripe Issuing API and restricted at the network layer before merchant receipt prints.
Constraint 3: Immutable Receipting. Donors must receive immutable transactional receipts within 120 seconds of redemption. These receipts must strictly prohibit the transmission of any identifying beneficiary parameters.
Constraint 4: Ledger Integrity. The financial ledger (Aurora) must guarantee accuracy and immutability through cryptographic logging and ACID compliance. All transactions must be traceable for audit purposes without linking to beneficiary PII.
Constraint 5: Multi-Tenant Data Isolation. The platform must enforce strict multi-tenant data isolation to ensure that regional credit pools and NGO data are segregated and secure.

### 1.3 Strategic Architecture Decisions

Virtual Card Provisioning Strategy: The system will utilize Stripe Issuing API for backend issuance of temporary Visa/Mastercard tokens. This leverages existing banking networks for clearing while allowing precise control over fund usage via MCC and location restrictions. This approach minimizes the need for custom payment infrastructure and aligns with PCI-DSS Level 1 requirements by offloading sensitive card data handling to a certified provider.
Anonymization by Design: The architecture must implement "privacy by design" at the data layer. Beneficiary data, if required for operational purposes (e.g., NGO vetting), must be processed in a secure, ephemeral environment and immediately discarded or pseudonymized. The redemption flow must be decoupled from any identity verification step that could link a transaction to a specific individual.
Directed Impact Flows: The system must support donor capabilities to assign funds globally, regionally by zip code, or to specific merchant properties. This requires a flexible credit pool management system that can track fund allocation without compromising beneficiary anonymity.

### 1.4 Compliance and Security Posture

PCI-DSS Level 1: As the platform handles financial transactions and virtual card data, it must meet the highest level of PCI-DSS compliance. This includes strict network security, access control, and regular vulnerability assessments. The use of Stripe Issuing API helps mitigate scope by reducing the volume of card data handled directly by Daya.
SOC2 Type II: The platform must demonstrate operational effectiveness of its security, availability, processing integrity, confidentiality, and privacy controls. This requires comprehensive logging, monitoring, and incident response procedures that do not compromise beneficiary anonymity.
Data Minimization: All data collection and retention must be strictly limited to what is necessary for the core functionality. Unused emergency credits must automatically roll back to the central regional pool after 72 hours to prevent ledger stagnation and reduce data retention risks.

### 1.6 Risk Management

Risk: PII Leakage via Logs. Mitigation: Implement strict log scrubbing and anonymization at the application and infrastructure levels. All logs must be audited for PII patterns.
Risk: Token Fraud. Mitigation: Utilize Stripe's built-in fraud detection and single-use token constraints. Implement real-time monitoring for unusual transaction patterns.
Risk: Ledger Discrepancies. Mitigation: Implement cryptographic logging and regular automated reconciliation between the Aurora ledger and Stripe transaction records.

### 2.1. Core Architectural Strategy: The Immutable Ledger

The financial integrity of the Daya platform rests on a centralized, cryptographically secured ledger (referred to internally as the Aurora ledger). This ledger serves as the single source of truth for all financial movements, including donor round-ups, credit pool allocations, and merchant settlements.

ACID Compliance: The ledger must enforce strict ACID (Atomicity, Consistency, Isolation, Durability) properties for all transaction processing. This ensures that a transaction is either fully committed or fully rolled back, preventing partial states that could lead to financial discrepancies.
Cryptographic Immutability: Every transaction record must be cryptographically hashed and linked to the previous record, creating an immutable chain. This provides a tamper-evident history that is critical for SOC2 Type II compliance and donor trust.
Double-Spending Prevention: The ledger must implement optimistic concurrency control or similar mechanisms to prevent the same virtual card token or credit balance from being redeemed multiple times, especially in high-concurrency POS environments.

### 2.7. Stakeholder Alignment and Business Value

Business Value: This technical strategy ensures the integrity of the Daya platform's core value proposition: converting donor capital into meal credits for beneficiaries. By guaranteeing accuracy and auditability, the platform builds trust with donors, beneficiaries, and regulatory bodies.
Stakeholder Alignment: This strategy aligns with the needs of all key stakeholders: Donors (trust in impact), Beneficiaries (frictionless redemption), Restaurant Partners (reliable payouts), and NGO Partners (responsible distribution).

---

#### 4.1.1. Financial Data Standards (PCI-DSS Level 1)

As the system processes micro-donations and round-up transactions via credit cards, it falls under the highest tier of payment card industry standards.

Scope of Compliance: PCI-DSS Level 1 applies to all systems that store, process, or transmit cardholder data. This includes the donor funding flow (Plaid/Stripe integration) and the virtual card provisioning layer (Stripe Issuing API).
Technical Constraint: The platform must never store raw Primary Account Numbers (PANs) or full magnetic stripe data. All card data handling must be offloaded to certified Payment Card Industry (PCI) service providers (e.g., Stripe) using tokenization. The Daya platform's internal ledger must only reference transaction IDs and tokenized references, never the underlying card details.
Network Layer Enforcement: Ineligible purchases (e.g., alcohol, non-food merchandise) must be dropped at the Stripe network layer before merchant receipt prints, ensuring the platform does not process prohibited financial transactions.

#### 4.1.2. Service Organization Controls (SOC2 Type II)

The platform's integrity, availability, and confidentiality must be auditable over time, not just at a point in time.

Audit Trail Immutability: The financial ledger must guarantee the accuracy and immutability of financial transactions through cryptographic logging. Every transaction event (donation, round-up, redemption, payout) must be recorded in an append-only, tamper-evident log.
Access Control: Access to sensitive donor and beneficiary data must be strictly role-based. System Administrators and NGO Partners must operate within tiered access models that prevent unauthorized data exfiltration.
Operational Resilience: The system must maintain high availability for donor-facing and redemption-facing interfaces. Offline operational resilience strategies must be defined to ensure critical redemption capabilities are not completely lost during partial network outages, though full transactional integrity requires online validation.

#### 4.1.3. Data Privacy and Anonymization

The core value proposition relies on the absolute anonymity of beneficiaries to preserve dignity and privacy.

PII Isolation: Beneficiary data must be absolutely anonymized. No PII (legal name, domestic background, SSN) may be stored on-platform or in production logs. Cryptographic profile creation for NGO vetting must occur without storing state IDs or SSNs on the Daya platform.
Transaction Receipt Constraints: Donors must receive immutable transactional receipts within 120 seconds of redemption. These receipts must strictly prohibit the transmission of any identifying beneficiary parameters. The receipt confirms the impact of the contribution without revealing the identity of the recipient.
Data Minimization: The system should only collect and retain data strictly necessary for the transaction clearing, regulatory reporting, and fraud prevention. Unused emergency credits must automatically roll back to the central regional pool after 72 hours of expiration to prevent ledger stagnation and unnecessary data retention.

### 4.2. Regulatory Obligations

Beyond technical standards, the platform must adhere to specific regulatory obligations inherent to its domain.

Anti-Money Laundering (AML) and Know Your Customer (KYC): While beneficiaries are anonymous, NGO Partners and Restaurant Partners must undergo vetting. The platform must support the cryptographic onboarding and verification processes required by financial regulators to prevent the platform from being used for money laundering or fraud.
Financial Reporting: The system must support the generation of reconciliation reports for merchant payouts and donor tax receipts. Automated daily net payouts must settle cleared credits to restaurant business checking accounts, requiring strict adherence to banking settlement windows.
Jurisdictional Data Residency: As a multi-tenant cloud platform, the platform must ensure that data residency requirements are met for all operating regions. [KNOWLEDGE_GAP: Specific data residency jurisdictions and corresponding legal requirements for the initial launch regions must be established by Legal to configure cloud region routing and data isolation policies.]

### 4.4. Unresolved Dependencies and Knowledge Gaps

The following items require resolution by Legal, Compliance, or Product stakeholders before the Design phase can finalize the technical architecture. These are not to be invented locally but must be resolved by the appropriate stakeholders or research lanes.

Data Residency Jurisdictions: [KNOWLEDGE_GAP: Specific data residency jurisdictions and corresponding legal requirements for the initial launch regions must be established by Legal to configure cloud region routing and data isolation policies.]
NGO Vetting Standards: [KNOWLEDGE_GAP: The specific cryptographic or documentary standards required for NGO vetting (e.g., specific government ID formats, tax-exempt status verification) must be defined by the Compliance team to ensure the onboarding flow meets regulatory requirements.]
Merchant Payout Banking Partners: [ASSUMPTION: The platform will utilize a single primary banking partner for automated daily net payouts to restaurant business checking accounts. This assumption must be validated by Finance to ensure the chosen partner supports the required settlement window and API integration capabilities.]

### 5.3. Anonymity and Privacy Boundaries

The technical strategy for privacy is defined by the principle of "Data Minimization at the Edge."

Client-Side Token Generation: Virtual card tokens must be generated and provisioned to the device's secure wallet (Apple/Google Wallet) without exposing the beneficiary's identity to the merchant or the payment network. The token itself must be visually identical to a standard consumer gift card to preserve the dignity of the beneficiary.
PII Isolation: Beneficiary data, including NGO-vetted profiles, must be stored in a separate, highly restricted data store with strict access controls. Production logs, error messages, and monitoring dashboards must be scrubbed of any PII fields. Any error handling that requires logging must use anonymized transaction IDs rather than beneficiary identifiers.
Donor Receipt Constraints: Donors must receive immutable transactional receipts within 120 seconds of redemption. These receipts must strictly prohibit the transmission of any identifying beneficiary parameters. The receipt generation service must be decoupled from the beneficiary identity service to prevent accidental data leakage.

### 5.6. Knowledge Gaps and Assumptions

The following items represent unresolved technical decisions or external dependencies that must be addressed before detailed design can proceed.

KNOWLEDGE_GAP: POS Integration Protocol Specifics - The exact API contracts, data formats, and authentication mechanisms for the "zero-footprint" POS integration with various merchant POS systems are not yet defined. This will dictate the complexity of the Merchant Fulfillment Flow and the robustness of the store-and-forward mechanism.
KNOWLEDGE_GAP: Regional Data Residency Requirements - While the system is multi-tenant, the specific legal requirements for data residency (e.g., GDPR, CCPA, or local jurisdictional laws) for beneficiary and donor data in different operational regions are not yet established. This will impact the cloud infrastructure design and data replication strategy.
EXTERNAL DEPENDENCY: Stripe Issuing API Capabilities - The platform's ability to meet "dignified redemption" and "ineligible purchase filtering" requirements depends on specific capabilities of the Stripe Issuing API (e.g., visual identity customization, MCC restrictions, location locking). Vendor verification is required to confirm these capabilities against project needs.
EXTERNAL DEPENDENCY: NGO Vetting Data Standards - The platform's ability to onboard beneficiaries depends on NGO partners providing data in a standardized, machine-readable format. Partner alignment is required to define the specific data schema and validation rules for this ingestion.
KNOWLEDGE_GAP: Operational Availability SLA - The specific availability target (e.g., 99.9% or 99.95%) for core redemption and transaction clearing services is an unresolved operational decision to be defined by the Operations and Finance teams.
KNOWLEDGE_GAP: Maintenance Window Duration - The specific duration of the maintenance window for credit expiration and rollback processes is an unresolved operational decision to be defined by the Operations team based on system load and transaction volume projections.

### 5.7. Strategic Implications for Downstream Phases

This technical strategy imposes several critical constraints on the Design and Development phases:

1. Database Schema Design: The dual-ledger architecture requires a database schema that strictly separates financial transaction data from beneficiary identity data, with clear foreign key relationships managed through anonymized token IDs.
2. API Contract Design: The API contracts for the Redemption Engine and the Financial Ledger must be designed to enforce anonymity at the API gateway level, ensuring that PII is never passed between services.
3. Security Architecture: The security architecture must prioritize the protection of the PII isolation boundary, implementing strict access controls, encryption at rest and in transit, and comprehensive audit logging for all access to beneficiary data.
4. Testing Strategy: The testing strategy must include rigorous privacy and security testing, including penetration testing, data leakage detection, and compliance validation against PCI-DSS and SOC2 standards.

This technical doctrine provides the necessary boundaries and strategic direction for the Daya platform, ensuring that the system is built to deliver on its social impact mission while maintaining the highest standards of financial integrity, privacy, and compliance.

---

### 3.3. Operational Thresholds and Reliability

Given the financial and social impact nature of the platform, high availability and data integrity are non-negotiable. The system must adhere to strict operational thresholds to ensure trust and reliability.

Availability SLA: The core redemption and transaction clearing services must maintain high availability during operational hours. This includes the Beneficiary App, the POS Integration layer, and the Stripe Issuing API integration. [KNOWLEDGE_GAP: Specific availability target (e.g., 99.9% or 99.95%) is an unresolved operational decision to be defined by the Operations and Finance teams to align with business impact requirements.]
Data Integrity and Ledger Consistency: The Financial Ledger Integrity and Audit capability requires ACID compliance for all financial transactions. Any discrepancy in the ledger must trigger an immediate alert to the System Administrator. The system must support zero data loss for transaction records.
Payout Settlement Latency: Automated daily net payouts to restaurant business checking accounts must be initiated following the end of the business day. [KNOWLEDGE_GAP: Specific settlement window (e.g., T+1, T+2) is an unresolved operational decision to be defined by the Finance and Operations team to ensure alignment with banking partner capabilities.]
Credit Expiration and Rollback: Unused emergency credits must automatically roll back to the central regional pool after 72 hours of expiration. This process must be completed within a defined maintenance window to avoid impacting peak transaction times. [KNOWLEDGE_GAP: Specific duration of the maintenance window is an unresolved operational decision to be defined by the Operations team based on system load and transaction volume projections.]
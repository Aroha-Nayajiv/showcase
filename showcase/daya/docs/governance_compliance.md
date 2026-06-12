# Governance, Compliance, and Privacy Obligations

## 1. Privacy & Anonymization Framework

The core operational constraint of the Daya platform is AbsoluteAnonymization. To comply with GDPR (Article 5(1)(c) Data Minimization) and CCPA/CPRA (definition of Personal Information), the platform must ensure that no PII (legal names, domestic backgrounds, SSNs) crosses into production logs or is stored on-platform.

### 1.1 Pseudo-Anonymized Redemption Protocol
The system converts micro-donations into single-use virtual card tokens locked to specific Merchant Category Codes (MCC) and location. This tokenization must occur client-side or at the Stripe network layer, ensuring that the beneficiary's identity is stripped before any transaction data reaches the donor or the merchant.

### 1.2 Data Flow Boundaries
Donor Receipts: Donors must receive immutable transactional receipts within 120 seconds of redemption. These receipts must strictly prohibit the transmission of any identifying beneficiary parameters. The receipt data model must be validated against PII patterns to prevent accidental leakage.
Merchant Fulfillment: Kitchens and merchants receive only the necessary order data (e.g., itemized food list, total value) without beneficiary PII. The POS integration must be zero-footprint or edge-dashboard based to minimize data exposure.
NGO Allocation Governance: NGO Administrators retain autonomy over vetting vulnerable populations. However, the platform must enforce a "Cryptographic Profile" creation process that does not store state IDs or SSNs on-platform. NGO vetting data must be segregated from the financial ledger.

### 1.3 PCI-DSS Level 1 Compliance
Payment Flows: All donor funding flows (Micro-DonationRound-Ups) via Plaid/Stripe must be processed in a PCI-DSS Level 1 compliant environment. No raw card data may touch Daya's servers.

Virtual Card Provisioning: Backend issuance of temporary Visa/Mastercard tokens via Stripe Issuing API must be restricted by MCC and location ID. Ineligible purchases (alcohol, non-food merchandise) must be dropped at the Stripe network layer before the merchant receipt prints, ensuring compliance with grant/funding restrictions.

### 1.4 AML & Fraud Prevention
Credit Pool Integrity: The "DirectedImpactFlows" capability allows donors to assign funds globally or regionally. AML controls must be applied to the central regional pool to prevent fraud or illicit fund routing. Transaction monitoring must flag unusual patterns (e.g., rapid round-tripping of funds).

Immutable Audit Trail: The 120-second immutable receipt requirement serves as the primary compliance audit trail. These records must be tamper-evident and retained for the duration required by financial regulators.

## 2. Data Retention & Lifecycle

To prevent data hoarding and ensure compliance with the "Right to be Forgotten" (GDPR Art. 17) and CCPA deletion rights, strict lifecycle rules are codified.

72-Hour Expiration Rule: Unused emergency credits must automatically roll back to the central regional pool after 72 hours of expiration. This prevents ledger stagnation and ensures that unclaimed financial data does not persist indefinitely. Beneficiary Data Purge: Since beneficiary data is absolutely anonymized, any residual metadata associated with a redeemed token must be purged from production logs immediately after the 120-second receipt generation window, unless required for financial audit retention. Financial Record Retention: The specific retention period for financial records is not yet established in project truth. <br> `KNOWLEDGE_GAP: Financial Record Retention Period - Legal/Compliance must establish the binding retention period for financial records based on IRS and financial regulatory requirements.`

## 3. Cross-Jurisdictional Regulatory Mapping

The following table maps specific regulatory requirements for the target deployment cities, focusing on food assistance and financial micro-donations.

San Francisco (SF) | Data Privacy (CCPA/CPRA) | Strict opt-out mechanisms for data collection; clear disclosure of data sharing with NGOs. | Privacy Policy; Client-side tokenization to minimize PII collection. San Francisco (SF) | Food Assistance | Compliance with local health codes for participating merchants. | Merchant vetting process; MCC restrictions on ineligible purchases. New York City (NYC) | Financial Services | NYC DFS regulations for money transmission; AML/KYC for high-value transactions. | PCI-DSS Level 1; Stripe Issuing compliance; AML transaction monitoring. New York City (NYC) | Data Privacy (NYDFS 23 NYCRR 500) | Cybersecurity incident reporting; data encryption standards. | Encryption at rest and in transit; Incident response plan. Chicago | Food Assistance | Compliance with Illinois food donation liability protection (Good Samaritan Act). | Merchant agreements; Platform terms of service limiting liability. Chicago | Data Privacy (BIPA - if biometric) | If POS integration uses biometric verification, strict consent and retention policies apply. | Avoid biometric data collection; Use standard card/token verification.

## 4. Decision Gaps & Ownership Clarity

The following items represent unresolved governance decisions that must be ratified before the Design phase to finalize the system blueprint.

NGO Data Storage Boundary: The specific technical mechanism for segregating NGO vetting data from the financial ledger is not yet defined. <br> `KNOWLEDGE_GAP: NGO Data Storage Boundary - Design Phase must define the segregation mechanism.`
POS Integration Standard: The exact protocol for zero-footprint POS integration is not yet ratified. <br> `KNOWLEDGE_GAP: POS Integration Standard - Design Phase must ratify the integration protocol.`
Financial Retention Period: The retention period for financial records is not yet established.
# Whole Product Vision and Scope: Daya (MealCredit)

## 1. Tripartite Actor Model and Interaction Boundaries

This section defines the authoritative actor model for Daya (MealCredit), establishing the operational boundaries for the initial 50,000 MAU across the San Francisco, New York City, and Chicago metropolitan footprints. The platform operates as a pseudo-anonymized financial ledger where local non-profit organizations (NGOs) serve as the critical trust anchors and mediators between Donors, Beneficiaries, and Merchant Partners (Restaurants).

### 1.1 The Donor (Funding Source)
**Role Definition:** The Donor is the capital provider, utilizing the platform to convert micro-donations into tangible social impact. Donors interact with the system primarily through the mobile application, leveraging automated financial integrations.

**Core Interactions & Boundaries:**
*   **Micro-Donation Round-Ups:** Donors authorize the system to calculate and transfer round-up amounts from their credit card spend via Plaid/Stripe integration. This funding mechanism is the primary liquidity source for the regional credit pools.
*   **Directed Impact Flows:** Donors may assign funds globally, regionally by zip code, or to specific merchant property types (e.g., healthy grocery partners). This capability allows for targeted social impact without compromising beneficiary anonymity.
*   **Immutable Receipting:** Upon a Beneficiary's redemption, the Donor receives an immutable transactional receipt within 120 seconds. This receipt strictly prohibits the transmission of any identifying beneficiary parameters, ensuring the donor's impact is quantified without compromising privacy.

**Operational Constraints:**
*   Donor data is isolated from Beneficiary data. No PII or demographic data regarding the recipient is visible to the Donor.
*   Funding flows are processed asynchronously to handle high-throughput micro-transactions.

### 1.2 The Beneficiary (End User)
**Role Definition:** The Beneficiary is the recipient of culinary credits, mediated by local NGOs. The platform's core mission is to decouple food assistance from social stigma through absolute anonymization.

**Core Interactions & Boundaries:**
*   **NGO-Mediated Onboarding:** Beneficiaries are onboarded by local NGO partners. NGOs retain autonomy over vetting and rotating vulnerable populations. Cryptographic profile creation occurs without storing state ID or SSN on-platform, ensuring client-side generation of clean tokenized vouchers.
*   **Anonymous Redemption:** Beneficiaries use the mobile app to map participating dining locations sorted by distance and dietary flags. The system queries the Aurora ledger to verify pool balance and generates a single-use virtual card token.
*   **Frictionless POS Clearing:** The token is pushed to the device's secure wallet (Apple/Google Wallet pass or barcode) for frictionless clearing at the Merchant Partner's POS. The transaction is visually identical to a standard consumer gift card, eliminating any social stigma.

**Absolute Anonymization:**
*   Beneficiary data must be absolutely anonymized with no PII such as legal name or domestic background stored on-platform or in production logs.
*   Credit Expiration: Unused emergency credits automatically roll back to the central regional pool after 72 hours of expiration to prevent ledger stagnation.

### 1.3 The Merchant Partner (Restaurant)
**Role Definition:** The Merchant Partner is the commercial establishment that accepts culinary credits as payment. They are vetted by NGOs and integrated into the platform via zero-footprint POS integrations or edge dashboards.

**Core Interactions & Boundaries:**
*   **Token Validation:** The POS system ingests the order and validates the virtual card token against Stripe Issuing restrictions (Merchant Category Code and location ID). Ineligible purchases (e.g., alcohol, non-food merchandise) are dropped at the Stripe network layer before the merchant receipt prints.
*   **Real-Time Throttling:** Kitchens can toggle real-time throttle parameters, such as a maximum of 15 MealCredit orders per hour, to prevent structural overload during peak times.
*   **Automated Settlement:** The system cross-references transaction logs against the financial ledger and initiates an automated net payout to the restaurant's business checking account within 24 hours. This ensures merchants are not exposed to donor funding volatility.

**Operational Constraints:**
*   Merchants must adhere to PCI-DSS Level 1 standards for handling payment data.
*   Merchant data is isolated from Beneficiary data. No information about the donor or the beneficiary's status is transmitted to the merchant.

### 1.5 Privacy and Anonymity Guarantees
**Role Definition:** This section defines the strict data isolation and anonymization boundaries required to maintain the platform's social impact mission and compliance posture.

**Core Interactions & Boundaries:**
*   **Absolute Anonymization:** Beneficiary data must be absolutely anonymized with no PII such as legal name or domestic background stored on-platform or in production logs.
*   **Donor-Recipient Decoupling:** Donors must receive immutable transactional receipts within 120 seconds of redemption, strictly prohibiting transmission of any identifying beneficiary parameters.
*   **Client-Side Tokenization:** Client-side generation of clean tokenized vouchers visually identical to consumer gift cards, ensuring no beneficiary demographic data crosses into production logs.

**Operational Constraints:**
*   Beneficiary data is isolated from Donor data. No PII or demographic data regarding the recipient is visible to the Donor.
*   Merchant data is isolated from Beneficiary data. No information about the donor or the beneficiary's status is transmitted to the merchant.

## 2. Multi-Tenant Architecture and Footprint Constraints

This section defines the multi-tenant architecture constraints for the initial 50,000 MAU across the San Francisco, New York City, and Chicago metropolitan footprints. The platform must ensure strict data isolation between these regions while maintaining a unified global ledger for financial integrity.

### 2.1 Multi-Tenant Data Isolation
**Role Definition:** The platform operates as a multi-tenant cloud environment where each metropolitan footprint (SF, NYC, Chicago) functions as a distinct logical tenant.

**Core Interactions & Boundaries:**
*   **Regional Credit Pools:** Each footprint maintains its own regional credit pool. Funds assigned regionally by donors are locked to the specific footprint.
*   **Data Segregation:** Beneficiary, Merchant, and NGO data must be strictly segregated by footprint to ensure regional compliance and operational independence.
*   **Global Ledger Integrity:** While data is isolated, the financial ledger must maintain global ACID compliance to ensure accurate cross-footprint reconciliation and reporting.

**Operational Constraints:**
*   Multi-tenant data isolation must be enforced at the database and application layer to prevent cross-tenant data leakage.
*   Regional credit pool utilization rates must be monitored independently, with alerts triggered if utilization exceeds 85%.

### 2.2 Offline Operational Resilience
**Role Definition:** The platform must ensure operational resilience in the event of network disruptions, particularly for POS transactions at Merchant Partners.

**Core Interactions & Boundaries:**
*   **Token-Based Offline Validation:** Virtual card tokens must be structured to allow for basic offline validation at the POS, ensuring transactions can be queued and processed when connectivity is restored.
*   **Graceful Degradation:** The mobile app must degrade gracefully in low-connectivity scenarios, allowing beneficiaries to view their tokens and nearby merchants.

**Operational Constraints:**
*   Offline transaction reconciliation must be automated to prevent ledger discrepancies.
*   Cache Hit Ratio (CHR) for restaurant search queries must remain above 92% to ensure app responsiveness even under poor network conditions.

### 2.3 Compliance and Regulatory Dependencies
**Role Definition:** The platform operates in a highly regulated environment (PCI-DSS Level 1, SOC2 Type II) and must navigate varying local regulations across three metropolitan footprints.

**Core Interactions & Boundaries:**
*   **NGO Data Handling:** Specific compliance requirements for NGO data handling in each jurisdiction (SF, NYC, Chicago) are not yet defined. Legal must establish the exact data retention and privacy obligations for NGO partners.
*   **Financial Licensing:** The platform's role as a financial intermediary requires clarification on necessary money transmitter licenses in each state.

**Operational Constraints:**
*   Compliance requirements must be mapped to specific jurisdictional laws before the design phase can finalize data storage schemas.
*   Financial licensing requirements must be confirmed by legal counsel to ensure the platform can legally operate in all three initial footprints.

### 2.4 Technical Implementation Details
**Role Definition:** Certain technical implementation details are currently open and require resolution to proceed with system design.

**Core Interactions & Boundaries:**
*   **Cache Technology:** The specific caching technology (e.g., Redis, Memcached) for restaurant search queries is not yet ratified. This decision impacts the architecture's scalability and consistency model.
*   **POS Integration Standard:** The specific zero-footprint POS integration standard (e.g., specific API version or middleware) is not yet ratified. This decision impacts the merchant onboarding timeline.

**Operational Constraints:**
*   Technical implementation details must be ratified by the engineering lead before the design phase can finalize API contracts.
*   Cache technology selection must be based on performance benchmarks and operational complexity, not just vendor preference.

### 2.5 Stakeholder Decision Rights
**Role Definition:** Clear decision rights are required to prevent bottlenecks and ensure accountability.

**Core Interactions & Boundaries:**
*   **Compliance Decisions:** Legal and Compliance teams own the final decision on regulatory requirements and data handling policies.
*   **Technical Decisions:** Engineering leads own the final decision on technology stack and implementation details.
*   **Product Decisions:** Product management owns the final decision on user journeys and feature scope.

**Operational Constraints:**
*   Decision rights must be formally documented and communicated to all stakeholders before the design phase begins.
*   Escalation paths must be defined for decisions that cannot be resolved at the team level.

## 3. Envisioned Capability Families

These capability families were discovered by Phase-0 Envisioning. They define the core functional domains that the Daya (MealCredit) platform must support.

### 3.1 Marketplace Liquidity and Credit Pool Management
**Role Definition:** Defines the core value exchange where donor capital is converted into regional credit pools for beneficiary redemption.

**Core Interactions & Boundaries:**
*   **Liquidity Ingestion:** Automated calculation of transaction round-ups from donor credit card spend via Plaid/Stripe integration.
*   **Pool Allocation:** Directed impact flows allow donors to assign funds globally, regionally, or to specific merchant types.
*   **Pool Utilization:** Real-time monitoring of credit pool balances and utilization rates across all footprints.

### 3.2 Dignified and Anonymous Redemption Engine
**Role Definition:** Ensures the beneficiary experience is frictionless and strictly anonymous, preserving dignity and privacy.

**Core Interactions & Boundaries:**
*   **Token Generation:** Single-use virtual card tokens generated client-side and pushed to secure wallets.
*   **POS Clearing:** Frictionless clearing at merchant POS, visually identical to standard consumer gift cards.
*   **Anonymization:** Absolute anonymization of beneficiary data, with no PII stored on-platform or in production logs.

### 3.3 Privileged Data Anonymization and Privacy
**Role Definition:** Enforces strict PII isolation and anonymization protocols to meet PCI-DSS and SOC2 Type II compliance requirements.

**Core Interactions & Boundaries:**
*   **Data Segregation:** Strict isolation of donor, beneficiary, and merchant data.
*   **Tokenization:** Client-side generation of clean tokenized vouchers.
*   **Audit Logging:** Immutable transactional receipts for donors, with no identifying beneficiary parameters.

### 3.4 Financial Ledger Integrity and Audit
**Role Definition:** Guarantees the accuracy and immutability of financial transactions through cryptographic logging and ACID compliance.

**Core Interactions & Boundaries:**
*   **ACID Compliance:** All financial transactions must adhere to ACID principles to ensure data integrity.
*   **Cryptographic Logging:** Immutable logs of all transactions for audit and reconciliation purposes.
*   **Reconciliation:** Automated reconciliation of transaction logs against financial ledgers.

### 3.5 Knowledge Gaps
*   **KNOWLEDGE_GAP:** Specific compliance requirements for NGO data handling in each jurisdiction (SF, NYC, Chicago) are not yet defined. Legal must establish the exact data retention and privacy obligations for NGO partners.
*   **KNOWLEDGE_GAP:** Financial licensing requirements for operating as a money transmitter in each state are not yet confirmed. Legal counsel must verify the necessary licenses.
*   **KNOWLEDGE_GAP:** The specific caching technology (e.g., Redis, Memcached) for restaurant search queries is not yet ratified. Engineering must evaluate options based on performance and operational complexity.
*   **KNOWLEDGE_GAP:** The specific zero-footprint POS integration standard is not yet ratified. Engineering must define the API contract for merchant onboarding.

### 3.6 Assumptions
*   **ASSUMPTION:** The platform will achieve 50,000 MAU across the three initial metropolitan footprints within the first year of operation. This assumption drives the initial capacity planning and infrastructure sizing.
*   **ASSUMPTION:** Merchant Partners will be willing to integrate with the platform's zero-footprint POS solution. This assumption is based on the value proposition of increased foot traffic and simplified reconciliation.
*   **ASSUMPTION:** Donors will continue to use micro-donation round-ups as the primary funding mechanism. This assumption is based on current trends in social impact fintech.

## 4. Cross-Document Term Consistency

This section ensures that all terms, IDs, and labels used in this artifact are consistent with other artifacts in the project.

### 4.2 Journey Names
*   **DonationandRoundUpProcessing:** Donor initiates a purchase or direct micro-donation via the mobile app or web interface. System calculates the round-up amount and securely processes the financial transaction through the payment gateway. Donor receives an immutable, anonymized transactional receipt confirming the impact of their contribution.
*   **AnonymousMealRedemption:** Beneficiary opens the mobile app and browses available restaurant partners based on location and dietary preferences. System generates a single-use, location-locked virtual card token and provisions it to the device's secure wallet. Beneficiary presents the token at the restaurant POS, where the system clears the transaction and deducts the credit from the regional pool.
*   **MerchantPayoutandReconciliation:** Restaurant partner submits daily transaction logs and settlement requests through the POS integration or dashboard. System cross-references the logs against the financial ledger and initiates an automated net payout to the restaurant's business account. Restaurant partner receives the funds and a reconciliation report, completing the fulfillment cycle.
*   **NGOVettingandOnboarding:** NGO partner submits an application for tiered access and begins the cryptographic onboarding process. System Administrator reviews the application, verifies the NGO's status, and grants delegated vetting permissions. NGO partner gains access to the dashboard to onboard beneficiaries and monitor regional credit pool utilization.

## 5. Out-of-Scope Signals

This section explicitly defines what is out of scope for the initial release of the Daya (MealCredit) platform.

*   **Direct Food Procurement:** The platform does not procure food directly. It facilitates financial transactions for food purchased at Merchant Partners.
*   **Physical Restaurant Management:** The platform does not manage the physical operations of Merchant Partners. It only integrates with their POS systems for transaction processing.
*   **Non-Food Merchandise:** Ineligible purchases like alcohol or non-food merchandise must be dropped at the Stripe network layer and are not supported by the platform.
*   **Physical Restaurant Management:** The platform does not manage the physical operations of Merchant Partners. It only integrates with their POS systems for transaction processing.
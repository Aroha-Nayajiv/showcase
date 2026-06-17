# Product Strategy & Scope Definition

### 1.1 Product Identity and Mission
The Daya platform (Product: MealCredit) is a regulated, multi-sided marketplace designed to decouple food assistance from social stigma. The core mission is to convert real-time financial micro-donations into fractional, anonymous culinary credits that are spent exactly like cash or standard gift cards at commercial restaurant establishments. By leveraging Pseudo-AnonymizedRedemption and AbsoluteAnonymization, the platform ensures that beneficiary demographic data is strictly off-platform, while donors receive immutable transactional receipts within 120 seconds of redemption.

### 1.2 System Classification
- **System Type:** Multi-sided Marketplace Platform (B2B2C).
- **Primary Domain:** Regulated Operations (Financial Services / Food Assistance).
- **Deployment Model:** Local runtime optimized for multi-tenant scalability across 3 initial metropolitan footprints (SF, NYC, Chicago).
- **Compliance Baseline:** SOC2 Type II structural planning and PCI-DSS Level 1 adherence are mandatory operating constraints.

### 1.3 Actor Roles and Boundaries
The platform operates through four distinct actor roles, each with specific authority and journey boundaries:

- **Contributor (ACT-2A20B038B1):** The funding source. Responsible for Contributor Onboarding & Funding (JNY-A9C1EB1FCC) and Contributor Primary Transaction Flow (JNY-4FC1874968). Contributors utilize Micro-DonationRound-Ups and DirectedImpactFlows to fund the credit pool.
- **Recipient (ACT-DC00FA84DC):** The beneficiary. Engages via Recipient Discovery & Redemption (JNY-76281D3F3C) and Recipient Anonymized Interaction (JNY-154AD4ADE0). The system enforces absolute anonymity, mapping analytics to high-entropy UUIDv4 keys to prevent PII reconstruction.
- **Merchant Partner (ACT-A14D3CDC5D):** The fulfillment entity. Responsible for Merchant Activation & Verification (JNY-82D2785E64) and Merchant Primary Fulfillment (JNY-01DD5AC877). Partners must integrate with the Integration & Payment Gateway Adapter (SUR-213BCD1816) to clear virtual card tokens.
- **Operator (ACT-FE96DD3975):** The governance entity. Manages Operator Governance & Liquidity Management (JNY-039CC03FAB) and Operator Offboarding & Data Sanitization (JNY-928D226FCB). The Operator monitors Donation-to-Redemption Velocity (DRV) and Credit Pool Utilization Rate to ensure system health.

### 1.4 Core Capability Ownership
Strategic scope is bounded by the following core capabilities:

- **Discovery & Allocation Engine (CAP-264DA83096):** Handles real-time geo-proximity indexing and balance refreshes for beneficiaries.
- **Identity & Access Management (CAP-361A59708B):** Manages secure onboarding for Contributors and Merchant Partners while maintaining Recipient anonymity.
- **Financial Transaction Processing (CAP-9CD814929D):** Executes VirtualCardProvisioning via Stripe Issuing API, ensuring zero raw credit card data touches application servers.
- **Compliance & Audit Governance (CAP-421F3AD853):** Enforces Compliance & Audit Governance (CAP-421F3AD853) by maintaining an append-only, cryptographic audit ledger in Aurora Postgres for all financial transactions.

### 1.6 Success Criteria Alignment
The product strategy is validated against the following success criteria:
- **Donation-to-Redemption Velocity (DRV):** Must remain under 14 days.
- **Merchant Retention Rate (MRR):** Measured month-over-month.
- **Credit Pool Utilization Rate:** Triggers alerts if above 85%.
- **Operational Uptime:** 99.99% across AWS multi-AZ configurations.
- **Accessibility:** Expo mobile app screens must meet WCAG 2.1 AA standards for low-vision beneficiaries.

### 1.7 Risk and Compliance Posture
- **PCI-DSS Level 1:** Enforced by ensuring zero raw credit card data touches application servers, using only Stripe Elements and SDK.
- **SOC2 Type II:** Structural planning required for detailed tracking logs for all infrastructure and administrative changes.
- **Data Anonymization:** Absolute anonymization where all beneficiary analytics map to high-entropy UUIDv4 keys, preventing PII reconstruction.
- **Financial Reconciliation:** Must be robust against partial failures, ensuring that credits issued but not cleared do not leave the ledger in an inconsistent state.

### 2.1 Contributor (ACT-2A20B038B1)
The Contributor is the financial engine of the platform, providing the capital that fuels the culinary credit pool. Their primary obligation is to fund the system through micro-donations, round-ups, or directed impact flows.

**Primary User Journeys:**
- **Contributor Onboarding & Funding (JNY-A9C1EB1FCC):** The Contributor initiates the relationship by creating an account and linking an external financial identity. This journey focuses on establishing trust and verifying the payment instrument. The system validates the payment method and transitions the Contributor to an active funding status, enabling automated round-ups or scheduled donations.
- **Contributor Primary Transaction Flow (JNY-4FC1874968):** Once active, the Contributor's financial instruments are monitored. The platform calculates fractional contributions based on configured rules (e.g., round-ups or fixed amounts). Funds are transferred to the central pool, and the Contributor receives an immutable transactional receipt within 120 seconds of beneficiary redemption.

### 2.2 Recipient (ACT-DC00FA84DC)
The Recipient is the beneficiary of the platform's mission. Their experience is designed to be frictionless, dignified, and completely anonymous to prevent social stigma.

**Primary User Journeys:**
- **Recipient Discovery & Redemption (JNY-76281D3F3C):** The Recipient uses the mobile app to map participating dining locations sorted by distance and dietary flags. The system queries the Aurora ledger to verify pool balance and generates a single-use virtual card token. This token is pushed to the phone as an Apple/Google Wallet pass or a scannable barcode for frictionless clearing at the POS.
- **Recipient Anonymized Interaction (JNY-154AD4ADE0):** Throughout the interaction, the system enforces absolute anonymity. No PII (legal name, domestic background) is stored on-platform or in production logs. All beneficiary analytics map to high-entropy UUIDv4 keys.

### 2.3 Merchant Partner (ACT-A14D3CDC5D)
The Merchant Partner (Restaurant) is the fulfillment entity. They must integrate with the platform to accept virtual card tokens and manage order fulfillment.

**Primary User Journeys:**
- **Merchant Activation & Verification (JNY-82D2785E64):** The Merchant Partner registers on the platform, undergoes verification, and configures their POS integration. They must ensure their menu items comply with platform rules (e.g., dropping ineligible purchases like alcohol at the Stripe network layer).
- **Merchant Primary Fulfillment (JNY-01DD5AC877):** The POS system ingests the order via zero-footprint integration or edge dashboard. The system validates the virtual card token against Stripe Issuing and clears the transaction. The Merchant Partner receives settlement payouts according to the configured schedule.

### 2.4 Operator (ACT-FE96DD3975)
The Operator manages the platform's governance, liquidity, and operational health. They ensure the system remains solvent, compliant, and performant.

**Primary User Journeys:**
- **Operator Governance & Liquidity Management (JNY-039CC03FAB):** The Operator monitors Donation-to-Redemption Velocity (DRV) and Credit Pool Utilization Rate. They manage the regional credit pools, ensuring that unused emergency credits auto-roll back to the central pool after 72 hours to prevent ledger stagnation.
- **Operator Offboarding & Data Sanitization (JNY-928D226FCB):** The Operator manages the offboarding of Merchant Partners or Contributors, ensuring all data is sanitized according to SOC2 Type II and PCI-DSS Level 1 requirements.

## 3. Architectural Surfaces & Integration

The platform's architecture is defined by four key surfaces that facilitate the flow of data, funds, and identity across the ecosystem.

### 3.1 Client Application Layer (SUR-E3E75E96CF)
The Client Application Layer provides the user-facing interfaces for Contributors, Recipients, and Merchant Partners. It is built using Expo for mobile and Next.js for web dashboards. This layer handles user interactions, local token storage (SecureStore), and offline fallback presentations (QR/barcodes).

### 3.2 API Gateway & Orchestration Layer (SUR-D6FFF7036F)
The API Gateway serves as the entry point for all client requests. It orchestrates the flow of data between the Client Application Layer and the Core Transaction & Ledger Service. It handles authentication, rate limiting, and request routing.

### 3.3 Core Transaction & Ledger Service (SUR-DD602DB92C)
The Core Transaction & Ledger Service is the heart of the platform. It maintains the append-only, cryptographic audit ledger in Aurora Postgres. It processes financial transactions, manages credit pool balances, and ensures financial reconciliation robust against partial failures.

### 3.4 Integration & Payment Gateway Adapter (SUR-213BCD1816)
The Integration & Payment Gateway Adapter handles all external financial integrations, primarily with Stripe Issuing and Plaid. It ensures that zero raw credit card data touches application servers and manages the provisioning of virtual card tokens.

## 4. Key Decision Axes & Knowledge Gaps

The following decision axes remain open and require resolution before downstream design and implementation phases can proceed.

### 4.1 Virtual Card Limit Enforcement
**Decision Axis:** Should the virtual card limit enforcement rely solely on Stripe's backend merchant-category-code (MCC) and geo-fencing rules, or require a pre-authorization validation step from the backend to enforce NGO-specific spending caps before card issuance?
**Owner:** Engineering / Product
**Evidence Needed:** Stripe Issuing API capabilities and NGO-specific spending policy requirements.

### 4.2 Offline Redemption Resilience
**Decision Axis:** For offline redemption resilience, should the system store a time-bound, signed JWT voucher on the client's SecureStore that requires network connectivity for verification (online-only when available), or implement a complex offline-counter mechanism with local cryptographic nonce tracking to allow offline clearing?
**Owner:** Engineering / Security
**Evidence Needed:** POS device capabilities and offline transaction volume projections.

### 4.3 POS Integration Middleware
**Decision Axis:** Which specific POS integration middleware strategy will be adopted: using Stripe's existing Square POS integration vs. building custom gRPC adapters for Toast and Clover to ensure consistent event streaming into the event-driven architecture?
**Owner:** Engineering / Partnerships
**Evidence Needed:** Merchant Partner POS market share and integration cost-benefit analysis.

### 4.4 Directed Impact Flow Processing
**Decision Axis:** Does the 'Directed Impact Flow' require real-time filtering of eligible merchants at the point of donation, or can it be processed asynchronously with a batch-settlement mechanism for unfulfilled directed funds?
**Owner:** Product / Engineering
**Evidence Needed:** Donor experience requirements and backend processing capacity.

### 4.5 Regulatory Compliance
The platform must comply with financial services regulations regarding virtual gift card issuance and money transmission licensing across 3 metro areas. This includes adhering to SOC2 Type II control environments and PCI-DSS Level 1 security standards.

### 4.6 Data Privacy & Anonymization
Beneficiary demographic data must be strictly off-platform. The platform stores only derived, anonymized credits. All beneficiary analytics map to high-entropy UUIDv4 keys, preventing PII reconstruction. Data retention policies must ensure unused emergency credits auto-roll back to the regional pool after 72 hours.

### 4.7 Risk Mitigation
- **Financial Reconciliation Risk:** Mitigated by robust partial failure handling in the Core Transaction & Ledger Service.
- **Data Leakage Risk:** Mitigated by enforcing PCI-DSS Level 1 and absolute anonymization standards.
- **Operational Risk:** Mitigated by achieving 99.99% operational uptime across AWS multi-AZ configurations and graceful degradation if POS partners fail.

## 5. Success Metrics & Monitoring

The platform's success will be measured against the following key performance indicators:

- **Donation-to-Redemption Velocity (DRV):** Target under 14 days.
- **Merchant Retention Rate (MRR):** Measured month-over-month.
- **Credit Pool Utilization Rate:** Alerts triggered at 85% threshold.
- **Stripe Webhook Processing Latency:** Target average below 150ms.
- **Cache Hit Ratio (CHR):** Target above 92% for restaurant search queries.
- **API Responsiveness:** Target p99 latency below 250ms under 10,000 concurrent connections.
- **Operational Uptime:** Target 99.99% across AWS multi-AZ configurations.

### 5.1 Decision Owners
- **Product Strategy & Scope:** VP of Product
- **Technical Architecture & Implementation:** CTO / Lead Architect
- **Compliance & Legal:** Chief Compliance Officer
- **Merchant Partnerships:** Head of Partnerships
- **Operations & Liquidity:** Head of Operations

### 5.2 Stakeholder Groups
- **Contributors (Donors):** Primary funding source.
- **Recipients (Beneficiaries):** Primary beneficiaries of the platform.
- **Merchant Partners (Restaurants):** Primary fulfillment entities.
- **Operators (NGOs/Platform Admins):** Governance and liquidity management.
- **Regulators:** Compliance oversight.

## 6. Implementation Roadmap & Phasing

### 6.1 Phase 1: MVP Launch (SF, NYC, Chicago)
- Focus on core transaction flows and basic merchant onboarding.
- Establish initial liquidity pools and compliance frameworks.

### 6.2 Phase 2: Scale & Optimization
- Expand to additional metropolitan footprints.
- Optimize performance and scalability based on Phase 1 metrics.
- Introduce advanced features like Directed Impact Flows.

## 7. Conclusion

The Daya platform (MealCredit) represents a significant opportunity to decouple food assistance from social stigma through a regulated, multi-sided marketplace. By leveraging modern fintech technologies and adhering to strict compliance and privacy standards, the platform can create a sustainable and impactful ecosystem for Contributors, Recipients, and Merchant Partners. The key to success lies in resolving the open decision axes, maintaining operational excellence, and continuously monitoring success metrics to drive iterative improvement.
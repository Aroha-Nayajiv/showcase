# Product Vision and Scope Definition

This artifact establishes the authoritative product model for the **daya** platform, a tripartite social-impact fintech marketplace connecting Donors, Beneficiaries, and Merchant Partners (Restaurants) via local NGOs. The scope explicitly covers the three primary user journeys: DonorFundingFlow (micro-donation round-ups via Plaid/Stripe), BeneficiaryRedemptionFlow (anonymous virtual card token generation and POS clearing), and MerchantFulfillmentFlow (zero-footprint POS integration and order validation). It codifies the core business rules: absolute anonymization of beneficiary data (no PII in logs), 120-second immutable receipt generation for donors, 72-hour credit expiration rollback to the regional pool, and real-time kitchen throttle parameters. It also defines the initial success criteria (KPIs) including Donation-to-Redemption Velocity (DRV) under 14 days, 99.99% AWS multi-AZ uptime, and specific latency targets for Stripe webhooks and API responsiveness.

## 1.1. Actor Definitions and Journey Touchpoints

The daya platform operates within a 3-metro footprint (San Francisco, New York City, Chicago). The following actor definitions and journey touchpoints formalize the system's primary interactions.

### 1.1.2. Beneficiary Actor
**Definition:** An individual in need of food assistance who uses the daya app to locate participating dining locations. Beneficiary data must be absolutely anonymized with no PII (such as legal name or domestic background) stored on-platform or in production logs.

**Journey Touchpoints (BeneficiaryRedemptionFlow):**
1. **Discovery:** Beneficiary app maps participating dining locations sorted by distance and dietary flags.
2. **Token Generation:** System queries Aurora ledger to verify pool balance and generates a single-use virtual card token.
3. **Redemption:** Token is pushed to the phone as an Apple/Google Wallet pass or barcode for frictionless clearing at the POS.

### 1.1.3. Merchant Partner Actor
**Definition:** A restaurant or kitchen partner that fulfills orders using the daya platform. Merchants must be able to toggle real-time throttle parameters (e.g., maximum of 15 MealCredit orders per hour) to prevent structural overload. Ineligible purchases (e.g., alcohol, non-food merchandise) are dropped at the Stripe network layer.

**Journey Touchpoints (MerchantFulfillmentFlow):**
1. **Ingestion:** POS system ingests order via zero-footprint integration or edge dashboard.
2. **Validation:** System validates the virtual card token against Stripe Issuing restrictions.
3. **Settlement:** Automated daily net payout settles cleared credits to the restaurant's business checking account within 24 hours.

## 1.2. Core Architectural Invariants

### 1.2.1. Absolute Anonymization
Beneficiary data must be absolutely anonymized. No PII (legal name, domestic background) is stored on-platform or in production logs. Client-side generation of clean tokenized vouchers ensures visually identical consumer gift cards without exposing beneficiary demographic data.

**Operational Mechanism:** Client-side generation of clean tokenized vouchers visually identical to consumer gift cards, ensuring no beneficiary demographic data crosses into production logs.

**Architectural Implication:** The system acts as a blind proxy. The Donor funds the pool; the NGO allocates eligibility; the Beneficiary redeems a token. The Donor and Merchant never see the Beneficiary's identity. The NGO Administrator sees only the allocation metrics, not the individual's PII, unless explicitly required by external compliance (which is out of scope for this platform's core data model).

## 1.3. Scope Boundaries

**In-Scope:**
- Anonymous credit fulfillment and financial clearing.
- Marketplace liquidity tracking and operational metrics.
- NGO vetting and allocation governance (high-level dependency).
- Tripartite platform architecture connecting Donors, Beneficiaries, and Merchants via NGOs.

**Out-of-Scope:**
- Detailed implementation tuning of specific POS integrations.
- Future scaling architecture beyond 50,000 MAU.
- Third-party cloud dependency management beyond specified stack.
- Risk Register details (see sibling artifact `inception_risk_constraints`).
- Success Criteria definitions (see sibling artifact `inception_success_criteria`).
- Governance, Compliance, and Privacy Obligations (see sibling artifact `inception_governance_compliance`).

## 1.4. Decision Foundations and Open Gaps

The following decisions are required to finalize the product scope and ensure downstream design integrity. These are not yet ratified and represent the current state of project truth.

| Decision Axis | Current Status | Owner / Evidence Needed |
| :--- | :--- | :--- |
| NGO Data Storage Boundary | **KNOWLEDGE_GAP:** Exact data retention and storage requirements for NGO-vetted beneficiary lists are not established. | NGO Compliance Lead / Legal Counsel |
| Credit Expiration Policy | **ASSUMPTION:** 72-hour expiration is the default policy for unused emergency credits. | Product Strategy / VP Ratification |
| POS Integration Standard | **KNOWLEDGE_GAP:** Specific POS vendor APIs supported in the initial 3-metro launch are not established. | Engineering Lead / Merchant Partners |
| Donor Receipt Format | **ASSUMPTION:** Immutable transactional receipts are generated within 120 seconds via email or in-app notification. | Product Strategy / VP Ratification |
# Risk Register & Operating Constraints

## 1. Executive Summary & Scope

This artifact defines the risk posture, binding technical constraints, and unresolved decision axes for the Daya (MealCredit) platform. It serves as the foundational risk register for the inception phase, ensuring that financial integrity, regulatory compliance, and operational resilience are established before downstream design and implementation phases.

The scope is strictly bounded to the tripartite marketplace connecting Donors, Beneficiaries, and Merchant Partners (Restaurants) through local non-profit organizations (NGOs). All risks and constraints herein are derived from the project requirement, the SoftwareDNA product definition, and the established system blueprint.

## 2. Financial Risk Catalog

The following risks are critical to the financial viability and regulatory compliance of the platform. Each risk is mapped to the specific capability or journey it impacts.

### 2.1 Reconciliation Failures

*   **Risk ID:** RISK-FIN-001
*   **Description:** Complex reconciliation logic failures when handling partial redemptions, expired credits, or third-party system failures (e.g., Stripe webhook drops). This could lead to ledger discrepancies between the internal Aurora Ledger and external banking networks.
*   **Impact:** High. Financial loss, donor trust erosion, and regulatory non-compliance.
*   **Mitigation Strategy:** Implement idempotent transaction processing and automated daily reconciliation jobs between the `Financial Ledger & Clearing` capability and Stripe Connect. The `Merchant Settlement & Reconciliation` capability must handle grace periods for failed settlements.
*   **Owner:** Platform Operator
*   **Status:** Open - Requires detailed reconciliation algorithm design in Design Phase.

### 2.2 Credit Pool Utilization & Liquidity Stagnation

*   **Risk ID:** RISK-FIN-002
*   **Description:** Credit Pool Utilization Rate exceeding 85% or Donation-to-Redemption Velocity (DRV) exceeding 14 days. This indicates liquidity stagnation, where funds are not circulating efficiently between Donors and Beneficiaries, potentially leading to platform insolvency or beneficiary access denial.
*   **Impact:** High. Operational failure and loss of beneficiary trust.
*   **Mitigation Strategy:** Automated alerts must be triggered if utilization exceeds 85%. The `Inventory & Liquidity Balancing` capability must dynamically adjust credit issuance rates based on real-time pool levels. DRV must be monitored continuously.
*   **Owner:** Platform Operator
*   **Status:** Open - Thresholds are defined in Success Criteria but dynamic adjustment logic is unresolved.

### 2.3 Donor Fund Segregation

*   **Risk ID:** RISK-FIN-003
*   **Description:** Failure to strictly segregate donor funds (via Stripe Vault) from beneficiary impact analytics and operational funds. Commingling funds could violate financial regulations and donor trust agreements.
*   **Impact:** Critical. Legal liability and regulatory fines.
*   **Mitigation Strategy:** Enforce strict data isolation between metropolitan tenants and logical segregation of financial instruments. The `Financial Transaction Engine` must ensure that donor PII and fund sources are never cross-pollinated with beneficiary data.
*   **Owner:** Platform Operator
*   **Status:** Open - Requires detailed data architecture design.

## 3. Binding Technical Constraints

These constraints are non-negotiable and must be adhered to in all subsequent design and implementation phases. They are derived from compliance requirements (PCI-DSS, SOC2) and operational necessities.

### 3.1 PCI-DSS Level 1 Adherence

*   **Constraint ID:** CON-FB739F5332
*   **Description:** Enforce PCI-DSS Level 1 by routing all card data through Stripe Elements and SDK; never store raw PANs.
*   **Binding Rule:** The system must never store, process, or transmit raw Primary Account Numbers (PANs). All card data must be routed through Stripe Elements and the Stripe SDK. Raw PANs are strictly prohibited from entering the Daya platform's infrastructure, including logs, databases, or memory.
*   **Owner:** Platform Operator
*   **Status:** Binding

### 3.3 Latency Sensitivity

*   **Constraint ID:** CON-F1195DEBD1
*   **Description:** Maintain p99 API latency below 250ms for critical redemption and voucher creation actions.
*   **Binding Rule:** The system must ensure a frictionless experience for Beneficiaries and Merchant Partners during peak POS transaction windows. API Responsiveness p99 latency must remain below 250ms under 10,000 concurrent connections.
*   **Owner:** Platform Operator
*   **Status:** Binding

### 3.4 Operational Uptime

*   **Constraint ID:** CON-22FBC079F6
*   **Description:** Achieve 99.99% operational uptime using AWS multi-AZ configurations for all core services.
*   **Binding Rule:** This is a non-negotiable constraint for a financial instrument handling platform. All core services must be deployed across multiple Availability Zones to ensure high availability.
*   **Owner:** Platform Operator
*   **Status:** Binding

## 4. Unresolved Decision Axes & Knowledge Gaps

The following areas require explicit decision-making before the Design phase can finalize architectural trade-offs. These are not failures but necessary steps to ground the design in project-specific reality.

### 4.1 Legal Liability Boundaries

*   **Decision Axis:** Legal liability boundaries regarding ineligible merchant purchases.
*   **Context:** The `Compliance & Anonymization Engine` must drop transactions for ineligible purchases (e.g., alcohol, non-food items) at the Stripe network layer. However, the legal recourse and liability assignment for attempted ineligible purchases must be defined by Legal.
*   **Knowledge Gap:** What is the specific legal liability framework for ineligible merchant purchases? Who is liable if a Merchant Partner attempts to process an ineligible purchase that bypasses the network layer drop?
*   **Owner:** Legal / Platform Operator
*   **Status:** Unresolved

### 4.2 Cross-Border Data Sovereignty

*   **Decision Axis:** Cross-border data sovereignty if expanding beyond US metros.
*   **Context:** Initial operations are strictly within US jurisdictions (SF, NYC, Chicago). However, future expansion may require compliance with international data sovereignty laws.
*   **Assumption:** Initial operations will be strictly within US jurisdictions. This must be ratified by Legal.
*   **Owner:** Legal / Strategy
*   **Status:** Assumption - Pending Ratification

### 4.3 Beneficiary Data Retention Periods

*   **Decision Axis:** Specific retention period for beneficiary demographic data.
*   **Context:** The system must retain immutable financial ledger entries in Aurora for statutory compliance (7+ years implied). However, the specific retention period for beneficiary demographic data (classified as 'Anonymous') is unresolved.
*   **Knowledge Gap:** What retention period is binding for beneficiary demographic data under GLBA and CCPA?
*   **Owner:** Legal / Compliance
*   **Status:** Unresolved

### 4.4 Credit Pool Segmentation

*   **Decision Axis:** Centralized vs. Segmented Credit Pools.
*   **Context:** Should the platform adopt a strict centralized credit ledger (single pool per metro) or allow for granular, segmented credit pools (e.g., distinct pools for Vegan, Halal, or specific NGO allocations) to support donor-directed impact flows?
*   **Knowledge Gap:** What is the required granularity for credit pool segmentation to support donor-directed impact flows?
*   **Owner:** Product / Platform Operator
*   **Status:** Unresolved

## 5. Success Criteria Validation

The following success criteria are derived from the project requirement and SoftwareDNA. They serve as the measurable targets for platform health and will dictate architectural and business decisions in subsequent phases.

### 5.1 Velocity and Liquidity Metrics

*   **Donation-to-Redemption Velocity (DRV):** The system must achieve a DRV of under 14 days. This metric measures the time elapsed between a Donor's micro-donation round-up and the subsequent redemption of those funds by a Beneficiary at a Merchant Partner.
*   **Credit Pool Utilization Rate:** The platform must maintain a Credit Pool Utilization Rate below 85%. Automated alerts must be triggered if utilization exceeds this threshold to prevent ledger stagnation.

### 5.2 Financial Sustainability and Retention

*   **Merchant Retention Rate (MRR):** MRR is measured month-over-month. The target is to maintain a high retention rate among Merchant Partners, as their onboarding and POS integration represent the highest friction point in the ecosystem.
*   **Monthly Recurring Revenue (MRR):** While specific financial targets are currently a KNOWLEDGE_GAP, the revenue model is anchored in the `Merchant Settlement & Reconciliation` capability.

### 5.3 Technical Performance and Reliability

*   **API Responsiveness:** The p99 API latency for critical redemption and voucher creation actions must remain below 250ms under 10,000 concurrent connections.
*   **Stripe Webhook Processing Latency:** To ensure sub-150ms clearing times, the system must track Stripe Webhook Processing Latency.
*   **Operational Uptime:** The platform must achieve 99.99% operational uptime using AWS multi-AZ configurations for all core services.

## 6. Follow-Up Questions

The following questions must be resolved before the Design phase can proceed:

1.  **Question:** What is the specific legal liability framework for ineligible merchant purchases?
    **Why Critical:** The `Compliance & Anonymization Engine` must be designed to drop these transactions, but the legal recourse and liability assignment for attempted ineligible purchases must be defined by Legal.
2.  **Question:** What are the specific beneficiary data retention periods required by GLBA and CCPA?
    **Why Critical:** This determines the data lifecycle policies for the `Financial Ledger & Clearing` and `Compliance & Anonymization Engine` capabilities.
3.  **Question:** What is the target Monthly Recurring Revenue (MRR) for the first 12 months?
    **Why Critical:** This drives the financial modeling for the `Merchant Settlement & Reconciliation` and `Financial Ledger & Clearing` capabilities.
4.  **Question:** Should the platform adopt a strict centralized credit ledger (single pool per metro) or allow for granular, segmented credit pools?
    **Why Critical:** This decision impacts the data architecture of the `Inventory & Liquidity Balancing` capability and the complexity of the `Financial Ledger & Clearing` system.
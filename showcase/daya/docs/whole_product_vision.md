# Whole-Product Vision & Scope Definition

## 1. Executive Summary

This document establishes the foundational product model for **Daya** (product name: **MealCredit**), a tripartite, social-impact fintech marketplace. The platform mission is to decouple food assistance from social stigma by converting real-time financial micro-donations into fractional, anonymous culinary credits. These credits are spent exactly like cash or standard gift cards at commercial restaurant establishments.

The system operates as a multi-sided marketplace connecting three primary actor groups—**Donors**, **Beneficiaries**, and **Merchant Partners** (Restaurants)—through the enabling role of local non-profit organizations (**NGOs**). The initial target scale is 50,000 Monthly Active Users (MAU) across three metropolitan footprints: San Francisco (SF), New York City (NYC), and Chicago.

The primary strategic objective is to transition from a single-city MVP architecture to a resilient, multi-tenant architecture capable of supporting these three initial metropolitan footprints. This document defines the core system classification, the binding compliance and trust constraints, and the decision foundations required to proceed to downstream design and implementation phases.

### 2.1 System Identity
*   **Product Name:** Daya (MealCredit)
*   **System Type:** Fintech Platform / Multi-sided Marketplace
*   **Primary Domain:** Directed Impact Flows and Absolute Anonymization
*   **Deployment Model:** Multi-tenant, Multi-metro (SF, NYC, Chicago)
*   **Compliance Regime:** SOC2 Type II, PCI-DSS Level 1, GDPR/CCPA

### 2.2 Core System Classification
The platform is classified as a **Fintech Platform** because it facilitates the movement of value (micro-donations) and the issuance of redeemable financial instruments (virtual card tokens) via standard banking networks (Stripe Issuing). It is a **Multi-sided Marketplace** because it requires the simultaneous interaction of distinct user groups (Donors, Beneficiaries, Merchants) to create value.

### 2.3 Scope Boundaries
*   **In-Scope:**
    *   Micro-donation round-up integration via Plaid/Stripe.
    *   Generation and management of single-use virtual card tokens.
    *   Real-time redemption and settlement processing.
    *   NGO onboarding, eligibility verification, and regional liquidity management.
    *   Merchant POS integration and fraud detection.
    *   Donor impact receipts and transactional history.
*   **Out-of-Scope (Explicitly Deferred):**
    *   Direct cash disbursement to beneficiaries (platform is strictly credit-based).
    *   Physical food procurement or supply chain logistics (handled by Merchant Partners).
    *   Legacy NGO database migration (NGOs manage their own legacy systems; Daya integrates via API or manual upload).

## 3. Tripartite Actor Ecosystem

The Daya platform relies on a specific actor model to ensure dignity, privacy, and operational efficiency. The following actors are established in the living product model and remain binding.

### 3.1 Primary Actors

#### 3.1.1 Donor (ACT-80C62C7814)
*   **Role:** Provides the capital for the credit pool via micro-donations.
*   **Key Journeys:**
    *   **Funder Onboarding and Funding Setup (JNY-10C5ADD243):** Integrate credit card via Plaid/Stripe for micro-donation round-ups; assign funds globally or to specific regional/merchant targets.
    *   **Donor Round-Up & Impact Verification (JNY-D980A59D43):** Receive immutable transactional receipts within 120 seconds of redemption, strictly prohibiting transmission of any identifying beneficiary parameters.
*   **Obligations:** Donors must receive immutable transactional receipts within 120 seconds of redemption. These receipts must strictly prohibit the transmission of any identifying beneficiary parameters.

#### 3.1.2 Beneficiary (ACT-ADA6716160)
*   **Role:** The end-user who receives and redeems culinary credits.
*   **Key Journeys:**
    *   **Beneficiary Dignified Redemption (JNY-1A3DBC558B):** App maps participating dining locations sorted by distance and dietary flags; system queries Aurora ledger to verify pool balance and generates single-use virtual card token; token pushed to phone as Apple/Google Wallet pass or barcode for frictionless clearing at POS.
*   **Obligations:** Beneficiary data must be absolutely anonymized with no PII such as legal name or domestic background stored on-platform or in production logs.

#### 3.1.3 Merchant Partner (ACT-A14D3CDC5D)
*   **Role:** Commercial restaurant establishments that accept MealCredits as payment.
*   **Key Journeys:**
    *   **Merchant Fulfillment & Settlement (JNY-A4C99AE47D):** POS system ingests order via zero-footprint integration or edge dashboard; system validates virtual card token against Stripe Issuing rest...
*   **Obligations:** Kitchens must be able to toggle real-time throttle parameters to prevent structural overload. Ineligible purchases like alcohol or non-food merchandise must be dropped at the Stripe network layer.

### 3.2 Enabling & Governance Actors

#### 3.2.1 NGO Representative (ACT-40FE7F0541)
*   **Role:** Local non-profit organization that manages beneficiary eligibility and regional liquidity.
*   **Key Journeys:**
    *   **NGO Allocation & Liquidity Management (JNY-FC09C6602B):** Initiates eligibility screening process based on predefined criteria; system validates Recipient identity securely without storing sensitive PII.
*   **Obligations:** Manages the alias-to-person mapping off-platform. The platform only stores the alias and associated redemption tokens.

#### 3.2.2 Platform Operator (ACT-0E3EE366E3)
*   **Role:** Oversees platform health, compliance, and operational metrics.
*   **Obligations:** Responsible for monitoring system uptime, latency targets, and fraud detection alerts.

#### 3.2.3 Platform Administrator (ACT-086A974D63)
*   **Role:** Manages system configuration, user access, and global policy enforcement.
*   **Obligations:** Manages DirectedImpactFlows configuration and global system settings.

#### 3.2.4 Gatekeeper (ACT-AC2B839C3F)
*   **Role:** Initiates eligibility screening for Recipients.
*   **Obligations:** Validates Recipient identity securely without storing sensitive PII.

#### 3.2.5 Dispute Adjudicator (ACT-7BA340FF76)
*   **Role:** Resolves conflicts between actors (e.g., merchant-beneficiary disputes).
*   **Key Journeys:**
    *   **Dispute Adjudication and Resolution (JNY-F223639A10):** Handles evidence submission and resolution workflows.

## 4. Binding Compliance & Trust Constraints

The Daya platform operates in a highly regulated environment. The following constraints are binding and must be adhered to in all design and implementation phases.

### 4.1 Absolute Anonymization (Beneficiary PII)
*   **Rule:** Beneficiary data must be absolutely anonymized. No PII such as legal name, SSN, or domestic background is stored on-platform or in production logs.
*   **Implementation:** Identity is managed via cryptographic aliases (ACT-40FE7F0541: NGO Representative manages the alias-to-person mapping off-platform). The platform only stores the alias and associated redemption tokens.
*   **Constraint:** Any attempt to log or transmit beneficiary PII to funders, providers, or standard logs is a critical security violation.
*   **Evidence:** CON-5CA3E5A67B (Classify Beneficiary PII as 'Restricted No-PII'; ensure no legal names, SSNs, or demographics are stored on-platform beyond crypto...)

### 4.2 PCI-DSS Level 1 Adherence
*   **Rule:** The platform must adhere to PCI-DSS Level 1 requirements managed primarily through Stripe's compliance scope.
*   **Implementation:** Implement Stripe Elements and Stripe SDK globally to ensure zero raw credit card data touches application servers (PCI-DSS Level 1).
*   **Evidence:** CON-31C0A24105 (Implement Stripe Elements and Stripe SDK globally to ensure zero raw credit card data touches application servers (PCI-DSS Level 1).)

### 4.3 SOC2 Type II Audit Trails
*   **Rule:** Plan infrastructure and logging to support SOC2 Type II audit trails for all administrative and ledger operations.
*   **Implementation:** Push all infrastructure modifications and API adjustments to AWS CloudTrail for SOC2 Type II audit evidence.
*   **Evidence:** CON-00789EFED7 (Push all infrastructure modifications and API adjustments to AWS CloudTrail for SOC2 Type II audit evidence.)

### 4.4 Donor Transaction History & Retention
*   **Rule:** Donors must receive immutable transactional receipts within 120 seconds of redemption.
*   **Constraint:** These receipts must strictly prohibit the transmission of any identifying beneficiary parameters. The receipt confirms the impact (e.g., "Funded 2 meals at [Merchant Name]") without revealing who received the meals.
*   **Retention:** Donor transaction history must be retained for 7 years for tax purposes, in compliance with CON-746AF68070.
*   **Evidence:** CON-746AF68070 (Define data retention policies for Donor transaction history and impact receipts (e.g., 7 years for tax purposes).)

## 5. Strategic Objectives & Scaling

### 5.1 MVP to Multi-Metro Scaling
*   **Objective:** Transition from a single-city MVP architecture to a resilient multi-tenant architecture across 3 metropolitan footprints (SF, NYC, Chicago).
*   **Key Challenges:**
    *   **Data Sovereignty:** Ensure strict data partitioning in DynamoDB/PostgreSQL to isolate NGO regional data to prevent cross-contamination (CON-709C3F21C2).
    *   **Latency:** Achieve p99 latency <250ms for Voucher Creation and Scanning Callback Processing under 10,000 concurrent connections (CON-78A549ECB3).
    *   **Uptime:** Maintain 99.99% operational uptime across AWS multi-AZ configurations (CON-725D8AA177).

### 5.2 Market Liquidity & Search Performance
*   **Objective:** Ensure the efficiency of the marketplace by enabling Beneficiaries to quickly find participating Merchant Partners.
*   **Constraint:** The system must achieve a Cache Hit Ratio (CHR) greater than 92% for restaurant search queries via the Redis Enterprise Cluster.
*   **Evidence:** CON-59F8C209D1 (Ensure Cache Hit Ratio (CHR) for restaurant search queries exceeds 92% via Redis Enterprise Cluster.)

### 5.3 Webhook Processing Latency
*   **Objective:** Ensure timely settlement and ledger updates by processing Stripe Webhook events to merchant ledger entries rapidly.
*   **Constraint:** The system must process Stripe Webhook events to merchant ledger entries within an average latency of 150 milliseconds.
*   **Evidence:** CON-AE9B9C163C (Process Stripe Webhook events to merchant ledger entry within 150ms average latency.)

## 6. Risk Identification & Mitigation (High-Level)

*Note: Detailed risk mitigation strategies are deferred to the Risk Register & Technical Constraints artifact. This section outlines high-level risk categories.*

### 6.1 Merchant Collusion Detection and Cash-Out Fraud Prevention
*   **Risk Description:** Merchant Partners (ACT-A14D3CDC5D) may collude with Beneficiaries (ACT-ADA6716160) to convert MealCredits into cash or ineligible goods, violating the platform's social impact mission. This includes "cash-out" schemes where merchants accept tokens but provide cash or non-food items, or where merchants and beneficiaries artificially inflate transaction volumes to drain donor funds.
*   **Mapping to Capabilities:**
    *   **Fraud Detection & Prevention (CAP-50F5F57DBF):** Requires real-time anomaly detection to identify patterns indicative of collusion, such as a single beneficiary consistently transacting at a single merchant, or a merchant processing an unusually high volume of transactions from a small number of beneficiaries.
    *   **Merchant Failover & Resilience (CAP-3701C64DAE):** Requires mechanisms to suspend merchant accounts and freeze pending settlements when fraud is suspected, preventing further financial loss.
*   **Technical Constraints & Binding Obligations:**
    *   **Transaction Monitoring:** The system must implement real-time transaction monitoring using the Fraud Detection & Prevention capability to flag transactions that deviate from established behavioral baselines (CON-29859B910F).
    *   **MCC Enforcement:** Virtual card tokens must be strictly locked to specific Merchant Category Codes (MCC) for eligible purchases (e.g., food and beverage) and dropped at the Stripe network layer for ineligible purchases (e.g., alcohol or non-food merchandise).

### 6.2 System Resilience & Offline Capability
*   **Risk Description:** Network outages or POS system failures could prevent transaction validation, leading to lost sales and beneficiary frustration.
*   **Mitigation Strategy:**
    *   **Offline Token Cryptographic Signature Validation Logic (CON-A016F9DA51):** Design offline token generation to use hardware-backed SecureStore with time-bound, signature-verified cryptograms.
    *   **Offline Fallback:** Ensure offline fallback QR codes are large enough and high-contrast enough for easy scanning by cashiers (CON-ED34D14363).

## 7. Sibling Artifact Deferrals

To maintain clear scope boundaries, the following concerns are deferred to sibling artifacts:

*   **Stakeholder Map & Decision Rights:** Detailed decision rights for compliance violations are deferred to the Stakeholder Map & Decision Rights artifact.
*   **Risk Register & Technical Constraints:** Specific risk mitigation strategies for compliance failures are deferred to the Risk Register & Technical Constraints artifact.
*   **Success Criteria & Operational Metrics:** Specific KPIs for compliance adherence are deferred to the Success Criteria & Operational Metrics artifact.
*   **Compliance, Privacy & Regulatory Obligations:** Detailed regulatory obligations are deferred to the Compliance, Privacy & Regulatory Obligations artifact.

### 7.1 Assumptions
*   **ASSUMPTION:** The 10,000 concurrent connections metric refers to simultaneous active sessions across all three metropolitan footprints (SF, NYC, Chicago), not per region. This assumption is grounded in the project requirement's target scale of 50,000 MAU across 3 metros.

### 7.2 Knowledge Gaps
*   **KNOWLEDGE_GAP:** The specific infrastructure sizing (e.g., number of Redis nodes, Aurora instance classes) required to guarantee these constraints under peak load has not been determined. This requires further capacity planning and load testing in the Design phase.
*   **KNOWLEDGE_GAP:** The exact definition of "downtime" for the 99.99% uptime calculation (e.g., does it include planned maintenance windows?) has not been explicitly defined. This should be clarified with the Platform Operator (ACT-0E3EE366E3) and documented in the Compliance, Privacy & Regulatory Obligations artifact.

## 8. Conclusion

This Whole-Product Vision & Scope Definition establishes the foundational constraints and actor model for the Daya (MealCredit) platform. By strictly adhering to the binding compliance rules (Absolute Anonymization, PCI-DSS Level 1, SOC2 Type II) and defining the tripartite actor ecosystem, this document provides the necessary decision foundations for downstream design and implementation phases. All subsequent activities must trace back to these binding rules and scope boundaries.
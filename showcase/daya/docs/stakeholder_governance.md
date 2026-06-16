# Stakeholder Map & Decision Rights

## 1.0 Executive Summary

This artifact establishes the authoritative stakeholder map and decision-rights framework for the Daya MealCredit platform. It maps the nine canonical actor roles to their specific business concerns and system interactions, defines the decision-rights matrix specifying who holds authority for critical actions, and establishes the governance model for the tripartite marketplace. It also identifies unresolved decision axes regarding cross-metro regulatory compliance and data sovereignty that require executive resolution before the platform proceeds to the Design phase.

## 2.0 Canonical Actor Roles & Business Concerns

The following table maps the established actor roles to their primary business concerns and system interactions within the Daya MealCredit platform.

| Actor Role | Primary Business Concern | System Interaction & Obligations |
| :--- | :--- | :--- |
| Donor (ACT-80C62C7814) | Micro-donation funding and impact verification. | Initiates Micro-DonationRound-Ups via Plaid/Stripe; receives immutable receipts within 120 seconds of redemption. |
| Beneficiary (ACT-ADA6716160) | Dignified, stigma-free access to food. | Interacts with the Dignified Redemption Engine (CAP-AEF45AC9BE); receives pseudo-anonymized virtual card tokens. |
| Merchant Partner (ACT-A14D3CDC5D) | Fulfillment of orders and settlement of funds. | Integrates with POS systems (Toast, Clover, Square) via Supply Chain & Fulfillment Orchestration (CAP-B7676E2CFD); receives daily net payouts. |
| NGO Representative (ACT-40FE7F0541) | Beneficiary eligibility and regional liquidity management. | Manages NGO Allocation & Liquidity Management (JNY-FC09C6602B); verifies eligibility without storing PII. |
| Funder (ACT-6517910ADB) | Institutional funding and directed impact flows. | Defines funding preferences and targets via DirectedImpactFlows; monitors high-level impact metrics. |
| Recipient (ACT-DC00FA84DC) | Eligibility verification and voucher acquisition. | Undergoes screening by the Gatekeeper (ACT-AC2B839C3F); acquires vouchers for distribution to Beneficiaries. |
| Service Provider (ACT-6B462E6D21) | Inventory sync and service activation. | Registers business details and connects POS/inventory systems via API; configures transaction routing rules. |
| Platform Administrator (ACT-086A974D63) | Governance, compliance, and system-wide policy. | Manages Admin & Governance (CAP-7028695606); enforces data retention policies and access controls. |
| Platform Operator (ACT-0E3EE366E3) | Operational resilience and incident response. | Monitors system uptime (99.99% target); manages Merchant Failover & Resilience (CAP-3701C64DAE). |
| Dispute Adjudicator (ACT-7BA340FF76) | Independent resolution of transactional conflicts. | Reviews evidence for Dispute Initiation and Evidence Submission (JNY-31E6BD77E9); issues binding resolutions. |

## 3.0 Decision Rights Matrix

The following matrix defines the RACI (Responsible, Accountable, Consulted, Informed) assignments for critical operational and governance decisions. This matrix ensures that the Platform Administrator (ACT-086A974D63) and Platform Operator (ACT-0E3EE366E3) maintain oversight while empowering NGO Representatives (ACT-40FE7F0541) and Merchant Partners (ACT-A14D3CDC5D) to operate within their defined boundaries.

| Decision Area | Description | Responsible | Accountable | Consulted | Informed | Governing Concern |
| --- | --- | --- | --- | --- | --- | --- |
| Beneficiary Eligibility | Approval of Recipient eligibility for MealCredit vouchers based on regional criteria. | NGO Representative (ACT-40FE7F0541) | Platform Administrator (ACT-086A974D63) | Gatekeeper (ACT-AC2B839C3F) | Beneficiary (ACT-ADA6716160) | Absolute Anonymization (CON-5CA3E5A67B) |
| Merchant Onboarding | Approval of Merchant Partner (ACT-A14D3CDC5D) for POS integration and settlement. | Platform Operator (ACT-0E3EE366E3) | Platform Administrator (ACT-086A974D63) | Service Provider (ACT-6B462E6D21) | Funder (ACT-6517910ADB) | PCI-DSS Level 1 (CON-31C0A24105) |
| Fund Allocation | Assignment of Directed Impact Flows to specific regions or merchant types. | Donor (ACT-80C62C7814) | Platform Administrator (ACT-086A974D63) | Funder (ACT-6517910ADB) | NGO Representative (ACT-40FE7F0541) | Marketplace Liquidity (CAP-6A13D9607A) |
| Dispute Resolution | Adjudication of transaction disputes between Merchant and Beneficiary. | Dispute Adjudicator (ACT-7BA340FF76) | Platform Administrator (ACT-086A974D63) | Merchant Partner (ACT-A14D3CDC5D) | Beneficiary (ACT-ADA6716160) | Evidence Chain of Custody (CON-63104E8927) |
| Operational Throttling | Adjustment of Merchant throttle limits to prevent structural overload. | Merchant Partner (ACT-A14D3CDC5D) | Platform Operator (ACT-0E3EE366E3) | System Orchestrator (ACT-F3EDC42DEA) | NGO Representative (ACT-40FE7F0541) | System Resilience (CON-83B6B3C1D2) |
| Compliance & Audit | Review of SOC2 Type II audit evidence and PCI-DSS compliance status. | Platform Operator (ACT-0E3EE366E3) | Platform Administrator (ACT-086A974D63) | External Auditor | All Actors | SOC2 Type II (CON-00789EFED7) |

## 4.0 Unresolved Decision Axes

The following decision axes require executive resolution before the platform can proceed to the Design phase. These gaps are critical for ensuring compliance and operational readiness.

*   **Cross-Metro Regulatory Compliance:** The specific regulatory requirements for charitable giving and digital assets in SF, NYC, and Chicago are not yet fully defined. This is a KNOWLEDGE_GAP: Legal must establish jurisdiction-specific compliance rules before ratification.
*   **Data Sovereignty & Cross-Border Flow:** The rules for data residency and cross-border data flow for multi-metro deployment are not yet defined. This is a KNOWLEDGE_GAP: Legal must establish data sovereignty policies before ratification.
*   **Merchant Partnership Agreements:** The specific terms for merchant partnership agreements, including settlement latency and liability for POS integration failures, are not yet defined. This is a KNOWLEDGE_GAP: Legal must draft partnership agreements before ratification.

## 5.0 Follow-Up Questions

*   **Question:** Who owns exception approval for exports?
*   **Why Critical:** The artifact references an approval path but current truth does not identify the owner.
*   **Answerable:** false
*   **Blocking:** true
*   **Source Role:** refiner
# Risk Register and Operating Constraints

## 1. Executive Summary and Scope

This document establishes the authoritative risk posture and binding operating constraints for the Daya MealCredit platform during the inception phase. It captures the specific risks associated with the tripartite actor model (Donors, Beneficiaries, Merchant Partners) and the financial nature of the product (micro-donations, fractional culinary credits). The register explicitly addresses the critic's concerns regarding data anonymization, financial transaction integrity, and compliance guardrails.

### 1.1 Risk Register

The following risks are identified based on the project's concern surface. Each risk is mapped to its primary actor and journey, with a clear distinction between inherent risk and the required mitigation posture.

| Risk ID | Risk Description | Primary Actor / Journey | Impact Level | Mitigation Strategy / Constraint | Status |
| --- | --- | --- | --- | --- | --- |
| RISK-001 | **Beneficiary Data Re-identification**: Risk that beneficiary PII (legal name, address) is inadvertently stored or logged, violating the core value proposition of absolute anonymization. | Beneficiary / DignifiedRedemption | Critical | **Constraint 1 (Zero-PII Storage)**: Schema validation must reject any payload containing PII fields. Automated data lineage scans must verify no PII columns exist in the Aurora ledger. | Open |
| RISK-002 | **Donor Receipt Correlation**: Risk that donor transactional receipts contain identifying beneficiary parameters, breaking the trust model. | Donor / Micro-DonationRound-Up | High | **Constraint 2 (Strict Separation)**: Receipt generation service must operate in a sandboxed environment with no read-access to beneficiary identity tables. Penetration testing must attempt to correlate receipt data with beneficiary identity. | Open |
| RISK-003 | **Token Misuse / Fraud**: Risk that single-use virtual card tokens are reused, transferred, or used outside designated MCC/location boundaries. | Restaurant (Merchant) / MerchantFulfillment | High | **Constraint 3 (Pseudo-Anonymized Redemption)**: Token generation service must cryptographically bind the token to the MCC and location ID. Transaction logs must be audited to ensure tokens are not reused. | Open |
| RISK-004 | **Financial Overload**: Risk of structural overload on merchant kitchens due to burst traffic, leading to service degradation or double-spending. | Restaurant (Merchant) / MerchantFulfillment | Medium | **Constraint 4 (Financial Throttling)**: Aurora ledger must enforce hard limits on redemption rates per merchant ID. Load testing must simulate burst traffic to verify throttling mechanisms. | Open |
| RISK-005 | **NGO Allocation Governance**: Risk of misallocation of credits due to lack of clear oversight or vetting processes by NGO Administrators. | NGO Administrator / NGOAllocation&Oversight | Medium | **Governance Dependency**: This risk is managed through the NGO Allocation & Oversight journey. Specific vetting protocols and rotation schedules are defined in the Governance artifact. | Open |
| RISK-006 | **POS Integration Latency**: Risk that POS gateway latency exceeds acceptable thresholds, causing redemption failures at the point of sale. | Restaurant (Merchant) / MerchantFulfillment | Medium | **Performance Constraint**: API Responsiveness p99 latency must be below 250ms under 10,000 concurrent connections. Stripe Webhook Processing Latency average must be below 150ms. | Open |

### 1.2 Binding Operating Constraints

The following constraints are binding for all system components, data stores, and external integrations. Violation of these constraints constitutes a critical failure of the platform's core value proposition and regulatory compliance.

**Constraint 1: Zero-PII Storage for Beneficiaries**
Beneficiary Personally Identifiable Information (PII)—including legal names, domestic addresses, and social security numbers—must never be stored on the Daya platform or in production logs. The system must rely on client-side generation of clean, tokenized vouchers that are visually identical to consumer gift cards, ensuring no demographic data crosses into production logs.
*   **Enforcement Mechanism:** Data ingestion pipelines must implement schema validation that rejects any payload containing PII fields for beneficiary records.
*   **Verification:** Automated data lineage scans must verify that no PII columns exist in the Aurora ledger or any downstream analytics stores.

**Constraint 2: Strict Separation of Donor Intent and Beneficiary Identity**
Donor transactional receipts must be immutable and generated within 120 seconds of redemption. These receipts must strictly prohibit the transmission of any identifying beneficiary parameters. Donors must only see the impact of their funds (e.g., 'Meal provided at [Merchant Name]'), never the identity of the recipient.
*   **Enforcement Mechanism:** The receipt generation service must operate in a sandboxed environment with no read-access to beneficiary identity tables.
*   **Verification:** Penetration testing must attempt to correlate donor receipt data with beneficiary identity data; any successful correlation is a critical failure.

**Constraint 3: Pseudo-Anonymized Redemption and Token Locking**
The system must convert micro-donations into single-use virtual card tokens locked to specific Merchant Category Codes (MCC) and location. These tokens must clear via standard banking networks (Stripe Issuing) while stripping PII.
*   **Enforcement Mechanism:** The token generation service must cryptographically bind the token to the MCC and location ID, ensuring the token cannot be used outside the designated scope.
*   **Verification:** Transaction logs must be audited to ensure tokens are not reused or transferred between unrelated MCCs.

**Constraint 4: Financial Throttling and Overload Prevention**
Kitchens (Merchants) must be able to toggle real-time throttle parameters, such as a maximum of 15 MealCredit orders per hour, to prevent structural overload. This constraint ensures that the platform's financial liability remains within manageable bounds during high-demand periods.
*   **Enforcement Mechanism:** The Aurora ledger must enforce hard limits on redemption rates per merchant ID.
*   **Verification:** Load testing must simulate burst traffic to verify that throttling mechanisms activate correctly and do not result in double-spending or ledger inconsistencies.

### 1.3 Compliance Guardrails: PCI-DSS Level 1 and SOC2 Type II

The Daya MealCredit platform processes credit card data via Plaid and Stripe, necessitating strict adherence to PCI-DSS Level 1 standards. Simultaneously, as a fintech platform handling donor funds and merchant payouts, SOC2 Type II structural planning is required to ensure operational security and data integrity over time.

**PCI-DSS Level 1 Structural Planning:**
*   **Scope Definition:** The cardholder data environment (CDE) is strictly limited to the Stripe Issuing and Plaid integration layers. The Daya platform itself must never store, process, or transmit full Primary Account Numbers (PANs). All sensitive authentication data (SAD) must be stripped at the point of entry.
*   **Tokenization Requirement:** Virtual card tokens generated via Stripe Issuing must be treated as the primary financial instrument. The platform must ensure that tokenization is performed by a PCI-compliant provider (Stripe) and that token vaults are never accessed directly by Daya systems.

**SOC2 Type II Structural Planning:**
*   **Confidentiality Control Mapping:** The 'Zero-PII' constraint (Constraint 1) directly supports the SOC2 Confidentiality control objective. By ensuring no PII is stored, the platform minimizes the risk of unauthorized disclosure of confidential beneficiary data.
*   **Security Control Mapping:** The 'Strict Separation' constraint (Constraint 2) supports the SOC2 Security control objective by enforcing least-privilege access to beneficiary identity data.
*   **Availability Control Mapping:** The 'Financial Throttling' constraint (Constraint 4) supports the SOC2 Availability control objective by preventing service degradation due to overload.

### 1.4 Knowledge Gaps and Assumptions

The following items require resolution in subsequent phases or through external research.

*   **KNOWLEDGE_GAP:** Specific regulatory nuances for each of the three initial metropolitan footprints (SF, NYC, Chicago) regarding food assistance program compliance are not yet defined. These must be researched in the Product phase.
*   **KNOWLEDGE_GAP:** Exact KPI thresholds for Merchant Retention Rate (MRR) and Donation-to-Redemption Velocity (DRV) beyond the initial targets (DRV < 14 days) are not yet ratified. These will be defined in the Success Criteria artifact.
*   **ASSUMPTION:** The Aurora ledger is the single source of truth for all credit pool balances and transaction records. This assumption must be validated against the Design phase data model.
*   **ASSUMPTION:** Stripe Issuing API provides sufficient reliability and latency characteristics to support the 150ms average processing latency target. This assumption must be validated through performance testing in the Design phase.

### 1.5 Sibling Artifact References

*   **Product Vision and Scope Definition:** This artifact's scope is bounded by the product vision; see that artifact for the full treatment of user journeys and success criteria.
*   **Success Criteria and Decision Foundations:** This artifact's risk mitigations are aligned with the success criteria; see that artifact for the full treatment of KPIs and decision foundations.
*   **Governance, Compliance, and Privacy Obligations:** This artifact's anonymization constraints are grounded in the governance obligations; see that artifact for the full treatment of compliance and privacy policies.
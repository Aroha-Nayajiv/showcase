# Operating Model and Stakeholder Alignment

## 1. Core Actor Roles and Responsibilities

The platform operates on a strict separation of duties to ensure financial integrity, regulatory compliance, and beneficiary dignity. The following roles are defined based on their functional interaction with the system.

### 1.1 The Operator (Daya Platform)
**Primary Function:** Infrastructure, Compliance, and Liquidity Orchestration.
The Operator owns the core fintech rails, ensuring the integrity of the credit pool and the security of the transaction ledger. The Operator does not interact with beneficiary PII and does not adjudicate social eligibility.

*   **Financial Reconciliation:** Manages the Stripe Custom Connected Accounts and Stripe Issuing virtual card tokens. Ensures that micro-donations from Funders are accurately converted into regional credit pools and that Providers are settled within the 24-hour net payout window.
*   **Compliance and Security:** Enforces PCI-DSS Level 1 standards by never storing raw card data. Maintains the append-only cryptographic audit trail in Amazon Aurora Serverless v2 for SOC2 Type II auditing. Manages multi-tenant data segregation across SF, NYC, and Chicago footprints.
*   **Platform Governance:** Configures and enforces business rules, such as the 72-hour credit expiration rollback and Merchant Category Code (MCC) restrictions to prevent ineligible purchases (e.g., alcohol). Manages the automated regulatory reporting generation.
*   **Dispute Resolution:** Reviews flagged transactions and chargebacks via the immutable ledger. Authorizes financial reversals via Stripe Connect based on cryptographic token signatures, without accessing beneficiary identity data.

### 1.2 The Facilitator (NGO Partner)
**Primary Function:** Beneficiary Credentialing and Dignity Preservation.
The Facilitator is the trusted social intermediary that bridges the gap between vulnerable populations and the digital platform. Their role is strictly limited to social vetting and profile management, operating under a "cryptographic profile" model that eliminates the need for state IDs or SSNs on the platform.

*   **Eligibility and Onboarding:** Submits digital identity and proof of organizational legitimacy to the Operator. Creates anonymous profiles for Recipients using a tiered onboarding system. Assigns eligibility tiers based on local social needs, not financial creditworthiness.
*   **Profile Management:** Manages the lifecycle of Recipient profiles, including rotation of vulnerable populations. Ensures that beneficiary demographic status, legal name, and domestic background are never transmitted to the Operator or stored in production logs.
*   **Community Liaison:** Acts as the primary point of contact for Recipients facing technical barriers, providing support for the digital voucher interface (tokenized pass) without compromising the anonymity of the Funder.

### 1.3 The Provider (Restaurant Partner)
**Primary Function:** Service Fulfillment and POS Integration.
The Provider is a commercial entity (Restaurant) that accepts MealCredits as a form of payment. They are integrated into the platform via low-friction POS integrations (Toast, Clover, Square) or an edge dashboard.

*   **Service Readiness:** Submits business details and POS integration credentials for verification. Configures payment settlement endpoints to receive automated daily net payouts.
*   **Transaction Clearing:** Scans the Recipient's digital token/barcode at the POS terminal. The platform performs a real-time authorization check against the credit pool balance. The Provider receives immediate settlement confirmation.
*   **Operational Throttling:** Manages real-time throttle parameters (e.g., maximum 15 MealCredit orders per hour) to prevent structural overload during peak dining times. Toggles availability based on inventory and capacity.

### 1.4 The Funder (Donor)
**Primary Function:** Liquidity Provision and Impact Transparency.
The Funder provides the financial capital for the platform, typically through micro-donation round-ups via Plaid/Stripe. They require absolute transparency regarding the impact of their contributions without seeing the identity of the Recipient.

*   **Funding Configuration:** Links external banking sources and configures donation rules (directed to specific regions/merchants or pool-based). The platform processes recurring contributions and allocates equivalent digital credit units to regional pools.
*   **Impact Receipting:** Receives immutable transactional receipts within a 120-second latency window of a Recipient's redemption. These receipts confirm fund transfer and pool balance updates without transmitting any identifying beneficiary parameters.
*   **Data Export:** Submits requests for historical impact reporting. The platform processes anonymized aggregate data generation complying with privacy standards (CCPA/GDPR), providing secure download links for audit purposes.

### 1.5 The Recipient (Beneficiary)
**Primary Function:** Dignified Service Redemption.
The Recipient is the end-user of the social impact service. Their interaction with the platform is designed to be indistinguishable from a standard consumer gift card experience, ensuring absolute anonymity and zero social stigma.

*   **Credential Management:** Receives a digital voucher interface (tokenized pass) linked to their anonymous ID. Views available service providers near their location, sorted by distance and dietary flags.
*   **Redemption:** Presents the digital token/barcode at the Provider location. The token is consumed upon successful clearing, and the balance is updated in real-time.
*   **Privacy Protection:** Benefits from absolute PII anonymization. Their demographic status and legal identity are never exposed to Funders, Providers, or the Operator's transaction logs.

## 2. Critical Interaction Flows

### 2.1 Facilitator-Mediated Recipient Onboarding and Credentialing
This flow establishes the Recipient's identity within the system while preserving absolute anonymity from Funders and Providers.

1.  **Profile Creation:** The Facilitator submits a digital identity and proof of organizational legitimacy via the admin portal. The platform generates a unique, high-entropy UUIDv4 for the Recipient, ensuring no PII is stored.
2.  **Credentialing and Vetting:** The Operator reviews the Facilitator's documentation against compliance criteria and performs background checks. Upon approval, the Operator generates unique access keys and activates the Facilitator role.
3.  **Eligibility Assignment:** The Facilitator assigns an eligibility tier to the Recipient based on local needs. This tier determines the credit allocation rules (e.g., daily limits, expiration windows).
4.  **Token Issuance:** The platform generates a single-use, pseudo-anonymized virtual card token (via Stripe Issuing) linked to the Recipient's anonymous ID. This token is pushed to the Recipient's device as a digital pass (Apple/Google Wallet) or a secure QR code.

### 2.2 Operator-Mediated Provider Activation and Settlement
This flow ensures Providers are legitimate, compliant, and financially settled.

1.  **Provider Onboarding:** The Provider submits business details and POS integration credentials (e.g., Toast, Clover, Square) for verification.
2.  **Verification and Configuration:** The Operator verifies the business status, confirms the MCC is eligible for culinary credits, and configures the payment settlement endpoints via Stripe Connect.
3.  **Catalogue Sync and Activation:** The platform activates the Provider, syncs their menu catalogue, and marks them as available in the discovery layer for Recipients.
4.  **Settlement Execution:** After a transaction clears, the Operator's automated system triggers a net payout to the Provider's business checking account within 24 hours, ensuring liquidity for the merchant.

### 2.3 Facilitator-Mediated Dispute Resolution and Eligibility Management
The Facilitator acts as the first line of support for Recipients, handling issues that require human judgment without compromising anonymity.

1.  **Issue Reporting:** A Recipient reports an issue (e.g., token not working, Provider refusal) to the Facilitator.
2.  **Investigation:** The Facilitator reviews the Recipient's transaction history (anonymized) and logs the issue in the admin portal.
3.  **Operator Escalation:** If the issue involves a financial discrepancy or potential fraud, the Facilitator escalates the case to the Operator. The Operator reviews the immutable append-only ledger audit log and offline cryptographic token signatures to verify transaction validity.
4.  **Resolution:** The Operator authorizes any necessary financial reversals via Stripe Connect, updates the regional credit pool balance, and notifies the Provider of the resolution status. The Facilitator communicates the outcome to the Recipient without revealing internal platform mechanics.

## 3. Governance Framework and Decision Rights

The governance model is structured to balance the speed of a fintech marketplace with the rigorous compliance requirements of social-impact financial services. Decision rights are assigned based on the domain of impact: financial, operational, or compliance.

### 3.1 Decision Authority Matrix

| Decision Domain | Scope | Primary Authority | Consulted | Informed |
| :--- | :--- | :--- | :--- | :--- |
| **Financial Liquidity** | Credit pool allocation rules, expiration policies (72h rollback), and micro-donation round-up thresholds. | Platform Operator | Finance Lead, NGO Facilitators | Donors, Merchant Partners |
| **Compliance & Risk** | PCI-DSS Level 1 adherence, SOC2 Type II audit readiness, and beneficiary data anonymization standards. | Platform Operator | Legal/Compliance Advisor | All Stakeholders |
| **NGO Credentialing** | Approval of NGO Facilitator digital identities and proof of organizational legitimacy. | NGO Facilitator | Platform Operator | Beneficiaries |
| **Merchant Onboarding** | Verification of Provider business status, POS integration credentials, and settlement endpoint configuration. | Platform Operator | Legal/Compliance Advisor | Merchant Partners |
| **Dispute Resolution** | Authorization of financial reversals (chargebacks) and resolution of Provider-initiated refund requests. | Platform Operator | Finance Lead | Provider, Donor |

### 3.2 Escalation Paths

1.  **Operational Escalation:** Issues related to POS integration latency or credit pool exhaustion are escalated from the Platform Operator to the Engineering Lead for immediate system intervention.
2.  **Compliance Escalation:** Any potential breach of PCI-DSS Level 1 standards or unauthorized PII exposure is immediately escalated to the Legal/Compliance Advisor and the Platform Operator for containment and audit.
3.  **Strategic Escalation:** Decisions affecting the multi-tenant architecture across SF, NYC, and Chicago, or changes to the core business model (e.g., introducing direct cash disbursement), require approval from the Executive Sponsor.

### 3.3 Reputational and Social Risks

*   **Stigma and Anonymity Breach:**
    *   **Description:** Any failure in the absolute anonymization of Beneficiary data (e.g., PII leakage in logs, UI glitches revealing identity) would cause severe reputational damage and undermine the core value proposition of "dignity by design."
    *   **Impact:** Critical. Existential risk to the platform's mission and user trust.
    *   **Mitigation Obligation:** Enforce absolute PII anonymization at the code and infrastructure level. Conduct regular security audits and penetration testing.
    *   **Knowledge Gap:** The specific technical controls for ensuring "absolute anonymization" in the mobile app (e.g., SecureStore encryption standards) are partially defined but require validation against the chosen framework (Expo v51/React Native). `KNOWLEDGE_GAP: Validate SecureStore encryption standards and data retention policies for the mobile app to ensure absolute PII anonymization.`

*   **NGO Partner Trust and Adoption:**
    *   **Description:** NGOs may be hesitant to adopt the "cryptographic profile" onboarding process if they perceive it as overly complex or if they require more control over beneficiary data than the platform allows.
    *   **Impact:** High. Slows down Beneficiary acquisition and limits platform scale.
    *   **Mitigation Obligation:** Provide clear documentation and training for NGO Facilitators. Emphasize the benefits of reduced administrative burden and enhanced security.
    *   **Knowledge Gap:** The specific KPIs for NGO adoption success in the first 6 months are not yet defined. `KNOWLEDGE_GAP: Define KPIs for NGO adoption success, including onboarding completion rate, active facilitator count, and beneficiary enrollment rate.`

### 3.4 Knowledge Gaps

*   **NGO Adoption KPIs:** The specific KPIs for NGO adoption success in the first 6 months are not yet defined. Owner: Product Lead; Evidence Needed: Market research on NGO engagement metrics.
*   **Legal Structure for Intermediary Role:** The specific legal structure for the intermediary role between donors, NGOs, and restaurants to minimize liability is not yet defined. Owner: Legal/Compliance Advisor; Evidence Needed: Legal opinion on fintech intermediary liability.
*   **Minimum Viable Transaction Volume:** The minimum viable transaction volume to sustain merchant participation before achieving network effects is not yet defined. Owner: Finance Lead; Evidence Needed: Financial modeling of unit economics.

### 3.5 Assumptions

*   **ASSUMPTION: NGO Facilitator Trust:** It is assumed that local NGOs will be willing to adopt the 'cryptographic profile' onboarding process without requiring state IDs, based on their existing trust relationships with vulnerable populations. Owner: NGO Relations Lead; Evidence Needed: Pilot program feedback.
*   **ASSUMPTION: Merchant POS Integration:** It is assumed that commercial restaurants in the initial 3-city rollout (SF, NYC, Chicago) will have POS systems compatible with the low-friction integration (Toast/Clover/Square) or edge dashboard. Owner: Engineering Lead; Evidence Needed: POS vendor API documentation.

## 4. Decision Foundations and Open Questions

The following decisions are critical for the operating model and require resolution before the next phase.

1.  **Minimum Viable Transaction Volume:** What is the minimum viable transaction volume to sustain merchant participation before achieving network effects? `ASSUMPTION: Initial target is 50 transactions per merchant per week to ensure viability.`
2.  **Legal Structure:** How do we legally structure the intermediary role between donors, NGOs, and restaurants to minimize liability? `KNOWLEDGE_GAP: Legal counsel must define the optimal legal structure (e.g., DAO, LLC, Non-Profit subsidiary) for the intermediary role.`
3.  **NGO Adoption KPIs:** What are the specific KPIs for NGO adoption success in the first 6 months? `KNOWLEDGE_GAP: Define KPIs for NGO adoption success, including onboarding completion rate, active facilitator count, and beneficiary enrollment rate.`

## 5. Cross-Reference to Sibling Artifacts

*   **Risk Register:** Detailed risk mitigation strategies and ownership are further elaborated in the inception_risk_constraints artifact.
*   **Compliance Governance:** Specific compliance requirements and audit procedures are defined in the inception_compliance_governance artifact.
*   **Decision Foundations:** Open questions and decision trade-offs are tracked in the inception_decision_foundations artifact.

## 6. Interaction Boundaries and Data Flow

The following matrix defines the data exchange boundaries between actors. No PII crosses the boundary between the Operator and the Recipient/Facilitator except for anonymous UUIDs and eligibility tiers.

| Interaction Pair | Data Exchanged | Privacy/Security Constraint | Governance Owner |
| :--- | :--- | :--- | :--- |
| **Operator <-> Facilitator** | NGO Legitimacy, Recipient Anonymous ID, Eligibility Tier | No PII (Name/SSN) crosses the boundary. Cryptographic profile only. | Operator validates; Facilitator creates. |
| **Operator <-> Provider** | POS Credentials, Settlement Endpoints, Transaction Tokens | No Recipient PII. Token is locked to MCC/Location. | Operator issues; Provider consumes. |
| **Operator <-> Funder** | Banking Source, Donation Rules, Impact Receipts | No Recipient Identity. Receipts are aggregate/anonymized. | Funder configures; Operator reports. |
| **Facilitator <-> Recipient** | Eligibility, Voucher Access, Support | No Funder Identity. Dignity-preserving interface. | Facilitator manages; Recipient uses. |
| **Provider <-> Recipient** | Order Details, Token Scan | No Funder Identity. No Recipient PII in logs. | Provider fulfills; Recipient redeems. |

## 7. Conclusion and Next Steps

This Operating Model and Stakeholder Alignment document provides the structural framework for the MealCredit platform. It defines the decision rights, operational boundaries, and compliance controls necessary to support the tripartite marketplace. The next steps involve resolving the identified knowledge gaps and ratifying the operating model with key stakeholders (Legal, Operations, Product). Once ratified, the model will serve as the foundation for the Design phase, where technical contracts and implementation details will be developed.

The operating model ensures that MealCredit can scale to 50,000 MAU while maintaining the highest standards of security, privacy, and compliance. By aligning stakeholders around a clear governance framework, we can mitigate risks and ensure a successful launch across SF, NYC, and Chicago.

---

## 8. Executive Summary

This document establishes the structural and operational framework for the **MealCredit** platform (product name: Daya). It defines the roles, responsibilities, and interactions of the five core actors: **Funder**, **Recipient**, **Provider**, **Facilitator**, and **Operator**. The operating model is designed to decouple food assistance from social stigma by converting real-time financial micro-donations into fractional, anonymous culinary credits. The platform targets a scale of 50,000 Monthly Active Users (MAU) across three initial metropolitan footprints: San Francisco, New York City, and Chicago.

The core operational constraint is the absolute separation of financial identity (Funder) and beneficiary identity (Recipient), mediated by the NGO Facilitator who acts as the sole trusted entity for beneficiary credentialing. This model ensures strict adherence to PCI-DSS Level 1 and SOC2 Type II compliance requirements while maintaining the dignity and anonymity of Recipients.
# Contributor Funding Mechanics

## 1. Product Overview

This artifact defines the product rules, user journeys, and acceptance criteria for the Contributor (ACT-2A20B038B1) funding ecosystem. The primary objective is to decouple food assistance from social stigma by converting real-time financial micro-donations into fractional, anonymous culinary credits. The platform mission is to connect Contributors, Beneficiaries (Recipients), and Merchant Partners (Restaurants) through local non-profit organizations (NGOs).

The Contributor funding flow is the engine of the MealCredit marketplace. It must provide a frictionless, low-friction onboarding experience that converts donor intent into liquid credits within three steps, while strictly adhering to PCI-DSS Level 1 and SOC2 Type II compliance standards. Success requires a seamless integration with external payment gateways (Plaid for bank linking, Stripe for payment processing) to ensure secure, automated funding.

## 3. Primary Journeys

### 3.1 Contributor Onboarding & Funding (JNY-A9C1EB1FCC)

This journey outlines the end-to-end experience for the Contributor (ACT-2A20B038B1) from account creation to the first successful funding of the credit pool.

**Step 1: Account Creation & Identity Verification**
*   **Action:** The Contributor creates an account using email or social login. The system initiates identity verification to comply with financial regulations.
*   **Product Rule:** Identity verification must be completed via a secure, third-party KYC (Know Your Customer) provider integrated with the Compliance & Audit Governance (CAP-421F3AD853) capability. No raw PII is stored on-platform beyond what is strictly required for KYC compliance.
*   **Dignity Check:** The onboarding flow is branded as a general financial contribution platform, not a "food aid" application, to maintain the dignity of all actors.

**Step 2: Payment Method Linking (Plaid Integration)**
*   **Action:** The Contributor links their external financial identity (bank account or credit card) using Plaid for secure bank linking.
*   **Product Rule:** The system must use Plaid's secure tokenization to ensure zero raw credit card data touches application servers (PCI-DSS Level 1 compliance). The Contributor must explicitly authorize the linking of their financial instrument.
*   **Error Handling:** If the bank link fails, the system logs the error and pauses the funding cycle without exposing raw decline reasons. The Contributor is prompted to update the payment method.

**Step 3: Funding Configuration**
*   **Action:** The Contributor configures their funding preferences, choosing between "Round-Up" donations or "Fixed-Amount" contributions.
*   **Product Rule:** The system must allow Contributors to set auto-funding rules (e.g., round up every transaction to the nearest dollar, or donate $5 weekly). Contributors can also assign funds globally, regionally by zip code, or to specific merchant property types (Directed Impact Flows).
*   **Success Criteria:** The Contributor receives a confirmation notification that their funding cycle is active.

### 3.2 Contributor Primary Transaction Flow (JNY-4FC1874968)

This journey details the automated calculation and transfer of funds from the Contributor (ACT-2A20B038B1) to the central credit pool.

**Step 1: Transaction Monitoring & Calculation**
*   **Action:** The system monitors linked external transactions via Plaid webhooks or triggers scheduled donations based on the Contributor's configuration.
*   **Product Rule:** The platform calculates the fractional contribution based on the configured rules (e.g., round-up amount or fixed sum). This calculation must occur in real-time or at the scheduled interval with high precision.
*   **Directed Impact:** If the Contributor has specified a Directed Impact Flow, the system tags the incoming funds with the designated region or merchant type for allocation by the Discovery & Allocation Engine (CAP-264DA83096).

**Step 2: Fund Transfer to Credit Pool**
*   **Action:** Funds are transferred to the central credit pool via Stripe Issuing/Processing.
*   **Product Rule:** The transfer must be atomic and idempotent to prevent double-charging or lost funds. The system must maintain an append-only, cryptographic audit ledger in Aurora Postgres (CON-199A4FEDC7) for all financial transactions.
*   **Anonymization:** The transfer is mapped to a high-entropy UUIDv4 key to ensure absolute anonymization of the Contributor's identity in downstream analytics (CON-9DEA275205).

**Step 3: Immutable Receipt Generation**
*   **Action:** The Contributor receives an immutable transactional receipt within 120 seconds of the donation.
*   **Product Rule:** The receipt must confirm the amount donated, the timestamp, and the impact (e.g., "This donation provides 2 meals"). It must strictly prohibit the transmission of any identifying beneficiary parameters.
*   **Success Criteria:** Donation-to-Redemption Velocity (DRV) is tracked, ensuring the funds are utilized effectively within the target timeframe (under 14 days).

### 3.3 Contributor Error & Recovery (JNY-CF7DEC4F04)

This journey covers scenarios where funding attempts fail or require manual intervention.

**Step 1: Payment Failure Detection**
*   **Action:** A payment attempt fails due to insufficient funds, bank rejection, or network error.
*   **Product Rule:** The system logs the error and pauses the recurring funding cycle. The Contributor is notified via push notification and email with a clear, non-technical explanation (e.g., "Payment failed. Please update your payment method.").

**Step 2: User Remediation**
*   **Action:** The Contributor updates their payment method or resolves the bank issue.
*   **Product Rule:** The system must allow the Contributor to retry the failed transaction or resume the recurring cycle with the new payment method. No manual intervention from the Operator (ACT-FE96DD3975) is required for standard payment failures.

**Step 3: Cycle Resumption**
*   **Action:** Upon successful validation of the new payment method, the funding cycle resumes automatically.
*   **Product Rule:** The system must backfill any missed scheduled donations if the Contributor has configured "catch-up" rules, or skip them if configured as "skip-on-failure".

## 4. Feature Specifications & Acceptance Criteria

### 4.1 Round-Up Donation Logic

**Description:** Allows Contributors to automatically donate the fractional change from their everyday purchases.

**Acceptance Criteria:**
1.  **AC-1.1:** The system must integrate with Plaid to monitor linked transaction feeds in near real-time.
2.  **AC-1.2:** The system must calculate the round-up amount (e.g., $4.50 coffee -> $0.50 round-up) with cent-level precision.
3.  **AC-1.3:** The Contributor must be able to toggle round-up donations on/off at any time via the mobile app.
4.  **AC-1.4:** Round-up amounts must be batched and transferred to the credit pool at a configurable frequency (e.g., daily or weekly) to minimize transaction fees.
5.  **AC-1.5:** The Contributor must receive a weekly summary of their round-up contributions, including total amount donated and estimated meals provided.

### 4.3 Payment Gateway Integration (Plaid & Stripe)

**Description:** Secure integration with external financial services to facilitate funding.

**Acceptance Criteria:**
1.  **AC-3.1:** The system must use Plaid's Link SDK for secure bank account linking, ensuring no raw banking credentials are stored on-platform.
2.  **AC-3.2:** The system must use Stripe Elements and SDK for payment processing, ensuring zero raw credit card data touches application servers (PCI-DSS Level 1 compliance).
3.  **AC-3.3:** The system must handle Stripe webhooks reliably, with a target average processing latency below 150ms (CON-D792CA1810).
4.  **AC-3.4:** The system must implement idempotency keys for all payment intents to prevent duplicate charges in case of network retries.
5.  **AC-3.5:** The system must log all infrastructure and administrative changes to AWS CloudTrail (CON-0B2D40801A) for auditability.

### 4.4 Fund Allocation & Directed Impact

**Description:** Allows Contributors to direct their funds to specific regions, zip codes, or merchant types.

**Acceptance Criteria:**
1.  **AC-4.1:** The Contributor must be able to select "Global" (default), "Regional" (by zip code), or "Merchant Type" (e.g., healthy grocery partners) when configuring their funding.
2.  **AC-4.2:** The system must tag incoming funds with the selected allocation criteria and pass this metadata to the Discovery & Allocation Engine (CAP-264DA83096).
3.  **AC-4.3:** The system must provide Contributors with visibility into where their directed funds are being utilized (e.g., "Your $20 donation was used at 3 restaurants in Chicago").
4.  **AC-4.4:** If a directed fund cannot be fulfilled within a reasonable timeframe, the system must notify the Contributor and offer to re-allocate the funds globally.

### 4.5 PCI-DSS Level 1 Compliance
*   **Constraint:** Zero raw credit card data may touch application servers. All payment data must be tokenized via Stripe Elements and SDK.
*   **Enforcement:** The mobile app must never store or log raw card numbers. All payment intents must be created server-side using Stripe's API with secure keys.

### 4.6 SOC2 Type II Control Environments
*   **Constraint:** The system must operate within SOC2 Type II control environments, generating detailed tracking logs for all infrastructure and administrative changes.
*   **Enforcement:** All funding transactions, user actions, and system events must be logged to an append-only, cryptographic audit ledger in Aurora Postgres (CON-199A4FEDC7). Logs must be pushed to AWS CloudTrail (CON-0B2D40801A).

### 4.7 Absolute Anonymization
*   **Constraint:** Beneficiary demographic data must be strictly off-platform. The platform stores only derived, anonymized credits.
*   **Enforcement:** All Contributor transactions are mapped to high-entropy UUIDv4 keys. No PII (legal name, domestic background) is stored on-platform or in production logs. Receipts must not contain any identifying information about the Recipient (ACT-DC00FA84DC).

## 5. Unresolved Decisions & Knowledge Gaps

### 5.1 Directed Impact Real-Time Filtering
*   **Knowledge Gap:** Does the 'Directed Impact Flow' require real-time filtering of eligible merchants at the point of donation, or can it be processed asynchronously with a batch-settlement mechanism for unfulfilled directed funds?
*   **Impact:** This decision affects the latency of the Contributor Primary Transaction Flow and the complexity of the Discovery & Allocation Engine (CAP-264DA83096).
*   **Owner:** Product Strategy / Technical Architecture

### 5.2 Round-Up Batching Threshold
*   **Knowledge Gap:** What is the optimal minimum batch threshold for round-up donations to minimize Stripe transaction fees while maintaining the perception of real-time impact for the Contributor?
*   **Impact:** A low threshold increases fee overhead; a high threshold delays impact visibility.
*   **Owner:** Product Strategy / Finance

### 5.3 KYC Provider Selection
*   **Knowledge Gap:** Which specific KYC provider will be integrated for Contributor identity verification, and what are the associated latency and cost implications?
*   **Impact:** This affects the onboarding flow duration and compliance posture.
*   **Owner:** Compliance / Technical Architecture

## 6. Success Metrics

*   **Donation-to-Redemption Velocity (DRV):** Target under 14 days.
*   **Contributor Retention Rate (CRR):** Measured month-over-month.
*   **Stripe Webhook Processing Latency:** Target average below 150ms.
*   **API Responsiveness:** p99 latency below 250ms under 10,000 concurrent connections.
*   **Operational Uptime:** 99.99% across AWS multi-AZ configurations.

## 7. Accessibility & UX Requirements

*   **WCAG 2.1 AA Compliance:** All UI elements in the Contributor funding flow must meet contrast ratios, text resizing, and screen reader compatibility standards.
*   **Low-Vision Support:** High-contrast modes and large touch targets must be available for all funding configuration screens.
*   **Language Support:** The interface must support multiple languages based on the user's profile or device settings.
*   **Dignity Check:** The Contributor interface must not stigmatize the Recipient (ACT-DC00FA84DC). All impact messaging must focus on the Contributor's positive action, not the Recipient's need.

## 8. Error Handling & Edge Cases

*   **Payment Decline:** If a payment is declined, the system must pause the funding cycle and notify the Contributor. The system must not retry automatically without user confirmation to prevent overdrafts.
*   **Network Timeout:** If the funding request times out, the system must check the status with the payment gateway before confirming success or failure to the Contributor.
*   **Insufficient Funds:** If the Contributor's linked account has insufficient funds, the system must notify the Contributor and pause the cycle until funds are available or a new payment method is added.
*   **Duplicate Transaction:** The system must use idempotency keys to prevent duplicate charges in case of network retries or user double-clicks.

## 9. Integration with Sibling Artifacts

*   **Discovery & Allocation Engine (CAP-264DA83096):** Contributor funds tagged with Directed Impact Flows are passed to this capability for allocation to eligible Merchant Partners (ACT-A14D3CDC5D).
*   **Compliance & Audit Governance (CAP-421F3AD853):** All Contributor funding transactions are logged to the audit ledger for SOC2 Type II compliance.
*   **Identity & Access Management (CAP-361A59708B):** Contributor onboarding and KYC are handled by this capability.
*   **Financial Transaction Processing (CAP-9CD814929D):** The actual transfer of funds from the Contributor to the credit pool is executed by this capability via Stripe.

## 10. Future Scope (Out of Scope for MVP)

*   **Advanced Analytics Dashboard:** Detailed insights into Contributor impact and donation patterns.
*   **Multi-Currency Expansion:** Support for non-USD currencies in initial metro footprints.
*   **Corporate Sponsorship Flows:** Bulk funding mechanisms for corporate partners.

## 11. Conclusion

This artifact defines the product rules for the Contributor (ACT-2A20B038B1) funding mechanics, ensuring a secure, compliant, and dignified experience for donors. By integrating Plaid and Stripe, enforcing PCI-DSS Level 1 and SOC2 Type II standards, and providing clear, impact-driven journeys, the platform will successfully convert donor intent into liquid credits for the MealCredit ecosystem. The unresolved decisions identified in Section 6 must be addressed by the Technical Architecture and Product Strategy teams before the Design phase begins.
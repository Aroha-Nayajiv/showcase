# Restaurant Partner Onboarding & POS Integration

This artifact defines the product requirements for the Restaurant Partner (Provider) lifecycle within the MealCredit ecosystem. It covers Provider Activation and Service Readiness, the MerchantFulfillmentFlow (POS integration and clearing), and the operational controls required to maintain PCI-DSS Level 1 compliance and absolute PII anonymization.

## 1. Provider Activation and Service Readiness

This section defines the user stories and acceptance criteria for the initial onboarding of Merchant Partners. The goal is to verify business legitimacy and securely ingest POS credentials without exposing beneficiary data.

### 1.1 User Stories

#### US-1.1: Merchant Onboarding and KYC Verification
As a Provider, I want to submit my business details and proof of organizational legitimacy via the Merchant Portal, so that the Operator can verify my eligibility to participate in the MealCredit network.

**Acceptance Criteria:**
1. The Provider navigates to the "Onboarding" section of the Merchant Portal.
2. The Provider enters business registration details (Legal Name, Tax ID/EIN, Business Address).
3. The Provider uploads required documentation (e.g., Business License, Food Service Permit) via a secure, encrypted upload endpoint.
4. The system assigns a status of "Pending Verification" to the application.
5. Constraint: No beneficiary PII is collected or stored during this phase. All data is encrypted at rest and in transit.

#### US-1.2: POS Credentialing and Integration
As a Provider, I want to securely link my existing POS system (Toast, Clover, or Square) to the MealCredit platform, so that I can accept culinary credits without installing new hardware or learning a new interface.

**Acceptance Criteria:**
1. The Provider selects their POS provider (Toast, Clover, or Square) from a supported list.
2. The system initiates a secure OAuth 2.0 handshake with the selected POS provider's API to request necessary permissions (read menu, process payments).
3. Upon successful authorization, the system automatically ingests the restaurant's current menu catalog, mapping internal menu items to the platform's Merchant Category Code (MCC) requirements.
4. The Provider receives a visual confirmation in the dashboard stating: "POS Integration Active. You are now ready to accept MealCredits."
5. Constraint: POS credentials are stored in an encrypted vault compliant with PCI-DSS Level 1 standards.

#### US-1.3: Operational Throttle Configuration
As a Provider, I want to set real-time throttle parameters for MealCredit orders, so that I can prevent structural overload during peak hours while maintaining service quality.

**Acceptance Criteria:**
1. The Merchant Dashboard includes a "MealCredit Settings" section.
2. The Provider can toggle a "Max MealCredit Orders Per Hour" slider or input field.
3. The system enforces this limit in real-time; if the limit is reached, the POS integration returns a specific "Throttle Limit Reached" status to the beneficiary's app, preventing further redemptions at that location for the duration of the hour.
4. The Provider can view a real-time counter of active MealCredit orders processed in the current hour.

## 2. MerchantFulfillmentFlow: Service Redemption and Clearing

This section defines the operational requirements for the Provider during the redemption process. The core objective is to ensure that the POS interaction is seamless, secure, and strictly anonymous.

### 2.1 Persona: Provider (Restaurant Partner)
**Goal:** Process a MealCredit redemption at the POS terminal with zero friction, ensuring the transaction clears against the regional credit pool without exposing any beneficiary identity or demographic data.

#### US-2.1: Token Ingestion and Validation
As the POS System, I must ingest the MealCredit token and validate it against the ledger in real-time to prevent double-spending and ensure fund availability.

**Acceptance Criteria:**
1. The restaurant's POS terminal (or edge dashboard) scans the beneficiary's barcode or reads the Wallet pass.
2. The POS system sends the token to the MealCredit validation endpoint.
3. The system validates the token's cryptographic signature, checks the regional credit pool balance, and verifies that the token has not been previously consumed.
4. If valid, the system reserves the funds and returns a "Success" status to the POS, allowing the transaction to complete.
5. If invalid (expired, insufficient funds, or already used), the system returns a clear "Declined" status with a generic error message (e.g., "Payment Declined") to the POS, without revealing the specific reason to the merchant or beneficiary to protect anonymity.

#### US-2.2: Ineligible Purchase Interception
As the POS System, I must ensure that ineligible items (e.g., alcohol, non-food merchandise) are dropped at the Stripe network layer before the merchant receipt prints.

**Acceptance Criteria:**
1. The POS system sends the order details to the MealCredit validation endpoint.
2. The system checks the order items against the MCC restrictions and ineligible category list.
3. If ineligible items are detected, the system returns a "Declined - Ineligible Items" status to the POS.
4. The POS system displays a generic "Payment Declined" message to the beneficiary, protecting their anonymity.
5. Constraint: The POS system must not log or display the specific reason for the decline to the beneficiary.

#### US-2.3: Settlement Confirmation
As the Provider, I want to receive a settlement confirmation notification for each cleared transaction, so that I can reconcile my daily sales.

**Acceptance Criteria:**
1. Upon successful validation, the system triggers a settlement confirmation via Stripe Connect.
2. The Provider receives a notification in the Merchant Dashboard confirming the transaction amount and timestamp.
3. The system generates an immutable audit trail entry for regulatory reporting requirements.
4. Constraint: The settlement confirmation must not include any beneficiary PII or identifying information.

### 2.2 PII Anonymization Constraints
**Goal:** Ensure that the POS interaction is indistinguishable from a standard consumer gift card transaction, preventing any social bias or tracking of the beneficiary.

1. The POS system must never receive or store beneficiary PII (Name, DOB, Address, SSN).
2. The MealCredit token must be a single-use, pseudo-anonymous virtual card token generated via Stripe Issuing.
3. The token must be locked to the specific MCC and location ID of the restaurant.
4. The token must contain no PII, no beneficiary name, and no internal user ID.
5. Constraint: All beneficiary demographic data must be irreversibly anonymized before any data crosses the POS integration boundary.

### 3.1 Edge Cases

**Edge Case: Offline Token Validation**
*   **Scenario:** The POS system loses connectivity to the MealCredit validation endpoint.
*   **Response:** The POS system falls back to a cached list of valid token prefixes or a local edge validation rule. The merchant is notified via a non-intrusive dashboard alert that "Offline Mode Active" and that transactions are being queued for later settlement. Once connectivity is restored, the system automatically synchronizes the queued transactions with the central ledger.
*   **Constraint:** Offline-validated tokens must be strictly single-use and cannot be replayed.

**Edge Case: Dispute Resolution**
*   **Scenario:** A merchant claims they did not receive the offline token verification.
*   **Response:** The Platform Admin must be able to review the immutable append-only ledger audit log and offline cryptographic token signature to verify transaction validity without accessing beneficiary PII. The Admin can then authorize a financial reversal via Stripe Connect if the transaction is found to be invalid.

**Edge Case: Lost or Stolen Virtual Card**
*   **Scenario:** A beneficiary reports a lost or stolen virtual card.
*   **Response:** The system must immediately invalidate the token in the SecureStore and the central ledger. The NGO Facilitator must be able to issue a new token to the beneficiary without requiring a new onboarding process.

### 3.2 Knowledge Gaps & Assumptions

**KNOWLEDGE_GAP:** POS Provider API Specifics - The exact API endpoints and error codes for Toast, Clover, and Square POS integrations must be established by the Design phase. The product spec assumes standard OAuth 2.0 flows and webhook capabilities, but specific implementation details (e.g., how to handle partial refunds or voids) need to be mapped to each provider's unique API.

**ASSUMPTION:** Offline Validation Mechanism - It is assumed that a localized, cryptographically signed token can be validated by the POS system without a real-time connection to the central ledger. This requires the POS system to have a secure, up-to-date copy of the public key or validation rules. Evidence needed: Verification of offline validation feasibility with the selected POS providers.

**KNOWLEDGE_GAP:** Settlement Thresholds - The minimum payout threshold for automated daily net payouts via Stripe Connect has not been established. This needs to be defined to ensure compliance with financial regulations and to manage cash flow for both the platform and the merchants.

**ASSUMPTION:** Throttle Limit Impact - It is assumed that a "Max MealCredit Orders Per Hour" throttle will not significantly impact the merchant's overall revenue or customer satisfaction. Evidence needed: Merchant feedback on acceptable throttle limits during peak hours.

## 4. Cross-References

*   **Beneficiary Discovery & Redemption Journey:** This artifact defers to the sibling artifact for the full treatment of the token generation and offline redemption mechanics.
*   **Identity, Access & Offline Capability Foundation:** This artifact assumes that the Recipient's location data is handled in compliance with the privacy and anonymization standards defined in the sibling artifact.
*   **Operator Governance and Monitoring:** This artifact assumes that the Operator has the tools to monitor DRV, Credit Pool Utilization, and system metrics as defined in the sibling artifact.

## 5. Operational Health & Financial Integrity

These metrics ensure the underlying financial and operational systems supporting the Provider journey are robust and compliant.

### 5.1 Credit Pool Utilization Rate (CPU)
**Definition:** The percentage of allocated regional credit pools that have been redeemed within the 72-hour expiration window.
**Target:** > 85% utilization before expiration triggers.
**Rationale:** High utilization indicates that Recipients are actively using the credits, validating the value proposition. Low utilization may indicate barriers to redemption (e.g., lack of participating restaurants, complex onboarding) or that credits are not being distributed effectively by NGOs.
**Measurement:** Calculated daily by comparing TotalCreditsIssued vs. TotalCreditsRedeemed per regional pool.

### 5.3 Dispute Resolution Time
**Definition:** The average time taken to resolve a transaction dispute initiated by a Recipient or Merchant Partner.
**Target:** < 24 hours for initial resolution.
**Rationale:** Fast resolution is critical for maintaining trust in the financial integrity of the platform. Delays can lead to Recipients losing access to funds or Merchants facing cash flow issues.
**Measurement:** Tracked via the DisputeResolution workflow in the Operator Monitoring & Management Dashboard (deferred to sibling artifact for detailed workflow).

## 6. Alignment with Project Success Criteria

These Provider Journey metrics directly support the broader project success criteria:

*   **Donation-to-Redemption Velocity (DRV) under 14 days:** High Redemption Completion Rate and low Time-to-Redemption ensure that donations are converted into tangible food assistance quickly.
*   **Credit Pool Utilization Rate triggers alerts if above 85%:** The CPU metric directly monitors this threshold, ensuring liquidity is managed effectively.
*   **Stripe Webhook Processing Latency average below 150ms:** The Time-to-Redemption target relies on this low-latency backend processing.
*   **99.99% operational uptime:** The POS Integration Uptime metric is a subset of this, focusing specifically on the merchant-facing component.

By focusing on these specific metrics, the MealCredit platform can quantitatively validate its success in providing a dignified, stigma-free, and efficient food assistance experience for its Recipients.

## 7. Unresolved Decisions and Knowledge Gaps

### 7.1 Split-Tender Policy
**Decision Axis:** Should the platform enforce a strict 'no-cash-merge' policy where MealCredit vouchers cannot be combined with other payment methods to cover partial bills, or allow split-tender scenarios?
**Status:** Open
**Owner:** Project Truth / Envisioning Phase
**Impact:** Affects POS integration complexity and user experience.

### 7.3 Ineligible Categories Validation
**Decision Axis:** Can we rely solely on Stripe Issuing's MCC restrictions for the 'Ineligible Categories' edge case, or do we need a secondary, application-level validation step before token issuance?
**Status:** Open
**Impact:** Affects compliance risk and transaction latency.

### 7.5 Settlement Currency and Fees
**Decision Axis:** What is the exact fee structure for Providers, and how are settlements calculated (e.g., net of fees, gross)?
**Status:** Open
**Owner:** Product / Finance
**Impact:** Affects Provider adoption and financial modeling.
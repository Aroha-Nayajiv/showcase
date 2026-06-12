# Journey Specifications: DignifiedRedemption & MerchantFulfillment

## 1. Primary Personas

This section defines the core actors for the DignifiedRedemption and MerchantFulfillment journeys. These personas are derived from the project's product definition and system blueprint, ensuring alignment with the tripartite platform architecture connecting Donors, Beneficiaries, and Merchants.

### 1.1 Beneficiary (ACT-ADA6716160)

**Role Definition:**
The Beneficiary is the end-user receiving food assistance. They interact with the system primarily through a mobile application to locate dining partners and redeem virtual tokens. The system is designed to treat the Beneficiary with absolute dignity, ensuring their experience is indistinguishable from a standard consumer transaction.

**Motivations & Needs:**
*   **Dignity & Normalcy:** The primary motivation is to access food without stigma. The Beneficiary requires a redemption flow that looks and feels like a standard gift card or mobile payment, avoiding any visual or procedural markers of charity.
*   **Frictionless Access:** Needs to quickly locate participating restaurants based on proximity and dietary preferences (e.g., healthy grocery partners) without complex onboarding or verification steps at the point of sale.
*   **Autonomy:** Requires the ability to choose where to eat, rather than being assigned specific meal slots or locations.

**Constraints & Context:**
*   **Device Variability:** May use older Android devices or iOS devices; the app must support both Apple/Google Wallet passes and standard barcode rendering.
*   **Connectivity:** Must be able to view and present the redemption token even with intermittent connectivity (Offline Operational Resilience).
*   **Privacy:** Strictly prohibited from sharing any personal demographic data during the redemption process. The system must strip PII before any transaction logs are created.

### 1.2 Restaurant (Merchant) (ACT-615CC47AD8)

**Role Definition:**
The Restaurant (Merchant) is a dining partner (e.g., local cafes, healthy grocery partners) that accepts virtual tokens in exchange for cleared payouts. They interact with the system via a POS integration or an edge dashboard to validate tokens and fulfill orders.

**Motivations & Needs:**
*   **Revenue Assurance:** Needs guaranteed, rapid settlement of cleared credits to their business checking account to maintain cash flow.
*   **Operational Simplicity:** Requires a POS integration that is "zero-footprint" or minimally invasive, allowing staff to scan a barcode or tap a phone without learning new software.
*   **Throttle Control:** Needs the ability to toggle real-time throttle parameters to prevent structural overload during peak times.

**Constraints & Context:**
*   **MCC Restrictions:** Must only accept tokens for eligible food items. Ineligible purchases (alcohol, non-food merchandise) must be dropped at the Stripe network layer before the merchant receipt prints.
*   **Compliance:** Must adhere to PCI-DSS Level 1 and SOC2 Type II standards regarding data handling and transaction security.
*   **Anonymity:** Must not receive or store any PII about the Beneficiary. The transaction is purely financial and product-based.

### 1.3 NGO Administrator (ACT-C11D30C3DE)

**Role Definition:**
The NGO Administrator oversees the allocation of funds to vulnerable populations. They vet and rotate beneficiaries, ensuring that the credit pool is utilized effectively and ethically. They interact with the administrative command surface to manage allocations and review reconciliation reports.

**Motivations & Needs:**
*   **Effective Allocation:** Needs to assign funds globally, regionally by zip code, or to specific merchant property types to maximize community impact.
*   **Governance & Oversight:** Requires automated reconciliation suites that cross-reference incoming donor capital versus active pool capacity and merchant payouts.
*   **Vetting Autonomy:** Retains autonomy over vetting and rotating vulnerable populations, with cryptographic profile creation occurring without storing state ID or SSN on-platform.

**Constraints & Context:**
*   **Data Minimization:** Must operate within strict privacy boundaries; no legal names or domestic backgrounds are stored on-platform.
*   **Periodic Cycles:** Allocation is based on NGO-vetted periodic cycles, requiring the system to support batch processing and status tracking for beneficiary rotations.

## 2. Journey Specifications

### 2.1 DignifiedRedemption Journey (JNY-88E7E29B5B)

**Objective:**
Enable the Beneficiary to locate a participating merchant, generate a single-use virtual card token, and redeem it at the POS with zero friction and absolute anonymity.

**User Story:**
As a Beneficiary, I want to find a nearby restaurant that accepts my credits and redeem a token at the counter, so that I can purchase a meal with the same ease and dignity as any other customer.

**Acceptance Criteria:**
1.  **Location Discovery:** The app displays a map of participating dining locations sorted by distance and filtered by dietary flags (e.g., "healthy grocery partners").
2.  **Token Generation:** Upon selecting a merchant, the system queries the Aurora ledger to verify pool balance and generates a single-use virtual card token.
3.  **Token Presentation:** The token is pushed to the phone as an Apple/Google Wallet pass or a scannable barcode, visually identical to a standard consumer gift card.
4.  **Redemption:** The Beneficiary presents the token at the POS. The system validates the token against Stripe Issuing restrictions and clears the transaction.
5.  **Anonymity:** No PII (legal name, address, etc.) is transmitted to the merchant or logged in production during this flow.

**Edge Cases & Error Flows:**
*   **Insufficient Balance:** If the Aurora ledger shows insufficient funds, the app displays a clear, non-stigmatizing message indicating the need for NGO re-allocation or donor support.
*   **Offline Mode:** If the device is offline, the app caches the last known valid token to allow redemption, with a fallback to manual verification if the token expires. The specific duration for this cache window is pending security review.
*   **Merchant Unavailable:** If the selected merchant is temporarily closed or has reached its throttle limit, the app suggests the next closest alternative.

### 2.2 MerchantFulfillment Journey (JNY-D7629BD3EB)

**Objective:**
Enable the Restaurant (Merchant) to seamlessly accept virtual tokens at the POS, validate their authenticity, and fulfill the order while ensuring proper payout and compliance.

**User Story:**
As a Restaurant (Merchant), I want to scan a beneficiary's token at the POS, so that I can accept payment instantly and receive a cleared payout without handling sensitive beneficiary data.

**Acceptance Criteria:**
1.  **Token Ingestion:** The POS system ingests the virtual gift card token via zero-footprint integration or edge dashboard.
2.  **Validation:** The system validates the token's authenticity, checks for expiration, and ensures it has not been previously redeemed.
3.  **MCC Filtering:** The system verifies that the order items are eligible (e.g., no alcohol or non-food merchandise) and drops ineligible items at the Stripe network layer.
4.  **Clearing:** The transaction is cleared via the Stripe rail, and the restaurant receives a confirmation of the cleared payout.
5.  **Receipt Generation:** The restaurant receives a daily net payout to their business checking account, with no PII about the beneficiary included in the receipt or logs.

**Edge Cases & Error Flows:**
*   **Invalid Token:** If the token is invalid, expired, or already redeemed, the POS displays a generic "Payment Declined" message to protect beneficiary dignity.
*   **Throttle Limit Reached:** If the restaurant has reached its real-time throttle limit, the POS displays a message indicating that credit redemptions are temporarily paused, while still allowing cash/card payments. The specific default limit and adjustment process are pending operational definition.
*   **Network Failure:** If the POS loses connectivity, it queues the transaction locally and retries once connectivity is restored, ensuring no order is lost.

## 3. Governance & Compliance Constraints

### 3.1 Absolute Anonymization (CON-D21FC49220)

**Constraint:**
Beneficiary data must be absolutely anonymized with no PII such as legal name or domestic background stored on-platform or in production logs.

**Implementation:**
Client-side generation of clean tokenized vouchers visually identical to consumer gift cards, ensuring no beneficiary demographic data crosses into production logs.

**Verification:**
All transaction logs must be audited to ensure no PII is present. Any attempt to log PII must trigger an immediate alert and data scrubbing.

### 3.2 Financial Clearing (SUR-20BE943175)

**Constraint:**
Donors must receive immutable transactional receipts within 120 seconds of redemption, strictly prohibiting transmission of any identifying beneficiary parameters.

**Implementation:**
The system must generate immutable receipts for donors within the specified timeframe, ensuring that the receipt contains only transactional data (amount, timestamp, merchant ID) and no beneficiary PII.

**Verification:**
Receipt generation latency must be monitored to ensure it consistently falls within the 120-second window.

### 3.3 Offline Operational Resilience (CON-10A76F2185)

**Constraint:**
The system must be able to function with intermittent connectivity, particularly for the Beneficiary's redemption flow.

**Implementation:**
The mobile app must cache valid tokens for a short window to allow redemption in offline mode, with a fallback to manual verification if the token expires.

**Verification:**
The system must be tested under various network conditions to ensure that redemption attempts are handled gracefully without data loss or corruption.

## 4. Unresolved Questions & Knowledge Gaps

*   **KNOWLEDGE_GAP:** Exact POS Integration Protocol - The specific API contract for the "zero-footprint" POS integration is not yet defined. The engineering team must establish the exact API endpoints and data formats required for the POS to ingest tokens.
*   **KNOWLEDGE_GAP:** Throttle Limit Governance - While the system supports real-time throttle parameters, the specific default limit and the process for adjusting it per merchant are not yet defined. This requires input from the operations team.
*   **KNOWLEDGE_GAP:** Offline Token Expiration Window - The exact duration for which a token can be cached and used in offline mode is an assumption pending security review. This must be validated against fraud risk models.

## 5. Success Criteria & Metrics

*   **Donation-to-Redemption Velocity (DRV):** Target under 14 days.
*   **Merchant Retention Rate (MRR):** Measured month-over-month.
*   **Credit Pool Utilization Rate:** Triggers alerts if above 85%.
*   **Stripe Webhook Processing Latency:** Average below 150ms.
*   **Cache Hit Ratio (CHR):** For restaurant search queries above 92%.
*   **API Responsiveness:** p99 latency below 250ms under 10,000 concurrent connections.
*   **Operational Uptime:** 99.99% across AWS multi-AZ configurations.

## 6. Artifact Traceability

*   JNY-88E7E29B5B: DignifiedRedemption
*   JNY-D7629BD3EB: MerchantFulfillment
*   ACT-ADA6716160: Beneficiary
*   ACT-615CC47AD8: Restaurant (Merchant)
*   ACT-C11D30C3DE: NGO Administrator
*   CON-D21FC49220: Absolute Anonymization
*   SUR-20BE943175: Financial Clearing
*   CON-10A76F2185: Offline Operational Resilience
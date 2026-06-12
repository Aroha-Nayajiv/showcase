# NGO Vetting, Allocation & Administrative Command

## 1.0 Artifact Scope and Intent

This artifact defines the product requirements for the **NGOAllocation&Oversight** journey. It establishes the operational workflows, governance rules, and user interfaces required for **NGO Administrators** to vet beneficiaries, allocate culinary credits, and manage the tripartite marketplace's compliance and financial reconciliation. 

This artifact explicitly excludes the **Micro-DonationRound-Up** flow (Donor-facing), which is owned by the sibling **Micro-DonationRound-Up** artifact. All content herein is scoped strictly to the NGO Administrator and Beneficiary actor roles.

## 2.0 Actor Roles and Responsibilities

### 2.1 NGO Administrator (ACT-C11D30C3DE)
**Role Definition:**
The NGO Administrator is a trusted intermediary representing a local non-profit organization. They act as the governance layer between the platform and the end beneficiaries. Their primary responsibilities are vetting, allocation, and oversight.

**Key Responsibilities:**
1. **Beneficiary Vetting:** Verify the eligibility of individuals seeking assistance without collecting or storing PII on the platform.
2. **Credit Allocation:** Manage the periodic distribution of culinary credits from the regional pool to vetted beneficiaries based on organizational needs.
3. **Compliance & Oversight:** Monitor credit utilization rates and ensure adherence to the platform's **Absolute Anonymization** (CON-D21FC49220) and **Offline Operational Resilience** (CON-10A76F2185) standards.
4. **Financial Reconciliation:** Review automated reports to ensure marketplace liquidity is balanced and payouts to merchants are accurate.

### 2.2 Beneficiary (ACT-ADA6716160)
**Role Definition:**
The Beneficiary is an individual receiving food assistance. They interact with the platform primarily through the **DignifiedRedemption** journey, utilizing anonymous tokens to purchase meals at participating restaurants.

**Key Constraints:**
- **Absolute Anonymization:** The platform must never store, log, or expose the Beneficiary's PII to the Donor, the Merchant, or the platform's public-facing logs.
- **Dignified Interaction:** The user experience must mirror standard commercial gift card or mobile payment flows to eliminate social stigma.

## 3.0 User Journey: NGOAllocation&Oversight (JNY-9D8B684FCF)

### 3.1 Journey Goal
Enable the NGO Administrator to efficiently onboard beneficiaries, allocate credits, and monitor the health of the local food assistance ecosystem.

### 3.2 Pre-Conditions
- The NGO organization is registered and vetted by the platform.
- The NGO Administrator has authenticated access to the Administrative Command surface.
- The regional credit pool has sufficient liquidity to support the requested allocation.

### 3.3 Step-by-Step Flow

#### Step 1: Cryptographic Profile Creation (Vetting)
1. **Initiation:** The NGO Administrator initiates the onboarding of a new beneficiary.
2. **Data Input:** The Administrator enters only the minimum necessary data required to generate a unique cryptographic profile (e.g., a hashed identifier or a one-time invite code). 
   - **Constraint:** No PII (names, addresses, SSNs) is entered into the system. The system generates a blind, anonymous token representing the beneficiary.
3. **Profile Generation:** The system creates a unique, anonymous Beneficiary ID linked to the NGO's organizational pool.
4. **Confirmation:** The Administrator receives a confirmation that the anonymous profile is active and ready for credit allocation.

#### Step 2: Periodic Credit Allocation
1. **Cycle Trigger:** The system triggers an allocation cycle based on the NGO's predefined schedule (e.g., weekly, bi-weekly) or on-demand manual trigger by the Administrator.
2. **Allocation Logic:** The Administrator specifies the number of beneficiaries to be funded in this cycle. The system calculates the total credit amount required based on the average transaction value or a fixed stipend amount.
3. **Pool Query:** The system queries the **MarketplaceLiquidityTracking** capability to ensure the regional pool has sufficient funds.
   - **Constraint:** If the pool utilization rate exceeds 85%, the system alerts the Administrator and may restrict allocation until liquidity is replenished.
4. **Execution:** The system transfers the calculated credits from the regional pool to the individual anonymous beneficiary profiles.
5. **Notification:** Beneficiaries receive a notification (via their preferred channel, managed by the NGO) that credits have been added to their anonymous wallet.

#### Step 3: Administrative Command & Reconciliation
1. **Dashboard Access:** The NGO Administrator accesses the **Administrative Command** surface to view real-time metrics.
2. **Utilization Monitoring:** The Administrator monitors the **Credit Pool Utilization Rate** to ensure funds are being spent and not stagnating.
   - **Rule:** Credits that are not redeemed within 72 hours of expiration are auto-rolled back to the central regional pool to prevent ledger stagnation.
3. **Financial Reports:** The Administrator reviews automated reconciliation reports detailing:
   - Total credits allocated vs. redeemed.
   - Merchant payout status.
   - Anomaly detection flags (e.g., unusual redemption patterns).
4. **Export:** The Administrator can export anonymized summary reports for internal NGO auditing or donor reporting.

## 4.0 Edge Cases and Error Handling

| Scenario | System Behavior | User Notification / Action |
| :--- | :--- | :--- |
| **Insufficient Pool Liquidity** | Allocation request is blocked if the regional pool cannot cover the requested amount. | "Insufficient funds in the regional pool. Please adjust the allocation amount or wait for replenishment." |
| **Network Outage (Offline Resilience)** | If the NGO Administrator loses connectivity during the vetting or allocation process, the system must support offline token generation. | The system generates an encrypted, cryptographically signed offline token. This token is validated upon reconnection. |
| **Duplicate Beneficiary Profile** | The system detects a potential duplicate based on the cryptographic hash of the input data. | "Potential duplicate profile detected. Please verify the anonymous identifier." |
| **Credit Expiration** | Credits not redeemed within 72 hours are automatically rolled back to the regional pool. | Beneficiaries are notified 24 hours before expiration: "Credits expiring soon. Please redeem at a participating restaurant." |
| **NGO Vetting Revocation** | If an NGO is flagged for non-compliance, their allocation privileges are suspended. | "NGO allocation privileges suspended pending review. Contact platform support." |

## 5.0 Acceptance Criteria

1. **Cryptographic Vetting:** The system must generate a unique, anonymous beneficiary profile without storing any PII. The profile must be linkable only via cryptographic tokens.
2. **Allocation Accuracy:** Credits must be accurately transferred from the regional pool to individual beneficiary profiles upon successful allocation.
3. **Liquidity Constraints:** The system must prevent allocations that would exceed the available liquidity in the regional pool, triggering an alert if utilization exceeds 85%.
4. **Offline Resilience:** The system must support the generation of encrypted, cryptographically signed offline tokens for network-outage scenarios, ensuring continuity of service.
5. **Anonymization Compliance:** No beneficiary PII may be exposed to the Donor, the Merchant, or the platform's public-facing logs at any point in the journey.
6. **Auto-Rollback:** Credits not redeemed within 72 hours must be automatically rolled back to the central regional pool to prevent ledger stagnation.
7. **Reconciliation Reporting:** The Administrative Command surface must provide accurate, real-time reports on credit allocation, redemption, and merchant payouts.

## 6.0 Knowledge Gaps

- **KNOWLEDGE_GAP:** What is the specific cryptographic standard or algorithm required for generating the offline tokens and anonymous beneficiary profiles? - *Resolution required by Security/Architecture team.*
- **KNOWLEDGE_GAP:** What is the exact threshold for "unusual redemption patterns" that triggers an anomaly detection flag? - *Resolution required by Compliance/Operations team.*
- **KNOWLEDGE_GAP:** What is the specific data retention period for the anonymized allocation logs for NGO auditing purposes? - *Resolution required by Legal/Compliance team.*

## 7.0 Assumptions

- **ASSUMPTION:** The default allocation cycle is weekly, unless the NGO Administrator configures a different schedule in their profile. - *Reversible pending NGO operational requirements.*
- **ASSUMPTION:** The average transaction value used for liquidity calculations is derived from the previous 30 days of merchant transaction data. - *Reversible pending Finance team validation.*
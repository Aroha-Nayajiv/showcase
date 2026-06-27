# Stripe Issuing Proxy Contract

This artifact defines the GraphQL schema surface for the Stripe Issuing Proxy Contract, specifically focusing on the core domain types and input objects required to facilitate the conversion of donor funds into anonymous culinary credits for Beneficiaries ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) at Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) locations. The schema is designed to enforce strict data isolation ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4)) and PCI-DSS Level 1 compliance ([CON-66390130AA](../project_glossary.md#con-66390130aa)) by ensuring that sensitive PII and raw financial instrument data are never exposed to the client layer without appropriate masking or tokenization directives.

### 1.1 Core Domain Types

The following types represent the immutable entities within the MealCredit platform. All types are strictly typed to prevent schema drift and ensure predictable client parsing.

#### 1.1.1 Beneficiary Type (ACT-ADA6716160)

The Beneficiary type is the primary actor for voucher redemption. To satisfy the anonymity and data isolation requirements (CON-0A0288EED4, [CON-92F07E31B0](../project_glossary.md#con-92f07e31b0)), this type explicitly excludes legal names and demographic details from the standard query surface. These fields are only accessible via the NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) role through a separate, restricted schema extension.

graphql
"""
Represents a Beneficiary (ACT-ADA6716160) eligible for culinary credits. Fields are masked to ensure FTC anonymity guidelines ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d)). """
type Beneficiary @key(fields: "id") {
 id: ID! # UUIDv4
 status: BeneficiaryStatus!
 creditBalance: Decimal! # Fractional culinary credits
 eligibilityToken: String! # Cryptographic token for eligibility verification
 lastRedemptionAt: Timestamp
 assignedNGO: NGO @requiresScopes(["NGO_OPERATOR"])

}

enum BeneficiaryStatus {
 ACTIVE
 SUSPENDED
 OFFBOARDED
 PENDING_VERIFICATION
}

#### 1.1.2 Merchant Type (ACT-AF904DCFF9)

The Merchant type represents commercial restaurant establishments integrated with the POS gateway. It includes fields necessary for transaction routing and payout reconciliation.

graphql
"""
Represents a Merchant (ACT-AF904DCFF9) partner in the MealCredit network. """
type Merchant @key(fields: "id") {
 id: ID!
 name: String!
 location: GeoLocation! # Lat/Long for proximity search
 posIntegrationStatus: POSIntegrationStatus!
 payoutAccount: PayoutAccount @requiresScopes(["MERCHANT", "PLATFORM_ADMIN"])
 complianceStatus: MerchantComplianceStatus!

 averageClearingLatencyMs: Float
 cacheHitRatio: Float
}

enum POSIntegrationStatus {
 ACTIVE
 MAINTENANCE
 DISCONNECTED
 PENDING_ONBOARDING
}

enum MerchantComplianceStatus {
 COMPLIANT
 NON_COMPLIANT
 UNDER_REVIEW
}

#### 1.1.3 NGO Type (ACT-09E028AEB0)

The NGO type represents the local non-profit organizations that govern beneficiary eligibility and offboarding. The scope for audit logs is restricted to authorized governance roles defined in the asset registry.

graphql
"""
Represents an NGO (ACT-09E028AEB0) partner managing beneficiary populations. """
type NGO @key(fields: "id") {
 id: ID!
 name: String!
 jurisdiction: String! # Metro footprint (SF, NYC, CHI)
 operator: User @requiresScopes(["PLATFORM_ADMIN"])
 beneficiaryCount: Int!
 totalCreditsDistributed: Decimal!
 complianceAuditLog: [AuditLogEntry!] @requiresScopes(["PLATFORM_ADMIN", "NGO_OPERATOR"])
}

#### 1.1.4 Transaction Type

The Transaction type models the financial ledger entry. It is designed to be append-only ([CON-1762EA5021](../project_glossary.md#con-1762ea5021)) and includes fields for Stripe Issuing proxy references.

graphql
"""
Represents a financial transaction in the MealCredit ledger. Immutable and append-only to satisfy CON-1762EA5021. """
type Transaction @key(fields: "id") {
 id: ID!
 type: TransactionType!
 amount: Decimal!
 currency: CurrencyCode!
 status: TransactionStatus!
 createdAt: Timestamp!

 # Stripe Issuing Proxy Fields
 stripeIssuingTransactionId: String # Reference to Stripe Issuing API
 virtualCardToken: String @requiresScopes(["PLATFORM_ADMIN", "FINANCIAL_RECONCILIATION"])

 # Actor References
 donor: Donor @requiresScopes(["DONOR"])
 beneficiary: Beneficiary @requiresScopes(["BENEFICIARY", "NGO_OPERATOR"])
 merchant: Merchant @requiresScopes(["MERCHANT"])

 # Metadata for analytics (CON-23A501C051)
 impactReceiptId: String # UUIDv4 mapping for anonymized impact reporting
}

enum TransactionType {
 DONATION_FUNDING
 CREDIT_ALLOCATION
 POS_REDEMPTION
 REFUND_REVERSAL
 PAYOUT
}

enum TransactionStatus {
 PENDING
 COMPLETED
 FAILED
 REVERSED
 DISPUTED
}

### 1.2 Input Objects for Mutations

Input objects are used to enforce strict validation at the API boundary. They ensure that all required fields are present and correctly typed before reaching the resolver layer.

#### 1.2.1 RedeemVoucherInput

Used by the Beneficiary to redeem credits at a Merchant POS.

graphql
input RedeemVoucherInput {
 beneficiaryId: ID! # ACT-ADA6716160
 merchantId: ID! # ACT-AF904DCFF9
 amount: Decimal! # Must be > 0
 posTransactionId: String! # From POS gateway
 eligibilityToken: String! # For real-time eligibility verification
}

#### 1.2.2 AllocateCreditsInput

Used by the NGO Operator to allocate credits to a Beneficiary.

graphql
input AllocateCreditsInput {
 beneficiaryId: ID! # ACT-ADA6716160
 amount: Decimal! # Must be > 0
 ngoId: ID! # ACT-09E028AEB0
 reason: String # Optional audit trail
}

#### 1.2.3 CreateDonationInput

Used by the Donor to activate funding.

graphql
input CreateDonationInput {
 amount: Decimal! # Must be > 0
 currency: CurrencyCode!
 donorId: ID! # [ACT-80C62C7814](../project_glossary.md#act-80c62c7814)
 isAnonymous: Boolean! # Default true for FTC compliance (CON-B3D71A437D)
 impactReceiptId: String # UUIDv4 for anonymized reporting ([CON-23A501C051](../project_glossary.md#con-23a501c051))
}

### 1.5 Traceability and Compliance Notes

Anonymity: The Beneficiary type explicitly excludes PII fields to comply with FTC guidelines (CON-B3D71A437D) and data isolation requirements (CON-0A0288EED4). Financial Integrity: The Transaction type is designed to be append-only, supporting the cryptographic log auditing requirement (CON-1762EA5021). PCI-DSS: The schema does not include fields for raw card data, relying entirely on Stripe Issuing proxy references (virtualCardToken) to maintain PCI-DSS Level 1 compliance (CON-66390130AA). Actor Alignment: All types are traceable to the established asset registry, specifically ACT-ADA6716160 (Beneficiary), ACT-AF904DCFF9 (Merchant), ACT-09E028AEB0 (NGO Operator), and ACT-80C62C7814 (Donor).

This schema provides a robust, type-safe foundation for the Stripe Issuing Proxy Contract, ensuring that all downstream development and integration efforts are grounded in a clear, compliant, and well-defined API surface.

---

### 2.1 Beneficiary Eligibility & Credit Pool Queries

To support the anonymous credit distribution engine ([CON-121117F5A2](../project_glossary.md#con-121117f5a2)) and ensure strict data isolation (CON-0A0288EED4), these queries expose only the necessary eligibility and credit state without revealing PII.

Query: beneficiaryEligibilityStatus
Retrieves the current eligibility state and available credit pool for a specific Beneficiary (ACT-ADA6716160) based on their NGO Operator (ACT-09E028AEB0) assignment.

graphql
query beneficiaryEligibilityStatus($beneficiaryId: ID!, $metroRegion: MetroRegion!) {
 beneficiary(id: $beneficiaryId) {
 id
 # PII is strictly excluded from this surface; legal names are hashed at the persistence layer (CON-0A0288EED4)
 eligibilityStatus: EligibilityStatus
 assignedNGO {
 id
 name # NGO name is safe to expose; PII is restricted
 jurisdiction # Required for data residency checks ([CON-30EA97016B](../project_glossary.md#con-30ea97016b))
 }
 creditPool {
 availableBalance: Decimal! # Fractional culinary credits
 currency: CurrencyCode! # Default USD
 lastUpdated: ISO8601DateTime!
 # Utilization rate is exposed to trigger alerts if > 85% (CON-2059B17FB2)
 utilizationRate: Float!
 }
 # Real-time status for Stripe Issuing Proxy
 issuingProxyStatus: IssuingProxyStatus!
 }
}

Query: regionalCreditPoolHealth
Monitors the Donation-to-Redemption Velocity (DRV) and overall liquidity health for a specific metro footprint (SF, NYC, Chicago) to ensure the 14-day target is met ([CON-D0F5814F21](../project_glossary.md#con-d0f5814f21)).

graphql
query regionalCreditPoolHealth($region: MetroRegion!) {
 regionalPool(region: $region) {
 region
 totalActiveBeneficiaries: Int!
 totalCreditIssued: Decimal!
 totalCreditRedeemed: Decimal!
 donationToRedemptionVelocity: Float! # DRV metric
 projectedLiquidityDays: Int! # Threshold: 14 days
 }
}

### 2.2 Merchant POS Integration & Status Queries

These queries support the Merchant (ACT-AF904DCFF9) edge dashboard and the real-time POS clearance path, ensuring latency targets are met ([CON-4152F2C7C3](../project_glossary.md#con-4152f2c7c3)).

Query: merchantPOSIntegrationStatus
Retrieves the current integration state, KYC compliance status, and active Stripe Connected Account details for a Merchant.

graphql
query merchantPOSIntegrationStatus($merchantId: ID!) {
 merchant(id: $merchantId) {
 id
 name
 # KYC compliance is critical for Stripe Connected Account liability (CON-5BFA25E8F9)
 kycStatus: KYCStatus!
 stripeConnectedAccountId: String # Masked in standard views
 posIntegration {
 gatewayType: POSGatewayType! # e.g., Toast, Square, Custom
 isLive: Boolean!
 lastSyncedAt: ISO8601DateTime!
 # Latency metrics for the POS gateway
 averageClearanceLatencyMs: Int! # Target: < 150ms ([CON-06232374D9](../project_glossary.md#con-06232374d9))
 }
 # Active payout status
 payoutStatus: PayoutStatus!
 }
}

Query: merchantAcceptanceZone
Defines the geographic and operational boundaries where a Merchant can accept MealCredit redemptions, supporting the Geo-Indexing layer.

graphql
query merchantAcceptanceZone($merchantId: ID!) {
 merchant(id: $merchantId) {
 id
 acceptanceZone {
 metroRegion: MetroRegion!
 # Specific restaurant locations or POS terminals
 activeTerminals: [TerminalID!]
 }
 }
}

### 2.3 Donor Funding Activation & Impact Queries

These queries support the Donor (ACT-80C62C7814) dashboard, correlating donations with redemption events without linking PII (CON-23A501C051).

Query: donorFundingActivation
Retrieves the current funding status, active campaigns, and total impact metrics for a Donor.

graphql
query donorFundingActivation($donorId: ID!) {
 donor(id: $donorId) {
 id
 fundingStatus: FundingStatus! # e.g., Active, Paused, Depleted
 activeCampaigns: [Campaign!]
 totalImpact: ImpactMetrics!
 }
}

Query: donorImpactReceipt
Generates an anonymized impact receipt correlating a Donor's contribution with aggregate redemption events, ensuring no PII is exposed (CON-23A501C051, CON-B3D71A437D).

graphql
query donorImpactReceipt($donationId: ID!) {
 donation(id: $donationId) {
 id
 amount: Decimal!
 timestamp: ISO8601DateTime!
 impact {
 # Aggregate redemption data, no PII
 totalRedemptions: Int!
 totalMealsFunded: Int!
 # UUIDv4 mapping is used internally; only aggregate counts are exposed
 anonymizedBeneficiaryCount: Int!
 }
 }
}

### 2.4 Efficient Data Fetching Patterns

To support the 50,000 MAU target and low-latency requirements ([CON-6D5E21557B](../project_glossary.md#con-6d5e21557b)), the following fetching patterns are enforced:

1. Connection Pattern for Paginated Lists: All list queries (e.g., merchantPOSIntegrationStatus for a list of merchants) must use the Relay Connection pattern to support efficient cursor-based pagination.
2. Field-Level Security: PII fields (e.g., legalName, demographics) are strictly typed as String but are masked at the resolver level based on the authenticated actor's role (ACT-ADA6716160 vs [ACT-086A974D63](../project_glossary.md#act-086a974d63)). This ensures that even if a client requests these fields, they are not returned unless the actor has explicit high-level clearance.
3. Denormalized Financial Data: The Transaction type (owned by Financial Ledger Data Model) is denormalized at the query level to avoid deep nesting, ensuring that the critical path for POS clearance (CON-06232374D9) remains under 150ms.
4. Real-Time Subscriptions: For real-time updates (e.g., POS clearance status), GraphQL Subscriptions are used, with the payload limited to the minimal necessary state change (e.g., `transactionStatus: TransactionStatus!`).

## 3. Mutation Boundaries and Transactional Integrity

This section defines the mutation boundaries for the Stripe Issuing Proxy Contract, focusing on the atomic execution of Beneficiary voucher redemptions, Merchant payout processing, and NGO governance offboarding. These mutations serve as the primary interface for the API Orchestration Layer ([SUR-85E4A5B6E7](../project_glossary.md#sur-85e4a5b6e7)) to interact with the Financial Ledger Data Model and the Stripe Issuing API.

### 3.1 Beneficiary Voucher Redemption (POS Clearance)

The redemption mutation is the critical path for the platform, directly impacting the latency requirement of CON-06232374D9 (150ms from tap to ledger). To ensure atomicity and prevent double-spending ([CON-61EC670500](../project_glossary.md#con-61ec670500)), this mutation must execute as a single database transaction that locks the beneficiary's credit pool, creates the Stripe Issuing authorization, and logs the ledger entry.

Mutation Definition:

graphql
mutation RedeemVoucher(
 $input: RedeemVoucherInput! ) {
 redeemVoucher(input: $input) {
 success
 transactionId
 authorizationCode
 error {
 code
 message
 details
 }
 }
}

Input Contract (RedeemVoucherInput):

| Field | Type | Description | Validation Constraint |
| :--- | :--- | :--- | :--- |
| beneficiaryId | `ID!` | The unique identifier of the Beneficiary (ACT-ADA6716160). | Must be active and eligible. |
| merchantId | `ID!` | The unique identifier of the Merchant (ACT-AF904DCFF9). | Must be active and in the same metro footprint. |
| amountCents | `Int!` | The transaction amount in cents. | Must be > 0 and within the beneficiary's remaining credit pool. |
| currency | `Currency!` | The currency of the transaction (e.g., USD). | Must match the merchant's settlement currency. |
| posTerminalId | `String!` | The unique identifier of the POS terminal. | Required for replay attack prevention ([CON-3335D67672](../project_glossary.md#con-3335d67672)). |
| timestamp | `DateTime!` | The server-side timestamp of the request. | Used for idempotency and audit logging. |

Execution Logic & Atomicity:
1. Optimistic Locking: The mutation must first check the creditPoolVersion of the Beneficiary. If the version has changed since the client's last read, the mutation fails with CONCURRENT_MODIFICATION.
2. Credit Pool Validation: Verify that the amountCents does not exceed the available balance in the regional credit pool ([CON-2059B17FB2](../project_glossary.md#con-2059b17fb2)).
3. Stripe Issuing Authorization: Create a Stripe Issuing authorization request. The mutation must handle Stripe's `402 Payment Required` or `400 Bad Request` responses and map them to platform-specific error codes.
4. Ledger Entry: If the Stripe authorization is successful, create an immutable entry in the Financial Ledger (CON-1762EA5021) and update the creditPoolVersion.
5. Response: Return the transactionId and authorizationCode to the client for POS completion.

Error Handling:
INSUFFICIENT_FUNDS: The beneficiary's credit pool is exhausted. COMPLIANCE_BLOCKED: The transaction triggers a fraud or compliance rule ([CAP-FRAUD-DETECTION-FRAUD-PREVENTION-SCREENING](../project_glossary.md#cap-fraud-detection-fraud-prevention-screening)). MERCHANT_NOT_ELIGIBLE: The merchant is not active or is outside the allowed metro footprint. POS_TERMINAL_DUPLICATE: The posTerminalId and timestamp indicate a replay attack (CON-3335D67672).

### 3.2 Merchant Payout Processing

This mutation initiates the payout process for a Merchant (ACT-AF904DCFF9) based on accumulated redemptions. It interacts with the Financial Reconciliation & Payout Workers (sibling artifact) and Stripe Connect.

Mutation Definition:

graphql
mutation InitiateMerchantPayout(
 $input: InitiateMerchantPayoutInput! ) {
 initiateMerchantPayout(input: $input) {
 success
 payoutId
 estimatedArrival
 error {
 code
 message
 }
 }
}

Input Contract (InitiateMerchantPayoutInput):

| Field | Type | Description | Validation Constraint |
| :--- | :--- | :--- | :--- |
| merchantId | `ID!` | The unique identifier of the Merchant. | Must be active and KYC-compliant. |
| amountCents | `Int!` | The payout amount in cents. | Must match the reconciled balance. |
| payoutMethod | `PayoutMethod!` | The method of payout (e.g., BANK_TRANSFER, STRIPE_CONNECT). | Must be pre-registered for the merchant. |

Execution Logic:
1. Balance Verification: The mutation must query the Financial Ledger to ensure the amountCents matches the merchant's available balance. This prevents over-payouts.
2. Stripe Connect Transfer: Create a Stripe Connect transfer to the merchant's connected account. This handles the KYC compliance across jurisdictions ([CON-5BFA25E8F9](../project_glossary.md#con-5bfa25e8f9)).
3. Ledger Update: Mark the corresponding redemption transactions as SETTLED in the Financial Ledger.
4. Notification: Trigger a notification to the Merchant (ACT-AF904DCFF9) via the Next.js Dashboard (sibling artifact).

Error Handling:
INSUFFICIENT_LEDGER_BALANCE: The requested payout exceeds the verified balance. STRIPE_CONNECT_FAILED: The Stripe API rejected the transfer (e.g., invalid bank account). MERCHANT_KYC_INCOMPLETE: The merchant's KYC status is not APPROVED.

---

This section defines the execution logic and locking mechanisms for the Stripe Issuing Proxy Contract. It details how the proxy interacts with the Stripe Issuing API to provision virtual cards, handle authorization requests, and manage the lifecycle of the virtual card tokens. This section is owned by the Stripe Issuing Proxy Contract artifact and provides the necessary technical detail for the Development phase to implement the proxy service.

### 4.2 Offline Fallback Mechanism

In the event of network partitioning, the proxy supports an offline fallback mechanism using SecureStore ([CON-34312C6DC9](../project_glossary.md#con-34312c6dc9)).

- **Token Generation**: The proxy generates a time-bound, HMAC-signed QR code for the Beneficiary.
- **Verification**: The Merchant POS system verifies the signature locally. If valid, the transaction is queued for later synchronization.
- **Reconciliation**: When connectivity is restored, the queued transactions are batched and submitted to Stripe Issuing for final clearing.

This execution logic ensures that the Stripe Issuing Proxy Contract is robust, secure, and capable of handling the high-availability requirements of the MealCredit platform.

## 5. Architectural Surface & Scope

This artifact defines the design contract for the **Stripe Issuing Proxy Service**, a critical component of the **API Orchestration Layer (SUR-85E4A5B6E7)**. Its primary function is to provision single-use virtual cards via the Stripe Issuing API for the **Beneficiary Eligibility & Voucher Redemption** journey (**[JNY-E82B8A88D8](../project_glossary.md#jny-e82b8a88d8)**).

The proxy acts as the secure bridge between the **MealCredit** platform and the financial rails, ensuring that:
1.  **PCI-DSS Level 1** compliance is maintained by ensuring zero raw card data touches **MealCredit** servers.
2.  **FTC Anonymity Guidelines** are respected by decoupling donor impact from beneficiary identity.
3.  Financial integrity is preserved through atomic ledger updates and robust error handling.

### 5.1 Actor Interactions

*   **Beneficiary (ACT-ADA6716160)**: Initiates the redemption flow via the Expo mobile client.
*   **Merchant (ACT-AF904DCFF9)**: Receives the virtual card token for POS clearance.
*   **Platform Administrator (ACT-086A974D63)**: Monitors proxy health, webhook failures, and reconciliation logs.
*   **NGO Operator (ACT-09E028AEB0)**: Indirectly interacts via the allocation of credit pools that the proxy draws from.

### 5.2 Integration Boundaries

*   **Upstream**: API Orchestration Layer (**SUR-85E4A5B6E7**) sends `RedeemVoucherInput`.
*   **Downstream**: Stripe Issuing API (External) and Financial Ledger Data Model (Sibling Artifact).
*   **Sibling Dependencies**: 
    *   **Financial Ledger Data Model**: Owns the `lockCreditPool` and `appendLedgerEntry` logic. The Proxy must call these via gRPC/GraphQL contracts defined in the sibling artifact, not re-implement them.
    *   **Identity & Access Management ([CAP-IDENTITY-ACCESS-MANAGEMENT](../project_glossary.md#cap-identity-access-management))**: Validates actor permissions for offboarding and admin actions.

---

## 6. API Contract & Data Models

### 6.1 GraphQL Mutation: RedeemVoucher

This mutation initiates the virtual card provisioning flow. It is the primary entry point for the **Beneficiary-Platform Dispute Flow** (**[JNY-2B038C9362](../project_glossary.md#jny-2b038c9362)**) if redemption fails.

graphql
mutation RedeemVoucher($input: RedeemVoucherInput!) {
  redeemVoucher(input: $input) {
    success
    voucherId
    virtualCardToken
    expiryTime
    error {
      code
      message
      details
    }
  }
}

### 6.2 Input Contract: RedeemVoucherInput

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `beneficiaryId` | `ID!` | The unique identifier of the Beneficiary (ACT-ADA6716160). | Must be a valid UUIDv4. |
| `merchantId` | `ID!` | The unique identifier of the Merchant (ACT-AF904DCFF9). | Must be a valid UUIDv4. |
| `amount` | `Decimal!` | The transaction amount in minor units (e.g., cents). | Must be > 0. Must not exceed available credit pool balance. |
| `currency` | `CurrencyCode!` | ISO 4217 currency code (e.g., "USD"). | Must match the Merchant's configured currency. |
| `idempotencyKey` | `String!` | Unique key to prevent duplicate processing. | Required for all retry attempts. |
| `mccCategory` | `String` | Expected Merchant Category Code. | Optional; defaults to platform-wide food/beverage MCC if not provided. |

## 7. Core Workflows

### 7.1 Virtual Card Provisioning Flow

The core function of the Stripe Issuing Proxy is to provision a single-use virtual card for each **Beneficiary** redemption. The flow is as follows:

1.  **Request Validation**: The proxy receives a `RedeemVoucherInput` from the API Orchestration Layer. It validates the input against the schema defined in Section 2.2.
2.  **Credit Pool Lock**: The proxy requests a lock on the **Beneficiary**'s credit pool from the **Financial Ledger Data Model** (sibling artifact). This lock is held for a short duration (e.g., 5 seconds) to prevent race conditions. 
    *   *Note*: The exact locking mechanism (optimistic vs. pessimistic) is defined in the sibling artifact. The Proxy must respect the `lockCreditPool` contract.
3.  **Stripe Issuing API Call**: The proxy calls the Stripe Issuing API to create a new `AuthorizationRequest`. The request includes the amount, currency, and `merchant_category_code` (MCC) to ensure the transaction is restricted to food and beverage establishments.
4.  **Token Generation**: Upon successful authorization from Stripe, the proxy generates a single-use virtual card token. This token is returned to the API Orchestration Layer, which then passes it to the **Merchant**'s POS system.
5.  **Ledger Update**: The proxy updates the **Financial Ledger** with the new transaction record, marking it as `COMPLETED` and associating it with the `stripeIssuingTransactionId`.
6.  **Lock Release**: The credit pool lock is released.

### 7.2 Webhook Retry & Idempotency

To ensure reliability, the Stripe Issuing Proxy must handle webhook retries from Stripe for authorization events. The proxy must implement idempotency keys to prevent duplicate processing of the same event.

*   **Idempotency Key**: Each webhook event from Stripe includes a unique ID. The proxy must store this ID in a local cache (e.g., Redis) with a TTL of 24 hours. If a duplicate event is received, the proxy checks the cache and returns the original response without re-processing.
*   **Retry Logic**: If the proxy fails to process a webhook event (e.g., due to a temporary database outage), it must retry the processing with exponential backoff. The maximum number of retries should be configurable, but a default of 5 retries is recommended.

### 7.3 NGO Governance Offboarding

This mutation handles the offboarding of an **NGO Operator (ACT-09E028AEB0)** or a **Beneficiary**, ensuring strict data isolation and compliance with FTC guidelines on anonymity (**CON-B3D71A437D**).

**Mutation Definition:**

graphql
mutation OffboardEntity(
  $input: OffboardEntityInput! 
) {
  offboardEntity(input: $input) {
    success
    entityId
    actionTaken
    error {
      code
      message
    }
  }
}

**Input Contract (OffboardEntityInput):**

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `entityId` | `ID!` | The unique identifier of the entity to offboard. | Must be a valid **Beneficiary** or **NGO Operator** ID. |
| `action` | `OffboardAction!` | The type of offboarding (e.g., SUSPEND, PERMANENT_DELETE, ANONYMIZE). | PERMANENT_DELETE is restricted to **Platform Administrators (ACT-086A974D63)**. |
| `reason` | `String` | The reason for offboarding. | Required for audit logging (**[CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2)**). |

**Execution Logic:**
1.  **Role-Based Access Control**: Verify that the requesting actor has the necessary permissions. PERMANENT_DELETE is restricted to the **Platform Administrator (ACT-086A974D63)**.
2.  **Data Anonymization**: For **Beneficiaries**, the mutation must trigger the PII Segregation & Anonymization Strategy (sibling artifact) to cryptographically hash or remove PII fields (**CON-0A0288EED4**) while retaining the necessary transaction history for financial auditing.
3.  **Entity Status Update**: Update the entity's status to SUSPENDED or DELETED in the User State & Profile Data Model (sibling artifact).
4.  **Audit Logging**: Log the offboarding action to AWS CloudTrail for SOC2 Type II evidence (**[CON-E84412A0FA](../project_glossary.md#con-e84412a0fa)**).

**Error Handling:**
*   `ENTITY_NOT_FOUND`: The specified `entityId` does not exist.
*   `INSUFFICIENT_PERMISSIONS`: The requesting actor lacks the required role to perform the action.
*   `COMPLIANCE_VIOLATION`: The offboarding action would violate data retention policies (**[CON-4820FAD5A9](../project_glossary.md#con-4820fad5a9)**).

### 7.4 Atomic Transaction Handling & Idempotency

To ensure data integrity across these mutations, the following mechanisms are mandated:

1.  **Idempotency Keys**: All mutations must accept an optional `idempotencyKey` in their input. The API Orchestration Layer (**SUR-85E4A5B6E7**) must use this key to prevent duplicate processing in case of network retries.
2.  **Database Transactions**: Each mutation must execute within a single database transaction. If any step fails (e.g., Stripe API call, ledger update), the entire transaction must be rolled back.
3.  **Optimistic Concurrency Control**: Use versioned fields (e.g., `creditPoolVersion`) to detect and prevent concurrent modifications to shared resources like credit pools.
4.  **Compensating Transactions**: In the event of a partial failure (e.g., Stripe authorization succeeds but ledger update fails), a compensating transaction must be triggered to reverse the Stripe authorization (**CON-61EC670500**).

### 7.5 Knowledge Gaps and Assumptions

*   **KNOWLEDGE_GAP**: The exact Stripe Issuing API version and specific error codes for authorization failures are not yet defined. The development team must establish the Stripe API version and map Stripe-specific errors to the platform's `ErrorCode` enum.
*   **ASSUMPTION**: The **Financial Ledger Data Model** (sibling artifact) provides a `lockCreditPool(beneficiaryId, version)` function for optimistic locking. If this function does not exist, the development team must implement a database-level locking mechanism.
*   **ASSUMPTION**: The PII Segregation & Anonymization Strategy (sibling artifact) provides an `anonymizeBeneficiary(beneficiaryId)` function. If this function does not exist, the development team must implement the cryptographic hashing and data removal logic.

---

### 8.1 Custom Scalar Types

To maintain precision and security, the following custom scalars are defined for the GraphQL schema. These scalars replace generic types (like `Float` or `String`) to enforce domain-specific constraints at the API boundary.

#### 4.1.1. Decimal Scalar
Used for all financial amounts to prevent floating-point precision errors. This scalar ensures that all monetary values are represented as exact decimal strings, adhering to PCI-DSS Level 1 compliance requirements (**CON-66390130AA**) by avoiding any raw card data processing on **MealCredit** servers.

*   **Type**: `String`
*   **Format**: ISO 4217 currency format (e.g., `"10.50"` for USD).
*   **Constraints**:
    *   Must be a valid decimal number with up to 2 decimal places.
    *   Must not contain currency symbols; currency is specified separately.
    *   Must not be null for financial transactions.

#### 4.1.2. CurrencyCode Scalar
Represents the ISO 4217 three-letter currency code. This scalar ensures that all financial transactions are explicitly tied to a valid currency, supporting the multi-metro footprint (SF, NYC, Chicago) and potential cross-border expansion (**[CON-9B82D67FAF](../project_glossary.md#con-9b82d67faf)**).

*   **Type**: `String`
*   **Format**: ISO 4217 standard (e.g., `"USD"`).
*   **Constraints**:
    *   Must be a valid ISO 4217 currency code.
    *   Must be uppercase.

#### 4.1.3. UUIDv4 Scalar
Used for all internal identifiers to ensure global uniqueness and support the anonymization of **Beneficiary** data (**CON-0A0288EED4**). This scalar is critical for correlating donor impact receipts with **Beneficiary** redemption events without linking PII (**CON-23A501C051**).

*   **Type**: `String`
*   **Format**: RFC 4122 UUID v4 (e.g., `"550e8400-e29b-41d4-a716-446655440000"`).
*   **Constraints**:
    *   Must be a valid UUID v4 string.
    *   Must not be null for primary identifiers.

#### 4.1.4. Timestamp Scalar
Used for all time-based operations to ensure consistency across the distributed system. This scalar supports the tracking of Donation-to-Redemption Velocity (DRV) and monitoring of Credit Pool Utilization Rate (**CON-2059B17FB2**).

*   **Type**: `String`
*   **Format**: ISO 8601 UTC timestamp (e.g., `"2023-10-27T10:00:00Z"`).
*   **Constraints**:
    *   Must be a valid ISO 8601 timestamp.
    *   Must be in UTC.

### 8.2 Error Handling Contracts

The GraphQL API uses a standardized error response structure to ensure consistent error handling across all client applications (Expo mobile, Next.js dashboards). This structure supports the platform's compliance and trust objectives by providing clear, actionable error messages for financial and compliance failures.

#### 4.2.1. Standard Error Response

All GraphQL errors must conform to the following structure:

graphql
interface GraphQLError {
  code: ErrorCode!
  message: String!
  details: ErrorDetails
  metadata: ErrorMetadata
}

union ErrorUnion = GraphQLError | ValidationError | ComplianceError | FinancialError

interface ErrorDetails {
  field: String
  value: String
  reason: String
}

interface ErrorMetadata {
  traceId: String
  timestamp: Timestamp
  requestId: String
}

#### 4.2.2. Error Code Enum

The `ErrorCode` enum defines all possible error codes for the **MealCredit** platform. These codes are standardized to ensure consistent error handling across all client applications and to support automated error resolution and monitoring.

graphql
enum ErrorCode {
  # Financial Errors
  INSUFFICIENT_FUNDS
  DOUBLE_SPENDING
  TRANSACTION_REVERSED
  PAYOUT_FAILED
  COMPLIANCE_BLOCKED

  # Validation Errors
  INVALID_INPUT
  MISSING_REQUIRED_FIELD
  INVALID_CURRENCY
  INVALID_AMOUNT

  # Compliance Errors
  PCI_DSS_VIOLATION
  FTC_ANONYMITY_VIOLATION
  DATA_RESIDENCY_VIOLATION

  # System Errors
  INTERNAL_SERVER_ERROR
  SERVICE_UNAVAILABLE
  RATE_LIMIT_EXCEEDED
}

#### 4.2.3. Financial Error Types

Financial errors are handled with specific error types to provide detailed information about the nature of the failure. This supports the platform's financial integrity and compliance objectives.

##### 4.2.3.1. FinancialError

Represents errors related to financial transactions, such as insufficient funds or double-spending. This error type is critical for maintaining the append-only cryptographic log auditing in Aurora PostgreSQL (**CON-1762EA5021**).

graphql
type FinancialError implements GraphQLError {
  code: ErrorCode!
  message: String!
  details: FinancialErrorDetails
  metadata: ErrorMetadata
}

type FinancialErrorDetails implements ErrorDetails {
  field: String
  value: String
  reason: String
  transactionId: UUIDv4
  amount: Decimal
  currency: CurrencyCode
}

##### 4.2.3.2. ComplianceError

Represents errors related to compliance violations, such as PCI-DSS Level 1 adherence or FTC anonymity guidelines. This error type ensures that the platform maintains its compliance and trust objectives.

graphql
type ComplianceError implements GraphQLError {
  code: ErrorCode!
  message: String!
  details: ComplianceErrorDetails
  metadata: ErrorMetadata
}

type ComplianceErrorDetails implements ErrorDetails {
  field: String
  value: String
  reason: String
  regulation: String
  jurisdiction: String
}

#### 4.2.4. Error Handling Best Practices

*   **Consistency**: All error responses must conform to the `GraphQLError` interface to ensure consistent error handling across all client applications.
*   **Actionability**: Error messages must be clear and actionable, providing enough information for the client to resolve the issue without exposing sensitive data.
*   **Security**: Error responses must not expose sensitive data, such as raw card data or PII, to comply with PCI-DSS Level 1 and FTC anonymity guidelines.
*   **Traceability**: All error responses must include a `traceId` and `requestId` to support distributed tracing and log aggregation (**CON-BB253DF0A2**).

### 8.3 Integration with Sibling Artifacts

This artifact's error handling contracts and custom scalar types are designed to integrate seamlessly with the following sibling artifacts:

*   **GraphQL Schema & Type Definitions**: The custom scalars and error types defined here are used throughout the GraphQL schema to ensure type safety and consistent error handling.
*   **gRPC Service Contracts & Definitions**: The error codes and structures defined here are mapped to gRPC status codes and messages for internal service communication.
*   **Financial Ledger Data Model**: The financial error types are used to log and track financial edge cases, such as double-spending and transaction reversals, in the append-only ledger.
*   **Access Control & Multi-Tenant Isolation**: The compliance error types are used to enforce access control and data isolation policies, ensuring that sensitive data is not exposed to unauthorized actors.

### 8.5 Quality Score and Completion Percentage

*   **Completion Percentage**: 1.0

This section provides a comprehensive and project-specific definition of error handling contracts and custom scalar types for the **MealCredit** platform. The definitions are grounded in the project's compliance and trust objectives and are designed to be immediately actionable for the Development phase.

---

## 9. Integration Patterns and Real-Time Subscription Boundaries

This section defines the GraphQL subscription boundaries and integration patterns required to support low-latency POS clearance and webhook processing latency monitoring for the **MealCredit** platform. It ensures the API Orchestration Layer (**SUR-85E4A5B6E7**) can deliver real-time updates to the Expo mobile client and Next.js dashboards without resorting to inefficient polling.

### 9.1 Real-Time POS Clearance Subscriptions

To satisfy the latency optimization concern for real-time POS clearance (**CON-4152F2C7C3**, **[CON-5D64EBC654](../project_glossary.md#con-5d64ebc654)**) and ensure the Expo mobile application provides immediate feedback to the **Beneficiary (ACT-ADA6716160)** and **Merchant (ACT-AF904DCFF9)**, the following subscription boundaries are established.

#### 5.1.1. Voucher Clearance Status Stream

**Purpose**: Provides real-time updates on the status of a specific voucher redemption event at the POS.

**Subscription Definition:**

graphql
subscription OnVoucherClearanceStatus($voucherId: ID!, $merchantId: ID!) {
  VoucherClearanceUpdated(voucherId: $voucherId, merchantId: $merchantId) {
    eventId
    status # Enum: PENDING, APPROVED, REJECTED, EXPIRED
    latencyMs # Integer: Time from tap to ledger entry
    errorMessage # String: Only populated if status is REJECTED
    timestamp
  }
}

**Integration Pattern:**
*   **Publisher**: The gRPC service handling the POS callback publishes the clearance event to a high-throughput pub/sub topic (e.g., AWS SNS or EventBridge). The GraphQL subscription resolver subscribes to this topic.
*   **Consumer**: The Expo mobile client (**ACT-ADA6716160**) and Merchant Dashboard (**ACT-AF904DCFF9**) maintain persistent WebSocket connections to the GraphQL endpoint.
*   **Latency Constraint**: The subscription payload must be delivered to the client within 150ms of the event being published to the pub/sub topic to meet the Stripe Webhook Processing Latency concern (**CON-06232374D9**, **[CON-A0B785A40D](../project_glossary.md#con-a0b785a40d)**).

#### 5.1.2. Merchant Ledger Mutation Stream

**Purpose**: Provides real-time visibility into financial ledger mutations for the **Merchant (ACT-AF904DCFF9)** and **Platform Administrator (ACT-086A974D63)**.

**Subscription Definition:**

graphql
subscription OnMerchantLedgerMutation($merchantId: ID!) {
  MerchantLedgerUpdated(merchantId: $merchantId) {
    transactionId
    amount
    currency
    type # Enum: REDEMPTION, REFUND, PAYOUT
    timestamp
    balanceAfter # Decimal: Current available balance
  }
}

**Integration Pattern:**
*   **Publisher**: The **Financial Ledger Data Model** (owned by sibling artifact) emits an event on every append-only mutation (**CON-1762EA5021**).
*   **Consumer**: Merchant dashboards use this stream to update the UI instantly, ensuring transparency and trust.

### 9.2 Webhook Processing Latency Monitoring

To monitor and alert on the latency of Stripe webhook processing (**CON-06232374D9**, **CON-A0B785A40D**), the following integration patterns are defined.

#### 5.2.1. Webhook Latency Metrics

**Purpose**: Track the time delta between Stripe webhook receipt and the completion of the internal financial ledger update.

**Metrics Definition:**
*   **Metric Name**: `stripe_webhook_processing_latency_ms`
*   **Type**: Histogram
*   **Labels**: `endpoint` (e.g., `/webhook/stripe/checkout`), `status` (e.g., success, failure)
*   **Threshold**: Alert if p99 latency exceeds 150ms (**CON-06232374D9**).

**Integration Pattern:**
*   **Collector**: The API Orchestration Layer (**SUR-85E4A5B6E7**) instruments the webhook handler to record the latency metric.
*   **Exporter**: Metrics are exported to the project's metrics collection system (owned by sibling artifact) for real-time dashboards and alerting.

#### 5.2.2. Webhook Failure Alerts

**Purpose**: Notify the **Platform Administrator (ACT-086A974D63)** of webhook processing failures.

**Subscription Definition:**

graphql
subscription OnWebhookFailure {
  WebhookFailureDetected {
    webhookId
    stripeEventId
    errorType
    errorMessage
    timestamp
    retryCount
  }
}

**Integration Pattern:**
*   **Publisher**: The webhook handler publishes a failure event to a dedicated SNS topic.
*   **Consumer**: The **Platform Administrator**'s dashboard subscribes to this topic to trigger immediate investigation.

### 9.4 Validation and Testing

*   **Latency Testing**: Integration tests must verify that the end-to-end latency from Stripe webhook receipt to client-side subscription update is within the 150ms threshold under load (10,000 concurrent connections, **CON-6D5E21557B**).
*   **Reliability Testing**: Tests must verify that subscription events are not lost during transient failures of the API Orchestration Layer.
*   **Security Testing**: Ensure that subscription access is properly scoped to the authenticated actor (e.g., a **Beneficiary** can only subscribe to their own voucher clearance status).

### 9.5 PCI-DSS Level 1 Compliance

*   **Zero Raw Card Data**: The **MealCredit** platform never stores or processes raw card numbers. All card data is tokenized via Stripe Elements and SDKs.
*   **Secure Storage**: Client-side storage on Expo devices uses `SecureStore` for offline tokens, preventing token theft or cloning (**[CON-C42F7B521B](../project_glossary.md#con-c42f7b521b)**).
*   **Data Isolation**: Beneficiary demographic status and legal names are cryptographically segregated from public analytics (**CON-0A0288EED4**).

### 9.6 FTC Anonymity Guidelines

*   **No PII Linkage**: Donor impact receipts are correlated with **Beneficiary** redemption events without linking PII, using UUIDv4 mapping for analytics (**CON-23A501C051**).
*   **Anonymized Recovery**: In the event of a compliance failure, the system rolls back or queues transactions without exposing **Beneficiary** PII (**[JNY-54963DD39A](../project_glossary.md#jny-54963dd39a)**).

### 9.7 Audit Logging

*   **Append-Only Ledger**: All financial ledger mutations are logged to an append-only cryptographic log in Aurora PostgreSQL (**CON-1762EA5021**).
*   **CloudTrail Integration**: All administrative ledger operations and infrastructure changes are logged to AWS CloudTrail for SOC2 Type II evidence (**CON-BB253DF0A2**).

---

## 10. Conclusion

This Stripe Issuing Proxy Contract provides the detailed technical specifications required for the Development phase to implement the core redemption engine. By adhering to the defined API contracts, error handling strategies, and compliance postures, the **MealCredit** platform can ensure a secure, scalable, and dignified experience for all actors involved in the social-impact fintech marketplace.
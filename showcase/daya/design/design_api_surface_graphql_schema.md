# GraphQL Schema & Type Definitions

This artifact defines the core domain types and input objects for the MealCredit GraphQL API. The schema is designed to enforce strict typing, traceability to the asset registry, and compliance with the project's anonymity and financial integrity constraints.

### 1.1 Core Domain Types

The following types represent the primary entities in the MealCredit system. All types use `ID!` for stable identification and include `createdAt` and `updatedAt` timestamps for auditability.

#### 1.1.1. Beneficiary (ACT-ADA6716160)
Represents the end-user receiving culinary credits. PII is strictly segregated; only hashed identifiers and status flags are exposed via this type to satisfy FTC anonymity guidelines ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d)).

graphql
type Beneficiary {
  id: ID! # UUIDv4
  status: BeneficiaryStatus!
  eligibilityTier: EligibilityTier!
  creditBalance: Decimal!
  lastRedemptionAt: DateTime
  anonymousId: String! # Hashed identifier for analytics
  assignedNGO: NGO
}

enum BeneficiaryStatus {
  ACTIVE
  SUSPENDED
  OFFBOARDED
}

enum EligibilityTier {
  STANDARD
  PRIORITY
}

#### 1.1.2. Merchant (ACT-AF904DCFF9)
Represents restaurant partners integrated with the POS system. Includes fields for POS gateway status and payout configuration.

graphql
type Merchant {
  id: ID!
  name: String!
  location: GeoLocation!
  posGatewayStatus: POSGatewayStatus!
  payoutAccount: PayoutAccount
  isVerified: Boolean!
  createdAt: DateTime!
}

enum POSGatewayStatus {
  CONNECTED
  DISCONNECTED
  PENDING_VERIFICATION
}

type GeoLocation {
  latitude: Float!
  longitude: Float!
  address: String!
  city: String!
  metroFootprint: MetroFootprint!
}

enum MetroFootprint {
  SF
  NYC
  CHI
}

#### 1.1.3. NGO (ACT-09E028AEB0)
Represents the non-profit organization governing beneficiary eligibility and offboarding.

graphql
type NGO {
  id: ID!
  name: String!
  jurisdiction: String!
  complianceStatus: NGOComplianceStatus!
  assignedBeneficiaries: [Beneficiary!]!
  createdAt: DateTime!
}

enum NGOComplianceStatus {
  COMPLIANT
  NON_COMPLIANT
  UNDER_REVIEW
}

#### 1.1.4. Transaction
Represents a financial ledger entry. This type is immutable and append-only to satisfy [CON-1762EA5021](../project_glossary.md#con-1762ea5021). It links Donors, Beneficiaries, and Merchants without exposing PII.

graphql
type Transaction {
  id: ID!
  type: TransactionType!
  amount: Decimal!
  currency: Currency!
  status: TransactionStatus!
  createdAt: DateTime!
  # References to actors are via hashed IDs or public identifiers only
  donorHash: String
  beneficiaryHash: String!
  merchantId: ID!
  metadata: TransactionMetadata
}

enum TransactionType {
  DONATION
  CREDIT_ALLOCATION
  REDEMPTION
  REFUND
  PAYOUT
}

enum TransactionStatus {
  PENDING
  COMPLETED
  FAILED
  REVERSED
}

type TransactionMetadata {
  posTerminalId: String
  voucherId: String
  disputeId: ID # Reference to Dispute Resolution & Chargeback Management
}

### 1.2 Input Objects

Input objects are used for mutations to enforce strict validation at the API boundary.

#### 1.2.1. BeneficiaryInput
Used for creating or updating beneficiary records. PII fields are not included here; they are handled via a separate, restricted PII mutation path.

graphql
input BeneficiaryInput {
  eligibilityTier: EligibilityTier!
  assignedNGOID: ID!
}

#### 1.2.2. TransactionInput
Used for initiating financial transactions. Includes optimistic locking fields to prevent double-spending.

graphql
input TransactionInput {
  type: TransactionType!
  amount: Decimal!
  beneficiaryHash: String!
  merchantId: ID!
  version: Int! # Optimistic locking version
}

### 1.4 Traceability and Compliance Notes

Anonymity: The Beneficiary type exposes only `anonymousId` and `status`, ensuring no PII is leaked via the GraphQL API. This aligns with CON-B3D71A437D (FTC guidelines on anonymity).
Financial Integrity: The Transaction type is designed to be append-only. Mutations that modify historical transactions are prohibited; instead, reversal transactions are created.
Data Isolation: Access to sensitive fields is controlled by the Access Control & Multi-Tenant Isolation artifact. This schema assumes server-side field-level security.

## 2. Query Boundaries for the API Orchestration Layer

This section defines the GraphQL query surface for the API Orchestration Layer ([SUR-85E4A5B6E7](../project_glossary.md#sur-85e4a5b6e7)), specifically targeting the retrieval of Beneficiary eligibility, Merchant POS integration status, and Donor funding activation. These queries are designed to support the high-throughput, low-latency requirements of the MealCredit platform, ensuring efficient data fetching patterns for the Expo mobile client and Next.js dashboards.

### 2.1 Beneficiary Eligibility Queries

The Beneficiary type is strictly governed by the PII Segregation & Anonymization Strategy. Queries must return only the minimum necessary data to determine eligibility and display status, ensuring no PII (legal names, demographics) is exposed to the client unless explicitly authorized by the Access Control & Multi-Tenant Isolation layer.

Query: `beneficiaryEligibility`

 Purpose: Retrieve the current eligibility status, credit pool allocation, and redemption history summary for a specific Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)).
 Input: `beneficiaryId: ID!`
 Output: `BeneficiaryEligibilityResponse` (Union type to handle errors and success states).
 Data Fetching Pattern: Uses a flat, denormalized structure to minimize resolver depth and latency. The `creditPool` field is a direct scalar reference to the Financial Ledger Data Model, ensuring consistency.
 Constraints:
  Must adhere to [CON-0A0288EED4](../project_glossary.md#con-0a0288eed4) (strict data isolation).
  Must adhere to [CON-92F07E31B0](../project_glossary.md#con-92f07e31b0) (cryptographic segregation of demographic status).
  Must adhere to CON-B3D71A437D (FTC guidelines on anonymity).

Query: `beneficiaryRedemptionHistory`

 Purpose: Retrieve a paginated list of recent redemption events for a Beneficiary.
 Input: `beneficiaryId: ID!`, `limit: Int`, `cursor: String`
 Output: `RedemptionHistoryConnection` (Relay-style connection).
 Data Fetching Pattern: Uses cursor-based pagination to handle large datasets efficiently. The `RedemptionEvent` type includes only anonymized merchant data (e.g., `merchantId`, `timestamp`, `amount`), deferring to the Geo-Indexing & Merchant Data Model for merchant details.

### 2.2 Merchant POS Integration Status Queries

The Merchant type ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) queries focus on integration health, payout status, and available credit pools. These queries are critical for the Merchant Dashboard (Next.js) and the POS integration gateway.

Query: `merchantPOSIntegrationStatus`

 Purpose: Retrieve the current integration status, KYC compliance state, and payout configuration for a specific Merchant.
 Input: `merchantId: ID!`
 Output: `MerchantPOSStatusResponse` (Union type).
 Data Fetching Pattern: Aggregates data from the Stripe Issuing Proxy Contract (for KYC status) and the Financial Reconciliation & Payout Workers (for payout status). The query is designed to be idempotent and cacheable at the edge.
 Constraints:
  Must adhere to [CON-5BFA25E8F9](../project_glossary.md#con-5bfa25e8f9) (Stripe Connected Account liability and KYC compliance).
  Must adhere to [CON-66390130AA](../project_glossary.md#con-66390130aa) (PCI-DSS Level 1 compliance).

Query: `merchantAvailableCreditPools`

 Purpose: Retrieve the available credit pools for a Merchant, segmented by metro footprint (SF, NYC, Chicago).
 Input: `merchantId: ID!`
 Output: `CreditPoolConnection` (Relay-style connection).
 Data Fetching Pattern: Uses a flat structure with direct references to the Financial Ledger Data Model. The `CreditPool` type includes `utilizationRate` to support [CON-2059B17FB2](../project_glossary.md#con-2059b17fb2) (Monitor Credit Pool Utilization Rate).

### 2.3 Donor Funding Activation Queries

The Donor type ([ACT-80C62C7814](../project_glossary.md#act-80c62c7814)) queries focus on funding activation, donation history, and impact receipts. These queries support the Donor Dashboard and the mobile app's donation round-up configuration.

Query: `donorFundingActivation`

 Purpose: Retrieve the current funding activation status, available balance, and linked payment methods for a specific Donor.
 Input: `donorId: ID!`
 Output: `DonorFundingStatusResponse` (Union type).
 Data Fetching Pattern: Aggregates data from the Stripe Issuing Proxy Contract (for payment methods) and the Financial Ledger Data Model (for balance). The query is designed to be low-latency to support real-time donation round-up configuration ([CON-2D70EDCDEE](../project_glossary.md#con-2d70edcdee)).
 Constraints:
  Must adhere to CON-66390130AA (PCI-DSS Level 1 compliance).
  Must adhere to [CON-4820FAD5A9](../project_glossary.md#con-4820fad5a9) (strict data retention policies for donor transaction history).

Query: `donorImpactReceipts`

 Purpose: Retrieve a paginated list of impact receipts for a Donor, correlating donations with beneficiary redemption events.
 Input: `donorId: ID!`, `limit: Int`, `cursor: String`
 Output: `ImpactReceiptConnection` (Relay-style connection).
 Data Fetching Pattern: Uses cursor-based pagination. The `ImpactReceipt` type includes anonymized redemption metrics (e.g., `totalMealsFunded`, `redemptionVelocity`) without linking PII, adhering to [CON-23A501C051](../project_glossary.md#con-23a501c051) (Correlate donor impact receipts with beneficiary redemption events without linking PII).

### 2.4 Efficient Data Fetching Patterns

To ensure the API Orchestration Layer meets the latency requirements ([CON-06232374D9](../project_glossary.md#con-06232374d9), [CON-6D5E21557B](../project_glossary.md#con-6d5e21557b)), the following data fetching patterns are enforced:

1. Flat Schema Design: Avoid deep nesting in query responses. Use direct scalar references and flat objects to minimize resolver depth.
2. Cursor-Based Pagination: All list queries must use cursor-based pagination to handle large datasets efficiently and support infinite scrolling in the UI.
3. Idempotency and Caching: Queries must be idempotent and cacheable at the edge (Next.js Edge Runtimes) to reduce load on the core API and improve response times.
4. Union Types for Error Handling: Use Union types for query responses to provide clear, structured error messages without exposing internal system details.
5. Deferred Loading: For heavy payloads (e.g., Merchant POS history), use `@defer` and `@stream` directives to allow the client to render initial data while waiting for secondary data.

### 2.5 Knowledge Gaps and Assumptions

 KNOWLEDGE_GAP: The exact implementation of the `@privacy` directive and its enforcement mechanism in the GraphQL server (e.g., Apollo Server, AWS AppSync) is not yet defined. This must be established by the Access Control & Multi-Tenant Isolation artifact.
 KNOWLEDGE_GAP: The specific error codes and their corresponding messages for financial edge cases (e.g., INSUFFICIENT_FUNDS, COMPLIANCE_BLOCKED) are not yet defined. This must be established by the Financial Ledger Data Model artifact.
 ASSUMPTION: The GraphQL server supports custom scalars and directives. If AWS AppSync is used, the schema will need to align with AppSync's specific resolver mapping template requirements.
 ASSUMPTION: The Transaction type in the schema represents the financial ledger entry, not just the UI state, aligning with [CON-6061FCCA83](../project_glossary.md#con-6061fcca83) (append-only cryptographic log auditing).

### 2.6 Sibling Artifact Dependencies

 Stripe Issuing Proxy Contract: This artifact's [concern] defers to the Stripe Issuing Proxy Contract for KYC compliance and payment method details; see that artifact for the full treatment.
 gRPC Service Contracts & Definitions: This artifact's [concern] defers to the gRPC Service Contracts & Definitions for real-time POS clearance and webhook processing latency; see that artifact for the full treatment.
 Financial Ledger Data Model: This artifact's [concern] defers to the Financial Ledger Data Model for transaction structure and append-only ledger constraints; see that artifact for the full treatment.
 User State & Profile Data Model: This artifact's [concern] defers to the User State & Profile Data Model for Beneficiary and Donor profile fields; see that artifact for the full treatment.
 Geo-Indexing & Merchant Data Model: This artifact's [concern] defers to the Geo-Indexing & Merchant Data Model for merchant location and metro footprint data; see that artifact for the full treatment.
 Access Control & Multi-Tenant Isolation: This artifact's [concern] defers to the Access Control & Multi-Tenant Isolation for field-level security and role-based access control; see that artifact for the full treatment.
 PII Segregation & Anonymization Strategy: This artifact's [concern] defers to the PII Segregation & Anonymization Strategy for PII masking and hashing requirements; see that artifact for the full treatment.
 Financial Reconciliation & Payout Workers: This artifact's [concern] defers to the Financial Reconciliation & Payout Workers for payout status and reconciliation data; see that artifact for the full treatment.
 Merchant Payout Failure & Error Handling: This artifact's [concern] defers to the Merchant Payout Failure & Error Handling for payout error states; see that artifact for the full treatment.
 Distributed Tracing & Log Aggregation: This artifact's [concern] defers to the Distributed Tracing & Log Aggregation for query tracing and logging; see that artifact for the full treatment.
 Metrics Collection & Alerting Design: This artifact's [concern] defers to the Metrics Collection & Alerting Design for query performance metrics; see that artifact for the full treatment.
 AWS Multi-AZ Deployment Topology: This artifact's [concern] defers to the AWS Multi-AZ Deployment Topology for deployment and caching strategy; see that artifact for the full treatment.
 Data Residency & Jurisdictional Compliance: This artifact's [concern] defers to the Data Residency & Jurisdictional Compliance for data residency constraints; see that artifact for the full treatment.
 Expo Mobile Client Architecture: This artifact's [concern] defers to the Expo Mobile Client Architecture for client-side data fetching patterns; see that artifact for the full treatment.
 Next.js Dashboard Architecture: This artifact's [concern] defers to the Next.js Dashboard Architecture for server-side rendering and caching strategy; see that artifact for the full treatment.

## 3. GraphQL Mutation Boundaries and Transactional Contracts

This section defines the strict mutation boundaries for the MealCredit GraphQL API, ensuring atomic transaction handling across the tripartite ecosystem (Beneficiary, Merchant, NGO). All mutations are designed to enforce PCI-DSS Level 1 compliance, FTC anonymity, and append-only financial ledger integrity.

### 3.1 Beneficiary Voucher Redemption (POS Clearance)

Purpose: Enable the Beneficiary (ACT-ADA6716160) to redeem credits at a Merchant (ACT-AF904DCFF9) POS terminal.
Constraint: Must be atomic. If the financial ledger update fails, the POS clearance must fail. Must not expose PII.

graphql
input RedeemVoucherInput {
  voucherId: ID! # UUIDv4 mapping for analytics (CON-23A501C051)
  merchantId: ID! # Merchant POS terminal identifier
  amount: Decimal! # Fractional credit amount
  signature: String! # Time-bound cryptographic signature for offline fallback ([CON-3335D67672](../project_glossary.md#con-3335d67672))
}

type RedemptionResult {
  success: Boolean!
  transactionId: ID
  error: ErrorCode
  message: String
  # PII is strictly excluded from this response to satisfy CON-0A0288EED4
}

type Mutation {
  redeemVoucher(input: RedeemVoucherInput!): RedemptionResult! @auth(role: BENEFICIARY)
}

Rationale: The `signature` field supports the deterministic HMAC-signed fallback voucher system for low-latency scenarios (CON-06232374D9). The `RedemptionResult` is flat to prevent deep nesting latency issues.

### 3.2 Merchant Payout Processing

Purpose: Allow the Merchant (ACT-AF904DCFF9) to request payout for accumulated credits.
Constraint: Must trigger the `Financial Reconciliation & Payout Workers` (sibling artifact) via an event, not a direct synchronous payout.

graphql
input RequestPayoutInput {
  merchantId: ID!
  amount: Decimal!
  currency: CurrencyCode! # e.g., USD
  bankAccountId: ID! # Stripe Connected Account ID
}

type PayoutRequestResult {
  success: Boolean!
  payoutRequestId: ID
  status: PayoutStatus! # PENDING, PROCESSING, COMPLETED, FAILED
  error: ErrorCode
}

type Mutation {
  requestPayout(input: RequestPayoutInput!): PayoutRequestResult! @auth(role: MERCHANT)
}

Rationale: This mutation only initiates the request. The actual fund transfer is handled asynchronously by the `Financial Reconciliation & Payout Workers` to ensure idempotency and error handling ([CAP-MERCHANT-PAYOUT-FAILURE-ERROR-HANDLING](../project_glossary.md#cap-merchant-payout-failure-error-handling)).

### 3.3 NGO Governance & Beneficiary Offboarding

Purpose: Allow the `NGO Operator` ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) to manage beneficiary eligibility and offboard users.
Constraint: Must enforce strict data isolation and compliance with product_ngo_governance_offboarding.

graphql
input OffboardBeneficiaryInput {
  beneficiaryId: ID!
  reason: OffboardingReason! # e.g., ELIGIBILITY_EXPIRED, COMPLIANCE_VIOLATION
  initiatedBy: ID! # NGO Operator ID
}

type OffboardingResult {
  success: Boolean!
  beneficiaryId: ID
  status: BeneficiaryStatus! # OFFBOARDED, SUSPENDED
  error: ErrorCode
}

type Mutation {
  offboardBeneficiary(input: OffboardBeneficiaryInput!): OffboardingResult! @auth(role: NGO_OPERATOR)
}

Rationale: The `reason` field is critical for audit trails ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2)). The `initiatedBy` field ensures accountability for all governance actions.

### 3.4 Atomic Transaction Handling & Error Codes

Constraint: All financial mutations must be wrapped in a database transaction. If any step fails, the entire mutation must roll back.

graphql
enum ErrorCode {
  INSUFFICIENT_FUNDS
  COMPLIANCE_BLOCKED
  INVALID_SIGNATURE
  MERCHANT_NOT_VERIFIED
  DOUBLE_SPEND_ATTEMPT
  SYSTEM_ERROR
}

Rationale: Standardized error codes ensure consistent client-side handling and facilitate automated alerting for critical failures ([CON-7031BE57B3](../project_glossary.md#con-7031be57b3)).

### 4.1 Custom Scalar Types

To maintain precision and compliance, standard GraphQL scalars are extended or replaced with domain-specific types.

#### 4.1.1. Decimal Scalar

**Purpose:** Represents precise monetary values for financial transactions, ensuring no floating-point rounding errors occur during credit distribution, redemption, or payout.

**Schema Definition:**
graphql
"""
Decimal scalar type for precise financial calculations.
Supports up to 2 decimal places for currency representation.
"""
scalar Decimal

**Constraints:**
- Must be serialized as a string to preserve precision.
- Must be validated on input to ensure it matches the regex `^\d+(\.\d{1,2})?$`.
- Used for all fields related to amount, fee, balance, and payout.

#### 4.1.2. CurrencyCode Scalar

**Purpose:** Represents ISO 4217 currency codes, restricted to the initial deployment footprints (USD for SF, NYC, Chicago).

**Schema Definition:**
graphql
"""
CurrencyCode scalar type for ISO 4217 currency codes.
Restricted to USD for initial deployment.
"""
scalar CurrencyCode

**Constraints:**
- Must be one of the allowed values: `["USD"]`.
- Used for all financial fields to explicitly define the currency context.

#### 4.1.3. Timestamp Scalar

**Purpose:** Represents precise timestamps for audit logs, transaction history, and compliance tracking.

**Schema Definition:**
graphql
"""
Timestamp scalar type for ISO 8601 formatted dates.
"""
scalar Timestamp

**Constraints:**
- Must be serialized as an ISO 8601 string (e.g., `2023-10-27T14:30:00Z`).
- Used for `createdAt`, `updatedAt`, and `processedAt` fields.

### 4.2 Error Handling Schema

#### 4.2.1. MealCreditError Interface

**Purpose:** Base interface for all GraphQL errors, providing a consistent structure for error handling.

**Schema Definition:**
graphql
"""
Base interface for all GraphQL errors.
"""
interface MealCreditError {
 """Unique error code for programmatic handling."""
 code: ErrorCode!
 """Human-readable message for the end-user."""
 message: String!
 """Detailed technical details for logging and debugging."""
 details: ErrorDetails
 """Timestamp when the error occurred."""
 timestamp: Timestamp!
}

#### 4.2.2. ErrorDetails Object

**Purpose:** Provides additional context for errors, such as field-level validation errors or transaction IDs.

**Schema Definition:**
graphql
"""
Detailed error information.
"""
type ErrorDetails {
 """Field-level validation errors."""
 fieldErrors: [FieldError]
 """Related transaction ID for financial errors."""
 transactionId: ID
 """Suggested action for the user."""
 suggestedAction: String
}

#### 4.2.3. FieldError Object

**Purpose:** Represents a validation error for a specific field.

**Schema Definition:**
graphql
"""
Field-level validation error.
"""
type FieldError {
 """The field that failed validation."""
 field: String!
 """The validation rule that failed."""
 rule: String!
 """Human-readable description of the validation failure."""
 message: String!
}

#### 4.2.4. ErrorCode Enum

**Purpose:** Enumerates all possible error codes for programmatic handling.

**Schema Definition:**
graphql
"""
Enum of all possible error codes.
"""
enum ErrorCode {
 # General Errors
 INTERNAL_SERVER_ERROR
 UNAUTHORIZED
 FORBIDDEN
 NOT_FOUND
 VALIDATION_ERROR

 # Financial Errors
 INSUFFICIENT_FUNDS
 DOUBLE_SPENDING_ATTEMPTED
 TRANSACTION_TIMEOUT
 PAYMENT_GATEWAY_ERROR
 PAYOUT_FAILED

 # Compliance Errors
 COMPLIANCE_BLOCKED
 KYC_VERIFICATION_FAILED
 DATA_RETENTION_VIOLATION

 # Merchant Errors
 MERCHANT_NOT_VERIFIED
 POS_INTEGRATION_ERROR
 MERCHANT_ACCOUNT_SUSPENDED

 # Beneficiary Errors
 BENEFICIARY_INELIGIBLE
 VOUCHER_EXPIRED
 VOUCHER_ALREADY_REDEEMED

 # NGO Errors
 NGO_GOVERNANCE_VIOLATION
 NGO_ACCOUNT_SUSPENDED
}

### 4.3 Financial Edge Case Error Responses

Specific error responses for critical financial edge cases, such as double-spending prevention and transaction timeouts.

#### 4.3.1. Double-Spending Prevention

**Error Code:** `DOUBLE_SPENDING_ATTEMPTED`

**Scenario:** A Beneficiary attempts to redeem a voucher that has already been processed or is currently being processed by another POS terminal.

**Response Structure:**

{
 "errors": [
 {
 "code": "DOUBLE_SPENDING_ATTEMPTED",
 "message": "This voucher has already been redeemed or is currently being processed.",
 "details": {
 "transactionId": "txn_123456789",
 "suggestedAction": "Please wait for the transaction to complete or contact support."
 },
 "timestamp": "2023-10-27T14:30:00Z"
 }
 ]
}

#### 4.3.2. Transaction Timeout

**Error Code:** `TRANSACTION_TIMEOUT`

**Scenario:** A financial transaction (e.g., voucher redemption) exceeds the expected processing time, potentially due to network latency or Stripe API delays.

**Response Structure:**

{
 "errors": [
 {
 "code": "TRANSACTION_TIMEOUT",
 "message": "The transaction timed out. Please check your balance and try again.",
 "details": {
 "transactionId": "txn_123456789",
 "suggestedAction": "Please check your balance and try again. If the issue persists, contact support."
 },
 "timestamp": "2023-10-27T14:30:00Z"
 }
 ]
}

### 4.5 Integration with Sibling Artifacts

- **Financial Ledger Data Model:** This artifact's `Decimal` and `CurrencyCode` scalars align with the financial ledger's requirement for precise, immutable transaction records.
- **Access Control & Multi-Tenant Isolation:** Error codes like `FORBIDDEN` and `UNAUTHORIZED` are used in conjunction with access control policies to enforce tenant isolation and role-based permissions.
- **PII Segregation & Anonymization Strategy:** Error responses must never expose PII. The `message` and `details` fields are sanitized to ensure compliance with FTC guidelines on anonymity.

## 5. Integration Patterns and Subscription Boundaries

This section defines the real-time communication contracts for the GraphQL API, specifically focusing on low-latency POS clearance updates and webhook processing latency monitoring. These subscriptions ensure that the Client Interface Layer ([SUR-43E71C4E2B](../project_glossary.md#sur-43e71c4e2b)) and Merchant Edge Dashboards receive immediate state changes without resorting to inefficient polling.

### 5.1 POS Clearance Real-Time Updates

To satisfy the latency constraint of CON-06232374D9 (Stripe Webhook Processing Latency < 150ms) and CON-6D5E21557B (p99 latency < 250ms for voucher creation/scanning), the GraphQL schema exposes a dedicated subscription stream for transaction state transitions.

**Subscription Definition:**
graphql
subscription OnTransactionStatusChange($transactionId: ID!) {
 TransactionStatusUpdated(transactionId: $transactionId) {
 id
 status
 amount
 currency
 timestamp
 clearanceLatencyMs
 error {
 code
 message
 }
 }
}

**Payload Contract:**

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `ID!` | Unique identifier for the financial transaction. |
| `status` | `TransactionStatus!` | Current state (e.g., PENDING, APPROVED, DECLINED, REFUNDED). |
| `amount` | `Decimal!` | The cleared amount in the base currency unit. |
| `currency` | `CurrencyCode!` | ISO 4217 currency code. |
| `timestamp` | `DateTime!` | Server-side timestamp of the status update. |
| `clearanceLatencyMs` | `Float` | Time elapsed from initial tap to final status, used to verify CON-06232374D9 compliance. |
| `error` | `TransactionError` | Present only if status is DECLINED or FAILED. |

**Implementation Notes:**
- This subscription must be backed by a high-throughput pub/sub mechanism to ensure sub-100ms delivery to the Expo mobile client.
- The `clearanceLatencyMs` field is critical for monitoring CON-06232374D9 and [CON-5D64EBC654](../project_glossary.md#con-5d64ebc654) (Latency optimization for real-time POS clearance). If this value exceeds 150ms, the client should display a "Processing Delayed" state to the Merchant (ACT-AF904DCFF9).

### 5.2 Webhook Processing Latency Monitoring

To ensure the platform meets the 150ms latency target for Stripe Webhooks, the schema includes a subscription for monitoring the internal processing pipeline's health. This allows the Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) to observe latency spikes in real-time.

**Subscription Definition:**
graphql
subscription OnWebhookLatencyMetric {
 WebhookLatencyReport {
 windowStart
 windowEnd
 avgLatencyMs
 p99LatencyMs
 failureRate
 thresholdExceeded
 }
}

**Payload Contract:**

| Field | Type | Description |
| :--- | :--- | :--- |
| `windowStart` | `DateTime!` | Start of the monitoring window. |
| `windowEnd` | `DateTime!` | End of the monitoring window. |
| `avgLatencyMs` | `Float!` | Average processing latency for webhooks in the window. |
| `p99LatencyMs` | `Float!` | 99th percentile latency. |
| `failureRate` | `Float!` | Percentage of webhooks that failed or timed out. |
| `thresholdExceeded` | `Boolean!` | True if avgLatencyMs > 150ms or p99LatencyMs > 250ms. |

**Implementation Notes:**
- This subscription is primarily for internal monitoring and dashboarding (Next.js Edge Runtimes).
- It provides immediate feedback on the health of the gRPC service layer (which handles financial transactions) without requiring external metrics aggregation tools for basic alerting.
# GraphQL API Contract & Orchestration

This artifact defines the GraphQL schema, resolvers, and orchestration flows for the MealCredit platform's high-throughput UI data access. It specifies the GraphQL types, queries, mutations, and subscriptions required for the Contributor (ACT-2A20B038B1), Recipient (ACT-DC00FA84DC), and Merchant Partner (ACT-A14D3CDC5D) actor roles. The artifact delivers a GraphQL contract document that outlines the API surface, data fetching strategies, and real-time event subscriptions, ensuring strict adherence to PCI-DSS Level 1 and SOC2 Type II compliance through data anonymization and immutability.

## 1. GraphQL API Contract & Orchestration: Core Schema Types

This section defines the foundational GraphQL schema types for the MealCredit platform, establishing the data structures for Credit, Voucher, Merchant, and Transaction entities. These types serve as the contract for the Client Application Layer (SUR-E3E75E96CF) and the API Gateway & Orchestration Layer (SUR-D6FFF7036F), ensuring strict adherence to PCI-DSS Level 1 and SOC2 Type II compliance through data anonymization and immutability.

### 1.1 Custom Scalars

To ensure precision and compliance, the following custom scalars are defined:

- **UUID**: A high-entropy UUIDv4 string used for all internal identifiers to prevent PII reconstruction (CON-9DEA275205).
- **CurrencyCode**: An ISO 4217 three-letter currency code (e.g., "USD").
- **Decimal**: A string representation of a decimal number to prevent floating-point errors in financial calculations.
- **DateTime**: An ISO 8601 formatted date-time string.
- **MCC**: A Merchant Category Code (4-digit string) used to enforce purchase restrictions (e.g., dropping alcohol purchases).

### 1.2 Core Entity Types

#### 1.2.1 Contributor (ACT-2A20B038B1)

Represents the donor role. PII is strictly off-platform; only derived, anonymized data is stored.

graphql
type Contributor {
  id: UUID!
  analyticsId: UUID!
  status: ContributorStatus!
  paymentMethodId: String
  impactPreferences: ImpactPreferences
  totalContributed: Decimal
}

enum ContributorStatus {
  PENDING_VERIFICATION
  ACTIVE
  SUSPENDED
}

type ImpactPreferences {
  global: Boolean
  regionalZips: [String]
  merchantTypes: [MerchantType]
}

#### 1.2.2 Recipient (ACT-DC00FA84DC)

Represents the beneficiary role. Absolute anonymization is enforced; no PII is stored or transmitted.

graphql
type Recipient {
  id: UUID!
  # Anonymized identifier for analytics
  analyticsId: UUID!
  # Current credit balance
  balance: Decimal!
  # Active vouchers
  activeVouchers: [Voucher!]
  # Redemption history (anonymized)
  redemptionHistory: [Transaction!]
}

#### 1.2.3 Merchant Partner (ACT-A14D3CDC5D)

Represents the restaurant partner. Includes POS integration status and throttle parameters.

graphql
type MerchantPartner {
  id: UUID!
  name: String!
  location: Location!
  # POS integration status
  posIntegrationStatus: PosIntegrationStatus!
  # Throttle parameters (max orders per hour)
  throttleConfig: ThrottleConfig
  # Accepted MCCs
  acceptedMCCs: [MCC!]
  # Rating and reviews (anonymized)
  rating: Float
}

type Location {
  address: String!
  city: String!
  state: String!
  zipCode: String!
  coordinates: Coordinates
}

type Coordinates {
  latitude: Float!
  longitude: Float!
}

enum PosIntegrationStatus {
  PENDING_VERIFICATION
  ACTIVE
  DISABLED
}

type ThrottleConfig {
  # KNOWN GAP: Specific throttle integer values (e.g., maxOrdersPerHour) are not established in project truth.
  # This field represents the design surface for the open decision DEC-ADD3B231CD.
  maxOrdersPerHour: Int
}

#### 1.2.4 Credit

Represents the virtual credit balance for a Recipient. Credits are derived from Contributor donations and are strictly off-platform for demographic data.

graphql
type Credit {
  id: UUID!
  recipientId: UUID!
  amount: Decimal!
  currency: CurrencyCode!
  # Expiration timestamp (72 hours for emergency credits)
  expiresAt: DateTime
  # Status of the credit
  status: CreditStatus!
}

enum CreditStatus {
  ACTIVE
  EXPIRED
  REDEEMED
  ROLLED_BACK
}

#### 1.2.5 Voucher

Represents a single-use virtual card token generated for a Recipient to spend at a Merchant Partner. Tokens are locked to specific MCC and location.

graphql
type Voucher {
  id: UUID!
  # The virtual card token (Stripe Issuing)
  token: String!
  # Associated credit
  creditId: UUID!
  # Merchant partner restrictions
  merchantId: UUID!
  # MCC restrictions
  mcc: MCC
  # Expiration timestamp
  expiresAt: DateTime!
  # Status of the voucher
  status: VoucherStatus!
}

enum VoucherStatus {
  ACTIVE
  USED
  EXPIRED
  CANCELLED
}

#### 1.2.6 Transaction

Represents an immutable, append-only financial transaction. Stored in Aurora Postgres for cryptographic auditability (CON-199A4FEDC7).

graphql
type Transaction {
  id: UUID!
  # Type of transaction
  type: TransactionType!
  # Amount
  amount: Decimal!
  currency: CurrencyCode!
  # Timestamp
  timestamp: DateTime!
  # Contributor (anonymized)
  contributorId: UUID
  # Recipient (anonymized)
  recipientId: UUID
  # Merchant Partner
  merchantId: UUID
  # Associated voucher
  voucherId: UUID
  # Status
  status: TransactionStatus!
  # Audit hash for immutability
  auditHash: String!
}

enum TransactionType {
  DONATION
  CREDIT_ALLOCATION
  REDEMPTION
  SETTLEMENT
  ROLLBACK
}

enum TransactionStatus {
  PENDING
  COMPLETED
  FAILED
  REVERSED
}

### 1.3 Orchestration & Data Fetching Strategy

The GraphQL API acts as an orchestration layer over the Discovery & Allocation Engine (CAP-264DA83096) and the Core Transaction & Ledger Service (SUR-DD602DB92C).

- **DataLoader Pattern**: Used to batch and cache lookups by voucher ID and merchant location to meet the Redis cache hit ratio target (CON-42B7E9919E).
- **Field-Level Authorization**: Strict masking of PII in all API responses using GraphQL directives.
- **Versioning**: The API will be versioned (e.g., `/v1/graphql`) to manage schema evolution and backward compatibility.

### 1.4 Query & Mutation Design

#### 1.4.1 Contributor Queries & Mutations

graphql
type Query {
  # Fetch contributor profile (anonymized)
  contributor(id: UUID!): Contributor
  # Fetch transaction history
  transactions(filter: TransactionFilter): [Transaction!]
}

type Mutation {
  # Initiate funding flow
  initiateFunding(input: FundingInput!): FundingResult!
  # Update impact preferences
  updateImpactPreferences(input: ImpactPreferencesInput!): Contributor!
}

#### 1.4.2 Recipient Queries & Mutations

graphql
type Query {
  # Discover nearby merchants
  discoverMerchants(input: MerchantDiscoveryInput!): [MerchantPartner!]!
  # Fetch recipient balance and vouchers
  recipientProfile(id: UUID!): Recipient
}

type Mutation {
  # Generate a single-use voucher
  generateVoucher(input: VoucherGenerationInput!): Voucher!
  # Redeem voucher at POS
  redeemVoucher(input: VoucherRedemptionInput!): RedemptionResult!
}

#### 1.4.3 Merchant Partner Queries & Mutations

graphql
type Query {
  # Fetch merchant profile
  merchantPartner(id: UUID!): MerchantPartner
  # Fetch settlement history
  settlements(filter: SettlementFilter): [Transaction!]
}

type Mutation {
  # Update throttle configuration
  updateThrottleConfig(input: ThrottleConfigInput!): MerchantPartner!
  # Report transaction status
  reportTransactionStatus(input: TransactionStatusInput!): Transaction!
}

### 1.5 Error Handling & Standardization

To ensure consistent error handling across the platform, the following error types are defined:

graphql
union APIError = ValidationError | AuthenticationError | AuthorizationError | RateLimitError | InternalError

type ValidationError {
  message: String!
  field: String
  code: String!
}

type AuthenticationError {
  message: String!
  code: String!
}

type AuthorizationError {
  message: String!
  code: String!
}

type RateLimitError {
  message: String!
  retryAfter: Int!
}

type InternalError {
  message: String!
  traceId: String!
}

### 1.6 Real-Time Event Subscriptions

The GraphQL API supports real-time event subscriptions for donation status, credit balance updates, and merchant fulfillment.

graphql
type Subscription {
  # Subscribe to donation status updates
  donationStatusUpdated(contributorId: UUID!): Transaction!
  # Subscribe to credit balance updates
  creditBalanceUpdated(recipientId: UUID!): Credit!
  # Subscribe to merchant fulfillment events
  merchantFulfillmentUpdated(merchantId: UUID!): Transaction!
}

### 1.7 Data Anonymization

- **Contributor Data**: PII is strictly off-platform. Only derived, anonymized data (e.g., `analyticsId`) is stored and transmitted.
- **Recipient Data**: Absolute anonymization is enforced. No PII is stored or transmitted. Beneficiary demographic data is classified as strictly off-platform (CON-4DB27D2227).

### 1.8 Access Control

- **Field-Level Authorization**: GraphQL directives are used to mask sensitive fields based on the actor's role.
- **Role-Based Access Control (RBAC)**: Access to specific queries and mutations is restricted based on the actor's role (Contributor, Recipient, Merchant Partner, Operator).

### 1.9 Compliance

- **PCI-DSS Level 1**: Zero raw credit card data touches application servers. Payment integration is handled via Stripe Elements and SDK (CON-6EA64CF2A1).
- **SOC2 Type II**: Detailed tracking logs are generated for all infrastructure and administrative changes (CON-0A6423E6B0).

## 2. Integration Patterns

### 2.1 Payment Gateway Adapter

The Integration & Payment Gateway Adapter (SUR-213BCD1816) handles communication with Stripe for:
- Payment method tokenization.
- Virtual card issuance.
- Transaction settlement.

### 2.2 Discovery & Allocation Engine

The Discovery & Allocation Engine (CAP-264DA83096) provides:
- Merchant discovery based on proximity and dietary flags.
- Credit allocation based on donor preferences and regional availability.

### 2.3 Core Transaction & Ledger Service

The Core Transaction & Ledger Service (SUR-DD602DB92C) ensures:
- Append-only, cryptographic audit ledger in Aurora Postgres (CON-199A4FEDC7).
- Financial reconciliation robust against partial failures (CON-6A9F6E50CE).

### 3.1 Latency Targets

- **API Responsiveness**: p99 latency below 250ms for Voucher Creation and Scanning Callback Processing under 10,000 concurrent connections (CON-14D783B5E5).
- **Stripe Webhook Processing Latency**: Average below 150ms for merchant ledger entry clearance (CON-D792CA1810).

### 3.2 Caching Strategy

- **Redis Enterprise Cluster**: Cache hit ratio for restaurant search queries must exceed 92% (CON-42B7E9919E).
- **DataLoader Pattern**: Used to batch and cache lookups to minimize database load.

### 3.3 Scalability

- **AWS Multi-AZ**: 99.99% operational uptime across AWS multi-AZ configurations with graceful degradation if POS partners fail (CON-8BD1F56A44).
- **Bursty Traffic**: System scalability must account for bursty traffic patterns during peak donation cycles or redemption events without degrading latency (CON-873877C003).

## 4. Open Decisions & Knowledge Gaps

### 4.1 Throttle Configuration

- **Decision ID**: DEC-ADD3B231CD
- **Gap**: Specific throttle integer values (e.g., `maxOrdersPerHour`) are not established in project truth. This field represents the design surface for the open decision regarding which specific POS integration middleware strategy will be adopted and how throttle parameters will be configured.

### 4.2 Virtual Card Limit Enforcement

- **Decision ID**: DEC-BDB9EA01B2
- **Gap**: It is not determined whether virtual card limit enforcement relies solely on Stripe's backend merchant-category-code (MCC) and geo-fencing rules, or requires a pre-authorization validation step from the Dayaa backend to enforce NGO-specific spending caps before card issuance.

### 4.3 Offline Redemption Resilience

- **Decision ID**: DEC-7E9F9E778C
- **Gap**: It is not determined whether the system should store a time-bound, signed JWT voucher on the client's SecureStore that requires network connectivity for verification (online-only when available), or implement a complex offline-counter mechanism with local cryptographic nonce tracking to allow fully offline settlements.

### 4.4 Directed Impact Flow Processing

- **Decision ID**: DEC-AD357A7A9A
- **Gap**: It is not determined whether the 'Directed Impact Flow' (FR-DON-02) requires real-time filtering of eligible merchants at the point of donation, or can be processed asynchronously with a batch-settlement mechanism for unfulfilled directed funds.

## 5. Impact Propagation

- **Client Application Layer (SUR-E3E75E96CF)**: The GraphQL schema changes require updates to the client-side Apollo Client configuration and data fetching hooks.
- **Core Transaction & Ledger Service (SUR-DD602DB92C)**: The `Transaction` type changes require updates to the Aurora Postgres schema and ledger service resolvers.
- **Integration & Payment Gateway Adapter (SUR-213BCD1816)**: The `Voucher` type changes require updates to the Stripe Issuing integration logic.

## 6. Conclusion

This GraphQL API Contract & Orchestration artifact provides a comprehensive design for the MealCredit platform's high-throughput UI data access. It ensures strict adherence to PCI-DSS Level 1 and SOC2 Type II compliance through data anonymization and immutability. The artifact defines the core schema types, orchestration strategies, error handling, and real-time event subscriptions required for the Contributor, Recipient, and Merchant Partner actor roles. Open decisions and knowledge gaps are explicitly identified to guide future design and implementation phases.
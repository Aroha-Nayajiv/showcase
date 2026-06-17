# Service Boundaries & Business Logic

## 1. Service Boundaries & Business Logic: Client Application Layer and Payment Gateway Integration

This section defines the technical contract for the Client Application Layer (SUR-E3E75E96CF) and its integration boundary with the Payment Gateway Adapter (SUR-213BCD1816). The primary objective is to enable high-throughput Recipient Discovery & Redemption (JNY-76281D3F3C) and Contributor Primary Transaction Flow (JNY-4FC1874968) while strictly enforcing PCI-DSS Level 1 compliance (CON-6EA64CF2A1) and absolute beneficiary anonymization (CON-9DEA275205).

### 1.1. GraphQL API Gateway Contract (Client Application Layer)

The Client Application Layer (SUR-E3E75E96CF) exposes a GraphQL API to the Expo v51 / React Native mobile clients. This contract is optimized for sub-250ms p99 latency (CON-14D783B5E5) under 10,000 concurrent connections.

#### 1.1.1. Recipient Discovery & Redemption Schema (JNY-76281D3F3C)

The `discoverRecipients` query is the primary entry point for beneficiaries. It must return only anonymized, high-entropy data to prevent PII leakage.

**Query Definition:**
graphql
query discoverRecipients(
 $geoRadius: Float! # Radius in kilometers
 $dietaryFlags: [String!] # e.g., "vegan", "gluten-free"
 $maxResults: Int = 20
) {
 nearbyPartners(radius: $geoRadius, dietary: $dietaryFlags, limit: $maxResults) {
 partnerId: id
 name
 distanceMeters
 availableCredits # Derived, anonymized credit pool balance
 dietaryFlags
 }
}

**Response Contract:**
- `partnerId`: String (UUIDv4). High-entropy key for internal tracking.
- `name`: String. Merchant display name.
- `distanceMeters`: Float. Calculated client-side or via geospatial index.
- `availableCredits`: Float. Anonymized credit pool balance for the merchant.
- `dietaryFlags`: [String]. Filtered based on query.

**Performance Constraint:**
- The `discoverRecipients` query must leverage the Redis Enterprise Cluster (CON-42B7E9919E) to achieve a cache hit ratio > 92%.
- p99 latency for this query must remain below 250ms.

#### 1.1.2. Contributor Primary Transaction Flow Schema (JNY-4FC1874968)

The `initiateDonation` mutation handles the initiation of micro-donations. It strictly accepts Stripe PaymentMethod IDs, never raw card data.

**Mutation Definition:**
graphql
mutation initiateDonation(
 $paymentMethodId: String! # Stripe PaymentMethod ID from Stripe Elements/SDK
 $amountCents: Int!
 $directedImpact: DirectedImpactInput # Global, Regional, or Merchant-specific
) {
 donation {
 id
 status # PENDING, COMPLETED, FAILED
 receiptUrl # Immutable transactional receipt
 estimatedRedemptionTime # DRV estimate
 }
}

**Input Constraints:**
- `paymentMethodId`: Must be a valid Stripe PaymentMethod ID. The API Gateway must reject any request containing raw PANs, CVVs, or expiration dates.
- `directedImpact`: Optional. Allows donors to assign funds globally, regionally (zip code), or to specific merchant property types.

**Response Contract:**
- `id`: String (UUIDv4). Unique donation identifier.
- `status`: Enum. PENDING indicates the transaction is being processed by the Core Transaction & Ledger Service.
- `receiptUrl`: String. URL to the immutable transactional receipt, available within 120 seconds of redemption.
- `estimatedRedemptionTime`: Float. Estimated Donation-to-Redemption Velocity (DRV) in days.

### 1.2. Payment Gateway Adapter Integration Boundary (SUR-213BCD1816)

The integration boundary between the Client Application Layer (SUR-E3E75E96CF) and the Payment Gateway Adapter (SUR-213BCD1816) is the critical control point for PCI-DSS Level 1 compliance (CON-6EA64CF2A1).

#### 1.2.1. Tokenization Enforcement

- **Zero Raw Data Policy:** The Client Application Layer must never receive, store, or log raw credit card data. All payment instrument data must be tokenized client-side using Stripe Elements and SDK.
- **PaymentMethod ID Validation:** The GraphQL API Gateway must validate that the `paymentMethodId` provided in the `initiateDonation` mutation is a valid, active Stripe PaymentMethod ID before forwarding the request to the Core Transaction & Ledger Service.
- **Error Handling:** If a payment method is invalid or declined, the API Gateway must return a standardized `PaymentMethodError` type, masking any raw decline reasons from the issuing bank to prevent information leakage.

#### 1.2.2. Virtual Card Provisioning (Pseudo-AnonymizedRedemption)

For the Recipient Discovery & Redemption flow, the system generates single-use virtual card tokens.

- **Token Generation:** The Core Transaction & Ledger Service (SUR-DD602DB92C) issues a single-use virtual card token via the Stripe Issuing API. This token is locked to specific Merchant Category Codes (MCC) and location.
- **Anonymization:** The virtual card token is pushed to the Recipient's device as an Apple Wallet pass or barcode. No beneficiary PII is associated with the token in the application logs or database.
- **POS Clearing:** The token clears via standard banking networks, with PII stripped at the Stripe network layer.

### 1.3. Security & Compliance Posture

#### 1.3.1. Absolute Anonymization (CON-9DEA275205)

- **Beneficiary Data:** All beneficiary analytics must map to high-entropy UUIDv4 keys. No PII (legal name, demographic data) is stored on-platform or in production logs.
- **Receipt Generation:** Donors receive immutable transactional receipts within 120 seconds of redemption. These receipts strictly prohibit the transmission of any identifying beneficiary parameters.

#### 1.3.2. PCI-DSS Level 1 Adherence (CON-6EA64CF2A1)

- **Scope Reduction:** By ensuring zero raw credit card data touches application servers, the PCI-DSS scope is significantly reduced. The Client Application Layer is treated as a pass-through for Stripe tokens.
- **Audit Trail:** All payment method validations and token issuances are logged to the append-only, cryptographic audit ledger in Aurora Postgres (CON-199A4FEDC7) for SOC2 Type II compliance.

### 1.4. Identity & Access Management (IAM) Boundaries

The Client Application Layer (SUR-E3E75E96CF) enforces strict role-based access control (RBAC) to ensure that Contributors (ACT-2A20B038B1), Recipients (ACT-DC00FA84DC), and Operators (ACT-FE96DD3975) can only access data and functions appropriate to their roles.

#### 1.4.1. Authentication & Authorization

- **Authentication:** All API requests must be authenticated using short-lived JWTs issued by the Identity & Access Management capability (CAP-361A59708B). Tokens must be validated against the central identity provider before any business logic is executed.
- **Authorization:** The API Gateway must enforce RBAC policies. For example, only Recipients (ACT-DC00FA84DC) can invoke the `generateRedemptionToken` mutation, while only Contributors (ACT-2A20B038B1) can invoke `initiateDonation`.

#### 1.4.2. Session Management

- **Token Rotation:** JWTs must be rotated upon sensitive actions (e.g., funding a new payment method) to prevent session hijacking.
- **Revocation:** Operators (ACT-FE96DD3975) must be able to revoke tokens for compromised accounts immediately, with revocation propagated to the API Gateway within 5 seconds.

### 1.5. Error Handling & Resilience

#### 1.5.1. Standardized Error Responses

All API errors must conform to a standardized schema to ensure consistent client-side handling:

- {'code': 'PAYMENT_DECLINED', 'message': 'The payment method was declined by the issuing bank.', 'details': {'stripe_error_code': 'card_declined'}}

#### 1.5.2. Circuit Breakers & Fallbacks

- **Circuit Breakers:** The API Gateway must implement circuit breakers for downstream services (e.g., Stripe Issuing, Aurora Postgres) to prevent cascading failures.
- **Fallbacks:** In the event of a Stripe Issuing outage, the system must degrade gracefully by returning a `SERVICE_UNAVAILABLE` error to the client, with a clear message indicating that redemptions are temporarily paused.

### 1.6. Integration with Core Transaction & Ledger Service (SUR-DD602DB92C)

The Client Application Layer (SUR-E3E75E96CF) communicates with the Core Transaction & Ledger Service (SUR-DD602DB92C) via asynchronous gRPC calls for financial integrity.

#### 1.6.1. gRPC Contract for Donation Processing

protobuf
service TransactionService {
 rpc ProcessDonation (DonationRequest) returns (DonationResponse);
 rpc GenerateRedemptionToken (RedemptionRequest) returns (RedemptionResponse);
}

message DonationRequest {
 string contributor_id = 1;
 string payment_method_id = 2;
 int32 amount_cents = 3;
 DirectedImpact directed_impact = 4;
}

message DonationResponse {
 string donation_id = 1;
 DonationStatus status = 2;
 string receipt_url = 3;
}

message RedemptionRequest {
 string recipient_id = 1;
 string merchant_id = 2;
 float amount_cents = 3;
}

message RedemptionResponse {
 string token_id = 1;
 string token_value = 2;
 string wallet_pass_url = 3;
}

#### 1.6.2. POS Callback Handling

The Core Transaction & Ledger Service (SUR-DD602DB92C) exposes a gRPC endpoint for POS partners to submit redemption callbacks. This ensures that financial transactions are recorded in the append-only ledger (CON-199A4FEDC7) before the merchant is notified of success.

protobuf
service PosCallbackService {
 rpc SubmitRedemption (RedemptionCallback) returns (RedemptionCallbackResponse);
}

message RedemptionCallback {
 string token_id = 1;
 string merchant_id = 2;
 float amount_cents = 3;
 string transaction_hash = 4;
}

message RedemptionCallbackResponse {
 bool success = 1;
 string error_message = 2;
}

### 1.7. Data Models & Persistence

#### 1.7.1. Append-Only Audit Ledger (Aurora Postgres)

All financial transactions must be recorded in an append-only, cryptographic audit ledger in Aurora Postgres (CON-199A4FEDC7). This ledger is immutable and serves as the source of truth for SOC2 Type II compliance.

**Ledger Schema:**
- `transaction_id`: UUIDv4 (Primary Key)
- `timestamp`: TIMESTAMP WITH TIME ZONE
- `actor_id`: UUID (Contributor, Recipient, or Merchant Partner)
- `transaction_type`: ENUM (DONATION, REDEMPTION, REFUND)
- `amount_cents`: BIGINT
- `currency`: VARCHAR(3)
- `metadata`: JSONB (Anonymized, high-entropy)
- `hash_chain`: VARCHAR (SHA-256 hash of previous transaction)

#### 1.7.2. High-Throughput State Store (DynamoDB)

Amazon DynamoDB is used for sub-10ms transactional state management, such as tracking active virtual card tokens and contributor funding statuses.

**DynamoDB Schema:**
- `partition_key`: `actor_id#type` (e.g., `ACT-DC00FA84DC#TOKEN`)
- `sort_key`: `token_id` (UUIDv4)
- `attributes`: `status`, `expiry_timestamp`, `merchant_id`, `amount_cents`

### 1.8. Cross-Metro Event-Driven State Transitions

The system leverages a hybrid event-driven architecture to ensure consistency across the 3 initial metropolitan footprints (SF, NYC, Chicago). Events are published to a central event bus and consumed by regional services.

**Event Schema:**

- **event_id**: UUIDv4
- **event_type**: DONATION_COMPLETED
- **timestamp**: ISO8601
- **payload**: {'donation_id': 'UUIDv4', 'contributor_id': 'UUIDv4', 'amount_cents': 1000, 'region': 'SF'}

**Event Bus Protocol:**
- The specific event bus technology (e.g., Kafka vs. SQS) is deferred to a sibling artifact; Design phase should specify the chosen event bus technology to ensure cross-metro consistency.

### 1.9. Merchant Partner (ACT-A14D3CDC5D) Integration

Merchant Partners (ACT-A14D3CDC5D) interact with the system via a zero-footprint POS integration or edge dashboard. The system must validate virtual card tokens against Stripe Issuing in real-time.

**POS Integration Contract:**
- **Token Validation:** The POS system sends the virtual card token to the Core Transaction & Ledger Service (SUR-DD602DB92C) for validation.
- **Response:** The service returns a `VALID` or `INVALID` status, along with the authorized amount.
- **Settlement:** Funds are settled to the Merchant Partner (ACT-A14D3CDC5D) via Stripe Connect, with payouts occurring within 24 hours of redemption.

### 1.10. Operator (ACT-FE96DD3975) Governance & Liquidity Management

Operators (ACT-FE96DD3975) use the system to monitor liquidity pools and manage regional allocations. The API must provide real-time dashboards for Credit Pool Utilization Rate and Donation-to-Redemption Velocity (DRV).

**Operator API Endpoints:**
- `GET /api/v1/liquidity/pools`: Returns real-time credit pool balances by region.
- `POST /api/v1/liquidity/transfer`: Allows Operators to transfer credits between regional pools.
- `GET /api/v1/metrics/drv`: Returns real-time DRV metrics.

### 1.11. Compliance & Audit Governance (CAP-421F3AD853)

All system activities must be logged to AWS CloudTrail (CON-0B2D40801A) for infrastructure and administrative changes. Application-level logs must be anonymized and stored in S3 with strict access controls.

**Audit Log Requirements:**
- **Immutability:** Logs must be stored in a WORM (Write Once, Read Many) bucket.
- **Retention:** Logs must be retained for a minimum of 7 years to comply with financial regulations.
- **Access:** Access to audit logs must be restricted to Operators (ACT-FE96DD3975) and external auditors.

### 1.12. Scalability & Performance

The system must handle bursty traffic patterns during peak donation cycles or redemption events without degrading latency.

**Performance Targets:**
- **API Responsiveness:** p99 latency below 250ms under 10,000 concurrent connections (CON-14D783B5E5).
- **Cache Hit Ratio:** Redis Enterprise Cluster cache hit ratio for restaurant search queries must exceed 92% (CON-42B7E9919E).
- **Operational Uptime:** 99.99% operational uptime across AWS multi-AZ configurations (CON-8BD1F56A44).

### 1.13. Knowledge Gaps & Assumptions

- **KNOWLEDGE_GAP:** The specific event bus technology (e.g., Kafka vs. SQS) for cross-metro event-driven state transitions is not yet established. This decision must be made by the Technical Architecture artifact to ensure cross-metro consistency.
- **ASSUMPTION:** The system will rely solely on Stripe's backend merchant-category-code (MCC) and geo-fencing rules for virtual card limit enforcement, without requiring a pre-authorization validation step from the Dayaa backend. This assumption is reversible pending DEC-BDB9EA01B2 resolution.
- **ASSUMPTION:** The system will store a time-bound, signed JWT voucher on the client's SecureStore for offline redemption resilience, requiring network connectivity for verification. This assumption is reversible pending DEC-7E9F9E778C resolution.
- **KNOWLEDGE_GAP:** The specific POS integration middleware strategy (e.g., Stripe Square POS vs. custom gRPC adapters for Toast/Clover) is not yet established. This decision must be made by the Integration & Payment Gateway Adapter artifact.

### 1.14. Follow-Up Questions

- **Question:** What transport-security version requirement is binding for this project?
- **Question:** What retention period is binding for this record class?
- **Question:** Which specific POS integration middleware strategy will be adopted?
- **Question:** Should the virtual card limit enforcement rely solely on Stripe's backend rules or require a pre-authorization validation step?
- **Question:** For offline redemption resilience, should the system store a time-bound, signed JWT voucher or implement a complex offline-counter mechanism?
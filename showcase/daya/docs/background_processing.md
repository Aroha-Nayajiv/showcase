# Background Processing & Async Workers

## 1. Asynchronous API Gateway & Orchestration Layer Contract

This artifact defines the asynchronous orchestration contract for the API Gateway & Orchestration Layer (SUR-D6FFF7036F), specifically focusing on the entry points for the Contributor Primary Transaction Flow (JNY-4FC1874968). The design decouples high-throughput UI data retrieval from the financial transaction processing pipeline, ensuring PCI-DSS Level 1 compliance by ensuring zero raw credit card data touches application servers, using only Stripe Elements and SDK.

### 1.1 Architectural Rationale & Trade-offs

The system utilizes a hybrid architecture: high-throughput CRUD over GraphQL for UI state, and asynchronous gRPC services for financial transactions. This decoupling is critical for maintaining p99 latency below 250ms for Voucher Creation and Scanning Callback Processing under 10,000 concurrent connections (CON-14D783B5E5). Synchronous processing of financial transactions would block the UI and degrade latency during peak donation cycles (CON-873877C003). The trade-off is eventual consistency for transaction status, which is acceptable for financial flows where durability and idempotency are prioritized over immediate UI updates.

### 1.2 GraphQL Entry Points for High-Throughput UI Data

The GraphQL schema exposes read-only queries for high-frequency UI updates, such as contributor balance, transaction history, and donation round-up configurations. These queries are served from a denormalized cache or read-model to ensure sub-10ms response times.

**Query: contributorTransactionHistory**
- **Purpose:** Retrieve paginated transaction history for a Contributor (ACT-2A20B038B1).
- **Input:** `contributorId: ID!`, `cursor: String`, `limit: Int = 20`.
- **Output:** TransactionHistoryConnection containing edges (TransactionNode) and pageInfo.
- **Data Source:** DynamoDB (high-throughput UI state) for recent transactions; Aurora Postgres (append-only cryptographic audit ledger) for historical reconciliation if needed.
- **Constraints:** Must not return raw payment instrument details. Only transaction IDs, amounts, timestamps, and status.

**Query: donorRoundUpConfiguration**
- **Purpose:** Retrieve the current round-up configuration for a Contributor.
- **Input:** `contributorId: ID!`.
- **Output:** RoundUpConfiguration object (enabled: Boolean, targetPool: String, minRoundUp: Float).
- **Data Source:** DynamoDB.

### 1.3 Event Triggers for Contributor Primary Transaction Flow (JNY-4FC1874968)

The Contributor Primary Transaction Flow is initiated via a GraphQL mutation that triggers an asynchronous event. This mutation does not process the financial transaction directly but enqueues it for the async worker pool.

**Mutation: initiateMicroDonationRoundUp**
- **Purpose:** Trigger the calculation and transfer of a micro-donation round-up from a Contributor's linked external transaction.
- **Input:**
  - `contributorId: ID!`: The ID of the Contributor (ACT-2A20B038B1).
  - `externalTransactionId: ID!`: The ID of the external transaction (from Plaid/Stripe) to round up.
  - `idempotencyKey: String!`: A unique key to prevent duplicate processing.
- **Output:** TransactionInitiationResult.
  - `requestId: ID!`: A unique ID for tracking the asynchronous request.
  - `status: TransactionStatus!`: Initial status (e.g., PENDING).
  - `estimatedCompletionTime: ISO8601DateTime`: Estimated time for completion.
- **Behavior:**
  1. Validate the contributorId and externalTransactionId.
  2. Check for duplicate idempotencyKey to prevent double-charging.
  3. Create a TransactionRequest record in DynamoDB with status PENDING.
  4. Publish an event MicroDonationRoundUpInitiated to the event bus (e.g., AWS EventBridge/SNS/SQS).
  5. Return the TransactionInitiationResult immediately.

**Event: MicroDonationRoundUpInitiated**
- **Payload:**
  - `requestId: ID!`
  - `contributorId: ID!`
  - `externalTransactionId: ID!`
  - `idempotencyKey: String!`
  - `timestamp: ISO8601DateTime`
- **Consumer:** Async Worker Pool (gRPC service boundary for Financial Transaction Processing (CAP-9CD814929D)).

### 1.4 Idempotency and Error Handling

To ensure financial reconciliation is robust against partial failures, ensuring that credits issued but not cleared do not leave the ledger in an inconsistent state (CON-6A9F6E50CE), all transaction mutations must enforce strict idempotency.

- **Idempotency Key:** The idempotencyKey provided in the mutation input is used to check for existing completed transactions. If a transaction with the same key is already COMPLETED, the mutation returns the existing result without reprocessing.
- **Error Handling:** If the async worker fails to process the event, it will retry with exponential backoff. If it exceeds the maximum retry count, the event is moved to a Dead-Letter Queue (DLQ) for manual intervention. The TransactionRequest status in DynamoDB is updated to FAILED with an error code.

### 1.5 Dual-Database Write Strategy (DynamoDB & Aurora Postgres)

The system employs a dual-database write strategy to balance high-velocity event logging with cryptographic audit integrity. This section defines the synchronization and conflict resolution patterns between the two stores.

- **Write Path:**
  1. **Aurora Postgres (Append-Only Ledger):** All financial transactions are first written to an append-only table in Aurora Postgres (CON-199A4FEDC7). This table serves as the source of truth for financial reconciliation and regulatory compliance. Writes are synchronous to ensure durability before the event is published.
  2. **DynamoDB (High-Velocity State):** A message is published to the event bus, which triggers an async worker to update the DynamoDB table. This table holds the denormalized, high-velocity state used for UI queries and real-time balance checks.

- **Synchronization & Conflict Resolution:**
  - **Reconciliation Worker:** A background reconciliation worker runs on a scheduled interval (e.g., every 5 minutes) to compare the Aurora Postgres ledger against the DynamoDB state. 
  - **Conflict Resolution Strategy:** In the event of a divergence (e.g., DynamoDB update fails or is delayed), the Aurora Postgres ledger is treated as the authoritative source. The reconciliation worker will re-process the failed DynamoDB updates. If a transaction exists in Aurora but not in DynamoDB, it is backfilled. If a transaction exists in DynamoDB but not in Aurora, it is flagged as an anomaly and moved to a quarantine queue for manual review.
  - **72-Hour Credit Rollback:** Unused emergency credits must automatically roll back to the central regional pool after 72 hours of expiration to prevent ledger stagnation. This is enforced by a scheduled Lambda function that queries Aurora Postgres for expired credits and triggers a reversal event in the async worker pool.

### 1.6 Knowledge Gaps

- `KNOWLEDGE_GAP: event_bus_protocol - The specific event bus protocol (e.g., AWS EventBridge, SNS/SQS) and event schema version must be established by the Event Bus & Message Queue Design artifact.`
- `KNOWLEDGE_GAP: async_worker_implementation - The specific gRPC service implementation details for the Financial Transaction Processing (CAP-9CD814929D) are deferred to the gRPC Financial Transaction Contract artifact.`

### 2.1 Service Definition: FinancialTransactionService

The FinancialTransactionService is a high-throughput, stateless gRPC service responsible for processing financial events. It communicates with the Aurora Postgres ledger and the Stripe Issuing API.

**Service: FinancialTransactionService**

**RPC: ProcessDonation**
- **Purpose:** Process a micro-donation round-up event and update the ledger.
- **Request:**
  - `requestId: string`
  - `contributorId: string`
  - `amount: double`
  - `currency: string`
  - `idempotencyKey: string`
- **Response:**
  - `transactionId: string`
  - `status: TransactionStatus`
  - `timestamp: string`
- **Error Codes:**
  - `ALREADY_PROCESSED`: Idempotency key conflict.
  - `INVALID_AMOUNT`: Amount is below minimum threshold.
  - `LEDGER_WRITE_FAILURE`: Aurora Postgres write failed.

**RPC: IssueVirtualCard**
- **Purpose:** Issue a single-use virtual card token for a beneficiary redemption.
- **Request:**
  - `beneficiaryId: string` (Anonymized UUIDv4)
  - `merchantId: string`
  - `amount: double`
  - `currency: string`
  - `redemptionToken: string`
- **Response:**
  - `virtualCardToken: string`
  - `expiryTime: string`
  - `status: CardStatus`
- **Error Codes:**
  - `INSUFFICIENT_FUNDS`: Beneficiary credit pool is empty.
  - `MERCHANT_NOT_ELIGIBLE`: Merchant does not meet MCC criteria.
  - `STRIPE_ISSUING_FAILURE`: Stripe API call failed.

**RPC: ReconcileLedger**
- **Purpose:** Trigger a reconciliation check between Aurora Postgres and DynamoDB.
- **Request:**
  - `batchId: string`
  - `startTime: string`
  - `endTime: string`
- **Response:**
  - `reconciliationId: string`
  - `discrepancies: int`
  - `status: ReconciliationStatus`

### 2.2 Data Models & Schemas

**TransactionRequest**
- `requestId: string` (UUIDv4)
- `contributorId: string` (UUIDv4)
- `externalTransactionId: string`
- `amount: double`
- `currency: string`
- `status: TransactionStatus` (PENDING, COMPLETED, FAILED)
- `idempotencyKey: string`
- `timestamp: ISO8601DateTime`

**VirtualCardToken**
- `token: string` (Single-use, encrypted)
- `beneficiaryId: string` (Anonymized UUIDv4)
- `merchantId: string`
- `amount: double`
- `currency: string`
- `expiryTime: ISO8601DateTime`
- `status: CardStatus` (ACTIVE, USED, EXPIRED)

### 2.3 Error Handling & Retries

- **Retry Policy:** gRPC calls to Stripe Issuing API will retry with exponential backoff (max 3 retries) for transient errors (e.g., 5xx, rate limits).
- **Dead-Letter Queue (DLQ):** Events that fail after max retries are moved to a DLQ for manual intervention. The TransactionRequest status in DynamoDB is updated to FAILED.
- **Idempotency:** All financial mutations are idempotent, using the `idempotencyKey` to prevent duplicate processing.

### 2.4 Performance & Scalability

- **p99 Latency:** The system must maintain p99 latency below 250ms for Voucher Creation and Scanning Callback Processing under 10,000 concurrent connections (CON-14D783B5E5).
- **Throughput:** The gRPC service must handle bursty traffic patterns during peak donation cycles or redemption events without degrading latency (CON-873877C003).
- **Caching:** Redis Enterprise Cluster cache hit ratio for restaurant search queries must exceed 92% (CON-42B7E9919E).

### 2.5 Monitoring & Observability

- **Donation-to-Redemption Velocity (DRV):** Monitor DRV and Credit Pool Utilization Rate with automated alerts at 85% threshold (CON-AA14245C03).
- **Stripe Webhook Processing Latency:** Track Stripe Webhook Processing Latency with a target average below 150ms for merchant ledger entry clearance (CON-D792CA1810).
- **Operational Uptime:** Achieve 99.99% operational uptime across AWS multi-AZ configurations with graceful degradation if POS partners fail (CON-8BD1F56A44).

### 2.6 Sibling Dependencies

- **API Gateway & Orchestration Layer (SUR-D6FFF7036F):** Defines the entry points for the Contributor Primary Transaction Flow (JNY-4FC1874968).
- **Core Transaction & Ledger Service (SUR-DD602DB92C):** Defines the data models and persistence strategy for the Aurora Postgres ledger.
- **Integration & Payment Gateway Adapter (SUR-213BCD1816):** Defines the integration with Stripe Issuing API for virtual card issuance.

## 3. Serverless Function Boundaries for Contributor Flow

This section defines the serverless function boundaries for the Contributor Primary Transaction Flow (JNY-4FC1874968), specifically focusing on the micro-donation round-up calculation and funding logic.

### 3.1 Function: CalculateRoundUp

- **Purpose:** Calculate the fractional contribution based on the Contributor's configured round-up rules.
- **Input:** `externalTransactionId: string`, `contributorId: string`.
- **Output:** `roundUpAmount: double`.
- **Logic:**
  1. Retrieve the Contributor's round-up configuration from DynamoDB.
  2. Fetch the external transaction details from Plaid/Stripe.
  3. Calculate the round-up amount (e.g., round up to nearest $1, $5, $10).
  4. Return the calculated amount.

### 3.2 Function: FundCreditPool

- **Purpose:** Transfer the calculated round-up amount from the Contributor's linked payment method to the central credit pool.
- **Input:** `contributorId: string`, `roundUpAmount: double`, `idempotencyKey: string`.
- **Output:** `transactionId: string`.
- **Logic:**
  1. Validate the idempotencyKey to prevent duplicate funding.
  2. Initiate a payment transfer via Stripe API.
  3. Update the TransactionRequest status in DynamoDB to COMPLETED.
  4. Publish a Funded event to the event bus.

## 4. Operational Governance & Success Criteria

This section defines the operational governance and success criteria for the asynchronous processing backbone, ensuring alignment with the project's compliance and performance goals.

### 4.1 Success Criteria

- **Donation-to-Redemption Velocity (DRV):** Under 14 days.
- **Merchant Retention Rate (MRR):** Measured month-over-month.
- **Credit Pool Utilization Rate:** Alerts triggered if above 85%.
- **Stripe Webhook Processing Latency:** Average below 150ms.
- **Cache Hit Ratio (CHR):** For restaurant search queries above 92%.
- **API Responsiveness:** p99 latency below 250ms under 10,000 concurrent connections.
- **Operational Uptime:** 99.99% across AWS multi-AZ configurations.

### 4.2 Compliance & Audit

- **SOC2 Type II:** Operate within SOC2 Type II control environments, generating detailed tracking logs for all infrastructure and administrative changes (CON-0A6423E6B0).
- **PCI-DSS Level 1:** Enforce PCI-DSS Level 1 by ensuring zero raw credit card data touches application servers (CON-6EA64CF2A1).
- **Audit Trail:** Push all infrastructure modifications and administrative ledger operations to unalterable AWS CloudTrail logs (CON-0B2D40801A).
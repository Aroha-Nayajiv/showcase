# Financial Reconciliation & Payout Workers

### 1.1 TransactionSettledEvent

The TransactionSettledEvent is published by the Stripe Issuing Proxy Contract upon successful completion of a POS clearance. It serves as the primary trigger for the Financial Reconciliation Engine to update the internal ledger.

Schema Definition:

{
 "$schema": "http://json-schema.org/draft-07/schema#",
 "type": "object",
 "required": [
 "event_id",
 "event_type",
 "timestamp",
 "version",
 "settlement_id",
 "correlation_id",
 "merchant_id",
 "amount_cents",
 "currency",
 "stripe_payment_intent_id",
 "metadata"
 ],
 "properties": {
 "event_id": {
 "type": "string",
 "description": "Unique identifier for this event instance, used for idempotency checks."
 },
 "event_type": {
 "type": "string",
 "description": "The specific type of financial event."
 },
 "timestamp": {
 "type": "string",
 "description": "ISO 8601 timestamp of when the event was generated."
 },
 "version": {
 "type": "string",
 "description": "Schema version for backward compatibility."
 },
 "settlement_id": {
 "type": "string",
 "description": "Unique identifier for the settlement batch this transaction belongs to."
 },
 "correlation_id": {
 "type": "string",
 "description": "UUIDv4 mapping to correlate donor impact receipts with beneficiary redemption events without linking PII."
 },
 "merchant_id": {
 "type": "string",
 "description": "Identifier for the Merchant actor."
 },
 "amount_cents": {
 "type": "integer",
 "description": "Transaction amount in cents."
 },
 "currency": {
 "type": "string",
 "description": "ISO 4217 currency code."
 },
 "stripe_payment_intent_id": {
 "type": "string",
 "description": "Stripe PaymentIntent ID for reconciliation."
 },
 "metadata": {
 "type": "object",
 "description": "Additional context, including geo-location and device info."
 }
 }
}

Key Design Decisions:
Idempotency: The event_id is used as the primary idempotency key in the reconciliation worker to prevent duplicate ledger mutations. Anonymization: The correlation_id is a UUIDv4 that maps to beneficiary data without exposing PII, adhering to [CON-23A501C051](../project_glossary.md#con-23a501c051). Traceability: The stripe_payment_intent_id links the internal event to the external Stripe transaction for audit purposes.

### 1.3 Schema Registry and Versioning

To ensure backward compatibility and strict data isolation, all events are registered in a Schema Registry (e.g., Confluent Schema Registry). The version field in each event payload allows consumers to handle schema evolution gracefully. Any breaking changes to the schema must be accompanied by a version bump and a migration plan for existing consumers.

Versioning Strategy:
Major Version: Breaking changes (e.g., removing fields, changing types). Minor Version: Additive changes (e.g., adding new optional fields). Patch Version: Non-breaking changes (e.g., documentation updates).

This approach ensures that the Financial Reconciliation & Payout Workers can evolve independently while maintaining compatibility with downstream consumers.

---

### 2.1 Ingestion and Idempotency Contract

The engine exposes a secure ingestion endpoint (e.g., /api/v1/webhooks/stripe) that acts as the sole entry point for financial events. To prevent replay attacks and handle network retries, the engine enforces a strict idempotency model.

Signature Verification: Every incoming request must include a valid Stripe-Signature header. The engine verifies this against the stored webhook signing secret. Requests failing verification are immediately rejected with a 401 Unauthorized to prevent spoofing. Idempotency Key: The id field from the Stripe Event payload (e.g., evt_123456) serves as the global idempotency key. The engine maintains a processed_events registry (backed by the Financial Ledger Data Model artifact) to track these keys. Deduplication Logic: Upon ingestion, the engine queries the registry for the event ID. If found, the event is acknowledged to Stripe with a 200 OK and processing is skipped. If not found, the event is queued for processing, and the ID is immediately registered to prevent race conditions during concurrent processing.

### 2.2 Event Normalization and Ledger Matching

Once validated, the Stripe event is normalized into a platform-agnostic FinancialEvent schema. This step decouples the engine from Stripe-specific payload structures, allowing for future payment provider integration.

Event Mapping: The engine maps Stripe event types (e.g., charge.succeeded, charge.refunded, charge.dispute.created) to internal ledger actions. Ledger Correlation: The engine uses the metadata.stripe_payment_intent_id to locate the corresponding [CAP-TRANSACTION-FINANCIAL-ENGINE](../project_glossary.md#cap-transaction-financial-engine) ledger entry. This entry must exist in a PENDING or SETTLED state. If no matching ledger entry is found, the event is routed to a RECONCILIATION_ERROR queue for manual review by the Platform Administrator.

### 2.3 Deterministic State Transitions and Edge Case Handling

The core of the reconciliation logic is a deterministic state machine that governs the lifecycle of a financial transaction. This ensures that edge cases like double-spending and voided transactions are handled consistently.

#### 2.3.1. Transaction Lifecycle States

1. PENDING: The transaction has been initiated (e.g., POS tap) but not yet confirmed by Stripe.
2. SETTLED: Stripe has confirmed the charge (charge.succeeded). The funds are reserved in the CAP-TRANSACTION-FINANCIAL-ENGINE ledger.
3. RECONCILED: The internal ledger entry has been successfully matched and updated. The transaction is now eligible for the Payout Orchestration Service.
4. REFUNDED: A full or partial refund has been processed (charge.refunded). The ledger is updated to reflect the credit.
5. DISPUTED: A chargeback has been initiated (charge.dispute.created). The ledger is frozen, and the Dispute Adjudicator workflow is triggered.
6. VOIDED: The transaction was cancelled before capture (payment_intent.canceled). The ledger entry is marked as void and excluded from reconciliation.

#### 2.3.2. Double-Spending Prevention

To prevent double-spending, the engine enforces a strict "one-event-per-ledger-entry" rule. The Financial Ledger Data Model artifact defines the ledger entry schema, which includes a version column for optimistic locking. When the engine attempts to transition a ledger entry from SETTLED to RECONCILED, it checks the version. If the version has changed (indicating a concurrent update), the transaction is retried with exponential backoff. If retries are exhausted, the event is flagged for manual intervention.

#### 2.3.3. Voided Transactions and Refunds

Voided Transactions: If a payment_intent.canceled event is received for a PENDING transaction, the engine immediately marks the ledger entry as VOIDED. No further reconciliation or payout is possible for this entry. Refunds: If a charge.refunded event is received, the engine calculates the refund amount and updates the ledger entry's net_amount. If the refund is partial, the ledger entry remains RECONCILED but with a reduced balance. If the refund is full, the ledger entry is marked as REFUNDED.

### 2.4 Error Handling and Retry Policy

The engine implements a robust error handling strategy to ensure no financial event is lost.

Transient Errors: Network timeouts or database locks result in a 503 Service Unavailable response to Stripe. The engine retries the processing with exponential backoff (up to 3 attempts). Permanent Errors: Invalid event structures or unrecoverable state mismatches result in a 400 Bad Request response. The event is logged to the Distributed Tracing & Log Aggregation system and flagged for manual review. Dead Letter Queue (DLQ): Events that fail after all retries are moved to a DLQ. The Platform Administrator can inspect and reprocess these events via the Next.js Dashboard.

### 2.5 Integration Points and Dependencies

Upstream: Stripe Issuing Proxy Contract (for webhook ingestion). Downstream: Financial Ledger Data Model (for state updates), Payout Orchestration Service (for triggering payouts upon RECONCILED status). External: Stripe API (for event ingestion and signature verification).

## 3. Payout Orchestration Service

The Payout Orchestration Service is the deterministic engine responsible for aggregating settled financial transactions into daily payout batches for Merchant actors. It operates as a scheduled, event-driven workflow that bridges the internal financial ledger with the external Stripe Connected Account infrastructure, ensuring strict compliance with jurisdictional KYC requirements and automated error handling.

### 3.1 Architectural Workflow

The service operates on a scheduled batch cycle, triggered by a scheduled event (e.g., AWS EventBridge cron) at a configurable time (e.g., 02:00 UTC). The workflow consists of four deterministic phases:

1. Ledger Snapshot & Aggregation: The service queries the Financial Ledger for all transactions in a SETTLED state within the previous 24-hour window. It groups these transactions by merchant_id and stripe_connected_account_id.
2. Jurisdictional Routing & Compliance Check: Before generating a payout, the service validates the merchant's KYC status and jurisdictional constraints. This step ensures that payouts are only initiated for merchants who have passed the Implied concern: Manage Stripe Connected Account liability and KYC compliance across multiple jurisdictions (SF, NYC, Chicago).
3. Stripe Payout Creation: The service invokes the Stripe API to create a payout object for each eligible merchant. The payout amount is calculated as the sum of settled transactions minus any applicable platform fees or chargeback reserves.
4. State Transition & Confirmation: Upon successful API response, the service updates the transaction records to PAYOUT_INITIATED and publishes a PayoutInitiatedEvent to the event bus for downstream reconciliation.

### 3.2 Integration with Stripe Connected Accounts

The service interacts with Stripe via a dedicated StripePayoutAdapter interface. This adapter abstracts the Stripe API calls and handles authentication using the platform's master Stripe API key, scoped to the specific Stripe Connected Account of each merchant.

API Contract: Payout Creation

{
 "endpoint": "POST /api/v1/v1/payouts",
 "request": {
 "stripe_account_id": "string (UUIDv4)",
 "amount_cents": "integer",
 "currency": "string (ISO 4217)",
 "metadata": {
 "batch_id": "string (UUIDv4)",
 "settlement_period_end": "ISO 8601"
 }
 },
 "response": {
 "payout_id": "string (Stripe ID)",
 "status": "string",
 "expected_arrival_date": "integer (unix timestamp)"
 }
}

Idempotency: All Stripe API calls must include an idempotency key derived from the batch_id and merchant_id to prevent duplicate payouts in case of network retries.

### 3.3 Jurisdictional Routing Logic

To address the Implied concern: Manage Stripe Connected Account liability and KYC compliance across multiple jurisdictions (SF, NYC, Chicago), the Payout Orchestration Service implements a jurisdictional routing matrix. This matrix is driven by the merchant's registered business address and the corresponding Stripe Connected Account's country.

Routing Rules:

| Jurisdiction | KYC Requirement | Payout Frequency | Reserve Policy |
|---|---|---|---|
| US (SF, NYC, Chicago) | Full KYC (SSN/EIN) | [KNOWLEDGE_GAP: Payout frequency (e.g., T+1, T+2) not established in project truth - Platform Administrator must define] | [KNOWLEDGE_GAP: Reserve policy percentage not established in project truth - Platform Administrator must define] |
| International | Enhanced Due Diligence | [KNOWLEDGE_GAP: Payout frequency (e.g., T+7) not established in project truth - Platform Administrator must define] | [KNOWLEDGE_GAP: Reserve policy percentage not established in project truth - Platform Administrator must define] |

Implementation:
The service must query the MerchantProfile data model (owned by User State & Profile Data Model) to retrieve the merchant's jurisdiction and kyc_status. If the kyc_status is not VERIFIED, the merchant is excluded from the current batch and flagged for manual review.

### 3.4 Payout Failure Retry Mechanisms

The service must implement a robust retry mechanism for failed Stripe API calls or Stripe-side payout failures. This is critical for maintaining financial consistency and ensuring merchants are paid promptly.

Retry Policy:

Initial Failure: If the Stripe API returns a transient error (e.g., 502 Bad Gateway, 429 Too Many Requests), the service will retry the payout creation after a fixed delay of 5 minutes. Persistent Failure: If the payout fails after 3 retries, the transaction is marked as PAYOUT_FAILED and a PayoutFailureEvent is published to the event bus. This event triggers the Merchant Payout Failure & Error Handling workflow (owned by sibling artifact). Manual Intervention: Payouts that fail due to non-transient errors (e.g., insufficient_funds, account_closed) require manual intervention by a Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)). The service will not automatically retry these cases.

Error Handling Contract:

{
 "event_type": "PayoutFailureEvent",
 "payload": {
 "merchant_id": "string (UUIDv4)",
 "payout_batch_id": "string (UUIDv4)",
 "error_code": "string",
 "error_message": "string",
 "is_transient": "boolean"
 }
}

### 3.5 Observability and Monitoring

The Payout Orchestration Service must emit metrics and logs to support operational monitoring. Key metrics include:

payout_batch_duration: Time taken to process a single batch. payout_success_rate: Percentage of successful payouts per batch. payout_failure_count: Number of failed payouts per batch, categorized by error type. stripe_api_latency: Latency of Stripe API calls.

Logs must include the batch_id, merchant_id, and stripe_payout_id (if available) to enable traceability across the system.

## 4. Aurora PostgreSQL Financial Ledger Data Models

This section defines the immutable, append-only data models for the Financial Reconciliation & Payout Workers. These schemas enforce strict ACID compliance, cryptographic audit trails, and disaster recovery consistency for the MealCredit platform.

### 4.1 Financial Ledger Schema

The core ledger table stores every financial mutation as an immutable record. This design supports the Implied concern: Implement append-only cryptographic log auditing in Aurora PostgreSQL for all financial ledger mutations.

Schema Definition:

{
 "table_name": "financial_ledger",
 "columns": {
 "ledger_id": {
 "type": "UUID",
 "primary_key": true,
 "description": "Unique identifier for the ledger entry."
 },
 "event_id": {
 "type": "STRING",
 "unique": true,
 "description": "Corresponds to the idempotency key from the event bus."
 },
 "merchant_id": {
 "type": "UUID",
 "description": "Foreign key to the Merchant actor."
 },
 "transaction_type": {
 "type": "ENUM",
 "values": ["SETTLED", "REFUNDED", "DISPUTED", "VOIDED"],
 "description": "Current state of the transaction."
 },
 "amount_cents": {
 "type": "BIGINT",
 "description": "Transaction amount in cents."
 },
 "currency": {
 "type": "STRING",
 "description": "ISO 4217 currency code."
 },
 "stripe_payment_intent_id": {
 "type": "STRING",
 "description": "External Stripe reference."
 },
 "correlation_id": {
 "type": "UUID",
 "description": "Anonymized mapping to beneficiary/donor impact."
 },
 "created_at": {
 "type": "TIMESTAMP",
 "default": "CURRENT_TIMESTAMP",
 "description": "Timestamp of ledger entry creation."
 },
 "updated_at": {
 "type": "TIMESTAMP",
 "default": "CURRENT_TIMESTAMP",
 "description": "Timestamp of last update."
 },
 "version": {
 "type": "INTEGER",
 "description": "Optimistic locking version for concurrent updates."
 }
 }
}

### 4.2 Processed Events Registry

To support idempotency and prevent duplicate processing, the engine maintains a registry of processed event IDs. This table is append-only and is periodically archived based on retention policies defined by the Platform Administrator.

Schema Definition:

{
 "table_name": "processed_events",
 "columns": {
 "event_id": {
 "type": "STRING",
 "primary_key": true,
 "description": "The unique Stripe event ID."
 },
 "processed_at": {
 "type": "TIMESTAMP",
 "default": "CURRENT_TIMESTAMP",
 "description": "Timestamp when the event was processed."
 },
 "status": {
 "type": "ENUM",
 "values": ["SUCCESS", "FAILED"],
 "description": "Outcome of the processing attempt."
 }
 }
}

### 4.3 Disaster Recovery & Consistency

To ensure financial ledger consistency in the event of infrastructure failure, the platform relies on Aurora PostgreSQL's multi-AZ deployment and automated backups. The specific retention period for financial records, Recovery Point Objective (RPO), and Recovery Time Objective (RTO) targets are not established in project truth and require Business Continuity owner confirmation.

KNOWLEDGE_GAP: Disaster Recovery - The specific retention period (e.g., 7 days), RPO, and RTO targets for the financial ledger are not established in project truth and require Business Continuity owner confirmation.

### 4.4 Data Retention and Archival

To comply with financial regulations governing quasi-cash instruments, specifically regarding unclaimed property and escheatment laws, the platform must define strict data retention policies for donor transaction history vs. anonymous redemption analytics. The minimum retention period and archival threshold for financial records are not established in project truth and must align with legal/regulatory requirements defined by the Platform Administrator.

KNOWLEDGE_GAP: Data Retention - The minimum retention period and archival threshold for financial records are not established in project truth and must align with legal/regulatory requirements defined by the Platform Administrator.

### 4.5 Cryptographic Audit Trail

To ensure SOC2 Type II structural planning is baked into the infrastructure-as-code and access control policies, all administrative ledger operations and infrastructure changes are logged to AWS CloudTrail for SOC2 Type II evidence. The financial_ledger table itself serves as the primary immutable audit trail for financial transactions.

### 4.6 Implied Concern: Classify all beneficiary-related data as 'Highly Sensitive' and restrict database access to cryptographic hashing layers only.

The correlation_id field in the financial_ledger table is a UUIDv4 that maps to beneficiary data without exposing PII. This ensures that beneficiary demographic status and legal names are cryptographically segregated from public transaction logs, adhering to CON-23A501C051 and [CON-2788862587](../project_glossary.md#con-2788862587).

### 5. Financial Ledger Design & Reconciliation Architecture

This section defines the immutable financial ledger schema, the reconciliation worker logic, and the automated payout orchestration contracts. The design ensures strict adherence to PCI-DSS Level 1 and SOC2 Type II requirements by maintaining an append-only audit trail and enforcing cryptographic integrity across all financial mutations.

#### 5.1 Immutable Ledger Entries (ledger_entries)

The `ledger_entries` table serves as the single source of truth for all financial mutations. It is designed to be append-only; rows are never updated or deleted. Instead, corrective entries (reversals) are appended to maintain a complete audit history. This design supports the Implied concern: Implied concern: Implement append-only cryptographic log auditing in Aurora PostgreSQL for all financial ledger mutations.

**Table Schema:**

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `entry_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier for the ledger entry. |
| `external_event_id` | VARCHAR(255) | NOT NULL, UNIQUE | The Stripe Event ID (e.g., `evt_123...`). Ensures idempotency; duplicate events are rejected. |
| `correlation_id` | UUID | NOT NULL | Links the entry to the original POS transaction or voucher redemption event. |
| `merchant_id` | UUID | NOT NULL, REFERENCES merchants(id) | The Merchant (Restaurant) associated with this financial event. |
| `entry_type` | ENUM | NOT NULL | Values: `SETTLEMENT`, `REFUND`, `CHARGEBACK`, `PAYOUT_ADJUSTMENT`. |
| `amount_cents` | BIGINT | NOT NULL | The monetary amount in minor units (e.g., USD cents). Positive for credits, negative for debits. |
| `currency` | CHAR(3) | NOT NULL, DEFAULT 'USD' | ISO 4217 currency code. |
| `status` | ENUM | NOT NULL, DEFAULT 'PENDING' | Values: `PENDING`, `COMMITTED`, `RECONCILED`, `FAILED`. |
| `ledger_hash` | CHAR(64) | NOT NULL | SHA-256 hash of the previous row's `entry_id` + `entry_type` + `amount_cents` + `external_event_id`. Forms the cryptographic chain. |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Timestamp of the ledger mutation. |
| `metadata` | JSONB | DEFAULT '{}' | Optional structured data for reconciliation notes or Stripe response payloads. |

**Immutability & Audit Constraints:**

1.  **Append-Only Enforcement:** A database trigger `prevent_ledger_modification` will block any `UPDATE` or `DELETE` operations on the `ledger_entries` table. Only `INSERT` is permitted.
2.  **Cryptographic Chain:** The `ledger_hash` column must be calculated on the client side or via a database function before insertion. The function verifies that the hash matches the previous row's hash, ensuring no rows have been tampered with or inserted out of sequence.
3.  **Idempotency Key:** The `external_event_id` is unique. Any attempt to insert a duplicate Stripe Event ID will result in a `409 Conflict` error, preventing double-counting of settlements.

#### 5.2 Payout Batches (payout_batches)

The `payout_batches` table tracks the aggregation of settled transactions into payout cycles for Merchants. This table is linked to the `ledger_entries` table via `correlation_id`.

**Table Schema:**

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `batch_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier for the payout batch. |
| `merchant_id` | UUID | NOT NULL, REFERENCES merchants(id) | The Merchant receiving the payout. |
| `batch_date` | DATE | NOT NULL | The date the batch was generated. |
| `total_amount_cents` | BIGINT | NOT NULL | Sum of all `SETTLEMENT` entries in this batch. |
| `stripe_transfer_id` | VARCHAR(255) | NULLABLE | The Stripe Transfer ID once the payout is initiated. |
| `status` | ENUM | NOT NULL, DEFAULT 'PENDING' | Values: `PENDING`, `INITIATED`, `COMPLETED`, `FAILED`. |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Timestamp of batch creation. |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Timestamp of last status update. |

**Relationships:**

A `payout_batch` is linked to multiple `ledger_entries` where `entry_type = 'SETTLEMENT'` and `status = 'COMMITTED'`. The `total_amount_cents` in `payout_batches` must match the sum of `amount_cents` in the associated `ledger_entries`.

#### 5.3 Disaster Recovery & Consistency

To ensure financial ledger consistency in the event of infrastructure failure, the Aurora PostgreSQL cluster is configured with the following disaster recovery parameters. This addresses the Implied concern: Implied concern: Disaster recovery procedures for financial ledger consistency in the event of infrastructure failure.

1.  **Write-Ahead Logging (WAL):** WAL archiving is enabled. The specific retention period for WAL logs is not yet established in project truth.
2.  **Multi-AZ Deployment:** The Aurora cluster is deployed across multiple Availability Zones (AZ) in each metropolitan footprint (SF, NYC, CHI). In the event of an AZ failure, the cluster automatically fails over to a healthy AZ.
3.  **Read Replicas:** Read replicas are used for reporting and reconciliation queries to avoid impacting the write performance of the primary ledger. These replicas are also configured for WAL archiving.
4.  **Cross-Region Replication:** For critical compliance and data residency requirements, WAL logs are replicated to a secondary region to protect against regional outages.

**Recovery Objectives:**

*   **Recovery Point Objective (RPO):** [KNOWLEDGE_GAP: RPO target not established in project truth - Platform Administrator must define based on business continuity requirements].
*   **Recovery Time Objective (RTO):** [KNOWLEDGE_GAP: RTO target not established in project truth - Platform Administrator must define based on business continuity requirements].

#### 5.4 Data Retention and Archival

Financial records must be retained for compliance purposes. The Implied concern: Implied concern: Comply with financial regulations governing quasi-cash instruments, specifically regarding unclaimed property and escheatment laws, dictates the minimum retention period.

**Retention Policy:**

*   **Minimum Retention Period:** [KNOWLEDGE_GAP: Retention period not established in project truth - Platform Administrator must define based on legal/regulatory requirements].
*   **Archival Strategy:** Entries older than the defined retention threshold are moved to cold storage (e.g., AWS S3 Glacier) to reduce primary database costs. The specific archival threshold is not yet established.

#### 5.5 Implied Concerns Addressed

*   **Implied concern: Implement append-only cryptographic log auditing in Aurora PostgreSQL for all financial ledger mutations:** Addressed by the `ledger_hash` column and the `prevent_ledger_modification` trigger.
*   **Implied concern: Disaster recovery procedures for financial ledger consistency in the event of infrastructure failure:** Addressed by the WAL configuration, Multi-AZ deployment, and cross-region replication strategies.

#### 5.6 Knowledge Gaps

*   **KNOWLEDGE_GAP: payout_frequency** - The exact payout frequency (daily, weekly, bi-weekly) for Merchants is not specified. This affects the `batch_date` logic and the `payout_batches` table design. Decision owner: Product/Finance.
*   **KNOWLEDGE_GAP: currency_support** - The requirement mentions USD, but cross-border expansion is implied. The `currency` column supports multiple currencies, but the exact list of supported currencies and exchange rate source is not defined. Decision owner: Finance/Engineering.
*   **KNOWLEDGE_GAP: chargeback_handling** - The `entry_type` includes `CHARGEBACK`, but the specific workflow for handling chargebacks (e.g., automatic reversal, manual review) is not detailed. This impacts the status transitions and metadata structure. Decision owner: Compliance/Finance.

---

This section defines the integration contracts for the Financial Reconciliation & Payout Workers, detailing the API endpoints and message queue bindings for the [CAP-MERCHANT-PAYOUT-FAILURE-ERROR-HANDLING](../project_glossary.md#cap-merchant-payout-failure-error-handling) capability. This step ensures that the Merchant and NGO Operator actors receive timely notifications of payout statuses and failures, and defines the error handling boundaries for the Implied concern: Merchant Payout Failure & Error Handling.

#### 6.1 Payout Status Notification API (Merchant & NGO Operator)

The Payout Status Notification API provides a secure, authenticated endpoint for Merchants and NGO Operators to query the status of their payout batches. This API is designed to support the Next.js Dashboard Architecture (Edge runtimes) and the Expo Mobile Client Architecture (via API Gateway).

**Endpoint:** `POST /api/v1/payouts/status`

**Authentication:** Bearer Token (JWT) with scope `payout:read` for Merchants and `payout:admin` for NGO Operators.

**Request Body:**

{
 "batch_id": "string (UUIDv4, required)",
 "actor_id": "string (UUIDv4, required) - The ID of the Merchant or NGO Operator requesting the status."
}

**Response Body (200 OK):**

{
 "batch_id": "string (UUIDv4)",
 "merchant_id": "string (UUIDv4)",
 "status": "string (PENDING, INITIATED, COMPLETED, FAILED)",
 "total_amount_cents": "integer",
 "stripe_payout_id": "string (nullable, populated if status is COMPLETED or FAILED)"
}

**Error Responses:**
*   `401 Unauthorized`: Invalid or expired JWT.
*   `403 Forbidden`: Actor ID does not match the batch owner.
*   `404 Not Found`: Batch ID not found.
*   `429 Too Many Requests`: Rate limiting applied.

#### 6.2 Message Queue Bindings for CAP-MERCHANT-PAYOUT-FAILURE-ERROR-HANDLING

The Financial Reconciliation & Payout Workers utilize a message queue to handle asynchronous payout processing and error handling. The following bindings define the topics and queues used for the CAP-MERCHANT-PAYOUT-FAILURE-ERROR-HANDLING capability.

**Message Queue Broker:** AWS SQS (Standard Queue for high throughput, FIFO Queue for strict ordering of payout batches).

**Topics/Queues:**

1.  **payout-initiation-queue (FIFO):**
    *   **Producer:** Financial Reconciliation Engine.
    *   **Consumer:** Payout Orchestration Service.
    *   **Message Schema:**
        
        {
         "event_id": "string (UUIDv4)",
         "merchant_id": "string (UUIDv4)",
         "batch_id": "string (UUIDv4)",
         "amount_cents": "integer",
         "currency": "string (ISO 4217)",
         "retry_policy": {
          "max_retries": "integer",
          "initial_delay_ms": "integer"
         }
        }

2.  **payout-failure-queue (Standard):**
    *   **Producer:** Payout Orchestration Service (on failure).
    *   **Consumer:** Error Handling Worker.
    *   **Message Schema:**
        
        {
         "event_id": "string (UUIDv4)",
         "merchant_id": "string (UUIDv4)",
         "batch_id": "string (UUIDv4)",
         "error_code": "string",
         "error_message": "string",
         "timestamp": "string (ISO 8601)"
        }

3.  **payout-completion-queue (Standard):**
    *   **Producer:** Payout Orchestration Service (on success).
    *   **Consumer:** Notification Service.
    *   **Message Schema:**
        
        {
         "event_id": "string (UUIDv4)",
         "merchant_id": "string (UUIDv4)",
         "batch_id": "string (UUIDv4)",
         "stripe_transfer_id": "string",
         "timestamp": "string (ISO 8601)"
        }

#### 6.3 Error Handling Boundaries and Retry Logic

The Financial Reconciliation & Payout Workers implement a robust error handling strategy to ensure that transient failures do not result in permanent payout failures. The following boundaries and retry logic are defined:

**Retry Policy:**
*   **Max Retries:** 3 attempts.
*   **Backoff Strategy:** Exponential backoff, starting at 1 second, doubling with each retry.
*   **Failure Threshold:** If a payout fails after 3 retries, it is moved to the `payout-failure-queue` for manual intervention by the NGO Operator.

**Error Classification:**
*   **Transient Errors:** Network timeouts, Stripe API rate limits, temporary service unavailability. These are retried.
*   **Permanent Errors:** Invalid merchant account, insufficient funds, Stripe API configuration errors. These are not retried and are moved to the `payout-failure-queue`.

**Notification Mechanism:**
*   **Merchant Notification:** Upon payout failure, the Error Handling Worker triggers a notification to the Merchant via the Payout Status Notification API and an in-app notification (via SSE).
*   **NGO Operator Notification:** Upon payout failure, the Error Handling Worker triggers a notification to the NGO Operator via the Payout Status Notification API and an email alert (if configured).

#### 6.4 Idempotency and Deduplication

To prevent duplicate payouts, the Financial Reconciliation & Payout Workers implement idempotency checks at the message queue level and the database level.

**Message Queue Level:**
*   Each message in the `payout-initiation-queue` includes a unique `event_id`. The Payout Orchestration Service checks for duplicate `event_ids` before processing.

**Database Level:**
*   The `payout_batches` table in Aurora PostgreSQL includes a unique constraint on `batch_id`. Any attempt to insert a duplicate `batch_id` will fail, and the error will be caught and logged.

#### 6.5 Validation and Testing

*   **Unit Tests:** Unit tests should be written for the Payout Orchestration Service to verify the retry logic and error classification.
*   **Integration Tests:** Integration tests should be written to verify the message queue bindings and the end-to-end payout flow.
*   **Load Testing:** Load testing should be performed to ensure that the message queues can handle the expected throughput of 50,000 MAU.

#### 6.6 Security and Compliance

*   **Data Isolation:** The Payout Status Notification API enforces strict data isolation, ensuring that Merchants and NGO Operators can only access their own payout data.
*   **Encryption:** All data in transit is encrypted using TLS 1.3. All data at rest is encrypted using AES-256.
*   **Audit Logging:** All payout-related events are logged to AWS CloudTrail for SOC2 Type II compliance.

#### 6.7 Performance and Scalability

*   **Latency:** The Payout Status Notification API is designed to respond within 200ms for 95% of requests.
*   **Scalability:** The message queues are designed to scale horizontally to handle the expected throughput of 50,000 MAU.
*   **Caching:** The Payout Status Notification API uses Redis to cache payout status responses, reducing database load.

#### 6.8 Monitoring and Alerting

*   **Metrics:** The Financial Reconciliation & Payout Workers expose metrics for payout success rate, failure rate, and average processing time.
*   **Alerts:** Alerts are configured to trigger if the payout failure rate exceeds 1% or if the average processing time exceeds 5 seconds.

#### 6.9 Future Enhancements

*   **Multi-Currency Support:** Future enhancements may include support for multi-currency payouts.
*   **Real-Time Payouts:** Future enhancements may include support for real-time payouts, reducing the latency from transaction to payout.
*   **Advanced Error Handling:** Future enhancements may include more sophisticated error handling, such as automatic retry with different payment methods.

---

### 7. Cross-Artifact Dependencies and Integration

This section outlines the dependencies between the Financial Reconciliation & Payout Workers and other artifacts in the system.

#### 7.1 Upstream Dependencies

*   **Stripe Issuing Proxy Contract:** Provides the source of truth for transaction events.
*   **Financial Ledger Data Model:** Defines the schema for the internal ledger.
*   **Merchant Profile Data Model:** Provides merchant KYC and jurisdictional data.

#### 7.2 Downstream Dependencies

*   **Payout Orchestration Service:** Consumes `RECONCILED` events to initiate payouts.
*   **Dispute Adjudicator Workflow:** Consumes `DISPUTED` events to trigger manual review.
*   **Analytics & Reporting:** Consumes anonymized ledger data for impact reporting.

#### 7.3 Sibling Artifacts

*   **Merchant Payout Failure & Error Handling:** Defines the workflow for handling payout failures.
*   **Compliance, Security & Audit:** Defines the audit trail requirements.
*   **Fraud Detection & Fraud Prevention Screening:** Defines the fraud detection rules that may flag transactions for review.

---

### 8. Knowledge Gaps and Open Decisions

This section summarizes the unresolved decisions that must be addressed before implementation can proceed.

| Decision Axis | Impact | Decision Owner | Evidence Needed |
| :--- | :--- | :--- | :--- |
| Payout Frequency | Determines cash flow requirements and Stripe API usage. | Platform Administrator | Project requirement or business rule defining payout schedule. |
| Reserve Policy | Impacts merchant liquidity and platform risk exposure. | Platform Administrator | Project requirement or business rule defining reserve percentage. |
| Database Technology | Affects scalability, consistency, and cost. | Platform Administrator | Project requirement or technical architecture decision. |
| Retention Period | Compliance obligation for financial records. | Platform Administrator | Legal/regulatory requirement or compliance policy. |
| RPO/RTO Targets | Defines disaster recovery capabilities. | Platform Administrator | Business continuity plan or SLA requirements. |

---

### 9. Conclusion

The Financial Reconciliation & Payout Workers artifact provides a comprehensive design for the asynchronous event-driven architecture that powers the MealCredit platform's financial operations. By leveraging Stripe's robust infrastructure and implementing strict idempotency, audit trails, and error handling, the platform ensures financial consistency, compliance, and trust. The unresolved knowledge gaps identified in this artifact must be addressed by the Platform Administrator to finalize the implementation details.
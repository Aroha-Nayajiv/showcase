# Background Processing & Async Workers

## 1. Asynchronous Financial Event Schema

This section defines the canonical event schemas for the asynchronous financial backbone of MealCredit. These schemas decouple the high-latency financial reconciliation and merchant settlement processes from the low-latency Pseudo-Anonymous Redemption Engine, ensuring sub-150ms latency for POS card taps while maintaining strict ledger consistency.

### 1.1. TransactionEvent Schema

The TransactionEvent is published by the Pseudo-Anonymous Redemption Engine immediately after a successful POS clearance. It carries the necessary context for the Financial Reconciliation Engine to process the ledger update asynchronously.

Schema Definition:

| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| event_id | string | Yes | Unique identifier for this event instance (UUIDv4). | `"550e8400-e29b-41d4-a716-446655440000"` |
| event_version | string | Yes | Schema version for backward compatibility. | `"1.0"` |
| event_type | string | Yes | Constant value identifying the event. | `"TRANSACTION_COMPLETED"` |
| timestamp | string | Yes | ISO 8601 UTC timestamp of the event creation. | `"2024-05-20T14:30:00.000Z"` |
| transaction_id | string | Yes | Unique identifier for the financial transaction (UUIDv4). | `"7c9e6679-7425-40de-944b-e07fc1f90ae7"` |
| idempotency_key | string | Yes | Unique key to prevent duplicate processing of the same transaction. | `"pos_scan_12345_20240520"` |
| beneficiary_token | string | Yes | Cryptographically hashed/anonymous identifier for the beneficiary. | `"sha256:a1b2c3d4..."` |
| amount | number | Yes | Transaction amount in minor currency units (e.g., cents). | 1500 |
| currency | string | Yes | ISO 4217 currency code. | `"USD"` |
| merchant_id | string | Yes | Unique identifier for the Merchant Partner (Restaurant). | `"MERCHANT-001"` |
| metro_region | string | Yes | Metropolitan footprint where the transaction occurred. | `"SF"` |
| pos_terminal_id | string | Yes | Identifier for the specific POS terminal used. | `"TERMINAL-ABC-123"` |
| donor_pool_id | string | Yes | Identifier for the donor credit pool from which funds were drawn. | `"POOL-SF-001"` |
| metadata | object | No | Additional contextual data (e.g., order items, tips). | `{"tip_amount": 200, "order_count": 2}` |

Design Rationale:
- Anonymization: The beneficiary_token ensures that PII is not exposed in the async logs, adhering to [CON-0A0288EED4](../project_glossary.md#CON-0A0288EED4) (Implied concern: Implement strict data isolation where beneficiary demographic status and legal names are cryptographically segregated from public ...).
- Idempotency: The idempotency_key is critical for handling retries from the payment processor (e.g., Stripe) without double-processing transactions.
- Decoupling: By including donor_pool_id and metro_region, the Financial Reconciliation Engine can update the correct credit pool and track regional metrics without needing to query the Redemption Engine.

### 1.2. PayoutEvent Schema

The PayoutEvent is published by the Financial Reconciliation Engine after it has aggregated daily transaction logs, matched them against settlement reports, and generated a settlement report for automated payouts to Merchant Partners.

Schema Definition:

| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| event_id | string | Yes | Unique identifier for this event instance (UUIDv4). | `"660e8400-e29b-41d4-a716-446655440001"` |
| event_version | string | Yes | Schema version for backward compatibility. | `"1.0"` |
| event_type | string | Yes | Constant value identifying the event. | `"PAYOUT_INITIATED"` |
| timestamp | string | Yes | ISO 8601 UTC timestamp of the event creation. | `"2024-05-21T02:00:00.000Z"` |
| payout_id | string | Yes | Unique identifier for the payout batch (UUIDv4). | `"880e8400-e29b-41d4-a716-446655440002"` |
| merchant_id | string | Yes | Unique identifier for the Merchant Partner receiving the payout. | `"MERCHANT-001"` |
| stripe_connect_account_id | string | Yes | Stripe Connected Account ID for the merchant. | `"acct_1234567890"` |
| total_amount | number | Yes | Total payout amount in minor currency units. | 15000 |
| currency | string | Yes | ISO 4217 currency code. | `"USD"` |
| settlement_period_start | string | Yes | Start of the settlement period (ISO 8601 UTC). | `"2024-05-20T00:00:00.000Z"` |
| settlement_period_end | string | Yes | End of the settlement period (ISO 8601 UTC). | `"2024-05-20T23:59:59.999Z"` |
| transaction_count | number | Yes | Number of transactions included in this payout. | 10 |
| status | string | Yes | Current status of the payout. | `"PENDING"` |
| metadata | object | No | Additional contextual data (e.g., fee breakdown). | `{"platform_fee": 500, "net_amount": 14500}` |

Design Rationale:
- Security: The stripe_connect_account_id is used to route the payout securely via Stripe Connect, ensuring that sensitive financial tokens are not stored in plain text in the event logs.
- Traceability: The settlement_period_start and settlement_period_end fields allow for precise reconciliation of daily logs against payout batches.
- Status Tracking: The status field enables the Merchant Payout Failure & Error Handling artifact to track and retry failed payouts.

### 1.3. Event Bus Integration

These events are published to the Amazon EventBridge bus. The TransactionEvent is routed to the Financial Reconciliation Engine, while the PayoutEvent is routed to the Merchant Notification Service and the Financial Reconciliation Engine for status updates.

Routing Rules:
- TransactionEvent -> FinancialReconciliationEngine (via SQS FIFO queue for ordered processing).
- PayoutEvent -> MerchantNotificationService (via SNS for real-time alerts) and FinancialReconciliationEngine (for status tracking).

Error Handling:
- Failed events are routed to a Dead Letter Queue (DLQ) for manual inspection and retry.
- Idempotency checks are performed by the Financial Reconciliation Engine to prevent duplicate processing.

### 1.4. Knowledge Gaps

- `KNOWLEDGE_GAP: Exact event bus implementation details (e.g., specific EventBridge rule syntax, SQS FIFO queue configuration) must be established by the Infrastructure Topology & Deployment Design artifact.`
- `KNOWLEDGE_GAP: Specific error handling and retry logic for Stripe webhook processing must be established by the Merchant Payout Failure & Error Handling artifact.`

---

## 2. Financial Reconciliation Engine Architecture

The Financial Reconciliation Engine is the asynchronous backbone of the MealCredit platform, responsible for aggregating transaction logs from the Pseudo-Anonymous Redemption Engine, matching them against the immutable financial ledger, and generating the daily settlement reports required for automated payouts. This design ensures strict ledger consistency while decoupling high-latency financial operations from the sub-150ms real-time POS clearance path.

### 2.1. Event Ingestion and Aggregation

The engine ingests financial events via an asynchronous event bus. To ensure data integrity and order, events are published to an Amazon SQS FIFO queue, which guarantees exactly-once processing and message ordering within a message group ID (e.g., merchant_id or transaction_id).

Event Schema (TransactionEvent):
- event_id: UUIDv4 (Unique identifier for the event)
- event_version: String (e.g., "1.0")
- transaction_id: UUIDv4 (The unique ID of the financial transaction)
- beneficiary_token: String (Cryptographically hashed/anonymous token, ensuring PII segregation)
- amount: Decimal (The fractional credit amount spent)
- currency: String (ISO 4217 code, e.g., "USD")
- merchant_id: String (Unique identifier for the Merchant Partner)
- timestamp: ISO 8601 (UTC timestamp of the transaction)
- idempotency_key: String (To prevent double-processing of events)

Aggregation Logic:
The engine consumes events from the SQS FIFO queue.
It applies an idempotency check using the idempotency_key to ensure that no transaction is processed more than once, even in the event of network retries or duplicate webhook deliveries.
Aggregated transaction logs are stored in the immutable financial ledger (see Sibling Artifact: Financial Ledger Data Model) as append-only records.

### 2.2. Immutable Ledger Matching and Consistency

The core of the reconciliation process is matching the ingested transaction logs against the immutable financial ledger to ensure consistency. This is achieved through a nightly batch job (orchestrated via AWS Step Functions) that performs the following steps:

1. Ledger Snapshot: A snapshot of the financial ledger is taken at the end of each business day.
2. Event Matching: The engine matches the aggregated transaction logs against the ledger snapshot. Any discrepancies (e.g., missing transactions, amount mismatches) are flagged as exceptions.
3. Hash-Checksum Verification: To ensure tamper-evidence, the engine verifies the cryptographic hash of the previous ledger row for each new entry, as mandated by the append-only logging requirement ([CON-1762EA5021](../project_glossary.md#CON-1762EA5021), [CON-6061FCCA83](../project_glossary.md#CON-6061FCCA83)).

Consistency Guarantees:
- Double-Spending Prevention: The idempotency keys and the immutable ledger structure prevent double-spending of credits.
- Voided Transactions: Voided transactions are recorded as negative entries in the ledger, ensuring that the net balance is accurately reflected.

### 2.3. Daily Settlement Report Generation

Once the reconciliation is complete and the ledger is confirmed to be consistent, the engine generates the daily settlement report. This report is the primary input for the automated daily payout process.

Settlement Report Structure:
- payout_id: UUIDv4 (Unique identifier for the payout batch)
- merchant_id: String (The Merchant Partner receiving the payout)
- total_amount: Decimal (The total net amount to be paid out after fees and adjustments)
- currency: String (ISO 4217 code)
- stripe_connect_account_id: String (The Stripe Connected Account ID for the merchant)
- status: String (e.g., "PENDING", "COMPLETED", "FAILED")
- transaction_count: Integer (The number of transactions included in the payout)
- reconciliation_hash: String (A cryptographic hash of the entire settlement report for integrity verification)

Data Flow for DRV Tracking:
- The settlement report also feeds into the Donation-to-Redemption Velocity (DRV) tracking system. By aggregating redemption events by regional pool, the engine provides the data necessary to monitor liquidity health against the 14-day target ([CON-D0F5814F21](../project_glossary.md#CON-D0F5814F21), [CON-F89C70071E](../project_glossary.md#CON-F89C70071E)).

### 2.4. Reconciliation Discrepancy Remediation Workflow

When the Financial Reconciliation Engine identifies a discrepancy (e.g., missing transactions, amount mismatches, or hash-checksum failures), it triggers a structured remediation workflow to ensure data integrity before proceeding to payout.

Remediation Workflow:
1. Exception Flagging: The engine logs the discrepancy in the immutable audit log ([CON-1762EA5021](../project_glossary.md#CON-1762EA5021)) and marks the affected transaction(s) as `RECONCILIATION_EXCEPTION`.
2. Automated Retry: For transient errors (e.g., temporary network blips during event ingestion), the engine attempts an automated retry up to 3 times with exponential backoff.
3. Manual Review Queue: If the discrepancy persists after retries, the exception is routed to a manual review queue accessible by the Platform Administrator ([ACT-086A974D63](../project_glossary.md#ACT-086A974D63)).
4. Resolution Actions: The Platform Administrator can:
   - Manually reconcile the transaction by adjusting the ledger entry.
   - Initiate a refund/reversal if the transaction is deemed invalid.
   - Escalate to the Dispute Adjudicator ([ACT-7BA340FF76](../project_glossary.md#ACT-7BA340FF76)) if the discrepancy involves a potential fraud or beneficiary dispute.
5. Audit Trail: All remediation actions are logged with a timestamp, actor ID, and reason code to maintain a complete audit trail for SOC2 Type II compliance ([CON-81FB01F06B](../project_glossary.md#CON-81FB01F06B), [CON-E84412A0FA](../project_glossary.md#CON-E84412A0FA)).

### 2.5. Error Handling and Retry Logic

- Idempotency: The use of idempotency_key ensures that retries do not result in duplicate financial entries.
- Dead Letter Queue (DLQ): Events that fail processing after a configurable number of retries are moved to a Dead Letter Queue for manual inspection and remediation.
- Alerting: Automated alerts are triggered if the Credit Pool Utilization Rate exceeds 85% ([CON-2059B17FB2](../project_glossary.md#CON-2059B17FB2), [CON-7031BE57B3](../project_glossary.md#CON-7031BE57B3)) or if reconciliation discrepancies exceed a defined threshold.

---

## 3. Automated Daily Payout Orchestration Service

The Automated Daily Payout Orchestration Service is the critical bridge between the asynchronous Financial Reconciliation Engine and the external payment processor (Stripe). Its primary function is to aggregate verified, reconciled transaction logs into batch settlement files, initiate payouts to Merchant Partners (Restaurants) via Stripe Connect, and manage the lifecycle of these payouts including failure handling and reconciliation.

### 3.1. Service Architecture and Data Flow

The service operates on a daily batch schedule, triggered by an event from the Financial Reconciliation Engine indicating that the previous day's ledger is finalized and immutable.

1. Trigger: The Financial Reconciliation Engine publishes a DailyLedgerFinalizedEvent to the event bus. This event contains the date, total_reconciled_amount, and merchant_settlement_summary (aggregated by merchant_id).
2. Aggregation & Validation: The Payout Orchestration Service consumes this event. It validates the merchant_settlement_summary against the immutable ledger stored in Aurora PostgreSQL (referencing the `Financial Ledger Data Model` artifact for schema details). It ensures that the sum of individual transaction credits matches the aggregated settlement amount for each merchant.
3. Payout File Generation: For each merchant with a positive settlement balance, the service generates a payout request payload. This payload includes the merchant_id, payout_amount, currency (USD), and a unique payout_id (UUIDv4).
4. Stripe Integration: The service calls the Stripe API to create a Transfer or Payout object for each merchant. It uses the stripe_connect_account_id associated with the merchant (referencing the `Integration Adapters & External Contracts` artifact for Stripe API specifics).
5. State Management: The service updates the local payouts table with the Stripe payout_id and sets the status to PENDING. It then publishes a PayoutInitiatedEvent to the event bus.
6. Reconciliation: The service subscribes to Stripe Webhooks for payout.succeeded and payout.failed events. Upon receiving a success webhook, it updates the local payout status to COMPLETED. Upon failure, it updates the status to FAILED and triggers the `Merchant Payout Failure & Error Handling` artifact's workflow.

### 3.2. API Contracts

#### 3.2.1. Initiate Payouts (Internal gRPC)

This endpoint is called by the Financial Reconciliation Engine upon daily ledger finalization.

Request:


{
 "reconciliation_date": "2024-05-20",
 "settlements": [
 {
 "merchant_id": "MERCH-001",
 "payout_id": "PAYOUT-001",
 "idempotency_key": "payout_idemp_001_20240520",
 "total_amount": 15000,
 "transaction_count": 50
 }
 ]
}


Response:


{
 "batch_id": "BATCH-20240520-001",
 "payouts": [
 {
 "merchant_id": "MERCH-001",
 "payout_id": "PAYOUT-001",
 "status": "PENDING"
 }
 ]
}

#### 3.2.2. Stripe Webhook Handler (Internal gRPC)

This endpoint processes Stripe webhooks to update payout status.

Request (Stripe Webhook Payload):


{
 "event_type": "payout.succeeded",
 "payout_id": "po_1234567890",
 "amount": 15000,
 "currency": "USD",
 "arrival_date": "2024-05-22"
}


Response:


{
 "status": "processed",
 "new_status": "COMPLETED"
}

### 3.3. Idempotency and Retry Logic

To ensure financial consistency and prevent duplicate payouts, the service implements strict idempotency:

1. Idempotency Key: Each payout request to Stripe includes a unique idempotency_key derived from the payout_id (UUIDv4). This ensures that if the service retries a request due to a network timeout, Stripe will not create duplicate payouts.
2. Retry Policy: Failed payout requests (e.g., due to Stripe API rate limits or temporary outages) are retried with exponential backoff. The retry policy is defined as:
 - Initial delay: 1 second
 - Max retries: 5
 - Max delay: 1 hour
 - Jitter: Randomized between 0 and 1 second to prevent thundering herd.
3. Dead Letter Queue: If a payout fails after all retries, it is moved to a Dead Letter Queue (DLQ) for manual review and automated error handling (referencing the `Merchant Payout Failure & Error Handling` artifact).

### 3.4. Security and Compliance

- Data Isolation: Payout requests only include the merchant_id and stripe_connect_account_id. No beneficiary PII or donor information is included in the payout payload, ensuring strict data isolation ([CON-0A0288EED4](../project_glossary.md#CON-0A0288EED4)).
- Secure Vault Access: The service retrieves Stripe API keys and stripe_connect_account_id secrets from a secure vault (e.g., AWS Secrets Manager) at runtime. Secrets are never stored in the application code or configuration files.
- Audit Logging: All payout initiation, success, and failure events are logged to an append-only cryptographic log in Aurora PostgreSQL (CON-1762EA5021, [CON-6061FCCA83](../project_glossary.md#CON-6061FCCA83)) for SOC2 Type II compliance ([CON-81FB01F06B](../project_glossary.md#CON-81FB01F06B), [CON-E84412A0FA](../project_glossary.md#CON-E84412A0FA)).

### 3.5. Knowledge Gaps and Assumptions

- `KNOWLEDGE_GAP: Payout Frequency and Thresholds: The project requirement mentions "daily batch settlements" but does not specify minimum payout thresholds or exact payout schedules (e.g., next-day, T+2). The `Merchant Payout Failure & Error Handling` artifact should define these thresholds.`
- `KNOWLEDGE_GAP: Stripe Connect Account Onboarding: The process for onboarding Merchant Partners onto Stripe Connect (KYC, verification) is not detailed in this artifact. It is assumed that the `Integration Adapters & External Contracts` artifact covers the Stripe API integration, but the onboarding workflow itself is a separate concern.`
- `ASSUMPTION: Stripe API Version: The service assumes the use of the latest stable Stripe API version. The exact API version must be confirmed by the `Integration Adapters & External Contracts` artifact.`
- `ASSUMPTION: Currency: The service assumes all payouts are in USD. If multi-currency support is required in the future, the settlements payload must include a currency field for each merchant, and the Stripe API call must be updated accordingly.`

### 3.6. Integration with Sibling Artifacts

- Financial Reconciliation Engine: Consumes DailyLedgerFinalizedEvent and provides PayoutInitiatedEvent.
- Merchant Payout Failure & Error Handling: Receives PayoutFailedEvent for manual review and automated remediation.
- Integration Adapters & External Contracts: Defines the Stripe API client library, error codes, and webhook signature verification.
- Financial Ledger Data Model: Provides the source of truth for transaction amounts and merchant balances.
- Security Architecture & Access Control: Defines the secure vault access patterns for Stripe secrets.

This design ensures that the payout orchestration service is robust, secure, and compliant with the project's financial and data privacy requirements. It provides a clear contract for integration with the Financial Reconciliation Engine and Stripe, enabling the development team to implement the service with confidence.

---

## 4. Error Handling and Retry Mechanisms for Async Workers

This section defines the robust error handling, retry logic, and dead-letter queue (DLQ) architecture for the MealCredit async worker ecosystem. It ensures that high-throughput financial reconciliation and merchant settlement remain resilient against transient failures, payment processor unavailability, and reconciliation discrepancies, while maintaining strict data isolation and auditability.

### 4.1. Retry Strategy

All async workers (Financial Reconciliation Engine, Payout Orchestration Service) adhere to a standardized retry strategy to handle transient failures:

- Exponential Backoff: Retries are spaced exponentially to avoid overwhelming downstream services.
- Jitter: Random jitter is added to retry delays to prevent thundering herd problems.
- Max Retries: A maximum number of retries is enforced before moving to the DLQ.

### 4.2. Dead Letter Queue (DLQ) Management

Events that fail after all retries are moved to a DLQ. The DLQ is monitored by the Platform Administrator ([ACT-086A974D63](../project_glossary.md#ACT-086A974D63)) for manual intervention.

- Inspection: Failed events are inspected to determine the root cause.
- Remediation: Based on the root cause, the event is either re-processed, corrected, or discarded.
- Alerting: Automated alerts are triggered if the DLQ size exceeds a defined threshold.

### 4.3. Circuit Breaker Pattern

To prevent cascading failures, the Payout Orchestration Service implements a circuit breaker pattern when interacting with the Stripe API.

- Failure Threshold: If a certain number of consecutive failures occur, the circuit breaker opens.
- Half-Open State: After a timeout, the circuit breaker enters a half-open state, allowing a single request to test the downstream service.
- Closed State: If the test request succeeds, the circuit breaker closes, and normal operation resumes.

## 5. Donation-to-Redemption Velocity (DRV) and Credit Pool Utilization

This section defines the data flow and architectural considerations for tracking the Donation-to-Redemption Velocity (DRV) and monitoring Credit Pool Utilization, ensuring liquidity health and preventing ledger stagnation.

### 5.1. DRV Tracking Data Flow

The DRV metric measures the speed at which donated funds are redeemed by beneficiaries. It is a key indicator of program effectiveness and liquidity health.

Data Flow:
1. Event Capture: The Financial Reconciliation Engine captures redemption events from the TransactionEvent schema.
2. Aggregation: Events are aggregated by metro_region and donor_pool_id.
3. Velocity Calculation: The DRV is calculated as the ratio of total redeemed amount to total donated amount over a rolling 14-day window ([CON-D0F5814F21](../project_glossary.md#CON-D0F5814F21), [CON-F89C70071E](../project_glossary.md#CON-F89C70071E)).
4. Storage: DRV metrics are stored in a time-series database (e.g., Amazon Timestream) for efficient querying and visualization.

### 5.2. Credit Pool Utilization Alerts

The Credit Pool Utilization Rate monitors the percentage of available credits that have been redeemed. Automated alerts are triggered when thresholds are exceeded to prevent liquidity issues.

Alerting Rules:
- Threshold: Alerts are triggered when the Credit Pool Utilization Rate exceeds 85% ([CON-2059B17FB2](../project_glossary.md#CON-2059B17FB2), [CON-7031BE57B3](../project_glossary.md#CON-7031BE57B3)).
- Notification: Alerts are sent to the Platform Administrator (ACT-086A974D63) and the NGO Operator ([ACT-09E028AEB0](../project_glossary.md#ACT-09E028AEB0)) via SNS.
- Action: The Platform Administrator can initiate emergency credit top-ups or adjust donation flows to rebalance the pool.

### 5.3. Knowledge Gaps

- `KNOWLEDGE_GAP: The exact formula for calculating DRV (e.g., simple ratio vs. weighted average) must be defined by the Product Strategy artifact.`
- `KNOWLEDGE_GAP: The specific time-series database technology and retention policy for DRV metrics must be defined by the Infrastructure Topology & Deployment Design artifact.`

---

## 6. Integration with Sibling Artifacts

This artifact integrates with the following sibling artifacts to ensure end-to-end financial integrity:

- Financial Ledger Data Model: Provides the source of truth for transaction amounts and merchant balances.
- Merchant Payout Failure & Error Handling: Receives PayoutFailedEvent for manual review and automated remediation.
- Integration Adapters & External Contracts: Defines the Stripe API client library, error codes, and webhook signature verification.
- Security Architecture & Access Control: Defines the secure vault access patterns for Stripe secrets.
- Infrastructure Topology & Deployment Design: Defines the event bus, queue, and database infrastructure.

This design ensures that the async worker ecosystem is robust, secure, and compliant with the project's financial and data privacy requirements.

### 4. Error Handling, Retry Logic, and Dead-Letter Queue Architecture

This section defines the asynchronous error handling, retry strategies, and dead-letter queue (DLQ) mechanisms for the Financial Reconciliation, Payout Orchestration, and DRV Tracking workers. It ensures financial consistency, prevents silent data loss, and provides clear remediation paths for the Platform Administrator.

#### 4.1. Retry Strategy and Exponential Backoff

To handle transient failures (e.g., network timeouts, temporary payment processor unavailability), all async workers (Financial Reconciliation, Payout Orchestration, DRV Tracking) will implement a standardized exponential backoff with jitter strategy.

**Retry Policy:**
- **Initial Delay:** 1 second.
- **Backoff Multiplier:** 2x.
- **Maximum Retries:** 5 attempts before moving to the Dead-Letter Queue (DLQ).
- **Jitter:** Randomized delay between 0 and 500ms added to each retry to prevent thundering herd effects.
- **Maximum Delay:** Capped at 60 seconds between retries.

**Error Classification:**
- **Transient Errors (Retryable):** HTTP 429 (Too Many Requests), HTTP 500/502/503/504 (Server Errors), Network Timeouts, Connection Refused. These are retried.
- **Permanent Errors (Non-Retryable):** HTTP 400 (Bad Request - invalid payload), HTTP 401/403 (Authentication/Authorization failures), HTTP 404 (Resource Not Found), Schema Validation Errors. These are immediately routed to the DLQ.

**Idempotency Enforcement:**
- All retryable operations MUST be idempotent. Each event processed by an async worker MUST include a unique `idempotency_key` (UUIDv4).
- Workers MUST check for the existence of the `idempotency_key` in the financial ledger before processing. If the key exists, the event is acknowledged as successfully processed, and no duplicate ledger mutation occurs.

#### 4.2. Dead-Letter Queue (DLQ) Structure

Events that exceed the maximum retry count or encounter permanent errors are routed to a dedicated Dead-Letter Queue (DLQ). This ensures that no financial event is silently lost and provides a clear path for manual or automated remediation by the Platform Administrator.

**DLQ Architecture:**
- **Storage:** Amazon SQS FIFO Queue (to preserve event ordering and guarantee exactly-once processing).
- **Naming Convention:** `<environment>-mealcredit-async-dlq.fifo` (e.g., `prod-mealcredit-async-dlq.fifo`).
- **Retention Period:** 14 days (configurable, but must be sufficient for manual review).

**DLQ Event Schema:**
Each message in the DLQ MUST contain the original event payload plus metadata about the failure:


{
  "original_event": {
    "event_id": "uuid-v4",
    "event_type": "TransactionEvent | PayoutEvent",
    "payload": { ... },
    "timestamp": "ISO-8601"
  },
  "failure_metadata": {
    "error_code": "PERMANENT_ERROR | MAX_RETRIES_EXCEEDED",
    "error_message": "Detailed error string from processor or worker",
    "retry_count": 5,
    "failed_worker": "FinancialReconciliationWorker | PayoutOrchestrationWorker"
  }
}


**Data Isolation in DLQ:**
- Beneficiary PII MUST NOT be stored in the DLQ. Only hashed `beneficiary_token` and anonymized transaction data are permitted.
- Access to the DLQ is restricted to the Platform Administrator role via IAM policies.

#### 4.3. Alerting Triggers for Platform Administrator

The Platform Administrator MUST be alerted immediately when events enter the DLQ or when retry thresholds are approached, to prevent financial discrepancies from accumulating.

**Alerting Triggers:**
1. **DLQ Entry:** An alert is triggered immediately when an event is routed to the DLQ.
   - **Severity:** Critical.
   - **Notification Channel:** PagerDuty / Email.
   - **Message:** "Async Worker DLQ Entry: [Event Type] [Event ID] failed after [Retry Count] retries. Error: [Error Message]."
2. **Retry Threshold Warning:** An alert is triggered when an event reaches 80% of its maximum retry count (e.g., 4th retry out of 5).
   - **Severity:** Warning.
   - **Notification Channel:** Email / Slack.
   - **Message:** "Async Worker Retry Warning: [Event Type] [Event ID] is on retry [Retry Count] of [Max Retries]."
3. **DLQ Volume Spike:** An alert is triggered if the DLQ message count exceeds a threshold (e.g., > 10 messages in 5 minutes).
   - **Severity:** Critical.
   - **Notification Channel:** PagerDuty / Email.
   - **Message:** "DLQ Volume Spike: [Count] messages in the last 5 minutes. Potential systemic issue."

**Alerting Implementation:**
- This artifact's alerting design defers to the `Observability & Monitoring Design` artifact for the specific implementation of CloudWatch Alarms and SNS topics. This artifact defines the what and when, not the how of the monitoring infrastructure.

#### 4.4. Reconciliation Failure Handling and Remediation Workflow

When a transaction fails reconciliation (e.g., mismatch between POS event and Stripe settlement report), the system MUST log the discrepancy and trigger a manual review process. This section explicitly defines the remediation workflow for the Platform Administrator.

**Reconciliation Discrepancy Event:**
- If the Financial Reconciliation Engine detects a mismatch, it creates a `ReconciliationDiscrepancyEvent`.
- This event is NOT retried automatically. It is immediately routed to the DLQ for manual review by the Platform Administrator.
- The event MUST include:
  - `transaction_id`: The ID of the transaction in question.
  - `expected_amount`: The amount from the POS event.
  - `actual_amount`: The amount from the Stripe settlement report.
  - `discrepancy_type`: `AMOUNT_MISMATCH | MISSING_TRANSACTION | EXTRA_TRANSACTION`.

**Manual Review and Remediation Workflow:**
1. **Notification:** The Platform Administrator receives a Critical Alert (Section 4.3) upon DLQ entry.
2. **Triage:** The Administrator accesses the Merchant Dashboard (owned by `Frontend & Presentation Layer Design`) to view `ReconciliationDiscrepancyEvents` from the DLQ.
3. **Investigation:** The Administrator reviews the `expected_amount` vs. `actual_amount` and `discrepancy_type` to determine the root cause (e.g., POS terminal misconfiguration, Stripe reporting delay, or fraud).
4. **Resolution Action:** The Administrator MUST take one of the following actions:
   - **RESOLVED (Manual Adjustment):** If the discrepancy is due to a known reporting delay or minor rounding error, the Administrator manually adjusts the ledger entry via the dashboard. A `reason_code` (e.g., `ROUNDING_ADJUSTMENT`, `REPORTING_DELAY`) MUST be recorded in the `reconciliation_line_items.discrepancy_notes` field.
   - **ESCALATED (Compliance/Legal):** If the discrepancy suggests fraud, systemic failure, or regulatory non-compliance, the Administrator marks the event as `ESCALATED`. This triggers a separate audit trail log for the Compliance team.
   - **IGNORED (False Positive):** If the discrepancy is determined to be a false positive (e.g., duplicate reporting), the Administrator marks it as `IGNORED` with a justification note.
5. **Archival:** Resolved, Escalated, or Ignored discrepancies are archived for SOC2 Type II audit evidence. The `ReconciliationDiscrepancyEvent` is removed from the active DLQ view but retained in the immutable ledger.

#### 4.5. Payment Processor Unavailability Handling

In the event of a prolonged Stripe API outage, the Payout Orchestration Worker MUST gracefully degrade and prevent financial loss.

**Circuit Breaker Pattern:**
- A circuit breaker MUST be implemented around all Stripe API calls.
- **Failure Threshold:** If 5 consecutive requests fail, the circuit opens.
- **Open State:** No new payout requests are sent to Stripe. Events are queued in an internal retry buffer.
- **Half-Open State:** After 5 minutes, one test request is sent to Stripe. If successful, the circuit closes. If it fails, the circuit remains open for another 5 minutes.
- **Closed State:** Normal operation resumes.

**Graceful Degradation:**
- While the circuit is open, the Payout Orchestration Worker continues to process internal ledger updates but pauses external Stripe API calls.
- The Platform Administrator is alerted via the DLQ Volume Spike alert (Section 4.3).

#### 4.6. Data Retention and Auditability

- **DLQ Retention:** DLQ messages are retained for 14 days. After 14 days, they are automatically archived to Amazon S3 for long-term storage (SOC2 Type II evidence).
- **Audit Log:** All DLQ entries, manual resolutions, and circuit breaker state changes are logged to an append-only cryptographic log in Aurora PostgreSQL (CON-1762EA5021, CON-6061FCCA83) for auditability.

#### 4.8. Summary of Error Handling Flow

1. **Event Received:** Async Worker receives event from EventBridge/SQS.
2. **Idempotency Check:** Worker checks for `idempotency_key` in ledger.
3. **Processing:** Worker attempts to process event (e.g., update ledger, call Stripe).
4. **Success:** Event acknowledged, ledger updated.
5. **Transient Error:** Event retried with exponential backoff (up to 5 times).
6. **Permanent Error / Max Retries Exceeded:** Event routed to DLQ.
7. **Alerting:** Platform Administrator alerted via PagerDuty/Email.
8. **Manual Review:** Platform Administrator reviews DLQ event, resolves discrepancy (RESOLVED/ESCALATED/IGNORED), and archives for audit.

This error handling framework ensures that MealCredit's financial backbone is resilient, auditable, and maintainable, even in the face of external failures and data discrepancies.

---

## 5. Data Persistence Layer for Async Workers

This section defines the database schemas and persistence strategies for the asynchronous worker ecosystem. The design ensures strict financial consistency, supports the immutable ledger requirements (CON-1762EA5021, CON-6061FCCA83), and enables efficient aggregation for the Financial Reconciliation Engine.

### 5.1. Immutable Financial Ledger Schema

The core of the async worker persistence is the immutable financial ledger. This table stores every financial mutation (donation, redemption, payout) as an append-only record. It is the single source of truth for all financial reconciliation.

**Table: financial_ledger_entries**

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `entry_id` | UUID | PK, NOT NULL | Unique identifier for the ledger entry. |
| `entry_hash` | VARCHAR(64) | NOT NULL | SHA-256 hash of the previous entry's hash and current data. Ensures immutability. |
| `previous_entry_hash` | VARCHAR(64) | NOT NULL | Hash of the immediately preceding ledger entry. |
| `transaction_id` | UUID | NOT NULL, UNIQUE | ID of the originating transaction (e.g., from Stripe or POS). |
| `event_type` | ENUM | NOT NULL | Type of event: `DONATION_RECEIVED`, `CREDIT_ISSUED`, `REDEMPTION_INITIATED`, `REDEMPTION_COMPLETED`, `PAYOUT_INITIATED`, `PAYOUT_COMPLETED`. |
| `actor_id` | UUID | NOT NULL | ID of the actor involved (Donor, Beneficiary, Merchant, NGO). |
| `actor_type` | ENUM | NOT NULL | Type of actor: `DONOR`, `BENEFICIARY`, `MERCHANT`, `NGO`. |
| `amount_cents` | BIGINT | NOT NULL | Amount in smallest currency unit (e.g., cents). |
| `currency` | CHAR(3) | NOT NULL | ISO 4217 currency code (e.g., USD). |
| `metadata_json` | JSONB | | Additional context (e.g., `donation_round_up`, `pos_terminal_id`). |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Timestamp of the ledger entry creation. |
| `reconciliation_status` | ENUM | NOT NULL | Status: `PENDING_RECONCILIATION`, `RECONCILED`, `DISCREPANCY_FOUND`. |

**Design Rationale:**
- **Immutability:** The `entry_hash` and `previous_entry_hash` fields create a cryptographic chain. Any attempt to modify a past entry will break the hash chain, making tampering immediately detectable.
- **Append-Only:** No UPDATE or DELETE operations are permitted on this table. Corrections are made via new entries with a `CORRECTION` event type.
- **Efficiency:** Indexes on `transaction_id`, `actor_id`, and `created_at` support efficient querying for reconciliation and reporting.

### 5.2. Reconciliation State Schema

The Financial Reconciliation Engine uses this schema to track the state of daily reconciliation processes. It maps external payment processor settlements (e.g., Stripe) to internal ledger entries.

**Table: reconciliation_batches**

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `batch_id` | UUID | PK, NOT NULL | Unique identifier for the reconciliation batch. |
| `batch_date` | DATE | NOT NULL | The date for which this batch is reconciling. |
| `processor_type` | ENUM | NOT NULL | Type of payment processor: `STRIPE`. |
| `processor_batch_id` | VARCHAR(255) | NOT NULL | ID of the batch from the external processor (e.g., Stripe Report ID). |
| `total_expected_cents` | BIGINT | NOT NULL | Total amount expected from the processor for this batch. |
| `total_reconciled_cents` | BIGINT | NOT NULL | Total amount successfully reconciled. |
| `status` | ENUM | NOT NULL | Status: `INITIATED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`. |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Timestamp of batch creation. |
| `completed_at` | TIMESTAMP | | Timestamp of batch completion. |

**Table: reconciliation_line_items**

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `line_item_id` | UUID | PK, NOT NULL | Unique identifier for the line item. |
| `batch_id` | UUID | FK, NOT NULL | Reference to the parent `reconciliation_batches` record. |
| `ledger_entry_id` | UUID | FK, NOT NULL | Reference to the `financial_ledger_entries` record. |
| `processor_transaction_id` | VARCHAR(255) | | ID of the transaction from the external processor. |
| `amount_cents` | BIGINT | NOT NULL | Amount from the processor record. |
| `match_status` | ENUM | NOT NULL | Status: `MATCHED`, `UNMATCHED`, `DISCREPANCY`. |
| `discrepancy_notes` | TEXT | | Notes explaining any discrepancy, including manual resolution codes. |

**Design Rationale:**
- **Batch Processing:** Reconciliation is performed in daily batches, aligning with the `Financial Reconciliation & Payout` journey ([JNY-35EBA169C6](../project_glossary.md#JNY-35EBA169C6)).
- **Traceability:** Each line item links a processor transaction to a specific ledger entry, providing full auditability.
- **Discrepancy Handling:** The `match_status` and `discrepancy_notes` fields allow for manual or automated investigation of mismatches, supporting the remediation workflow in Section 4.4.

### 5.3. Payout History Schema

This schema tracks the status and details of merchant payouts. It is updated by the Payout Worker as it interacts with the payment processor (e.g., Stripe).

**Table: payout_records**

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `payout_id` | UUID | PK, NOT NULL | Unique identifier for the payout. |
| `merchant_id` | UUID | FK, NOT NULL | Reference to the merchants table. |
| `stripe_payout_id` | VARCHAR(255) | | ID of the payout in the Stripe system. |
| `amount_cents` | BIGINT | NOT NULL | Total amount to be paid out. |
| `currency` | CHAR(3) | NOT NULL | ISO 4217 currency code. |
| `status` | ENUM | NOT NULL | Status: `PENDING`, `PROCESSING`, `PAID`, `FAILED`, `CANCELLED`. |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Timestamp of payout creation. |
| `paid_at` | TIMESTAMP | | Timestamp of successful payout. |
| `failed_at` | TIMESTAMP | | Timestamp of payout failure. |
| `error_message` | TEXT | | Error message if the payout failed. |

**Design Rationale:**
- **Idempotency:** The `stripe_payout_id` allows the Payout Worker to safely retry failed payouts without creating duplicates.
- **Status Tracking:** The `status` field provides clear visibility into the payout lifecycle, supporting the `Merchant Payout Error Handling Flow` ([JNY-90B07623FB](../project_glossary.md#JNY-90B07623FB)).

### 5.4. Donation-to-Redemption Velocity (DRV) Tracking

To support the `Donation-to-Redemption Velocity (DRV)` metric (CON-D0F5814F21, CON-F89C70071E), we maintain a materialized view that aggregates credit issuance and redemption data by region and time window.

**View: drv_metrics_daily**

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `region` | VARCHAR(50) | Metropolitan footprint (e.g., SF, NYC, CHI). |
| `date` | DATE | The date for the metric. |
| `total_credits_issued_cents` | BIGINT | Total credits issued to beneficiaries in this region on this date. |
| `total_credits_redeemed_cents` | BIGINT | Total credits redeemed by beneficiaries in this region on this date. |
| `velocity_ratio` | DECIMAL(5,2) | Ratio of `total_credits_redeemed_cents` to `total_credits_issued_cents`. |

**Design Rationale:**
- **Aggregation:** This view pre-aggregates data, enabling efficient querying for the `Track Donation-to-Redemption Velocity (DRV)` concern (CON-D0F5814F21).
- **Regional Isolation:** The `region` column supports the `Regional Pool` logic for DRV tracking, allowing for metro-specific analysis.

### 5.5. Data Retention and Archival

To comply with data retention policies ([CON-4820FAD5A9](../project_glossary.md#CON-4820FAD5A9), [CON-6F604D5455](../project_glossary.md#CON-6F604D5455)) and manage storage costs, historical data will be archived to cold storage (e.g., Amazon S3 Glacier) after a defined period.

- **Active Data:** All data in the above tables is retained in the primary Aurora PostgreSQL database for 13 months.
- **Archival:** After 13 months, data is moved to S3 Glacier in a compressed, encrypted format. The primary database retains only summary-level aggregates for reporting.
- **Access:** Archived data can be restored for audit or legal purposes, subject to approval from the Platform Administrator (ACT-086A974D63).

### 5.7. Performance and Scalability

- **Indexing:** Strategic indexes are created on frequently queried columns (e.g., `transaction_id`, `actor_id`, `created_at`) to ensure fast lookups.
- **Partitioning:** The `financial_ledger_entries` table is partitioned by `created_at` (monthly) to improve query performance and simplify archival.
- **Connection Pooling:** The async workers use connection pooling to manage database connections efficiently, especially under high load.

### 5.8. Knowledge Gaps

- `KNOWLEDGE_GAP: Exact data retention period for donor transaction history vs. anonymous redemption analytics must be established by the Compliance team.`
- `KNOWLEDGE_GAP: Specific encryption key management strategy (e.g., AWS KMS key rotation schedule) must be defined by the Security team.`

---

## 3. gRPC and Event Bus Contracts for Async Workers

This section defines the asynchronous gRPC and event bus contracts for financial ledger mutations, ensuring strict consistency between the synchronous payment processing layer and the asynchronous reconciliation workers.

### 3.1. gRPC Service Definition

The `FinancialLedgerService` exposes gRPC endpoints for async workers to query ledger state and push reconciliation results. This service is internal-only and secured via mTLS.

protobuf
syntax = "proto3";

package financial_ledger;

service FinancialLedgerService {
  // Query the current balance for a specific actor
  rpc GetActorBalance (ActorBalanceRequest) returns (ActorBalanceResponse);

  // Push a new financial mutation to the immutable ledger
  rpc AppendLedgerEntry (LedgerEntryRequest) returns (LedgerEntryResponse);

  // Update the reconciliation status of a batch
  rpc UpdateReconciliationBatch (ReconciliationBatchRequest) returns (ReconciliationBatchResponse);
}

message ActorBalanceRequest {
  string actor_id = 1; // UUIDv4
  string actor_type = 2; // DONOR, BENEFICIARY, MERCHANT, NGO
}

message ActorBalanceResponse {
  int64 balance_cents = 1;
  string currency = 2; // ISO 4217
  string last_updated_at = 3; // ISO-8601
}

message LedgerEntryRequest {
  string entry_id = 1; // UUIDv4
  string transaction_id = 2; // UUIDv4
  string event_type = 3; // DONATION_RECEIVED, CREDIT_ISSUED, etc.
  string actor_id = 4; // UUIDv4
  string actor_type = 5; // DONOR, BENEFICIARY, MERCHANT, NGO
  int64 amount_cents = 6;
  string currency = 7; // ISO 4217
  string metadata_json = 8; // JSON string
  string idempotency_key = 9; // UUIDv4 for retry safety
}

message LedgerEntryResponse {
  bool success = 1;
  string error_message = 2; // Populated if success is false
}

message ReconciliationBatchRequest {
  string batch_id = 1; // UUIDv4
  string status = 2; // COMPLETED, FAILED
  int64 total_reconciled_cents = 3;
  string discrepancy_notes = 4; // Optional
}

message ReconciliationBatchResponse {
  bool success = 1;
  string error_message = 2;
}


### 3.2. Event Bus Contracts (Amazon EventBridge)

Async workers publish and consume events via Amazon EventBridge. All events MUST follow the CloudEvents 1.0 specification.

#### 3.2.1. Event: FinancialMutationEvent

Published by the synchronous payment processing layer when a new financial transaction occurs (e.g., donation, redemption). Consumed by the Financial Reconciliation and DRV Tracking workers.


{
  "source": "mealcredit.payment_processor",
  "type": "financial.mutation",
  "specversion": "1.0",
  "id": "uuid-v4",
  "time": "ISO-8601",
  "subject": "transaction_id",
  "datacontenttype": "application/json",
  "data": {
    "transaction_id": "uuid-v4",
    "event_type": "REDEMPTION_COMPLETED",
    "actor_id": "uuid-v4",
    "actor_type": "BENEFICIARY",
    "amount_cents": 1500,
    "currency": "USD",
    "idempotency_key": "uuid-v4",
    "metadata": {
      "pos_terminal_id": "term_123",
      "merchant_id": "uuid-v4"
    }
  }
}


#### 3.2.2. Event: ReconciliationBatchCompletedEvent

Published by the Financial Reconciliation Worker when a daily reconciliation batch is completed. Consumed by the Payout Orchestration Worker to trigger payouts for reconciled merchants.


{
  "source": "mealcredit.reconciliation_engine",
  "type": "reconciliation.batch.completed",
  "specversion": "1.0",
  "id": "uuid-v4",
  "time": "ISO-8601",
  "subject": "batch_id",
  "datacontenttype": "application/json",
  "data": {
    "batch_id": "uuid-v4",
    "batch_date": "YYYY-MM-DD",
    "total_reconciled_cents": 5000000,
    "status": "COMPLETED",
    "discrepancy_count": 0
  }
}


#### 3.2.3. Event: PayoutInitiatedEvent

Published by the Payout Orchestration Worker when a payout is initiated to Stripe. Consumed by the Financial Reconciliation Worker to update the ledger status.


{
  "source": "mealcredit.payout_orchestrator",
  "type": "payout.initiated",
  "specversion": "1.0",
  "id": "uuid-v4",
  "time": "ISO-8601",
  "subject": "payout_id",
  "datacontenttype": "application/json",
  "data": {
    "payout_id": "uuid-v4",
    "merchant_id": "uuid-v4",
    "amount_cents": 250000,
    "currency": "USD",
    "stripe_payout_id": "po_stripe_123",
    "idempotency_key": "uuid-v4"
  }
}


### 3.3. Idempotency and Retry Logic for Stripe Webhooks

To ensure financial consistency, all Stripe webhook processing and merchant payouts MUST be idempotent. The `idempotency_key` field in the gRPC and EventBridge contracts is critical for this.

**Idempotency Enforcement:**
- **Stripe Webhooks:** The `WebhookHandler` MUST extract the `idempotency_key` from the Stripe event payload. Before processing, it checks the `financial_ledger_entries` table for an existing entry with the same `idempotency_key`. If found, the event is acknowledged as successfully processed, and no duplicate ledger mutation occurs.
- **Payout Orchestration:** The `PayoutWorker` MUST use the `idempotency_key` when calling the Stripe API. If a payout fails, the worker retries with the same `idempotency_key`. Stripe will return the original payout object, preventing duplicate charges.

**Retry Logic:**
- **Transient Errors:** If a Stripe API call fails with a transient error (e.g., 429, 500), the worker retries with exponential backoff (Section 4.1).
- **Permanent Errors:** If a Stripe API call fails with a permanent error (e.g., 400, 401), the event is routed to the DLQ (Section 4.2).

### 3.4. Data Flow for DRV Tracking and Credit Pool Utilization Alerts

The DRV Tracking Worker consumes `FinancialMutationEvent` events to calculate the Donation-to-Redemption Velocity (DRV) and monitor Credit Pool Utilization.

**Data Flow:**
1. **Event Ingestion:** The DRV Tracking Worker subscribes to the `financial.mutation` event type on EventBridge.
2. **Aggregation:** For each event, the worker updates a materialized view (`drv_metrics_daily`) with the latest credit issuance and redemption data, partitioned by `region` and `date`.
3. **DRV Calculation:** The worker calculates the `velocity_ratio` (total_credits_redeemed_cents / total_credits_issued_cents) for each region.
4. **Credit Pool Utilization Alert:** The worker monitors the total credits issued vs. total credits redeemed for each region. If the utilization rate exceeds 85% (CON-2059B17FB2, CON-7031BE57B3), the worker publishes a `CreditPoolUtilizationWarning` event to EventBridge.
5. **Alerting:** The `CreditPoolUtilizationWarning` event triggers an alert to the Platform Administrator (ACT-086A974D63) via PagerDuty, indicating that a regional credit pool is nearing depletion and may require manual intervention or additional funding activation.

**Knowledge Gap:**
- `KNOWLEDGE_GAP: The exact threshold for Credit Pool Utilization Rate (85%) is a design assumption. The Compliance team must confirm if this threshold aligns with regulatory requirements for quasi-cash instruments (CON-226A13FFB8, CON-B1DFEBEC8C).`

---

## VP decision

**Decision:** Approved

---

## VP feedback

(No feedback)

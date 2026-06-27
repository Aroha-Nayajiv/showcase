# Merchant Payout Failure & Error Handling

## 1. Merchant Payout Error Taxonomy & Classification

This artifact defines the canonical error taxonomy, Stripe status mappings, and financial edge-case handling rules for the Merchant Payout Failure & Error Handling surface. It ensures that the Financial Reconciliation & Payout Workers ([JNY-35EBA169C6](../project_glossary.md#jny-35eba169c6)) can categorize, route, and audit payout events with precision, directly supporting the Transaction & Financial Engine capability ([CAP-TRANSACTION-FINANCIAL-ENGINE](../project_glossary.md#cap-transaction-financial-engine)) and the Merchant Payout Error Handling Flow ([JNY-90B07623FB](../project_glossary.md#jny-90b07623fb)).

### 1.1 Stripe Payout Status Mapping

The following table defines the canonical mapping between Stripe's asynchronous payout statuses and the platform's internal error codes. This mapping is the single source of truth for the Merchant Payout Failure & Error Handling surface.

| Stripe Status | Internal Error Code | Severity | Description & Action |
| :--- | :--- | :--- | :--- |
| pending | PAYOUT_PENDING | INFO | Payout is queued or processing. No action required. Monitor for transition to paid or failed. |
| paid | PAYOUT_SUCCESS | INFO | Funds have been successfully transferred to the Merchant's bank account. Update merchant ledger balance. |
| failed | PAYOUT_FAILED_BANK | WARNING | Payout failed due to bank rejection (e.g., closed account, invalid routing). Trigger Merchant Payout Error Handling Flow (JNY-90B07623FB) to notify the Merchant and pause further payouts until resolved. |
| canceled | PAYOUT_CANCELED | WARNING | Payout was canceled by the Platform Administrator or the Merchant. Revert any reserved funds in the internal ledger. |
| errored | PAYOUT_SYSTEM_ERROR | CRITICAL | Payout failed due to a platform-side error (e.g., Stripe API timeout, internal validation failure). Immediate investigation required. |

### 1.2 Financial Edge Case Taxonomy

This taxonomy explicitly handles financial edge cases, specifically double-spending prevention and voided transactions, as required by the Transaction & Financial Engine capability. These cases are categorized for downstream reconciliation and audit logging.

| Edge Case | Internal Error Code | Severity | Description & Action |
| :--- | :--- | :--- | :--- |
| Double-Spending Attempt | DOUBLE_SPEND_ATTEMPT | CRITICAL | A Beneficiary attempted to redeem credits that were already consumed. The transaction is blocked, and the Fraud Detection & Fraud Prevention Screening capability is triggered. |
| Voided Transaction | TRANSACTION_VOIDED | WARNING | A transaction was voided by the Merchant or Platform Administrator before settlement. The credit is returned to the Beneficiary's pool. |
| Insufficient Funds | INSUFFICIENT_CREDIT_POOL | ERROR | The Merchant's payout request exceeds the available balance in the associated Credit Pool. The payout is rejected, and the Merchant is notified. |
| Duplicate Payout Request | DUPLICATE_PAYOUT_REQUEST | ERROR | A payout request with an idempotency key that already exists is received. The system returns the status of the original request. |

### 1.3 Audit Logging & Compliance

All error events, particularly those with CRITICAL or ERROR severity, must be logged to AWS CloudTrail for SOC2 Type II evidence, as specified in [CON-E84412A0FA](../project_glossary.md#con-e84412a0fa). The log entry must include:

- Event ID: Unique identifier for the error event.
- Timestamp: ISO 8601 formatted timestamp of the event.
- Error Code: The canonical internal error code.
- Severity Level: The severity level assigned to the error.
- Merchant ID: The ID of the affected Merchant (anonymized if required by PII Segregation & Anonymization Strategy).
- Stripe Payout ID: The original Stripe payout ID, if applicable.
- Action Taken: A brief description of the automated action taken (e.g., "Paused payouts", "Triggered fraud alert").

### 1.4 Integration Points

- Financial Reconciliation & Payout Workers: This taxonomy provides the error codes that the reconciliation workers will use to categorize and route payout events.
- Merchant Payout Error Handling Flow (JNY-90B07623FB): The PAYOUT_FAILED_BANK and PAYOUT_SYSTEM_ERROR codes will trigger this user journey to guide the Merchant through resolution.
- Fraud Detection & Fraud Prevention Screening ([CAP-FRAUD-DETECTION-FRAUD-PREVENTION-SCREENING](../project_glossary.md#cap-fraud-detection-fraud-prevention-screening)): The DOUBLE_SPEND_ATTEMPT code will trigger this capability for immediate investigation.

### 2.2 Idempotency Store and Append-Only Log Storage

The idempotency state is stored in a dedicated, append-only table within the Aurora PostgreSQL database. This table is part of the broader append-only cryptographic log ([CON-6061FCCA83](../project_glossary.md#con-6061fcca83)) and is designed to be immutable once written.

**Table Schema: payout_idempotency_log**

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier for the log entry. |
| idempotency_key_hash | CHAR(64) | UNIQUE, NOT NULL | The SHA-256 hash of the idempotency key. |
| merchant_id | UUID | NOT NULL, REFERENCES merchants(id) | The merchant associated with the payout. |
| payout_batch_id | UUID | NOT NULL | The batch ID for the payout. |
| status | ENUM | NOT NULL, CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED')) | The current status of the payout request. |
| request_payload | JSONB | NOT NULL | The original payout request payload for audit purposes. |
| response_payload | JSONB | NULL | The response payload from the Stripe Issuing Proxy (if completed). |
| error_code | VARCHAR(50) | NULL | The error code if the status is 'FAILED'. |
| created_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL | Timestamp of the initial request. |
| updated_at | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL | Timestamp of the last status update. |
| ledger_hash | CHAR(64) | NOT NULL | A cryptographic hash of the previous row's ledger_hash and current row data, ensuring append-only integrity. |

**Append-Only Integrity:**
The ledger_hash column ensures that the log is cryptographically verifiable. Any attempt to modify a past row will break the hash chain, alerting the SOC2 Type II audit system ([CON-FBBBF07295](../project_glossary.md#con-fbbbf07295)).

### 2.3 API Contract for Payout Idempotency

The following API contract defines the interface for submitting and checking payout requests. This contract is consumed by the Financial Reconciliation & Payout Workers.

**Endpoint: `POST /api/v1/payouts/submit`**

**Request Headers:**

| Header | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| Idempotency-Key | String | Yes | The generated idempotency key hash. |
| Content-Type | String | Yes | `application/json` |

**Request Body:**

{
 "merchant_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
 "payout_batch_id": "11111111-2222-3333-4444-555555555555",
 "transaction_ref": "TXN-20231027-001",
 "amount": 10000,
 "currency": "USD",
 "metadata": {
 "source": "financial_reconciliation_worker"
 }
}

**Response Codes:**

- `201 Created`: Payout request accepted and queued for processing.
- `200 OK`: Payout request is a duplicate of a previously completed request. Returns the original response payload.
- `409 Conflict`: Payout request is a duplicate of a previously failed request. The client may retry with a new idempotency key.
- `422 Unprocessable Entity`: Invalid idempotency key or request payload.
- `500 Internal Server Error`: Unexpected server error.

**Response Body (200 OK - Duplicate):**

{
 "status": "COMPLETED",
 "payout_id": "payout_123456",
 "response_payload": {
 "stripe_charge_id": "ch_1234567890",
 "settled_at": "2023-10-27T10:00:00Z"
 }
}

### 2.4 Validation Logic for Duplicate Detection

The validation logic is executed by the Merchant Payout Failure & Error Handling service upon receiving a `POST /api/v1/payouts/submit` request.

1. Key Generation: The service generates the idempotency_key_hash from the request body.
2. Lookup: The service queries the payout_idempotency_log table for a row with a matching idempotency_key_hash.
3. Status Check:
 - If a row is found and its status is COMPLETED, the service returns the `200 OK` response with the original response_payload.
 - If a row is found and its status is FAILED, the service returns a `409 Conflict` response, allowing the client to retry with a new key.
 - If no row is found, the service proceeds to step 4.
4. Insertion: The service inserts a new row into the payout_idempotency_log table with status set to PENDING.
5. Processing: The request is then queued for processing by the Financial Reconciliation & Payout Workers.

## 3. Merchant Payout Reconciliation API & Data Models

This artifact defines the API contracts and data models for the Merchant Payout Reconciliation service, enabling the Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) to manage failed payouts, initiate manual retries, and review reconciliation reports. This service acts as the operational interface for the capabilities defined in [CAP-MERCHANT-PAYOUT-FAILURE-ERROR-HANDLING](../project_glossary.md#cap-merchant-payout-failure-error-handling) and the journey JNY-90B07623FB.

### 3.1 Architectural Context & Boundaries

The Merchant Payout Reconciliation service is a stateless API layer that orchestrates interactions between the Platform Administrator dashboard, the Financial Reconciliation & Payout Workers (sibling artifact), and the Stripe Issuing Proxy (sibling artifact).

- Primary Actor: Platform Administrator (ACT-086A974D63).
- Key Capability: CAP-MERCHANT-PAYOUT-FAILURE-ERROR-HANDLING.
- Key Journey: JNY-90B07623FB (Merchant Payout Error Handling Flow).
- Dependencies:
 - Financial Ledger Data Model (Sibling): For reading immutable transaction states.
 - Financial Reconciliation & Payout Workers (Sibling): For executing retry logic and payout adjustments.
 - Stripe Issuing Proxy (Sibling): For interacting with Stripe's payout and dispute APIs.

### 3.2 Data Models

#### 3.2.1. Payout Failure Event
Represents a discrete failure event during the payout lifecycle. This model is derived from the immutable ledger entries in the Financial Ledger Data Model.

{
 "payout_failure_id": "string (UUIDv4)",
 "merchant_id": "string (UUIDv4)",
 "stripe_payout_id": "string",
 "error_code": "string",
 "failure_message": "string",
 "amount_failed": {
 "value": "integer (cents)",
 "currency": "string (ISO 4217)"
 },
 "attempted_at": "string (ISO 8601 UTC)",
 "status": "string (Enum: PENDING_REVIEW, RETRY_IN_PROGRESS, RETRY_SUCCESS, RETRY_EXHAUSTED, MANUAL_ADJUSTMENT_PENDING)",
 "metadata": {
 "trace_id": "string",
 "error_stack_hash": "string (SHA-256)"
 }
}

#### 3.2.2. Reconciliation Report
A summary view of payout health for a specific merchant over a time range. This model aggregates data from the Financial Ledger Data Model.

{
 "report_id": "string (UUIDv4)",
 "merchant_id": "string (UUIDv4)",
 "report_period": {
 "start_date": "string (ISO 8601 UTC)",
 "end_date": "string (ISO 8601 UTC)"
 },
 "total_payouts_attempted": "integer",
 "total_payouts_succeeded": "integer",
 "total_payouts_failed": "integer",
 "total_amount_attempted": {
 "value": "integer (cents)",
 "currency": "string (ISO 4217)"
 },
 "total_amount_failed": {
 "value": "integer (cents)",
 "currency": "string (ISO 4217)"
 },
 "failure_rate_percentage": "float",
 "top_failure_codes": [
 {
 "code": "string",
 "count": "integer"
 }
 ]
}

### 3.3 API Endpoints

All endpoints are protected by OAuth2/JWT and require the `Platform Administrator` role (ACT-086A974D63) with appropriate scopes.

#### 3.3.1. List Failed Payouts
Retrieves a paginated list of failed payouts, supporting filtering by error type, date range, and merchant status.

- Method: GET
- Path: `/api/v1/reconciliation/payout-failures`
- Query Parameters:
 - merchant_id (optional): Filter by specific merchant.
 - failure_code (optional): Filter by specific failure code.
 - status (optional): Filter by status (e.g., PENDING_REVIEW).
 - start_date (optional): ISO 8601 date.
 - end_date (optional): ISO 8601 date.
 - page (optional, default 1): Page number.
 - page_size (optional, default 20, max 100): Items per page.
- Response: `200 OK` with a list of PayoutFailureEvent objects.
- Error Responses:
 - `400 Bad Request`: Invalid query parameters.
 - `401 Unauthorized`: Missing or invalid JWT.
 - `403 Forbidden`: Insufficient permissions.

#### 3.3.2. Get Payout Failure Details
Retrieves detailed information for a specific failed payout, including audit logs and retry history.

- Method: GET
- Path: `/api/v1/reconciliation/payout-failures/{payout_failure_id}`
- Response: `200 OK` with a PayoutFailureEvent object.
- Error Responses:
 - `404 Not Found`: Payout failure ID not found.

#### 3.3.3. Initiate Manual Retry
Triggers a manual retry for a specific failed payout. This action is logged for audit purposes.

- Method: POST
- Path: `/api/v1/reconciliation/payout-failures/{payout_failure_id}/retry`
- Request Body: None (or optional reason string for audit log).
- Response: `202 Accepted` with a RetryJob object containing the job ID for status tracking.
- Error Responses:
 - `400 Bad Request`: Payout is not in a retryable state.
 - `404 Not Found`: Payout failure ID not found.

#### 3.3.4. Generate Reconciliation Report
Generates a reconciliation report for a specific merchant over a specified time range.

- Method: POST
- Path: `/api/v1/reconciliation/reports`
- Request Body:

{
 "merchant_id": "string (UUIDv4)",
 "start_date": "string (ISO 8601 UTC)",
 "end_date": "string (ISO 8601 UTC)"
}

- Response: `200 OK` with a ReconciliationReport object.
- Error Responses:
 - `400 Bad Request`: Invalid date range or merchant ID.

### 3.5 Knowledge Gaps & Assumptions

- `KNOWLEDGE_GAP: The exact max_retries value and backoff strategy for automatic retries are defined in the Financial Reconciliation & Payout Workers sibling artifact. This API contract assumes a default of 3 retries with exponential backoff, but the exact values must be synchronized.`
- `KNOWLEDGE_GAP: The specific failure_code enum values are derived from Stripe's API error codes. A complete mapping of Stripe error codes to our internal failure_code enum must be established and documented in the Stripe Issuing Proxy sibling artifact.`
- ASSUMPTION: The Platform Administrator role (ACT-086A974D63) has access to all payout failure data across all merchants. If multi-tenant isolation is required, the Access Control & Multi-Tenant Isolation sibling artifact must define the scoping rules for this API.
- ASSUMPTION: The trace_id in the PayoutFailureEvent metadata is propagated from the Distributed Tracing & Log Aggregation sibling artifact, enabling end-to-end traceability of the failed payout.

### 3.6 Validation

This design is complete when:
1. The API endpoints are implemented and tested against the defined contracts.
2. The data models are implemented in the Financial Ledger Data Model sibling artifact.
3. The retry logic is implemented in the Financial Reconciliation & Payout Workers sibling artifact.
4. The audit logging is integrated with the Distributed Tracing & Log Aggregation sibling artifact.
5. The Platform Administrator dashboard (Next.js Dashboard Architecture sibling artifact) is updated to consume these APIs.

---

### 4.1 Alerting Thresholds & Automated Notifications

The alerting system is designed to detect anomalies in the payout lifecycle, specifically focusing on the CAP-MERCHANT-PAYOUT-FAILURE-ERROR-HANDLING capability. Alerts are triggered based on real-time monitoring of the CAP-TRANSACTION-FINANCIAL-ENGINE and [CAP-TRANSACTION-REFUND-REVERSAL-ENGINE](../project_glossary.md#cap-transaction-refund-reversal-engine).

#### 4.1.1. Critical Failure Thresholds

The following thresholds define when an automated alert is triggered. These thresholds are calibrated to balance operational responsiveness with noise reduction, ensuring that the Platform Administrator is not overwhelmed by transient errors.

| Alert Type | Metric | Threshold | Severity | Notification Channel |
| :--- | :--- | :--- | :--- | :--- |
| Systemic Payout Failure | Payout Failure Rate | > 5% of total payout attempts in a 15-minute window | Critical | PagerDuty, SMS, Email |
| Credit Pool Exhaustion | Credit Pool Utilization Rate | > 85% (as per [CON-2059B17FB2](../project_glossary.md#con-2059b17fb2)) | High | Email, Dashboard Alert |
| Stripe Webhook Latency | Stripe Webhook Processing Latency | > 150ms average (as per [CON-06232374D9](../project_glossary.md#con-06232374d9)) | Medium | Email, Dashboard Alert |
| Merchant Payout Stagnation | Time-to-Payout | > 24 hours for any single merchant batch | High | Email, Dashboard Alert |
| Compliance Violation | PCI-DSS Level 1 Compliance Check | Any raw card data detection | Critical | PagerDuty, SMS, Email |

#### 4.1.2. Notification Mechanisms

- PagerDuty Integration: Used for Critical and High severity alerts. Ensures immediate attention from the on-call Platform Administrator.
- Email Notifications: Used for Medium and High severity alerts. Sent to the `NGO Operator` and `Platform Administrator` distribution lists.
- Dashboard Alerts: Real-time visual indicators in the Next.js Merchant Dashboard and Admin Dashboard.

### 4.2 SOC2 Type II Audit Logging via AWS CloudTrail

To ensure compliance with [CON-81FB01F06B](../project_glossary.md#con-81fb01f06b) and CON-E84412A0FA, all administrative ledger operations and infrastructure changes related to merchant payouts are logged to AWS CloudTrail. This provides an immutable, cryptographically verifiable audit trail.

#### 4.2.1. CloudTrail Event Categories

The following event categories are captured and logged:

1. Administrative Ledger Operations:
 - Manual payout overrides by `Platform Administrator`.
 - Dispute resolution actions by `Dispute Adjudicator`.
 - Fraud investigation actions by `Platform-NGO Fraud Investigation Flow` ([JNY-CA74D631DC](../project_glossary.md#jny-ca74d631dc)).

2. Infrastructure Changes:
 - Changes to IAM roles and policies affecting payout services.
 - Modifications to AWS Lambda function configurations.
 - Updates to Aurora PostgreSQL security groups.

#### 4.2.2. Log Retention & Integrity

- Retention Period: `KNOWLEDGE_GAP: The exact log retention period for SOC2 Type II compliance must be established by the Compliance Officer. Standard practice is 7 years for financial records.`
- Integrity: CloudTrail logs are encrypted at rest using AWS KMS and signed to prevent tampering.

### 4.3 Error Handling & Recovery Workflows

#### 4.3.1. Payout Failure Classification

Payout failures are classified into three categories to determine the appropriate response:

1. Transient Failure: Temporary network or service issues. Handled by automatic retry with exponential backoff.
2. Permanent Failure: Invalid merchant account, insufficient funds, or compliance block. Requires manual intervention by the `Platform Administrator`.
3. Systemic Failure: Widespread payout failures indicating a platform-level issue. Triggers Critical alerts and requires immediate escalation.

#### 4.3.2. Recovery Actions

- Transient Failures: Automatic retry up to 3 times. If unsuccessful, the transaction is marked for manual review.
- Permanent Failures: Transaction is rolled back, and the Merchant is notified via the Next.js Dashboard. The `NGO Operator` is alerted to investigate the merchant's account status.
- Systemic Failures: Payout service is paused. The `Platform Administrator` is notified via PagerDuty. A post-mortem is initiated.
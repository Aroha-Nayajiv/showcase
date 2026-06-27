# Integration Adapters & External Contracts

## 1. Stripe Issuing Proxy & Virtual Card Provisioning API Contract

This artifact defines the internal API contract for the Stripe Issuing Proxy, enabling the secure provisioning of virtual culinary credits for Beneficiaries (ACT-ADA6716160). The design strictly enforces PCI-DSS Level 1 compliance (CON-66390130AA) by ensuring zero raw card data touches MealCredit servers, relying entirely on Stripe Elements/Checkout for any sensitive data entry.

### 1.1 Architectural Boundary & Compliance Posture

The Stripe Issuing Proxy acts as a secure adapter between the internal event-driven serverless architecture and the external Stripe Issuing API. Its primary responsibility is to translate internal credit pool allocations into Stripe Issuing Card objects without ever handling, logging, or storing raw Primary Account Numbers (PANs), CVVs, or Expiry dates.

 Compliance Constraint: All card data entry must occur client-side via Stripe Elements or hosted checkout flows. The MealCredit backend only receives and processes Stripe-generated tokens.
 Data Isolation: Beneficiary demographic status and legal names are cryptographically segregated from public-facing transaction data (CON-0A0288EED4, CON-92F07E31B0). The proxy only handles the financial instrument mapping.
 Latency Target: Card provisioning requests must be processed asynchronously to maintain the p99 latency target of 250ms for POS clearance (CON-6D5E21557B, CON-7F03CF540E). Provisioning is a setup action, not a real-time transaction, but the API must return immediately with a correlation ID for status polling.

### 1.2 Internal API Contract: Card Provisioning

The following REST API endpoint is defined for the internal API Orchestration Layer (SUR-85E4A5B6E7) to trigger virtual card creation for a verified Beneficiary.

Endpoint: `POST /v1/issuing/cards`

Request Schema:

- **beneficiary_id**: string (UUIDv4, required)
- **credit_pool_id**: string (UUIDv4, required)
- **initial_allocation_amount**: integer (cents, required, > 0)
- **metadata**: {'ngo_operator_id': 'string (UUIDv4, required)', 'campaign_id': 'string (optional)'}

Response Schema (202 Accepted):

- **correlation_id**: string (UUIDv4, unique request identifier)
- **status**: PROVISIONING_IN_PROGRESS
- **polling_endpoint**: /v1/issuing/cards/{correlation_id}/status

Error Responses:

 `400 Bad Request`: Invalid UUID format, missing required fields, or initial_allocation_amount exceeds the available balance in the specified credit_pool_id.
 `403 Forbidden`: The beneficiary_id is not verified or is currently suspended.
 `409 Conflict`: A provisioning request for this beneficiary_id is already in progress.

### 1.3 External Stripe API Mapping

The proxy maps the internal request to the Stripe Issuing API. The following mapping ensures that no sensitive data is exposed in logs or internal databases.

| Internal Field | Stripe Metadata Key | Transformation Logic |
|---|---|---|
| beneficiary_id | `metadata[beneficiary_hash]` | Hashed using SHA-256 with a project-specific salt. Never stored as plain text. |
| credit_pool_id | `metadata[pool_id]` | Passed as-is for internal reconciliation. |
| metro_region | `metadata[region]` | Passed as-is for regional reporting. |
| initial_allocation_amount | amount (in issuing.card_issuance) | Converted from cents to integer for Stripe. |
| ngo_operator_id | `metadata[ngo_id]` | Passed as-is for audit trails. |

Stripe API Call:

http
POST https://api.stripe.com/v1/issuing/card_issuances
{
 "card": {
 "currency": "usd",
 "type": "virtual",
 "spending_controls": {
 "spending_limits": [
 {
 "amount": 10000, // Example: $100.00
 "interval": "daily",
 "categories": ["food_and_drink"]
 }
 ]
 }
 },
 "metadata": {
 "beneficiary_hash": "<SHA256_HASH>",
 "pool_id": "<UUID>",
 "ngo_id": "<UUID>"
 }
}

### 1.4 Webhook Handling & Status Synchronization

To maintain consistency between the internal state and Stripe's state, the proxy must handle Stripe webhooks for card issuance events.

Webhook Event: issuing_card_issued

Processing Logic:
1. Verify the webhook signature using Stripe's secret key.
2. Extract the card_id and metadata from the event payload.
3. Update the internal issuing_cards table (owned by sibling artifact: Data Model & Schema Design) with the stripe_card_id and `status: active`.
4. Trigger an internal event card.provisioned to notify downstream services (e.g., Mobile App Push Notifications) that the Beneficiary can now use their virtual card.

Latency Consideration: Webhook processing must be idempotent to handle duplicate events from Stripe. The correlation_id or card_id should be used as the idempotency key.

### 1.5 Validation & Acceptance Criteria

 PCI-DSS Compliance: No raw card data is logged or stored in any MealCredit database or log file.
 API Contract: The `POST /v1/issuing/cards` endpoint returns a `202 Accepted` with a correlation_id within 100ms.
 Data Integrity: The beneficiary_hash is correctly generated and stored in Stripe metadata.
 Error Handling: Invalid requests return clear, structured error messages without exposing internal system details.

---

## 2. POS Gateway Webhook Integration Contract

This section defines the technical contract for the Stripe Webhook Adapter, which processes real-time POS transaction events. The adapter acts as the bridge between the external Payment Processing Surface (SUR-5B18C8719F) and the internal API Orchestration Layer (SUR-85E4A5B6E7), ensuring strict PCI-DSS Level 1 compliance by ensuring zero raw card data touches MealCredit servers, relying entirely on Stripe Elements and Stripe Issuing tokens.

### 2.1 Event Schema & Payload Mapping

The adapter MUST strictly accept and validate the checkout.session.completed event type. The internal ledger mutation logic is triggered only upon this specific event.

Input Schema (Stripe checkout.session.completed):

- **id**: evt_1234567890
- **type**: checkout.session.completed
- **data**: {'object': {'id': 'cs_1234567890', 'payment_intent': 'pi_1234567890', 'customer': 'cus_1234567890', 'metadata': {'beneficiary_id': 'uuid_v4_hashed', 'merchant_id': 'acct_1234567890', 'transaction_ref': 'uuid_v4_internal'}, 'amount_total': 1500, 'currency': 'usd'}}

Internal Ledger Mutation Logic:
Upon successful validation, the adapter MUST execute the following synchronous steps:
1. Extract Metadata: Parse beneficiary_id and merchant_id from the session metadata.
2. Validate Amount: Ensure amount_total matches the expected credit pool deduction.
3. Append-Only Ledger Insert: Execute an INSERT into the Financial Ledger Data Model (deferred to sibling artifact: Data Model & Schema Design) with the following fields:
transaction_id: UUIDv4 (internal)
beneficiary_id: Hashed UUID (from metadata)
merchant_id: Stripe Connected Account ID (from metadata)
amount: Integer (cents)
currency: String (ISO 4217)
status: "COMPLETED"
stripe_event_id: String (for audit trail)
timestamp: ISO 8601 UTC
4. Response: Return `200 OK` immediately after the ledger insert to minimize latency.

## 3. Offline Token Verification Contract

This contract defines the cryptographic verification logic and state reconciliation process for offline QR/barcode fallback mechanisms. It ensures that MealCredit transactions can proceed with sub-150ms latency (CON-06232374D9) even during network partitions, while strictly preventing replay attacks (CON-AA83B13877) and maintaining financial ledger consistency (CON-10F4381094).

### 3.1 Cryptographic Token Structure

The offline token is a self-contained, time-bound JWT (JSON Web Token) signed using the project's master signing key. It is generated by the Beneficiary's Expo mobile application (ACT-ADA6716160) and scanned by the Merchant's (ACT-AF904DCFF9) POS device.

Token Schema:

| Field | Type | Description | Constraint |
|---|---|---|---|
| iss | String | Issuer ID | Must be mealcredit-offline |
| sub | String | Beneficiary UUID | Hashed/Anonymized ID (CON-0A0288EED4) |
| iat | Integer | Issued At (Unix Timestamp) | Must be within T_WINDOW of current time |
| exp | Integer | Expiration (Unix Timestamp) | iat + T_WINDOW |
| nonce | String | Random Nonce | 128-bit random string to prevent identical token replay |
| amt | Float | Requested Amount | Must be <= beneficiary_credit_pool |
| sig | String | HMAC-SHA256 Signature | Signed over `iss:sub:iat:exp:nonce:amt` using MASTER_SIGNING_KEY |

Assumption: T_WINDOW is set to 60 seconds. MASTER_SIGNING_KEY is rotated quarterly. These values are `ASSUMPTION: T_WINDOW=60s, Key Rotation=Quarterly - Security Architecture & Access Control must ratify these thresholds based on PCI-DSS and operational risk.`

### 3.2 Verification Logic

The Offline Token Verification Adapter (part of the API Orchestration Layer, SUR-85E4A5B6E7) performs the following synchronous checks upon receiving a scanned token:

1. Signature Validation: Verify sig against the payload using the current active MASTER_SIGNING_KEY. If invalid, reject immediately (401 Unauthorized).
2. Time-Bound Check: Ensure exp > current_time and iat < current_time. Reject if outside the T_WINDOW to prevent replay attacks (CON-AA83B13877).
3. Nonce Uniqueness (Local Cache): Check the local Redis cache (SUR-5B18C8719F) for the nonce. If present, reject as a replay attempt. If absent, add nonce to cache with a TTL of T_WINDOW + 10s.
4. Credit Pool Validation: Query the Financial Ledger (SUR-FA61592CD4) to ensure the beneficiary_credit_pool has sufficient balance for amt. This query must be optimized for p99 latency < 250ms (CON-6D5E21557B).

### 3.3 Fallback State Reconciliation

In the event of a network partition where the central ledger is unreachable, the Merchant POS device (running Next.js on Edge runtime) acts as a local state holder.

1. Local Ledger: The POS device maintains a local, append-only SQLite database of pending offline transactions.
2. Token Generation: The Beneficiary app generates the token locally, signed with the shared MASTER_SIGNING_KEY.
3. Reconciliation Process:
 When connectivity is restored, the POS device batches pending transactions and pushes them to the central `POST /v1/reconciliation/offline` endpoint.
 The central system validates the signatures and nonces again (to prevent double-spending across multiple POS devices).
 Valid transactions are committed to the Aurora PostgreSQL ledger (SUR-FA61592CD4).
 Invalid transactions (e.g., double-spent nonces) are flagged for manual review by the Dispute Adjudicator (ACT-7BA340FF76).

### 3.4 Security & Compliance Constraints

 PCI-DSS Level 1 (CON-66390130AA): Zero raw card data is stored or transmitted. The token contains only anonymized beneficiary IDs and transaction amounts.
 Data Isolation (CON-0A0288EED4): Beneficiary demographic data is never included in the token payload.
 Replay Attack Prevention (CON-AA83B13877): The combination of time-bound expiration and unique nonces ensures that a captured token cannot be reused.

### 3.5 Dependencies & Deferrals

 Data Model: The beneficiary_credit_pool schema is defined in the Financial Ledger Data Model artifact.
 Security: The MASTER_SIGNING_KEY rotation policy is defined in the Security Architecture & Access Control artifact.
 API Surface: The `POST /v1/reconciliation/offline` endpoint contract is defined in the API Surface & Contract Design artifact.

---

## 4. Data Persistence Layer Schema for SUR-FA61592CD4

This section defines the Aurora PostgreSQL schema for SUR-FA61592CD4, focusing on the financial ledger and beneficiary credit pools. It enforces strict data isolation (CON-0A0288EED4) by cryptographically segregating beneficiary demographic status and legal names from public data, ensuring PCI-DSS Level 1 compliance (CON-66390130AA) by storing zero raw card data.

### 4.1 Beneficiary Identity & PII Segregation

To satisfy CON-0A0288EED4 and CON-FCFF86A326 (Classify all beneficiary-related data as 'Highly Sensitive'), the schema splits beneficiary identity into two distinct tables. The beneficiary_pii table is restricted to cryptographic hashing layers only, while the beneficiary_credit_profile table holds operational data.

Table: beneficiary_pii
beneficiary_id (UUID, PK): Stable local identifier.
legal_name_hash (VARCHAR(64)): SHA-256 hash of the legal name. Never stored in plaintext.
demographic_status_hash (VARCHAR(64)): SHA-256 hash of demographic status. Never stored in plaintext.
salt (VARCHAR(64)): Unique salt per record to prevent rainbow table attacks.
created_at (TIMESTAMPTZ): Record creation time.

Table: beneficiary_credit_profile
beneficiary_id (UUID, PK, FK to beneficiary_pii): Links to PII table.
stripe_issuing_card_id (VARCHAR(255)): Reference to Stripe Issuing Card ID. No raw PAN/CVV.
credit_pool_id (UUID, FK to credit_pools): Links to the donor-funded pool.
current_balance (NUMERIC(15, 4), NOT NULL): Current available credits.
is_active (BOOLEAN): Status of the credit profile.
last_transaction_id (UUID): Reference to the last processed transaction.

### 4.2 Financial Ledger & Credit Pools

The financial ledger must be append-only to ensure auditability (CON-1762EA5021, CON-6061FCCA83). Credit pools track the aggregate funds from donors (CON-2059B17FB2, CON-7031BE57B3).

Table: credit_pools
pool_id (UUID, PK): Unique identifier for the donor-funded pool.
donor_id (UUID, FK to donors): The donor who funded this pool.
total_funded (NUMERIC(15, 4), NOT NULL): Total amount funded.
total_redeemed (NUMERIC(15, 4), NOT NULL, DEFAULT 0): Total amount redeemed.
utilization_rate (NUMERIC(5, 4), GENERATED ALWAYS AS (total_redeemed / total_funded) STORED): Computed column for monitoring (CON-2059B17FB2).
status (ENUM: 'ACTIVE', 'EXHAUSTED', 'FROZEN'): Current state of the pool.

Table: financial_ledger
ledger_id (UUID, PK): Unique identifier for the ledger entry.
transaction_id (UUID, NOT NULL): Reference to the external/internal transaction.
beneficiary_id (UUID, FK to beneficiary_credit_profile): The beneficiary involved.
pool_id (UUID, FK to credit_pools): The pool debited/credited.
amount (NUMERIC(15, 4), NOT NULL): Positive for credit, negative for debit.
transaction_type (ENUM: 'DONATION', 'REDEMPTION', 'REFUND', 'ADJUSTMENT'): Type of mutation.
timestamp (TIMESTAMPTZ, NOT NULL): When the mutation occurred.
hash_chain (VARCHAR(64), NOT NULL): SHA-256 hash of the previous ledger entry's hash, ensuring immutability.
previous_hash (VARCHAR(64), NOT NULL): Hash of the previous entry.

### 4.3 Data Isolation & Access Control

Row-Level Security (RLS): Enabled on all tables. beneficiary_pii is accessible only by the `Platform Administrator` (ACT-086A974D63) role. beneficiary_credit_profile is accessible by `NGO Operator` (ACT-09E028AEB0) and Merchant (ACT-AF904DCFF9) roles, but only for their assigned beneficiaries/merchants.
Column-Level Security: legal_name_hash and demographic_status_hash are restricted to the `Platform Administrator` role.
Audit Logging: All mutations to financial_ledger are logged to AWS CloudTrail (CON-BB253DF0A2, CON-FBBBF07295).

## 5. API Orchestration Layer Contract (SUR-85E4A5B6E7)

This section defines the internal service boundaries and event-driven messaging patterns that connect the Stripe Proxy, POS Gateway, and Offline Verification services. It ensures strict data isolation, PCI-DSS Level 1 compliance, and sub-150ms latency for the MealCredit platform.

### 5.1 Architectural Surface & Service Boundaries

The API Orchestration Layer (SUR-85E4A5B6E7) acts as the central nervous system for financial transactions. It decouples the external financial rails (Stripe Issuing/Connect) from the internal business logic (Beneficiary Eligibility, Merchant Operations) via a strict event-driven contract.

Service Boundaries:

1. Stripe Proxy Service (SPS):
 Responsibility: Manages all interactions with Stripe Issuing and Stripe Connect. It is the sole entry point for any data that could potentially touch raw card details, ensuring PCI-DSS Level 1 compliance (CON-66390130AA) by tokenizing all sensitive data before it enters the MealCredit system.
 Boundary: SPS exposes a RESTful API for internal services to request virtual card provisioning and transaction status. It does not expose any internal state or business logic.
 Dependency: Relies on the `Stripe Issuing Proxy Contract` (sibling artifact) for specific API calls to Stripe.

2. POS Gateway Service (PGS):
 Responsibility: Handles real-time POS transaction webhooks from Stripe. It validates the webhook signature, extracts the transaction details, and publishes a TransactionCompleted event to the internal event bus. It also handles the synchronous response to the POS terminal to ensure sub-150ms latency (CON-06232374D9).
 Boundary: PGS is a high-throughput, low-latency service. It does not perform complex business logic; it only validates, transforms, and publishes events.
 Dependency: Relies on the `POS Gateway Webhook Integration Contract` (sibling artifact) for webhook schema.

3. Offline Verification Service (OVS):
 Responsibility: Manages the fallback QR/barcode token verification logic. It validates the cryptographic signature of offline tokens and publishes a OfflineTransactionVerified event to the internal event bus. It also handles the reconciliation of offline transactions with the online ledger.
 Boundary: OVS is a stateless service that validates tokens against a shared secret key (managed securely). It does not store transaction history.
 Dependency: Relies on the `Offline Cryptographic Token Verification Contract` (sibling artifact) for token structure.

### 5.2 Event-Driven Messaging Patterns

The platform uses an event-driven architecture to ensure scalability and resilience. All financial transactions are modeled as events, allowing for asynchronous processing and eventual consistency.

Event Bus:
 Technology: AWS EventBridge (or equivalent serverless event bus).
 Schema: All events must conform to the MealCreditEvent schema, which includes a version, type, source, id, time, and data field.

Key Events:

1. TransactionCompleted (Published by PGS):
 Trigger: Stripe webhook checkout.session.completed received and validated.
 Payload:

- **version**: 1.0
- **type**: TransactionCompleted
- **source**: pos_gateway_service
- **id**: evt_1234567890
- **time**: 2023-10-27T10:00:00Z
- **data**: {'stripe_payment_intent_id': 'pi_1234567890', 'beneficiary_id': 'uuid_v4_hashed', 'merchant_id': 'acct_1234567890', 'amount': 1500, 'currency': 'usd', 'transaction_hash': 'abc123def456'}

 Consumers: Financial Ledger Service, Notification Service.

2. OfflineTransactionVerified (Published by OVS):
 Trigger: Offline QR/barcode token successfully validated.
 Payload:

- **version**: 1.0
- **type**: OfflineTransactionVerified
- **source**: offline_verification_service
- **id**: evt_0987654321
- **time**: 2023-10-27T10:05:00Z
- **data**: {'token_id': 'tok_1234567890', 'beneficiary_id': 'uuid_v4_hashed', 'merchant_id': 'acct_1234567890', 'amount': 1500, 'signature': 'sig_1234567890'}

 Consumers: Financial Ledger Service, Reconciliation Service.

3. CardProvisioningRequested (Published by Internal API):
 Trigger: Internal API call to provision a new virtual card for a Beneficiary.
 Payload:

- **version**: 1.0
- **type**: CardProvisioningRequested
- **source**: internal_api_orchestration
- **id**: evt_1122334455
- **time**: 2023-10-27T10:10:00Z
- **data**: {'beneficiary_id': 'ben_1234567890', 'credit_pool_id': 'pool_1234567890'}

 Consumers: Stripe Proxy Service.

### 5.3 Latency & Throughput SLAs

To prevent restaurant queue stagnation (CON-4152F2C7C3, CON-5D64EBC654), the following SLAs are enforced:

 POS Clearance Latency: The end-to-end latency from card tap to ledger entry must average below 150ms (CON-06232374D9) and maintain a p99 latency below 250ms (CON-6D5E21557B, CON-7F03CF540E) under 10,000 concurrent connections.
 Throughput: The system must support a minimum of 500 transactions per second (TPS) across the 3 initial metropolitan footprints (SF, NYC, Chicago).
 Availability: 99.99% operational uptime (CON-BF1CD5707E, CON-FD21121DD5).

### 5.4 Error Handling & Resilience

 Idempotency: All event consumers must be idempotent to handle duplicate events from the event bus. The TransactionCompleted event must include a unique transaction_hash to prevent double-spending (CON-61EC670500, CON-72D9CECAF8).
 Dead Letter Queues (DLQ): All event consumers must have a DLQ configured. Events that fail processing after 3 retries must be moved to the DLQ for manual inspection.
 Circuit Breakers: The Stripe Proxy Service must implement circuit breakers to prevent cascading failures if Stripe's API is unavailable. The fallback mechanism for offline transactions (OVS) must be independent of the online Stripe API.

### 5.5 Knowledge Gaps & Assumptions

 KNOWLEDGE_GAP: The exact retention period for financial events in the event bus is not specified. ASSUMPTION: 7-year retention for financial records is required for SOC2 Type II compliance. Owner: Compliance Officer. Evidence needed: Specific jurisdictional requirements for financial data retention.
 KNOWLEDGE_GAP: The specific error codes and retry policies for Stripe API failures are not defined. ASSUMPTION: Standard Stripe API error codes will be used, with a 3-retry policy with exponential backoff. Owner: Engineering Lead. Evidence needed: Stripe API documentation for latest error codes.
 ASSUMPTION: The MealCreditEvent schema will be versioned, with v1.0 being the initial version. Owner: Platform Architect. Evidence needed: Agreement from all service owners on schema versioning strategy.
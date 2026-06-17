# Core Domain Model & Data Schema

## 1. DynamoDB Entity Schemas for High-Throughput Transactional State

This section defines the authoritative DynamoDB entity schemas for the MealCredit platform, specifically targeting the Recipient Discovery Session and Voucher Redemption state machines. These schemas are engineered to satisfy the absolute anonymization requirement (CON-9DEA275205) by ensuring all beneficiary analytics are mapped to high-entropy UUIDv4 keys, preventing any PII reconstruction. The design prioritizes sub-10ms read/write latency to support the 50,000 MAU target across three metropolitan footprints.

### 1.1 Core Design Principles & Anonymization Strategy

Absolute Anonymization (CON-9DEA275205): No PII (legal name, address, demographic data) is stored in DynamoDB. All beneficiary interactions are mapped to a recipient_token (UUIDv4). This token is generated client-side or by the Identity & Access Management capability (CAP-361A59708B) and is the sole identifier for the Recipient (ACT-DC00FA84DC). High-Throughput Optimization: Schemas are optimized for the Recipient Discovery & Redemption journey (JNY-76281D3F3C). Partition keys are designed to distribute load evenly across partitions to handle bursty traffic during peak donation cycles (CON-873877C003). State Machine Integrity: Voucher Redemption state is managed via conditional writes to prevent race conditions during concurrent redemption attempts.

### 1.3 Entity: VoucherRedemption

This entity manages the state of a single-use virtual card token. It ensures that a voucher can only be redeemed once, maintaining financial integrity.

| voucher_id | String | UUIDv4 for the single-use virtual card token. | Primary Partition Key. |
| created_at | String | ISO 8601 timestamp of voucher creation. | Primary Sort Key. |
| recipient_token | String | UUIDv4 of the beneficiary who owns the voucher. | Required for analytics mapping. |
| merchant_token | String | UUIDv4 of the Merchant Partner (ACT-A14D3CDC5D). | Required for settlement. |
| amount | Number | Value of the voucher in cents. | Integer. |
| currency | String | ISO 4217 currency code (e.g., "USD"). | Enum: USD. |
| status | String | Current redemption state. | Enum: ISSUED, REDEEMED, EXPIRED. |
| expiry_ts | Number | Unix timestamp for 72-hour auto-rollback (CON-AEB925BD12). | Used for TTL. |
| metadata | Map | JSON object for MCC restrictions, location locks. | Flexible schema. |

Access Patterns:
Issue Voucher: PutItem with conditional write `attribute_not_exists(voucher_id)` to prevent duplicate issuance. Redeem Voucher: UpdateItem with conditional write `status = ISSUED` and `attribute_exists(voucher_id)`. On success, update status to REDEEMED and record redeemed_at timestamp. Check Status: GetItem on voucher_id.

### 1.4 Global Secondary Indexes (GSIs)

To support efficient discovery and reconciliation without scanning the entire table:

GSI-1: RecipientByMetro
Partition Key: current_metro (String)
Sort Key: last_active_ts (Number)
Use Case: Query active recipients in a specific metro for targeted allocation or emergency credit distribution.

GSI-2: VoucherByMerchant
Partition Key: merchant_token (String)
Sort Key: created_at (String)
Use Case: Query vouchers issued to a specific merchant for settlement and reconciliation.

### 1.5 Data Retention & Expiry

- Recipient Sessions: TTL set to 24 hours. Expired sessions are automatically deleted by DynamoDB.
- Voucher Redemptions: TTL set to 72 hours from creation (CON-AEB925BD12). Unused emergency credits auto-roll back to the regional pool after this period. Expired vouchers are marked as EXPIRED and eventually deleted.

## 2. Core Domain Model & Data Schema: AWS Aurora Serverless v2 Append-Only Cryptographic Audit Ledger

This section defines the authoritative data schema for the financial transaction ledger, hosted on AWS Aurora Serverless v2. It enforces the append-only, cryptographic audit requirement (CON-199A4FEDC7) and ensures reconciliation robustness against partial failures (CON-6A9F6E50CE). This schema is the single source of truth for all financial flows, strictly decoupled from the high-throughput DynamoDB state used for Recipient Discovery (JNY-76281D3F3C).

### 2.2 Entity: FinancialEvent

This entity captures every financial transaction, including donations, voucher issuances, redemptions, and settlements.

| event_id | UUIDv4 | Unique identifier for the financial event. | Primary Partition Key. |
| created_at | ISO 8601 | Timestamp of event creation. | Primary Sort Key. |
| event_type | String | Type of financial event. | Enum: DONATION, VOUCHER_ISSUE, VOUCHER_REDEEM, SETTLEMENT, REVERSAL. |
| amount | Number | Transaction amount in cents. | Integer. |
| currency | String | ISO 4217 currency code. | Enum: USD. |
| contributor_token | String | UUIDv4 of the Contributor (ACT-2A20B038B1). | Required for donation events. |
| recipient_token | String | UUIDv4 of the Recipient (ACT-DC00FA84DC). | Required for voucher events. |
| merchant_token | String | UUIDv4 of the Merchant Partner (ACT-A14D3CDC5D). | Required for redemption/settlement events. |
| previous_event_hash | String | SHA-256 hash of the previous event's data. | Cryptographic chain integrity. |
| metadata | Map | JSON object for additional context (e.g., transaction ID, Stripe reference). | Flexible schema. |

Access Patterns:
Append Event: PutItem with event_id as partition key. No conditional writes required for append-only behavior. Query by Contributor: Query on GSI-1 (contributor_token, created_at). Query by Merchant: Query on GSI-2 (merchant_token, created_at).

## 3. API Contracts for Hybrid GraphQL/gRPC Architecture

This section defines the API contracts for the hybrid GraphQL/gRPC architecture, ensuring seamless data flow between the Client Application Layer and the Core Transaction & Ledger Service.

### 3.2 gRPC API (Core Transaction & Ledger Service)

The gRPC API serves the Core Transaction & Ledger Service, ensuring financial integrity and atomicity for transactional operations.

#### 3.2.1. RPC: ProcessRedemption

Input: `voucher_id: String!`, `merchant_token: String!`, `amount: Int!`
Output: RedemptionConfirmation object
Description: Processes a voucher redemption, updating the DynamoDB state and appending an event to the Aurora ledger.

#### 3.2.2. RPC: ReconcileLedger

Input: `start_date: String!`, `end_date: String!`
Output: LedgerReconciliation object
Description: Reconciles the DynamoDB state with the Aurora ledger to ensure consistency.

### 3.3 Integration Patterns

- Stripe Integration: The platform integrates with Stripe for payment processing and virtual card issuance. All raw credit card data is handled by Stripe Elements and SDK, ensuring zero raw credit card data touches application servers (CON-6EA64CF2A1).
- POS Integration: The platform integrates with POS systems via zero-footprint integration or edge dashboard, allowing merchants to ingest orders and validate virtual card tokens (JNY-01DD5AC877).

### 3.4 Security Posture

Absolute Anonymization: All beneficiary analytics are mapped to high-entropy UUIDv4 keys, preventing PII reconstruction (CON-9DEA275205). Cryptographic Audit Ledger: The append-only, cryptographic audit ledger in Aurora Postgres ensures tamper-evidence and compliance (CON-199A4FEDC7). Data Encryption: All data at rest and in transit is encrypted using AES-256 and TLS 1.3, respectively.

### 3.5 Knowledge Gaps

- KNOWLEDGE_GAP: Exact Stripe Issuing API version and error handling behavior for virtual card issuance and redemption. - Stripe API documentation and SDK version must be established before implementation.
- KNOWLEDGE_GAP: Specific POS integration middleware strategy (e.g., Stripe Square POS vs. custom gRPC adapters for Toast/Clover). - Decision required from Operator (ACT-FE96DD3975) based on merchant partner requirements.

### 3.6 Assumptions

- ASSUMPTION: SHA-256 is the binding cryptographic hash algorithm for ledger chaining. - Grounded in industry standard for tamper-evidence; binding confirmation required from security team.
- ASSUMPTION: DynamoDB TTL cleanup is sufficient for expired session and voucher data. - Grounded in DynamoDB native feature; operational monitoring required to verify cleanup latency.
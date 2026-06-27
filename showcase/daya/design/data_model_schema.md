# Data Model & Schema Design

## 1. Beneficiary Voucher State Schema (DynamoDB)

This section defines the DynamoDB schema for the Beneficiary Voucher State table, optimized for high-velocity reads and writes across the 3 initial metropolitan footprints (SF, NYC, Chicago). The schema enforces strict data isolation ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4)) by ensuring demographic status is never co-located with voucher redemption tokens in the same partition.

### 1.1 Table Configuration

Table Name: MealCredit-VoucherState

 Partition Key (PK): BeneficiaryID (String)
  Rationale: Co-locates all vouchers for a single beneficiary to enable fast balance lookups and real-time state updates during the Beneficiary Eligibility & Voucher Redemption journey ([JNY-E82B8A88D8](../project_glossary.md#jny-e82b8a88d8)).
 Sort Key (SK): VoucherID (String)
  Rationale: Uniquely identifies each voucher instance (UUIDv4) for the same beneficiary, supporting multiple concurrent vouchers.
 Global Secondary Index (GSI): GSI-MerchantVoucher
  GSI PK: MerchantID (String)
  GSI SK: VoucherID (String)
  Rationale: Enables the Merchant-Beneficiary Refund Flow ([JNY-E5F45D37C6](../project_glossary.md#jny-e5f45d37c6)) by allowing merchants to query vouchers they issued to a specific beneficiary without scanning the entire table.
 Provisioned Capacity: Auto-scaling enabled with a target utilization of 75% to handle peak event-driven load ([CON-121117F5A2](../project_glossary.md#con-121117f5a2)).

### 1.2 Item Schema

Each item in the MealCredit-VoucherState table represents a single voucher instance. The schema strictly excludes any PII or demographic data.

PK | String | BeneficiaryID (UUIDv4). Partition key.
SK | String | VoucherID (UUIDv4). Sort key.
MerchantID | String | Merchant ID. Used for GSI indexing.
Amount | Number | Decimal. Fractional credit amount. Must be > 0.
Status | String | Enum: ISSUED, REDEEMED, REFUNDED, EXPIRED.
ExpiryTimestamp | Number | Unix Epoch. Timestamp after which the voucher is invalid.
CreatedAt | Number | Unix Epoch. Timestamp of voucher creation.
UpdatedAt | Number | Unix Epoch. Timestamp of last status change.
RedemptionToken | String | Base64. Cryptographically signed token for POS validation.
Metadata | Map | JSON. Optional metadata (e.g., donorCampaignID, region).

### 1.3 Data Isolation Enforcement (CON-0A0288EED4)

To satisfy the strict data isolation requirement, demographic status and legal names are never stored in this table. Instead:

1. PII Segregation: Beneficiary demographic data is stored in a separate MealCredit-BeneficiaryProfile table (owned by the User State & Profile Data Model artifact). This table uses BeneficiaryID as its PK.
2. Access Control: IAM policies restrict access to the MealCredit-BeneficiaryProfile table to the NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) and Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) roles only. The Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) and Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) roles have no access to this table.
3. Anonymization: The RedemptionToken is generated using a deterministic HMAC-SHA256 hash of the VoucherID and a secret key, ensuring that the token itself does not leak any beneficiary information.

### 1.4 Index Strategy and Performance

 Balance Lookups: Queries against `PK = BeneficiaryID` return all vouchers for a beneficiary in a single read operation, enabling real-time balance calculations.
 Refund Queries: Queries against GSI-MerchantVoucher with `MerchantID = <merchant_id>` and `SK = <beneficiary_id>` (using a filter expression) allow merchants to quickly locate vouchers for refund processing.
 Cache Hit Ratio (CHR): To maintain a CHR above 92% ([CON-527BFA6796](../project_glossary.md#con-527bfa6796)), frequently accessed voucher states (e.g., ISSUED) are cached in Redis. The DynamoDB schema is designed to minimize read amplification, reducing the load on the cache.

### 1.5 Knowledge Gaps

 `KNOWLEDGE_GAP: Voucher Expiry Policy - The specific duration for voucher expiry (e.g., 14 days, 30 days) is not defined in the project truth. This impacts the ExpiryTimestamp field and the overall liquidity health (CON-D0F5814F21). Decision owner: Product Owner. Evidence needed: Business requirement for voucher validity period.`
 `KNOWLEDGE_GAP: GSI Write Capacity - The expected write throughput for the GSI-MerchantVoucher index is not defined. If a single merchant issues a high volume of vouchers, this could lead to hot partitions. Decision owner: Infrastructure Architect. Evidence needed: Expected voucher issuance rate per merchant.`

## 2. Immutable Financial Ledger Schema (Aurora PostgreSQL)

This section defines the Aurora PostgreSQL schema for the Transaction Ledger and Credit Pool tables. It enforces the append-only cryptographic log auditing requirement ([CON-1762EA5021](../project_glossary.md#con-1762ea5021)) and supports the Donation-to-Redemption Velocity (DRV) metric ([CON-D0F5814F21](../project_glossary.md#con-d0f5814f21)) through strict PII segregation and UUIDv4 mapping ([CON-23A501C051](../project_glossary.md#con-23a501c051)).

### 2.1. Cryptographic Audit Log Table (audit_log)

To satisfy CON-1762EA5021, all mutations to the financial ledger are recorded in an append-only table. This table acts as the source of truth for SOC2 Type II evidence ([CON-81FB01F06B](../project_glossary.md#con-81fb01f06b)) and prevents tampering via a cryptographic hash chain.

Table: audit_log

log_id | BIGSERIAL | `PRIMARY KEY` | Auto-incrementing logical sequence number for ordering.
ledger_id | UUID | `NOT NULL` | The UUID of the specific ledger entry being audited.
ledger_type | VARCHAR(50) | `NOT NULL` | Enum: TRANSACTION, CREDIT_ALLOCATION, REFUND, VOID.
action | VARCHAR(20) | `NOT NULL` | Enum: INSERT, UPDATE, DELETE.
previous_hash | CHAR(64) | `NOT NULL` | SHA-256 hex digest of the hash column from the previous row (ordered by log_id).
current_hash | CHAR(64) | `NOT NULL` | SHA-256 hex digest of `log_id | ledger_id | ledger_type | action | previous_hash`.
payload | JSONB | `NOT NULL` | The full state of the record at the time of the mutation.
created_at | TIMESTAMPTZ | `DEFAULT NOW()` | Timestamp of the mutation.
actor_id | UUID | `NOT NULL` | ID of the system or user triggering the audit event.

Integrity Constraint:
A CHECK constraint must be enforced on the current_hash column to ensure it matches the SHA-256 computation of its dependencies. This guarantees that any alteration to a previous row breaks the chain, immediately flagging a compliance violation.

### 2.2. Transaction Ledger Table (transaction_ledger)

This table records all financial movements. It is designed for high-throughput writes and supports the double-spending prevention logic ([CON-61EC670500](../project_glossary.md#con-61ec670500)) via strict state transitions.

Table: transaction_ledger

transaction_id | UUID | `PRIMARY KEY` | UUIDv4 identifier for the transaction.
donor_funding_id | UUID | `NOT NULL` | Foreign Key to donor_funding_events. Links the credit to its source.
beneficiary_anon_id | UUID | `NOT NULL` | UUIDv4 mapping for the beneficiary. No PII stored here.
merchant_id | UUID | `NOT NULL` | Foreign Key to merchant_profiles.
amount_cents | INTEGER | `NOT NULL` | Transaction amount in smallest currency unit.
currency | CHAR(3) | `DEFAULT 'USD'` | ISO 4217 currency code.
status | VARCHAR(20) | `NOT NULL` | Enum: PENDING, COMPLETED, VOIDED, REFUNDED.
created_at | TIMESTAMPTZ | `DEFAULT NOW()` | Timestamp of transaction creation.
updated_at | TIMESTAMPTZ | `DEFAULT NOW()` | Timestamp of last status change.
hash_chain_ref | BIGINT | `NOT NULL` | References log_id in audit_log for this transaction's initial creation.

Indexes:
 idx_txn_beneficiary_status: `(beneficiary_anon_id, status)` - Optimizes balance lookups for the Beneficiary-Platform Dispute Flow ([JNY-2B038C9362](../project_glossary.md#jny-2b038c9362)).
 idx_txn_merchant_date: `(merchant_id, created_at DESC)` - Optimizes Merchant Payout Error Handling Flow ([JNY-90B07623FB](../project_glossary.md#jny-90b07623fb)) reconciliation.

### 2.3. Credit Pool Table (credit_pools)

This table manages the liquidity of donor funds. It supports the Donation-to-Redemption Velocity (DRV) metric (CON-D0F5814F21) by tracking the flow of funds from Donor to Beneficiary.

Table: credit_pools

pool_id | UUID | `PRIMARY KEY` | UUIDv4 identifier for the credit pool.
donor_id | UUID | `NOT NULL` | Foreign Key to donor_profiles.
pool_type | VARCHAR(50) | `NOT NULL` | Enum: GLOBAL, REGIONAL, EVENT_SPECIFIC.
total_allocated_cents | BIGINT | `NOT NULL` | Total funds allocated to this pool.
total_redeemed_cents | BIGINT | `DEFAULT 0` | Total funds redeemed from this pool.
region_code | CHAR(2) | NULLABLE | ISO 3166-2 region code (e.g., 'CA', 'NY', 'IL'). NULL for global pools.
created_at | TIMESTAMPTZ | `DEFAULT NOW()` | Pool creation timestamp.
expires_at | TIMESTAMPTZ | NULLABLE | Expiration timestamp for time-bound pools.

DRV Calculation Logic:
The DRV metric is calculated by joining credit_pools with transaction_ledger on donor_funding_id. The velocity is measured as the time delta between credit_pools.created_at and the earliest transaction_ledger.created_at for a given donor_funding_id where `status = 'COMPLETED'`.

### 2.4. PII Segregation and Anonymization

To satisfy CON-0A0288EED4 and CON-23A501C051, the transaction_ledger and credit_pools tables do not contain any PII fields (names, emails, addresses).

 Beneficiary Identity: The beneficiary_anon_id in transaction_ledger is a UUIDv4 generated by the Identity & Access Management system ([CAP-IDENTITY-ACCESS-MANAGEMENT](../project_glossary.md#cap-identity-access-management)).
 Mapping: The mapping between beneficiary_anon_id and actual PII is stored in a separate, highly restricted beneficiary_pii table (owned by the User State & Profile Data Model artifact).
 Analytics: Analytics queries (e.g., DRV) operate solely on beneficiary_anon_id, ensuring that no de-anonymization attacks can link beneficiaries to donors through metadata analysis ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d)).

### 2.5. Sibling Dependencies

 User State & Profile Data Model: This artifact defers to that artifact for the beneficiary_pii table schema and the beneficiary_anon_id generation logic.
 Access Control & Multi-Tenant Isolation: This artifact defers to that artifact for the Row Level Security (RLS) policies that will restrict access to audit_log and transaction_ledger based on actor roles (Platform Administrator, NGO Operator, etc.).
 Financial Reconciliation & Payout Workers: This artifact defers to that artifact for the specific batch processing logic that will aggregate total_redeemed_cents in credit_pools.

### 2.6. Validation and Testing

 Integrity Test: A unit test must verify that inserting a row with an incorrect current_hash in audit_log fails the CHECK constraint.
 Anonymity Test: A query test must verify that joining transaction_ledger with credit_pools yields no PII fields, only beneficiary_anon_id.
 Performance Test: A load test must verify that the idx_txn_beneficiary_status index maintains sub-10ms lookup times for balance queries under 10,000 concurrent connections ([CON-6D5E21557B](../project_glossary.md#con-6d5e21557b)).

## 3. Redis Enterprise Cluster Schema for Geo-Indexing and Caching

This section defines the Redis Enterprise Cluster schema to support high-velocity Restaurant Search and Voucher Scanning surfaces. The design prioritizes sub-millisecond read latency for proximity searches and strict atomicity for double-spending prevention, ensuring a Cache Hit Ratio (CHR) above 92% (CON-527BFA6796) through intelligent TTL policies and write-through invalidation.

### 3.1. Restaurant Search Geo-Indexing (SUR-43E71C4E2B)

To support the Client Interface Layer's proximity search requirements, we utilize Redis Sorted Sets (ZSET) with geospatial coordinates as scores. This allows for efficient range queries (e.g., "find restaurants within 5km") without the overhead of full-text search for location-based filtering.

#### 3.1.1. Schema Definition

 Key Pattern: `geo:restaurant:{metro_region}:{restaurant_id}`
 Data Structure: ZSET
 Score: Geohash-encoded latitude/longitude (e.g., `ZADD geo:restaurant:SF:1001 37.7749 -122.4194`)
 Member: restaurant_id (UUIDv4)

#### 3.1.2. Query Contract

 Proximity Search: `ZRANGEBYSCORE geo:restaurant:{metro_region} {min_score} {max_score} BYSCORE` (where min/max are geohash ranges for the radius).
 Pagination: `LIMIT {offset} {count}` to support infinite scroll in the mobile app.

#### 3.1.3. Cache Invalidation Strategy

 Trigger: Merchant updates restaurant profile (location, status) via the Merchant Dashboard.
 Action: `ZREM geo:restaurant:{metro_region}:{restaurant_id}` followed by immediate ZADD with updated coordinates.
 TTL: No TTL on the ZSET itself; individual member updates are atomic. The ZSET is rebuilt periodically (e.g., nightly) from the DynamoDB Merchant table to ensure consistency.

### 3.2. Voucher Scanning & Double-Spending Prevention (CON-61EC670500)

To prevent double-spending of anonymous credits, the `voucher:token:state` key serves as the source of truth for real-time voucher status. This design ensures that a voucher can only be redeemed once, even under high concurrency (10,000+ concurrent connections).

#### 3.2.1. Schema Definition

 Key Pattern: `voucher:token:{voucher_id}`
 Data Structure: HASH
 Fields:
  status: ISSUED, REDEEMED, EXPIRED, VOIDED
  amount: Decimal string (e.g., "15.50")
  merchant_id: UUIDv4 of the issuing merchant
  beneficiary_hash: SHA-256 hash of the beneficiary ID (for audit trails without PII)
  created_at: ISO-8601 timestamp
  expires_at: ISO-8601 timestamp

#### 3.2.2. Atomic Redemption Flow

1. Check: `HGET voucher:token:{voucher_id} status` returns ISSUED.
2. Lock/Update: `HSETNX voucher:token:{voucher_id} status REDEEMED` (atomic check-and-set).
3. Fallback: If HSETNX returns 0, the voucher was already redeemed. Return `409 Conflict` to the POS terminal.

#### 3.2.3. TTL Policy

 TTL: Set to `expires_at + 1 hour`. This ensures that expired vouchers are automatically cleaned up from Redis, reducing memory pressure and preventing stale data from being queried.
 Eviction Policy: allkeys-lru to prioritize frequently accessed active vouchers over older, expired ones.

### 3.3. Cache Hit Ratio (CHR) Optimization (CON-527BFA6796)

To achieve a CHR above 92%, the following strategies are implemented:

1. Write-Through Caching: All voucher state changes are written to DynamoDB first, then immediately propagated to Redis. This ensures Redis is always up-to-date with the latest state.
2. Read-Through Caching: The application layer checks Redis first. If a miss occurs, it fetches from DynamoDB, updates Redis, and returns the data.
3. Pre-warming: During peak hours (e.g., lunch/dinner rushes), active vouchers for high-traffic merchants are pre-warmed in Redis to avoid cold-start latency.
4. Data Locality: Redis clusters are deployed in the same AWS region as the application servers to minimize network latency.

## 4. PII Segregation and Data Residency Architecture

This section defines the cryptographic and structural boundaries required to segregate 'Highly Sensitive' beneficiary data (CON-<timestamp>) from public-facing voucher tokens, while enforcing strict data residency for the SF, NYC, and Chicago metropolitan footprints ([CON-30EA97016B](../project_glossary.md#con-30ea97016b)). The design ensures that no single data store or service endpoint can correlate a beneficiary's legal identity with their financial redemption events, satisfying FTC guidelines on anonymity (CON-B3D71A437D) and PCI-DSS Level 1 compliance ([CON-66390130AA](../project_glossary.md#con-66390130aa)).

### 4.1. Cryptographic Data Isolation

 Beneficiary PII is stored in a dedicated, highly restricted database table (MealCredit-BeneficiaryProfile) that is physically and logically isolated from the voucher state and transaction ledger tables. Access to this table is restricted to the NGO Operator (ACT-09E028AEB0) and Platform Administrator (ACT-086A974D63) roles only.
 The RedemptionToken used for POS validation is generated using a deterministic HMAC-SHA256 hash of the VoucherID and a secret key. This ensures that the token itself does not leak any beneficiary information, even if intercepted.
 All analytics queries (e.g., DRV) operate solely on beneficiary_anon_id, ensuring that no de-anonymization attacks can link beneficiaries to donors through metadata analysis (CON-B3D71A437D).

### 4.2. Data Residency and Jurisdictional Compliance

To satisfy CON-30EA97016B, all user data must be stored within the geographic boundaries of the metropolitan regions where the user resides. This is critical for compliance with local data protection regulations and ensuring low-latency access for the 50,000 MAU target.

 Metro Footprint Mapping:
  `ASSUMPTION: SF Metro Footprint maps to AWS us-west-2 region. NYC Metro Footprint maps to AWS us-east-1 region. Chicago Metro Footprint maps to AWS us-east-2 region. This mapping is reversible pending confirmation from the Infrastructure Topology & Deployment Design artifact.`
  `ASSUMPTION: Cross-region replication is disabled for PII data to ensure strict data residency compliance. Replication is only enabled for non-sensitive, globally accessible data (e.g., merchant catalogs) where latency optimization is prioritized over strict residency.`

### 4.3. Follow-Up Questions

 Question: What are the exact data residency jurisdictional compliance rules for each metropolitan region?
  Why Critical: The data residency architecture depends on the specific legal requirements for each region.
  Answerable: false
  Blocking: true
  Source Role: refiner

## 5. API Contracts & Integration Boundaries

This section defines the synchronous and asynchronous contracts between the platform services and external systems (Stripe, POS Gateways) to ensure reliable data flow and error handling.

### 5.1. Synchronous POS Clearance Contract

The POS clearance contract defines the interface between the Merchant POS terminal and the MealCredit Redemption Engine. It must support high availability and low latency to prevent queue stagnation ([CON-4152F2C7C3](../project_glossary.md#con-4152f2c7c3)).

 Endpoint: `POST /api/v1/redemption/validate`
 Request Body:
  voucher_id: UUIDv4 (Required)
  merchant_id: UUIDv4 (Required)
  amount_cents: Integer (Required)
  timestamp: ISO-8601 (Required)
 Response Body:
  status: Enum: APPROVED, DECLINED, ERROR
  message: String (Human-readable reason for decline)
  transaction_id: UUIDv4 (If approved)

### 5.2. Asynchronous Payout Reconciliation

The payout reconciliation process is handled asynchronously via Stripe Connect webhooks. This ensures that payouts are not blocked by transient network issues or Stripe API latency.

 Event: `stripe.webhook.received`
 Payload:
  event_type: String (e.g., `payout.created`, `payout.failed`)
  payout_id: String (Stripe payout ID)
  amount_cents: Integer
  status: String (e.g., `pending`, `paid`, `failed`)

### 5.3. Error Handling & Retry Logic

 All external API calls must implement exponential backoff with jitter to handle transient failures.
 Failed payouts must be queued for manual review by the Platform Administrator (ACT-086A974D63) after 3 retry attempts.
 POS clearance errors must be logged with a unique correlation ID for traceability.

### 5.4. Knowledge Gaps

 `KNOWLEDGE_GAP: POS Gateway Integration Protocol - The specific protocol (e.g., REST, gRPC, GraphQL) for the POS gateway integration is not defined. This impacts the latency and payload structure of the clearance contract. Decision owner: Infrastructure Architect. Evidence needed: POS vendor API documentation.`
 `KNOWLEDGE_GAP: Stripe Webhook Signature Verification - The specific algorithm for verifying Stripe webhook signatures is not defined. This impacts the security of the payout reconciliation process. Decision owner: Security Engineer. Evidence needed: Stripe API documentation.`

### 6.2. SOC2 Type II Structural Planning

 All administrative ledger operations and infrastructure changes are logged to AWS CloudTrail for SOC2 Type II evidence ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2)).
 Access controls are reviewed and audited regularly.
 Incident response procedures are documented and tested.

### 6.3. FTC Anonymity Guidelines

 No PII is stored in the transaction ledger or voucher state tables.
 Analytics queries operate solely on anonymized identifiers.
 De-anonymization attacks are prevented through strict data isolation and access controls (CON-B3D71A437D).

## 7. Dependency Management & Versioning

This section defines the dependency management and versioning strategy for the platform's software components and external services.

### 7.1. Software Dependency Management

 All software dependencies are managed using a package manager (e.g., npm, pip, Maven).
 Dependency versions are locked to specific versions to ensure reproducibility.
 Regular dependency updates are performed to address security vulnerabilities.

### 7.2. External Service Versioning

 All external service APIs are versioned (e.g., /api/v1/).
 API versioning is communicated to consumers via headers or URL paths.
 Deprecated API versions are supported for a defined period before being retired.

### 7.3. Knowledge Gaps

 `KNOWLEDGE_GAP: Dependency Update Policy - The specific policy for dependency updates (e.g., automated, manual, quarterly) is not defined. This impacts the security and stability of the platform. Decision owner: Infrastructure Architect. Evidence needed: Platform stability requirements.`
 `KNOWLEDGE_GAP: API Deprecation Policy - The specific policy for API deprecation (e.g., notification period, sunset date) is not defined. This impacts the consumer experience and platform stability. Decision owner: Product Owner. Evidence needed: Consumer requirements.`

## 8. Disaster Recovery & Business Continuity

This section defines the disaster recovery and business continuity procedures to ensure the platform's resilience in the event of infrastructure failure.

### 8.1. Disaster Recovery Plan

 Regular backups of all data stores are performed.
 Backup data is stored in a separate geographic region.
 Disaster recovery procedures are tested regularly.

### 8.2. Business Continuity Plan

 Critical business processes are identified and documented.
 Alternative processes are defined for critical business processes.
 Business continuity procedures are tested regularly.

## 9. Monitoring & Observability

This section defines the monitoring and observability strategy for the platform to ensure operational visibility and proactive issue detection.

### 9.1. Metrics & Alerts

 Key performance indicators (KPIs) are defined and monitored.
 Alerts are configured for critical KPIs.
 Alert thresholds are reviewed and adjusted regularly.

### 9.2. Logging & Tracing

 All application logs are centralized and searchable.
 Distributed tracing is implemented for critical workflows.
 Log retention policies are defined and enforced.

## 10. Future Enhancements & Roadmap

This section outlines potential future enhancements and roadmap items for the platform.

### 10.1. Feature Enhancements

 Multi-currency support.
 Advanced analytics dashboard.
 Mobile wallet integration.

### 10.2. Technical Enhancements

 Microservices architecture migration.
 AI/ML-driven fraud detection.
 Enhanced offline capabilities.

## 11. Conclusion

This Data Model & Schema Design artifact provides a comprehensive blueprint for the Daya (MealCredit) platform. It addresses the core requirements for data isolation, compliance, scalability, and performance. The design is grounded in the project truth and adheres to the established asset registry and canonical labels. Unresolved decisions are explicitly flagged as knowledge gaps or assumptions, ensuring transparency and traceability.

### 4. Data Model & Schema Design

This section defines the structural contracts for the data persistence layer, ensuring strict data isolation, financial integrity, and low-latency access patterns required for the MealCredit platform.

#### 4.1. Cryptographic PII Segregation Strategy

To prevent de-anonymization attacks (CON-B3D71A437D) and ensure that demographic status is never exposed to the Merchant or POS systems, we implement a Cryptographic Hashing Layer that acts as the sole bridge between PII and transactional data.

##### 4.1.1. The PII Vault (Aurora PostgreSQL)

The 'Highly Sensitive' data is stored in a dedicated, isolated schema within Aurora PostgreSQL, accessible only by the NGO Operator (ACT-09E028AEB0) and the Platform Administrator (ACT-086A974D63). This table is physically separated from the voucher issuance logic.

Table: pii_vault.beneficiary_identity

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| beneficiary_uuid | UUID | PK, Default `gen_random_uuid()` | Internal system identifier for the beneficiary. |
| legal_name_hash | VARCHAR(64) | NOT NULL, Unique | SHA-256 hash of the beneficiary's legal name. Used for NGO verification only. |
| dob_hash | VARCHAR(64) | NOT NULL | SHA-256 hash of the date of birth. Used for age-restriction compliance. |
| ngo_id | UUID | FK, NOT NULL | References the NGO Operator (ACT-09E028AEB0) responsible for this beneficiary. |
| eligibility_status | VARCHAR(20) | NOT NULL | Enum: APPROVED, PENDING, REVOKED. |
| created_at | TIMESTAMPTZ | Default `NOW()` | Timestamp of initial registration. |
| updated_at | TIMESTAMPTZ | Default `NOW()` | Timestamp of last status change. |

Access Control:
- NGO Operator (ACT-09E028AEB0): Can read eligibility_status and legal_name_hash for their assigned beneficiaries. Cannot read raw PII.
- Platform Administrator (ACT-086A974D63): Can read all fields for audit and compliance purposes (CON-81FB01F06B).
- Financial Engine ([CAP-TRANSACTION-FINANCIAL-ENGINE](../project_glossary.md#cap-transaction-financial-engine)): Has NO access to this table. It only receives a beneficiary_uuid from the Identity & Access Management (CAP-IDENTITY-ACCESS-MANAGEMENT) service.

##### 4.1.2. The Voucher Token (DynamoDB)

Voucher tokens stored in DynamoDB contain zero PII. They are linked to the beneficiary only via the beneficiary_uuid, which is a random UUID generated during onboarding. This UUID is never derived from PII, preventing reverse-engineering.

Table: voucher_state

| Key Type | Name | Data Type | Description |
| :--- | :--- | :--- | :--- |
| PK | `BENEFICIARY#<beneficiary_uuid>` | String | Groups all vouchers for a single beneficiary. |
| SK | `VOUCHER#<voucher_uuid>` | String | Unique identifier for the specific voucher instance. |
| GSI1_PK | `MERCHANT#<merchant_uuid>` | String | Enables querying vouchers by merchant for reconciliation. |
| GSI1_SK | `BENEFICIARY#<beneficiary_uuid>` | String | Enables querying all vouchers for a beneficiary across merchants. |
| Attribute | `amount_cents` | Number | Fractional credit value. |
| Attribute | `status` | String | Current lifecycle state: ISSUED, REDEEMED, EXPIRED, REFUNDED. |
| Attribute | `expiry_timestamp` | Number | Unix timestamp for voucher expiration. |
| Attribute | `created_at` | Number | Unix timestamp of issuance. |

Data Isolation Enforcement:
- The beneficiary_uuid in DynamoDB is a blind token. It has no semantic meaning and cannot be correlated with legal_name_hash in PostgreSQL without the Identity & Access Management service, which is strictly gated.
- Merchant Partners (ACT-AF904DCFF9) only see the voucher_uuid and the amount_cents. They never see the beneficiary_uuid or any PII.

#### 4.2. Metro Footprint Mapping

Each metropolitan footprint (SF, NYC, Chicago) is mapped to a specific AWS Region to ensure data sovereignty and low-latency access.

ASSUMPTION: Metro Footprint Mapping
The specific AWS region-to-footprint mapping (e.g., SF to us-west-2, NYC to us-east-1, CHI to us-east-2) is an open infrastructure decision pending the Infrastructure Topology & Deployment Design artifact.
Cross-region replication for PII data is disabled to ensure strict residency. Financial ledger data (append-only) may be replicated for disaster recovery ([CON-10F4381094](../project_glossary.md#con-10f4381094)), but PII remains local.
DynamoDB tables are created per region. The API Orchestration Layer ([SUR-85E4A5B6E7](../project_glossary.md#sur-85e4a5b6e7)) routes requests to the correct region based on the beneficiary_uuid's geo-assignment.
Redis Enterprise Clusters are deployed in each region for geo-indexing ([SUR-43E71C4E2B](../project_glossary.md#sur-43e71c4e2b)) and caching. Cross-region Redis replication is disabled for PII.

#### 4.3. Anonymization for Analytics and DRV

To track Donation-to-Redemption Velocity (DRV) (CON-D0F5814F21) without linking PII, we use UUIDv4 Mapping (CON-23A501C051).

##### 4.3.1. The Anonymization Bridge

A separate, read-only Analytics Data Warehouse (e.g., Amazon Redshift) receives aggregated, anonymized data from the financial ledger. The mapping between beneficiary_uuid and donor_impact_receipt is handled via a UUIDv4 mapping table that is:
1. Cryptographically Hashed: The mapping is stored as a hash, preventing reverse lookup.
2. Time-Bound: The mapping is deleted after a fixed retention period (e.g., 14 days) to ensure no long-term correlation is possible.
3. Access-Restricted: Only the Platform Administrator (ACT-086A974D63) can access the mapping table for audit purposes.

Table: analytics.uuid_mapping

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| beneficiary_uuid | UUID | PK | The blind token from DynamoDB. |
| donor_impact_uuid | UUID | PK | The UUID associated with the donor's impact receipt. |
| created_at | TIMESTAMPTZ | Default `NOW()` | Timestamp of mapping creation. |
| expires_at | TIMESTAMPTZ | NOT NULL | Timestamp after which the mapping is deleted. |

Data Retention Policy:
- PII Data: Retained for the duration of the beneficiary's eligibility plus 7 years (for financial compliance).
- Voucher Tokens: Retained for 1 year after expiration.
- UUID Mapping: Deleted after 14 days.

### 5. Integration Patterns and API Contracts for Transaction & Financial Engine

This section defines the synchronous and asynchronous integration patterns between the three primary data stores (DynamoDB, Aurora PostgreSQL, Redis) to support the Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE) and Dispute Resolution & Chargeback Management ([CAP-DISPUTE-RESOLUTION-CHARGEBACK-MANAGEMENT](../project_glossary.md#cap-dispute-resolution-chargeback-management)). The design prioritizes the p99 latency requirement of 250ms (CON-6D5E21557B) for real-time POS clearance while ensuring eventual consistency for financial reconciliation ([JNY-35EBA169C6](../project_glossary.md#jny-35eba169c6)).

#### 5.1. Synchronous POS Clearance Contract (Real-Time)

The real-time clearance path is the critical latency-sensitive surface. It must validate voucher state, deduct credits, and confirm redemption within 250ms p99.

Integration Flow:
1. Merchant POS sends a RedemptionRequest to the API Orchestration Layer (SUR-85E4A5B6E7).
2. Orchestrator validates the request signature and extracts the VoucherID.
3. Orchestrator queries Redis Enterprise Cluster ([SUR-5B18C8719F](../project_glossary.md#sur-5b18c8719f)) for the voucher state. This is the primary read path to ensure CHR > 92% (CON-527BFA6796).
   - Hit: Redis returns the voucher state (Amount, Status, Expiry, BeneficiaryID).
   - Miss: Orchestrator falls back to DynamoDB ([SUR-FA61592CD4](../project_glossary.md#sur-fa61592cd4)) to read the BeneficiaryVoucherState item, updates the Redis cache, and proceeds.
4. Orchestrator performs a conditional write to DynamoDB to update the voucher status from ISSUED to REDEEMED (or PARTIALLY_REDEEMED). This write is strongly consistent to prevent double-spending (CON-61EC670500).
5. Orchestrator publishes a VoucherRedeemedEvent to the Event Bus for asynchronous processing.
6. Orchestrator returns a `200 OK` with the redemption confirmation to the Merchant POS.

API Contract: RedemptionRequest

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| VoucherID | String (UUIDv4) | Yes | The unique identifier of the voucher to be redeemed. |
| MerchantID | String (UUIDv4) | Yes | The ID of the merchant processing the redemption. |
| Amount | Decimal | Yes | The amount being redeemed. Must be <= Voucher.RemainingBalance. |
| Timestamp | ISO 8601 | Yes | The time of the request. |
| Signature | String | Yes | HMAC-SHA256 signature of the request payload, signed by the Merchant's private key. |

API Contract: RedemptionResponse

| Field | Type | Description |
| :--- | :--- | :--- |
| Status | Enum | APPROVED, DECLINED_INSUFFICIENT_FUNDS, DECLINED_EXPIRED, DECLINED_INVALID_VOUCHER. |
| TransactionID | String (UUIDv4) | Unique ID for the redemption transaction. |
| RemainingBalance | Decimal | The remaining balance on the voucher after redemption. |
| Message | String | Human-readable reason for decline if Status is DECLINED. |

Latency Budget:
- API Gateway: 10ms
- Orchestrator Logic: 20ms
- Redis Read: 5ms
- DynamoDB Conditional Write: 50ms
- Event Bus Publish: 10ms
- Total Target: < 100ms (leaving 150ms buffer for network jitter and edge cases to meet 250ms p99).

#### 5.2. Asynchronous Financial Reconciliation Stream

The reconciliation path handles the eventual consistency between the financial ledger and the voucher state. It is driven by the VoucherRedeemedEvent published in the synchronous path.

Integration Flow:
1. Event Bus delivers the VoucherRedeemedEvent to the Financial Reconciliation Service (CAP-TRANSACTION-FINANCIAL-ENGINE).
2. Financial Reconciliation Service writes an immutable record to the Aurora PostgreSQL Transaction_Ledger table. This record includes the TransactionID, VoucherID, MerchantID, Amount, Timestamp, and a cryptographic hash of the previous ledger entry (CON-1762EA5021).
3. Financial Reconciliation Service updates the Credit_Pool table in Aurora PostgreSQL to reflect the reduction in available donor funds.
4. Financial Reconciliation Service publishes a ReconciliationCompleteEvent to the Analytics Stream for DRV calculation (CON-D0F5814F21) and donor impact reporting (CON-23A501C051).

Data Model: Transaction_Ledger (Aurora PostgreSQL)

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| TransactionID | UUID | PK | Unique transaction identifier. |
| VoucherID | UUID | FK | Reference to the voucher. |
| MerchantID | UUID | FK | Reference to the merchant. |
| BeneficiaryID | UUID | FK | Reference to the beneficiary (hashed/anonymized for privacy). |
| Amount | Decimal | | Amount redeemed. |
| TransactionType | Enum | | REDEMPTION, REFUND, VOID. |
| Timestamp | Timestamp | | When the transaction occurred. |
| PreviousLedgerHash | String | | SHA-256 hash of the previous row's hash, forming a chain. |
| CurrentLedgerHash | String | | SHA-256 hash of the current row's content, used for integrity verification. |

#### 5.3. Dispute Resolution & Chargeback Management

The dispute resolution flow (JNY-2B038C9362) relies on the immutable ledger and the voucher state in DynamoDB.

Integration Flow:
1. Dispute Adjudicator ([ACT-7BA340FF76](../project_glossary.md#act-7ba340ff76)) initiates a dispute via the Admin Dashboard (SUR-43E71C4E2B).
2. Orchestrator retrieves the Transaction_Ledger records for the disputed TransactionID from Aurora PostgreSQL.
3. Orchestrator retrieves the current VoucherState from DynamoDB to verify the voucher's status and balance.
4. Orchestrator validates the dispute against the Dispute_Policy table (defined in Security Architecture & Access Control artifact).
5. If the dispute is approved, Orchestrator triggers a RefundEvent:
   - Refund Service writes a REFUND record to the Transaction_Ledger in Aurora PostgreSQL.
   - Refund Service updates the VoucherState in DynamoDB to restore the redeemed amount to the RemainingBalance.
   - Refund Service updates the Credit_Pool in Aurora PostgreSQL to restore the donor funds.

API Contract: DisputeInitiationRequest

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| TransactionID | String (UUIDv4) | Yes | The ID of the transaction being disputed. |
| DisputeReason | Enum | Yes | FRAUD, MERCHANT_ERROR, BENEFICIARY_ERROR, OTHER. |
| Evidence | Object | No | Additional evidence provided by the Dispute Adjudicator. |

API Contract: DisputeResolutionResponse

| Field | Type | Description |
| :--- | :--- | :--- |
| DisputeID | String (UUIDv4) | Unique ID for the dispute. |
| Status | Enum | OPEN, RESOLVED_APPROVED, RESOLVED_DENIED. |
| ResolutionDetails | String | Explanation of the resolution. |
| RefundAmount | Decimal | Amount refunded, if applicable. |

#### 5.4. Data Consistency and Conflict Resolution

- Strong Consistency for Vouchers: DynamoDB reads and writes for voucher state are strongly consistent to prevent double-spending. This is non-negotiable for financial integrity.
- Eventual Consistency for Analytics: DRV and donor impact metrics are calculated from the ReconciliationCompleteEvent stream, allowing for eventual consistency. This decouples the real-time POS path from the analytics path.
- Conflict Resolution: In the event of a network partition, the DynamoDB conditional write ensures that only one redemption is processed per voucher balance. The Aurora PostgreSQL ledger provides the single source of truth for financial reconciliation, which can be used to reconcile any discrepancies between DynamoDB and the ledger.

#### 5.5. Knowledge Gaps and Assumptions

KNOWLEDGE_GAP: Dispute Adjudicator Access Control
The specific RBAC permissions for the Dispute Adjudicator (ACT-7BA340FF76) to initiate and resolve disputes are not defined in this artifact. This is covered in the Security Architecture & Access Control artifact.

KNOWLEDGE_GAP: Stripe Webhook Latency
The exact latency contribution of Stripe Webhook processing to the overall POS clearance time is not quantified. This must be measured and optimized to ensure the 150ms target ([CON-06232374D9](../project_glossary.md#con-06232374d9)) is met.

ASSUMPTION: Event Bus Technology
The specific event bus technology (e.g., AWS EventBridge, Kafka) is not specified. The design assumes a standard event bus with at-least-once delivery semantics. The implementation details are deferred to the Integration Adapters & External Contracts artifact.

ASSUMPTION: Redis Cache Invalidation
The cache invalidation strategy for DynamoDB updates is assumed to be a write-through cache with a TTL of 5 minutes. This ensures that stale data is eventually cleared without requiring complex invalidation logic.

#### 5.6. Alignment with Project Context

- Scalability: The separation of synchronous (DynamoDB/Redis) and asynchronous (Aurora PostgreSQL) paths allows the system to scale independently. The synchronous path handles high-velocity POS transactions, while the asynchronous path handles heavy financial reconciliation.
- Compliance: The immutable ledger in Aurora PostgreSQL supports PCI-DSS Level 1 and SOC2 Type II compliance by providing a complete, auditable trail of all financial transactions. The PII segregation is maintained by storing beneficiary PII in a separate table (defined in PII Segregation & Anonymization Strategy artifact) and only referencing hashed IDs in the ledger.
- Anonymity: The BeneficiaryID in the Transaction_Ledger is hashed/anonymized, ensuring that no PII is linked to donor impact receipts (CON-23A501C051). The correlation is done via UUIDv4 mapping in the analytics stream.
- Latency: The 250ms p99 target is achieved by minimizing the number of data store hops in the synchronous path (Redis -> DynamoDB) and offloading heavy processing to the asynchronous path.

This design provides a clear, implementable contract for the Transaction & Financial Engine and Dispute Resolution capabilities, ensuring alignment with the project's scalability, compliance, and latency requirements.

---

## VP decision

**Decision:** Approved

---

## VP feedback

- Section 4.2 Metro Footprint Mapping: Convert the specific AWS region-to-footprint mappings (e.g., SF to us-west-2) to ASSUMPTION: tags, as the requirement does not specify the infrastructure topology.
- Section 4.3.1 The Anonymization Bridge: Convert the 14-day retention period for the UUID mapping table to KNOWLEDGE_GAP: - the specific retention window is not defined in the project truth.
- Section 4.1.1 The PII Vault: Convert the 7-year PII retention period to KNOWLEDGE_GAP: - the specific retention window is not defined in the project truth.
- Section 5.5 Knowledge Gaps and Assumptions: Convert the 5-minute Redis cache invalidation TTL to ASSUMPTION: - the specific cache policy is not defined in the project truth.

# Geo-Indexing & Merchant Data Model

### 4.1 Core Data Structures

The system utilizes Redis GEOHASH for efficient spatial indexing of Merchant Partners ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) locations. This choice is driven by the need to maintain a Cache Hit Ratio (CHR) above 92% for restaurant search queries ([CON-527BFA6796](../project_glossary.md#con-527bfa6796)) and to support the p99 latency target of below 250ms for voucher creation and scanning callbacks ([CON-6D5E21557B](../project_glossary.md#con-6d5e21557b)).

Primary Index Set: `geo:merchants:{region}:{city}`
Type: GEOADD
Purpose: Stores the geographic coordinates (longitude, latitude) of all active Merchant Partners within a specific metropolitan footprint (SF, NYC, CHI).
Member ID: merchant_id (UUIDv4)
Coordinates: longitude, latitude
Rationale: Isolating data by region and city supports data residency and jurisdictional compliance requirements ([CON-30EA97016B](../project_glossary.md#con-30ea97016b)) and simplifies disaster recovery procedures ([CON-10F4381094](../project_glossary.md#con-10f4381094)).

Proximity Search Query: GEORADIUSBYMEMBER / GEORADIUS
Purpose: Retrieves a list of merchant_ids within a specified radius (e.g., 5km) of a Beneficiary's ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) current location.
Performance Constraint: Must complete within the overall p99 latency target of 250ms to ensure the end-to-end voucher creation and scanning callback latency is met.

### 4.2 Key Naming Conventions

Strict key naming conventions are enforced to ensure clarity, prevent collisions, and support operational monitoring.

Format: `geo:merchants:{region}:{city}`
Examples:
`geo:merchants:US:SF`
`geo:merchants:US:NYC`
`geo:merchants:US:CHI`
Region Code: ISO 3166-1 alpha-2 (e.g., US).
City Code: ISO 3166-2 state code + city abbreviation (e.g., `CA:SF`, `NY:NYC`, `IL:CHI`).

### 4.3 TTL Policies

To balance data freshness with memory efficiency and write amplification, the following TTL policies are applied:

Merchant Location Data: 24 hours.
Rationale: Merchant locations are relatively static. A 24-hour TTL ensures data is refreshed regularly without requiring real-time updates for every minor change. Updates are triggered by POS integration events ([JNY-356F465DB3](../project_glossary.md#jny-356f465db3)).
Refresh Mechanism: On every successful POS check-in or location update event, the TTL is reset to 24 hours.

Search Cache (Optional): 5 minutes.
Rationale: Caches the results of frequent proximity searches to further reduce Redis load and improve p99 latency. This is an optimization layer on top of the primary GEOHASH index.

## 1. Merchant Data Model Schema

This section defines the canonical Merchant data model for the Data Persistence Layer ([SUR-FA61592CD4](../project_glossary.md#sur-fa61592cd4)). The schema is designed to support the Merchant Onboarding & POS Integration journey (JNY-356F465DB3) and the Merchant Payout Error Handling Flow ([JNY-90B07623FB](../project_glossary.md#jny-90b07623fb)), while strictly adhering to PCI-DSS Level 1 compliance ([CON-66390130AA](../project_glossary.md#con-66390130aa)) and data isolation requirements ([CON-92F07E31B0](../project_glossary.md#con-92f07e31b0)).

### 1.1 Core Merchant Entity

The Merchant entity serves as the primary record for all restaurant partners. It is immutable in its core identity fields but mutable in its operational status and configuration.

merchant_id | UUID (v4) | Primary Key, Not Null | Internal unique identifier for the merchant.
stripe_account_id | String | Unique, Not Null | External Stripe Connected Account ID. Used for payout routing and liability management ([CON-5BFA25E8F9](../project_glossary.md#con-5bfa25e8f9)).
legal_name | String | Not Null, Encrypted | The legal business name. Classified as 'Highly Sensitive' (CON-<timestamp>). Stored in a segregated, encrypted schema accessible only to Platform Administrators ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) and authorized NGO Operators ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)).
display_name | String | Not Null | The public-facing name shown to Beneficiaries (ACT-ADA6716160) in the app.
status | Enum | Not Null | Current operational state: PENDING_VERIFICATION, ACTIVE, SUSPENDED, DECOMMISSIONED.
onboarding_date | Timestamp | Not Null | Date and time of initial platform registration.
last_updated | Timestamp | Not Null | Timestamp of the last modification to the record.

To support proximity-based search and maintain the 92% Cache Hit Ratio (CHR) target (CON-527BFA6796), location data is stored in two forms: a structured relational record and a Redis GEOHASH entry.

address_line_1 | String | Not Null | Street address.
city | String | Not Null | City name (e.g., SF, NYC, Chicago). Used for jurisdictional data residency (CON-30EA97016B).
state | String | Not Null | State/Province code.
postal_code | String | Not Null | ZIP/Postal code.
latitude | Decimal(9,6) | Not Null | Geographic latitude for Redis GEOHASH indexing.
longitude | Decimal(9,6) | Not Null | Geographic longitude for Redis GEOHASH indexing.
geo_hash_key | String | Unique | The Redis key for this merchant's location (e.g., `geo:merchant:{city}:{merchant_id}`).

Redis Integration Note: The latitude and longitude fields are synchronized to Redis via an event-driven pipeline. The Redis key format is `geo:merchant:{city}:{merchant_id}` to ensure data isolation by metro footprint. TTL is set to 24 hours, refreshed on every POS update.

### 1.3 Payout Configuration

Payout details are stored securely, referencing external financial instruments rather than raw banking data to maintain PCI-DSS Level 1 compliance (CON-66390130AA).

payout_method | Enum | Not Null | Type of payout: STRIPE_CONNECT, BANK_TRANSFER.
stripe_payout_id | String | Nullable | Reference to the Stripe External Account ID.
routing_token | String | Encrypted, Nullable | Encrypted token for bank routing (if not using Stripe Connect).
account_token | String | Encrypted, Nullable | Encrypted token for bank account number.
payout_schedule | Enum | Not Null | Frequency of payouts: DAILY, WEEKLY, MONTHLY.
payout_threshold | Decimal | Default 100.00 | Minimum balance required before a payout is triggered.

### 1.5 Assumptions

- `ASSUMPTION: Stripe Connect Integration` - The platform will use Stripe Connect for all merchant payouts, eliminating the need to store raw bank details. This assumption is based on the requirement for PCI-DSS Level 1 compliance (CON-66390130AA) and simplifies KYC management (CON-5BFA25E8F9). Evidence needed: Stripe API documentation for Connect onboarding flows.
- `ASSUMPTION: Redis GEOHASH TTL` - A 24-hour TTL for Redis GEOHASH entries is assumed sufficient for merchant location freshness. Evidence needed: Merchant update frequency data from the POS integration team.

## 2. Restaurant Search API Contract

This section defines the technical contract for the restaurant search endpoint, enabling the Client Interface Layer ([SUR-43E71C4E2B](../project_glossary.md#sur-43e71c4e2b)) to perform proximity-based queries against the Redis GEOHASH index. The contract ensures strict adherence to the p99 latency target of 250ms (CON-6D5E21557B) and supports the multi-modal interaction paths required for Beneficiary (ACT-ADA6716160) redemption.

### 2.1 Endpoint Specification

HTTP Method: GET
Path: `/v1/merchants/search`
Description: Retrieves a list of active Merchant Partners (ACT-AF904DCFF9) within a specified geographic radius, optimized for low-latency retrieval from the Redis GEOHASH index.
Authentication: Requires a valid JWT bearer token associated with a Beneficiary (ACT-ADA6716160) or Platform Administrator (ACT-086A974D63) session.

### 2.2 Request Parameters

The API accepts query parameters to define the search scope. All parameters are mandatory to ensure deterministic index lookups.

lat | float | Yes | Latitude of the search origin point. | Range: -90.0 to 90.0
lon | float | Yes | Longitude of the search origin point. | Range: -180.0 to 180.0
radius | int | Yes | Search radius in meters. | Max: 50,000 meters (50km)
limit | int | No | Maximum number of results to return. | Default: 20; Max: 100
sort_by | string | No | Sorting criteria for results. | Values: distance, rating

### 2.3 Response Payload Structure

The response returns a JSON object containing a list of merchant profiles. To maintain anonymity and reduce payload size, PII is excluded from this endpoint. The structure aligns with the canonical Merchant data model defined in the Data Persistence Layer (SUR-FA61592CD4).

{
 "status": "success",
 "data": {
 "merchants": [
 {
 "merchant_id": "STR-8821A9C4",
 "display_name": "Example Restaurant",
 "distance_meters": 1200,
 "rating": 4.8,
 "is_active": true,
 "accepts_credits": true
 }
 ],
 "total_count": 1,
 "search_origin": {
 "lat": 37.7749,
 "lon": -122.4194
 }
 }
}

### 2.4 Error Codes

The API returns standard HTTP status codes and specific error codes to facilitate client-side handling of edge cases, such as invalid coordinates or service unavailability.

200 | SUCCESS | Search completed successfully. | Render merchant list.
400 | INVALID_COORDINATES | Latitude or longitude out of range. | Prompt user to enable location services.
400 | RADIUS_EXCEEDED | Requested radius exceeds 50km limit. | Reduce search radius.
404 | NO_MERCHANTS_FOUND | No active merchants within the specified radius. | Display "No nearby partners" message.
500 | SERVICE_UNAVAILABLE | Redis GEOHASH index is unreachable. | Retry with exponential backoff.
503 | RATE_LIMIT_EXCEEDED | Client has exceeded API rate limits. | Wait for retry-after header.

### 2.5 Performance & Caching Strategy

To achieve the 92% Cache Hit Ratio (CHR) target (CON-527BFA6796), the following caching strategy is enforced:

1. Client-Side Caching: Expo mobile clients (ACT-ADA6716160) must cache search results for a minimum of 5 minutes, keyed by lat, lon, and radius.
2. Edge Caching: Next.js Edge runtimes (SUR-43E71C4E2B) will cache responses for 1 minute using Vercel Edge Cache, leveraging the surrogate-key header.
3. Redis TTL: The Redis GEOHASH index entries for merchant locations will have a TTL of 24 hours, refreshed on every POS update to ensure data freshness while minimizing write amplification.

### 2.6 Dependencies

Redis GEOHASH Index: This endpoint relies on the Redis GEOHASH index for O(log(N)) lookup complexity.
Merchant Data Model: The response payload structure is derived from the canonical Merchant data model defined in the Data Persistence Layer (SUR-FA61592CD4).
Client Interface Layer: This contract is consumed by the Expo mobile client and Next.js dashboard (SUR-43E71C4E2B).

### 2.9 Risk Mitigation

Risk: Redis memory exhaustion due to high cardinality of merchant locations.
Mitigation: Implement strict TTLs and use Redis Cluster to shard data across multiple nodes based on geographic region.
Risk: Latency spikes during peak redemption events.
Mitigation: Use asynchronous updates for non-critical merchant metadata, keeping the GEOHASH index lightweight. Implement circuit breakers to fall back to a cached, slightly stale index if Redis latency exceeds 250ms.

### 2.10 Integration Notes

Stripe Issuing Proxy Contract: This artifact's [concern] defers to the Stripe Issuing Proxy Contract for [specific aspect]; see that artifact for the full treatment.
GraphQL Schema & Type Definitions: This artifact's [concern] defers to the GraphQL Schema & Type Definitions for [specific aspect]; see that artifact for the full treatment.
gRPC Service Contracts & Definitions: This artifact's [concern] defers to the gRPC Service Contracts & Definitions for [specific aspect]; see that artifact for the full treatment.
Financial Ledger Data Model: This artifact's [concern] defers to the Financial Ledger Data Model for [specific aspect]; see that artifact for the full treatment.
User State & Profile Data Model: This artifact's [concern] defers to the User State & Profile Data Model for [specific aspect]; see that artifact for the full treatment.
Access Control & Multi-Tenant Isolation: This artifact's [concern] defers to the Access Control & Multi-Tenant Isolation for [specific aspect]; see that artifact for the full treatment.
PII Segregation & Anonymization Strategy: This artifact's [concern] defers to the PII Segregation & Anonymization Strategy for [specific aspect]; see that artifact for the full treatment.
Financial Reconciliation & Payout Workers: This artifact's [concern] defers to the Financial Reconciliation & Payout Workers for [specific aspect]; see that artifact for the full treatment.
Merchant Payout Failure & Error Handling: This artifact's [concern] defers to the Merchant Payout Failure & Error Handling for [specific aspect]; see that artifact for the full treatment.
Distributed Tracing & Log Aggregation: This artifact's [concern] defers to the Distributed Tracing & Log Aggregation for [specific aspect]; see that artifact for the full treatment.
Metrics Collection & Alerting Design: This artifact's [concern] defers to the Metrics Collection & Alerting Design for [specific aspect]; see that artifact for the full treatment.
AWS Multi-AZ Deployment Topology: This artifact's [concern] defers to the AWS Multi-AZ Deployment Topology for [specific aspect]; see that artifact for the full treatment.
Data Residency & Jurisdictional Compliance: This artifact's [concern] defers to the Data Residency & Jurisdictional Compliance for [specific aspect]; see that artifact for the full treatment.
Expo Mobile Client Architecture: This artifact's [concern] defers to the Expo Mobile Client Architecture for [specific aspect]; see that artifact for the full treatment.
Next.js Dashboard Architecture: This artifact's [concern] defers to the Next.js Dashboard Architecture for [specific aspect]; see that artifact for the full treatment.

---

## 3. Integration Patterns: Redis Geo-Indexing and Transaction & Financial Engine

This section defines the integration patterns between the Redis geo-indexing layer and the Transaction & Financial Engine ([CAP-TRANSACTION-FINANCIAL-ENGINE](../project_glossary.md#cap-transaction-financial-engine)) to support the anonymous credit distribution and redemption lifecycle. The primary goal is to ensure that when a Beneficiary (ACT-ADA6716160) initiates a redemption, the system can rapidly identify eligible Merchant Partners (ACT-AF904DCFF9) and securely authorize the corresponding financial transaction without exposing Personally Identifiable Information (PII) or compromising the anonymity guarantees required by the platform.

The Transaction & Financial Engine must manage credit pools on a per-metro footprint basis (SF, NYC, Chicago) to align with data residency requirements (CON-30EA97016B) and to enable localized credit distribution. The Redis geo-indexing layer will serve as the primary lookup mechanism for identifying merchants within a specific geographic radius, but the financial engine must enforce credit pool boundaries.

Geo-Partitioned Credit Pools: Each metro footprint will have a dedicated logical credit pool within the Transaction & Financial Engine. When a Beneficiary searches for nearby merchants, the Redis GEOHASH query will return a list of merchant IDs. The Transaction & Financial Engine will then validate that these merchants are associated with the correct regional credit pool.
Utilization Rate Monitoring: The system must monitor the Credit Pool Utilization Rate, triggering automated alerts when thresholds exceed 85% ([CON-2059B17FB2](../project_glossary.md#con-2059b17fb2)). This monitoring will be integrated into the Redis geo-indexing layer by maintaining a counter for active credits distributed per metro footprint, which is updated in real-time as merchants are identified and credits are allocated.

### 4.1 Architectural Surface Mapping

The geo-indexing and merchant data surfaces are mapped to the following architectural layers:

- **Client Interface Layer (SUR-43E71C4E2B)**: The Expo mobile client consumes the geo-indexed merchant list for proximity-based search.
- **API Orchestration Layer ([SUR-85E4A5B6E7](../project_glossary.md#sur-85e4a5b6e7))**: The GraphQL API acts as the primary consumer of the Redis geo-index for search queries and the Transaction & Financial Engine for credit validation.
- **Data Persistence Layer (SUR-FA61592CD4)**: Aurora PostgreSQL serves as the system of record for merchant KYC, payout details, and static attributes.
- **Payment Processing Surface ([SUR-5B18C8719F](../project_glossary.md#sur-5b18c8719f))**: The Transaction & Financial Engine interacts with the geo-index to validate merchant location during POS clearing.

### 4.2 Scope Boundaries

- **In-Scope**: Redis Geo-Index schema, Merchant Data Model (PostgreSQL), Data Residency & Jurisdictional Compliance, Encryption Standards, Access Control & Data Isolation, Integration Flows (Search, Clearing, Error Handling).
- **Out-of-Scope**: Detailed UI/UX for the Beneficiary search interface (Product phase), Merchant POS hardware integration specifics (Merchant Module), Fraud Detection ML model training (Future phase).

### 4.3 Canonical Actor & Capability Bindings

- **ACT-ADA6716160 (Beneficiary)**: Primary consumer of the geo-indexed merchant list.
- **ACT-AF904DCFF9 (Merchant)**: Subject of the merchant data model; location and eligibility are validated against this data.
- **ACT-086A974D63 (Platform Administrator)**: Owner of merchant KYC approval and fraud investigation workflows.
- **ACT-09E028AEB0 (NGO Operator)**: Owner of beneficiary eligibility and offboarding; has restricted access to sensitive merchant data for dispute resolution.
- **[CAP-MARKETPLACE-MATCHMAKING](../project_glossary.md#cap-marketplace-matchmaking)**: The capability that drives the proximity-based search logic.
- **[CAP-MERCHANT-NGO-OPERATIONS](../project_glossary.md#cap-merchant-ngo-operations)**: The capability governing merchant onboarding and NGO association.

### 4.4 Latency & Performance Targets

The geo-indexing layer must support high-throughput, low-latency queries to prevent queue stagnation at the POS.

- **Search Latency**: The Redis GEOHASH query must complete within the p99 latency target of 250ms (CON-6D5E21557B).
- **Clearing Latency**: The Transaction & Financial Engine must validate merchant location and deduct credits within the p99 latency target of 250ms (CON-6D5E21557B).
- **Cache Hit Ratio (CHR)**: The Redis Enterprise Cluster must maintain a CHR above 92% for restaurant search queries (CON-527BFA6796).

### 4.5 Data Residency & Jurisdictional Compliance

To satisfy CON-30EA97016B (Data residency and jurisdictional compliance for user data across multiple metropolitan regions), the geo-indexing and merchant data must be strictly partitioned by metropolitan footprint (SF, NYC, Chicago). This ensures that beneficiary and merchant data never cross jurisdictional boundaries in transit or at rest.

| Data Surface | Isolation Mechanism | Scope | Grounded Target |
| :--- | :--- | :--- | :--- |
| Redis Geo-Index | Logical Sharding by Region: Redis keys are prefixed with the metro ID (e.g., `geo:merchant:sf:`, `geo:merchant:nyc:`). Access control lists (ACLs) restrict cross-region key access. | Per-Metro Footprint | CON-30EA97016B |
| PostgreSQL Merchant Data | Row-Level Security (RLS): RLS policies enforce that queries for merchant data are scoped to the requesting user's or NGO's jurisdiction. | Per-Metro Footprint | CON-30EA97016B |
| PII & Demographic Data | Cryptographic Segregation: Beneficiary demographic status and legal names are stored in a separate, highly restricted schema/table, accessible only to authorized Platform Administrators (ACT-086A974D63) and NGO Operators (ACT-09E028AEB0). | Global (but isolated) | CON-92F07E31B0 |

**Assumption**: AWS RDS and ElastiCache instances are deployed in separate Availability Zones within each metropolitan region (SF, NYC, Chicago) to ensure low-latency access and strict data locality. Evidence needed: Final AWS Multi-AZ Deployment Topology (sibling artifact) to confirm regional endpoint configurations.

### 4.6 PostgreSQL Merchant Schema

The Merchant Data Model in Aurora PostgreSQL serves as the system of record for merchant identity, KYC status, and payout details. All sensitive data is encrypted at rest.

- **merchant_id (UUID)**: Primary key, immutable.
- **metro_region (Enum)**: `SF`, `NYC`, `CHI`. Used for RLS policies and geo-sharding.
- **business_name (String)**: Publicly visible to Beneficiaries.
- **cuisine_type (Array<String>)**: Used for search filtering.
- **kyc_status (Enum)**: `PENDING`, `APPROVED`, `REJECTED`, `SUSPENDED`. Controlled by Platform Administrators (ACT-086A974D63).
- **payout_details (JSONB)**: Encrypted at the application level before storage. Contains Stripe Connected Account IDs.
- **geo_coordinates (Point)**: Lat/Long pair used for initial indexing into Redis.
- **created_at / updated_at (Timestamp)**: Audit fields.

The Redis Geo-Index provides the high-speed, proximity-based search capability. It is a logical mirror of the PostgreSQL merchant data, optimized for spatial queries.

- **Key Pattern**: `geo:merchant:{metro_region}:{merchant_id}`
- **Data Structure**: `GEOADD` command using `geo:merchant:{metro_region}` as the sorted set key.
- **Members**: `merchant_id` (string), `longitude` (double), `latitude` (double).
- **TTL**: No TTL on active merchants. Expired entries are cleaned up via a scheduled Lambda function triggered by PostgreSQL updates.

### 5.1 Merchant Eligibility and Credit Authorization Flow

The integration between the Redis geo-indexing layer and the Transaction & Financial Engine follows a strict sequence to ensure that only eligible merchants can accept credits and that sufficient funds are available in the donor's pool.

1. **Beneficiary Search Request**: The Beneficiary's mobile client (Expo v51 / React Native) sends a proximity-based search request to the API Orchestration Layer (SUR-85E4A5B6E7).
2. **Redis Geo-Index Lookup**: The API layer queries the Redis GEOHASH index using the Beneficiary's location to retrieve a list of nearby Merchant IDs. This query must complete within the p99 latency target of 250ms (CON-6D5E21557B).
3. **Merchant Eligibility Check**: The API layer forwards the list of Merchant IDs to the Transaction & Financial Engine. The engine validates each merchant's status (e.g., active, KYC-compliant) and checks their association with the correct regional credit pool.
4. **Credit Availability Verification**: For each eligible merchant, the Transaction & Financial Engine verifies the availability of credits in the corresponding regional pool. If the pool is depleted or the utilization rate exceeds the 85% threshold, the merchant is excluded from the results.
5. **Response Payload**: The API layer returns a filtered list of eligible merchants to the Beneficiary's client, including anonymized merchant details (e.g., name, distance, cuisine type) but excluding any PII or donor-specific information.

### 5.2 Real-Time POS Clearing and Credit Deduction

When a Beneficiary presents a voucher at a Merchant Partner's POS, the Transaction & Financial Engine must interact with the Redis geo-indexing layer to validate the merchant's location and authorize the credit deduction.

1. **POS Clearing Request**: The Merchant's POS system sends a clearing request to the Transaction & Financial Engine, including the voucher ID and the merchant's unique identifier.
2. **Location Validation**: The Transaction & Financial Engine queries the Redis geo-indexing layer to confirm that the merchant's current location matches the location stored in the index. This step prevents fraud where a merchant might attempt to use a voucher outside their designated service area.
3. **Credit Deduction**: Upon successful location validation, the Transaction & Financial Engine deducts the corresponding credit amount from the regional credit pool and updates the Redis geo-indexing layer with the new utilization rate. This update must be atomic to prevent race conditions during peak redemption events.
4. **Anonymized Receipt Generation**: The Transaction & Financial Engine generates an anonymized receipt for the Beneficiary, correlating the donor impact with the redemption event without linking PII ([CON-23A501C051](../project_glossary.md#con-23a501c051)). This receipt is stored in the Financial Ledger Data Model (owned by sibling artifact) and referenced by a UUIDv4 mapping.

### 5.3 Error Handling and Fallback Mechanisms

To ensure high availability and resilience, the integration must include robust error handling and fallback mechanisms in case the Redis geo-indexing layer or the Transaction & Financial Engine experiences latency or failure.

- **Latency Thresholds**: If the Redis GEOHASH query exceeds 100ms, the API layer should trigger a fallback to a cached, slightly stale list of merchants. This ensures that the Beneficiary's search experience is not degraded by transient latency spikes.
- **Credit Pool Exhaustion**: If the Transaction & Financial Engine determines that a regional credit pool is exhausted, it should return a specific error code to the API layer, which will then inform the Beneficiary's client that credits are temporarily unavailable in their area. The client should display a message encouraging the Beneficiary to try again later or to check other nearby merchants.
- **Location Mismatch**: If the merchant's location in the Redis geo-indexing layer does not match the location provided in the POS clearing request, the Transaction & Financial Engine should reject the clearing request and log an alert for the Platform Administrator (ACT-086A974D63) to investigate potential fraud.

### 5.4 Encryption Standards

All data at rest and in transit for the geo-indexing and merchant data models must adhere to the following encryption standards to support PCI-DSS Level 1 compliance (CON-66390130AA) and SOC2 Type II structural planning ([CON-81FB01F06B](../project_glossary.md#con-81fb01f06b)).

#### 4.1.1 Data at Rest

| Component | Algorithm | Key Management | Notes |
| :--- | :--- | :--- | :--- |
| Aurora PostgreSQL | AES-256 | AWS KMS (Key Management Service) | Keys must be rotated annually. Merchant payout details (bank tokens) are encrypted at the application level before storage. |
| Redis (ElastiCache) | AES-256 | AWS KMS | In-transit encryption is mandatory. At-rest encryption is enabled for all nodes. |
| S3 (Backups/Logs) | AES-256 | AWS KMS | All backups and audit logs are encrypted. Access is restricted via IAM policies. |

#### 4.1.2 Data in Transit

| Channel | Protocol | Certificate Management | Notes |
| :--- | :--- | :--- | :--- |
| Client to API | TLS 1.3 | AWS ACM (Automated Certificate Management) | All Expo mobile client and Next.js dashboard traffic must use TLS 1.3. |
| API to Database | TLS 1.2+ | Internal CA or AWS ACM | Internal service-to-service communication (GraphQL/gRPC to DB) must use mutual TLS (mTLS) where possible. |
| API to Redis | TLS 1.2+ | Internal CA or AWS ACM | Redis connections must be encrypted. |

### 5.5 Access Control & Data Isolation

Access to the geo-indexing and merchant data is governed by the Access Control & Multi-Tenant Isolation strategy (sibling artifact). The following specific controls apply to this data surface:

1. **Merchant Data Access**:
   - **Public Profile**: Anonymized merchant data (name, location, cuisine type) is accessible to all authenticated Beneficiaries (ACT-ADA6716160) for search and redemption.
   - **Sensitive Data**: Legal names, payout details, and KYC status are restricted to Platform Administrators (ACT-086A974D63) and the specific NGO Operator (ACT-09E028AEB0) associated with the merchant.
   - **Audit Logging**: All access to sensitive merchant data is logged to AWS CloudTrail ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2)) for SOC2 Type II evidence.

2. **Geo-Indexing Access**:
   - **Read Access**: Open to all authenticated users for proximity-based search.
   - **Write Access**: Restricted to the Merchant Onboarding service and POS integration adapters. Writes are idempotent and versioned to prevent race conditions.

3. **Beneficiary Data Isolation**:
   - Beneficiary demographic data is cryptographically segregated from public merchant data. Access is strictly limited to authorized NGO Operators and Platform Administrators for compliance and dispute resolution ([JNY-2B038C9362](../project_glossary.md#jny-2b038c9362)).

### 5.6 Knowledge Gaps

- **KG-001**: The exact mechanism for updating the Redis geo-indexing layer with real-time merchant location changes (e.g., push vs. pull updates) is not yet defined. This decision impacts the latency and consistency of the geo-indexing data.
- **KG-002**: Specific key rotation policy for AWS KMS keys (e.g., 1-year vs. 2-year rotation). This is required for SOC2 Type II compliance.
- **KG-003**: Exact mTLS certificate management strategy for internal service-to-service communication. This is required for security posture validation.
- **KG-004**: Specific data retention period for offline cached merchant data on Expo devices. This is required for privacy and storage optimization.

## 6. Validation Criteria

This integration design is considered complete when:
1. The API layer can successfully query the Redis geo-indexing layer and return a list of eligible merchants within the p99 latency target.
2. The Transaction & Financial Engine can validate merchant eligibility and credit availability in real-time.
3. The POS clearing flow can successfully deduct credits and update the utilization rate without exposing PII or compromising anonymity.
4. Error handling and fallback mechanisms are implemented and tested under simulated failure conditions.
5. Security and compliance requirements are met, including data isolation, encryption, and audit logging.
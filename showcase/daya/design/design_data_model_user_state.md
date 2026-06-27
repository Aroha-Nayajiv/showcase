# User State & Profile Data Model

This artifact defines the DynamoDB schema for the User State & Profile Data Model, supporting the tripartite actor model (Donor, Beneficiary, NGO Operator) for the MealCredit platform. The design prioritizes high-velocity lookups for POS redemption and donor impact tracking while enforcing strict data isolation to support absolute anonymization of beneficiary data.

### 1.2 Global Secondary Indexes (GSIs)

To support high-velocity lookups without exposing PII, we define the following GSIs. These indexes allow for efficient querying by hashed identifiers or tokens.

| GSI Name | Partition Key (GSI PK) | Sort Key (GSI SK) | Purpose |
| :--- | :--- | :--- | :--- |
| GSI-BeneficiaryLookup | `GSI1PK#<BeneficiaryTokenHash>` | `GSI1SK#<StateVersion>` | High-velocity POS lookups by token. BeneficiaryTokenHash is a cryptographic hash of the redemption token. |
| GSI-DonorLookup | `GSI2PK#<DonorEmailHash>` | `GSI2SK#<StateVersion>` | Donor impact queries and reconciliation. DonorEmailHash is a cryptographic hash of the donor's email. |
| GSI-NGOLookup | `GSI3PK#<NGOOperatorID>` | `GSI3SK#<StateVersion>` | NGO governance and beneficiary management. NGOOperatorID is the UUID of the NGO operator. |

### 1.3 Data Isolation and PII Segregation

To comply with Implied concern: Implied concern: Implement strict data isolation where beneficiary demographic status and legal names are cryptographically segreg... ([CON-92F07E31B0](../project_glossary.md#con-92f07e31b0)) and Implied concern: Implied concern: Classify all beneficiary-related data as 'Highly Sensitive' and restrict database access to cryptographic hashing layers only. ([CON-FCFF86A326](../project_glossary.md#con-fcff86a326)), PII fields are stored in a separate, highly restricted DynamoDB table or a restricted column family.

| Table Name | Content | Access Control |
| :--- | :--- | :--- |
| Public Profile Table (`MealCredit-UserProfiles`) | Contains only hashed identifiers, non-sensitive state (e.g., eligibility status, voucher balance), and metadata. No PII is stored here. | Standard IAM policies for operational roles. |
| Sensitive Profile Table (`MealCredit-UserProfiles-PII`) | Contains legal names, demographic status, and other sensitive data. | Restricted via strict IAM policies and KMS encryption. Linked to the public profile via a shared, hashed identifier. |

### 1.4 Actor-Specific Data Models

#### 1.4.1. Donor Profile
| Field | Type | Constraints |
| :--- | :--- | :--- |
| donorID | String | UUIDv4, Unique |
| emailHash | String | SHA-256 Hash. Unique. |
| fundingHistory | List | List of transaction IDs. |
| roundUpConfig | JSONB | Flexible configuration. Supports multi-modal interaction preferences (voice, tap, scan). |
| impactReceipts | List | List of receipt IDs. |

#### 1.4.2. Beneficiary Profile
| Field | Type | Constraints |
| :--- | :--- | :--- |
| beneficiaryID | String | UUIDv4, Unique |
| tokenHash | String | SHA-256 Hash. Unique. |
| eligibilityStatus | Enum | `ACTIVE`, `SUSPENDED`, `OFFBOARDED`. Managed by NGO Operators. |
| voucherBalance | Decimal | `>= 0` |
| redemptionHistory | List | List of transaction IDs. |

#### 1.4.3. NGO Operator Profile
| Field | Type | Constraints |
| :--- | :--- | :--- |
| ngoOperatorID | String | UUIDv4, Unique |
| ngoID | String | UUIDv4 |
| governanceRoles | List | List of roles. |
| beneficiaryManagement | List | List of beneficiary IDs managed. |

### 1.5 Scalability and Performance

| Metric | Target | Reference |
| :--- | :--- | :--- |
| Concurrent Connections | 10,000 | [CON-7F03CF540E](../project_glossary.md#con-7f03cf540e) |
| p99 Latency (Beneficiary Lookup) | < 250ms | [CON-6D5E21557B](../project_glossary.md#con-6d5e21557b) |
| Auto Scaling | Predictive Scaling Enabled | Peak event-driven loads |
| Write Batching | Enabled | Mitigate GSI write capacity contention |

## 2. Donor User State Schema

This section defines the data model for the Donor actor ([ACT-80C62C7814](../project_glossary.md#act-80c62c7814)), focusing on funding history, donation round-up configuration, and impact receipt correlation. The schema is designed to support the platform's mission of decoupling food assistance from social stigma while ensuring strict compliance with data retention policies ([CON-4820FAD5A9](../project_glossary.md#con-4820fad5a9), [CON-6F604D5455](../project_glossary.md#con-6f604d5455)) and enabling anonymous impact tracking ([CON-23A501C051](../project_glossary.md#con-23a501c051)).

### 2.1 Core Donor Profile Entity

The core donor profile is stored in the primary DynamoDB table, partitioned by `PK#DON#<UUID>` to ensure logical separation from other actor types. This entity holds non-sensitive profile data and configuration settings.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| PK | String | `PK#DON#<UUID>` |
| SK | String | `SK#PROFILE` |
| donor_uuid | String | UUIDv4, Unique. Globally unique identifier for the donor. |
| email_hash | String | SHA-256 Hash. Hashed email address for GSI lookup (GSI-2). Used for impact correlation without exposing PII. |
| display_name | String | Optional, Max 50 chars. Optional public-facing name for donor dashboards. |
| created_at | Timestamp | ISO 8601. Account creation timestamp. |
| last_updated | Timestamp | ISO 8601. Last profile update timestamp. |
| status | Enum | `ACTIVE`, `SUSPENDED`, `CLOSED`. Current account status. |
| jurisdiction | String | ISO 3166-1 alpha-2. Primary jurisdiction for data residency (e.g., US-CA, US-NY, US-IL). |

### 2.2 Donation Round-Up Configuration

Donor preferences for donation round-ups are stored in a JSONB-like structure within the DynamoDB item, allowing for flexible configuration without schema migrations. This supports multi-modal interaction paths (voice, tap, scan) as required by [CON-2D70EDCDEE](../project_glossary.md#con-2d70edcdee).

| Attribute | Type | Description |
| :--- | :--- | :--- |
| round_up_config | Object | Configuration object for donation round-ups. |
| round_up_config.enabled | Boolean | Default: false. Whether round-up donations are active. |
| round_up_config.threshold | Number | Min: 0.01, Max: 100.00. Minimum transaction amount to trigger round-up. |
| round_up_config.round_to | Number | Min: 0.01, Max: 10.00. Amount to round up to (e.g., 0.01 for nearest cent). |
| round_up_config.frequency | Enum | `PER_TRANSACTION`, `DAILY`, `WEEKLY`. Frequency of round-up donations. |
| round_up_config.max_monthly | Number | Min: 0.00. Optional monthly cap for round-up donations. |

### 2.3 Funding History & Impact Receipt Correlation

Funding history is tracked via a separate DynamoDB table (or GSI) to support high-velocity writes and queries. This table links donor transactions to impact receipts, enabling correlation with beneficiary redemption events without linking PII (CON-23A501C051).

| Attribute | Type | Description |
| :--- | :--- | :--- |
| PK | String | `PK#DON#<UUID>` |
| SK | String | `SK#TXN#<UUID>` |
| transaction_id | String | UUIDv4, Unique. Unique identifier for the donation transaction. |
| amount | Number | Min: 0.01. Donation amount in USD. |
| currency | String | ISO 4217. Currency code (default: USD). |
| timestamp | Timestamp | ISO 8601. Transaction timestamp. |
| stripe_charge_id | String | Stripe ID. Reference to the Stripe charge for reconciliation. |
| impact_receipt_id | String | UUIDv4. Unique ID for the generated impact receipt. |
| redemption_uuid_map | Array | UUIDv4[]. List of anonymized beneficiary redemption UUIDs correlated with this donation. |

### 2.4 Data Retention & Compliance

Data retention policies are enforced through lifecycle rules and access controls. PII (legal names, demographic status) is stored in a separate, highly restricted table, linked only via cryptographic hashing or UUIDv4 mapping to the public-facing donor profile, satisfying [CON-0A0288EED4](../project_glossary.md#con-0a0288eed4) and CON-92F07E31B0.

| Data Class | Retention Policy | Implementation |
| :--- | :--- | :--- |
| Donor Transaction History | Retain for 7 years for financial compliance. | DynamoDB TTL on TXN items. |
| Anonymous Redemption Analytics | Retain indefinitely for impact reporting. | No TTL on redemption_uuid_map entries. |
| PII Data | Retain only as long as necessary for KYC/AML. | Automated deletion after KYC verification period. |

### 2.5 Cross-References

| Artifact | Relationship |
| :--- | :--- |
| Stripe Issuing Proxy Contract | Donor funding transactions are initiated via Stripe; see Stripe Issuing Proxy Contract for payment processing details. |
| GraphQL Schema & Type Definitions | Donor profile and transaction data are exposed via GraphQL; see GraphQL Schema & Type Definitions for API contracts. |
| PII Segregation & Anonymization Strategy | PII is stored separately; see PII Segregation & Anonymization Strategy for segregation details. |
| Financial Ledger Data Model | Transaction records are mirrored in the financial ledger; see Financial Ledger Data Model for ledger schema. |

### 2.6 Beneficiary Profile Schema (Public/Operational)

This schema stores the operational state required for voucher redemption and platform interaction. It is designed to be low-latency and highly available, stored in DynamoDB.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| beneficiary_id | UUIDv4 | PK. Unique identifier for the beneficiary. Used for internal tracking and correlation with donor impact (CON-23A501C051). |
| eligibility_status | Enum | `ACTIVE`, `SUSPENDED`, `OFFBOARDED`. Current status of the beneficiary's eligibility for meal credits. Managed by NGO Operators ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)). |
| credit_balance | Decimal | `>= 0`. Current balance of meal credits available for redemption. |
| redemption_token_hash | String | SHA-256 Hash. Cryptographic hash of the redemption token. Used for high-velocity POS lookups without exposing PII (CON-0A0288EED4). |
| preferred_language | String | ISO 639-1. Language preference for the mobile app and wallet passes. |
| last_redemption_timestamp | Timestamp | ISO 8601. Timestamp of the last successful redemption. Used for tracking Donation-to-Redemption Velocity (DRV) ([CON-D0F5814F21](../project_glossary.md#con-d0f5814f21)). |
| device_fingerprint_hash | String | SHA-256 Hash. Hash of the device identifier for fraud prevention and security ([CON-34312C6DC9](../project_glossary.md#con-34312c6dc9)). |

### 2.7 PII Segregation & Anonymization

To ensure absolute anonymity and compliance with FTC guidelines, all Personally Identifiable Information (PII) is segregated into a separate, highly restricted data store. The operational schema above contains no PII.

| Strategy | Implementation |
| :--- | :--- |
| Segregation Strategy | PII fields (legal name, demographic status, contact information) are stored in a separate, encrypted DynamoDB table or a highly restricted column family with KMS encryption. Access is restricted to authorized NGO Operators (ACT-09E028AEB0) and Platform Administrators ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) via strict IAM policies. |
| Anonymization | Beneficiary data is anonymized for analytics and donor impact reporting. Correlation between donor impact receipts and beneficiary redemption events is done using UUIDv4 mapping without linking PII (CON-23A501C051, [CON-413928CB1C](../project_glossary.md#con-413928cb1c)). |
| Data Classification | All beneficiary-related data is classified as 'Highly Sensitive' (CON-<timestamp>). Database access is restricted to cryptographic hashing layers only for non-authorized roles. |

### 2.8 Voucher Redemption History

Redemption history is stored in an append-only log to ensure auditability and support financial reconciliation. This log is stored in Aurora PostgreSQL ([CON-1762EA5021](../project_glossary.md#con-1762ea5021), [CON-6061FCCA83](../project_glossary.md#con-6061fcca83)).

| Attribute | Type | Description |
| :--- | :--- | :--- |
| redemption_id | UUIDv4 | PK. Unique identifier for the redemption event. |
| beneficiary_id | UUIDv4 | FK. Reference to the beneficiary. |
| merchant_id | UUIDv4 | FK. Reference to the merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) where the redemption occurred. |
| amount | Decimal | `> 0`. Amount of meal credits redeemed. |
| timestamp | Timestamp | ISO 8601. Timestamp of the redemption event. |
| transaction_hash | String | SHA-256. Hash of the transaction for auditability. |
| status | Enum | `SUCCESS`, `FAILED`, `REVERSED`. Status of the redemption transaction. |

### 2.9 Eligibility Management

Eligibility is managed by NGO Operators (ACT-09E028AEB0) through the NGO Governance & Beneficiary Offboarding journey ([JNY-4C4BA15817](../project_glossary.md#jny-4c4ba15817)). The eligibility_status field in the operational schema is updated based on decisions made by NGO Operators.

| Workflow | Description |
| :--- | :--- |
| Onboarding | Beneficiaries are onboarded by NGO Operators, who verify eligibility and create the beneficiary profile. |
| Offboarding | NGO Operators can offboard beneficiaries, changing their eligibility_status to OFFBOARDED. This triggers a compliance failure and anonymized recovery process ([JNY-54963DD39A](../project_glossary.md#jny-54963dd39a)). |
| Suspension | Beneficiaries can be suspended in cases of fraud or dispute ([JNY-2B038C9362](../project_glossary.md#jny-2b038c9362), [JNY-CA74D631DC](../project_glossary.md#jny-ca74d631dc)). |

### 2.10 Compliance & Security Constraints

| Constraint | Implementation |
| :--- | :--- |
| PCI-DSS Level 1 | Zero raw card data touches MealCredit servers. All payment processing is handled by Stripe ([CON-66390130AA](../project_glossary.md#con-66390130aa), [CON-C4F0E02638](../project_glossary.md#con-c4f0e02638)). |
| SOC2 Type II | Infrastructure-as-code and access control policies are designed to support SOC2 Type II compliance ([CON-81FB01F06B](../project_glossary.md#con-81fb01f06b), [CON-E84412A0FA](../project_glossary.md#con-e84412a0fa)). |
| Data Residency | User data is stored in compliance with jurisdictional requirements for SF, NYC, and Chicago ([CON-30EA97016B](../project_glossary.md#con-30ea97016b), [CON-4093C26BCC](../project_glossary.md#con-4093c26bcc), [CON-9B82D67FAF](../project_glossary.md#con-9b82d67faf), [CON-DDB51EBF45](../project_glossary.md#con-ddb51ebf45)). |
| Latency | p99 latency for voucher creation and scanning callbacks must be below 250ms under 10,000 concurrent connections (CON-6D5E21557B, CON-7F03CF540E). |

### 2.11 Knowledge Gaps

| Gap ID | Description |
| :--- | :--- |
| `KNOWLEDGE_GAP: PII Segregation & Anonymization Strategy` | The specific technical implementation of PII segregation (e.g., separate table vs. column family) and the exact KMS key management strategy must be defined in the `PII Segregation & Anonymization Strategy` artifact. |
| `KNOWLEDGE_GAP: Eligibility Verification Process` | The specific criteria and process for NGO Operators to verify beneficiary eligibility must be defined in the `NGO Governance & Beneficiary Offboarding` artifact. |
| `KNOWLEDGE_GAP: Fraud Detection Mechanisms` | The specific fraud detection mechanisms for beneficiary accounts (e.g., device fingerprinting, behavioral analysis) must be defined in the `Fraud Detection & Fraud Prevention Screening` artifact. |

### 2.12 Dependencies

| Dependency | Relationship |
| :--- | :--- |
| Stripe Issuing Proxy Contract | The redemption process relies on the Stripe Issuing Proxy for virtual card provisioning or HMAC-signed fallback vouchers. |
| GraphQL Schema & Type Definitions | The beneficiary profile schema must be reflected in the GraphQL schema for API access. |
| gRPC Service Contracts & Definitions | The redemption history log must be accessible via gRPC services for financial reconciliation. |
| Financial Ledger Data Model | Redemption events must be recorded in the financial ledger for reconciliation and payout. |
| Access Control & Multi-Tenant Isolation | Access to beneficiary PII must be controlled by the access control and multi-tenant isolation strategy. |
| Data Residency & Jurisdictional Compliance | Data storage and processing must comply with data residency requirements for SF, NYC, and Chicago. |
| Expo Mobile Client Architecture | The beneficiary mobile app must interact with the beneficiary profile schema for eligibility and redemption. |
| Next.js Dashboard Architecture | The NGO Operator dashboard must interact with the beneficiary profile schema for eligibility management. |

### 3.1 Core Schema Definition

The NGO Operator state is stored in the primary DynamoDB UserProfiles table, partitioned by `PK#NGO#<NGO_ID>`.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| PK | String | `PK#NGO#<UUID>`. Primary Key: Identifies the NGO entity. |
| SK | String | `SK#<StateVersion>`. Sort Key: Supports versioned state updates (e.g., eligibility changes). |
| actor_type | String | Enum: `NGO_OPERATOR`. Actor classification. |
| ngo_id | String | UUIDv4. Unique identifier for the NGO entity. |
| legal_name | String | Required, Max 255 chars. Official registered name of the non-profit organization. |
| tax_id | String | Required, Masked. Tax ID/EIN for compliance and payout verification. Stored in encrypted PII table. |
| status | String | Enum: `PENDING_VERIFICATION`, `ACTIVE`, `SUSPENDED`, `OFFBOARDED`. Current operational status. |
| jurisdiction | String | ISO 3166-2. Metropolitan region (SF, NYC, CHI) for data residency and compliance. |
| governance_roles | List | Array of Strings. List of roles assigned to the operator within the NGO (e.g., ADMIN, AUDITOR, CASE_WORKER). |
| compliance_flags | Object | JSON. Key-value pairs for compliance status (e.g., kyc_verified, audit_trail_enabled). |
| created_at | Timestamp | ISO 8601. Record creation time. |
| updated_at | Timestamp | ISO 8601. Last state update time. |

### 3.2 Governance Roles & Access Control

The governance_roles field defines the operator's permissions within the NGO's scope. This aligns with the Access Control & Multi-Tenant Isolation contract.

| Role | Permissions |
| :--- | :--- |
| ADMIN | Full access to NGO settings, beneficiary management, and compliance reports. |
| AUDITOR | Read-only access to compliance logs, audit trails, and anonymized impact reports. |
| CASE_WORKER | Access to beneficiary eligibility verification and offboarding workflows. |

Note: Specific RBAC matrix details are deferred to the Access Control & Multi-Tenant Isolation artifact.

### 3.3 Beneficiary Offboarding Workflow State

The NGO Operator schema includes a dedicated state machine for beneficiary offboarding, supporting the Beneficiary-Platform Dispute Flow (JNY-2B038C9362) and NGO Governance & Beneficiary Offboarding journey (JNY-4C4BA15817).

| Attribute | Type | Description |
| :--- | :--- | :--- |
| offboarding_queue | List | List of BeneficiaryIDs pending offboarding review. |
| offboarding_reason | String | Reason for offboarding (e.g., ELIGIBILITY_EXPIRED, FRAUD_SUSPECTED, VOLUNTARY_EXIT). |
| last_audit_date | Timestamp | Date of the last compliance audit for this NGO. |
| audit_trail_ref | String | Reference to the immutable audit log entry (linked to Financial Ledger Data Model). |

## 4. Beneficiary PII Cryptographic Segregation and Hashing Strategy

This section defines the cryptographic hashing and segregation strategy for Beneficiary Personally Identifiable Information (PII), ensuring that demographic status and legal names are isolated from public-facing data models. This design directly addresses the project's core mission to decouple food assistance from social stigma by eliminating tracking and social bias at the data layer.

### 4.1 Cryptographic Hashing for Public-Facing Identifiers

To enable high-velocity lookups (e.g., at POS terminals) without exposing PII, all public-facing beneficiary identifiers will be derived using a deterministic, salted cryptographic hash.

| Parameter | Specification |
| :--- | :--- |
| Algorithm | SHA-256 (Secure Hash Algorithm 256-bit). |
| Salt | A project-wide, static, high-entropy salt (stored in AWS Secrets Manager, not in the database) will be concatenated with the raw PII (e.g., legal name + date of birth) before hashing. This prevents rainbow table attacks. |
| Output Format | Hexadecimal string stored in the public-facing DynamoDB table. |
| Lookup Mechanism | When a Beneficiary presents a voucher (e.g., via QR code or NFC tap), the system will hash the presented identifier using the same salt and algorithm, then perform a point lookup in the public-facing table using the hash as the Partition Key. |

### 4.2 Data Segregation Architecture

PII will be physically segregated from public-facing data using a dual-table strategy within the same DynamoDB instance, enforced by strict IAM policies.

| Table Name | Partition Key | Attributes | Access |
| :--- | :--- | :--- | :--- |
| Public-Facing Table (`MealCredit_Beneficiary_Public`) | `PK#BEN#<HashedIdentifier>` | BeneficiaryID (UUIDv4), EligibilityStatus, CreditBalance, LastRedemptionTimestamp, NGOOperatorID. | Readable by Merchant (ACT-AF904DCFF9) and `Platform Administrator` (ACT-086A974D63) roles for transaction processing. No PII fields are present. |
| Private PII Table (`MealCredit_Beneficiary_PII`) | `PK#BEN#<UUIDv4>` | LegalName, DateOfBirth, DemographicStatus, ContactInformation, ConsentTimestamp. | Readable ONLY by `NGO Operator` (ACT-09E028AEB0) and `Platform Administrator` (ACT-086A974D63) roles for eligibility verification and offboarding. Merchant (ACT-AF904DCFF9) role has ZERO access to this table. Encryption: Server-Side Encryption (SSE) with AWS KMS keys, restricted to specific IAM roles. |

### 4.3 Anonymization for Analytics and Impact Reporting

To correlate donor impact with beneficiary redemption without linking PII, a UUIDv4 mapping strategy will be used.

| Component | Description |
| :--- | :--- |
| Mapping Table | A separate, highly restricted DynamoDB table (`MealCredit_Beneficiary_Analytics_Map`) will store the mapping between BeneficiaryID (UUIDv4) and AnonymizedRedemptionID (UUIDv4). |
| Usage | The `Financial Ledger Data Model` (sibling artifact) will use AnonymizedRedemptionID to track redemption events. The Donor (ACT-80C62C7814) impact receipts will reference AnonymizedRedemptionID, ensuring no PII is ever exposed in analytics or donor-facing reports. |
| Data Retention | PII data will be subject to strict retention policies (CON-4820FAD5A9), with automated deletion workflows triggered by `NGO Operator` (ACT-09E028AEB0) actions or regulatory requirements. |

### 4.5 Validation Criteria

| Criterion | Target |
| :--- | :--- |
| Latency | p99 latency for Beneficiary token lookup < 250ms (CON-6D5E21557B). |
| Isolation | No PII fields are returned in GSI queries without explicit, authorized IAM role. |
| Scalability | System handles 10,000 concurrent connections without degradation (CON-7F03CF540E). |
| Anonymity | No de-anonymization attacks can link beneficiaries to donors through metadata analysis ([CON-C22D030D21](../project_glossary.md#con-c22d030d21)). |

This design ensures that the platform's core mission of decoupling food assistance from social stigma is technically enforced at the data layer, providing a robust foundation for trust and compliance.
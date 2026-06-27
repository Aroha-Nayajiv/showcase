# Data Residency & Jurisdictional Compliance

### 1. Data Classification & PII Segregation Strategy

To eliminate social bias and ensure absolute anonymization of beneficiary data, all Beneficiary PII is classified as 'Highly Sensitive' and segregated from the primary financial ledger via cryptographic hashing layers.

Classification Matrix:

| Data Category | Sensitivity Level | Storage Location | Authorized Roles |
|---|---|---|---|
| Beneficiary Legal Names | Highly Sensitive | Isolated Hashing Layer (DB-PII) | NGO Operator (Read-Only), Platform Administrator (Audit) |
| Beneficiary Demographic Status | Highly Sensitive | Isolated Hashing Layer (DB-PII) | NGO Operator (Read-Only), Platform Administrator (Audit) |
| Donor Transaction History | Sensitive | Primary Financial Ledger (DB-Fin) | Donor, Platform Administrator (Audit) |
| Anonymous Redemption Analytics | Public | Analytics Data Warehouse | All Actors (Aggregated) |
| Merchant POS Credentials | Confidential | Secure Vault (AWS Secrets Manager) | Merchant, Platform Administrator |

Segregation Mechanism:

1. Cryptographic Hashing: Beneficiary legal names and demographic status are hashed using SHA-256 with a unique, per-tenant salt before storage in the primary Aurora PostgreSQL instance. The mapping table (Plain Text -> Hash) is stored in a separate, strictly isolated database instance (DB-PII) with different IAM roles.
2. UUIDv4 Mapping: A UUIDv4 is generated for each Beneficiary and used as the primary key across all systems. The DB-PII instance holds the mapping between UUIDv4 and PII. The DB-Fin instance only references the UUIDv4.
3. Access Control: Access to DB-PII is restricted to the NGO Operator role for eligibility verification and the Platform Administrator for audit purposes. The Dispute Adjudicator role has no direct access to DB-PII and must rely on anonymized UUIDv4 references.

### 2. Data Retention Policies

Strict data retention policies are defined to comply with financial regulations and FTC guidelines on anonymity. The specific retention windows for Beneficiary and Donor PII are currently unresolved and must be validated against NGO operational requirements and local privacy laws.

| Data Category | Retention Policy | Disposition Method | Compliance Driver |
|---|---|---|---|
| Donor Transaction History | [KNOWLEDGE_GAP: Exact legal retention period for financial records] | Archival to Cold Storage | Financial Compliance (IRS/SEC) |
| Donor PII (Name, Email) | [KNOWLEDGE_GAP: Exact legal retention period for donor PII] | Anonymization (Hashing) | FTC Anonymity Guidelines |
| Beneficiary PII (Name, Demographics) | [KNOWLEDGE_GAP: Exact legal retention period for beneficiary PII] | Cryptographic Erasure | FTC Anonymity Guidelines |
| Anonymous Redemption Analytics | Indefinite | Aggregated & Stored | Business Intelligence |
| Merchant Payout Records | [KNOWLEDGE_GAP: Exact legal retention period for merchant payout records] | Archival to Cold Storage | Financial Compliance |

Implementation Notes:

Donor PII Anonymization: Donor PII (Name, Email) is hashed and removed from the primary user profile after the legally mandated retention period, leaving only the anonymized transaction history for impact reporting.
Beneficiary PII Erasure: Beneficiary PII is automatically erased after the legally mandated retention period or upon offboarding by the NGO Operator. The UUIDv4 mapping is also removed from DB-PII.
Analytics Aggregation: Redemption events are aggregated into anonymous impact receipts for donors, correlating donor impact with beneficiary redemption events without linking PII, using UUIDv4 mapping for analytics ([CON-23A501C051](../project_glossary.md#con-23a501c051)).

#### 2.1 Tenant-to-Region Mapping Strategy

The API Orchestration Layer must implement a deterministic Tenant-to-Region mapping service. This service acts as the single source of truth for data locality, ensuring that requests from a specific NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) or Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) are routed exclusively to the correct regional cluster.

Mapping Registry: A centralized, highly available configuration service (e.g., AWS Systems Manager Parameter Store or a dedicated region_config table in the primary Aurora PostgreSQL cluster) will store the mapping of Tenant_ID (NGO Operator ID) to Region_ID.
Resolution Logic: Every incoming API request must include a Tenant_ID header (derived from the JWT issued during authentication). The Orchestration Layer will resolve this ID to a Region_ID before any business logic is executed.
Consistency Guarantee: The mapping must be eventually consistent across all API Gateway instances, with a maximum staleness of 5 seconds to prevent routing errors during tenant migrations.

#### 2.2 Regional Data Isolation and Routing

The API Orchestration Layer must enforce strict data isolation by routing requests to region-specific service endpoints. This ensures that data does not cross metropolitan boundaries unless explicitly authorized for backup or disaster recovery purposes.

Regional Endpoints: Each metro footprint will have its own dedicated set of API Gateway endpoints and backend service instances (GraphQL and gRPC). The Orchestration Layer will use DNS-based or header-based routing to direct traffic to the correct regional cluster.
Cross-Region Traffic Blocking: By default, all cross-region API calls are blocked. Any request that attempts to access data from a region other than the one specified in the Tenant_ID mapping will be rejected with a `403 Forbidden` error, citing jurisdictional compliance violations.
Latency Optimization: To prevent restaurant queue stagnation ([CON-4152F2C7C3](../project_glossary.md#con-4152f2c7c3), [CON-5D64EBC654](../project_glossary.md#con-5d64ebc654)), the Orchestration Layer must minimize routing overhead. Region resolution should be cached at the edge (Lambda@Edge or API Gateway) with a short TTL (e.g., 60 seconds) to ensure sub-10ms routing latency.

#### 2.3 Error Handling and Fallback

In the event of a region-specific failure, the API Orchestration Layer must implement a graceful degradation strategy that prioritizes data integrity and compliance over availability.

- Regional Outages: If a regional cluster becomes unavailable, the Orchestration Layer will return a `503 Service Unavailable` error with a clear message indicating the regional outage. No cross-region failover will be attempted automatically to prevent data residency violations.
- Mapping Service Failure: If the Tenant-to-Region mapping service is unavailable, the Orchestration Layer will default to denying all requests (`403 Forbidden`) to prevent accidental data leakage. This is a safe-fail posture.

#### 2.4 Integration with Sibling Artifacts

Access Control & Multi-Tenant Isolation: This artifact defers to the Access Control & Multi-Tenant Isolation artifact for the specific IAM policies and role-based access controls that enforce data isolation at the database level.
PII Segregation & Anonymization Strategy: This artifact defers to the PII Segregation & Anonymization Strategy artifact for the specific cryptographic hashing and data masking techniques used to protect Beneficiary PII.
AWS Multi-AZ Deployment Topology: This artifact defers to the AWS Multi-AZ Deployment Topology artifact for the specific infrastructure components (VPCs, Subnets, Security Groups) that physically isolate the regional clusters.

This design ensures that the API Orchestration Layer acts as the primary enforcement point for data residency and jurisdictional compliance, providing a robust and auditable foundation for the MealCredit platform.

### 3. Multi-Region AWS Infrastructure Topology and Data Persistence Layer Architecture

This section defines the physical and logical distribution of the MealCredit platform across the three initial metropolitan footprints (San Francisco, New York City, Chicago). The architecture prioritizes data sovereignty, PCI-DSS Level 1 compliance, and 99.99% operational uptime through strict regional isolation and high-availability configurations.

#### 3.1 Regional Isolation and Data Residency Strategy

To satisfy `Data residency and jurisdictional compliance for user data across multiple metropolitan regions` ([CON-30EA97016B](../project_glossary.md#con-30ea97016b), [CON-4093C26BCC](../project_glossary.md#con-4093c26bcc)), the platform will not utilize a single global database. Instead, each metro footprint will operate as an independent, sovereign data zone.

Data Sovereignty Enforcement:
All Beneficiary PII (legal names, demographic status) and financial transaction logs generated within a metro footprint must remain within that footprint's AWS region boundaries.
Cross-region replication is strictly prohibited for PII and financial ledger data. Only anonymized, aggregated analytics data may be replicated to a central reporting region for global dashboarding, subject to `Define strict data retention policies for donor transaction history vs. anonymous redemption analytics` ([CON-4820FAD5A9](../project_glossary.md#con-4820fad5a9), [CON-6F604D5455](../project_glossary.md#con-6f604d5455)).
`KNOWLEDGE_GAP: Data Residency & Jurisdictional Compliance - Legal/Compliance must establish the exact data residency requirements for potential future cross-border expansion beyond the initial US metro footprints` ([CON-9B82D67FAF](../project_glossary.md#con-9b82d67faf), [CON-DDB51EBF45](../project_glossary.md#con-ddb51ebf45)).

#### 3.2 Data Persistence Layer: Aurora PostgreSQL

The core financial ledger and user state will be stored in Amazon Aurora PostgreSQL, chosen for its ACID compliance, high availability, and global database features (used here for read-only cross-region analytics only).

Cluster Configuration per Metro:
Engine: Aurora PostgreSQL (Compatible with PostgreSQL 15+)
Instance Class: db.r6g.xlarge (or equivalent) for primary writer nodes to handle high-throughput financial transactions.
Availability: Multi-AZ deployment within the metro region.
Storage: Aurora Storage (auto-scaling up to 128 TB per cluster) with encryption at rest using AWS KMS keys specific to each metro region.
Backup & Retention: [KNOWLEDGE_GAP: Exact automated backup retention period for financial ledger consistency] - Financial Compliance (IRS/SEC)
Point-in-time recovery (PITR) enabled.
`KNOWLEDGE_GAP: Data Residency & Jurisdictional Compliance - Legal/Compliance must establish the exact financial record retention period (e.g., 7 years) to align with IRS and financial regulations` ([CON-226A13FFB8](../project_glossary.md#con-226a13ffb8), [CON-B1DFEBEC8C](../project_glossary.md#con-b1dfebec8c)).

High Availability & Failover:
Aurora PostgreSQL provides automatic failover to a standby replica in a different AZ within < 60 seconds, supporting the `Achieve 99.99% operational uptime across AWS multi-AZ configurations for all critical service endpoints` ([CON-BF1CD5707E](../project_glossary.md#con-bf1cd5707e), [CON-FD21121DD5](../project_glossary.md#con-fd21121dd5)).
Read replicas will be deployed in the same metro region to offload read-heavy operations (e.g., merchant dashboard queries, donor impact reports).

#### 3.3 Caching Layer: Redis Enterprise Cluster

To ensure low-latency access for high-frequency operations (e.g., POS clearance, voucher validation), Redis Enterprise will be deployed in each metro region.

Cluster Configuration per Metro:
Engine: Redis Enterprise (Active-Active Global Database)
Deployment: Multi-AZ within the metro region.
Purpose:
Session management for Expo mobile clients and Next.js dashboards.
Caching for merchant location data and restaurant search results (`Maintain Cache Hit Ratio (CHR) above 92% for restaurant search queries using the Redis Enterprise Cluster` ([CON-527BFA6796](../project_glossary.md#con-527bfa6796), [CON-EA7C3EFECB](../project_glossary.md#con-ea7c3efecb)).
Temporary storage for offline fallback QR/barcode tokens (`Protect against replay attacks on offline fallback QR/barcode tokens using time-bound cryptographic signatures` ([CON-3335D67672](../project_glossary.md#con-3335d67672), [CON-AA83B13877](../project_glossary.md#con-aa83b13877)).
Data Isolation: Redis namespaces will be used to logically isolate data between different NGO Operators and Metro Footprints within the same cluster, though physical separation per metro is preferred for strict data residency.

#### 3.4 API Orchestration and Routing

The API Orchestration Layer ([SUR-85E4A5B6E7](../project_glossary.md#sur-85e4a5b6e7)) will route requests to the appropriate metro-specific data persistence layer based on the user's or tenant's region.

Region-Aware Routing:
API Gateway endpoints will be configured with region-specific routing rules.
Requests from Expo mobile clients and Next.js dashboards will be routed to the nearest AWS region based on the user's location or NGO Operator's registered metro.
`KNOWLEDGE_GAP: Data Residency & Jurisdictional Compliance - Engineering must define the exact mechanism for determining the user's primary metro footprint (e.g., NGO Operator assignment, IP geolocation, or explicit user selection) to ensure correct API routing`.

Cross-Region Communication:
Inter-service communication across metro regions (e.g., for global donor impact reporting) will be handled via asynchronous event streaming (e.g., AWS EventBridge) with anonymized data payloads.
Synchronous cross-region calls are prohibited to prevent latency spikes and data residency violations.

#### 3.5 Security and Compliance Controls

Encryption:
All data in transit will be encrypted using TLS 1.3.
All data at rest will be encrypted using AWS KMS keys managed per metro region.
`KNOWLEDGE_GAP: Data Residency & Jurisdictional Compliance - Security/Compliance must define the exact key rotation policy and key management practices for AWS KMS keys`.

Audit Logging:
All administrative operations and infrastructure changes will be logged to AWS CloudTrail for SOC2 Type II evidence (`Log all administrative ledger operations and infrastructure changes to AWS CloudTrail for SOC2 Type II evidence` ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2), [CON-FBBBF07295](../project_glossary.md#con-fbbbf07295)).
Database access logs will be enabled for Aurora PostgreSQL and Redis Enterprise to monitor for unauthorized access attempts.

Network Security:
All data persistence resources (Aurora, Redis) will be deployed in private subnets within each metro VPC.
Access will be restricted to the API Orchestration Layer and authorized management tools via Security Groups and IAM roles.
`KNOWLEDGE_GAP: Data Residency & Jurisdictional Compliance - Security/Compliance must define the exact VPC peering or Transit Gateway configuration for secure cross-region communication if required for future expansion`.

### 4. Identity & Access Management (IAM) and Data Isolation Controls

This section defines the IAM architecture and cryptographic data isolation controls for the MealCredit platform. It ensures strict segregation of Beneficiary PII (demographic status, legal names) from public-facing services, enforcing the platform's core mission to decouple food assistance from social stigma. This design aligns with the multi-tenant, multi-metro (SF, NYC, Chicago) architecture and supports the Platform Administrator and NGO Operator roles.

#### 4.1 Identity & Access Management (IAM) Architecture

The platform utilizes a centralized Identity Provider (IdP) integrated with AWS IAM for service-to-service authentication. User-facing authentication is handled via the Next.js Dashboard and Expo Mobile Client, leveraging OIDC (OpenID Connect) flows.

##### 5.1.1. Role-Based Access Control (RBAC) Matrix

Access to sensitive data is strictly governed by the following RBAC matrix. Note that the Platform Administrator has broad infrastructure visibility but is explicitly restricted from viewing raw Beneficiary PII without a break-glass audit trail. The NGO Operator is restricted to their assigned metro footprint and tenant scope.

| Role | Actor ID | Scope | PII Access | Audit Logging |
|---|---|---|---|---|
| Platform Administrator | [ACT-086A974D63](../project_glossary.md#act-086a974d63) | Global System Health, Financial Reconciliation, Compliance Logs | None (Hashed only) | All actions logged to CloudTrail |
| NGO Operator | ACT-09E028AEB0 | Assigned Metro Footprint, Assigned Beneficiary Cohort | Hashed Only (Demographic status) | All actions logged to CloudTrail |
| Dispute Adjudicator | [ACT-7BA340FF76](../project_glossary.md#act-7ba340ff76) | Dispute Records, Transaction History | Hashed Only (Legal names) | All actions logged to CloudTrail |
| Donor | [ACT-80C62C7814](../project_glossary.md#act-80c62c7814) | Donor Profile, Impact Receipts | Self (Donor PII) | Standard logging |
| Beneficiary | ACT-ADA6716160 | Voucher Balance, Redemption History | Self (Beneficiary PII) | Standard logging |
| Merchant | [ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9) | POS Integration, Payout Status | None (No Beneficiary PII) | Standard logging |

##### 5.1.2. Break-Glass Access for PII

In the event of a critical dispute or compliance investigation, a Platform Administrator may request temporary access to raw Beneficiary PII. This process requires:
1. Justification: A mandatory, detailed justification for the access request.
2. [KNOWLEDGE_GAP: Data Residency & Jurisdictional Compliance - Governance must establish the exact authorization mechanism (e.g., Dual Authorization) and time-bound token duration for break-glass access].
3. Immutable Audit Log: The access event, including the requesting admin, justification, and data accessed, is written to an append-only cryptographic log (see Section 4.4).

### 5. Validation & Testing

Audit Trail Verification: Automated tests must verify that no raw PII is written to the primary financial ledger (DB-Fin).
Data Residency Check: Network traffic analysis must confirm that data does not leave the designated metro region unless explicitly routed for backup.
De-anonymization Test: Penetration tests must fail to link a donor to a beneficiary via metadata analysis ([CON-C22D030D21](../project_glossary.md#con-c22d030d21)).
Retention Policy Test: Automated jobs must verify that PII is anonymized or erased after the specified retention period.

This artifact's [Access Control & Multi-Tenant Isolation] defers to [Access Control & Multi-Tenant Isolation] for specific IAM role definitions; see that artifact for the full treatment. This artifact's [PII Segregation & Anonymization Strategy] defers to [PII Segregation & Anonymization Strategy] for detailed hashing algorithms; see that artifact for the full treatment.

This section defines the data residency and jurisdictional compliance strategy for the MealCredit platform, ensuring user data is stored and processed within required geographic boundaries while maintaining strict cryptographic isolation of Beneficiary PII to prevent de-anonymization attacks.

#### 6.1 Cryptographic Data Isolation Strategy

To prevent de-anonymization attacks and ensure strict data isolation, Beneficiary PII is never stored in plaintext in the primary financial ledger or public-facing databases. Instead, a Cryptographic Hashing Layer is implemented.

##### 4.1.1. PII Segregation Model

Primary Ledger (Aurora PostgreSQL): Stores only hashed identifiers for Beneficiary legal names and demographic status. The hashing algorithm must be SHA-256 with a unique, salted key per metro footprint to prevent cross-metro correlation. Secure Vault (AWS Secrets Manager / KMS): Stores the mapping between raw PII and hashed identifiers. This vault is physically and logically isolated from the primary ledger. Access to the vault is restricted to the Platform Administrator role (ACT-086A974D63) and only via the Break-Glass process. Public-Facing Services (GraphQL/gRPC): Expose only the hashed identifiers. No raw PII is ever transmitted to the Expo Mobile Client or Next.js Dashboard unless explicitly requested via the Break-Glass process.

##### 4.1.2. Data Residency Enforcement

Data isolation is enforced at the infrastructure level to comply with jurisdictional requirements:

Metro-Local Clusters: Each metro footprint (SF, NYC, Chicago) has its own Aurora PostgreSQL cluster and Redis Enterprise Cluster. Data is never replicated across metro boundaries for operational purposes. IAM Policy Scopes: IAM policies are scoped to specific AWS Regions. An NGO Operator (ACT-09E028AEB0) in NYC can only authenticate and access resources within the us-east-1 (NYC) region. Cross-region access is explicitly denied by default.

#### 6.2 Multi-Tenant Isolation Controls

The platform supports multiple NGOs per metro footprint. Isolation is enforced at the database and application layers.

##### 4.2.1. Database-Level Isolation

Schema-per-Tenant: Each NGO Operator is assigned a dedicated database schema within their metro-specific Aurora PostgreSQL cluster. This ensures physical separation of data at the database level. Row-Level Security (RLS): RLS policies are applied to shared tables (e.g., global configuration tables) to ensure that an NGO Operator can only access rows associated with their tenant ID.

##### 4.2.2. Application-Level Isolation

Tenant Context Injection: Every API request (GraphQL/gRPC) must include a tenant_id header. The API Orchestration Layer validates this header against the authenticated user's IAM role and scope. Request Filtering: All database queries are automatically filtered by tenant_id and metro_region to prevent cross-tenant data leakage.

#### 6.3 Append-Only Cryptographic Log Auditing and SOC2 Type II Evidence Collection

This section defines the immutable audit logging architecture for the MealCredit platform, ensuring that all administrative ledger operations and infrastructure changes are cryptographically verifiable. This design supports SOC2 Type II structural planning ([CON-E84412A0FA](../project_glossary.md#con-e84412a0fa)) and provides the evidence trail required for compliance verification across the SF, NYC, and Chicago metropolitan footprints.

##### 4.3.1. Immutable Ledger Architecture

To satisfy the requirement for append-only cryptographic log auditing in Aurora PostgreSQL ([CON-1762EA5021](../project_glossary.md#con-1762ea5021), [CON-6061FCCA83](../project_glossary.md#con-6061fcca83)), the platform will implement a dual-layer logging strategy. This ensures that no historical record can be altered or deleted, even by Platform Administrators (ACT-086A974D63).

Table Schema:

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| log_id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier for the log entry. |
| event_timestamp | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | The exact time the event occurred, in UTC. |
| actor_id | UUID | NOT NULL | The ID of the actor performing the action (e.g., NGO Operator, Platform Admin). |
| actor_role | VARCHAR(50) | NOT NULL | The role of the actor (e.g., 'Platform Administrator', 'NGO Operator'). |
| action_type | VARCHAR(100) | NOT NULL | The specific action performed (e.g., 'BENEFICIARY_OFFBOARD', 'LEDGER_ADJUSTMENT'). |
| target_entity_id | UUID | NULLABLE | The ID of the entity affected by the action (e.g., Beneficiary ID, Transaction ID). |
| metadata_jsonb | JSONB | NOT NULL | Structured payload containing pre- and post-state snapshots, IP address, and user-agent. |
| previous_hash | CHAR(64) | NOT NULL | The SHA-256 hash of the previous row's log_id + event_timestamp + metadata_jsonb + previous_hash. |
| current_hash | CHAR(64) | NOT NULL | The SHA-256 hash of the current row's log_id + event_timestamp + metadata_jsonb + previous_hash. |
| region_id | VARCHAR(10) | NOT NULL | The metro region where the event occurred (e.g., 'SF', 'NYC', 'CHI'). |

Cryptographic Chaining Logic:

The current_hash for each row is computed as:
`SHA256(log_id || event_timestamp || metadata_jsonb || previous_hash)`

This creates a Merkle-tree-like structure where any alteration to a historical row would invalidate the hash of that row and all subsequent rows, making tampering immediately detectable.

##### 4.3.2. AWS CloudTrail Integration

All infrastructure-as-code changes and administrative API calls to AWS services (e.g., RDS, IAM, S3) will be captured by AWS CloudTrail. To ensure SOC2 Type II compliance (CON-BB253DF0A2, CON-FBBBF07295), CloudTrail logs will be:

1. Enabled for all regions: SF, NYC, and Chicago.
2. Delivered to a dedicated, immutable S3 bucket: This bucket will have Object Lock enabled in 'Compliance' mode to prevent deletion or overwriting for a minimum retention period.
3. Cross-referenced: The log_id from the Aurora audit_log table will be included in the metadata_jsonb of relevant CloudTrail events, allowing for seamless correlation between application-level actions and infrastructure-level changes.

##### 4.3.3. SOC2 Type II Evidence Collection Strategy

To streamline the SOC2 Type II audit process, the platform will implement automated evidence collection pipelines that map directly to SOC2 Trust Service Criteria (TSC).

Automated Evidence Extraction:
A dedicated 'Compliance Service' (part of the API Orchestration Layer) will periodically extract and hash the audit_log table. This service will:

1. Generate Daily Hashes: Compute a SHA-256 hash of the entire audit_log table for the previous day.
2. Store Hashes in S3: Upload these daily hashes to the immutable S3 bucket, creating a verifiable chain of daily integrity.
3. Provide Audit API: Expose a read-only API endpoint that allows auditors to request the hash chain for any given date range, along with the raw log entries for verification.

Key SOC2 Controls Mapped:

| Control ID | Control Objective | Implementation Evidence |
| :--- | :--- | :--- |
| CC6.1 (Logical Access) | All administrative actions are logged with actor_id and actor_role. | audit_log table, actor_role field |
| CC6.6 (Security Events) | All failed login attempts and privilege escalation attempts are logged. | audit_log table, action_type = 'LOGIN_FAILURE', 'PRIVILEGE_ESCALATION' |
| CC7.2 (System Monitoring) | Real-time alerts for suspicious activity (e.g., multiple failed logins, unusual data exports). | CloudTrail logs, Aurora audit_log table |
| CC8.1 (Change Management) | All infrastructure changes are logged in CloudTrail and correlated with application logs. | CloudTrail logs, audit_log table |

##### 4.3.4. Data Retention and Archival

To comply with financial regulations and data residency requirements (CON-30EA97016B, CON-4093C26BCC), audit logs will be retained for a minimum period. The exact retention duration for audit logs and the hot storage window must be established by legal and compliance teams to align with specific financial regulations.

Retention Policy:

| Storage Tier | Retention Window | Description |
| :--- | :--- | :--- |
| Hot Storage (Aurora PostgreSQL) | [KNOWLEDGE_GAP: Exact retention period for hot storage audit logs - Legal/Compliance must establish this before implementation] | Active, queryable logs. |
| Warm Storage (S3 Standard) | [KNOWLEDGE_GAP: Exact warm storage transition period - Legal/Compliance must establish this before implementation] | Archived logs accessible for standard retrieval. |
| Cold Storage (S3 Glacier Deep Archive) | [KNOWLEDGE_GAP: Exact cold storage retention period - Legal/Compliance must establish this before implementation] | Long-term archival for regulatory compliance. |

Archival Process:

1. Monthly Batch Job: A scheduled Lambda function will query the audit_log table for entries older than the hot storage threshold.
2. Export to S3: These entries will be exported to CSV format and uploaded to the 'Warm Storage' S3 bucket.
3. Hash Verification: The SHA-256 hash of the exported CSV will be stored in the audit_log table to ensure integrity during archival.
4. Delete from Aurora: Once successfully archived and verified, the entries will be deleted from the Aurora PostgreSQL table.

##### 4.3.5. Access Control for Audit Logs

Access to the audit_log table and CloudTrail logs will be strictly controlled via IAM roles and policies.

Platform Administrators (ACT-086A974D63): Can read audit logs for investigation purposes but cannot write or delete them. NGO Operators (ACT-09E028AEB0): Have no direct access to the audit_log table. They can only view anonymized summaries of their own organization's activities via the Next.js Dashboard. Dispute Adjudicators (ACT-7BA340FF76): Have read-only access to specific log entries related to disputes they are handling, scoped by target_entity_id.

#### 6.4 Anonymization for Analytics

UUIDv4 Mapping: Beneficiary redemption events are correlated with donor impact receipts using UUIDv4 mappings. No PII is included in analytics queries. Aggregation Thresholds: Analytics reports must enforce a minimum aggregation threshold to prevent re-identification of small cohorts. The exact minimum cohort size must be established by the Compliance & Security team before implementation.

#### 6.5 Validation and Testing

To ensure the integrity of the audit logging system, the following tests will be implemented:

1. Tamper Detection Test: A script will attempt to modify a historical row in the audit_log table and verify that the hash chain is broken and the tampering is detected.
2. Archival Integrity Test: A script will verify that the hash of the archived CSV matches the hash stored in the audit_log table.
3. Access Control Test: Automated tests will verify that Platform Administrators cannot delete audit logs and that NGO Operators cannot access the audit_log table directly.

This design ensures that the MealCredit platform maintains a robust, tamper-proof audit trail, supporting SOC2 Type II compliance and providing the necessary evidence for regulatory verification.

#### 6.6 Jurisdictional Data Boundaries

The platform operates across three initial metropolitan footprints: San Francisco (SF), New York City (NYC), and Chicago (CHI). To comply with data residency requirements (CON-30EA97016B, CON-4093C26BCC), all user data must be stored and processed within the geographic boundaries of the user's designated metro footprint.

Data Sovereignty: User data, including Beneficiary PII, Donor financial information, and Merchant transaction logs, must not leave the AWS Region associated with their metro footprint unless explicitly required for cross-metro aggregation (e.g., global reporting) and only after strict anonymization. Cross-Border Compliance: If the platform expands beyond the initial US metro footprints, cross-border data residency compliance must be ensured (CON-9B82D67FAF, CON-DDB51EBF45). This requires a separate architectural review to determine data localization requirements for each new jurisdiction.

#### 6.7 Infrastructure-Level Data Isolation

Data isolation is enforced at the infrastructure level to prevent cross-metro data leakage.

Data is never replicated across metro boundaries for operational purposes. IAM Policy Scopes: IAM policies are scoped to specific AWS Regions. An NGO Operator in NYC can only authenticate and access resources within the us-east-1 (NYC) region. Cross-region access is explicitly denied by default.

#### 6.8 Data Retention and Archival

Retention Policy:

| Storage Tier | Retention Window | Description |
| :--- | :--- | :--- |
| Hot Storage (Aurora PostgreSQL) | [KNOWLEDGE_GAP: Exact retention period for hot storage audit logs - Legal/Compliance must establish this before implementation] | Active, queryable logs. |
| Warm Storage (S3 Standard) | [KNOWLEDGE_GAP: Exact warm storage transition period - Legal/Compliance must establish this before implementation] | Archived logs accessible for standard retrieval. |
| Cold Storage (S3 Glacier Deep Archive) | [KNOWLEDGE_GAP: Exact cold storage retention period - Legal/Compliance must establish this before implementation] | Long-term archival for regulatory compliance. |

Archival Process:

1. Monthly Batch Job: A scheduled Lambda function will query the audit_log table for entries older than the hot storage threshold.
2. Export to S3: These entries will be exported to CSV format and uploaded to the 'Warm Storage' S3 bucket.
3. Hash Verification: The SHA-256 hash of the exported CSV will be stored in the audit_log table to ensure integrity during archival.
4. Delete from Aurora: Once successfully archived and verified, the entries will be deleted from the Aurora PostgreSQL table.

#### 6.9 Beneficiary PII Retention and Erasure

To adhere to FTC Anonymity Guidelines and data minimization principles, Beneficiary PII must be retained for the minimum duration necessary to fulfill the transaction and legal obligations.

Retention Period: Beneficiary PII (legal names, demographic status) must be retained for a maximum of [KNOWLEDGE_GAP: Exact Beneficiary PII retention period - Legal/Compliance must establish this before implementation] after the associated transaction is completed, unless a longer retention period is required by financial regulations (e.g., anti-money laundering laws). Erasure Process: After the retention period, Beneficiary PII must be cryptographically erased from the Secure Vault and all associated databases. The hashed identifiers may be retained for analytics purposes, provided they cannot be reverse-engineered to identify the individual. Knowledge Gap: What specific financial regulations (e.g., unclaimed property, escheatment laws) require a longer retention period for Beneficiary PII than the standard? This must be resolved by the Compliance & Security team before implementation.

#### 6.10 Break-Glass Access Protocol

Access to the Secure Vault for raw PII is restricted to the Platform Administrator role (ACT-086A974D63) and only via the Break-Glass process. The specific governance mechanisms for this process, such as dual authorization requirements and session token durations, are not established in the project requirement and must be defined by the Compliance & Security team.

 Break-Glass Protocol: [ASSUMPTION: Break-Glass access requires dual authorization and short-lived session tokens - Reversible pending Compliance & Security team definition of exact governance mechanisms].
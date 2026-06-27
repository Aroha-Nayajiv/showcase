# Infrastructure Topology & Deployment Design

## 1. Regional Deployment Strategy

To meet the target scale of 50,000 MAU and ensure high availability, the platform will adopt a Single-Region, Multi-AZ deployment model for each metro footprint. This approach minimizes latency for local users and simplifies data residency compliance (CON-30EA97016B, CON-4093C26BCC) while avoiding the complexity and cost of active-active cross-region replication for financial transactions.

*   **SF Region:** AWS us-west-2 (Oregon). Primary hub for West Coast operations.
*   **NYC Region:** AWS us-east-1 (N. Virginia). Primary hub for East Coast operations.
*   **CHI Region:** AWS us-east-2 (Ohio). Primary hub for Midwest operations.

Each region operates as an independent logical tenant with isolated VPCs, databases, and compute resources. Cross-region replication is reserved for disaster recovery (CON-10F4381094) and is not used for active transaction processing to prevent split-brain financial ledger issues.

### 1.1 Network Topology & Segmentation

Each regional VPC is segmented into public, private, and isolated subnets to enforce strict security boundaries and PCI-DSS Level 1 compliance (CON-66390130AA).

*   **Public Subnets:** Host NAT Gateways for outbound internet access from private subnets. No compute resources reside here.
*   **Private Subnets (Application Tier):** Host the API Gateway endpoints, Lambda functions for event-driven processing, and ECS Fargate tasks for gRPC services. These subnets have no direct internet access.
*   **Private Subnets (Data Tier):** Host Aurora PostgreSQL, DynamoDB Global Tables (if used for non-financial data), and ElastiCache Redis clusters. These subnets are strictly isolated from the public internet.
*   **Isolated Subnets (Database Tier):** Host the primary Aurora PostgreSQL instances for the financial ledger. These subnets have no internet gateway or NAT gateway access, ensuring zero raw card data or PII can exfiltrate.

### 1.2 Core Infrastructure Services

#### 1.2.1. Compute & Orchestration

*   **API Gateway:** Serves as the ingress for RESTful APIs and GraphQL queries. Configured with WAF for DDoS protection and rate limiting.
*   **AWS Lambda:** Handles event-driven serverless functions, including Stripe webhook processing, voucher validation, and notification dispatch. Provisioned Concurrency is used for critical webhook handlers to ensure <150ms latency (CON-06232374D9).
*   **ECS Fargate:** Hosts the gRPC financial services for high-throughput, low-latency POS callbacks. Fargate allows for precise resource allocation and scaling based on concurrent connection load.

#### 1.2.2. Data Persistence

*   **Aurora PostgreSQL (Serverless v2):** The primary database for the financial ledger. Chosen for its ACID compliance, high availability, and ability to support append-only cryptographic logging (CON-1762EA5021). Data is encrypted at rest using AWS KMS keys managed by the Platform Administrator.
*   **DynamoDB:** Used for high-scale, low-latency event storage and caching of non-financial data (e.g., merchant profiles, restaurant search indices). If used for financial data, it must be paired with a robust reconciliation process.
    *   `KNOWLEDGE_GAP: Financial ledger reconciliation strategy - The decision to use Aurora PostgreSQL for the financial ledger is based on ACID requirements. However, the specific reconciliation process (e.g., periodic hash-checksums vs. distributed write-ahead ledger) is not yet defined. This must be detailed in the Financial Ledger Data Model artifact.`
*   **Redis Enterprise Cluster:** Provides caching for restaurant search queries and session data, targeting a Cache Hit Ratio (CHR) above 92% (CON-527BFA6796). Deployed in a multi-AZ configuration for high availability.

### 1.3 Knowledge Gaps & Assumptions

*   `ASSUMPTION: Single-Region Active Deployment - It is assumed that each metro footprint will operate in a single AWS Region for active traffic. Cross-region replication is deferred to Phase 2 for disaster recovery. Evidence needed: Business requirement for active-active cross-region failover.`
*   `ASSUMPTION: Stripe Connected Accounts - It is assumed that Stripe Connected Accounts will be used for merchant payouts, requiring KYC compliance across jurisdictions (SF, NYC, Chicago). Evidence needed: Confirmation of Stripe product selection for payouts.`

---

## 2. Multi-Tenant Data Isolation & Cryptographic Segregation Strategy

This section defines the logical and physical data isolation boundaries for the MealCredit platform, ensuring strict segregation between NGO Operator operational data and Highly Sensitive Beneficiary information. The strategy is designed to support 50,000 MAU across SF, NYC, and Chicago while maintaining PCI-DSS Level 1 and SOC2 Type II compliance.

### 2.1 Logical Isolation Architecture

The platform utilizes a Multi-Tenant Logical Isolation model within a shared AWS infrastructure footprint per metropolitan region. This approach balances cost-efficiency with strict data segregation requirements.

*   **Tenant Boundary Definition:**
    *   **NGO Operator (ACT-09E028AEB0):** Each NGO Operator is treated as a distinct logical tenant. Their operational data (merchant onboarding, payout reconciliation, user management) is isolated via Row-Level Security (RLS) policies in the primary data store.
    *   **Beneficiary (ACT-ADA6716160):** Beneficiary data is further segmented. While beneficiaries are associated with an NGO Operator, their Personally Identifiable Information (PII) is cryptographically segregated from the NGO Operator's direct query scope.
    *   **Donor (ACT-80C62C7814) & Merchant (ACT-AF904DCFF9):** Donor and Merchant data are treated as separate logical domains with cross-referencing via anonymized UUIDs to prevent PII linkage.

*   **Implementation Mechanism:**
    *   **Database Level:** Aurora PostgreSQL (Serverless v2) will enforce isolation using Row-Level Security (RLS) policies. Each query must include a tenant_id context variable. RLS policies will automatically filter rows based on the authenticated user's NGO Operator association.
    *   **Application Level:** The API Orchestration Layer (SUR-85E4A5B6E7) will inject the tenant_id into the database connection context for every request originating from an NGO Operator or Beneficiary client.

### 2.2 Cryptographic Segregation of Highly Sensitive Data

To adhere to CON-<timestamp> (Classify all beneficiary-related data as 'Highly Sensitive') and CON-92F07E31B0 (Implement strict data isolation where beneficiary demographic status and legal names are cryptographically segregated), the following strategy is implemented:

*   **Data Classification:**
    *   **Highly Sensitive Data (HSD):** Legal names, government-issued ID numbers, demographic status, and contact information.
    *   **Operational Data:** Beneficiary ID, credit balance, transaction history, and redemption status.

*   **Cryptographic Hashing Strategy:**
    *   **Deterministic Hashing for Linkage:** Beneficiary PII (e.g., legal name + DOB) will be hashed using HMAC-SHA256 with a rotating salt key stored in AWS KMS. This allows for deterministic matching (e.g., for fraud prevention) without storing plaintext PII.
    *   **One-Way Hashing for Storage:** All HSD fields will be stored as one-way hashes in the primary operational schema. The plaintext PII will be stored in a separate, highly restricted HSD Vault (a dedicated Aurora PostgreSQL schema with stricter IAM policies and encryption keys).
    *   **Access Control:** Access to the HSD Vault is restricted to the Platform Administrator (ACT-086A974D63) and authorized NGO Operator (ACT-09E028AEB0) roles for specific, audited offboarding or dispute resolution workflows (JNY-4C4BA15817, JNY-2B038C9362).

*   **Anonymization for Analytics:**
    *   CON-23A501C051 (Correlate donor impact receipts with beneficiary redemption events without linking PII) is addressed by using UUIDv4 mapping for analytics. The mapping table between UUIDs and hashed PII is stored in the HSD Vault and is never exposed to the analytics engine or NGO Operator dashboards.

### 3.1 Financial Ledger: Aurora PostgreSQL (Serverless v2)

The financial ledger is the system's source of truth for all monetary movements. It must guarantee ACID compliance and support append-only cryptographic logging for SOC2 Type II auditability.

*   **Deployment Topology:** Multi-AZ deployment within each metro region (us-west-2 for SF, us-east-1 for NYC, us-east-2 for Chicago). Cross-region replication is configured for Disaster Recovery (CON-10F4381094) but is not active-active for transaction processing to prevent split-brain financial states.
*   **Compliance & Security:**
    *   **Encryption:** Data at rest is encrypted using AWS KMS keys managed by the Platform Administrator. Data in transit is encrypted via TLS 1.3.
    *   **Audit Logging:** All financial ledger mutations are logged to an append-only cryptographic log (CON-1762EA5021). These logs are streamed to AWS CloudTrail for SOC2 Type II evidence (CON-BB253DF0A2).
    *   **Access Control:** Database access is restricted to the API Orchestration Layer and gRPC Financial Services via VPC endpoints. No direct public internet access is permitted.
*   **Performance Constraints:**
    *   **Latency:** The ledger must support real-time debit/credit operations with p99 latency < 100ms to ensure Stripe Webhook Processing Latency averages below 150ms (CON-06232374D9).
    *   **Scalability:** Serverless v2 scaling units are configured to handle peak event-driven load (CON-121117F5A2) during donation spikes.

### 3.2 High-Scale Event Storage: DynamoDB

DynamoDB is utilized for high-throughput, low-latency storage of non-financial event data, including user session states, merchant inventory updates, and anonymous redemption analytics.

*   **Deployment Topology:** Single-region deployment per metro footprint (SF, NYC, Chicago) with global tables enabled for cross-region read replication. This ensures low-latency access for local users while maintaining data durability.
*   **Data Isolation:**
    *   **Multi-Tenancy:** Logical isolation is enforced via partition keys that include the metro_region and tenant_id (NGO Operator ID). This aligns with the multi-tenant architecture requirement (CON-30EA97016B).
    *   **Anonymization:** Beneficiary demographic data is never stored in DynamoDB. Only anonymized UUIDs and redemption counts are persisted, ensuring FTC guidelines on anonymity are met (CON-B3D71A437D).
*   **Performance Constraints:**
    *   **Throughput:** Provisioned capacity is set to auto-scale with a minimum of 1,000 WCUs/RCUs per table, scaling up to handle 50,000 MAU.
    *   **Latency:** p99 latency for read/write operations must be < 50ms to support real-time POS clearance (CON-4152F2C7C3).

### 3.3 Caching Layer: Redis Enterprise Cluster

Redis Enterprise Cluster is deployed to cache high-frequency read data, such as restaurant search results, merchant profiles, and active voucher states, to reduce load on the primary database.

*   **Deployment Topology:** Active-Active cluster across multiple Availability Zones within each metro region. This ensures high availability and low-latency access for the Expo mobile application and Next.js dashboards.
*   **Cache Strategy:**
    *   **Cache-Aside Pattern:** Used for restaurant search and merchant profiles. TTL is set to 5 minutes for merchant profiles and 1 minute for search results to balance freshness and load reduction.
    *   **Session Storage:** User sessions for the Expo app and web dashboards are stored in Redis with a 24-hour TTL.
*   **Performance Constraints:**
    *   **Cache Hit Ratio (CHR):** Target CHR > 92% for restaurant search queries (CON-527BFA6796). Automated alerts are configured to trigger if CHR drops below 85%.
    *   **Latency:** p99 latency for cache read/write operations must be < 10ms.

---

## 4. API Orchestration Layer and Integration Patterns

This section defines the API Orchestration Layer (SUR-85E4A5B6E7), serving as the central nervous system for the MealCredit platform. It details the interaction between the GraphQL API, gRPC financial services, and Stripe Webhooks to ensure real-time POS clearance latency targets are met while maintaining strict PCI-DSS Level 1 and SOC2 Type II compliance.

### 4.1 Architectural Overview and Service Boundaries

The API Orchestration Layer is a hybrid architecture designed to handle high-throughput CRUD operations via GraphQL and low-latency, high-integrity financial transactions via gRPC. This separation ensures that heavy analytical queries do not compete for resources with critical payment processing paths.

*   **GraphQL API Gateway (SUR-85E4A5B6E7):** Serves as the primary ingress for the Expo mobile clients (Beneficiary, Donor) and Next.js dashboards (NGO Operator, Platform Administrator, Merchant). It handles user state management, merchant discovery, and non-financial metadata.
*   **gRPC Financial Services:** A dedicated, internal service mesh for financial transactions. This layer is optimized for low-latency, bidirectional streaming, and strict type safety. It handles voucher creation, POS clearance, and ledger mutations.
*   **Stripe Webhook Processor:** An event-driven serverless function that ingests Stripe events (e.g., payment_intent.succeeded, charge.failed) and translates them into internal platform events for ledger updates and merchant payouts.

### 4.2 GraphQL API Orchestration

The GraphQL API is the public-facing contract for all non-financial interactions. It is designed to be stateless and horizontally scalable.

#### 4.2.1. Core GraphQL Operations

*   **Beneficiary Eligibility & Voucher Redemption (JNY-E82B8A88D8):**
    *   `query getBeneficiaryStatus(ngoId: ID!, beneficiaryId: ID!): BeneficiaryStatus!` - Returns the current credit balance and eligibility status. This query is heavily cached (Redis) to ensure <50ms response times.
    *   `mutation requestVoucher(amount: Float!, metroRegion: MetroRegion!): Voucher!` - Initiates the voucher creation process. This mutation triggers an asynchronous gRPC call to the Financial Service and returns a Voucher object with a `status: PENDING`. The client polls for completion or receives a Server-Sent Event (SSE) update.

*   **Merchant & NGO Operations (JNY-356F465DB3, JNY-4C4BA15817):**
    *   `query getMerchantDashboard(merchantId: ID!): MerchantDashboard!` - Returns real-time sales data, pending payouts, and dispute notifications.
    *   `mutation updateMerchantProfile(merchantId: ID!, profile: MerchantProfileInput!): Merchant!` - Allows NGO Operators to update merchant KYC and operational details.

*   **Donor Onboarding & Funding Activation (JNY-62D850E94B):**
    *   `mutation activateDonorFunding(donorId: ID!, fundingSource: FundingSourceInput!): DonorAccount!` - Integrates with Stripe Checkout to activate recurring or one-time donations.
    *   `query getDonorImpactReceipts(donorId: ID!): [ImpactReceipt!]!` - Returns anonymized impact metrics, correlating donor contributions with redemption events without linking PII (CON-23A501C051).

#### 4.2.2. Performance and Caching Strategy

*   **Cache Hit Ratio (CHR):** The GraphQL layer must maintain a CHR above 92% for restaurant search and beneficiary status queries using the Redis Enterprise Cluster (CON-527BFA6796).
*   **SSE for Real-Time Updates:** Next.js dashboards utilize Server-Sent Events (SSE) to receive real-time updates on voucher status, dispute notifications, and payout confirmations, replacing the legacy polling mechanism.

### 4.3 gRPC Financial Services Integration

The gRPC layer is the critical path for financial integrity. It is designed to handle the strict latency requirements of POS clearance.

#### 4.3.1. Service Contracts and Boundaries

*   **Voucher Creation Service:**
    *   `rpc CreateVoucher(CreateVoucherRequest) returns (CreateVoucherResponse);`
    *   Input: beneficiaryId, amount, metroRegion.
    *   Output: voucherId, token, expiry, status.
    *   Latency Target: p99 latency below 250ms for voucher creation under 10,000 concurrent connections (CON-6D5E21557B).

*   **POS Clearance Service:**
    *   `rpc ClearTransaction(ClearTransactionRequest) returns (ClearTransactionResponse);`
    *   Input: voucherToken, merchantId, amount, timestamp.
    *   Output: transactionId, status (APPROVED/DECLINED), remainingBalance.
    *   Latency Target: p99 latency below 250ms for scanning callbacks (CON-6D5E21557B).
    *   Double-Spending Prevention: The service must implement strict idempotency keys to prevent double-spending (CON-61EC670500). Each voucherToken can only be cleared once per transaction.

#### 4.3.2. Inter-Service Communication

*   **GraphQL to gRPC:** The GraphQL resolvers for financial mutations (requestVoucher, clearTransaction) act as thin clients, forwarding requests to the gRPC services. They do not contain business logic but handle authentication, authorization, and input validation.
*   **gRPC to Aurora PostgreSQL:** The gRPC services interact with Aurora PostgreSQL for financial ledger mutations. All mutations are wrapped in ACID transactions to ensure consistency.
*   **gRPC to Redis:** The gRPC services use Redis for caching voucher states and session data to reduce database load.

### 4.4 Stripe Webhook Processing and Integration

Stripe Webhooks are the primary mechanism for receiving real-time updates on payment events. The processing layer must be highly available and idempotent.

#### 4.4.1. Webhook Processing Pipeline

*   **Ingress:** Stripe Webhooks are sent to a dedicated AWS API Gateway endpoint, which triggers an AWS Lambda function.
*   **Verification:** The Lambda function verifies the Stripe signature to ensure the payload is authentic.
*   **Event Translation:** The Lambda function translates Stripe events (e.g., payment_intent.succeeded) into internal platform events (e.g., DonorFundingActivated).
*   **Event Bus:** The internal event is published to an AWS EventBridge bus, which triggers downstream services (e.g., Financial Service for ledger updates, Notification Service for donor receipts).
*   **Latency Target:** Stripe Webhook Processing Latency must average below 150ms from card tap to merchant ledger entry (CON-06232374D9). This is achieved by using Lambda Provisioned Concurrency for critical webhook handlers.

#### 4.4.2. Error Handling and Retries

*   **Dead-Letter Queue (DLQ):** Failed webhook events are sent to a DLQ for manual inspection and retry. This ensures no payment event is lost.
*   **Idempotency:** All webhook handlers must be idempotent to handle duplicate events from Stripe.

### 4.6 SOC2 Type II Structural Planning

To achieve SOC2 Type II certification, the infrastructure must be designed with "trust but verify" principles baked into the deployment pipeline. The following structural controls are mandatory:

*   **Infrastructure as Code (IaC) Auditability:** All AWS resources (VPCs, Subnets, Security Groups, IAM Roles) must be defined in version-controlled IaC templates (e.g., Terraform or AWS CDK). This ensures that every infrastructure change is tracked, reviewed, and reproducible, providing the evidence trail required for SOC2 Type II audits.
*   **Automated Compliance Scanning:** Implement automated compliance scanning within the CI/CD pipeline using tools like AWS Config Rules or Open Policy Agent (OPA). Policies must enforce:
    *   No open security groups (all ingress/egress must be explicitly defined).
    *   Encryption at rest enabled for all storage services (S3, RDS, EBS).
    *   Multi-AZ deployment for all critical services (Aurora, ElastiCache).
*   **Access Control Reviews:** Define a quarterly access review process for all privileged accounts (Platform Administrator, NGO Operator). Access must be granted via least-privilege IAM roles, with temporary credentials (STS) for service-to-service communication.

### 4.7 AWS CloudTrail Logging and Administrative Auditing

To ensure complete traceability of all administrative and infrastructure changes, AWS CloudTrail must be configured as the central audit log for the platform.

*   **Management Events:** Enable CloudTrail for all management events (e.g., IAM changes, S3 bucket policy updates, RDS instance modifications). These logs must be delivered to a dedicated, encrypted S3 bucket with Object Lock enabled to prevent tampering.
*   **Data Events:** Enable data event logging for critical resources:
    *   **Aurora PostgreSQL:** Log all DML operations (INSERT, UPDATE, DELETE) on the financial ledger and beneficiary PII tables. This supports the requirement for append-only cryptographic log auditing (CON-1762EA5021).
    *   **S3 Buckets:** Log all access events to sensitive data buckets (e.g., donor PII, merchant KYC documents).
*   **Log Integrity and Retention:** CloudTrail logs must be encrypted with AWS KMS keys managed by the Platform Administrator.
    *   `KNOWLEDGE_GAP: Financial log retention period - The specific legal retention window for financial logs in NYC and Chicago requires verification by the records-governance owner. The assumed 7-year retention is not yet grounded in project truth.`
*   **Alerting:** Configure CloudWatch Alarms to trigger immediate notifications for:
    *   IAM role changes or new user creation.
    *   Security group modifications that open ports to 0.0.0.0/0.
    *   CloudTrail configuration changes (e.g., stopping logging).

### 4.8 Offline Fallback Security for Expo Mobile Applications

To ensure resilience during network outages while maintaining security, the Expo mobile application must implement a secure offline fallback mechanism for voucher redemption. This design prevents token theft, cloning, and replay attacks.

*   **Secure Client-Side Storage:** All offline tokens and cryptographic keys must be stored in the Expo SecureStore (backed by Android Keystore and iOS Keychain). This ensures that tokens are encrypted at rest and inaccessible to other applications or root/jailbroken devices.
*   **Time-Bound Cryptographic Signatures:** Offline vouchers must be generated as JWT-like tokens signed with a time-bound HMAC-SHA256 signature. The token must include:
    *   `beneficiary_id_hash`: A deterministic hash of the beneficiary ID (no PII).
    *   `credit_amount`: The fractional credit value.
    *   `expiry_timestamp`: A short-lived validity window (e.g., 15 minutes) to prevent replay attacks (CON-3335D67672).
    *   `merchant_id`: The target merchant ID to restrict token usage.
*   **Replay Attack Prevention:** The merchant POS system must validate the token's signature and timestamp upon scan. If the timestamp is outside the validity window, the token is rejected. Additionally, the platform must maintain a short-term cache of recently used token hashes to prevent immediate replay within the validity window.
*   **Offline Fallback Interface:** The Expo app must provide a simplified, intuitive interface for offline redemption, clearly displaying the token's expiry time and remaining credit. This interface must be accessible via voice commands and high-contrast modes to meet WCAG standards (CON-68497304B1, CON-FA7A13E601).

### 4.9 Implementation Notes

*   **IaC Templates:** Create Terraform modules for VPC, Aurora, ElastiCache, and CloudTrail.
*   **Security Groups:** Define strict ingress/egress rules for all subnets.
*   **KMS Keys:** Create KMS keys for CloudTrail, Aurora, and S3 encryption.
*   **Expo SecureStore:** Implement SecureStore integration for offline token storage.
*   **CloudWatch Alarms:** Configure alarms for critical security events.

### 4.10 Follow-Up Questions

*   **Question:** Who owns the offline token revocation strategy?
    *   **Why Critical:** The current design assumes a short-lived token strategy, but a formal revocation process is needed for fraud scenarios.
    *   **Answerable:** False
    *   **Blocking:** True
*   **Question:** What is the exact legal retention period for financial logs in NYC and Chicago?
    *   **Why Critical:** The assumed 7-year retention may need adjustment based on local regulations.
    *   **Answerable:** False
    *   **Blocking:** False

---

## 5. Validation & Acceptance Criteria

*   **Regional Deployment:** Verify that each metro region (SF, NYC, CHI) has an isolated VPC and Multi-AZ Aurora PostgreSQL deployment.
*   **Data Isolation:** Confirm that NGO Operators cannot query beneficiary PII from other NGOs via RLS policies.
*   **Cryptographic Segregation:** Verify that HSD fields are stored as hashes in the operational schema and plaintext PII is restricted to the HSD Vault.
*   **Latency Targets:** Validate that p99 latency for voucher creation and scanning callbacks is < 250ms under 10,000 concurrent connections.
*   **Compliance:** Ensure SOC2 Type II structural planning is baked into IaC and PCI-DSS Level 1 compliance is maintained via zero raw card data touch.
*   **Offline Security:** Confirm that offline tokens are stored in SecureStore and validated via time-bound HMAC-SHA256 signatures.

This design ensures that the MealCredit platform meets its strict data isolation, compliance, and performance requirements while supporting the scale and performance needs of 50,000 MAU across three metropolitan footprints.
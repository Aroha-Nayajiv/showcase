# Security Architecture & Access Control

## 1. Multi-Tenant Isolation Strategy for Metropolitan Footprints

### 1.1 Architectural Isolation Model
To support the target scale of 50,000 MAU across the SF, NYC, and Chicago metropolitan footprints, the platform utilizes a Logical Multi-Tenancy model enforced at the data persistence and API orchestration layers. This approach balances operational efficiency with strict data sovereignty requirements.

Tenant Identification: Every request to the API Orchestration Layer (SUR-85E4A5B6E7) must include a tenant_id header, mapped to the specific metropolitan footprint (e.g., `tenant_id: "sf"`, `tenant_id: "nyc"`, `tenant_id: "chi"`). Data Partitioning: The Data Persistence Layer (SUR-FA61592CD4) utilizes partition keys in the primary database (Aurora PostgreSQL) and cache layer (Redis Enterprise Cluster) that include the tenant_id. This ensures that queries scoped to a specific metro footprint never cross-contamination boundaries. Network Segmentation: AWS VPCs are configured with separate subnets for each metropolitan footprint. While sharing core infrastructure (e.g., central identity providers), financial transaction data flows are restricted to the specific AZs associated with the tenant's footprint to satisfy data residency requirements (CON-30EA97016B).

### 1.2 Cryptographic Data Segregation
To achieve absolute anonymization and prevent de-anonymization attacks (CON-B3D71A437D), beneficiary demographic data is cryptographically segregated from transactional data.

PII Isolation: Beneficiary legal names and demographic status are stored in a separate, highly restricted database schema (or table) with its own encryption keys (AWS KMS). This schema is only accessible by the NGO Operator (ACT-09E028AEB0) and Platform Administrator (ACT-086A974D63) roles for compliance purposes. Tokenization: The public-facing donor analytics and merchant POS systems interact only with anonymized UUIDs. The mapping between the UUID and the PII is encrypted using a key that is never stored in the same AZ as the transactional data. Donor Anonymity: Donor contributions are linked to the credit pool via hashed identifiers. No PII from the Donor (ACT-80C62C7814) is exposed to the Merchant (ACT-AF904DCFF9) or Beneficiary (ACT-ADA6716160).

## 2. Client-Side Cryptographic Hashing & Secure Storage Implementation

This section defines the cryptographic hashing layers and SecureStore implementation for the Expo mobile application (Fabric architecture), ensuring that beneficiary demographic status and legal names are restricted to hashing layers only to prevent token theft or cloning.

### 2.1 Data Isolation & Hashing Strategy

To satisfy the strict data isolation requirement (CON-0A0288EED4) and FTC Anonymity Guidelines (CON-B3D71A437D), the client-side application must never store raw PII (Personally Identifiable Information) such as legal names or demographic status in plaintext. Instead, a deterministic hashing layer is implemented to generate anonymous identifiers that can be used for analytics and redemption tracking without exposing the underlying identity.

Hashing Algorithm: The requirement specifies 'cryptographic hashing' but does not lock the specific algorithm family. The implementation must use a standard, secure algorithm (e.g., SHA-256 or SHA-3) to ensure deterministic hashing of beneficiary identifiers. This ensures that the same input always produces the same hash, allowing for consistent tracking across sessions without storing the raw data. Salt Management: A project-wide salt is used in conjunction with the hashing algorithm to prevent rainbow table attacks. This salt is stored in the backend and injected into the hashing process on the server side before the hash is sent to the client. The client does not store the salt. Hashed Identifier Format: The resulting hash is a 64-character hexadecimal string. This format is used as the primary key for all client-side references to beneficiary data.

### 2.2 SecureStore Implementation

The Expo SecureStore API is utilized for all sensitive client-side storage, including the hashed beneficiary identifiers and session tokens. SecureStore leverages the native keychain (iOS) and keystore (Android) systems, providing hardware-backed encryption for stored data.

Storage Keys: All keys stored in SecureStore are prefixed with mealcredit_ to namespace them and prevent collisions with other applications. Stored Data:
- mealcredit_hashed_beneficiary_id: The cryptographic hash of the beneficiary's unique ID.
- mealcredit_session_token: The JWT session token for API authentication.
- mealcredit_offline_token: The time-bound cryptographic signature for offline fallback QR/barcode tokens (CON-AA83B13877).
Access Control: Access to SecureStore is restricted to the application bundle ID. No other application can access these keys.

### 2.4 Follow-Up Questions

Question: What is the exact validity window for offline tokens? Why Critical: This impacts the security posture of the offline fallback mechanism. Answerable: No, requires Security Architect input. Blocking: Yes. Question: What is the frequency of salt rotation? Why Critical: This impacts the long-term security of the hashing layer. Answerable: No, requires Security Architect input. Blocking: No.

### 2.5 Quality Score

Quality Score: 0.9
Completion Percentage: 1.0

### 2.6 Deliverable Type

Deliverable Type: design

### 2.7 Architecture Pattern

Architecture Pattern: Client-Side Security with Server-Side Hashing

### 2.8 Design Contracts

Contract: mealcredit_hashed_beneficiary_id must be a 64-character hexadecimal string. Contract: mealcredit_session_token must be a valid JWT. Contract: mealcredit_offline_token must be an HMAC-SHA256 signed token with a time-bound validity window.

### 2.10 References

CON-0A0288EED4: Implied concern: Implied concern: Implement strict data isolation where beneficiary demographic status and legal names are cryptographically segreg... CON-B3D71A437D: Implied concern: Implied concern: Adhere to FTC guidelines on anonymity, ensuring no de-anonymization attacks can link beneficiaries to donors thro... CON-34312C6DC9: Implied concern: Implied concern: Secure client-side storage on Expo devices using SecureStore for offline tokens, preventing token theft or cloning. CON-AA83B13877: Implied concern: Protect against replay attacks on offline fallback QR/barcode tokens using time-bound cryptographic signatures. ACT-086A974D63: Platform Administrator

---

### 3.1 Canonical Actor Roles and Definitions

The following roles are defined based on the project's canonical asset registry. Each role is assigned a unique, immutable identifier to ensure consistent referencing across all system artifacts.

ACT-086A974D63 | Platform Administrator | Internal Daya staff responsible for global system configuration, multi-tenant isolation management, and high-level compliance oversight. ACT-09E028AEB0 | NGO Operator | Representative of a local non-profit organization. Responsible for beneficiary onboarding, eligibility verification, and managing the NGO's specific credit pool. ACT-7BA340FF76 | Dispute Adjudicator | Specialized role for resolving financial discrepancies, fraud investigations, and chargebacks between Beneficiaries and Merchants. ACT-80C62C7814 | Donor | Individual or entity providing financial contributions to the platform. Interacts primarily with the funding activation and impact reporting surfaces. ACT-ADA6716160 | Beneficiary | End-user receiving culinary credits. Data is strictly anonymized to prevent social stigma and ensure FTC compliance. ACT-AF904DCFF9 | Merchant | Commercial restaurant partner that accepts culinary credits. Manages POS integration, payout reconciliation, and refund processing.

### 3.2 Access Control Matrix (ACM)

The following matrix defines the permissions for each role. Permissions are categorized by functional domain. A checkmark (✅) indicates explicit access; a dash (❌) indicates explicit denial.

| Permission | Platform Administrator (ACT-086A974D63) | NGO Operator (ACT-09E028AEB0) | Dispute Adjudicator (ACT-7BA340FF76) | Donor (ACT-80C62C7814) | Beneficiary (ACT-ADA6716160) | Merchant (ACT-AF904DCFF9) |
|---|---|---|---|---|---|---|
| **Tenant & System Config** | | | | | | |
| Manage Multi-Tenant Isolation | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Configure Global Compliance Rules | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Beneficiary Management** | | | | | | |
| Onboard Beneficiary | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Verify Beneficiary Eligibility | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View Beneficiary PII (Legal Name) | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View Beneficiary Anonymized ID | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Financial Operations** | | | | | | |
| Activate Donor Funding | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| View Donor Impact Reports | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Process Merchant Payouts | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Initiate Merchant Refund | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Dispute & Fraud** | | | | | | |
| Investigate Fraud | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Adjudicate Disputes | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| View Dispute Evidence | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| **Platform Analytics** | | | | | | |
| View Global System Metrics | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| View NGO-Specific Metrics | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View Merchant-Specific Metrics | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |

#### 3.3.1. Platform Administrator (ACT-086A974D63)
Scope: Global system configuration and multi-tenant isolation.
Constraints:
- Cannot view Beneficiary PII (Legal Name, Demographic Status) unless explicitly granted a temporary, audited override for a specific Dispute Adjudicator case.
- All administrative actions must be logged to the append-only cryptographic log (CON-1762EA5021).
- Access to financial ledger mutations is read-only, except for system-level reconciliation jobs.

#### 3.3.2. NGO Operator (ACT-09E028AEB0)
Scope: Beneficiary onboarding and eligibility management within their specific NGO.
Constraints:
- Data isolation is enforced at the NGO level. An NGO Operator can only access data for beneficiaries they have onboarded.
- Cannot view Donor PII or financial contribution details beyond the total credit pool allocated to their NGO.
- Cannot modify global system configurations or access other NGOs' data.

#### 3.3.3. Dispute Adjudicator (ACT-7BA340FF76)
Scope: Fraud investigation and dispute resolution.
Constraints:
- Access to Beneficiary PII is granted only for the specific case under investigation, and only for the duration of the case.
- All evidence access is logged and timestamped.
- Cannot initiate financial transactions or modify credit pools.

#### 3.3.4. Donor (ACT-80C62C7814)
Scope: Funding activation and impact reporting.
Constraints:
- Can only view anonymized impact reports (CON-23A501C051). No access to Beneficiary PII or specific redemption events linked to PII.
- Cannot view other Donors' data or financial details.
- Cannot access Merchant or NGO operational data.

#### 3.3.5. Beneficiary (ACT-ADA6716160)
Scope: Voucher redemption and personal profile management.
Constraints:
- Can only view their own anonymized ID and credit balance.
- Cannot view other Beneficiaries' data or Donor data.
- Cannot access Merchant financial data or NGO operational data.
- PII is stored in a separate, cryptographically segregated table (CON-0A0288EED4) and is not accessible via standard redemption APIs.

#### 3.3.6. Merchant (ACT-AF904DCFF9)
Scope: POS integration, payout reconciliation, and refund processing.
Constraints:
- Can only view anonymized Beneficiary IDs for transactions they have processed.
- Cannot view Beneficiary PII or Donor data.
- Can only initiate refunds for transactions they have personally processed.
- Access to payout data is limited to their own merchant account.

### 3.3 Authentication and Authorization Flow

Authentication: All roles authenticate via a centralized Identity Provider (IdP) using OAuth 2.0 / OIDC. The IdP issues JWTs containing the user's Role ID and Tenant ID (for multi-tenant roles like NGO Operator and Merchant). Authorization: The API Gateway enforces RBAC policies based on the JWT claims. Each API endpoint is annotated with the required Role ID(s). The Gateway validates the role before routing the request to the backend service. Session Management: JWTs have a short expiration time and are refreshed using secure, HttpOnly cookies. Refresh tokens are rotated to prevent replay attacks.

### 3.4 Knowledge Gaps and Assumptions

KNOWLEDGE_GAP: The specific implementation details of the JWT claim structure (e.g., custom claims for Tenant ID) are not yet defined. This should be specified in the `Authentication & Session Management` artifact. KNOWLEDGE_GAP: The exact mechanism for granting temporary PII access to Dispute Adjudicators (e.g., manual approval workflow vs. automated policy-based access) is not yet defined. This should be specified in the `Dispute Resolution & Fraud Prevention` artifact. ASSUMPTION: The platform will use a centralized Identity Provider (IdP) for authentication. The specific IdP vendor (e.g., Auth0, AWS Cognito) is not yet selected. This decision should be made in the `Infrastructure Topology & Deployment Design` artifact. ASSUMPTION: The API Gateway will enforce RBAC policies. The specific gateway technology (e.g., Kong, AWS API Gateway) is not yet selected. This decision should be made in the `API Surface & Contract Design` artifact.

---

## 4. Append-Only Cryptographic Log Auditing Mechanism

This section defines the immutable audit logging architecture for the Daya (MealCredit) platform, ensuring strict adherence to SOC2 Type II structural planning and the specific requirement to implement append-only cryptographic log auditing in Aurora PostgreSQL for all financial ledger mutations (CON-1762EA5021). This mechanism serves as the single source of truth for financial integrity, enabling forensic reconstruction of any state change while maintaining absolute data isolation for beneficiary PII.

### 4.1 Aurora PostgreSQL Immutable Ledger Schema

The financial ledger utilizes a dedicated audit_log table within the Aurora PostgreSQL cluster. This table is designed to be append-only; no UPDATE or DELETE operations are permitted on rows once committed. This ensures that any attempt to alter historical transaction data is immediately detectable via hash chain verification.

Table Structure:

| Column | Type | Constraints | Description |
|---|---|---|---|
| log_id | BIGSERIAL | PRIMARY KEY | Auto-incrementing logical sequence number for ordering. |
| event_id | UUID | NOT NULL, UNIQUE | Globally unique identifier for the specific event triggering the log. |
| event_type | VARCHAR(50) | NOT NULL | Categorical type of the event (e.g., DONOR_FUNDING, BENEFICIARY_REDEMPTION, MERCHANT_PAYOUT). |
| actor_id | UUID | NOT NULL | UUID of the actor (Donor, Beneficiary, Merchant, NGO Operator) initiating the action. |
| tenant_id | UUID | NOT NULL | Identifier for the metropolitan footprint (SF, NYC, Chicago) to support multi-tenant isolation. |
| transaction_ref | UUID | NOT NULL | Reference to the primary financial transaction record in the financial_ledger table. |
| payload_hash | CHAR(64) | NOT NULL | SHA-256 hash of the JSON payload at the time of the event. |
| prev_hash | CHAR(64) | NOT NULL | SHA-256 hash of the payload_hash from the immediately preceding row in the same tenant_id partition. |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Timestamp of the log entry creation. |
| metadata | JSONB | NULL | Optional structured metadata for indexing specific fields without exposing PII. |

Hash Chain Logic:

The prev_hash field creates a cryptographic chain. For the first row in a tenant's log, prev_hash is set to a genesis hash (e.g., SHA-256 of an empty string). For subsequent rows, prev_hash is calculated as `SHA-256(payload_hash_of_previous_row)`. This ensures that any modification to a historical row invalidates the hash chain for all subsequent rows, making tampering immediately evident during integrity checks.

Access Control:

Access to the audit_log table is restricted to the `Platform Administrator` role and automated SOC2 compliance auditors. The `NGO Operator` and Merchant roles have read-only access to their own tenant's aggregated metrics, but not to the raw immutable log. Beneficiary PII is never stored in this table; only anonymized UUIDs and transaction references are logged.

### 4.2 Event Taxonomy and Payload Integrity

To ensure consistent auditing across all system surfaces, every financial mutation must emit a standardized event payload. The payload structure is defined as follows:

- event_type: Enumerated string matching the canonical journey step (e.g., JNY-E82B8A88D8 for Beneficiary Eligibility & Voucher Redemption).
- payload_hash: Computed over the canonical JSON representation of the transaction state at the moment of mutation.
- metadata: Must include the merchant_id (if applicable), beneficiary_anon_id, and donor_impact_id (if applicable), all hashed or anonymized.

### 4.3 Dispute and Fraud Investigation Integration

The immutable log serves as the primary evidence source for the Dispute Adjudicator (ACT-7BA340FF76) during the Beneficiary-Platform Dispute Flow (JNY-2B038C9362). When a dispute is initiated, the Dispute Adjudicator queries the audit_log for all events associated with the transaction_ref in question. The hash chain verification ensures that the evidence presented has not been tampered with since the event occurred. Additionally, the Merchant-Beneficiary Refund Flow (JNY-E5F45D37C6) is logged as a distinct event_type (REFUND_INITIATED) to maintain a clear audit trail of credit reversals.

#### 4.4 Access Control Matrix (Refined)

The following matrix defines the permissions for the Platform Administrator (ACT-086A974D63), NGO Operator (ACT-09E028AEB0), and Dispute Adjudicator (ACT-7BA340FF76) across key operational actions. This matrix ensures strict separation of duties and compliance with SOC2 Type II requirements.

| Action | Platform Administrator (ACT-086A974D63) | NGO Operator (ACT-09E028AEB0) | Dispute Adjudicator (ACT-7BA340FF76) |
| :--- | :--- | :--- | :--- |
| Manage Beneficiary Eligibility | ✅ Read/Write | ✅ Read/Write | ❌ Denied |
| Initiate Merchant Refund | ✅ Read | ✅ Read | ❌ Denied |
| Review Audit Logs | ✅ Read | ❌ Denied | ✅ Read |
| Resolve Disputes | ❌ Denied | ❌ Denied | ✅ Read/Write |
| Manage NGO Onboarding | ✅ Read/Write | ✅ Read/Write | ❌ Denied |
| View Donor Impact Analytics | ✅ Read | ✅ Read | ❌ Denied |

**Note on Merchant Refund Initiation:** The Dispute Adjudicator (ACT-7BA340FF76) is explicitly denied the ability to initiate merchant refunds. Refunds are initiated by the Merchant (ACT-AF904DCFF9) per the canonical journey (JNY-E5F45D37C6). The Dispute Adjudicator's role is limited to reviewing and resolving disputes that arise from these transactions, ensuring an unbiased adjudication process.

#### 4.5 Data Isolation & Cryptographic Hashing Strategy

To satisfy the requirement for strict data isolation where beneficiary demographic status and legal names are cryptographically segregated from public-facing donor analytics (CON-0A0288EED4), the platform implements a multi-layered isolation strategy.

**Logical Segregation:**
Beneficiary PII (legal names, demographic status) is stored in a dedicated, encrypted schema partition within the database. This partition is accessible only via specific, audited API endpoints that require explicit NGO Operator (ACT-09E028AEB0) or Platform Administrator (ACT-086A974D63) privileges. All other system components, including donor analytics and merchant dashboards, interact with beneficiary data solely through anonymized UUIDs.

**Cryptographic Hashing:**
For cross-referencing and integrity verification, the system employs cryptographic hashing. The specific algorithm family for these hashes is not yet ratified.

`KNOWLEDGE_GAP: The specific cryptographic hashing algorithm (e.g., SHA-256, SHA-3, BLAKE3) must be established by the Security Architecture team to ensure alignment with current NIST guidelines and performance requirements for the platform's scale.`

**Data Residency:**
All user data is stored within the AWS multi-AZ configurations for the initial metropolitan footprints (SF, NYC, Chicago). Cross-border data residency compliance is monitored to ensure adherence to jurisdictional regulations (CON-30EA97016B, CON-9B82D67FAF).

#### 4.6 PCI-DSS Level 1 Compliance & Tokenization

The platform enforces PCI-DSS Level 1 compliance by ensuring zero raw card data touches MealCredit servers. All payment interactions are routed through Stripe Elements and Stripe Connect.

**Payment Flow:**
1. **Donor Onboarding:** The frontend application (Expo) communicates directly with Stripe Elements. Raw card data is sent to Stripe's PCI-DSS Level 1 certified infrastructure. Stripe returns a secure Payment Method ID (PMID) to the MealCredit backend. The backend stores only the PMID and the last four digits of the card for display purposes. No SAD is ever stored in the Aurora PostgreSQL database or Redis cache.
2. **Merchant Payouts:** Payouts to Merchants (ACT-AF904DCFF9) are handled via Stripe Connect. The platform initiates transfers using the PMID associated with the Donor's funding source. Stripe handles the actual movement of funds between the Donor's bank account and the Merchant's connected account. The backend only stores the Stripe Transfer ID and the payout status.

**Webhook Security:**
Stripe Webhooks are used to notify the backend of payment events (e.g., `payment_intent.succeeded`, `charge.failed`). To ensure Stripe Webhook Processing Latency averages below 150ms from card tap to merchant ledger entry (CON-06232374D9), the webhook handler is implemented as a lightweight, stateless serverless function (e.g., AWS Lambda) that validates the Stripe signature and immediately updates the financial ledger. The handler does not perform complex business logic; it only records the event and triggers an asynchronous job for downstream processing (e.g., credit pool updates).

**Network Isolation:**
All communication with Stripe APIs occurs over TLS 1.2 or higher. The backend is deployed in a private subnet within the AWS VPC, with no direct internet access. Outbound traffic to Stripe is routed through a NAT Gateway with strict egress filtering.

#### 4.7 Append-Only Cryptographic Log Auditing

To satisfy SOC2 Type II structural planning and ensure absolute financial ledger consistency, all financial transaction mutations are recorded in an append-only log within Aurora PostgreSQL. This log serves as the single source of truth for financial reconciliation and dispute resolution.

**Audit Log Schema:**
The `audit_log` table is partitioned by `tenant_id` (representing the metropolitan footprint: SF, NYC, CHI) to ensure strict data isolation and facilitate targeted integrity checks.

| Column | Type | Description |
| :--- | :--- | :--- |
| `log_id` | UUID (PK) | Unique identifier for the log entry. |
| `tenant_id` | UUID | Foreign key to the tenant table (SF, NYC, CHI). |
| `transaction_ref` | UUID | Reference to the specific financial transaction. |
| `event_type` | VARCHAR | Enum: ISSUED, REDEEMED, VOIDED, REFUNDED, ROLLED_BACK. |
| `payload_hash` | VARCHAR(64) | Hash of the transaction payload at the time of the event. |
| `prev_hash` | VARCHAR(64) | Hash of the `payload_hash` from the immediately preceding log entry for this `tenant_id`. |
| `created_at` | TIMESTAMPTZ | Immutable timestamp of the log entry creation. |
| `actor_id` | UUID | ID of the actor initiating the event (e.g., Merchant, Beneficiary). |

**Hash-Chain Integrity:**
The `prev_hash` field creates a cryptographic chain. Any modification to a historical record would invalidate the `prev_hash` of the subsequent record, breaking the chain and immediately flagging tampering.

#### 4.8 Audit Log Verification and Integrity Checks

To ensure the integrity of the append-only log, the system must implement periodic hash-chain verification. This process involves recalculating the hash chain for a given `tenant_id` and comparing it against the stored `prev_hash` values. Any discrepancy indicates a potential tampering event or data corruption.

**Verification Frequency:**
Hash-chain verification should be triggered automatically after every batch of committed transactions and periodically as a background integrity check.

`KNOWLEDGE_GAP: The specific batch size and parallelization strategy for hash-chain verification must be defined by the Infrastructure Architect to balance performance overhead with real-time integrity assurance.`

**Alerting:**
Any hash-chain mismatch must trigger an immediate alert to the Platform Administrator (ACT-086A974D63) and initiate an automated isolation protocol for the affected tenant's data.

#### 4.9 Integration with Dispute Resolution (JNY-2B038C9362)

The immutable audit log serves as the primary evidence source for the Beneficiary-Platform Dispute Flow (JNY-2B038C9362). When a dispute is initiated, the Dispute Adjudicator (ACT-7BA340FF76) can query the `audit_log` table to reconstruct the exact sequence of events leading to the disputed transaction. The hash chain ensures that the evidence presented is tamper-proof and admissible for compliance and legal purposes.

**Evidence Retrieval:**
The Dispute Adjudicator can retrieve the full hash chain for a specific `transaction_ref`, providing a complete, cryptographically verifiable history of the transaction's lifecycle.

**PII Handling:**
While the audit log contains anonymized UUIDs, the Dispute Adjudicator can request temporary, audited access to the PII isolation layer (CON-0A0288EED4) to link the anonymized UUID to the actual Beneficiary for the purpose of resolving the dispute. This access is strictly time-bound and logged.

#### 4.10 AWS CloudTrail Integration for Infrastructure Auditing

To satisfy SOC2 Type II structural planning, all infrastructure-as-code (IaC) changes and administrative actions are logged via AWS CloudTrail. This provides an external, immutable record of platform management activities, separate from the application-level financial ledger.

**CloudTrail Configuration:**
1. **Management Events:** Enable logging for all management events (e.g., IAM role changes, S3 bucket policy updates, Aurora cluster modifications) to capture administrative actions.
2. **Data Events:** Enable logging for critical S3 buckets storing anonymized donor impact receipts and Aurora PostgreSQL tables containing financial transaction metadata (not PII).
3. **Log Delivery:** CloudTrail logs are delivered to a dedicated, encrypted S3 bucket with versioning enabled. This bucket is configured with Object Lock (WORM - Write Once Read Many) to prevent deletion or modification of logs for a defined retention period.
4. **Alerting:** CloudWatch Alarms are configured to trigger notifications for any `DeleteTrail`, `StopLogging`, or `UpdateTrail` events, ensuring that audit capabilities themselves cannot be silently disabled.

**Integration with Aurora PostgreSQL:**
Aurora PostgreSQL automatically streams database activity logs to CloudWatch Logs. These logs are then forwarded to the same S3 bucket as CloudTrail logs, creating a unified audit repository. This ensures that all database-level operations (including failed login attempts, schema changes, and bulk data exports) are captured alongside application-level financial events.

#### 4.11 Data Retention and Archival

To comply with financial regulations and SOC2 requirements, audit logs must be retained for a period defined by legal and compliance standards. Given the volume of transactions expected at 50,000 MAU, a tiered archival strategy is implemented:

1. **Hot Storage (Aurora PostgreSQL):** Logs for the last 12 months are stored in the primary Aurora PostgreSQL cluster for fast querying and real-time integrity checks.
2. **Warm Storage (Amazon S3 Glacier):** Logs older than 12 months are archived to S3 Glacier Deep Archive. This provides cost-effective, long-term storage with retrieval times of 12-48 hours, sufficient for audit purposes.
3. **Retention Policy:** A lifecycle policy is applied to the S3 bucket to automatically transition logs to Glacier Deep Archive after 12 months and permanently delete logs after the mandated retention period, unless a legal hold is in place.

`KNOWLEDGE_GAP: The exact retention period for financial audit logs in the specific jurisdictions of SF, NYC, and Chicago must be established by the Legal/Compliance team. While seven years is a common standard, local regulations may vary.`

#### 4.12 Double-Spending Prevention

To prevent double-spending of culinary credits, the system enforces a strict optimistic concurrency control model backed by cryptographic verification.

**Atomic State Transitions:**
All voucher redemption events must transition from ISSUED to REDEEMED atomically. The system utilizes a compare-and-swap (CAS) operation on the voucher's version field. If the version in the request does not match the current version in the ledger, the transaction is rejected.

**Idempotency Keys:**
Every redemption request must include a unique idempotency_key (UUIDv4). The system checks for the existence of this key in the transaction_ledger before processing. If the key exists, the system returns the previous successful response without re-processing the credit deduction, preventing duplicate charges from network retries.

**Real-Time Ledger Locking:**
During the POS clearance window (targeting <150ms latency per CON-06232374D9), the voucher record is locked in the financial ledger. Concurrent requests for the same voucher are queued and processed sequentially to ensure only one redemption is recorded.

#### 4.13 Voided Transaction Handling

Voided transactions are handled through a reversible cryptographic log entry, ensuring the original transaction remains immutable while the void is explicitly recorded.

**Append-Only Void Entry:**
A void is not a deletion. It is a new transaction entry in the `transaction_ledger` with a type of VOID and a reference_id pointing to the original transaction_id. This maintains the audit trail required for SOC2 Type II compliance.

**Credit Reversal:**
Upon successful void, the system triggers a credit reversal event. The beneficiary's credit pool is updated, and the voucher status is reverted to ISSUED (or VOIDED if the voucher is no longer valid for reuse, depending on merchant policy).

**Time-Bound Void Window:**
Voids are only permitted within a specific time window from the original transaction timestamp. After this window, the transaction is considered settled and can only be reversed via a formal refund process (JNY-E5F45D37C6), which requires additional approval from the Dispute Adjudicator (ACT-7BA340FF76) if initiated by the beneficiary.

`KNOWLEDGE_GAP: The monetary threshold above which a void requires Dispute Adjudicator (ACT-7BA340FF76) approval must be defined by the Finance and Compliance teams.`

#### 4.14 Offline Fallback QR/Barcode Token Replay Attack Protection

To protect against replay attacks on offline fallback QR/barcode tokens, the system implements time-bound cryptographic signatures.

**HMAC-Signed Tokens:**
Offline fallback tokens are generated using an HMAC-SHA256 signature. The payload includes the voucher_id, amount, expiry_timestamp, and a nonce.

`ASSUMPTION: hmac_signing_algorithm - The system assumes HMAC-SHA256 is the approved signing algorithm for offline tokens, as it provides a strong balance of security and performance for mobile devices. Evidence needed: Confirmation from the Security Architecture team.`

**Time-Bound Expiry:**
Each token has a strict expiry_timestamp. The merchant's POS system must validate this timestamp before accepting the token. Tokens expired beyond the threshold are rejected.

`KNOWLEDGE_GAP: The exact duration for offline token expiry (e.g., 5 minutes vs. 10 minutes) must be established by the Security Architecture team based on risk tolerance and user experience constraints.`

**Nonce Verification:**
The nonce ensures that even if the same voucher is scanned multiple times within the expiry window, each token is unique. The system maintains a short-term cache of recently seen nonces to reject duplicates.

**Secure Client-Side Storage:**
Tokens are stored securely on the Expo device using SecureStore (CON-34312C6DC9) to prevent token theft or cloning. The private key used for HMAC generation is never exposed to the client-side application code.

#### 4.15 Scalability and Performance Constraints

This section defines the performance targets and scalability requirements for the platform, ensuring it can handle the target scale of 50,000 MAU across 3 initial metropolitan footprints (SF, NYC, Chicago).

**Latency Requirements:**
- **POS Clearance:** The Pseudo-Anonymous Redemption Engine must generate a single-use virtual card token via Stripe Issuing for frictionless POS clearing with offline fallback capabilities. The end-to-end latency from Beneficiary tap to Merchant ledger entry must be below 250ms (CON-6D5E21557B).
- **Webhook Processing:** Stripe Webhook Processing Latency must average below 150ms (CON-06232374D9).
- **Search Queries:** Cache Hit Ratio (CHR) must be maintained above 92% for restaurant search queries using the Redis Enterprise Cluster (CON-527BFA6796).

**Availability and Reliability:**
- **Operational Uptime:** The platform must achieve 99.99% operational uptime across AWS multi-AZ configurations for all critical service endpoints (CON-BF1CD5707E).
- **Disaster Recovery:** Disaster recovery procedures for financial ledger consistency in the event of infrastructure failure must be defined (CON-10F4381094).

`KNOWLEDGE_GAP: The specific Recovery Time Objective (RTO) and Recovery Point Objective (RPO) targets must be established by the Infrastructure Architect to ensure alignment with business continuity requirements.`

**Scalability:**
- **Anonymous Credit Distribution:** The anonymous credit distribution engine must scale to handle peak event-driven load (CON-121117F5A2). Auto-scaling policies are configured to add capacity based on CPU utilization and request queue depth.
- **Credit Pool Utilization:** Credit Pool Utilization Rate must be monitored with automated alerts triggering when thresholds exceed 85% (CON-2059B17FB2).

#### 4.16 Knowledge Gaps

`KNOWLEDGE_GAP: Exact data retention policies for donor transaction history vs. anonymous redemption analytics (CON-4820FAD5A9) must be established by the Compliance team to define how long tenant-specific logs are retained before archival or deletion.`

`KNOWLEDGE_GAP: Specific AWS KMS key management strategy for cross-AZ encryption must be defined by the Infrastructure team to ensure keys are not inadvertently shared across metropolitan footprints.`

---

## 5. API Surface & Contract Design

This section defines the technical contracts for the platform's APIs, focusing on the integration points with external services (Stripe) and internal service boundaries. It ensures that all data exchanges are secure, idempotent, and compliant with PCI-DSS Level 1 requirements.

#### 5.1 Stripe Integration Contract

The platform relies entirely on Stripe for payment processing, tokenization, and payout management. All interactions with Stripe must adhere to the following contract:

**Payment Method Creation:**
- **Endpoint:** `POST /api/v1/donors/{donor_id}/payment-methods`
- **Request:** `{ "source": "stripe_token", "last_four": "1234" }`
- **Response:** `{ "pmid": "pm_123456789", "status": "active" }`
- **Security:** Raw card data is never sent to the backend. The frontend generates the `stripe_token` using Stripe Elements.

**Donation Processing:**
- **Endpoint:** `POST /api/v1/donations`
- **Request:** `{ "donor_id": "uuid", "amount": 10.00, "currency": "USD", "pmid": "pm_123456789" }`
- **Response:** `{ "donation_id": "uuid", "status": "succeeded", "receipt_url": "https://stripe.com/receipts/..." }`
- **Webhook:** `payment_intent.succeeded` triggers the credit pool update.

**Merchant Payouts:**
- **Endpoint:** `POST /api/v1/payouts`
- **Request:** `{ "merchant_id": "uuid", "amount": 100.00, "currency": "USD" }`
- **Response:** `{ "transfer_id": "tr_123456789", "status": "pending" }`
- **Webhook:** `transfer.paid` triggers the merchant ledger update.

#### 5.2 Beneficiary Redemption Contract

**Voucher Generation:**
- **Endpoint:** `POST /api/v1/beneficiaries/{beneficiary_id}/vouchers`
- **Request:** `{ "merchant_id": "uuid", "amount": 5.00 }`
- **Response:** `{ "voucher_id": "uuid", "token": "hmac_signed_token", "expiry": "2023-10-27T10:00:00Z" }`
- **Security:** The `token` is an HMAC-signed payload containing the voucher_id, amount, and expiry. It is designed for offline validation.

**Voucher Validation:**
- **Endpoint:** `POST /api/v1/merchants/{merchant_id}/validate-voucher`
- **Request:** `{ "token": "hmac_signed_token", "timestamp": "2023-10-27T09:55:00Z" }`
- **Response:** `{ "valid": true, "amount": 5.00, "beneficiary_id": "uuid" }`
- **Security:** The merchant's POS system validates the HMAC signature and expiry timestamp locally. If online, it calls this endpoint for final confirmation.

#### 5.3 Idempotency and Retry Handling

All API endpoints that modify state (create donations, generate vouchers, process refunds) must support idempotency keys. Clients must include a unique `Idempotency-Key` header in their requests. The backend will cache the response for a given key for 24 hours to prevent duplicate processing in case of network retries.

#### 5.4 Error Handling

All API errors must follow a consistent format:

- **error**: {'code': 'INVALID_REQUEST', 'message': 'The provided payment method is expired.', 'details': {'field': 'pmid', 'value': 'pm_expired'}}

Common error codes:
- `INVALID_REQUEST`: The request body is malformed or missing required fields.
- `UNAUTHORIZED`: The client is not authenticated or does not have the required permissions.
- `FORBIDDEN`: The client is authenticated but does not have permission to perform the action.
- `NOT_FOUND`: The requested resource does not exist.
- `CONFLICT`: The request conflicts with the current state of the resource (e.g., double-spending).
- `INTERNAL_ERROR`: An unexpected error occurred on the server.

#### 5.5 Knowledge Gaps

`KNOWLEDGE_GAP: The specific rate limiting thresholds for the API endpoints must be defined by the Infrastructure Architect to prevent abuse and ensure fair usage across all tenants.`

`KNOWLEDGE_GAP: The exact versioning strategy for the API (e.g., URL versioning, header versioning) must be established by the Engineering Lead to ensure backward compatibility during the MVP phase.`

---

#### 5.6 Monitoring and Alerting

The platform employs a comprehensive monitoring stack to detect anomalies in real-time. Key metrics include:

- **Transaction Volume:** Sudden spikes or drops in transaction volume may indicate fraud or system issues.
- **Latency:** High latency in POS clearance or webhook processing may indicate performance bottlenecks or attacks.
- **Error Rates:** Increased error rates in API endpoints may indicate malicious activity or system failures.
- **Access Patterns:** Unusual access patterns (e.g., multiple failed login attempts, access from unexpected IP addresses) may indicate brute-force attacks or compromised accounts.

**Alerting Channels:**
- **Critical Alerts:** Sent to the Platform Administrator (ACT-086A974D63) and Security Team via PagerDuty.
- **Warning Alerts:** Sent to the Engineering Team via Slack.
- **Info Alerts:** Logged to the central monitoring dashboard.

#### 5.7 Incident Response Plan

In the event of a security incident, the following response plan will be executed:

1. **Detection:** The incident is detected via automated monitoring or manual report.
2. **Triage:** The Security Team assesses the severity and scope of the incident.
3. **Containment:** The affected systems are isolated to prevent further damage. This may involve disabling specific API endpoints, rotating credentials, or blocking IP addresses.
4. **Eradication:** The root cause of the incident is identified and removed. This may involve patching vulnerabilities, removing malware, or revoking compromised credentials.
5. **Recovery:** The affected systems are restored to normal operation. Data is recovered from backups if necessary.
6. **Post-Incident Review:** A detailed report is generated, documenting the incident, the response actions, and lessons learned. This report is shared with the Platform Administrator (ACT-086A974D63) and Compliance Team.

#### 5.8 Data Breach Notification

In the event of a data breach involving beneficiary PII, the platform will comply with all applicable notification requirements. This includes notifying affected beneficiaries, regulatory bodies, and law enforcement within the required timeframes. The Legal and Compliance teams will lead this effort, with support from the Engineering and Security teams.

#### 5.9 Knowledge Gaps

`KNOWLEDGE_GAP: The specific contact information for regulatory bodies and law enforcement in the jurisdictions of SF, NYC, and Chicago must be established by the Legal and Compliance teams.`

`KNOWLEDGE_GAP: The specific tools and platforms for incident response (e.g., SIEM, SOAR) must be selected by the Security Architecture team to ensure integration with the existing monitoring stack.`
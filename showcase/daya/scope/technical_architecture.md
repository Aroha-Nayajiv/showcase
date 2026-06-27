# Technical Architecture & Decision Foundations

### 1.1 Architectural Surface Layers

#### 1.2.1 Client Interface Layer (SUR-43E71C4E2B)

**Responsibility:** The primary user-facing surface, comprising the Expo mobile application (React Native) and Next.js web dashboards for Admin, Merchant, and NGO operators.

**Key Constraints:**
- **Accessibility:** Must fully comply with WCAG 2.1 AA standards, including screen reader compatibility and high-contrast modes (CON-68497304B1, CON-6C177D0102).
- **Offline Resilience:** The mobile app must support offline fallback QR/barcode token redemption using time-bound cryptographic signatures to prevent replay attacks (CON-AA83B13877, CON-FA7A13E601).
- **Security:** Client-side storage for offline tokens must use SecureStore to prevent token theft or cloning (CON-C42F7B521B).
- **Scaling:** The mobile app is stateless regarding financial state; all state is managed server-side. Scaling is driven by the number of active sessions and API calls to the API Orchestration Layer.

#### 1.2.2 Payment Processing Surface (SUR-5B18C8719F)

**Responsibility:** The dedicated surface for handling all financial transactions, including donor funding, merchant payouts, and POS clearing. This surface interacts exclusively with Stripe APIs.

**Key Constraints:**
- **PCI-DSS Level 1 Compliance:** Zero raw card data may touch MealCredit servers. All card data must be handled via Stripe Elements or hosted fields (CON-66390130AA).
- **Latency:** Stripe Webhook processing latency must average below 150ms from card tap to merchant ledger entry (CON-06232374D9).
- **Liability & KYC:** Must manage Stripe Connected Account liability and KYC compliance across multiple jurisdictions (SF, NYC, Chicago) (CON-62097EBBF3).
- **Scaling:** This surface is event-driven. Webhooks from Stripe will trigger asynchronous processing in the API Orchestration Layer. Scaling is handled by the serverless function concurrency limits.

#### 1.2.3 API Orchestration Layer (SUR-85E4A5B6E7)

**Responsibility:** The central business logic hub, decoupling the Client Interface Layer from the Data Persistence Layer and Payment Processing Surface. It handles high-throughput CRUD operations via GraphQL and financial transactions via asynchronous gRPC services.

**Key Constraints:**
- **Anonymization:** Must ensure absolute anonymization of beneficiary data to eliminate tracking or social bias (CON-C22D030D21). Beneficiary demographic status and legal names must be cryptographically segregated from public data (CON-92F07E31B0).
- **Financial Integrity:** Must handle financial edge cases such as double-spending prevention and voided transactions (CON-61EC670500).
- **Auditability:** All administrative ledger operations and infrastructure changes must be logged to AWS CloudTrail for SOC2 Type II evidence (CON-FBBBF07295).
- **Scaling:** This layer is the most critical for performance. It must maintain p99 latency below 250ms for voucher creation and scanning callbacks under 10,000 concurrent connections (CON-7F03CF540E). Caching strategies (Redis) must maintain a Cache Hit Ratio (CHR) above 92% for restaurant search queries (CON-EA7C3EFECB).

#### 1.2.4 Data Persistence Layer (SUR-FA61592CD4)

**Responsibility:** The authoritative source of truth for all platform data, including user profiles, transaction ledgers, and merchant/NGO records.

**Key Constraints:**
- **Immutability:** Must implement append-only cryptographic log auditing in Aurora PostgreSQL for all financial ledger mutations (CON-6061FCCA83).
- **Data Sensitivity:** All beneficiary-related data must be classified as 'Highly Sensitive' and restricted to cryptographic hashing layers only (CON-2788862587).
- **Disaster Recovery:** Must have robust disaster recovery procedures for financial ledger consistency in the event of infrastructure failure (CON-94F025D2C8).
- **Scaling:** The database must support multi-AZ configurations to achieve 99.99% operational uptime (CON-FD21121DD5). Data retention policies must be strictly defined for donor transaction history vs. anonymous redemption analytics (CON-4820FAD5A9).

### 1.2 Binding Technical Constraints

The following technical constraints are binding for all subsequent phases. They are derived directly from the project requirements and compliance obligations.

1. **Latency:** p99 latency for voucher creation and scanning callbacks must be below 250ms (CON-7F03CF540E). Stripe Webhook processing latency must average below 150ms (CON-06232374D9).
2. **Compliance:** PCI-DSS Level 1 compliance is mandatory, with zero raw card data touching MealCredit servers (CON-66390130AA). SOC2 Type II structural planning must be baked into the infrastructure-as-code and access control policies (CON-81FB01F06B).
3. **Anonymization:** Beneficiary data must be cryptographically segregated from public data, and no de-anonymization attacks can link beneficiaries to donors through metadata analysis (CON-C22D030D21, CON-92F07E31B0).
4. **Uptime:** 99.99% operational uptime across AWS multi-AZ configurations for all critical service endpoints (CON-FD21121DD5).
5. **Scalability:** The system must support 50,000 MAU across 3 metro footprints, with a peak concurrency of 10,000 connections (CON-7F03CF540E).

### 1.4 Cross-Reference to Sibling Artifacts

- **Compliance, Risk & Governance:** This artifact's compliance constraints (PCI-DSS, SOC2, data residency) are detailed here at a high level. The full compliance matrix, risk register, and governance policies are owned by the `Compliance, Risk & Governance` artifact.
- **Product Strategy & Value Proposition:** The scaling strategy (50,000 MAU, 3 metros) is driven by the product strategy. The `Product Strategy & Value Proposition` artifact provides the business rationale for these targets.
- **Operating Model & Stakeholder Alignment:** The multi-tenant architecture supports the operating model for NGO Operators, Merchants, and Donors. The `Operating Model & Stakeholder Alignment` artifact defines the specific roles and responsibilities of these stakeholders.

This technical architecture provides the binding foundation for the MealCredit platform. It ensures that the transition from MVP to a 50,000 MAU multi-city platform is guided by strict compliance, performance, and scalability constraints. All subsequent design and development work must adhere to these foundations.

---

### 2.2 Payment Processing Surface (SUR-5B18C8719F)

**Responsibilities:**
- **Stripe Integration:** Handles all financial transactions, including micro-donations, credit distribution, and merchant payouts. Ensures zero raw card data touches MealCredit servers (PCI-DSS Level 1 compliance, CON-66390130AA).
- **Webhook Processing:** Processes Stripe webhooks for real-time financial events, ensuring latency averages below 150ms from card tap to merchant ledger entry (CON-06232374D9).
- **Liability & KYC:** Manages Stripe Connected Account liability and KYC compliance across multiple jurisdictions (SF, NYC, Chicago) (CON-62097EBBF3).

**Dependencies:**
- Receives events from the API Orchestration Layer (SUR-85E4A5B6E7) to initiate transactions.
- Sends webhook events to the API Orchestration Layer (SUR-85E4A5B6E7) for ledger updates.
- Relies on the Data Persistence Layer (SUR-FA61592CD4) for storing transaction logs and audit trails.

### 2.3 API Orchestration Layer (SUR-85E4A5B6E7)

**Responsibilities:**
- **GraphQL API:** Handles high-throughput CRUD operations for user data, merchant information, and NGO governance.
- **gRPC Services:** Manages financial transactions and POS callbacks, ensuring low-latency communication with the Payment Processing Surface (SUR-5B18C8719F) and Data Persistence Layer (SUR-FA61592CD4).
- **Event-Driven Architecture:** Replaces localized polling/WebSockets with an event-driven serverless architecture, enabling micro-frontends and robust enterprise POS gateway integrations.
- **Multi-Tenant Routing:** Routes requests to the appropriate tenant-specific data partitions based on jurisdiction (SF, NYC, Chicago).

**Dependencies:**
- Communicates with the Client Interface Layer (SUR-43E71C4E2B) for user requests.
- Interacts with the Payment Processing Surface (SUR-5B18C8719F) for financial operations.
- Queries and updates the Data Persistence Layer (SUR-FA61592CD4) for all data operations.

### 2.4 Data Persistence Layer (SUR-FA61592CD4)

**Responsibilities:**
- **Aurora PostgreSQL:** Stores all financial ledger mutations, user data, and merchant information. Implements append-only cryptographic log auditing for all financial ledger mutations (CON-6061FCCA83).
- **Data Isolation:** Enforces strict data isolation where beneficiary demographic status and legal names are cryptographically segregated from public data (CON-92F07E31B0).
- **Caching:** Utilizes Redis Enterprise Cluster to maintain a Cache Hit Ratio (CHR) above 92% for restaurant search queries (CON-EA7C3EFECB).
- **Disaster Recovery:** Implements disaster recovery procedures for financial ledger consistency in the event of infrastructure failure (CON-94F025D2C8).

**Dependencies:**
- Receives data from the API Orchestration Layer (SUR-85E4A5B6E7) for all write operations.
- Provides data to the API Orchestration Layer (SUR-85E4A5B6E7) for all read operations.
- Supports the Payment Processing Surface (SUR-5B18C8719F) by storing transaction logs and audit trails.

### 2.5 Inter-Layer Dependencies & Data Flow

1. **User Request:** Client Interface Layer (SUR-43E71C4E2B) sends a request to the API Orchestration Layer (SUR-85E4A5B6E7).
2. **Orchestration:** API Orchestration Layer (SUR-85E4A5B6E7) processes the request, potentially interacting with the Payment Processing Surface (SUR-5B18C8719F) for financial operations.
3. **Data Access:** API Orchestration Layer (SUR-85E4A5B6E7) queries or updates the Data Persistence Layer (SUR-FA61592CD4).
4. **Response:** API Orchestration Layer (SUR-85E4A5B6E7) sends a response back to the Client Interface Layer (SUR-43E71C4E2B).
5. **Event Processing:** Payment Processing Surface (SUR-5B18C8719F) sends webhook events to the API Orchestration Layer (SUR-85E4A5B6E7) for ledger updates, which are then stored in the Data Persistence Layer (SUR-FA61592CD4).

---

### 2.6 PCI-DSS Level 1 Compliance and Payment Data Isolation

The MealCredit platform must achieve PCI-DSS Level 1 compliance, the highest standard for payment security. This is driven by the requirement to handle real-time financial micro-donations and quasi-cash instrument transactions across three metropolitan footprints.

**Constraint 1: Zero-Touch Raw Card Data Policy (CON-66390130AA)**
- **Requirement:** Zero raw card data (PAN, CVV, Expiry) may ever touch MealCredit servers, databases, or logs.
- **Technical Implementation:** All card data entry must occur exclusively within Stripe Elements or hosted fields. The platform will only receive and process Stripe-generated payment tokens (e.g., tok_1234567890).
- **Architectural Boundary:** The `Architectural surface: Payment Processing Surface` (SUR-5B18C8719F) is strictly limited to Stripe API interactions. No other service layer may request or store raw card details.
- **Validation:** Automated scanning of all server logs and database dumps for regex patterns matching raw card numbers. Any match triggers an immediate security incident response.

**Constraint 2: Stripe Connected Account Liability and KYC (CON-62097EBBF3)**
- **Requirement:** Manage Stripe Connected Account liability and KYC compliance across multiple jurisdictions (SF, NYC, Chicago).
- **Technical Implementation:** The `API Orchestration Layer` (SUR-85E4A5B6E7) must enforce strict KYC data collection workflows for Merchant (ACT-AF904DCFF9) and NGO Operator (ACT-09E028AEB0) onboarding. This includes collecting and securely transmitting tax IDs, business addresses, and bank account details to Stripe Connect.
- **Data Isolation:** KYC data must be stored in a cryptographically segregated database schema, accessible only by the Platform Administrator (ACT-086A974D63) and automated Stripe sync services.

### 2.7 Beneficiary Data Anonymization and Privacy

The core mission of MealCredit is to eliminate social stigma. This requires absolute anonymization of beneficiary data, ensuring that no PII can be linked to donation or redemption events.

**Constraint 3: Cryptographic Segregation of Beneficiary PII (CON-92F07E31B0)**
- **Requirement:** Implement strict data isolation where beneficiary demographic status and legal names are cryptographically segregated from public transaction data.
- **Technical Implementation:**
  - **Database Partitioning:** Beneficiary PII (names, contact info) must be stored in a separate, encrypted database partition or schema from transactional data (redemption events, credit balances).
  - **Access Control:** Direct database access to the PII partition is restricted to cryptographic hashing layers only. Application-level access requires multi-factor authentication and is logged to AWS CloudTrail (CON-FBBBF07295).
  - **Hashing:** All PII must be hashed using a strong, salted algorithm (e.g., Argon2id) before storage. The salt must be stored separately from the hash.

**Constraint 4: FTC Guidelines on Anonymity (CON-C22D030D21)**
- **Requirement:** Adhere to FTC guidelines on anonymity, ensuring no de-anonymization attacks can link beneficiaries to donors through metadata analysis.
- **Technical Implementation:**
  - **Metadata Stripping:** All redemption events must be stripped of geolocation metadata, device fingerprints, and IP addresses before being stored in the analytics data warehouse.
  - **Aggregation:** Donor impact receipts (CON-23A501C051) must be generated using aggregated, anonymized data sets. No individual beneficiary redemption event can be traced back to a specific donor.
  - **Audit:** Regular third-party audits must be conducted to test for de-anonymization vulnerabilities.

### 2.8 Financial Regulations and Quasi-Cash Instruments

MealCredit's culinary credits function as quasi-cash instruments, subjecting the platform to specific financial regulations.

**Constraint 7: Compliance with Financial Regulations (CON-B1DFEBEC8C)**
- **Requirement:** Comply with financial regulations governing quasi-cash instruments, specifically regarding unclaimed property and escheatment laws.
- **Technical Implementation:**
  - **Unclaimed Property Tracking:** The Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE) must track the age of all culinary credits. Credits that remain unused for a specified period must be flagged for escheatment reporting.
  - **Audit Trail:** All financial transactions must be logged in an append-only cryptographic log (CON-6061FCCA83) to ensure immutability and auditability.
  - **Knowledge Gap:** `KNOWLEDGE_GAP: Specific escheatment thresholds and reporting requirements for quasi-cash instruments in SF, NYC, and Chicago are not yet defined. Legal must establish these thresholds before ratification.`

---

### 2.9 Event Bus Technology

- **Decision Axis:** Selection of the event bus technology for the event-driven serverless architecture.
- **Status:** Open.
- **Rationale:** The specific event bus technology is not defined in the project requirement and should remain an open decision.
- **KNOWLEDGE_GAP:** The specific event bus technology (e.g., AWS EventBridge, Kafka, RabbitMQ) must be selected based on throughput requirements and operational complexity. Engineering Lead must evaluate options against the 10,000 concurrent connection target.

### 2.10 Offline Token Cryptography

- **Decision Axis:** Selection of the cryptographic algorithm for offline QR/barcode tokens.
- **Status:** Open.
- **Rationale:** The specific cryptographic algorithm for offline tokens is not defined and should remain an open decision.
- **KNOWLEDGE_GAP:** The specific cryptographic algorithm (e.g., HMAC-SHA256, Ed25519) and key rotation policy for time-bound offline QR/barcode tokens must be defined. Security Lead must select an algorithm that balances security with the low-latency requirements of offline validation.

### 2.11 Financial Ledger Implementation

- **Decision Axis:** Selection of the ledger implementation strategy for financial mutations.
- **Status:** Open.
- **Rationale:** The specific ledger implementation strategy is not defined and should remain an open decision.
- **KNOWLEDGE_GAP:** The specific ledger implementation strategy (e.g., Append-Only PostgreSQL Log, Distributed Write-Ahead Ledger on DynamoDB) must be selected based on consistency requirements and scalability needs. Engineering Lead must evaluate options against the PCI-DSS Level 1 compliance and 99.99% uptime targets.

### 2.12 POS Vendor and Region Specifics

- **Decision Axis:** Selection of specific POS vendor integrations and AWS region mappings.
- **Status:** Open.
- **Rationale:** Specific POS vendor names (e.g., Toast, Clover, Square) and AWS region names (e.g., us-west-2, us-east-1, us-central-1) are invented specifics not grounded in the project requirement.
- **KNOWLEDGE_GAP:** The specific POS vendor integrations and AWS region mappings must be defined based on merchant preferences and data residency requirements. Operations Lead must establish these mappings before ratification.

### 2.14 Open Decisions and Knowledge Gaps

This section establishes the binding compliance and privacy constraints for the MealCredit platform. These constraints must be strictly adhered to in all subsequent design and development phases. Any deviation from these constraints requires explicit approval from the Platform Administrator (ACT-086A974D63) and the Legal team.

- `KNOWLEDGE_GAP: Exact data residency laws for SF, NYC, and Chicago are not yet defined. Legal must establish specific jurisdictional requirements before ratification.`
- `KNOWLEDGE_GAP: Specific escheatment thresholds and reporting requirements for quasi-cash instruments in SF, NYC, and Chicago are not yet defined. Legal must establish these thresholds before ratification.`
- `KNOWLEDGE_GAP: Specific POS gateway APIs for initial Merchant Partners are not yet identified. Product/Engineering must identify target integrations before API contract finalization.`
- `KNOWLEDGE_GAP: Initial AWS region selection and multi-region expansion strategy are not yet defined. Platform Administrator must define the initial deployment footprint and data routing rules.`
- `KNOWLEDGE_GAP: Specific cryptographic algorithm for offline fallback tokens is not yet defined. Security Engineering must select the algorithm (e.g., HMAC-SHA256 vs. Ed25519) based on device constraints.`
- `KNOWLEDGE_GAP: Specific event bus technology for asynchronous credit issuance is not yet defined. Platform Administrator must select the eventing mechanism (e.g., AWS EventBridge, SNS/SQS) based on throughput requirements.`
- `KNOWLEDGE_GAP: Specific financial ledger implementation strategy (PostgreSQL vs. DynamoDB) is not yet defined. Platform Administrator must select the ledger technology based on consistency and scalability trade-offs.`

### 3.1 Anonymous Credit Distribution Engine Scalability (CON-121117F5A2)

Decision Context: The anonymous credit distribution engine must handle peak event-driven loads (e.g., large donor campaigns) without degrading the real-time POS clearance latency for Beneficiaries (CON-5D64EBC654). The system must decouple donation ingestion from credit issuance to prevent backpressure.

Open Decision:
 Axis: Credit Issuance Throughput vs. Real-Time Latency.
 Options:
 1. Synchronous Issuance: Credit is issued immediately upon donation confirmation. Risk: High latency during peak loads; potential for POS clearance failures.
 2. Asynchronous Issuance (Recommended): Donations are ingested via an event bus, and credits are issued asynchronously to a pre-funded pool. Benefit: Decouples donor load from beneficiary experience; ensures POS clearance latency remains under 250ms (CON-7F03CF540E).
 Resolution: Adopt Asynchronous Issuance. The API Orchestration Layer will acknowledge donations immediately but queue credit issuance events. A dedicated worker service will process these events, ensuring the Credit Pool Utilization Rate (CON-7031BE57B3) is monitored and alerts trigger at 85%.
 Owner: Platform Administrator (ACT-086A974D63).
 Timeline: Resolution required before Design Phase API contract finalization.

### 3.2 Real-Time POS Clearance Latency (CON-5D64EBC654)

Decision Context: To prevent restaurant queue stagnation, POS clearance must be optimized for real-time performance. The system must handle 10,000 concurrent connections with a p99 latency below 250ms (CON-7F03CF540E).

Open Decision:
 Axis: POS Clearance Protocol and Caching Strategy.
 Options:
 1. Direct Database Lookup: Query Aurora PostgreSQL for beneficiary balance and credit validity. Risk: High latency under load; database connection pool exhaustion.
 2. Redis Enterprise Cluster Caching (Recommended): Maintain a hot cache of beneficiary credit balances and voucher states in Redis. Benefit: Sub-millisecond read latency; supports high concurrency. Cache Hit Ratio (CHR) must be maintained above 92% (CON-EA7C3EFECB).
 Resolution: Implement Redis Enterprise Cluster Caching. The API Orchestration Layer will validate vouchers against the Redis cache. Any balance updates will be propagated asynchronously to Aurora PostgreSQL for auditability (CON-6061FCCA83).
 Owner: Platform Administrator (ACT-086A974D63).
 Timeline: Resolution required before Design Phase API contract finalization.

### 3.3 Offline Fallback Mechanisms (CON-AA83B13877)

Decision Context: In the event of network outages, the platform must support offline fallback QR/barcode tokens. These tokens must be protected against replay attacks using time-bound cryptographic signatures.

Open Decision:
 Axis: Offline Token Cryptography and Revocation Strategy.
 Options:
 1. HMAC-Signed Tokens: Tokens contain a timestamp and a HMAC signature. Risk: Requires local cache of revoked tokens to prevent replay attacks within the validity window.
 2. One-Time Use Nonces: Tokens are single-use and require a local nonce list. Risk: High storage overhead on the device.
 Resolution: Adopt HMAC-Signed Tokens with a local revocation cache. The Expo mobile application (Client Interface Layer) will store a rolling window of revoked token hashes in SecureStore (CON-C42F7B521B). The Merchant Dashboard (Web) will validate these tokens against the API Orchestration Layer when connectivity is restored.
 Owner: Security Engineer.
 Timeline: Resolution required before Design Phase API contract finalization.

### 3.4 Financial Edge-Case Handling (CON-61EC670500)

Decision Context: The system must handle financial edge cases such as double-spending prevention and voided transactions. The financial ledger must be immutable and auditable.

Open Decision:
 Axis: Ledger Immutability and Reconciliation.
 Options:
 1. Append-Only PostgreSQL Log: Use PostgreSQL's ACID properties to create an append-only ledger. Benefit: Strong consistency; simpler to implement.
 2. Distributed Write-Ahead Ledger: Use a distributed ledger (e.g., DynamoDB Streams). Risk: Complexity; potential for eventual consistency issues.
 Resolution: Adopt Append-Only PostgreSQL Log. All financial transactions will be recorded in an append-only table in Aurora PostgreSQL. Periodic hash-checksums will be generated to ensure data integrity. This aligns with SOC2 Type II structural planning (CON-81FB01F06B) and logging to AWS CloudTrail (CON-FBBBF07295).
 Owner: Platform Administrator (ACT-086A974D63).
 Timeline: Resolution required before Design Phase API contract finalization.

### 3.5 Knowledge Gaps and Assumptions

KG-01 | Data Residency Jurisdictions: Specific data residency laws for SF, NYC, and Chicago are not yet confirmed. | May require additional regional deployments or data routing rules. | Legal / Compliance | Before Design Phase
KG-02 | Stripe Connected Account KYC: KYC requirements for Merchant Partners (Restaurants) across multiple jurisdictions (SF, NYC, Chicago) are not fully defined. | May impact Merchant Onboarding & POS Integration (JNY-356F465DB3) timeline. | Legal / Compliance | Before Design Phase
KG-03 | POS Gateway Integration: Specific POS gateway APIs for initial Merchant Partners are not yet identified. | May impact API Orchestration Layer design. | Product / Engineering | Before Design Phase
KG-04 | AWS Region Selection: Initial MVP region and multi-region expansion strategy are not yet defined. | Defines initial infrastructure scope and data residency compliance. | Platform Administrator (ACT-086A974D63) | Before Design Phase
KG-05 | Expo Version: Expo v51 with Fabric architecture is the target frontend stack. | Defines frontend development constraints. | Frontend Lead | Before Design Phase

This document consolidates the binding technical constraints, multi-tenant scaling strategy, and architectural surface mappings required to transition MealCredit from a single-city MVP to a resilient, event-driven platform supporting 50,000 Monthly Active Users (MAU) across San Francisco, New York, and Chicago.

### 3.6 Multi-Tenant Scaling Strategy

To support 50,000 MAU across three metropolitan footprints, the platform will adopt a Shared Infrastructure, Logical Isolation model. This approach balances the operational efficiency of a single cloud footprint with the strict data residency and compliance requirements of financial services.

Tenant Isolation: Financial data and beneficiary PII will be partitioned by jurisdiction_id (SF, NYC, CHI) within a single Amazon Aurora PostgreSQL cluster. This ensures strict logical isolation without the prohibitive cost of maintaining three separate database clusters. Latency & Throughput Targets:
 POS Clearance: The system must maintain p99 latency below 250ms for voucher creation and scanning callbacks under 10,000 concurrent connections (CON-7F03CF540E). This is achieved by routing high-throughput POS callbacks via asynchronous gRPC services. Webhook Processing: Stripe Webhook processing latency must average below 150ms from card tap to merchant ledger entry (CON-06232374D9). This requires synchronous Stripe API calls for immediate ledger updates, decoupled from non-critical analytics. Caching Strategy: To support the target Cache Hit Ratio (CHR) above 92% for restaurant search queries (CON-EA7C3EFECB), the architecture mandates a Redis Enterprise Cluster. This layer sits between the API Orchestration Layer and the Data Persistence Layer to absorb read-heavy traffic.

### 3.9 Open Architectural Decisions & Knowledge Gaps

The following decisions remain unresolved and must be ratified before the Design phase:

Offline Fallback Mechanism: Should the Pseudo-Anonymous Redemption Engine route POS clearing exclusively through real-time Stripe Issuing virtual card provisioning, or implement a deterministic HMAC-signed fallback voucher system for low-latency/high-availability scenarios? (CON-AA83B13877)
 Financial Ledger Reconciliation: Should financial ledger reconciliation be handled via an append-only immutable log in PostgreSQL (ACID) with periodic hash-checksums, or a distributed write-ahead ledger on DynamoDB for horizontal scale? (CON-61EC670500)
 Regional Pool Implementation: For the Donation-to-Redemption Velocity (DRV) metric, should the 'Regional Pool' be implemented as a logical isolation layer within a single DynamoDB table or as physically separate DynamoDB tables per metro footprint (SF, NYC, CHI)? (CON-F89C70071E)

## 4. Actor and Journey Traceability Matrix

This section maps the canonical actor roles and user journeys to the architectural surfaces and capabilities defined in the preceding sections, ensuring complete traceability and scope coverage.

### 4.1 Actor Role Bindings

Platform Administrator (ACT-086A974D63): Oversees compliance failure recovery, financial reconciliation, and platform-wide configuration.
NGO Operator (ACT-09E028AEB0): Manages beneficiary eligibility, offboarding, and regional credit pool oversight.
Dispute Adjudicator (ACT-7BA340FF76): Reviews and resolves beneficiary-platform disputes using immutable ledger logs.
Donor (ACT-80C62C7814): Initiates micro-donations via round-ups or directed impact flows.
Beneficiary (ACT-ADA6716160): Redeems anonymous culinary credits at participating merchants.
Merchant (ACT-AF904DCFF9): Accepts payments, manages POS integration, and handles refunds.

### 4.2 User Journey Mappings

Donor Onboarding & Funding Activation (JNY-62D850E94B): Handled by the Payment Processing Surface (SUR-5B18C8719F) and API Orchestration Layer (SUR-85E4A5B6E7).
Beneficiary Eligibility & Voucher Redemption (JNY-E82B8A88D8): Orchestrated by the API Orchestration Layer (SUR-85E4A5B6E7) with caching via Redis (CON-EA7C3EFECB) and ledger updates in Aurora PostgreSQL (CON-6061FCCA83).
Merchant Onboarding & POS Integration (JNY-356F465DB3): Managed by the Platform Administrator (ACT-086A974D63) and integrated via the Payment Processing Surface (SUR-5B18C8719F).
Financial Reconciliation & Payout (JNY-35EBA169C6): Executed by the API Orchestration Layer (SUR-85E4A5B6E7) with audit trails in the Data Persistence Layer (SUR-FA61592CD4).
Compliance Failure & Anonymized Recovery (JNY-54963DD39A): Triggered by the Platform Administrator (ACT-086A974D63) using immutable logs from the Data Persistence Layer (SUR-FA61592CD4).
NGO Governance & Beneficiary Offboarding (JNY-4C4BA15817): Managed by the NGO Operator (ACT-09E028AEB0) with data purging enforced by the Data Persistence Layer (SUR-FA61592CD4).
Merchant-Beneficiary Refund Flow (JNY-E5F45D37C6): Processed by the Transaction Refund & Reversal Engine (CAP-TRANSACTION-REFUND-REVERSAL-ENGINE) via the API Orchestration Layer (SUR-85E4A5B6E7).
Beneficiary-Platform Dispute Flow (JNY-2B038C9362): Adjudicated by the Dispute Adjudicator (ACT-7BA340FF76) using evidence from the Data Persistence Layer (SUR-FA61592CD4).
Merchant Payout Error Handling Flow (JNY-90B07623FB): Handled by the Merchant Payout Failure & Error Handling capability (CAP-MERCHANT-PAYOUT-FAILURE-ERROR-HANDLING) via the API Orchestration Layer (SUR-85E4A5B6E7).
Platform-NGO Fraud Investigation Flow (JNY-CA74D631DC): Investigated by the Platform Administrator (ACT-086A974D63) and NGO Operator (ACT-09E028AEB0) using Fraud Detection & Fraud Prevention Screening (CAP-FRAUD-DETECTION-FRAUD-PREVENTION-SCREENING).

### 4.3 Capability Surface Alignment

Identity & Access Management (CAP-IDENTITY-ACCESS-MANAGEMENT): Enforced at the API Orchestration Layer (SUR-85E4A5B6E7) and Client Interface Layer (SUR-43E71C4E2B).
Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE): Core logic resides in the API Orchestration Layer (SUR-85E4A5B6E7) with state in the Data Persistence Layer (SUR-FA61592CD4).
Marketplace & Matchmaking (CAP-MARKETPLACE-MATCHMAKING): Driven by the API Orchestration Layer (SUR-85E4A5B6E7) using Redis caching (CON-EA7C3EFECB) for location-aware allocation.
Compliance, Security & Audit (CAP-COMPLIANCE-SECURITY-AUDIT): Implemented across all surfaces, with specific controls on the Payment Processing Surface (SUR-5B18C8719F) and Data Persistence Layer (SUR-FA61592CD4).
Merchant & NGO Operations (CAP-MERCHANT-NGO-OPERATIONS): Managed via the API Orchestration Layer (SUR-85E4A5B6E7) and Client Interface Layer (SUR-43E71C4E2B).
Dispute Resolution & Chargeback Management (CAP-DISPUTE-RESOLUTION-CHARGEBACK-MANAGEMENT): Handled by the Dispute Adjudicator (ACT-7BA340FF76) using data from the Data Persistence Layer (SUR-FA61592CD4).
# Technical Architecture & Integration Strategy

## 1. Client Application Layer (SUR-E3E75E96CF) Specifications

The Client Application Layer (SUR-E3E75E96CF) serves as the primary interface for Recipients (ACT-DC00FA84DC) and Contributors (ACT-2A20B038B1), built on Expo v51 with the React Native Fabric architecture. This layer is designed to decouple food assistance from social stigma by ensuring absolute anonymity and providing robust offline capabilities for low-tech POS environments.

### 1.1 Identity & Access Management (CAP-361A59708B) Integration

The Client Application Layer (SUR-E3E75E96CF) delegates all authentication and session management to the Identity & Access Management (CAP-361A59708B) capability.

*   **Authentication Flow:** Contributors (ACT-2A20B038B1) authenticate via OAuth 2.0 / OIDC using Stripe Elements and SDK to ensure PCI-DSS Level 1 compliance (CON-6EA64CF2A1). Recipients (ACT-DC00FA84DC) authenticate via anonymous, device-bound session tokens issued by Identity & Access Management (CAP-361A59708B) upon first launch, ensuring no PII is required for access.
*   **Session Security:** All session tokens are stored locally using device-level SecureStore. Tokens are cryptographically signed to prevent forgery and tampering, addressing the security concern for offline token storage (CON-0346AE051D).
*   **Anonymization:** Identity & Access Management (CAP-361A59708B) maps Recipient (ACT-DC00FA84DC) identities to high-entropy UUIDv4 keys, ensuring that beneficiary demographic data remains strictly off-platform (CON-9DEA275205, CON-4DB27D2227).

### 1.2 Discovery & Allocation Engine (CAP-264DA83096) Integration

The Client Application Layer (SUR-E3E75E96CF) interacts with the Discovery & Allocation Engine (CAP-264DA83096) to enable Recipient (ACT-DC00FA84DC) discovery of Merchant Partners (ACT-A14D3CDC5D).

*   **Discovery Query:** The app sends geo-proximity queries to the Discovery & Allocation Engine (CAP-264DA83096) via the API Gateway & Orchestration Layer (SUR-D6FFF7036F). Queries include user location, dietary preferences, and available credit balance.
*   **Caching Strategy:** To support offline discovery where possible, the app caches search results from the Discovery & Allocation Engine (CAP-264DA83096) locally using AsyncStorage with a TTL-based invalidation strategy. This supports the requirement for a Redis Enterprise Cluster cache hit ratio exceeding 92% (CON-42B7E9919E) by reducing redundant network requests.
*   **Credit Allocation:** When a Recipient (ACT-DC00FA84DC) selects a Merchant Partner (ACT-A14D3CDC5D), the app requests a single-use, anonymized virtual card token from the Discovery & Allocation Engine (CAP-264DA83096). This token is locked to specific Merchant Category Codes (MCC) and location, ensuring compliance with business rules for pseudo-anonymized redemption.

### 1.3 Offline Token Storage & Forgery Prevention (CON-0346AE051D)

To ensure resilience and privacy, the Client Application Layer (SUR-E3E75E96CF) implements a secure offline token storage mechanism.

*   **Secure Storage:** Tokens are stored in `expo-secure-store`, leveraging the native Keychain (iOS) and Keystore (Android). This prevents extraction by malicious applications or rooted/jailbroken devices.
*   **Cryptographic Signing:** Each token is signed with a secret key known only to the Core Transaction & Ledger Service (SUR-DD602DB92C). The signature includes the token value, expiration timestamp, and a nonce. The app verifies the signature locally before presenting the token for redemption.
*   **Token Lifecycle:** Tokens are short-lived and single-use. If a token is not used within its validity period, it is invalidated server-side. Unused emergency credits auto-roll back to the regional pool after 72 hours (CON-AEB925BD12).

### 1.4 Offline Fallback QR/Barcode Presentations (CON-036979982A)

To ensure compatibility with standard, low-tech POS devices, the Client Application Layer (SUR-E3E75E96CF) generates scannable offline fallback codes.

*   **QR Code Generation:** The app generates high-density QR codes (ISO/IEC 18004) containing the signed redemption payload. These codes are rendered as static images, ensuring they are scannable by basic POS scanners without requiring a camera or internet connection on the merchant side.
*   **Barcode Fallback:** As an additional fallback, the app can generate 1D Code 128 barcodes containing a compressed version of the redemption payload. This ensures compatibility with legacy POS systems that may not support QR scanning.
*   **Visual Design:** The vouchers are visually identical to consumer gift cards, maintaining the principle of absolute anonymization and reducing social stigma for Recipients (ACT-DC00FA84DC).

### 1.5 Performance & Latency Constraints

The Client Application Layer (SUR-E3E75E96CF) must adhere to strict latency constraints to ensure a frictionless experience for Recipients (ACT-DC00FA84DC) and Contributors (ACT-2A20B038B1).

*   **API Responsiveness:** The Client Application Layer (SUR-E3E75E96CF) must maintain p99 latency below 250ms for Voucher Creation and Scanning Callback Processing under 10,000 concurrent connections (CON-14D783B5E5).
*   **Offline Resilience:** The application must function seamlessly in offline or low-connectivity environments, relying on local SecureStore and cached discovery data to prevent service degradation.

## 3. Core Transaction & Ledger Service (SUR-DD602DB92C) Specifications

The Core Transaction & Ledger Service (SUR-DD602DB92C) is the financial backbone of the Daya MealCredit platform, responsible for maintaining the integrity of the credit pool, processing transactions, and ensuring absolute financial reconciliation.

### 3.1 Append-Only Cryptographic Audit Ledger

To ensure financial integrity and regulatory compliance, the Core Transaction & Ledger Service (SUR-DD602DB92C) maintains an append-only, cryptographic audit ledger in Aurora Postgres (CON-199A4FEDC7).

*   **Immutability:** All financial transactions are recorded as immutable entries in the ledger. Once written, entries cannot be altered or deleted, ensuring a tamper-proof history of all credit movements.
*   **Cryptographic Hashing:** Each ledger entry includes a cryptographic hash of the previous entry, creating a chain of trust that allows for easy detection of any unauthorized modifications.
*   **CloudTrail Integration:** All infrastructure modifications and administrative ledger operations are pushed to unalterable AWS CloudTrail logs (CON-0B2D40801A), providing an additional layer of auditability for SOC2 Type II compliance (CON-0A6423E6B0).

### 3.2 Financial Reconciliation & Partial Failure Handling

The Core Transaction & Ledger Service (SUR-DD602DB92C) ensures robust financial reconciliation, even in the event of partial failures.

*   **Idempotency:** All transaction endpoints are idempotent, ensuring that duplicate requests do not result in double-spending or ledger corruption.
*   **Partial Failure Recovery:** In the event of a partial failure (e.g., credit issued but not cleared), the system employs a reconciliation process to ensure that credits are either fully cleared or rolled back to the regional pool, preventing ledger stagnation (CON-6A9F6E50CE).
*   **Auto-Rollback:** Unused emergency credits automatically roll back to the regional pool after 72 hours (CON-AEB925BD12), ensuring that the credit pool remains dynamic and responsive to actual demand.

## 4. Integration & Payment Gateway Adapter (SUR-213BCD1816) Specifications

The Integration & Payment Gateway Adapter (SUR-213BCD1816) serves as the bridge between the Daya MealCredit platform and external financial networks, primarily Stripe.

### 4.1 Stripe Integration & PCI-DSS Level 1 Compliance

The Integration & Payment Gateway Adapter (SUR-213BCD1816) ensures strict adherence to PCI-DSS Level 1 compliance by ensuring zero raw credit card data touches application servers.

*   **Stripe Elements & SDK:** All payment instrument interactions are handled exclusively via Stripe Elements and SDK, ensuring that sensitive card data is collected directly by Stripe and never exposed to the Daya platform.
*   **Tokenization:** Stripe returns secure tokens for all payment instruments, which are used by the platform to process transactions without handling raw card data (CON-6EA64CF2A1).
*   **Webhook Processing:** The Integration & Payment Gateway Adapter (SUR-213BCD1816) processes Stripe webhooks with a target average latency below 150ms for merchant ledger entry clearance (CON-D792CA1810).

### 4.2 Enterprise POS Gateway for Merchant Partners

The Integration & Payment Gateway Adapter (SUR-213BCD1816) facilitates seamless integration with Merchant Partner (ACT-A14D3CDC5D) POS systems.

*   **Zero-Footprint Integration:** The adapter supports zero-footprint integration, allowing Merchant Partners (ACT-A14D3CDC5D) to ingest orders via standard POS interfaces without requiring custom software installations.
*   **Edge Dashboard:** For merchants without standard POS integration, an edge dashboard provides a web-based interface for order ingestion and settlement.
*   **Throttle Parameters:** Kitchens can toggle real-time throttle parameters, such as a maximum of 15 MealCredit orders per hour, to prevent structural overload (Business Rule).

## 5. Infrastructure Topology & Scalability

The Daya MealCredit platform is deployed on AWS multi-AZ configurations to ensure 99.99% operational uptime and graceful degradation if POS partners fail (CON-8BD1F56A44).

### 5.1 AWS Multi-AZ Configuration

*   **High Availability:** All core services, including the API Gateway & Orchestration Layer (SUR-D6FFF7036F) and the Core Transaction & Ledger Service (SUR-DD602DB92C), are deployed across multiple Availability Zones to ensure high availability and fault tolerance.
*   **Graceful Degradation:** The system is designed to gracefully degrade in the event of a regional outage, prioritizing critical financial transactions and offline redemption capabilities.

### 5.2 Redis Enterprise Cluster Caching

*   **Cache Hit Ratio:** The platform utilizes a Redis Enterprise Cluster to cache restaurant search queries, targeting a cache hit ratio exceeding 92% (CON-42B7E9919E).
*   **Latency Reduction:** Caching significantly reduces latency for discovery queries, supporting the p99 latency targets (CON-14D783B5E5) and improving the overall user experience for Recipients (ACT-DC00FA84DC).

### 5.3 Scalability & Bursty Traffic

*   **Bursty Traffic Handling:** The system scalability must account for bursty traffic patterns during peak donation cycles or redemption events without degrading latency (CON-873877C003).
*   **Auto-Scaling:** AWS auto-scaling groups are configured to dynamically adjust compute resources based on real-time demand, ensuring consistent performance during peak periods.

## 6. Compliance, Risk & Regulatory Obligations

The Daya MealCredit platform operates within a highly regulated environment, requiring strict adherence to SOC2 Type II and PCI-DSS Level 1 standards.

### 6.1 SOC2 Type II Control Environments

*   **Detailed Tracking Logs:** The platform generates detailed tracking logs for all infrastructure and administrative changes, ensuring comprehensive auditability (CON-0A6423E6B0).
*   **Access Controls:** Strict access controls are enforced via Identity & Access Management (CAP-361A59708B), ensuring that only authorized personnel can access sensitive systems and data.

### 6.2 Data Privacy & Anonymization

*   **Absolute Anonymization:** All beneficiary analytics map to high-entropy UUIDv4 keys, preventing PII reconstruction (CON-9DEA275205).
*   **Off-Platform Demographic Data:** Beneficiary demographic data is classified as strictly off-platform; the platform stores only derived, anonymized credits (CON-4DB27D2227).
*   **Data Retention:** Unused emergency credits auto-roll back to the regional pool after 72 hours (CON-AEB925BD12). Data retention policies are enforced to ensure compliance with regulatory requirements.

## 7. Open Decisions & Knowledge Gaps

The following decisions remain open and require resolution before downstream phases can proceed.

*   **DEC-BDB9EA01B2:** Should the virtual card limit enforcement rely solely on Stripe's backend merchant-category-code (MCC) and geo-fencing rules, or require a pre-authorization validation step from the Daya backend to enforce NGO-specific spending caps before card issuance?
*   **DEC-7E9F9E778C:** For offline redemption resilience, should the system store a time-bound, signed JWT voucher on the client's SecureStore that requires network connectivity for verification (online-only when available), or implement a complex offline-counter mechanism with local cryptographic nonce tracking to allow offline verification?
*   **DEC-ADD3B231CD:** Which specific POS integration middleware strategy will be adopted: using Stripe's existing Square POS integration vs. building custom gRPC adapters for Toast and Clover to ensure consistent event streaming into the event-driven architecture?
*   **DEC-AD357A7A9A:** Does the 'Directed Impact Flow' (FR-DON-02) require real-time filtering of eligible merchants at the point of donation, or can it be processed asynchronously with a batch-settlement mechanism for unfulfilled directed funds?

## 8. Success Signals & Monitoring

The platform's success will be measured against the following key performance indicators (KPIs).

*   **Donation-to-Redemption Velocity (DRV):** Target under 14 days.
*   **Merchant Retention Rate (MRR):** Measured month-over-month.
*   **Credit Pool Utilization Rate:** Triggers alerts if above 85%.
*   **Stripe Webhook Processing Latency:** Average below 150ms.
*   **Cache Hit Ratio (CHR):** For restaurant search queries above 92%.
*   **API Responsiveness:** p99 latency below 250ms under 10,000 concurrent connections.
*   **Operational Uptime:** 99.99% across AWS multi-AZ configurations.

## 9. Conclusion

This Technical Architecture & Integration Strategy provides a comprehensive blueprint for the Daya MealCredit platform, translating the tripartite ecosystem into a resilient, multi-AZ AWS serverless architecture. By adhering to strict compliance standards, ensuring absolute beneficiary anonymization, and leveraging a hybrid API orchestration strategy, the platform is positioned to scale effectively across its initial metropolitan footprints while maintaining the highest standards of security and user experience.
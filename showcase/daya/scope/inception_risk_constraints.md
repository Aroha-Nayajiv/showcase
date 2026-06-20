# Risk Register and Technical Constraints

### 2.1 Donation-to-Redemption Velocity (DRV) Mismatch

**Risk Description:** The platform must maintain a Donation-to-Redemption Velocity (DRV) under 14 days (CON-9D8C6B4773). If DRV exceeds this target, funds become 'stale,' reducing liquidity velocity and increasing administrative overhead for expiration policies. Conversely, if DRV is too fast, it may indicate insufficient Funder engagement or fraudulent redemption patterns.

**Impact:** Medium. Reduced operational efficiency; potential for fraud; decreased impact transparency for Funders.

**Mitigation Strategy:**
*   Monitor DRV metrics in real-time via the Transaction & Liquidity Engine (CAP-65F7377EBE).
*   Define and enforce expiration policies for unused emergency credits (72-hour rollback to central regional pool) to prevent ledger stagnation.
*   Analyze DRV trends to adjust Funder engagement strategies and directed impact flows (DirectedImpactFlows).

**Owner:** Operator (ACT-FE96DD3975)

### 2.2 Double-Spending and Clearing Latency

**Risk Description:** In low-connectivity environments or during high-throughput POS clearing, there is a risk of double-spending if virtual credit tokens are not synchronized in real-time (CON-8F05AD69D4). This risk is exacerbated by the reliance on hardware-backed SecureStore (CON-460D6EBABD) for offline token validation.

**Impact:** High. Financial loss; fraud; erosion of trust with Merchant Partners (Providers).

**Mitigation Strategy:**
*   Enforce real-time synchronization between virtual credit issuance and physical POS terminal clearing.
*   Utilize high-entropy UUIDv4 keys for all transactional state to prevent token prediction or replay attacks.
*   Implement graceful degradation of network dependencies (CON-0018D09145) with strict offline token limits and localized valid cryptographic signatures.

### 2.4 PCI-DSS Level 1 Compliance and Raw Data Storage

**Risk Description:** Implement PCI-DSS Level 1 compliance by never storing raw credit card data; use Stripe Elements and SDK globally (CON-5D30D227A5). Any inadvertent storage of raw card data would result in immediate compliance failure and potential loss of payment processing capabilities.

**Impact:** Critical. Loss of payment processing; regulatory fines; platform shutdown.

**Mitigation Strategy:**
*   Use Stripe Elements and SDK for all donor payment inputs to ensure raw card data never touches platform servers.
*   Conduct regular PCI-DSS Level 1 compliance audits and penetration testing.
*   Ensure all financial ledger entries are retained in Aurora Postgres app-only log indefinitely for compliance (CON-3E7B720F8F), while transient transactional state is purged securely.

## 1. Privacy and Anonymization Risks

The platform's mission to decouple food assistance from social stigma requires absolute anonymization of beneficiary data.

| Risk ID | Risk Title | Impact | Technical Constraint | Owner |
| :--- | :--- | :--- | :--- | :--- |
| PRIV-RISK-01 | Beneficiary PII Leakage | Critical: Violation of social stigma prevention mission, potential GDPR/CCPA violations, and loss of user trust. | Enforce absolute PII anonymization (CON-1BC6B8851E). Beneficiary demographic status, legal name, and domestic background must not cross into production logs or DB tables. All analytics must use high-entropy UUIDv4 keys (CON-2DE50DC545). | Operator |
| PRIV-RISK-02 | Failure of Right-to-Erasure | High: Violation of CCPA/GDPR right-to-erasure workflows (CON-B68D690D72). | Implement automated workflows for right-to-erasure that ensure complete deletion of PII from all active and backup systems within the mandated timeframe. Financial ledger entries must be retained only as required by law (CON-3E7B720F8F). | Operator |
| PRIV-RISK-03 | Funder-Recipient Linkage | Critical: Violation of strict zero-knowledge anonymity (CON-705CB41089) and social stigma prevention. | Architectural design must ensure no data path exists that links a Funder's identity to a Recipient's identity. Transactional receipts to Funders must be strictly anonymized. | Operator |

### 1.1 Graceful Degradation in Low-Connectivity Environments

**Risk ID:** OP-CONT-001
**Risk Title:** Service Continuity Failure in Low-Connectivity Environments
**Concern Reference:** CON-0018D09145 (Implied concern: Graceful degradation of network dependencies to ensure service continuity in low-connectivity environments.)

**Risk Description:**
Beneficiaries (Recipients) in the target metropolitan footprints (SF, NYC, Chicago) may experience intermittent or low-bandwidth network connectivity when attempting to redeem credits at restaurant locations. If the platform relies exclusively on real-time cloud validation for voucher presentation, beneficiaries may be unable to access their credits or complete transactions, leading to service failure and reputational damage.

**Technical Constraints & Mitigations:**
1.  **Offline-First Token Architecture:** The mobile application must implement an offline-first strategy for voucher presentation. Vouchers must be cached locally on the device using hardware-backed SecureStore (CON-460D6EBABD) with localized valid cryptographic signatures.
2.  **Cryptographic Validation:** The POS scanning interface (Provider Edge Dashboard or integrated POS system) must be capable of validating the cryptographic signature of the offline token locally before attempting cloud synchronization. This ensures that the token is valid and has not been tampered with, even if the network is down.
3.  **Synchronization Queue:** Transactions performed in offline mode must be queued locally and synchronized with the central ledger (Aurora Postgres) once connectivity is restored. The system must handle potential conflicts (e.g., double-spending if the same token is presented in multiple locations) via a deterministic resolution strategy defined in the Transaction & Liquidity Engine.

**Owner:** Operator (Platform Engineering)
**Severity:** High

### 1.2 Multi-Tenant Data Segregation (CON-2BCB3D9CF7)

**Risk:** Cross-tenant data visibility in Aurora Postgres and DynamoDB could lead to unauthorized access to beneficiary profiles or financial transaction histories across different NGO jurisdictions.

**Technical Constraints:**
*   **Aurora Postgres:** All tables storing beneficiary or transactional data must include a tenant_id column. Database-level Row Level Security (RLS) policies must be enforced to ensure that queries from a specific tenant context can only access rows matching that tenant_id. No raw SQL queries in the application layer may bypass these policies.
*   **DynamoDB:** All Global Secondary Indexes (GSI) and Primary Keys must include the tenant_id as a partition or sort key component. Access policies for DynamoDB tables must explicitly restrict operations to the requesting tenant's ID. Cross-tenant queries are strictly prohibited.

**Mitigation:**
*   Implement strict schema validation to ensure tenant_id is present and immutable in all write operations.
*   Conduct regular automated audits to detect any queries that attempt to access data outside the authorized tenant scope.

### 1.4 Secure Offline Token Storage (CON-460D6EBABD)

**Risk:** Unauthorized access to localized valid cryptographic signatures or virtual card tokens stored on the beneficiary's device, leading to potential fraud or double-spending.

**Constraints:**
*   **SecureStore:** All offline tokens and cryptographic signatures must be stored using the device hardware-backed SecureStore (iOS Keychain / Android Keystore). Standard AsyncStorage or local storage is strictly prohibited for any sensitive token data.
*   **Signature Validation:** Tokens must include a localized valid cryptographic signature that is verified against the device's hardware security module. Any attempt to tamper with the stored token must result in immediate invalidation.

**Mitigation:**
*   Implement biometric or PIN-based unlock requirements for accessing the SecureStore on the client device.
*   Design the token validation logic to fail securely if the hardware-backed storage is compromised or inaccessible.

### 1.5 Critical API Latency and Throughput Constraints

The platform must maintain strict latency bounds to ensure a frictionless redemption experience for Recipients and Providers. Failure to meet these thresholds will directly impact Merchant Retention Rate (MRR) and user trust.

**Constraint (CON-FD2AD44598):** The system must achieve a p99 latency of less than 250ms for critical APIs, specifically Voucher Creation and Scanning Callback, under a load of 10,000 concurrent connections across the three metropolitan footprints (SF, NYC, Chicago).

**Risk R6.1: API Latency Degradation under Peak Load.**
*   **Description:** During peak redemption hours (e.g., lunch/dinner rushes), the hybrid GraphQL/gRPC architecture may experience latency spikes if the GraphQL layer becomes a bottleneck for high-throughput CRUD operations, or if gRPC services for financial transactions are blocked by downstream Stripe API latency.
*   **Impact:** High latency (>250ms p99) will cause POS terminal timeouts, leading to failed transactions, frustrated Providers, and potential double-spending attempts if Recipients retry.
*   **Mitigation:** Implement aggressive caching for Voucher Creation requests where possible. Ensure gRPC services for Scanning Callbacks are stateless and horizontally scalable. Monitor p99 latency in real-time and trigger auto-scaling policies for the Orchestration & API Gateway (SUR-AFB5E258ED) when concurrent connections exceed the defined threshold.

### 1.6 Stripe Webhook Processing Latency

Real-time financial synchronization is critical for maintaining ledger accuracy and preventing double-spending.

**Constraint (CON-521D9D9565):** The system must process Stripe Webhook Latency from card tap to merchant ledger entry in less than 150ms on average.

**Risk R6.2: Stripe Webhook Processing Bottleneck.**
*   **Description:** If the platform's webhook ingestion service is overwhelmed by high-volume Stripe events (e.g., mass redemptions), the average processing time may exceed 150ms, causing delays in updating the Aurora Postgres ledger and DynamoDB transactional state.
*   **Impact:** Delayed ledger updates can lead to stale balance views for NGOs and Funders, and potential race conditions in the Transaction & Liquidity Engine (CAP-65F7377EBE).
*   **Mitigation:** Implement a dedicated, high-throughput webhook ingestion service using Go/gRPC, decoupled from the main GraphQL API. Use a durable message queue (e.g., AWS SQS) to buffer incoming Stripe events and process them asynchronously but with strict priority ordering. Monitor average processing latency and alert if it exceeds the defined threshold.

### 1.7 Cache Hit Ratio (CHR) for Restaurant Search

Efficient location-aware allocation is essential for a positive Recipient experience.

**Constraint (CON-0E4070B49D):** The system must achieve a Cache Hit Ratio (CHR) greater than 92% for restaurant search queries via the Redis location-cache layer.

**Risk R6.3: Low Cache Hit Ratio Leading to Database Overload.**
*   **Description:** If the Redis location-cache layer is not effectively populated or suffers from high eviction rates due to memory pressure, the CHR will drop below 92%, forcing a significant portion of search queries to hit the Aurora Postgres database directly.
*   **Impact:** Increased database load will degrade overall system performance, increase latency for all API calls, and potentially violate the p99 latency constraint (CON-FD2AD44598).
*   **Mitigation:** Implement a robust caching strategy with appropriate TTLs for restaurant location and availability data. Monitor CHR in real-time and adjust cache eviction policies (e.g., LRU) to prioritize frequently accessed restaurant data. Ensure Redis Enterprise Cluster is properly sized for the expected query volume.

### 1.8 Beneficiary Accessibility Standards

**Constraint (CON-08F4F56C98):** Ensure beneficiary app screens (voucher display, restaurant search) meet WCAG 2.1 AA standards for visually impaired users.

**Risk R6.5: Accessibility Non-Compliance.**
*   **Description:** Failure to meet WCAG 2.1 AA standards may exclude visually impaired beneficiaries from using the platform, violating the social impact mission and potentially exposing the platform to legal liability.
*   **Impact:** High. Exclusion of target demographic; reputational damage; legal risk.
*   **Mitigation:** Integrate accessibility testing into the CI/CD pipeline. Ensure all Expo v51 / React Native components meet WCAG 2.1 AA standards for contrast, touch targets, and screen reader compatibility.

### 2.3 Assumptions

*   **ASSUMPTION:** The Stripe API latency is stable and does not exceed 100ms on average. If Stripe experiences outages or slowdowns, the platform's webhook processing latency will be impacted, requiring fallback mechanisms.
*   **ASSUMPTION:** The Redis Enterprise Cluster can be sized to maintain a >92% CHR for restaurant search queries without excessive memory costs. This requires further load testing to validate.

## 3. Cross-Reference to Sibling Artifacts

*   **Compliance, Privacy, and Governance Framework:** This artifact defers to the Compliance artifact for the detailed PCI-DSS Level 1 and SOC2 Type II structural planning requirements that underpin the security of the financial transactions processed by these APIs.
*   **Operating Model and Stakeholder Alignment:** This artifact defers to the Operating Model artifact for the specific roles and responsibilities of the Operator and Facilitator in monitoring and responding to performance alerts.

## 4. Validation Criteria

This artifact is complete when:
1.  All technical performance risks (R6.1-R6.5) are clearly defined with specific constraints (CON-FD2AD44598, CON-521D9D9565, CON-0E4070B49D, CON-5D603E1301, CON-08F4F56C98).
2.  Mitigation strategies are actionable and aligned with the project's technology stack (Expo v51, Next.js, Go/gRPC, Redis, Aurora Postgres).
3.  Knowledge gaps and assumptions are explicitly stated.
4.  Cross-references to sibling artifacts are clear and concise.
5.  Decision axes are identified for future resolution in later phases.

## 5. Operational Resilience and Continuity

### 5.1 Double-Spending and Real-Time Synchronization Failures

**Risk ID:** OP-DS-002
**Risk Title:** Double-Spending Due to Real-Time Synchronization Latency
**Concern Reference:** CON-8F05AD69D4 (Implied concern: Real-time synchronization between virtual credit issuance and physical POS terminal clearing to prevent double-spending.)

**Risk Description:**
A critical financial risk exists where a single virtual credit token could be presented and cleared at multiple POS terminals simultaneously, or where a token is spent after its balance has already been depleted by a concurrent transaction. This risk is exacerbated by network latency between the POS terminal, the gRPC financial services, and the central ledger.

**Mitigations:**
1.  **Atomic Clearing via gRPC:** All financial transactions and POS callbacks must be processed via asynchronous gRPC services to ensure low-latency, high-throughput communication. The clearing process must be atomic, ensuring that a token is marked as 'consumed' in the ledger at the exact moment of authorization.
2.  **Real-Time Balance Verification:** The system must enforce real-time balance verification against the central ledger (Aurora Postgres) before any token is cleared. The Transaction & Liquidity Engine (CAP-65F7377EBE) must reject any transaction that attempts to spend more than the available balance in the regional credit pool.
3.  **Idempotency Keys:** Every POS transaction must include a unique idempotency key. The system must reject any duplicate transaction attempts using the same idempotency key, preventing double-spending even in the event of network retries or client-side errors.

**Severity:** Critical

### 5.2 POS Partner Webhook Integrity and Fallback Protocols

**Risk ID:** OP-POS-003
**Risk Title:** Webhook Payload Integrity and Fallback Protocol Failure
**Concern Reference:** CON-A763D481AA (Implied concern: Manage contractual mandates from POS partners (Toast/Clover/Square) regarding webhook payload integrity and fallback protocols.)

**Risk Description:**
The platform relies on webhook integrations with POS partners (Toast, Clover, Square) to trigger clearing events and update ledger balances. If webhook payloads are tampered with, or if the webhook delivery fails due to network issues or partner API outages, the platform may fail to process transactions correctly, leading to financial discrepancies and service disruptions.

**Mitigations:**
1.  **Webhook Signature Verification:** All incoming webhooks from POS partners must be validated using cryptographic signatures provided by the partners. The platform must reject any webhook that fails signature verification to prevent payload tampering.
2.  **Retry and Fallback Mechanisms:** The platform must implement a robust retry mechanism with exponential backoff for failed webhook deliveries. If a webhook fails after a defined number of retries, the transaction must be flagged for manual review by the Operator, and the Provider must be notified to initiate a fallback clearing process.
3.  **Contractual Compliance:** The platform's webhook integration must adhere to the contractual mandates of each POS partner regarding payload format, frequency, and error handling. This includes ensuring that the platform's API endpoints are available and responsive to partner health checks.

**Severity:** High

### 5.3 Provider Edge Dashboard Usability

**Constraint (CON-5D603E1301):** Ensure restaurant edge dashboard is usable on low-cost tablet hardware common in commercial kitchens.

**Risk R5.4: Provider Onboarding Friction.**
*   **Description:** If the edge dashboard requires high-end hardware or modern browser features not available on low-cost tablets, Providers may fail to activate or experience poor performance during peak hours.
*   **Impact:** Reduced Provider retention; increased support tickets; slower network expansion.
*   **Mitigation:** Design the edge dashboard with progressive enhancement principles. Ensure core scanning and order management functions work on older hardware and browsers. Conduct usability testing on target low-cost devices.

### 5.5 Decision Axes

*   **Axis:** Auto-scaling thresholds for the Orchestration & API Gateway.
    *   **Decision:** Define the exact concurrent connection count that triggers auto-scaling to balance cost and performance.
*   **Axis:** Cache eviction policies for the Redis location-cache layer.
    *   **Decision:** Determine the optimal TTL and eviction strategy (e.g., LRU, LFU) to maximize CHR while ensuring data freshness for restaurant availability.
*   **Axis:** Split-Tender Policy for MealCredit Vouchers.
    *   **Decision:** Should the platform enforce a strict 'no-cash-merge' policy where MealCredit vouchers cannot be combined with other payment methods to cover partial bills, or allow split-tender scenarios? (DEC-576DF4154D)
*   **Axis:** Credit Pool Stagnation Handling.
    *   **Decision:** How should we handle the 'Credit Pool Stagnation' rule (72h rollback) when a beneficiary runs out of credits while physically at a restaurant? (DEC-99BB2C7E2B)
*   **Axis:** Ineligible Categories Validation.
    *   **Decision:** Can we rely solely on Stripe Issuing's MCC restrictions for the 'Ineligible Categories' edge case, or do we need a secondary, application-level validation step before token issuance? (DEC-DA1AB02D02)
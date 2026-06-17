# API Gateway & Orchestration Layer

## 1. API Gateway & Orchestration Layer (SUR-D6FFF7036F) Hybrid Integration Contract

This artifact defines the architectural surface for the API Gateway & Orchestration Layer (SUR-D6FFF7036F), serving as the primary ingress point for all actor interactions (Contributor, Recipient, Merchant Partner, Operator). It establishes the hybrid integration pattern mandated by the binding decision registry: GraphQL for high-throughput, low-latency CRUD operations and asynchronous gRPC for financial integrity-critical transaction processing.

### 1.1 Architectural Surface & Protocol Mapping

The Gateway enforces strict protocol segregation to optimize for distinct operational profiles while maintaining a unified ingress for all actors.

| Operational Profile | Protocol | Target Service Surface | Primary Actors | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| High-Throughput CRUD | GraphQL (HTTP/2) | Client Application Layer (SUR-E3E75E96CF) | Recipient (ACT-DC00FA84DC), Contributor (ACT-2A20B038B1) | Restaurant discovery, voucher generation, balance checks, WCAG 2.1 AA compliant data fetching. |
| Financial Integrity | gRPC (HTTP/2) | Core Transaction & Ledger Service (SUR-DD602DB92C) | Contributor (ACT-2A20B038B1), Merchant Partner (ACT-A14D3CDC5D) | Contributor Primary Transaction Flow (JNY-4FC1874968), Merchant Settlement & Payout (JNY-40AA027A61), POS callbacks. |
| Governance & Admin | GraphQL (HTTP/2) | Operational Governance & Success Criteria (SUR-21B42056F5) | Operator (ACT-FE96DD3975) | Liquidity management, credit pool utilization monitoring, partner onboarding status. |

**Rationale:** GraphQL is selected for UI data to allow the Expo mobile app to fetch nested data (e.g., restaurant details + available vouchers) in a single round-trip, minimizing latency for mobile clients in low-bandwidth areas. gRPC is selected for financial operations to ensure strict serialization, low overhead, and strong contract enforcement for financial operations, preventing UI-layer leakage into the ledger.

### 1.2 Ingress & Actor Routing

The Gateway acts as the single entry point for all actor interactions, enforcing authentication and routing based on the actor's role and the nature of the request.

*   **Contributor (ACT-2A20B038B1):**
    *   **GraphQL:** Queries for contribution history, directed impact flow configuration, and round-up rules.
    *   **gRPC:** Mutations for initiating micro-donation round-ups (JNY-4FC1874968) and funding cycles.
*   **Recipient (ACT-DC00FA84DC):**
    *   **GraphQL:** Queries for restaurant discovery (JNY-76281D3F3C), voucher generation, and balance checks. All beneficiary PII is stripped at the gateway level before reaching downstream services.
*   **Merchant Partner (ACT-A14D3CDC5D):**
    *   **GraphQL:** Queries for settlement reports and operational status.
    *   **gRPC:** Callbacks for POS transaction clearing (JNY-01DD5AC877) and settlement requests (JNY-40AA027A61).
*   **Operator (ACT-FE96DD3975):**
    *   **GraphQL:** Queries for system-wide metrics, credit pool utilization, and partner management.

### 1.3 Security & Compliance Boundary

The Gateway serves as the immutable PCI-DSS Level 1 and SOC2 Type II compliance boundary. It enforces strict RBAC and data masking at the ingress point.

*   **PII Stripping:** All raw credit card data is stripped via Stripe Elements/SDK at the Client Application Layer (SUR-E3E75E96CF) before reaching the Gateway. The Gateway ensures zero PII touches the core transaction services.
*   **Data Masking:** Any residual PII (e.g., for audit logging) is masked at the Gateway level. No raw PII or credit card data is logged or passed to downstream services.
*   **Authentication:** All financial transactions are routed through secure, authenticated gRPC channels. Access control is enforced via strict RBAC policies defined in the sibling Security Architecture artifact.

### 1.4 Performance & Scalability Targets

The Gateway is designed to handle bursty traffic patterns during peak donation cycles or redemption events without degrading latency.

*   **p99 Latency:** Maintain p99 latency below 250ms for Voucher Creation and Scanning Callback Processing under 10,000 concurrent connections.
*   **Cache Hit Ratio:** Ensure Redis Enterprise Cluster cache hit ratio for restaurant search queries exceeds 92%.
*   **Stripe Webhook Processing Latency:** Track Stripe Webhook Processing Latency with a target average below 150ms for merchant ledger entry clearance.
*   **Operational Uptime:** Achieve 99.99% operational uptime across AWS multi-AZ configurations with graceful degradation if POS partners fail.

### 1.5 Cross-Metro Event-Driven State Transitions

The Gateway translates high-level GraphQL mutations into granular gRPC commands for the Core Transaction & Ledger Service, managing cross-metro event-driven state transitions for the tripartite actor model.

*   **State Translation:** A GraphQL mutation for `generateVoucher` is translated into a gRPC command for the Ledger Service to reserve credits and generate a single-use virtual card token.
*   **Event Propagation:** Successful transactions are published to the Event Bus (owned by sibling artifact) for downstream processing, such as sending immutable transactional receipts to Contributors within 120 seconds of redemption.

### 1.6 GraphQL Schema Contracts for Client Application Layer and Operational Governance

This section defines the GraphQL schema contracts for the API Gateway & Orchestration Layer (SUR-D6FFF7036F), specifically targeting the Client Application Layer (SUR-E3E75E96CF) and Operational Governance (SUR-21B42056F5). These contracts facilitate high-throughput, low-latency CRUD operations for Recipient Discovery & Redemption (JNY-76281D3F3C), Merchant Primary Fulfillment (JNY-01DD5AC877), and Operator Governance & Liquidity Management (JNY-039CC03FAB). The schema is designed to support WCAG 2.1 AA standards for low-vision beneficiaries and handle bursty traffic patterns during peak donation cycles.

#### 1.6.1 Recipient Discovery & Redemption (JNY-76281D3F3C)

The Recipient Discovery & Redemption flow requires high-throughput read operations. The schema exposes:

*   `restaurants`: A paginated list of participating merchants, filterable by location, dietary flags, and distance. Optimized for Redis caching to ensure >92% hit ratio.
*   `voucher`: Generates a single-use, anonymized virtual credential for the selected partner. This mutation triggers the gRPC call to the Core Transaction & Ledger Service (SUR-DD602DB92C) to reserve credits.
*   `balance`: Returns the current anonymized credit balance for the authenticated Recipient (ACT-DC00FA84DC).

#### 1.6.2 Merchant Primary Fulfillment (JNY-01DD5AC877)

The Merchant Primary Fulfillment flow focuses on transaction clearing and settlement reporting:

*   `settlementReport`: Provides merchants with a summary of cleared transactions and pending payouts.
*   `operationalStatus`: Allows merchants to toggle real-time throttle parameters (e.g., maximum of 15 MealCredit orders per hour) to prevent structural overload.

### 1.7 Sibling Deferrals

*   **Core Domain Model & Data Schema:** Defers to sibling artifact for detailed data types and constraints.
*   **Service Boundaries & Business Logic:** Defers to sibling artifact for granular business rules and service boundaries.
*   **Integration Adapters & External Systems:** Defers to sibling artifact for specific POS and payment gateway integration details.
*   **Security Architecture & Access Control:** Defers to sibling artifact for detailed RBAC policies and access control matrices.
*   **Observability & Operational Governance:** Defers to sibling artifact for telemetry, logging, and alerting strategies.

---

## 2. gRPC Service Contracts for Core Transaction & Ledger Service

This section defines the gRPC service contracts for the API Gateway & Orchestration Layer (SUR-D6FFF7036F), specifically targeting the Core Transaction & Ledger Service (SUR-DD602DB92C). These contracts ensure strict serialization, low overhead, and strong contract enforcement for financial operations, preventing UI-layer leakage into the ledger.

### 2.1 Financial Transaction Processing (CAP-9CD814929D)

The gRPC service exposes methods for high-integrity financial operations:

*   `InitiateMicroDonation`: Initiates a micro-donation round-up (JNY-4FC1874968) from a Contributor (ACT-2A20B038B1).
*   `ClearPOSTransaction`: Processes a POS callback from a Merchant Partner (ACT-A14D3CDC5D) (JNY-01DD5AC877).
*   `SettlePayout`: Initiates the automated daily net payout to merchant accounts (JNY-40AA027A61).

### 2.2 Data Integrity & Audit

*   **Append-Only Ledger:** All financial transactions are recorded in an append-only, cryptographic audit ledger in Aurora Postgres (CON-199A4FEDC7).
*   **Immutable Receipts:** Contributors receive immutable transactional receipts within 120 seconds of redemption, strictly prohibiting transmission of any identifying beneficiary parameters.

### 2.3 Error Handling & Recovery

*   **Partial Failures:** Financial reconciliation is robust against partial failures, ensuring that credits issued but not cleared do not leave the ledger in an inconsistent state (CON-6A9F6E50CE).
*   **Error Codes:** Standard gRPC status codes are used, with specific application-level error codes for financial failures (e.g., `INSUFFICIENT_CREDITS`, `MCC_VIOLATION`).

---

## 3. Integration Patterns & External Systems

This section defines the integration patterns for connecting the API Gateway & Orchestration Layer (SUR-D6FFF7036F) to external systems, including payment gateways and POS integrations.

### 3.1 Payment Gateway Adapter (SUR-213BCD1816)

*   **Stripe Integration:** The Gateway integrates with Stripe for payment processing and virtual card issuance. Raw credit card data is handled exclusively by Stripe Elements/SDK at the client level.
*   **Webhook Processing:** Stripe webhooks are processed asynchronously to ensure low latency for client-facing operations. Target average processing latency is below 150ms (CON-D792CA1810).

### 3.2 POS Integration Middleware

*   **Zero-Footprint Integration:** The Gateway supports zero-footprint POS integration, allowing merchants to ingest orders via a standard web dashboard or edge device.
*   **Offline Resilience:** The system is designed to support offline fallback QR codes and barcode presentations that are scannable by standard, low-tech POS devices (CON-036979982A). Secure offline token storage using device-level SecureStore with cryptographic signatures is required to prevent token forgery in offline mode (CON-0346AE051D).

### 3.3 Event Bus Integration

*   **Event-Driven Architecture:** The Gateway publishes events to a central Event Bus for downstream processing. This includes transaction completion, voucher generation, and settlement events.
*   **Event Schema:** Events follow a standardized schema to ensure consistency across the system.

---

### 3.4 Telemetry & Logging

*   **Structured Logging:** All API Gateway interactions are logged with structured metadata, including actor ID, request ID, and latency.
*   **PII Masking:** Logs are automatically masked to ensure no PII is stored in production logs (CON-8A8949BE4A).
*   **CloudTrail Integration:** All infrastructure modifications and administrative ledger operations are pushed to unalterable AWS CloudTrail logs (CON-0B2D40801A).

### 3.5 Monitoring & Alerting

*   **Key Metrics:** The Gateway monitors key metrics including p99 latency, cache hit ratio, and webhook processing latency.
*   **Alerting:** Automated alerts are triggered for critical thresholds, such as credit pool utilization above 85% (CON-AA14245C03) or p99 latency exceeding 250ms (CON-14D783B5E5).
*   **Dashboards:** Operational dashboards provide real-time visibility into system health and performance.

## 4. Knowledge Gaps & Assumptions

The following items require resolution or assumption to complete the design.

*   **KNOWLEDGE_GAP:** Exact POS integration middleware strategy (Stripe Square vs. custom gRPC for Toast/Clover) is not yet established. Decision ID: DEC-ADD3B231CD.
*   **KNOWLEDGE_GAP:** Offline redemption resilience mechanism (JWT vs. local cryptographic nonce) is not yet established. Decision ID: DEC-7E9F9E778C.
*   **ASSUMPTION:** Virtual card limit enforcement relies on Stripe's backend MCC and geo-fencing rules, with pre-authorization validation pending further design. Decision ID: DEC-BDB9EA01B2.
*   **ASSUMPTION:** Directed Impact Flow processing is asynchronous with batch-settlement for unfulfilled funds. Decision ID: DEC-AD357A7A9A.
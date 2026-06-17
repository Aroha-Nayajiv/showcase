# Integration Adapters & External Systems

## 1. Hybrid GraphQL/gRPC Orchestration Layer Architecture

This section defines the architectural boundary and data contracts between the high-throughput GraphQL API Gateway (SUR-D6FFF7036F) and the asynchronous gRPC Core Transaction & Ledger Service (SUR-DD602DB92C). The architecture enforces a strict separation of concerns: GraphQL handles stateful, low-latency CRUD operations for the Client Application Layer (SUR-E3E75E96CF), while gRPC handles idempotent, cryptographically signed financial transactions to ensure PCI-DSS Level 1 and SOC2 Type II compliance.

### 1.1 Architectural Boundary & Flow

The system utilizes a Synchronous GraphQL for State, Asynchronous gRPC for Money pattern. This decouples the UI latency from the financial processing latency, ensuring the p99 latency target of < 250ms for Voucher Creation and Scanning Callback Processing (CON-14D783B5E5) is met even under 10,000 concurrent connections.

1. GraphQL Layer (SUR-D6FFF7036F): Receives client requests (e.g., requestVoucher, scanVoucher). Performs immediate validation (identity, balance, MCC restrictions) against the Redis Enterprise Cluster (CON-42B7E9919E) and DynamoDB state store.
2. Event Bus: Upon successful validation, the GraphQL layer publishes a TransactionInitiatedEvent to the internal event bus (e.g., AWS EventBridge/Kinesis). This event contains the idempotency_key and transaction_payload.
3. gRPC Layer (SUR-DD602DB92C): Consumes the event, performs the actual financial transaction (ledger update, Stripe Issuing API call), and writes to the append-only Aurora Postgres ledger (CON-199A4FEDC7).
4. State Update: The gRPC service publishes a TransactionCompletedEvent back to the event bus, which triggers a GraphQL subscription update to the client.

### 1.2 GraphQL API Contract (SUR-D6FFF7036F)

The GraphQL schema defines the high-throughput CRUD operations. All financial mutations must include an idempotency_key to prevent double-spending.

Mutation: requestVoucher
Input: `recipientId: ID!`, `merchantId: ID!`, `amount: Float!`, `idempotencyKey: String!`
Output: `VoucherRequest { voucherId: ID!, status: VoucherStatus!, estimatedClearingTime: Int! }`
Behavior: Validates recipientId against `Recipient (ACT-DC00FA84DC)` pool balance. Returns PENDING status immediately. Publishes TransactionInitiatedEvent.

Mutation: scanVoucher
Input: `voucherId: ID!`, `merchantId: ID!`, `transactionAmount: Float!`, `mccCode: String!`
Output: `ScanResult { success: Boolean!, message: String, transactionId: ID }`
Behavior: Validates voucherId signature and expiry. Checks mccCode against Pseudo-AnonymizedRedemption rules. Returns SUCCESS or DECLINED immediately. Publishes TransactionInitiatedEvent.

Subscription: transactionStatus
Input: `transactionId: ID!`
Output: `TransactionStatusUpdate { status: TransactionStatus, error: String, receiptUrl: String }`
Behavior: Real-time updates to the client as the gRPC service processes the transaction.

### 1.4 Error Handling & Idempotency

Idempotency: All gRPC financial RPCs must accept an idempotency_key (UUIDv4). If a request with the same key is received, the service returns the original result without re-processing.
Error Codes:
INVALID_IDEMPOTENCY_KEY: The key is malformed or missing.
INSUFFICIENT_FUNDS: Recipient pool balance is insufficient.
MCC_RESTRICTION_VIOLATION: Purchase is not allowed (e.g., alcohol).
STRIPE_API_ERROR: External payment gateway failure.
LEDGER_WRITE_FAILURE: Aurora Postgres write failure.
Retry Logic: GraphQL layer implements exponential backoff for transient gRPC errors (e.g., UNAVAILABLE).

### 1.5 Validation Criteria

Contract: The GraphQL schema must include idempotency_key for all financial mutations.
Contract: The gRPC contract must include idempotency_key in all financial RPCs.
Contract: The architecture must support p99 latency < 250ms for Voucher Creation and Scanning Callback Processing (CON-14D783B5E5).
Contract: The architecture must enforce PCI-DSS Level 1 compliance (CON-6EA64CF2A1).

This artifact provides the technical contracts for the hybrid GraphQL/gRPC orchestration layer, enabling the Development phase to implement the SUR-D6FFF7036F and SUR-DD602DB92C surfaces.

---

## 2. Plaid/Stripe Donor Round-Up Integration

This section defines the technical contracts for the Plaid and Stripe integration surfaces, specifically focusing on the Donor Round-Up Integration (Micro-DonationRound-Ups) and the enforcement of PCI-DSS Level 1 compliance via Stripe Elements and SDK.

### 2.1 PCI-DSS Level 1 Compliance Enforcement

To strictly enforce PCI-DSS Level 1 compliance, the platform must ensure that zero raw credit card data (PAN, CVV, or Expiry) ever touches the application servers. All donor funding interactions must utilize Stripe Elements and the Stripe SDK for client-side tokenization.

Integration Flow:
1. Client (Contributor Onboarding & Funding): The mobile app initializes Stripe Elements to securely collect card details.
2. Tokenization: Stripe SDK generates a secure payment method token, which is sent to the backend.
3. Ledger Update: The backend associates the token with the `Contributor (ACT-2A20B038B1)` profile and configures the Micro-DonationRound-Ups rule.

### 2.2 Micro-DonationRound-Ups Logic

The platform calculates fractional contributions based on configured rules. When a donor makes a purchase, the round-up amount is automatically transferred to the central pool.

Data Model:
- `donor_id`: UUID referencing `Contributor (ACT-2A20B038B1)`.
- `round_up_rule`: Configuration object defining the rounding threshold (e.g., round to nearest $1.00).
- `ledger_entry`: Immutable record of the micro-donation in Aurora Postgres (CON-199A4FEDC7).

### 2.3 Directed Impact Flows

Donors can assign funds globally, regionally by zip code, or to specific merchant property types like healthy grocery partners. This requires a DirectedImpactFlow configuration in the donor's profile.

Implementation:
- The backend validates the DirectedImpactFlow rules against the `Merchant Partner (ACT-A14D3CDC5D)` registry.
- Funds are allocated to the regional pool and tagged with the directed impact metadata.

---

## 3. Zero-Footprint POS Integration & Offline Resilience

This section defines the integration patterns for Merchant Partners (ACT-A14D3CDC5D) to accept MealCredits via zero-footprint integration or edge dashboard, ensuring offline QR/barcode scanning and secure token storage.

### 3.1 Offline QR/Barcode Scanning

To ensure frictionless clearing at POS, the system generates single-use, anonymized virtual credentials that can be presented as QR codes or barcodes.

Design:
- The `Recipient (ACT-DC00FA84DC)` app generates a QR code representing the `voucherId`.
- The POS system scans the QR code and sends a `scanVoucher` request to the GraphQL API.
- The system validates the voucher signature and balance before clearing the transaction.

### 3.2 Secure Token Storage

To prevent token forgery in offline mode, the system uses device-level SecureStore with cryptographic signatures.

Implementation:
- The mobile app stores the voucher token in the device's SecureStore.
- The token includes a cryptographic signature that can be verified by the POS system or the backend.

### 3.4 SOC2 Type II Control Environments

The platform operates within SOC2 Type II control environments, generating detailed tracking logs for all infrastructure and administrative changes.

Implementation:
- All infrastructure modifications are pushed to unalterable AWS CloudTrail logs (CON-0B2D40801A).
- Administrative ledger operations are logged in Aurora Postgres (CON-199A4FEDC7).

### 3.5 Data Privacy & Anonymization

Data privacy and anonymization must be enforced at the architectural level, not just application logic, to prevent PII leakage in production logs.

Implementation:
- Beneficiary demographic data is classified as strictly off-platform; the platform stores only derived, anonymized credits (CON-4DB27D2227).
- All beneficiary analytics map to high-entropy UUIDv4 keys, preventing PII reconstruction (CON-9DEA275205).

### 3.6 Financial Reconciliation

Financial reconciliation must be robust against partial failures, ensuring that credits issued but not cleared do not leave the ledger in an inconsistent state.

Implementation:
- The system uses an append-only, cryptographic audit ledger in Aurora Postgres (CON-199A4FEDC7).
- Reconciliation jobs run periodically to detect and resolve any discrepancies.

---

## 4. Discovery & Allocation Engine

This section defines the Discovery & Allocation Engine (CAP-264DA83096), which handles restaurant search queries and credit pool allocation.

### 4.1 Restaurant Search & Caching

The system ensures Redis Enterprise Cluster cache hit ratio for restaurant search queries exceeds 92% (CON-42B7E9919E).

Implementation:
- Restaurant data is cached in Redis Enterprise Cluster.
- Search queries are routed to the cache first, with a fallback to Aurora Postgres if the cache miss occurs.

### 4.2 Credit Pool Allocation

The system monitors Donation-to-Redemption Velocity (DRV) and Credit Pool Utilization Rate with automated alerts at 85% threshold (CON-AA14245C03).

Implementation:
- The engine tracks the credit pool utilization rate in real-time.
- If the threshold is exceeded, automated alerts are triggered for the `Operator (ACT-FE96DD3975)`.

---

### 4.3 Success Criteria Monitoring

- Donation-to-Redemption Velocity (DRV) under 14 days.
- Merchant Retention Rate (MRR) measured month-over-month.
- Credit Pool Utilization Rate triggers alerts if above 85%.
- Stripe Webhook Processing Latency average below 150ms.
- Cache Hit Ratio (CHR) for restaurant search queries above 92%.
- API Responsiveness p99 latency below 250ms under 10,000 concurrent connections.
- 99.99% operational uptime across AWS multi-AZ configurations.

### 4.4 Operational Governance

The `Operator (ACT-FE96DD3975)` is responsible for monitoring these success criteria and taking corrective action as needed.

Implementation:
- Dashboards are configured to display real-time metrics for all success criteria.
- Automated alerts are sent to the Operator team when thresholds are breached.

---

## 5. Cross-Artifact Alignment & Impact

This artifact aligns with the following sibling artifacts:
- `inception_product_strategy`: Defines the product vision and user journeys.
- `inception_technical_architecture`: Defines the high-level system architecture.
- `inception_compliance_risk`: Defines the compliance and risk management framework.
- `inception_operational_governance`: Defines the operational governance and success criteria.

Impact Propagation:
- Changes to the GraphQL/gRPC contracts in this artifact may require updates to the `Client Application Layer` (SUR-E3E75E96CF) and `Integration & Payment Gateway Adapter` (SUR-213BCD1816) artifacts.
- Changes to the compliance mechanisms may require updates to the `Compliance & Audit Governance` (CAP-421F3AD853) capability.

---

### 5.1 Knowledge Gaps

- KNOWLEDGE_GAP: Exact Stripe Issuing API rate limits and error handling behavior for virtual card creation - Stripe API documentation must be consulted.
- KNOWLEDGE_GAP: Specific POS middleware strategy (Stripe Square vs. custom gRPC) - Decision pending merchant partner requirements.

### 5.2 Assumptions

- ASSUMPTION: AWS EventBridge/Kinesis will be used as the internal event bus - Reversible pending infrastructure team confirmation.
- ASSUMPTION: Redis Enterprise Cluster will be used for caching - Reversible pending performance benchmarking results.
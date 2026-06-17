# Observability & Operational Governance

## 1. Hybrid GraphQL/gRPC Telemetry Instrumentation Strategy

This section defines the telemetry instrumentation strategy for the Daya platform, ensuring SOC2 Type II auditability and PCI-DSS Level 1 compliance across the hybrid GraphQL/gRPC architecture. The strategy mandates OpenTelemetry (OTel) as the standard SDK, with strict adherence to W3C TraceContext for trace propagation and rigorous PII scrubbing for all beneficiary data.

### 1.1 OpenTelemetry Resource Attributes

All spans emitted by the Daya platform services must include the following standardized resource attributes to ensure consistent filtering, aggregation, and compliance reporting:

| Attribute Key | Type | Description | Grounded Value / Example |
| :--- | :--- | :--- | :--- |
| `service.name` | String | The logical name of the service emitting the span. | `daya-graphql-gateway`, `daya-grpc-ledger` |
| `service.version` | String | The semantic version of the service. | `1.0.0` |
| `deployment.environment` | String | The deployment environment (e.g., dev, staging, prod). | `production` |
| `deployment.region` | String | The AWS region where the service is deployed. | `us-west-2` |
| `audit.event_type` | String | The high-level category of the event (e.g., financial, administrative). | `financial_transaction` |
| `actor.role` | String | The actor role associated with the event, if applicable. | `Contributor`, `Recipient`, `Merchant Partner` |
| `actor.id` | String | The high-entropy UUIDv4 key for the actor, ensuring absolute anonymization. | `550e8400-e29b-41d4-a716-446655440000` |

**KNOWLEDGE_GAP:** The exact mapping of `actor.role` values to the canonical actor IDs (e.g., `ACT-2A20B038B1` for Contributor) must be established by the Identity & Access Management artifact to ensure consistency across all telemetry data.

### 1.2 Trace Propagation Headers (W3C TraceContext)

To ensure end-to-end traceability across the hybrid GraphQL/gRPC architecture, all services must adhere to the W3C TraceContext standard for trace propagation.

*   **GraphQL Layer (SUR-E3E75E96CF):** The API Gateway & Orchestration Layer must inject the `traceparent` and `tracestate` headers into all outgoing HTTP requests to downstream GraphQL resolvers. Incoming requests from the Client Application Layer must be parsed to extract the trace context.
*   **gRPC Layer (SUR-DD602DB92C):** Internal service-to-service communication via gRPC must use the OTel gRPC propagator to seamlessly inject and extract trace context from gRPC metadata.
*   **External Integrations (SUR-213BCD1816):** When interacting with external systems (e.g., Stripe, Plaid), the trace context must be propagated via HTTP headers where supported. For systems that do not support W3C TraceContext, the trace ID must be captured as a custom attribute on the span.

### 1.3 Span Naming Conventions

To facilitate efficient querying and debugging, all spans must adhere to the following naming conventions:

*   **GraphQL Operations:** `GraphQL / <OperationType> / <TypeName> / <FieldName>`
    *   *Example:* `GraphQL / Mutation / Contributor / donate`
*   **gRPC Services:** `gRPC / <ServiceName> / <MethodName>`
    *   *Example:* `gRPC / LedgerService / CreateTransaction`
*   **External Calls:** `External / <ServiceName> / <Operation>`
    *   *Example:* `External / Stripe / CreatePaymentIntent`

### 1.4 PII Scrubbing and Anonymization

To comply with PCI-DSS Level 1 and absolute anonymization requirements (CON-8A8949BE4A, CON-9DEA275205), all spans must undergo a strict PII scrubbing process before export.

*   **Attribute Sanitization:** A dedicated OTel Span Processor must be implemented to strip any attribute containing PII (e.g., names, emails, raw credit card numbers) before the span leaves the application process.
*   **High-Entropy UUIDs:** All beneficiary analytics must map to high-entropy UUIDv4 keys, preventing PII reconstruction. The `actor.id` attribute must always contain the UUIDv4 key, never the PII.
*   **Financial Data:** Zero raw credit card data may touch application servers. All financial transactions must be instrumented using only tokenized references from the payment gateway (e.g., Stripe).

### 1.5 SOC2 Type II Auditability

To ensure SOC2 Type II auditability, the telemetry strategy must support the generation of immutable, cryptographically verifiable audit trails.

*   **Append-Only Ledger:** All financial transactions and administrative actions must be captured in an append-only, cryptographic audit ledger in Aurora Postgres (CON-199A4FEDC7). Telemetry spans must include a reference to the corresponding audit ledger entry.
*   **Trace Context Linking:** The trace context must be linked to the audit ledger entry to enable end-to-end traceability from the initial user action to the final financial settlement.
*   **Data Retention:** Telemetry data must be retained for a period sufficient to support SOC2 Type II audits, as defined by the Compliance & Audit Governance capability (CAP-421F3AD853).

**KNOWLEDGE_GAP:** The exact data retention period for telemetry data required to satisfy SOC2 Type II audits must be established by the Compliance & Audit Governance artifact.

## 2. Immutable Audit Ledger Schema

This section defines the schema for the append-only, cryptographic audit ledger in Aurora Postgres (CON-199A4FEDC7). This ledger serves as the single source of truth for all financial transactions and administrative actions, ensuring SOC2 Type II compliance.

### 2.1 Ledger Table Structure

The `audit_ledger` table must enforce immutability through database-level constraints and application-level append-only logic.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `ledger_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier for the ledger entry. |
| `event_type` | VARCHAR(50) | NOT NULL | High-level category (e.g., `FINANCIAL_TRANSACTION`, `ADMIN_ACTION`). |
| `actor_id` | UUID | NOT NULL | High-entropy UUIDv4 key for the actor (Contributor, Recipient, Merchant Partner, Operator). |
| `transaction_ref` | VARCHAR(255) | NOT NULL | Reference to the external transaction (e.g., Stripe PaymentIntent ID). |
| `amount_cents` | BIGINT | NOT NULL | Transaction amount in smallest currency unit. |
| `currency` | CHAR(3) | NOT NULL | ISO 4217 currency code (e.g., `USD`). |
| `metadata_json` | JSONB | DEFAULT '{}' | Additional context, including trace IDs and operational flags. |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Timestamp of the event. |
| `signature` | BYTEA | NOT NULL | Cryptographic signature of the event payload to ensure integrity. |

### 2.2 Immutability and Integrity

*   **Append-Only Enforcement:** Database triggers must prevent `UPDATE` and `DELETE` operations on the `audit_ledger` table. Only `INSERT` operations are permitted.
*   **Cryptographic Signatures:** Each entry must be signed using a rotating key managed by AWS KMS. The signature must cover the `event_type`, `actor_id`, `transaction_ref`, `amount_cents`, and `metadata_json` fields.
*   **Trace Context Linking:** The `metadata_json` field must include the `traceparent` header value to link the ledger entry back to the distributed trace.

### 2.3 Data Retention and Archival

*   **Retention Policy:** Telemetry and ledger data must be retained for a period sufficient to satisfy SOC2 Type II audit requirements.

## 3. Automated Alerting and Operational Governance

This section defines the automated alerting strategy for key operational metrics, ensuring proactive management of liquidity and system health.

### 3.1 Key Performance Indicators (KPIs)

The following KPIs must be monitored with automated alerting:

*   **Donation-to-Redemption Velocity (DRV):** The time elapsed between a donor's contribution and a beneficiary's redemption.
    *   *Target:* Under 14 days.
    *   *Alert Threshold:* Alert if DRV exceeds 14 days for any regional pool.
*   **Credit Pool Utilization Rate:** The percentage of the total regional credit pool that has been issued but not yet redeemed.
    *   *Alert Threshold:* Alert if utilization exceeds 85% to prevent liquidity exhaustion.
*   **Stripe Webhook Processing Latency:** The time taken to process incoming Stripe webhooks.
    *   *Target:* Average below 150ms.
    *   *Alert Threshold:* Alert if average latency exceeds 150ms over a 5-minute window.
*   **Cache Hit Ratio (CHR):** The ratio of successful Redis cache lookups to total lookups for restaurant search queries.
    *   *Target:* Above 92%.
    *   *Alert Threshold:* Alert if CHR drops below 92%.
*   **API Responsiveness (p99 Latency):** The 99th percentile latency for API requests.
    *   *Target:* Below 250ms under 10,000 concurrent connections.
    *   *Alert Threshold:* Alert if p99 latency exceeds 250ms.
*   **Operational Uptime:** The percentage of time the system is available.
    *   *Target:* 99.99% across AWS multi-AZ configurations.
    *   *Alert Threshold:* Alert on any downtime event.

### 3.2 Alerting Channels and Escalation

*   **Channels:** Alerts must be routed to PagerDuty for critical events (e.g., liquidity exhaustion, API latency spikes) and Slack for informational events (e.g., utilization rate warnings).
*   **Escalation:** Critical alerts must include runbook links to the relevant operational procedures (e.g., Merchant Operational Recovery, Contributor Error & Recovery).

### 3.3 Dashboarding

*   **Operational Dashboard:** A real-time dashboard must be maintained, displaying the above KPIs, system health status, and active incident tickets.
*   **Access Control:** Dashboard access must be restricted to Operators (ACT-FE96DD3975) and relevant stakeholders.

## 4. Integration & Payment Gateway Adapter Telemetry

This section details the specific telemetry requirements for the Integration & Payment Gateway Adapter (SUR-213BCD1816), ensuring end-to-end visibility into external financial flows.

### 4.1 Stripe Integration

*   **Webhook Processing:** All incoming Stripe webhooks must be instrumented with a span that captures the webhook event type, payload size, and processing latency.
*   **Payment Intent Creation:** Spans must be generated for each `PaymentIntent` creation, capturing the donor ID (anonymized), amount, and any directed impact flags.
*   **Error Handling:** Failed webhook deliveries or payment intent creations must trigger high-priority alerts and be logged to the audit ledger.

## 5. Operational Runbooks and Incident Response

This section defines the operational runbooks and incident response procedures linked to the alerting strategy.

### 5.1 Liquidity Exhaustion Runbook

*   **Trigger:** Credit Pool Utilization Rate exceeds 85%.
*   **Actions:**
    1.  Alert Operator (ACT-FE96DD3975) via PagerDuty.
    2.  Investigate the cause of high redemption velocity.
    3.  If necessary, trigger emergency funding protocols or pause new credit issuance.
    4.  Communicate with NGO partners to manage beneficiary expectations.

### 5.3 Payment Gateway Failure Runbook

*   **Trigger:** Stripe Webhook Processing Latency exceeds 150ms or failure rate increases.
*   **Actions:**
    1.  Alert Engineering and Finance teams.
    2.  Check Stripe status page and API health.
    3.  Implement fallback mechanisms if available.
    4.  Reconcile any missed transactions manually if necessary.

### 6.2 Future Enhancements

*   **Advanced Analytics Dashboard:** A dedicated dashboard for deep-dive analysis of donation patterns and merchant performance will be developed in a future phase.
*   **Multi-Currency Support:** Dynamic configuration of tax rules and localization for multi-currency operations will be addressed in a future phase (CON-D2D56B8C01, CON-FB06A81917).
*   **Cross-Border Data Compliance:** Strategies for cross-border data compliance if NGOs operate in jurisdictions requiring strict data localization will be developed in a future phase (CON-64DE3440F4).
# Operational Governance & Success Criteria

### 1.1 Liquidity & Credit Pool Governance
*   **Decision Right:** Allocation of emergency credit pools, adjustment of Donation-to-Redemption Velocity (DRV) thresholds, and management of Credit Pool Utilization Rate alerts.
*   **Owner:** Operator (ACT-FE96DD3975) in coordination with local NGO partners.
*   **Constraint:** Unused emergency credits must auto-roll back to the regional pool after 72 hours (CON-AEB925BD12). The Operator must monitor Credit Pool Utilization Rate and trigger alerts at the 85% threshold (CON-AA14245C03).

### 1.2 Merchant Partner Lifecycle & Fulfillment
*   **Decision Right:** Approval of new Merchant Partners (ACT-A14D3CDC5D), validation of POS integration standards, and enforcement of Merchant Category Code (MCC) restrictions for eligible purchases.
*   **Owner:** Operator (ACT-FE96DD3975) via the Partner & Merchant Lifecycle Management capability (CAP-78C64ECFE0).
*   **Constraint:** Merchant Partners must be able to toggle real-time throttle parameters to prevent structural overload. Ineligible purchases (alcohol, non-food) must be dropped at the Stripe network layer.

### 1.3 Contributor Funding & Directed Impact
*   **Decision Right:** Configuration of Micro-Donation Round-Ups via Plaid/Stripe, setting Directed Impact Flows (global, regional, or specific merchant types), and validation of contributor funding sources.
*   **Owner:** Contributor (ACT-2A20B038B1) with Operator oversight for anti-money laundering (AML) compliance.
*   **Constraint:** Contributors must receive immutable transactional receipts within 120 seconds of redemption. No identifying beneficiary parameters may be transmitted to the Contributor.

### 1.4 Recipient Anonymization & Discovery
*   **Decision Right:** Management of the Discovery & Allocation Engine (CAP-264DA83096) to ensure location-based recommendations are sorted by distance and dietary flags without exposing PII.
*   **Owner:** Operator (ACT-FE96DD3975) with strict adherence to Absolute Anonymization protocols.
*   **Constraint:** Beneficiary demographic data must be strictly off-platform. The platform stores only derived, anonymized credits mapped to high-entropy UUIDv4 keys (CON-9DEA275205). No PII (legal name, domestic background) may be stored on-platform or in production logs.

## 2.0 Binding Operational Constraints

The following constraints are non-negotiable and must be enforced by the platform's architecture and operational procedures. They are derived from regulatory requirements, security mandates, and business integrity.

### 2.1 PCI-DSS Level 1 Compliance
*   **Constraint:** Zero raw credit card data may touch application servers. All payment processing must be handled via Stripe Elements and SDK (CON-6EA64CF2A1). The platform must maintain SOC2 Type II control environments (CON-0A6423E6B0).
*   **Operational Impact:** All financial transactions must be processed through the Financial Transaction Processing capability (CAP-9CD814929D) using Stripe Custom Connected Accounts and Issuing API.

### 2.2 Absolute Beneficiary Anonymization
*   **Constraint:** Beneficiary data must be absolutely anonymized. Client-side generation of clean tokenized vouchers must be visually identical to consumer gift cards, ensuring no demographic or identity data crosses into production logs (CON-8A8949BE4A).
*   **Operational Impact:** Analytics must map to high-entropy UUIDv4 keys. Regulatory compliance requires maintainable audit trails that link financial flows to high-level events without linking to individual beneficiaries (CON-DE21E04933).

### 2.3 Financial Reconciliation & Ledger Integrity
*   **Constraint:** Financial reconciliation must be robust against partial failures, ensuring credits issued but not cleared do not leave the ledger in an inconsistent state (CON-6A9F6E50CE). An append-only, cryptographic audit ledger must be maintained in Aurora Postgres for all financial transactions (CON-199A4FEDC7).
*   **Operational Impact:** Daily batch processing must reconcile all authorized transactions for the previous period, transferring funds to Merchant Partners via secure rails within 24 business hours (JNY-40AA027A61).

### 2.4 System Scalability & Performance
*   **Constraint:** System scalability must account for bursty traffic patterns during peak donation cycles or redemption events without degrading latency (CON-873877C003). The platform must maintain p99 latency below 250ms for Voucher Creation and Scanning Callback Processing under 10,000 concurrent connections (CON-14D783B5E5).
*   **Operational Impact:** The Redis Enterprise Cluster cache hit ratio for restaurant search queries must exceed 92% (CON-42B7E9919E). Stripe Webhook Processing Latency must average below 150ms for merchant ledger entry clearance (CON-D792CA1810).

## 3.0 Decision Rights Matrix

This matrix defines the primary decision owners and their cross-functional dependencies for the operational lifecycle.

| Decision Domain | Primary Owner | Cross-Functional Dependencies | Binding Constraints |
| :--- | :--- | :--- | :--- |
| Credit Pool Allocation | Operator (ACT-FE96DD3975) | Recipient (ACT-DC00FA84DC), NGO Partners | Auto-rollback after 72 hours; Alert at 85% utilization |
| Merchant Onboarding | Operator (ACT-FE96DD3975) | Merchant Partner (ACT-A14D3CDC5D) | POS integration validation; MCC restriction enforcement |
| Funding Configuration | Contributor (ACT-2A20B038B1) | Operator (ACT-FE96DD3975) | AML compliance; Immutable receipt within 120s |
| Anonymization Protocol | Operator (ACT-FE96DD3975) | Recipient (ACT-DC00FA84DC) | No PII in logs; UUIDv4 mapping; PCI-DSS Level 1 |

## 4.0 Success Criteria and Measurable Signals

The following measurable signals validate operational health and project success. These metrics are derived directly from the project's success criteria and must be monitored continuously.

### 4.1 Donation-to-Redemption Velocity (DRV)
*   **Metric:** Time elapsed between donor contribution and beneficiary redemption.
*   **Target:** Under 14 days.
*   **Owner:** Operator (ACT-FE96DD3975).
*   **Rationale:** Ensures liquidity is actively circulating and not stagnating in the central pool.

### 4.2 Merchant Retention Rate (MRR)
*   **Metric:** Month-over-month percentage of active Merchant Partners (ACT-A14D3CDC5D) continuing to accept MealCredits.
*   **Target:** [KNOWLEDGE_GAP: Specific MRR target percentage - Owner: Operations/Finance must establish baseline before Design phase].
*   **Rationale:** Validates the commercial viability and value proposition for the Merchant Partner ecosystem.

### 4.3 Credit Pool Utilization Rate
*   **Metric:** Percentage of total available emergency credits currently allocated or in use.
*   **Target:** Automated alerts triggered at 85% threshold (CON-AA14245C03).
*   **Owner:** Operator (ACT-FE96DD3975).
*   **Rationale:** Prevents liquidity exhaustion and ensures sufficient funds are available for peak redemption events.

### 4.4 Stripe Webhook Processing Latency
*   **Metric:** Average time to process Stripe webhooks for merchant ledger entry clearance.
*   **Target:** Below 150ms (CON-D792CA1810).
*   **Owner:** Operator (ACT-FE96DD3975).
*   **Rationale:** Ensures real-time financial reconciliation and prevents ledger inconsistencies.

### 4.5 Cache Hit Ratio (CHR)
*   **Metric:** Percentage of restaurant search queries served directly from the Redis Enterprise Cluster cache.
*   **Target:** Above 92% (CON-42B7E9919E).
*   **Owner:** Operator (ACT-FE96DD3975).
*   **Rationale:** Critical for maintaining low latency and system scalability during high-traffic discovery events.

### 4.6 API Responsiveness
*   **Metric:** p99 latency for Voucher Creation and Scanning Callback Processing.
*   **Target:** Below 250ms under 10,000 concurrent connections (CON-14D783B5E5).
*   **Owner:** Operator (ACT-FE96DD3975).
*   **Rationale:** Guarantees frictionless redemption experiences for Recipients (ACT-DC00FA84DC) even during peak donation cycles.

### 4.7 Operational Uptime
*   **Metric:** Percentage of time the platform is available across AWS multi-AZ configurations.
*   **Target:** 99.99% (CON-8BD1F56A44).
*   **Owner:** Operator (ACT-FE96DD3975).
*   **Rationale:** Ensures continuous access for Contributors, Recipients, and Merchant Partners, with graceful degradation if POS partners fail.

## 5.0 Risk Register

This section identifies critical operational risks and their mitigation strategies. Risks are categorized by their primary impact domain.

| Risk ID | Risk Description | Impact Domain | Mitigation Strategy | Owner |
| :--- | :--- | :--- | :--- | :--- |
| RISK-001 | Money Transmission License (MTL) non-compliance in target metro areas (SF, NYC, Chicago). | Regulatory | [KNOWLEDGE_GAP: Specific bonding requirements for MTLs in SF, NYC, and Chicago - Legal/Operator must resolve these before Design phase]. | Operator (ACT-FE96DD3975) |
| RISK-002 | Fraudulent credit card usage by Contributors (ACT-2A20B038B1) to generate unauthorized MealCredits. | Financial | Enforce strict AML/KYC checks via Plaid/Stripe; implement velocity limits on round-up configurations. | Operator (ACT-FE96DD3975) |
| RISK-003 | POS integration failures leading to redemption friction for Recipients (ACT-DC00FA84DC). | Operational | Develop robust offline fallback QR codes and barcode presentations scannable by standard, low-tech POS devices (CON-036979982A). | Operator (ACT-FE96DD3975) |
| RISK-004 | Data privacy breach exposing beneficiary demographic data. | Security | Enforce absolute anonymization; client-side generation of tokenized vouchers; strict off-platform storage of PII (CON-8A8949BE4A). | Operator (ACT-FE96DD3975) |
| RISK-005 | System latency degradation during peak donation cycles impacting p99 performance. | Performance | Implement Redis Enterprise Cluster caching for search queries; optimize Aurora Postgres ledger writes. | Operator (ACT-FE96DD3975) |
| RISK-006 | Merchant Partner (ACT-A14D3CDC5D) churn due to slow settlement payouts. | Commercial | Ensure daily batch processing reconciles transactions and transfers funds within 24 business hours (JNY-40AA027A61). | Operator (ACT-FE96DD3975) |
| RISK-007 | Cross-border data localization violations if NGOs operate in restricted jurisdictions. | Compliance | [KNOWLEDGE_GAP: Specific data localization requirements for target NGO jurisdictions - Legal/Compliance must map these before Design phase]. | Operator (ACT-FE96DD3975) |

## 6.0 Unresolved Decision Gaps

The following decisions must be resolved by the designated owners before the Design phase can proceed. These gaps represent critical dependencies for operational readiness.

*   **DEC-BDB9EA01B2:** Should the virtual card limit enforcement rely solely on Stripe's backend merchant-category-code (MCC) and geo-fencing rules, or require a pre-authorization validation step from the Dayaa backend to enforce NGO-specific spending caps before card issuance?
*   **DEC-7E9F9E778C:** For offline redemption resilience, should the system store a time-bound, signed JWT voucher on the client's SecureStore that requires network connectivity for verification (online-only when available), or implement a complex offline-counter mechanism with local cryptographic nonce tracking to allow offline clearing?
*   **DEC-ADD3B231CD:** Which specific POS integration middleware strategy will be adopted: using Stripe's existing Square POS integration vs. building custom gRPC adapters for Toast and Clover to ensure consistent event streaming into the event-driven architecture?
*   **DEC-AD357A7A9A:** Does the 'Directed Impact Flow' (FR-DON-02) require real-time filtering of eligible merchants at the point of donation, or can it be processed asynchronously with a batch-settlement mechanism for unfulfilled directed funds?
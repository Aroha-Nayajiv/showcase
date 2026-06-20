# Product Vision and Scope Boundaries

## 1. Core Mission and Value Proposition

The MealCredit platform is a tripartite social-impact fintech marketplace designed to decouple food assistance from social stigma. By converting real-time financial micro-donations into fractional, anonymous culinary credits, the platform enables beneficiaries to spend exactly like cash or standard gift cards at commercial restaurant establishments. This approach ensures dignity by design, eliminating the visibility of aid status during transactions.

## 2. Tripartite Actor Model

The platform operates by connecting three primary actor groups through local non-profit organizations:

*   **Funders (Donors):** Individuals or entities who contribute via micro-donation round-ups or direct transfers. They receive immutable, anonymized impact receipts within 120 seconds of redemption, ensuring transparency without compromising beneficiary privacy.
*   **Recipients (Beneficiaries):** Vulnerable individuals who receive anonymous, tokenized culinary credits. Their access is managed via a mobile interface that functions identically to consumer gift cards, utilizing Apple/Google Wallet passes or barcodes for frictionless POS clearing.
*   **Providers (Merchant Partners):** Commercial restaurants and food establishments that accept MealCredits. They benefit from automated daily net payouts via Stripe Connect and real-time transactional liquidity, with operational throttle limits to prevent structural overload.

### 3.1 Funder (Donor) Role and Boundaries
The Funder is the capital source for the platform, converting micro-donations into culinary credits.

**Decision Rights:**
*   **Allocation Strategy:** The Funder determines the flow of funds via Directed Impact Flows (e.g., global pool, specific zip code, or specific merchant types like healthy grocery partners).
*   **Transparency Preferences:** The Funder configures the level of impact reporting they receive, strictly limited to anonymized aggregate data.

**Operational Boundaries:**
*   **Anonymity Constraint:** The Funder is strictly prohibited from accessing any PII, demographic data, or identity information of the Recipient. All interactions are mediated through high-entropy UUIDv4 keys.
*   **Financial Scope:** The Funder's interaction is limited to funding via Plaid/Stripe micro-donation round-ups. They do not interact with Providers or Facilitators.

**Key Interactions:**
*   **With Platform:** Funds are allocated to regional credit pools (SF, NYC, Chicago). The Funder receives immutable transactional receipts within 120 seconds of a Recipient's redemption.
*   **With Recipient:** Zero direct interaction. The relationship is strictly zero-knowledge (CON-705CB41089).

### 3.5 Cross-Actor Interaction Matrix

| Interaction | Actor A | Actor B | Description | Constraint |
| :--- | :--- | :--- | :--- | :--- |
| Funding | Funder | Platform | Converts round-ups to credits; allocates to regional pools. | N/A |
| Vetting | Facilitator | Recipient | Stores cryptographic profile; no PII. | Recipient PII hidden from Platform/Funder |
| Allocation | Facilitator | Platform | Assigns credits to Recipient UUID. | N/A |
| Redemption | Recipient | Provider | Validates token; clears via Stripe Issuing. | Funder/Recipient identities hidden from each other and Provider |
| Settlement | Provider | Platform | Automated payout via Stripe Connect. | N/A |
| Reporting | Funder | Platform | Provides anonymized aggregate impact data. | Recipient PII never exposed |

### 3.7 PCI-DSS Level 1 and Financial Rails

As a platform processing and routing financial transactions via Stripe Issuing and Stripe Connect, MealCredit must adhere to PCI-DSS Level 1 standards. This is the highest level of certification, required for entities processing over 6 million transactions annually or those that have suffered a major data breach.

*   **Zero Raw Card Data Storage:** The platform must never store, process, or transmit raw Primary Account Numbers (PANs). All card data entry must be handled exclusively via Stripe Elements and the Stripe SDK, ensuring data flows directly from the client to Stripe's PCI-DSS certified environment.
*   **Virtual Card Tokenization:** Beneficiary credits are issued as single-use virtual card tokens via Stripe Issuing. These tokens are locked to specific Merchant Category Codes (MCCs) related to food and dining, and to specific geographic locations (SF, NYC, Chicago). The platform must ensure these tokens are cryptographically signed and validated in real-time during the scanning callback.
*   **Stripe Webhook Latency:** To prevent double-spending and ensure real-time ledger synchronization, the platform must process Stripe Webhook events (card taps, merchant ledger entries) with an average latency of less than 150ms (CON-521D9D9565). This requires an asynchronous architecture for high-throughput financial transactions.

### 3.8 Data Privacy and Anonymization (CCPA/GDPR)

MealCredit's core value proposition is decoupling food assistance from social stigma. This requires absolute anonymization of beneficiary data, exceeding standard GDPR/CCPA requirements.

*   **Absolute PII Anonymization:** Beneficiary demographic status, legal name, and domestic background must not cross into production logs or database tables (CON-1BC6B8851E). All beneficiary interactions are routed via high-entropy UUIDv4 keys (CON-2DE50DC545). No PII is ever visible to Funders or Providers.
*   **Right-to-Erasure Workflows:** The platform must support automated right-to-erasure workflows for NGO-managed profiles. However, financial ledger entries must be retained indefinitely in Aurora Postgres for compliance purposes, purging only transient transactional state (CON-3E7B720F8F). This creates a tension between privacy and financial auditability that must be resolved via strict data segregation.
*   **Multi-Tenant Data Segregation:** To prevent cross-tenant visibility across SF, NYC, and Chicago, the platform must enforce strict data segregation in Amazon Aurora Postgres and DynamoDB (CON-2BCB3D9CF7). This includes row-level security policies and tenant-scoped access keys.

### 3.9 Financial Licensing and Regulatory Compliance

MealCredit acts as an intermediary between donors, NGOs, and merchants, moving funds via Stripe Issuing and Stripe Connect. This triggers specific financial licensing requirements.

*   **Money Transmitter Licenses (MTL):** The platform must ensure compliance with money transmitter laws in all operating jurisdictions (CA, NY, IL). This is managed via Stripe's regulatory framework, but MealCredit must maintain explicit records of its role as a technology provider rather than a direct money transmitter where possible.
*   **SOC2 Type II Structural Planning:** The platform must achieve SOC2 Type II structural planning and auditing via unalterable AWS CloudTrail logs for all infrastructure and API modifications (CON-D3DA4E5E71). All administrative ledger operations and API adjustments must be logged to AWS CloudTrail for immutable audit trails (CON-7655D2A8DE).
*   **Automated Regulatory Reporting:** The platform must generate automated regulatory reports to satisfy financial compliance requirements without manual intervention (CON-6431109B98). This includes transaction summaries, fee disclosures, and anonymized impact reports for Funders.

### 3.10 Cross-Reference to Sibling Artifacts

*   **Compliance, Privacy, and Governance Framework:** This artifact defers to the sibling artifact for the full treatment of policy matrices, audit schedules, and governance bodies.
*   **Risk Register and Technical Constraints:** This artifact defers to the sibling artifact for the full treatment of risk mitigation strategies and technical failure modes.
*   **Operating Model and Stakeholder Alignment:** This artifact defers to the sibling artifact for the full treatment of stakeholder decision rights and operational workflows.

## 4. Key Success Signals

### 4.1 Liquidity and Velocity Metrics

These metrics track the efficiency of the financial rails and the engagement of the Funder and Recipient actor groups.

*   **Donation-to-Redemption Velocity (DRV)**
    *   **Definition:** The average time elapsed between a Funder's micro-donation round-up and the subsequent redemption of those funds by a Recipient at a Provider location.
    *   **Target:** < 14 days.
    *   **Rationale:** Rapid velocity ensures that the credit pool remains liquid and that the social impact is realized quickly, reinforcing the value proposition for Funders and ensuring Recipients have immediate access to resources.
    *   **Measurement:** Aggregated timestamp delta between `Stripe Webhook` confirmation of donation and `Service Redemption and Clearing` completion event.

*   **Credit Pool Utilization Rate**
    *   **Definition:** The percentage of the total regional credit pool that has been actively redeemed within a given reporting period.
    *   **Target:** Maintain utilization between 60% and 85%.
    *   **Constraint:** Trigger operational alerts if utilization exceeds 85% to prevent ledger stagnation and ensure sufficient liquidity for new Recipients. If utilization drops below 60%, trigger Funder engagement campaigns.
    *   **Measurement:** `(Total Redeemed Credits / Total Issued Credits) * 100` per metro footprint.

### 4.2 Operational and Technical Performance

These metrics ensure the platform meets the high-availability and low-latency requirements necessary for a fintech marketplace.

*   **Operational Uptime**
    *   **Target:** 99.99% availability across AWS multi-AZ configurations.
    *   **Rationale:** Critical for maintaining trust with Provider partners and ensuring Recipients can access their credentials at any time.
    *   **Measurement:** AWS CloudWatch synthetic monitoring and CloudTrail audit logs.

*   **API Responsiveness and Latency**
    *   **Target:** p99 latency < 250ms for critical APIs (Voucher Creation, Scanning Callback) under 10,000 concurrent connections.
    *   **Target:** Stripe Webhook Processing Latency < 150ms average.
    *   **Rationale:** Ensures frictionless redemption experiences at POS terminals and real-time synchronization between virtual credit issuance and physical clearing.
    *   **Measurement:** Distributed tracing via AWS X-Ray and Prometheus metrics for gRPC and GraphQL endpoints.

*   **Cache Hit Ratio (CHR)**
    *   **Target:** > 92% for restaurant search queries via the Redis location-cache layer.
    *   **Rationale:** Optimizes performance for the Recipient's discovery experience and reduces load on the Aurora Postgres ledger.
    *   **Measurement:** Redis `INFO stats` and application-level cache miss logging.

### 4.3 Stakeholder and Ecosystem Health

These metrics track the adoption and retention of the three primary actor groups.

*   **Merchant Retention Rate (MRR)**
    *   **Definition:** The percentage of Provider partners (Restaurants) that remain active and accepting MealCredits month-over-month.
    *   **Target:** > 90% monthly retention.
    *   **Rationale:** High retention indicates that the zero-footprint POS integration and automated daily net payouts via Stripe Connect are providing sufficient value to commercial partners.

*   **Funder Engagement and Transparency**
    *   **Target:** 100% of Funders receive immutable transactional receipts within 120 seconds of redemption.
    *   **Rationale:** Immediate transparency is a core trust signal for the Funder actor group, validating the 'Directed Impact Flows' capability.

### 4.4 Knowledge Gaps and Assumptions

*   **KNOWLEDGE_GAP:** Specific baseline values for Merchant Retention Rate (MRR) in the social-impact fintech sector are not yet established. Industry benchmarks for general gift-card platforms may not apply directly to the NGO-mediated model. Legal and Operations leads must define the initial baseline target before ratification.
*   **ASSUMPTION:** The 14-day DRV target assumes that NGO Facilitators (ACT-436E6BA706) allocate credits to Recipients within 48 hours of receipt. If NGO allocation cycles are longer (e.g., weekly), the DRV will be artificially inflated by NGO processing time rather than platform inefficiency. This assumption must be validated against NGO operational workflows.
*   **ASSUMPTION:** The 99.99% uptime target is achievable with the proposed AWS multi-AZ architecture and serverless components (Lambda, API Gateway) without requiring dedicated provisioned capacity for peak loads. This assumption should be validated during the Design phase with capacity planning models.

This section defines the explicit operational boundaries for the MealCredit platform, ensuring that the initial 50,000 MAU rollout across San Francisco, New York, and Chicago remains focused on the core tripartite value exchange while preventing scope creep into non-essential features.

### 4.5 In-Scope Features (MVP & Phase 1)

The following capabilities are strictly in-scope for the initial release and must be fully implemented to satisfy the core product vision:

*   **Multi-Modal Voucher Access (CON-EF1F2F2EBE):** The platform must support three distinct redemption methods to ensure accessibility:
    1.  Apple/Google Wallet Passes: Primary method for iOS and Android users, utilizing hardware-backed SecureStore (CON-460D6EBABD) for offline token validity.
    2.  1D Barcodes: Fallback for legacy POS systems that cannot scan QR codes.
    3.  2D Barcodes (QR): Standard method for modern POS terminals.
*   **Pseudo-Anonymized Redemption (CON-8F05AD69D4):** The system must generate single-use virtual card tokens via Stripe Issuing that are locked to specific Merchant Category Codes (MCC) and location. These tokens must clear via standard banking networks while stripping all PII from the transaction payload.
*   **Real-Time Scanning Callback (CON-FD2AD44598):** The API must process scanning callbacks with a p99 latency of < 250ms under 10,000 concurrent connections. The system must enforce real-time synchronization between virtual credit issuance and physical POS terminal clearing to prevent double-spending.
*   **Dynamic Liquidity Management (CON-CA1E9CC141):** The platform must balance credit pool availability against redemption velocity. Unused emergency credits must automatically roll back to the central regional pool after 72 hours of expiration to prevent ledger stagnation.
*   **Multi-Tenant Data Segregation (CON-2BCB3D9CF7):** The architecture must enforce strict data isolation in Aurora Postgres and DynamoDB to prevent cross-tenant visibility across the SF, NYC, and Chicago footprints.
*   **Provider & Fulfillment Management (CAP-D96776E7F7):** Providers (Restaurants) must be able to toggle real-time throttle parameters (e.g., max 15 MealCredit orders per hour) to prevent structural overload on their POS systems.
*   **Automated Regulatory Reporting (CON-6431109B98):** The system must generate immutable audit trail entries for all financial transactions to satisfy SOC2 Type II structural planning and PCI-DSS Level 1 compliance requirements.

### 4.6 Out-of-Scope Elements (Explicit Exclusions)

To prevent scope creep and ensure the MVP delivers on its core mission, the following are explicitly excluded from the initial release:

*   **Direct Cash Disbursement:** The platform will never disburse direct cash to beneficiaries. All assistance is strictly in the form of fractional, anonymous culinary credits.
*   **International Expansion:** The initial scope is strictly limited to the three metropolitan footprints (SF, NYC, Chicago). No international payment rails or multi-currency support is included.
*   **Physical POS Hardware Manufacturing:** The platform relies on existing POS integrations (Toast, Clover, Square) or a lightweight edge dashboard. No proprietary hardware is developed or distributed.
*   **Beneficiary Identity Linking for Funders:** Funders (Donors) will never receive identifying information about Recipients (Beneficiaries). All impact reporting is strictly aggregated and anonymized.
*   **NGO Operational ERP:** The platform does not provide full enterprise resource planning for NGOs. NGOs only use the platform for beneficiary vetting and credit allocation, not for their internal financial management.

### 4.7 Scope Boundary Governance

*   **Decision Rights:** Any feature request that falls outside the in-scope list must be formally rejected or deferred to Phase 2 unless it directly addresses a critical compliance gap (e.g., new PCI-DSS requirements).
*   **Stakeholder Alignment:** The scope is aligned with the primary value proposition of decoupling food assistance from social stigma. Any feature that introduces PII leakage or increases redemption friction is out of scope.
*   **Technical Constraints:** The scope is bounded by the target technology stack (Expo v51, Next.js, Go/gRPC, AWS). Any feature requiring a technology outside this stack must be justified as a critical dependency.
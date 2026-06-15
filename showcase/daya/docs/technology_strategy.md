# Technology Strategy & Architectural Foundations

## 1. Executive Summary & Strategic Intent

The Daya (MealCredit) platform is a tripartite, social-impact fintech marketplace connecting Donors, Beneficiaries, and Merchant Partners (Restaurants) through local non-profit organizations (NGOs). The platform mission is to decouple food assistance from social stigma by converting real-time financial micro-donations into fractional, anonymous culinary credits that are spent exactly like cash or standard gift cards at commercial restaurant establishments.

This artifact establishes the technical bedrock for the platform, defining the hybrid API orchestration model, architectural surfaces, data fabric, and compliance obligations. The strategy mandates a hybrid API Gateway utilizing GraphQL for CRUD operations and asynchronous gRPC (Go) for high-throughput financial and POS transactions, ensuring sub-150ms clearing times and strict PCI-DSS Level 1 compliance.

## 2. Architectural Strategy & Hybrid API Gateway

### 2.1 Hybrid API Orchestration Model

To balance the flexibility required for complex beneficiary discovery with the low-latency, high-throughput demands of financial clearing, the platform employs a dual-protocol architecture routed through the Hybrid API Gateway (SUR-6930995FDB).

*   **GraphQL (CRUD & Discovery):** The GraphQL layer serves as the primary interface for the Consumer & Partner Mobile/Web Interfaces (SUR-33611C2BCB) and the Next.js Edge Dashboards (SUR-182248FE43). It handles complex, nested queries for beneficiary geo-discovery, merchant partner catalogs, and donor impact reporting. This layer abstracts the underlying microservices, allowing the Expo Mobile Client (SUR-49E785B31C) to fetch exactly the data needed for a specific view without over-fetching.
*   **gRPC (Financial & POS Transactions):** The gRPC layer, implemented in Go, handles the high-frequency, latency-sensitive financial transactions. This includes the generation of single-use virtual card tokens, real-time balance checks against the Aurora Ledger, and the processing of Stripe Webhooks. By using a binary protocol over HTTP/2, gRPC minimizes payload size and connection overhead, ensuring that the Financial Transaction Engine (CAP-38C04FAFE0) can sustain the required throughput during peak POS windows.

### 2.2 Stripe Integration Layer & Clearing

The Stripe Integration Layer (SUR-D6063C9A12) is the critical bridge between the platform's internal ledger and external banking networks. 

*   **Token Generation:** Upon beneficiary redemption, the system queries the Financial Ledger & Clearing (CAP-0E02003C70) to verify pool balance. It then requests a single-use virtual card token from Stripe Issuing. This token is pushed to the beneficiary's device as an Apple/Google Wallet pass or a barcode.
*   **Webhook Processing:** Merchant Partners (ACT-A14D3CDC5D) process orders via zero-footprint integration or edge dashboards. The system validates the virtual card token against Stripe Issuing REST APIs. Stripe Webhooks are processed asynchronously by the gRPC services to ensure sub-150ms clearing times (CON-1AE00052F2). This latency target is critical for maintaining the integrity of the Financial Ledger & Clearing (CAP-0E02003C70) and ensuring that donor receipts are generated within the 120-second window mandated by the product strategy.
*   **Ineligible Purchase Filtering:** Ineligible purchases (e.g., alcohol, non-food merchandise) are dropped at the Stripe network layer using MCC (Merchant Category Code) filtering, ensuring compliance with donor intent and platform policy (CON-0119C23C31).

### 3.1 Expo Mobile Client (SUR-49E785B31C)

The Expo Mobile Client serves the Beneficiary (ACT-ADA6716160) and Donor (ACT-80C62C7814) actor groups. 

*   **Multi-Modal Access:** The client must support multi-modal access (barcode, NFC tap, voice guidance) for redemption flows (CON-29A1AAF909). This ensures accessibility for visually impaired beneficiaries and aligns with WCAG contrast and screen reader standards (CON-56C11CE749).
*   **Offline Fallback:** To address the reliability of offline fallback mechanisms in remote areas (CON-7D440BDFE0), the client must buffer payments locally if downstream POS partners experience an outage. The system must ensure Graceful Network Degradation: system must buffer payments locally if downstream POS partners experience outage (CON-6955572E22).
*   **Anonymization:** The client-side generation of clean tokenized vouchers visually identical to consumer gift cards ensures no beneficiary demographic data crosses into production logs (CON-E2097E2500).

### 3.2 Next.js Edge Dashboards (SUR-182248FE43)

The Next.js Edge Dashboards serve the Merchant Partner (ACT-A14D3CDC5D) and Platform Operator (ACT-0E3EE366E3) actor groups.

*   **Legacy Tablet Support:** The dashboards must be designed to be usable on legacy tablets with varying OS versions (CON-BDAFF34259). This ensures that older POS hardware in restaurant kitchens can still interact with the platform.
*   **Real-Time Throttling:** Kitchens must be able to toggle real-time throttle parameters, such as a maximum of 15 MealCredit orders per hour, to prevent structural overload. This capability is exposed via the Edge Dashboard.

### 3.3 Internal Operations & Admin Dashboards (SUR-F2DF3A9E16)

The Internal Operations & Admin Dashboards serve the NGO Administrator (ACT-C11D30C3DE) and Platform Operator (ACT-0E3EE366E3) actor groups.

*   **NGO Beneficiary Vetting:** The NGO Administrator uses this surface to manage the NGO Beneficiary Vetting & Pool Management (JNY-35F6A11F27) journey. This includes vetting new beneficiaries and managing their pool allocations.
*   **Compliance & Governance:** The Platform Operator uses this surface for the Compliance and Governance Review (JNY-574359B2C4) journey, monitoring system health, audit trails, and regulatory compliance.

### 4.1 Immutable Financial Ledger (Aurora)

The AWS Data Fabric (SUR-25E8C8F0F0) is anchored by an immutable financial ledger stored in Amazon Aurora. 

*   **Statutory Compliance:** The system must retain immutable financial ledger entries in Aurora for statutory compliance (7+ years implied) (CON-2E7E7AF557). This ensures that all financial transactions are auditable and tamper-proof.
*   **Data-at-Rest Encryption:** Strict data-at-rest encryption must be implemented for Aurora Ledger and DynamoDB tables containing NGO vetting data (CON-06310F87C9). This protects sensitive information from unauthorized access.

### 4.2 Event-Driven Data Backbone (SUR-F444C812A4)

The Event-Driven Data Backbone facilitates asynchronous communication between microservices.

*   **Event-Driven Orchestration:** The Event-Driven Orchestration (CAP-9C74EC302F) capability uses an event bus to decouple services. For example, when a donor completes a round-up, an event is published to the bus, triggering downstream processes such as credit pool updates and donor receipt generation.
*   **Inventory & Liquidity Balancing:** The Inventory & Liquidity Balancing (CAP-9E0331974E) capability monitors the credit pool utilization rate. Automated alerts are triggered if the rate exceeds predefined thresholds, ensuring that the platform can manage liquidity effectively (CON-05500FBF62).

### 4.3 Multi-Tenant Data Isolation

*   **Strict Data Isolation:** The platform must enforce strict data isolation between metropolitan tenants (CON-50C3D26A11). This is achieved through schema-level separation in Aurora and partition keys in DynamoDB, ensuring that data from one metro footprint (e.g., SF) is never accessible to another (e.g., NYC).
*   **Cross-Border Data Sovereignty:** If the platform expands beyond US metros, cross-border data sovereignty (CON-C17BDE5276) must be considered. This will require additional data residency controls and potentially separate infrastructure deployments.

### 4.4 PCI-DSS Level 1 Adherence

The architecture must enforce PCI-DSS Level 1 by routing all card data through Stripe Elements and SDKs; never store raw PANs (CON-FB739F5332). This ensures that the platform never touches sensitive cardholder data, significantly reducing the scope of PCI compliance audits.

### 4.5 SOC2 Type II Audit Trails

The system must maintain immutable audit trails via AWS CloudTrail for all infrastructure modifications and administrative ledger operations (CON-DA469874B5, CON-0B8B980826). This supports SOC2 Type II requirements by providing a verifiable record of all system activities.

### 4.6 Absolute Anonymization

All beneficiary demographic data must be classified as 'Anonymous'; store only high-entropy UUIDv4 keys in production logs (CON-8E702F2E36). This ensures strict data segregation and anonymization to prevent re-identification of vulnerable user groups (CON-5147ECDEA0). The separation of donor PII (Stripe Vault) from beneficiary impact analytics (Redis/DynamoDB) is also critical (CON-B19CA2E31F).

## 5. Success Criteria & Decision Foundations

The Daya (MealCredit) platform's success is defined by measurable operational velocity, financial sustainability, and strict adherence to latency and availability targets. These criteria serve as the primary decision foundations for the inception phase, ensuring that the technology strategy directly supports the business mission of decoupling food assistance from social stigma while maintaining a resilient, multi-tenant fintech architecture.

### 5.1 Operational Velocity & Impact

*   **Donation-to-Redemption Velocity (DRV):** The platform must achieve a DRV under 14 days. This metric measures the efficiency of converting donor funds into tangible impact for beneficiaries. A slower velocity indicates friction in the redemption flow or insufficient merchant partner adoption.
*   **Credit Pool Utilization Rate:** The platform must monitor the Credit Pool Utilization Rate, triggering alerts if it exceeds 85%. This ensures that the platform is effectively circulating funds and not allowing credits to stagnate in the ledger.

### 5.2 Financial Sustainability & Partner Retention

Financial sustainability is driven by the retention of Merchant Partners and the consistent flow of donor capital. The following metrics define the economic viability of the platform:

*   **Merchant Retention Rate (MRR):** Measured on a month-over-month basis, the MRR must remain above a defined threshold for the initial 3 metropolitan footprints. This metric is critical for validating the value proposition of the Next.js Edge Dashboards (SUR-182248FE43) and the zero-footprint POS integrations. A drop in MRR below this threshold requires an immediate review of the Merchant Settlement & Reconciliation (CAP-0AFA130856) process and payout latency.
*   **Monthly Recurring Revenue (MRR):** While specific revenue targets are subject to final business model ratification, the platform must achieve a positive unit economics model per transaction. This includes tracking the net payout to merchants via Stripe Connect (CAP-0AFA130856) within 24 business hours, ensuring that operational costs do not outpace the volume of cleared transactions.

### 5.3 Technical Performance & Latency Thresholds

Given the high-throughput, low-latency requirements of a fintech marketplace, the following technical performance thresholds are binding for the hybrid API Gateway (SUR-6930995FDB) and the Event-Driven Data Backbone (SUR-F444C812A4):

*   **API Responsiveness (p99 Latency):** The p99 API latency for critical redemption and voucher creation actions must remain below 250ms under a load of 10,000 concurrent connections (CON-F1195DEBD1). This ensures a frictionless experience for Beneficiaries at the POS terminal and prevents structural overload for Merchant Partners.
*   **Stripe Webhook Processing Latency:** To ensure sub-150ms clearing times (CON-1AE00052F2), the asynchronous gRPC services handling financial transactions must process Stripe webhooks with an average latency of under 150ms. This is critical for maintaining the integrity of the Financial Ledger & Clearing (CAP-0E02003C70) and ensuring that donor receipts are generated within the 120-second window mandated by the product strategy.
*   **Operational Uptime:** The platform must achieve 99.99% operational uptime using AWS multi-AZ configurations for all core services (CON-22FBC079F6). This high-availability fault tolerance (CON-CC23130B06) is non-negotiable for a fintech platform handling financial transactions and ensuring no loss of funds during outages.

### 5.4 Compliance & Security Benchmarks

While detailed compliance obligations are deferred to the Compliance, Privacy & Governance Obligations artifact, the following high-level benchmarks are established as decision foundations:

*   **PCI-DSS Level 1 Adherence:** The architecture must enforce PCI-DSS Level 1 by routing all card data through Stripe Elements and SDKs, ensuring that raw PANs are never stored in the platform's infrastructure (CON-FB739F5332).
*   **SOC2 Type II Audit Trails:** The system must maintain immutable audit trails via AWS CloudTrail for all infrastructure modifications and administrative ledger operations (CON-DA469874B5, CON-0B8B980826), supporting SOC2 Type II requirements.
*   **Absolute Anonymization:** All beneficiary demographic data must be classified as 'Anonymous', with only high-entropy UUIDv4 keys stored in production logs (CON-8E702F2E36). This ensures strict data segregation and anonymization to prevent re-identification of vulnerable user groups (CON-5147ECDEA0).

## 6. Knowledge Gaps & Unresolved Decisions

The following knowledge gaps must be resolved in subsequent phases to finalize the success criteria and architectural decisions:

*   **KNOWLEDGE_GAP: Jurisdiction-Specific Compliance:** The exact regulatory requirements for financial instruments (gift cards, virtual accounts) across the initial US metropolitan footprints (SF, NYC, Chicago) and potential future cross-border expansions (CON-C17BDE5276) must be confirmed by Legal. This will impact the design of the Tax & Regulatory Reporting (CAP-191989E653) capability.
*   **KNOWLEDGE_GAP: Merchant Partner Onboarding SLA:** The specific Service Level Agreement (SLA) for merchant onboarding and POS integration readiness is not yet defined. This will impact the capacity planning for the Partner & Beneficiary Lifecycle Management (CAP-359633FD94) capability.
*   **KNOWLEDGE_GAP: Donor Acquisition Cost (CAC):** The target Customer Acquisition Cost (CAC) for Donors and Contributors is not yet established. This will impact the marketing budget and the definition of the Directed Impact Flows (CAP-18F5D7C894) effectiveness.
*   **KNOWLEDGE_GAP: Credit Pool Segmentation Strategy:** The decision to adopt a strict centralized credit ledger (single pool per metro) or allow for granular, segmented credit pools (e.g., distinct pools for Vegan, Halal, or specific NGO allocations) to support donor-directed impact flows (DEC-04FA090142) remains open. This will impact the complexity of the Financial Ledger & Clearing (CAP-0E02003C70) and the Geo-Discovery & Allocation (CAP-18F5D7C894) capabilities.
*   **KNOWLEDGE_GAP: Virtual Card Provisioning Model:** Given the requirement for 'no raw credit card account' touching servers, the decision to generate Stripe Issuing virtual cards per-transaction (high latency) or pre-provision them in a batched wallet linked to the beneficiary session (low latency) (DEC-27EB3762D5) must be made. This will impact the p99 API latency and the overall user experience.
*   **KNOWLEDGE_GAP: Offline Redemption Fallback Mechanism:** For the offline redemption fallback (Edge Case B), the decision on whether the local SecureStore token should be a static cryptographically signed QR code validated by a serverless Lambda function later, or a dynamic time-limited token validated by a localized edge caching layer (DEC-2342963516) must be resolved. This will impact the reliability of the system in areas with poor connectivity.

## 7. Decision Rationale

These success criteria are grounded in the project's core mission to decouple food assistance from social stigma. By prioritizing DRV and MRR, the platform ensures that donor capital is efficiently converted into tangible impact for Beneficiaries while maintaining a sustainable ecosystem for Merchant Partners. The strict latency and uptime thresholds are necessary to build trust with all actor groups, particularly in a fintech context where reliability and speed are paramount. The compliance benchmarks ensure that the platform operates within the strict legal and ethical boundaries required for handling sensitive financial and demographic data.

These criteria will serve as the primary input for the Design phase, where technical architectures will be evaluated against their ability to meet these specific KPIs. Any architectural decision that compromises these foundations will require explicit justification and risk acceptance from the Platform Operator and Legal stakeholders.
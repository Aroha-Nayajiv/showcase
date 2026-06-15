# Success Criteria & Decision Foundations

## 1. Measurable Success Criteria (KPIs)

The viability of the Daya (MealCredit) platform is defined by the following quantifiable Key Performance Indicators (KPIs), mapped directly to the tripartite actor model and the core mission of decoupling food assistance from social stigma.

### 1.1 Donation-to-Redemption Velocity (DRV)
- **Target:** Under 14 days from initial micro-donation to final beneficiary redemption.
- **Rationale:** Rapid velocity ensures that donor capital is actively circulating within the local food ecosystem, maximizing the tangible impact of DirectedImpactFlows and preventing capital stagnation in the central regional pool.
- **Measurement:** Tracked via the Financial Ledger & Clearing (CAP-0E02003C70) by correlating the timestamp of a successful Micro-DonationRound-Ups transaction with the timestamp of a successful BeneficiaryVoucherActivation&Redemption event.
- **Governance Constraint:** Automated alerts must be triggered if the DRV exceeds 14 days for any given metropolitan footprint, requiring immediate operational review (CON-05500FBF62).

### 1.2 Merchant Retention Rate (MRR)
- **Target:** Measured month-over-month; baseline target of 90% retention for Merchant Partners (ACT-A14D3CDC5D) in the initial 3-metro launch.
- **Rationale:** High retention is critical for the sustainability of the Fulfillment Partner network. If restaurants do not find the zero-footprint integration or edge dashboard (SUR-182248FE43) operationally viable, the beneficiary redemption network collapses.
- **Measurement:** Calculated by tracking active Merchant Partners who have processed at least one order via the MerchantOrderAcceptance&Settlement journey (JNY-9182903B2E) in the current month versus the previous month.

### 1.3 API Latency and Performance Thresholds
- **Target:** p99 API latency below 250ms for critical redemption and voucher creation actions.
- **Rationale:** To ensure a frictionless, stigma-free experience for the Beneficiary (ACT-ADA6716160), the redemption flow must be as fast as a standard credit card tap. Latency spikes during peak POS windows (CON-476AC52317) directly translate to lost transactions and donor frustration.
- **Measurement:** Monitored via the Event-Driven Data Backbone (SUR-F444C812A4) and AWS CloudWatch metrics, specifically tracking the Hybrid API Gateway (SUR-6930995FDB) response times.
- **Secondary Target:** Stripe Webhook Processing Latency must average below 150ms to ensure sub-150ms clearing times for financial transactions (CON-1AE00052F2).

### 1.4 Operational Uptime and Reliability
- **Target:** 99.99% operational uptime across all AWS multi-AZ configurations.
- **Rationale:** As a fintech platform handling financial instruments, high availability is non-negotiable to prevent loss of funds or transaction failures during critical redemption windows (CON-CC23130B06, CON-22FBC079F6).
- **Measurement:** Tracked via AWS CloudWatch Synthetics and internal health check endpoints.

### 1.5 Credit Pool Utilization Rate
- **Target:** Automated alerts triggered if utilization exceeds 85%.
- **Rationale:** Ensures the Financial Transaction Engine (CAP-38C04FAFE0) maintains sufficient liquidity to cover pending redemptions without over-extending the donor funding base.
- **Measurement:** Calculated by the Inventory & Liquidity Balancing (CAP-9E0331974E) capability, comparing active virtual card tokens against the total funded capital pool.

### 1.7 Cache Hit Ratio (CHR)
- **Target:** Cache Hit Ratio for restaurant search queries above 92%.
- **Rationale:** High cache efficiency is required to maintain sub-250ms p99 latency for the Geo-Discovery & Allocation (CAP-18F5D7C894) capability during peak metropolitan traffic.
- **Measurement:** Monitored via the Event-Driven Data Backbone (SUR-F444C812A4) by tracking Redis/DynamoDB query response times and cache miss rates.

---

## 2. Binding Technical Constraints

### 2.1 PCI-DSS Level 1 Adherence

To maintain the highest level of trust and regulatory compliance, the platform must enforce PCI-DSS Level 1 standards. This is the most stringent level of certification available and is required for all entities that process over 6 million Visa transactions annually or have suffered a major data breach.

- **Data Isolation and Routing:** All cardholder data, including Primary Account Numbers (PANs), must be routed exclusively through the Stripe Elements and SDK. The platform is strictly prohibited from storing, processing, or transmitting raw PANs on any internal servers, databases, or logs. This is enforced by the `Enforce PCI-DSS Level 1 by routing all card data through Stripe Elements and SDK; never store raw PANs` concern (CON-FB739F5332).
- **Tokenization Mandate:** The system must utilize Stripe Issuing to provision single-use virtual card tokens. These tokens are locked to specific Merchant Category Codes (MCCs) and locations, ensuring that even if a token is intercepted, it cannot be used for ineligible purchases (e.g., alcohol, non-food items). This aligns with the Pseudo-AnonymizedRedemption domain concept.
- **Network Security:** The platform's network architecture must be segmented to isolate the cardholder data environment (CDE) from the rest of the corporate network. All inbound and outbound traffic to the CDE must be restricted and monitored.

### 2.2 SOC2 Type II Compliance

The platform must be architected to support SOC2 Type II requirements, which focus on the operational effectiveness of security controls over a period of time. This is critical for establishing trust with donors, NGO partners, and regulatory bodies.

- **Immutable Audit Trails:** All infrastructure modifications, administrative ledger operations, and financial transactions must be logged to AWS CloudTrail. These logs must be immutable and retained for a minimum of 7 years to satisfy statutory compliance requirements (CON-2E7E7AF557, CON-DA469874B5).
- **Access Control Logging:** All administrative access to the Financial Ledger & Clearing (CAP-0E02003C70) and Partner & Beneficiary Lifecycle Management (CAP-359633FD94) systems must be logged and reviewed quarterly.

### 2.3 Data Sovereignty and Anonymization

- **Strict Data Segregation:** Strict data segregation and anonymization must be enforced to prevent re-identification of vulnerable user groups (CON-5147ECDEA0).
- **Anonymous Data Handling:** All beneficiary demographic data must be classified as 'Anonymous'; only high-entropy UUIDv4 keys should be stored in production logs (CON-8E702F2E36).
- **Cross-Border Considerations:** If the platform expands beyond US metros, cross-border data sovereignty laws must be evaluated to ensure compliance with local data protection regulations (CON-C17BDE5276).

---

## 3. Open Strategic Decisions and Gaps

The following decisions and knowledge gaps must be resolved before proceeding to the Design phase to ensure architectural coherence and regulatory compliance.

### 3.1 Credit Pool Architecture
- **Decision Axis:** Should the platform adopt a strict centralized credit ledger (single pool per metro) or allow for granular, segmented credit pools (e.g., distinct pools for Vegan, Halal, or specific NGO allocations) to support donor-directed impact flows?
- **Impact:** This decision dictates the schema for the Financial Ledger & Clearing (CAP-0E02003C70) and the complexity of the Inventory & Liquidity Balancing (CAP-9E0331974E) capability.
- **Owner:** Product Strategy / Engineering Lead
- **Status:** `KNOWLEDGE_GAP: Credit Pool Segmentation Strategy - Owner: Product Strategy`

### 3.2 Virtual Card Provisioning Latency
- **Decision Axis:** Given the requirement for 'zero raw credit card account' touching servers, should the Stripe Issuing virtual card be generated per-transaction (high latency) or pre-provisioned in a batched wallet linked to the beneficiary session (low latency)?
- **Impact:** This decision affects the p99 API latency target (250ms) and the user experience during redemption.
- **Owner:** Engineering Lead / Product Strategy
- **Status:** `KNOWLEDGE_GAP: Virtual Card Provisioning Mechanism - Owner: Engineering Lead`

### 3.3 Offline Redemption Fallback
- **Decision Axis:** For the offline redemption fallback (Edge Case B), should the local SecureStore token be a static cryptographically signed QR code validated by a serverless Lambda function later, or a dynamic time-limited token validated by a localized edge caching layer?
- **Impact:** This decision impacts the reliability of offline fallback mechanisms in remote areas (CON-7D440BDFE0) and the complexity of the Expo Mobile Client (SUR-49E785B31C).
- **Owner:** Engineering Lead / Security Architect
- **Status:** `KNOWLEDGE_GAP: Offline Redemption Token Strategy - Owner: Engineering Lead`

### 3.4 Donor Directed Impact Matching
- **Decision Axis:** How should the system handle 'Donor Directed Impact' (FR-DON-02) when a donor targets a 'merchant property type' but the specific restaurant's MCC code in the Stripe ledger does not match the donor's intent filter, causing transaction drops?
- **Impact:** This decision affects the user experience for donors and the reconciliation logic for the Financial Transaction Engine (CAP-38C04FAFE0).
- **Owner:** Product Strategy / Engineering Lead
- **Status:** `KNOWLEDGE_GAP: Donor Directed Impact Matching Logic - Owner: Product Strategy`

### 3.5 Legal Liability Boundaries
- **Decision Axis:** What are the specific legal liability boundaries regarding ineligible merchant purchases (e.g., alcohol, non-food items) when the platform's MCC filtering fails?
- **Impact:** This decision affects the Compliance & Audit Governance (CAP-421F3AD853) and the terms of service for Merchant Partners (ACT-A14D3CDC5D).
- **Owner:** Legal / Compliance
- **Status:** `KNOWLEDGE_GAP: Legal Liability Boundaries for Ineligible Purchases - Owner: Legal/Compliance`

---

### 3.6 Reputational Risk
- **Risk:** Breach of beneficiary anonymity could severely damage the platform's social mission and public trust.
- **Mitigation:** Utilize Cryptographic Profile Creation for beneficiary identities to ensure no PII cross-pollinates into analytics or donor receipts (CON-E2097E2500). Classify all beneficiary demographic data as 'Anonymous'; store only high-entropy UUIDv4 keys in production logs (CON-8E702F2E36).
- **Owner:** Platform Operator (ACT-0E3EE366E3) / Security Architect

## 4. Success Signals

The following signals indicate that the Daya (MealCredit) platform is meeting its inception-phase objectives and is ready for the Design phase:

1. **KPI Baselines Established:** All KPIs (DRV, MRR, API Latency, Uptime, Credit Pool Utilization, CHR) have defined targets and measurement strategies.
2. **Compliance Constraints Defined:** PCI-DSS Level 1 and SOC2 Type II requirements are explicitly mapped to technical controls.
3. **Strategic Decisions Resolved:** All open strategic decisions and knowledge gaps have been assigned owners and target resolution dates.
4. **Risk Mitigation Plans Approved:** All high-priority risks have identified mitigation strategies and owners.
5. **Stakeholder Alignment:** All primary actors (Donor, Beneficiary, Merchant Partner, NGO Administrator, Platform Operator) have their success criteria and constraints validated.

---

## 5. Decision Foundations

### 5.1 Actor Roles and Responsibilities
- **Platform Operator (ACT-0E3EE366E3):** Responsible for system uptime, compliance monitoring, and operational risk mitigation.
- **Donor (ACT-80C62C7814):** Responsible for funding the credit pool and adhering to donation guidelines.
- **Beneficiary (ACT-ADA6716160):** Responsible for using credits within the designated merchant network and adhering to anonymization protocols.
- **Merchant Partner (ACT-A14D3CDC5D):** Responsible for accepting credits, providing goods/services, and adhering to PCI-DSS compliance.
- **NGO Administrator (ACT-C11D30C3DE):** Responsible for vetting beneficiaries and managing pool allocations.

### 5.2 Journey Mapping
- **Contributor Onboarding and Funding Setup (JNY-6C7A41A295):** Establishes the donor funding flow.
- **Beneficiary Voucher Activation & Redemption (JNY-C08A483C99):** Defines the core redemption experience.
- **Merchant Order Acceptance & Settlement (JNY-9182903B2E):** Ensures merchant compliance and payout reconciliation.
- **Platform Reconciliation & Compliance Audit (JNY-B28683CC8E):** Validates financial integrity and regulatory adherence.

### 5.3 Capability Ownership
- **Financial Ledger & Clearing (CAP-0E02003C70):** Owned by Platform Operator.
- **Financial Transaction Engine (CAP-38C04FAFE0):** Owned by Platform Operator.
- **Compliance & Audit Governance (CAP-421F3AD853):** Owned by Compliance Officer.
- **Compliance & Anonymization Engine (CAP-8BE92AC200):** Owned by Security Architect.
- **Event-Driven Orchestration (CAP-9C74EC302F):** Owned by Engineering Lead.

---

## 6. Follow-Up Questions

1. What credit pool segmentation strategy is binding for the initial 3-metro launch?
2. What virtual card provisioning mechanism is required to meet the p99 API latency target?
3. What offline redemption token strategy is preferred for remote area reliability?
4. What donor directed impact matching logic is required for MCC code mismatches?
5. What legal liability boundaries are established for ineligible merchant purchases?
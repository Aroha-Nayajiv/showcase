# Risk Register & Technical Constraints

### 1. Binding Data Handling Rules

#### 1.1 Beneficiary PII (Restricted No-PII)
**Constraint:** Beneficiary data must be absolutely anonymized. No PII such as legal name or domestic background is stored on-platform or in production logs.
**Mechanism:** Client-side generation of clean tokenized vouchers visually identical to consumer gift cards, ensuring no beneficiary demographic data crosses into production logs.
**Owner:** Platform Administrator (ACT-086A974D63) for policy; Platform Operator (ACT-0E3EE366E3) for enforcement.

#### 1.2 Donor Transaction History
**Constraint:** Donors must receive immutable transactional receipts within 120 seconds of redemption, strictly prohibiting transmission of any identifying beneficiary parameters.
**Mechanism:** Directed Impact Flows allow donors to assign funds globally, regionally, or to specific merchant types, but receipts must only confirm the meal funded, not who received it.
**Retention:** Data retention policies for Donor transaction history and impact receipts must be defined. [KNOWLEDGE_GAP: What is the binding retention period for Donor transaction history and impact receipts? - Owner: Legal/Compliance]

### 2. Binding Technical Performance Constraints

The MealCredit platform operates under strict technical performance constraints to ensure a frictionless, dignified, and reliable experience for Beneficiaries and Merchant Partners across the SF, NYC, and Chicago metropolitan footprints. These constraints are non-negotiable invariants that govern architectural decisions, infrastructure provisioning, and operational monitoring.

#### 2.1 System Availability and Resilience
Given the critical nature of food assistance, the platform must maintain exceptional availability to ensure that Beneficiaries can access meals whenever and wherever needed.

**Operational Uptime:** The platform must maintain 99.99% operational uptime across AWS multi-AZ configurations (CON-725D8AA177). This requires a resilient architecture leveraging AWS Auto Scaling, multi-AZ database deployments, and global load balancing to mitigate the impact of regional outages. The Merchant Failover & Resilience capability (CAP-3701C64DAE) must be designed to support this uptime target, including offline fallback mechanisms for POS integrations.
**Offline Token Validation:** To support system resilience and offline capability, the platform must guarantee that transactions can be processed or validated even during network outages (CON-83B6B3C1D2). This involves the Offline Token Validation Service (SUR-F9B88612F0) and the use of hardware-backed SecureStore for time-bound, signature-verified cryptograms (CON-F348873C08). The Offline Token Cryptographic Signature Validation Logic (CON-A016F9DA51) must be robust enough to handle edge cases where network connectivity is intermittent or unavailable.

#### 2.2 Search and Discovery Performance
The Beneficiary Dignified Redemption journey (JNY-1A3DBC558B) begins with the Beneficiary app mapping participating dining locations. The performance of this search functionality is critical to user satisfaction and engagement.

**Cache Hit Ratio (CHR):** The system must ensure a Cache Hit Ratio (CHR) for restaurant search queries exceeds 92% via Redis Enterprise Cluster (CON-59F8C209D1). This high CHR target minimizes database load and ensures that Beneficiaries receive near-instantaneous search results for restaurants filtered by distance, dietary flags, and other criteria. The Redis Enterprise Cluster must be configured with appropriate eviction policies and data structures to support this performance level under peak load.

#### 2.3 Scalability and Concurrency
The platform is designed to scale to 50,000 Monthly Active Users (MAU) across three initial metropolitan footprints. Performance constraints must hold under this projected load.

**Concurrent Connection Handling:** The p99 latency constraint of <250ms for Voucher Creation and Scanning Callback Processing is explicitly defined under 10,000 concurrent connections (CON-78A549ECB3). This requires careful capacity planning for the Backend Orchestration Layer (SUR-AEEE5250CE) and the Async gRPC Financial Services (SUR-1D08816305) to ensure that resource contention does not degrade performance as concurrency increases.
**Merchant Throttle Limits:** To prevent structural overload during peak service, Merchant Partners must implement operational throttle limits. The system must alert on Merchants hitting Operational Throttle Limits or POS integration errors (CON-50A5358898). This requires real-time monitoring and alerting capabilities integrated into the Merchant/Supplier Dashboard (SUR-3D4148A435). [KNOWLEDGE_GAP: What is the specific operational throttle limit (e.g., max orders per hour) for Merchant Partners? - Owner: Product/Operations]

#### 2.4 Traceability and Latency Targets
To ensure end-to-end system integrity and financial reconciliation, specific latency targets must be met for critical asynchronous processes.

*   **Voucher Creation & Scanning:** Achieve p99 latency <250ms for Voucher Creation and Scanning Callback Processing under 10,000 concurrent connections (CON-78A549ECB3).
*   **Stripe Webhook Processing:** Process Stripe Webhook events to merchant ledger entry within 150ms average latency (CON-AE9B9C163C).
*   **Operational Uptime:** Maintain 99.99% operational uptime across AWS multi-AZ configurations (CON-725D8AA177).
*   **Search Performance:** Ensure Cache Hit Ratio (CHR) for restaurant search queries exceeds 92% via Redis Enterprise Cluster (CON-59F8C209D1).
*   **Offline Resilience:** Guarantee that transactions can be processed or validated even during network outages (CON-83B6B3C1D2). This involves the Offline Token Validation Service (SUR-F9B88612F0) and the use of hardware-backed SecureStore for time-bound, signature-verified cryptograms (CON-F348873C08). The Offline Token Cryptographic Signature Validation Logic (CON-A016F9DA51) must be robust enough to handle edge cases where network connectivity is intermittent or unavailable.
*   **Merchant Throttling:** Alert on Merchants hitting Operational Throttle Limits or POS integration errors (CON-50A5358898). [KNOWLEDGE_GAP: What is the specific operational throttle limit (e.g., max orders per hour) for Merchant Partners? - Owner: Product/Operations]

#### 2.5 Data Privacy & Anonymization Risks
*   **Risk:** Leakage of Beneficiary PII (legal names, demographics) into production logs or donor-facing receipts.
*   **Impact:** Violation of absolute anonymization principles, leading to severe reputational damage and regulatory penalties.
*   **Mitigation:** Enforce strict data partitioning in DynamoDB/PostgreSQL to isolate NGO regional data to prevent cross-contamination (CON-709C3F21C2); Classify Beneficiary PII as 'Restricted No-PII'; ensure no legal names, SSNs, or demographics are stored on-platform beyond cryptographic aliases (CON-5CA3E5A67B); Ensure beneficiary data handling complies with local privacy laws (e.g., CCPA in SF) by enforcing strict anonymization and UUIDv4 generation (CON-C43D84B266).

### 3. Open Decision Gaps

*   **DEC-5DE6023861:** Should the Pseudo-Anonymous Redemption Engine generate single-use tokens per transaction (high friction, low fraud risk) or batch-assign a rotating pool of 3-5 valid tokens to the user's wallet for offline resilience (lower friction, higher token loss risk)?
*   **DEC-0D5E43E715:** For the Merchant Module (FR-RES-01), will the platform enforce a mandatory POS integration via Stripe Tap to Pay/Connect APIs for all merchants, or allow a fallback 'merchant-entered voucher code' workflow for smaller establishments?
*   **DEC-713373C65C:** When routing the 'Directed Impact Flows' (FR-DON-02), should the platform enforce strict geo-fencing at the API level for donation acceptance, or allow global donations that are assigned to 'unassigned regional pools' for later distribution by NGO admins?
*   **DEC-B47DF89DA9:** For NFR-PERF-01 (p99 latency < 250ms) in the real-time transparency engine, should donor receipts be generated synchronously via GraphQL at the moment of redemption, or asynchronously via Golang microservices emitting to a public-facing SSE stream?
*   **KNOWLEDGE_GAP:** What is the binding retention period for Donor transaction history and impact receipts? - Owner: Legal/Compliance
*   **KNOWLEDGE_GAP:** What is the specific operational throttle limit (e.g., max orders per hour) for Merchant Partners? - Owner: Product/Operations
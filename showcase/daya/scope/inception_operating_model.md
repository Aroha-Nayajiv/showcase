# Operating Model & Stakeholder Alignment

### 2.1 Tripartite Ecosystem: Donor, Beneficiary, Merchant

The core value exchange relies on the seamless interaction between the three primary market participants. Their boundaries are strictly defined to prevent scope creep and ensure clear accountability.

#### Donor (ACT-80C62C7814)
**Primary Interaction Boundary:** The Donor initiates the value chain by providing real-time financial micro-donations. Their interaction is limited to funding activation and impact visualization.
**Key Responsibilities:**
- Activate funding via the Donor Onboarding & Funding Activation journey (JNY-62D850E94B).
- Configure donation round-ups and redemption history via multi-modal paths (voice, tap, scan) as per CON-2D70EDCDEE.
- Receive anonymized impact receipts correlated with beneficiary redemption events without PII linkage, using UUIDv4 mapping for analytics (CON-23A501C051).
**Strategic Constraint:** Donor data must be strictly segregated from beneficiary demographic data to prevent de-anonymization attacks (CON-C22D030D21).

#### Beneficiary (ACT-ADA6716160)
**Primary Interaction Boundary:** The Beneficiary is the end-user of the culinary credits, interacting with the platform primarily through the NGO Operator for eligibility and through Merchants for redemption.
**Key Responsibilities:**
- Undergo eligibility verification and offboarding via NGO Operator governance (JNY-4C4BA15817).
- Redeem credits at Merchant locations via the Beneficiary Eligibility & Voucher Redemption journey (JNY-E82B8A88D8).
- Utilize offline fallback interfaces that are intuitive and accessible (CON-FA7A13E601).
**Strategic Constraint:** All beneficiary-related data is classified as 'Highly Sensitive' and restricted to cryptographic hashing layers only (CON-2788862587). Legal names and demographic status are cryptographically segregated from public-facing data (CON-92F07E31B0).

#### Merchant (ACT-AF904DCFF9)
**Primary Interaction Boundary:** The Merchant (Restaurant) partners fulfill the culinary credits, acting as the redemption endpoint. Their interaction is focused on POS integration and payout management.
**Key Responsibilities:**
- Complete onboarding and POS integration via the Merchant Onboarding & POS Integration journey (JNY-356F465DB3).
- Process redemptions in real-time, ensuring latency optimization to prevent queue stagnation (CON-5D64EBC654).
- Manage payout errors and handle refunds via the Merchant Payout Error Handling Flow (JNY-90B07623FB) and Merchant-Beneficiary Refund Flow (JNY-E5F45D37C6).
**Strategic Constraint:** Merchants must adhere to strict data retention policies, ensuring donor transaction history is not linked to redemption analytics (CON-4820FAD5A9).

#### NGO Operator (ACT-09E028AEB0)
**Primary Interaction Boundary:** The NGO Operator acts as the trusted intermediary between the Platform and the Beneficiary community. They are responsible for local compliance, beneficiary onboarding, and offboarding.
**Key Responsibilities:**
- Manage NGO Governance and Beneficiary Offboarding (JNY-4C4BA15817).
- Oversee Merchant & NGO Operations (CAP-MERCHANT-NGO-OPERATIONS).
- Ensure local compliance with jurisdictional regulations in SF, NYC, and Chicago.
**Strategic Constraint:** NGO Operators must ensure that beneficiary eligibility decisions are transparent and auditable, while maintaining the anonymity of the donor-beneficiary link.

#### Platform Administrator (ACT-086A974D63)
**Primary Interaction Boundary:** The Platform Administrator oversees the technical and operational integrity of the MealCredit platform. They are responsible for system-wide configuration, security, and compliance.
**Key Responsibilities:**
- Manage Identity & Access Management (CAP-IDENTITY-ACCESS-MANAGEMENT) for all actor roles.
- Oversee Compliance, Security & Audit (CAP-COMPLIANCE-SECURITY-AUDIT) to ensure PCI-DSS Level 1 and SOC2 Type II adherence.
- Monitor system performance, including Credit Pool Utilization Rate (CON-7031BE57B3) and Donation-to-Redemption Velocity (CON-F89C70071E).
**Strategic Constraint:** The Platform Administrator must ensure that the infrastructure supports 99.99% operational uptime across AWS multi-AZ configurations (CON-FD21121DD5) and that all administrative ledger operations are logged to AWS CloudTrail for SOC2 Type II evidence (CON-FBBBF07295).

#### Dispute Adjudicator (ACT-7BA340FF76)
**Primary Interaction Boundary:** The Dispute Adjudicator handles edge cases and conflicts that cannot be resolved through automated systems or standard operational flows. This role is critical for maintaining trust in the financial and social impact aspects of the platform.
**Key Responsibilities:**
- Manage Beneficiary-Platform Dispute Flow (JNY-2B038C9362) and Platform-NGO Fraud Investigation Flow (JNY-CA74D631DC).
- Oversee Dispute Resolution & Chargeback Management (CAP-DISPUTE-RESOLUTION-CHARGEBACK-MANAGEMENT).
- Investigate and resolve fraud detection and prevention screening issues (CAP-FRAUD-DETECTION-FRAUD-PREVENTION-SCREENING).
**Strategic Constraint:** Dispute Adjudicator decisions must be fully auditable and aligned with financial regulations governing quasi-cash instruments, including unclaimed property and escheatment laws (CON-B1DFEBEC8C).

### 2.4 Strategic Roadmap & Partnership Requirements

The operating model supports a phased rollout across the three initial metropolitan footprints (SF, NYC, Chicago). The strategic roadmap focuses on:

1. **Phase 1: MVP Launch (SF):** Establish core tripartite interactions, validate NGO Operator workflows, and ensure PCI-DSS Level 1 compliance for payment processing.
2. **Phase 2: Scale & Modernization (NYC, Chicago):** Transition to a resilient multi-tenant architecture, implement event-driven serverless components, and expand POS gateway integrations.
3. **Phase 3: Optimization & Trust:** Enhance fraud detection capabilities, optimize latency for real-time POS clearance, and refine anonymization techniques to eliminate any potential for de-anonymization attacks.

**Partnership requirements include:**
- **NGO Partners:** Local non-profit organizations with established beneficiary networks in each metro footprint.
- **Merchant Partners:** Commercial restaurant establishments willing to integrate with the MealCredit POS gateway.
- **Payment Processors:** Stripe Connected Account services for PCI-DSS Level 1 compliant payment processing (CON-66390130AA, CON-62097EBBF3).

### 3.5 Actor-Capability Mapping Matrix

The following matrix defines the primary interaction boundaries for each actor role. Roles are mapped to capabilities based on their functional responsibility within the tripartite ecosystem (Donor, Beneficiary, Merchant) and the supporting governance layers (NGO, Platform, Adjudicator).

| Actor Role | Capability | Operational Boundary |
| :--- | :--- | :--- |
| Donor (ACT-80C62C7814) | Transaction & Financial Engine | Initiates micro-donations; receives anonymized impact receipts. No access to beneficiary PII. |
| | Marketplace & Matchmaking | Views high-level, anonymized impact metrics (e.g., meals funded) to drive engagement. |
| Beneficiary (ACT-ADA6716160) | Identity & Access Management | Onboarded via NGO Operator; manages personal device security (SecureStore) and redemption preferences. |
| | Marketplace & Matchmaking | Discovers participating Merchant Partners (Restaurants) based on location and cuisine preferences. |
| | Transaction & Financial Engine | Redeems culinary credits via POS scan/tap; receives real-time clearance confirmation. |
| Merchant (ACT-AF904DCFF9) | Merchant & NGO Operations | Manages POS integration, menu availability, and payout reconciliation. |
| | Transaction & Financial Engine | Processes redemption callbacks; handles refund/reversal requests initiated by Beneficiaries. |
| | Merchant Payout Failure & Error Handling | Receives alerts for failed payouts; initiates manual reconciliation if automated clearing fails. |
| NGO Operator (ACT-09E028AEB0) | Identity & Access Management | Verifies Beneficiary eligibility; manages Beneficiary lifecycle (onboarding/offboarding). |
| | Merchant & NGO Operations | Vets and onboards Merchant Partners within their jurisdiction; monitors local compliance. |
| | Compliance, Security & Audit | Ensures local data residency compliance; audits Beneficiary data handling for FTC anonymity adherence. |
| Platform Administrator (ACT-086A974D63) | Identity & Access Management | Manages global RBAC for NGO Operators and Platform Admins; oversees system-wide security policies. |
| | Transaction & Financial Engine | Monitors Credit Pool Utilization Rate; manages global financial ledger integrity and currency conversion. |
| | Compliance, Security & Audit | Oversees SOC2 Type II structural planning; manages AWS CloudTrail logging and PCI-DSS Level 1 compliance. |
| Dispute Adjudicator (ACT-7BA340FF76) | Dispute Resolution & Chargeback Management | Reviews escalated disputes between Beneficiaries and Merchants; issues final rulings on credit reversals. |
| | Fraud Detection & Fraud Prevention Screening | Analyzes flagged transactions for double-spending or replay attacks; updates fraud prevention rules. |

### 3.6 Stakeholder Alignment & Decision Rights

To ensure effective governance, decision rights are distributed across the actor roles based on their proximity to the data and financial flows.

**Beneficiary Eligibility:** The NGO Operator (ACT-09E028AEB0) holds sole authority for verifying and maintaining Beneficiary eligibility. This ensures that local context and community trust are leveraged for onboarding, while the Platform Administrator (ACT-086A974D63) retains oversight for global policy compliance.
**Merchant Onboarding & Vetting:** The NGO Operator (ACT-09E028AEB0) is responsible for vetting Merchant Partners (Restaurants) within their jurisdiction, ensuring they meet local standards and POS integration requirements. The Platform Administrator (ACT-086A974D63) provides the technical framework for POS integration but does not approve individual merchants.
**Dispute Resolution:** The Dispute Adjudicator (ACT-7BA340FF76) operates independently of the NGO Operator and Platform Administrator to ensure impartiality. They have access to anonymized transaction logs and POS data to resolve disputes between Beneficiaries and Merchants, with final rulings binding on all parties.

### 3.7 Cross-Reference to Sibling Artifacts

**Compliance, Risk & Governance:** This artifact defers to the sibling artifact for the detailed risk register, specific compliance controls (e.g., PCI-DSS Level 1 technical requirements), and the formal governance committee structure. The operating model here defines who is responsible for compliance, while the sibling artifact defines how compliance is achieved.
**Technical Architecture & Decision Foundations:** This artifact defers to the sibling artifact for the specific technical implementation of the Transaction & Financial Engine (e.g., GraphQL vs. gRPC, Aurora PostgreSQL schema) and the Identity & Access Management system (e.g., Expo SecureStore, RBAC tiers). The operating model here defines the functional boundaries and data isolation requirements that the technical architecture must enforce.

### 4.8 PCI-DSS Level 1 Adherence and Payment Isolation

To achieve PCI-DSS Level 1 compliance, the operating model mandates that zero raw card data touches MealCredit servers. The Platform Administrator (ACT-086A974D63) is responsible for ensuring that all financial interactions are routed exclusively through Stripe Elements and Stripe Issuing virtual card provisioning.

**Data Boundary:** The Architectural surface: Payment Processing Surface (SUR-5B18C8719F) acts as the sole entry point for payment data, immediately tokenizing it via Stripe. The Architectural surface: Data Persistence Layer (SUR-FA61592CD4) is strictly prohibited from storing raw Primary Account Numbers (PANs) or CVV codes.
**Operational Control:** The Platform Administrator must enforce automated scanning of the codebase and infrastructure-as-code (IaC) to detect any potential leakage of sensitive authentication data (SAD). Any detected leakage triggers an immediate incident response protocol.
**Constraint Alignment:** This directly addresses CON-66390130AA (Enforce PCI-DSS Level 1 compliance by ensuring zero raw card data touches MealCredit servers, relying entirely on Stripe Elements/...). The Platform Administrator owns the compliance evidence collection for SOC2 Type II structural planning (CON-81FB01F06B).

### 4.9 FTC Anonymity Guidelines and Beneficiary Data Segregation

The core mission of decoupling food assistance from social stigma requires an operating model that prevents any de-anonymization attacks. The Platform Administrator and NGO Operator (ACT-09E028AEB0) must enforce strict data isolation where beneficiary demographic status and legal names are cryptographically segregated from public-facing data and donor impact analytics.

**Cryptographic Segregation:** Beneficiary-related data is classified as 'Highly Sensitive' (CON-2788862587). Access to this data is restricted to cryptographic hashing layers only. The NGO Operator can view hashed identifiers for eligibility verification but cannot access raw PII without explicit, logged, and time-bound authorization from the Platform Administrator.
**Anti-De-anonymization:** The Platform Administrator must implement and monitor controls to ensure no metadata analysis can link beneficiaries to donors (CON-C22D030D21). This includes stripping all PII from donor impact receipts and ensuring that redemption events are correlated using UUIDv4 mapping for analytics (CON-23A501C051).
**Operational Control:** The NGO Operator is responsible for the initial onboarding and offboarding of beneficiaries (JNY-4C4BA15817), but all data handling must occur within the isolated, hashed environment. The Platform Administrator audits these interactions to ensure no PII leakage occurs during the handoff.

### 4.10 Financial Ledger Integrity and Auditability

To maintain trust and ensure financial accuracy, the operating model requires an append-only cryptographic log auditing system for all financial ledger mutations. The Platform Administrator is responsible for the integrity of this log.

**Append-Only Logging:** All financial transactions, including donations, credit distributions, and redemptions, must be recorded in an append-only log in Aurora PostgreSQL (CON-6061FCCA83). This ensures that no historical transaction can be altered or deleted, providing a tamper-proof audit trail.
**Cryptographic Hashing:** Each log entry must be cryptographically hashed and linked to the previous entry, creating a chain of custody for all financial data. The Platform Administrator must implement automated integrity checks to detect any tampering.
**SOC2 Type II Evidence:** All administrative ledger operations and infrastructure changes must be logged to AWS CloudTrail for SOC2 Type II evidence (CON-FBBBF07295). The Platform Administrator is responsible for generating and retaining this evidence for audit purposes.
**Constraint Alignment:** This addresses CON-6061FCCA83 (Implement append-only cryptographic log auditing in Aurora PostgreSQL for all financial ledger mutations) and CON-FBBBF07295 (Log all administrative ledger operations and infrastructure changes to AWS CloudTrail for SOC2 Type II evidence).

### 4.11 Unresolved Compliance Dependencies

**KNOWLEDGE_GAP:** Specific jurisdictional data residency requirements for NYC and Chicago beyond standard US federal laws are not yet defined. Legal counsel must confirm if any local ordinances impose additional data storage or processing constraints for financial or health-related data.
**KNOWLEDGE_GAP:** The exact threshold for 'de-anonymization risk' in the context of FTC guidelines is not quantified. The Platform Administrator must work with legal counsel to define a measurable risk score for metadata analysis to ensure compliance with CON-C22D030D21.
**ASSUMPTION:** The platform will rely entirely on Stripe for PCI-DSS Level 1 compliance, with no raw card data stored internally. This assumption is grounded in the project requirement and CON-66390130AA. If Stripe's capabilities change, the operating model must be re-evaluated.
**ASSUMPTION:** Beneficiary data will be hashed using a salted SHA-256 algorithm for initial segregation. This assumption is based on industry best practices for 'Highly Sensitive' data (CON-2788862587). The specific hashing algorithm and salt management strategy must be ratified by the Platform Administrator and security team.

### 4.12 NGO Operator Legal Entity Structure

To resolve KYC/AML compliance gaps and ensure proper liability distribution across the tripartite ecosystem, the legal structure of NGO Operators must be explicitly defined.

Legal Entity Classification: NGO Operators must be formally registered as 501(c)(3) non-profit organizations or their international equivalents to qualify for platform onboarding. This classification is required to satisfy KYC/AML regulations governing the flow of quasi-cash instruments (CON-B1DFEBEC8C). Governance & Accountability: Each NGO Operator must designate a primary Compliance Officer responsible for beneficiary eligibility verification and local regulatory adherence. The Platform Administrator (ACT-086A974D63) retains the right to audit NGO Operator compliance records and suspend onboarding privileges if KYC/AML standards are not met. Strategic Constraint: The legal entity structure must ensure that NGO Operators are legally insulated from platform-level financial liabilities while maintaining full accountability for beneficiary data handling and eligibility decisions.

This operating model ensures that MealCredit can scale to 50,000 MAU while maintaining the highest standards of security, privacy, and financial integrity. The Platform Administrator and NGO Operator roles are clearly defined in their compliance responsibilities, ensuring accountability and traceability.

This artifact establishes the foundational operating model for the MealCredit platform, explicitly defining the roles, responsibilities, and interaction boundaries for the six key actors: Donor (ACT-80C62C7814), Beneficiary (ACT-ADA6716160), Merchant (ACT-AF904DCFF9), NGO Operator (ACT-09E028AEB0), Platform Administrator (ACT-086A974D63), and Dispute Adjudicator (ACT-7BA340FF76). It maps the tripartite actor ecosystem to the required compliance and financial capabilities, defines the strategic roadmap, regulatory risk posture, and partnership requirements, and establishes the operating model for decoupling food assistance from social stigma through anonymous culinary credits.

### 5.13 Platform Administrator (ACT-086A974D63) Governance
The Platform Administrator acts as the neutral arbiter of the financial and technical infrastructure. Their authority is strictly bounded by the requirements of the Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE) and Compliance, Security & Audit (CAP-COMPLIANCE-SECURITY-AUDIT).

 Credit Pool Management: The Platform Administrator owns the global and regional Credit Pool Utilization Rate (CON-7031BE57B3). They are responsible for setting the automated alert thresholds and initiating liquidity injection protocols from Donor funds (ACT-80C62C7814). They do not decide who gets credits, only how much liquidity is available to the system.
 Merchant Onboarding & POS Integration (JNY-356F465DB3): The Platform Administrator defines the technical and financial criteria for Merchant (ACT-AF904DCFF9) acceptance, including PCI-DSS Level 1 compliance verification (CON-66390130AA) and Stripe Connected Account KYC requirements (CON-62097EBBF3). They manage the liability framework for merchant payouts.
 Dispute Adjudication Oversight: The Platform Administrator provides the technical infrastructure for the Dispute Adjudicator (ACT-7BA340FF76) but does not make final adjudication decisions on beneficiary eligibility. They handle technical disputes (e.g., failed POS callbacks, double-spending prevention per CON-61EC670500).

### 5.14 Transaction & Financial Engine
The Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE) serves as the operational backbone of the platform, governing the flow of funds, credit pool liquidity, and financial reconciliation. This engine ensures that the tripartite ecosystem operates with strict financial integrity and compliance.

 Credit Pool Management: The engine aggregates micro-donations into a centralized credit pool, managing liquidity across the three metropolitan footprints (SF, NYC, Chicago). It enforces automated alerts when the Credit Pool Utilization Rate (CON-7031BE57B3) approaches critical thresholds, ensuring sufficient funds are available for Beneficiary (ACT-ADA6716160) redemptions.
 Financial Reconciliation: Daily transaction logs from all Merchant (ACT-AF904DCFF9) partners are aggregated and reconciled against donor funds. The Platform Administrator (ACT-086A974D63) oversees this process to ensure that payouts align with verified redemption events, maintaining an immutable audit trail for SOC2 Type II compliance (CON-81FB01F06B).
 Liquidity & Velocity Monitoring: The engine tracks the Donation-to-Redemption Velocity (DRV) (CON-F89C70071E) to monitor the health of the credit distribution cycle. This metric ensures that donor funds are converted into active culinary credits efficiently, balancing donor confidence with operational liquidity.

### 5.15 Dispute Adjudicator (ACT-7BA340FF76) Escalation Path
The Dispute Adjudicator serves as the final arbiter for edge cases that cannot be resolved by the Platform Administrator or NGO Operator. This role is critical for maintaining trust in the tripartite model.

 Escalation Triggers:
 1. Beneficiary Eligibility Disputes: When a Beneficiary challenges an NGO Operator's eligibility decision.
 2. Merchant Payout Error Handling Flow (JNY-90B07623FB): When a Merchant disputes a payout calculation or a failed transaction that the Platform Administrator's automated systems cannot resolve.
 3. Fraud Allegations: When the Platform-NGO Fraud Investigation Flow (JNY-CA74D631DC) identifies potential collusion or sophisticated fraud that requires human review.
 Decision Rights: The Dispute Adjudicator has the authority to reverse transactions, suspend NGO Operator privileges, or blacklist Merchant accounts. Their decisions are final and are logged in the append-only cryptographic log (CON-6061FCCA83) for SOC2 Type II evidence (CON-81FB01F06B).

### 5.16 Donor (ACT-80C62C7814) & Beneficiary (ACT-ADA6716160) Interaction
 Donor: The Donor interacts primarily through the Donor Onboarding & Funding Activation (JNY-62D850E94B) journey. They configure donation preferences (round-up, directed impact, or open pool) and receive immutable transactional receipts within 120 seconds of Beneficiary redemption. They do not interact directly with Beneficiaries or Merchants.
 Beneficiary: The Beneficiary interacts through the Beneficiary Eligibility & Voucher Redemption (JNY-E82B8A88D8) journey. They receive anonymous culinary credits that are visually identical to consumer gift cards, ensuring no demographic data crosses into production logs. They interact with Merchants for redemption but have no direct financial link to Donors.

### 5.17 Knowledge Gaps and Assumptions

 KNOWLEDGE_GAP: The specific legal entity structure for the NGO Operators is not defined. This impacts the KYC/AML requirements for their Stripe Connected Accounts (CON-62097EBBF3). Legal must establish the exact compliance burden for NGO Operators before the Merchant Onboarding & POS Integration (JNY-356F465DB3) can be fully specified.
 ASSUMPTION: It is assumed that the Dispute Adjudicator is a human-in-the-loop role, not an automated system, given the sensitivity of eligibility and fraud decisions. This requires a dedicated interface in the Architectural surface: Client Interface Layer (SUR-43E71C4E2B) for the Dispute Adjudicator.
 ASSUMPTION: It is assumed that the Platform Administrator does not have access to the raw PII of Beneficiary (ACT-ADA6716160) to maintain strict anonymity. The NGO Operator acts as the trusted intermediary for all PII-related decisions.

This governance structure ensures that the MealCredit platform can scale to 50,000 MAU across three metropolitan footprints while maintaining the highest standards of compliance, security, and social impact integrity.

---

### 1.1 Donor Funding & Credit Pool Management

The financial lifecycle begins with the Donor (ACT-80C62C7814) funding the platform. To maintain anonymity and prevent de-anonymization attacks (CON-C22D030D21), donor funds are aggregated into a centralized Credit Pool rather than being directly assigned to specific beneficiaries at the point of donation.

 Funding Mechanism: Donors contribute via real-time micro-donations. These transactions are processed through the Payment Processing Surface (SUR-5B18C8719F) using Stripe Elements, ensuring zero raw card data touches MealCredit servers (CON-66390130AA).
 Credit Pool Utilization: The platform must monitor Credit Pool Utilization Rate with automated alerts triggering when thresholds exceed 85% (CON-7031BE57B3). This ensures sufficient liquidity for beneficiary redemptions across all three metro footprints (SF, NYC, Chicago).
 Donation-to-Redemption Velocity (DRV): The financial model tracks DRV to monitor liquidity health against a 14-day target (CON-F89C70071E). This metric is critical for balancing donor confidence (seeing impact) with operational liquidity (ensuring credits are available for redemption).
 Anonymity Preservation: Donor identity is cryptographically segregated from beneficiary redemption events. Analytics rely on UUIDv4 mapping (CON-23A501C051) to correlate impact without linking PII.

### 1.2 Merchant Payout & Liability Management

Merchant Partners (ACT-AF904DCFF9) are compensated for fulfilled culinary credits. The financial model must manage Stripe Connected Account liability and KYC compliance across multiple jurisdictions (SF, NYC, Chicago) (CON-62097EBBF3).

 Payout Flow: Payouts are processed via Stripe Connect, leveraging its native liability framework. The Platform Administrator (ACT-086A974D63) oversees the onboarding of Merchant Connected Accounts, ensuring KYC compliance before funds are released.
 Payout Error Handling: A dedicated Merchant Payout Error Handling Flow (JNY-90B07623FB) is established to manage failed payouts due to KYC expiration, bank account issues, or Stripe API errors. The Merchant & NGO Operations capability (CAP-MERCHANT-NGO-OPERATIONS) is responsible for resolving these errors.
 Data Residency: Payout data must comply with data residency and jurisdictional compliance for user data across multiple metropolitan regions (CON-30EA97016B). Financial records for each metro footprint are logically isolated to ensure jurisdictional integrity.

### 1.3 Refund & Reversal Handling

Refunds and reversals are critical for maintaining trust and financial accuracy. The model must handle edge cases such as double-spending prevention and voided transactions (CON-61EC670500).

 Refund Flow: The Merchant-Beneficiary Refund Flow (JNY-E5F45D37C6) allows for refunds initiated by the Merchant or Beneficiary. Refunds are processed through the Transaction Refund & Reversal Engine (CAP-TRANSACTION-REFUND-REVERSAL-ENGINE), which credits the original donor pool or adjusts the merchant's pending payout.
 Double-Spending Prevention: The financial ledger must implement strict controls to prevent double-spending. This is achieved through an append-only cryptographic log auditing in Aurora PostgreSQL for all financial ledger mutations (CON-6061FCCA83). Each transaction is hashed and chained, ensuring immutability.
 Reversal Latency: Refund processing must be completed within a defined operational window to maintain merchant cash flow. Any delays trigger an alert to the Platform Administrator.

### 1.4 Fraud Detection & Prevention Screening

Fraud prevention is a core component of the financial operating model, protecting both donors and merchants.

 Screening Mechanism: The Fraud Detection & Fraud Prevention Screening capability (CAP-FRAUD-DETECTION-FRAUD-PREVENTION-SCREENING) monitors all transactions for anomalous patterns. This includes monitoring for unusual donation spikes, rapid redemption cycles, or merchant account irregularities.
 Dispute Resolution: The Dispute Resolution & Chargeback Management capability (CAP-DISPUTE-RESOLUTION-CHARGEBACK-MANAGEMENT) handles chargebacks initiated by donors or merchants. The Dispute Adjudicator (ACT-7BA340FF76) reviews flagged transactions and makes final determinations based on evidence from the append-only ledger.
 Offline Fallback Security: For offline fallback QR/barcode tokens, the system must protect against replay attacks using time-bound cryptographic signatures (CON-AA83B13877). This ensures that even in low-connectivity scenarios, fraudulent redemptions are prevented.

### 1.5 Key Operational Risks

The following risks are identified as critical to the tripartite model (Donor, Beneficiary, Merchant) and NGO Operator governance. Each risk is mapped to its primary impact area and required mitigation posture.

 Double-Spending and Fraudulent Redemption (High Impact)
  Risk: Beneficiaries or malicious actors attempting to redeem the same culinary credit multiple times simultaneously, or using cloned offline fallback tokens.
  Impact: Direct financial loss to the Donor pool and Merchant partners; erosion of trust in the platform's financial integrity.
  Mitigation Posture: Implement deterministic HMAC-signed fallback vouchers for offline scenarios (CON-AA83B13877) and real-time Stripe Issuing virtual card provisioning for online/POS clearing. All redemption events must be logged in an append-only cryptographic ledger (CON-6061FCCA83) to enable forensic auditing.

 Beneficiary Data Leakage and De-anonymization (Critical Impact)
  Risk: Metadata analysis or database access errors linking Beneficiary (ACT-ADA6716160) identities to Donor (ACT-80C62C7814) contributions, violating the core mission of decoupling food assistance from social stigma.
  Impact: Severe reputational damage; violation of FTC anonymity guidelines (CON-C22D030D21); potential legal liability.
  Mitigation Posture: Cryptographically segregate beneficiary demographic data from public-facing data (CON-92F07E31B0). Restrict database access to cryptographic hashing layers only. Enforce strict data retention policies (CON-4820FAD5A9) and conduct regular de-anonymization attack simulations.

 Merchant Payout Failures and Reconciliation Drift (High Impact)
  Risk: Delays or errors in transferring cleared funds from the Platform to Merchant (ACT-AF904DCFF9) partners, leading to cash flow issues for restaurants and potential churn.
  Impact: Merchant dissatisfaction; disruption of service availability for Beneficiaries.
  Mitigation Posture: Implement robust error handling for Stripe Connected Account payouts (CAP-MERCHANT-PAYOUT-FAILURE-ERROR-HANDLING). Establish automated reconciliation processes to detect drift between ledger entries and bank statements. Define clear SLAs for payout processing.

 Credit Pool Liquidity Shortfalls (Medium Impact)
  Risk: Rapid depletion of the credit pool in a specific metro footprint due to higher-than-expected redemption rates, leaving Beneficiaries without access to credits.
  Impact: Service disruption for Beneficiaries; negative user experience.
  Mitigation Posture: Monitor Credit Pool Utilization Rate with automated alerts (CON-7031BE57B3). Implement dynamic credit distribution mechanisms to balance liquidity across metros. Define clear thresholds for triggering donor funding campaigns.

### 1.6 Success Metrics and KPIs

The following metrics will be used to monitor the health of the operating model post-launch. They are aligned with the system evolution objectives and project constraints.

 Credit Pool Utilization Rate (CPUR)
  Definition: The percentage of the total available credit pool that has been redeemed within a specific period.
  Target: Maintain CPUR between 60% and 85% to ensure liquidity without excessive waste. Trigger alerts if CPUR exceeds 85% (CON-7031BE57B3).
  Owner: Platform Administrator (ACT-086A974D63)

 Donation-to-Redemption Velocity (DRV)
  Definition: The average time elapsed between a Donor's contribution and the corresponding Beneficiary redemption event.
  Target: Achieve a DRV of 14 days or less to ensure timely impact and liquidity health (CON-F89C70071E).
  Owner: NGO Operator (ACT-09E028AEB0)

 POS Clearance Latency (p99)
  Definition: The 99th percentile latency for a redemption transaction from the initial scan/tap to final ledger entry.
  Target: Maintain p99 latency below 250ms for voucher creation and scanning callbacks under 10,000 concurrent connections (CON-7F03CF540E). Ensure Stripe Webhook Processing Latency averages below 150ms (CON-06232374D9).
  Owner: Platform Administrator (ACT-086A974D63)

 Merchant Payout Success Rate
  Definition: The percentage of merchant payout transactions that complete successfully without manual intervention or error handling.
  Target: Achieve a payout success rate of 99.5% or higher.
  Owner: Platform Administrator (ACT-086A974D63)

 Data Isolation Compliance Score
  Definition: A measure of the platform's adherence to data segregation and anonymization requirements, derived from automated audits and penetration testing.
  Target: 100% compliance with FTC anonymity guidelines (CON-C22D030D21) and PCI-DSS Level 1 requirements (CON-66390130AA).
  Owner: Dispute Adjudicator (ACT-7BA340FF76) / Compliance Officer

---

### 1.7 Phased Rollout Strategy

The platform will launch in three metropolitan footprints: San Francisco (SF), New York City (NYC), and Chicago (CHI). The rollout will follow a phased approach to manage operational complexity and compliance verification.

 Phase 1: San Francisco (SF)
  Focus: MVP validation, core actor flows (Donor, Beneficiary, Merchant), and initial compliance audits.
  Partners: Initial NGO partners in SF, select Merchant partners in high-traffic areas.
  Success Criteria: 5,000 MAU, successful PCI-DSS Level 1 certification, and stable Credit Pool Utilization Rate.

 Phase 2: New York City (NYC)
  Focus: Scale validation, increased Merchant density, and advanced fraud detection mechanisms.
  Partners: Expanded NGO network, larger Merchant partners with higher transaction volumes.
  Success Criteria: 15,000 MAU, reduced POS Clearance Latency, and improved Merchant Payout Success Rate.

 Phase 3: Chicago (CHI)
  Focus: Full multi-metro operational maturity, cross-metro liquidity balancing, and advanced analytics.
  Partners: Nationwide NGO partnerships, national Merchant chains.
  Success Criteria: 50,000 MAU, optimized Credit Pool Utilization Rate across all metros, and full SOC2 Type II compliance.

## 2. Actor Roles & Responsibilities

This section defines the six key actors in the MealCredit ecosystem, mapping their responsibilities to the platform's compliance, financial, and operational capabilities. The operating model ensures that the tripartite user base (Donors, Beneficiaries, Merchants) is supported by robust NGO governance and platform administration.

### 2.1 Beneficiary (ACT-ADA6716160)

The **Beneficiary (ACT-ADA6716160)** is the end-user receiving culinary credits. Their primary journey is the **Beneficiary Eligibility & Voucher Redemption (JNY-E82B8A88D8)**.

*   **Core Responsibilities:**
    *   Maintain an active profile managed by an NGO Operator.
    *   Utilize the mobile application to locate participating merchants and redeem credits.
    *   Adhere to the platform's code of conduct regarding fraud and misuse.
*   **Compliance & Security Boundaries:**
    *   **Absolute Anonymization:** The platform enforces strict data isolation where beneficiary demographic status and legal names are cryptographically segregated from public-facing data (CON-92F07E31B0). No PII is stored in production logs or exposed to donors.
    *   **Accessibility:** The mobile application and digital wallet passes must be fully compatible with screen readers and high-contrast modes to ensure equitable access for visually impaired users (CON-68497304B1).
    *   **Offline Access:** The platform must ensure offline fallback interfaces are intuitive and accessible without requiring complex technical troubleshooting, allowing redemption in low-connectivity environments (CON-FA7A13E601).

### 2.2 Donor (ACT-80C62C7814)

The **Donor (ACT-80C62C7814)** funds the credit pool through micro-donations. Their primary journey is **Donor Onboarding & Funding Activation (JNY-62D850E94B)**.

*   **Core Responsibilities:**
    *   Link a primary payment method via secure providers (e.g., Plaid/Stripe).
    *   Configure donation preferences (round-up, directed impact, or open pool).
    *   Receive immutable transactional receipts within 120 seconds of a beneficiary's redemption.
*   **Compliance & Security Boundaries:**
    *   **Impact Correlation:** Donors must receive impact receipts that correlate with beneficiary redemption events without linking PII, using UUIDv4 mapping for analytics (CON-23A501C051).
    *   **Data Retention:** Strict data retention policies must be defined for donor transaction history versus anonymous redemption analytics to ensure compliance with financial regulations (CON-4820FAD5A9).

### 2.3 Merchant (ACT-AF904DCFF9)

The **Merchant (ACT-AF904DCFF9)** represents commercial restaurant partners. Their primary journey is **Merchant Onboarding & POS Integration (JNY-356F465DB3)**.

*   **Core Responsibilities:**
    *   Submit business verification documents and banking details for KYC/AML compliance.
    *   Integrate with the standard POS gateway or activate the tablet-based edge dashboard.
    *   Process MealCredit tokens at the point of sale and manage real-time throttle parameters to prevent structural overload.
*   **Compliance & Security Boundaries:**
    *   **PCI-DSS Level 1:** Zero raw card data touches MealCredit servers; the platform relies entirely on Stripe Elements and Issuing for tokenization (CON-66390130AA).
    *   **Latency Optimization:** Real-time POS clearance must be optimized to prevent restaurant queue stagnation, targeting low-latency interactions (CON-5D64EBC654).
    *   **Payout Error Handling:** The platform must support the **Merchant Payout Error Handling Flow (JNY-90B07623FB)** to resolve discrepancies in daily settlements and ensure merchant trust.

### 2.4 NGO Operator (ACT-09E028AEB0)

The **NGO Operator (ACT-09E028AEB0)** acts as the governance layer for beneficiary eligibility. Their primary journey is **NGO Governance & Beneficiary Offboarding (JNY-4C4BA15817)**.

*   **Core Responsibilities:**
    *   Approve beneficiary profiles and assign initial credit balances.
    *   Initiate offboarding requests for beneficiaries who are no longer eligible.
    *   Confirm data export and account deactivation completion during offboarding.
*   **Compliance & Security Boundaries:**
    *   **KYC/AML Compliance:** NGO Operators must undergo rigorous verification to prevent fraud. The specific legal entity structure for NGO Operators is not yet defined, impacting the exact KYC/AML requirements for their Stripe Connected Accounts (CON-62097EBBF3). Legal must establish the exact compliance burden for NGO Operators before the Merchant Onboarding & POS Integration (JNY-356F465DB3) can be fully specified.
    *   **Fraud Investigation:** The platform must support the **Platform-NGO Fraud Investigation Flow (JNY-CA74D631DC)** to detect and isolate anomalous transaction patterns.

### 3.1 Identity & Access Management (CAP-IDENTITY-ACCESS-MANAGEMENT)

*   **Scope:** Manages authentication and authorization for all six actor roles.
*   **Operational Boundary:**
    *   Implements strict data isolation where beneficiary demographic status and legal names are cryptographically segregated from public-facing data (CON-92F07E31B0).
    *   Secures client-side storage on Expo devices using SecureStore for offline tokens, preventing token theft or cloning (CON-C42F7B521B).
    *   Protects against replay attacks on offline fallback QR/barcode tokens using time-bound cryptographic signatures (CON-AA83B13877).

### 3.3 Merchant & NGO Operations (CAP-MERCHANT-NGO-OPERATIONS)

*   **Scope:** Facilitates the onboarding, verification, and ongoing management of Merchants and NGO Operators.
*   **Operational Boundary:**
    *   **Merchant Onboarding:** Supports the **Merchant Onboarding & POS Integration (JNY-356F465DB3)** journey, including KYC/AML verification and POS gateway integration.
    *   **NGO Governance:** Supports the **NGO Governance & Beneficiary Offboarding (JNY-4C4BA15817)** journey, including profile approval and data purging.
    *   **Matchmaking:** Provides the **Marketplace & Matchmaking (CAP-MARKETPLACE-MATCHMAKING)** capability to connect Beneficiaries with participating Merchants based on location and dietary flags.

### Phase 1: MVP & Single-City Launch
*   **Focus:** Establish core financial engine, basic POS integration, and initial NGO partnerships in one metro footprint.
*   **Key Deliverables:**
    *   Functional **Donor Onboarding & Funding Activation (JNY-62D850E94B)**.
    *   Basic **Beneficiary Eligibility & Voucher Redemption (JNY-E82B8A88D8)**.
    *   Initial **Merchant Onboarding & POS Integration (JNY-356F465DB3)**.
    *   Achieve 99.99% operational uptime across AWS multi-AZ configurations for all critical service endpoints (CON-FD21121DD5).

### Phase 2: Multi-City Scale & Optimization
*   **Focus:** Expand to SF, NYC, and Chicago; optimize latency and cache performance.
*   **Key Deliverables:**
    *   Scale the anonymous credit distribution engine during peak event-driven load (CON-121117F5A2).
    *   Maintain Cache Hit Ratio (CHR) above 92% for restaurant search queries using the Redis Enterprise Cluster (CON-EA7C3EFECB).
    *   Maintain p99 latency below 250ms for voucher creation and scanning callbacks under 10,000 concurrent connections (CON-7F03CF540E).
    *   Ensure Stripe Webhook Processing Latency averages below 150ms from card tap to merchant ledger entry (CON-06232374D9).

## 5. Unresolved Questions & Knowledge Gaps

The following items require resolution before the platform can proceed to detailed design and implementation.

*   **KNOWLEDGE_GAP:** The specific legal entity structure for the NGO Operators is not defined. This impacts the KYC/AML requirements for their Stripe Connected Accounts (CON-62097EBBF3). Legal must establish the exact compliance burden for NGO Operators before the Merchant Onboarding & POS Integration (JNY-356F465DB3) can be fully specified.
*   **KNOWLEDGE_GAP:** The exact rules for cross-border data residency compliance if the platform expands beyond the initial US metro footprints are not yet defined. This impacts the data isolation strategy for future phases.
*   **KNOWLEDGE_GAP:** The specific algorithm for correlating donor impact receipts with beneficiary redemption events without linking PII is not yet defined. UUIDv4 mapping is proposed, but the exact implementation details need to be ratified.
*   **KNOWLEDGE_GAP:** The specific retention period for donor transaction history vs. anonymous redemption analytics is not yet defined. This must be aligned with FTC guidelines and internal data governance policies.

## 6. Conclusion

This Operating Model & Stakeholder Alignment artifact provides a comprehensive framework for the MealCredit platform. It defines the roles, responsibilities, and interaction boundaries for all key actors, maps the tripartite ecosystem to compliance and financial capabilities, and establishes the strategic roadmap for phased rollout. By addressing the critical ID binding mismatches and explicitly defining the NGO Operator legal entity structure, this artifact ensures that the platform can scale to 50,000 MAU across three metropolitan footprints while maintaining the highest standards of compliance, security, and social impact integrity.
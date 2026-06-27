# Dispute Resolution & Fraud Investigation

## 1. Beneficiary-Platform Dispute Flow (JNY-2B038C9362)

### 1.2. Core Principles
1. **Dignity and Frictionless Access**: The interface must be simple, non-judgmental, and accessible. A Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) should not feel stigmatized when reporting an issue.
2. **Absolute Anonymity**: The dispute submission must not require PII. The system must rely on transactional metadata (e.g., transaction hash, timestamp, merchant ID) to correlate the dispute with the ledger.
3. **PCI-DSS Level 1 Compliance**: The dispute interface must never accept, store, or transmit raw card data. All financial references must be tokenized or hashed.
4. **SOC2 Type II Structural Planning**: All dispute interactions must be logged to AWS CloudTrail ([CON-FBBBF07295](../project_glossary.md#con-fbbbf07295)) for auditability, ensuring that the Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) can investigate without accessing beneficiary PII.

### 1.3. User Stories

#### Story 1.1: Frictionless Dispute Initiation
As a Beneficiary (ACT-ADA6716160),
I want to report a transaction error using only the transaction reference (e.g., a QR code or transaction hash) from my Redemption History ([CON-2D70EDCDEE](../project_glossary.md#con-2d70edcdee)),
So that I can resolve the issue without sharing my identity or navigating a complex form.

**Acceptance Criteria:**
- The Beneficiary (ACT-ADA6716160) can access a "Report an Issue" button directly from the transaction details in their Redemption History (CON-2D70EDCDEE).
- The system pre-populates the dispute form with the transaction hash, timestamp, and merchant ID.
- The Beneficiary (ACT-ADA6716160) can select a reason for the dispute from a predefined, non-stigmatizing list (e.g., "Double Charged," "Credit Not Applied," "Incorrect Amount").
- The Beneficiary (ACT-ADA6716160) can optionally add a text description, but it is not required.
- The system confirms receipt of the dispute with a generic, non-descriptive message (e.g., "We've received your report and will look into it.").

#### Story 1.2: Anonymous Evidence Submission
As a Beneficiary (ACT-ADA6716160),
I want to upload evidence (e.g., a photo of a receipt) without attaching my name or account details,
So that the Platform Administrator (ACT-086A974D63) can investigate the issue while maintaining my anonymity.

**Acceptance Criteria:**
- The system allows the Beneficiary (ACT-ADA6716160) to upload a single image file as evidence.
- The system automatically strips all metadata (EXIF data) from the uploaded image to prevent de-anonymization via metadata analysis ([CON-C22D030D21](../project_glossary.md#con-c22d030d21)).
- The Beneficiary (ACT-ADA6716160) is not required to provide any additional personal information to upload evidence.

#### Story 1.3: Resolution Notification
As a Beneficiary (ACT-ADA6716160),
I want to receive a notification when my dispute is resolved,
So that I know if my credits have been restored or if the issue was not valid, without being able to trace the investigation process.

**Acceptance Criteria:**
- The Beneficiary (ACT-ADA6716160) receives a push notification or in-app message when the dispute status changes to "Resolved."
- The notification does not reveal the outcome details (e.g., "Credits Restored" vs. "Dispute Denied") to prevent potential social bias or stigma. Instead, it provides a generic message (e.g., "Your report has been reviewed.").
- If credits are restored, they are automatically added to the Beneficiary (ACT-ADA6716160)'s balance without requiring further action.

### 1.4. Edge Cases and Error Flows

1. **Duplicate Dispute Submission**:
   - **Scenario**: A Beneficiary (ACT-ADA6716160) submits multiple disputes for the same transaction.
   - **Handling**: The system detects duplicate transaction hashes and merges the new submission into the existing dispute case. The Beneficiary (ACT-ADA6716160) is notified that the case is already under review.

2. **Invalid Transaction Reference**:
   - **Scenario**: A Beneficiary (ACT-ADA6716160) attempts to report a dispute for a transaction that does not exist or is outside the retention period.
   - **Handling**: The system displays a clear, non-technical error message (e.g., "We couldn't find this transaction. Please check the details and try again."). No PII is logged in the error response.

3. **Fraudulent Dispute Pattern**:
   - **Scenario**: A Beneficiary (ACT-ADA6716160) submits a high volume of disputes that are later determined to be fraudulent.
   - **Handling**: The Platform Administrator (ACT-086A974D63) can flag the account for review based on aggregated, anonymized dispute patterns. The Beneficiary (ACT-ADA6716160) is not notified of the fraud flag to prevent retaliation or gaming of the system.

### 1.5. Assumptions
- **ASSUMPTION**: Transaction Hash Uniqueness - The transaction hash is assumed to be globally unique and sufficient to identify a specific transaction without PII. Evidence needed: Verification from the Transaction & Financial Engine ([CAP-TRANSACTION-FINANCIAL-ENGINE](../project_glossary.md#cap-transaction-financial-engine)) that hashes are collision-resistant and unique.
- **ASSUMPTION**: Push Notification Delivery - The system assumes that push notifications are reliably delivered to the Beneficiary (ACT-ADA6716160)'s device. Evidence needed: Confirmation from the Client Interface Layer ([SUR-43E71C4E2B](../project_glossary.md#sur-43e71c4e2b)) that notification delivery rates meet the 99.99% uptime target ([CON-BF1CD5707E](../project_glossary.md#con-bf1cd5707e)).

---

## 2. Merchant-Beneficiary Refund Flow (JNY-E5F45D37C6)

### 2.1. Purpose and Scope
This section defines the product-level workflow for the Merchant-Beneficiary Refund Flow ([JNY-E5F45D37C6](../project_glossary.md#jny-e5f45d37c6)). The primary objective is to enable Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) partners to reverse transactions for Beneficiary (ACT-ADA6716160) users in cases of error, while strictly maintaining the platform's core value proposition: absolute anonymity and dignity. The flow must prevent any exposure of Beneficiary PII (legal names, demographic status) to the Merchant, adhering to Implied concern: Implied concern: Implement strict data isolation where beneficiary demographic status and legal names are cryptographically segreg... ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4)) and Implied concern: Implied concern: Implement strict data isolation where beneficiary demographic status and legal names are cryptographically segregated from public ... ([CON-92F07E31B0](../project_glossary.md#con-92f07e31b0)).

### 2.2. Trigger Conditions for Refunds
Refunds are initiated only under specific, verifiable conditions to prevent fraud and ensure financial integrity (Implied concern: Handling of financial edge cases such as double-spending prevention and voided transactions ([CON-61EC670500](../project_glossary.md#con-61ec670500))). The Merchant interface will only allow refund initiation for the following scenarios:

1. **Double-Scan/Double-Tap**: The Beneficiary's credit was deducted twice for a single transaction due to a POS latency issue (Implied concern: Implied concern: Ensure Stripe Webhook Processing Latency averages below 150ms from card tap to merchant ledger entry. ([CON-06232374D9](../project_glossary.md#con-06232374d9))).
2. **Voided Transaction**: The Merchant cancelled the order before the Beneficiary received the goods/services, but the credit was already tentatively reserved or deducted.
3. **Service Failure**: The goods/services were not provided, or were significantly different from what was advertised, requiring a full reversal.

**KNOWLEDGE_GAP**: The exact time window (e.g., 5 minutes, 24 hours) within which a Merchant can initiate a refund for a double-scan must be established by the Platform Administrator to balance user experience with fraud prevention.

#### Story 2.3.1: Merchant Initiates Refund via POS Interface
As a Merchant (ACT-AF904DCFF9),
I want to initiate a refund for a recent transaction using a transaction hash or QR code,
So that I can correct errors without needing to know the Beneficiary's identity.

**Acceptance Criteria:**
- The Merchant POS interface provides a "Refund" button for transactions completed within the last [KNOWLEDGE_GAP: time window].
- The Merchant is prompted to enter the Transaction Hash (a client-side generated hash accessible to the Beneficiary via their Redemption History) or scan the Beneficiary's Offline Fallback QR/Barcode.
- The system validates the transaction hash against the Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE) ledger.
- The Merchant sees only the transaction amount, timestamp, and a masked transaction ID. No Beneficiary name, photo, or demographic data is displayed.
- The Merchant selects the reason for the refund (Double-Scan, Void, Service Failure).

#### Story 2.3.2: System Executes Anonymized Credit Reversal
As a Platform System,
I want to reverse the credit deduction in the Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE) and log the event in the append-only cryptographic log ([CON-1762EA5021](../project_glossary.md#con-1762ea5021)),
So that the Beneficiary's credit balance is restored without exposing any PII to the Merchant.

**Acceptance Criteria:**
- Upon Merchant confirmation, the system triggers a credit reversal in the Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE).
- The reversal is logged in the append-only cryptographic log auditing in Aurora PostgreSQL (CON-1762EA5021) with a hash checksum to ensure immutability (Implied concern: Implied concern: Implement append-only cryptographic log auditing in Aurora PostgreSQL for all financial ledger mutations. ([CON-6061FCCA83](../project_glossary.md#con-6061fcca83))).
- The Beneficiary's credit pool is updated in real-time. If the Beneficiary is offline, the credit is restored upon their next sync.
- The system generates a Dispute Resolution & Chargeback Management ([CAP-DISPUTE-RESOLUTION-CHARGEBACK-MANAGEMENT](../project_glossary.md#cap-dispute-resolution-chargeback-management)) record for audit purposes, linking the Merchant's action to the Beneficiary's transaction via a non-PII UUIDv4 mapping (Implied concern: Implied concern: Correlate donor impact receipts with beneficiary redemption events without linking PII, using UUIDv4 mapping for analytics. ([CON-23A501C051](../project_glossary.md#con-23a501c051))).

#### Story 2.3.3: Beneficiary Receives Anonymized Refund Notification
As a Beneficiary (ACT-ADA6716160),
I want to receive a notification that my credit has been restored,
So that I am aware of the correction without feeling stigmatized or exposed.

**Acceptance Criteria:**
- The Beneficiary receives a push notification via the Expo mobile application stating: "Your credit for a recent transaction has been restored."
- The notification does not mention the Merchant's name, the reason for the refund, or any PII.
- The Beneficiary can view the restored credit in their Redemption History as a "Refunded" entry, linked to the original transaction hash.
- The notification is delivered via Server-Sent Events (SSE) for real-time updates, ensuring low latency (Implied concern: Implied concern: Maintain p99 latency below 250ms for voucher creation and scanning callbacks under 10,000 concurrent connections. ([CON-6D5E21557B](../project_glossary.md#con-6d5e21557b))).

### 2.5. Compliance and Security Constraints

- **PCI-DSS Level 1**: The refund flow must not involve any raw card data. All transactions are processed through Stripe Elements and Stripe Issuing virtual cards, ensuring zero raw card data touches MealCredit servers (Implied concern: Implied concern: Enforce PCI-DSS Level 1 compliance by ensuring zero raw card data touches MealCredit servers, relying entirely on Stripe Elements/... ([CON-66390130AA](../project_glossary.md#con-66390130aa))).
- **SOC2 Type II**: All refund actions are logged in AWS CloudTrail for auditability (Implied concern: Implied concern: Log all administrative ledger operations and infrastructure changes to AWS CloudTrail for SOC2 Type II evidence. ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2))).
- **Anonymity**: The refund flow must not allow the Merchant to infer the Beneficiary's identity through metadata analysis (Implied concern: Implied concern: Adhere to FTC guidelines on anonymity, ensuring no de-anonymization attacks can link beneficiaries to donors through metadata anal... (CON-C22D030D21)).

### 2.6. Knowledge Gaps

- **KNOWLEDGE_GAP**: The exact time window for Merchant-initiated refunds (e.g., 5 minutes, 24 hours) must be established by the Platform Administrator to balance user experience with fraud prevention.
- **KNOWLEDGE_GAP**: The specific error codes and messages for the POS interface when a refund is denied (e.g., transaction already refunded, transaction expired) must be defined by the Design phase.
- **KNOWLEDGE_GAP**: The exact mechanism for handling refunds when the Beneficiary's credit pool is in a different metro footprint (SF, NYC, Chicago) than the Merchant must be defined by the Design phase, considering Implied concern: Implied concern: Data residency and jurisdictional compliance for user data across multiple metropolitan regions ([CON-30EA97016B](../project_glossary.md#con-30ea97016b)).

---

## 3. Platform-NGO Fraud Investigation Flow (JNY-CA74D631DC)

This section defines the product scope and user stories for the Platform-NGO Fraud Investigation Flow ([JNY-CA74D631DC](../project_glossary.md#jny-ca74d631dc)). It details the NGO Operator's role in investigating flagged transactions while adhering to SOC2 Type II audit logging requirements.

#### Story 3.1: NGO Operator Fraud Case Review
As an NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)),
I want to view a dashboard of flagged transactions and fraud cases,
So that I can prioritize and investigate potential fraud while maintaining beneficiary anonymity.

**Acceptance Criteria:**
1. The NGO Operator dashboard displays a list of flagged cases with a unique Case ID, timestamp, and risk score.
2. Each case summary must NOT display the Beneficiary's legal name or PII. Instead, it must display a masked identifier (e.g., BEN-XXXX-XXXX).
3. The operator can filter cases by risk score, date range, and metro footprint (SF, NYC, Chicago).
4. Clicking a case opens a detailed view showing transaction history, device fingerprints (hashed), and location data (city-level only).

#### Story 3.2: Investigate Suspicious Transaction
As an NGO Operator (ACT-09E028AEB0),
I want to drill down into a specific flagged transaction to see its full context,
So that I can determine if the activity is fraudulent or a false positive.

**Acceptance Criteria:**
1. The detailed view shows the transaction amount, merchant (ACT-AF904DCFF9), and timestamp.
2. The view includes a "Fraud Indicators" section listing reasons for the flag (e.g., "Velocity Check Failed," "Device Mismatch").
3. The operator can view the "Credit Pool Utilization" for the associated Beneficiary to check for anomalies ([CON-2059B17FB2](../project_glossary.md#con-2059b17fb2)).
4. All data access is logged to AWS CloudTrail for SOC2 Type II evidence (CON-FBBBF07295).

#### Story 3.3: Resolve Fraud Case
As an NGO Operator (ACT-09E028AEB0),
I want to mark a case as "Confirmed Fraud" or "False Positive" and take action,
So that the Platform can adjust the Beneficiary's credit pool and update the ledger.

**Acceptance Criteria:**
1. If "Confirmed Fraud," the operator can choose to "Revoke Credits" or "Suspend Account."
2. If "False Positive," the operator can "Clear Flag" and add a note for future reference.
3. The action triggers an automated notification to the Platform Administrator (ACT-086A974D63) for audit review.
4. The action is immutably logged in the append-only cryptographic log (CON-1762EA5021).

---

## 4. Dispute Resolution & Chargeback Management

This section defines the product scope for the Dispute Resolution & Chargeback Management capability (CAP-DISPUTE-RESOLUTION-CHARGEBACK-MANAGEMENT). It establishes the rules for handling financial reversals initiated by external payment processors (e.g., Stripe) and internal platform disputes, ensuring strict adherence to PCI-DSS Level 1 and SOC2 Type II compliance while maintaining absolute beneficiary anonymity.

### 4.1. Chargeback Lifecycle & Rules

The platform must support a fully automated chargeback lifecycle for transactions processed via Stripe Issuing. When a Beneficiary (ACT-ADA6716160) disputes a transaction with their card issuer, the platform must receive a webhook notification and automatically trigger a credit reversal.

- **Automatic Reversal**: Upon receiving a chargeback.created event, the system must immediately reverse the corresponding culinary credit from the Merchant's (ACT-AF904DCFF9) ledger and restore it to the regional credit pool. This ensures the Beneficiary is not financially penalized for a disputed transaction.
- **Merchant Notification**: The Merchant must be notified of the chargeback via the Merchant Edge Dashboard. The notification must include the transaction hash and the reason code provided by the card issuer, but must NOT include any Beneficiary PII or identifying metadata.
- **Dispute Window**: The platform must enforce a strict dispute window of [KNOWLEDGE_GAP: Dispute Resolution & Chargeback Management - Product Owner must establish the exact number of days allowed for a Beneficiary to contest a transaction after redemption].
- **Evidence Submission**: If the Merchant wishes to contest the chargeback, they must be able to upload evidence (e.g., signed receipt, POS logs) within [KNOWLEDGE_GAP: Dispute Resolution & Chargeback Management - Product Owner must establish the number of days allowed for Merchant evidence submission].

### 4.2. Anonymity & Data Isolation in Disputes

To prevent de-anonymization attacks ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d)), all dispute-related data must be handled with extreme care.

- **Beneficiary Identity Masking**: The Beneficiary's identity must never be exposed to the Merchant or the Dispute Adjudicator ([ACT-7BA340FF76](../project_glossary.md#act-7ba340ff76)) during the dispute process. The dispute interface must rely solely on transaction hashes and non-identifying metadata.
- **Data Retention**: Dispute-related logs and evidence must be retained for [KNOWLEDGE_GAP: Dispute Resolution & Chargeback Management - Product Owner must establish the data retention period for dispute evidence in compliance with financial regulations]. After this period, all data must be cryptographically hashed or purged.
- **PCI-DSS Level 1 Compliance**: No raw card data may be stored or processed by the platform. All dispute evidence must be reviewed through a secure, isolated interface that does not cache or log sensitive payment information.

### 4.3. Fraud Investigation Integration

The Dispute Resolution & Chargeback Management capability must integrate with the Fraud Detection & Fraud Prevention Screening capability ([CAP-FRAUD-DETECTION-FRAUD-PREVENTION-SCREENING](../project_glossary.md#cap-fraud-detection-fraud-prevention-screening)) to identify patterns of fraudulent activity.

- **Pattern Detection**: The system must automatically flag transactions that exhibit signs of fraud, such as multiple chargebacks from the same Beneficiary within a short timeframe or unusual redemption patterns from a specific Merchant.
- **Flagging Mechanism**: When a potential fraud pattern is detected, the transaction must be automatically flagged for review by the NGO Operator (ACT-09E028AEB0) and the Platform Administrator (ACT-086A974D63). The flag must include a risk score and a summary of the suspicious activity, without revealing the Beneficiary's identity.
- **Resolution Workflow**: The NGO Operator must be able to investigate the flagged transaction and recommend a resolution (e.g., approve the chargeback, reject the chargeback, or escalate to the Platform Administrator). The Platform Administrator must have the final authority to approve or reject the resolution.

### 4.4. Compliance & Audit Trail

All dispute and chargeback actions must be logged in an append-only cryptographic log (CON-1762EA5021) to ensure a tamper-proof audit trail for SOC2 Type II compliance.

- **Immutable Logging**: Every action taken during the dispute lifecycle (e.g., chargeback received, evidence uploaded, resolution approved) must be recorded in the immutable log with a timestamp, actor ID, and action hash.
- **Audit Access**: Only the Platform Administrator and authorized compliance auditors may access the full audit log. Access must be logged and monitored.
- **Regulatory Reporting**: The platform must be able to generate reports on dispute rates, chargeback volumes, and fraud incidents for regulatory reporting purposes. These reports must be anonymized and aggregated to prevent de-anonymization.

---

## 5. Fraud Detection & Fraud Prevention Screening

This section defines the product scope for the Fraud Detection & Fraud Prevention Screening capability (CAP-FRAUD-DETECTION-FRAUD-PREVENTION-SCREENING). It establishes the automated screening triggers and criteria for flagging suspicious activity across all defined flows, ensuring the platform maintains trust while protecting the anonymity of the Beneficiary (ACT-ADA6716160).

### 5.1. Automated Screening Triggers

The system must automatically flag transactions and user behaviors that deviate from established baseline patterns. These triggers are designed to catch fraud without requiring manual intervention for every transaction.

- **Velocity Anomalies**:
  - **Beneficiary Velocity**: A single Beneficiary account attempting to redeem credits at an unusually high frequency within a short time window (e.g., more than X redemptions per hour). This helps detect account takeover or automated scraping of credits.
  - **Merchant Velocity**: A single Merchant (ACT-AF904DCFF9) processing an unusually high volume of refunds or voided transactions in a short period, which may indicate collusion or internal fraud.
  - **Geographic Impossibility**: A Beneficiary account attempting to redeem credits from two geographically distant locations within a timeframe that makes physical travel impossible.

- **Transaction Pattern Anomalies**:
  - **Round-Trip Funding**: Detection of funds flowing from a Donor ([ACT-80C62C7814](../project_glossary.md#act-80c62c7814)) to a specific Beneficiary and then back to the same Donor (or an associated account) via a Merchant, indicating potential money laundering or donation fraud.
  - **Structuring**: A Beneficiary consistently redeeming credits in amounts just below a certain threshold to avoid detection or reporting requirements.
  - **Unusual Merchant Activity**: A Merchant suddenly experiencing a spike in transactions from new, unverified Beneficiary accounts, which may indicate a new fraud ring targeting the platform.

- **Device & Behavioral Anomalies**:
  - **Device Fingerprinting**: A single device attempting to create multiple Beneficiary accounts or log into multiple accounts simultaneously.
  - **Bot-like Behavior**: Automated patterns in API requests or user interactions that suggest the use of bots or scripts to exploit the system.

### 5.2. Criteria for Flagging Suspicious Activity

When a trigger is hit, the system must flag the activity for review by the Platform Administrator (ACT-086A974D63) or the Dispute Adjudicator (ACT-7BA340FF76). The flagging criteria must be clear and actionable.

- **High Confidence Flags (Auto-Block)**:
  - **Confirmed Fraudulent Device**: A device fingerprint previously confirmed as fraudulent by the Dispute Adjudicator.
  - **PCI-DSS Violation Attempt**: Any attempt to transmit raw card data or PII through the platform, which is strictly prohibited (CON-66390130AA).
  - **Duplicate Transaction**: A transaction with the same hash and amount attempted twice within a very short window, indicating a potential double-spend attack.

- **Medium Confidence Flags (Manual Review)**:
  - **Velocity Threshold Exceeded**: A transaction that exceeds the defined velocity thresholds (e.g., X redemptions per hour) but does not meet the criteria for an auto-block.
  - **Geographic Anomaly**: A transaction from a location that is inconsistent with the user's typical pattern, but not impossible.
  - **New Merchant High Volume**: A new Merchant (ACT-AF904DCFF9) processing a high volume of transactions in the first 24 hours of onboarding.

- **Low Confidence Flags (Monitoring)**:
  - **Minor Velocity Deviation**: A transaction that slightly exceeds normal velocity patterns but is within acceptable bounds.
  - **Unusual but Plausible Behavior**: A transaction that is unusual but does not clearly indicate fraud (e.g., a Beneficiary redeeming credits at a new Merchant type).

### 5.3. Screening Across Defined Flows

The fraud detection system must be integrated into all key user journeys to ensure comprehensive coverage.

- **Beneficiary-Platform Dispute Flow ([JNY-2B038C9362](../project_glossary.md#jny-2b038c9362))**:
  - If a Beneficiary files a dispute, the system must automatically check for patterns of frequent disputes from the same account or Merchant. A high rate of disputes may indicate a fraudulent Beneficiary or a problematic Merchant.
  - The dispute submission interface must be monitored for bot-like behavior or automated submissions.

- **Merchant-Beneficiary Refund Flow (JNY-E5F45D37C6)**:
  - The refund process must be monitored for patterns of excessive refunds from a single Merchant or to a single Beneficiary. This helps detect collusion or internal fraud.
  - Refunds must be validated against the original transaction to ensure they are legitimate and not part of a round-trip funding scheme.

- **Platform-NGO Fraud Investigation Flow (JNY-CA74D631DC)**:
  - The NGO Operator (ACT-09E028AEB0) must have access to a dashboard that highlights flagged activities related to their Beneficiaries or Merchants. This allows for proactive investigation and management of fraud risks.
  - The Dispute Adjudicator (ACT-7BA340FF76) must be able to review flagged activities and make decisions on whether to block accounts, freeze funds, or escalate to law enforcement if necessary.

### 5.4. Knowledge Gaps

- **KNOWLEDGE_GAP**: Fraud Thresholds - Specific numerical thresholds for velocity anomalies (e.g., redemptions per hour) and geographic impossibility must be established by the Product Owner based on initial MVP data.
- **KNOWLEDGE_GAP**: Fraud Scoring Model - The specific algorithm or model used to calculate fraud confidence scores (High, Medium, Low) must be defined by the Data Science team.
- **KNOWLEDGE_GAP**: Law Enforcement Integration - The process for escalating confirmed fraud to law enforcement and the data that can be shared must be defined by the Legal and Compliance team.

### 5.5. Follow-Up Questions

- **Question**: Who owns the definition of fraud thresholds and scoring models?
  - **Why Critical**: These definitions are critical for the effectiveness of the fraud detection system.
  - **Answerable**: False
  - **Blocking**: True
  - **Source Role**: Executor
- **Question**: What is the process for appealing a fraud flag?
  - **Why Critical**: Users (Beneficiaries and Merchants) need a clear path to appeal false positives.
  - **Answerable**: False
  - **Blocking**: False
  - **Source Role**: Executor

---

## VP decision

**Decision:** Approved

---

## VP feedback

(No feedback)

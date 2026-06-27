# Merchant Onboarding & POS Integration

## 1. Merchant KYC/AML Verification Flow

This section defines the product requirements for the initial business verification and identity screening phase of the Merchant Onboarding & POS Integration journey. It ensures that all Merchant Partners (Restaurants) ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) are legally vetted to handle MealCredit quasi-cash instruments before they are granted access to the POS integration layer.

### 1.1. Onboarding Entry & Jurisdiction Detection

User Story: As a prospective Restaurant Partner, I want to begin the onboarding process by simply entering my business name and location, so that the system can automatically determine the specific financial regulations (KYC/AML) I must comply with based on my operating jurisdiction (SF, NYC, or Chicago).

Acceptance Criteria:
The Merchant Onboarding entry point ([JNY-356F465DB3](../project_glossary.md#jny-356f465db3)) must capture the primary business address and legal business name.
The system must dynamically load the required KYC/AML data fields based on the detected jurisdiction (SF, NYC, Chicago) to satisfy [CON-5BFA25E8F9](../project_glossary.md#con-5bfa25e8f9) (Manage Stripe Connected Account liability and KYC compliance across multiple jurisdictions).
If the business address falls outside the three initial metropolitan footprints, the system must display a clear "Service Not Available" state, deferring to the Merchant Onboarding & POS Integration scope boundary.

### 1.2. Business Verification Data Collection

User Story: As a Restaurant Partner, I need to provide specific business details (EIN, DBA, ownership structure) so that the platform can perform the necessary AML screening and establish the legal entity for Stripe Connect integration.

Acceptance Criteria:
The product must require the collection of the Employer Identification Number (EIN) or Social Security Number (SSN) for sole proprietors.
The product must require the collection of the "Doing Business As" (DBA) name if it differs from the legal entity name.
The product must require the collection of primary ownership details (name, DOB, address) for any individual owning 25% or more of the business, in alignment with standard AML beneficial ownership rules.
KNOWLEDGE_GAP: The exact percentage threshold for beneficial ownership (e.g., 25% vs 50%) must be established by the Compliance team to ensure alignment with [CON-B1DFEBEC8C](../project_glossary.md#con-b1dfebec8c) (Comply with financial regulations governing quasi-cash instruments, specifically regarding unclaimed property and escheatment laws).

### 1.3. Identity Screening Integration (Stripe Connect)

User Story: As a Restaurant Partner, I want to complete my identity verification through a secure, branded flow that integrates with Stripe Connect, so that I can be approved for payouts without the platform ever handling sensitive raw identity documents directly.

Acceptance Criteria:
The product must abstract the Stripe Connect onboarding flow into a seamless, multi-step UI that guides the Merchant through identity verification.
The system must ensure that no raw PII or sensitive identity documents are stored on MealCredit servers, relying entirely on Stripe Elements/Connected Accounts for payment processing, satisfying [CON-66390130AA](../project_glossary.md#con-66390130aa) (Enforce PCI-DSS Level 1 compliance by ensuring zero raw card data touches MealCredit servers).
The product must handle Stripe's asynchronous verification status updates, providing clear UI states for "Pending Review," "Approved," and "Rejected."

### 1.4. Approval and Rejection States

User Story: As a Restaurant Partner, I need to receive clear, actionable feedback if my KYC/AML verification is rejected, so that I can correct the information and resubmit without starting the entire onboarding process over.

Acceptance Criteria:
If the KYC/AML verification fails, the Merchant Dashboard must display a specific, non-technical reason for the rejection (e.g., "Name mismatch with government ID," "EIN not found in IRS database").
The product must allow Merchants to resubmit corrected information without losing previously entered business details.
The product must log all KYC/AML verification attempts and outcomes to AWS CloudTrail for SOC2 Type II evidence, as required by [CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2) (Log all administrative ledger operations and infrastructure changes to AWS CloudTrail for SOC2 Type II evidence).

### 1.7. Sibling Deferrals

Beneficiary Eligibility & Voucher Redemption: The specific rules for how a Merchant's approved status impacts their ability to receive MealCredit vouchers are defined in the Beneficiary Eligibility & Voucher Redemption artifact.
Donor Onboarding & Funding Activation: The funding source for the MealCredit vouchers is defined in the Donor Onboarding & Funding Activation artifact.
NGO Governance & Beneficiary Offboarding: The role of the NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) in verifying Merchant legitimacy is defined in the NGO Governance & Beneficiary Offboarding artifact.
Dispute Resolution & Fraud Investigation: The specific fraud investigation workflows triggered by KYC anomalies are defined in the Dispute Resolution & Fraud Investigation artifact.

---

### 2.1. Merchant Onboarding Journey (JNY-356F465DB3)

The Merchant Onboarding & POS Integration journey is a linear, multi-step flow designed to minimize drop-off while ensuring strict KYC/KYB (Know Your Customer/Business) compliance. The product must guide the Merchant through identity verification, business data collection, and payout configuration.

User Story: As a Merchant Partner, I want to complete my business verification and link my bank account through a single, guided interface so that I can start accepting MealCredit payments without navigating complex financial forms.

Acceptance Criteria:
1. Progressive Disclosure: The onboarding flow must dynamically adjust fields based on the Merchant's operating region (SF, NYC, or Chicago) to satisfy local regulatory requirements.
2. Identity Verification: The system must integrate with Stripe Identity (or equivalent) to verify the legal identity of the business owner. The Merchant must upload a government-issued ID and a selfie for liveness detection.
3. Business Data Collection: The system must collect the Employer Identification Number (EIN), DBA (Doing Business As) name, and business address. This data is used to screen against AML (Anti-Money Laundering) lists.
4. Rejection Handling: If KYC verification fails, the Merchant must receive a clear, non-technical error message explaining the reason (e.g., "ID image was blurry," "EIN does not match records") and be allowed to retry without losing previously entered data.
5. PCI-DSS Compliance: The Merchant must never be presented with a form to enter raw credit card numbers. All payment instrument data is collected via Stripe Elements or hosted fields.

### 2.2. Jurisdictional Compliance (SF, NYC, Chicago)

The platform must enforce strict data isolation and compliance rules based on the Merchant's physical location. The product must ensure that the Connected Account is configured correctly for each jurisdiction.

User Story: As a Platform Administrator, I need the system to automatically apply the correct KYC requirements and payout schedules based on the Merchant's registered business address so that we remain compliant with local financial regulations.

Acceptance Criteria:
1. Dynamic Form Fields:
SF (California): Must collect CA-specific business license numbers if applicable.
NYC (New York): Must collect NYC-specific business registration certificates.
Chicago (Illinois): Must collect IL-specific tax identification numbers.
2. Data Residency: Ensure cross-border data residency compliance if the platform expands beyond the initial US metro footprints. For now, all data must be stored in US-based AWS regions.
3. Unclaimed Property: The system must track unclaimed property laws for each jurisdiction. If a Merchant's payout is held for more than the statutory period, the system must flag the account for escheatment review.
KNOWLEDGE_GAP: The exact statutory period for unclaimed property escheatment must be established by the Legal team to ensure alignment with CON-B1DFEBEC8C (Comply with financial regulations governing quasi-cash instruments, specifically regarding unclaimed property and escheatment laws).

### 2.3. Payout Configuration & Scheduling

The product must define how Merchants configure their payout preferences and how the platform handles the automated transfer of funds from the Stripe Connected Account to the Merchant's bank account.

User Story: As a Merchant, I want to choose my payout schedule (daily, weekly, or monthly) and link my primary business bank account so that I receive my earnings automatically without manual intervention.

Acceptance Criteria:
1. Bank Account Linking: The system must use Stripe's bank account tokenization to securely link the Merchant's bank account. The Merchant must confirm the account via micro-deposits or instant verification.
2. Payout Schedule Options: The system must offer at least three payout schedules: Daily, Weekly, and Monthly. The default schedule must be established by the Finance team.
KNOWLEDGE_GAP: The default payout schedule for new Merchants must be established by the Finance team to ensure alignment with operational cash-flow requirements.
3. Payout Delays: The system must enforce a holding period for new Merchants (e.g., 7 days) to mitigate fraud risk. This holding period must be clearly communicated during onboarding.
4. Payout Errors: If a payout fails due to bank account issues, the system must notify the Merchant via email and in-app notification, providing a direct link to update their banking details.

### 2.4. Liability & Risk Management

The product must ensure that the platform's liability is minimized by leveraging Stripe Connect's liability shift features. The Merchant must be fully aware of their responsibilities regarding chargebacks and fraud.

User Story: As a Platform Administrator, I need to ensure that all Merchants are legally bound to Stripe's terms of service and understand their liability for chargebacks and fraud before they can activate their POS integration.

Acceptance Criteria:
1. Terms of Service Acceptance: The Merchant must explicitly accept Stripe's Terms of Service and the Platform's Merchant Agreement during onboarding. This acceptance must be logged for audit purposes.
2. Chargeback Education: The system must provide a brief, interactive tutorial on how to handle chargebacks, including the importance of retaining proof of delivery (e.g., signed receipts, photos of the meal).
3. Fraud Monitoring: The system must integrate with Stripe Radar to automatically flag suspicious transactions. Merchants must be able to view their fraud score and transaction history in the Merchant Edge Dashboard.

### 2.5. Integration with POS Systems

The product must define the contract for how POS systems interact with the MealCredit platform to process anonymous credit redemptions. This integration must be robust, low-latency, and secure.

User Story: As a Merchant, I want my existing POS system to seamlessly accept MealCredit payments so that my staff can process transactions without learning a new interface.

Acceptance Criteria:
1. POS Gateway Integration: The system must support integration with major POS providers (e.g., Toast, Square, Clover) via a standardized API. The integration must be configured by the Platform Administrator or the NGO Operator.
2. Asynchronous Processing: POS transactions must be processed asynchronously via gRPC services to ensure high availability and low latency. The POS system must receive a confirmation within the established latency threshold.
KNOWLEDGE_GAP: The exact POS clearance latency threshold must be established by the Engineering team to ensure alignment with [CON-06232374D9](../project_glossary.md#con-06232374d9) (Implied concern: Ensure Stripe Webhook Processing Latency averages below 150ms from card tap to merchant ledger entry).
3. Offline Fallback: In the event of a network outage, the POS system must be able to process transactions using a time-bound, HMAC-signed QR code. The product must define the user experience for this offline mode, ensuring it is intuitive and accessible.
4. Reconciliation: The system must provide a daily reconciliation report to the Merchant, detailing all transactions, fees, and net payouts. This report must be accessible via the Merchant Edge Dashboard.

### 2.7. Edge Cases & Error Flows

1. KYC Rejection: If the Merchant's KYC is rejected, the system must provide a clear reason and allow them to resubmit. The Merchant's account must be in a 'Pending Verification' state until approved.
2. Bank Account Mismatch: If the Merchant's bank account details do not match the legal business name, the system must flag the account for manual review by the Platform Administrator.
3. POS Integration Failure: If the POS integration fails to connect, the system must notify the Merchant and provide troubleshooting steps. The Merchant must be able to retry the connection from the dashboard.
4. Payout Failure: If a payout fails, the system must hold the funds in the Stripe Connected Account and notify the Merchant. The Merchant must be able to update their banking details and retry the payout.

### 2.8. Accessibility & UX Standards

The Merchant Edge Dashboard must adhere to WCAG 2.1 AA standards, ensuring keyboard-only navigation and low-vision readability. This is critical for ensuring that all Merchants, regardless of ability, can manage their accounts effectively.

Acceptance Criteria:
1. Keyboard Navigation: All interactive elements in the onboarding flow and dashboard must be accessible via keyboard navigation.
2. Screen Reader Compatibility: All form fields, error messages, and status updates must be properly labeled for screen readers.
3. High Contrast Mode: The dashboard must support high-contrast modes to assist users with low vision.

### 2.9. Sibling Deferrals

Beneficiary Eligibility & Voucher Redemption: This artifact's voucher issuance defers to [JNY-E82B8A88D8](../project_glossary.md#jny-e82b8a88d8) for specific eligibility rules; see that artifact for the full treatment.
Donor Onboarding & Funding Activation: This artifact's funding source defers to [JNY-62D850E94B](../project_glossary.md#jny-62d850e94b) for donor impact flows; see that artifact for the full treatment.
NGO Governance & Beneficiary Offboarding: This artifact's NGO verification defers to [JNY-4C4BA15817](../project_glossary.md#jny-4c4ba15817) for offboarding workflows; see that artifact for the full treatment.
Dispute Resolution & Fraud Investigation: This artifact's fraud investigation defers to [JNY-2B038C9362](../project_glossary.md#jny-2b038c9362) for adjudication processes; see that artifact for the full treatment.

---

## 3. Merchant Edge Dashboard UX

### 3.1. Design Philosophy & Accessibility Mandate
The Merchant Edge Dashboard is the primary operational interface for the Merchant (ACT-AF904DCFF9) to manage their restaurant's participation in the MealCredit platform. Given the diverse nature of restaurant staff (including individuals with varying levels of technical proficiency and potential visual or motor impairments), the dashboard must strictly adhere to WCAG 2.1 AA standards. This is not merely a compliance checkbox but a core usability requirement to ensure that all restaurant employees can effectively process transactions and manage finances.

Accessibility Standards:
Keyboard-Only Navigation: All interactive elements (buttons, forms, tables, modals) must be fully operable using only a keyboard (Tab, Shift+Tab, Enter, Escape, Arrow keys). Focus indicators must be highly visible (e.g., a 3px solid outline with high contrast against the background).
Low-Vision Readability: The interface must support dynamic text resizing up to 200% without loss of content or functionality. Color must not be the sole means of conveying information (e.g., error states must include icons and text labels, not just red borders).
Screen Reader Compatibility: All dynamic content updates (e.g., real-time transaction notifications) must be announced to screen readers using ARIA live regions.

### 3.2. Dashboard Layout & Information Architecture
The dashboard is structured into three primary views: Overview, Transactions, and Payouts. This structure is designed to provide immediate financial visibility while allowing deep dives into specific operational details.

#### 3.2.1. Overview View (Home)
This is the default landing page, providing a high-level snapshot of the merchant's financial health and recent activity.

Key Metrics Cards:
Today's Revenue: Displays the total amount of MealCredit redeemed today. This is updated in real-time via Server-Sent Events (SSE) to ensure accuracy during peak hours.
Pending Payouts: Shows the total amount of funds currently in the settlement process, along with the estimated payout date.
Active Vouchers: Displays the number of active, unexpired vouchers currently in the merchant's POS system (for inventory management purposes).

Recent Transactions Feed:
A scrollable list of the last 10 transactions.
Each entry includes: Timestamp, Transaction ID (truncated for privacy, e.g., TXN-...4567), Amount, and Status (e.g., Completed, Pending, Failed).
Action: Clicking/tapping an entry expands to show full details, including the anonymous Beneficiary ID (for internal tracking, if required by local NGO policy) and the specific restaurant location (if multi-location).

#### 3.2.2. Transactions View
This view provides a comprehensive, filterable history of all financial activity.

Filtering & Sorting:
Users can filter transactions by date range, status, and amount.
Sorting is available by date (newest/oldest) and amount (highest/lowest).
Search: A search bar allows filtering by Transaction ID or anonymous Beneficiary ID.

Transaction Detail Modal:
When a transaction is selected, a modal opens with full details:
Transaction ID: Full, untruncated ID.
Timestamp: Exact date and time of the transaction.
Amount: The value of the MealCredit redeemed.
Status: Current status (e.g., Settled, Disputed, Refunded).
POS Terminal ID: The specific terminal used for the transaction (critical for multi-location restaurants).
Error Message (if applicable): If the transaction failed, a clear, human-readable error message is displayed (e.g., "Insufficient credit pool balance" or "Network timeout").

#### 3.2.3. Payouts View
This view manages the merchant's connection to Stripe Connect and tracks the flow of funds.

Payout Schedule:
Displays the current payout schedule (e.g., "Daily at 5:00 PM PST").
Status Indicator: A clear visual indicator (e.g., a green checkmark for "On Track", a yellow warning for "Delayed") shows the status of the next scheduled payout.

Payout History:
A table listing all past payouts, including:
Payout Date: The date the funds were transferred.
Amount: The total amount transferred.
Stripe Payout ID: The reference ID from Stripe for reconciliation.
Status: Completed, Pending, or Failed.

- Bank Account Management:
- A secure section to view and update the linked bank account details (managed via Stripe Connect's secure UI, ensuring PCI-DSS compliance). The dashboard itself does not store or display raw bank account numbers.

### 3.3. Real-Time Financial Visibility & Offline Fallback Integration

The dashboard must provide real-time visibility into transaction status, even in the event of network interruptions, by integrating with the offline QR/barcode token management interface.

- **Real-Time Sync:**
  - The dashboard uses Server-Sent Events (SSE) to push transaction updates to the Merchant's browser. This ensures that the "Today's Revenue" card and the "Recent Transactions Feed" are always up-to-date without requiring a page refresh.

- **Offline Fallback Status:**
  - A persistent status banner at the top of the dashboard indicates the current connectivity status: "Online" or "Offline - Syncing".
  - When in "Offline - Syncing" mode, the dashboard displays a count of transactions pending upload (e.g., "3 transactions pending sync").
  - Once the connection is restored, the dashboard automatically syncs the pending transactions and updates the "Today's Revenue" and "Recent Transactions Feed" accordingly. A success notification is displayed to the user.

- **QR/Barcode Token Management:**
  - A dedicated section within the "Transactions" view allows the Merchant to view the status of their offline QR/barcode tokens.
  - This includes a list of active tokens, their expiration times, and a log of any failed redemption attempts due to token replay or expiration.

### 3.4. Error States & Empty States

Clear, actionable error and empty states are critical for maintaining Merchant trust and operational efficiency.

**Error States:**
- **Network Error:** If the dashboard loses connection, a prominent banner appears: "Connection lost. Transactions are being stored locally and will sync automatically when the connection is restored."
- **Payout Failure:** If a payout fails, a detailed error message is displayed in the "Payouts" view, along with a "Contact Support" button that opens a pre-filled support ticket with the relevant Stripe error code.

**Empty States:**
- **No Transactions:** If no transactions have occurred today, the "Recent Transactions Feed" displays a friendly message: "No transactions yet today. Your first redemption will appear here."
- **No Pending Payouts:** If no payouts are currently in process, the "Pending Payouts" card displays: "No pending payouts. Your next payout is scheduled for [Date]."

---

## 4. Offline Fallback QR/Barcode Token System

This section defines the product logic and user experience for the offline fallback QR/barcode token system. This capability ensures that Merchant Partners (Restaurants) can continue to accept MealCredit redemptions during network outages, maintaining operational continuity and trust with Beneficiaries.

### 4.1. Product Objective & Scope

The Offline Fallback Token System allows a Merchant to generate a time-bound, cryptographically signed QR code that a Beneficiary can present to clear a transaction without real-time connectivity to the MealCredit core. The system must balance three competing priorities:
1. **Operational Continuity:** Ensure zero downtime for Merchants during network failures.
2. **Security:** Prevent replay attacks and double-spending using time-bound cryptographic signatures.
3. **User Experience:** Maintain the frictionless, stigma-free experience for Beneficiaries.

**Scope Boundary:** This artifact defines the product behavior, token lifecycle, and Merchant/Beneficiary UX. The technical implementation of the cryptographic signing (e.g., specific HMAC algorithms) is deferred to the Design phase, but the product must mandate the security properties (time-bound, non-reusable).

### 4.2. Actor Roles & Responsibilities

- **Merchant (ACT-AF904DCFF9):** Initiates the offline mode, generates the fallback token, and reviews pending offline transactions upon reconnection.
- **Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)):** Presents the offline token for redemption. The Beneficiary must have sufficient credit balance (verified locally or via cached state) to initiate the request.
- **Platform System:** Validates the token signature and reconciles the transaction asynchronously once connectivity is restored.

### 4.3. User Journey: Offline Redemption Flow

#### 4.3.1. Merchant Initiates Offline Mode

1. **Trigger:** The Merchant detects a loss of network connectivity or manually activates "Offline Mode" via the Merchant Edge Dashboard.
2. **System Response:** The Merchant Dashboard displays a prominent "Offline Mode Active" banner. The system generates a new Offline Fallback Token (a QR code) valid for a specific time window.
3. **Token Display:** The QR code is displayed on the Merchant's POS device or tablet. The token includes a visible countdown timer (e.g., "Valid for 15 minutes") to reinforce its time-bound nature.

#### 4.3.2. Beneficiary Presents Token

1. **Action:** The Beneficiary opens their MealCredit mobile app and selects "Pay with Offline Token."
2. **Validation:** The app verifies the Beneficiary's local cached balance (if available) or prompts the Beneficiary to proceed with a "Pending" status if offline.
3. **Presentation:** The Beneficiary displays their unique, time-bound QR code to the Merchant.

#### 4.3.3. Token Exchange & Capture

1. **Scan:** The Merchant scans the Beneficiary's QR code using the Merchant Edge Dashboard.
2. **Verification:** The Merchant's device performs a local cryptographic verification of the Beneficiary's token signature. This ensures the token is valid and has not been tampered with.
3. **Confirmation:** Upon successful local verification, the Merchant's device displays "Payment Accepted (Offline)." The transaction is stored locally in a secure, pending queue.

### 4.5. Merchant Edge Dashboard: Offline Transaction Management

The Merchant Edge Dashboard ([CON-6C177D0102](../project_glossary.md#con-6c177d0102)) must provide clear visibility into offline transactions.

1. **Pending Transactions Queue:** A dedicated section in the dashboard lists all offline transactions awaiting reconciliation. Each entry shows:
   - Transaction ID
   - Timestamp (local device time)
   - Amount
   - Status (e.g., "Pending Reconciliation")
2. **Reconciliation Status:** Upon reconnection, the dashboard updates the status of each pending transaction to "Settled" or "Failed" (if a double-spend is detected).
3. **Accessibility:** The dashboard must support keyboard-only navigation and high-contrast modes to ensure accessibility for all Merchant staff (CON-6C177D0102, [CON-CD9BDF7662](../project_glossary.md#con-cd9bdf7662)).

### 4.6. Error Handling & Edge Cases

1. **Double-Spend Detected:** If the platform detects that a token has been used more than once during reconciliation, the transaction is marked as "Failed." The Merchant is notified, and the Beneficiary's credit is restored. The Merchant must then manually refund the Beneficiary (e.g., via cash or alternative payment).
2. **Extended Outage:** If the outage persists for an extended period, the system may rotate the signing key more frequently to limit the window of vulnerability. The product must define the maximum allowable offline window (e.g., 24 hours) after which offline mode is disabled.
3. **Beneficiary Balance Insufficient:** If the Beneficiary's local cached balance is insufficient, the app should prompt them to wait for connectivity or use an alternative payment method. The product must define how "cached balance" is updated and synchronized.

### 4.7. Knowledge Gaps & Assumptions

- **KNOWLEDGE_GAP:** Offline Window Duration: The exact maximum duration for which offline mode can be sustained (e.g., 1 hour, 24 hours) is not yet defined. This impacts the key rotation strategy and the risk of double-spending. Owner: Product Lead / Security Architect. Evidence Needed: Risk assessment of extended offline periods.
- **ASSUMPTION:** Local Balance Caching: It is assumed that the Beneficiary's mobile app caches the user's credit balance locally to allow for offline validation. Owner: Product Lead. Evidence Needed: Confirmation of local storage strategy in the Beneficiary app spec.
- **ASSUMPTION:** Merchant Device Capability: It is assumed that Merchant devices (tablets/POS) have sufficient local storage and processing power to handle cryptographic verification and store pending transactions. Owner: Technical Architect. Evidence Needed: Hardware requirements for Merchant POS integration.

### 4.8. Acceptance Criteria

1. **AC-1:** Merchant can activate "Offline Mode" and generate a valid QR code within 5 seconds of network loss detection.
2. **AC-2:** Beneficiary can present a valid offline token that is accepted by the Merchant's device without real-time connectivity.
3. **AC-3:** The system prevents replay attacks by enforcing time-bound validity and single-use constraints.
4. **AC-4:** Upon reconnection, all pending offline transactions are automatically reconciled with the core platform.
5. **AC-5:** The Merchant Edge Dashboard clearly displays the status of all pending offline transactions and provides clear instructions for handling double-spend failures.

---

## 5. Merchant Payout Error Handling Flow

This section defines the product requirements for the Merchant Payout Error Handling Flow ([JNY-90B07623FB](../project_glossary.md#jny-90b07623fb)). It details how the platform detects, communicates, and resolves failures in the automated financial settlement process for Merchant Partners (ACT-AF904DCFF9). The goal is to ensure financial transparency, maintain trust, and minimize operational friction for restaurant partners.

### 5.1. Payout Lifecycle & Failure Detection

The platform initiates automated payouts to Merchant Partners via Stripe Connect. Failures are detected through two primary channels:

1. **Stripe Webhook Events:** Real-time notifications from Stripe regarding payout status (e.g., `payout.failed`, `payout.pending`).
2. **Internal Ledger Reconciliation:** Daily asynchronous reconciliation between the MealCredit financial ledger and Stripe's settlement reports.

**Failure Categories:**
- **Bank Rejection:** The receiving bank rejects the transfer due to closed accounts, incorrect routing numbers, or compliance holds.
- **Stripe Processing Error:** Internal Stripe errors (e.g., insufficient balance in Stripe Connect account, API timeouts).
- **Compliance Hold:** Payouts frozen due to AML/KYC flags or regulatory reviews.

### 5.2. Merchant Notification & Visibility

When a payout fails, the Merchant must be immediately informed through the Merchant Edge Dashboard (accessible via web and tablet). The dashboard must provide clear, actionable status updates.

**Dashboard Requirements:**
- **Payout Status Indicator:** A prominent visual indicator (e.g., red alert icon) next to the affected payout in the "Recent Payouts" list.
- **Error Message:** A human-readable explanation of the failure (e.g., "Payout failed: Bank account closed. Please update your banking details.").
- **Action Button:** A direct link to the "Update Banking Details" or "Resolve Issue" workflow.
- **Estimated Resolution Time:** If available, an estimate of when the payout will be retried or resolved.

**Accessibility Compliance:**
- All error messages and status indicators must meet WCAG 2.1 AA standards, including high-contrast modes and screen reader compatibility ([CON-68497304B1](../project_glossary.md#con-68497304b1), CON-CD9BDF7662).
- The dashboard must support keyboard-only navigation for all critical actions (CON-6C177D0102, [CON-D0DEFC531A](../project_glossary.md#con-d0defc531a)).

### 5.3. Resolution Workflows

The platform must provide clear pathways for Merchants to resolve common payout errors.

**Scenario A: Bank Account Issues**
- **Trigger:** Stripe returns a `bank_account.failed` event.
- **Merchant Action:** The Merchant is prompted to update their banking details (routing number, account number) via a secure, PCI-DSS Level 1 compliant form (CON-66390130AA, [CON-C4F0E02638](../project_glossary.md#con-c4f0e02638)).
- **System Action:** Upon successful update, the system automatically retries the payout within 24 hours.

**Scenario B: Compliance Holds**
- **Trigger:** Stripe places a hold on the payout due to KYC/AML reviews.
- **Merchant Action:** The Merchant receives a notification to submit additional documentation (e.g., EIN verification, business license) via the dashboard.
- **System Action:** The payout remains in "Pending" status until the documentation is reviewed and approved by the Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) or NGO Operator (ACT-09E028AEB0).

**Scenario C: Technical Errors**
- **Trigger:** Internal system errors or Stripe API timeouts.
- **Merchant Action:** No immediate action required. The system automatically retries the payout up to three times over a 48-hour period.
- **System Action:** If all retries fail, the payout is marked as "Failed" and a support ticket is automatically created for the Platform Administrator to investigate.

### 5.4. Financial Reconciliation & Discrepancies

To ensure financial integrity, the platform must perform daily reconciliation between the internal ledger and Stripe settlement reports.

**Reconciliation Process:**
- **Automated Matching:** The system matches internal transaction records with Stripe settlement files.
- **Discrepancy Detection:** Any mismatches (e.g., missing transactions, amount differences) are flagged for review.
- **Resolution:** Discrepancies are escalated to the Platform Administrator for manual investigation and correction.

**Audit Trail:**
- All payout events, errors, and resolutions must be logged in an append-only cryptographic log in Aurora PostgreSQL for SOC2 Type II evidence ([CON-1762EA5021](../project_glossary.md#con-1762ea5021), [CON-6061FCCA83](../project_glossary.md#con-6061fcca83), CON-BB253DF0A2, [CON-FBBBF07295](../project_glossary.md#con-fbbbf07295)).

### 5.6. Acceptance Criteria

1. **AC-1:** The Merchant Dashboard displays a clear error message and status indicator for any failed payout within 5 minutes of the failure event.
2. **AC-2:** Merchants can update their banking details via a secure, PCI-DSS Level 1 compliant form directly from the error notification.
3. **AC-3:** The system automatically retries failed payouts due to technical errors up to three times over 48 hours.
4. **AC-4:** All payout events and resolutions are logged in an append-only audit trail for SOC2 Type II compliance.
5. **AC-5:** The Merchant Dashboard meets WCAG 2.1 AA accessibility standards, including keyboard navigation and screen reader compatibility.

---

## VP decision

**Decision:** Approved

---

## VP feedback

(No feedback)

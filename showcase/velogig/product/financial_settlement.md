# Financial Settlement and InstantPay Dispute Resolution

## 1. InstantPay Liquidity Pipeline

### 1.1 Overview and User Value
The InstantPay feature allows the Workforce Provider ([ACT-146D8465B0](../project_glossary.md#act-146d8465b0)) to bypass the standard settlement cycle and receive funds immediately upon shift completion. This capability is critical for gig workers who require immediate liquidity to cover living expenses or shift-related costs. The product experience must be seamless, transparent, and trustworthy, clearly communicating fees and fund availability in real-time.

### 1.2 User Stories and Acceptance Criteria

#### Story 1.2.1: Request InstantPay
As a Workforce Provider (ACT-146D8465B0),
I want to request an InstantPay transfer for a completed shift,
So that I can access my earnings immediately rather than waiting for the standard settlement period.

Acceptance Criteria:
1. Eligibility Check: The "Request InstantPay" button is only visible and active if:
The shift status is "Completed" and verified by the Client ([ACT-3ED1615F18](../project_glossary.md#act-3ed1615f18)) or Tenant.
The provider has a valid, verified bank account linked to their profile.
The provider has not exceeded their daily InstantPay transaction limit.
2. Fee Transparency: Upon selecting "Request InstantPay," a modal/screen displays:
The gross amount of the shift.
The InstantPay fee (calculated as a percentage of the gross amount, based on the Tenant's vertical configuration).
The net amount to be deposited.
A clear disclaimer that the fee is non-refundable once the transfer is initiated.
3. Confirmation: The provider must explicitly confirm the transaction by entering their device passcode or biometric authentication.

#### Story 1.2.2: Real-Time Liquidity Check
As a Workforce Provider (ACT-146D8465B0),
I want to receive immediate feedback on whether InstantPay is available for my current balance,
So that I am not misled into thinking funds are available when they are not.

Acceptance Criteria:
1. Liquidity Verification: When the provider initiates the request, the system performs a real-time check against the Financial Settlement Ledger ([SUR-778E10F5D5](../project_glossary.md#sur-778e10f5d5)).
2. Success State: If sufficient liquidity is available in the Tenant's dedicated bank node:
The UI displays a "Processing..." state for no more than 3 seconds.
Upon success, the UI displays a "Funds Sent" confirmation with the estimated arrival time (e.g., "Within 15 minutes").
The shift status updates to "Paid (Instant)".
3. Insufficient Liquidity State: If the Tenant's bank node lacks sufficient funds:
The UI displays a clear error message: "InstantPay is temporarily unavailable due to high demand. Your request has been queued for standard settlement."
The provider is given the option to "Cancel and Request Standard Settlement" or "Retry in 1 Hour."
No fee is charged for the failed attempt.

#### Story 1.2.3: Pending Verification Handling
As a Workforce Provider (ACT-146D8465B0),
I want to be informed if my account is not yet eligible for InstantPay,
So that I can take steps to resolve the issue.

Acceptance Criteria:
1. Unverified Bank Account: If the provider's bank account is not yet verified:
- The "Request InstantPay" button is disabled.
- A tooltip or link directs the provider to the "Link Bank Account" flow, with a note: "InstantPay requires a verified bank account."
2. Pending Credential Verification: If the provider's vertical-specific credentials (e.g., healthcare license, hazmat certification) are under review:
- The "Request InstantPay" button is disabled.
- The UI displays: "InstantPay is available once your [Credential Type] is fully verified."

### 1.4 User Story: Real-Time Fee Breakdown and Routing

As a Commercial Client (ACT-3ED1615F18) managing a multi-site corporate entity,
I want to see a transparent, real-time breakdown of all fees deducted from my settlement payments,
So that I can accurately forecast operational costs and reconcile them against my internal accounting systems without manual calculation.

Acceptance Criteria:
1. Dashboard Visibility: The Commercial Client dashboard must display a "Fee Breakdown" widget for every completed shift settlement. This widget must explicitly list:
The gross shift amount paid by the Client.
The platform service fee (percentage or flat rate).
Any vertical-specific compliance or regulatory surcharges (e.g., Healthcare credential verification fees).
The net amount routed to the Workforce Provider (ACT-146D8465B0).
2. Vertical Configuration Alignment: The fee structure displayed must dynamically reflect the "hot-swappable vertical configuration package" applied to the Client's Tenant. For example, a Healthcare Client must see credential verification fees, while a Law Enforcement Client must see specific per-diem pool management fees.
3. Audit Trail Linkage: Each fee line item must be hyperlinked to the immutable audit trail ([CON-9B0CF18683](../project_glossary.md#con-9b0cf18683)) for that specific transaction, allowing the Client to drill down into the compliance rules that triggered the fee.
4. Routing Transparency: The system must visually confirm that the net amount is routed to the Workforce Provider's linked bank node, and the platform fees are routed to the Financial Settlement Ledger (SUR-778E10F5D5) for tax automation.

### 1.5 User Story: Automated Tax Data Capture During Shift Completion

As a Commercial Client (ACT-3ED1615F18) responsible for tax compliance,
I want to have all necessary tax data (provider classification, earnings, and location) automatically captured and validated at the moment a shift is marked as "Completed" by the Workforce Provider,
So that I can generate accurate 1099-K/1099 forms at year-end without manually collecting or verifying provider information.

Acceptance Criteria:
1. Automatic Data Aggregation: Upon shift completion, the system must automatically aggregate all earnings for a Workforce Provider within the current tax year. This aggregation must include:
Total gross payments.
Any tips or bonuses paid through the platform.
The provider's verified tax identification information (collected during Provider Onboarding).
2. Vertical-Specific Compliance: The system must apply the correct tax data capture rules based on the vertical. For Industrial/Hazmat providers, the system must capture DOT/OSHA clearance status as part of the compliance audit, even if it does not directly impact 1099-K data, to ensure the Implied concern: Ensure CJIS compliance for all Law Enforcement vertical data handling (CON-<timestamp>) is met for relevant verticals.
3. Error Handling for Missing Data: If a Workforce Provider's tax information is incomplete or invalid at the time of shift completion, the system must flag the transaction in the Client's dashboard with a "Tax Data Incomplete" warning. The Client must be able to view this warning and, if permitted by their Tenant configuration, send a notification to the Provider to update their details.
4. Immutable Record: The captured tax data must be stored as an immutable record linked to the Financial Settlement Ledger (SUR-778E10F5D5) to satisfy the Implied concern: Maintain immutable audit trails for all configuration changes, overrides, and state changes (CON-9B0CF18683).

### 1.6 User Story: Consolidated 1099-K/1099 Form Generation and Notification

As a Commercial Client (ACT-3ED1615F18) preparing for tax season,
I want to receive automated notifications and downloadable consolidated 1099-K/1099 forms for all my Workforce Providers,
So that I can fulfill my tax reporting obligations efficiently and avoid penalties for late or inaccurate filings.

Acceptance Criteria:
1. Automated Notification: The system must send a notification to the Commercial Client's designated admin email (and in-app notification) when the platform's tax year concludes and the 1099-K/1099 forms are ready for download. This notification must include a summary of the total number of providers covered and the total value of transactions processed.
2. Consolidated Download: The Client must be able to download a single, consolidated CSV or PDF file containing all 1099-K/1099 data for all providers associated with their Tenant. This file must be structured to be directly importable into common accounting software.
3. Vertical Segregation: If a Client operates across multiple verticals (e.g., both Healthcare and Industrial), the consolidated report must clearly segregate the data by vertical to facilitate accurate reporting under different regulatory frameworks.
4. Data Residency Compliance: The generation and storage of these tax forms must adhere to the Implied concern: Data Residency and Sovereignty: Ensuring compliance with cross-jurisdictional data protection laws (GDPR, CCPA) while supporting m... ([CON-50D510498D](../project_glossary.md#con-50d510498d)). The system must ensure that tax data is stored and processed only in regions compliant with the Client's primary jurisdiction.

### 1.7 Edge Cases and Error Flows

1. Provider Dispute Impacting Tax Data: If a Workforce Provider initiates an InstantPay Dispute ([JNY-2975757D41](../project_glossary.md#jny-2975757d41)) that results in a reversal of funds, the system must automatically adjust the aggregated tax data for that provider. The Client must be notified of the adjustment and provided with a "Revised Tax Summary" for the affected period.
2. Cross-Border Transactions: If a Workforce Provider is located in a different jurisdiction than the Commercial Client, the system must flag the transaction for manual review if the automated tax rules cannot determine the correct withholding requirements. The Client must be able to override the automated classification, with the override logged in the immutable audit trail.
3. Late Provider Onboarding: If a Workforce Provider completes onboarding after the tax year cutoff, the system must exclude them from the current year's 1099-K/1099 generation and flag them for inclusion in the next year's report. The Client must be able to view a list of "Excluded Providers" with the reason for exclusion.

### 1.8 Knowledge Gaps and Assumptions

KNOWLEDGE_GAP: Tax Form Generation Engine: The specific third-party service or internal engine responsible for generating the actual 1099-K/1099 PDF/CSV files has not been defined. The Design phase must select a compliant provider or build an internal generator that adheres to IRS specifications. KNOWLEDGE_GAP: Cross-Border Tax Rules: The specific tax withholding rules for cross-border gig work (e.g., US Client, EU Provider) are not defined. The product team must consult with legal counsel to establish the rules for these edge cases. ASSUMPTION: Vertical Configuration Ownership: It is assumed that the "hot-swappable vertical configuration packages" (mentioned in the project requirement) include the fee structures and tax data capture rules. If these are managed by a separate "Regulations" entity, the integration points between the Financial Settlement Ledger and the Regulations engine must be defined in the Design phase. ASSUMPTION: Client Admin Permissions: It is assumed that the Commercial Client has a designated "Admin" role ([ACT-B91695A020](../project_glossary.md#act-b91695a020)) who is responsible for receiving tax notifications and downloading forms. The specific permission model for this role is defined in the Identity & Access ([CAP-IDENTITY-ACCESS](../project_glossary.md#cap-identity-access)) artifact.

### 1.9 Handoff to Design

The Design team must create the following UI components based on these requirements:
1. Fee Breakdown Widget: A collapsible panel in the settlement detail view that shows the gross, fees, and net amounts.
2. Tax Data Warning Banner: A prominent warning banner in the Client dashboard for any shifts with incomplete provider tax data.
3. Tax Document Download Portal: A dedicated section in the Client settings or reporting dashboard for downloading consolidated 1099-K/1099 forms.
4. Audit Trail Viewer: A drill-down view for the immutable audit trail, accessible from the Fee Breakdown Widget.

All UI components must adhere to the Implied concern: Ensure mobile web modal for client onboarding is accessible via standard WCAG guidelines ([CON-FE093BFFFC](../project_glossary.md#con-fe093bfffc)) and the Implied concern: Provide high-contrast and large-text modes for dispatch coordinators working in varied lighting conditions ([CON-44BE0A2F7F](../project_glossary.md#con-44be0a2f7f)) to ensure accessibility for all users.

---

This section defines the product-level user journey, acceptance criteria, and edge cases for the InstantPay Dispute Resolution workflow (JNY-2975757D41). It governs the interaction between the Workforce Provider (ACT-146D8465B0) and the Commercial Client (ACT-3ED1615F18) when a financial transaction requires reversal or adjustment.

### 2.1 Dispute Initiation (Provider Side)

The Workforce Provider (ACT-146D8465B0) initiates a dispute when they believe the InstantPay settlement is incorrect or the service was not rendered as agreed.

User Story:
As a Workforce Provider, I want to instantly flag a completed shift for dispute so that the funds are temporarily held and the Commercial Client is notified, preventing me from losing recourse if the Client refuses to pay or underpays.

Acceptance Criteria:
1. Trigger: The Provider can initiate a dispute within 24 hours of the InstantPay settlement confirmation.
2. Evidence Submission: The interface must allow the Provider to upload evidence (e.g., photos of the work site, timestamped logs, or text descriptions) to support their claim.
3. Fund Status: Upon submission, the disputed amount is immediately moved from "Available" to "Disputed/Held" status in the Provider's wallet. The Provider cannot withdraw these funds until the dispute is resolved.
4. Notification: The Commercial Client (ACT-3ED1615F18) receives an immediate in-app and email notification detailing the dispute reason and the amount in question.

Edge Cases:
- Expired Window: If the Provider attempts to dispute after the 24-hour window, the system must display a clear error message stating that the transaction is closed and no further disputes can be initiated for that shift.
- Partial Dispute: The Provider must be able to dispute a specific portion of the total payout (e.g., disputing a $50 penalty while accepting the $450 base pay).

### 2.2 Dispute Review and Response (Client Side)

The Commercial Client (ACT-3ED1615F18) has a defined window to review the dispute and either accept the claim or contest it.

User Story:
As a Commercial Client, I want to review the Provider's evidence and either approve the refund or contest the claim so that I can resolve billing discrepancies fairly without manual intervention.

Acceptance Criteria:
1. Review Interface: The Client dashboard must display the Provider's evidence and a clear "Accept Dispute" or "Contest Dispute" button.
2. Response Window: The Client has a defined window to respond. If no action is taken, the system automatically rules in favor of the Provider (default resolution).
3. Contest Action: If the Client contests, they must provide a counter-statement and optional evidence. The dispute status changes to "Under Review" and is escalated to Platform Operator ([ACT-0E3EE366E3](../project_glossary.md#act-0e3ee366e3)) for mediation.
4. Accept Action: If the Client accepts, the disputed funds are immediately reversed from the Client's account and credited back to the Provider's wallet. The InstantPay fee is also refunded to the Client.

Edge Cases:
- Auto-Resolution: If the response window expires, the system must automatically execute the Provider-favorable resolution and log the event in the immutable audit trail.
- Escalation: If contested, the dispute enters a manual mediation queue. The Provider and Client are notified that the Platform Operator (ACT-0E3EE366E3) will review the case.

### 2.3 Resolution and Settlement Adjustment

This step covers the final financial adjustments and the closure of the dispute workflow.

User Story:
As a Platform Operator, I need to ensure that all dispute resolutions result in accurate, auditable financial adjustments to maintain trust and compliance with tax automation requirements.

Acceptance Criteria:
1. Fund Reversal: Upon resolution (whether by Provider acceptance, Client acceptance, or Platform mediation), the system must execute the necessary ledger adjustments to move funds between the Client and Provider accounts.
2. Fee Adjustment: If the dispute is resolved in favor of the Provider, the InstantPay processing fee charged to the Client must be refunded. If resolved in favor of the Client, the fee is retained by the platform.
3. Audit Trail: Every step of the dispute (initiation, evidence upload, response, resolution) must be recorded in the immutable audit trail (CON-9B0CF18683) with timestamps and actor IDs.
4. Notification: Both parties receive a final resolution notification summarizing the outcome and the updated wallet balances.

Edge Cases:
- Insufficient Client Funds: If the Client's account does not have sufficient funds to cover the disputed amount and fee refund, the system must flag the Client's account for collection procedures and notify the Platform Operator.
- Partial Refunds: In cases of partial disputes, the system must accurately calculate the proportional fee refund based on the disputed amount.

### 2.4 Agency Administrator Oversight

The Agency Administrator (ACT-B91695A020) requires visibility into dispute trends to manage agency risk and provider relations.

User Story:
As an Agency Administrator, I want to view a summary of all disputes initiated by providers under my agency's management, so that I can identify systemic issues with client billing or provider conduct.

Acceptance Criteria:
1. Dispute Dashboard: The Agency Administrator dashboard must display a list of all active and resolved disputes for the agency's providers.
2. Filtering: The Administrator must be able to filter disputes by status (Open, Resolved, Escalated), date range, and involved provider.
3. Export Capability: The Administrator must be able to export dispute data to CSV for internal review and compliance auditing.
4. Notification: The Administrator must be notified immediately when a dispute is escalated to the Platform Operator (ACT-0E3EE366E3) for mediation.

### 2.5 Follow-Up Questions

1. Dispute Fee: Should the Platform charge a small fee for initiating a dispute to prevent frivolous claims, and if so, who bears this fee (Provider or Client)?
2. Mediation SLA: What is the maximum allowable time for the Platform Operator to resolve a mediated dispute before it escalates to external arbitration?
3. Repeat Offenders: Are there specific penalties or account restrictions for Clients who frequently contest valid disputes?

## 3. Financial Account Closure and Data Export

This section defines the product requirements for the Account Closure and Data Export ([JNY-B2BD1D1897](../project_glossary.md#jny-b2bd1d1897)) journey, focusing on the financial aspects of terminating a VeloGig account. It ensures that all financial obligations are settled, pending transactions are resolved, and users retain access to their financial history for tax and compliance purposes.

#### 4.1.1. Workforce Provider (ACT-146D8465B0) Account Closure

Story $IP.1: Request Account Closure and Final Settlement
As a Workforce Provider (ACT-146D8465B0), I want to initiate the account closure process so that I can permanently leave the platform while ensuring I receive all my outstanding earnings.

Acceptance Criteria:
1. The user can initiate account closure from the account settings menu.
2. Upon initiation, the system displays a summary of the user's current financial status:
   - Available balance (ready for InstantPay or standard withdrawal).
   - Pending balance (from completed shifts awaiting settlement).
   - Any outstanding fees or charges.
3. The system clearly states that account closure will freeze all incoming shift assignments and client requests.
4. The user must confirm the closure action via a secondary confirmation dialog.

Story $IP.2: Resolve Pending InstantPay Requests
As a Workforce Provider (ACT-146D8465B0), I want to know how pending InstantPay requests are handled during account closure so that I am not surprised by delayed payments.

Acceptance Criteria:
1. If the user has any pending InstantPay requests at the time of closure, the system displays a warning.
2. The system provides two options:
   - Option A: Cancel all pending InstantPay requests and revert them to standard settlement timelines (if applicable).
   - Option B: Allow pending InstantPay requests to complete, but note that no new funds will be added to the balance.
3. If the user chooses Option A, the system cancels the requests and updates the balance accordingly.
4. If the user chooses Option B, the system processes the requests and then proceeds with closure once all pending transactions are settled.

Story $IP.3: Export Financial Transaction History
As a Workforce Provider (ACT-146D8465B0), I want to export my complete financial transaction history before closing my account so that I can maintain records for tax purposes.

Acceptance Criteria:
1. Before finalizing account closure, the system prompts the user to export their financial data.
2. The export includes:
   - All completed shift payments.
   - All InstantPay transactions (successful and failed).
   - All fee deductions (platform fees, payment processing fees).
   - All tax-related documents (e.g., 1099-K forms, if applicable).
3. The export is provided in a standard, machine-readable format (e.g., CSV or PDF).
4. The user can download the export file before proceeding with closure.

#### 4.1.2. Commercial Client (ACT-3ED1615F18) Account Closure

Story $IP1.1: Settle Outstanding Invoices
As a Commercial Client (ACT-3ED1615F18), I want to settle all outstanding invoices before closing my account so that I avoid any legal or financial penalties.

Acceptance Criteria:
1. The system checks for any outstanding invoices or unpaid fees associated with the client account.
2. If outstanding balances exist, the system blocks account closure until all invoices are paid.
3. The system provides a direct link to the payment portal to settle outstanding balances.
4. Once all balances are cleared, the system allows the user to proceed with closure.

Story $IP1.2: Export Client Financial Records
As a Commercial Client (ACT-3ED1615F18), I want to export my financial records, including invoices and payment history, before closing my account.

Acceptance Criteria:
1. The system provides a comprehensive export of all financial data associated with the client account.
2. The export includes:
   - All invoices issued.
   - All payment receipts.
   - All fee breakdowns.
   - All tax-related documents.
3. The export is provided in a standard, machine-readable format (e.g., CSV or PDF).
4. The user can download the export file before proceeding with closure.

#### 4.2.1. Insufficient Funds for Final Settlement
Scenario: A Workforce Provider (ACT-146D8465B0) has a negative balance due to overpayments or fees.
Behavior: The system blocks account closure and requires the user to repay the negative balance before proceeding.
Error Message: "Account closure is blocked due to an outstanding balance of $[amount]. Please repay this amount to proceed."

#### 4.2.2. Pending Disputes
Scenario: A Workforce Provider (ACT-146D8465B0) or Commercial Client (ACT-3ED1615F18) has an active dispute resolution case.
Behavior: The system blocks account closure until the dispute is resolved.
Error Message: "Account closure is blocked due to an active dispute. Please resolve the dispute before proceeding."

#### 4.2.3. Data Export Failure
Scenario: The system fails to generate the financial export file due to a technical error.
Behavior: The system displays an error message and allows the user to retry the export. If the error persists, the user is advised to contact support.
Error Message: "Failed to generate financial export. Please try again or contact support."

### 3.1 Cross-References

JNY-B2BD1D1897: Account Closure and Data Export (User Journey)
ACT-146D8465B0: Workforce Provider (Actor Role)
ACT-3ED1615F18: Commercial Client (Actor Role)
CON-9B0CF18683: Maintain immutable audit trails for all configuration changes, overrides, and state changes.
[CON-A658A99280](../project_glossary.md#con-a658a99280): Automate generation of consolidated 1099-K/1099 forms for tax compliance.
SUR-778E10F5D5: Financial Settlement Ledger (Architectural Surface)

## 4. Financial Governance and Audit Trail Specifications

This section defines the product-level requirements for maintaining immutable audit trails for all configuration changes, overrides, and state changes related to financial transactions. It ensures that all financial actions are traceable and auditable as per the Implied concern: Maintain immutable audit trails for all configuration changes, overrides, and state changes. (CON-9B0CF18683).

### 4.1 Immutable Audit Trail for Financial State Changes

User Story: As a Platform Operator (ACT-0E3EE366E3) or Agency Administrator (ACT-B91695A020), I need to view a tamper-proof, chronological log of all financial state changes (e.g., InstantPay requests, fee adjustments, dispute resolutions) so that I can ensure regulatory compliance and investigate any discrepancies.

Acceptance Criteria:
1. System shall record an immutable audit entry for every financial state change, including:
   - Timestamp (UTC)
   - Actor ID (e.g., Workforce Provider, Commercial Client, Platform Operator)
   - Action type (e.g., INSTANT_PAY_REQUEST, FEE_ADJUSTMENT, DISPUTE_RESOLVED)
   - Pre-change state (e.g., PENDING)
   - Post-change state (e.g., COMPLETED)
   - Transaction ID (linked to the Financial Settlement Ledger (SUR-778E10F5D5))
2. System shall prevent any modification or deletion of audit entries once created.
3. System shall provide a read-only view of the audit trail to Platform Operators (ACT-0E3EE366E3) and Agency Administrators (ACT-B91695A020).
4. System shall allow filtering of the audit trail by date range, actor, and action type.

Edge Cases:
- If a system error occurs during a financial transaction, the system must log the error state and the attempted action, ensuring the audit trail remains consistent.

### 4.2 Notification Mechanisms for Significant Financial Events

User Story: As a Platform Operator (ACT-0E3EE366E3), I need to receive immediate notifications for significant financial events (e.g., large InstantPay requests, dispute escalations) so that I can take proactive measures to mitigate risk.

Acceptance Criteria:
1. System shall send real-time notifications to Platform Operators (ACT-0E3EE366E3) for:
   - InstantPay requests exceeding a defined threshold (KNOWLEDGE_GAP: threshold_amount - Platform Operator must establish this value based on risk tolerance).
   - Dispute escalations that cannot be resolved automatically.
   - Failed financial transactions due to compliance checks.
2. System shall provide a dashboard within the Platform Operator (ACT-0E3EE366E3) interface to view all recent notifications.
3. System shall allow Platform Operators (ACT-0E3EE366E3) to configure notification preferences (e.g., email, in-app).

Edge Cases:
- If the notification system is temporarily unavailable, the system must queue notifications and deliver them once the system is restored, ensuring no significant event is missed.

### 4.3 Compliance Reporting Features

User Story: As a Platform Operator (ACT-0E3EE366E3) or Agency Administrator (ACT-B91695A020), I need to generate compliance reports (e.g., 1099-K/1099 forms, transaction summaries) so that I can meet tax and regulatory requirements.

Acceptance Criteria:
1. System shall generate consolidated 1099-K/1099 forms for tax compliance as per the Implied concern: Automate generation of consolidated 1099-K/1099 forms for tax compliance. (CON-A658A99280).
2. System shall allow Agency Administrators (ACT-B91695A020) to export transaction summaries in a standard format (e.g., CSV, PDF) for internal auditing.
3. System shall ensure that all compliance reports are generated from the immutable audit trail to ensure data integrity.
4. System shall provide a preview of the compliance report before final generation to allow for verification.

Edge Cases:
- If a transaction spans multiple tax years, the system must correctly allocate the transaction to the appropriate tax year in the compliance report.

### 4.4 Summary of Deliverables

Immutable audit trail for financial state changes. Real-time notification mechanisms for significant financial events. Compliance reporting features for tax and regulatory requirements. Clear definition of knowledge gaps and assumptions for further resolution.
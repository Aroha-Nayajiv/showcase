# Donor Contribution & Matching Journey

### 1.1 Persona: The Impact-Driven Funder

**Motivation:** Wants to contribute to food security without the friction of large lump-sum donations or the stigma of traditional charity.
**Pain Points:** Distrust of opaque donation tracking; desire for "set and forget" automation; concern about data privacy.
**Key Need:** Immediate visibility into how their round-ups translate to meals, without compromising beneficiary anonymity.

### 1.2 User Story: Secure Banking Integration

As a new Funder,
I want to securely link my primary checking or credit card using Plaid,
So that I can enable automated micro-donation round-ups without exposing raw financial data to MealCredit.

**Acceptance Criteria:**
1. **Entry Point:** Upon first login, the Funder is presented with a "Start Funding" CTA on the dashboard.
2. **Plaid Integration:** Clicking the CTA triggers the Plaid Link UI (embedded in the Expo v51 React Native app).
3. **Bank Selection:** The Funder selects their financial institution from the Plaid directory.
4. **Authentication:** The Funder authenticates directly with their bank via Plaid's secure modal (no credentials stored by MealCredit).
5. **Verification:** Upon successful link, the system displays the verified bank name and last 4 digits of the linked account.
6. **Stripe Connection:** The system automatically provisions a Stripe Custom Connected Account for the Funder, linking the verified bank account for settlement and round-up sourcing.
7. **PCI-DSS Compliance:** The UI explicitly states that MealCredit never sees raw card numbers or bank passwords, adhering to PCI-DSS Level 1 standards.

**Edge Cases & Error Flows:**
* **Bank Not Supported:** If the user's bank is not in Plaid's network, display a clear error message: "We currently do not support your financial institution. Please use a different card or bank."
* **Link Timeout:** If the Plaid session times out, allow the user to restart the linking process without losing their onboarding progress.
* **Insufficient Funds:** If the linked account has insufficient funds for a round-up, the system should not fail the transaction but should notify the Funder via push notification to update their funding source.

### 1.3 User Story: Micro-Donation Round-Up Configuration

As a Funder,
I want to configure my donation rules (global pool vs. directed impact) and set a round-up threshold,
So that I can control how my everyday spending contributes to the culinary credit pool.

1. **Rule Selection:** After linking a bank, the Funder is prompted to choose a donation strategy:
   * **Global Pool:** All round-ups go to the central regional pool (SF/NYC/Chicago) to be distributed by NGOs based on need.
   * **Directed Impact:** Round-ups are assigned to specific criteria (e.g., "Healthy Grocery Partners," "Specific Zip Codes," or "All Restaurants").
2. **Round-Up Threshold:** The Funder sets a minimum transaction amount to trigger a round-up (e.g., "Round up purchases over $5.00").
   * `ASSUMPTION:` Default threshold is $5.00. Owner: Product Manager. Evidence needed: Market research on donor friction points.
3. **Round-Up Amount:** The Funder chooses the round-up granularity:
   * **100% Round-Up:** Round up to the nearest dollar.
   * **Custom Amount:** Set a fixed daily/weekly contribution cap (e.g., "$2.00 per week").
4. **Preview Impact:** The UI displays a simulated impact statement: "Based on your average spend, this could provide ~X meals per month."
5. **Confirmation:** The Funder confirms the settings. The system saves the configuration to the Aurora ledger and activates the Stripe webhook listener for round-up events.

**Edge Cases & Error Flows:**
* **Directed Impact Unavailable:** If the Funder selects "Directed Impact" but no specific criteria are available in their region, default to "Global Pool" with a clear explanation: "Directed options are not yet available in your area. Your funds will support the regional pool."
* **Cap Exceeded:** If the Funder sets a weekly cap and exceeds it, subsequent round-ups are paused until the next billing cycle. A notification informs the user of the pause.

### 1.6 Knowledge Gaps & Assumptions

* `KNOWLEDGE_GAP:` Round-Up Threshold Default: The default threshold for triggering a round-up (e.g., $5.00) is not specified in the project requirement. Owner: Product Manager. Evidence needed: User research on donation friction.
* `KNOWLEDGE_GAP:` Directed Impact Criteria: The specific criteria for "Directed Impact" (e.g., specific MCC codes, zip code granularity) are not fully defined. Owner: Product Manager. Evidence needed: NGO partner requirements.
* `ASSUMPTION:` Stripe Webhook Latency: It is assumed that Stripe webhooks for round-up events will be processed within 150ms, as per the system blueprint. Owner: Engineering. Evidence needed: Stripe API performance benchmarks.
* `ASSUMPTION:` Plaid Link UI Customization: It is assumed that the Plaid Link UI can be customized to match MealCredit's branding within the Expo v51 React Native app. Owner: Design. Evidence needed: Plaid API documentation.

---

### 2.1 User Persona & Context
* **Actor:** Funder (Donor)
* **Context:** Post-banking integration (Plaid/Stripe) and pre-first-round-up. The Funder has linked a credit card and is now configuring how the "round-up" logic applies to their spending.
* **Goal:** Establish a recurring donation rule that aligns with their values (e.g., "Support my local community" vs. "Support global hunger relief") without requiring manual transaction entry.

### 2.2 Core Configuration Modes
The interface presents two mutually exclusive primary modes for fund allocation. The Funder must select one as the default behavior for their round-up contributions.

#### Mode A: Global Impact Pool (Default)
* **Definition:** Funds are deposited into the central regional liquidity pool (e.g., "SF Bay Area Pool") and are available for redemption by any eligible Beneficiary within that metro footprint, managed by local NGOs.
* **User Experience:**
  * **Label:** "Support Local Community"
  * **Description:** "Your round-ups go into the general fund for [Metro Area], helping anyone in need nearby."
  * **Visual Cue:** A map pin icon centered on the user's current metro footprint (SF, NYC, or Chicago).
  * **Impact Metric:** Displays aggregate "Meals Provided" for the region to show collective impact.

#### Mode B: Directed Impact Flows
* **Definition:** Funds are restricted to specific geographic regions (zip codes) or merchant property types (e.g., "Healthy Grocery Partners"). This requires the Funder to make explicit selections.
* **User Experience:**
  * **Label:** "Direct My Impact"
  * **Description:** "Choose exactly where your donations go."
  * **Configuration Options:**
    1. **Geographic Targeting:** Funder selects specific zip codes or neighborhoods. Constraint: Must be within the active metro footprint (SF, NYC, Chicago).
    2. **Merchant Type Targeting:** Funder selects specific Merchant Category Codes (MCC) or property types (e.g., "Grocery Stores," "Cafes," "Family Restaurants").
  * **Visual Cue:** A checklist interface with toggle switches for categories or a map with selectable zones.

### 2.3 Round-Up Configuration & Logic
Regardless of the allocation mode, the Funder must configure the financial mechanics of the round-up.

* **Trigger Source:** Linked Credit Card (via Plaid/Stripe).
* **Rounding Logic:**
  * **Standard Round-Up:** Round up each transaction to the nearest $1.00.
  * **Custom Amount:** Funder sets a fixed daily/weekly contribution amount (e.g., "$2.00 per week").
  * **Multiplier:** Funder can choose to multiply the round-up (e.g., "2x the difference").
* **Frequency:**
  * **Real-Time:** Deducted immediately after each transaction.
  * **Daily Batch:** Aggregated and deducted once per day.
  * **Weekly Batch:** Aggregated and deducted once per week.
* **UI Element:** A slider or input field for "Weekly Contribution Cap" to prevent budget overruns.

### 2.6 Acceptance Criteria
1. Given a Funder has linked a bank account, When they access the Donation Rule Configuration screen, Then they must see two distinct modes: "Global Impact Pool" and "Directed Impact Flows."
2. Given a Funder selects "Directed Impact Flows," When they choose a geographic target, Then the system must validate that the target is within the active metro footprint (SF, NYC, Chicago).
3. Given a Funder configures a round-up, When they review the summary, Then they must see a projected impact metric (e.g., "X meals per month") and a privacy assurance statement.
4. Given a Funder confirms the rule, When the first transaction occurs, Then the system must apply the round-up logic and deposit funds into the selected pool/flow.

### 2.8 Follow-Up Questions
1. **Question:** Should Funders be able to split their round-ups between Global and Directed flows (e.g., 50/50)?
   * **Why Critical:** This adds significant UI complexity but increases donor engagement.
   * **Answerable:** No. **Blocking:** Yes.
2. **Question:** What is the minimum threshold for "Directed Impact" to be viable (e.g., must have at least 10 active partners in the zip code)?
   * **Why Critical:** Prevents Funder frustration from selecting empty zones.
   * **Answerable:** No. **Blocking:** Yes.

---

## 3. Real-Time Transparency Engine Experience

### 3.2 User Stories

#### US-3.1: Immutable Impact Receipt Generation
As a Funder,
I want to receive an immutable, timestamped receipt immediately after my micro-donation is redeemed by a Beneficiary,
So that I can verify the impact of my contribution without compromising the Beneficiary's privacy.

1. **Trigger:** The system generates a receipt event upon successful POS clearing of a virtual card token.
2. **Latency:** The receipt is pushed to the Funder's mobile app (Expo/React Native) via Server-Sent Events (SSE) or push notification within 120 seconds of the POS clearing event.
3. **Content:** The receipt includes:
   * Transaction ID (hashed/immutable reference).
   * Timestamp of redemption.
   * Amount redeemed (e.g., "$12.50 for a meal").
   * Impact summary (e.g., "1 meal provided").
   * NO Beneficiary PII, location details, or NGO identifiers.
4. **Immutability:** The receipt is cryptographically signed and stored in the append-only ledger (Aurora Postgres) to prevent tampering.

#### US-3.2: Privacy-Preserving Receipt Display
As a Funder,
I want to view my impact receipts in a clean, gift-card-style interface,
So that the experience feels dignified and familiar, avoiding any stigma associated with charity.

1. **UI Design:** Receipts are displayed in a feed similar to a transaction history in a banking app.
2. **Anonymization:** No names, photos, or specific locations of Beneficiaries are shown.
3. **Visual Consistency:** The receipt design aligns with the MealCredit brand, using neutral, positive imagery (e.g., a meal icon, not a person).

#### US-3.3: Receipt Verification and Audit
As a Funder,
I want to verify the authenticity of my receipts,
So that I can trust the platform's integrity and use them for personal impact reporting.

1. **Verification:** Each receipt contains a unique, verifiable hash.
2. **Export:** Funders can export their receipt history (anonymized) for personal records or tax purposes.

### 3.3 Edge Cases and Error Flows

#### 3.3.1. Receipt Delivery Failure
**Scenario:** The SSE connection drops or the push notification fails.
**System Response:** The system retries delivery up to 3 times with exponential backoff. If all retries fail, the receipt is queued in the Funder's "Pending Impact" section until successful delivery.
**User Experience:** The Funder sees a "Receipt Pending" status with a "Retry" button.

#### 3.3.2. Ledger Discrepancy
**Scenario:** The Funder disputes a receipt, claiming it was not redeemed.
**System Response:** The system provides access to the immutable ledger entry for that transaction ID, showing the POS clearing timestamp and token hash.
**User Experience:** The Funder can view the "Proof of Impact" which includes the hashed transaction details but no PII.

#### 3.3.3. High Latency
**Scenario:** The 120-second latency threshold is exceeded due to high system load.
**System Response:** The system displays a "High Demand" message to the Funder, explaining that impact receipts may be delayed.
**User Experience:** The Funder is informed of the delay and can check back later.

### 4.2 User Story: Impact History

As a Funder,
I want to view a detailed history of my contributions and their corresponding redemptions,
So that I can track my giving over time and export data for tax purposes.

1. **History View:** A chronological list of all round-up transactions and their associated impact receipts.
2. **Filtering:** Funders can filter by date range, transaction type (round-up vs. direct donation), or impact status (pending vs. cleared).
3. **Export:** A "Download Report" button generates a CSV/PDF of the filtered history, compliant with tax reporting standards.
4. **Privacy:** The exported report contains only transaction IDs, amounts, and timestamps; no Beneficiary PII is included.

### 4.5 The Real-Time Transparency Receipt

Upon the successful redemption of a MealCredit by a Beneficiary at a Merchant Partner, the Funder receives an immutable transparency receipt. This receipt is the primary mechanism for building trust and demonstrating the efficacy of the micro-donation model.

**User Story:**
As a Funder, I want to receive a notification immediately after my donation is used, so that I can see the direct result of my contribution without compromising the privacy of the person I helped.

**Acceptance Criteria:**
1. **Latency Constraint:** The transparency receipt must be generated and delivered to the Funder within 120 seconds of the Beneficiary's successful redemption at the POS terminal. This aligns with the system's real-time transparency engine requirements.
2. **Anonymization Enforcement:** The receipt must never contain any PII of the Beneficiary. No names, photos, demographic data, or specific location details (beyond the general city/region, e.g., "San Francisco") are permitted.
3. **Immutable Ledger:** The receipt must reference a unique transaction ID that is cryptographically signed and stored in the append-only ledger, ensuring it cannot be altered or deleted.
4. **Content of Receipt:** The receipt must include:
   - A visual confirmation of the meal provided (e.g., "You just funded a meal at [Restaurant Name]").
   - The amount of the micro-donation applied.
   - The timestamp of the redemption.
   - A link to the immutable transaction record on the ledger.

**Edge Cases:**
- **Receipt Delay:** If the receipt is not received within 120 seconds, the app must display a "Processing Impact" status with an estimated time, and automatically push the notification once the ledger confirms the transaction.
- **Duplicate Notifications:** The system must ensure that only one receipt is generated per redemption event, even if multiple donors contributed to the same credit pool.

### 4.6 Impact Aggregation and Visualization

Funders need to see how their individual micro-donations aggregate into larger social impact. This section defines the "Impact Dashboard" and "Impact Feed" features.

**User Story:**
As a Funder, I want to see a dashboard that aggregates my contributions and shows the total number of meals funded, so that I can understand the cumulative impact of my participation in the MealCredit platform.

1. **Impact Dashboard:** The Funder's profile must include a dedicated "Impact" tab that displays:
   - **Total Meals Funded:** A running count of meals funded by the user's donations.
   - **Total Amount Donated:** The cumulative sum of all micro-donations and round-ups.
   - **Impact Map:** A visual map (SF, NYC, Chicago) showing the geographic distribution of the user's funded meals, using aggregated data points to prevent re-identification.
2. **Impact Feed:** A chronological feed of the user's recent impact events, similar to a social media feed, showing:
   - "You funded a meal at [Restaurant Name] in [City] on [Date]."
   - "Your round-up of $0.50 helped fund a meal at [Restaurant Name]."
3. **Aggregation Logic:** Individual transactions must be aggregated by day or week if the volume is high, to prevent clutter and maintain privacy. The aggregation must be transparent, allowing the user to drill down into individual transactions if desired.

**Edge Cases:**
- **Zero Impact:** If a user has not funded any meals recently, the dashboard must display a "Your impact is growing" message with a call-to-action to configure their round-up settings.
- **Directed Impact Visibility:** If a user has configured "Directed Impact Flows" (e.g., to a specific zip code), the impact map must highlight those specific areas to show the targeted nature of their contribution.

### 4.7 Merchant and NGO Impact Stories

To provide context and emotional connection, the platform will share anonymized stories of impact from Merchant Partners and NGO Facilitators.

**User Story:**
As a Funder, I want to read anonymized stories from Merchants and NGOs about how MealCredits are helping the community, so that I can feel more connected to the mission of decoupling food assistance from social stigma.

1. **Story Feed:** The app must include a "Stories" section that features:
   - **Merchant Spotlights:** Anonymized quotes or short videos from Restaurant Partners about how MealCredits have increased their foot traffic or supported their community.
   - **NGO Insights:** Anonymized reports from NGO Facilitators on the general trends of redemption (e.g., "This month, 500 meals were funded in the Mission District").
2. **Anonymization:** All stories must be strictly anonymized. No Beneficiary names, photos, or specific identifying details are allowed. Merchant names may be used with their consent, but Beneficiary data must be completely stripped.
3. **Frequency:** New stories must be added weekly to keep the feed fresh and engaging.

**Edge Cases:**
- **Content Moderation:** All stories must be reviewed by the Operator team to ensure they comply with the absolute anonymization policy before being published.
- **Regional Relevance:** Stories should be prioritized based on the Funder's location or the regions they have directed their impact to, if applicable.

### 4.8 Success Metrics

- **Receipt Delivery Rate:** Percentage of redemptions that result in a receipt delivered within 120 seconds.
- **Funder Engagement Rate:** Percentage of Funders who view the Impact Dashboard at least once per week.
- **Impact Story Click-Through Rate:** Percentage of Funders who click on impact stories from the feed.

This section provides a comprehensive product specification for the Impact Visualization and Feedback Loop, ensuring that Funders receive timely, anonymized, and meaningful feedback on their contributions, thereby reinforcing trust and encouraging continued participation in the MealCredit platform.

---

## 5. End-to-End Funder Journey Synthesis

This section synthesizes the complete Funder (Donor) lifecycle within the MealCredit platform, ensuring seamless transitions between banking setup, donation configuration, and impact feedback. The journey is designed to maximize trust through transparency while maintaining absolute anonymity for beneficiaries.

### 5.5 Sibling Dependencies

- **Beneficiary Discovery & Redemption Journey:** This artifact defers to the Beneficiary Journey for the exact mechanics of token generation and POS clearing. The Funder journey only requires the outcome (redemption) to trigger the receipt.
- **Restaurant Partner Onboarding & POS Integration:** This artifact defers to the Restaurant Partner Journey for the POS integration details. The Funder journey only requires the validation of the token at the POS.
- **Operator Monitoring & Management Dashboard:** This artifact defers to the Operator Dashboard for the alerting mechanisms for credit pool utilization and webhook latency.
- **Identity, Access & Offline Capability Foundation:** This artifact defers to the Identity Foundation for the specific RBAC and offline token storage mechanisms. The Funder journey assumes a secure, authenticated session.

### 5.6 Quality & Compliance Notes

- **Security:** All beneficiary data must be anonymized before any matching or receipt generation. Financial data must adhere to PCI-DSS Level 1 standards.
- **Testability:** The Funder journey must be traceable to grounded project truth, with explicit knowledge gaps and reversible assumptions. Each user story has clear, testable acceptance criteria.
- **Anonymization:** The system must ensure that no PII crosses into production logs or DB tables. The Funder receipt must never contain beneficiary identifiers.

This synthesis ensures that the Funder journey is not just a series of isolated steps, but a cohesive, trust-building experience that aligns with MealCredit's mission of decoupling food assistance from social stigma.
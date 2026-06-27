# Donor Onboarding & Funding Activation

## 1. Donor Onboarding & Funding Activation

This section defines the product requirements for the Donor ([ACT-80C62C7814](../project_glossary.md#act-80c62c7814)) journey ([JNY-62D850E94B](../project_glossary.md#jny-62d850e94b)), covering account creation, secure payment integration, and initial funding configuration.

### 1.1. Account Creation & Identity Verification

Goal: Enable the Donor to create a secure account while establishing the necessary identity foundation for financial compliance.

User Story:
As a Donor, I want to create an account using my email and a secure password, so that I can access the platform and begin funding meals for beneficiaries.

Acceptance Criteria:
1. Registration Flow: The system shall accept an email address and a strong password (min 12 chars, mixed case, number, symbol) to create a provisional account.
2. Email Verification: The system shall send a time-bound verification link to the provided email. The account remains in a "Pending Verification" state until the link is clicked.
3. Data Residency ([CON-30EA97016B](../project_glossary.md#con-30ea97016b)): The system shall store the Donor's PII (name, email, address) in a data partition that respects the jurisdictional compliance requirements for SF, NYC, and Chicago. No PII shall be stored in regions outside the US.
4. Security ([CON-81FB01F06B](../project_glossary.md#con-81fb01f06b)): The system shall implement SOC2 Type II structural planning by logging all account creation and modification events to an immutable audit log.

Edge Cases & Error States:
- Duplicate Email: If the email is already registered, the system shall prompt the user to log in or recover their account, rather than revealing the existence of the account to prevent email enumeration.
- Weak Password: The system shall provide real-time feedback on password strength before submission.

### 1.2. Secure Payment Method Integration

Goal: Enable the Donor to link a funding source securely, ensuring zero raw card data touches MealCredit servers.

User Story:
As a Donor, I want to securely link my credit card or bank account via Plaid/Stripe, so that I can fund my donation pool without exposing my sensitive financial data.

Acceptance Criteria:
1. PCI-DSS Level 1 Compliance ([CON-66390130AA](../project_glossary.md#con-66390130aa)): The system shall use Stripe Elements and Plaid Link for all payment method inputs. No raw card numbers, CVVs, or bank account details shall be transmitted to or stored by MealCredit servers.
2. Payment Method Linking: The system shall present a secure modal (via Stripe/Plaid SDK) for the Donor to enter their payment details. Upon successful tokenization, the system shall store the resulting payment method ID (e.g., pm_123...) linked to the Donor's profile.
3. Multi-Jurisdictional Support ([CON-5BFA25E8F9](../project_glossary.md#con-5bfa25e8f9)): The system shall support payment methods issued in the US, Canada, and other supported jurisdictions, handling currency conversion and KYC requirements as dictated by the payment provider.
4. Offline Token Storage ([CON-34312C6DC9](../project_glossary.md#con-34312c6dc9)): The system shall securely store any necessary offline tokens (e.g., for session management) using the device's SecureStore, ensuring they are not accessible to other apps or the OS.

Edge Cases & Error States:
- Declined Card: If the payment provider declines the card, the system shall display a generic error message ("We were unable to process your payment method. Please try a different card or contact your bank.") to avoid revealing specific decline reasons.
- Plaid/Stripe API Failure: If the payment provider API is unavailable, the system shall display a "Service Temporarily Unavailable" message and allow the user to retry later.

### 1.3. Initial Funding & Donation Configuration

Goal: Enable the Donor to configure their funding preferences and make their first donation.

User Story:
As a Donor, I want to configure my donation preferences (e.g., round-up, directed impact, or open pool) and make an initial funding deposit, so that I can start supporting beneficiaries immediately.

Acceptance Criteria:
1. Funding Activation: The system shall allow the Donor to make an initial one-time deposit or set up a recurring donation schedule. The account transitions to "Active Funding" status upon successful completion of the first transaction.
2. Donation Configuration ([CON-2D70EDCDEE](../project_glossary.md#con-2d70edcdee)): The system shall provide multi-modal interaction paths (e.g., voice commands, tap-to-donate, scan-to-donate) for configuring donation round-up settings. The default configuration shall be an "Open Pool" donation, where funds are distributed to any eligible beneficiary.
3. Directed Impact (Optional): The system shall allow the Donor to optionally direct their funds to a specific NGO or cause, if such options are enabled by the NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)).
4. Impact Receipts: Upon successful funding, the system shall generate an immutable impact receipt, confirming the donation amount and the date, which can be shared or downloaded by the Donor.

Edge Cases & Error States:
- Insufficient Funds: If the Donor's linked payment method fails during the initial funding attempt, the system shall prompt them to add a new payment method.
- Configuration Save Failure: If the system fails to save the Donor's donation preferences, it shall retain the default "Open Pool" configuration and notify the user of the sync issue.

### 1.4. Sibling Dependencies

Beneficiary Eligibility & Voucher Redemption: This artifact defers to the Beneficiary Eligibility & Voucher Redemption artifact for the specific rules governing which beneficiaries are eligible to receive funds from the Donor's pool.
Merchant Onboarding & POS Integration: This artifact defers to the Merchant Onboarding & POS Integration artifact for the details of how merchants accept and clear the culinary credits funded by the Donor.
NGO Governance & Beneficiary Offboarding: This artifact defers to the NGO Governance & Beneficiary Offboarding artifact for the rules governing how NGOs manage beneficiary eligibility and offboarding, which may impact Donor-directed donations.
Dispute Resolution & Fraud Investigation: This artifact defers to the Dispute Resolution & Fraud Investigation artifact for the procedures handling fraudulent donations or disputes related to Donor funding.

---

## 2. Secure Payment Method Integration

This section defines the product requirements for linking primary payment methods via Plaid/Stripe, ensuring the experience aligns with the Payment Processing Surface ([SUR-5B18C8719F](../project_glossary.md#sur-5b18c8719f)) and satisfies the Implied concern: Enforce PCI-DSS Level 1 compliance by ensuring zero raw card data touches MealCredit servers, relying entirely on Stripe Elements/Plaid (CON-66390130AA).

### 2.1. User Stories & Acceptance Criteria

#### US-2.1: Link Primary Credit/Debit Card via Stripe Elements

As a Donor (ACT-80C62C7814),
I want to securely enter my credit or debit card details using a familiar, branded interface,
So that I can fund my MealCredit wallet without worrying about data security or PCI compliance.

Acceptance Criteria:
1. Secure Interface: The card entry form must be rendered entirely within a Stripe-hosted iframe (Stripe Elements). The MealCredit UI must not contain native `<input>` fields for card number, expiry, or CVC.
2. PCI-DSS Level 1 Alignment: Zero raw card data (PAN, CVV) may be present in the MealCredit DOM, network requests, or local storage. The only data transmitted to MealCredit servers must be a secure, ephemeral payment method token.
3. Multi-modal Interaction: The interface must support standard touch input. For accessibility, it must also support keyboard navigation and screen readers, adhering to WCAG 2.1 AA standards ([CON-68497304B1](../project_glossary.md#con-68497304b1), [CON-CD9BDF7662](../project_glossary.md#con-cd9bdf7662)).
4. Real-time Validation: The Stripe Element must provide real-time visual feedback for invalid card formats, expired cards, or declined pre-authorizations.
5. Success State: Upon successful tokenization and pre-authorization (e.g., $0.01 hold), the UI must display a success message confirming the card is linked and ready for funding.

#### US-2.2: Link Bank Account via Plaid Link for ACH

As a Donor (ACT-80C62C7814),
I want to securely link my bank account using Plaid Link,
So that I can set up recurring donations or larger one-time transfers with lower processing fees and higher trust.

Acceptance Criteria:
1. Secure Banking API: The bank linking process must be initiated and completed entirely within the Plaid Link modal. MealCredit must never handle raw banking credentials (username/password).
2. Identity Verification: Plaid must be configured to perform instant customer identity verification (KYC) as part of the linking flow, satisfying the Implied concern: Comply with financial regulations governing quasi-cash instruments, specifically regarding unclaimed property and escheatment laws ([CON-B1DFEBEC8C](../project_glossary.md#con-b1dfebec8c)).
3. Jurisdictional Compliance: The Plaid integration must be configured to support data residency and jurisdictional compliance (CON-30EA97016B) for user data across the initial US metro footprints (SF, NYC, Chicago).
4. Success State: Upon successful linking, the UI must confirm the bank account is linked and display the last four digits of the account for donor reference.

#### US-2.3: Payment Method Management & Default Selection

As a Donor (ACT-80C62C7814),
I want to view my linked payment methods and set a default,
So that my recurring donations or round-ups are automatically drawn from my preferred source.

Acceptance Criteria:
1. View Linked Methods: The Donor Dashboard must display a list of all linked payment methods (cards and bank accounts), showing only the last four digits and the card brand (Visa, Mastercard, etc.) for security.
2. Set Default: The donor must be able to select one payment method as the "Default" for all future transactions and round-ups.
3. Remove Method: The donor must be able to remove a linked payment method, with a confirmation dialog to prevent accidental deletion.
4. Error Handling: If a linked card is declined or a bank account is closed, the UI must clearly notify the donor and prompt them to update their payment method.

### 2.2. Edge Cases & Error Flows

1. Card Declined Pre-Auth: If the $0.01 pre-authorization fails, the UI must display a clear, non-technical error message (e.g., "Your card was declined. Please check your details or try a different card.") and provide a "Try Again" button that re-opens the Stripe Element.
2. Plaid Link Session Timeout: If the Plaid Link session times out, the UI must gracefully close the modal and prompt the donor to "Link Bank Account Again."
3. Network Failure During Tokenization: If the network fails while sending the token to the MealCredit server, the UI must display a "Connection Error" message and allow the donor to retry without re-entering their card details (by re-using the existing Stripe Element).
4. Duplicate Payment Method: If the donor attempts to link a card that is already linked (detected via Stripe's duplicate detection), the UI must inform the donor that the card is already linked and skip the confirmation step.

### 2.3. Data Residency & Security Constraints

Data Residency: All payment method tokens and associated donor PII must be stored in accordance with the Implied concern: Data residency and jurisdictional compliance for user data across multiple metropolitan regions (CON-30EA97016B). This implies that donor data from SF, NYC, and Chicago must be stored in AWS regions compliant with local data sovereignty laws.
Secure Client-Side Storage: Any sensitive tokens or session identifiers stored on the Expo mobile device must use SecureStore (CON-34312C6DC9) to prevent token theft or cloning.
SOC2 Type II Planning: The access control policies for viewing linked payment methods must be designed to support SOC2 Type II structural planning (CON-81FB01F06B), ensuring that only authorized personnel (Platform Administrator [ACT-086A974D63](../project_glossary.md#act-086a974d63)) can access audit logs related to payment method changes.

### 2.4. Knowledge Gaps & Assumptions

KNOWLEDGE_GAP: The exact fee structure for ACH vs. Credit Card transactions is not specified. This will impact the donor's choice of payment method and the UI's recommendation engine. Owner: Product/Finance.
KNOWLEDGE_GAP: The specific Plaid products to be used (e.g., Auth vs. Transactions) are not defined. This impacts the depth of KYC and the ability to verify account ownership. Owner: Product/Compliance.
ASSUMPTION: Stripe Connect is the chosen payment processor for the platform, as implied by the technical architecture references (Stripe Webhooks [CON-06232374D9](../project_glossary.md#con-06232374d9), PCI-DSS Level 1 CON-66390130AA). This assumption is necessary to specify Stripe Elements and Plaid Link integration details.
ASSUMPTION: The "Default" payment method is a donor-controlled setting, not a platform-controlled one. This aligns with the donor-centric onboarding journey.

### 2.5. Handoff to Design

UI Components: Design must create wireframes for the Stripe Element integration, Plaid Link modal, and Payment Method Management dashboard.
Accessibility: Ensure all payment entry fields and error messages are accessible via screen readers and keyboard navigation.
Branding: The Stripe Element must be styled to match MealCredit's brand guidelines while maintaining Stripe's security indicators.

This section provides the complete product specification for secure payment method integration, ensuring compliance, security, and a seamless donor experience.

---

## 3. DonorModule Funding Engine Configuration

This section defines the product requirements for the DonorModule funding engine, enabling the Donor (ACT-80C62C7814) to configure how their financial contributions are processed, allocated, and tracked. The engine supports micro-donation round-ups, directed impact preferences, and open pool allocations, ensuring a frictionless and transparent funding experience.

### 3.1. Micro-Donation Round-Ups

User Story: As a Donor (ACT-80C62C7814), I want to automatically round up my everyday purchases to the nearest dollar (or custom increment) so that I can contribute to the platform's mission without feeling the financial impact of each individual donation.

Acceptance Criteria:
1. Configuration: The Donor can enable or disable the round-up feature at any time via the DonorModule settings.
2. Increment Selection: The Donor can select the round-up increment (e.g., nearest $1, $5, $10) or define a custom percentage of their transaction value.
3. Source Deduction: Round-up amounts are automatically deducted from the Donor's primary linked payment method (via Plaid/Stripe) and transferred to their MealCredit balance.
4. Transparency: Each round-up transaction is logged in the Donor's transaction history with a clear label (e.g., "Round-up from [Merchant Name]") and the exact amount contributed.
5. Multi-Modal Interaction: The round-up configuration and history can be accessed and managed via voice commands (e.g., "Hey MealCredit, show my round-up history"), tap-to-view in the mobile app, and scan-to-configure via QR codes on partner receipts.

Edge Cases & Error Flows:
- Insufficient Funds: If the Donor's linked payment method is declined for a round-up, the system must immediately notify the Donor via push notification and in-app alert, prompting them to update their payment method or disable round-ups.
- Transaction Reversal: If the original purchase is reversed or refunded, the corresponding round-up amount must be automatically reversed and credited back to the Donor's MealCredit balance.

### 3.2. Directed Impact Preferences

User Story: As a Donor (ACT-80C62C7814), I want to direct my donations to specific NGOs or impact categories (e.g., "SF Bay Area Food Banks," "Youth Nutrition Programs") so that I can ensure my contributions align with my personal values and desired social outcomes.

Acceptance Criteria:
1. NGO Selection: The Donor can select one or more NGOs from a curated list of partner organizations. The list is filtered by the Donor's selected metropolitan footprint (SF, NYC, or Chicago).
2. Impact Categories: The Donor can assign their donations to predefined impact categories (e.g., "Emergency Food Relief," "Long-Term Nutrition Support") which are mapped to specific NGO programs.
3. Allocation Rules: The Donor can set allocation rules for their funding (e.g., "100% to [NGO X]" or "50% to [NGO X], 50% to [NGO Y]").
4. Dynamic Updates: The Donor can update their directed impact preferences at any time. New allocations apply to all future transactions until changed.
5. Impact Receipts: The Donor receives an immutable impact receipt for each directed donation, detailing the amount, the specific NGO/program, and the estimated impact (e.g., "This donation provided 5 meals").

Edge Cases & Error Flows:
- NGO Unavailability: If a selected NGO is no longer active or has reached its funding cap for a specific program, the system must notify the Donor and prompt them to select an alternative NGO or category.
- Compliance Check: All directed impact preferences must be validated against the Implied concern: Comply with financial regulations governing quasi-cash instruments (CON-B1DFEBEC8C) to ensure no funds are directed to prohibited entities.

### 3.3. Open Pool Allocations

User Story: As a Donor (ACT-80C62C7814), I want to contribute to an open pool of funds that is distributed among all partner NGOs based on their current needs and capacity, so that I can support the platform's overall mission without having to choose specific recipients.

Acceptance Criteria:
1. Pool Contribution: The Donor can allocate a fixed percentage or amount of their total donations to the open pool.
2. Distribution Logic: The open pool funds are distributed to NGOs based on a transparent, pre-defined algorithm (e.g., proportional to the number of active Beneficiaries ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) in each NGO's network).
3. Transparency Dashboard: The Donor can view a dashboard showing the total open pool balance, the distribution ratio per NGO, and the total impact of the open pool.
4. Flexibility: The Donor can switch between directed impact preferences and open pool allocations at any time.

Edge Cases & Error Flows:
- Pool Insufficiency: If the open pool is depleted, the system must notify the Donor and prompt them to either contribute more to the pool or switch to directed impact preferences.

### 3.4. Multi-Modal Interaction Paths

User Story: As a Donor (ACT-80C62C7814), I want to interact with the DonorModule funding engine using multiple input methods (voice, tap, scan) so that I can configure and monitor my donations in the most convenient way for my current context.

Acceptance Criteria:
1. Voice Commands: The mobile app must support voice commands for common funding actions (e.g., "Enable round-ups," "Show my impact receipts").
2. Tap-to-View: The Donor can tap on a transaction in their history to view detailed impact information and related receipts.
3. Scan-to-Configure: The Donor can scan a QR code on a partner receipt to instantly view the round-up amount and confirm the donation.
4. Accessibility: All multi-modal interactions must comply with WCAG 2.1 AA standards, ensuring accessibility for users with visual or motor impairments.

Edge Cases & Error Flows:
- Voice Recognition Failure: If a voice command is not recognized, the system must provide a clear error message and suggest alternative phrasing or fall back to the text-based interface.
- QR Code Expiry: If a QR code is scanned after its validity period, the system must prompt the Donor to generate a new code or view the transaction history directly.

## 4. Impact Tracking & Immutable Receipts

This section defines the product requirements for the Donor (ACT-80C62C7814) to view immutable impact receipts and track their Donation-to-Redemption Velocity (DRV). The core product challenge is providing donors with tangible proof of their impact while strictly adhering to the anonymity and data isolation constraints required to eliminate social stigma and comply with FTC guidelines.

### 4.1. Immutable Impact Receipts

The platform must generate an immutable, verifiable receipt for every funding event. This receipt serves as the primary trust mechanism for the Donor, confirming that their contribution has been successfully processed and allocated.

User Story:
As a Donor (ACT-80C62C7814), I want to receive an immutable, timestamped impact receipt immediately after my donation is processed, so that I have a verifiable record of my contribution for personal tracking and tax purposes.

Acceptance Criteria:
1. Receipt Generation: Upon successful funding activation (e.g., round-up completion or direct deposit), the system generates a digital impact receipt.
2. Immutable Storage: The receipt is cryptographically hashed and stored in an append-only ledger (e.g., Aurora PostgreSQL with append-only logging [CON-1762EA5021](../project_glossary.md#con-1762ea5021)) to prevent tampering.
3. Content Requirements: The receipt must include:
   - A unique, non-sequential receipt ID.
   - The exact timestamp of the transaction.
   - The amount donated (in fiat currency).
   - The equivalent culinary credits issued to the Beneficiary pool.
   - The specific NGO (NGO Operator ACT-09E028AEB0) or regional pool that received the funds.
   - A cryptographic hash or QR code linking to the public, anonymized ledger entry.
4. Accessibility: Receipts are accessible via the Donor's mobile app (Expo) and web dashboard (Next.js) and can be exported as a PDF.

Constraints & Edge Cases:
- Privacy: The receipt must NOT contain any PII of the Beneficiary (ACT-ADA6716160) or the specific Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) where the credits were eventually spent. It only confirms the allocation to the pool.
- Failure State: If the funding event fails (e.g., bank decline), no receipt is generated. The Donor is notified of the failure and prompted to retry.

### 4.2. Donation-to-Redemption Velocity (DRV) Tracking

The DRV metric allows the Donor to see the speed and efficiency with which their donated credits are being utilized by Beneficiaries. This provides a sense of immediate impact and liquidity health.

User Story:
As a Donor (ACT-80C62C7814), I want to track the Donation-to-Redemption Velocity (DRV) of my contributions, so that I can see how quickly my donations are being converted into meals for Beneficiaries in my target region.

Acceptance Criteria:
1. Metric Definition: DRV is defined as the average time elapsed between a credit being issued to a Beneficiary pool and the credit being fully redeemed at a Merchant POS.
2. Dashboard Visualization: The Donor dashboard displays the current DRV for their specific funding pool (e.g., "Your donations in SF are being redeemed in an average of 4.2 hours").
3. Real-time Updates: DRV metrics are updated in near real-time via Server-Sent Events (SSE) on the Next.js web dashboard to reflect the latest redemption events.
4. Anonymization: The DRV data is aggregated and anonymized. No individual Beneficiary or Merchant data is exposed. The correlation between donor impact and redemption is achieved using UUIDv4 mapping for analytics ([CON-23A501C051](../project_glossary.md#con-23a501c051), [CON-413928CB1C](../project_glossary.md#con-413928cb1c)) without linking PII.

Constraints & Edge Cases:
- Data Residency: DRV metrics must be segmented by metro footprint (SF, NYC, Chicago) to comply with data residency requirements (CON-30EA97016B, [CON-4093C26BCC](../project_glossary.md#con-4093c26bcc)). A Donor funding the SF pool should only see SF DRV metrics.
- Low Volume Edge Case: If there are insufficient redemption events in a pool to calculate a statistically significant DRV (e.g., fewer than 10 redemptions in the last 24 hours), the dashboard should display "Insufficient data to calculate velocity" rather than a misleading average.

### 4.3. Anonymized Correlation & Analytics

The underlying product logic must ensure that the correlation between donor impact and beneficiary redemption is strictly anonymized. This is critical for maintaining the platform's mission to decouple food assistance from social stigma.

Product Requirements:
1. UUIDv4 Mapping: The system must use UUIDv4 mapping to link donor funding events to beneficiary redemption events at the analytics layer. This mapping must never be exposed to the Donor or the Beneficiary.
2. PII Segregation: Beneficiary demographic status and legal names must be cryptographically segregated from public redemption analytics ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4), [CON-92F07E31B0](../project_glossary.md#con-92f07e31b0)). The Donor's view of DRV and impact receipts must only see aggregated, anonymized data.
3. FTC Compliance: The anonymization process must adhere to FTC guidelines on anonymity, ensuring no de-anonymization attacks can link beneficiaries to donors through metadata analysis ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d), [CON-C22D030D21](../project_glossary.md#con-c22d030d21)).

Knowledge Gaps:
- `KNOWLEDGE_GAP: Analytics - The specific threshold for "statistically significant" DRV data (e.g., minimum number of redemptions) must be established by the Product and Data teams.`
- `KNOWLEDGE_GAP: Data Retention - The specific data retention policy for donor transaction history vs. anonymous redemption analytics (CON-4820FAD5A9, CON-6F604D5455) must be defined to ensure compliance with financial regulations (CON-B1DFEBEC8C).`

### 4.4. Multi-Modal Interaction for Impact

The Donor should be able to view their impact receipts and DRV metrics through multiple interaction paths, ensuring accessibility and convenience.

User Story:
As a Donor (ACT-80C62C7814), I want to view my impact receipts and DRV metrics through multi-modal interaction paths (voice, tap, scan), so that I can access my impact data in the way that is most convenient for me.

Acceptance Criteria:
1. Mobile App (Expo): The primary interface for viewing receipts and DRV. Supports touch interactions and screen reader compatibility (WCAG) (CON-68497304B1, CON-CD9BDF7662).
2. Web Dashboard (Next.js): Provides a more detailed view of DRV trends and historical receipts. Supports keyboard-only navigation ([CON-6C177D0102](../project_glossary.md#con-6c177d0102), [CON-D0DEFC531A](../project_glossary.md#con-d0defc531a)).
3. Voice Interaction (Future State): The product spec notes the requirement for multi-modal interaction paths (CON-2D70EDCDEE, [CON-FC09C32F32](../project_glossary.md#con-fc09c32f32)). For this phase, the architecture must support future integration of voice commands (e.g., "Hey MealCredit, show my last receipt") via the Expo mobile app.

Constraints & Edge Cases:
- Offline Fallback: If the Donor's device is offline, the app should cache the last known DRV and receipt data. Upon reconnection, it should sync any new data. The offline fallback interface must be intuitive ([CON-387CDD9AEB](../project_glossary.md#con-387cdd9aeb), [CON-FA7A13E601](../project_glossary.md#con-fa7a13e601)).

### 5.1. Jurisdictional Data Residency (CON-30EA97016B)

Objective: Ensure that all Donor PII and financial data are stored and processed within the specific metropolitan footprint (SF, NYC, or Chicago) where the Donor resides, preventing cross-border or cross-jurisdictional data leakage.

User Stories & Acceptance Criteria:

 US-5.1.1: Geo-Location and Data Routing
  As a Donor (ACT-80C62C7814),
  I want my account to be automatically associated with the correct metropolitan data zone (SF, NYC, or Chicago) based on my IP address and billing address during onboarding,
  So that my data remains compliant with local data residency laws.
  Acceptance Criteria:
  The onboarding flow must capture the Donor's primary residence (City/State) as a mandatory field.
  The system must map the residence to one of the three active metro footprints: San Francisco (SF), New York City (NYC), or Chicago (CHI).
  All PII and financial records for a Donor must be logically or physically isolated within the data store corresponding to their assigned metro footprint.
  If a Donor's residence is outside the three initial metro footprints, the onboarding flow must display a clear error message stating that the service is currently limited to SF, NYC, and Chicago, and prevent account creation.

 US-5.1.2: Data Residency Transparency
  As a Donor (ACT-80C62C7814),
  I want to be informed about where my data is stored during onboarding,
  So that I can trust that my information is handled according to local regulations.
  Acceptance Criteria:
  The onboarding consent screen must explicitly state that data is stored within the [Assigned Metro Footprint] data center.
  The privacy policy must clearly define the data residency boundaries for each metro footprint.

### 5.2. Quasi-Cash Financial Compliance (CON-B1DFEBEC8C)

Objective: Ensure the platform complies with financial regulations governing quasi-cash instruments, specifically regarding unclaimed property and escheatment laws. This prevents the platform from inadvertently holding dormant funds without proper legal handling.

User Stories & Acceptance Criteria:

 US-5.2.1: Dormant Balance Monitoring
  As a Platform Administrator (ACT-086A974D63),
  I want the system to track the inactivity period of any Donor's funding balance,
  So that we can identify accounts that may be subject to unclaimed property laws.
  Acceptance Criteria:
  The system must define a "Dormant Account" threshold based on the lack of any donation activity or profile updates for a specific period.
  KNOWLEDGE_GAP: The exact number of days constituting a "Dormant Account" must be established by the Compliance team based on the specific regulations of SF, NYC, and CHI. `ASSUMPTION: 12 months` is used as a placeholder for design purposes; this value is reversible and requires legal evidence.
  The system must flag accounts that exceed this dormant threshold for review.

 US-5.2.2: Escheatment Notification Flow
  As a Donor (ACT-80C62C7814),
  I want to receive notifications if my account is approaching the dormant status threshold,
  So that I can reactivate my account and prevent my funds from being escheated to the state.
  Acceptance Criteria:
  The system must send a proactive email notification to the Donor when their account reaches 80% of the dormant threshold period.
  The notification must clearly explain the concept of unclaimed property and provide a direct link to reactivate their account or withdraw remaining funds.
  A second notification must be sent upon reaching the dormant threshold, detailing the next steps for escheatment if no action is taken.

 US-5.2.3: Unclaimed Property Reporting
  As a Platform Administrator (ACT-086A974D63),
  I want the system to generate a report of all dormant accounts that have exceeded the escheatment period,
  So that we can comply with state-specific unclaimed property filing requirements.
  Acceptance Criteria:
  The system must provide an exportable report of dormant accounts, including Donor ID, last known address, and remaining balance.
  The report must be segmented by jurisdiction (SF, NYC, CHI) to facilitate accurate state filing.
  KNOWLEDGE_GAP: The specific data fields required for unclaimed property reporting in each jurisdiction (SF, NYC, CHI) must be established by the Compliance team. `ASSUMPTION: Standard fields (Name, Address, SSN/Last 4, Balance)` are used as a placeholder; this requires legal evidence.

### 5.3. Secure Client-Side Storage for Offline Tokens (CON-34312C6DC9)

Objective: Ensure that offline tokens and sensitive donor configuration data are securely stored on the Expo mobile device using the platform's SecureStore implementation, preventing token theft, cloning, or unauthorized access if the device is compromised.

User Stories & Acceptance Criteria:

 US-5.3.1: Secure Token Storage
  As a Donor (ACT-80C62C7814),
  I want my offline fallback tokens and sensitive configuration data to be encrypted at rest on my device,
  So that my impact data remains secure even if my device is lost or stolen.
  Acceptance Criteria:
  The Expo mobile application must utilize the SecureStore API to store offline tokens and sensitive donor configuration data.
  Data stored via SecureStore must be encrypted using device-specific keys (e.g., iOS Keychain, Android Keystore).
  The application must ensure that no plaintext tokens or PII are cached in standard AsyncStorage or local storage.

 US-5.3.2: Token Lifecycle Management
  As a Donor (ACT-80C62C7814),
  I want my offline tokens to be automatically invalidated after a set period or upon app logout,
  So that stale tokens cannot be used to replay impact data or access outdated information.
  Acceptance Criteria:
  Offline tokens stored in SecureStore must include a time-bound cryptographic signature ([CON-AA83B13877](../project_glossary.md#con-aa83b13877)) to prevent replay attacks.
  The application must automatically purge SecureStore entries upon explicit user logout or after a defined inactivity period.
  The system must support remote token revocation via the backend, which will invalidate SecureStore tokens upon the next successful sync.

### 5.4. DonorModule Configuration: Open Pool Distribution Logic

Objective: Define the product behavior for the "Open Pool" donation configuration, ensuring that funds directed to the global or regional pool are correctly allocated and tracked without being tied to a specific NGO or merchant type.

User Stories & Acceptance Criteria:

 US-5.4.1: Open Pool Allocation
  As a Donor (ACT-80C62C7814),
  I want to configure my donations to flow into the "Open Pool" (global or regional),
  So that my funds can be distributed to any eligible Beneficiary in my chosen footprint without restriction.
  Acceptance Criteria:
  The Donor onboarding and funding configuration flow must include an "Open Pool" option alongside directed impact flows.
  When "Open Pool" is selected, the system must route the donation to the central regional pool for the Donor's assigned metro footprint (SF, NYC, or CHI).
  The system must ensure that Open Pool funds are subject to the same 72-hour rollback policy for emergency credits as directed funds (FR-BEN-03).

 US-5.4.2: Open Pool Impact Visibility
  As a Donor (ACT-80C62C7814),
  I want to see the aggregate impact of my Open Pool contributions on the DRV dashboard,
  So that I can understand the overall liquidity health of my regional pool.
  Acceptance Criteria:
  The DRV dashboard must clearly distinguish between directed impact DRV and Open Pool DRV.
  Open Pool DRV metrics must be aggregated and anonymized, adhering to the same FTC compliance standards (CON-B3D71A437D, CON-C22D030D21) as directed impact metrics.

### 5.5. Summary of Unresolved Questions

`KNOWLEDGE_GAP: Analytics - The specific threshold for "statistically significant" DRV data (e.g., minimum number of redemptions) must be established by the Product and Data teams.`
`KNOWLEDGE_GAP: Data Retention - The specific data retention policy for donor transaction history vs. anonymous redemption analytics (CON-4820FAD5A9, CON-6F604D5455) must be defined to ensure compliance with financial regulations (CON-B1DFEBEC8C).`
`KNOWLEDGE_GAP: Voice Interaction - The specific voice commands and integration points for the "Future State" voice interaction requirement (CON-2D70EDCDEE, CON-FC09C32F32) must be defined in a later phase.`
`KNOWLEDGE_GAP: Dormant Account Threshold - The exact number of days constituting a "Dormant Account" must be established by the Compliance team based on the specific regulations of SF, NYC, and CHI. `ASSUMPTION: 12 months` is used as a placeholder for design purposes; this value is reversible and requires legal evidence.`
`KNOWLEDGE_GAP: Unclaimed Property Reporting Fields - The specific data fields required for unclaimed property reporting in each jurisdiction (SF, NYC, CHI) must be established by the Compliance team. `ASSUMPTION: Standard fields (Name, Address, SSN/Last 4, Balance)` are used as a placeholder; this requires legal evidence.`

---

## VP decision

**Decision:** Approved

---

## VP feedback

(No feedback)

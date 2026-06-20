# Beneficiary Discovery & Redemption Journey

This artifact defines the product scope, user stories, and acceptance criteria for the Recipient (Beneficiary) within the MealCredit platform. The core mission is to decouple food assistance from social stigma by ensuring the beneficiary experience is indistinguishable from a standard consumer gift card or mobile wallet transaction.

## 1. Anonymous Profile & Credentialing

This section defines the product requirements for the initial onboarding of the Recipient (Beneficiary) and the NGO Facilitator. The core objective is to establish a pseudo-anonymous identity that allows the Recipient to access the MealCredit platform without exposing any Personally Identifiable Information (PII) to the platform, donors, or merchants. This aligns with the project's mission to decouple food assistance from social stigma.

### 1.2 Persona: Recipient (Beneficiary)

The Recipient is the end-user who will use the MealCredit platform to find restaurants and redeem credits. The onboarding experience must be dignified, simple, and strictly anonymous.

**User Story 1.2.1: Recipient Profile Creation via Access Code**
As a Recipient,
I want to enter a unique access code provided by my NGO Facilitator into the MealCredit app,
So that I can create a pseudo-anonymous profile and begin using the platform without providing my legal name, address, or other PII.

**Acceptance Criteria:**
* The app must have a prominent "Enter Access Code" screen on the welcome flow.
* Upon valid code entry, the system must validate the code against the ledger and transition the user to the profile creation screen.
* If the code is invalid, expired, or already used, the app must display a generic error message: "Invalid or expired code. Please contact your facilitator."
* The system must generate a unique, non-reversible pseudo-ID for the user upon successful code redemption.

**User Story 1.2.2: Pseudo-Anonymous Profile Setup**
As a Recipient,
I want to set up my profile by choosing a display name and preferred language, without entering my legal name or contact details,
So that I can personalize my experience while maintaining my anonymity and privacy.

**Acceptance Criteria:**
* The profile setup screen must allow the user to select a "Display Name" (e.g., "User123" or a custom alias).
* The user must be able to select their preferred language for the app interface.
* The system must NOT require an email address or phone number for the initial profile creation.
* All PII fields (legal name, SSN, address) must be explicitly hidden or omitted from the UI.
* The system must store only the pseudo-ID, display name, and language preference in the user profile table.

**User Story 1.2.3: Secure Offline Token Storage**
As a Recipient,
I want my access credentials and initial balance information to be stored securely on my device,
So that I can use the app even in areas with poor or no network connectivity, ensuring dignity and reliability.

**Acceptance Criteria:**
* The app must utilize hardware-backed secure storage (e.g., iOS Keychain, Android Keystore) to store the user's pseudo-ID and cryptographic keys.
* The app must cache the user's current balance and eligible restaurant list locally for offline access.
* The app must handle network errors gracefully, allowing the user to view their balance and nearby restaurants even when offline.

### 1.5 Knowledge Gaps & Assumptions

* **KNOWLEDGE_GAP: Code Expiration Policy** - The exact duration for which access codes remain valid (e.g., 7 days, 30 days) is not specified. This decision must be established by the Product Owner based on NGO operational workflows.
* **KNOWLEDGE_GAP: Facilitator Authentication** - The method for authenticating NGO Facilitators (e.g., SSO, email/password, government ID verification) is not defined. This is covered in the "Identity, Access & Offline Capability Foundation" artifact.
* **ASSUMPTION: Pseudo-ID Generation** - The system will generate a cryptographically secure, non-reversible pseudo-ID for each Recipient upon code redemption. This ID will be used for all internal tracking and balance management.
* **ASSUMPTION: Offline Balance Sync** - The system will allow Recipients to view their balance and nearby restaurants offline, but actual redemption transactions will require eventual consistency and network connectivity to clear with the POS system.

### 1.7 Definition of Done

* User stories 1.1.1, 1.1.2, 1.2.1, 1.2.2, and 1.2.3 are implemented and tested.
* All PII is confirmed to be excluded from the system.
* Offline functionality is verified on both iOS and Android devices.
* Edge cases (invalid code, expired code, network failure) are handled gracefully.
* Accessibility standards (WCAG) are met for the onboarding flow.
* Security review confirms that access codes are cryptographically secure and single-use.
* Product Owner has accepted the implementation based on the acceptance criteria.

---

## 2. Location-Aware Restaurant Discovery

This section defines the product requirements for the Recipient (Beneficiary) to discover participating restaurants. The core objective is to provide a frictionless, stigma-free discovery experience that mirrors standard consumer food-delivery or map applications, while strictly enforcing the platform's absolute anonymization and geo-fencing constraints.

### 2.2 User Stories

#### US-2.1: Location Permission and Initial Discovery
As a Recipient,
I want the app to automatically detect my current location and display nearby participating restaurants,
So that I can quickly find a place to eat without manually searching for addresses.

**Acceptance Criteria:**
1. Upon first launch, the app requests location permission with a clear, non-stigmatizing explanation (e.g., "To find restaurants near you").
2. If permission is granted, the app displays a map and a list of participating restaurants sorted by proximity.
3. If permission is denied, the app allows the user to manually enter a City, Zip Code, or Neighborhood to view available restaurants in that area.
4. The list and map must only show restaurants that are currently active and have available credit pool capacity in the local region (SF, NYC, or Chicago).

#### US-2.2: Filtering by Dietary and Accessibility Needs
As a Recipient,
I want to filter the list of restaurants by dietary preferences (e.g., Vegetarian, Vegan, Gluten-Free) and accessibility features (e.g., Wheelchair Accessible),
So that I can find a restaurant that meets my specific needs without visiting places that cannot accommodate me.

**Acceptance Criteria:**
1. The discovery screen includes a "Filters" button that opens a modal with dietary and accessibility checkboxes.
2. Filters are applied in real-time to the map and list views.
3. If no restaurants match the selected filters, the app displays a clear, non-judgmental empty state: "No restaurants found with these preferences nearby. Try adjusting your filters or expanding your search area."
4. The app must not store or log the user's specific dietary preferences in a way that could be linked to their identity.

#### US-2.3: Viewing Restaurant Details and Eligible Menu Items
As a Recipient,
I want to tap on a restaurant to see its details, including its address, hours, and a list of menu items that are eligible for MealCredit,
So that I can decide if I want to visit and know exactly what I can order.

**Acceptance Criteria:**
1. Tapping a restaurant opens a detail view showing the restaurant name, distance, address, and operating hours.
2. The detail view includes a "Menu" section that lists only the items eligible for MealCredit, clearly marked with their price in MealCredit units.
3. Ineligible items (e.g., alcohol, non-food merchandise) are explicitly excluded from the menu view.
4. The app displays a "Last Updated" timestamp for the menu to ensure the user is seeing current information.

#### US-2.4: Real-Time Availability and Throttle Indicators
As a Recipient,
I want to see if a restaurant is currently accepting MealCredit orders and if there are any capacity limits,
So that I do not travel to a restaurant that is temporarily unable to fulfill my order.

**Acceptance Criteria:**
1. The restaurant list and detail view display a real-time status indicator (e.g., "Accepting Orders," "Temporarily Unavailable," "High Demand").
2. If a restaurant has a real-time throttle limit that is nearing capacity, the app displays a warning: "This restaurant is currently experiencing high demand. Please check back later."
3. The status is updated via Server-Sent Events (SSE) to ensure the user sees the most current information without refreshing the page.

### 2.3 Edge Cases and Error Flows

1. **No Internet Connection:**
   If the user loses connectivity while browsing, the app caches the last known list of restaurants and their menus.
   A banner appears: "You are offline. Showing saved restaurant list."
   The user can still view saved restaurants but cannot see real-time availability or update their location.

2. **Location Permission Denied:**
   If the user denies location permission, the app defaults to a manual search interface.
   The user can enter a Zip Code or City to view restaurants in that area.

3. **No Restaurants in Area:**
   If no restaurants are found in the user's selected area, the app displays a clear empty state with a "Request New Partner" button (which defers to the Operator Monitoring & Management Dashboard for processing).

4. **Restaurant Closed or Out of Service:**
   If a user attempts to select a restaurant that is currently closed or has been deactivated by the Operator, the app displays a clear error: "This restaurant is currently unavailable. Please select another option."

### 2.4 Sibling Dependencies

* **Identity, Access & Offline Capability Foundation:** This artifact defers to that artifact for the specific implementation of offline caching and secure local storage of the restaurant list.
* **Restaurant Partner Onboarding & POS Integration:** This artifact defers to that artifact for the specific data schema of restaurant menus, eligibility rules, and real-time availability status.
* **Operator Monitoring & Management Dashboard:** This artifact defers to that artifact for the definition of "High Demand" thresholds and the processing of "Request New Partner" submissions.

---

## 3. Frictionless, Offline-Capable Redemption

This section defines the product requirements for the Recipient's redemption journey. The core objective is to ensure the experience is indistinguishable from a standard consumer gift card or mobile wallet transaction, while strictly enforcing absolute PII anonymization and offline-first token validation.

### 3.2 User Story: POS Scanning and Validation

As a Restaurant Partner (Provider),
I want to scan the Recipient's pseudo-anonymized token at the POS terminal,
So that the system can validate the token's authenticity and deduct the appropriate amount from the regional credit pool without requiring real-time beneficiary PII.

**Acceptance Criteria:**
1. **Scan Interface:** The POS integration (via zero-footprint edge dashboard or enterprise gateway) must accept the scanned token and immediately trigger a validation request.
2. **Pseudo-Anonymized Validation:** The validation request must only transmit the token's cryptographic signature and the transaction amount. No beneficiary PII (name, ID, location history) may be included in the validation payload.
3. **Real-Time Clearing:** The system must validate the token against the regional credit pool (e.g., SF, NYC, or Chicago) and return a success/failure response within the latency thresholds defined in the system success criteria.
4. **Ineligible Category Interception:** If the scanned order contains ineligible items (e.g., alcohol, non-food merchandise), the POS system must drop these items at the payment network layer before the receipt is printed, ensuring only eligible culinary credits are applied.

### 3.4 Edge Cases and Failure States

* **Lost or Stolen Token:** If a Recipient reports a lost or stolen virtual card, the NGO Facilitator must be able to invalidate the current token and issue a new one via the admin portal, ensuring the old token is immediately rejected by the POS system.
* **Network Failure During Validation:** If the POS system fails to receive a response from the central ledger within the defined latency threshold, the transaction must be declined to prevent double-spending, and the Recipient must be notified to retry or contact support.
* **Token Expiration:** Unused emergency credits must automatically roll back to the central regional pool after 72 hours of expiration. The app must clearly display the expiration date on the token screen.

## 3.6. Alignment with Project Context

**Absolute Anonymization:** This journey strictly enforces the project's requirement for absolute PII anonymization. No beneficiary demographic data crosses into production logs or the POS validation payload.

**PCI-DSS Level 1 Compliance:** The use of virtual card tokens ensures that raw credit card data is never stored on the platform, adhering to PCI-DSS Level 1 requirements.

**Multi-Tenant Architecture:** The validation process queries the regional credit pool (SF, NYC, or Chicago), ensuring multi-tenant data segregation as defined in the system blueprint.

**Donor Transparency:** Upon successful redemption, the Donor will receive an immutable transactional receipt within 120 seconds, strictly prohibiting the transmission of any identifying beneficiary parameters.

## 4. Privacy & Stigma Mitigation

This section defines the product requirements for ensuring that the Recipient's interaction with the MealCredit platform and participating restaurants is strictly pseudo-anonymized. The core objective is to decouple food assistance from social stigma by ensuring that no PII (Personally Identifiable Information) or donor-attribution data is visible to the Restaurant Partner or the POS system during the redemption flow.

### 4.1 Pseudo-Anonymized Token Presentation

The Recipient's primary interface for redemption is a single-use, pseudo-anonymized virtual card token. This token must be visually indistinguishable from a standard consumer gift card or mobile wallet pass to prevent any social signaling.

**User Story 4.1.1: Recipient View of Redemption Token**
As a Recipient,
I want to view a clean, branded virtual card token in my mobile app (or Apple/Google Wallet pass),
So that I can present it at the restaurant POS without feeling stigmatized or revealing my beneficiary status.

**Acceptance Criteria:**
1. The token UI must display a generic brand name (e.g., "MealCredit") and a unique, high-entropy barcode/QR code.
2. The UI must not display any text indicating "Donation," "Charity," "Beneficiary," or "NGO" on the front or back of the virtual card.
3. The token must be visually identical to a standard gift card, using standard color palettes and typography consistent with the project's design system.
4. The token must be generated client-side or fetched securely via an authenticated session, ensuring no PII is rendered in the app's local cache or logs.

**Edge Cases & Error Flows:**
*   **Expired Token:** If the token has expired (e.g., 72-hour rollback policy), the UI must display a generic "Token Expired" message and prompt the Recipient to contact their NGO Facilitator for a new allocation. No details about the expiration policy or donor funds should be shown.
*   **Insufficient Balance:** If the token balance is insufficient for the order, the UI must display a generic "Insufficient Funds" message. It must not specify the exact remaining balance or the source of the funds.

### 4.2 POS Interaction & Data Stripping

The interaction between the Recipient's token and the Restaurant's POS system must be strictly pseudo-anonymous. The POS system must only receive the necessary financial authorization data, stripped of any beneficiary identity or donor attribution.

**User Story 4.2.1: Restaurant POS Receipt of Pseudo-Anonymized Payment**
As a Restaurant Partner (POS System),
I want to receive a standard payment authorization request from the MealCredit system,
So that I can process the transaction without ever seeing the Recipient's identity or the source of the funds.

**Acceptance Criteria:**
1. The POS integration must receive a transaction payload containing only:
    *   A unique, non-reusable transaction ID (UUIDv4).
    *   The authorization token (single-use virtual card token).
    *   The transaction amount.
    *   The Merchant Category Code (MCC) for validation.
2. The payload must not contain any beneficiary PII (name, ID, NGO affiliation, location history beyond the immediate transaction context).
3. The payload must not contain any donor attribution data (e.g., "Funded by [Donor Name]" or "Directed Impact Flow ID").
4. The POS receipt printed or displayed to the Recipient must be a standard merchant receipt, showing only the restaurant's branding, the items purchased, and the payment method as "MealCredit" or "Virtual Card."

**Technical Constraints (Product View):**
*   The system must enforce Absolute Anonymization at the network layer. No beneficiary demographic data, legal name, or domestic background may cross into production logs or POS communication channels.
*   The transaction must be cleared via standard banking networks to ensure the POS treats it as a standard financial instrument.

### 4.3 Donor Transparency & Recipient Privacy Boundary

While Donors require transparency on the impact of their contributions, this transparency must never compromise the Recipient's anonymity. The system must enforce a strict zero-knowledge boundary between Donors and Recipients.

**User Story 4.3.1: Donor Receipt of Anonymized Impact**
As a Donor,
I want to receive an immutable transactional receipt within 120 seconds of a Recipient's redemption,
So that I can confirm my contribution was used, without ever learning the identity of the Recipient.

**Acceptance Criteria:**
1. The Donor's receipt must confirm the redemption event (e.g., "Your contribution funded a meal at [Restaurant Name]").
2. The receipt must strictly prohibit the transmission of any identifying beneficiary parameters (name, location, NGO, etc.).
3. The receipt must be generated within 120 seconds of the POS clearing the transaction, ensuring real-time transparency for the Donor.
4. The receipt must be immutable and stored in the Donor's audit trail for tax/compliance purposes.

**Assumptions & Knowledge Gaps:**
*   **ASSUMPTION:** The restaurant name is the only identifiable entity shared with the Donor. If the project requires further anonymization (e.g., "a restaurant in SF"), this must be explicitly defined.
*   **KNOWLEDGE_GAP:** The exact format and content of the Donor's immutable receipt (e.g., PDF vs. in-app notification) is not yet defined. This should be specified in the Donor Contribution & Matching Journey artifact.

### 4.4 Offline-First Privacy & Security

To ensure dignity and accessibility, the redemption flow must support offline capabilities without compromising security or privacy. The token must be stored securely on the device and validated without requiring real-time network access to the central ledger for every scan.

**User Story 4.4.1: Secure Offline Token Storage**
As a Recipient,
I want to store my redemption token securely on my device (using hardware-backed SecureStore),
So that I can present it at the POS even in low-connectivity environments, without risking token theft or PII leakage.

**Acceptance Criteria:**
1. The token must be stored in the device's hardware-backed SecureStore (e.g., iOS Keychain, Android Keystore).
2. The token must be encrypted at rest and only accessible to the MealCredit app.
3. The token must be single-use and time-bound. Once presented, it must be invalidated on the device and the central ledger.
4. The app must handle network failures gracefully, allowing the Recipient to present the token even if the device is offline, with the POS system handling the eventual consistency of the balance update.

**Edge Cases:**
*   **Device Loss:** If a Recipient loses their device, the token must be immediately revocable by the NGO Facilitator via the admin portal. The Facilitator must be able to issue a new token to the Recipient without exposing the lost token's details.
*   **Token Replay:** The POS system must validate the token against the central ledger (or a cached, eventually consistent copy) to prevent replay attacks. If the token is already used, the POS must display a generic "Invalid Token" message.

### 4.5 Offline Redemption & Reconciliation

This section defines the product requirements for handling redemption when the Recipient's device has no network connectivity, and the subsequent reconciliation process.

**User Story 4.5.1: Offline Redemption Presentation**
As a Recipient,
I want to present my stored token at the POS even when my device is offline,
So that I can access food assistance regardless of network availability.

**Acceptance Criteria:**
1. The app must allow the Recipient to view and present the token barcode/QR code without an active internet connection.
2. The token must contain sufficient cryptographic proof (e.g., a signed, time-bound nonce) to allow the POS to validate its authenticity locally or via a cached ledger state.
3. The POS must queue the transaction locally if it cannot reach the central ledger, and the MealCredit backend must reconcile the transaction once connectivity is restored.
4. The Recipient must receive a visual confirmation (e.g., a checkmark) that the token was successfully presented, even if the backend settlement is pending.

**Edge Cases & Error Flows:**
*   **Double-Spend Prevention:** If a Recipient presents the same offline token at multiple POS terminals before reconciliation, the system must flag the duplicate transaction. The first cleared transaction stands; subsequent attempts must be rejected with a "Token Already Redeemed" message.
*   **Reconciliation Failure:** If the central ledger rejects a queued offline transaction (e.g., due to insufficient funds discovered after the fact), the system must notify the NGO Facilitator to resolve the discrepancy with the Recipient. The Recipient must not be charged or penalized for system reconciliation delays.

### 4.6 Summary of Privacy & Stigma Mitigation Controls

| Control Area | Requirement | Grounded Target | Owner |
| :--- | :--- | :--- | :--- |
| Token UI | Generic, non-stigmatizing design | Visually identical to consumer gift card | Design |
| POS Data | PII-stripped transaction payload | Payload contains only auth data | Design/Dev |
| Donor Receipt | Anonymized impact confirmation | No beneficiary PII in receipt | Product |
| Offline Storage | Hardware-backed SecureStore | Single-use, time-bound token | Dev |
| Audit Trail | Immutable, PII-free log | Append-only, compliant with SOC2/PCI | Ops/Compliance |

This section ensures that the Recipient's journey is dignified, private, and stigma-free, while maintaining the necessary compliance and security standards for the platform.

---

## 5.1. Core Redemption Metrics

These metrics directly measure the efficiency and success of the core transaction loop: Discovery -> Token Generation -> POS Redemption.

| Metric | Definition | Target | Measurement Method |
| :--- | :--- | :--- | :--- |
| Redemption Completion Rate (RCR) | The percentage of generated virtual card tokens that are successfully cleared at a POS terminal. | > 95% | `(Successful POS Clears / Total Tokens Generated) * 100` |
| Time-to-Redemption (TTR) | The average elapsed time between a token being generated (assigned to the Recipient) and the moment it is successfully cleared at a POS. | < 24 hours | Average duration tracked in the Aurora ledger from `token_issued` to `token_cleared` events. |
| First-Attempt Success Rate (FASR) | The percentage of POS scans that result in a successful transaction on the very first attempt, without requiring a retry or manual intervention. | > 90% | `(First-Attempt Successes / Total Scan Attempts) * 100` |

## 5.2. Stigma-Free Experience Validation

These metrics validate the core mission of decoupling food assistance from social stigma by measuring the friction and dignity of the user experience.

| Metric | Definition | Target | Measurement Method |
| :--- | :--- | :--- | :--- |
| Frictionless Redemption Score | A composite score based on the average time taken by the Recipient to present the token at the POS after selecting a restaurant. | < 30 seconds | Tracked via client-side timestamps in the Expo mobile app from `token_viewed` to `scan_initiated`. |
| Anonymous Profile Adoption Rate | The percentage of Recipients who complete the NGO Facilitator credentialing and profile setup without dropping off. | > 85% | `(Completed Profiles / Profiles Initiated) * 100` |
| User Satisfaction Score (SUS) | The System Usability Scale (SUS) score collected from Recipients post-redemption, specifically focusing on the ease of use and perceived dignity of the experience. | > 75 (Good) | In-app survey triggered 1 hour post-redemption. |

## 5.4. Offline Capability and Resilience

Given the requirement for offline-first capability, these metrics ensure the system remains robust in low-connectivity environments.

| Metric | Definition | Target | Measurement Method |
| :--- | :--- | :--- | :--- |
| Offline Token Presentation Success | The percentage of times a Recipient can successfully view and present their offline token without requiring a network refresh. | 100% | Tracked via client-side SecureStore access logs. |
| Eventual Consistency Latency | The maximum time delay between an offline token scan and its synchronization with the central Aurora ledger. | < 5 minutes | Measured from `offline_scan_timestamp` to `ledger_update_timestamp`. |

## 5.6. Data Collection and Privacy

All metrics must be collected in strict adherence to the Absolute Anonymization principle. No PII (Personally Identifiable Information) such as legal names, addresses, or demographic data will be stored in production logs or associated with these KPIs. Data will be aggregated and anonymized at the source before being sent to the analytics pipeline.

*   **Client-Side Telemetry:** Expo app will send anonymized event logs (e.g., `token_generated`, `scan_initiated`) with a unique, non-reversible session ID.
*   **Server-Side Aggregation:** The Aurora ledger will aggregate transaction data (e.g., `token_cleared`, `amount`) without linking it to individual Recipient identities.
*   **Survey Data:** SUS surveys will be collected via a separate, anonymized form that does not require Recipient login or PII.
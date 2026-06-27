# UI/UX Artifact: Beneficiary Eligibility & Voucher Redemption Flow

This artifact defines the high-fidelity interaction design for the **NGO Operator** ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) to assign eligibility to a **Beneficiary** ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)), and the subsequent **Beneficiary** experience for discovering and redeeming anonymous culinary credits. The design strictly enforces data isolation ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4), [CON-92F07E31B0](../project_glossary.md#con-92f07e31b0)), anonymity ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d), [CON-C22D030D21](../project_glossary.md#con-c22d030d21)), and accessibility ([CON-68497304B1](../project_glossary.md#con-68497304b1), [CON-6C177D0102](../project_glossary.md#con-6c177d0102)).

---

### 1.1 Screen: Eligibility Assignment Dashboard

**Purpose:** Allow the NGO Operator to select a verified Beneficiary record and initiate the credential generation process.

**Layout & Components:**
*   **Header:** "Beneficiary Eligibility Management" with a "Privacy & Compliance" badge indicating active data isolation mode.
*   **Search/Filter Bar:** Search by Beneficiary ID (UUIDv4) or name (masked, e.g., "J D"). Filter by NGO branch and eligibility status.
*   **Beneficiary List:** A table or card list showing masked names, eligibility status (Pending, Active, Revoked), and last redemption date.
*   **Action Button:** "Assign Eligibility" (disabled if already Active).

**Interaction States:**
*   **Empty State:** "No beneficiaries found matching your criteria."
*   **Loading State:** Skeleton loaders for list items.
*   **Error State:** "Failed to load beneficiary records. Please try again." with a "Retry" button.

**Accessibility:**
*   All text elements must have a minimum contrast ratio of 4.5:1 (WCAG AA).
*   Keyboard navigation must be supported for all interactive elements.
*   Screen reader labels must clearly indicate the masked nature of the data (e.g., "Beneficiary name: J D, status: Pending").

### 1.2 Screen: Secure Credential Handoff

**Purpose:** Generate and display the anonymous credential for the Beneficiary to scan.

**Layout & Components:**
*   **Confirmation Modal:** "Confirm Eligibility Assignment" with a summary of the Beneficiary's masked details and a warning that no PII will be transmitted.
*   **Credential Display:** A large, high-contrast QR code centered on the screen.
*   **Manual Entry Fallback:** A text field displaying the alphanumeric token (e.g., "MC-XXXX-XXXX-XXXX") with a "Copy" button.
*   **Privacy Mode Toggle:** A prominent toggle that, when activated, blurs all PII fields on the screen (including the masked name) to prevent shoulder-surfing.
*   **Countdown Timer:** A 5-minute timer for the credential's validity, with a "Regenerate" button.

**Interaction States:**
*   **Generating:** "Generating secure credential..." with a spinner.
*   **Success:** QR code and manual token displayed.
*   **Expired:** "Credential expired. Please regenerate." with a "Regenerate" button.
*   **Error:** "Failed to generate credential. Please try again." with a "Retry" button.

**Accessibility:**
*   The QR code must be large enough to be scannable by standard smartphone cameras (minimum 2x2 inches on a standard display).
*   The manual entry token must be in a monospace font for easy reading.
*   The "Privacy Mode" toggle must be clearly labeled and have a visible state indicator.

### 1.3 Data Isolation & Security Measures

*   **PII Masking:** All PII fields are masked in the UI. The NGO Operator can only see the masked name and eligibility status.
*   **No PII Transmission:** The credential generation process does not transmit any PII to the client device. Only the anonymous credential (QR code/token) is sent.
*   **Audit Logging:** All eligibility assignments and credential generations are logged to AWS CloudTrail ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2)) for SOC2 Type II compliance.
*   **Data Retention:** Beneficiary demographic data is stored in a separate, encrypted database with restricted access ([CON-2788862587](../project_glossary.md#con-2788862587)).

---

## 2. Find & Redeem Location Discovery Interface

This artifact defines the high-fidelity UI/UX for the Beneficiary's 'Find & Redeem' screen, ensuring the experience is indistinguishable from a standard, premium gift card application. The design strictly enforces anonymity by hiding all 'charity', 'donation', or 'MealCredit' branding, presenting the interface as a neutral restaurant discovery tool.

### 2.1 Screen Layout & Information Architecture

The screen utilizes a split-view layout optimized for mobile devices (Expo v51 / React Native):

*   **Top Section (20% height):** A persistent, minimal header displaying the user's available balance (e.g., "$12.50") and a 'History' icon. No logo or app name is displayed to maintain anonymity.
*   **Middle Section (60% height):** A map-based view (using React Native Maps) showing nearby restaurant pins. Pins are neutral icons (e.g., a simple fork and knife) without color-coding that might imply 'charity' status. A list view toggle is available for users who prefer a text-based list.
*   **Bottom Section (20% height):** A filter bar and search input. The search input is labeled "Search restaurants" to maintain neutrality.

### 2.2 Anonymity & Data Isolation Enforcement

To adhere to strict data isolation (CON-0A0288EED4, CON-92F07E31B0) and FTC guidelines on anonymity (CON-B3D71A437D, CON-C22D030D21):

*   **No PII Display:** The UI must never display the Beneficiary's name, demographic status, or any identifier linked to their donor or NGO origin.
*   **Neutral Terminology:** All UI strings must use neutral, empowering language. For example, instead of "Meal Credits," use "Balance." Instead of "Donated by," use "Funded by."
*   **Metadata Hiding:** Any backend data related to the source of funds (e.g., donor campaign IDs) must be stripped from the UI payload before rendering.

### 2.3 Interaction Design & States

*   **Loading State:** A skeleton loader for the map and list items, ensuring smooth perceived performance.
*   **Empty State:** If no restaurants are found within the default radius, display a neutral message: "No restaurants found nearby. Try adjusting your filters."
*   **Error State:** If the map fails to load, display a retry button and a message: "Unable to load map. Please check your connection."
*   **Filtering:** Users can filter by dietary flags (FR-BEN-02) such as "Vegetarian," "Vegan," or "Gluten-Free." These filters are presented as simple toggle chips.

### 2.5 Responsive Design

*   **Mobile-First:** The design is optimized for mobile devices, with a focus on thumb-friendly interactions.
*   **Tablet Support:** On tablets, the split-view layout expands to show the map on the left and the list on the right.

### 2.6 Deliverable

The deliverable for this step is a set of high-fidelity wireframes and interaction specifications for the 'Find & Redeem' screen, including:

*   Wireframes for the map view and list view.
*   Interaction specifications for filtering, searching, and selecting a restaurant.
*   Accessibility annotations for all UI elements.
*   Responsive design guidelines for mobile and tablet.

This artifact ensures that the Beneficiary's experience is dignified, anonymous, and indistinguishable from a standard gift card app, while providing the necessary functionality to discover and redeem meals at local restaurants.

---

## 3. POS Redemption Flow and Clearance Feedback Loop

This artifact defines the high-fidelity interaction design for the Beneficiary's Point of Sale (POS) redemption flow. The primary objective is to ensure the experience is indistinguishable from a standard gift card transaction while strictly enforcing anonymity and providing immediate, clear feedback on the financial clearance status. The design addresses the p99 latency concerns of [CON-6D5E21557B](../project_glossary.md#con-6d5e21557b) and [CON-7F03CF540E](../project_glossary.md#con-7f03cf540e) by optimizing the visual feedback loop for real-time clearance.

### 3.1 Interaction Flow: The 'Tap, Scan, Go' Sequence

The redemption flow is designed to be completed in under 3 seconds to prevent restaurant queue stagnation ([CON-4152F2C7C3](../project_glossary.md#con-4152f2c7c3), [CON-5D64EBC654](../project_glossary.md#con-5d64ebc654)). The sequence is as follows:

1.  **Initiation:** The Beneficiary opens the MealCredit app and navigates to the 'Redeem' tab. The screen displays a large, high-contrast QR code (or barcode) that is automatically refreshed every 60 seconds to prevent replay attacks ([CON-AA83B13877](../project_glossary.md#con-aa83b13877)). The code is cryptographically signed and time-bound.
2.  **Scanning:** The Merchant's POS system ([JNY-356F465DB3](../project_glossary.md#jny-356f465db3)) scans the QR code. The Beneficiary's device immediately detects the scan event via a local Bluetooth Low Energy (BLE) handshake or NFC tap, providing haptic feedback (a single, sharp vibration) to confirm the scan was successful. This local feedback is critical for perceived latency.
3.  **Clearance Feedback:** The app transitions to a 'Processing' state, which must be displayed within 100ms of the scan detection. This state is a full-screen overlay with a subtle, non-distracting animation (e.g., a pulsing ring) and the text 'Confirming with Restaurant...'.
4.  **Success/Failure:**
    *   **Success:** Upon receiving a positive response from the backend (Stripe Issuing virtual card provisioning or HMAC-signed voucher validation), the screen transitions to a 'Success' state. This state displays a large green checkmark, the text 'Payment Confirmed', and the remaining balance. The Beneficiary receives a double-haptic feedback (success pattern). The screen auto-dismisses after 2 seconds, returning to the 'Redeem' tab.
    *   **Failure:** If the transaction fails (e.g., insufficient funds, network error, or merchant decline), the screen transitions to a 'Declined' state. This state displays a red 'X', the text 'Transaction Declined', and a clear, non-technical reason (e.g., 'Insufficient Balance' or 'Network Error'). A 'Retry' button is prominently displayed. The Beneficiary receives a triple-haptic feedback (error pattern).

### 3.3 Latency Optimization and Offline Resilience

To meet the p99 latency target of 250ms (CON-6D5E21557B, CON-7F03CF540E), the following strategies are implemented:

*   **Local State Management:** The app maintains a local cache of the most recent transaction status. If the network is unavailable, the app can display the last known status and queue the transaction for retry when connectivity is restored.
*   **Optimistic UI Updates:** The 'Processing' state is displayed immediately upon scan detection, before the backend response is received. This provides immediate feedback to the user, reducing perceived latency.
*   **Error Handling:** Network errors are handled gracefully with clear, actionable messages. The app will automatically retry the transaction up to 3 times with exponential backoff before displaying a failure state.

## 4. Offline Fallback Interface for Voucher Redemption

This artifact defines the offline fallback interface for the Beneficiary Eligibility & Voucher Redemption Flow ([JNY-E82B8A88D8](../project_glossary.md#jny-e82b8a88d8)). It ensures that the Beneficiary (ACT-ADA6716160) can redeem anonymous culinary credits at a Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) even when network connectivity is lost, adhering to strict data isolation (CON-0A0288EED4) and security requirements ([CON-34312C6DC9](../project_glossary.md#con-34312c6dc9), CON-AA83B13877).

### 4.1 Secure Client-Side Storage Visualization (SecureStore)

The interface must provide clear, accessible feedback regarding the secure storage of offline tokens using the device's SecureStore (CON-34312C6DC9). This visualization is critical for user trust and transparency, ensuring the Beneficiary understands that their anonymous identity and credit balance are protected locally.

*   **Visual Indicator:** A persistent, high-contrast status badge in the top-right corner of the 'Find & Redeem' screen. The badge will display a lock icon and the text 'Offline Mode: Secure'.
*   **Storage Details:** Upon tapping the badge, a modal will appear detailing:
    *   **Token Type:** 'Anonymous Voucher Token (Time-Bound)'
    *   **Storage Location:** 'Device Secure Enclave (SecureStore)'
    *   **Data Isolation:** 'No PII or demographic data stored locally.'
    *   **Expiry:** 'Token valid for [TBD] hours from generation.'
*   **Accessibility:** The modal must be fully navigable via VoiceOver/TalkBack, with all text elements having appropriate `accessibilityLabel` and `accessibilityHint` properties.

### 4.2 Time-Bound Cryptographic Signature Display

The offline voucher must display a time-bound cryptographic signature (CON-AA83B13877) to prevent replay attacks. The UI must present this signature in a scannable format while also providing a human-readable fallback for verification.

*   **Primary Display:** A large, high-contrast QR code centered on the screen. The QR code will encode the signed token payload.
*   **Secondary Display:** Below the QR code, a monospaced, alphanumeric string representing the token's unique identifier. This string will be copyable to the clipboard for manual entry if scanning fails.
*   **Expiry Timer:** A prominent, animated countdown timer next to the QR code, indicating the remaining validity period of the offline token. The timer will turn red when less than 5 minutes remain.
*   **Signature Verification:** The UI will not display the raw cryptographic signature. Instead, it will display a 'Verified' checkmark icon next to the token, indicating that the local SDK has successfully validated the signature against the stored public key.

### 4.3 Intuitive Interaction Paths & Troubleshooting

The offline interface must be intuitive and accessible, requiring no complex technical troubleshooting from the Beneficiary ([CON-387CDD9AEB](../project_glossary.md#con-387cdd9aeb), [CON-FA7A13E601](../project_glossary.md#con-fa7a13e601)).

*   **Empty State:** If no offline token is available, the screen will display a simple, encouraging message: 'Go online to get your meal credit.' with a 'Check Connection' button.
*   **Error State:** If the offline token is expired or invalid, the screen will display: 'This token has expired. Please go online to get a new one.' with a 'Go Online' button.
*   **Merchant Edge Dashboard Integration:** The Merchant POS Integration & Dashboard (sibling artifact) will be designed to accept the offline QR code and validate it upon reconnection. This artifact defers to the Merchant POS Integration & Dashboard for the specific merchant-side validation logic.
*   **Accessibility Compliance:** All interactive elements will meet WCAG 2.1 AA standards, with a minimum touch target size of 44x44 points and sufficient color contrast ratios.

### 4.4 Knowledge Gaps and Assumptions

*   `KNOWLEDGE_GAP: Offline Token Expiry Duration` - The exact time-bound duration for the offline voucher token (e.g., 1 hour, 24 hours) must be established by the Product Owner, based on risk tolerance and user experience requirements.
*   `KNOWLEDGE_GAP: Merchant Offline Validation Logic` - The specific mechanism by which the Merchant POS Integration & Dashboard validates the offline token upon reconnection (e.g., batch upload, real-time sync) must be defined in the Merchant POS Integration & Dashboard artifact.
*   `ASSUMPTION: SecureStore Availability` - It is assumed that all target devices (iOS and Android) support the Expo SecureStore API for local, encrypted key-value storage. This is a standard capability for modern mobile devices.
*   `ASSUMPTION: QR Code Scanning Capability` - It is assumed that the Beneficiary's device has a functional camera and that the Expo Camera API can be used to scan the QR code for validation by the merchant.

### 4.6 Mobile Accessibility (Expo/React Native)

The mobile interface must prioritize dignity and anonymity. All UI elements must be accessible via VoiceOver (iOS) and TalkBack (Android).

#### 5.1.1. Semantic Landmarks and Labels

*   **Beneficiary Dashboard:** The main screen must use `accessibilityRole="header"` for the greeting and `accessibilityRole="button"` for the 'Find & Redeem' CTA. The balance display must use `accessibilityLabel="Available balance: [amount] credits"` to ensure screen readers announce the value without ambiguity.
*   **Restaurant List:** Each restaurant card must have a unique `accessibilityIdentifier` and `accessibilityLabel` that includes the restaurant name, distance, and dietary flags (e.g., "Restaurant A, 0.5 miles, Vegetarian options available").
*   **QR Code:** The QR code for redemption must have `accessibilityLabel="Scan this code to redeem credits"` and `accessibilityHint="Point your camera at the code"`. It must also have a fallback `accessibilityLabel="Manual entry code: [code]"` for users who cannot scan.

#### 5.1.2. High Contrast and Color Independence

*   **Color Contrast:** All text and interactive elements must meet a minimum contrast ratio of 4.5:1 against their background (WCAG AA). This is critical for users with low vision (CON-68497304B1).
*   **Color Independence:** No information should be conveyed by color alone. For example, error states must include an icon and text, not just a red border. Success states must include a checkmark icon and text.
*   **Dynamic Type:** The UI must support dynamic type scaling up to 200% without breaking layout. Text must wrap and buttons must expand to accommodate larger font sizes.

#### 5.1.3. Touch Target Size

*   All interactive elements (buttons, links, toggles) must have a minimum touch target size of 44x44 points (iOS) or 48x48 dp (Android) to accommodate users with motor impairments.

### 4.7 Merchant Edge Dashboard Accessibility (Next.js/Web)

The merchant edge dashboard must support keyboard-only navigation (CON-6C177D0102, [CON-D0DEFC531A](../project_glossary.md#con-d0defc531a)) to ensure that restaurant staff can process redemptions without a mouse.

#### 5.2.1. Keyboard Navigation

*   **Tab Order:** The tab order must follow the visual layout of the page. Logical groups (e.g., 'Scan QR', 'Manual Entry', 'Transaction History') must be navigable via Tab and Shift+Tab.
*   **Focus Indicators:** All focusable elements must have a visible, high-contrast focus indicator (e.g., a 2px solid outline) that is not removed by CSS.
*   **Skip Links:** A 'Skip to Main Content' link must be the first focusable element on the page, allowing keyboard users to bypass the navigation menu.

#### 5.2.2. Screen Reader Compatibility

*   **ARIA Labels:** All interactive elements must have appropriate ARIA labels (e.g., `aria-label="Redeem credits"`).
*   **Live Regions:** Dynamic updates (e.g., 'Redemption successful') must be announced to screen readers using `aria-live="polite"` regions.
*   **Form Labels:** All form inputs must have associated `<label>` elements or `aria-label` attributes.

### 4.8 Implementation Notes

*   **Testing:** Accessibility must be tested with real screen readers (VoiceOver, TalkBack, NVDA) and keyboard-only navigation. Automated tools (e.g., axe-core) are a starting point but not sufficient.
*   **Documentation:** Accessibility guidelines must be documented in the project's design system and shared with all frontend developers.
*   **Continuous Monitoring:** Accessibility compliance must be part of the CI/CD pipeline, with automated checks for contrast ratios and ARIA usage.

This artifact defines the high-fidelity interaction design for the **NGO Operator** (ACT-09E028AEB0) to assign eligibility to a **Beneficiary** (ACT-ADA6716160), and the subsequent **Beneficiary** experience for discovering and redeeming anonymous culinary credits. The design strictly enforces data isolation (CON-0A0288EED4, CON-92F07E31B0), anonymity (CON-B3D71A437D, CON-C22D030D21), and accessibility (CON-68497304B1, CON-6C177D0102).

---

## 5. Validation Criteria

The wireframes clearly show the 'Generate Anonymous Credential' flow, the 'Privacy Mode' toggle, the QR code display, and the fallback manual entry option.
The interaction states (loading, success, error) are defined and accessible.
The design explicitly references the data isolation constraints (CON-0A0288EED4, CON-92F07E31B0) in the accompanying documentation.
The design adheres to WCAG 2.1 AA standards for accessibility.

This artifact defers to the Offline Fallback & Accessibility Interface artifact for the design of the offline redemption flow and the Core Design System & Token Architecture artifact for the specific design tokens and component library used.
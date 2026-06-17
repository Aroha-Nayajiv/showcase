# Recipient Discovery UX

## 1. Recipient Discovery UX: Persona and Primary Journey

### 1.1 Recipient Persona: The Dignified Diner (ACT-DC00FA84DC)
The Recipient is a community member in need of nutritional support who values privacy, autonomy, and social inclusion above all else. They are not seeking charity in the traditional sense; they are seeking the freedom to choose their own meals at standard commercial establishments without stigma or bureaucratic friction.

**Key Characteristics:**
*   **Tech Literacy:** Variable, but assumed to have access to a smartphone (iOS or Android) and basic digital literacy. The interface must be intuitive enough for low-literacy users.
*   **Privacy Sensitivity:** Extremely high. The Recipient will not engage with a platform that requires extensive personal data collection, visible identification, or public acknowledgment of their status.
*   **Primary Goal:** To find a nearby, reputable restaurant where they can enjoy a meal that feels like a normal dining experience, not a handout.
*   **Emotional State:** Often anxious about social judgment. The UX must actively reduce anxiety by normalizing the interaction.

**Accessibility Requirements (CON-ADA1B3458C):**
*   The interface must meet WCAG 2.1 AA standards to support low-vision users relying on screen readers.
*   High-contrast modes and scalable text are mandatory.
*   Voice-over compatibility is critical for all interactive elements.

### 1.2 Primary Journey: Recipient Discovery & Redemption (JNY-76281D3F3C)
This journey outlines the end-to-end experience for the Recipient, from discovering available dining options to successfully redeeming their credits. The focus is on minimizing steps, maximizing clarity, and ensuring absolute anonymity.

#### Step 1: Secure, Anonymous Entry
*   **Action:** The Recipient opens the MealCredit app. No login screen is presented. Instead, the app immediately prompts for a simple, privacy-preserving entry method (e.g., a unique QR code provided by their NGO case worker, or a one-time passcode).
*   **Outcome:** The Recipient is authenticated without creating a persistent account linked to their PII. The system generates a session token for this interaction.
*   **Dignity Check:** The app never asks for name, address, or income verification at this stage.

#### Step 2: Location-Aware Discovery
*   **Action:** The app requests location access (with clear, non-intrusive explanation). Upon granting permission, the Recipient is presented with a map view (or list view) of nearby Merchant Partners (ACT-A14D3CDC5D).
*   **Visuals:** The map displays pins for participating restaurants. Pins are styled to look like standard food delivery app pins, avoiding any "charity" or "discount" iconography that might signal stigma.
*   **Filtering:** The Recipient can filter by:
    *   Distance (e.g., "Within 1 mile")
    *   Cuisine Type (e.g., "Italian", "Asian")
    *   Dietary Flags (e.g., "Vegetarian", "Gluten-Free")
*   **Performance:** The map must load within 2 seconds on 4G networks. Cache hit ratio for restaurant search queries must exceed 92% (CON-42B7E9919E).

#### Step 3: Merchant Selection and Credit Verification
*   **Action:** The Recipient taps a restaurant pin to view details (menu highlights, distance, rating). They select "Redeem Credits" for a specific meal.
*   **System Check:** The system queries the Discovery & Allocation Engine (CAP-264DA83096) to verify the Recipient's available credit balance and ensures the selected merchant is active and accepting credits.
*   **Feedback:** If credits are insufficient, a clear, non-judgmental message appears: "Your current balance covers a meal up to $X. Would you like to see other options?"

#### Step 4: Voucher Generation and Presentation
*   **Action:** Upon confirmation, the system generates a single-use, anonymized virtual card token (Pseudo-AnonymizedRedemption). This token is presented as a visually standard gift card or barcode within the app.
*   **Security:** The token is stored securely on the device using device-level SecureStore with cryptographic signatures to prevent forgery (CON-0346AE051D).
*   **Offline Fallback:** If the device loses connectivity, the app falls back to a cached, scannable QR code/barcode that is compatible with standard, low-tech POS devices (CON-036979982A).

#### Step 5: Frictionless Redemption
*   **Action:** The Recipient presents the barcode/QR code to the Merchant Partner at the POS.
*   **Merchant Interaction:** The merchant scans the code. The POS system validates the token against the central ledger. The transaction clears instantly.
*   **Recipient Experience:** The Recipient receives a simple "Thank You" animation in the app. No receipt is printed or shown that identifies them as a beneficiary. The interaction feels identical to paying with a standard gift card.

### 1.3 Edge Cases and Error Flows

**No Internet Connectivity:**
*   **Scenario:** The Recipient is in a dead zone when attempting to redeem.
*   **Response:** The app displays the last cached voucher. The merchant scans it. The transaction is queued for later validation. If the token is invalid, the merchant is notified to deny the order.

**Insufficient Credits:**
*   **Scenario:** The Recipient's credits have expired or are insufficient for the selected meal.
*   **Response:** The app clearly states the remaining balance and suggests lower-cost options or directs them to their NGO for top-ups. No shame is implied.

**Merchant Out of Stock:**
*   **Scenario:** The Recipient arrives at the restaurant, but their preferred item is unavailable.
*   **Response:** The app allows the Recipient to select an alternative item from the menu. The voucher is dynamically adjusted to the new value. If the new value is lower, the remainder is returned to their pool (if applicable) or forfeited based on policy.

**Accessibility Failure:**
*   **Scenario:** A screen reader user cannot navigate the map.
*   **Response:** The app provides a text-based list view of nearby merchants as an immediate fallback, ensuring the Recipient is not locked out of the discovery process.

### 1.4 Acceptance Criteria

1.  **Discovery UX:** The Recipient can filter participating Merchant Partners (ACT-A14D3CDC5D) by distance, cuisine, and dietary flags within the Discovery & Allocation Engine (CAP-264DA83096) interface.
2.  **Anonymity:** The redemption flow generates a single-use token that contains no PII, ensuring absolute anonymization (CON-9DEA275205) during the transaction with the Merchant Partner.
3.  **Offline Resilience:** The app successfully generates and displays a scannable offline fallback token (CON-036979982A) when network connectivity is lost, compatible with standard POS scanners.
4.  **Security:** The offline token is cryptographically signed and stored in device-level SecureStore (CON-0346AE051D) to prevent forgery or tampering.
5.  **Partial Payments:** The system supports partial payment logic, allowing the Recipient to cover the remaining balance of a meal using an alternative payment method if their MealCredit balance is insufficient.

### 1.5 Knowledge Gaps

*   **KNOWLEDGE_GAP:** The specific offline token validity period (e.g., 24 hours, 7 days) is not established in the project requirement. The Product Owner must ratify the specific numeric target to close this gap.
*   **KNOWLEDGE_GAP:** The exact discovery radius default (e.g., 1 mile, 5 miles) for the map view is not established. This should be defined based on typical NGO distribution patterns.
*   **KNOWLEDGE_GAP:** The specific POS integration middleware strategy (e.g., Stripe Square vs. custom gRPC adapters) is not ratified. This impacts the offline token format and scanning compatibility.

### 1.6 Follow-Up Questions

*   What offline token validity period is binding for this record class?
*   What discovery radius default is required for the initial metropolitan footprints?
*   Which POS integration middleware strategy is ratified for the MVP?
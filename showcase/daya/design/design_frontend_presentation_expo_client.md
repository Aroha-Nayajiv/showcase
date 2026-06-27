# Expo Mobile Client Architecture

This section defines the technical architecture for the Expo mobile client, ensuring secure client-side storage, offline fallback capabilities, and strict adherence to accessibility standards.

### 1.1 Core Storage Mechanism: expo-secure-store

All sensitive cryptographic material and beneficiary identifiers must be stored using `expo-secure-store`. This library provides a secure, hardware-backed abstraction over the underlying operating system's keychain (iOS) and Keystore (Android).

*   **Hardware Backing:** The implementation must enforce hardware-backed encryption where available. This ensures that cryptographic keys are generated and stored within the device's Trusted Execution Environment (TEE) or Secure Enclave, preventing extraction even if the device is rooted or jailbroken.
*   **Access Control:** Access to stored items must be gated by the device's native biometric (FaceID/TouchID) or passcode authentication. The application must not bypass these OS-level security prompts.
*   **Prohibited Storage:** The use of `AsyncStorage`, SQLite, or any plaintext file storage for sensitive data is strictly prohibited. This includes, but is not limited to: offline tokens, cryptographic signing keys, beneficiary legal names, and donor-linked PII.

### 1.2 Offline Token Cryptography and Lifecycle

To support the Beneficiary Eligibility & Voucher Redemption journey ([JNY-E82B8A88D8](../project_glossary.md#jny-e82b8a88d8)) and ensure PCI-DSS Level 1 compliance ([CON-66390130AA](../project_glossary.md#con-66390130aa)), offline tokens must be cryptographically signed and time-bound.

*   **Token Generation:** Offline tokens are generated client-side using the `expo-crypto` library. The token payload consists of a unique transaction ID, a timestamp, and a nonce, signed using an HMAC-SHA256 algorithm with a device-bound secret key.
*   **Token Storage:** The device-bound secret key used for signing is stored exclusively in `expo-secure-store`. The generated token itself (the QR/barcode payload) is transient and displayed to the user; it is not persisted to long-term storage.
*   **Time-Bound Validation:** Tokens must include a validity window (e.g., 15 minutes) to prevent replay attacks. The Merchant POS system will reject tokens older than this window.
*   **Replay Attack Mitigation:** The server-side ledger tracks used transaction IDs. Upon reconnection, offline tokens are reconciled against this ledger. If a token is presented twice, the second attempt is rejected.

### 1.3 Data Isolation and Anonymization

To adhere to FTC guidelines on anonymity ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d)) and strict data isolation ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4)), the client architecture must ensure that beneficiary demographic status and legal names are cryptographically segregated from public-facing data.

*   **PII Segregation:** Beneficiary PII (legal names, demographic status) is never stored in `expo-secure-store` unless explicitly required for identity verification by the NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)). In such cases, it is stored with the highest security level and encrypted with a key derived from the user's biometric.
*   **Anonymized Credits:** Culinary credits are represented by anonymous UUIDs. These UUIDs are stored in `expo-secure-store` and are not linked to PII on the device. The mapping between UUIDs and PII is maintained server-side in the Financial Ledger Data Model (deferred to sibling artifact).
*   **Data Residency:** The client must not cache any data that violates Data Residency and Jurisdictional Compliance ([CON-30EA97016B](../project_glossary.md#con-30ea97016b)). All cached data must be tagged with its jurisdictional origin, and the client must enforce local deletion if the user moves to a non-compliant region.

### 1.4 Security Hardening and Device Integrity

To prevent token theft and cloning, the application must implement device integrity checks.

*   **Root/Jailbreak Detection:** The application must detect rooted or jailbroken devices. If detected, access to `expo-secure-store` must be disabled, and all local tokens must be wiped. The application should display a clear error message to the user.
*   **Emulator Detection:** The application must detect if it is running in an emulator. Emulators are not supported for production use, and the application should refuse to start or restrict functionality.
*   **Key Rotation:** The device-bound secret key must be rotatable. The NGO Operator (ACT-09E028AEB0) must be able to trigger a key rotation via the dashboard, invalidating all tokens signed with the old key.

### 1.5 Accessibility and User Experience

The secure storage architecture must not compromise accessibility ([CON-68497304B1](../project_glossary.md#con-68497304b1), [CON-6C177D0102](../project_glossary.md#con-6c177d0102)).

*   **Biometric Fallback:** If biometric authentication is unavailable (e.g., device does not support it), the application must fall back to a strong passcode, ensuring that security is not bypassed.
*   **Screen Reader Compatibility:** All security prompts (biometric, passcode) must be fully compatible with screen readers and high-contrast modes.
*   **Offline Fallback UI:** The offline fallback interface must be intuitive and accessible, requiring no complex technical troubleshooting from the Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)).

### 1.6 Offline Token Persistence and Reconciliation

To ensure transaction integrity during network outages, the client must manage the lifecycle of offline tokens with strict persistence rules.

*   **Transient Storage:** Offline tokens are generated on-demand and stored in volatile memory (RAM) until they are displayed to the user. They are not persisted to disk to prevent unauthorized access via file system enumeration.
*   **Reconnection Logic:** Upon reconnection, the client must synchronize offline transactions with the server. The server maintains a ledger of used nonce values. If a nonce is presented again, the transaction is rejected as a replay attempt.
*   **Conflict Resolution:** In the event of a double-spend attempt (e.g., token presented at two different POS terminals simultaneously), the server-side ledger acts as the source of truth. The first validated transaction is committed; subsequent attempts are rejected, and the client is notified to display a failure state to the Beneficiary.

### 2.1 Cryptographic Token Structure

To protect against replay attacks and maintain anonymity, offline tokens must be deterministic, time-bound, and cryptographically signed. The token payload is structured as follows:

| Field | Type | Description | Constraint |
| :--- | :--- | :--- | :--- |
| `nonce` | UUIDv4 | Unique identifier for this specific redemption attempt. | Must be generated client-side using `expo-crypto`. |
| `timestamp` | ISO 8601 | The exact time the token was generated. | Must be within the validity window (see 2.3). |
| `credit_amount` | Decimal | The fractional credit value being redeemed. | Must match the merchant's POS request or a predefined menu item. |
| `merchant_id_hash` | SHA-256 | Hashed identifier of the target merchant. | Prevents token reuse across different merchant locations. |
| `signature` | HMAC-SHA256 | Cryptographic signature of the above fields. | Signed with the device-bound secret key (see 2.2). |

**Token Encoding:** The payload fields are concatenated into a JSON string, then Base64URL-encoded to create a compact, URL-safe string optimized for QR code density. This ensures fast scanning and minimal data entry errors.

### 2.2 Secure Client-Side Storage

Sensitive cryptographic keys and tokens must never be stored in plain text or accessible via the JavaScript runtime.

*   **Storage Mechanism:** Use `expo-secure-store` for all sensitive data. This leverages the underlying OS keychain (iOS) or Keystore (Android), providing hardware-backed encryption.
*   **Key Management:** The device-bound secret key used for HMAC signing is generated during the Beneficiary Eligibility phase (JNY-E82B8A88D8) and stored exclusively in `expo-secure-store`. It is never transmitted to the server after initial provisioning.
*   **Data Isolation:** No raw PII, donor-linked data, or unhashed beneficiary names are stored on the device. Only the nonce, timestamp, `credit_amount`, and `merchant_id_hash` are included in the token payload.

### 2.3 Time-Bound Validation and Replay Protection

To prevent replay attacks, tokens are strictly time-bound and single-use.

*   **Validity Window:** Tokens are valid for a maximum of 15 minutes from generation. The merchant's POS system will reject any token with a timestamp older than this window.
*   **Clock Skew Tolerance:** A tolerance of +/- 2 minutes is allowed for device clock skew, but significant skew will flag the transaction for manual audit.
*   **Replay Detection:** Upon reconnection, the client synchronizes offline transactions with the server. The server maintains a ledger of used nonce values. If a nonce is presented again, the transaction is rejected as a replay attempt.
*   **Revocation:** If a device is reported lost or compromised, the NGO Operator (ACT-09E028AEB0) can trigger a remote key rotation via the dashboard, invalidating all tokens signed with the compromised key.

### 2.4 Merchant POS Integration

The Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) POS system must be capable of:

1.  **Scanning:** Reading the Base64URL-encoded QR code.
2.  **Decoding:** Parsing the JSON payload.
3.  **Validation:** Verifying the HMAC signature using a shared secret (provided via the Stripe Issuing Proxy Contract) and checking the timestamp against the current server time.
4.  **Submission:** Sending the validated token to the server for final ledger reconciliation upon reconnection.

This artifact's [concern] defers to [Stripe Issuing Proxy Contract] for the shared secret provisioning mechanism; see that artifact for the full treatment.

### 3.1 Core Accessibility Principles & Standards

The MealCredit mobile application (Expo v51 / React Native Fabric) and Wallet passes must adhere to WCAG 2.1 Level AA standards. The following principles are mandatory:

1.  **Perceivable:** Information and user interface components must be presentable to users in ways they can perceive. This includes providing text alternatives for non-text content, providing captions and alternatives for multimedia, and creating content that can be presented in different ways without losing meaning.
2.  **Operable:** User interface components and navigation must be operable. This includes making all functionality available from a keyboard, giving users enough time to read and use content, and avoiding content that is known to cause seizures or physical reactions.
3.  **Understandable:** Information and the operation of the user interface must be understandable. This includes making text readable and understandable, making web pages appear and operate in predictable ways, and helping users avoid and correct mistakes.
4.  **Robust:** Content must be robust enough that it can be interpreted by a wide variety of user agents, including assistive technologies.

### 3.2 Screen Reader Compatibility (VoiceOver / TalkBack)

The MealCredit application must provide comprehensive support for iOS VoiceOver and Android TalkBack.

#### 3.2.1. Semantic Labeling

All interactive elements (buttons, links, input fields, cards) must have explicit, descriptive accessibility labels (`accessibilityLabel` in React Native). Default labels like "Button" or "Image" are prohibited.

*   **Beneficiary Dashboard:** The main dashboard must clearly announce the user's current MealCredit balance, recent transaction history, and nearby Merchant (ACT-AF904DCFF9) locations. Example: `accessibilityLabel="Balance: $15.50. Last transaction: Lunch at Joe's Diner, $8.25."`
*   **Voucher Redemption:** The QR code display screen must provide a clear announcement upon loading: `accessibilityLabel="Voucher ready for scan. Valid for 15 minutes."`
*   **Merchant Onboarding:** Forms for Merchant onboarding must have clear, associated labels for each input field, announced before the input field itself.

#### 3.2.2. Dynamic Announcements

Use `AccessibilityInfo` and `AccessibilityEvent` to announce dynamic content changes, such as successful transaction completions, error messages, or updates to the Beneficiary's MealCredit balance. These announcements should be polite (not interruptive) and concise.

#### 3.2.3. Focus Order

The logical focus order for all screens must be intuitive and consistent with the visual layout. Custom focus order (`accessibilityViewIsModal`, `focusable`) must be explicitly defined for complex components like modals, bottom sheets, and custom navigation bars.

### 3.3 High-Contrast Modes & Color Independence

The MealCredit application must function correctly in all system-defined high-contrast modes and color inversion settings.

#### 3.3.1. Color Palette & Contrast Ratios

*   All text and interactive elements must maintain a minimum contrast ratio of 4.5:1 against their background (WCAG AA).
*   The application must not rely solely on color to convey information. For example, error states must use both color (e.g., red) and an icon or text label (e.g., "Error").
*   The design system must define a set of accessible color tokens that are tested against common color blindness simulations (deuteranopia, protanopia, tritanopia).

#### 3.3.2. Dynamic Type & Font Scaling

The application must support dynamic type scaling on iOS and font scaling on Android. Text elements must resize appropriately without breaking the layout or overlapping other elements. The maximum supported font size must be tested up to 200% scaling.

### 3.4 Keyboard-Only Navigation & Motor Accessibility

While the primary interface is touch-based, the MealCredit application must support keyboard navigation for users who rely on switch control, voice control, or external keyboards.

#### 3.4.1. Focus Indicators

All focusable elements must have a clear, visible focus indicator (e.g., a high-contrast outline) that is not obscured by other elements.

#### 3.4.2. Touch Target Size

All interactive elements must have a minimum touch target size of 44x44 points (iOS) or 48x48 dp (Android) to accommodate users with motor impairments.

### 3.5 Wallet Pass Accessibility

The MealCredit Wallet passes (Apple Wallet / Google Wallet) must also adhere to accessibility standards.

#### 3.5.1. Pass Content

*   The pass must include a clear, concise description of the credit value and expiration date.
*   The pass must not rely on color alone to indicate status (e.g., active vs. expired).

#### 3.5.2. Pass Interaction

*   Tapping the pass should provide clear feedback (e.g., haptic feedback) and announce the action to screen readers.
*   The pass must be compatible with VoiceOver and TalkBack, providing a clear description of the pass's purpose and value.

### 3.6 Testing & Validation

Accessibility compliance must be validated through a combination of automated and manual testing.

#### 3.6.1. Automated Testing

*   Integrate accessibility linting tools (e.g., `eslint-plugin-jsx-a11y`) into the CI/CD pipeline to catch common accessibility issues early.
*   Use automated accessibility testing tools (e.g., Axe, Lighthouse) to scan the application for WCAG violations.

#### 3.6.2. Manual Testing

*   Conduct manual testing with screen readers (VoiceOver, TalkBack) on both iOS and Android devices.
*   Test with users who have diverse accessibility needs, including visual, motor, and cognitive impairments.
*   Perform keyboard navigation testing to ensure all functionality is accessible without a mouse or touch.

### 3.7 Alignment with Project Concerns

This accessibility architecture directly addresses the following project concerns:

*   **CON-68497304B1:** Ensure the Expo mobile application and Wallet passes are fully compatible with screen readers and high-contrast modes for visually impaired users.
*   **CON-6C177D0102:** Design the merchant edge dashboard to support keyboard-only navigation and low-vision readability standards.
*   **[CON-387CDD9AEB](../project_glossary.md#con-387cdd9aeb):** Ensure offline fallback interfaces are intuitive and accessible without requiring complex technical troubleshooting.
*   **[CON-FA7A13E601](../project_glossary.md#con-fa7a13e601):** Ensure offline fallback interfaces are intuitive and accessible without requiring complex technical troubleshooting.

This architecture ensures that the MealCredit platform is inclusive and accessible to all users, aligning with its mission to decouple food assistance from social stigma.

---

### 4.1 Merchant Onboarding Data Capture (Expo Mobile)

The Expo mobile application serves as the primary interface for Merchant (ACT-AF904DCFF9) onboarding, particularly for initial KYC/AML data collection and POS device registration.

#### 4.1.1. Data Collection Contract

The mobile client must capture and securely transmit the following merchant attributes to the GraphQL Schema & Type Definitions (owned by sibling artifact) for validation:

| Field | Type | Constraint | Source |
| :--- | :--- | :--- | :--- |
| `merchant_legal_name` | String | Non-empty, max 255 chars | User Input |
| `merchant_tax_id` | String | Alphanumeric, length 9-15 | User Input |
| `business_address` | Object | Lat/Long, Street, City, State, Zip | User Input + Geolocation API |
| `pos_device_id` | String | UUIDv4, unique per device | Device Hardware ID |
| `pos_device_model` | String | Enum: Square, Clover, Custom | Device Detection |
| `integration_type` | Enum | API_DIRECT, SDK_INTEGRATED | User Selection |

**KNOWLEDGE_GAP:** `merchant_onboarding_kyc_fields` - `NGO Operator` must establish the exact KYC/AML fields required for merchant onboarding based on jurisdictional compliance (CON-30EA97016B, [CON-5BFA25E8F9](../project_glossary.md#con-5bfa25e8f9)). The current design assumes standard US merchant KYC fields.

#### 4.1.2. Secure Data Transmission

*   All PII collected during onboarding must be encrypted in transit using TLS 1.3.
*   Sensitive fields (e.g., `merchant_tax_id`) must be hashed client-side before transmission if required by PII Segregation & Anonymization Strategy (owned by sibling artifact).
*   The mobile client must use `expo-secure-store` to cache the merchant's session token and POS device credentials securely.

### 4.2 Real-Time POS Clearance and Latency Optimization

To prevent restaurant queue stagnation ([CON-4152F2C7C3](../project_glossary.md#con-4152f2c7c3), [CON-5D64EBC654](../project_glossary.md#con-5d64ebc654)), the client must optimize the clearance flow for low latency.

*   **Pre-Validation:** The client must perform local validation of the token structure and signature before transmission to ensure immediate feedback on malformed requests.
*   **Concurrent Requests:** The client must use parallel HTTP requests for fetching merchant menu data and validating transaction status to minimize round-trip time.
*   **Caching Strategy:** Merchant menu data and static configuration should be cached locally using `expo-secure-store` or `MMKV` to reduce network dependency during peak hours.

### 4.3 Merchant Payout Failure & Error Handling

To support the Merchant Payout Error Handling Flow ([JNY-90B07623FB](../project_glossary.md#jny-90b07623fb)), the client must provide clear feedback on payout status.

*   **Status Polling:** The client must poll the server for payout status updates at defined intervals.
*   **Error Display:** If a payout fails, the client must display a clear error message to the Merchant, including the error code and suggested resolution steps.
*   **Retry Logic:** The client must implement exponential backoff for retrying failed payout status requests.

### 4.4 Validation Criteria

*   **Functional:** Verify that a Merchant can successfully onboard and register their POS device.
*   **Security:** Verify that all onboarding data is encrypted in transit and stored securely.
*   **Performance:** Verify that POS clearance latency meets the target threshold (CON-4152F2C7C3).
*   **Error Handling:** Verify that payout failures are clearly communicated to the Merchant.

This architecture ensures that the MealCredit platform provides a seamless and secure experience for Merchant partners, facilitating efficient transaction processing and payout management.

This section defines the technical architecture for the Expo mobile client, ensuring secure client-side storage, offline fallback capabilities, and strict adherence to accessibility standards. The architecture is designed to support the tripartite social-impact fintech platform (Daya/MealCredit) across three metropolitan footprints (SF, NYC, Chicago).

### 4.1.2. Offline Fallback Token Generation

To support low-latency and high-availability scenarios, the client must generate time-bound, single-use cryptographic tokens for offline redemption.

- **Token Format**: The offline fallback token is an HMAC-SHA256 signed payload containing the transaction amount, timestamp, and nonce.
- **Validity Window**: The token has a strict validity window (e.g., 15 minutes) to prevent replay attacks ([CON-3335D67672](../project_glossary.md#con-3335d67672)).
- **Signature**: The signature is generated using the device-bound secret key stored in `expo-secure-store`.

**KNOWLEDGE_GAP**: The exact format and cryptographic algorithm for the offline fallback token are not fully defined in upstream truth. The current design assumes HMAC-SHA256 with a 15-minute validity window. The `Platform Administrator` must define the exact format and cryptographic algorithm for the offline fallback token.

### 4.2.1. Clearance Request Contract

{
 "request_id": "uuidv4",
 "beneficiary_token": "string (HMAC-SHA256)",
 "merchant_id": "uuidv4",
 "amount": "decimal",
 "timestamp": "ISO 8601",
 "signature": "string (HMAC-SHA256)"
}

- **beneficiary_token**: A time-bound, HMAC-signed token generated by the Beneficiary (ACT-ADA6716160) device, ensuring anonymity and preventing replay attacks (CON-3335D67672).
- **signature**: A client-side signature generated using the merchant's private key stored in `expo-secure-store`, ensuring the request originates from a trusted POS device.

## 4.3. Integration with Transaction & Financial Engine

The Expo mobile client integrates with the Transaction & Financial Engine via the gRPC Service Contracts & Definitions (owned by sibling artifact). The integration must ensure:

1. **Low Latency**: POS clearance requests must be processed within 150ms ([CON-06232374D9](../project_glossary.md#con-06232374d9)) to prevent queue stagnation at the restaurant.
2. **Idempotency**: The mobile client must include a unique `request_id` to handle network retries without double-charging.
3. **Offline Fallback**: If the mobile client loses connectivity, it must queue clearance requests locally using `expo-secure-store` (with encryption) and sync when connectivity is restored. The offline fallback QR/barcode token (CON-3335D67672) must be used in this scenario.

**ASSUMPTION**: `offline_fallback_token_format` - `Platform Administrator` must define the exact format and cryptographic algorithm for the offline fallback token. The current design assumes an HMAC-SHA256 signed token with a 15-minute validity window.

## 5. Beneficiary Eligibility & Voucher Redemption Architecture

This section defines the client-side architecture for the Expo mobile application (Fabric architecture) governing the Beneficiary journey. It details the data models for anonymous credit distribution, the offline-first voucher redemption flow, and the integration with the Dispute Resolution & Chargeback Management capability.

### 5.1 Beneficiary Eligibility & Onboarding Data Model

The client must manage the state of a Beneficiary's (ACT-ADA6716160) eligibility as determined by the NGO Operator (ACT-09E028AEB0). This data is highly sensitive and must be treated as such.

**Data Model: BeneficiaryProfile**
- **beneficiary_id**: UUIDv4. Client-side stable identifier for the local device session.
- **ngo_id**: UUIDv4. Reference to the governing NGO Operator (ACT-09E028AEB0).
- **eligibility_status**: Enum `[PENDING, APPROVED, SUSPENDED, REVOKED]`.
- **credit_pool_id**: UUIDv4. Reference to the specific anonymous credit pool this beneficiary is allocated to.
- **last_sync_timestamp**: ISO 8601. Timestamp of the last successful synchronization with the server.
- **local_encrypted_pii_hash**: String. A cryptographic hash of the beneficiary's PII, stored locally to verify identity without exposing raw data. Raw PII is never stored on the device.

**Integration Note**: The `ngo_id` and `eligibility_status` are authoritative sources of truth managed by the NGO Operator (ACT-09E028AEB0) and the Access Control & Multi-Tenant Isolation artifact. The client must defer to the server for the final determination of eligibility.

### 5.2 Anonymous Credit Distribution & Wallet State

The core mission is to decouple food assistance from social stigma. The client must manage fractional, anonymous culinary credits.

**Data Model: CreditWallet**
- **wallet_id**: UUIDv4. Unique identifier for the beneficiary's credit wallet.
- **available_balance**: Decimal. The current available balance in fractional units.
- **pending_balance**: Decimal. Credits that have been allocated but not yet fully cleared.
- **currency_code**: String. Always USD (or local equivalent based on metro footprint: SF, NYC, CHI).
- **last_transaction_id**: String. The ID of the most recent transaction for local reconciliation.

**Offline-First Token Generation**:
To support the offline fallback QR/barcode token mechanism (CON-3335D67672), the client must generate time-bound, single-use cryptographic tokens.

**Data Model: OfflineToken**
- **token_id**: UUIDv4. Unique identifier for the token.
- **amount**: Decimal. The value of the credit being redeemed.
- **timestamp**: ISO 8601. The time the token was generated.
- **nonce**: String. A unique random value to prevent replay attacks.
- **signature**: String. An HMAC-SHA256 signature of the payload, signed with a device-bound secret key stored in `expo-secure-store`.
- **expiry_window**: Integer. The validity window in seconds (e.g., 900 seconds / 15 minutes).

**Security Constraint**: The device-bound secret key used for signing OfflineToken objects must be stored exclusively in `expo-secure-store` ([CON-34312C6DC9](../project_glossary.md#con-34312c6dc9)). No raw card data or PII may ever touch the client's JavaScript runtime or local storage outside of this secure enclave.

### 5.3 Voucher Redemption Flow (POS Integration)

The redemption flow must be intuitive and accessible (CON-387CDD9AEB) while ensuring strict data isolation (CON-0A0288EED4).

**Flow Steps**:
1. **Initiation**: Beneficiary selects a restaurant (Merchant Partner) and items. The client calculates the total amount.
2. **Token Generation**: The client generates an OfflineToken if offline, or requests a real-time Stripe Issuing virtual card token if online. The decision to use offline vs. online routing is deferred to the `Stripe Issuing Proxy Contract` artifact.
3. **Presentation**: The token is displayed as a QR code or barcode. The UI must be fully compatible with screen readers and high-contrast modes (CON-68497304B1).
4. **Scanning**: The Merchant's POS system scans the token.
5. **Validation**:
   - **Online**: The POS sends the token to the server for immediate validation and deduction.
   - **Offline**: The POS validates the cryptographic signature locally. The transaction is queued for later reconciliation.
6. **Confirmation**: The client receives a confirmation (or queued acknowledgment) and updates the local CreditWallet state.

**Accessibility Requirement**: The redemption UI must support keyboard-only navigation and low-vision readability standards (CON-6C177D0102). All interactive elements must have appropriate ARIA labels.

### 5.4 Dispute Resolution & Chargeback Management Integration

The client must support the Beneficiary-Platform Dispute Flow ([JNY-2B038C9362](../project_glossary.md#jny-2b038c9362)) and Merchant-Beneficiary Refund Flow ([JNY-E5F45D37C6](../project_glossary.md#jny-e5f45d37c6)).

**Data Model: DisputeRecord**
- **dispute_id**: UUIDv4. Unique identifier for the dispute.
- **transaction_id**: String. Reference to the original transaction.
- **status**: Enum `[OPEN, UNDER_REVIEW, RESOLVED, CLOSED]`.
- **initiator**: Enum `[BENEFICIARY, MERCHANT, PLATFORM]`.
- **reason_code**: String. Coded reason for the dispute (e.g., ITEM_NOT_RECEIVED, WRONG_AMOUNT).
- **evidence**: Array of Strings. URLs or local paths to uploaded evidence (e.g., photos, receipts).
- **created_at**: ISO 8601.
- **resolved_at**: ISO 8601 (nullable).

**Integration Note**: The DisputeRecord is managed by the Dispute Resolution & Chargeback Management capability ([CAP-DISPUTE-RESOLUTION-CHARGEBACK-MANAGEMENT](../project_glossary.md#cap-dispute-resolution-chargeback-management)). The client must provide a UI for beneficiaries to initiate disputes and view their status. The client must defer to the server for the final adjudication of disputes.

**Refund Handling**:
If a refund is initiated by the Merchant, the client must update the CreditWallet balance upon receiving the refund notification. The client must handle edge cases such as double-spending prevention and voided transactions ([CON-61EC670500](../project_glossary.md#con-61ec670500)) by validating the transaction state against the server before applying local updates.

### 5.5 Data Residency & Compliance Constraints

The client must ensure that all beneficiary-related data is classified as 'Highly Sensitive' (CON-<timestamp>).

**Constraints**:
- **No PII Caching**: The client must not cache any PII (legal names, demographic status) in `AsyncStorage` or local SQLite databases.
- **Anonymized Analytics**: Any analytics data sent to the server must be anonymized. The client must use UUIDv4 mapping to correlate donor impact receipts with beneficiary redemption events without linking PII ([CON-23A501C051](../project_glossary.md#con-23a501c051)).
- **Data Retention**: The client must adhere to strict data retention policies for donor transaction history vs. anonymous redemption analytics ([CON-4820FAD5A9](../project_glossary.md#con-4820fad5a9)). Local data must be purged according to the server's retention policy.

### 5.6 Knowledge Gaps & Assumptions

- **KNOWLEDGE_GAP**: The exact API contract for the `Stripe Issuing Proxy` to request real-time virtual card tokens is not defined in this artifact. The client must defer to the `Stripe Issuing Proxy Contract` artifact for the specific request/response schema.
- **KNOWLEDGE_GAP**: The specific error codes and retry logic for the `Dispute Resolution & Chargeback Management` capability are not defined. The client must defer to the `Dispute Resolution & Chargeback Management` artifact for the specific error handling strategy.
- **ASSUMPTION**: The `expo-secure-store` library is available and supports hardware-backed encryption on all target devices (iOS/Android). Evidence needed: Confirmation of target device OS versions and hardware capabilities.
- **ASSUMPTION**: The offline fallback QR/barcode token validation logic is implemented on the Merchant's POS system. The client is responsible only for token generation and presentation. Evidence needed: Confirmation of POS system capabilities and integration requirements.
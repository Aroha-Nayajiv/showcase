# Frontend & Presentation Layer Design

### 1.2 State Management for Anonymous Credit Distribution

The client manages a local state machine for the credit balance, synchronized with the server via optimistic updates.

#### 1.3.1 State Model
CreditState:
 `balance: number`: The current anonymous credit balance.
 `lastSyncTimestamp: number`: For conflict resolution.
 `isEligible: boolean`: Derived from the eligibility check.
RedemptionState:
 `status: 'idle' | 'processing' | 'success' | 'failed' | 'offline'`.
 `pendingTransactionId: string | null`: For optimistic rollback.

#### 1.3.2 Synchronization Strategy
Optimistic UI: When a user initiates a redemption, the CreditBalanceCard immediately deducts the amount. If the API call fails, the UI reverts the balance.
Offline Resilience: If the network is unavailable, the client switches to Offline Mode. The POSInteractionView generates a time-bound cryptographic token (deferred to Offline Cryptographic Token Verification). The token is stored in SecureStore ([CON-34312C6DC9](../project_glossary.md#CON-34312C6DC9)) to prevent theft.
Reconciliation: Upon reconnection, the client sends a reconciliation request to the API Orchestration Layer to resolve any pending offline transactions.

### 1.3 Integration with Client Interface Layer (SUR-43E71C4E2B)

The client interacts with the Client Interface Layer ([SUR-43E71C4E2B](../project_glossary.md#SUR-43E71C4E2B)) through a typed service layer.

ClientInterfaceService:
 `fetchEligibility(userId: string): Promise<EligibilityResponse>`: Fetches the user's eligibility status.
 `initiateRedemption(amount: number, merchantId: string): Promise<RedemptionInitiationResponse>`: Starts the redemption process.
 `submitDispute(disputeData: DisputePayload): Promise<DisputeSubmissionResponse>`: Submits a dispute for the Beneficiary-Platform Dispute Flow ([JNY-2B038C9362](../project_glossary.md#JNY-2B038C9362)).

### 1.4 Quality & Compliance Checklist

 [ ] Data Isolation: No PII is rendered in the UI state or logs.
 [ ] Accessibility: All interactive elements have accessibilityLabel and accessibilityRole.
 [ ] Offline Resilience: The client handles network failures gracefully with optimistic updates and offline tokens.
 [ ] Security: Sensitive data is stored in SecureStore (CON-34312C6DC9).
 [ ] Performance: Virtualized lists are used for large datasets to maintain CHR > 92% ([CON-527BFA6796](../project_glossary.md#CON-527BFA6796)).

---

### 2.1 Architectural Surface & Integration Boundary

The Merchant Edge Dashboard operates as a client-side application within the Next.js framework, serving as the primary presentation layer for the Merchant ([ACT-AF904DCFF9](../project_glossary.md#ACT-AF904DCFF9)) and NGO Operator ([ACT-09E028AEB0](../project_glossary.md#ACT-09E028AEB0)) roles. It does not process financial transactions directly; instead, it acts as a stateful presentation shell that delegates all data mutations and sensitive operations to the API Orchestration Layer ([SUR-85E4A5B6E7](../project_glossary.md#SUR-85E4A5B6E7)).

Integration Contract with API Orchestration Layer (SUR-85E4A5B6E7):
The dashboard communicates exclusively via RESTful or GraphQL endpoints exposed by the API Orchestration Layer. The frontend is strictly decoupled from business logic, relying on the API layer for:
1. Authentication & Authorization: Token validation and role-based access control (RBAC) enforcement.
2. Data Fetching: Real-time retrieval of merchant inventory, redemption logs, and payout statuses.
3. State Mutation: Submission of merchant profile updates, payout account details, and dispute responses.

Boundary Note: The specific API endpoint paths, request/response schemas, and error codes are defined in the sibling artifact `API Surface & Contract Design`. This artifact assumes the existence of a standardized error envelope (e.g., `{ code: string, message: string, details?: object }`) for consistent UI error handling.

### 2.2 React Component Structure & Hierarchy

The component tree is organized by functional domain to ensure maintainability and testability. All components must be accessible by default, utilizing semantic HTML5 elements and ARIA (Accessible Rich Internet Applications) attributes where native semantics are insufficient.

#### 2.2.1 Core Layout & Shell
DashboardLayout: The root container managing the global state (e.g., user session, theme). It enforces the keyboard navigation focus trap and manages the responsive grid system.
SidebarNavigation: A collapsible navigation menu. Must support `tabindex="0"` and `role="navigation"`. Each link must have a unique id for programmatic focus management.
TopBar: Contains the user profile dropdown, notification bell, and global search. Must include aria-label for all icon-only buttons.

#### 2.2.2 Merchant Operations Components
MerchantDashboardHome: The landing view displaying key metrics (e.g., Daily Redemption Volume, Pending Payouts). Data is fetched via a custom hook useMerchantMetrics.
RedemptionHistoryTable: A data grid component displaying past transactions. Must support keyboard sorting (`Shift+Arrow`), row selection (Space), and pagination (Arrow keys). Implements virtualization for large datasets to maintain performance.
PayoutManagementPanel: A form-based component for managing Stripe Connected Account details. Integrates with Stripe Elements for secure input of sensitive banking information, ensuring no PII or financial data is stored in local state or localStorage.
DisputeResolutionCenter: A workflow component for the Merchant (ACT-AF904DCFF9) to respond to disputes initiated by Beneficiaries ([ACT-ADA6716160](../project_glossary.md#ACT-ADA6716160)). Includes a file upload interface for evidence submission, with strict client-side validation for file types and sizes.

#### 2.2.3 NGO Governance Components
- NGOOperatorDashboard: A specialized view for NGO Operators (ACT-09E028AEB0) to monitor merchant performance and compliance.
- BeneficiaryRedemptionAnalytics: A charting component visualizing redemption trends. Must be accessible via data tables for screen readers, providing an alternative to visual charts.

### 2.3 Keyboard-Only Navigation & Accessibility (WCAG 2.1 AA)

To meet the requirement for keyboard-only navigation and low-vision readability ([CON-6C177D0102](../project_glossary.md#CON-6C177D0102), [CON-D0DEFC531A](../project_glossary.md#CON-D0DEFC531A)), the following standards are enforced:

1. Focus Management:
A global FocusTrap component ensures that focus never escapes modal dialogs or sidebars.
Focus indicators must be visible and high-contrast (minimum 3:1 contrast ratio against adjacent colors).
The useFocusManager custom hook provides utilities for programmatically moving focus after asynchronous operations (e.g., form submission).

2. Keyboard Shortcuts:
`Alt+1` to `Alt+9`: Quick navigation to primary sidebar sections.
Escape: Closes modals, dropdowns, and clears temporary search states.
Tab / `Shift+Tab`: Standard navigation through interactive elements.

3. Screen Reader Support:
All interactive elements must have descriptive aria-label or aria-labelledby attributes.
Live regions (`aria-live="polite"`) are used to announce dynamic content updates (e.g., "Redemption successful") without interrupting the user's current task.
Images and icons must have alt text or `role="img"` with aria-label.

4. Low-Vision Readability:
The UI must support a minimum font size of 16px for body text.
All text must scale up to 200% without loss of content or functionality.
Color is never the sole means of conveying information (e.g., error states must include icons and text labels in addition to red color).

### 2.4 State Management & Data Flow

Server State: Managed via a lightweight data-fetching library (e.g., React Query or SWR) to handle caching, revalidation, and background updates. This ensures that the UI reflects the most recent data from the API Orchestration Layer without unnecessary re-renders.
Client State: Managed via React Context or a lightweight state management library (e.g., Zustand) for global UI state (e.g., theme, user preferences, modal visibility). Sensitive data (e.g., payment tokens) is never stored in client state.
Optimistic Updates: For non-critical actions (e.g., toggling a notification preference), the UI updates immediately before the API response is received, providing a responsive user experience. Rollback is handled on error.

### 2.5 Error Handling & User Feedback

Network Errors: Displayed via a global ErrorBoundary component that provides a "Retry" button. Specific error codes (e.g., 401, 403, 500) trigger tailored user messages.
Form Validation: Client-side validation provides immediate feedback on input errors (e.g., invalid email format). Errors are announced to screen readers via aria-describedby.
Loading States: Skeleton screens are used for initial data loading to reduce perceived latency. Spinners are used for asynchronous actions (e.g., form submission).

### 2.6 Knowledge Gaps & Assumptions

KG-001 | KNOWLEDGE_GAP | Specific API endpoint paths and request/response schemas for merchant operations. | API Surface & Contract Design | API Surface & Contract Design artifact
KG-002 | KNOWLEDGE_GAP | Specific Stripe Elements integration details for secure banking data input. | Stripe Issuing Proxy Contract | Stripe Issuing Proxy Contract artifact
KG-003 | KNOWLEDGE_GAP | Specific design tokens (colors, spacing, typography) for the UI theme. | Design System / UI Kit | Design System documentation
KG-004 | KNOWLEDGE_GAP | Specific accessibility audit tooling and reporting requirements. | Compliance & Security | SOC2 Type II audit requirements

Assumption: The API Orchestration Layer (SUR-85E4A5B6E7) provides a consistent error envelope format for all API responses. This assumption is necessary for implementing a unified error handling strategy in the frontend.

Assumption: The project will use a standard React state management library (e.g., React Query) for server state. This assumption is based on industry best practices for Next.js applications and ensures efficient data fetching and caching.

### 2.7 Deliverable Summary

This design provides a complete, implementable contract for the Merchant Edge Dashboard. It defines the component structure, accessibility requirements, and integration points with the API Orchestration Layer. The design is grounded in project truth, specifically addressing the requirements for keyboard-only navigation, low-vision readability, and secure handling of sensitive data. It defers to sibling artifacts for API contracts, Stripe integration details, and design tokens, ensuring a single source of truth across the project.

---

### 3.1 Secure Offline Token Storage (SecureStore)

To support the offline fallback QR/barcode token system and ensure seamless POS interactions, the client must securely persist authentication and session tokens. Raw tokens must never be stored in plain text or accessible via standard AsyncStorage, which is vulnerable to device-level extraction.

Implementation Contract:
Storage Mechanism: Utilize expo-secure-store for all token persistence. This leverages the native Keychain (iOS) and Keystore (Android) APIs, ensuring tokens are encrypted at rest and bound to the device's hardware security module where available.
Token Lifecycle:
Access Tokens: Stored immediately upon successful authentication via the setItemAsync method. Must be tagged with a secure key identifier derived from the user's session context.
Refresh Tokens: Stored with a longer TTL, but subject to rotation upon each access token refresh. Rotation events must trigger an immediate overwrite of the stored value to prevent replay attacks.
Offline Voucher Tokens: If the system implements deterministic HMAC-signed fallback vouchers (as per `Offline Cryptographic Token Verification` sibling artifact), the private signing key or seed material must be stored in SecureStore and never exposed to the JavaScript runtime.
Security Constraints:
requiresBiometrics and requiresDeviceCredentials must be set to true for all SecureStore operations to ensure that token retrieval requires active user authentication (FaceID, TouchID, or PIN) on the device.
Tokens must be cleared from SecureStore immediately upon user logout or when the application detects a security event (e.g., jailbreak detection).

Knowledge Gap: The specific token rotation policy (e.g., absolute maximum lifetime of refresh tokens) must be established by the `Access Control & Multi-Tenant Isolation` artifact to ensure alignment with SOC2 Type II evidence requirements.

### 3.2 Cryptographic Hashing Layers for Beneficiary Data

To adhere to the project's mandate for absolute anonymization and to prevent de-anonymization attacks, beneficiary demographic status and legal names must be cryptographically segregated from public-facing data. The client must never store or transmit raw PII in a way that can be linked back to the individual without the NGO Operator's explicit, audited intervention.

Implementation Contract:
Data Classification: All beneficiary-related data must be classified as 'Highly Sensitive'. The client application must enforce a strict data minimization principle, only caching data necessary for the immediate user journey (e.g., current voucher balance, recent transaction history).
Hashing Strategy:
Local Hashing: For any local analytics or debugging purposes that require user identification, the client must generate a UUIDv4 mapping. This mapping must be stored locally in an encrypted, isolated storage container (e.g., a separate SecureStore namespace or an encrypted SQLite database) and must never be transmitted to the server in plain text.
Server-Side Correlation: The client must rely on the server to correlate donor impact receipts with beneficiary redemption events. The client should only transmit hashed identifiers or anonymous session tokens to the `Transaction & Financial Engine`.
Memory Safety:
Sensitive data objects must be explicitly nullified from memory after use. JavaScript's garbage collection is non-deterministic; therefore, developers must implement explicit cleanup routines to overwrite sensitive variables with null or random bytes before they go out of scope.
Screens displaying beneficiary information must implement dynamic screen capture prevention (e.g., react-native-screen-capture-prevention) to mitigate risks from malicious screen-recording apps.

Assumption: The specific hashing algorithm (e.g., SHA-256, SHA-3) and salt management strategy are assumed to be defined by the `PII Segregation & Anonymization Strategy` sibling artifact. This design defers to that artifact for the exact cryptographic primitives.

### 3.3 Protection Against Token Theft and Cloning

To prevent token theft or cloning, the client architecture must implement multi-layered defenses that bind tokens to the device's unique hardware identity and detect tampering.

Implementation Contract:
Device Fingerprinting:
The client must generate a unique, persistent device fingerprint using a combination of hardware identifiers (e.g., Android ID, IDFV on iOS) and cryptographic keys generated on first launch. This fingerprint must be stored in SecureStore and included in all API requests as a X-Device-Id header.
The server must validate this fingerprint against known good devices. Any mismatch or new device detection must trigger a security review and potential token invalidation.
Jailbreak/Root Detection:
The application must implement runtime checks to detect if the device is jailbroken (iOS) or rooted (Android). If a compromised environment is detected, the application must:
 1. Refuse to launch or enter a restricted "safe mode".
 2. Clear all SecureStore contents immediately.
 3. Log the security event to the `Distributed Tracing & Log Aggregation` system for forensic analysis.
Token Binding:
Access tokens must be bound to the device fingerprint. If a token is used from a different device fingerprint than the one it was issued to, the server must reject the request and invalidate the token. This prevents token replay attacks even if the token is extracted from one device and used on another.
Biometric Re-authentication:
Sensitive operations (e.g., viewing full redemption history, initiating a refund) must require biometric re-authentication. The client must use expo-local-authentication to prompt the user for biometric verification before exposing sensitive data or allowing critical actions.

Knowledge Gap: The specific thresholds for triggering a security review (e.g., number of failed biometric attempts before lockout) must be established by the `Access Control & Multi-Tenant Isolation` artifact to ensure alignment with SOC2 Type II evidence requirements.

### 3.4 Offline Cryptographic Token Verification (POS Fallback)

To ensure POS clearance continuity during network outages, the client must generate and validate offline vouchers using a deterministic cryptographic sequence. This design replaces any reliance on real-time Stripe Issuing virtual card provisioning during offline windows, ensuring the Pseudo-Anonymous Redemption Engine can function without direct cloud dependency.

#### 3.4.1 Token Structure & Replay Prevention
Offline vouchers must contain a mandatory `nonce` and `sequence_number` field to prevent replay attacks and ensure single-use validity. The token structure is defined as follows:

| Field | Type | Description | Constraint |
|---|---|---|---|
| `nonce` | string (UUIDv4) | Unique identifier for the specific redemption event | Must be globally unique per transaction |
| `sequence_number` | integer | Monotonically increasing counter for the device session | Must be stored securely in SecureStore (CON-34312C6DC9) |
| `amount` | number | The credit amount being redeemed | Must match the local balance state |
| `merchant_id` | string | The ID of the Merchant (ACT-AF904DCFF9) accepting the voucher | Must be pre-cached in the local search index |
| `timestamp` | integer | Unix epoch time of token generation | Must be within a 15-minute validity window |
| `signature` | string (HMAC-SHA256) | Cryptographic signature of the above fields | Signed using the device-bound private key |

#### 3.4.2 Token Generation & Validation Flow
1. Generation: When the POSInteractionView detects an offline state, it retrieves the current `sequence_number` from SecureStore, increments it, and generates a new `nonce`. It constructs the payload and signs it using the device-bound private key stored in SecureStore.
2. Display: The signed token is rendered as a QR code or barcode on the RedemptionScreen.
3. Validation: The Merchant (ACT-AF904DCFF9) POS system (or tablet dashboard) scans the token, extracts the fields, and verifies the signature using the public key (which must be distributed to merchants via the API Orchestration Layer). The merchant system checks the `sequence_number` against a local cache of recently seen numbers to prevent replay attacks.
4. Reconciliation: Upon reconnection, the client sends a batch of offline transactions to the API Orchestration Layer. The server validates the `sequence_number` against its own ledger to ensure no double-spending occurred and updates the global credit pool.

Knowledge Gap: The specific public key distribution mechanism for merchants (e.g., periodic push via API, embedded in POS app binary) must be established by the `Merchant Onboarding & POS Integration` artifact.

Assumption: The offline validity window is set to 15 minutes. This assumption balances the need for offline usability with the risk of token theft if a device is lost.

### 3.5 Performance & Caching Strategy

To support the Implied concern: Maintain Cache Hit Ratio (CHR) above 92% for restaurant search queries using the Redis Enterprise Cluster. (CON-527BFA6796), the client must implement a robust local caching strategy.

#### 3.5.1 Local Cache Implementation
- Search Index: The MerchantSearchList component must cache the results of location-aware queries in an encrypted local database (e.g., SQLite). The cache must be invalidated when the user's location changes significantly or when a new search is performed.
- Balance Cache: The CreditBalanceCard must cache the last known balance and sync timestamp. Optimistic updates must be applied to this cache before the API response is received.
- Eviction Policy: The local cache must implement an LRU (Least Recently Used) eviction policy to prevent unbounded memory growth. The maximum cache size must be defined by the `Access Control & Multi-Tenant Isolation` artifact.

Knowledge Gap: The specific maximum cache size (in MB) and the exact LRU eviction threshold must be established by the `Access Control & Multi-Tenant Isolation` artifact.

Assumption: The client will use a standard SQLite wrapper (e.g., react-native-sqlite-storage) for local persistence. This assumption is based on the need for structured, queryable local storage with encryption support.

## 3.4. Integration with Offline Fallback Mechanisms

In the event of network connectivity loss, the client must be able to generate and validate offline fallback QR/barcode tokens. This requires secure client-side cryptographic operations.

Implementation Contract:
Cryptographic Library: The client must use a lightweight, audited cryptographic library (e.g., react-native-quick-crypto or expo-crypto) to perform HMAC-SHA256 operations locally. This library must be integrated with SecureStore to access the private signing key.
Token Generation:
Offline tokens must be time-bound and include a unique nonce/sequence_number to prevent replay attacks. The token structure must be defined by the `Offline Cryptographic Token Verification` sibling artifact.
The client must cache the last N valid offline tokens in SecureStore to allow for limited offline usage even if the device loses connectivity for an extended period.
Validation:
The client must validate the cryptographic signature of any offline token presented for redemption. If the signature is invalid or the token has expired, the client must reject the transaction and prompt the user to reconnect to the network.

Assumption: The specific structure of the offline token (e.g., payload fields, encoding format) is assumed to be defined by the `Offline Cryptographic Token Verification` sibling artifact. This design defers to that artifact for the exact token schema.

### 3.7 Accessibility and Usability Considerations

To ensure the secure client-side storage architecture does not compromise accessibility, the following measures must be implemented:

Implementation Contract:
Screen Reader Compatibility: All security prompts (e.g., biometric authentication, jailbreak detection warnings) must be fully compatible with screen readers (VoiceOver on iOS, TalkBack on Android). Labels and instructions must be clear and concise.
High-Contrast Modes: The application must support high-contrast modes to ensure that security-related UI elements (e.g., warning banners, error messages) are easily readable by users with visual impairments.
Keyboard Navigation: The merchant edge dashboard and any administrative interfaces must support keyboard-only navigation to ensure accessibility for users who cannot use touch interfaces.

### 3.8 Summary of Dependencies and Deferrals

This artifact relies on the following sibling artifacts for specific details:
Access Control & Multi-Tenant Isolation: For token rotation policies and security review thresholds.
PII Segregation & Anonymization Strategy: For specific hashing algorithms and salt management.
Offline Cryptographic Token Verification: For offline token structure and validation logic.
Distributed Tracing & Log Aggregation: For logging security events.

This artifact defers to the `Expo Mobile Client Architecture` sibling artifact for general application structure and lifecycle management.

### 3.9 Quality and Validation Posture

Testability: The SecureStore integration must be mockable in unit tests to allow for testing of token storage and retrieval logic without relying on native device APIs.
Performance: Cryptographic operations must be performed on the native thread to avoid blocking the JavaScript main thread, ensuring smooth UI performance even during complex hashing operations.
Compliance: All storage and hashing mechanisms must be designed to support SOC2 Type II audit evidence, with clear logging of all security events and data access patterns.

---

This artifact defines the presentation layer contracts, state management, and user interaction flows for the MealCredit offline fallback mechanism. It ensures that the Beneficiary (ACT-ADA6716160) can successfully redeem credits at a Merchant (ACT-AF904DCFF9) via QR/barcode scanning even when the Expo mobile client (SUR-43E71C4E2B) lacks network connectivity, while strictly adhering to `Implied concern: Protect against replay attacks on offline fallback QR/barcode tokens using time-bound cryptographic signatures.` ([CON-AA83B13877](../project_glossary.md#CON-AA83B13877)) and `Implied concern: Ensure offline fallback interfaces are intuitive and accessible without requiring complex technical troubleshooting.` ([CON-FA7A13E601](../project_glossary.md#CON-FA7A13E601)).

### 4.2 Offline Token Presentation Contract

The offline voucher is a cryptographically signed, time-bound data structure rendered as a scannable QR/barcode. The presentation layer must render this token with high contrast and accessibility compliance (`Implied concern: Ensure the Expo mobile application and Wallet passes are fully compatible with screen readers and high-contrast modes for visually...` [CON-68497304B1](../project_glossary.md#CON-68497304B1)).

#### 4.2.1. Token Payload Schema (Presentation View)

The frontend must parse and display the following fields from the signed token payload. These fields are derived from the `Financial Ledger Data Model` (sibling artifact) but presented in a simplified, user-centric format.

| Field | Type | Display Logic | Screen Reader Label |
| :--- | :--- | :--- | :--- |
| token_id | UUIDv4 | Hidden in QR data; displayed as a short alphanumeric hash (last 6 chars) for user verification. | "Voucher ID ending in [hash]" |
| amount | Decimal | Formatted as currency (e.g., "$12.50"). Must use large, high-contrast typography. | "Value of [amount]" |
| expiry_timestamp | ISO 8601 | Displayed as relative time (e.g., "Expires in 15 mins") and absolute time. | "Expires at [time]" |
| merchant_id | String | Displayed as "Valid at: [Merchant Name]" (resolved from `Geo-Indexing & Merchant Data Model` sibling). | "Valid at [Merchant Name]" |
| signature_hash | String | Hidden in QR data; displayed as a short alphanumeric hash (last 6 chars) for user verification. | "Security code ending in [hash]" |

#### 4.2.2. QR/Barcode Generation Contract

 Format: QR Code (preferred for density) or Code 128 Barcode. `ASSUMPTION: QR Code is selected for higher data capacity and error correction; Merchant POS systems must support QR scanning.`
 Payload Encoding: The QR data must contain the raw JSON payload of the signed token, including the cryptographic signature, to allow the Merchant's POS system to verify the signature locally or via a lightweight API call.
 Refresh Rate: The QR code must auto-refresh every 60 seconds (or the token's expiry_timestamp, whichever is shorter) to prevent replay attacks. The UI must show a visual countdown timer.

### 4.3 User Interaction Flow & Error Handling

The offline interface must guide the Beneficiary through a simple, linear path with clear, non-technical error messages. Complex technical troubleshooting is explicitly forbidden (CON-FA7A13E601).

#### 4.3.1. Primary Flow: Offline Redemption

1. Initiation: User navigates to "Redeem" screen. System detects `network_status === 'offline'`.
2. Token Generation: System retrieves the latest valid offline token from SecureStore (CON-34312C6DC9). If no valid token exists, display "No Voucher Available" with a simple "Try Again" button.
3. Display: Render the QR code and the `Token Payload Schema` (4.2.1) fields.
4. Scanning: Merchant scans QR code. The UI provides haptic feedback (vibration) and a green checkmark animation upon successful scan detection (via device camera or NFC tap if supported).
5. Confirmation: Display "Voucher Scanned!" with the token_id and amount. Instruct user to wait for the Merchant to confirm completion.
6. Sync: Once `network_status === 'online'`, the system automatically queues the redemption event for the `Financial Reconciliation & Payout Workers` (sibling artifact).

#### 4.3.2. Error States & User-Facing Messages

| Error State | User-Facing Message | System Action |
| :--- | :--- | :--- |
| Token Expired | "This voucher has expired. Please generate a new one." | Disable QR code. Show "Generate New Voucher" button. |
| Token Already Used | "This voucher was already scanned. Please generate a new one." | Disable QR code. Show "Generate New Voucher" button. |
| No Network & No Token | "We couldn't load your voucher. Please check your connection and try again." | Show "Retry" button. |
| Scan Failed (Merchant) | "Scan not recognized. Please ensure the QR code is fully visible and try again." | Keep QR code visible. Show "Help" button (links to simple FAQ). |
| Low Battery | "Low battery detected. Voucher may expire soon." | Show warning banner. Keep QR code visible. |

### 4.4 Security & Integrity Constraints

The offline interface must enforce strict security boundaries to prevent fraud and replay attacks.

 Secure Storage: Offline tokens must be stored in SecureStore (CON-34312C6DC9) on the Expo device. They must NOT be stored in AsyncStorage or local SQLite databases.
 Time-Bound Validity: Each token must have a strict expiry_timestamp (e.g., 15 minutes from generation). The UI must not allow rendering of expired tokens.
 Replay Prevention: The token payload must include a unique nonce or sequence_number that is tracked by the `Offline Cryptographic Token Verification` sibling artifact. Once a token is scanned and verified, it is marked as "used" and cannot be re-scanned.
 Signature Verification: The QR payload must include a cryptographic signature (e.g., HMAC-SHA256) generated by the backend. The Merchant's POS system must verify this signature before accepting the redemption. The frontend does not verify the signature; it only displays the token.

### 4.6 Cross-Reference & Handoff

 To Development: Implement the `Offline Voucher Screen` component in the Expo mobile client. Use the `Token Payload Schema` (4.2.1) for data binding. Integrate with SecureStore for token storage.
 To Design: Provide high-fidelity mockups for the `Offline Voucher Screen` including error states and accessibility modes.
 To QA: Develop test cases for offline redemption flows, including token expiration, replay attacks, and network reconnection scenarios.

This artifact provides a complete, implementable design for the offline fallback interface, ensuring security, usability, and compliance with project requirements.

---

#### 5.1.1. Data Isolation & Tokenization
Expo Mobile Client (Beneficiary/Donor): All payment inputs are captured exclusively via Stripe.js (React Native wrapper). The StripeProvider component initializes the SDK with the platform's publishable key. Card details are tokenized client-side into a PaymentMethod or PaymentIntent ID before any network request is made to the MealCredit API.
Next.js Dashboard (NGO/Platform): Dashboard interactions for funding or payouts utilize Stripe.js embedded elements or hosted payment links. The dashboard never renders raw card forms; it only handles the confirmation of tokenized transactions via Stripe Webhooks.
Data Flow Constraint: The PaymentMethod ID is the only payment-related payload sent to the `API Orchestration Layer`. The API then proxies this ID to the Stripe Issuing Proxy Contract.

#### 5.1.2. Secure Storage & Offline Fallback
- SecureStore Integration: Sensitive session tokens and offline fallback QR/barcode tokens are stored in expo-secure-store, leveraging the device's hardware-backed keystore (Android KeyStore / iOS Keychain). This prevents token theft or cloning (CON-34312C6DC9).
- Offline Token Generation: For low-connectivity scenarios, the frontend generates time-bound, HMAC-signed QR codes using the SecureStore-held private key. These tokens are verified by the Merchant POS via the Offline Cryptographic Token Verification service, ensuring no raw card data is exposed during offline redemption.

### 4.7 Stripe Elements Integration & Payment Processing

The frontend integrates with Stripe Elements to handle all donor funding activations and merchant payout configurations.

#### 5.2.1. Donor Funding Activation (Expo Mobile)
Component: DonationPaymentForm
Integration: Utilizes `useStripe()` hook to render CardElement or PaymentRequestButtonElement.
Flow:
 1. User enters donation amount and selects funding source.
 2. `Stripe.confirmPayment()` is called client-side.
 3. Stripe returns a PaymentIntent status.
 4. Frontend sends payment_intent_id to the `API Orchestration Layer` to trigger the product_donor_funding_activation capability.
- Error Handling: UI displays specific error messages mapped from Stripe's error.code (e.g., card_declined, insufficient_funds) without exposing raw gateway errors.

#### 5.2.2. Merchant Payout Configuration (Next.js Dashboard)
Component: MerchantPayoutSetup
Integration: Uses Stripe.js to collect bank account or card details for Stripe Connect onboarding.
Flow:
 1. NGO Operator initiates onboarding for a Merchant.
 2. Dashboard renders Stripe Elements for KYC and payout method collection.
 3. Details are tokenized and sent to the Stripe Issuing Proxy Contract for Connected Account creation.
- Compliance: Ensures PCI-DSS Level 1 compliance by ensuring zero raw card data touches MealCredit servers, relying entirely on Stripe Elements ([CON-66390130AA](../project_glossary.md#CON-66390130AA)).

### 4.8 UI/UX Accessibility & Multi-Modal Interaction

The frontend design prioritizes accessibility and multi-modal interaction paths to ensure inclusivity for all actor groups.

#### 5.3.1. Accessibility Standards (WCAG 2.1 AA)
Expo Mobile:
Screen Reader Support: All interactive elements (buttons, forms, QR codes) are tagged with accessibilityLabel and accessibilityHint. Color contrast ratios meet WCAG AA standards for visually impaired users (CON-68497304B1).
High-Contrast Mode: The UI theme system supports dynamic high-contrast modes, ensuring readability in low-light or high-glare environments (e.g., restaurant dining areas).
Next.js Dashboard:
Keyboard Navigation: All administrative workflows (NGO governance, merchant onboarding) are fully navigable via keyboard (CON-6C177D0102).
Low-Vision Readability: Typography scales fluidly, and focus states are clearly defined for keyboard-only users.

#### 5.3.2. Multi-Modal Interaction Paths
Voice/Tap/Scan: The mobile client supports multi-modal interaction paths for donation round-up configuration and redemption history ([CON-2D70EDCDEE](../project_glossary.md#CON-2D70EDCDEE)). For example, beneficiaries can redeem credits via:
Tap: NFC tap on supported POS devices.
Scan: QR code scan via camera.
Voice: Voice-command integration for donation configuration (future phase, but UI hooks are reserved).

### 4.9 Performance & Latency Optimization

The frontend is optimized to meet the strict latency requirements for real-time POS clearance.

#### 5.4.1. Latency Targets
- POS Clearance: The mobile client must achieve p99 latency below 250ms for voucher creation and scanning callbacks under 10,000 concurrent connections ([CON-6D5E21557B](../project_glossary.md#CON-6D5E21557B)).
- Webhook Processing: The frontend must handle Stripe Webhook processing latency averaging below 150ms from card tap to merchant ledger entry ([CON-06232374D9](../project_glossary.md#CON-06232374D9)).

#### 5.4.2. Caching & State Management
- Redis Enterprise Cluster: Restaurant search queries and merchant availability data are cached with a Cache Hit Ratio (CHR) target above 92% (CON-527BFA6796). The frontend leverages optimistic UI updates to mask network latency during redemption flows.
- Offline-First Architecture: The Expo client implements a local SQLite database to cache recent transaction history and offline tokens, ensuring intuitive and accessible offline fallback interfaces ([CON-387CDD9AEB](../project_glossary.md#CON-387CDD9AEB)).

### 4.10 Cross-Platform Component Architecture

The frontend utilizes a shared component library to ensure consistency across Expo Mobile and Next.js Dashboard.

#### 5.5.1. Shared Design Tokens
Color Palette: Defined in tokens.css (Next.js) and theme.ts (Expo), ensuring consistent branding and accessibility compliance.
Typography: Fluid typography scales based on device orientation and user preferences.
Icons: Unified icon set using react-native-vector-icons (Expo) and lucide-react (Next.js) for consistent visual language.

#### 5.5.2. Error Handling & User Feedback
Global Error Boundary: Wraps all major views to catch and display user-friendly error messages in case of unexpected failures.
Loading States: Skeleton loaders and spinners are used to indicate loading states, preventing UI freezing and improving perceived performance.
Toast Notifications: Non-intrusive toast notifications provide real-time feedback for successful transactions, errors, and system alerts.

### 4.12 Anonymity & Metadata Sanitization Contract

To satisfy the FTC Anonymity Guidelines and prevent de-anonymization attacks, the frontend must enforce a strict "Zero-PII in Analytics" policy. All telemetry, logging, and user-facing data must be decoupled from donor identity and beneficiary PII.

#### 6.1.1. UUIDv4 Mapping for Analytics

All user interactions must be mapped to ephemeral, non-reversible UUIDv4 identifiers. The frontend must never transmit raw user IDs, email addresses, or donor names to analytics endpoints.

| Beneficiary Identity | Never transmitted to analytics. | Mapped to beneficiary_anon_id (UUIDv4) generated at onboarding. Stored locally in SecureStore. |
| Donor Identity | Never transmitted to analytics. | Mapped to donor_anon_id (UUIDv4) generated at first login. Stored locally in SecureStore. |
| Merchant Identity | Transmitted only for POS context. | Mapped to merchant_id (UUIDv4) retrieved from the Merchant & NGO Operations registry. |
| Transaction Events | Transmitted as event_type + amount + anon_id. | Linked via transaction_uuid (UUIDv4) generated by the Financial Ledger. |
| Device Metadata | Sanitized before transmission. | device_id hashed locally; only os_version and app_version transmitted. |

**Implementation Contract:**
The AnalyticsService must accept only UUIDv4 strings as user identifiers.
Any attempt to log PII (e.g., user_email, full_name) must trigger a silent drop and a local error log.
The `Donor Impact Receipt` must use the donor_anon_id to correlate donations with redemption velocity without revealing donor identity.

#### 6.1.2. Metadata Sanitization Rules

The frontend must strip all sensitive metadata from API requests and analytics payloads.

- **Geolocation:** Only coarse-grained city-level data (e.g., "San Francisco") is transmitted for regional pool analytics. Exact GPS coordinates are never sent to analytics or third-party services.
- **Device Fingerprinting:** Hardware identifiers (IMEI, IDFA, Android ID) are never collected. A random UUIDv4 is generated per app installation and stored in SecureStore.
- **Network Metadata:** IP addresses are stripped from client-side logs. Server-side logging (owned by Distributed Tracing & Log Aggregation) handles IP-based security monitoring.

### 4.13 Expo Mobile Client Architecture

The mobile client is built using Expo (React Native) to support cross-platform deployment (iOS/Android) for Beneficiaries, Donors, and Merchants. It must integrate with the Offline Cryptographic Token Verification system for low-latency POS clearance.

#### 6.2.1. Component Structure

| Component | Responsibility | Dependencies |
| :--- | :--- | :--- |
| SecureWallet | Manages SecureStore for offline tokens and UUIDv4 mappings. | expo-secure-store, uuid library |
| AnonEventTracker | Sanitizes and queues analytics events for batched transmission. | AnalyticsService, NetworkManager |
| POSScanner | Captures QR/barcode tokens and initiates HMAC verification. | react-native-camera, Offline Cryptographic Token Verification |
| DonorDashboard | Displays donation history and impact receipts (anonymized). | Financial Ledger Data Model (read-only) |
| BeneficiaryRedemption | Displays voucher QR codes and redemption history. | SecureWallet, Merchant & NGO Operations |

#### 6.2.2. Offline Token Management

The SecureWallet component must store the offline HMAC key and the last known beneficiary_anon_id in SecureStore.
On app launch, the client must attempt to sync with the API Orchestration Layer to refresh the token cache. If offline, it must fall back to the last valid token.
Token expiration must be handled client-side with a grace period of 5 minutes to prevent POS queue stagnation.

**Replay Prevention Contract:**
To satisfy the Offline Cryptographic Token Verification requirements, every offline voucher token generated by the SecureWallet must include a deterministic nonce and a monotonically increasing sequence_number. These fields are cryptographically bound to the HMAC signature to prevent replay attacks. The POS scanner must validate the sequence_number against the last known valid sequence to ensure token freshness.

### 4.14 Next.js Dashboard Architecture

The web dashboard is built using Next.js for NGO Operators and Platform Administrators. It must provide a high-contrast, keyboard-accessible interface for managing NGO governance and beneficiary offboarding.

#### 6.3.1. Component Structure

| Component | Responsibility | Dependencies |
| :--- | :--- | :--- |
| NGOGovernancePanel | Manages NGO onboarding, offboarding, and compliance status. | Access Control & Multi-Tenant Isolation |
| ComplianceAuditLog | Displays append-only logs of administrative actions. | Distributed Tracing & Log Aggregation |
| AnalyticsOverview | Visualizes DRV, CHR, and Credit Pool Utilization. | Metrics Collection & Alerting Design |
| BeneficiarySearch | Allows NGO Operators to search for beneficiaries by beneficiary_anon_id. | User State & Profile Data Model |
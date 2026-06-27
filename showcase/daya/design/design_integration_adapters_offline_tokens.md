# Offline Cryptographic Token Verification Design

## 1. System Context and Trust Boundaries

The Offline Cryptographic Token Verification system operates across three primary trust domains:

1. **The Beneficiary Device (Expo Mobile App):** A semi-trusted environment. The app generates the token and stores it in SecureStore ([CON-34312C6DC9](../project_glossary.md#con-34312c6dc9)). It is assumed that the device OS is secure, but the user may attempt to extract the token.
2. **The Merchant POS (Scanner/Edge Device):** A semi-trusted environment. The POS device validates the token's cryptographic signature and timestamp locally. It does not have real-time access to the central ledger for every scan but must queue events for eventual consistency.
3. **The Central Ledger (Aurora PostgreSQL):** The source of truth. It performs final reconciliation, double-spend prevention, and nonce tracking.

**Boundary Rule:** No PII (legal names, demographic status) may ever leave the Beneficiary Device or the Central Ledger. The offline token must contain only hashed identifiers and cryptographic proofs.

## 2. Threat Model (STRIDE Analysis)

We apply STRIDE to the offline token lifecycle to identify and mitigate specific attack vectors.

| Threat | Attack Vector | Mitigation |
| :--- | :--- | :--- |
| **Spoofing** | An attacker generates a fake token claiming to be a valid Beneficiary. | **HMAC-SHA256 Signing:** Tokens are signed with a rotating secret key known only to the Central Ledger and distributed to Merchants via secure channels. POS devices reject any token with an invalid signature. |
| **Tampering** | An attacker modifies the token payload (e.g., increasing credit amount). | **Canonical JSON Serialization:** The payload is serialized in a strict, deterministic order before signing. Any change to fields (amount, expiry, nonce) invalidates the HMAC signature. |
| **Repudiation** | A Merchant claims a valid token was rejected or a Beneficiary claims a valid token was not issued. | **Append-Only Ledger:** All token issuance and redemption events are logged to the append-only cryptographic log ([CON-1762EA5021](../project_glossary.md#con-1762ea5021)). The token itself contains a unique nonce that serves as an immutable proof of redemption. |
| **Information Disclosure** | An attacker intercepts the token and extracts PII or donor information. | **Anonymization by Design:** The token payload contains only a hashed_beneficiary_id (UUIDv4 mapping) and credit_amount. No donor PII or beneficiary legal names are included ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4)). |
| **Denial of Service** | An attacker floods the POS with invalid tokens to slow down service. | **Local Validation Caching:** POS devices cache the current signing key and validate signatures locally without network calls. Invalid signatures are rejected instantly. Rate limiting is applied at the POS edge. |
| **Elevation of Privilege** | A low-privilege POS user attempts to approve refunds or void transactions offline. | **Role-Based Access Control (RBAC):** Offline tokens are strictly for redemption. Refund/void operations require a separate, authenticated gRPC call to the central ledger (deferred to Financial Reconciliation & Payout Workers artifact). |

## 3. Offline Token Structure and Cryptographic Integrity

The offline token is a JSON Web Token (JWT)-like structure, signed via HMAC-SHA256. It is designed to be self-contained and verifiable without network access.

### 3.1 Token Payload Schema

The token payload is a JSON object serialized to a canonical string for signing. It contains the minimum necessary data to validate credit availability and prevent double-spending, while strictly avoiding the transmission of PII to satisfy CON-0A0288EED4 (Data Isolation).

| Field | Type | Description | Constraint |
| :--- | :--- | :--- | :--- |
| `v` | String | Protocol version | Must be `"1.0"` |
| `t` | Integer | Issuance timestamp (Unix epoch) | Must be within the valid time window |
| `e` | Integer | Expiration timestamp (Unix epoch) | `e > t` |
| `c` | Number | Credit amount (in smallest currency unit, e.g., cents) | `c > 0` |
| `h` | String | Hashed Beneficiary ID | SHA-256 hash of the internal Beneficiary ID |
| `n` | String | Nonce (Unique Transaction ID) | UUIDv4, generated per token |
| `s` | String | HMAC-SHA256 Signature | Hex-encoded signature of the payload |

**Data Privacy Note:** The `h` field contains a cryptographic hash of the Beneficiary ID, not the ID itself. This ensures that the Merchant's POS system cannot de-anonymize the Beneficiary, aligning with [CON-B3D71A437D](../project_glossary.md#con-b3d71a437d) (FTC Anonymity Guidelines).

### 3.2 HMAC Generation Contract

The signature `s` is generated using HMAC-SHA256 to ensure integrity and authenticity. The secret key is rotated periodically and distributed to Merchants via a secure out-of-band channel (e.g., encrypted email or secure portal).

1. **Canonicalization:** The JSON payload (excluding the `s` field) is serialized to a compact JSON string with keys sorted alphabetically.
2. **Signing:** `HMAC-SHA256(secret_key, canonical_json_payload)`
3. **Encoding:** The resulting byte array is encoded as a lowercase hexadecimal string.

**Example Payload (before signing):**

{
 "c": 500,
 "e": 1715000120,
 "h": "a1b2c3d4e5f6...",
 "n": "550e8400-e29b-41d4-a716-446655440000",
 "t": 1715000000,
 "v": "1.0"
}

### 3.3 Replay Attack Prevention and Time-Window Validation

To satisfy [CON-AA83B13877](../project_glossary.md#con-aa83b13877), the token enforces a strict time window and nonce tracking.

1. **Time-Window Validation:** The POS system must reject any token where `e` is in the past or `t` is more than `ASSUMPTION: 15 minutes` in the future. This prevents the use of stale tokens.
2. **Nonce Tracking:** The `n` field (UUIDv4) must be unique per transaction. The POS system maintains a local cache of recently used nonces (TTL matching the token's time window). If a nonce is seen twice within the window, the transaction is flagged as a potential replay attack.
3. **Clock Skew Mitigation:** The POS system must synchronize its clock with an NTP server before generating or validating tokens. A small tolerance (e.g., +/- 30 seconds) is allowed for clock skew, but this is an `ASSUMPTION: 30 seconds` that must be validated against the POS hardware capabilities.

### 4.1 Storage Mechanism

Use `expo-secure-store` (which wraps iOS Keychain and Android Keystore).

### 4.2 Key Management

The token is stored under a key derived from the Beneficiary's session ID, ensuring it is only accessible to the authenticated app instance.

### 4.3 Access Control

The token is only accessible when the app is in the foreground and the user is authenticated.

### 4.4 Secure Storage Architecture

The Expo application must utilize `expo-secure-store` to persist the Offline Cryptographic Token. This leverages the underlying platform security modules:

*   **iOS:** Keychain Services with `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` to prevent backup and iCloud sync.
*   **Android:** Android Keystore System, binding the key to the hardware-backed secure enclave where available.

**Constraint:** No plaintext token data may be stored in AsyncStorage, Realm, SQLite, or any non-encrypted local storage mechanism. The token must be treated as a high-value credential equivalent to a session cookie.

### 5.1 Nonce Tracking

The Central Ledger maintains a Redis cache of all issued nonces. The TTL of each nonce entry matches the token's expiration time.

### 5.2 POS Validation

1. POS scans the QR/barcode and extracts the token payload.
2. POS validates the HMAC signature using the current local key.
3. POS checks the timestamp and expiration to ensure the token is within the valid time window.
4. POS queues the redemption event locally with the nonce.

### 5.3 Server-Side Reconciliation

1. When the POS device regains connectivity, it syncs queued redemption events to the Central Ledger.
2. The Central Ledger checks the nonce against the Redis cache.
3. If the nonce is present and unused, the redemption is processed, and the nonce is marked as used.
4. If the nonce is already used, the redemption is rejected as a double-spend attempt, and an alert is triggered for the Dispute Adjudicator ([ACT-7BA340FF76](../project_glossary.md#act-7ba340ff76)).

### 6.1 Verification Algorithm

The POS scanner executes a local, deterministic verification routine upon scanning a Beneficiary's ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) QR/barcode. This routine must complete within 150ms to prevent queue stagnation.

**Input:** `token_string` (Base64URL encoded JSON)
**Output:** `VerificationResult` (Enum: `VALID`, `INVALID_SIGNATURE`, `EXPIRED`, `INVALID_FORMAT`)

**Algorithm Steps:**

1. **Parsing & Validation (T < 20ms):**
   *   Decode `token_string` from Base64URL to JSON.
   *   Validate JSON structure against the Offline Token Schema (defined in Section 3).
   *   Extract fields: `v` (version), `t` (timestamp), `e` (expiration), `c` (credit amount), `h` (hashed beneficiary ID), `s` (signature).
   *   Constraint: If any field is missing or malformed, return `INVALID_FORMAT` immediately.

2. **Timestamp & Expiration Check (T < 5ms):**
   *   Retrieve local system time `T_now` from the POS device's secure clock.
   *   Assumption: POS devices are configured to synchronize with an NTP server at least once every 24 hours. Clock skew is bounded to +/- 2 minutes.
   *   Check if `T_now > e` (expiration timestamp). If true, return `EXPIRED`.
   *   Check if `T_now < t - skew_tolerance`. If true, return `EXPIRED` (future-dated token).

3. **HMAC Signature Verification (T < 100ms):**
   *   Construct the canonical payload string: `canonical = JSON.stringify({v, t, e, c, h})`.
   *   Retrieve the current Merchant-specific HMAC secret key `K_merchant` from the POS device's secure local storage (e.g., Android Keystore / iOS Keychain).
   *   Compute `HMAC = HMAC-SHA256(K_merchant, canonical)`.
   *   Compare HMAC with the provided `s` (signature) using a constant-time comparison function to prevent timing attacks.
   *   If `HMAC != s`, return `INVALID_SIGNATURE`.

4. **Result:**
   *   If all checks pass, return `VALID`.

### 6.2 POS Scanner State Machine

The POS scanner operates in a finite state machine to manage the lifecycle of a redemption attempt.

**States:**

1. **IDLE:**
   *   Waiting for a QR/barcode scan event.
   *   Transition: On scan event -> `VERIFYING`.

2. **VERIFYING:**
   *   Executing the Verification Algorithm (6.1).
   *   Transition: On `VALID` -> `PROCESSING`.
   *   Transition: On `INVALID_SIGNATURE`, `EXPIRED`, or `INVALID_FORMAT` -> `ERROR`.

3. **PROCESSING:**
   *   Deducting the credit amount `c` from the local cached balance for the hashed beneficiary ID `h`.
   *   Assumption: Local balance is synchronized with the central ledger (Financial Ledger Data Model) when connectivity is available. In offline mode, the POS maintains a local 'allowance' buffer.
   *   Transition: On successful deduction -> `SUCCESS`.
   *   Transition: On insufficient local balance -> `ERROR`.

4. **SUCCESS:**
   *   Displaying 'Redemption Successful' to the Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)).
   *   Queuing the redemption event for later synchronization with the central ledger (gRPC Service Contracts & Definitions).
   *   Transition: On user confirmation or timeout -> `IDLE`.

5. **ERROR:**
   *   Displaying a user-friendly error message (e.g., 'Invalid Token', 'Token Expired').
   *   Logging the error locally for later audit (Distributed Tracing & Log Aggregation).
   *   Transition: On user dismissal -> `IDLE`.

### 6.3 Latency Optimization Strategies

To ensure the 150ms latency target ([CON-4152F2C7C3](../project_glossary.md#con-4152f2c7c3)):

*   **Local Key Storage:** HMAC keys are stored in hardware-backed secure storage (Android Keystore / iOS Keychain) to minimize retrieval latency and prevent extraction.
*   **Efficient Cryptography:** HMAC-SHA256 is chosen for its balance of security and performance on low-power POS devices. ECDSA is rejected due to higher computational overhead.
*   **Minimal I/O:** The verification algorithm relies solely on local CPU and memory. No network calls are made during the verification phase.
*   **Pre-computation:** If possible, the POS device pre-fetches and caches the latest HMAC key rotation schedule to avoid delays during key rotation events.

### 6.4 Security Considerations

*   **Replay Attacks:** The token's expiration timestamp `e` and the local time check mitigate simple replay attacks. However, a determined attacker could replay a token within its validity window. This is mitigated by the central ledger's nonce tracking (defined in Section 5).
*   **Clock Skew:** The `skew_tolerance` parameter (Assumption: +/- 2 minutes) must be configurable by the Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) to accommodate varying POS device clock accuracies.
*   **Key Compromise:** If a Merchant's HMAC key is compromised, the Platform Administrator must be able to rotate keys and invalidate all tokens signed with the old key. This requires a key versioning scheme (e.g., `K_merchant_v1`, `K_merchant_v2`) and the POS device must support fetching the latest key version when online.

## 7. Error Handling and Edge Cases

*   **Expired Token:** If `e < current_time`, the POS must reject the token and prompt the Beneficiary to refresh their voucher in the app.
*   **Invalid Signature:** If the HMAC verification fails, the POS must reject the token and log the event for security review.
*   **Nonce Collision:** If a nonce is already in the local cache, the POS must reject the token and flag the Merchant for potential fraud investigation.

## 8. Knowledge Gaps and Assumptions

*   **KNOWLEDGE_GAP: token_expiry_duration** - The exact maximum lifetime of an offline token (e.g., 60s, 120s, 300s) must be established by the Security Team based on POS transaction latency baselines and acceptable risk tolerance.
*   **KNOWLEDGE_GAP: key_rotation_frequency** - The frequency of HMAC secret key rotation (e.g., hourly, daily) must be defined to balance security with the operational complexity of distributing keys to all POS devices.
*   **ASSUMPTION: POS_clock_accuracy** - POS devices are assumed to have reasonably accurate system clocks (within +/- 2 minutes of UTC). If not, NTP sync must be enforced before token generation. Evidence needed: POS hardware specifications and network configuration.
*   **ASSUMPTION: SecureStore_availability** - SecureStore is assumed to be available and secure on all target Expo devices (iOS/Android). Evidence needed: Expo documentation and device compatibility matrix.
*   **KNOWLEDGE_GAP: POS Device Clock Synchronization** - The exact NTP synchronization frequency and tolerance for POS devices in the target merchant network must be established to accurately configure the `skew_tolerance` parameter.
*   **KNOWLEDGE_GAP: Local Balance Buffer Size** - The maximum offline credit allowance (buffer) that a POS device can hold before requiring synchronization with the central ledger must be defined to prevent excessive financial exposure during extended outages.

## 9. Architectural Overview & Scope

This artifact defines the design for the Offline Cryptographic Token Verification mechanism within the MealCredit platform. It addresses the critical requirement to enable Beneficiary (ACT-ADA6716160) redemption at Merchant (ACT-AF904DCFF9) POS terminals in low-connectivity or offline scenarios, while strictly adhering to PCI-DSS Level 1 compliance and SOC2 Type II structural planning.

The system decouples the immediate POS clearance from the central financial ledger by issuing time-bound, cryptographically signed tokens. These tokens are stored securely on the Beneficiary's device and validated locally by the Merchant's POS interface. Synchronization with the central ledger occurs asynchronously to prevent double-spending and ensure financial integrity.

### 9.1 Design Principles
Zero Raw Card Data: Consistent with the project mandate, zero raw card data touches MealCredit servers or client devices. The offline token is a cryptographic voucher, not a payment instrument containing PANs.
Strict Anonymization: Beneficiary demographic status and legal names are cryptographically segregated from the token payload. The token contains only the necessary cryptographic proof of value and validity.
Offline-First Resilience: The POS validation logic must function without network access, ensuring the Beneficiary experience is not degraded by connectivity issues.

## 10. Token Cryptography & Payload Structure

The Offline Cryptographic Token is a JSON Web Token (JWT) signed with HMAC-SHA256 (or an equivalent strong symmetric algorithm as determined by the final security audit). The token is generated by the backend and signed with a key managed by the Platform Administrator (ACT-086A974D63).

### 10.1 Encryption at Rest
The JWT is encrypted before storage on the Beneficiary's device using AES-256-GCM. The encryption key is derived from a device-specific master key stored in SecureStore under the key mealcredit_master_key. This master key is generated once during the Beneficiary's first app launch and is bound to the device's unique hardware identifier.

Encryption Parameters:
Algorithm: AES-256-GCM
Key Derivation: HKDF (HMAC-based Key Derivation Function) with a salt derived from the Beneficiary's anonymous UUID.
IV: 96-bit random IV generated per encryption operation.
Authentication Tag: 128-bit GCM authentication tag.

## 11. Secure Client-Side Storage Contract

The Expo mobile application is responsible for secure storage and retrieval of the offline token. The following TypeScript interfaces define the contract for the SecureStore service.

### 11.1 Token Storage Interface

typescript
interface OfflineToken {
 token: string; // Encrypted JWT string
 issued_at: number;
 expires_at: number;
 nonce: string;
}

interface SecureStoreService {
 storeOfflineToken(token: OfflineToken): Promise<void>;
 getOfflineToken(): Promise<OfflineToken | null>;
 deleteOfflineToken(): Promise<void>;
 isTokenValid(): Promise<boolean>;
}

### 11.2 Secure Deletion After Redemption
Upon successful redemption of the voucher at the Merchant POS (ACT-AF904DCFF9), the application must immediately call `deleteOfflineToken()` to remove the token from the device. This prevents the token from being reused in a replay attack if the device is compromised or if the token is intercepted.

### 11.3 Device Integrity Checks
If the device is rooted (Android) or jailbroken (iOS), the SecureStore may be less secure. The application should detect this condition and refuse to store or use offline tokens. This can be achieved by checking for common root/jailbreak detection indicators.

### 12.1 Token Nonce and Ledger State
To prevent replay attacks, every Offline Cryptographic Token must contain a unique, server-generated nonce (UUIDv4). This nonce serves as the primary key for the financial ledger's redemption state.

Nonce Generation: The nonce is generated by the central ledger at the time of token issuance and embedded in the HMAC payload.
Ledger Lookup: The Financial Ledger Data Model (owned by sibling artifact) must maintain an append-only immutable log (CON-1762EA5021) where each nonce is indexed. Once a nonce is marked as REDEEMED, it cannot be reused.
Double-Spending Prevention: If a token is presented for redemption a second time (either locally on a disconnected POS or during a sync window), the system checks the nonce against the ledger. If the nonce is already REDEEMED, the transaction is rejected.

### 12.2 Offline Synchronization Protocol
When a POS scanner (Merchant ACT-AF904DCFF9) or Beneficiary device regains connectivity, it must synchronize its local queue of offline transactions with the central ledger.

Sync Queue: The POS device maintains a local, encrypted queue of pending transactions. Each entry includes the nonce, timestamp, amount, and hmac_signature.
Batch Submission: Upon reconnection, the POS device submits the batch of pending transactions to the central API Orchestration Layer ([SUR-85E4A5B6E7](../project_glossary.md#sur-85e4a5b6e7)) via a secure gRPC endpoint (owned by sibling artifact).
Idempotency Check: The central ledger processes the batch by checking each nonce for existence in the REDEEMED state.
If nonce is new: Mark as REDEEMED, update the financial ledger, and return a success acknowledgment.
If nonce exists: Return a DUPLICATE_REDEMPTION error. The POS device must log this discrepancy for the Dispute Adjudicator (ACT-7BA340FF76) to review.

### 12.3 Cryptographic Invalidation and Revocation
To ensure that a token verified and synchronized is cryptographically invalidated across all devices:

Global State Update: The REDEEMED status of a nonce is immediately propagated to all active POS devices via the gRPC stream ([SUR-5B18C8719F](../project_glossary.md#sur-5b18c8719f)). This ensures that even if a device is offline during the initial sync, it will receive the invalidation state upon reconnection.
Token Expiration: Tokens have a strict expiration time (exp). Any token presented after its exp timestamp is automatically rejected by the POS device's local validation logic, preventing the use of stale tokens.
Revocation List: In the event of a compromised key or widespread fraud, the central ledger can issue a revocation_list update via the gRPC stream. POS devices must check the nonce against this list before processing any offline transaction.

### 12.4 Latency and Availability Constraints
- Sync Latency: The synchronization protocol must handle batches of up to 10,000 concurrent connections ([CON-6D5E21557B](../project_glossary.md#con-6d5e21557b)) with a p99 latency below 250ms for the initial validation callback.
- Offline Fallback: The local POS validation logic must be able to verify the HMAC signature and timestamp without network access, ensuring that the Beneficiary (ACT-ADA6716160) experience is not degraded by connectivity issues ([CON-387CDD9AEB](../project_glossary.md#con-387cdd9aeb)).

## 13. Integration with Sibling Artifacts

Offline Cryptographic Token Verification (Step 2): This artifact relies on the token schema and HMAC signing contract defined in Step 2.
Expo Mobile Client Architecture: This artifact integrates with the overall Expo application structure, ensuring that the SecureStore service is accessible to all components that require offline token management.
Financial Ledger Data Model: The token's nonce and expires_at fields must align with the ledger's reconciliation logic to ensure accurate tracking of offline redemptions.

This contract ensures that the Offline Cryptographic Token is stored securely on the device, preventing theft and cloning, while enabling seamless offline redemption for Beneficiaries.
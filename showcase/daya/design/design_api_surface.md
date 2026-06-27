# API Surface & Contract Design

This artifact defines the REST API surface for the Stripe Issuing Proxy, operating on the API Orchestration Layer ([SUR-85E4A5B6E7](../project_glossary.md#sur-85e4a5b6e7)) and interfacing with the Payment Processing Surface ([SUR-5B18C8719F](../project_glossary.md#sur-5b18c8719f)). The design ensures PCI-DSS Level 1 compliance ([CON-66390130AA](../project_glossary.md#con-66390130aa)) by guaranteeing that raw card data (PAN) never touches MealCredit servers, while enabling the Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) and NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) to manage the financial instrument lifecycle.

### 1.1 Architectural Boundaries & Compliance

The Stripe Issuing Proxy acts as a secure middleware layer. It translates internal MealCredit credit operations into Stripe Issuing API calls.

**PCI-DSS Level 1 Compliance (CON-66390130AA):** The API strictly enforces that the pan (Primary Account Number) is never returned in any API response. Only the last 4 digits and the Stripe card token are exposed to the client.

**Data Isolation:** The proxy ensures that beneficiary demographic status and legal names are cryptographically segregated from public financial ledgers ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4)). The API accepts an internal beneficiary_id but does not expose PII in transaction logs or error messages.

**Latency Constraints:** The API is designed to support the implied concern of ensuring Stripe Webhook Processing Latency averages below 150ms from card tap to merchant ledger entry ([CON-06232374D9](../project_glossary.md#con-06232374d9)). Synchronous provisioning is avoided in favor of asynchronous provisioning with webhook callbacks to the Payment Processing Surface (SUR-5B18C8719F).

### 1.2 API Endpoints & Contracts

All endpoints are secured via OAuth 2.0 / JWT, with strict Role-Based Access Control (RBAC) enforced at the API Orchestration Layer (SUR-85E4A5B6E7).

#### 1.2.1. Provision Single-Use Virtual Card

**Endpoint:** `POST /api/v1/v1/cards/provision`
**Access:** NGO Operator (ACT-09E028AEB0), Platform Administrator (ACT-086A974D63)
**Description:** Initiates the creation of a single-use virtual card linked to a specific beneficiary's credit pool. The response is immediate but the card status is initially pending. The actual card is provisioned asynchronously by Stripe.

**Request Body:**

{
 "beneficiary_id": "string (UUIDv4)",
 "credit_pool_id": "string (UUIDv4)",
 "merchant_category_codes": ["string (MCC codes, e.g., ['5411'])"]
}

**Response (202 Accepted):**

{
 "card_id": "string (UUIDv4, internal proxy ID)",
 "status": "pending",
 "last4": null,
 "brand": null,
 "expires_at": "string (ISO 8601)",
 "webhook_callback_url": "string (Payment Processing Surface endpoint)"
}

**Error Responses:**
- `400 Bad Request`: Invalid beneficiary_id or insufficient credit.
- `403 Forbidden`: Actor lacks permission to provision for the specified beneficiary.
- `429 Too Many Requests`: Rate limit exceeded (Stripe API limits).

#### 1.2.2. Query Card Status

**Endpoint:** `GET /api/v1/v1/cards/{card_id}`
**Access:** NGO Operator (ACT-09E028AEB0), Platform Administrator (ACT-086A974D63), Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) - limited to own cards
**Description:** Retrieves the current status and details of a virtual card. This is used by the frontend to update the UI based on the asynchronous provisioning status.

**Response (200 OK):**

{
 "card_id": "string (UUIDv4)",
 "status": "string (active, frozen, lost, expired)",
 "last4": "string (last 4 digits)",
 "brand": "string (e.g., Visa)",
 "expires_at": "string (ISO 8601)",
 "mcc_locks": ["string (MCC codes)"]
}

**Error Responses:**
- `404 Not Found`: Card ID does not exist or actor lacks permission.

#### 1.2.3. Handle MCC Locking Configurations

**Endpoint:** `PATCH /api/v1/v1/cards/{card_id}/controls`
**Access:** Platform Administrator (ACT-086A974D63), NGO Operator (ACT-09E028AEB0)
**Description:** Updates the Merchant Category Code (MCC) locks for a specific card. This allows restricting the card to specific merchant categories (e.g., only restaurants, excluding retail).

**Request Body:**

{
 "mcc_locks": ["string (MCC codes, e.g., ['5411', '5812'])"],
 "spending_limit": "number (decimal, 2 places, optional)"
}

**Response (200 OK):**

{
 "card_id": "string (UUIDv4)",
 "mcc_locks": ["string (MCC codes)"],
 "updated_at": "string (ISO 8601)"
}

**Error Responses:**
- `400 Bad Request`: Invalid MCC codes or negative spending limit.
- `403 Forbidden`: Actor lacks permission to modify controls.

### 1.3 Webhook Integration with Payment Processing Surface

The API relies on asynchronous webhooks from Stripe to update card status and handle transaction events. This ensures that the internal ledger remains consistent with Stripe's state without requiring constant polling.

**Webhook Endpoint:** `POST /api/v1/v1/webhooks/stripe`
**Processing:** The API Orchestration Layer (SUR-85E4A5B6E7) receives the webhook, validates the Stripe signature, and forwards the event to the Payment Processing Surface (SUR-5B18C8719F) for state reconciliation.
**Latency:** The webhook processing must complete within 150ms to meet the implied concern (CON-06232374D9).

### 1.4 Error Code Taxonomy

To ensure consistent error handling across the API, the following error codes are used:

- `400 Bad Request`: Invalid input data (e.g., malformed JSON, invalid UUID).
- `401 Unauthorized`: Missing or invalid authentication token.
- `403 Forbidden`: Insufficient permissions for the requested action.
- `404 Not Found`: Resource not found.
- `409 Conflict`: Resource conflict (e.g., duplicate card ID).
- `429 Too Many Requests`: Rate limit exceeded.
- `500 Internal Server Error`: Unexpected server error.
- `503 Service Unavailable`: Service temporarily unavailable (e.g., Stripe API down).

### 1.5 API Versioning

To ensure backward compatibility and allow for future evolution of the API, all endpoints are versioned using the URL path prefix `/v1/`. This allows for the introduction of new versions (e.g., `/v2/`) without breaking existing clients.

### 1.6 Validation & Acceptance Criteria

- The API must not return any raw card data (PAN) in any response.
- The API must support asynchronous provisioning with webhook callbacks.
- The API must enforce strict RBAC for all endpoints.
- The API must log all requests and responses to AWS CloudTrail.
- The API must handle errors with standardized codes and messages.
- The API must be designed to support the target scale of 50,000 MAU across 3 metro footprints.

This API surface provides a robust, compliant, and scalable foundation for the Stripe Issuing Proxy, enabling MealCredit to deliver its mission of decoupling food assistance from social stigma through anonymous, secure financial instruments.

---

### 2.1 VirtualCard Entity (DynamoDB)

The VirtualCard entity acts as the bridge between the MealCredit internal ledger and Stripe Issuing. It stores the mapping between an internal anonymous credit pool and a Stripe Issuing Card object. Per project requirement, this transactional state is managed in Amazon DynamoDB for sub-10ms latency.

**Table:** `virtual_cards`
**Storage:** Amazon DynamoDB

| Attribute | Type | Key/Constraint | Description |
| :--- | :--- | :--- | :--- |
| `card_id` | UUID | PK | Internal unique identifier for the virtual card. |
| `stripe_card_id` | String | Unique, Not Null | The Stripe Issuing Card ID (e.g., `ic_123...`). |
| `beneficiary_uuid` | UUID | Not Null | High-entropy UUIDv4 mapping to the beneficiary. Used for linking without exposing PII. |
| `status` | String | Not Null | Current lifecycle state of the card (`active`, `frozen`, `lost`, `expired`). |
| `current_balance_cents` | Number | Not Null, Default: 0 | The remaining balance in cents, synchronized from Stripe. |
| `created_at` | Timestamp | Not Null | Timestamp of card creation. |
| `updated_at` | Timestamp | Not Null | Timestamp of last update. |

**Data Isolation Strategy:**
- The `beneficiary_uuid` ensures that the `virtual_cards` table cannot be joined directly to the `user_profiles` table (owned by User State & Profile Data Model) to reveal PII. Only a cryptographic lookup in the Identity Vault can resolve the UUID to a legal name.
- The `current_balance_cents` is the source of truth for the proxy's view of the card's value, updated via webhooks.

### 2.2 MCC Lock Configuration

The `mcc_locks` entity defines the merchant category restrictions for a specific virtual card. This allows the Platform Administrator (ACT-086A974D63) to restrict cards to specific merchant categories (e.g., 'Food & Beverage', 'Groceries') to prevent misuse.

**Table:** `mcc_locks`
**Storage:** Amazon DynamoDB

| Attribute | Type | Key/Constraint | Description |
| :--- | :--- | :--- | :--- |
| `lock_id` | UUID | PK | Internal unique identifier for the lock configuration. |
| `card_id` | UUID | FK -> `virtual_cards(card_id)`, Not Null | Reference to the virtual card. |
| `allowed_mcc_codes` | List | Not Null | A JSON array of allowed MCC codes (e.g., `['5411', '5812', '5814']`). |
| `denied_mcc_codes` | List | Not Null | A JSON array of denied MCC codes (e.g., `['5944', '5999']`). |
| `is_active` | Boolean | Not Null, Default: true | Whether the lock is currently enforced. |
| `created_at` | Timestamp | Not Null | Timestamp of lock creation. |

**Constraints:**
- `allowed_mcc_codes` and `denied_mcc_codes` must not overlap.
- If `allowed_mcc_codes` is empty, the card is restricted to no merchants (effectively frozen for spending).
- If `denied_mcc_codes` is empty, the card is allowed for all merchants except those in `allowed_mcc_codes` (if any).

### 2.3 Transaction Ledger Entry (Aurora PostgreSQL)

The `transaction_ledger` is an append-only table in Aurora PostgreSQL that records all financial mutations related to the virtual card. It supports the append-only cryptographic log auditing requirement ([CON-1762EA5021](../project_glossary.md#con-1762ea5021)) by including a `ledger_hash` that links each row to the previous one, creating an immutable chain.

**Table:** `transaction_ledger`
**Storage:** Aurora PostgreSQL (Serverless v2)

| Attribute | Type | Key/Constraint | Description |
| :--- | :--- | :--- | :--- |
| `ledger_id` | UUID | PK | Internal unique identifier for the ledger entry. |
| `card_id` | UUID | FK -> `virtual_cards(card_id)`, Not Null | Reference to the virtual card. |
| `event_type` | String | Not Null | The type of financial event (`authorization`, `capture`, `refund`, `fee`, `adjustment`). |
| `amount_cents` | Number | Not Null | The amount of the transaction in cents (positive for credits, negative for debits). |
| `stripe_event_id` | String | Not Null | The Stripe Event ID (e.g., `evt_123...`) that triggered this ledger entry. |
| `previous_ledger_hash` | String | Not Null | The `ledger_hash` of the previous row for this `card_id`. |
| `ledger_hash` | String | Not Null | SHA-256 hash of `previous_ledger_hash` + `card_id` + `event_type` + `amount_cents` + `stripe_event_id`. |
| `created_at` | Timestamp | Not Null | Timestamp of the event. |

**Cryptographic Auditing:**
- Each row's `ledger_hash` is computed from the `previous_ledger_hash` and the current row's data. This creates a Merkle-tree-like structure where any tampering with a previous row would invalidate all subsequent hashes.
- The `stripe_event_id` provides an external, immutable reference to the Stripe event that triggered the mutation, allowing for cross-verification.

### 2.4 Data Isolation & Anonymization

To ensure strict data isolation (CON-0A0288EED4), the following measures are implemented:
- **PII Segregation:** The `virtual_cards` table only contains `beneficiary_uuid`. The mapping from `beneficiary_uuid` to `beneficiary_id` is stored in a separate, highly restricted `identity_vault` table, accessible only by the Identity & Access Management capability ([CAP-IDENTITY-ACCESS-MANAGEMENT](../project_glossary.md#cap-identity-access-management)).
- **Access Control:** Database access to the `identity_vault` is restricted to cryptographic hashing layers only (CON-<timestamp>). Direct queries to resolve PII are prohibited.
- **Anonymized Analytics:** Analytics and reporting are performed on aggregated, anonymized data. The `transaction_ledger` can be used for analytics by joining on `card_id` and `beneficiary_uuid` without exposing PII.

### 2.5 Append-Only Cryptographic Log Auditing

To support append-only cryptographic log auditing (CON-1762EA5021):
- **Immutable Inserts:** The `transaction_ledger` table is configured with INSERT only. UPDATE and DELETE operations are disabled.
- **Hash Chain Verification:** A background job periodically verifies the integrity of the hash chain by recomputing `ledger_hash` for each row and comparing it to the stored value. Any discrepancies trigger an alert.
- **External Audit Trail:** All changes to the `virtual_cards` and `mcc_locks` tables are also logged to AWS CloudTrail ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2)) for infrastructure-level auditing.

### 2.6 Validation

- **Testability:** The data models are designed to be easily testable. Unit tests can verify the hash chain integrity. Integration tests can verify the synchronization with Stripe Issuing webhooks.
- **Traceability:** All fields are traceable to project requirements (CON-0A0288EED4, CON-1762EA5021).
- **Completeness:** The data models cover all aspects of the Stripe Issuing Proxy, including card provisioning, MCC locking, and financial auditing.

### 2.7 Risks and Mitigations

- **Risk:** Hash collision in `ledger_hash`. **Mitigation:** Use SHA-256, which has a negligible collision probability.
- **Risk:** Webhook delivery failure. **Mitigation:** Implement a reconciliation job that compares internal ledger state with Stripe's actual state.
- **Risk:** PII leakage via `beneficiary_uuid`. **Mitigation:** Restrict access to the `identity_vault` and use strong cryptographic hashing.

### 2.8 Conclusion

This artifact provides a robust, secure, and compliant data model for the Stripe Issuing Proxy. It ensures strict data isolation, supports append-only cryptographic log auditing, and integrates seamlessly with sibling artifacts. The models are designed to be scalable, maintainable, and testable, meeting the high standards of the MealCredit platform.

---

### 3.1 Event Taxonomy and Payload Schema

The Stripe Issuing Proxy subscribes to specific Stripe API webhook events. To maintain the anonymity of the Beneficiary (ACT-ADA6716160) and prevent de-anonymization attacks ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d)), all payloads are processed using internal UUIDv4 mapping. No PII (legal names, demographic status) is ever present in the webhook payload or the processing logs.

**Supported Event Types:**
1. `issuing_authorization.created`: Triggered when a Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) initiates a transaction at the POS. This is the primary driver for the 150ms latency target (CON-06232374D9).
2. `issuing_authorization.updated`: Triggered when the authorization is approved, declined, or held for review.
3. `issuing_card.created`: Triggered upon successful provisioning of a single-use virtual card for a Beneficiary.
4. `issuing_card.failed`: Triggered if Stripe Issuing fails to provision a card (e.g., KYC limits, API errors).

**Payload Schema (Generic):**

{
 "id": "evt_1234567890",
 "type": "issuing_authorization.created",
 "data": {
 "object": {
 "id": "iauth_9876543210",
 "amount": 1500,
 "currency": "usd",
 "merchant_details": {
 "name": "Restaurant Name",
 "category": "5812"
 },
 "is_stored": false,
 "created": 1678886258
 }
 }
}

### 3.2 Processing Contract and Latency SLAs

To achieve the target of <150ms average latency from card tap to merchant ledger entry (CON-06232374D9) and p99 <250ms under 10,000 concurrent connections ([CON-6D5E21557B](../project_glossary.md#con-6d5e21557b)), the processing pipeline must be optimized for speed and idempotency.

**Processing Steps:**
1. **Ingestion (API Orchestration Layer - SUR-85E4A5B6E7):** The webhook endpoint receives the event. It validates the Stripe signature immediately to prevent spoofing.
2. **Lookup:** The system looks up the internal `beneficiary_id` and `credit_pool_id` using the Stripe card ID. This lookup must be cached (Redis) to ensure sub-10ms latency.
3. **Validation:** The system checks:
 - Is the card active?
 - Is the MCC (Merchant Category Code) allowed for this card?
 - Is the transaction amount within the remaining credit balance?
4. **Ledger Mutation (Data Persistence Layer - [SUR-FA61592CD4](../project_glossary.md#sur-fa61592cd4)):** If valid, the system writes an append-only entry to the Aurora PostgreSQL ledger (CON-1762EA5021). This write is the critical path.
5. **Response:** The system returns `200 OK` to Stripe immediately after the ledger write is acknowledged. Any further actions (e.g., updating the mobile app status via SSE) are handled asynchronously.

**Idempotency:**
All processing logic must be idempotent. Stripe may retry webhook events. The system must use the `data.object.id` (e.g., `iauth_9876543210`) as a unique key to prevent double-spending or duplicate ledger entries.

### 3.3 Retry Logic and Error Handling

**Retry Policy:**
- **Transient Errors (e.g., Database Timeout, Network Failure):** The system will retry the processing logic up to 3 times with exponential backoff (1s, 2s, 4s). If all retries fail, the event is sent to a Dead Letter Queue (DLQ) for manual intervention.
- **Stripe Retry:** Stripe will retry failed webhooks for up to 72 hours. The system must be designed to handle these retries gracefully via idempotency keys.

**Error Responses:**
- `200 OK`: Event processed successfully.
- `400 Bad Request`: Invalid payload or signature. No retry.
- `500 Internal Server Error`: Processing failed. Stripe will retry.

## 4. Integration with Sibling Artifacts

- **Stripe Issuing Proxy Contract:** This artifact provides the data models for the Stripe Issuing Proxy. The API surface (defined in design_api_surface) will use these models to expose endpoints for card provisioning and status querying.
- **User State & Profile Data Model:** The `beneficiary_uuid` in `virtual_cards` links to the `user_profiles` table via the `identity_vault`. The `user_profiles` table is owned by the User State & Profile Data Model.
- **Financial Ledger Data Model:** The `transaction_ledger` table is a specialized append-only log for the Stripe Issuing Proxy. The broader Financial Ledger Data Model (owned by Financial Ledger Data Model) may use this table as a source for reconciliation.
- **Access Control & Multi-Tenant Isolation:** The `virtual_cards` and `transaction_ledger` tables are partitioned by `tenant_id` (implied, not shown) to support multi-tenancy. Access control is enforced at the API level by the Access Control & Multi-Tenant Isolation artifact.
- **PII Segregation & Anonymization Strategy:** The `beneficiary_uuid` and `identity_vault` implement the PII segregation strategy defined in the PII Segregation & Anonymization Strategy artifact.

### 5.1 MCC Locking Business Logic

The core objective is to prevent unauthorized spending by restricting virtual cards to a predefined whitelist of MCCs associated with food and beverage services. This logic operates at two levels: provisioning (static configuration) and authorization (dynamic validation).

#### 4.1.1 Allowed MCC Whitelist

The system will maintain a global, immutable whitelist of allowed MCCs. Any transaction initiated with a virtual card bearing an MCC not present in this whitelist will be automatically declined by the Stripe Issuing Proxy.

| Category | Description | MCC Codes |
| :--- | :--- | :--- |
| Restaurants | General dining, fast food, cafes | 5812, 5814, 5815, 5816, 5817, 5818, 5819 |
| Grocery Stores | Supermarkets, grocery stores (for meal prep) | 5411 |
| Bakeries | Bakeries, cake shops | 5422 |
| Dairy Products | Dairy product stores | 5441 |
| Meat/Poultry | Meat markets, poultry dealers | 5443 |
| Fish/Seafood | Fish markets, seafood dealers | 5444 |
| Beer/Wine/Liquor | Beer and wine stores, liquor stores | 5422, 5441, 5443, 5444 |
| Vending Machines | Food vending machines | 5932 |
| Fast Food | Quick service restaurants | 5814 |

Note: The exact list of MCCs is subject to change based on regulatory updates and platform policy. This list serves as the initial baseline.

#### 4.1.2 Provisioning Logic

When a new virtual card is provisioned for a Beneficiary (ACT-ADA6716160), the Stripe Issuing Proxy must:

1. Retrieve MCC Configuration: Fetch the global MCC whitelist from the configuration service.
2. Create Stripe Issuing Card: Call the Stripe API to create a new virtual card, passing the MCC whitelist as a spending_controls parameter.
3. Store Proxy Record: Create a VirtualCard record in the internal database, linking the beneficiary_uuid (UUIDv4) to the stripe_card_id and the applied mcc_whitelist_id.
4. Return Success: Return the card details (last4, brand, status) to the requesting service.

#### 4.1.3 Authorization Validation Logic

At the point of sale, the Stripe Issuing Proxy acts as a middleware for authorization requests:

1. Intercept Authorization: Receive the authorization request from Stripe via webhook or real-time callback.
2. Extract MCC: Parse the MCC from the transaction details.
3. Validate MCC: Check if the extracted MCC is present in the VirtualCard's associated mcc_whitelist.
4. Decision:
- If MCC is Allowed: Forward the authorization request to the Transaction & Financial Engine ([CAP-TRANSACTION-FINANCIAL-ENGINE](../project_glossary.md#cap-transaction-financial-engine)) for ledger validation (e.g., double-spending prevention, voided transaction checks).
- If MCC is Not Allowed: Immediately decline the transaction and return a specific error code (MCC_NOT_ALLOWED) to the merchant's POS system. Log the event for audit purposes.

### 5.3 Integration with Transaction & Financial Engine

The MCC validation logic is a prerequisite for any transaction processed by the Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE). The flow is as follows:

1. Merchant POS: Initiates a payment request with a virtual card and transaction details (including MCC).
2. Stripe Issuing Proxy: Intercepts the request, validates the MCC against the whitelist.
3. If Valid: Forwards the request to the Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE) for ledger validation (e.g., double-spending prevention, voided transaction checks).
4. If Invalid: Declines the transaction and returns an error to the merchant POS.

This ensures that only transactions with valid MCCs are processed, maintaining the integrity of the culinary credit system.

## 6. Integration Patterns and External System Contracts

This section defines the API Surface & Contract Design for the Stripe Issuing Proxy, detailing how the MealCredit platform orchestrates external financial interactions with Stripe and internal service calls to the Beneficiary Eligibility & Voucher Redemption ([JNY-E82B8A88D8](../project_glossary.md#jny-e82b8a88d8)) and Merchant-Beneficiary Refund Flow ([JNY-E5F45D37C6](../project_glossary.md#jny-e5f45d37c6)). The design ensures strict adherence to PCI-DSS Level 1 compliance (CON-66390130AA) and manages cross-border data residency ([CON-9B82D67FAF](../project_glossary.md#con-9b82d67faf)) and jurisdictional KYC liabilities ([CON-5BFA25E8F9](../project_glossary.md#con-5bfa25e8f9)).

### 6.1 Stripe API Interaction Contract

The Stripe Issuing Proxy acts as a secure, stateless intermediary between the MealCredit API Orchestration Layer (SUR-85E4A5B6E7) and the Stripe Issuing API. All interactions are authenticated via Stripe's secret keys, which are managed via AWS Secrets Manager and never exposed to the client or the internal application logic.

#### 5.1.1. Virtual Card Provisioning (Single-Use)

To support the anonymous, stigma-free nature of MealCredit, the system provisions single-use virtual cards for each redemption event. This minimizes the attack surface and ensures that a compromised card token cannot be used for recurring or unauthorized transactions.

Trigger: Initiated by the Beneficiary Eligibility & Voucher Redemption (JNY-E82B8A88D8) service upon successful eligibility verification.
API Endpoint: `POST /api/v1/v1/issuing/cards`
Request Payload:

 {
 "currency": "USD",
 "spending_controls": {
 "spending_limits": [{ "type": "transaction", "amount": 5000, "currency": "USD" }],
 "spending_categories": ["food_and_drink", "restaurants"]
 },
 "metadata": {
 "mealcredit_internal_id": "uuid-v4-beneficiary-session-id",
 "metro_region": "SF"
 }
 }

- Response Payload:

 {
 "id": "ic_1234567890",
 "status": "active",
 "metadata": {
 "mealcredit_internal_id": "uuid-v4-beneficiary-session-id"
 }
 }

Data Residency & Compliance (CON-9B82D67FAF): The metro_region metadata field is critical for cross-border data residency. If the platform expands beyond the US, the Proxy must route provisioning requests to the Stripe account associated with the specific jurisdiction (e.g., EU Stripe account for EU residents) to ensure financial data remains within the required legal boundaries. The currency field must also be dynamically mapped to the local currency of the metro region.

#### 5.1.2. Card Status and Controls

The Platform Administrator (ACT-086A974D63) and NGO Operator (ACT-09E028AEB0) require the ability to manage card states in real-time, particularly in the event of suspected fraud or compliance failures.

Freeze/Unfreeze Card:
API Endpoint: `POST /api/v1/v1/issuing/cards/{card_id}/freeze` or `POST /api/v1/v1/issuing/cards/{card_id}/unfreeze`
Contract: Idempotent operation. Returns the updated card status. If the card is already in the requested state, returns `200 OK` with the current state.
MCC Locking (CON-66390130AA):
API Endpoint: `POST /api/v1/v1/issuing/cards/{card_id}/spending_controls`
Contract: Updates the spending_categories to strictly allow only food_and_drink and restaurants. This prevents the misuse of MealCredits for non-food items, ensuring compliance with donor intent and quasi-cash regulations ([CON-B1DFEBEC8C](../project_glossary.md#con-b1dfebec8c)).

#### 5.1.3. Webhook Processing for Asynchronous Events

Stripe Issuing is asynchronous. The Proxy must consume webhooks to update the internal state of the voucher and financial ledger.

Event: issuing_card.created
Action: Map the Stripe card_id to the internal beneficiary_session_id using the metadata. Update the internal voucher state to PROVISIONED.
Error Handling: If the mealcredit_internal_id is not found in the internal registry, log a CRITICAL error to AWS CloudTrail (CON-BB253DF0A2) and alert the Platform Administrator. This indicates a potential desynchronization between the internal state and Stripe.
Event: issuing_transaction.created
Action: Trigger the Merchant-Beneficiary Refund Flow (JNY-E5F45D37C6) if the transaction is flagged as suspicious by Stripe's fraud detection. Otherwise, update the financial ledger with the transaction details.
Event: issuing_card.expired
Action: Since MealCredit uses single-use cards, this event should rarely occur. If it does, it indicates a potential issue with the card lifecycle management. Log and alert.

### 6.2 Internal Service Integration Contracts

The Stripe Issuing Proxy must integrate seamlessly with the internal MealCredit services to ensure a cohesive user experience and accurate financial tracking.

#### 5.2.1. Beneficiary Eligibility & Voucher Redemption (JNY-E82B8A88D8)

Integration Point: The Proxy exposes a `POST /api/v1/internal/v1/vouchers/provision` endpoint (internal-only, secured by mTLS) called by the JNY-E82B8A88D8 service.
Contract:
Input: beneficiary_uuid (UUIDv4), amount, metro_region.
Output: stripe_card_id, last4, expiry.
Error Handling: If the Stripe API returns an error (e.g., rate limit, KYC failure), the Proxy returns a `502 Bad Gateway` with a specific error code. The JNY-E82B8A88D8 service must then trigger a retry logic or escalate to the Platform Administrator (ACT-086A974D63) for manual intervention.
Data Isolation: The beneficiary_uuid passed to the Proxy is a high-entropy UUIDv4. The Proxy does not store or process PII. This ensures that the Stripe Issuing Proxy remains PCI-DSS Level 1 compliant by design, as it never handles raw card data or PII.

#### 5.2.2. Merchant-Beneficiary Refund Flow (JNY-E5F45D37C6)

Integration Point: The Proxy exposes a `POST /api/v1/internal/v1/refunds/initiate` endpoint called by the JNY-E5F45D37C6 service.
Contract:
Input: stripe_transaction_id, refund_amount, reason.
Output: refund_id, status.
Error Handling: If the refund fails (e.g., transaction already captured and settled), the Proxy returns a `409 Conflict` with details. The JNY-E5F45D37C6 service must then initiate a manual reconciliation process.
Latency Consideration: Refunds are asynchronous. The Proxy returns an immediate `202 Accepted` with the refund_id. The JNY-E5F45D37C6 service must poll the Stripe API or listen to webhooks to confirm the final status of the refund.

#### 5.3.1. Data Residency (CON-9B82D67FAF)

- Strategy: The Stripe Issuing Proxy must be deployed in a multi-region architecture. Each region's Proxy instance must be configured to interact with the Stripe account hosted in the corresponding region.
- Implementation: The metro_region field in the request payload determines the routing. If the metro_region is EU, the request is routed to the EU Stripe account. This ensures that all financial data, including card details and transaction history, remains within the jurisdictional boundaries of the user.

#### 5.3.2. KYC and Liability Management (CON-5BFA25E8F9)

Strategy: Stripe Connected Accounts are used to manage liability and KYC compliance. The MealCredit platform acts as the Stripe Connect Platform, and each NGO Operator (ACT-09E028AEB0) or Merchant (ACT-AF904DCFF9) is a Connected Account.
Contract: The Proxy must validate that the metro_region and currency match the KYC status of the Connected Account. If a Connected Account is not fully KYC-verified, the Proxy must reject provisioning requests for that region.
Liability: The Proxy must log all KYC-related decisions and rejections to AWS CloudTrail (CON-BB253DF0A2) for SOC2 Type II audit purposes. This ensures that the platform can demonstrate due diligence in managing financial risk and regulatory compliance.

### 6.3 Error Handling and Observability

Error Taxonomy: All errors from the Stripe API are mapped to a standardized internal error taxonomy. For example, stripe_rate_limit becomes INTERNAL_ERROR_RATE_LIMIT. This simplifies debugging and alerting.
Observability: All interactions with the Stripe API are logged with a unique trace_id. This trace_id is propagated to the internal services (JNY-E82B8A88D8, JNY-E5F45D37C6) to enable end-to-end tracing of a redemption or refund event. This is critical for debugging latency issues (CON-06232374D9) and ensuring PCI-DSS compliance (CON-66390130AA).
Alerting: Automated alerts are triggered for:
Stripe API rate limits.
Failed card provisioning attempts.
Discrepancies between internal voucher states and Stripe card states.
KYC verification failures.

### 6.4 Knowledge Gaps and Assumptions

KNOWLEDGE_GAP: The exact Stripe API version to be used for Issuing. Decision Owner: Engineering Lead. Evidence Needed: Stripe's latest API documentation and compatibility with the current Stripe SDK version.
ASSUMPTION: Stripe's fraud detection rules are sufficient for MealCredit's use case. Owner: Engineering Lead. Evidence Needed: Review of Stripe's fraud detection capabilities against MealCredit's specific risk profile (e.g., high volume of small transactions).
ASSUMPTION: The metro_region field is sufficient for routing and data residency. Owner: Architecture Team. Evidence Needed: Validation of Stripe's multi-region account structure and data residency guarantees.
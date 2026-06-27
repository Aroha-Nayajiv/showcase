# Access Control & Multi-Tenant Isolation Design

This design artifact defines the Identity & Access Management ([CAP-IDENTITY-ACCESS-MANAGEMENT](../project_glossary.md#cap-identity-access-management)) boundary conditions, multi-tenant data isolation strategies, and API contracts for the Daya platform (MealCredit). It ensures strict data segregation between NGOs, Donors, and Merchants while adhering to PCI-DSS Level 1, SOC2 Type II, and FTC Anonymity Guidelines.

### 1.1 Canonical Actor Role Definitions

The following six actor roles are defined based on the canonical asset registry. Each role has specific boundary conditions regarding data access and operational scope.

- **Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63))**: Global system oversight. Access to all tenant data, infrastructure logs, and compliance reports. No direct access to beneficiary PII without explicit audit trail.
- **NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0))**: Tenant-specific governance. Manages beneficiary eligibility, offboarding ([JNY-4C4BA15817](../project_glossary.md#jny-4c4ba15817)), and fraud investigation ([JNY-CA74D631DC](../project_glossary.md#jny-ca74d631dc)) within their assigned NGO tenant.
- **Dispute Adjudicator ([ACT-7BA340FF76](../project_glossary.md#act-7ba340ff76))**: Cross-tenant dispute resolution. Access to transaction logs and beneficiary-merchant interactions ([JNY-E5F45D37C6](../project_glossary.md#jny-e5f45d37c6)) for dispute resolution ([JNY-2B038C9362](../project_glossary.md#jny-2b038c9362)).
- **Donor ([ACT-80C62C7814](../project_glossary.md#act-80c62c7814))**: Donor-specific data. Access to donation history, impact receipts, and redemption correlation ([CON-23A501C051](../project_glossary.md#con-23a501c051)). No access to beneficiary PII.
- **Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160))**: Tenant-specific redemption. Access to voucher balance, redemption history, and offline fallback tokens. Strictly isolated from donor and merchant operational data.
- **Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9))**: Merchant-specific operations. Access to POS integration, payout status ([JNY-90B07623FB](../project_glossary.md#jny-90b07623fb)), and anonymized transaction aggregates. No access to beneficiary PII or donor data.

### 1.2 JWT Claim Structure for Multi-Tenant Isolation

To enforce multi-tenant isolation across the API Orchestration Layer ([SUR-85E4A5B6E7](../project_glossary.md#sur-85e4a5b6e7)), all JWTs issued by the Identity Provider must include the following claims. This structure ensures that the API gateway and downstream services can immediately validate tenant boundaries and role permissions.

#### 1.2.1 Standard Claims

- `iss`: Issuer identifier (e.g., `https://auth.mealcredit.com`)
- `sub`: Subject identifier (unique user ID)
- `exp`: Expiration time (Unix timestamp)
- `iat`: Issued at time (Unix timestamp)
- `jti`: JWT ID (unique identifier for token revocation)

#### 1.2.2 Custom Claims for Access Control

- `role`: String value representing the canonical actor role (e.g., `Platform Administrator`, `NGO Operator`). Must match one of the six canonical roles defined in Section 1.1.
- `tenant_id`: String value representing the unique identifier for the NGO tenant. For Platform Administrators, this may be null or empty to indicate global access. For all other roles, this must be a valid, active tenant ID.
- `permissions`: Array of strings representing specific permissions granted to the role within the tenant. This allows for fine-grained access control beyond the base role definition.

#### 1.2.3 JWT Validation Rules

1. **Tenant Isolation**: The API Orchestration Layer (SUR-85E4A5B6E7) MUST validate that the `tenant_id` claim in the JWT matches the tenant context of the requested resource. Any mismatch results in a `403 Forbidden` response.
2. **Role Enforcement**: The API Orchestration Layer MUST validate that the `role` claim in the JWT is authorized to perform the requested action on the target resource.
3. **Token Revocation**: The `jti` claim MUST be checked against a revocation list (e.g., Redis) to ensure the token has not been revoked.

### 2.1 Architectural Isolation Strategy: Hybrid Schema Model

To balance operational efficiency with strict compliance requirements, the Data Persistence Layer ([SUR-FA61592CD4](../project_glossary.md#sur-fa61592cd4)) utilizes a Hybrid Schema Model. This approach avoids the prohibitive connection overhead of fully physical isolation while providing stronger logical boundaries than a single shared schema.

- **Shared Operational Schema (public)**:
  - **Scope**: Contains non-sensitive, high-throughput operational data required for platform functionality across all tenants.
  - **Entities**: Merchant locations, restaurant menus, anonymized transaction aggregates, platform configuration, and public-facing API metadata.
  - **Access**: Readable by all authenticated roles (Merchant, Donor, Platform Administrator) with appropriate RBAC. No PII is stored here.

- **Tenant-Specific Schemas (`tenant_<id>`)**:
  - **Scope**: Contains all Personally Identifiable Information (PII) and sensitive demographic data for a specific NGO or jurisdictional footprint.
  - **Entities**: Beneficiary legal names, demographic status, legal guardians, contact information, and NGO-specific governance records.
  - **Access**: Strictly isolated. Only the Platform Administrator (ACT-086A974D63) and authorized NGO Operator (ACT-09E028AEB0) for that specific tenant can access these schemas. Merchant (ACT-AF904DCFF9) and Donor (ACT-80C62C7814) roles have zero access to these schemas.

- **Anonymized Analytics Schema (analytics)**:
  - **Scope**: Contains aggregated, non-reversible data for reporting and Donation-to-Redemption Velocity (DRV) monitoring ([CON-D0F5814F21](../project_glossary.md#con-d0f5814f21)).
  - **Entities**: Hashed beneficiary tokens, transaction counts, regional pool utilization, and anonymized impact metrics.
  - **Access**: Readable by Platform Administrator (ACT-086A974D63) and Dispute Adjudicator (ACT-7BA340FF76) for compliance and fraud investigation (JNY-CA74D631DC). No PII is present.

### 2.2 Cryptographic Segregation of Beneficiary Data (CON-0A0288EED4)

To prevent de-anonymization attacks ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d)) and ensure that beneficiary demographic status and legal names are cryptographically segregated, the following mechanisms are enforced within the `tenant_<id>` schemas:

- **Field-Level Encryption (FLE)**:
  - **Target Fields**: `legal_name`, `date_of_birth`, `guardian_contact`, `address_line_1`, `ssn_last_4` (if required for KYC).
  - **Mechanism**: All target fields are encrypted at rest using AES-256-GCM. Encryption keys are managed via AWS KMS, with a unique Data Key per tenant.
  - **Access Control**: Decryption occurs only within the application layer (API Orchestration Layer - SUR-85E4A5B6E7) after successful RBAC validation. The database never stores plaintext PII.

- **Tokenization for Merchant Interaction**:
  - **Beneficiary Token**: A UUIDv4-based token is generated for each beneficiary. This token is used in all merchant-facing interactions (e.g., voucher scanning, POS callbacks).
  - **Isolation**: The mapping between the `beneficiary_token` and the actual `tenant_<id>.beneficiaries` record is stored in a separate, highly restricted `token_mapping` table within the `tenant_<id>` schema. This table is only accessible by the Platform Administrator (ACT-086A974D63) and the specific NGO Operator (ACT-09E028AEB0).
  - **Merchant View**: Merchants (ACT-AF904DCFF9) only ever see the `beneficiary_token` and the credit balance. They cannot infer demographic status or legal names.

- **Row-Level Security (RLS) Policies**:
  - **Purpose**: To provide a database-level safety net against application-layer misconfigurations or direct SQL injection attacks.
  - **Policy Definition**: RLS policies are applied to all tables within `tenant_<id>` schemas.
  - **Policy Logic**:
    - `SELECT`: Only roles with `tenant_admin` or `ngo_operator` claims can select rows where `tenant_id` matches the JWT claim.
    - `INSERT/UPDATE/DELETE`: Restricted to `tenant_admin` and `ngo_operator` roles.
    - `ANONYMOUS_USER`: All other roles (Merchant, Donor) are denied access to the `tenant_<id>` schema entirely.

### 2.3 Data Residency and Jurisdictional Enforcement (CON-30EA97016B)

To comply with data residency and jurisdictional requirements ([CON-30EA97016B](../project_glossary.md#con-30ea97016b)) across the SF, NYC, and Chicago footprints, the Data Persistence Layer (SUR-FA61592CD4) is deployed in a multi-region Aurora PostgreSQL configuration.

- **Region-Aware Schema Routing**:
  - **SF Footprint**: Aurora PostgreSQL cluster in `us-west-2`. All `tenant_<id>` schemas for NGOs operating in SF are created in this cluster.
  - **NYC Footprint**: Aurora PostgreSQL cluster in `us-east-2`. All `tenant_<id>` schemas for NGOs operating in NYC are created in this cluster.
  - **Chicago Footprint**: Aurora PostgreSQL cluster in `us-east-1`. All `tenant_<id>` schemas for NGOs operating in Chicago are created in this cluster.

- **Cross-Region Data Replication Restrictions**:
  - **PII Replication**: PII data within `tenant_<id>` schemas is NOT replicated across regions. Each region maintains its own isolated copy of its tenant data.
  - **Shared Schema Replication**: The `public` schema (non-sensitive operational data) is replicated across regions using Aurora Global Database to ensure low-latency access for merchants and donors regardless of their location.
  - **Analytics Replication**: The `analytics` schema is replicated across regions for global reporting, but it contains only anonymized, aggregated data.

- **Jurisdictional Tagging**:
  - **Tenant Metadata**: Each `tenant_<id>` schema includes a `jurisdiction_code` field (e.g., `US-CA`, `US-NY`, `US-IL`) that is immutable after creation.
  - **Access Control Enforcement**: The API Orchestration Layer (SUR-85E4A5B6E7) validates that the requesting user's jurisdiction matches the tenant's jurisdiction before allowing access to the `tenant_<id>` schema. Cross-jurisdictional access is denied unless explicitly authorized by a Platform Administrator (ACT-086A974D63) for audit purposes.

### 2.4 Knowledge Gaps and Assumptions

- `KNOWLEDGE_GAP: Exact Encryption Key Management Strategy - The specific KMS key rotation policy and key management service (e.g., AWS KMS vs. HashiCorp Vault) must be established by the Security Architecture team. Evidence needed: Security team's preferred key management standard.`
- `KNOWLEDGE_GAP: RLS Policy Enforcement Performance Impact - The performance impact of RLS policies on high-throughput queries (e.g., POS callbacks) must be benchmarked. Evidence needed: Load testing results from the Development phase.`
- `ASSUMPTION: Tenant ID Generation - It is assumed that tenant_id will be a UUIDv4 generated at NGO onboarding. Owner: Platform Administrator (ACT-086A974D63). Evidence needed: Confirmation from the User State & Profile Data Model artifact.`
- `ASSUMPTION: Jurisdiction Code Standard - It is assumed that jurisdiction codes will follow the ISO 3166-2 standard (e.g., US-CA). Owner: Compliance Team. Evidence needed: Confirmation from the Data Residency & Jurisdictional Compliance artifact.`

### 2.5 Integration Points and Dependencies

- **API Orchestration Layer (SUR-85E4A5B6E7)**: Must inject the `tenant_id` and `role` claims from the JWT into the database connection context to enable RLS.
- **Identity & Access Management (CAP-IDENTITY-ACCESS-MANAGEMENT)**: Must ensure that JWTs contain the correct `tenant_id` and `role` claims for each actor.
- **Financial Ledger Data Model**: Must ensure that financial transactions are linked to the correct `tenant_id` for reconciliation and payout.
- **Merchant Payout Failure & Error Handling**: Must ensure that payout errors are logged with the correct `tenant_id` for audit purposes.

This design ensures that the Data Persistence Layer (SUR-FA61592CD4) provides a robust, compliant, and scalable foundation for the MealCredit platform, strictly enforcing data isolation and residency requirements.

### 3.1 Middleware Logic: JWT Validation & Tenant Isolation

All requests to the Client Interface Layer ([SUR-43E71C4E2B](../project_glossary.md#sur-43e71c4e2b)) must pass through the Access Control Middleware. This middleware is responsible for:

1. **JWT Verification**: Validates the JSON Web Token (JWT) signature, expiration, and issuer (`iss`) claims. The JWT must contain the `sub` (subject/actor ID), `role` (actor role), and `tenant_id` (metro footprint: SF, NYC, or CHI) claims.
2. **Tenant Isolation Enforcement**: Extracts the `tenant_id` from the JWT and injects it into the request context. All downstream API handlers must use this `tenant_id` to scope database queries and resource access, ensuring strict multi-tenant isolation ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4)).
3. **Role-Based Access Control (RBAC)**: Checks the `role` claim against the requested endpoint's required permissions. If the role does not have explicit permission, the middleware returns a `403 Forbidden` response.
4. **PCI-DSS Compliance Gate**: For any endpoint related to payment instruments (e.g., Donor Funding), the middleware must verify that the request does not contain raw card data fields (e.g., `card_number`, `cvv`). If such fields are detected, the request is immediately rejected with a `400 Bad Request` and an audit log entry is generated.

### 3.2 Journey-Specific API Contracts

#### 3.2.1. Merchant Onboarding (JNY-356F465DB3)

- **Endpoint**: `POST /api/v1/merchants/onboard`
- **Required Role**: NGO Operator (ACT-09E028AEB0) or Platform Administrator (ACT-086A974D63)
- **Tenant Scope**: `tenant_id` from JWT must match the merchant's target metro footprint.

**Request Schema**:

{
  "merchant_name": "string (required, max 100 chars)",
  "dba_name": "string (required, max 100 chars)",
  "address": {
    "street": "string (required)",
    "city": "string (required)",
    "state": "string (required, 2-letter code)",
    "zip": "string (required, 5-digit US zip)"
  },
  "contact_email": "string (required, valid email)",
  "contact_phone": "string (required, valid phone)",
  "tax_id": "string (required, SSN/EIN format)",
  "bank_account": {
    "routing_number": "string (required, 9-digit ABA)",
    "account_number": "string (required, masked in transit via Stripe Elements)"
  }
}

**Response Schema**:

{
  "merchant_id": "string (UUIDv4)",
  "status": "string (pending_approval | active | rejected)",
  "stripe_account_id": "string (nullable, provided by Stripe Issuing Proxy Contract)"
}

**Error Handling**:
- `400 Bad Request`: Invalid schema or missing required fields.
- `403 Forbidden`: Role does not have permission to onboard merchants.
- `409 Conflict`: Merchant with the same tax_id or bank_account already exists in the tenant.

#### 3.2.2. Donor Onboarding & Funding Activation (JNY-62D850E94B)

- **Endpoint**: `POST /api/v1/donors/fund`
- **Required Role**: Donor (ACT-80C62C7814)
- **Tenant Scope**: `tenant_id` from JWT (Donor's home metro).

**Request Schema**:

{
  "amount_cents": "integer (required, > 0)",
  "payment_method_id": "string (required, Stripe PaymentMethod ID)"
}

*Note: The `payment_method_id` is obtained client-side via Stripe Elements. No raw card data is transmitted in this request.*

**Response Schema**:

{
  "transaction_id": "string (UUIDv4)",
  "status": "string (success | failed)",
  "donor_credit_balance_cents": "integer (updated balance)"
}

**Error Handling**:
- `400 Bad Request`: Invalid amount or `payment_method_id`.
- `401 Unauthorized`: Invalid or expired JWT.
- `402 Payment Required`: Payment failed (e.g., insufficient funds, card declined).
- `409 Conflict`: Donor has reached their monthly funding limit (if applicable).

#### 3.2.3. Beneficiary Eligibility & Voucher Redemption (JNY-E82B8A88D8)

- **Endpoint**: `POST /api/v1/beneficiaries/redeem`
- **Required Role**: Beneficiary (ACT-ADA6716160)
- **Tenant Scope**: `tenant_id` from JWT (Beneficiary's home metro).

**Request Schema**:

{
  "merchant_id": "string (required, UUIDv4)",
  "redemption_amount_cents": "integer (required, > 0)",
  "voucher_token": "string (required, HMAC-signed token from PII Segregation & Anonymization Strategy)"
}

**Response Schema**:

{
  "redemption_id": "string (UUIDv4)",
  "status": "string (success | failed)",
  "receipt_url": "string (nullable, URL to anonymized receipt)"
}

**Error Handling**:
- `400 Bad Request`: Invalid schema or `voucher_token` format.
- `401 Unauthorized`: Invalid or expired JWT.
- `403 Forbidden`: Beneficiary is not eligible for redemption in this tenant or `merchant_id` is not in the same tenant.
- `409 Conflict`: Redemption amount exceeds remaining balance.

### 3.3 Access Control Matrix (RBAC)

| Endpoint | Platform Administrator (ACT-086A974D63) | NGO Operator (ACT-09E028AEB0) | Dispute Adjudicator (ACT-7BA340FF76) | Donor (ACT-80C62C7814) | Beneficiary (ACT-ADA6716160) | Merchant (ACT-AF904DCFF9) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST /api/v1/merchants/onboard` | WRITE | WRITE | - | - | - | - |
| `GET /api/v1/merchants/{id}` | READ | READ (own) | - | - | - | READ (own) |
| `POST /api/v1/donors/fund` | - | - | - | WRITE | - | - |
| `GET /api/v1/donors/{id}/balance` | READ | READ (own) | - | READ (own) | - | - |
| `POST /api/v1/beneficiaries/redeem` | - | - | - | - | WRITE | - |
| `GET /api/v1/beneficiaries/{id}/history` | READ | READ (own) | READ (audit) | - | READ (own) | - |
| `POST /api/v1/disputes/submit` | - | WRITE | WRITE | - | WRITE | WRITE |
| `GET /api/v1/disputes/{id}` | READ | READ (own) | READ | READ (own) | READ (own) | READ (own) |

### 3.4 SOC2 Type II Structural Planning (CON-81FB01F06B)

- **Audit Logging**: All administrative ledger operations and infrastructure changes are logged to AWS CloudTrail for SOC2 Type II evidence ([CON-FBBBF07295](../project_glossary.md#con-fbbbf07295)).
- **Access Reviews**: Regular access reviews are conducted by the Platform Administrator (ACT-086A974D63) to ensure that role assignments and permissions remain aligned with current job functions.

### 3.5 FTC Anonymity Guidelines (CON-B3D71A437D)

- **Data Segregation**: Beneficiary demographic data is cryptographically segregated from public analytics (CON-0A0288EED4). This prevents de-anonymization attacks that could link beneficiaries to donors through metadata analysis.
- **Anonymized Reporting**: All donor impact receipts and redemption analytics are generated using aggregated, non-reversible data (CON-23A501C051). No PII is included in donor-facing communications.

## 4. Operational Resilience & Error Handling

### 4.1 Token Revocation & Session Management

- **Revocation List**: JWTs are short-lived, and a revocation list (e.g., Redis) is used to track invalidated tokens. This ensures that compromised tokens can be immediately invalidated.
- **Session Timeout**: Sessions are automatically terminated after a period of inactivity, requiring re-authentication.

### 4.2 Error Handling Standards

- **Consistent Error Responses**: All API errors follow a standardized format, including an error code, a human-readable message, and a reference to relevant documentation.
- **Audit Logging**: All access violations, failed authentication attempts, and suspicious activities are logged for security monitoring and incident response.

## 5. Future Considerations & Scalability

- **Dynamic Tenant Provisioning**: The system supports dynamic tenant provisioning, allowing new NGOs to be onboarded without requiring database schema changes.
- **Cross-Tenant Analytics**: While data is strictly isolated, aggregated analytics across tenants are supported through the `analytics` schema, enabling platform-wide insights without compromising individual tenant privacy.

### 5.3 Compliance & Audit Logging

All access control decisions (allow/deny) and payment-related events (fund/redeem) must be logged to AWS CloudTrail ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2)) for SOC2 Type II evidence. Logs must include:
- timestamp
- actor_id (from JWT sub)
- actor_role (from JWT role)
- tenant_id (from JWT tenant_id)
- endpoint (e.g., `POST /api/v1/donors/fund`)
- action (e.g., FUND_INITIATED)
- result (e.g., SUCCESS, FAILED, FORBIDDEN)
- request_id (for traceability)

No PII (e.g., beneficiary legal names, donor payment details) may be included in these logs.

This artifact's [concern] defers to [Stripe Issuing Proxy Contract] for [payment instrument handling]; see that artifact for the full treatment.
This artifact's [concern] defers to [Next.js Dashboard Architecture] for [dashboard component integration]; see that artifact for the full treatment.

---

### 5.4 AWS CloudTrail Integration for Infrastructure & API Orchestration

AWS CloudTrail will be enabled on the API Orchestration Layer (SUR-85E4A5B6E7) to capture all administrative actions, identity management events, and infrastructure-as-code deployments. This satisfies the requirement to log all administrative ledger operations and infrastructure changes (CON-BB253DF0A2).

Scope of CloudTrail Logging:
- Management Events: All calls to AWS services that create, modify, or delete resources (e.g., IAM role changes, S3 bucket policy updates, RDS instance modifications).
- Data Events: S3 bucket access logs for storing audit artifacts and CloudWatch Logs API calls.
- Custom API Gateway Logging: All GraphQL and gRPC requests passing through the API Orchestration Layer (SUR-85E4A5B6E7) will be logged with full request/response headers (excluding PII payloads) to CloudWatch Logs, which are then forwarded to CloudTrail for centralized correlation.

Retention and Integrity:
- CloudTrail logs will be stored in an S3 bucket with Object Lock enabled in Governance mode to prevent deletion or modification for a minimum of 7 years, satisfying SOC2 Type II retention requirements.
- Log file validation will be enabled to ensure that logs have not been tampered with since delivery.

Knowledge Gap:
- `knowledge_gap: CloudTrail log retention period must be established by the Compliance Officer to align with specific jurisdictional requirements for financial data (e.g., 7 years for PCI-DSS vs. 3 years for general SOC2).`

### 5.5 Append-Only Cryptographic Ledger in Aurora PostgreSQL

All financial ledger mutations (donations, credit distributions, merchant payouts, refunds) and beneficiary state changes (eligibility, offboarding) will be recorded in an append-only table within Aurora PostgreSQL. This ledger will use cryptographic hashing to create a tamper-evident chain, satisfying the requirement for append-only cryptographic log auditing ([CON-1762EA5021](../project_glossary.md#con-1762ea5021)).

Ledger Table Schema Design:
- ledger_id: UUIDv4, primary key.
- timestamp: TIMESTAMPTZ, indexed.
- actor_id: UUID, references the actor (ACT-086A974D63, ACT-09E028AEB0, etc.).
- action_type: ENUM (e.g., 'DONATION_RECEIVED', 'CREDIT_ISSUED', 'MERCHANT_PAYOUT_INITIATED', 'BENEFICIARY_OFFBOARDED').
- payload_hash: VARCHAR(64), SHA-256 hash of the transaction payload.
- previous_hash: VARCHAR(64), SHA-256 hash of the previous ledger entry.
- block_number: BIGINT, auto-incrementing sequence number.
- signature: VARCHAR(128), digital signature of the entry by the signing key.

Cryptographic Chain Integrity:
Each new entry's previous_hash is computed from the ledger_id, timestamp, actor_id, action_type, payload_hash, and signature of the immediately preceding entry.
The signature is generated using a hardware security module (HSM) or AWS KMS key, ensuring that only authorized services can append to the ledger.
Any attempt to modify a historical entry will break the hash chain, which will be detected by periodic integrity checks.

Integrity Verification Process:
- A background worker will perform daily integrity checks by recomputing the hash chain from the first entry to the current entry and comparing it against a stored root hash.
- Any discrepancy will trigger an immediate alert to the Platform Administrator (ACT-086A974D63) and trigger a forensic investigation workflow.

Knowledge Gap:
- `knowledge_gap: The specific KMS key management strategy (e.g., AWS KMS vs. HashiCorp Vault) for signing ledger entries must be established by the Security Architect to ensure key rotation and access control policies are aligned with SOC2 Type II requirements.`

### 5.6 Audit Log Correlation and Access Control

To ensure that audit logs are themselves protected from unauthorized access or modification, access to the CloudTrail S3 bucket and the Aurora PostgreSQL ledger table will be strictly controlled via IAM policies and RLS policies.

Access Control for Audit Logs:
- Only the Platform Administrator (ACT-086A974D63) and Dispute Adjudicator (ACT-7BA340FF76) roles will have read access to the CloudTrail S3 bucket and the Aurora PostgreSQL ledger table.
- All access to audit logs will be logged to a separate, immutable audit log table to prevent log tampering.

Correlation Strategy:
- Each CloudTrail event will include a requestId that is correlated with the corresponding Aurora PostgreSQL ledger entry via a correlation_id field in the ledger table.
- This allows for end-to-end tracing of an administrative action from the API gateway (CloudTrail) to the database (Aurora PostgreSQL).

Knowledge Gap:
- `knowledge_gap: The specific correlation_id generation strategy (e.g., UUIDv4, trace ID from distributed tracing) must be established by the Development Lead to ensure seamless correlation between CloudTrail events and Aurora PostgreSQL ledger entries.`

### 6.1 Identity & Access Management (IAM) Architecture

The platform utilizes a centralized Identity Provider (IdP) to issue JSON Web Tokens (JWTs) that enforce Role-Based Access Control (RBAC) and Multi-Tenant Isolation. The JWT structure is the single source of truth for authorization decisions at the API Orchestration Layer (SUR-85E4A5B6E7).

#### 5.1.1 Canonical Actor Roles & JWT Claims

All actor interactions are mediated through JWTs containing the following standard and custom claims:

| Claim | Description | Scope |
|---|---|---|
| sub | Unique Subject Identifier (UUIDv4) | All Actors |
| iss | Issuer (IdP URL) | System |
| exp | Expiration Timestamp | System |
| role | Primary Role Identifier | See Actor Registry |
| tenant_id | Metro Footprint Identifier | SF, NYC, CHI |
| scope | Granular Permission Set | Role-Dependent |

Actor Role Registry (Verbatim from Asset Registry):

- Platform Administrator (ACT-086A974D63): Full system access, infrastructure configuration, and cross-tenant oversight. Scope: `admin:`.
- NGO Operator (ACT-09E028AEB0): Manages beneficiary eligibility and NGO-specific fund pools. Scope: `ngo:manage`, `beneficiary:read`.
- Dispute Adjudicator (ACT-7BA340FF76): Reviews and resolves Beneficiary-Platform Dispute Flow (JNY-2B038C9362). Scope: `dispute:review`, `dispute:resolve`.
- Donor (ACT-80C62C7814): Initiates donations and views impact receipts. Scope: `donor:donate`, `donor:receipt`.
- Beneficiary (ACT-ADA6716160): Redeems credits at merchants. Scope: `beneficiary:redeem`, `beneficiary:profile`.
- Merchant (ACT-AF904DCFF9): Accepts payments and manages POS integration. Scope: `merchant:pos`, `merchant:payout`.

#### 5.1.2 Token Lifecycle & Revocation

- Access Token TTL: 15 minutes. Short-lived to minimize impact of token theft.
- Refresh Token TTL: 7 days. Stored securely in SecureStore on Expo devices ([CON-34312C6DC9](../project_glossary.md#con-34312c6dc9)) and in HTTP-only, Secure cookies for Next.js dashboards.
- Revocation Strategy: Access tokens are stateless. Revocation is handled via a short-lived blocklist (Redis) for critical events (e.g., account compromise, NGO offboarding). Refresh tokens are rotated on each use.

Data isolation is enforced at the database layer using Aurora PostgreSQL (SUR-FA61592CD4) to ensure strict separation of beneficiary PII and financial data across metro footprints.

#### 5.2.1 Schema Strategy

- Shared Public Schema: Contains non-sensitive, operational data (e.g., merchant locations, anonymized transaction aggregates, global configuration). Accessible by all roles with appropriate scope.
- Tenant-Specific Schemas (`tenant_<id>`): Contains sensitive PII (e.g., beneficiary legal names, demographic status) and tenant-specific financial ledgers. Access is restricted to roles with tenant_id matching the schema.
- Row-Level Security (RLS): Applied to shared tables where PII is hashed or tokenized (e.g., beneficiary_tokens) to prevent lateral movement even if schema isolation is bypassed.

#### 5.2.2 Data Isolation Enforcement

| Data Class | Isolation Mechanism | Enforcement Strategy | Concerns |
|---|---|---|---|
| Beneficiary PII (Name, Demographics) | `tenant_<id>` Schema | Schema Isolation + RLS | CON-0A0288EED4, CON-<timestamp> |
| Financial Ledger Entries | `tenant_<id>` Schema | Schema Isolation + RLS | CON-1762EA5021, [CON-6061FCCA83](../project_glossary.md#con-6061fcca83) |
| Merchant POS Data | Shared Public Schema | Role-Based Scope | [CON-4152F2C7C3](../project_glossary.md#con-4152f2c7c3) |
| Donor Transaction History | Shared Public Schema | Role-Based Scope | [CON-4820FAD5A9](../project_glossary.md#con-4820fad5a9) |
| Anonymized Analytics | Analytics Read-Replica | ETL Pipeline (No PII) | CON-23A501C051, [CON-413928CB1C](../project_glossary.md#con-413928cb1c) |

### 6.3 Access Control API Contracts

The API Orchestration Layer (SUR-85E4A5B6E7) enforces access control via middleware that validates JWT claims before routing requests to downstream services.

#### 5.3.1 Middleware Validation Logic

1. JWT Verification: Validate signature, issuer, and expiration.
2. Role Extraction: Extract role and scope from JWT.
3. Tenant Isolation: Extract tenant_id from JWT and inject into database connection context.
4. Scope Authorization: Verify that the requested API endpoint is included in the scope claim.
5. Audit Logging: Log all access control decisions to AWS CloudTrail (CON-BB253DF0A2, CON-FBBBF07295).

#### 5.3.2 Error Responses

- 401 Unauthorized: Invalid or expired JWT.
- 403 Forbidden: Valid JWT, but insufficient scope or tenant mismatch.
- 404 Not Found: Resource exists, but is not accessible by the current tenant (tenant isolation enforced).

#### 5.4.1 Audit Log Schema

| Field | Type | Description |
|---|---|---|
| timestamp | ISO 8601 | Event time |
| actor_id | UUID | Subject of the action |
| actor_role | String | Role from JWT |
| tenant_id | String | Metro footprint |
| action | String | API endpoint or database operation |
| resource_id | UUID | Target resource |
| outcome | String | SUCCESS, FAILURE |
| reason | String | Error message if FAILURE |
| ip_address | String | Client IP address |
| user_agent | String | Client user agent |

#### 5.4.2 Anonymization & De-anonymization Prevention

- FTC Guidelines Compliance: No de-anonymization attacks can link beneficiaries to donors through metadata analysis (CON-B3D71A437D, [CON-C22D030D21](../project_glossary.md#con-c22d030d21)).
- UUIDv4 Mapping: Donor impact receipts are correlated with beneficiary redemption events using UUIDv4 mapping, ensuring no PII is linked (CON-23A501C051, CON-413928CB1C).
- Data Retention: Strict data retention policies are enforced for donor transaction history vs. anonymous redemption analytics (CON-4820FAD5A9, [CON-6F604D5455](../project_glossary.md#con-6f604d5455)).

### 6.4 Validation & Testing

- Unit Tests: Validate JWT claim parsing and validation logic.
- Integration Tests: Verify API endpoints enforce tenant isolation and role-based scope.
- Security Penetration Testing: Test for token manipulation, replay attacks, and cross-tenant data leakage.
- Audit Log Verification: Ensure all access control decisions are logged correctly and are tamper-evident.
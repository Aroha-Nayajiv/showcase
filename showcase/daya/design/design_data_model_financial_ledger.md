# Financial Ledger Data Model

This section defines the authoritative Aurora PostgreSQL schema for the immutable financial ledger, ensuring strict typing, constraints, and PCI-DSS compliance for the MealCredit platform. It consolidates the core ledger, cryptographic audit logging, and PCI-DSS tokenization models into a single, non-redundant structure.

### 1.1 Design Principles and Constraints

The ledger schema is designed to satisfy the following critical requirements:
- **Immutability:** Financial transactions must be append-only. No UPDATE or DELETE operations are permitted on the ledger tables. This is enforced via database-level triggers and Row-Level Security (RLS) policies.
- **PCI-DSS Level 1 Compliance:** Zero raw card data (PAN) is stored. Only Stripe PaymentMethod IDs or Token IDs are referenced. The `donor_payment_methods` table stores only derived display data (last four digits) as permitted by PCI-DSS.
- **Anonymity:** Beneficiary demographic data is cryptographically segregated from public ledger entries. The `beneficiary_profiles` table is isolated, and the ledger references only anonymized hashes or UUIDs.
- **Traceability:** Every transaction is linked to a specific `credit_pool` and beneficiary (via anonymized hash) to enable reconciliation without PII leakage.
- **Cryptographic Integrity:** The ledger implements a hash-chained structure to prevent tampering with historical financial mutations, satisfying SOC2 Type II evidence requirements.

### 1.2 Core Schema Definitions

#### 1.2.1. credit_pools Table
Represents the source of funds for each metro footprint (SF, NYC, CHI). This table tracks the liquidity available for credit issuance.

```sql
CREATE TABLE credit_pools (
    pool_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metro_region VARCHAR(3) NOT NULL CHECK (metro_region IN ('SF', 'NYC', 'CHI')),
    total_allocated NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    available_balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    currency_code VARCHAR(3) NOT NULL DEFAULT 'USD',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Constraint: available_balance cannot be negative
ALTER TABLE credit_pools ADD CONSTRAINT chk_available_balance_non_negative
    CHECK (available_balance >= 0);
```

#### 1.2.2. financial_ledger Table (Immutable Core)
The single source of truth for all financial mutations (donations, credit issuances, redemptions, refunds, payouts). This table replaces the fragmented `ledger_entries` and `financial_ledger` tables from the executor draft to eliminate schema contradictions.

```sql
CREATE TABLE financial_ledger (
    ledger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence_number BIGINT NOT NULL,
    transaction_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'DONATION_RECEIVED', 
        'CREDIT_ISSUED', 
        'CREDIT_REDEEMED', 
        'REFUND_PROCESSED', 
        'PAYOUT_INITIATED',
        'ADJUSTMENT'
    )),
    amount_cents BIGINT NOT NULL CHECK (amount_cents > 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'USD',
    actor_id UUID NOT NULL, -- References the relevant actor (Donor, Beneficiary, Merchant, NGO)
    actor_type VARCHAR(20) NOT NULL CHECK (actor_type IN (
        'DONOR', 'BENEFICIARY', 'MERCHANT', 'NGO', 'PLATFORM'
    )),
    credit_pool_id UUID NOT NULL REFERENCES credit_pools(pool_id),
    metadata_jsonb JSONB NOT NULL DEFAULT '{}',
    previous_hash BYTEA NOT NULL,
    current_hash BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL, -- System or Actor ID
    CONSTRAINT uq_ledger_sequence UNIQUE (sequence_number),
    CONSTRAINT fk_previous_hash FOREIGN KEY (previous_hash) REFERENCES financial_ledger(current_hash)
);

```

**Key Design Decisions:**
- **sequence_number:** A monotonically increasing integer that provides a strict ordering of events, independent of `created_at` timestamps which may have slight variations. This is critical for deterministic hash chaining.
- **previous_hash:** A SHA-256 hash of the `current_hash` of the immediately preceding row (ordered by `sequence_number`). This creates a cryptographic chain where any modification to a historical record invalidates all subsequent hashes.
- **current_hash:** A SHA-256 hash of the row's content (`sequence_number`, `transaction_id`, `event_type`, `amount_cents`, `actor_id`, `metadata_jsonb`). This ensures data integrity for each individual record.
- **metadata_jsonb:** Stores flexible, non-indexed data related to the transaction (e.g., Stripe PaymentIntent ID, POS terminal ID, redemption location). This keeps the core schema lean and performant.

#### 1.2.3. donor_payment_methods Table (PCI-Compliant)
Stores the mapping between the MealCredit Donor ([ACT-80C62C7814](../project_glossary.md#act-80c62c7814)) and their Stripe payment method tokens. No raw card data is stored.

```sql
CREATE TABLE donor_payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id UUID NOT NULL, -- Reference to the users table (Donor role)
    stripe_payment_method_id VARCHAR(255) NOT NULL, -- The Stripe pm_... ID
    stripe_customer_id VARCHAR(255) NOT NULL, -- The Stripe cus_... ID
    card_brand VARCHAR(50) NOT NULL, -- e.g., 'visa', 'mastercard'
    last_four CHAR(4) NOT NULL, -- PCI Rule: Only last four digits
    expiry_month SMALLINT NOT NULL, -- PCI Rule: Stored for display only
    expiry_year SMALLINT NOT NULL, -- PCI Rule: Stored for display only
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

```

**PCI Compliance Note:** The `stripe_payment_method_id` is a token. It cannot be reverse-engineered to reveal the underlying PAN. The `last_four`, `expiry_month`, and `expiry_year` are considered "derived" data from the token and are permitted for display purposes under PCI-DSS.

#### 1.2.4. beneficiary_profiles Table (Segregated PII)
Segregated PII table. Only accessible by authorized roles (e.g., Platform Administrator, NGO Operator) for compliance purposes. This table is not directly joinable with the `financial_ledger` in standard queries.

```sql
CREATE TABLE beneficiary_profiles (
    beneficiary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name_hash VARCHAR(64) NOT NULL, -- SHA-256 hash of legal_name + ngo_id + salt
    demographic_status VARCHAR(50) NOT NULL, -- e.g., 'eligible', 'pending'
    ngo_id UUID NOT NULL, -- Reference to NGO Operator (ACT-09E028AEB0)
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_legal_name_hash UNIQUE (legal_name_hash)
);

```

**Anonymization Strategy:** The `financial_ledger` table stores an anonymized `actor_id` (UUIDv4) for beneficiaries. This `actor_id` is mapped to the `beneficiary_profiles` table only through a separate, highly restricted mapping table (`beneficiary_id_mapping`) that is also subject to strict RLS policies. This ensures that donor impact receipts can be correlated with beneficiary redemption events using UUIDv4 mapping ([CON-23A501C051](../project_glossary.md#con-23a501c051)) without linking PII.

#### 1.3.2. Row-Level Security (RLS) Policies
RLS policies are enforced to prevent UPDATE and DELETE operations on the `financial_ledger` table for all roles except the `Platform Administrator` ([ACT-086A974D63](../project_glossary.md#act-086a974d63)), who may only perform SELECT operations for audit purposes.

```sql
ALTER TABLE financial_ledger ENABLE ROW LEVEL SECURITY;

-- Prevent all modifications except inserts
CREATE POLICY prevent_updates_deletes ON financial_ledger
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Allow inserts only through the trigger
CREATE POLICY allow_inserts ON financial_ledger
    FOR INSERT
    WITH CHECK (true);
```

### 1.3 Performance and Scalability Considerations

- **Partitioning:** The `financial_ledger` table will be partitioned by `created_at` (monthly) to manage growth and optimize query performance for recent transactions. Historical partitions can be archived to cold storage.
- **Indexing:**
  - `idx_ledger_transaction_id`: Index on `transaction_id` for fast lookups by transaction.
  - `idx_ledger_actor_id`: Index on `actor_id` for querying an actor's transaction history.
  - `idx_ledger_event_type`: Index on `event_type` for filtering by transaction type.
- **Hash Computation:** SHA-256 is used for hash computation due to its balance of security and performance. The `pgcrypto` extension is required.

### 1.4 Knowledge Gaps and Assumptions

- **KNOWLEDGE_GAP: The exact format of the metadata JSONB field needs to be defined by the Transaction & Financial Engine ([CAP-TRANSACTION-FINANCIAL-ENGINE](../project_glossary.md#cap-transaction-financial-engine)) to ensure consistency across all transaction types.**
- **KNOWLEDGE_GAP: The specific hashing algorithm for legal_name_hash (e.g., SHA-256, SHA-3) needs to be confirmed with the Security team to ensure compliance with current standards.**
- **ASSUMPTION: pgcrypto Extension:** It is assumed that the `pgcrypto` extension is enabled in the Aurora PostgreSQL instance for SHA-256 hash computation. If not, a custom function or application-level hashing will be required.
- **ASSUMPTION: gen_random_uuid():** It is assumed that the `pgcrypto` extension is also used for UUID generation. If not, `uuid-ossp` or application-level UUID generation will be required.
- **KNOWLEDGE_GAP: ledger_id vs transaction_id:** The schema includes both `ledger_id` (primary key) and `transaction_id` (business identifier). It is assumed that `transaction_id` is generated by the `Transaction & Financial Engine` (CAP-TRANSACTION-FINANCIAL-ENGINE) and is unique across the system. If `transaction_id` is not globally unique, a composite key or additional indexing may be required.

### 1.5 Validation and Verification

- **Integrity Checks:** Periodic integrity checks will be run to verify the hash chain. Any broken chain will trigger an immediate alert to the `Platform Administrator` (ACT-086A974D63).
- **Audit Trail:** All administrative operations on the ledger (e.g., manual adjustments, which should be rare) will be logged in a separate `ledger_audit_log` table, which is also append-only and hash-chained.
- **Unit Tests:** Verify that no raw card data (PAN, CVV) is ever logged or stored in the `ledger_entries` or `donor_payment_methods` tables.
- **Integration Tests:** Verify that the Stripe tokenization flow works correctly and that the `stripe_payment_method_id` is correctly stored and used for subsequent transactions.
- **Penetration Testing:** Conduct regular penetration tests to ensure that no vulnerabilities exist that could allow extraction of raw card data from the Stripe tokens or the database.
- **PCI-DSS Compliance Audit:** Regular audits by a Qualified Security Assessor (QSA) to ensure ongoing compliance with PCI-DSS Level 1 requirements.

This schema provides a robust, cryptographically secure, and compliant foundation for the financial ledger, ensuring traceability and integrity for SOC2 Type II evidence.

### 1.6 Immutability and Cryptographic Chaining Enforcement

To guarantee append-only behavior and prevent unauthorized modifications, the following database-level mechanisms are implemented:

#### 1.3.1. Trigger Function for Hash Chaining
A `BEFORE INSERT` trigger ensures that the `previous_hash` is correctly set to the `current_hash` of the last inserted row. This automates the cryptographic linking process.

```sql
CREATE OR REPLACE FUNCTION fn_ledger_hash_chain()
RETURNS TRIGGER AS $$
DECLARE
    last_row RECORD;
BEGIN
    -- Fetch the most recent row by sequence_number
    SELECT current_hash INTO last_row
    FROM financial_ledger
    ORDER BY sequence_number DESC
    LIMIT 1;

    -- If no previous row exists, use a genesis hash (e.g., SHA-256 of 'genesis')
    IF last_row IS NULL THEN
        NEW.previous_hash := digest('genesis', 'sha256');
    ELSE
        NEW.previous_hash := last_row.current_hash;
    END IF;

    -- Calculate current hash
    NEW.current_hash := digest(
        NEW.sequence_number::text || 
        NEW.transaction_id::text || 
        NEW.event_type || 
        NEW.amount_cents::text || 
        NEW.actor_id::text || 
        NEW.metadata_jsonb::text,
        'sha256'
    );
```

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ledger_hash_chain
    BEFORE INSERT ON financial_ledger
    FOR EACH ROW
    EXECUTE FUNCTION fn_ledger_hash_chain();

### 1.7 Data Isolation and Anonymization

To comply with FTC guidelines on anonymity ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d), [CON-C22D030D21](../project_glossary.md#con-c22d030d21)) and ensure strict data isolation ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4), [CON-92F07E31B0](../project_glossary.md#con-92f07e31b0)), beneficiary PII is cryptographically segregated from the financial ledger.

- **Beneficiary PII Storage:** Beneficiary demographic data and legal names are stored in the `beneficiary_profiles` table, which is not directly joinable with the `financial_ledger` table in standard queries. Access to this table is restricted to the `NGO Operator` ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) and `Platform Administrator` (ACT-086A974D63) roles.
- **Anonymized Ledger Entries:** The `financial_ledger` table only stores an anonymized `actor_id` for beneficiaries. This `actor_id` is a UUIDv4 that is mapped to the beneficiary's PII only through a separate, highly restricted mapping table (`beneficiary_id_mapping`) that is also subject to strict RLS policies.
- **UUIDv4 Mapping for Analytics:** As per CON-23A501C051 and [CON-413928CB1C](../project_glossary.md#con-413928cb1c), donor impact receipts are correlated with beneficiary redemption events using UUIDv4 mapping, ensuring no PII is linked in the analytics layer.

## 2. Transaction & Financial Engine API Contracts

This section defines the synchronous and asynchronous API contracts for the Transaction & Financial Engine (CAP-TRANSACTION-FINANCIAL-ENGINE). These contracts govern the creation of MealCredits, their redemption at Merchant POS terminals, and the subsequent financial reconciliation. The design prioritizes low-latency clearance for POS interactions (targeting <150ms for webhook processing as per [CON-06232374D9](../project_glossary.md#con-06232374d9)) and strict idempotency to prevent double-spending.

### 2.1 Voucher Creation & Issuance (Donor/NGO -> Beneficiary)

This contract handles the conversion of donor funds into fractional, anonymous culinary credits for beneficiaries. It is triggered by the NGO Operator (ACT-09E028AEB0) or Donor (ACT-80C62C7814) via the GraphQL layer, which then invokes the Financial Engine.

**Endpoint:** `POST /api/v1/credits/issue`
**Auth:** JWT (Bearer Token) with scopes: `credits:issue`, `donor:manage`
**Latency Target:** <200ms (synchronous acknowledgment)

**Request Body:**

{
 "idempotency_key": "string (UUIDv4, required)",
 "beneficiary_id": "string (UUIDv4, required)",
 "amount_cents": "integer (required)",
 "currency_code": "string (ISO 4217, default: USD)",
 "metadata": {
 "campaign_id": "string (optional, for donor impact tracking)",
 "anonymous_flag": "boolean (default: true, ensures PII segregation)"
 }
}

**Response (201 Created):**

{
 "transaction_id": "string (UUIDv4, unique ledger entry)",
 "status": "string (ISSUED)",
 "amount_cents": "integer",
 "timestamp": "string (ISO 8601 UTC)"
}

**Error Handling:**
- `409 Conflict`: `idempotency_key` already exists. Returns the original successful response.
- `402 Payment Required`: Source account has insufficient funds or Stripe authorization failed.
- `422 Unprocessable Entity`: Invalid `beneficiary_group_id` or amount constraints violated.

### 2.2 POS Scanning & Redemption Callback (Merchant -> Financial Engine)

This contract handles real-time voucher redemption at Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) POS terminals. It is a high-throughput, low-latency endpoint designed to clear transactions quickly to prevent queue stagnation ([CON-4152F2C7C3](../project_glossary.md#con-4152f2c7c3)). It relies on the gRPC service layer for internal communication with the Ledger and Credit Pool services.

**Endpoint:** `POST /api/v1/pos/redemption/validate`
**Auth:** mTLS (Mutual TLS) with Merchant API Key and Certificate
**Latency Target:** <50ms (internal processing), <150ms (total round-trip)

**Request Body:**

{
 "merchant_id": "string (UUIDv4, required)",
 "voucher_token": "string (required, time-bound cryptographic signature)",
 "transaction_reference": "string (UUIDv4, merchant's internal POS ID)",
 "geo_location": {
 "latitude": "float",
 "longitude": "float",
 "metro_region": "string (SF, NYC, CHI)"
 }
}

**Response (200 OK):**

{
 "status": "APPROVED",
 "transaction_id": "string (UUIDv4)",
 "receipt_hash": "string (SHA-256 of receipt data for audit)",
 "timestamp": "string (ISO 8601 UTC)"
}

**Response (402 Insufficient Funds):**

{
 "status": "DECLINED",
 "message": "Beneficiary credit pool balance is insufficient for this transaction."
}

**Error Handling:**
- `401 Unauthorized`: Invalid mTLS certificate or expired Merchant API Key.
- `400 Bad Request`: Invalid `voucher_token` signature or expired token (time-bound cryptographic signatures per [CON-3335D67672](../project_glossary.md#con-3335d67672)).
- `409 Conflict`: `transaction_reference` already processed (idempotency check).

### 2.3 Payout Processing & Reconciliation (Financial Engine -> Stripe/NGO)

This contract manages the periodic settlement of funds from the platform's holding accounts to Merchant partners and the reconciliation of donor funds. It is an asynchronous process triggered by the Financial Reconciliation & Payout Workers (sibling artifact).

**Endpoint:** `POST /api/v1/payouts/process`
**Auth:** Internal Service-to-Service (JWT with `payout:process` scope)
**Latency Target:** N/A (Asynchronous batch processing)

**Request Body:**

{
 "batch_id": "string (UUIDv4, required)",
 "payout_type": "enum [MERCHANT_SETTLEMENT, NGO_FEE_RECONCILIATION]",
 "items": [
 {
 "merchant_id": "string (UUIDv4)",
 "amount_cents": "integer",
 "fee_amount_cents": "integer (platform fee, if applicable)"
 }
 ],
 "net_payout_cents": "integer"
}

**Response (202 Accepted):**

{
 "batch_id": "string (UUIDv4)",
 "status": "ACCEPTED",
 "ledger_entries_created": "integer (count of new immutable ledger entries)"
}

**Error Handling:**
- `400 Bad Request`: Invalid `payout_type` or malformed `items` array.
- `500 Internal Server Error`: Stripe Connected Account ([CON-5BFA25E8F9](../project_glossary.md#con-5bfa25e8f9)) integration failure or ledger write failure.

### 2.4 Idempotency & Consistency Guarantees

To ensure data integrity and prevent double-spending ([CON-61EC670500](../project_glossary.md#con-61ec670500)), all write operations (Issuance, Redemption, Payout) MUST support idempotency keys. The Financial Engine will:
1. Check for the existence of the `idempotency_key` (or `transaction_reference`) in the `financial_ledger` table.
2. If found, return the original successful response without re-processing.
3. If not found, proceed with the transaction, create a new ledger entry, and store the key.

The `current_hash` field in all responses provides a cryptographic link to the previous entry, ensuring the append-only nature of the ledger ([CON-1762EA5021](../project_glossary.md#con-1762ea5021)). Any attempt to modify a historical entry will invalidate the hash chain, triggering an immediate alert.

### 2.5 Latency & Availability Optimization

To meet the <150ms latency target for POS clearance (CON-06232374D9):
- **Caching:** Credit pool balances will be cached in Redis ([CON-527BFA6796](../project_glossary.md#con-527bfa6796)) with a short TTL (e.g., 5 seconds) to reduce database load. Cache invalidation will occur immediately after a successful redemption.
- **Connection Pooling:** The gRPC service layer will use persistent connections to the Aurora PostgreSQL database to minimize handshake overhead.
- **Asynchronous Logging:** Audit logs ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2)) will be written asynchronously to AWS CloudTrail to avoid blocking the critical redemption path.

### 2.6 Encryption at Rest and in Transit
- **Encryption at Rest:** All columns in `financial_ledger`, `donor_payment_methods`, and `beneficiary_profiles` are encrypted at rest using AWS RDS encryption (AES-256). The `stripe_payment_method_id` and `last_four` fields are particularly sensitive and must be included in the encryption scope.
- **Encryption in Transit:** All data in transit is encrypted using TLS 1.3. API endpoints must enforce HTTPS.

### 2.7 Access Control
- **Access Control:** Access to the `financial_ledger` and `donor_payment_methods` tables is restricted to the `Transaction & Financial Engine` service account and the `Platform Administrator` (ACT-086A974D63) for audit purposes. Direct SQL access by developers is prohibited.
- **Audit Logging:** All access to these tables is logged via AWS CloudTrail (CON-BB253DF0A2) and internal audit logs ([CON-FBBBF07295](../project_glossary.md#con-fbbbf07295)) to ensure traceability for SOC2 Type II compliance.
# Next.js Dashboard Architecture

This section defines the Next.js App Router layout structure, Server-Side Rendering (SSR) strategy, and Server-Sent Events (SSE) integration for the three primary dashboards (Admin, Restaurant, NGO). The architecture prioritizes strict data isolation and role-based access control (RBAC) to ensure PCI-DSS Level 1 compliance and absolute anonymization of beneficiary data.

## 1. Root Layout and Middleware Enforcement

The application utilizes a single Next.js App Router root layout (`app/layout.tsx`) that serves as the entry point for all authenticated users. To enforce security and role-based access, a Next.js Middleware (`middleware.ts`) is implemented at the edge.

### 1.1 Middleware Logic
The middleware intercepts all requests to `/dashboard/`. It validates the JSON Web Token (JWT) issued by the Identity Provider (IdP) and extracts the user's role claim.

### 1.2 RBAC Enforcement
The middleware implements a strict allow-list routing strategy. If a user's role does not match the required role for the requested path, the middleware immediately returns a `403 Forbidden` response. This prevents unauthorized access to specific dashboard surfaces before any rendering or data fetching occurs.

### 1.3 Role Mapping
The middleware maps JWT claims to the following actor roles:
- `Platform Administrator` ([ACT-086A974D63](../project_glossary.md#act-086a974d63))
- `NGO Operator` ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0))
- `Merchant` ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9))

## 2. Dynamic Route Structure

The dashboard is structured using dynamic routes to encapsulate role-specific navigation and data fetching. This ensures that each role's UI components are isolated and only loaded when necessary.

## 3. Server-Side Rendering (SSR) Strategy

To ensure secure hydration of initial dashboard state and prevent PII leakage, all dashboard components are implemented as Server Components (RSC). This approach ensures that sensitive data is fetched and processed on the server, and only sanitized, role-appropriate data is sent to the client.

### 3.1 Server Components (RSC)
All initial dashboard data fetching is performed using Server Components. This ensures that zero PII is leaked to the client bundle, satisfying [CON-0A0288EED4](../project_glossary.md#con-0a0288eed4) (strict data isolation) and [CON-66390130AA](../project_glossary.md#con-66390130aa) (PCI-DSS compliance).

### 3.2 Data Fetching Patterns
- **Admin Dashboard**: Fetches aggregated financial metrics and user management data from the backend API. Data is pre-sanitized to remove any PII before being passed to the client.
- **NGO Dashboard**: Fetches beneficiary eligibility data and impact reports. Beneficiary demographic status and legal names are cryptographically segregated from public-facing data, as per CON-0A0288EED4.
- **Merchant Dashboard**: Fetches transaction history and payout status. Data is fetched in real-time to ensure merchants have up-to-date information on their POS integrations.

## 4. Server-Sent Events (SSE) Integration for Real-Time Dashboard Updates

This section defines the Server-Sent Events (SSE) architecture for the Next.js Dashboard, enabling low-latency, real-time visibility into transaction statuses, payout updates, and credit pool utilization for the `Platform Administrator` (ACT-086A974D63), `NGO Operator` (ACT-09E028AEB0), and `Merchant` (ACT-AF904DCFF9). This design replaces the legacy polling/WebSockets approach with an event-driven serverless architecture, aligning with the system evolution objective to modernize the platform's real-time data delivery.

### 4.1 Architectural Overview and Data Flow
The SSE integration leverages the Next.js App Router's streaming capabilities to push updates from the backend to the dashboard clients. The architecture ensures that sensitive financial data is streamed securely without exposing PII, adhering to the strict data isolation requirements (CON-0A0288EED4) and PCI-DSS Level 1 compliance (CON-66390130AA).

1. **Client Initialization**: The Next.js Dashboard client (React Server Components) initializes an EventSource connection upon mounting, authenticated via a short-lived JWT passed in the query parameters or headers.
2. **Stream Routing**: The Next.js API route (`/api/dashboard/stream`) acts as a proxy, validating the user's role and tenant context. It subscribes to the internal event bus for events relevant to the user's scope.
3. **Event Filtering**: The backend filters events based on the user's role and jurisdictional data residency constraints ([CON-30EA97016B](../project_glossary.md#con-30ea97016b)). For example, a Merchant in SF only receives events related to their specific POS terminals and local credit pools.
4. **Stream Delivery**: The validated and filtered events are serialized into the SSE format and streamed to the client with minimal latency, targeting the p99 latency threshold of 250ms for voucher creation and scanning callbacks ([CON-6D5E21557B](../project_glossary.md#con-6d5e21557b)).

### 4.3 Event Stream Schema
The event stream defines the structure of the data pushed to the dashboard. Each event type corresponds to a specific business action or state change.

| Event Type | Description | Payload Schema | Target Roles |
| :--- | :--- | :--- | :--- |
| `transaction.update` | Real-time update on a POS transaction status (e.g., cleared, pending, failed). | `{ "transaction_id": "uuid", "status": "string", "amount": "number", "timestamp": "ISO8601" }` | `Merchant` (ACT-AF904DCFF9), `NGO Operator` (ACT-09E028AEB0) |
| `payout.status` | Update on the status of a merchant payout (e.g., initiated, completed, failed). | `{ "payout_id": "uuid", "status": "string", "amount": "number", "error_code": "string | null" }` | `Merchant` (ACT-AF904DCFF9), `Platform Administrator` (ACT-086A974D63) |
| `credit_pool.utilization` | Update on the current utilization rate of a regional credit pool. | `{ "region": "string", "utilization_rate": "number", "threshold_exceeded": "boolean" }` | `Platform Administrator` (ACT-086A974D63), `NGO Operator` (ACT-09E028AEB0) |
| `donor.impact` | Anonymized impact receipt generated from a donor round-up or direct donation. | `{ "donor_id_hash": "string", "total_credits_issued": "number", "timestamp": "ISO8601" }` | `Platform Administrator` (ACT-086A974D63) |
| `dispute.alert` | Notification of a new dispute filed by a Beneficiary or Merchant. | `{ "dispute_id": "uuid", "type": "string", "severity": "string", "timestamp": "ISO8601" }` | `Platform Administrator` (ACT-086A974D63), `Dispute Adjudicator` ([ACT-7BA340FF76](../project_glossary.md#act-7ba340ff76)) |

### 4.4 Client-Side Event Listener Patterns
The Next.js dashboard components implement a robust client-side listener to handle real-time updates without full page reloads. This ensures a seamless user experience and maintains low-latency visibility.

**Implementation Strategy**:
1. **Custom Hook**: A `useDashboardStream` hook is created to manage the EventSource lifecycle.
2. **Reconnection Logic**: The hook implements exponential backoff for reconnections in case of network interruptions. It uses the `Last-Event-ID` header to replay missed events, ensuring data consistency.
3. **State Management**: Received events are dispatched to a global state store or directly update the component's local state, triggering re-renders only for the affected UI elements.
4. **Error Handling**: The hook listens for error events and provides user-friendly feedback in the UI, such as a "Reconnecting..." indicator or a notification if the stream is permanently closed.

**Example Hook Structure**:
```typescript
// Simplified conceptual structure
function useDashboardStream() {
  const [events, setEvents] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource('/api/dashboard/stream', {
      withCredentials: true,
    });

    eventSource.onopen = () => setIsConnected(true);
    eventSource.onerror = () => {
      setIsConnected(false);
      // Implement exponential backoff reconnection logic
    };

    eventSource.addEventListener('transaction.update', (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, { type: 'transaction.update', ...data }]);
      // Update specific UI components
    });

    // ... other event listeners ...

    return () => eventSource.close();
  }, []);

  return { events, isConnected };
}
```

### 5.1 Unit Tests
Unit tests will be written for the middleware to ensure that RBAC is correctly enforced for all roles.

### 5.2 Integration Tests
Integration tests will be written to verify that the Server Components correctly fetch and sanitize data from the backend API.

### 5.3 Security Scans
Automated security scans will be integrated into the CI/CD pipeline to detect any potential PII leakage or security vulnerabilities in the dashboard components.

### 6.1 Micro-Frontends
As the platform scales, the dashboard may be decomposed into micro-frontends to improve modularity and independent deployment of role-specific features.

### 6.2 Real-Time Updates
The architecture supports the integration of Server-Sent Events (SSE) for real-time updates to dashboard data, as required by the project's modernization objectives.

This architecture provides a secure, scalable, and maintainable foundation for the Next.js dashboards, ensuring that the platform's compliance and trust objectives are met while delivering a high-quality user experience for all actor groups.

## 7. Knowledge Gaps and Assumptions

- **KNOWLEDGE_GAP: Event Bus Technology** - The specific event bus technology (e.g., AWS EventBridge, Redis Pub/Sub, Kafka) used to route events to the Next.js SSE endpoint is not yet defined. This decision impacts the latency and scalability of the SSE stream. Owner: Architecture Team. Evidence needed: Performance benchmarks for different event bus solutions at 50,000 MAU scale.
- **ASSUMPTION: JWT Validation Performance** - It is assumed that JWT validation on the server side for each SSE connection can be performed within the 250ms latency target. If this is not the case, caching strategies for JWT public keys or session tokens will be required. Owner: Security Team. Evidence needed: JWT validation performance metrics for the chosen identity provider.
- **ASSUMPTION: IdP JWT Role Claim Format** - The Identity Provider (IdP) issues JWTs with a role claim that exactly matches the canonical actor role labels (e.g., "Platform Administrator", "NGO Operator", "Merchant"). If the IdP uses different role names, a mapping layer must be implemented in the middleware. Owner: Identity Provider Team. Evidence needed: IdP schema documentation.
- **ASSUMPTION: Browser Support** - It is assumed that all target browsers for the Next.js dashboard support the EventSource API. This is a standard feature in all modern browsers, but legacy browser support (if required) would necessitate a fallback mechanism. Owner: Frontend Team. Evidence needed: Browser usage statistics for the target audience.

## 8. Admin Dashboard Technical Data Models and API Contracts

This section defines the technical data models and API contracts for the Platform Administrator (ACT-086A974D63) dashboard. The Admin Dashboard serves as the central oversight interface for the MealCredit platform, providing visibility into system-wide transaction logs, user management, and compliance reporting. All data models are designed to support the platform's strict data isolation and anonymization requirements (CON-0A0288EED4, [CON-FCFF86A326](../project_glossary.md#con-fcff86a326)).

### 8.1 User Management API Contract

The User Management API allows Platform Administrators to view, search, and manage user accounts across all actor roles (Donor, Beneficiary, Merchant, NGO Operator). Due to strict PII segregation (CON-0A0288EED4), direct access to raw PII (e.g., legal names, demographic status) is restricted to cryptographic hashing layers. Administrators interact with anonymized user profiles.

#### 4.1.1. List Users Endpoint

Method: GET
Path: `/api/v1/admin/users`
Description: Retrieves a paginated list of users based on role, status, and jurisdiction.
Authentication: JWT with admin role claim.
Query Parameters:
role (string, optional): Filter by actor role (e.g., beneficiary, donor, merchant).
status (string, optional): Filter by account status (e.g., active, suspended, pending_verification).
jurisdiction (string, optional): Filter by metro footprint (e.g., SF, NYC, CHI).
page (integer, default: 1): Page number for pagination.
limit (integer, default: 20, max: 100): Number of items per page.

- Response Body (200 OK):

 {
 "data": [
 {
 "user_id": "usr_8f7a6b5c4d3e2f1a",
 "role": "beneficiary",
 "status": "active",
 "jurisdiction": "SF",
 "created_at": "2024-01-15T10:00:00Z",
 "last_login": "2024-06-09T18:30:00Z",
 "anonymized_id": "anon_ben_9a8b7c6d5e4f3g2h"
 },
 {
 "user_id": "usr_1a2b3c4d5e6f7g8h",
 "role": "donor",
 "status": "active",
 "jurisdiction": "NYC",
 "created_at": "2024-02-20T14:00:00Z",
 "last_login": "2024-06-08T09:15:00Z",
 "anonymized_id": "anon_don_1h2g3f4e5d6c7b8a"
 }
 ],
 "meta": {
 "total_count": 1250,
 "current_page": 1,
 "total_pages": 63
 }
 }

#### 4.1.2. Get User Details Endpoint

Method: GET
Path: `/api/v1/admin/users/{user_id}`
Description: Retrieves detailed, anonymized information for a specific user. Direct PII is not exposed; instead, a hash of the PII is provided for internal reference if authorized.
Authentication: JWT with admin role claim.
Path Parameters:
user_id (string): The unique identifier of the user.

- Response Body (200 OK):

 {
 "user_id": "usr_8f7a6b5c4d3e2f1a",
 "role": "beneficiary",
 "status": "active",
 "jurisdiction": "SF",
 "pii_hash": "sha256:a1b2c3d4e5f6...",
 "associated_ngos": [
 "ngo_sf_001"
 ],
 "transaction_count": 15,
 "last_redemption_date": "2024-06-09T18:30:00Z"
 }

### 8.2 System-Wide Transaction Logs API Contract

The Transaction Logs API provides Platform Administrators with a comprehensive, append-only view of all financial and operational transactions. This supports compliance auditing ([CON-1762EA5021](../project_glossary.md#con-1762ea5021)) and fraud detection ([CAP-FRAUD-DETECTION-FRAUD-PREVENTION-SCREENING](../project_glossary.md#cap-fraud-detection-fraud-prevention-screening)). Logs are immutable and cryptographically verifiable.

#### 4.2.1. List Transaction Logs Endpoint

Method: GET
Path: `/api/v1/admin/transactions`
Description: Retrieves a paginated list of system-wide transactions, filtered by type, date range, and status.
Authentication: JWT with admin role claim.
Query Parameters:
type (string, optional): Filter by transaction type (e.g., donation, redemption, payout, refund).
status (string, optional): Filter by transaction status (e.g., completed, pending, failed, reversed).
start_date (string, ISO 8601): Start of the date range.
end_date (string, ISO 8601): End of the date range.
page (integer, default: 1): Page number for pagination.
limit (integer, default: 50, max: 200): Number of items per page.

- Response Body (200 OK):

 {
 "data": [
 {
 "transaction_id": "txn_9f8e7d6c5b4a3210",
 "type": "redemption",
 "status": "completed",
 "amount": 12.50,
 "currency": "USD",
 "timestamp": "2024-06-09T18:30:00Z",
 "ledger_hash": "sha256:abc123...",
 "pos_terminal_id": "pos_sf_001"
 },
 {
 "transaction_id": "txn_1a2b3c4d5e6f7g8h",
 "type": "donation",
 "status": "completed",
 "amount": 5.00,
 "currency": "USD",
 "timestamp": "2024-06-09T17:00:00Z",
 "payment_method": "stripe_card"
 }
 ],
 "meta": {
 "total_count": 5430,
 "current_page": 1,
 "total_pages": 109
 }
 }

#### 4.2.2. Get Transaction Details Endpoint

Method: GET
Path: `/api/v1/admin/transactions/{transaction_id}`
Description: Retrieves detailed information for a specific transaction, including all associated metadata and audit trail entries.
Authentication: JWT with admin role claim.
Path Parameters:
transaction_id (string): The unique identifier of the transaction.

- Response Body (200 OK):

 {
 "transaction_id": "txn_9f8e7d6c5b4a3210",
 "type": "redemption",
 "status": "completed",
 "amount": 12.50,
 "currency": "USD",
 "timestamp": "2024-06-09T18:30:00Z",
 "ledger_hash": "sha256:abc123...",
 "pos_terminal_id": "pos_sf_001",
 "audit_trail": [
 {
 "event": "transaction_initiated",
 "timestamp": "2024-06-09T18:29:55Z",
 "actor": "pos_terminal",
 "details": "POS scan initiated"
 },
 {
 "event": "fraud_check_passed",
 "timestamp": "2024-06-09T18:29:56Z",
 "actor": "fraud_detection_service",
 "details": "No anomalies detected"
 },
 {
 "event": "ledger_entry_created",
 "timestamp": "2024-06-09T18:29:57Z",
 "actor": "financial_engine",
 "details": "Append-only log entry created"
 }
 ]
 }

### 8.3 Data Models

#### 4.4.1. Anonymized User Profile

This model represents a user account as seen by the Admin Dashboard, with all PII replaced by cryptographic hashes or anonymized identifiers.

Fields:
user_id (string, UUID): Unique identifier for the user.
role (string): Actor role (e.g., beneficiary, donor, merchant, ngo_operator).
status (string): Account status (e.g., active, suspended, pending_verification).
jurisdiction (string): Metro footprint (e.g., SF, NYC, CHI).
created_at (string, ISO 8601): Timestamp of account creation.
last_login (string, ISO 8601): Timestamp of last successful login.
anonymized_id (string): UUIDv4 mapping for analytics without PII ([CON-23A501C051](../project_glossary.md#con-23a501c051)).
pii_hash (string, SHA-256): Cryptographic hash of the user's PII for internal reference.
associated_ngos (array of strings): List of NGO IDs associated with the user (if applicable).
transaction_count (integer): Total number of transactions performed by the user.
last_redemption_date (string, ISO 8601): Date of the last redemption event (if applicable).

#### 4.4.2. Transaction Log Entry

This model represents a single entry in the append-only financial ledger, as viewed by the Admin Dashboard.

Fields:
transaction_id (string, UUID): Unique identifier for the transaction.
type (string): Transaction type (e.g., donation, redemption, payout, refund).
status (string): Transaction status (e.g., completed, pending, failed, reversed).
amount (number): Transaction amount in USD.
currency (string): Currency code (e.g., USD).
beneficiary_id (string, UUID): ID of the beneficiary (if applicable).
donor_id (string, UUID): ID of the donor (if applicable).
merchant_id (string, UUID): ID of the merchant (if applicable).
timestamp (string, ISO 8601): Timestamp of the transaction.
ledger_hash (string, SHA-256): Hash of the ledger entry for integrity verification.
pos_terminal_id (string, optional): ID of the POS terminal (if applicable).
payment_method (string, optional): Payment method used (e.g., stripe_card, offline_token).
audit_trail (array of objects): List of audit events associated with the transaction.
  event (string): Type of audit event.
  timestamp (string, ISO 8601): Timestamp of the event.
  actor (string): Actor or service that performed the event.
  details (string): Additional details about the event.

### 9.2 NGO Operator Dashboard Architecture

The NGO Operator Dashboard provides oversight of beneficiary eligibility, credit distribution, and platform compliance. It must ensure strict data isolation and anonymization.

#### 5.2.1. NGO Operator Dashboard Data Models

The following data models define the structure of the data fetched and displayed by the NGO Operator Dashboard.

NGO Beneficiary Registry
Tracks the eligibility and status of beneficiaries managed by an NGO.

| Field | Type | Description | Constraints |
|---|---|---|---|
| beneficiary_id | string | Unique identifier for the beneficiary. | UUIDv4, Primary Key |
| ngo_id | string | Identifier for the managing NGO Operator (ACT-09E028AEB0). | Foreign Key |
| eligibility_status | enum | Current eligibility status. | ELIGIBLE, SUSPENDED, OFFBOARDED |
| credit_pool_id | string | Identifier for the associated credit pool. | Foreign Key |
| last_redemption_date | timestamp | Date of the last redemption. | Nullable |
| anonymized_id | string | Cryptographically hashed identifier for analytics. | Required |

NGO Credit Distribution Log
Records all credit distribution events initiated by the NGO.

| Field | Type | Description | Constraints |
|---|---|---|---|
| distribution_id | string | Unique identifier for the distribution event. | UUIDv4, Primary Key |
| ngo_id | string | Identifier for the NGO Operator (ACT-09E028AEB0). | Foreign Key |
| credit_pool_id | string | Identifier for the associated credit pool. | Foreign Key |
| amount_distributed | decimal | Total amount of credits distributed. | > 0.00 |
| beneficiary_count | integer | Number of beneficiaries affected. | > 0 |
| timestamp | timestamp | Time of distribution. | ISO 8601 |
| initiated_by | string | Identifier of the NGO Operator who initiated the distribution. | Foreign Key |

#### 5.2.2. NGO Operator Dashboard API Contracts

These contracts define the RESTful endpoints and SSE streams for the NGO Operator Dashboard.

GET `/api/v1/ngo/dashboard/overview`
Retrieves the high-level summary metrics for the NGO's dashboard.

 Response (200 OK):

 {
 "total_beneficiaries": 500,
 "active_beneficiaries": 450,
 "pending_disputes": 2,
 "total_distributed_this_month": 15000.00
 }

GET `/api/v1/ngo/dashboard/beneficiaries`
Retrieves a paginated list of beneficiaries managed by the NGO.

 Query Parameters:
  page: integer (default: 1)
  limit: integer (default: 50, max: 100)
  eligibility_status: enum (optional, filter by ELIGIBLE, SUSPENDED, OFFBOARDED)

 Response (200 OK):

 {
 "data": [
 {
 "beneficiary_id": "ben_123",
 "eligibility_status": "ELIGIBLE",
 "anonymized_id": "hash_abc123"
 }
 ],
 "pagination": {
 "page": 1,
 "total_pages": 10
 }
 }

POST `/api/v1/ngo/dashboard/distribute-credits`
Initiates a credit distribution event for beneficiaries.

 Request Body:

 {
 "credit_pool_id": "pool_123",
 "amount_per_beneficiary": 25.00,
 "beneficiary_ids": ["ben_123", "ben_456"]
 }

 Response (21 Created):

 {
 "distribution_id": "dist_123",
 "status": "PROCESSING",
 "estimated_completion_time": "2023-10-27T15:00:00Z"
 }

SSE Stream: `/api/v1/ngo/dashboard/events/stream`
Provides real-time updates for credit distribution status and compliance alerts.

 Event: distribution_completed

 {
 "distribution_id": "dist_123",
 "beneficiary_count": 2,
 "total_amount": 50.00
 }

 Event: compliance_alert
 Triggered when a potential compliance violation is detected (e.g., PII leakage attempt).

 {
 "alert_type": "PII_LEAKAGE_ATTEMPT",
 "timestamp": "2023-10-27T14:30:00Z",
 "severity": "CRITICAL"
 }

### 9.3 POS Integration Data Flows

The POS integration data flows ensure that credit redemptions are processed securely and efficiently, with real-time feedback to the Merchant Dashboard.

1. Beneficiary Presentation: The Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) presents a QR code or NFC token at the Merchant (Restaurant) (ACT-AF904DCFF9) POS.
2. POS Scan & Validation: The POS terminal scans the token and sends a validation request to the `gRPC Service Contracts & Definitions` (sibling artifact) for real-time verification of the credit pool and beneficiary eligibility.
3. Real-Time Clearance: Upon successful validation, the `Transaction & Financial Engine` ([CAP-TRANSACTION-FINANCIAL-ENGINE](../project_glossary.md#cap-transaction-financial-engine)) processes the transaction, deducts the credit from the pool, and generates a `Real-Time Transaction Event`.
4. SSE Stream Update: The `Real-Time Transaction Event` is published to the SSE stream, which is consumed by the Merchant Dashboard to update the UI in real-time.
5. Receipt Generation: A digital receipt is generated and sent to the Beneficiary's mobile device, correlating the donor impact with the redemption event without linking PII (CON-23A501C051).

### 10.2 Event Types

The following event types are defined for the dashboards:

- `transaction_clearance`: Triggered when a POS transaction is successfully cleared.
- `credit_pool_alert`: Triggered when credit pool utilization exceeds a threshold.
- `distribution_completed`: Triggered when an NGO credit distribution is finalized.
- `compliance_alert`: Triggered when a potential compliance violation is detected.
- `payout_status_update`: Triggered when a merchant payout status changes.

### 11.1 Component Architecture

- `DashboardLayout`: Wraps the dashboard content with navigation and header.
- `RoleGuard`: Protects routes and components based on the user's role claim.
- `DataGrid`: A reusable table component for displaying paginated data.
- `RealTimeChart`: A chart component that updates in real-time via SSE.

### 11.2 Accessibility

All UI components must adhere to WCAG 2.1 AA standards, ensuring keyboard-only navigation and screen reader compatibility ([CON-68497304B1](../project_glossary.md#con-68497304b1), [CON-6C177D0102](../project_glossary.md#con-6c177d0102)).

## 13. Core Dashboard Components & Routing

The application is structured around three primary dashboard environments, each enforcing specific RBAC middleware.

### 13.1 Merchant Dashboard (Restaurant POS Integration)

**Target User:** `Merchant` (ACT-AF904DCFF9)
**Primary Surface:** `SUR-9119D8B358` (Product: Merchant POS Integration)

The Merchant Dashboard provides a low-friction interface for transaction monitoring, payout tracking, and dispute management. It is optimized for high-availability and low-latency interactions to prevent queue stagnation at the POS.

*   **Real-Time Transaction Feed:** Utilizes SSE to stream `transaction_cleared` and `transaction_declined` events from the `Payment Processing Surface` ([SUR-5B18C8719F](../project_glossary.md#sur-5b18c8719f)).
*   **Payout Status Tracking:** Displays the current settlement status of daily net payouts, integrating with the `Financial Reconciliation & Payout Workers` (sibling artifact).
*   **Dispute Management:** Provides a UI for `Merchant-Beneficiary Refund Flow` ([JNY-E5F45D37C6](../project_glossary.md#jny-e5f45d37c6)) and `Beneficiary-Platform Dispute Flow` ([JNY-2B038C9362](../project_glossary.md#jny-2b038c9362)), allowing merchants to initiate reversals and view adjudication outcomes.

### 13.2 NGO Operator Dashboard (NGOCentralCommand)

**Target User:** `NGO Operator` (ACT-09E028AEB0)
**Primary Surface:** `SUR-610861D01A` (Product: NGO Governance & Beneficiary Offboarding)

The NGO Dashboard serves as the administrative layer for beneficiary eligibility, credit pool management, and compliance reporting.

*   **Beneficiary Management:** Interfaces with the `BeneficiaryModule` to verify eligibility, assign `credit_pool_id`s, and manage offboarding workflows.
*   **Compliance & Audit:** Provides access to anonymized impact reports, correlating donor impact receipts with beneficiary redemption events without linking PII (CON-23A501C051).
*   **Credit Pool Monitoring:** Displays real-time `Credit Pool Utilization Rate` metrics, triggering alerts when thresholds exceed 85% ([CON-2059B17FB2](../project_glossary.md#con-2059b17fb2)).

### 13.3 Platform Administrator Dashboard

**Target User:** `Platform Administrator` (ACT-086A974D63)
**Primary Surface:** `SUR-43E71C4E2B` (Design: API Surface)

The Admin Dashboard provides system-wide oversight, including merchant onboarding approval, fraud investigation, and infrastructure monitoring.

*   **Merchant Onboarding:** Manages the `Merchant Onboarding & POS Integration` ([JNY-356F465DB3](../project_glossary.md#jny-356f465db3)) lifecycle, including KYC document review and POS gateway configuration.
*   **Fraud Investigation:** Interfaces with the `Platform-NGO Fraud Investigation Flow` ([JNY-CA74D631DC](../project_glossary.md#jny-ca74d631dc)) to review flagged transactions and manage automated freezes.
*   **System Health:** Monitors critical infrastructure metrics, including `Cache Hit Ratio (CHR)` for Redis and `p99 latency` for voucher creation callbacks.

### 14.1 SSE Stream Configuration

*   **Endpoint:** `/api/dashboard/stream` (Protected by RBAC middleware)
*   **Transport:** HTTP/2 or HTTP/1.1 with `Content-Type: text/event-stream`
*   **Heartbeat:** Ping messages sent every 15 seconds to maintain connection stability across CDN edge nodes.

### 15.1 Merchant POS Session State

The `Merchant POS Session State` tracks the current operational status of a merchant's integration with the MealCredit platform.

typescript
interface MerchantPOSState {
  merchant_id: string;
  pos_gateway_id: string; // e.g., Toast, Clover, Square
  connection_status: 'CONNECTED' | 'DISCONNECTED' | 'DEGRADED';
  last_sync_timestamp: number;
  pending_payouts: PayoutSummary[];
  active_disputes: DisputeSummary[];
}

### 15.2 Beneficiary Management Schemas

Beneficiary management schemas ensure that beneficiary data is handled securely and in compliance with privacy regulations. This process is managed by the `PII Segregation & Anonymization Strategy` (sibling artifact).

1.  **Eligibility Verification:** NGO Operators (ACT-09E028AEB0) verify beneficiary eligibility through the NGO Operator Dashboard.
2.  **Anonymized ID Generation:** Upon verification, an `anonymized_id` is generated using a cryptographic hash function, ensuring that PII is not stored in the main beneficiary registry.
3.  **Credit Pool Assignment:** The beneficiary is assigned to a `credit_pool_id` and their `eligibility_status` is set to `ELIGIBLE`.
4.  **Data Isolation:** All PII-related data is stored in a separate, highly restricted database, accessible only to authorized NGO Operators for verification purposes.

### 15.3 Payout Status Tracking

Payout status tracking ensures that merchants are compensated accurately and timely for cleared credits. This process is managed by the `Financial Reconciliation & Payout Workers` (sibling artifact).

1.  **Daily Reconciliation:** At the end of each business day, the `Financial Reconciliation & Payout Workers` aggregate all `SUCCESS` transactions for each merchant.
2.  **Payout Calculation:** The total payout amount is calculated, accounting for any fees or adjustments.
3.  **Payout Status Update:** The payout status is updated in the `Merchant POS Session State` and reflected in the Merchant Dashboard's overview endpoint.
4.  **SSE Stream Update:** A `payout_status_changed` event is published to the SSE stream, notifying the Merchant Dashboard of the updated payout status.

### 15.4 Role-Based Access Control (RBAC)

Access to dashboard routes and API endpoints is enforced via middleware that validates the user's JWT against their assigned role.

*   **Platform Administrator:** Full access to Admin Dashboard, user management, and system configuration.
*   **NGO Operator:** Access to NGO Dashboard, beneficiary management, and compliance reporting.
*   **Merchant:** Access to Merchant Dashboard, transaction history, and payout tracking.

### 15.5 Data Isolation & Anonymization

*   **PII Segregation:** Beneficiary PII is cryptographically segregated from public transaction logs (CON-0A0288EED4, [CON-92F07E31B0](../project_glossary.md#con-92f07e31b0)).
*   **Anonymized Analytics:** Donor impact receipts are correlated with beneficiary redemption events using UUIDv4 mapping, ensuring no PII is transmitted to donors (CON-23A501C051).
*   **Data Residency:** User data is stored in compliance with jurisdictional requirements for SF, NYC, and Chicago (CON-30EA97016B, [CON-4093C26BCC](../project_glossary.md#con-4093c26bcc)).

### 15.6 Audit Logging

All administrative actions and financial ledger mutations are logged to an append-only cryptographic log in Aurora PostgreSQL (CON-1762EA5021, [CON-6061FCCA83](../project_glossary.md#con-6061fcca83)). These logs are also exported to AWS CloudTrail for SOC2 Type II evidence ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2), [CON-FBBBF07295](../project_glossary.md#con-fbbbf07295)).

## 16. Alignment with Project Context

This architecture aligns with the MealCredit project requirements by:
*   Supporting the `Merchant (Restaurant)` (ACT-AF904DCFF9) and `NGO Operator` (ACT-09E028AEB0) actor roles.
*   Enabling real-time POS clearance to prevent queue stagnation ([CON-4152F2C7C3](../project_glossary.md#con-4152f2c7c3)).
*   Ensuring strict data isolation and anonymization of beneficiary data (CON-0A0288EED4, CON-92F07E31B0).
*   Integrating with the `Transaction & Financial Engine` (CAP-TRANSACTION-FINANCIAL-ENGINE) and `Merchant & NGO Operations` ([CAP-MERCHANT-NGO-OPERATIONS](../project_glossary.md#cap-merchant-ngo-operations)) capabilities.
*   Supporting the target scale of 50,000 MAU across 3 metropolitan footprints (SF, NYC, Chicago).

This artifact defers to the `Financial Reconciliation & Payout Workers` artifact for detailed payout logic and to the `PII Segregation & Anonymization Strategy` artifact for detailed data handling procedures.

## 17. Impact Propagation

*   **Merchant Dashboard:** Changes to the `Merchant POS Session State` interface will require updates to the `Merchant Onboarding & POS Integration` (JNY-356F465DB3) artifact.
*   **NGO Dashboard:** Changes to the `Beneficiary Management Schemas` will require updates to the `NGO Governance & Beneficiary Offboarding` ([JNY-4C4BA15817](../project_glossary.md#jny-4c4ba15817)) artifact.
*   **Admin Dashboard:** Changes to the `Platform Administrator Dashboard` RBAC will require updates to the `Identity & Access Management` ([CAP-IDENTITY-ACCESS-MANAGEMENT](../project_glossary.md#cap-identity-access-management)) artifact.
# Security Architecture & Access Control

## 1. Identity & Access Management (CAP-361A59708B) Model

This section defines the Identity & Access Management (CAP-361A59708B) model for the tripartite marketplace, specifying RBAC policies for Contributor, Recipient, Merchant Partner, and Operator roles, including authentication flows and session management. The architecture enforces strict separation between public discovery surfaces and authenticated financial actions.

### 1.1 Identity Provider (IdP) Architecture

The system utilizes a centralized Identity Provider (IdP) to manage authentication and authorization for all actor roles. The IdP serves as the single source of truth for user identities, issuing JSON Web Tokens (JWTs) for session management.

*   **IdP Selection:** [KNOWLEDGE_GAP: Identity Provider - The specific IdP vendor (e.g., AWS Cognito, Auth0, Okta) must be established based on SOC2 Type II compliance requirements and integration capabilities with the chosen cloud infrastructure.]
*   **Token Format:** All authentication tokens will be JWTs, signed using RS256 asymmetric keys. The IdP will manage key rotation and revocation.
*   **Session Management:** Sessions will be managed via short-lived access tokens (e.g., 15 minutes) and long-lived refresh tokens (e.g., 7 days). Refresh tokens will be stored securely on the client side (e.g., HTTP-only cookies for web, SecureStore for mobile).

### 1.2 Role-Based Access Control (RBAC) Policies

Access to system resources is governed by RBAC policies defined for each actor role. The following table outlines the permissions for each role:

| Actor Role | ID | Permissions |
| :--- | :--- | :--- |
| Contributor | ACT-2A20B038B1 | View donation history, configure round-up rules, view impact reports, update payment methods. |
| Recipient | ACT-DC00FA84DC | Discover merchants, redeem credits, view transaction history (anonymized), update profile preferences (no PII). |
| Merchant Partner | ACT-A14D3CDC5D | View settlement reports, manage POS integration settings, toggle throttle parameters, view redemption history. |
| Operator | ACT-FE96DD3975 | Full administrative access, manage merchant onboarding, monitor system health, adjust credit pool parameters, generate compliance reports. |

### 1.3 Authentication Flows

#### 1.3.1. Contributor Onboarding & Funding

1.  **Registration:** Contributor provides email and password. IdP creates user record and issues initial JWT.
2.  **Payment Method Linking:** Contributor links external financial identity via Plaid/Stripe integration. This step is handled by the Payment Gateway Adapter, which returns a tokenized payment method ID to the IdP for association with the Contributor's account.
3.  **Round-Up Configuration:** Contributor configures auto-funding or round-up rules. These rules are stored in the Core Domain Model and referenced by the Background Processing & Async Workers.

#### 1.3.2. Recipient Discovery & Redemption

1.  **Anonymous Access:** Recipients can browse merchant listings without authentication. This is handled by the API Gateway & Orchestration Layer, which serves public data from the Discovery & Allocation Engine.
2.  **Redemption Authentication:** To redeem credits, the Recipient must authenticate. This can be done via a one-time passcode (OTP) sent to a pre-registered email or phone number, or via a biometric prompt on the mobile app. The IdP validates the OTP/biometric and issues a short-lived JWT.
3.  **Token Generation:** Upon successful authentication, the system generates a single-use virtual card token via the Payment Gateway Adapter. This token is pushed to the Recipient's device.

#### 1.3.3. Merchant Partner Activation & Verification

1.  **Registration:** Merchant Partner submits business registration details. This triggers a verification workflow managed by the Operator.
2.  **Verification:** Operator reviews and approves the Merchant Partner's application. Upon approval, the Merchant Partner's account is marked 'Live' and they are granted access to the Merchant Dashboard.
3.  **POS Integration:** Merchant Partner provides POS integration details. This is handled by the POS System Integration Design artifact, which defines the technical interface for POS devices to communicate with the platform.

#### 1.4.1. PCI-DSS Level 1 Compliance Boundaries (CON-6EA64CF2A1)

To enforce PCI-DSS Level 1 compliance, the architecture ensures that zero raw credit card data touches application servers. All payment processing is offloaded to the Payment Gateway Adapter (Stripe/Plaid).

*   **Data Flow:** The Client Application Layer communicates directly with the Payment Gateway Adapter to tokenize payment instruments. The Core Transaction & Ledger Service never receives or logs raw PAN (Primary Account Number) data.
*   **Tokenization:** Payment methods are stored as opaque tokens by the IdP, linked to the Contributor's account. These tokens are used for transaction initiation but cannot be reverse-engineered to reveal the underlying card details.
*   **Audit Logging:** All access to financial data is logged to AWS CloudTrail (CON-0B2D40801A) and the append-only Aurora Postgres ledger (CON-199A4FEDC7) to ensure immutable audit trails for SOC2 Type II compliance.

#### 1.4.2. Absolute Anonymization Architecture (CON-9DEA275205, CON-8A8949BE4A)

The system enforces absolute anonymization where all beneficiary analytics map to high-entropy UUIDv4 keys, preventing PII reconstruction.

*   **PII Classification:** Data is strictly classified into Anonymized Credits (On-Platform) and Off-Platform PII (Excluded). The platform stores only derived, anonymized credits represented as high-entropy UUIDv4 keys.
*   **Off-Platform PII:** Beneficiary demographic data, including legal names, addresses, and domestic backgrounds, are strictly off-platform (CON-4DB27D2227). This data is managed by the NGO partner and never enters the Dayaa production environment.
*   **Analytics Mapping:** All internal tracking, analytics, and financial reconciliation use the UUIDv4 keys. These keys are cryptographically unguessable and cannot be reverse-engineered to identify the beneficiary.

#### 1.4.3. Secure Offline Token Storage (CON-0346AE051D)

To support offline redemption resilience, the system designs secure offline token storage using device-level SecureStore with cryptographic signatures.

*   **SecureStore Integration:** The Recipient's mobile app utilizes the device's native SecureStore (Apple Keychain / Android Keystore) to store single-use virtual card tokens.
*   **Cryptographic Signatures:** Tokens are signed by the Core Transaction & Ledger Service using RS256 keys. This ensures that tokens cannot be forged or tampered with, even if the device is compromised.
*   **Offline Validation:** POS devices validate the cryptographic signature of the token locally. If network connectivity is unavailable, the POS device can verify the token's validity based on the signature and expiration time, ensuring frictionless clearing.

### 1.4 Data Retention Policy

Data retention policies are enforced to comply with SOC2 Type II and financial regulations. Unused emergency credits auto-roll back to the regional pool after 72 hours (CON-AEB925BD12).

*   **Transaction Logs:** Immutable transaction logs are retained for a period defined by the Compliance & Audit Governance sibling artifact.
*   **PII Retention:** No PII is retained on-platform. Off-platform PII retention is governed by the NGO partner's policies.
*   **Token Expiration:** Single-use virtual card tokens expire immediately after redemption or after a defined grace period (e.g., 24 hours) if not used, ensuring no lingering access.

### 1.5 Knowledge Gaps

*   [KNOWLEDGE_GAP: Identity Provider - The specific IdP vendor (e.g., AWS Cognito, Auth0, Okta) must be established based on SOC2 Type II compliance requirements and integration capabilities with the chosen cloud infrastructure.]
*   [KNOWLEDGE_GAP: MFA Implementation - The specific MFA methods (e.g., TOTP, SMS, Email) for Operator accounts must be established based on security requirements and user experience considerations.]
*   [KNOWLEDGE_GAP: Offline Token Validation - The specific cryptographic algorithm and key management strategy for offline token validation must be established based on security requirements and POS device capabilities.]
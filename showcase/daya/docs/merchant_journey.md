# Merchant Onboarding & Verification

## 1. Merchant Partner KYC Data Collection Flow

This section defines the product requirements for the Know Your Customer (KYC) data collection flow for the Merchant Partner (ACT-A14D3CDC5D). The goal is to establish a frictionless yet compliant onboarding experience that satisfies PCI-DSS Level 1 and SOC2 Type II requirements while minimizing the time-to-live for new restaurant partners.

### 1.1 Onboarding Entry & Identity Verification

The Merchant Partner (ACT-A14D3CDC5D) initiates onboarding via the web dashboard. The system must collect identity information for the Authorized Representative (AR) to establish legal accountability.

**User Stories:**
*   **US-1.1.1:** As a Merchant Partner (ACT-A14D3CDC5D), I want to upload a government-issued photo ID (Driver's License or Passport) for the Authorized Representative, so that the system can verify my identity against official records.
*   **US-1.1.2:** As a Merchant Partner (ACT-A14D3CDC5D), I want to enter my legal business name and Tax ID (EIN/SSN), so that the platform can validate my business registration and prepare for financial settlement.

**Acceptance Criteria:**
*   The UI must support drag-and-drop upload for ID documents (PDF, JPG, PNG).
*   The system must perform real-time OCR and liveness detection (if available) to validate the ID document.
*   The system must mask the Tax ID in the UI after submission, showing only the last 4 digits for confirmation.
*   **Error State:** If the ID is expired or the name does not match the business registration, the system must display a clear error message and allow the user to re-upload or request manual review.

### 1.2 POS Integration Setup (Product Requirements)

This section defines the product requirements for the Merchant Partner (ACT-A14D3CDC5D) to establish a secure, PCI-DSS Level 1 compliant connection between their Point-of-Sale (POS) hardware and the MealCredit platform. The goal is to enable the Merchant Partner to accept and clear MealCredit transactions seamlessly.

**User Stories:**
*   **US-1.2.1:** As a Merchant Partner (ACT-A14D3CDC5D), I want to easily pair my POS hardware with the MealCredit system so that I can accept transactions without replacing my existing equipment.
*   **US-1.2.2:** As a Merchant Partner (ACT-A14D3CDC5D), I want to configure my POS settings to ensure that MealCredit transactions are processed distinctly from standard payments.

**Acceptance Criteria:**
*   The system provides a guided setup wizard within the Merchant Dashboard for hardware pairing.
*   The wizard supports common POS hardware models used by restaurant partners, with clear visual instructions for physical connection (USB, Bluetooth, or Ethernet).
*   The system automatically detects and validates the connected hardware model.
*   If the hardware is not supported, the system provides a clear error message and a link to the approved hardware list.

**Edge Cases:**
*   **Hardware Not Detected:** If the hardware is not detected after a reasonable timeout, the system prompts the user to check physical connections and retry.
*   **Incompatible Hardware:** If the hardware is incompatible, the system clearly states the reason and provides a list of compatible devices.

### 1.3 Data Privacy & Anonymization

The KYC flow must adhere to the platform's core principle of Absolute Anonymization (CON-8A8949BE4A). While the Merchant Partner (ACT-A14D3CDC5D) provides PII for compliance, this data must never be exposed to the Recipient (ACT-DC00FA84DC) or stored in production logs in a readable format.

**User Stories:**
*   **US-1.3.1:** As a Merchant Partner (ACT-A14D3CDC5D), I want to be assured that my business details are used solely for compliance and settlement, so that I can trust the platform with sensitive financial information.
*   **US-1.3.2:** As a Merchant Partner (ACT-A14D3CDC5D), I want to understand how my data is encrypted and stored, so that I can verify PCI-DSS Level 1 compliance.

**Acceptance Criteria:**
*   All PII collected during KYC must be encrypted at rest using AES-256 or higher.
*   The system must not log any PII (names, addresses, Tax IDs) in application logs or CloudTrail (CON-0B2D40801A).
*   The Recipient (ACT-DC00FA84DC) must only see the Merchant Partner's (ACT-A14D3CDC5D) public-facing profile (name, cuisine, distance), never the legal business details or AR identity.

### 1.4 Edge Cases & Failure States

*   **ID Rejection:** If the ID verification fails, the user must be able to request a manual review by an Operator (ACT-FE96DD3975). The system must provide a status update within a defined SLA.
    *   `KNOWLEDGE_GAP: Operator must establish the SLA for manual review turnaround time.`
*   **Business Mismatch:** If the business name on the ID does not match the business registration, the system must flag this for manual review and pause the onboarding flow until resolved.
*   **Geospatial Exclusion:** If the business address is outside the active metro footprint, the system must display a clear message explaining that the platform is not yet available in that region and offer to notify the user when expansion occurs.

### 1.5 Contract Signing & Activation

Before the Merchant Partner (ACT-A14D3CDC5D) can accept MealCredits, they must agree to the platform's legal terms. This process ensures that both parties understand their obligations regarding financial settlement, data privacy, and service levels.

**User Stories:**
*   **US-1.5.1:** As a Merchant Partner (ACT-A14D3CDC5D), I want to review and digitally sign the Merchant Agreement so that I can activate my account and start accepting transactions.
*   **US-1.5.2:** As a Merchant Partner (ACT-A14D3CDC5D), I want to receive a copy of the signed agreement for my records.

**Acceptance Criteria:**
*   The system must present the Merchant Agreement in a clear, readable format.
*   The Merchant Partner (ACT-A14D3CDC5D) must explicitly acknowledge and accept the terms via a digital signature.
*   Upon successful signing, the system must generate a timestamped, immutable record of the agreement.
*   The Merchant Partner (ACT-A14D3CDC5D) must be able to download a PDF copy of the signed agreement.

### 1.6 Handoff to Next Step

This KYC flow is the first step in the Merchant Onboarding & Verification artifact. Upon successful completion, the Merchant Partner (ACT-A14D3CDC5D) will proceed to the POS integration setup, where technical details for the POS gateway adapter will be configured.

This artifact's POS integration setup defers to the Integration & Payment Gateway Adapter (SUR-213BCD1816) for the specific technical standards and API contracts required for PCI-DSS Level 1 compliance.

This artifact's contract signing defers to the Operator Governance & Liquidity Management (CAP_inception_operational_governance) for the legal terms and liability clauses that must be presented to the Merchant Partner (ACT-A14D3CDC5D).

---

### 2.1 Hardware Pairing and Configuration

The Merchant Partner must be able to pair their existing POS hardware (e.g., card readers, barcode scanners) with the MealCredit integration layer. This process must be frictionless to minimize onboarding time.

**User Story:**
*   As a Merchant Partner (ACT-A14D3CDC5D), I want to easily pair my POS hardware with the MealCredit system so that I can accept transactions without replacing my existing equipment.

**Acceptance Criteria:**
*   The system provides a guided setup wizard within the Merchant Dashboard for hardware pairing.
*   The wizard supports common POS hardware models used by restaurant partners, with clear visual instructions for physical connection (USB, Bluetooth, or Ethernet).
*   The system automatically detects and validates the connected hardware model.
*   If the hardware is not supported, the system provides a clear error message and a link to the approved hardware list.

**Edge Cases:**
*   **Hardware Not Detected:** If the hardware is not detected after a reasonable timeout, the system prompts the user to check physical connections and retry.
*   **Incompatible Hardware:** If the hardware is incompatible, the system clearly states the reason and provides a list of compatible devices.

### 2.2 Software SDK Initialization

The Merchant Partner must initialize the MealCredit SDK within their POS environment. This SDK handles the communication between the POS and the MealCredit platform, ensuring that transactions are processed securely and in real-time.

**User Story:**
*   As a Merchant Partner (ACT-A14D3CDC5D), I want to easily install and configure the MealCredit SDK so that my POS system can process MealCredit transactions.

**Acceptance Criteria:**
*   The system provides clear documentation and code snippets for SDK integration.
*   The SDK must support the most common POS operating systems and development frameworks used by restaurant partners.
*   The SDK must handle tokenization of transaction data to ensure PCI-DSS Level 1 compliance.
*   The SDK must provide error handling and logging capabilities to assist with troubleshooting.

### 2.3 Transaction Flow & Validation

Once the POS is integrated, the Merchant Partner (ACT-A14D3CDC5D) must be able to process MealCredit transactions. The system must validate the transaction against the Recipient's (ACT-DC00FA84DC) available credits and the Merchant's (ACT-A14D3CDC5D) eligibility.

**User Story:**
*   As a Merchant Partner (ACT-A14D3CDC5D), I want to process MealCredit transactions seamlessly so that I can serve Recipients (ACT-DC00FA84DC) without friction.

**Acceptance Criteria:**
*   The POS must send a transaction request to the MealCredit platform, including the tokenized voucher and order details.
*   The platform must validate the token, check the Recipient's (ACT-DC00FA84DC) credit balance, and verify the Merchant's (ACT-A14D3CDC5D) eligibility.
*   The platform must return a success or failure response to the POS within a reasonable timeframe.
*   The POS must display the transaction result to the Merchant Partner (ACT-A14D3CDC5D) and the Recipient (ACT-DC00FA84DC).

### 2.4 Error Handling & Reconciliation

The system must handle transaction failures gracefully and provide mechanisms for reconciliation to ensure financial accuracy.

**User Stories:**
*   As a Merchant Partner (ACT-A14D3CDC5D), I want to be notified of any transaction failures so that I can take appropriate action.
*   As a Merchant Partner (ACT-A14D3CDC5D), I want to access a reconciliation report to verify that all transactions have been processed correctly.

**Acceptance Criteria:**
*   The system must provide clear error messages for common failure scenarios (e.g., insufficient credits, invalid token, network error).
*   The system must log all transaction attempts, including failures, for audit and reconciliation purposes.
*   The Merchant Partner (ACT-A14D3CDC5D) must be able to access a daily reconciliation report via the Merchant Dashboard.
*   The system must support manual adjustment of transactions in case of system errors, with appropriate audit trails.

### 2.5 Offline Redemption Support

To ensure resilience in areas with poor connectivity, the system must support offline redemption. This allows Recipients (ACT-DC00FA84DC) to use MealCredits even when the POS is not connected to the internet.

**User Story:**
*   As a Merchant Partner (ACT-A14D3CDC5D), I want to be able to accept MealCredits even when my POS is offline so that I can serve Recipients (ACT-DC00FA84DC) without interruption.

**Acceptance Criteria:**
*   The system must generate offline-compatible tokens that can be validated by the POS without an internet connection.
*   The POS must store offline transactions securely and sync them with the platform once connectivity is restored.
*   The system must handle potential conflicts (e.g., double-spending) that may arise from offline transactions.
*   `KNOWLEDGE_GAP: Offline token validity period and discovery radius defaults remain open - Design phase should propose specific values for ratification.`

### 3.1 Verification Workflow

The Operator (ACT-FE96DD3975) is responsible for verifying the Merchant Partner's (ACT-A14D3CDC5D) onboarding data and approving their activation.

**User Story:**
*   As an Operator (ACT-FE96DD3975), I want to review the Merchant Partner's (ACT-A14D3CDC5D) KYC data, POS integration status, and signed contract so that I can approve their activation.

**Acceptance Criteria:**
*   The Operator (ACT-FE96DD3975) dashboard must display a summary of the Merchant Partner's (ACT-A14D3CDC5D) onboarding status.
*   The Operator (ACT-FE96DD3975) must be able to review the uploaded ID documents, business registration, and signed contract.
*   The Operator (ACT-FE96DD3975) must be able to approve or reject the onboarding request, with a reason for rejection if applicable.
*   Upon approval, the system must automatically activate the Merchant Partner's (ACT-A14D3CDC5D) account and notify them.

### 3.2 Activation Notification

Once the Merchant Partner (ACT-A14D3CDC5D) is approved, they must be notified and provided with instructions on how to start accepting transactions.

**User Story:**
*   As a Merchant Partner (ACT-A14D3CDC5D), I want to receive a notification that my account has been activated so that I can start accepting MealCredits.

**Acceptance Criteria:**
*   The system must send an email notification to the Merchant Partner (ACT-A14D3CDC5D) upon account activation.
*   The notification must include a link to the Merchant Dashboard and a summary of next steps.
*   The Merchant Partner (ACT-A14D3CDC5D) must be able to log in to the Merchant Dashboard and view their active status.

### 3.3 Post-Activation Support

The system must provide ongoing support to the Merchant Partner (ACT-A14D3CDC5D) to ensure a smooth experience.

**User Story:**
*   As a Merchant Partner (ACT-A14D3CDC5D), I want to access support resources and contact customer service so that I can resolve any issues that arise.

**Acceptance Criteria:**
*   The Merchant Dashboard must include a help center with FAQs, documentation, and troubleshooting guides.
*   The Merchant Partner (ACT-A14D3CDC5D) must be able to submit a support ticket directly from the dashboard.
*   The system must provide a clear escalation path for critical issues.
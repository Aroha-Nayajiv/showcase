# Credential Verification and Compliance Activation

### 1.1 Provider General Onboarding (JNY-DBCD184BF3)

**Objective:** Enable the Workforce Provider ([ACT-146D8465B0](../project_glossary.md#act-146d8465b0)) to establish a secure, verified identity and register their device for the Local-First Edge Engine ([SUR-D1A2EE5B7A](../project_glossary.md#sur-d1a2ee5b7a)).

#### User Story 1.1.2: Device Registration and Edge Engine Initialization
As a Workforce Provider,
I want to register my mobile device and initialize the local Edge Engine,
So that I can operate in offline mode and ensure my device integrity is verified.

**Acceptance Criteria:**
1. Given the provider has completed identity verification, When they launch the app for the first time, Then the app prompts for device permissions (Camera, Location, Biometrics) required for the Edge Device Integrity and Root Detection Engine ([CAP-EDGE-DEVICE-INTEGRITY-AND-ROOT-DETECTION-ENGINE](../project_glossary.md#cap-edge-device-integrity-and-root-detection-engine)).
2. Given permissions are granted, When the app initializes, Then the local Edge Engine (Ollama/vLLM/SGLang) is downloaded and configured for offline use, and a local device fingerprint is generated.
3. Given the device fingerprint is generated, When the provider attempts to log in from a new device, Then the system flags the login for additional verification (e.g., biometric re-authentication).

### 2.1 Healthcare Provider Onboarding and Credential Licensure Verification (JNY-B9F1C271F5)

**Context:** This journey covers the onboarding of Registered Nurses (RNs), Travel Nurses, and allied health professionals. The primary compliance driver is HIPAA, requiring strict data handling and verification of active state licenses.

#### User Story: Healthcare Provider License Submission
As a Workforce Provider,
I want to securely upload my state nursing license and DEA registration (if applicable),
So that I can be verified for healthcare shifts and ensure compliance with HIPAA regulations.

**Acceptance Criteria:**
1. **Document Upload:** The provider can upload a clear image or PDF of their state nursing license. The system must validate file types (e.g., JPG, PNG, PDF) and size limits.
2. **Data Extraction (Local-First):** The local edge engine (SUR-D1A2EE5B7A) extracts key fields (License Number, Expiration Date, State, Full Name) from the uploaded document. This processing occurs locally on the device to minimize data transit.
3. **Verification Status:** The system displays a "Pending Verification" status immediately after upload. The provider receives a notification once the verification is complete.
4. **HIPAA Compliance:** All uploaded documents are encrypted at rest and in transit. Access to these documents is restricted to authorized Agency Administrators and Platform Operators.

#### User Story: License Expiration and Renewal
As a Workforce Provider,
I want to receive a notification before my license expires,
So that I can renew it in time and avoid being deactivated from the platform.

**Acceptance Criteria:**
1. **Expiration Tracking:** The system tracks the expiration date of the uploaded license.
2. **Notification:** The provider receives a push notification and email reminder 90 days, 30 days, and 7 days before the license expiration date.
3. **Renewal Flow:** If a license expires, the provider is automatically deactivated from healthcare shift matching until a new, valid license is uploaded and verified.

#### User Story: Healthcare Credential Verification (HIPAA)
As an Agency Administrator,
I want to review and approve/reject healthcare provider credentials,
So that I can ensure only qualified and compliant providers are dispatched to healthcare clients.

**Acceptance Criteria:**
1. **Review Dashboard:** The Agency Administrator can view a list of providers pending verification, including their extracted license details.
2. **Approval/Rejection:** The administrator can approve the credential (marking the provider as "Verified") or reject it with a reason (e.g., "Expired License," "Illegible Document").
3. **Audit Trail:** All approval/rejection actions are logged with a timestamp and the administrator's ID for compliance auditing.

### 2.3 Edge Cases and Error Flows

1. **Illegible Document:** If the local edge engine cannot extract clear text from a document, the system prompts the provider to re-upload a clearer image.
2. **Expired Document:** If a document is expired, the system rejects the upload and prompts the provider to upload a renewed version.
3. **Network Partition:** If the provider is offline, the document upload is queued locally. Once connectivity is restored, the data is synced to the cloud relay ([SUR-50E19DC151](../project_glossary.md#sur-50e19dc151)) for verification.
4. **Fraud Detection:** If a document appears to be altered (e.g., inconsistent fonts, mismatched metadata), the system flags it for manual review by a Platform Operator.

---

### 3.1 Provider Device Integrity Check & Root Detection (JNY-07268FC66F)

**Purpose:** To verify that the Provider's device is secure, unmodified, and capable of running the local-first edge AI engine before allowing access to sensitive shift data or credential verification workflows.

#### 3.1.2 Acceptance Criteria

*   **AC 1.1:** The app must detect if the device is rooted (Android) or jailbroken (iOS) and block access to the "Shift Request" and "Clock-In" features if detected.
*   **AC 1.2:** The app must verify that the OS version meets the minimum requirements for the local-first edge AI engine (e.g., Android 10+, iOS 15+).
*   **AC 1.3:** If a device fails integrity checks, the app must display a "Device Not Secure" screen with a link to a help article explaining how to resolve the issue.
*   **AC 1.4:** The app must log all integrity check attempts (success/failure) to the local device database for later sync to the serverless cloud relay.
*   **AC 1.5:** The app must support "Safe Mode" for providers who need to access basic profile information but cannot pass full integrity checks (limited to non-sensitive data).

### 3.2 Offline Field Execution and Clock-In (JNY-F6CC7FB09F)

**Purpose:** To enable Providers to clock in, execute shifts, and capture work data in environments with poor or no network connectivity, ensuring data integrity and eventual consistency with the central platform.

#### 3.2.2 Acceptance Criteria

*   **AC 2.1:** The app must allow the provider to clock in and capture shift data (photos, notes, location) when the device is in "Offline Mode."
*   **AC 2.2:** All offline data must be stored locally in an encrypted database on the device.
*   **AC 2.3:** Upon reconnection, the app must automatically sync all offline data to the serverless cloud relay in the order it was captured.
*   **AC 2.4:** If a sync conflict occurs (e.g., shift status changed by Agency Administrator while offline), the app must notify the provider and present the conflicting data for resolution.
*   **AC 2.5:** The app must provide visual feedback (e.g., "Syncing...", "Sync Complete") to the provider during the sync process.

#### 3.2.3 Edge Cases & Error Flows

*   **Edge Case 1:** Provider clocks in offline, but the shift was cancelled by the Agency Administrator while offline. Resolution: Upon sync, the app must alert the provider that the shift is no longer active and log the discrepancy for Agency Administrator review.
*   **Edge Case 2:** Device runs out of storage while capturing offline data. Resolution: The app must warn the provider when storage is low and prioritize syncing older data to free up space.
*   **Error Flow:** Sync fails due to server error. Resolution: The app must retry the sync automatically up to 3 times, then notify the provider to try again later or contact support.

## 4. Platform Operator Governance and Tenant Policy Configuration

This section defines the product-level requirements for the Platform Operator Governance ([JNY-89AA69CFE6](../project_glossary.md#jny-89aa69cfe6)) and Tenant Policy Configuration and Governance ([JNY-F9EFC8A7AD](../project_glossary.md#jny-f9efc8a7ad)) journeys. These features enable the Platform Operator ([ACT-0E3EE366E3](../project_glossary.md#act-0e3ee366e3)) to manage the global compliance framework and allow Agency Administrators ([ACT-B91695A020](../project_glossary.md#act-b91695a020)) to configure vertical-specific rules, overrides, and audit trails.

#### 4.1.1. User Story: Manage Vertical Configuration Packages
As a Platform Operator (ACT-0E3EE366E3),
I want to create, version, and activate hot-swappable vertical configuration packages,
So that I can deploy industry-specific compliance and fee profiles (e.g., Healthcare, Industrial, Law Enforcement) to the platform without code changes.

**Acceptance Criteria:**
*   The Platform Operator can create a new vertical configuration package with a unique identifier and version number.
*   The operator can define compliance rulesets (e.g., credential requirements, data retention policies) for each vertical.
*   The operator can activate a configuration package for a specific Tenant or globally.
*   The system must support versioning; previous versions must remain accessible for audit and rollback purposes.
*   **KNOWLEDGE_GAP:** The exact mechanism for defining compliance rulesets (e.g., a visual rule builder, JSON schema, or natural language processing) is not yet defined. The design must allow for a flexible, extensible rules engine.

#### 4.1.2. User Story: View Global Audit Trails
As a Platform Operator (ACT-0E3EE366E3),
I want to view a centralized, immutable audit trail of all configuration changes, overrides, and state changes,
So that I can ensure compliance with regulatory requirements (e.g., CJIS, HIPAA) and investigate any security incidents.

**Acceptance Criteria:**
*   The audit trail must log all actions taken by Platform Operators and Agency Administrators.
*   Each log entry must include the actor's identity, timestamp, action performed, and the before/after state of the configuration.
*   The audit trail must be immutable; no entries can be deleted or modified.
*   The operator can filter the audit trail by date range, actor, and action type.
*   **KNOWLEDGE_GAP:** The specific retention period for audit logs is not yet defined. The design must support configurable retention policies per vertical.

#### 4.1.3. User Story: Manage System-Wide Overrides
As a Platform Operator (ACT-0E3EE366E3),
I want to apply system-wide overrides to specific compliance rules,
So that I can respond to urgent regulatory changes or security threats without waiting for a full configuration package update.

**Acceptance Criteria:**
*   The operator can create an override that temporarily suspends or modifies a specific compliance rule.
*   Overrides must have an expiration date or a manual deactivation requirement.
*   All overrides must be logged in the global audit trail.
*   The operator can view a list of all active overrides and their impact on specific Tenants or verticals.

#### 4.2.1. User Story: Configure Tenant-Specific Compliance Policies
As an Agency Administrator (ACT-B91695A020),
I want to configure compliance policies for my organization based on the active vertical configuration package,
So that I can ensure my organization meets the specific regulatory requirements for my industry (e.g., Healthcare, Industrial).

**Acceptance Criteria:**
*   The Agency Administrator can view the active vertical configuration package and its associated compliance rules.
*   The administrator can customize certain policy parameters (e.g., notification thresholds, approval workflows) within the bounds of the vertical package.
*   The system must validate that any customizations do not violate the core compliance rules of the vertical package.
*   The administrator can save and activate their custom policy configuration.

#### 4.2.2. User Story: Manage Tenant-Specific Overrides
As an Agency Administrator (ACT-B91695A020),
I want to apply overrides to specific compliance rules for my organization,
So that I can handle unique operational requirements or exceptions that are not covered by the standard vertical package.

**Acceptance Criteria:**
*   The Agency Administrator can create an override for a specific compliance rule.
*   Overrides must be justified with a reason code and an expiration date.
*   All overrides must be logged in the tenant-specific audit trail.
*   The administrator can view a list of all active overrides and their impact on their organization's operations.

#### 4.2.3. User Story: View Tenant-Specific Audit Trails
As an Agency Administrator (ACT-B91695A020),
I want to view a centralized, immutable audit trail of all configuration changes, overrides, and state changes within my organization,
So that I can ensure compliance with regulatory requirements and investigate any security incidents.

**Acceptance Criteria:**
*   The audit trail must log all actions taken by Agency Administrators and other authorized users within the organization.
*   Each log entry must include the actor's identity, timestamp, action performed, and the before/after state of the configuration.
*   The audit trail must be immutable; no entries can be deleted or modified.
*   The administrator can filter the audit trail by date range, actor, and action type.
*   The administrator can export the audit trail in a standard format (e.g., CSV, PDF) for external auditing.

### 4.1 Cross-Cutting Concerns

#### 4.3.1. Data Residency and Sovereignty
*   **ASSUMPTION:** The platform must support data residency requirements for different jurisdictions (e.g., GDPR, CCPA). The design must allow for the configuration of data storage locations per Tenant or vertical.
*   **KNOWLEDGE_GAP:** The specific data residency regions supported by the platform are not yet defined. The design must be extensible to support new regions as required.

#### 4.3.3. Offline-First Considerations
*   **ASSUMPTION:** The local-first edge engine must support the caching and synchronization of configuration changes and audit logs. The design must ensure that governance actions can be performed offline and synchronized when connectivity is restored.
*   **KNOWLEDGE_GAP:** The specific conflict resolution strategy for offline configuration changes is not yet defined. The design must allow for a robust conflict resolution mechanism.

### 4.2 Knowledge Gaps and Assumptions

The following items represent unresolved product decisions or explicit assumptions required to complete the Credential Verification and Compliance Activation artifact. These are carried forward for Design and Development to resolve or validate.

| ID | Type | Description | Owner | Evidence Needed |
|---|---|---|---|---|
| KG-01 | Knowledge Gap | The exact mechanism for defining compliance rulesets (e.g., visual rule builder, JSON schema) is not yet defined. | Product | Requirements from Legal/Compliance |
| KG-02 | Knowledge Gap | The specific retention period for audit logs is not yet defined. | Product | Regulatory requirements |
| KG-03 | Knowledge Gap | The specific data residency regions supported by the platform are not yet defined. | Product | Market requirements |
| KG-04 | Knowledge Gap | The specific RBAC model and permission hierarchy are not yet defined. | Product | Security requirements |
| KG-05 | Knowledge Gap | The specific conflict resolution strategy for offline configuration changes is not yet defined. | Product | Technical architecture |
| AS-01 | Assumption | The platform must support data residency requirements for different jurisdictions. | Product | Market requirements |
| AS-02 | Assumption | Access to governance features is restricted to users with the appropriate role. | Product | Security requirements |
| AS-03 | Assumption | The local-first edge engine must support the caching and synchronization of configuration changes and audit logs. | Product | Technical architecture |

---

### 5.1 InstantPay Dispute Resolution (JNY-2975757D41)

**Context:** VeloGig facilitates immediate financial settlement (InstantPay) for specialized gig work. Disputes arise primarily from credential verification failures (e.g., a healthcare provider's license expires mid-shift) or service quality disagreements between the Client and the Workforce Provider.

#### User Story: Provider Disputes InstantPay Hold
As a Workforce Provider (ACT-146D8465B0),
I want to formally dispute an InstantPay hold or deduction caused by a Client's claim of substandard service or a credential verification failure,
So that I can receive my earned compensation and maintain my platform reputation.

**Acceptance Criteria:**
1. **Initiation:** The Provider can initiate a dispute within 24 hours of the InstantPay transaction completion. The system must capture the dispute reason (e.g., "Credential Expired", "Service Not Rendered", "Pay Discrepancy").
2. **Evidence Submission:** The Provider can upload supporting evidence (e.g., shift logs, client communications, credential status screenshots) directly through the mobile interface.
3. **Status Tracking:** The dispute status must be visible in real-time: Submitted, `Under Review`, `Provider Evidence Submitted`, `Client Response Pending`, Resolved, or Escalated.
4. **Notification:** The Client ([ACT-3ED1615F18](../project_glossary.md#act-3ed1615f18)) is notified of the dispute and given a defined window (e.g., 48 hours) to respond with their own evidence.
5. **Resolution:** If the Client does not respond within the window, the dispute is automatically resolved in favor of the Provider, and funds are released.

#### User Story: Platform Operator Adjudication
As a Platform Operator (ACT-0E3EE366E3),
I want to review escalated disputes where Provider and Client evidence conflicts,
So that I can make a final, binding decision based on platform policies and regulatory requirements.

**Acceptance Criteria:**
1. **Escalation Trigger:** Disputes are escalated to the Platform Operator if the Client rejects the Provider's evidence or if the dispute involves a critical compliance failure (e.g., CJIS or HIPAA violation).
2. **Evidence Review:** The Platform Operator can view a side-by-side comparison of Provider and Client evidence, including timestamps and device integrity logs (from [CAP-EDGE-DEVICE-INTEGRITY-VERIFICATION](../project_glossary.md#cap-edge-device-integrity-verification)).
3. **Decision Recording:** The Operator must record a decision and a rationale. This decision is final and triggers an automatic fund transfer or hold release.
4. **Audit Trail:** All dispute interactions, evidence, and decisions are logged in the immutable audit trail ([CON-9B0CF18683](../project_glossary.md#con-9b0cf18683)) for regulatory compliance.

#### User Story: Credential-Related InstantPay Failure
As a Workforce Provider (ACT-146D8465B0),
I want to be immediately notified if my credential verification fails during a shift that has already triggered an InstantPay,
So that I can rectify the issue or dispute the resulting pay hold.

**Acceptance Criteria:**
1. **Real-time Alert:** If the Healthcare Credential Verification ([CAP-HEALTHCARE-CREDENTIAL-VERIFICATION](../project_glossary.md#cap-healthcare-credential-verification)) or Industrial Clearance Verification ([CAP-INDUSTRIAL-CLEARANCE-VERIFICATION](../project_glossary.md#cap-industrial-clearance-verification)) engine detects an invalid credential during a shift, the Provider receives an immediate push notification.
2. **Pay Hold:** The InstantPay for that shift is automatically placed in a `Pending Review` state.
3. **Rectification Path:** The Provider is given a clear path to update their credentials within a grace period (e.g., 24 hours) to have the pay released.
4. **Dispute Option:** If the Provider believes the credential failure is an error, they can initiate a dispute from the notification screen.

### 5.2 Account Closure and Data Export (JNY-B2BD1D1897)

**Context:** Users (Providers, Clients, Agencies) may request account closure for various reasons. VeloGig must ensure that data is exported in a usable format and that all regulatory and financial obligations are met before final deletion.

#### User Story: Provider Account Closure and Data Export
As a Workforce Provider (ACT-146D8465B0),
I want to request account closure and download a complete copy of my personal and professional data,
So that I can leave the platform while retaining my records for tax, legal, or future employment purposes.

**Acceptance Criteria:**
1. **Export Request:** The Provider can initiate an account closure request from the settings menu. The system must present a summary of data to be exported (e.g., profile, shift history, earnings, credentials, dispute history).
2. **Data Format:** The exported data must be provided in a standard, machine-readable format (e.g., JSON, CSV) and a human-readable format (e.g., PDF).
3. **Retention Period:** The system must retain the Provider's data for a mandatory period (e.g., 7 years) as required by tax and labor laws, even after account closure. The export must reflect this retention policy.
4. **Final Deletion:** After the retention period expires, the Provider's personal data is permanently deleted from the platform, except for anonymized aggregate data used for platform analytics.

#### User Story: Client Account Closure and Financial Reconciliation
As a Commercial Client (ACT-3ED1615F18),
I want to close my account and ensure all outstanding financial obligations (e.g., unpaid invoices, dispute holds) are resolved before closure,
So that I avoid future billing issues and legal liabilities.

**Acceptance Criteria:**
1. **Financial Check:** The system must perform a financial reconciliation check before allowing account closure. Any outstanding balances, dispute holds, or pending invoices must be flagged.
2. **Resolution Path:** The Client must resolve all outstanding financial obligations before the closure request can be finalized.
3. **Data Export:** The Client can export their business data (e.g., shift requests, provider interactions, invoices) before closure.
4. **Confirmation:** Upon successful closure, the Client receives a confirmation email with a summary of the closure date and a reference ID for their records.

#### User Story: Agency Administrator Account Closure
As a Agency Administrator (ACT-B91695A020),
I want to close my agency's account and ensure all associated Provider and Client data is handled according to multi-tenant isolation policies,
So that I can dissolve my agency's presence on VeloGig without violating data residency or compliance requirements.

**Acceptance Criteria:**
1. **Tenant Isolation:** The system must ensure that all data associated with the agency (Providers, Clients, shifts) is isolated and exported according to the agency's data residency requirements ([CON-50D510498D](../project_glossary.md#con-50d510498d)).
2. **Provider Notification:** All Providers associated with the agency must be notified of the agency's closure and given the option to transfer their profiles to another agency or remain as independent Providers.
3. **Compliance Audit:** The closure process must trigger a compliance audit to ensure that all regulatory obligations (e.g., CJIS, HIPAA) are met before data is deleted.
4. **Final Deletion:** After the compliance audit and retention period, all agency-specific data is permanently deleted from the platform.

### 5.3 Cross-Reference to Sibling Artifacts

- **Credential Verification (Step 1-2):** Disputes may be triggered by credential verification failures. Ensure seamless integration with the credential status engine.
- **Offline Field Execution (Step 3):** Dispute evidence may include offline shift logs. Ensure these logs are accessible and tamper-proof for dispute resolution.
- **Platform Operator Governance (Step 4):** The Platform Operator role is central to dispute adjudication. Ensure the governance model supports this function.
- **Tenant Policy Configuration (Step 4):** Data retention periods and export formats may vary by tenant vertical. Ensure the policy engine supports these variations.

### 5.4 Conclusion

This section defines the product-level requirements for InstantPay Dispute Resolution and Account Closure, ensuring that VeloGig can handle financial conflicts and user departures in a compliant, transparent, and user-friendly manner. The acceptance criteria are designed to be testable and actionable for the Design and Development phases.
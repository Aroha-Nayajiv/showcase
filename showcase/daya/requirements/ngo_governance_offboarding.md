# NGO Governance & Beneficiary Offboarding

## 1. Cryptographic Beneficiary Profile Creation

This section defines the product requirements for the NGO Operator (ACT-09E028AEB0) to onboard Beneficiaries (ACT-ADA6716160) into the MealCredit platform. The core objective is to establish a 'Cryptographic Profile' that allows the NGO to manage eligibility and distribution while ensuring that the Beneficiary's legal identity is cryptographically segregated from the public financial ledger, thereby eliminating social stigma and protecting 'Highly Sensitive' data (CON-<timestamp>).

### 1.1 User Story: Secure Profile Initialization

As an NGO Operator (ACT-09E028AEB0),
I want to create a new Beneficiary profile by entering legal identity data into a secure, isolated input form,
So that the system generates a unique, anonymous cryptographic voucher ID that can be used for financial transactions without exposing the Beneficiary's identity to the public ledger or other actors.

Acceptance Criteria:

1. Data Segregation: Upon submission of the Beneficiary's legal name and demographic status, the system must immediately hash and encrypt this PII. The PII must be stored in a segregated, 'Highly Sensitive' database partition (CON-<timestamp>) that is inaccessible to the public ledger, Donors (ACT-80C62C7814), or Merchants (ACT-AF904DCFF9).
2. Anonymous ID Generation: The system must generate a unique, non-reversible anonymous voucher ID (UUIDv4) that serves as the primary key for all future financial interactions. This ID must be the only identifier visible to the Beneficiary and the public ledger.
3. NGO Linkage: The NGO Operator's account must be cryptographically linked to the profile as the 'Sponsor,' allowing the NGO to view the Beneficiary's eligibility status and credit balance, but never their legal name or demographic details in the operational dashboard.
4. Security Validation: The input form must enforce strict validation to ensure no PII is logged in application logs or error messages. Any attempt to display PII in the UI must trigger a security alert.

### 1.2 User Story: Profile Verification and Activation

As an NGO Operator (ACT-09E028AEB0),
I want to verify the Beneficiary's identity through a secure, offline or in-app verification process,
So that I can activate the anonymous voucher ID and begin distributing credits, ensuring that only eligible individuals receive assistance.

Acceptance Criteria:

1. Verification Workflow: The system must provide a 'Verification' state for new profiles. The NGO Operator can mark a profile as 'Verified' only after confirming the Beneficiary's identity through approved offline or digital means.
2. Status Isolation: The 'Verified' status must be a metadata flag attached to the cryptographic profile. It must not alter the anonymity of the voucher ID or expose the Beneficiary's PII to any external system.
3. Activation Trigger: Upon verification, the system must activate the voucher ID, allowing it to be linked to a credit pool (CON-2059B17FB2) and used for redemption.
4. Audit Trail: The verification action must be logged in the append-only cryptographic log (CON-1762EA5021) with a timestamp and the NGO Operator's ID, ensuring accountability without linking to PII.

### 1.3 User Story: Demographic Data Management

As an NGO Operator (ACT-09E028AEB0),
I want to update the Beneficiary's demographic status (e.g., household size, dependency count) within the secure profile,
So that I can accurately calculate and allocate credit amounts based on need, while maintaining the strict data isolation required for compliance.

Acceptance Criteria:

1. Secure Update: Demographic updates must be performed through a secure, authenticated interface that re-encrypts the PII before storage. The public ledger must remain completely unaware of demographic changes.
2. Credit Recalculation: Changes to demographic status must trigger a recalculation of the Beneficiary's credit allocation based on the NGO's predefined rules. This must be reflected in the Beneficiary's wallet balance without altering the anonymous voucher ID.
3. History Tracking: All demographic changes must be versioned and stored in the segregated PII partition. The NGO Operator must be able to view the history of changes for internal reporting, but this history must never be exported to the public ledger or donor-facing analytics.
4. Compliance Alignment: The demographic data model must align with the data retention policies (CON-4820FAD5A9) and jurisdictional compliance requirements (CON-30EA97016B) to ensure that PII is handled according to local regulations.

### 1.4 Risk and Mitigation

 Risk: PII Leakage via Metadata. If the anonymous voucher ID is correlated with external data (e.g., transaction timestamps, merchant locations), the Beneficiary's identity could be inferred.
  Mitigation: The system must enforce strict data isolation (CON-0A0288EED4) and use randomized transaction delays or batching where possible to prevent precise correlation. The 'Highly Sensitive' classification (CON-<timestamp>) must be enforced at the database level.
 Risk: Unauthorized Access to PII. If an NGO Operator's account is compromised, the attacker could access the Beneficiary's legal identity.
  Mitigation: Implement multi-factor authentication (MFA) for all NGO Operator accounts. Enforce role-based access control (RBAC) that limits PII access to a minimal set of authorized personnel within the NGO.

### 1.5 Knowledge Gaps

 KNOWLEDGE_GAP: NGO Verification Protocol - NGO Leadership must establish the specific offline or digital verification methods (e.g., government ID scan, community referral) that are acceptable for activating a Beneficiary profile, as this impacts the UI/UX of the verification workflow.
 KNOWLEDGE_GAP: PII Retention Period - Legal/Compliance must define the exact retention period for 'Highly Sensitive' demographic data after a Beneficiary is offboarded, to ensure the 'Strict PII Purging' requirement (Step 3) is implemented correctly.

## 2. Emergency Credit Expiration Rollback

This section defines the product requirements for the emergency credit expiration rollback mechanism within the NGO Governance & Beneficiary Offboarding artifact. It enables the NGO Operator (ACT-09E028AEB0) to reverse the expiration of culinary credits for specific Beneficiaries (ACT-ADA6716160) due to administrative errors, system failures, or exceptional circumstances, while maintaining the integrity of the anonymous credit distribution engine and strict data privacy standards.

### 2.1. User Story: Emergency Rollback Request

As an NGO Operator (ACT-09E028AEB0),
I want to initiate an emergency rollback for a specific Beneficiary's expired credit pool,
So that the Beneficiary can access their funds if the expiration was premature, erroneous, or due to a system failure, without compromising the anonymity of the transaction or the integrity of the financial ledger.

### 2.2. Acceptance Criteria

#### 2.2.1. Rollback Eligibility and Visibility
AC $IP.1: The NGO Operator dashboard must display a list of Beneficiaries (ACT-ADA6716160) whose credit pools have expired within the last [KNOWLEDGE_GAP: rollback_window_days - NGO Governance Lead must establish the maximum number of days post-expiration during which a rollback is permitted, e.g., 7 days].
AC $IP.2: For each eligible Beneficiary, the dashboard must display the original expiration date, the remaining balance (if any), and the reason for expiration (e.g., 'Scheduled Expiration', 'System Error', 'Manual Suspension').
AC $IP.3: The Beneficiary's legal name and sensitive demographic data must be masked or hidden in the rollback interface, displaying only the anonymous voucher ID and the NGO-assigned internal reference ID to prevent de-anonymization (CON-B3D71A437D, CON-C22D030D21).

#### 2.2.2. Rollback Initiation and Justification
AC $IP1.1: The NGO Operator must be able to select a specific Beneficiary and initiate a rollback request.
AC $IP1.2: The system must require the NGO Operator to select a justification category from a predefined list (e.g., 'Administrative Error', 'System Failure', 'Beneficiary Hardship', 'Compliance Exception') and provide an optional free-text field for additional context.
AC $IP1.3: The system must enforce a limit on the number of rollback requests per Beneficiary per credit cycle to prevent financial abuse. [KNOWLEDGE_GAP: max_rollbacks_per_cycle - NGO Governance Lead must establish the maximum number of rollbacks allowed per Beneficiary per credit cycle, e.g., 1].

#### 2.2.3. Approval Workflow (if applicable)
AC $IP2.1: If the rollback amount exceeds [KNOWLEDGE_GAP: rollback_threshold_amount - NGO Governance Lead must establish the monetary threshold above which a secondary approval is required, e.g., $50], the request must be routed to a Platform Administrator (ACT-086A974D63) for secondary approval.
AC $IP2.2: The Platform Administrator (ACT-086A974D63) must receive a notification with the rollback request details, including the justification and the NGO Operator's identity, but without the Beneficiary's PII.
AC $IP2.3: The Platform Administrator (ACT-086A974D63) must be able to approve or reject the request. If rejected, the reason must be provided to the NGO Operator.

#### 2.2.4. Execution and Audit Logging
AC $IP3.1: Upon approval (or if no secondary approval is required), the system must execute the rollback, restoring the credit balance to the Beneficiary's anonymous wallet.
AC $IP3.2: The system must generate an immutable audit log entry (CON-6061FCCA83) for the rollback event, recording the NGO Operator ID, Beneficiary anonymous ID, timestamp, justification, and final status (Approved/Rejected).
AC $IP3.3: The Beneficiary must receive a notification (via the mobile app or SMS) that their credit has been restored, without revealing the source of the restoration (i.e., not explicitly stating 'NGO Operator initiated rollback' if it could lead to de-anonymization).

#### 2.2.5. Error Handling and Edge Cases
AC $IP4.1: If the rollback fails due to a system error, the system must log the failure and notify the NGO Operator and Platform Administrator (ACT-086A974D63) with a generic error message, allowing for manual retry.
AC $IP4.2: The system must prevent rollbacks for Beneficiaries who have already been fully offboarded and whose PII has been purged, as per the compliant offboarding process.
AC $IP4.3: The system must ensure that the rollback does not alter the historical financial ledger entries for the expired period, maintaining the integrity of the append-only log.

### 2.5. Knowledge Gaps

KNOWLEDGE_GAP: rollback_window_days - NGO Governance Lead must establish the maximum number of days post-expiration during which a rollback is permitted.
KNOWLEDGE_GAP: max_rollbacks_per_cycle - NGO Governance Lead must establish the maximum number of rollbacks allowed per Beneficiary per credit cycle.
KNOWLEDGE_GAP: rollback_threshold_amount - NGO Governance Lead must establish the monetary threshold above which a secondary approval is required.

## 3. Strict PII Purging and Cryptographic Offboarding

This section defines the product requirements for the irreversible destruction of Personally Identifiable Information (PII) during the Beneficiary offboarding process. The goal is to ensure that once a Beneficiary (ACT-ADA6716160) is offboarded by an NGO Operator (ACT-09E028AEB0), their legal name and demographic data are cryptographically destroyed or anonymized, while maintaining the integrity of the anonymous financial ledger for compliance and audit purposes.

### 3.1. User Story: Cryptographic PII Destruction

As an NGO Operator (ACT-09E028AEB0),
I want to permanently purge the legal name, demographic status, and any other 'Highly Sensitive' data associated with a Beneficiary (ACT-ADA6716160) upon offboarding,
So that the platform complies with data residency and jurisdictional compliance requirements (CON-30EA97016B, CON-9B82D67FAF) and ensures that no PII can ever be linked back to the anonymous voucher ID.

Acceptance Criteria:

1. Triggering the Purge:
  The NGO Operator can initiate the offboarding process for a specific Beneficiary profile from the NGO Central Command dashboard.
  Upon confirmation, the system must immediately revoke all active and pending voucher tokens associated with that Beneficiary.
  The system must display a final confirmation modal explicitly stating: "This action will permanently and irreversibly destroy all PII associated with this Beneficiary. This cannot be undone."

2. Cryptographic Segregation and Destruction:
  The system must identify all data fields classified as 'Highly Sensitive' (legal name, address, SSN, etc.) as defined by CON-<timestamp>.
  The system must execute a cryptographic destruction of these fields. This involves overwriting the data with random characters multiple times before deletion from the primary database.
  The system must ensure that any cached copies of this PII (e.g., in Redis or CDN caches) are invalidated and purged within [KNOWLEDGE_GAP: Cache invalidation latency - Platform Administrator must establish this] seconds.

3. Anonymization of Ledger Entries:
  The system must ensure that the Beneficiary's anonymous voucher ID remains in the financial ledger for audit purposes (CON-4820FAD5A9), but all links to the now-purged PII are severed.
  The system must generate a new, random UUIDv4 mapping for the offboarded Beneficiary's historical transactions, ensuring that even if the ledger is accessed, the transactions cannot be linked to the Beneficiary's identity.

4. Audit Logging:
  The system must log the offboarding event, including the timestamp, the NGO Operator ID, and the Beneficiary ID, to the append-only cryptographic log (CON-6061FCCA83).
  The log entry must explicitly state that PII has been purged and provide a hash of the destroyed data block for verification purposes.

### 3.2. User Story: Data Retention and Compliance

As an NGO Operator (ACT-09E028AEB0),
I want to ensure that the offboarding process adheres to strict data retention policies,
So that the platform remains compliant with financial regulations governing quasi-cash instruments (CON-226A13FFB8) and unclaimed property laws (CON-B1DFEBEC8C).

Acceptance Criteria:

1. Retention Policy Enforcement:
  The system must retain the anonymized financial transaction history for a period of [KNOWLEDGE_GAP: Financial data retention period - NGO Operator must establish this] years, as required by financial regulations.
  The system must ensure that no PII is retained beyond the point of cryptographic destruction.

2. Jurisdictional Compliance:
  The system must ensure that the purged data is deleted from all storage locations within the specific jurisdiction (SF, NYC, Chicago) where the Beneficiary was registered, in accordance with CON-30EA97016B and CON-9B82D67FAF.
  The system must provide a compliance report to the NGO Operator confirming that all data has been purged from the specified jurisdictions.

3. Unclaimed Property Handling:
  If a Beneficiary has remaining credit balance at the time of offboarding, the system must transfer these funds to the NGO's general pool or initiate the unclaimed property escheatment process as defined by CON-B1DFEBEC8C.
  The system must log the transfer of these funds to the audit log.

### 3.3. Edge Cases and Error Flows

1. Partial Purge Failure:
  If the cryptographic destruction of PII fails for any reason (e.g., database lock, network error), the system must halt the offboarding process and alert the NGO Operator.
  The system must not allow the offboarding to complete until all PII has been successfully purged.
  The system must log the failure and provide a retry mechanism for the NGO Operator.

2. Re-offboarding Request:
  If a previously offboarded Beneficiary requests re-onboarding, the system must treat them as a new Beneficiary.
  The system must not restore any previously purged PII. The NGO Operator must collect all data anew.
  The system must link the new Beneficiary profile to the anonymized historical transactions using the new UUIDv4 mapping.

3. Dispute Adjudicator Access:
  In the event of a financial dispute (JNY-2B038C9362), the Dispute Adjudicator (ACT-7BA340FF76) must be able to access the anonymized transaction history.
  The Dispute Adjudicator must NOT be able to access the purged PII. If PII is required for the dispute, the system must flag the dispute as requiring manual review by the Platform Administrator (ACT-086A974D63).

### 3.5. Validation

 The Designer can validate this by ensuring the UI provides a clear 'Purge PII' action for offboarded beneficiaries, a confirmation modal explaining the irreversible nature of the action, and a success state that confirms the PII has been destroyed.
 The Designer can validate the audit log by ensuring that the log entry for the offboarding event includes the hash of the destroyed data block and the timestamp of the purge.
 The Designer can validate the compliance report by ensuring that the report confirms the purging of data from all specified jurisdictions.

### 3.6. Alignment with Sibling Artifacts

 This artifact's [Dispute Resolution] defers to [JNY-2B038C9362] for the specific workflow of handling disputes involving offboarded beneficiaries; see that artifact for the full treatment.
 This artifact's [Financial Reconciliation] defers to [JNY-35EBA169C6] for the specific workflow of handling unclaimed property and escheatment; see that artifact for the full treatment.

## 4. NGO Central Command: Cryptographic Audit Logging & Offboarding

This section defines the product requirements for the NGO Central Command module, specifically focusing on the append-only cryptographic log auditing of administrative ledger operations and the compliant offboarding of Beneficiaries (ACT-ADA6716160). The system must ensure that all actions taken by the NGO Operator (ACT-09E028AEB0) are immutable, traceable, and compliant with SOC2 Type II structural planning (CON-E84412A0FA).

### 4.1. Append-Only Cryptographic Log Auditing

The NGO Central Command module must maintain an append-only cryptographic log of all administrative ledger operations. This log serves as the single source of truth for financial integrity and compliance evidence, ensuring that no administrative action can be altered or deleted without detection.

#### 4.1.1. User Story: Audit Log Visibility

As an NGO Operator (ACT-09E028AEB0) or Platform Administrator (ACT-086A974D63),
I want to view a real-time, append-only log of all administrative ledger operations performed on Beneficiary profiles,
So that I can ensure financial integrity, detect anomalies, and provide evidence for SOC2 Type II compliance.

#### 4.1.2. Acceptance Criteria

1. Immutable Ledger: The system must generate a new entry for every administrative action (e.g., credit allocation, profile update, offboarding initiation). Once written, entries must be cryptographically linked to the previous entry (e.g., via hash chaining) to prevent tampering.
2. Operation Details: Each log entry must include:
   - Timestamp (UTC).
   - Actor ID (NGO Operator ID).
   - Action Type (e.g., CREDIT_ALLOCATE, PROFILE_UPDATE, OFFBOARD_INITIATE).
   - Target Beneficiary ID (masked/anonymized where appropriate).
   - Pre-action state hash.
   - Post-action state hash.
   - Cryptographic signature of the action.
3. Read-Only Access: NGO Operators must have read-only access to the audit log. They cannot delete, edit, or hide entries.
4. SOC2 Alignment: The log structure must align with SOC2 Type II structural planning (CON-E84412A0FA) requirements for audit trails, ensuring that all changes to financial data are traceable to a specific user and time.
5. Performance: Log retrieval for a single Beneficiary profile must complete within an acceptable latency threshold. [KNOWLEDGE_GAP: NGO Operator must establish acceptable latency threshold for log retrieval, evidence needed: performance requirements for NGO Central Command].

#### 4.1.3. Edge Cases & Error Flows

- Log Corruption: If a log entry fails cryptographic verification, the system must alert the Platform Administrator (ACT-086A974D63) immediately and lock the affected Beneficiary profile from further administrative changes until the issue is resolved.
- High Volume: During peak NGO activity, the system must ensure that log generation does not block administrative actions. Logs should be generated asynchronously.

### 4.2. Compliant Beneficiary Offboarding

The offboarding process must ensure strict PII purging and data retention policies, aligning with the project's commitment to absolute anonymization and data isolation (CON-0A0288EED4, CON-92F07E31B0).

#### 4.2.1. User Story: Emergency Credit Expiration Rollback

As an NGO Operator (ACT-09E028AEB0),
I want to initiate an emergency credit expiration rollback for a Beneficiary (ACT-ADA6716160) who has been offboarded prematurely or incorrectly,
So that the Beneficiary can retain access to their remaining credits without stigma or financial loss.

#### 4.2.2. Acceptance Criteria

1. Rollback Trigger: The system must allow an NGO Operator to initiate a rollback if a Beneficiary's offboarding was triggered by an error (e.g., data entry mistake, system glitch).
2. Credit Restoration: The rollback must restore the Beneficiary's credit balance to the state prior to the erroneous offboarding action.
3. Audit Trail: The rollback action must be logged in the append-only cryptographic log (Section 4.1) with a specific action type OFFBOARD_ROLLBACK.
4. Notification: The Beneficiary must receive a notification (via the mobile app) that their credits have been restored, without revealing the internal administrative error.

#### 4.2.3. User Story: PII Purging & Data Retention

As an NGO Operator (ACT-09E028AEB0),
I want to initiate a compliant offboarding process that triggers strict PII purging for a Beneficiary (ACT-ADA6716160),
So that the platform adheres to data retention policies and minimizes liability by removing highly sensitive data.

#### 4.2.4. Acceptance Criteria

1. PII Classification: All beneficiary-related data must be classified as 'Highly Sensitive' (CON-<timestamp>).
2. Purge Trigger: Upon confirmation of offboarding, the system must trigger a cryptographic purge of all PII associated with the Beneficiary's profile, including legal names and demographic status.
3. Anonymized Retention: Transaction history and redemption data must be retained in an anonymized form for analytics and compliance, but must be cryptographically segregated from any PII (CON-0A0288EED4, CON-92F07E31B0).
4. Verification: The system must provide a verification report to the NGO Operator confirming that PII has been purged and only anonymized data remains.
5. Data Retention Policy: The system must enforce a data retention policy for anonymized data. [KNOWLEDGE_GAP: NGO Operator must establish specific retention period for anonymized transaction data, evidence needed: legal and compliance requirements for data retention].

### 4.3. Dispute Adjudicator Alignment

#### 4.3.1. User Story: Dispute Handoff

As an NGO Operator (ACT-09E028AEB0),
I want to flag a Beneficiary's offboarding for review by the Dispute Adjudicator (ACT-7BA340FF76) if there are unresolved financial discrepancies,
So that the Beneficiary's rights are protected and the platform maintains financial integrity.

#### 4.3.2. Acceptance Criteria

1. Flagging Mechanism: The NGO Operator must be able to flag a Beneficiary's offboarding for dispute review if they detect a discrepancy (e.g., missing credits, incorrect balance).
2. Dispute Adjudicator Access: The Dispute Adjudicator (ACT-7BA340FF76) must receive a notification and have access to the relevant anonymized transaction data and audit log entries to investigate the discrepancy.
3. Resolution: The Dispute Adjudicator must be able to resolve the dispute by either confirming the offboarding or reversing it (triggering the rollback process in Section 4.2.1).
4. Audit Trail: All dispute actions must be logged in the append-only cryptographic log.

### 4.4. Knowledge Gaps

- [KNOWLEDGE_GAP: NGO Operator must establish acceptable latency threshold for log retrieval, evidence needed: performance requirements for NGO Central Command].
- [KNOWLEDGE_GAP: NGO Operator must establish specific retention period for anonymized transaction data, evidence needed: legal and compliance requirements for data retention].

### 4.5. Follow-Up Questions

- Who owns the final decision on data retention periods for anonymized data? (Legal/Compliance)
- What is the acceptable latency for log retrieval for NGO Operators? (Performance/UX)

### 4.6. Implementation Notes

The audit log must be designed to scale with the number of NGO Operators and Beneficiaries.
The PII purge process must be robust and verifiable.
The dispute handoff process must be seamless and intuitive for NGO Operators.

### 4.7. Quality Score

Security: High (Cryptographic integrity, PII purging)
Testability: High (Clear acceptance criteria, edge cases)
Compliance: High (SOC2 Type II alignment, data retention)

### 4.8. Completion Percentage

- 1.0 (This section is complete and ready for review.)

### 4.9. Deliverable Type

- specification

---

## 5. NGO Governance & Beneficiary Offboarding

This section defines the product-level governance workflows for NGO Operators (ACT-09E028AEB0) managing the lifecycle of Beneficiaries (ACT-ADA6716160). The primary objective is to ensure that offboarding, credit expiration, and data purging processes strictly adhere to financial regulations governing quasi-cash instruments, specifically unclaimed property and escheatment laws (CON-B1DFEBEC8C). This artifact ensures that the Platform Administrator (ACT-086A974D63) and NGO Operator can manage beneficiary data with absolute anonymity (CON-B3D71A437D) while maintaining a cryptographically secure audit trail (CON-6061FCCA83).

### 5.1. Cryptographic Profile Management & Segregation

The NGO Operator must be able to create and manage beneficiary profiles where PII is cryptographically segregated from the public ledger. This ensures that the Merchant (ACT-AF904DCFF9) and the Platform's financial engine never see the beneficiary's legal name or demographic status.

User Story 5.1.1: NGO Operator Creates Cryptographic Beneficiary Profile
As an NGO Operator, I want to create a beneficiary profile that generates a unique cryptographic hash for the beneficiary's identity, so that I can issue credits without exposing their PII to the platform's financial ledger.

Acceptance Criteria:
1. The NGO Operator interface provides a secure form to input beneficiary PII (Legal Name, DOB, Demographic Status).
2. Upon submission, the system generates a Beneficiary_Crypto_ID (BCID) using a one-way hash function (e.g., SHA-256) of the PII salted with a project-specific nonce.
3. The PII is stored in a separate, highly restricted database partition (CON-<timestamp>) accessible only to the NGO Operator role.
4. The Beneficiary_Crypto_ID is returned to the NGO Operator and linked to the financial credit pool.
5. The system validates that the Beneficiary_Crypto_ID is unique across the entire platform to prevent duplicate credit issuance.

User Story 5.1.2: NGO Operator Updates Beneficiary Profile
As an NGO Operator, I want to update a beneficiary's demographic status or contact information, so that the platform's analytics remain accurate without compromising the beneficiary's anonymity.

Acceptance Criteria:
1. The NGO Operator can update PII fields in the secure profile view.
2. Upon update, the system recalculates the Beneficiary_Crypto_ID.
3. The system logs the profile update in the append-only cryptographic log (CON-1762EA5021) with a timestamp and the NGO Operator's ID, but does not expose the new PII to the financial ledger.
4. The system notifies the Platform Administrator (ACT-086A974D63) of the profile change for audit purposes, without revealing the PII.

### 5.2. Emergency Credit Expiration Rollbacks

This section defines the workflow for rolling back expired credits in compliance with unclaimed property laws. The system must ensure that credits are not permanently lost due to system errors or beneficiary inactivity, while maintaining strict data isolation.

User Story 5.2.1: NGO Operator Initiates Emergency Credit Rollback
As an NGO Operator, I want to initiate a rollback of expired credits for a specific beneficiary, so that they can continue to access food assistance without violating the platform's credit expiration policies.

Acceptance Criteria:
1. The NGO Operator interface displays a list of beneficiaries with expired credits within the last 30 days.
2. The NGO Operator can select a beneficiary and initiate a "Rollback" action.
3. The system verifies that the beneficiary's Beneficiary_Crypto_ID is valid and that the credits were expired due to inactivity (not fraud).
4. The system restores the expired credits to the beneficiary's wallet, generating a new transaction ID in the financial ledger.
5. The system logs the rollback event in the append-only cryptographic log (CON-6061FCCA83) with the NGO Operator's ID and the reason for rollback.

User Story 5.2.2: Platform Administrator Reviews Rollback Requests
As a Platform Administrator, I want to review all credit rollback requests initiated by NGO Operators, so that I can ensure compliance with financial regulations and prevent abuse.

Acceptance Criteria:
1. The Platform Administrator dashboard displays a list of all rollback requests with the beneficiary's Beneficiary_Crypto_ID, the amount rolled back, and the NGO Operator who initiated it.
2. The Platform Administrator can approve or reject rollback requests.
3. If rejected, the NGO Operator is notified with a reason, and the credits remain expired.
4. All approved and rejected rollback requests are logged in the append-only cryptographic log (CON-6061FCCA83) for SOC2 Type II evidence (CON-E84412A0FA).

### 5.3. Compliant Offboarding & Data Retention

This section defines the offboarding process for beneficiaries, ensuring that PII is purged in compliance with data retention policies and that any remaining credits are handled according to unclaimed property laws.

User Story 5.3.1: NGO Operator Initiates Beneficiary Offboarding
As an NGO Operator, I want to offboard a beneficiary from the platform, so that their PII is securely purged and any remaining credits are handled according to legal requirements.

Acceptance Criteria:
1. The NGO Operator interface provides an "Offboard Beneficiary" action for a selected beneficiary.
2. Upon initiation, the system checks for any remaining credits in the beneficiary's wallet.
3. If credits remain, the system flags the account for "Unclaimed Property Review" and transfers the credits to a central unclaimed property pool managed by the Platform Administrator.
4. The system initiates the PII purging process, deleting the beneficiary's legal name, DOB, and demographic status from the secure database partition.
5. The system retains the Beneficiary_Crypto_ID and transaction history in the append-only cryptographic log (CON-6061FCCA83) for audit purposes, but marks the PII as "Purged."

User Story 5.3.2: System Automates Unclaimed Property Transfer
As the System, I want to automatically transfer unclaimed credits to a central pool when a beneficiary is offboarded, so that the platform complies with escheatment laws.

Acceptance Criteria:
1. The system automatically triggers the unclaimed property transfer process when a beneficiary is offboarded with remaining credits.
2. The system generates a transaction in the financial ledger moving the credits from the beneficiary's wallet to the "Unclaimed Property Pool."
3. The system logs the transfer in the append-only cryptographic log (CON-6061FCCA83) with a timestamp and the reason ("Beneficiary Offboarded").
4. The Platform Administrator is notified of the transfer for reconciliation purposes.

### 5.4. Alignment with Dispute Adjudicator

This section ensures that offboarding-related financial discrepancies are handled in coordination with the Dispute Adjudicator (ACT-7BA340FF76) to maintain financial integrity.

User Story 5.4.1: Dispute Adjudicator Reviews Offboarding Disputes
As a Dispute Adjudicator, I want to review disputes related to beneficiary offboarding, so that I can resolve any financial discrepancies and ensure compliance.

Acceptance Criteria:
1. The Dispute Adjudicator interface displays a list of disputes related to offboarding, including the beneficiary's Beneficiary_Crypto_ID and the nature of the dispute.
2. The Dispute Adjudicator can review the transaction history and the PII purging log for the beneficiary.
3. The Dispute Adjudicator can resolve the dispute by approving or rejecting the offboarding action.
4. If rejected, the system restores the beneficiary's PII from the purge queue and reinstates their credits.
5. All dispute resolutions are logged in the append-only cryptographic log (CON-6061FCCA83) for audit purposes.

### 5.5. Knowledge Gaps & Assumptions

 KNOWLEDGE_GAP: Unclaimed Property Thresholds - The specific monetary threshold for unclaimed property escheatment (e.g., $50, $100) varies by jurisdiction (SF, NYC, Chicago). The `Dispute Adjudicator` or `Platform Administrator` must establish the exact threshold values for each metro footprint. Evidence needed: Legal counsel review of unclaimed property laws in CA, NY, and IL.
 ASSUMPTION: Cryptographic Hashing Algorithm - The system uses SHA-256 for generating Beneficiary_Crypto_IDs. This is a standard, secure choice, but the `Platform Administrator` should confirm if a more robust algorithm (e.g., SHA-3) is required for future-proofing. Evidence needed: Security audit report.
 ASSUMPTION: Data Retention Period for Audit Logs - The system retains the append-only cryptographic log (CON-6061FCCA83) indefinitely for SOC2 Type II compliance. The `Platform Administrator` must confirm if a specific retention period (e.g., 7 years) is required for financial records. Evidence needed: SOC2 Type II audit requirements.
 KNOWLEDGE_GAP: PII Purging Verification - The method for verifying that PII has been completely purged from all backups and caches is not defined. The `Platform Administrator` or `Security Team` must establish the verification process. Evidence needed: Data governance policy.

### 5.6. Edge Cases & Error Flows

1. Beneficiary Re-Enrollment: If a beneficiary is offboarded and then re-enrolled by the same or a different NGO Operator, the system must generate a new Beneficiary_Crypto_ID and treat them as a new user. The old Beneficiary_Crypto_ID must remain in the audit log but be marked as "Inactive."
2. Partial Purge Failure: If the PII purging process fails (e.g., due to a database lock), the system must halt the offboarding process and alert the NGO Operator and Platform Administrator. The beneficiary's status must remain "Active" until the purge is successful.
3. Dispute During Purge: If a dispute is filed against a beneficiary during the PII purging process, the system must pause the purge and notify the Dispute Adjudicator. The purge can only resume after the dispute is resolved.
4. Unclaimed Property Pool Overflow: If the unclaimed property pool exceeds a certain threshold (to be defined by `Platform Administrator`), the system must alert the Platform Administrator to initiate a manual review or transfer to a state-managed escheatment account.

### 5.7. Sibling Artifact References

 Beneficiary Eligibility & Voucher Redemption: This artifact's offboarding process assumes that the beneficiary's eligibility status is managed by the `Beneficiary Eligibility & Voucher Redemption` artifact. The offboarding process does not re-validate eligibility; it simply purges data and handles remaining credits.
 Dispute Resolution & Fraud Investigation: This artifact's dispute handling is limited to offboarding-related discrepancies. General fraud investigation is covered by the `Dispute Resolution & Fraud Investigation` artifact.
 Merchant Onboarding & POS Integration: This artifact does not interact with the merchant POS system. Any credit rollbacks or offboarding actions are handled internally within the platform's financial ledger.
 Donor Onboarding & Funding Activation: This artifact does not impact donor funding. The unclaimed property pool is funded by the platform's financial engine, not directly by donors.

### 5.8. Follow-Up Questions

1. Question: What is the exact monetary threshold for unclaimed property escheatment in SF, NYC, and Chicago?
  Why Critical: The system must automatically transfer credits to the unclaimed property pool when the threshold is exceeded. Without this value, the automation cannot be implemented.
  Answerable: No
  Blocking: Yes
  Source Role: Executor
2. Question: What is the specific retention period for financial audit logs required by SOC2 Type II?
  Why Critical: The system must retain logs for the required period. If the period is too short, the system will be non-compliant. If it is too long, it may violate data minimization principles.
  Answerable: No
  Blocking: Yes
  Source Role: Executor
3. Question: How should the system handle a beneficiary who is offboarded by one NGO and re-enrolled by another?
  Why Critical: The system must ensure that the new NGO Operator does not have access to the old beneficiary's PII or transaction history. The Beneficiary_Crypto_ID must be regenerated.
  Answerable: Yes (Assumed: New BCID generated)
  Blocking: No
  Source Role: Executor

---

## VP decision

**Decision:** Approved

---

## VP feedback

- Section 2.2.1 AC $IP.1: Convert the '30 days' visibility window to KNOWLEDGE_GAP - the maximum post-expiration rollback window is not defined in the project requirement and must be established by the NGO Governance Lead.
- Section 2.2.3 AC $IP2.1: Convert the '$50' secondary approval threshold to KNOWLEDGE_GAP - the monetary limit for Platform Administrator review is not defined in the project requirement and must be established by the NGO Governance Lead.
- Section 5.2.1 AC 1: Convert the '30 days' rollback window to KNOWLEDGE_GAP - the specific eligibility window for credit rollbacks is not defined in the project requirement and must be established by the NGO Governance Lead.
- Section 5.5 Knowledge Gaps & Assumptions: Convert the 'SHA-256' hashing algorithm assumption to KNOWLEDGE_GAP - the specific cryptographic algorithm for Beneficiary_Crypto_IDs is not defined in the project requirement and must be established by the Security Team.
- Section 5.5 Knowledge Gaps & Assumptions: Convert the 'indefinite' log retention assumption to KNOWLEDGE_GAP - the specific retention period for append-only logs is not defined in the project requirement and must be established by the Platform Administrator.

# Compliance, Risk & Governance Inception Artifact

### 1.1. San Francisco (SF) Footprint

**Primary Regulatory Drivers:**
*   **California Consumer Privacy Act (CCPA) / California Privacy Rights Act (CPRA):** As the foundational privacy law, it mandates strict consumer rights (access, deletion, opt-out of sale/sharing). For MealCredit, this directly impacts the 'Absolute Anonymization' strategy, requiring that beneficiary data be treated as 'Sensitive Personal Information' (SPI) with enhanced protections.
*   **Local Data Breach Notification Laws:** SF has specific notification timelines that may be stricter than California state law.

**Compliance Obligations:**
*   **Data Residency:** While CCPA does not mandate strict data residency within California, the 'Highly Sensitive' classification of beneficiary data ([CON-2788862587](../project_glossary.md#con-2788862587)) necessitates that all PII and demographic data for SF beneficiaries be stored in AWS data centers located within the US West (Oregon) or US West (N. California) regions to minimize cross-border transfer risks and ensure low-latency access for local operations.
    *   **KNOWLEDGE_GAP: Specific AWS region mapping for SF data residency - Owner: Cloud/Infrastructure Lead; evidence needed: final AWS region selection based on latency and cost analysis before Design phase.**
*   **Anonymization Standard:** To comply with CPRA's 'Sensitive Personal Information' rules, beneficiary demographic data must be cryptographically segregated from the public financial ledger. The Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) must not have access to raw PII, only to hashed tokens required for system operations.
*   **Merchant Compliance:** SF restaurants (Merchant Partners) must be contractually bound to PCI-DSS Level 1 compliance ([CON-66390130AA](../project_glossary.md#con-66390130aa)) and must not store any beneficiary PII on their local POS systems.

### 1.2. New York City (NYC) Footprint

**Primary Regulatory Drivers:**
*   **New York State Department of Financial Services (NYDFS) Cybersecurity Regulation (23 NYCRR 500):** As a fintech platform handling quasi-cash instruments, MealCredit may be subject to NYDFS oversight, particularly regarding data governance and incident response.
*   **NYC Local Law 158 (Data Breach Notification):** Requires notification to the NY Attorney General within 30 days of discovery, which is stricter than some other jurisdictions.
*   **Financial Consumer Protection:** NYC has robust local laws governing quasi-cash instruments, requiring clear disclosure of terms and conditions to beneficiaries.

**Compliance Obligations:**
*   **Data Residency:** To mitigate the risk of cross-border data transfer issues and ensure compliance with NYDFS expectations, all NYC beneficiary data must be stored in AWS data centers located within the US East (N. Virginia) or US East (Ohio) regions.
*   **Quasi-Cash Instrument Compliance:** The platform must adhere to [CON-B1DFEBEC8C](../project_glossary.md#con-b1dfebec8c), ensuring that unclaimed property and escheatment laws are strictly followed. This requires a robust tracking mechanism for dormant credits, which must be implemented without linking PII to donor impact receipts ([CON-23A501C051](../project_glossary.md#con-23a501c051)).
*   **Anonymization Standard:** NYC's strict data breach notification laws necessitate a 'Zero-Knowledge' posture for the financial ledger. Transaction blinding or batching must be implemented to obscure metadata that could be used for de-anonymization attacks ([CON-C22D030D21](../project_glossary.md#con-c22d030d21)).

### 1.3. Chicago (Chicago) Footprint

**Primary Regulatory Drivers:**
*   **Illinois Biometric Information Privacy Act (BIPA):** If the Expo mobile application ([SUR-43E71C4E2B](../project_glossary.md#sur-43e71c4e2b)) uses any biometric authentication (e.g., FaceID, TouchID) for beneficiary login, BIPA's strict consent and retention requirements apply. This is a critical risk area for the Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) actor.
*   **Illinois Consumer Fraud and Deceptive Business Practices Act:** Requires clear and non-deceptive disclosure of all terms, particularly regarding the 'anonymous' nature of the credits.
*   **Local Data Privacy Ordinances:** Chicago may have specific data privacy ordinances that align with or exceed state-level requirements.

**Compliance Obligations:**
*   **Data Residency:** All Chicago beneficiary data must be stored in AWS data centers located within the US East (N. Virginia) or US East (Ohio) regions to ensure proximity and compliance with local data sovereignty expectations.
*   **Biometric Data Handling:** If biometric data is collected, it must be stored locally on the device (using Expo's SecureStore, [CON-C42F7B521B](../project_glossary.md#con-c42f7b521b)) and never transmitted to MealCredit servers. A clear, explicit consent mechanism must be implemented before any biometric data is accessed.
*   **Anonymization Standard:** Chicago's consumer fraud laws require that the 'anonymous' nature of the credits is not misleading. The platform must ensure that no metadata analysis can link beneficiaries to donors (CON-C22D030D21), and this must be clearly communicated in the user interface.

### 1.4. Assumptions and Knowledge Gaps

*   **ASSUMPTION:** The platform will initially operate only within the US, so international regulations (GDPR, etc.) are out of scope for this specific micro-goal.
*   **ASSUMPTION:** The 'quasi-cash' nature of the credits is accepted as a given, requiring MTL analysis. REJECTED ALTERNATIVE: Treating all three cities as a single 'US' jurisdiction, which would ignore critical local nuances like SF's strict data privacy ordinances and NYC's specific financial consumer protection laws.
*   **KNOWLEDGE_GAP:** Specific data retention periods for donor transaction history vs. anonymous redemption analytics ([CON-4820FAD5A9](../project_glossary.md#con-4820fad5a9)) are not yet defined. Legal must establish these periods before ratification.
*   **KNOWLEDGE_GAP:** The exact 'unclaimed property' thresholds for each jurisdiction (SF, NYC, Chicago) are not yet defined. Legal must establish these thresholds before ratification.

### 1.5. Validation Criteria

The deliverable is validated by ensuring every identified regulation is mapped to a specific architectural control or policy. The 'done' criteria is a ratified Compliance Matrix that explicitly states which data resides where and which regulatory body has jurisdiction over each data type.

---

## 2. Absolute Anonymization and Data Segregation Strategy

This section defines the binding compliance and risk boundaries for the MealCredit platform to ensure absolute beneficiary anonymity, strictly enforcing NFR-SEC-01. The strategy is designed to eliminate social stigma by decoupling beneficiary identity from financial transactions, ensuring compliance with FTC guidelines on anonymity (CON-C22D030D21) and cryptographically segregating demographic data from public ledger entries ([CON-92F07E31B0](../project_glossary.md#con-92f07e31b0)).

### 2.1 Cryptographic Segregation Architecture

To satisfy the requirement that beneficiary demographic status and legal names are cryptographically segregated from public ledger data (CON-92F07E31B0), the platform will implement a strict 'Zero-Knowledge' data model. The financial ledger (managed by the Transaction & Financial Engine, [CAP-TRANSACTION-FINANCIAL-ENGINE](../project_glossary.md#cap-transaction-financial-engine)) will never store, process, or have access to raw Personally Identifiable Information (PII).

*   **Data Partitioning:** Beneficiary PII (names, addresses, demographic status) will be stored in a dedicated, highly restricted vault (e.g., AWS KMS encrypted storage) accessible only by the NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) for eligibility verification. The MealCredit core platform will only hold a hashed, non-reversible token representing the beneficiary.
*   **Access Control:** The Platform Administrator (ACT-086A974D63) will have no access to raw beneficiary PII. Access to the segregation layer is restricted to the NGO Operator role, ensuring that the platform itself remains an anonymous intermediary.
*   **Ledger Integrity:** All financial transactions on the ledger will reference only the hashed beneficiary token and the Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) identifier. This ensures that the financial trail is completely blind to beneficiary identity.

### 2.2 Metadata Analysis and De-anonymization Prevention

To comply with FTC guidelines on anonymity and prevent de-anonymization attacks through metadata analysis (CON-C22D030D21), the platform will enforce strict data minimization and obfuscation protocols on all transactional metadata.

*   **Transaction Blinding:** To prevent correlation attacks, transaction timestamps and amounts will be subject to 'blinding' or batching where necessary. This ensures that individual transaction patterns cannot be easily linked to specific beneficiary behaviors or locations.
*   **UUIDv4 Mapping for Analytics:** Correlation between donor impact receipts and beneficiary redemption events will be handled exclusively through UUIDv4 mapping (CON-23A501C051). This allows for aggregate impact reporting without linking PII to specific redemption events.
*   **Data Residency and Jurisdictional Compliance:** Given the multi-metro footprint (SF, NYC, Chicago), data residency constraints ([CON-30EA97016B](../project_glossary.md#con-30ea97016b)) will be enforced to ensure that beneficiary data remains within the jurisdiction of its origin, further reducing the risk of cross-border data exposure and de-anonymization.

---

### 3.1 Liability Boundaries

*   **Platform Liability:** MealCredit acts as the platform facilitating the transaction but does not hold funds in its own name for extended periods. The platform's liability is limited to the integrity of the transaction routing and the accuracy of the credit distribution logic. Liability for fraudulent transactions initiated by Donors is managed through Stripe's fraud detection tools, with the final financial liability resting with the Donor's issuing bank, subject to Stripe's platform policies.
*   **Merchant Liability:** Merchant Partners (ACT-AF904DCFF9) are fully responsible for the fulfillment of the culinary credits. Any disputes arising from the quality of service, refusal of service, or failure to redeem credits are the direct liability of the Merchant. The platform provides the dispute resolution framework ([CAP-DISPUTE-RESOLUTION-CHARGEBACK-MANAGEMENT](../project_glossary.md#cap-dispute-resolution-chargeback-management)) but does not assume financial liability for merchant performance.
*   **NGO Operator Liability:** NGO Operators (ACT-09E028AEB0) are responsible for the accurate onboarding and eligibility verification of Beneficiaries (ACT-ADA6716160). They bear no direct financial liability for payment processing but are accountable for the integrity of the beneficiary data that triggers credit distribution.

### 3.2 Cross-Jurisdictional KYC and Financial Compliance

As outlined in [CON-62097EBBF3](../project_glossary.md#con-62097ebbf3), the platform must manage Stripe Connected Account liability and Know Your Customer (KYC) compliance across SF, NYC, and Chicago. This requires:

1.  **Standard Onboarding for Merchants:** All Merchant Partners must complete Stripe's standard KYC verification, providing legal entity details, tax identification numbers, and bank account information for payouts. This is a one-time requirement per legal entity, regardless of the number of physical locations within a metro footprint.
2.  **Express Onboarding for NGOs:** NGO Operators will utilize Stripe's Express Onboarding to receive payouts for administrative fees or platform services. They must provide basic identity information and banking details, with the platform handling the collection of specific jurisdictional tax forms (e.g., W-9 or W-8BEN) through Stripe's hosted onboarding flows.
3.  **Donor Verification:** Donors do not require KYC verification for micro-donations below the threshold defined by Stripe's platform policies. However, for high-volume donors or those triggering fraud alerts, Stripe's identity verification tools may be invoked, with the results logged in the platform's audit trail for compliance review.

---

## 4. Data Retention and Cryptographic Segregation

### 4.1 Data Retention and Cryptographic Segregation (CON-4820FAD5A9)

To satisfy the 'Absolute Anonymization' requirement (NFR-SEC-01) and FTC guidelines (CON-C22D030D21), MealCredit must enforce strict data retention policies that cryptographically segregate Beneficiary demographic data from public financial ledger data. This ensures that donor impact receipts can be correlated with redemption events without linking PII.

**Data Classification and Retention Matrix:**

| Data Class | Description | Retention Policy | Access Control |
| :--- | :--- | :--- | :--- |
| **Beneficiary Demographic Data (Highly Sensitive)** | Legal names, addresses, government-issued ID hashes, NGO Operator (ACT-09E028AEB0) verification records. | Retained only for the duration of the Beneficiary's active eligibility period plus 30 days for audit purposes. Upon offboarding ([JNY-4C4BA15817](../project_glossary.md#jny-4c4ba15817)), this data is cryptographically hashed and deleted from the primary database, with the hash retained for fraud prevention ([CAP-FRAUD-DETECTION-FRAUD-PREVENTION-SCREENING](../project_glossary.md#cap-fraud-detection-fraud-prevention-screening)) for a maximum of 7 years to comply with financial audit requirements. | Restricted to the 'NGO Operator' (ACT-09E028AEB0) and 'Platform Administrator' (ACT-086A974D63) via role-based access control (RBAC). The 'Platform Administrator' has no access to raw PII, only to the hashed tokens. |
| **Donor Transaction History (Financially Sensitive)** | Donation amounts, timestamps, payment method tokens (Stripe), donor impact receipts. | Retained indefinitely for financial audit, tax reporting, and donor impact analytics. This data is linked to the Donor ([ACT-80C62C7814](../project_glossary.md#act-80c62c7814)) identity but is never linked to Beneficiary PII. | Accessible to the Donor (ACT-80C62C7814) and the 'Platform Administrator' (ACT-086A974D63) for compliance reporting. |
| **Anonymous Redemption Analytics (Public/Operational)** | Merchant (ACT-AF904DCFF9) redemption events, credit pool utilization rates ([CON-7031BE57B3](../project_glossary.md#con-7031be57b3)), Donation-to-Redemption Velocity (DRV) ([CON-F89C70071E](../project_glossary.md#con-f89c70071e)). | Retained indefinitely for operational analytics and platform optimization. | Accessible to all actor groups for dashboard visualization, but strictly devoid of any PII or direct Beneficiary identifiers. |

**Cryptographic Segregation Mechanism:**

The 'Data Persistence Layer' ([SUR-FA61592CD4](../project_glossary.md#sur-fa61592cd4)) must implement a 'Two-Store' architecture:
1.  **PII Vault:** A separate, highly encrypted database (e.g., AWS RDS with KMS encryption) storing Beneficiary demographic data. Access to this vault is logged via AWS CloudTrail ([CON-FBBBF07295](../project_glossary.md#con-fbbbf07295)) for SOC2 Type II evidence.
2.  **Public Ledger:** A separate, append-only cryptographic log ([CON-6061FCCA83](../project_glossary.md#con-6061fcca83)) in Aurora PostgreSQL storing all financial transactions. This ledger uses UUIDv4 mapping (CON-23A501C051) to link Donor transactions to Merchant redemptions without exposing Beneficiary identities.

**Cross-Reference:**
This artifact's data segregation strategy defers to the 'Technical Architecture & Decision Foundations' artifact for the specific implementation of the 'Two-Store' architecture and UUIDv4 mapping logic; see that artifact for the full treatment.

### 4.2 Unresolved Governance Gaps

*   **KNOWLEDGE_GAP:** The exact dormancy period for culinary credits in San Francisco, New York City, and Chicago has not been ratified by Legal. ASSUMPTION: 12 months is used as a conservative baseline, but this must be validated against local unclaimed property laws.
*   **KNOWLEDGE_GAP:** The specific banking partner holding the donor trust account has not been selected. The escheatment liability model depends on this partner's MTL coverage in each jurisdiction.
*   **KNOWLEDGE_GAP:** The 'Platform Administrator' (ACT-086A974D63) access policy for the PII Vault has not been fully defined. ASSUMPTION: Access is restricted to hashed tokens only, but the exact RBAC permissions need to be ratified by the 'NGO Operator' (ACT-09E028AEB0) and Legal.

### 4.3 Ratification and Next Steps

This compliance posture must be ratified by Legal and the 'Platform Administrator' (ACT-086A974D63) before the Design phase begins. The 'Technical Architecture & Decision Foundations' artifact must then implement the 'Two-Store' architecture and UUIDv4 mapping to enforce these policies.

**Follow-Up Questions:**
1.  Who owns the final ratification of the dormancy period for culinary credits across SF, NYC, and Chicago? (Source: Legal)
2.  Has the banking partner for the donor trust account been selected, and do they hold MTLs in all three jurisdictions? (Source: Finance/Legal)
3.  What are the specific RBAC permissions for the 'Platform Administrator' (ACT-086A974D63) regarding access to the PII Vault? (Source: Security/Legal)

---

## 5. SOC2 Type II Structural Planning and Cryptographic Audit Framework

This section synthesizes the SOC2 Type II structural planning requirements ([CON-81FB01F06B](../project_glossary.md#con-81fb01f06b)) and defines the append-only cryptographic log auditing (CON-6061FCCA83) for all financial ledger mutations. It establishes the governance framework for infrastructure-as-code (IaC) and access control policies, ensuring that compliance is baked into the operational fabric of the MealCredit platform across its three metropolitan footprints (SF, NYC, Chicago).

### 5.1 Access Control Policies

Access control must be strictly governed by the principle of least privilege, aligned with the actor roles defined in the project (Platform Administrator, NGO Operator, Dispute Adjudicator, Donor, Beneficiary, Merchant).

*   **Role-Based Access Control (RBAC):** Access to AWS accounts and services must be granted based on the actor role. For example, the Platform Administrator (ACT-086A974D63) has access to infrastructure management, while the NGO Operator (ACT-09E028AEB0) has access only to beneficiary management and reporting dashboards.
*   **Just-In-Time (JIT) Access:** For highly privileged operations (e.g., database schema changes, key rotation), JIT access must be implemented. This minimizes the attack surface by ensuring that elevated privileges are only granted for a limited, audited duration.
*   **Multi-Factor Authentication (MFA):** MFA is mandatory for all human access to production environments, including the Platform Administrator and Dispute Adjudicator ([ACT-7BA340FF76](../project_glossary.md#act-7ba340ff76)) roles.

### 5.2 Append-Only Cryptographic Log Auditing

To ensure the integrity of all financial ledger mutations and support absolute beneficiary anonymity, an append-only cryptographic log auditing system is mandated (CON-6061FCCA83). This system ensures that once a financial transaction is recorded, it cannot be altered or deleted, providing a tamper-evident trail for all financial activities.

#### 5.2.1 Ledger Mutation Auditing

*   **Append-Only Structure:** All financial ledger mutations (donations, credit issuances, redemptions, refunds) must be written to an append-only log. This log is immutable and cannot be modified after writing.
*   **Cryptographic Hashing:** Each log entry must include a cryptographic hash of the previous entry, creating a chain of integrity. This allows for the detection of any tampering with the log history.
*   **AWS CloudTrail Integration:** All administrative ledger operations and infrastructure changes must be logged to AWS CloudTrail (CON-FBBBF07295). CloudTrail logs provide a comprehensive audit trail of API calls and administrative actions, which is critical for SOC2 Type II evidence.
*   **Data Residency:** The audit logs must be stored in a manner that complies with data residency requirements for each metropolitan footprint (SF, NYC, Chicago). This may involve storing logs in region-specific S3 buckets with strict access controls.

#### 5.2.2 Anonymization and PII Segregation

The audit log must support the absolute anonymization of beneficiary data (NFR-SEC-01). While the log records financial transactions, it must not contain raw PII.

*   **Hashed Identifiers:** Beneficiary identities in the audit log must be represented by cryptographic hashes or anonymous UUIDs, not raw names or PII. This ensures that the audit trail cannot be used to de-anonymize beneficiaries.
*   **Segregation of Duties:** Access to the mapping between hashed identifiers and raw PII must be strictly controlled and segregated from the financial ledger audit log. This prevents any single actor from linking financial transactions to specific individuals.

### 5.3 Validation and Ratification

This SOC2 Type II structural planning and cryptographic audit framework is validated by its ability to provide continuous, tamper-evident evidence of compliance. The 'done' criteria is the ratification of the IaC policies, access control matrix, and audit log structure by the legal and compliance stakeholders.

**SOC2 Type II Control Matrix:**

| Control Area | Requirement | Implementation Strategy | Evidence Source |
| :--- | :--- | :--- | :--- |
| **Change Management** | All infrastructure changes must be version-controlled and reviewed. | IaC (Terraform/CDK) with peer review and automated policy checks. | IaC commit history, PR reviews, policy check logs. |
| **Access Control** | Least privilege access with MFA for all production access. | RBAC, JIT access, mandatory MFA for all human actors. | IAM policies, MFA enforcement logs, JIT access grants. |
| **Audit Logging** | Append-only, cryptographically hashed ledger for all financial mutations. | Immutable log with hash chaining, AWS CloudTrail integration. | Log integrity hashes, CloudTrail event history. |
| **Data Segregation** | PII must be cryptographically segregated from financial audit logs. | Hashed identifiers in logs, separate PII storage with restricted access. | Log content analysis, PII access control logs. |
| **Data Residency** | Data must reside within specified jurisdictions. | Region-specific S3 buckets and RDS instances. | AWS resource configuration, region tags. |

# Compliance, Risk & Governance Inception Artifact

---

## VP decision

**Decision:** Approved

---

## VP feedback

- Section 1.1 Data Residency: Convert the specific AWS region mapping (US West Oregon/N. California) to a KNOWLEDGE_GAP - the requirement does not mandate specific AWS regions, only that data residency constraints be enforced.

# Commercial Client and Corporate Entity Onboarding

## 1. Client Business Intake (JNY-AC150BF960)

### 1.1 User Story
As a Commercial Client ([ACT-3ED1615F18](../project_glossary.md#act-3ed1615f18)),
I want to complete a guided business intake process that captures my corporate identity, tax information, and organizational hierarchy,
So that I can establish a verified corporate entity on VeloGig, configure my initial trust posture, and begin posting specialized workforce shifts across my multi-site operations.

### 1.2 Acceptance Criteria

#### 1.2.1 Corporate Identity & Tax Verification
[ ] The intake flow must capture the Legal Entity Name, Tax ID (EIN), and primary business contact details.
[ ] The system must validate the format of the Tax ID against standard US formats.
[ ] The system must enforce strict data residency and sovereignty compliance (GDPR/CCPA) for all corporate entity data, with local-first storage for sensitive PII where applicable.
[ ] KNOWLEDGE_GAP: The specific third-party KYC/KYB verification provider (e.g., Stripe Identity, Onfido) must be established by the Product Owner to automate tax ID validation.

#### 1.2.2 Organizational Hierarchy Configuration
[ ] The client must be able to define a primary organizational hierarchy, starting with the Parent Corporate Entity.
[ ] The client must be able to add initial 'Sites' or 'Departments' under the Parent Entity to represent distinct operational locations.
[ ] The system must allow the client to assign a default 'Trust Posture' (e.g., Pending, Verified) to the newly created entity.
[ ] The system must support the 'Commercial Client Onboarding and Multi-Site Corporate Entity Setup' ([JNY-87BECA0CBC](../project_glossary.md#jny-87beca0cbc)) journey for adding subsequent sites.

#### 1.2.3 Initial Trust Posture & Compliance
[ ] Upon successful submission of the intake form, the client's account must be created with an initial 'Pending Verification' trust posture.
[ ] The system must restrict the client from posting shifts until the 'Pending Verification' posture is updated to 'Verified' by the Platform Operator ([ACT-0E3EE366E3](../project_glossary.md#act-0e3ee366e3)).
[ ] The system must log all manual assignment bypasses and overrides with device signature and timestamp.

### 1.4 Unresolved Questions
KNOWLEDGE_GAP: Should the platform act as a licensed Money Transmitter (MSB) to facilitate InstantPay, or rely on third-party split-payment providers to avoid direct financial compliance liability?
KNOWLEDGE_GAP: For Law Enforcement agencies, is off-duty work authorized under the 'general agreement' (per-diem pool) or does the system require agency-specific bilateral contracts for every shift authorization?
KNOWLEDGE_GAP: How strictly does the local-first AI enforce regulatory compliance versus providing advisory suggestions when operating in offline mode with conflicting or outdated local vector databases?

---

### 2.1 User Story: Multi-Site Corporate Entity Configuration
As a Commercial Client (ACT-3ED1615F18),
I want to configure my corporate entity's multi-site hierarchy and define the initial organizational structure,
So that I can accurately scope my workforce requirements across different physical locations and establish the correct compliance and fee profiles for each site.

### 2.2 Product Experience: The Onboarding Wizard
The onboarding process for a Commercial Client is a guided, multi-step wizard that transitions the client from a generic sign-up to a fully configured, multi-site corporate entity. This experience is designed to minimize friction while ensuring all necessary legal and operational data is captured to establish the client's initial trust posture.

#### Step 1: Corporate Identity Verification
The first step focuses on establishing the legal identity of the corporate entity. This is a critical trust-building step that ensures the platform is connecting with legitimate businesses.
Action: The client enters their legal business name, Tax ID/EIN, and primary business address.
Validation: The system performs a real-time validation of the Tax ID/EIN format. For MVP purposes, this is a format check; full KYB (Know Your Business) verification is deferred to a post-onboarding review.
Outcome: Upon successful validation, the client is assigned a default `Trust Posture: Pending Verification`.

#### Step 2: Multi-Site Hierarchy Configuration
This step allows the client to define their organizational structure. The platform supports a tree-like hierarchy of sites, allowing for centralized management with localized compliance rules.
Action: The client creates a "Parent Site" (the corporate headquarters) and can then add "Child Sites" (branches, facilities, or project locations).
Data Capture per Site:
Site Name and Address
Primary Contact for the site
Vertical Configuration: The client selects the primary industry vertical for the site (e.g., Healthcare, Industrial, Law Enforcement). This selection triggers the application of the corresponding hot-swappable vertical configuration package, which dictates the specific compliance rules (e.g., HIPAA for Healthcare, CJIS for Law Enforcement) and fee profiles.
Edge Case: If a client operates across multiple verticals, they can assign different verticals to different child sites. The parent site can have a default vertical, which is inherited by child sites unless overridden.

#### Step 3: Initial Trust Posture and Marketplace Access
The final step of the onboarding wizard establishes the client's initial access level to the VeloGig marketplace.
Action: The client reviews their configured entity and site hierarchy.
System Behavior:
The client is granted a `Pending Verification` trust posture.
Access Rights: Clients with a `Pending Verification` posture can browse the marketplace and view available shifts, but cannot post new shifts or engage with Workforce Providers ([ACT-146D8465B0](../project_glossary.md#act-146d8465b0)) until their verification is complete.
Notification: The client receives a confirmation email summarizing their entity setup and outlining the next steps for full verification.

## 3. Platform Operator Governance: Commercial Client Onboarding Review

### 3.1 Purpose and Scope
This section defines the product experience for the Platform Operator (ACT-0E3EE366E3) to review, validate, and approve the Commercial Client (ACT-3ED1615F18) onboarding and entity setup. This process ensures alignment with the Platform Operator Governance ([JNY-89AA69CFE6](../project_glossary.md#jny-89aa69cfe6)) journey and establishes the initial trust and compliance posture required for the client to post shifts on the VeloGig marketplace.

### 3.4 Vertical Configuration Provisioning

The Commercial Client must be able to select and activate a specific vertical configuration package during the Tenant Provisioning and Vertical Config Activation ([JNY-9E54D6B017](../project_glossary.md#jny-9e54d6b017)) journey. This selection dictates the regulatory rules, data residency requirements, and fee structures applied to the tenant.

User Story:
As a Commercial Client, I want to select a vertical configuration package (e.g., Healthcare, Law Enforcement, Industrial) so that the platform automatically applies the correct compliance rules, fee structures, and data handling policies to my organization.

Acceptance Criteria:
1. The Commercial Client is presented with a list of available vertical configuration packages during the onboarding flow.
2. Each package is clearly labeled with its target industry and key compliance requirements (e.g., "Healthcare: HIPAA Compliant, AES-256 Encryption").
3. Upon selection, the platform activates the corresponding configuration, which includes:
Regulatory Rules Engine: The Policy & Rules Engine ([SUR-782954DB8D](../project_glossary.md#sur-782954db8d)) is configured with the specific rules for the selected vertical.
Fee Structure: The Financial Settlement Ledger ([SUR-778E10F5D5](../project_glossary.md#sur-778e10f5d5)) is configured with the appropriate fee profiles for the vertical.
Data Residency: The Data Residency and Multi-Tenant Isolation Surface ([SUR-2FFD65DB4F](../project_glossary.md#sur-2ffd65db4f)) is configured to ensure data sovereignty compliance (e.g., GDPR, CCPA) as required by the vertical.
4. The Commercial Client can view the active vertical configuration and its associated compliance posture at any time.

Edge Cases:
- Multi-Vertical Clients: If a Commercial Client operates in multiple verticals (e.g., a staffing agency that provides both healthcare and industrial workers), the system must support the activation of multiple vertical configuration packages, with clear scoping of which package applies to which subset of workers or shifts.
- Configuration Conflicts: If a client attempts to activate a vertical configuration that conflicts with an existing policy (e.g., a data residency conflict), the system must display a clear error message and prevent the activation until the conflict is resolved.

### 3.5 Policy and Rules Engine Configuration

The Commercial Client must be able to configure and manage the Policy & Rules Engine (SUR-782954DB8D) to enforce specific business rules and compliance requirements within their tenant.

User Story:
As a Commercial Client, I want to configure and manage the Policy & Rules Engine so that I can enforce specific business rules, compliance requirements, and operational constraints within my organization.

Acceptance Criteria:
1. The Commercial Client can define and manage a set of business rules for their tenant (e.g., "Only certified nurses can be assigned to healthcare shifts").
2. The Policy & Rules Engine must be able to enforce these rules in real-time during shift matching and assignment.
3. The Commercial Client can view a log of all rule enforcement actions, including any violations and overrides.
4. The system must support the configuration of data retention and deletion policies compliant with CJIS and HIPAA ([CON-D7840A1341](../project_glossary.md#con-d7840a1341)).

Edge Cases:
- Rule Overrides: If a rule is overridden by an authorized user (e.g., an Agency Administrator), the system must log the override with the user's identity, timestamp, and reason for the override.
- Rule Conflicts: If two rules conflict, the system must have a defined precedence order (e.g., compliance rules take precedence over business rules) and notify the Commercial Client of the conflict.

### 3.6 Governance and Audit Trail

The Commercial Client must be able to configure and view governance settings and audit trails to ensure transparency and accountability.

User Story:
As a Commercial Client, I want to configure and view governance settings and audit trails so that I can ensure transparency and accountability for all actions taken within my organization.

Acceptance Criteria:
1. The Commercial Client can view an immutable audit trail of all configuration changes, overrides, and state changes ([CON-9B0CF18683](../project_glossary.md#con-9b0cf18683)).
2. The audit trail must include the user's identity, timestamp, and the specific change made.
3. The Commercial Client can export the audit trail in a standard format (e.g., CSV, PDF) for compliance reporting.
4. The system must support the configuration of user roles and permissions to ensure that only authorized users can make changes to critical settings.

Edge Cases:
- Audit Trail Tampering: The system must ensure that the audit trail is tamper-proof and cannot be modified or deleted by any user, including administrators.
- Data Export Limits: If the audit trail is very large, the system must support pagination or filtering to allow the Commercial Client to export specific subsets of the data.

### 3.7 Data Residency and Sovereignty

The Commercial Client must be able to configure data residency and sovereignty settings to ensure compliance with cross-jurisdictional data protection laws.

User Story:
As a Commercial Client, I want to configure data residency and sovereignty settings so that I can ensure compliance with cross-jurisdictional data protection laws (GDPR, CCPA) while supporting multi-tenant operations.

Acceptance Criteria:
1. The Commercial Client can specify the data residency region for their tenant (e.g., "US-East", "EU-West").
2. The system must ensure that all data for the tenant is stored and processed within the specified region.
3. The system must support the configuration of data transfer policies to ensure that data is not transferred across regions without explicit consent.
4. The system must provide a clear view of the data residency status for all tenant data.

Edge Cases:
- Cross-Border Data Transfers: If a Commercial Client needs to transfer data across regions (e.g., for a global client), the system must require explicit consent and provide a clear audit trail of the transfer.
- Data Residency Conflicts: If a client's data residency configuration conflicts with a regulatory requirement (e.g., a law that requires data to be stored in a specific country), the system must display a clear error message and prevent the configuration until the conflict is resolved.

### 3.8 Alignment with Sibling Artifacts

Tenant Vertical Configuration Provisioning ([JNY-04F8809204](../project_glossary.md#jny-04f8809204)): This section defines the product experience for configuring tenant policy and governance settings, which is a key part of the Tenant Vertical Configuration Provisioning journey.
Commercial Client Onboarding and Multi-Site Corporate Entity Setup (JNY-87BECA0CBC): This section defines the product experience for configuring tenant policy and governance settings, which is a key part of the Commercial Client Onboarding journey.
Platform Operator Governance (JNY-89AA69CFE6): This section defines the product experience for configuring tenant policy and governance settings, which is a key part of the Platform Operator Governance journey.

### 3.9 Conclusion

This section defines the product experience for the Commercial Client to configure tenant policy and governance settings, ensuring alignment with the Tenant Policy Configuration and Governance ([JNY-F9EFC8A7AD](../project_glossary.md#jny-f9efc8a7ad)) journey. The experience is designed to be intuitive, flexible, and compliant with the specific requirements of each vertical. The Commercial Client is empowered to manage their tenant's policy and governance settings with confidence, knowing that the platform is enforcing the correct rules and compliance requirements.

---

### 3.10 MVP Scope Definition

The MVP scope is strictly bounded to the Commercial Client (ACT-3ED1615F18) actor. It focuses on establishing the corporate identity, configuring the initial organizational hierarchy, and setting the baseline compliance posture. It explicitly excludes advanced features such as multi-tenant namespace management for sub-agencies, complex financial settlement configurations, and automated regulatory reporting beyond basic data classification.

#### 5.1.1. In-Scope Deliverables

1. Client Business Intake ([JNY-AC150BF960](../project_glossary.md#jny-ac150bf960)):
  A guided, multi-step digital form for capturing core corporate entity details (Legal Name, Tax ID, Primary Contact).
  Real-time validation of Tax ID formats for the target verticals (US, EU, etc.).
  Initial data classification and storage in the Local-First Edge Engine ([SUR-D1A2EE5B7A](../project_glossary.md#sur-d1a2ee5b7a)) for PII, ensuring compliance with Classify user PII and credential data as strictly protected, local-first storage ([CON-2D0886886F](../project_glossary.md#con-2d0886886f)).

2. Multi-Site Corporate Entity Setup (JNY-87BECA0CBC):
  A hierarchical tree structure for defining the client's organizational sites (e.g., Parent Company -> Regional Office -> Specific Hospital/Station).
  Assignment of a default Trust Posture (e.g., "Pending Verification") upon successful intake, allowing limited marketplace access (e.g., viewing shifts) while gating posting capabilities.
  Configuration of the primary Tenant Vertical (Law Enforcement, Healthcare, or Industrial) to trigger the appropriate Regulations (Rules Engine) profiles.

3. Initial Compliance Posture Establishment:
  Integration with the Policy & Rules Engine (SUR-782954DB8D) to apply vertical-specific compliance rules (e.g., HIPAA for Healthcare, CJIS for Law Enforcement) based on the selected Tenant Vertical.
  Explicit acknowledgment of Data Residency and Sovereignty ([CON-50D510498D](../project_glossary.md#con-50d510498d)) requirements during the setup flow, allowing the client to select their preferred data residency region.

#### 5.1.2. Out-of-Scope (Deferred to Future Phases)

 Multi-Tenant Namespace Management ([CAP-MULTI-TENANT-NAMESPACE-MANAGEMENT](../project_glossary.md#cap-multi-tenant-namespace-management)): Sub-agency or department-level tenant isolation is deferred. The MVP supports a single flat hierarchy per corporate entity.
 Advanced Financial Settlement (SUR-778E10F5D5): Complex fee structures, split payments, and InstantPay dispute resolution ([JNY-2975757D41](../project_glossary.md#jny-2975757d41)) are out of scope for the MVP onboarding artifact.
 Automated Regulatory Reporting: Generation of 1099-K/1099 forms ([CON-A658A99280](../project_glossary.md#con-a658a99280)) and automated tax compliance routing ([CON-4359544BC5](../project_glossary.md#con-4359544bc5)) are deferred.
 Viral Growth Loops: The Viral Engagement: Shared Invoicing Injection Point Conversion ([JNY-38902F6D90](../project_glossary.md#jny-38902f6d90)) and Shift-Swap Flywheel ([JNY-E787A4D47B](../project_glossary.md#jny-e787a4d47b)) are not part of the initial onboarding flow.

### 3.11 Success Metrics (MVP KPIs)

The success of the MVP onboarding artifact will be measured by the following key performance indicators (KPIs). These metrics are designed to validate both the user experience and the platform's compliance posture.

MVP-ONB-01 | Onboarding Completion Rate | Percentage of initiated Client Business Intake (JNY-AC150BF960) flows that result in a successfully created and verified corporate entity. | > 65% | Indicates the friction level of the intake process. A rate below 65% suggests excessive form fields or validation errors.
MVP-ONB-02 | Time-to-First-Post | Average time (in hours) from successful onboarding completion to the first shift posted by the Commercial Client (ACT-3ED1615F18). | < 24 hours | Measures the speed of value realization. Faster time-to-post correlates with higher early-stage retention.
MVP-ONB-03 | Compliance Posture Accuracy | Percentage of newly onboarded entities that are correctly assigned their vertical-specific compliance rules (HIPAA, CJIS, etc.) without manual intervention. | 100% | Critical for risk management. Any misclassification could lead to regulatory violations.
MVP-ONB-04 | Data Residency Selection Rate | Percentage of clients who actively select a data residency region during the onboarding flow. | > 90% | Validates that the Data Residency and Sovereignty (CON-50D510498D) concern is being addressed and that clients are aware of their options.
MVP-ONB-05 | Support Ticket Volume (Onboarding) | Number of support tickets related to onboarding failures, verification delays, or configuration errors per 100 onboarded clients. | < 5 tickets / 100 clients | Measures the clarity and robustness of the onboarding UX and validation logic.

### 3.12 Traceability Matrix

The following table maps the MVP deliverables to their upstream journey and capability sources, ensuring full traceability.

Client Business Intake Form | Client Business Intake (JNY-AC150BF960) | JNY-AC150BF960 | Captures core entity and contact data.
Multi-Site Hierarchy Setup | Commercial Client Onboarding and Multi-Site Corporate Entity Setup (JNY-87BECA0CBC) | JNY-87BECA0CBC | Defines the organizational tree.
Vertical-Specific Compliance | Policy & Rules Engine (SUR-782954DB8D) | SUR-782954DB8D | Applies HIPAA/CJIS rules based on vertical.
PII Data Classification | Classify user PII and credential data as strictly protected, local-first storage (CON-2D0886886F) | CON-2D0886886F | Ensures local-first storage for sensitive data.
Data Residency Selection | Data Residency and Sovereignty (CON-50D510498D) | CON-50D510498D | Allows client to select data residency region.
Trust Posture Assignment | Reputation and Trust Scoring System ([CAP-REPUTATION-AND-TRUST-SCORING-SYSTEM](../project_glossary.md#cap-reputation-and-trust-scoring-system)) | CAP-REPUTATION-AND-TRUST-SCORING-SYSTEM | Assigns initial "Pending Verification" status.

### 3.13 Knowledge Gaps and Assumptions

The following items are unresolved or assumed for the MVP scope. They must be addressed in subsequent phases or by the designated owners.

 KNOWLEDGE_GAP: MVP-ONB-KG-01 - Data Residency Region Options: The specific list of supported data residency regions (e.g., US-East, EU-West, APAC-South) has not been defined. Decision Owner: Platform Operator (ACT-0E3EE366E3). Evidence Needed: Legal and infrastructure constraints for the initial launch markets.
 KNOWLEDGE_GAP: MVP-ONB-KG-02 - Tax ID Validation Service: The specific third-party service or algorithm for real-time Tax ID validation has not been selected. Decision Owner: Platform Operator (ACT-0E3EE366E3). Evidence Needed: Cost, latency, and coverage analysis of available validation APIs.
 ASSUMPTION: MVP-ONB-AS-01 - Initial Trust Posture: The initial "Pending Verification" trust posture will allow the client to view shifts but not post them. This is a conservative approach to mitigate risk. Owner: Platform Operator (ACT-0E3EE366E3). Evidence Needed: Risk assessment of allowing unverified clients to post shifts.
 ASSUMPTION: MVP-ONB-AS-02 - Single Vertical per Entity: For the MVP, a corporate entity is assumed to operate within a single vertical (e.g., Healthcare only). Multi-vertical support is deferred. Owner: Product Management. Evidence Needed: Market demand for multi-vertical corporate entities.

### 3.14 Edge Cases and Error Flows

The MVP must handle the following edge cases gracefully:

1. Tax ID Validation Failure: If the Tax ID validation fails, the user must be presented with a clear error message and an option to submit for manual review by the Platform Operator (ACT-0E3EE366E3).
2. Network Partition During Onboarding: If the user loses connectivity during the multi-step intake, the Local-First Edge Engine (SUR-D1A2EE5B7A) must cache the partially completed form and allow the user to resume once connectivity is restored, ensuring Network Partition Tolerance ([CON-B861BB9CEA](../project_glossary.md#con-b861bb9cea)).
3. Duplicate Entity Detection: If a client attempts to onboard with a Tax ID that already exists in the system, the platform must prevent duplicate creation and prompt the user to log in or contact support.
4. Unsupported Vertical Selection: If a client selects a vertical that is not yet supported in the MVP (e.g., Law Enforcement if only Healthcare is live), the system must display a clear "Coming Soon" message and allow them to select a supported vertical or request early access.
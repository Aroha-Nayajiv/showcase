# Gig Worker Intake and Intelligent Matching

## 1. Vertical-Specific Identity Data Schema and Edge AI Input Mapping

This section defines the specific data fields and document types required for each vertical (Law Enforcement, Healthcare, Industrial) and maps them to the edge AI model's input capabilities. This establishes the foundational data schema for the Cryptographic Identity Validation capability, ensuring that the SSI credential structures align with the distinct regulatory requirements of each vertical.

### 1.2 Healthcare/Nursing Vertical

Regulatory Context: HIPAA, State Nursing Board Regulations, ACLS/BLS Certification Standards. Primary Actor: Gig Worker (Registered Nurse/Travel Nurse)

#### 1.2.1 Required Document Types and Data Fields

| Document Type | Required Data Fields | Verification Source | Edge AI Processing Method |
| :--- | :--- | :--- | :--- |
| State-Issued ID (Driver's License/State ID) | Full Name, DOB, Address, License Number, Expiration Date, Photo Hash | State DMV Registry | OCR Extraction + Liveness Check (Local SLM) |
| RN License | License Number, Expiration Date, Jurisdiction, Specialties | State Nursing Board | OCR Extraction + Digital Signature Verification |
| BLS/ACLS Certification Card | Certification Type, Expiration Date, Issuing Organization | American Heart Association / Red Cross | OCR Extraction + Hash Verification |
| State Background Check | Clearance Date, Expiration Date, Status (Clear/Conditional) | State/Federal Background Check | Hash Verification + Timestamp Validation |

### 1.3 Industrial/Hazmat Logistics Vertical

Regulatory Context: DOT/HOS Regulations, OSHA Hazmat Certification, CDL Standards. Primary Actor: Gig Worker (CDL Driver/Certified Technician)

### 1.5 Edge AI Output Schema

The edge AI model outputs a structured JSON object containing the extracted data, confidence scores, and hash values for verification.

- **verification_id**: string
- **vertical**: string
- **confidence_score**: float
- **extracted_data**: {'field_name': 'value'}
- **hashes**: {'document_hash': 'string', 'photo_hash': 'string'}
- {'field': 'string', 'message': 'string'}

### 2.1 User Journey: Secure Credential Intake

Actor: Gig Worker (ACT-706CCDBBAA)
Context: Initial onboarding or periodic re-verification via the provider_mobile_interface (SUR-E446EB8DFB).

1. Capture: The user opens the credential intake modal. The interface prompts for specific documents based on the active vertical configuration (e.g., State ID + LE Peace Officer Certificate for Law Enforcement; RN License + BLS Card for Healthcare).
2. Local Pre-Processing: Upon capture, the device's local storage (SUR-390FDF1433) temporarily holds the raw image/PDF. The edge AI inference layer (SUR-95065A003D) initializes the containerized SLM.
3. Visual Integrity Check: The SLM analyzes the document for visual tampering (e.g., font inconsistencies, pixel manipulation, expired dates). It outputs a confidence score for authenticity.
4. Credential Cross-Reference: The SLM extracts key data points (License Number, Expiration Date, Issuing Authority) and compares them against the user's input and any locally cached registry data. It does not send PII to the cloud.

### 2.2 User Journey: Cryptographic Proof Generation

Actor: Gig Worker (ACT-706CCDBBAA)
Context: Post-verification, preparing for asynchronous sync.

1. Hashing: The device generates a SHA-256 hash of the verified credential data and the SLM's confidence score.
2. Signing: The user's private key (stored in the device's secure enclave) signs the hash, creating a cryptographic proof of identity.
3. Local Wallet Storage: The signed proof and the original credential (encrypted) are stored in the device-local wallet. This ensures 100% core capability during network isolations exceeding 72 hours.
4. Proof Submission: Only the cryptographic proof (hash + signature) is queued for asynchronous sync to the serverless cloud relay. The raw PII remains on-device.

### 2.3 Agency Administrator Verification Flow

Actor: Agency Administrator (ACT-B91695A020)
Context: Reviewing worker onboarding status via the client_intake_interface (SUR-C55743A84F).

1. Proof Reception: The Agency Administrator receives the asynchronous sync payload containing the cryptographic proof.
2. Verification: The platform verifies the signature against the worker's public key and checks the hash against the local registry of approved credentials.
3. Status Update: If the proof is valid, the worker's status is updated to "Verified" in the agency's dashboard. If invalid, the worker is flagged for manual review.

## 3. Shift-Swap Flywheel Mechanics

This section defines the mechanics of the Shift-Swap Flywheel, allowing workers to delegate schedule conflicts to unregistered colleagues, converting them into platform users through viral loop triggers.

### 3.1 Shift Conflict Detection

1. Trigger: A Gig Worker (ACT-706CCDBBAA) identifies a schedule conflict for an assigned shift.
2. Initiation: The worker initiates a shift-swap request via the provider_mobile_interface (SUR-E446EB8DFB).
3. Notification: The system generates a unique, time-limited referral link containing the shift details and the worker's cryptographic proof of eligibility.

### 3.2 Viral Conversion Loop

1. Outreach: The worker shares the referral link with a potential substitute (non-platform user).
2. Onboarding: The substitute clicks the link and is prompted to complete a streamlined onboarding process, including credential capture and local AI verification.
3. Verification: The substitute's credentials are verified locally, and a cryptographic proof is generated.
4. Assignment: Upon successful verification, the substitute is assigned the shift, and the original worker is released from the obligation.
5. Reward: The original worker receives a platform credit or fee reduction for successfully converting a new user.

## 4. Acceptance Criteria

## 5. Edge Cases and Error Handling

### 5.1 Offline Sync Conflicts

Scenario: A worker's local state diverges from the cloud state during a network isolation. Resolution: Conflicts are resolved via the established asynchronous offline sync capability (asynchronous_offline_sync) without inventing specific synchronization algorithms. Conflicts are logged for manual review by the Agency Administrator (ACT-B91695A020).

### 5.2 Edge AI Model Drift

Scenario: The local SLM's accuracy degrades over time due to changes in document formats or tampering techniques. Resolution: The system periodically checks for model updates via the serverless cloud relay. Updates are downloaded and applied locally during periods of connectivity. The worker is notified of pending updates and must apply them before proceeding with verification.

### 5.3 Liquidity Partner Risk and Fraud

Scenario: A worker attempts to cash out funds using a compromised or fraudulent identity. Resolution: The specific fraud resolution logic and cross-referencing mechanisms are owned by the Risk Compliance phase. This artifact defers to the Cryptographic Identity Validation capability for the foundational proof generation, but does not define the downstream fraud database interactions or liquidity partner risk mitigation workflows.

## 6. Open Decisions and Knowledge Gaps

### 6.1 Specific Model Versions and Confidence Thresholds
Status: Open
Description: The specific versions of the containerized SLMs and the minimum confidence scores required for automated verification are not yet established.
Impact: These values will impact the performance and accuracy of the local-first edge AI verification workflow.
Owner: Technical Constraints Phase
Resolution Path: Define specific model versions and confidence thresholds in the technical constraints artifact.

### 6.2 Vertical Package Governance
Status: Open
Description: The governance model for hot-swapping vertical configuration packages (compliance rules, fee structures) is not yet defined.
Impact: This will impact how new verticals are onboarded and how compliance rules are updated.
Owner: Product Vision Phase
Resolution Path: Define the governance model for vertical packages in the product vision artifact.

### 6.3 Governing Entity Escalation Workflow
Status: Open
Description: The specific escalation workflow for the Governing Entity (ACT-8D5C6B1AF5) in case of compliance violations or fraud is not detailed.
Impact: This will impact the risk posture and compliance verification process.
Owner: Risk Compliance Phase
Resolution Path: Define the escalation workflow in the risk compliance artifact.

### 6.4 Viral CAC Reduction Traceability
Status: Open
Description: The specific metrics and mechanisms for the Viral CAC Reduction capability (viral_cac_reduction) are not fully detailed in this intake artifact.
Impact: This will impact the measurement of the shift-swap flywheel's effectiveness.
Owner: Success Criteria Phase
Resolution Path: Define specific CAC reduction metrics and viral loop tracking mechanisms in the success criteria artifact.
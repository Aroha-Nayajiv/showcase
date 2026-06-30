# Credential Verification and Compliance Activation

### 1.1 Unified Intake: The Unregistered Vendor to Workforce Provider Transition

The entry point for all specialized gig workers is the Unregistered Vendor ([ACT-C80EBF170E](../project_glossary.md#act-c80ebf170e)) state. This state represents a user who has downloaded the VeloGig application but has not yet been vetted for a specific vertical.

User Story 1.1.1: Initial Identity Capture
As an Unregistered Vendor (ACT-C80EBF170E), I want to create a secure, local-first identity profile so that I can begin the verification process without exposing my PII to the cloud until I am ready.

Acceptance Criteria:
 The application must capture basic identity data (Name, DOB, Contact Info) and store it in local-first storage ([CON-2D0886886F](../project_glossary.md#con-2d0886886f)).
 Data must be encrypted at rest using AES-256 and in transit via TLS 1.3 ([CON-F26B1E3984](../project_glossary.md#con-f26b1e3984)).
 The user must be prompted to select their primary vertical specialization during this initial setup.
 The system must perform a Provider Device Integrity Check & Root Detection ([JNY-07268FC66F](../project_glossary.md#jny-07268fc66f)) to ensure the device is not compromised before proceeding.

User Story 1.1.2: Vertical Selection and Configuration
As an Unregistered Vendor (ACT-C80EBF170E), I want to select my professional vertical (Healthcare, Industrial, or Law Enforcement) so that the platform can present the correct credentialing requirements.

Acceptance Criteria:
 The user must choose one of three verticals:
 1. Healthcare ([JNY-B9F1C271F5](../project_glossary.md#jny-b9f1c271f5)): For RNs, Travel Nurses, etc.
 2. Industrial/Hazmat ([JNY-EFB12D953E](../project_glossary.md#jny-efb12d953e)): For CDL Drivers, Certified Technicians.
 3. Law Enforcement ([JNY-DBCD184BF3](../project_glossary.md#jny-dbcd184bf3)): For Off-Duty Peace Officers/Deputies.
 Upon selection, the Policy & Rules Engine ([SUR-782954DB8D](../project_glossary.md#sur-782954db8d)) must dynamically load the vertical-specific compliance profile.
 The user must be informed of the specific documents required for their chosen vertical.

### 1.2 Vertical-Specific Credential Verification Journeys

Once the vertical is selected, the user transitions into the Provider Onboarding and Credential Verification ([JNY-5AEEEFDC4F](../project_glossary.md#jny-5aeeefdc4f)) journey. This journey is distinct for each vertical due to differing regulatory requirements.

#### 1.2.1. Healthcare Vertical: Healthcare Provider Onboarding (JNY-B9F1C271F5)

User Story 1.2.1.1: Medical License Capture
As a prospective Healthcare Provider, I want to capture my medical license and DEA number so that I can be verified for nursing gigs.

Acceptance Criteria:
 The user must upload images of their State Medical License and DEA Certificate.
 The system must perform local-first OCR (via the Local-First Edge Engine ([SUR-D1A2EE5B7A](../project_glossary.md#sur-d1a2ee5b7a))) to extract key fields (License Number, Expiration Date, State).
 Extracted data must be validated against the state medical board database (via the Serverless Cloud Relay ([SUR-50E19DC151](../project_glossary.md#sur-50e19dc151))).
 All PII and credential data must remain strictly protected, local-first storage (CON-2D0886886F) until verification is complete.
 The system must enforce HIPAA compliance ([CON-F6B76559A7](../project_glossary.md#con-f6b76559a7)) for all data handling.

#### 1.2.2. Industrial/Hazmat Vertical: Industrial/Hazmat Provider Onboarding (JNY-EFB12D953E)

User Story 1.2.2.1: DOT/OSHA Clearance Verification
As a prospective Industrial Provider, I want to upload my DOT card and OSHA certifications so that I can be verified for hazmat logistics gigs.

Acceptance Criteria:
 The user must upload images of their DOT Medical Card and OSHA 10/30 Hour cards.
 The system must perform local-first OCR to extract certification numbers and expiration dates.
 The system must verify the validity of the DOT number with the FMCSA database.
 The system must ensure that all certifications are current and not expired.
 The system must enforce CJIS compliance (CON-<timestamp>) for any law enforcement-related data if the user also has a law enforcement background.

#### 1.2.3. Law Enforcement Vertical: Provider General Onboarding (JNY-DBCD184BF3)

User Story 1.2.3.1: Law Enforcement Credential Capture
As a prospective Law Enforcement Provider, I want to upload my badge and agency authorization so that I can be verified for off-duty gigs.

Acceptance Criteria:
 The user must upload images of their Law Enforcement Badge and Agency ID.
 The system must perform local-first OCR to extract badge number and agency name.
 The system must verify the badge number with the agency's internal database (via the Serverless Cloud Relay (SUR-50E19DC151)).
 The system must enforce CJIS compliance (CON-<timestamp>) for all data handling.
 The system must ensure that the user's agency has a general agreement (per-diem pool) or a bilateral contract for off-duty work authorization.

### 1.3 Local-First Cryptographic Credential Wrapping

To support the Zero-Cost Footprint Philosophy, all credential data must be wrapped in a local-first cryptographic envelope before being synced to the cloud.

User Story 1.4.1: Secure Credential Sync
As a Workforce Provider ([ACT-146D8465B0](../project_glossary.md#act-146d8465b0)), I want my verified credentials to be securely synced to the cloud so that I can be matched with gigs while maintaining data sovereignty.

Acceptance Criteria:
 Once verified, the credential data must be encrypted with a device-specific key.
 The encrypted credential bundle must be synced to the Serverless Cloud Relay (SUR-50E19DC151).
 The cloud relay must store the encrypted bundle in a Multi-Tenant Namespace ([CAP-MULTI-TENANT-NAMESPACE-MANAGEMENT](../project_glossary.md#cap-multi-tenant-namespace-management)).
 The system must ensure that no PII leaves the client network unless explicitly synced via the serverless relay ([CON-D4AD539040](../project_glossary.md#con-d4ad539040)).

### 1.4 Knowledge Gaps and Assumptions

KNOWLEDGE_GAP: The specific API endpoints for verifying medical licenses with state boards are not defined. The Design phase must identify the specific state board APIs for each target jurisdiction. KNOWLEDGE_GAP: The specific API endpoints for verifying DOT numbers with the FMCSA are not defined. The Design phase must identify the FMCSA API contract. KNOWLEDGE_GAP: The specific API endpoints for verifying law enforcement badges with agency databases are not defined. The Design phase must identify the agency-specific API contracts or assume a centralized law enforcement verification service. ASSUMPTION: The Platform Operator ([ACT-0E3EE366E3](../project_glossary.md#act-0e3ee366e3)) is responsible for maintaining the mapping of vertical-specific compliance rules to the Policy & Rules Engine (SUR-782954DB8D). This is assumed to be part of the Platform Operator Governance ([JNY-89AA69CFE6](../project_glossary.md#jny-89aa69cfe6)) journey. ASSUMPTION: The Local-First Edge Engine (SUR-D1A2EE5B7A) is capable of performing OCR on credential documents with sufficient accuracy to extract key fields. This is assumed to be a capability of the containerized edge AI engine (Ollama/vLLM/SGLang) mentioned in the project requirement.

### 1.5 Handoff to Design

This artifact provides the user journeys and acceptance criteria for the Credential Verification and Compliance Activation feature. The Design phase must:

1. Create wireframes and high-fidelity mockups for the Unregistered Vendor (ACT-C80EBF170E) to Workforce Provider (ACT-146D8465B0) transition.
2. Design the vertical-specific credential capture interfaces for Healthcare, Industrial/Hazmat, and Law Enforcement.
3. Define the error states and empty states for failed verifications and expired credentials.
4. Ensure the UI adheres to WCAG guidelines ([CON-FE093BFFFC](../project_glossary.md#con-fe093bfffc)) for accessibility.
5. Design the Offline Field Execution and Clock-In ([JNY-F6CC7FB09F](../project_glossary.md#jny-f6cc7fb09f)) interface to support local-first credential storage.

This completes the product-level specification for Provider General Onboarding (JNY-DBCD184BF3) and Provider Onboarding and Credential Verification (JNY-5AEEEFDC4F).

---

## 2. Document Capture Interface Specifications

This section defines the product requirements for the VeloGig document capture interface, enabling Workforce Providers (ACT-146D8465B0) to submit physical licenses and certifications for verification. The interface is designed to ensure high-fidelity image capture while strictly enforcing local-first data protection and encryption standards.

### 2.1 Capture Workflow and User Experience

The capture flow is triggered during the Provider Onboarding and Credential Verification (JNY-5AEEEFDC4F) journey. The interface must guide the user through a step-by-step process to capture required documents for their specific vertical (Healthcare, Industrial, or Law Enforcement).

 Document Selection: The user selects the type of document to capture (e.g., RN License, CDL Card, DOT Medical Certificate, Peace Officer Commission). The interface dynamically updates the capture instructions based on the selected document type.
 Real-Time Quality Feedback: The camera interface must provide immediate visual feedback on image quality. If the image is blurry, poorly lit, or contains glare, the interface must display a clear, non-intrusive warning (e.g., "Please move to a well-lit area" or "Focus on the text") and prevent the user from proceeding until the image meets minimum quality thresholds.
 Guided Framing: An overlay must be displayed on the camera viewfinder to guide the user in framing the document correctly. The overlay should match the aspect ratio of common license and certification cards to ensure all critical information is captured within the frame.
 Auto-Capture and Review: Once the image meets quality and framing criteria, the user is prompted to review the captured image. The interface must allow the user to retake the photo or adjust the crop if necessary. The user must explicitly confirm the capture before the data is processed.

### 2.3 Vertical-Specific Capture Requirements

The interface must support the specific document types required for each vertical, as defined by the Policy & Rules Engine (SUR-782954DB8D):

 Healthcare (JNY-B9F1C271F5): Capture of state-issued RN licenses, BLS/CPR certification cards, and immunization records. The interface must support multi-page document capture for immunization records.
 Industrial/Hazmat (JNY-EFB12D953E): Capture of CDL cards, DOT medical certificates, and OSHA/Hazmat certification cards. The interface must support capture of both front and back of cards where applicable.
 Law Enforcement (JNY-DBCD184BF3): Capture of peace officer commission cards, CJIS compliance certificates, and state-specific certification documents. The interface must support capture of official government-issued IDs.

### 2.4 Error Handling and Edge Cases

 Capture Failure: If the camera is unavailable or permission is denied, the interface must display a clear error message explaining the issue and provide instructions on how to grant permission. The user must be able to proceed with the onboarding flow without capturing documents, but the account will remain in a "pending verification" state until documents are submitted.
 Network Interruption: If a network interruption occurs during the sync process, the interface must pause the sync and display a "Sync Paused" message. The user must be able to resume the sync manually or automatically when the connection is restored. All locally stored data must be preserved.
 Invalid Document: If the local edge AI engine (SUR-D1A2EE5B7A) determines that the captured document is invalid (e.g., expired, blurry, or missing critical information), the interface must display a clear error message indicating the specific issue and prompt the user to retake the photo.

### 2.5 Acceptance Criteria

 AC-2.1: The document capture interface must provide real-time visual feedback on image quality, preventing the user from capturing blurry or poorly lit images.
 AC-2.2: All captured document images and PII must be stored locally on the user's device in an encrypted format (AES-256) before any sync process is initiated.
 AC-2.3: All data transmitted to the serverless cloud relay must be encrypted using TLS 1.3.
 AC-2.4: The interface must support document capture for all vertical-specific document types (Healthcare, Industrial, Law Enforcement) as defined by the Policy & Rules Engine.
 AC-2.5: The interface must handle network interruptions gracefully, preserving locally stored data and allowing the user to resume the sync process manually or automatically.
 AC-2.6: The interface must display clear error messages for invalid documents, network failures, and camera permission issues, providing actionable guidance to the user.

---

### 3.1 Key Generation and Hardware-Backed Storage

The system must leverage the device's native secure enclave (e.g., Apple Secure Enclave, Android Keystore) to generate and store the provider's private cryptographic key. This key is the root of trust for all credential signing operations.

Actor: Workforce Provider (ACT-146D8465B0)

User Story: As a Workforce Provider, I want my private signing key generated and stored securely on my device's hardware enclave so that even if the device is compromised, my credentials cannot be forged or stolen.

Acceptance Criteria:
1. Upon successful identity verification, the Local-First Edge Engine (SUR-D1A2EE5B7A) initiates a key generation request to the device's hardware keystore.
2. The private key must never leave the secure enclave; only the public key is extracted for bundle creation.
3. The system must verify that the key generation was hardware-backed before proceeding to credential wrapping.
4. If the device lacks hardware-backed keystore support, the system must block credential wrapping and display an error state: "Security requirements not met. Please use a supported device."

### 3.2 Credential Bundle Construction

The Local-First Edge Engine (SUR-D1A2EE5B7A) is responsible for assembling the "Credential Bundle." This bundle contains the provider's verified professional data, the public key, and a cryptographic signature.

Data Components:
 Verified Credentials: Digital representations of licenses (e.g., RN License, DOT Card, Peace Officer ID) captured during the onboarding journey.
 Public Key: The public counterpart to the hardware-stored private key.
 Metadata: Timestamp of bundle creation, device integrity status (from [CAP-EDGE-DEVICE-INTEGRITY-VERIFICATION](../project_glossary.md#cap-edge-device-integrity-verification)), and vertical configuration ID.

Signing Process:
1. The Local-First Edge Engine (SUR-D1A2EE5B7A) hashes the credential data and metadata.
2. The hash is sent to the hardware enclave for signing using the private key.
3. The resulting signature is appended to the bundle.

Acceptance Criteria:
1. The bundle must be cryptographically signed such that any modification to the credential data invalidates the signature.
2. The bundle must be stored locally in an encrypted format (AES-256) within the Local-First Edge Engine (SUR-D1A2EE5B7A) storage.
3. The bundle must be ready for offline verification by Tenants (Agencies/Orgs) without requiring an internet connection.

### 3.3 Offline Verification and Sync

The signed credential bundle enables the Workforce Provider (ACT-146D8465B0) to prove their qualifications in offline scenarios (e.g., CON-<timestamp>: Sustain 100% core scheduling and compliance capability during network isolations >72 hours).

Offline Verification:
 When a Tenant (Agency Administrator) requests verification, the Local-First Edge Engine (SUR-D1A2EE5B7A) provides the signed bundle.
 The Tenant's device verifies the signature using the embedded public key. A valid signature confirms the credentials were issued by the provider and have not been tampered with.

Cloud Sync:
 When connectivity is restored, the Local-First Edge Engine (SUR-D1A2EE5B7A) pushes the signed bundle to the serverless cloud relay.
 The cloud relay stores the bundle for long-term audit and compliance reporting.

Acceptance Criteria:
1. The system must allow the provider to share their signed credential bundle via QR code or secure link for offline verification.
2. The system must automatically sync the bundle to the serverless cloud relay when connectivity is detected, without user intervention.
3. The system must handle sync conflicts by prioritizing the most recently signed bundle.

## 3.4. Key Revocation and Device Wipe

In the event of device loss or compromise, the Workforce Provider (ACT-146D8465B0) must be able to revoke their credentials.

User Story: As a Workforce Provider, I want to be able to remotely revoke my credential signing key if my device is lost, so that my credentials cannot be used by unauthorized parties.

Acceptance Criteria:
1. The Platform Operator (ACT-0E3EE366E3) must have the ability to trigger a credential revocation request via the Platform Operator Governance (JNY-89AA69CFE6) journey.
2. Upon revocation, the serverless cloud relay marks the associated public key as invalid.
3. The next time the device attempts to sync or verify, the system must detect the revocation and invalidate the local credential bundle.
4. The system must support remote wipe of local credential data via the Remote Wipe & Secure Key Revocation for Mobile Devices ([CAP-REMOTE-WIPE-SECURE-KEY-REVOCATION-FOR-MOBILE-DEVICES](../project_glossary.md#cap-remote-wipe-secure-key-revocation-for-mobile-devices)) capability.

## 4.1. Credential Review Dashboard

The Agency Administrator ([ACT-B91695A020](../project_glossary.md#act-b91695a020)) is presented with a prioritized queue of pending credential verifications. The system surfaces providers based on the urgency of their onboarding status and the expiration proximity of their existing credentials.

Dashboard Requirements:
- Provider Context: Each queue item must display the provider's name, selected vertical (Law Enforcement, Healthcare, Industrial), and the specific credentials currently under review (e.g., RN License, DOT Card, Peace Officer Commission).
- Document Preview: A secure, in-app viewer for the uploaded credential documents (images/PDF) captured during the Provider General Onboarding (JNY-DBCD184BF3) phase. The viewer must support zoom and pan for high-fidelity inspection.
- Local-First Integrity Check: The dashboard must display the status of the cryptographic signature validation for the submitted credentials, confirming that the data has not been tampered with since the local-first edge device (SUR-D1A2EE5B7A) signed it.
- Compliance Flags: Any automated flags from the Policy & Rules Engine (SUR-782954DB8D) regarding data residency ([CON-50D510498D](../project_glossary.md#con-50d510498d)) or format anomalies must be visible.

## 4.2. Approval and Rejection Actions

The Agency Administrator (ACT-B91695A020) has two primary actions: Approve and Reject. Each action triggers distinct downstream workflows.

Approve Action:
- Trigger: The administrator confirms the credential is valid, unexpired, and matches the provider's identity.
- Outcome: The provider's vertical-specific compliance profile is activated. The provider is immediately eligible for shift matching ([JNY-D3CEA10548](../project_glossary.md#jny-d3cea10548)) within that vertical.
- Notification: The provider receives a notification that their credentials are verified and they are now active in the selected vertical.

Reject Action:
- Trigger: The administrator identifies a discrepancy, expiration, or forgery.
- Outcome: The provider's status is updated to "Credential Rejected." The provider is notified with a generic reason code (e.g., "Document Expired," "Name Mismatch") to protect against fraud exploitation.
- Re-Submission: The provider is prompted to re-upload the corrected credential via the Provider Onboarding and Credential Verification (JNY-5AEEEFDC4F) journey.

## 4.3. Platform Operator Oversight

The Platform Operator (ACT-0E3EE366E3) retains oversight capabilities for cross-tenant compliance consistency and high-risk verticals (e.g., Law Enforcement CJIS compliance).

Oversight Requirements:
- Audit Trail Access: The Platform Operator (ACT-0E3EE366E3) can view the complete history of all credential approvals and rejections across all tenants.
- Override Capability: In cases of administrative error, the Platform Operator (ACT-0E3EE366E3) can override an Agency Administrator's (ACT-B91695A020) decision, reverting a rejection to pending or reactivating a profile.
- Compliance Reporting: The Platform Operator (ACT-0E3EE366E3) can generate reports on credential verification success rates and rejection reasons to identify systemic issues with specific verticals or document types.

## 4.4. Immutable Audit Trail

All actions taken during the Compliance Activation workflow must be recorded in an immutable audit trail ([CON-9B0CF18683](../project_glossary.md#con-9b0cf18683)). This ensures regulatory compliance and provides a clear chain of custody for all credential verifications.

Audit Trail Requirements:
- Event Logging: Every approval, rejection, and override must be logged with the actor's ID (Platform Operator or Agency Administrator), timestamp, and the specific credential ID involved.
- Data Integrity: Audit logs must be stored in a tamper-evident manner, leveraging the platform's local-first storage architecture where applicable, and synced to the serverless cloud relay (SUR-50E19DC151) for long-term retention.
- Access Control: Only authorized roles (Platform Operator, Agency Administrator) can view or export audit logs.

## 4. Offline Field Execution and Clock-In

### 4.1 Purpose and Scope
This section defines the product requirements for the Offline Field Execution and Clock-In journey (JNY-F6CC7FB09F). It ensures that Workforce Providers (ACT-146D8465B0) can securely clock in, execute shifts, and manage scheduling overrides while operating in a network-isolated environment. The system must sustain 100% core scheduling and compliance capability during network isolations exceeding 72 hours, satisfying the Network Partition Tolerance concern ([CON-B861BB9CEA](../project_glossary.md#con-b861bb9cea)) and the Local-First Edge Engine (SUR-D1A2EE5B7A) philosophy.

### 4.2 User Journey: Offline Clock-In and Shift Execution
Actor: Workforce Provider (ACT-146D8465B0)
Trigger: Provider arrives at a job site with no active internet connection.

1. Local Identity Verification:
   The provider opens the VeloGig mobile application.
   The app detects a lack of connectivity to the Serverless Cloud Relay (SUR-50E19DC151).
   The app automatically switches to Local-First Edge Engine mode.
   The provider authenticates locally using biometric data (fingerprint/face ID) or a PIN, which is validated against the locally cached, encrypted credential profile.
   Constraint: The local AI engine must verify that the provider's credential status (e.g., active license, current insurance) has not expired based on the last known sync date. If the last sync was >30 days ago, the provider must be prompted to sync immediately upon reconnection before clocking in.

2. Shift Selection and Context Loading:
   The app displays a list of upcoming shifts assigned by the Agency Administrator (ACT-B91695A020) or Peer Agency Coordinator ([ACT-233A718221](../project_glossary.md#act-233a718221)).
   Shift details (location, client, required equipment, specific compliance rules) are loaded from the local device storage.
   The provider selects the shift they are about to execute.

3. Geofenced Clock-In:
   The provider initiates a "Clock-In" action.
   The app uses the device's GPS to verify the provider is within the predefined geofence of the job site.
   Edge Case: If the provider is outside the geofence, the app must block the clock-in and display an error message: "You are not at the assigned job site. Please move to the correct location."
   Edge Case: If GPS is unavailable, the app must fall back to a manual location confirmation, requiring the provider to take a photo of a site-specific marker (e.g., a sign, a unique building feature) to prove presence.

4. Local Shift Execution Logging:
   Upon successful clock-in, the app begins logging shift events locally.
   Events include: clock-in time, location pings, break requests, and shift-swap requests.
   All data is encrypted at rest using AES-256 and stored in the local secure enclave.

### 4.3 Offline Shift Conflict and Scheduling Override Management
Actor: Workforce Provider (ACT-146D8465B0)
Concern: Offline Shift Conflict & Scheduling Override Management ([JNY-FE94EB17D1](../project_glossary.md#jny-fe94eb17d1))

1. Shift-Swap Request (Offline):
   If a provider needs to swap a shift, they can initiate a "Shift-Swap Flywheel" request while offline.
   The app identifies potential candidates from the locally cached roster of Workforce Providers (ACT-146D8465B0) who meet the basic criteria (e.g., same vertical, available time slot).
   The request is queued locally and marked as "Pending Sync."
   The provider receives immediate feedback: "Swap request queued. It will be processed when you reconnect."

2. Scheduling Override (Offline):
   In emergency situations, a provider may need to override a scheduled shift (e.g., canceling due to illness).
   The provider selects "Cancel Shift" and provides a reason.
   The app logs the cancellation locally and notifies the Agency Administrator (ACT-B91695A020) upon reconnection.
   Constraint: The app must prevent the provider from canceling a shift less than 2 hours before the start time without explicit manager approval (which will be requested upon reconnection).

### 4.4 Data Residency and Security in Offline Mode
Concern: Data Residency and Sovereignty (CON-50D510498D), Classify user PII and credential data as strictly protected, local-first storage (CON-2D0886886F)

1. Local-First Storage:
   All PII, credential data, and shift logs are stored exclusively on the user's device in offline mode.
   No data is transmitted to the Serverless Cloud Relay (SUR-50E19DC151) until a stable connection is re-established.
   Constraint: The local storage must be encrypted using keys derived from the device's hardware-backed keystore.

2. Data Integrity and Tamper Resistance:
   The Edge Device Integrity and Root Detection Engine ([CAP-EDGE-DEVICE-INTEGRITY-AND-ROOT-DETECTION-ENGINE](../project_glossary.md#cap-edge-device-integrity-and-root-detection-engine)) must continuously monitor the device environment.
   If root access or jailbreaking is detected, the app must lock the provider out of the clock-in functionality and require a remote wipe or re-verification upon reconnection.

3. Synchronization and Conflict Resolution:
   Upon reconnection, the app initiates a sync process with the Serverless Cloud Relay (SUR-50E19DC151).
   The Offline Shift Conflict Resolution Algorithm ([CAP-OFFLINE-SHIFT-CONFLICT-RESOLUTION-ALGORITHM](../project_glossary.md#cap-offline-shift-conflict-resolution-algorithm)) is triggered to resolve any conflicts between local changes and server-side state.
   Conflict Example: If a provider clocks in offline, but the Agency Administrator (ACT-B91695A020) cancels the shift online while the provider was offline, the system must flag this for manual review by the Platform Operator (ACT-0E3EE366E3) or Agency Administrator (ACT-B91695A020).
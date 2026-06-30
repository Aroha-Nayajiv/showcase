# Offline Field Execution and Clock-In

### 1.1 Purpose and Scope
This specification defines the product experience for the Workforce Provider ([ACT-146D8465B0](../project_glossary.md#act-146d8465b0)) to clock in, execute shifts, and clock out while operating in network isolation. The system relies on the Local-First Edge Engine ([SUR-D1A2EE5B7A](../project_glossary.md#sur-d1a2ee5b7a)) to capture high-integrity presence data (GPS, Wi-Fi BSSID, Biometrics) and generate a signed cryptographic proof of presence. The interface must be usable in low-light or high-stress field conditions, and the logic must handle local storage of pending transactions until a sync window is available.

### 1.2 User Journey: Offline Clock-In
Actor: Workforce Provider (ACT-146D8465B0)
Trigger: Provider arrives at the job site and initiates a shift.

1. Initiation: The Provider opens the VeloGig mobile application. The app immediately detects network connectivity status.
2. Offline Mode Detection: If no network is available, the app enters "Offline Mode" and displays a clear "Offline" indicator (addressing [CON-44BE0A2F7F](../project_glossary.md#con-44be0a2f7f) for high-contrast visibility).
3. Identity Verification: The Provider authenticates using biometric facial check. This check is performed locally by the Edge Engine, ensuring no PII leaves the device ([CON-2D0886886F](../project_glossary.md#con-2d0886886f)).
4. Location Capture: The Edge Engine captures GPS coordinates and Wi-Fi BSSID snapshots. It validates that the location matches the assigned shift site within a configurable tolerance.
5. Proof Generation: The Edge Engine generates a cryptographic proof of presence, signed with the device's private key stored in the secure enclave ([CON-F8A3E7F999](../project_glossary.md#con-f8a3e7f999)).
6. Confirmation: The Provider receives a clear "Clock-In Successful" confirmation with the timestamp and location data stored locally.

### 1.3 User Journey: Shift Execution
Actor: Workforce Provider (ACT-146D8465B0)
Trigger: Provider is actively working the shift.

1. Active Shift View: The Provider sees a "Shift in Progress" screen with a countdown timer and key shift details.
2. Spot Checks: The Edge Engine may trigger random biometric spot checks to verify the Provider's continued presence. These checks are event-driven to preserve battery life.
3. Local Logging: Any actions taken during the shift (e.g., break requests, incident reports) are logged locally with timestamps and cryptographic signatures.

## 2. Offline Shift Conflict & Scheduling Override Management

### 2.1 User Journey: Reconnection and Conflict Detection
1. Reconnection Trigger: The Workforce Provider's device detects network availability and initiates a secure sync session with the Serverless Cloud Relay.
2. Local State Submission: The Local-First Edge Engine packages all offline shift execution data (clock-ins, clock-outs, location proofs) and submits them to the relay.
3. Conflict Detection: The Serverless Cloud Relay compares the submitted local state against the authoritative cloud state. If a discrepancy is found (e.g., a shift was already filled by another provider, or a schedule override was applied by the Agency Administrator), a conflict is flagged.
4. Conflict Notification: The Workforce Provider receives a push notification and in-app alert detailing the conflict. The notification includes:
The specific shift or scheduling event affected.
A clear, plain-language explanation of the conflict (e.g., "Your clock-in time conflicts with a schedule override applied by your agency.").
The current authoritative status of the shift.

### 2.2 Conflict Resolution Algorithm Logic
The Offline Shift Conflict Resolution Algorithm ([CAP-OFFLINE-SHIFT-CONFLICT-RESOLUTION-ALGORITHM](../project_glossary.md#cap-offline-shift-conflict-resolution-algorithm)) determines the outcome of the conflict. The product logic must enforce the following resolution strategies:

Last-Write-Wins (LWW): In cases where no explicit override exists, the most recent timestamped action is considered authoritative. This is the default for simple clock-in/out discrepancies.
Priority-Based Override: If the conflict involves a schedule override applied by an Agency Administrator ([ACT-B91695A020](../project_glossary.md#act-b91695a020)) or a Platform Operator ([ACT-0E3EE366E3](../project_glossary.md#act-0e3ee366e3)), the override takes precedence over the provider's offline action, provided the override was applied before the provider's offline action was initiated (based on server-side timestamps).
Provider Credit Preservation: If the conflict results in the provider's shift being invalidated, the system must log the event and ensure the provider is credited for the time worked, subject to the agency's specific payout rules. This is a critical trust factor for the Workforce Provider.

### 3.1 Sync Status and User Experience
The Workforce Provider (ACT-146D8465B0) must have immediate, unambiguous visibility into the synchronization state of their offline data with the Serverless Cloud Relay ([SUR-50E19DC151](../project_glossary.md#sur-50e19dc151)). The UI must display a persistent, non-intrusive status indicator in the field execution header.

 Syncing State: When the device detects a network connection and begins uploading pending shift proofs, the indicator must show a "Syncing..." status with a subtle progress animation. The provider must be able to continue executing shifts without interruption.
 Synced State: Upon successful upload and server acknowledgment, the indicator must change to a "Synced" status with a green checkmark. This confirms that the immutable audit trail ([CON-9B0CF18683](../project_glossary.md#con-9b0cf18683)) has been updated on the cloud relay.
 Failed State: If a sync attempt fails (e.g., server timeout, authentication error), the indicator must turn red and display a "Sync Failed" message. Tapping this indicator must open a detailed error view explaining the failure and offering a "Retry" button.
 Offline State: When no network is available, the indicator must show an "Offline" icon. The provider must be explicitly informed that their actions are being stored locally and will sync automatically when connectivity is restored.

### 3.2 Synchronization Logic and Conflict Resolution
The product must define a clear, deterministic process for how offline data is merged with the cloud state upon reconnection.

 Queue-Based Upload: All offline actions (clock-ins, shift executions, biometric checks) are stored in a local, encrypted queue. Upon reconnection, the app must attempt to upload these items in chronological order.
 Conflict Detection: The Serverless Cloud Relay (SUR-50E19DC151) must validate each incoming offline proof against the current cloud state. If a conflict is detected (e.g., a provider clocks in at two different locations simultaneously, or a shift is already marked as completed by an admin override), the relay must reject the conflicting proof and return a specific error code.
 User Notification of Conflicts: When a conflict is detected, the Workforce Provider must be notified via a push notification and an in-app alert. The alert must clearly state which action was rejected and why (e.g., "Clock-in rejected: Duplicate entry detected").
 Resolution Workflow: The provider must be able to view the details of the rejected action and the conflicting cloud state. They must have the option to "Appeal" the decision, which triggers a review workflow for the Agency Administrator (ACT-B91695A020) or Platform Operator (ACT-0E3EE366E3).

### 3.3 Acceptance Criteria

 AC-3.1: The UI must display a clear "Syncing," "Synced," "Failed," or "Offline" status indicator at all times during field execution.
 AC-3.2: Offline actions must be successfully uploaded to the Serverless Cloud Relay (SUR-50E19DC151) within 5 seconds of network reconnection, assuming a queue of fewer than 100 items.
 AC-3.3: The system must detect and reject conflicting shift proofs, notifying the provider with a clear explanation.
 AC-3.4: All successful syncs must be logged in the immutable audit trail (CON-9B0CF18683) with a cryptographic signature.
 AC-3.5: The local audit log must be encrypted at rest and accessible for export upon provider request.

### 3.4 Edge Cases and Error Flows

 Edge Case: Intermittent Connectivity: If the network drops during a sync, the app must pause the upload queue and resume from the last successful item upon reconnection. The user must be notified of the pause and resume.
 Edge Case: Large Data Volume: If the local queue exceeds a certain size (e.g., 1000 items), the app must warn the provider and suggest connecting to Wi-Fi to expedite the sync.
 Error Flow: Server Unavailable: If the Serverless Cloud Relay (SUR-50E19DC151) is unavailable, the app must continue to store data locally and retry syncs at increasing intervals (exponential backoff).
 Error Flow: Invalid Cryptographic Signature: If a sync proof fails signature validation, the app must discard the proof, log the error, and notify the provider that the action could not be verified.

### 3.5 Sibling Dependencies

 Offline Field Execution and Clock-In ([JNY-F6CC7FB09F](../project_glossary.md#jny-f6cc7fb09f)): This section depends on the local data capture defined in the primary artifact. The sync process must handle all data types generated during the clock-in and shift execution journey.
 Offline Shift Conflict & Scheduling Override Management ([JNY-FE94EB17D1](../project_glossary.md#jny-fe94eb17d1)): This section must integrate with the conflict resolution algorithm to handle cases where offline actions conflict with cloud-side schedule changes.
 Tenant Policy Configuration and Governance ([JNY-F9EFC8A7AD](../project_glossary.md#jny-f9efc8a7ad)): Sync rules and data residency constraints must be configurable per tenant, as defined in this sibling artifact.

### 3.7 Local Data Protection and Storage

All data generated during offline execution (GPS coordinates, Wi-Fi BSSID snapshots, biometric facial checks, shift logs) must be treated as strictly protected, local-first storage (CON-2D0886886F). No provider or shift data may leave the client network unless explicitly synced via the Serverless Cloud Relay (SUR-50E19DC151) ([CON-D4AD539040](../project_glossary.md#con-d4ad539040)).

 Encryption at Rest: All local data stores must be encrypted using AES-256. Keys must be derived from and stored within the device's hardware-backed secure enclave or keystore (CON-F8A3E7F999).
 Data Minimization: Only data strictly necessary for the cryptographic proof of presence and shift execution should be stored locally. PII and credential data must be isolated in separate, encrypted containers.
 Local-First Architecture: The Local-First Edge Engine (SUR-D1A2EE5B7A) is responsible for managing the local data lifecycle, including automatic deletion of temporary cache data that is no longer required for sync.

### 3.8 Cryptographic Integrity and Key Management

To ensure the integrity of offline actions and prevent spoofing, the system must enforce high-entropy curve cryptography for offline device-to-device connections ([CON-5DC20C5FDE](../project_glossary.md#con-5dc20c5fde)).

 Key Storage: Cryptographic private keys used for signing shift proofs must be secured within the device's secure enclave/hardware-backed keystores (CON-F8A3E7F999). Keys must never be exposed to the application layer or stored in plaintext.
 Signing Process: All clock-in, clock-out, and shift execution events must be signed locally using the device's private key. The signature must include a timestamp, GPS coordinates, and a device integrity token.
 Proof Generation: The Edge Device Integrity and Root Detection Engine ([CAP-EDGE-DEVICE-INTEGRITY-VERIFICATION](../project_glossary.md#cap-edge-device-integrity-verification)) must validate the device's root status and environmental integrity before allowing a cryptographic signature to be generated. If the device is rooted or tampered with, the signing process must be blocked.

### 3.9 Offline Compliance and Regulatory Constraints

The system must enforce local compliance rules (CJIS, HIPAA) and data residency constraints offline ([CON-F6B76559A7](../project_glossary.md#con-f6b76559a7), CON-<timestamp>).

 CJIS Compliance (Law Enforcement): For Law Enforcement verticals, all data handling must comply with CJIS security policies. This includes strict access controls, audit logging, and data retention policies. Local data must be automatically purged after a successful sync or after a defined retention period (KNOWLEDGE_GAP: Exact retention period for local offline data must be established by the Compliance team).
 HIPAA Compliance (Healthcare): For Healthcare verticals, all PHI (Protected Health Information) must be encrypted at rest and in transit. Offline access to PHI must be logged and audited. The system must ensure that no PHI leaves the device unless explicitly authorized by the user and synced via a secure channel.
 Data Residency: The system must ensure that data residency constraints are respected even in offline mode. Local data must not be synced to a serverless relay in a different jurisdiction unless explicitly configured to do so ([CON-50D510498D](../project_glossary.md#con-50d510498d)).

### 3.10 Fraud Detection and Spoofing Prevention

To mitigate the risk of location spoofing and biometric bypass attempts, the system must implement robust local heuristics ([CON-08EB4DC34B](../project_glossary.md#con-08eb4dc34b)).

 Multi-Signal Validation: The Edge Device Integrity Verification Engine ([CAP-DEVICE-INTEGRITY-VERIFICATION-ENGINE](../project_glossary.md#cap-device-integrity-verification-engine)) must validate GPS data against Wi-Fi BSSID snapshots and cellular tower information. Inconsistencies between these signals should trigger a fraud alert and prevent the generation of a valid shift proof.
 Biometric Liveness Checks: Biometric facial checks must include liveness detection to prevent spoofing using photos or videos. The Local-First Edge Engine must run these checks locally to ensure privacy and reduce latency.
 Anomaly Detection: The system must log all manual assignment bypasses and overrides with device signature and timestamp ([CON-D543ADCA05](../project_glossary.md#con-d543adca05)). Unusual patterns of clock-ins or shift executions should trigger a review by the Agency Administrator (ACT-B91695A020).

### 3.12 Knowledge Gaps and Assumptions

 KNOWLEDGE_GAP: Exact retention period for local offline data. The Compliance team must establish the specific retention period for local offline data to ensure compliance with CJIS and HIPAA regulations.
 KNOWLEDGE_GAP: Specific thresholds for multi-signal validation. The Engineering team must define the specific thresholds for GPS/Wi-Fi/cellular signal consistency to determine when a fraud alert should be triggered.
 ASSUMPTION: Device Secure Enclave Availability. It is assumed that all target devices (iOS and Android) have a functional hardware-backed secure enclave or keystore. If a device lacks this capability, the system must fall back to a less secure software-based key storage mechanism, which must be explicitly flagged to the user.
 ASSUMPTION: Local LLM Inference Latency. It is assumed that the local LLM inference latency for biometric liveness checks and fraud detection heuristics will remain under 2 seconds ([CON-6DA28A5507](../project_glossary.md#con-6da28a5507)) to ensure a smooth user experience.

### 3.13 Follow-Up Questions

 Question: Who owns the definition of the "fraud alert" threshold for multi-signal validation?
  Why Critical: This threshold directly impacts the user experience (false positives) and security posture (false negatives).
  Answerable: False
  Blocking: True
 Question: What is the exact data retention policy for local offline data in the Law Enforcement vertical?
  Why Critical: Non-compliance with CJIS retention policies can result in legal liability.
  Answerable: False
  Blocking: True
- **Source Role": "executor

---

## 4. Accessibility and Field Usability Requirements

This section defines the accessibility and usability requirements for the Offline Field Execution and Clock-In journey (JNY-F6CC7FB09F). These requirements ensure that the Workforce Provider (ACT-146D8465B0) and Agency Administrator (ACT-B91695A020) can interact with the Local-First Edge Engine (SUR-D1A2EE5B7A) interface effectively in high-stress, low-light, or high-glare field conditions, while maintaining strict compliance with WCAG 2.1 AA standards.

### 4.1 High-Contrast and Low-Light Mode (CON-44BE0A2F7F)

User Story: As a Workforce Provider (ACT-146D8465B0) working in a dark environment (e.g., a police car at night, a dimly lit hospital corridor, or a warehouse), I need the interface to automatically adjust to a high-contrast, low-glare mode so that I can read critical shift data and clock-in buttons without eye strain or distraction.

Acceptance Criteria:
1. Automatic Detection: The interface must detect ambient light levels via device sensors. If light levels fall below a defined threshold, the system must automatically switch to 'Night Mode' (high-contrast dark theme).
2. Manual Override: Users must be able to manually toggle between 'Day Mode' (light theme) and 'Night Mode' (dark theme) in the settings, regardless of ambient light.
3. Contrast Ratios: All text and interactive elements must maintain a minimum contrast ratio of 4.5:1 against their background in both Day and Night modes, per WCAG 2.1 AA.
4. Glare Reduction: Night Mode must use deep, non-pure black backgrounds to reduce OLED burn-in risk and improve readability in low-light conditions.
5. Field Visibility: Buttons and critical actions (e.g., 'Clock In', 'Emergency') must be visually distinct with high-contrast borders or background fills to ensure they are identifiable at a glance.

### 4.2 Large-Text and Scalable Typography

User Story: As a Workforce Provider (ACT-146D8465B0) with visual impairments or as a Dispatch Coordinator ([ACT-233A718221](../project_glossary.md#act-233a718221)) viewing data on a small mobile device, I need the interface to support dynamic text scaling so that all information remains legible without horizontal scrolling.

Acceptance Criteria:
1. Dynamic Type Support: The interface must respect the device's system-level text size settings (e.g., iOS Dynamic Type, Android Font Scale).
2. Scalability: Text must scale up to 200% of its base size without breaking the layout or causing content to overflow its container.
3. Touch Target Size: All interactive elements (buttons, links, toggles) must have a minimum touch target size of 44x44 CSS pixels (or equivalent physical size) to accommodate users with motor impairments or those using the device in motion.
4. Line Height: Line height must be at least 1.5 times the font size to improve readability for users with dyslexia or visual processing difficulties.

### 4.3 Screen Reader and Assistive Technology Support (CON-063B970A17)

User Story: As a Workforce Provider (ACT-146D8465B0) who is blind or has low vision, I need the interface to be fully compatible with screen readers (e.g., VoiceOver, TalkBack) so that I can navigate the clock-in process and understand shift details independently.

Acceptance Criteria:
1. Semantic HTML: All UI components must use semantic HTML elements (e.g., `<button>`, `<nav>`, `<main>`) to ensure proper structure and navigation for screen readers.
2. ARIA Labels: All interactive elements must have descriptive aria-label or aria-labelledby attributes. For example, a 'Clock In' button must announce 'Clock In, button' to the screen reader.
3. Focus Management: When the user navigates between screens (e.g., from the shift list to the clock-in screen), focus must be programmatically moved to the most relevant element (e.g., the 'Clock In' button) to prevent disorientation.
4. Error Announcements: When an error occurs (e.g., 'Clock In Failed: Location Invalid'), the error message must be announced to the screen reader immediately, and the focus must be moved to the error message.
5. Local Desktop Admin Apps: For the Agency Administrator (ACT-B91695A020) using local desktop admin applications, the interface must support keyboard-only navigation and provide full screen reader compatibility for all administrative tasks, including shift overrides and audit log reviews.

### 4.4 Cognitive Load and Stress Reduction

User Story: As a Workforce Provider (ACT-146D8465B0) in a high-stress situation (e.g., a law enforcement officer responding to an emergency), I need the interface to be simple and uncluttered so that I can perform the clock-in action quickly and without confusion.

Acceptance Criteria:
1. Minimalist Design: The clock-in screen must display only the essential information: current time, shift status, and the 'Clock In' button. Secondary information (e.g., shift history, settings) must be accessible via a separate menu.
2. Clear Feedback: The interface must provide immediate, clear visual and haptic feedback when a user interacts with a button (e.g., a 'Clock In' button changes color and vibrates upon successful tap).
3. Confirmation Steps: Critical actions (e.g., 'Cancel Shift') must require a confirmation step to prevent accidental actions.
4. Consistent Layout: The layout of the clock-in screen must remain consistent across all verticals (Law Enforcement, Healthcare, Industrial) to reduce cognitive load for users who work across multiple agencies.

### 4.5 Verification and Testing

Automated Testing: All UI components must pass automated accessibility tests (e.g., axe-core, Lighthouse) for WCAG 2.1 AA compliance.
User Testing: Usability testing must be conducted with users who have visual and motor impairments to validate the effectiveness of the high-contrast and large-text modes.
Field Testing: The interface must be tested in real-world field conditions (e.g., low-light environments, high-glare conditions) to ensure readability and usability.
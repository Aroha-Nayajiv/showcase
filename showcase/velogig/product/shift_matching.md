# Shift Request, Matching, and Inter-Agency Discovery

## 1. Commercial Client Shift Request and Immediate Feedback

### 1.1 User Story
As a Commercial Client ([ACT-3ED1615F18](../project_glossary.md#act-3ed1615f18)) managing a multi-site corporate entity setup ([JNY-87BECA0CBC](../project_glossary.md#jny-87beca0cbc)),
I want to post a shift request with specific role, location, time, and certification requirements,
So that the VeloGig Policy & Rules Engine ([SUR-782954DB8D](../project_glossary.md#sur-782954db8d)) can immediately validate compliance and provide me with real-time market feedback on the likelihood of a fill.

### 1.2 Acceptance Criteria

#### 1.2.1 Shift Submission and Validation
- AC-1.1: Required Fields Enforcement
 The system MUST require the following fields before allowing submission:
Role: Selection from a vertical-specific dropdown (e.g., "Registered Nurse", "Off-Duty Deputy", "CDL Driver").
Location: Geospatial coordinates or a validated address within the platform's service area.
Time: Start and end timestamps, including timezone.
Required Certifications: A dynamic list of certifications based on the selected Role and Vertical (e.g., BLS for Healthcare, Hazmat for Industrial). The system MUST validate that the selected certifications are active and recognized by the Policy & Rules Engine (SUR-782954DB8D).

- AC-1.2: Vertical-Specific Compliance Check
 Upon submission, the system MUST run an immediate compliance check against the active vertical configuration package. If the shift violates any hard constraints (e.g., maximum shift duration, mandatory rest periods, or specific licensing requirements for Law Enforcement), the system MUST reject the submission and display the specific policy violation.

#### 1.2.2 Immediate System Feedback
- AC-1.3: Estimated Fill Time
 Upon successful validation, the system MUST display an "Estimated Fill Time" to the Commercial Client. This is a heuristic based on historical data for the selected Role, Location, and Time slot. [KNOWLEDGE_GAP: The specific algorithm or data source for calculating "Estimated Fill Time" is not yet defined. The Product Owner must establish the logic for this heuristic.] If no data is available, the system MUST display "Market Data Unavailable."

- AC-1.4: Provider Availability Indicator
 The system MUST display a qualitative indicator of provider availability (e.g., "High Demand", "Moderate Supply", "Low Supply") based on the number of active, credentialed Workforce Providers ([ACT-146D8465B0](../project_glossary.md#act-146d8465b0)) in the immediate vicinity who match the required certifications.

- AC-1.5: Inter-Agency Discovery Prompt
 If the system determines that local provider supply is insufficient to meet the "Estimated Fill Time" threshold, it MUST prompt the Commercial Client to enable "Inter-Agency Discovery" ([JNY-2105A9EBCD](../project_glossary.md#jny-2105a9ebcd)). This allows the shift to be broadcast to partner agencies, subject to the Peer Agency Coordinator's ([ACT-233A718221](../project_glossary.md#act-233a718221)) approval rules.

## 2. Workforce Provider Shift Discovery and Acceptance

### 2.1 User Story: Local-First Shift Discovery
As a Workforce Provider (ACT-146D8465B0),
I want to discover available shifts on my local device based on my verified credentials, current location, and availability,
So that I can accept high-value opportunities instantly, even when operating in offline or low-connectivity environments.

#### 2.2.1 Local-First Filtering Logic
The application MUST perform all shift filtering locally on the device using the Local-First Edge Engine ([SUR-D1A2EE5B7A](../project_glossary.md#sur-d1a2ee5b7a)) to ensure zero-latency discovery and $0 baseline compute costs.

AC 2.1: Credential-Based Filtering
 The app MUST filter out shifts that require certifications not present in the provider's locally cached, signed credential data. For Healthcare shifts, the app MUST verify the provider holds a valid credential status (e.g., active RN license). For Industrial shifts, the app MUST verify the provider holds a valid clearance status (e.g., OSHA-10, Hazmat). Edge Case: If a provider's local credential cache is expired or missing, the app MUST display a clear error state prompting them to sync with the serverless relay ([SUR-50E19DC151](../project_glossary.md#sur-50e19dc151)) to update their profile before viewing shifts.

AC 2.2: Proximity and Availability Filtering
 The app MUST filter shifts based on the provider's current geolocation (GPS) and the shift's location. KNOWLEDGE_GAP: Proximity Threshold - Product Owner must establish the default maximum distance (e.g., 10 miles) or travel time (e.g., 30 minutes) for a shift to appear in the default feed. The app MUST filter out shifts that conflict with the provider's locally stored availability calendar.

#### 2.2.2 Shift Discovery Interface
 AC 2.3: Shift Feed Display
 The provider MUST see a list of available shifts, each displaying: Role, Location, Start/End Time, Pay Rate, and Required Certifications.
 Each shift MUST include a "Match Score" indicator (e.g., High/Medium/Low) based on proximity and credential alignment.
 ASSUMPTION: Match Score - The score is a heuristic based on proximity and credential match, not a hard guarantee of acceptance. Owner: Product, Evidence needed: Historical matching data.

 AC 2.4: Offline State Handling
 If the device is offline, the app MUST display a banner indicating "Offline Mode: Showing cached shifts."
 The app MUST allow the provider to view and "Express Interest" in shifts, which are queued locally for synchronization when connectivity is restored.

#### 2.2.3 Shift Acceptance and Conflict Resolution
 AC 2.5: Acceptance Workflow
 The provider MUST be able to accept a shift with a single tap.
 Upon acceptance, the app MUST generate a cryptographic signature for the acceptance event to ensure non-repudiation.
 The app MUST immediately update the local availability calendar to block the accepted time slot.

AC 2.6: Offline Shift Conflict & Scheduling Override Management ([JNY-FE94EB17D1](../project_glossary.md#jny-fe94eb17d1))
 If the provider attempts to accept a shift that conflicts with an existing local commitment, the app MUST display a "Conflict Detected" warning. The provider MUST be able to override the conflict, but this action MUST be logged with a device signature and timestamp for audit purposes ([CON-9B0CF18683](../project_glossary.md#con-9b0cf18683)).

---

### 3.1 User Story: Peer Agency Coordinator

As a Peer Agency Coordinator (ACT-233A718221) managing a partner agency's workforce,
I want to discover and accept unfulfilled shifts broadcast by other agencies on the VeloGig platform,
So that I can fill critical staffing gaps for my agency's providers without manual outreach, leveraging the platform's zero-cost footprint to maximize utilization and revenue.

### 3.3 Acceptance Criteria: Cross-Agency Acceptance

1. Acceptance Workflow: The Peer Agency Coordinator MUST be able to select an available inter-agency shift and assign it to a specific provider from their agency's roster. Upon selection, the application MUST display a summary of the shift, the provider's eligibility, and any applicable inter-agency fee structures.
2. Cryptographic Confirmation: When the Peer Agency Coordinator confirms an assignment, the application MUST generate a cryptographic signature of the assignment transaction. This signature MUST be stored locally and synced to the Serverless Cloud Relay (SUR-50E19DC151) when connectivity is restored, ensuring the integrity of the assignment even during network partitions ([CON-B861BB9CEA](../project_glossary.md#con-b861bb9cea)).
3. Conflict Resolution: If a provider is already assigned to a shift (either internally or via another agency) that overlaps with the newly accepted inter-agency shift, the system MUST trigger the Offline Shift Conflict & Scheduling Override Management (JNY-FE94EB17D1) logic. The Peer Agency Coordinator MUST be presented with a conflict resolution prompt, allowing them to override the existing assignment only if they possess the necessary governance permissions.
4. Notification and Feedback: Upon successful acceptance, the Peer Agency Coordinator MUST receive an immediate on-screen confirmation. The originating agency's Coordinator MUST receive a notification (via the Serverless Cloud Relay) that their unfulfilled shift has been filled by a partner agency, including the provider's identity and the timestamp of the assignment.

### 3.4 Edge Cases and Error Flows

Network Partition During Acceptance: If the Peer Agency Coordinator attempts to accept a shift while offline, the application MUST queue the acceptance request locally. The UI MUST display a 'Pending Sync' status. Once connectivity is restored, the application MUST automatically sync the request and update the UI to 'Confirmed' or 'Failed' based on the server's response. Credential Expiration During Sync: If a provider's credentials expire while they are assigned to an inter-agency shift, the system MUST flag the assignment as 'Compliance Risk' upon the next sync. The Peer Agency Coordinator MUST be notified to review and potentially reassign the shift to a qualified provider. Duplicate Assignment Prevention: The system MUST ensure that a provider cannot be assigned to the same shift by multiple agencies. If a duplicate assignment is detected during sync, the system MUST reject the later assignment and notify both Peer Agency Coordinators of the conflict.

### 3.5 Follow-Up Questions

1. Question: What is the specific fee structure for inter-agency shift fills?
 Why Critical: The acceptance workflow and financial settlement ([SUR-778E10F5D5](../project_glossary.md#sur-778e10f5d5)) depend on knowing how fees are calculated and distributed between the originating and accepting agencies.
 Answerable: false
 Blocking: true
2. Question: How are conflicts resolved if a provider is assigned to overlapping shifts by different agencies?
 Why Critical: The Offline Shift Conflict & Scheduling Override Management (JNY-FE94EB17D1) artifact defines the general conflict resolution logic, but specific rules for inter-agency priority (e.g., does the originating agency always win?) are not defined.
 Answerable: false
 Blocking: true

---

## 4. Offline Field Execution and Clock-In (JNY-F6CC7FB09F)

## 5. Viral Engagement: Shift-Swap Flywheel Execution (JNY-E787A4D47B)

### 5.1 User Story: Provider-Initiated Shift Swap
As a Workforce Provider (ACT-146D8465B0),
I want to initiate a shift-swap request for an accepted shift, allowing me to find a replacement provider locally or through the network,
So that I can manage my schedule flexibly without losing the shift revenue or violating compliance rules.

#### 5.2.1 Swap Initiation and Local Matching
- AC-5.1: Swap Request Submission
 The provider MUST be able to initiate a shift-swap request via the mobile interface. The request MUST include the shift ID, the reason for the swap, and the desired replacement timeframe.
 The system MUST immediately lock the shift status to "Pending Swap" to prevent other providers from accepting it.

- AC-5.2: Viral Engagement and Candidate Discovery
 The Local-First Edge Engine (SUR-D1A2EE5B7A) MUST scan the provider's local network and cached provider directory for potential replacements who meet the shift's certification and proximity requirements.
 If local candidates are found, the system MUST present them to the initiating provider for selection.
 KNOWLEDGE_GAP: The specific algorithm for ranking local swap candidates (e.g., proximity vs. credential match vs. historical reliability) is not yet defined. The Product Owner must establish the ranking logic.

#### 5.2.2 Network Broadcast and Acceptance
- AC-5.3: Inter-Agency Broadcast (if local fails)
 If no local candidates are found, the system MUST broadcast the swap request to the Peer Agency Coordinator (ACT-233A718221) network, subject to the same inter-agency discovery rules defined in Section 3.

- AC-5.4: Replacement Acceptance and Verification
 When a replacement provider accepts the swap, the system MUST verify their credentials against the Policy & Rules Engine (SUR-782954DB8D) to ensure compliance.
 The system MUST generate a cryptographic signature for the swap transaction, updating the local availability calendars of both the initiating and replacing providers.

#### 5.2.3 Viral Loop Integration
- AC-5.5: Unregistered Vendor Conversion
 If the replacement provider is not yet registered on the platform, the system MUST trigger the "Unregistered Vendor" onboarding flow ([ACT-C80EBF170E](../project_glossary.md#act-c80ebf170e)), incentivizing them to complete registration to accept the shift.
 This conversion point MUST be tracked as a key metric for the Viral Growth Loop Orchestration ([CAP-VIRAL-GROWTH-LOOP-ORCHESTRATION](../project_glossary.md#cap-viral-growth-loop-orchestration)).

### 5.3 Data Residency and Sovereignty (CON-50D510498D)

The platform must enforce strict data residency boundaries to comply with cross-jurisdictional data protection laws (GDPR, CCPA) and vertical-specific mandates (CJIS, HIPAA). Data sovereignty is managed at the Tenant level via the Multi-Tenant Namespace Management capability ([CAP-MULTI-TENANT-NAMESPACE-MANAGEMENT](../project_glossary.md#cap-multi-tenant-namespace-management)).

Tenant-Level Isolation: Each Tenant (Agency/Organization) must be assigned a specific data residency region (e.g., US-East, EU-West) during the Tenant Vertical Configuration Provisioning journey ([JNY-04F8809204](../project_glossary.md#jny-04f8809204)). All data associated with that Tenant's shifts, providers, and clients must remain within the physical or logical boundaries of that region. Local-First Storage Mandate: Per the zero-cost footprint philosophy, all Provider PII, credential data, and shift history must be stored locally on the user's device (local-first storage). The serverless cloud relay (SUR-50E19DC151) acts only as an asynchronous sync layer. No raw PII or credential data may be persisted in the central cloud relay unless explicitly required for cross-tenant inter-agency discovery, and even then, it must be encrypted and anonymized where possible. Cross-Border Sync Restrictions: Inter-agency cooperative gig discovery (JNY-2105A9EBCD) must not trigger data transfers across jurisdictional boundaries unless the receiving Tenant's residency policy explicitly permits it. If a match is found across boundaries, the platform must notify both Tenants and require explicit consent before transferring any identifying information.

### 5.4 Encryption Standards (CON-F26B1E3984)

All data flows within the Shift Request, Matching, and Inter-Agency Discovery artifact must adhere to the following encryption standards:

In-Transit Encryption: All communication between the local-first edge engine (SUR-D1A2EE5B7A) and the serverless cloud relay (SUR-50E19DC151) must use TLS 1.3. Internal communication between microservices within the serverless relay must also use TLS 1.3. At-Rest Encryption: All data stored on the local-first edge engine must be encrypted using AES-256. Private keys for this encryption must be stored within the device's secure enclave or hardware-backed keystore ([CON-F8A3E7F999](../project_glossary.md#con-f8a3e7f999)). Data stored in the serverless relay must also be encrypted at rest using AES-256. Offline Device-to-Device Encryption: For inter-agency discovery and shift-swap flywheel operations ([JNY-E787A4D47B](../project_glossary.md#jny-e787a4d47b)) that occur in offline or low-connectivity modes, device-to-device connections must use high-entropy curve cryptography ([CON-5DC20C5FDE](../project_glossary.md#con-5dc20c5fde)). This ensures that even if devices are in close physical proximity, unauthorized eavesdropping is computationally infeasible.

### 5.5 Immutable Audit Trails (CON-9B0CF18683)

To maintain accountability and support compliance audits (SOC 2 Type II, CJIS, HIPAA), the platform must maintain immutable audit trails for all matching and discovery events.

Audit Log Scope: Every shift request, match event, provider acceptance, and inter-agency discovery interaction must be logged. Logs must include the timestamp, the actor ID (ACT-3ED1615F18, ACT-146D8465B0, or ACT-233A718221), the action taken, and the outcome. Immutability: Audit logs must be append-only and tamper-evident. In the local-first model, logs are stored locally and signed cryptographically. When synced to the serverless relay, they are appended to a central, immutable ledger (SUR-778E10F5D5). Manual Override Logging: Any manual bypass of the automated matching algorithm or inter-agency discovery rules must be explicitly logged with the device signature and timestamp of the operator ([CON-D543ADCA05](../project_glossary.md#con-d543adca05)). This is critical for Law Enforcement and Healthcare verticals where chain-of-command and accountability are paramount.

### 5.6 Knowledge Gaps and Assumptions

KNOWLEDGE_GAP: The exact mechanism for enforcing data residency at the local-first edge engine level (e.g., geo-fencing, IP-based routing, or Tenant-specific encryption keys) is not yet defined. The Design phase must determine the most efficient and secure method for enforcing [CON-50D510498D](../project_glossary.md#con-50d510498d) without impacting the zero-cost footprint philosophy. ASSUMPTION: The serverless cloud relay (SUR-50E19DC151) is assumed to be deployed in multiple regions to support data residency requirements. This assumption is based on the need to comply with GDPR and CCPA, which require data to remain within specific jurisdictions. Evidence needed: Confirmation of multi-region deployment strategy from the Infrastructure/DevOps team. KNOWLEDGE_GAP: The specific cryptographic algorithms and key lengths for offline device-to-device connections (CON-5DC20C5FDE) are not yet defined. The Design phase must select appropriate high-entropy curve cryptography standards (e.g., Curve25519, NIST P-256) that balance security with the computational constraints of mobile devices.
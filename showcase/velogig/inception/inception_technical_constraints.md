# Technical Constraints and Architecture Foundations

### 1.1. Core Philosophy: $0 Baseline Compute

The VeloGig platform is engineered around a structural cost elimination strategy where compute-heavy processes—real-time matching, data storage, and compliance auditing—are offloaded from centralized infrastructure to user devices. This 'Zero-Cost Footprint' ensures that the platform incurs near-zero infrastructure costs for idle state or unverified entities, scaling only when active transactions occur.

---

### 1.2. Local-First Edge Engine Constraints

To achieve the $0 baseline, the Local-First Edge Engine ([SUR-D1A2EE5B7A](../project_glossary.md#sur-d1a2ee5b7a)) must operate autonomously, handling the core workforce management logic offline.

*   **Runtime Environment:** The engine must containerize local AI runtimes (Ollama, vLLM, or SGLang) to support asynchronous execution. It must utilize 32k context windows and 4-bit or 8-bit quantized Small Language Models (SLMs) to ensure low-latency, local inference. The specific model architecture (e.g., Llama-3-8B-Instruct, Phi-3-Medium) is a design decision to be validated against target device hardware benchmarks.
*   **Offline Resilience:** The system must sustain 100% core scheduling and compliance capability during network isolations exceeding 72 hours (CON-<timestamp>). This requires robust local data persistence and conflict resolution mechanisms.
*   **Data Sovereignty:** User PII and credential data must be classified as strictly protected, local-first storage ([CON-2D0886886F](../project_glossary.md#con-2d0886886f)). No provider or shift data may leave the client network unless explicitly synced via the serverless relay ([CON-D4AD539040](../project_glossary.md#con-d4ad539040)).

---

### 1.3. Architectural Surface: Serverless Cloud Relay

The Serverless Cloud Relay ([SUR-50E19DC151](../project_glossary.md#sur-50e19dc151)) serves as the high-concurrency coordination layer, handling global state synchronization, financial settlement, and viral loop orchestration. It does not perform local edge processing or primary data storage for offline entities.

*   **Role:** Acts as the single source of truth for financial transactions and global regulatory compliance, reconciling data from distributed Edge Engines.
*   **Scalability:** Must support high-concurrency serverless architectures to handle viral loop spikes in user onboarding ([CON-FD460FF04B](../project_glossary.md#con-fd460ff04b)).
*   **Health Monitoring:** Must monitor async sync queue depths to prevent data loss during high-load periods ([CON-42707BCC80](../project_glossary.md#con-42707bcc80)).

---

### 1.4. Architectural Surface: Data Residency and Multi-Tenant Isolation

The Data Residency and Multi-Tenant Isolation Surface ([SUR-2FFD65DB4F](../project_glossary.md#sur-2ffd65db4f)) enforces strict tenant boundaries and jurisdictional compliance.

*   **Isolation Surface:** Must enforce strict tenant boundaries to prevent cross-tenant RAG contamination and ensure compliance boundaries are maintained.
*   **Regulatory Compliance:** The platform must ensure compliance with cross-jurisdictional data protection laws (GDPR, CCPA) while supporting multi-tenant operations ([CON-50D510498D](../project_glossary.md#con-50d510498d)). Data residency boundaries must be explicitly defined to prevent cross-border data leakage.

---

### 1.5. Decision Rationale

This architecture was chosen to eliminate the high baseline costs associated with traditional workforce dispatch platforms. By shifting compute to the edge, VeloGig can offer a $0 baseline to Tenants (Agencies/Orgs), making it highly competitive against rivals like RollKall. The strict separation of local-first processing and serverless relay ensures scalability and security, which are critical for the regulated verticals of Law Enforcement and Healthcare.

---

### 2.1. Offline Capability and Network Partition Tolerance

The Edge Engine must guarantee continuous core functionality during extended network outages, a critical requirement for field operations in Law Enforcement and Industrial environments.

*   **Constraint 2.1.1: 72-Hour Core Continuity**
    The Edge Engine must sustain 100% core scheduling and compliance capability during network isolations exceeding 72 hours (CON-<timestamp>). This includes the ability to:
    *   Process and store shift requests and acceptances.
    *   Execute local cryptographic signing for field proofs.
    *   Maintain the local vector database for regulatory compliance queries.
    *   Resolve local shift conflicts using the Offline Shift Conflict Resolution Algorithm ([CAP-OFFLINE-SHIFT-CONFLICT-RESOLUTION-ALGORITHM](../project_glossary.md#cap-offline-shift-conflict-resolution-algorithm)).

*   **Constraint 2.1.2: Asynchronous Execution and Context Window**
    The engine must utilize containerized edge AI runtimes (Ollama, vLLM, or SGLang) with asynchronous execution capabilities. It must support a minimum 32k context window to process local regulatory documents and shift histories without requiring cloud connectivity. Quantized Small Language Models (SLMs) are mandated to ensure performance on resource-constrained mobile devices.

*   **Constraint 2.1.3: Local LLM Inference Latency**
    To support real-time query responses for dispatch coordinators and providers, the local LLM inference latency must be maintained under 2 seconds for supported devices ([CON-6DA28A5507](../project_glossary.md#con-6da28a5507)). This constraint drives the selection of quantization levels and hardware acceleration requirements for the Edge Engine.

### 2.2. Local Data Storage and PII Protection

Data sovereignty and privacy are paramount. The Edge Engine is the primary custodian of sensitive user data, enforcing a strict local-first storage policy.

*   **Constraint 2.2.1: Strict Local-First PII Storage**
    User PII and credential data must be classified as strictly protected and stored locally on the device by default (CON-2D0886886F). No provider or shift data may leave the client network unless explicitly synced via the Serverless Cloud Relay (SUR-50E19DC151) (CON-D4AD539040).

*   **Constraint 2.2.2: Encryption at Rest**
    All local data stored by the Edge Engine must be encrypted using AES-256 encryption at rest ([CON-F26B1E3984](../project_glossary.md#con-f26b1e3984)). This includes local databases, vector stores, and cached regulatory documents.

*   **Constraint 2.2.3: Secure Key Management**
    Local cryptographic private keys, used for offline signing and SSI credentials, must be securely handled within device secure enclaves or hardware-backed keystores ([CON-F8A3E7F999](../project_glossary.md#con-f8a3e7f999), [CON-BDA3D95A26](../project_glossary.md#con-bda3d95a26)). The Edge Engine must never have direct, unencrypted access to these private keys in memory for extended periods.

### 2.3. Edge Device Integrity Verification

To prevent fraud and ensure the integrity of the workforce dispatch system, the Edge Engine must continuously verify the integrity of the device it runs on.

*   **Constraint 2.3.1: Root Detection and Device Health**
    The Edge Engine must integrate with the Edge Device Integrity and Root Detection Engine ([CAP-EDGE-DEVICE-INTEGRITY-AND-ROOT-DETECTION-ENGINE](../project_glossary.md#cap-edge-device-integrity-and-root-detection-engine)) to detect rooted, jailbroken, or tampered devices. This verification must occur before allowing access to sensitive operational data or cryptographic signing capabilities.

*   **Constraint 2.3.2: Fraud Detection in Offline Mode**
    The Edge Engine must implement robust local heuristics to detect spoofed location or biometric bypass attempts before syncing data to the cloud ([CON-08EB4DC34B](../project_glossary.md#con-08eb4dc34b)). These heuristics must operate independently of cloud connectivity.

*   **Constraint 2.3.3: Cryptographic Signature Validation**
    All online/offline transitions and critical field actions (e.g., clock-in, shift acceptance) must be accompanied by cryptographic signature validation results, which are captured and stored locally for later sync ([CON-97086EC29C](../project_glossary.md#con-97086ec29c)).

### 2.4. Hardware and Runtime Specifications

*   **KNOWLEDGE_GAP: Specific hardware requirements (e.g., minimum RAM, CPU cores) for the Edge Engine to reliably run quantized SLMs with a 32k context window on target mobile devices are not yet defined. This requires benchmarking against target device fleets.**
*   **KNOWLEDGE_GAP: The exact mechanism for 'hot-swapping' vertical configuration packages at the edge (e.g., over-the-air updates vs. pre-bundled packages) is not yet determined. This impacts the size and update frequency of the Edge Engine container.**
*   **ASSUMPTION: The Edge Engine will use a local SQLite or similar lightweight embedded database for primary data storage, given the constraints of mobile devices and the need for ACID compliance during offline operations. This assumption should be validated against performance requirements for large-scale shift histories.**

### 2.5. Sibling Dependencies and Cross-References

*   **Serverless Cloud Relay (SUR-50E19DC151):** The Edge Engine's sync protocol and data format must be compatible with the Serverless Cloud Relay. The Relay is responsible for handling high-concurrency spikes during viral loop onboarding (CON-FD460FF04B) and maintaining the global financial settlement ledger ([SUR-778E10F5D5](../project_glossary.md#sur-778e10f5d5)).
*   **Policy & Rules Engine ([SUR-782954DB8D](../project_glossary.md#sur-782954db8d)):** The Edge Engine must be able to download and apply policy rules from the central Policy & Rules Engine, ensuring that local compliance checks are always up-to-date when connectivity is available.
*   **Data Residency and Multi-Tenant Isolation Surface (SUR-2FFD65DB4F):** The Edge Engine must respect data residency boundaries, ensuring that tenant data is not mixed across jurisdictions, even when stored locally. This is critical for compliance with GDPR and CCPA (CON-50D510498D).

---

### 3.0 Serverless Cloud Relay Deep Dive

### 3.1. Synchronization and Data Integrity Boundaries

The Relay must enforce strict eventual consistency for all shift, provider, and client data. It acts as the single source of truth for financial transactions and regulatory compliance, but must never overwrite local-first data without cryptographic proof of validity.

*   **Conflict Resolution Protocol:** The Relay must implement a Conflict-free Replicated Data Type (CRDT) or operational transformation model to resolve conflicts arising from network partitions >72 hours (CON-<timestamp>). All local state changes must be cryptographically signed by the Local-First Edge Engine before being accepted by the Relay.
*   **Data Residency and Sovereignty:** The Relay must route data to distinct bank nodes or regional storage buckets to comply with cross-jurisdictional data protection laws (GDPR, CCPA) and vertical-specific regulations (CJIS, HIPAA) (CON-50D510498D, [CON-F6B76559A7](../project_glossary.md#con-f6b76559a7), CON-<timestamp>). No provider or shift data may leave the client network unless explicitly synced via the serverless relay (CON-D4AD539040).
*   **Encryption Standards:** All data in transit between the Edge Engine and the Relay must be encrypted using TLS 1.3, and data at rest must use AES-256 encryption (CON-F26B1E3984). Private keys for offline signing must remain within device secure enclaves and never be transmitted to the Relay (CON-F8A3E7F999).

### 3.2. High-Concurrency and Viral Loop Orchestration

The Relay must support high-concurrency serverless architectures to handle viral loop spikes in user onboarding and shift-swap flywheel execution (CON-FD460FF04B, [JNY-E787A4D47B](../project_glossary.md#jny-e787a4d47b)).

*   **Scalability Targets:** The Relay must auto-scale to handle sudden influxes of onboarding requests and shift-swap notifications without degradation. The target is to maintain sub-second response times for initial request acknowledgment during peak viral load.
*   **Viral Growth Loop Integration:** The Relay must support the 'Viral Engagement: Shared Invoicing Injection Point Conversion' ([JNY-38902F6D90](../project_glossary.md#jny-38902f6d90)) and 'Viral Engagement: Shift-Swap Flywheel Execution' (JNY-E787A4D47B) by providing low-latency APIs for real-time status updates and notification dispatch to unregistered or newly registered users.

### 3.3. Health Monitoring and Reliability

The Relay must provide robust health monitoring and async sync queue depth tracking to ensure platform reliability (CON-42707BCC80).

*   **Uptime Target:** The platform must target 99.99% uptime for the serverless cloud coordination layer ([CON-6B4B073836](../project_glossary.md#con-6b4b073836)).
*   **Queue Depth Monitoring:** The Relay must monitor async sync queue depths to prevent data loss during high-load periods. If queue depths exceed a defined threshold, the Relay must trigger backpressure mechanisms to protect the underlying data stores.
*   **Offline Transition Logging:** The Relay must capture cryptographic signature validation results for all online/offline transitions (CON-97086EC29C) to ensure auditability and detect potential spoofing or bypass attempts.

### 4.1. Key Management and Secure Enclave Integration

All cryptographic private keys used for offline signing and SSI (Self-Sovereign Identity) credential validation must be generated, stored, and used exclusively within the device's hardware-backed secure enclave or hardware keystore (CON-F8A3E7F999).

*   **Key Generation:** Keys must be generated using a cryptographically secure random number generator (CSPRNG) native to the device OS (e.g., Android Keystore, iOS Secure Enclave).
*   **Key Isolation:** Private keys must never leave the secure enclave in plaintext. All signing operations must be performed internally by the enclave, returning only the signature.
*   **Key Rotation:** Key rotation policies must be defined as a `KNOWLEDGE_GAP:` to align with specific vertical compliance requirements (e.g., CJIS frequency mandates vs. HIPAA best practices). Until ratified, the system must support on-demand key rotation triggered by the Platform Operator ([ACT-0E3EE366E3](../project_glossary.md#act-0e3ee366e3)) via the Policy & Rules Engine (SUR-782954DB8D).
*   **SSI Credential Binding:** Private keys must be bound to the user's identity (Workforce Provider ([ACT-146D8465B0](../project_glossary.md#act-146d8465b0)) or Commercial Client ([ACT-3ED1615F18](../project_glossary.md#act-3ed1615f18))) using decentralized identifiers (DIDs) and verifiable credentials (VCs), ensuring that offline proofs are tied to a verified identity even without network connectivity.

### 4.2. Encryption Algorithms for Data at Rest and in Transit

To ensure data sovereignty and protect PII (CON-2D0886886F) and credential data (CON-F6B76559A7, CON-97086EC29C), the following encryption standards are mandatory:

*   **Data at Rest:** All local data stored on the device, including shift records, location history, and credential caches, must be encrypted using AES-256 in GCM mode. This ensures both confidentiality and integrity of the local database.
*   **Data in Transit (Sync):** All data synchronized from the Local-First Edge Engine to the Serverless Cloud Relay must be transmitted over TLS 1.3 (CON-F26B1E3984).
*   **Offline Device-to-Device Connections:** In scenarios where devices communicate directly (e.g., Peer-to-Peer shift swaps), connections must be secured using high-entropy curve cryptography ([CON-5DC20C5FDE](../project_glossary.md#con-5dc20c5fde)), specifically Elliptic Curve Diffie-Hellman (ECDH) using the P-256 curve, to establish a shared secret for symmetric encryption.

### 4.3. Signature Validation and Proof Integrity

Every offline field proof (e.g., clock-in, shift completion, location check) must be cryptographically signed to prevent spoofing and ensure non-repudiation.

*   **Signing Algorithm:** All proofs must be signed using ECDSA (Elliptic Curve Digital Signature Algorithm) with the P-256 curve. This provides a strong balance between security and performance on mobile devices.
*   **Proof Structure:** Each proof payload must include:
    *   `payload_hash`: SHA-256 hash of the core data (timestamp, location, user ID, action type).
    *   `signature`: ECDSA signature of the payload_hash generated by the user's private key in the secure enclave.
    *   `public_key_identifier`: A reference to the public key or DID used for verification, allowing the Serverless Cloud Relay to validate the signature upon sync.
*   **Validation Logic:** The Offline Shift Conflict Resolution Algorithm (CAP-OFFLINE-SHIFT-CONFLICT-RESOLUTION-ALGORITHM) must verify the cryptographic signature of each proof before accepting it as a valid state change. Invalid signatures must be quarantined and flagged for manual review by the Agency Administrator ([ACT-B91695A020](../project_glossary.md#act-b91695a020)) or Platform Operator.

### 4.4. Cross-Reference to Sibling Artifacts

*   **Local-First Edge Engine (SUR-D1A2EE5B7A):** This section defines the cryptographic constraints that the Edge Engine must implement. The Edge Engine is responsible for enforcing these standards during offline operations.
*   **Serverless Cloud Relay (SUR-50E19DC151):** The Relay is responsible for validating the cryptographic signatures of proofs upon sync and ensuring that the data integrity is maintained during transmission.
*   **Policy & Rules Engine (SUR-782954DB8D):** The Rules Engine will manage the key rotation policies and compliance configurations that dictate how these cryptographic standards are applied across different verticals.

This section provides the binding technical constraints for cryptographic security, ensuring that VeloGig's offline-first architecture is both secure and compliant. The unresolved gaps must be addressed in subsequent phases to finalize the implementation details.

---

### 5.1. Data Residency and Sovereignty Boundaries

The platform must enforce strict data residency rules to comply with cross-jurisdictional data protection laws. Data sovereignty is a primary architectural constraint, not an optional feature.

*   **Jurisdictional Anchoring:** All Tenant data (including Provider credentials, shift logs, and financial records) must be logically and physically isolated within the jurisdiction of the Tenant's primary legal entity. The Serverless Cloud Relay (SUR-50E19DC151) must route and store data in region-specific cloud nodes. No cross-border data transfer is permitted without explicit, audited Tenant consent and legal review.
*   **Vertical-Specific Compliance:**
    *   **Law Enforcement (CJIS):** All data related to off-duty peace officers and deputies must reside exclusively within CJIS-compliant cloud regions. Data must never leave the client network unless explicitly synced via the serverless relay (CON-D4AD539040). Local storage on the Edge Engine must be encrypted with keys that never leave the device secure enclave (CON-F8A3E7F999).
    *   **Healthcare (HIPAA):** Protected Health Information (PHI) and credential data for nurses and travel nurses must be processed and stored in HIPAA-compliant environments. The Local-First Edge Engine (SUR-D1A2EE5B7A) must classify user PII and credential data as strictly protected, local-first storage (CON-2D0886886F). PHI must not be cached in the serverless relay beyond the minimum required for real-time matching.
    *   **Industrial/General (GDPR/CCPA):** For general gig workers and clients, data residency must respect the user's location. Right-to-be-forgotten and data export mechanisms ([JNY-B2BD1D1897](../project_glossary.md#jny-b2bd1d1897)) must be implemented at the tenant level, ensuring data can be purged from all edge and cloud nodes upon request.
*   **Data Residency Constraint:** The platform must implement a DataResidencyPolicy configuration package that is hot-swappable per Tenant. This policy defines the allowed geographic regions for data storage and processing. Violations of this policy must trigger an immediate sync halt and an alert to the Platform Operator (ACT-0E3EE366E3).

### 5.2. Multi-Tenant Isolation Surface

The platform must guarantee strict logical and physical isolation between Tenants to prevent data leakage and ensure compliance.

*   **Logical Isolation:** All data queries to the Serverless Cloud Relay must be scoped by TenantID. The Policy & Rules Engine (SUR-782954DB8D) must enforce access control policies that prevent any Tenant from accessing another Tenant's data, even if they share the same underlying cloud infrastructure.
*   **Physical Isolation (High-Security Verticals):** For Tenants operating in the Law Enforcement and Healthcare verticals, the platform must support physical isolation of data stores. This means dedicated database instances or cloud regions for these high-compliance Tenants, ensuring no shared storage layers with general commercial clients.
*   **Isolation Constraint:** The Local-First Edge Engine must maintain a strict TenantContext for all local operations. No local data from one Tenant can be mixed with data from another Tenant on the same device. If a device is used by multiple Tenants (e.g., a provider working for multiple agencies), the Edge Engine must enforce strict session-based isolation, ensuring data is never persisted across Tenant boundaries.
*   **Cross-Tenant Data Flow:** The only permitted cross-tenant data flow is the anonymized, aggregated metrics required for the Viral Growth Loop Orchestration ([CAP-VIRAL-GROWTH-LOOP-ORCHESTRATION](../project_glossary.md#cap-viral-growth-loop-orchestration)). These metrics must be stripped of all PII and Tenant-specific identifiers before being processed by the serverless relay.

### 5.3. Cryptographic Key Management and Data Protection

To support data residency and isolation, the platform must enforce robust cryptographic standards.

*   **Encryption at Rest:** All data stored on the Local-First Edge Engine must be encrypted using AES-256. Keys must be managed within the device's secure enclave or hardware-backed keystore (CON-F8A3E7F999). The serverless relay must also use AES-256 for data at rest.
*   **Encryption in Transit:** All data flows between the Edge Engine and the Serverless Cloud Relay must use TLS 1.3 (CON-F26B1E3984). For offline device-to-device connections (e.g., shift swaps), high-entropy curve cryptography must be enforced (CON-5DC20C5FDE).
*   **Key Rotation:** The platform must support automated key rotation policies defined in the DataResidencyPolicy. For CJIS and HIPAA verticals, key rotation must occur at least annually, or upon any suspected compromise.

### 5.5. Validation and Compliance

*   **Audit Trails:** All configuration changes to the DataResidencyPolicy and TenantContext must be logged in an immutable audit trail ([CON-9B0CF18683](../project_glossary.md#con-9b0cf18683)). These logs must be stored in a separate, read-only region to prevent tampering.
*   **Compliance Verification:** The platform must include automated compliance checks that verify data residency and isolation constraints are met during the sync process. Any violation must be flagged and reported to the Platform Operator.
*   **Testing:** Compliance with CJIS, HIPAA, and GDPR/CCPA must be verified through third-party audits. The platform must provide the necessary logs and data access controls to facilitate these audits.

This section establishes the binding constraints for data residency and multi-tenant isolation. These constraints are non-negotiable and must be enforced by the Local-First Edge Engine and Serverless Cloud Relay. Any deviation from these constraints requires explicit approval from the Platform Operator and legal counsel.

### 2.4. Unresolved Decisions and Knowledge Gaps

*   **KNOWLEDGE_GAP:** Specific hardware requirements (e.g., minimum RAM, CPU cores) for the Edge Engine to reliably run quantized SLMs with a 32k context window on target mobile devices are not yet defined. This requires benchmarking against target device fleets.
*   **KNOWLEDGE_GAP:** The exact mechanism for 'hot-swapping' vertical configuration packages at the edge (e.g., over-the-air updates vs. pre-bundled packages) is not yet determined. This impacts the size and update frequency of the Edge Engine container.
*   **ASSUMPTION:** The Edge Engine will use a local SQLite or similar lightweight embedded database for primary data storage, given the constraints of mobile devices and the need for ACID compliance during offline operations. This assumption should be validated against performance requirements for large-scale shift histories.
*   **ASSUMPTION:** The 'Zero-Cost Footprint' philosophy implies that the Edge Engine will not incur any cloud compute costs for idle state. This assumes that the Serverless Cloud Relay (SUR-50E19DC151) will only be invoked for sync and matching, not for continuous state management.
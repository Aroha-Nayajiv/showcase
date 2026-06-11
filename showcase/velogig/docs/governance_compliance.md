# Governance, Compliance, and Privacy Obligations

## 1. Regulatory Mapping to Modular Entities

This section maps the primary regulatory domains (Law Enforcement, Healthcare, Industrial) to VeloGig's core modular entities. This mapping dictates the data handling, validation, and audit requirements for each user journey.

| Entity | Regulatory Domain | Compliance Focus | Data & Validation Obligations |
| :--- | :--- | :--- | :--- |
| Seekers (Providers) | Law Enforcement (CJIS) | Off-duty peace officer credential validation; municipal labor laws; union contract constraints. | State-issued ID and professional credentials must be cryptographically validated against public registries during onboarding. |
| Seekers (Providers) | Healthcare (HIPAA) | Nurse data privacy; state-specific nursing board regulations; credential verification against public registries. | Professional credentials wrapped in an encrypted device-local wallet. Biometric facial check data must be handled per state biometric privacy laws. |
| Seekers (Providers) | Industrial (OSHA) | OSHA safety standards; CDL licensing requirements; hazmat transport regulations. | CDL and hazmat certifications must be validated against public registries. Safety compliance logs must be immutable. |
| Tenants (Agencies) | All Domains | Manage workforce and pay base software costs; ensure compliance of assigned Seekers. | Access to Seeker credential status and compliance logs. Must adhere to data minimization principles. |
| Clients (Vendors/Venues) | All Domains | Request specialized labor within geofenced areas; receive interactive digital invoice link. | Limited access to Seeker identity (masked until assignment). Invoice processing must comply with financial regulations. |
| Regulations (Rules Engine) | All Domains | Manage compliance, fee structures, and policy blocks per vertical. | Hot-swappable compliance profiles. Must enforce local labor laws and safety standards dynamically. |

## 2. Regulations Rules Engine Scope

The 'Regulations' Rules Engine is the primary mechanism for managing compliance across different verticals. It is designed to be hot-swappable, allowing VeloGig to adapt to new regulations without codebase fragmentation.

*   **Hot-Swappable Profiles:** Compliance profiles (e.g., HIPAA, CJIS, OSHA) are loaded dynamically. This allows VeloGig to support multiple verticals simultaneously.
*   **Policy Enforcement:** The engine enforces policy blocks per vertical. For example, a Seeker without a valid CDL license cannot be assigned to an industrial job requiring hazmat transport.
*   **Fee Structure Management:** The engine manages fee structures based on regulatory requirements. For example, different labor laws may dictate different minimum pay rates or overtime calculations.

## 3. Privacy and Data Retention

VeloGig is committed to privacy by design. This section outlines the key privacy obligations and data retention policies.

*   **GDPR/CCPA Compliance:** VeloGig complies with GDPR and CCPA regulations for worker location data, biometric facial check data, and other personal information. Users have the right to access, correct, and delete their data.
*   **Data Minimization:** Only the minimum necessary data is collected and processed. For example, location data is processed locally, and only compliance status is transmitted.
*   **Immutable Audit Logs:** All compliance-related actions are logged immutably. These logs are retained for a period defined by regulatory requirements.
*   **Data Sovereignty:** Data is stored in regions compliant with local regulations. For example, EU citizen data is stored in EU-based servers.

## 4. Financial Compliance: InstantPay

The InstantPay feature advances funds to workers minus a 1.5%-2.5% liquidity convenience fee. This section outlines the financial compliance boundaries.

*   **Liquidity Fee:** The 1.5%-2.5% fee is a financial compliance boundary. It must be clearly disclosed to users and compliant with financial regulations.
*   **Transaction Integrity:** All financial transactions must be recorded immutably. Disputes must be resolved through a defined process.
*   **Anti-Money Laundering (AML):** VeloGig must implement AML checks to prevent financial crimes. This includes monitoring for suspicious transactions and reporting them to relevant authorities.

## 5. Data Sovereignty and Edge AI Boundaries

VeloGig's local-first architecture fundamentally alters the traditional data sovereignty model. Because compute-heavy processes are offloaded to user devices via a local-first, containerized edge AI engine, the boundary between local processing and cloud relay must be strictly defined to satisfy regulatory requirements (CJIS, HIPAA, OSHA).

### 5.1 Local Edge AI Processing (The Edge Boundary)

The local-first architecture (utilizing runtimes such as Ollama, vLLM, or SGLang) processes sensitive data directly on the user's device. This ensures that raw sensitive data does not traverse the network unnecessarily.

*   **Credential Validation:** Provider credentials (state IDs, nursing licenses, CDLs) are scanned and wrapped in an encrypted, device-local wallet. Cryptographic validation against public registries occurs locally or via a zero-knowledge proof relay, ensuring the raw credential data is not stored centrally.
*   **Biometric Data Handling:** Biometric facial check data and high-accuracy GPS deltas are processed locally. The local LLM generates a cryptographic "Proof of Presence" (timestamped and signed with the user's private key) without transmitting the raw biometric image or precise location history to the cloud.
*   **Offline Compliance Enforcement:** The local vector database stores systemic regulatory docs, collective bargaining agreements, and regional labor laws. The local model runs semantic search to ensure shift assignments comply with local labor regulations before a supervisor finalizes an offline match. This ensures 100% core capability during network isolations extending past 72 continuous hours.

### 5.2 Serverless Cloud Relay (The Cloud Boundary)

The serverless cloud relay acts as a coordination layer, not a data repository for sensitive PII or PHI. It handles asynchronous synchronization and global state management.

*   **Data Minimization at Relay:** Only compliance status, cryptographic proofs, and anonymized scheduling metadata are transmitted to the cloud relay. Raw PII, PHI, and biometric templates remain device-local.
*   **Asynchronous Synchronization:** When connectivity is restored, the device synchronizes signed audit logs and compliance proofs. The cloud relay verifies the cryptographic signatures and updates the global tenant/seeker status without re-processing the raw underlying data.
*   **Zero Baseline Compute Costs:** By offloading the heavy lifting of compliance auditing and semantic search to the edge, the cloud relay maintains a $0 baseline compute cost for these processes, aligning with the procurement bypass strategy.

## 6. Sibling Artifact References

*   This artifact's Risk Register defers to the Risk Register and Operating Constraints artifact for detailed risk assessments and mitigation strategies.
*   This artifact's Success Criteria defers to the Success Criteria and Decision Foundations artifact for specific compliance-related KPIs and metrics.
*   This artifact's Product Vision defers to the Whole Product Vision and Scope artifact for high-level compliance goals and stakeholder expectations.

## 7. Unresolved Compliance Gaps

The following items require explicit resolution before downstream design phases can proceed. These are not defects in the current baseline but necessary knowledge gaps to be filled by project authorities.

*   **KNOWLEDGE_GAP: Specific Municipal Labor Laws** - The exact municipal labor laws and collective bargaining agreement constraints for Law Enforcement agencies vary by jurisdiction. The Rules Engine must be designed to ingest these dynamically, but the specific legal text sources for initial verticals are not yet established.
*   **KNOWLEDGE_GAP: Biometric Privacy Statutes** - While HIPAA and CJIS are addressed, specific state-level biometric privacy laws (e.g., BIPA in Illinois) impose strict retention and consent requirements for facial check data. The exact retention period and consent mechanism for biometric data must be defined by legal counsel.
*   **KNOWLEDGE_GAP: Financial Compliance Jurisdiction** - The 1.5%-2.5% liquidity fee for InstantPay must comply with financial regulations in all operating jurisdictions. The specific AML/KYC thresholds and reporting requirements for gig-economy advances are not yet established.
*   **KNOWLEDGE_GAP: Data Retention Periods** - While general principles are noted, the exact legally binding retention periods for labor compliance logs, biometric proofs, and credential validation records vary by vertical and jurisdiction. These must be explicitly defined by the compliance authority.

## 8. Governance, Compliance, and Privacy Obligations

This artifact establishes the authoritative compliance baseline for VeloGig, mapping the four modular entities (Tenants, Seekers, Clients, Regulations) to their respective regulatory domains. It covers: 1) Law Enforcement: Off-duty peace officer credential validation, municipal labor laws, and union contract constraints. 2) Healthcare: HIPAA compliance for nurse data, state-specific nursing board regulations, and credential verification against public registries. 3) Industrial: OSHA safety standards, CDL licensing requirements, and hazmat transport regulations. 4) Privacy & Data: GDPR/CCPA compliance for worker location data (GPS delta, Wi-Fi BSSID), biometric facial check data handling, and immutable audit log retention policies. It explicitly defines the 'InstantPay' liquidity fee structure (1.5%-2.5%) as a financial compliance boundary. BOUNDS: This artifact does not define the technical implementation details of the edge AI engine or the cloud relay, deferring to the System Blueprint and Design artifacts for those specifics.
# Technology Strategy and Constraints

## 1. Executive Summary and Architectural Posture

VeloGig is a universal, local-first marketplace and workforce dispatch platform designed to serve specialized gig economies across Law Enforcement, Healthcare, and Industrial/Hazmat Logistics. The platform's core value proposition is a zero-cost procurement model for agencies, achieved by offloading compute-heavy processes (real-time matching, compliance auditing) to user devices via a containerized edge AI engine.

This artifact defines the binding technical architecture, compliance obligations, and operational constraints for the VeloGig platform. It ensures alignment with the local-first edge AI strategy and specialized gig economy requirements, establishing the structural basis for all subsequent design and development phases.

## 2. Core Entity Model and Data Boundaries

This section defines the four foundational entities—Tenants, Seekers, Clients, and Regulations—and their relationships, which form the structural basis for all subsequent design and development phases.

### 2.1 Tenants (Agencies/Organizations)

**Definition:** Tenants are the primary organizational customers of the VeloGig platform. They are agencies or governing bodies that lease the platform infrastructure to manage their specific workforce verticals. Tenants do not pay for the base software, aligning with the zero-cost procurement model.

**Key Attributes:**
*   **Vertical Identity:** Each Tenant is associated with a specific vertical (e.g., Law Enforcement, Healthcare, Industrial Logistics) which dictates the applicable Regulations and fee profiles.
*   **Governance Role:** Tenants are responsible for configuring their local compliance rules, fee structures, and policy rules via the hot-swappable vertical configuration packages.
*   **Data Ownership:** Tenants own the data generated within their vertical, including shift logs, compliance records, and financial transactions.

**Actor Role:** Agency Administrator (ACT-B91695A020) is the primary user role for Tenants, responsible for onboarding and configuration.

**Relationships:**
*   **To Seekers:** Tenants employ or contract Seekers. They define the eligibility criteria for Seekers based on Regulations.
*   **To Regulations:** Tenants consume and configure Regulations. They do not create Regulations but select and adapt the hot-swappable packages provided by the platform.
*   **To Clients:** Tenants may also act as Clients in certain scenarios (e.g., an agency hiring its own off-duty officers for special events), but primarily they are the service providers' employers.

### 2.2 Seekers (Providers/Workers)

**Definition:** Seekers are the specialized gig providers who perform the work. They are the core supply side of the marketplace. Seekers are individuals with specific credentials and skills (e.g., off-duty peace officers, registered nurses, CDL drivers).

**Key Attributes:**
*   **Credentialing:** Seekers must undergo SSIOnboarding, where their state-issued ID and professional credentials are cryptographically validated against public registries and wrapped in an encrypted device-local wallet.
*   **Edge AI Capability:** Seekers' devices run the local-first edge AI engine to handle scheduling, compliance checks, and RAG without central compute.
*   **Offline Capability:** Seekers must be able to sustain 100% core capability during network isolations extending past 72 continuous hours.

**Actor Role:** Gig Worker (ACT-706CCDBBAA) is the primary user role for Seekers.

**Relationships:**
*   **To Tenants:** Seekers are contracted by Tenants. They must comply with the Regulations configured by their Tenant.
*   **To Clients:** Seekers perform services for Clients. They clock in/out and log work data via the platform.
*   **To Regulations:** Seekers' eligibility and actions are constrained by Regulations. Their local AI engine uses Regulations to validate shifts and compliance in real-time.

### 2.4 Regulations (Rules Engine)

**Definition:** Regulations are the hot-swappable vertical configuration packages that define compliance, fee structures, and policy rules per industry. They are the core abstraction that allows VeloGig to serve multiple verticals with a unified codebase.

**Key Attributes:**
*   **Vertical Specificity:** Regulations are tied to specific verticals (e.g., CJIS for Law Enforcement, HIPAA for Healthcare, DOT/HOS for Industrial Logistics).
*   **Hot-Swappable:** Regulation packages can be updated dynamically without requiring a full platform redeployment, ensuring compliance with evolving labor laws.

## 3. Technical Architecture and Constraints

### 3.1 Local-First Edge AI Strategy

To achieve the zero-cost procurement model, all compute-heavy processes must be offloaded to the user's device. The platform utilizes a containerized edge AI engine (e.g., Llama-3, Phi-3) running locally on the device.

*   **Constraint:** AI inference and data processing must run locally on containerized engines ensuring no provider or shift data leaves the client network.
*   **Constraint:** Compute-heavy processes must be offloaded to user devices via local-first edge AI to achieve zero baseline compute costs.
*   **Assumption:** The local AI engine must be capable of handling real-time matching and compliance auditing without central compute. The specific model weights and quantization levels required to fit within standard mobile device memory constraints are not yet established. Knowledge Gap: What are the minimum hardware specifications (RAM, CPU, GPU) required to run the local inference engine smoothly for the target device fleet?

### 3.2 Offline-First Data Integrity

VeloGig must support full offline operation for field operations during network isolations exceeding 72 hours.

*   **Constraint:** Providers must sustain 100% core capability during network isolations extending past 72 continuous hours.
*   **Constraint:** All configuration changes and state changes must log immutable audit entries with timestamp, user context, and device signature.
*   **Constraint:** Encrypted logs sync asynchronously via cellular beacon upon reconnection.
*   **Risk:** Offline data integrity and sync conflicts (CON-81DC407A40). Conflict resolution strategies for simultaneous edits from multiple devices must be defined. Knowledge Gap: What is the specific conflict resolution algorithm (e.g., Last-Writer-Wins, CRDTs) for asynchronous sync?

### 3.3 Financial Workflow and InstantPay

Financial workflows must support instant cash-out via the InstantPay Pipeline.

*   **Constraint:** Financial workflows must support instant cash-out via InstantPay Pipeline with a 1.5%-2.5% liquidity convenience fee.
*   **Risk:** Liquidity partner risk and fraud (CON-70713D057D). The platform must implement robust fraud detection mechanisms. Knowledge Gap: What are the specific fraud detection thresholds and real-time monitoring requirements mandated by the InstantPay liquidity partner?

## 4. Compliance and Regulatory Obligations

VeloGig operates in highly regulated industries, requiring strict adherence to vertical-specific compliance frameworks.

*   **Law Enforcement:** Compliance with CJIS (Criminal Justice Information Services) security policy is mandatory for all data handling and transmission.
*   **Healthcare:** Compliance with HIPAA (Health Insurance Portability and Accountability Act) is required for all patient and provider data.
*   **Industrial/Hazmat:** Compliance with DOT/HOS (Department of Transportation/Hours of Service) regulations is required for driver and technician scheduling.
*   **State Labor Laws:** The platform must dynamically adapt to varying state labor laws, which is facilitated by the hot-swappable Regulations engine.

**Data Sovereignty:** All data must remain within the jurisdictional boundaries defined by the Tenant's vertical and the worker's location. Knowledge Gap: What are the specific data residency requirements for each vertical, and how are they enforced technically?

## 5. Success Criteria and NFRs

The following Non-Functional Requirements (NFRs) are derived directly from the SoftwareDNA success criteria and must be validated in subsequent phases.

| NFR Category | Target / Constraint | Grounded Value / Status |
| :--- | :--- | :--- |
| **Compute Cost** | Zero baseline compute costs | Grounded in SoftwareDNA: Offload to user devices via local-first edge AI. |
| **Uptime** | 99.99% uptime for serverless cloud coordination layer | Grounded in SoftwareDNA: Using Cloudflare Workers and Supabase. |
| **Offline Capability** | 100% core capability during >72h network isolation | Grounded in SoftwareDNA: Local-first edge AI and encrypted local storage. |
| **Procurement Cost** | Base software costs managing agency $0 | Grounded in SoftwareDNA: Zero-cost procurement model. |
| **Local AI Performance** | Real-time matching and compliance auditing | Assumption: Local AI engine must achieve <200ms inference latency for real-time matching. Reversible pending hardware benchmarking. |
| **Sync Latency** | Asynchronous sync upon reconnection | Assumption: Sync latency must be <5 seconds for standard shift logs. Reversible pending network condition testing. |

## 6. Decision Rights and Governance

*   **Agency Administrator (ACT-B91695A020):** Responsible for onboarding, vertical configuration, and compliance rule setting. Primary flow: AgencyOnboardingandConfiguration (JNY-245DC907B2).
*   **Gig Worker (ACT-706CCDBBAA):** Responsible for credentialing, shift logging, and offline compliance. Primary flows: OfflineShiftMatchingandCompliance (JNY-6533801CDB), InvoiceGenerationandPaymentRouting (JNY-946740786C).
*   **Governing Entity (ACT-8D5C6B1AF5):** Responsible for overarching platform governance and vertical regulation updates. Primary flows: AgencyOnboardingandConfiguration (JNY-245DC907B2), InvoiceGenerationandPaymentRouting (JNY-946740786C).

## 7. Open Decisions and Knowledge Gaps

The following items require resolution before the Design phase can proceed:

1.  **Local AI Hardware Requirements:** What are the minimum hardware specifications for the target device fleet to run the local inference engine?
2.  **Conflict Resolution Strategy:** What is the specific conflict resolution algorithm for asynchronous sync?
3.  **Fraud Detection Thresholds:** What are the specific fraud detection thresholds and real-time monitoring requirements mandated by the InstantPay liquidity partner?
4.  **Data Residency Requirements:** What are the specific data residency requirements for each vertical, and how are they enforced technically?
5.  **Local AI Latency Target:** What is the acceptable inference latency for real-time matching on target devices?
6.  **Sync Latency Target:** What is the acceptable sync latency for standard shift logs upon reconnection?
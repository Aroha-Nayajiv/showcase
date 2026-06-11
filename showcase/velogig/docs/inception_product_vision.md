# Product Vision and Scope: VeloGig Universal Marketplace

## 1. Product Vision

VeloGig is a next-generation universal marketplace and workforce dispatch platform designed to serve specialized gig economies across multiple verticals, including Law Enforcement, Healthcare/Nursing, and Industrial/Hazmat Logistics. The platform abstracts the workforce management domain into four modular entities: Tenants (Agencies/Organizations), Seekers (Providers/Workers), Clients (Vendors/Venues), and Regulations (Rules Engine).

The core value proposition is built on a "zero-cost procurement model" for managing agencies, achieved by offloading compute-heavy processes to user devices via local-first edge AI. This allows VeloGig to offer base software at $0 cost to the managing agency, while generating revenue through transaction fees and liquidity convenience fees. The platform supports hot-swappable vertical configuration packages over a unified codebase, enabling rapid deployment across different industries without requiring separate codebases or extensive redeployment.

## 2. Core Entity Model

This section defines the four foundational entities of the VeloGig universal marketplace and their high-level relationships. This model serves as the semantic backbone for all subsequent business logic, compliance rules, and user journeys.

### 2.1 Entity Definitions

#### 2.1.1. Tenants (Agencies/Organizations) [ACT-B91695A020]
**Role:** The primary commercial and operational unit of the VeloGig platform. Tenants are the organizations that subscribe to the platform to manage their specialized workforce.

**Key Attributes:**
*   **Vertical Identity:** Defines the industry context (e.g., Law Enforcement, Healthcare, Industrial/Hazmat).
*   **Compliance Profile:** A set of binding regulatory constraints (e.g., CJIS for law enforcement, HIPAA for healthcare) that govern all operations within this tenant.
*   **Fee Structure:** The pricing model applied to transactions (e.g., percentage markup, flat fee) that determines revenue distribution.
*   **Configuration Package:** A hot-swappable set of rules that dictates how the platform behaves for this specific tenant.

**Business Obligation:** Tenants are responsible for defining the "Regulations" that apply to their workforce. They are the primary customer and the source of domain-specific logic.

#### 2.1.2. Seekers (Providers/Workers) [ACT-706CCDBBAA]
**Role:** The specialized gig workers who perform the services. Seekers are the supply side of the marketplace.

**Key Attributes:**
*   **Credential Set:** Professional licenses and certifications (e.g., RN license, CDL, Peace Officer Standards and Training (POST) certification).
*   **Availability:** Real-time or scheduled availability windows.
*   **Device Profile:** Information about the edge AI device used for local processing (e.g., model, quantization level, offline capability).
*   **Reputation Score:** A metric derived from past performance, compliance adherence, and client feedback.

**Business Obligation:** Seekers must maintain valid credentials and operate within the regulatory constraints defined by their Tenant. They are the primary users of the local-first edge AI for scheduling and compliance checks.

#### 2.1.3. Clients (Vendors/Venues)
**Role:** The entities that request and pay for services. Clients are the demand side of the marketplace.

**Key Attributes:**
*   **Service Requirements:** Specific needs for a shift (e.g., "Registered Nurse for ICU," "Hazmat Certified Driver").
*   **Payment Method:** Linked financial instrument for instant settlement via the InstantPay Pipeline.
*   **Dispute History:** Record of any past disputes or issues with providers.

**Business Obligation:** Clients are responsible for providing clear service requirements and timely payment. They are the primary source of revenue through transaction fees.

#### 2.1.4. Regulations (Rules Engine)
**Role:** The dynamic, hot-swappable configuration packages that define the operational boundaries for each vertical.

**Key Attributes:**
*   **Jurisdiction:** The legal or regulatory body governing the rules (e.g., State Nursing Board, DOT).
*   **Rule Set:** Specific constraints (e.g., maximum shift hours, required break intervals, credential expiration dates).
*   **Fee Rules:** How compliance surcharges or penalties are calculated.
*   **Versioning:** A version history to track changes and ensure auditability.

**Business Obligation:** Regulations are the "brain" of the vertical configuration. They must be enforceable by the local-first edge AI and must be updated dynamically without requiring a platform redeployment.

### 2.2 High-Level Relationships

The VeloGig marketplace operates on a four-way relationship model:

1.  **Tenant-Regulation:** A Tenant owns and configures a set of Regulations. This relationship is one-to-many (one Tenant can have multiple Regulation sets for different sub-verticals or jurisdictions).
2.  **Tenant-Seeker:** A Seeker is employed by or contracted with a Tenant. The Tenant defines the Regulations that the Seeker must adhere to.
3.  **Tenant-Client:** A Client contracts with a Tenant to provide services. The Tenant is responsible for fulfilling the Client's request using its pool of Seekers.
4.  **Seeker-Client:** A Seeker performs services for a Client. This relationship is mediated by the Tenant and governed by the Regulations.

### 2.3 Scope Boundaries

**In Scope:**
*   Defining the core entities, their attributes, and their high-level relationships.
*   Defining the hot-swappable nature of Regulations.
*   Establishing the zero-cost procurement model for agencies.
*   Defining the local-first edge AI constraints for data privacy and offline capability.

**Out of Scope:**
*   Detailed database schemas, API endpoints, or specific implementation details of the local-first edge AI. These are covered in subsequent Design and Development phases.
*   Specific vendor selection for the InstantPay liquidity partner.
*   Detailed UI/UX designs for the mobile or web interfaces.

**Assumption:** The platform supports multi-tenancy at the data and configuration level. Each Tenant's data and regulations are strictly isolated.

**Knowledge Gap:** The specific mechanism for "hot-swapping" Regulations (e.g., dynamic class loading, external rule engine) is not yet defined and requires technical selection in the Design phase.

## 3. Hot-Swappable Vertical Configuration Strategy

VeloGig achieves its "zero-cost footprint" and multi-vertical scalability through a Configuration-as-Code strategy. The platform does not hardcode business logic for specific industries (Law Enforcement, Healthcare, Industrial). Instead, it utilizes a unified core dispatch engine that is dynamically governed by Regulations packages. These packages are hot-swappable, allowing the platform to adapt to new workforce domains without code redeployment.

### 3.2 Configuration Lifecycle

1.  **Authoring:** Tenants (via Agency Administrators) or Governing Entities author Regulations packages using a standardized schema.
2.  **Validation:** Regulations packages are validated against a core schema to ensure they are well-formed and do not conflict with universal platform rules.
3.  **Deployment:** Validated Regulations packages are deployed to the platform. This deployment is hot-swappable, meaning it does not require a full platform restart or redeployment.
4.  **Versioning:** Each Regulations package is versioned. This allows for rollback in case of errors and provides an audit trail of regulatory changes.
5.  **Enforcement:** The local-first edge AI on the Seeker's device enforces the active Regulations package during shift matching and clock-in/out processes.

## 4. Governance and Decision Rights

This section defines the decision owners for the core entities and configuration changes. These roles are established in the living product model and remain binding.

| Decision Area | Primary Decision Owner | Supporting Roles | Notes |
| :--- | :--- | :--- | :--- |
| Tenant Configuration | Agency Administrator [ACT-B91695A020] | Governing Entity [ACT-8D5C6B1AF5] | Agency Admins configure vertical-specific rules and fee profiles. |
| Seeker Onboarding | Governing Entity [ACT-8D5C6B1AF5] | Agency Administrator [ACT-B91695A020] | Governing Entities validate professional credentials against public registries. |
| Regulation Updates | Agency Administrator [ACT-B91695A020] | Governing Entity [ACT-8D5C6B1AF5] | Updates require collaboration to ensure compliance with both agency and regulatory body rules. |
| Client Onboarding | Agency Administrator [ACT-B91695A020] | - | Agency Admins manage client relationships and service requirements. |

## 5. Success Criteria and KPIs

This section defines the measurable success criteria for the VeloGig platform, aligned with the project's business rules and strategic goals.

| KPI Category | Metric | Target | Rationale |
| :--- | :--- | :--- | :--- |
| **Cost Efficiency** | Zero Baseline Compute Cost | 100% | Achieved by offloading real-time matching and compliance auditing to user devices via local-first edge AI. |
| **Platform Reliability** | Serverless Cloud Uptime | 99.99% | Ensures high availability for the cloud coordination layer using Cloudflare Workers and Supabase. |
| **Offline Capability** | Core Capability During Isolation | 100% | Providers must sustain 100% core capability during network isolations extending past 72 continuous hours. |
| **Market Adoption** | Agency Procurement Bypass | Eliminated | Base software costs the managing agency $0, eliminating the need for procurement bypass. |
| **Financial Liquidity** | Instant Cash-Out Availability | 100% | Financial workflows must support instant cash-out via InstantPay Pipeline with a 1.5%-2.5% liquidity convenience fee. |

### 5.1 Compliance Obligations

*   **CJIS (Law Enforcement):** All data handling and storage must comply with CJIS security policies. This includes encryption at rest and in transit, access controls, and audit logging.
*   **HIPAA (Healthcare):** Protected Health Information (PHI) must be handled in accordance with HIPAA regulations. This includes strict access controls, audit trails, and data minimization principles.
*   **DOT/HOS (Industrial/Hazmat):** Hours of Service (HOS) regulations must be enforced by the local-first edge AI to prevent driver fatigue and ensure safety.
*   **State Labor Laws:** Each vertical must comply with the specific labor laws of the jurisdictions in which its Seekers operate. This includes minimum wage, overtime, and break requirements.

## 6. Unresolved Questions and Knowledge Gaps

The following questions remain unresolved and require further research or decision-making in subsequent phases.

1.  **Regulation Hot-Swap Mechanism:** What is the specific technical mechanism for "hot-swapping" Regulations (e.g., dynamic class loading, external rule engine)? This requires technical selection in the Design phase.
2.  **InstantPay Liquidity Partner:** Which specific liquidity partner will be used for the InstantPay Pipeline? This decision impacts integration complexity, fee structures, and regulatory compliance.
3.  **Conflict Resolution Strategy:** What is the specific algorithm for resolving data conflicts when devices reconnect after a network isolation? This requires a detailed technical design.
4.  **Edge AI Model Update Protocol:** What is the secure and efficient protocol for updating local-first edge AI models across a distributed fleet of devices?

## 7. Conclusion

VeloGig presents a compelling vision for a universal marketplace and workforce dispatch platform. By leveraging a local-first edge AI architecture and a hot-swappable vertical configuration strategy, VeloGig can achieve zero-cost procurement for agencies while maintaining high levels of compliance and reliability. The core entity model and governance structure provide a solid foundation for further development. The unresolved questions identified in this artifact will be addressed in subsequent phases to ensure a robust and scalable platform.
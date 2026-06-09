# ProNext Inception Phase Decomposition: Unified Product Vision, Decision Owners, and Strategic Constraints

## 1. Unified Product Vision and Architectural Baseline

ProNext is defined as a single, unified, AI-native healthcare procurement and supply chain platform, explicitly rejecting the legacy competitor model of bolting together disconnected products. This unified architecture is built on one data model, one AI layer, and one supplier network, providing a seamless procurement lifecycle from order to payment for post-acute and non-acute providers (SNFs, ALFs, rehab centers, critical access hospitals, community hospitals, urgent care clinics, and physician groups).

### 1.1 Core Product Differentiator: Unified Architecture vs. Legacy Silos

The primary strategic advantage of ProNext is its monolithic data and AI foundation, which eliminates the friction, data silos, and compliance risks inherent in legacy multi-product stacks.

*   **Single Data Model:** Unlike legacy systems that maintain separate databases for inventory, purchasing, and finance, ProNext utilizes a unified data model. This ensures that inventory levels, GPO contract pricing, and budget allocations are synchronized in real-time across all facilities and user roles. This unity is critical for the `AgenticProcurementAutomation` journey, where AI agents must detect low-stock and pre-fill requisitions with accurate, negotiated pricing without data latency or inconsistency.
*   **One AI Layer:** ProNext employs a single, centralized AI layer for all intelligent functions, including natural language order interpretation (`IntelligentOrdering&Catalog`), spend forecasting (`SpendAnalyticsandForecasting`), and contract compliance enforcement. This AI layer is strictly bound by the business rule that all inference and model weights must remain within the client infrastructure perimeter to guarantee HIPAA compliance. This ensures that no patient or financial data leaves the client network during AI processing.
*   **One Supplier Network:** The platform integrates with a single, unified supplier network via PunchOut (cXML/OCI) and direct API connections, covering 9,000+ supplier catalogs. This allows the AI to search across all catalogs simultaneously, surface GPO-negotiated pricing automatically, and flag cheaper compliant alternatives before an order is submitted, preventing maverick spend proactively rather than reactively.

## 2. Target Decision Owners and Stakeholder Authority

Effective governance of the ProNext platform requires clear decision ownership across the post-acute provider spectrum. The following decision owners are identified based on their functional authority over the procurement lifecycle and strategic constraints. These roles map directly to the canonical actor registry.

| Decision Domain | Canonical Actor (ID) | Primary Responsibility | Governing Journey / Concern |
| :--- | :--- | :--- | :--- |
| **Strategic Vision & ROI** | Executive Sponsor | Budget and Scope Approval | Authorizes the unified platform approach, defines high-level success criteria, and approves the initial investment in the AI-native architecture. |
| **Compliance & Data Residency** | Auditor (ACT-FB2D634F18) | HIPAA, HITRUST, SOC2 Governance | Ensures all AI inference remains within the client perimeter, validates audit trail integrity (`SUR-5E4A75DEE7`), and approves data handling policies. |
| **Procurement & GPO Strategy** | Procurement Manager (ACT-3435DBDA4A) | GPO Contract Enforcement | Defines GPO contract rates, approves vendor selection criteria, and ensures the AI layer correctly enforces contract compliance and prevents maverick spend. |
| **Operational Execution** | Inventory Manager (ACT-2BACA7884B) | Facility-Level Inventory | Manages real-time inventory visibility (`SUR-76CA4761B7`), approves AI-generated replenishment suggestions, and executes goods receipt via mobile scanning. |
| **Clinical Procurement** | Physician (ACT-F622146FED) | Clinical Item Requisition | Initiates requisitions for clinical supplies, relying on the AI to pre-fill negotiated pricing and ensure compliance with clinical standards. |

## 3. Strategic Constraints and Binding Decisions

The following strategic constraints are established to guide the design and development of the ProNext platform, ensuring alignment with the unified vision and regulatory requirements.

*   **Constraint 1: Unified Data Model Integrity:** The platform must maintain a single source of truth for all procurement data. Any fragmentation of data into siloed modules is strictly prohibited. This constraint ensures that the `AgenticProcurementAutomation` and `Real-TimeBudgetIntelligence` capabilities function accurately across all facilities.
*   **Constraint 2: AI Inference Data Residency:** All AI inference and model weights must remain within the client infrastructure perimeter. This is a non-negotiable constraint to guarantee HIPAA compliance. No patient or financial data may leave the client network during AI processing.
*   **Constraint 3: Mandatory Human-in-the-Loop Financial Gate:** A mandatory human confirmation gate is required before any financial commitment is made by AI agents. This ensures that 100% of financial commitments are reviewed and approved by an authorized decision owner (e.g., `Procurement Manager`) before a Purchase Order is generated.
*   **Constraint 4: Proactive Maverick Spend Prevention:** The AI layer must flag cheaper compliant alternatives and prevent maverick spend before an order is submitted. This shifts the compliance model from reactive auditing to proactive enforcement, leveraging the unified data model to check against GPO contracts in real-time.
*   **Constraint 5: Supplier Network Interoperability:** The platform must support PunchOut via cXML/OCI for direct supplier shopping and integrate with major GPOs. This ensures broad supplier coverage and seamless integration with existing procurement workflows.

## 4. Success Criteria and Measurable KPIs

To ensure the inception phase delivers a testable baseline, the following success criteria are defined. These metrics are directly traceable to the `CAP_inception_success_criteria` capability and the `SpendAnalyticsandForecasting` journey.

| Success Metric | Target / Threshold | Measurement Method | Traceability |
| :--- | :--- | :--- | :--- |
| **AI Data Residency** | 100% of inference within client perimeter | Infrastructure audit and network traffic logs | `CAP_inception_compliance_security_architecture` |
| **Financial Gate Enforcement** | 100% of AI-initiated financial commitments require human confirmation | System logs and audit trail (`SUR-5E4A75DEE7`) | `JNY-AC859AD751` |
| **Maverick Spend Prevention** | 100% of non-compliant orders blocked pre-submission | Transaction logs and compliance reports | `CON-4655F8BEBE` |
| **Facility Onboarding Speed** | Onboarding completed in days rather than months | Time-to-live metrics per facility | `CAP_inception_success_criteria` |
| **Invoice Matching Accuracy** | Real-time flagging of price/quantity discrepancies | Three-way match variance reports | `JNY-FA8FB27872` |

## 5. Critical Knowledge Gaps and Unresolved Decisions

The following gaps represent critical decisions that must be resolved before the Design phase can proceed. These are not implementation details, but strategic boundaries that define the scope of the unified platform.

*   **KNOWLEDGE_GAP: Specific GPO Contract Integration Volumes** - The exact number of GPO contracts and specific vendor APIs to be integrated at Go-Live vs. Phase 2 must be established by the Procurement Manager (`ACT-3435DBDA4A`) to scope the `vendor_integration` surface (`SUR-365F106CEF`).
*   **KNOWLEDGE_GAP: AI Model Weight Storage and Update Cadence** - While residency is mandated, the specific mechanism for storing, updating, and versioning model weights within the client perimeter (e.g., local vector DBs, containerized models) requires architectural definition to ensure performance and compliance.
*   **KNOWLEDGE_GAP: Mobile Inventory Hardware Compatibility** - The specific mobile devices and barcode/QR scanning hardware supported by the `Inventory Manager` (`ACT-2BACA7884B`) must be defined to ensure the `mobile_inventory` surface (`SUR-76CA4761B7`) is compatible with existing facility infrastructure.

## 6. Risk Register and Compliance Architecture Handoff

*Note: This artifact explicitly defers the detailed risk catalog and compliance security architecture to their respective sibling artifacts to maintain phase boundaries and prevent scope creep.*

*   **Risk Register:** The `Inception Risk Register: ProNext Healthcare Procurement Platform` (`CAP_inception_risk_register`) is the authoritative home for risk identification, categorization, and mitigation strategies. This artifact identifies strategic risks (e.g., unified data model complexity, AI inference latency) but delegates detailed risk quantification to the Risk Register artifact.
*   **Compliance Security Architecture:** The `Deliver Inception Phase Decomposition: Identify HIPAA, HITRUST, SOC2, and regulatory compliance and security architecture foundations` (`CAP_inception_compliance_security_architecture`) is the authoritative home for compliance mapping, data handling policies, and security controls. This artifact mandates the constraints (e.g., data residency) but delegates the architectural implementation details to the Compliance Security Architecture artifact.

## 7. Conclusion and Next Steps

This inception artifact establishes the authoritative baseline for the ProNext project. It defines the system as a unified, AI-native healthcare procurement and supply chain platform, explicitly mapping the four primary user journeys and identifying the real decision owners for its concern surface. The strategic constraints regarding data model unity, AI layer integration, and supplier network interoperability are now binding. The next phase (Design) must proceed by addressing the identified knowledge gaps and expanding the architectural details within the boundaries defined here.
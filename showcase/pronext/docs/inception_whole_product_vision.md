# ProNext Inception: Whole Product Vision and Decision Foundations

## 1. The 'One Platform' Invariant: ProNext Unified Architecture

ProNext is architected as a single, cohesive procurement and supply chain platform, explicitly rejecting the legacy industry standard of 'bolt-on' solutions that stitch together disconnected inventory, purchasing, and financial modules. This 'One Platform' invariant ensures that every care-setting operator—from skilled nursing facilities (SNFs) to critical access hospitals—experiences a unified procurement lifecycle from order to payment within a single login, backed by one data model, one AI layer, one supplier network, and one user experience (UX).

### 1.1 One Unified Data Model
Legacy competitors typically maintain siloed databases for inventory, purchasing, and financials, leading to data drift and reconciliation errors. ProNext utilizes a single, normalized data model that serves as the system of record for all procurement activities.

*   **Unified Entity Resolution:** A single 'Item' entity is shared across Intelligent Ordering, Inventory Management, and Smart AP Automation. This ensures that when a Procurement Requester (ACT-FA0309AFC6) orders an item, the system automatically updates inventory levels, budget availability, and financial commitments in real-time without batch reconciliation.
*   **Multi-Entity Support:** The data model natively supports multi-entity hierarchies (e.g., a health system managing multiple SNFs), allowing for centralized GPO contract management while enabling facility-level inventory visibility and budgeting.
*   **Traceability:** Every transaction is traceable from the initial order line item through to the three-way match in AP, providing end-to-end visibility into spend, compliance, and inventory movement.

### 1.2 One AI Layer
ProNext employs a single, centralized AI layer that powers all intelligent features, ensuring consistency, accuracy, and compliance across the platform. This AI layer is not a bolt-on chatbot but the core engine for decision support and automation.

*   **Intelligent Ordering & Catalog:** The AI agent interprets natural language or UI-based orders from staff, searches across 9,000+ supplier catalogs, and surfaces GPO-negotiated pricing automatically. It enforces contract compliance and prevents maverick spend by flagging cheaper compliant alternatives before the order is submitted.
*   **Agentic Procurement Automation:** AI agents autonomously detect low-stock levels across facilities, identify the best compliant vendor based on negotiated pricing and availability, and pre-fill Purchase Requisitions. These agents route requisitions through the correct approval chain, requiring mandatory human confirmation from a Finance Approver (ACT-D0B70FB938) before converting to a Purchase Order (PO).
*   **Real-Time Budget Intelligence:** The AI layer provides pre-approval budget impact visualization at the facility, department, and GL-code levels, enabling proactive financial governance.
*   **Smart AP Automation:** AI ingests invoices via EDI 810, cXML, or OCR, auto-matching them to originating POs and goods receipts. It flags real-time variances in price or quantity, streamlining the accounts payable process.
*   **Local Processing Constraint:** To guarantee HIPAA compliance, all AI inference and model weights remain within the client infrastructure perimeter, ensuring no patient or financial data leaves the local runtime.

### 1.3 One Supplier Network
ProNext integrates with a unified supplier network, eliminating the need for manual data entry or multiple supplier portals.

*   **PunchOut Integration:** The platform supports PunchOut via cXML/OCI for direct shopping with major suppliers like McKesson, Medline, Cardinal Health, and Sysco, allowing staff to shop within their familiar supplier catalogs while maintaining ProNext's contract compliance and data integrity.
*   **Hosted Internal Catalogs:** For suppliers without PunchOut integration, ProNext provides hosted internal catalogs for pre-approved items, ensuring all purchases are tracked and compliant.
*   **GPO Contract Enforcement:** GPO contract rates are automatically loaded at go-live and enforced during the ordering process, ensuring that every purchase leverages the best available negotiated pricing.

### 1.4 One User Experience (UX)
The UX is designed to be intuitive and consistent across all user roles and care settings, reducing training time and improving adoption.

*   **Natural Language Interface:** Staff can place orders using natural language or a clean, guided UI, lowering the barrier to entry for non-technical users.
*   **Role-Based Dashboards:** The UX adapts to the user's role: Procurement Requesters (ACT-FA0309AFC6) see ordering and inventory tools; Finance Approvers (ACT-D0B70FB938) see approval queues and budget insights; System Operators (ACT-0FC1969E12) see system health and compliance reports.
*   **Mobile-First Operations:** The platform supports mobile barcode/QR scanning for inventory management, enabling real-time stock checks and adjustments from the floor.

### 1.5 Contrast with Legacy Bolt-On Models

| Feature | Legacy Bolt-On Models | ProNext 'One Platform' Invariant |
| :--- | :--- | :--- |
| Data Model | Siloed databases for inventory, purchasing, and finance | Single, normalized data model |
| AI Layer | Disconnected AI tools or chatbots | Centralized AI engine for all intelligent features |
| Supplier Network | Manual entry or multiple disconnected portals | Unified PunchOut (cXML/OCI) and hosted catalogs |
| User Experience | Inconsistent UIs across modules | Single, role-based, intuitive UX |
| Compliance | Post-hoc compliance checks | Real-time contract compliance enforcement |
| Onboarding | Months of configuration and data migration | Days of onboarding using AI-guided playbooks |

This 'One Platform' invariant is the foundational strategic decision for ProNext, ensuring that the system delivers true end-to-end value rather than fragmented point solutions.

## 2. Executive Concern Surface and Decision Owners

The executive concern surface defines the primary decision domains that must be ratified to move ProNext from vision to execution. Each concern is mapped to its authoritative decision owner and the specific project axis it governs.

| Concern Domain | Decision Owner | Primary Axis / Artifact | Rationale |
| :--- | :--- | :--- | :--- |
| **AI Agent Autonomy & Human-in-the-Loop** | Product Strategy / VP of AI | `CAP_inception_compliance_security_architecture_agent_governance` | Defines the exact boundaries of autonomous action and the mandatory confirmation gates for financial commitments. |
| **GPO Contract Compliance & Spend Governance** | Procurement Leadership | `CAP_inception_whole_product_vision` | Establishes the rules for GPO rate enforcement, maverick spend prevention, and cheaper alternative flagging. |
| **Multi-Entity Approval Workflows** | Finance Leadership | `CAP_inception_operational_constraints` | Defines the routing logic for requisitions across facility hierarchies and budget thresholds. |
| **Data Perimeter & Local Processing** | Security Architecture | `CAP_inception_compliance_security_architecture_data_perimeter` | Mandates that all AI inference and model weights remain within the client infrastructure perimeter. |
| **Regulatory Compliance (HIPAA/HITRUST)** | Compliance Officer | `CAP_inception_compliance_security_architecture` | Ensures the platform meets healthcare-specific regulatory obligations for data privacy and security. |

### 2.1 Mandatory Human-in-the-Loop Confirmation
*   **Constraint:** AI agents are strictly prohibited from converting a Purchase Requisition into a binding Purchase Order (PO) without explicit, documented human confirmation.
*   **Owner:** Finance Approver (ACT-D0B70FB938)
*   **Mechanism:** The system must present a clear, auditable summary of the AI-generated requisition (including vendor, price, and compliance status) to the Finance Approver. The agent cannot proceed until the Approver explicitly approves the transaction.
*   **Rationale:** This prevents unauthorized financial commitments and ensures human oversight of all procurement spend.

### 2.2 Pre-Submission Maverick Spend Prevention
*   **Constraint:** The AI must flag cheaper compliant alternatives and prevent maverick spend *before* the order is submitted by the Procurement Requester (ACT-FA0309AFC6), not after.
*   **Mechanism:** During the ordering process, the AI layer must cross-reference the requested item against active GPO contracts and pre-approved catalogs. If a cheaper, compliant alternative exists, it must be surfaced to the user. If a non-compliant item is selected, the system must block submission or require an explicit exception workflow.
*   **Rationale:** This ensures that every purchase leverages negotiated pricing and maintains contract compliance, directly impacting the organization's bottom line.

### 2.3 Local Processing and Data Perimeter
*   **Constraint:** All AI inference and model weights must remain within the client infrastructure perimeter to guarantee HIPAA compliance.
*   **Owner:** System Operator (ACT-0FC1969E12)
*   **Mechanism:** No patient or financial data may leave the local runtime during AI inference. The AI models must be deployed and executed on-premises or within a private, client-controlled cloud environment.
*   **Rationale:** This is a critical compliance requirement to protect sensitive healthcare data and maintain regulatory adherence (HIPAA, HITRUST).

### 2.4 Real-Time Budget Intelligence
*   **Constraint:** The system must provide pre-approval budget impact visualization at the facility, department, and GL-code levels.
*   **Mechanism:** Before an order is submitted, the AI layer must calculate and display the projected budget impact, allowing the user to see the financial consequences of their procurement decisions in real-time.
*   **Rationale:** This enables proactive financial governance and prevents budget overruns.

## 3. Success Criteria and Decision Foundations

### 3.1 Observable Success Conditions
The following success criteria must be met for the ProNext platform to be considered successful at launch and during initial operations:

1.  **Zero Data Leakage:** Zero patient or financial data leaves the client network during AI inference.
2.  **Mandatory Human Confirmation:** Mandatory human confirmation is enforced for 100% of financial commitments made by agents.
3.  **Real-Time Spend Visibility:** Spend-to-budget visibility is available in real-time at facility, department, and GL-code levels.
4.  **Automated Invoice Matching:** Invoices are matched to POs and receipts automatically with real-time variance flagging.
5.  **Rapid Onboarding:** Facility onboarding is completed in days rather than months using AI-guided playbooks.

### 3.2 Unresolved Decision Axes
The following decisions remain open and require resolution before downstream development phases can proceed. These are critical gaps that must be addressed to finalize the product vision.

| Decision Axis | Current Status | Required Action | Owner |
| :--- | :--- | :--- | :--- |
| **Exact GPO Contract Data Loading Mechanism** | Not Determined | Define the specific ETL/ELT process and data format for loading GPO rates at go-live. | Procurement Leadership |
| **Specific AI Model Versions for Local Deployment** | Not Determined | Identify the specific AI models and their versions that will be deployed locally to meet performance and accuracy requirements. | VP of AI |
| **Detailed Multi-Entity Hierarchy Structure** | Not Determined | Define the exact hierarchy structure (e.g., Health System -> Facility -> Department) and how budget approvals flow through it. | Finance Leadership |
| **Exact PunchOut Integration Standards** | Not Determined | Confirm the specific cXML/OCI versions and supplier-specific integration requirements for the initial supplier network. | Procurement Leadership |

### 3.3 Knowledge Gap Registry
The following knowledge gaps have been identified and must be resolved by the research pipeline or subject matter experts before the next phase.

*   **KNOWLEDGE_GAP: Exact HIPAA compliance requirements for AI inference in a local runtime environment.** - *Responsible: Compliance Officer. Evidence needed: Legal review of HIPAA regulations regarding on-premises AI processing.*
*   **KNOWLEDGE_GAP: Specific performance benchmarks for AI inference latency within the local infrastructure perimeter.** - *Responsible: System Operator. Evidence needed: Infrastructure capacity planning and load testing results.*
*   **KNOWLEDGE_GAP: Detailed API contracts for PunchOut integration with major suppliers (McKesson, Medline, etc.).** - *Responsible: Procurement Leadership. Evidence needed: Supplier integration documentation.*

### 3.4 Follow-Up Questions for Project Leadership
The following questions require explicit answers from project leadership to close the unresolved decision axes and knowledge gaps.

1.  **What is the binding authority for HIPAA compliance interpretation regarding local AI inference?** - *Why critical: Determines the exact security architecture requirements.*
2.  **What is the specific decision owner for ratifying the GPO contract data loading process?** - *Why critical: Defines the ownership of the procurement data pipeline.*
3.  **What is the binding retention period for audit logs of AI agent actions?** - *Why critical: Impacts data storage architecture and compliance reporting.*

### 3.5 Inception Risk Register
*   **Risk:** AI model inaccuracy leading to incorrect vendor selection or pricing.
    *   **Mitigation:** Implement rigorous testing and validation of AI models against historical procurement data. Maintain human-in-the-loop confirmation for all financial commitments.
*   **Risk:** Failure to enforce GPO contract compliance, leading to maverick spend.
    *   **Mitigation:** Enforce real-time contract compliance checks during the ordering process. Provide clear visibility into contract rates and alternatives to users.
*   **Risk:** Data leakage during AI inference, violating HIPAA.
    *   **Mitigation:** Deploy AI models and data within the client infrastructure perimeter. Implement strict network segmentation and access controls.

### 3.6 Operational Constraints
*   **Constraint:** All AI inference and model weights must remain within the client infrastructure perimeter.
*   **Constraint:** Mandatory human-in-the-loop confirmation is required before any financial commitment is made by AI agents.
*   **Constraint:** AI must flag cheaper compliant alternatives and prevent maverick spend before order submission, not after.
*   **Constraint:** Invoices must be auto-matched to originating POs and goods receipts with real-time flagging of price/quantity discrepancies.
*   **Constraint:** GPO contract rates must be automatically loaded at go-live and enforced during the ordering process.

## 4. Conclusion

ProNext represents a paradigm shift in healthcare procurement, moving from fragmented, bolt-on solutions to a unified, AI-native platform. By adhering to the 'One Platform' invariant, enforcing binding constraints on AI agent behavior, and addressing critical decision gaps, ProNext is positioned to deliver significant value to post-acute and non-acute providers. The next phase of development must focus on resolving the unresolved decision axes and knowledge gaps identified in this artifact to ensure a successful launch.
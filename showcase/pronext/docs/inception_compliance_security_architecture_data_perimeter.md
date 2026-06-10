# Data Perimeter and AI Inference Constraints

## 1. Architectural Surface and Zero-Trust Boundary

The ProNext platform operates under a strict **Local Runtime** deployment model, as defined in the project system classification. This mandates that all model weights, inference containers, and agent decision logs must remain entirely within the client's infrastructure perimeter. The architectural surface for **Architectural surface: data_perimeter (inception_compliance_security_architecture_data_perimeter)** (SUR-BAFA208216) is defined by the following immutable constraints:

*   **Inference Isolation:** All AI/LLM inference engines (**HIPAA-NativeAIRuntime**) are containerized and executed on-premise or within a private, air-gapped VPC owned by the client. No outbound network calls to external model providers (e.g., OpenAI, Anthropic) are permitted for inference.
*   **Data Residency:** Patient data (PHI) and financial data (PII/PCI) are never transmitted outside the client's network boundary. Data ingress is strictly controlled via internal APIs and secure file drops; data egress is limited to structured, non-sensitive procurement signals (e.g., PO numbers, line item SKUs) destined for external suppliers.
*   **Zero-Trust Network:** Internal communication between the **Procurement Requester** (ACT-FA0309AFC6), **System Operator** (ACT-0FC1969E12), and **Finance Approver** (ACT-D0B70FB938) is authenticated and encrypted. No implicit trust is granted between microservices; all data flows are logged and audited.

## 2. Data Ingress Points

Data enters the ProNext perimeter through three primary channels. Each ingress point is subject to strict validation and sanitization to ensure no unauthorized PHI or financial data is ingested into the AI inference layer.

| Ingress Channel | Data Type | Source Actor / System | Processing Constraint |
| :--- | :--- | :--- | :--- |
| Intelligent Ordering & Catalog | Procurement Intent, SKU, Quantity | **Procurement Requester** (ACT-FA0309AFC6) via UI/NLP | NLP intent parsing occurs locally. No raw user queries are sent to external APIs. PII/PHI scrubbing is applied before catalog search. |
| Smart AP Automation | Invoices (EDI 810, cXML, OCR) | External Suppliers / Internal ERP | OCR and AI matching occur on-premise. Invoice data is matched against internal POs and Goods Receipts. No invoice images or raw text leave the perimeter. |
| Unified Inventory | Stock Levels, Par Levels, FIFO Data | Internal WMS / Mobile Scanning | Real-time inventory data is ingested via internal APIs. AI-predicted par level adjustments are calculated locally. |

## 4. AI Inference Constraints

The **HIPAA-NativeAIRuntime** ensures that AI inference is performed entirely within the client's infrastructure. The following constraints are enforced:

*   **Model Weights:** Model weights are stored and loaded from local, encrypted storage. They are never downloaded from external registries during runtime.
*   **Inference Containers:** Inference containers are ephemeral and isolated. They are destroyed after each inference cycle, ensuring no residual data remains in memory.
*   **Agent Decision Logs:** All agent decision logs are stored locally and are subject to the same retention and access controls as other patient and financial data. Logs are never transmitted to external services.
*   **Human-in-the-Loop:** As per the business rules, a mandatory human-in-the-loop confirmation gate is required before any financial commitment. The AI agent flags cheaper compliant alternatives, but the final decision rests with the **Finance Approver** (ACT-D0B70FB938).

## 5. Compliance and Audit Alignment

This artifact aligns with the broader regulatory architecture and risk posture of the ProNext platform:

*   **Regulatory Architecture:** The data perimeter constraints support the **Architectural surface: regulatory_architecture (inception_compliance_security_architecture)** (SUR-EF9A4B8C60) by ensuring that PHI and PII never traverse untrusted networks, satisfying core HIPAA and HITRUST requirements for data in transit and at rest.
*   **Risk Register:** The risk posture is informed by the **Architectural surface: Inception Risk Register: ProNext Healthcare Procurement Platform (inception_risk_register)** (SUR-B743876A4D), which identifies potential risks related to data leakage and compliance drift. The strict local runtime model mitigates the risk of external data exfiltration.
*   **Operational Constraints:** The artifact's operational constraints are aligned with the **Architectural surface: Operational Constraints and Integration Requirements (inception_operational_constraints)** (SUR-BAEC685276), which define the technical boundaries for the platform.
*   **Success Criteria:** The artifact's success criteria are aligned with the **Architectural surface: Deliver Inception Phase Decomposition: Define observable success conditions, KPI (inception_success_criteria)** (SUR-F6AE7738C0), which defines the KPIs for the platform's performance and compliance.

## 6. Knowledge Gaps and Assumptions

*   **KNOWLEDGE_GAP:** The exact data retention period for inference logs and agent decision logs is not yet defined. This must be aligned with the project's data retention policy and regulatory requirements (HIPAA, HITRUST). The **System Operator** (ACT-0FC1969E12) must establish this with legal/compliance.
*   **KNOWLEDGE_GAP:** The specific encryption standards for data at rest and in transit within the client's infrastructure are not yet defined. This must be aligned with the project's security architecture foundations (**Capability: Security Architecture Foundations (inception_compliance_security_architecture)** (CAP_inception_compliance_security_architecture)).
*   **ASSUMPTION:** The client's infrastructure provides sufficient compute resources to host the on-premise LLM services without performance degradation. This assumption must be validated during the Design phase.
*   **ASSUMPTION:** The client's ERP/EHR systems support the required API integrations for real-time inventory and budget data ingestion. This assumption must be validated during the Design phase.

## 7. Cross-Artifact References

*   This artifact's risk posture is informed by the Inception Risk Register (SUR-B743876A4D), which identifies potential risks related to data leakage and compliance drift.
*   This artifact's operational constraints are aligned with the Operational Constraints and Integration Requirements (SUR-BAEC685276), which define the technical boundaries for the platform.
*   This artifact's success criteria are aligned with the Success Metrics Definition (SUR-F6AE7738C0), which defines the KPIs for the platform's performance and compliance.
*   This artifact's agent governance is aligned with the Agent Governance and Human-in-the-Loop Confirmation (SUR-D93C62C328), which defines the human-in-the-loop requirements for financial commitments.
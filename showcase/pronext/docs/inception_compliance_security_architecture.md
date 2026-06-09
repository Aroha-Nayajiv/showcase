# Inception Compliance & Security Architecture

## 1. HIPAA-Native Data Perimeter and AI Runtime Boundaries

ProNext establishes a strict, non-negotiable data perimeter that guarantees no Protected Health Information (PHI) or financial data ever leaves the client's infrastructure. This architectural boundary is the primary compliance differentiator against cloud-only competitors, ensuring full alignment with HIPAA, HITRUST, and SOC2 requirements for data sovereignty.

### 1.1 Data Classification and Perimeter Mapping

All data within the ProNext ecosystem is classified into three distinct tiers, each with specific handling rules regarding the AI runtime boundary:

| Data Tier | Classification Scope | Perimeter Boundary | AI Inference Access |
| :--- | :--- | :--- | :--- |
| PHI | Patient demographics, clinical notes, physician orders (ACT-F622146FED) | Strictly Internal | Zero Access. Never transmitted to AI models. |
| Financial Data | GPO contract rates, invoice amounts, PO values, budget GL codes | Strictly Internal | Zero Access. Never transmitted to AI models. |
| Operational Data | Inventory counts, SKU descriptions, supplier catalog metadata, usage trends | Perimeter Boundary | Allowed. Only non-PII/PHI operational data is exposed to the AI for inference. |

### 1.2 On-Prem AI Runtime Architecture

The AI layer is not a SaaS service; it is a containerized runtime deployed within the client's VPC or on-prem data center. This ensures that all model weights, inference containers, and agent decision logs remain within the client infrastructure perimeter.

*   **Deployment Model:** Local runtime. The AI engine is packaged as a containerized service that integrates with the ProNext core via internal APIs.
*   **Configurable Endpoints:** The AI endpoint URL and model name are fully configurable per deployment with zero code changes. This allows clients to select their preferred local inference engine based on their existing hardware and security policies.
*   **Supported Inference Engines:** Ollama, vLLM, LM Studio, LocalAI, llama.cpp server.

### 1.3 Audit Trail and Traceability

All AI interactions are logged within the client's immutable audit trail (SUR-5E4A75DEE7). This includes:
*   The sanitized operational data sent to the AI.
*   The AI's response/recommendation.
*   The human decision (approve/reject) and the rationale.
*   The final financial commitment.

This ensures complete traceability for HITRUST and SOC2 audits, demonstrating that AI was used as a decision-support tool under strict human oversight, with no sensitive data ever leaving the perimeter.

## 2. Agentic Runtime Architecture & Compliance Gates

To ensure security, compliance, and vendor neutrality, the ProNext agentic runtime must be pluggable and strictly bound to the client infrastructure perimeter. The runtime will utilize the Model Context Protocol (MCP) to standardize how AI agents interact with internal data sources (inventory, GPO contracts, budget ledgers) and external supplier systems.

### 2.1 MCP Standardization and Local-First Inference

*   **MCP Standardization:** The runtime will implement the Model Context Protocol to expose internal capabilities (e.g., `get_inventory_levels`, `validate_gpo_contract`, `check_budget_availability`) as standardized tools. This ensures that any compliant LLM backend (e.g., Ollama, vLLM) can interact with the system without custom integration code.
*   **Local-First Inference:** Per the SoftwareDNA definition, all model weights, inference containers, and agent decision logs must remain within the client infrastructure perimeter. No PHI, financial data, or proprietary procurement data may be transmitted to external AI providers for inference.
*   **Configurable Endpoints:** The system must support fully configurable AI endpoint URLs and model names via environment variables or configuration files, allowing zero-code changes to switch between local and remote (if permitted by specific client security policies) inference engines.

### 2.2 Autonomous Agent Workflows & HITL Gates

AI agents are empowered to perform preparatory and analytical tasks autonomously, but financial commitments require explicit human authorization. The following workflow defines the boundary between autonomous action and mandatory human confirmation.

#### 2.2.1. Autonomous Detection & Preparation
Agents operate autonomously in the following phases:
*   **Low-Stock Detection:** Agents continuously monitor inventory levels across all facilities (Skilled Nursing, Assisted Living, etc.) against dynamic thresholds. When stock falls below the defined safety level, the agent triggers a replenishment workflow.
*   **Vendor Identification & Pricing:** The agent searches the 9,000+ supplier catalogs, prioritizing GPO-negotiated pricing. It identifies the best compliant vendor based on contract terms, availability, and historical performance.
*   **Requisition Pre-filling:** The agent pre-fills a Purchase Requisition with the identified items, negotiated pricing, and suggested vendor. It also flags any cheaper compliant alternatives available in the catalog.

#### 2.2.2. Mandatory Human-in-the-Loop (HITL) Confirmation
Before any financial commitment is made, the system enforces a strict HITL gate. This is a non-negotiable compliance requirement for HITRUST and SOC2.
*   **Requisition Review:** The pre-filled Purchase Requisition is routed to the appropriate approver (e.g., Procurement Manager) based on the facility, department, and GL-code.
*   **Approval Action:** The approver must explicitly review and confirm the requisition. The system does not auto-convert approved requisitions to Purchase Orders without this explicit human action.
*   **Exception Handling:** If an agent identifies a non-compliant or high-risk item (e.g., price drift > 5% from GPO rate), it must flag the item for mandatory human review before inclusion in the requisition.

### 2.3 HITRUST & SOC2 Audit Trail Requirements

To satisfy r13 (Audit Trail) and SOC2 CC6.1 (Logical and Physical Access Controls), the system must maintain an immutable, cryptographically verifiable log of all procurement actions. The audit trail (SUR-5E4A75DEE7) must capture:

1.  **Actor Identity:** The authenticated user or system agent initiating the action.
2.  **Action Type:** The specific operation performed (e.g., `REQUISITION_CREATE`, `APPROVAL_GRANTED`, `PO_ISSUED`).
3.  **Data Context:** The specific data elements modified or accessed, including the AI-generated recommendation and the human override (if any).
4.  **Timestamp:** A precise, synchronized timestamp for every event.
5.  **Outcome:** The final state change resulting from the action.

### 2.4 Regulatory Mapping

| Regulation | Control Objective | ProNext Architectural Control | Traceability |
| :--- | :--- | :--- | :--- |
| HIPAA | Data Sovereignty & PHI Protection | Strict data perimeter; Zero PHI access for AI runtime. | SUR-5E4A75DEE7 |
| HITRUST r13 | Audit Trail & Traceability | Immutable, cryptographically verifiable logs of all AI and human actions. | SUR-5E4A75DEE7 |
| SOC2 CC6.1 | Logical Access Controls | Role-based access control (RBAC) for Physician, Procurement Manager, Inventory Manager, Auditor. | ACT-F622146FED, ACT-3435DBDA4A, ACT-2BACA7884B, ACT-FB2D634F18 |
| SOC2 CC7.2 | System Monitoring | Real-time monitoring of AI inference logs and budget thresholds. | SUR-AD039605C0 |

### 2.5 Risk Register Handoff

The following architectural decisions directly feed into the Inception Risk Register (CAP_inception_risk_register):
*   **AI Hallucination Risk:** Mitigated by mandatory HITL gates and explicit flagging of non-compliant alternatives.
*   **Data Leakage Risk:** Mitigated by strict data classification and zero-access policies for PHI/Financial data in the AI runtime.
*   **Vendor Integration Risk:** Mitigated by MCP standardization and strict perimeter controls on external supplier data.

## 3. Open Decisions & Knowledge Gaps

The following decisions require resolution by the project decision owners before the Design phase can proceed.

| Decision Axis | Impact | Owner | Status |
| :--- | :--- | :--- | :--- |
| Specific AI Inference Engine Selection | Determines hardware requirements and containerization strategy. | Infrastructure Lead | Knowledge Gap |
| Exact Audit Log Retention Period | Determines storage costs and compliance with HIPAA/SOC2 retention rules. | Compliance Officer | Knowledge Gap |
| MCP Tool Definition for GPO Validation | Determines the precision of contract compliance enforcement. | Procurement Manager | Knowledge Gap |

## 4. Success Criteria & Verification

*   **HIPAA Compliance:** Zero PHI data transmitted to external AI endpoints. Verified by network traffic analysis and perimeter logging.
*   **HITRUST r13 Compliance:** 100% of procurement actions logged with actor, action, timestamp, and outcome. Verified by audit trail sampling.
*   **SOC2 CC6.1 Compliance:** All access to sensitive data (PHI, Financial) restricted to authorized roles. Verified by RBAC configuration review.
*   **AI Runtime Sovereignty:** All model weights and inference logs remain within the client infrastructure perimeter. Verified by deployment architecture review.
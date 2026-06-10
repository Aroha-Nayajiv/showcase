# Agent Governance and Human-in-the-Loop Confirmation

## 1. Governance Mandate and Scope

This artifact defines the mandatory Human-in-the-Loop (HITL) confirmation gates for ProNext's AI-native procurement agents. It enforces the SoftwareDNA business rule: "Mandatory human-in-the-loop confirmation gate is required before any financial commitment is made by AI agents." This governance model applies to all AI-driven actions within the `AgenticProcurementAutomation` and `IntelligentOrdering&Catalog` domains, ensuring that no Purchase Order (PO), Contract, or Payment Authorization is executed without explicit human consent.

The scope of this artifact is limited to the governance logic, decision ownership, and confirmation workflows. Implementation details regarding cryptographic signing, immutable audit log storage, and specific compliance control mappings (e.g., HIPAA 164.312) are governed by the `Security Architecture Foundations (inception_compliance_security_architecture)` and `Data Perimeter Enforcement (inception_compliance_security_architecture_data_perimeter)` capabilities.

## 2. Definition of Financial Commitment

For the purposes of this governance model, a "Financial Commitment" is defined as any AI-generated action that creates a binding obligation for the client to pay a vendor. This includes:

*   **Purchase Order (PO) Creation:** Generating a PO from a requisition.
*   **Contract Execution:** Signing or renewing a vendor contract.
*   **Payment Authorization:** Initiating a payment via ACH, Wire, or Check.
*   **Change Orders:** Modifying an existing PO or contract to increase value or scope.

## 3. HITL Confirmation Matrix

The following matrix defines the specific transaction types and thresholds that trigger mandatory HITL confirmation. All financial commitments, regardless of value, require explicit human approval.

| Transaction Type | Trigger Condition | HITL Requirement | Decision Owner | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| Purchase Order (PO) | Any value > $0 | Mandatory HITL | Finance Approver (ACT-D0B70FB938) | Ensures 100% compliance with SoftwareDNA mandate; prevents maverick spend. |
| Purchase Order (PO) | New Vendor Onboarding | Mandatory HITL | Finance Approver (ACT-D0B70FB938) | Mitigates fraud and compliance risk associated with new supplier relationships. |
| Contract Execution | Any value > $0 | Mandatory HITL | Finance Approver (ACT-D0B70FB938) | Legal and financial binding requires human accountability. |
| Payment Authorization | Any value > $0 | Mandatory HITL | Finance Approver (ACT-D0B70FB938) | Prevents unauthorized fund disbursement. |
| Change Order | Any value increase | Mandatory HITL | Finance Approver (ACT-D0B70FB938) | Ensures scope and budget changes are explicitly approved. |

## 4. The Confirmation Gate Workflow

The HITL confirmation is implemented as a "Confirmation Gate" within the `RequisitiontoOrderConversion` user journey. The workflow is as follows:

1.  **AI Agent Action:** The AI agent detects a need (e.g., low stock) and identifies the best compliant vendor and negotiated pricing.
2.  **Pre-Approval Visualization:** The system presents the AI-generated requisition to the `Finance Approver (ACT-D0B70FB938)` with real-time budget impact visualization (aligned with `Real-TimeBudgetIntelligence`).
3.  **Human Confirmation:** The `Finance Approver (ACT-D0B70FB938)` must explicitly approve the requisition. This action converts the requisition to a Purchase Order.
4.  **Audit Logging:** The approval action is logged in the immutable audit trail, capturing the agent ID, human actor ID, timestamp, and decision.

## 5. Agent Intent-to-Approval Context Mapping

This section defines the mandatory context payload that the ProNext AI agent must generate and present to the human reviewer (e.g., `Finance Approver (ACT-D0B70FB938)`) at the Confirmation Gate. This mapping ensures that the human reviewer can make an informed, compliant decision without needing to perform external research, satisfying the requirement for 100% human-in-the-loop confirmation on financial commitments.

### 5.1 Confirmation Gate Payload Structure

The AI agent's 'intent interpretation' output is transformed into a structured Confirmation Gate Payload. This payload is the single source of truth for the human reviewer's decision interface. It must contain the following mandatory fields:

| Field Category | Data Element | Description | Source |
| :--- | :--- | :--- | :--- |
| Intent Summary | agent_reasoning | A concise, natural language explanation of why the AI selected this specific vendor and item combination. | Derived from the AI's intent interpretation and ranking algorithm. |
| Compliance | gpo_compliance_status | Boolean flag indicating if the selected vendor and item are covered by an active GPO contract. | Cross-referenced against the loaded GPO contract database. |
| Compliance | contract_compliance_details | If compliant, the specific GPO contract ID and negotiated rate applied. If non-compliant, the reason for flagging. | GPO contract database lookup. |
| Financial | budget_impact | The total cost of the transaction, broken down by facility, department, and GL code. | Real-time budget intelligence engine. |
| Financial | variance_from_baseline | Percentage difference from the historical spend baseline for this item/facility. | AI-powered spend forecasting and historical data analysis. |
| Alternatives | cheaper_compliant_alternatives | List of cheaper, compliant alternatives flagged by the AI, if any exist. | AI agent's pre-submission check logic. |
| Audit | audit_trail_id | A unique, immutable identifier for this specific agent action and human review event. | System-generated UUID. |

### 5.2 Context Transfer Workflow

1.  **Agent Intent Interpretation:** The AI agent processes the user's request (e.g., "Order 50 boxes of N95 masks") and identifies the optimal vendor based on GPO contracts and budget constraints.
2.  **Payload Generation:** The agent constructs the Confirmation Gate Payload, populating all mandatory fields defined in Section 5.1.
3.  **Human Review Interface:** The `Finance Approver (ACT-D0B70FB938)` receives a notification to review the pending financial commitment. The interface displays the payload, highlighting any compliance flags or cheaper alternatives.
4.  **Decision Execution:** The `Finance Approver (ACT-D0B70FB938)` reviews the payload and either approves or rejects the commitment. If approved, the system proceeds to PO generation. If rejected, the agent logs the reason and may re-evaluate alternatives.

## 6. Sibling Artifact References

*   **Audit Trail:** The specific schema for the audit log is defined in the `Security Architecture Foundations (inception_compliance_security_architecture)` artifact.
*   **UI Components:** The specific UI components for the Confirmation Gate are defined in the `Unified Procurement Vision (inception_whole_product_vision)` artifact.
*   **Operational Constraints:** The latency and integration requirements for the Confirmation Gate are defined in the `Operational Constraints and Integration Requirements (inception_operational_constraints)` artifact.

## 7. Decision Gaps and Knowledge Requirements

The following decisions remain open and require resolution before downstream implementation:

*   **Audit Log Retention Period:** The specific retention period for HITL audit logs is not yet established. This is a compliance-driven decision that must align with HIPAA and organizational policy.
    *   `KNOWLEDGE_GAP: What is the binding retention period for HITL audit logs? - Compliance/Legal authority must establish this before it is treated as settled.`
*   **Cryptographic Signing Standards:** The specific cryptographic standards for signing HITL confirmations are not yet defined. This is a security architecture decision.
    *   `KNOWLEDGE_GAP: What cryptographic signing standards are binding for HITL confirmations? - Security Architecture authority must establish this before it is treated as settled.`

## 8. Follow-Up Questions

*   What retention period is binding for HITL audit logs?
*   What cryptographic signing standards are binding for HITL confirmations?
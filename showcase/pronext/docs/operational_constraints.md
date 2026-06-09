# Operational Constraints and Binding Decisions

## 1. Executive Summary and Scope

This document establishes the binding operational constraints for the ProNext platform. It defines the technical boundaries for AI inference, the compliance posture for data sovereignty, and the operating model for human-in-the-loop financial controls. These constraints are derived directly from the SoftwareDNA product definition and the HIPAA/HITRUST/SOC2 regulatory landscape. This artifact does not define success metrics (owned by `CAP_inception_success_criteria`) or risk registers (owned by `CAP_inception_risk_register`); it defines the non-negotiable boundaries within which those metrics and risks must be managed.

## 2. Data Sovereignty and AI Inference Constraints

### 2.1 Perimeter Enforcement
**Constraint:** All AI inference and model weights must remain strictly within the client infrastructure perimeter.

*   **Rationale:** To guarantee HIPAA compliance and maintain client trust, no Protected Health Information (PHI) or financial data may leave the client's network during AI processing.
*   **Binding Decision:** The platform must utilize a local runtime deployment model for the AI layer. Cloud-based LLM APIs are strictly prohibited for any data containing PHI or PII.
*   **Verification:** Network traffic analysis and AI runtime audit logs must confirm zero egress of sensitive data payloads to external inference endpoints.
*   **Evidence Surface:** `SUR-5E4A75DEE7` (Architectural surface: audit_trail) will capture all inference requests and responses to verify perimeter adherence.

### 2.2 Data Residency and Tenancy
**Constraint:** Multi-tenant architecture must enforce strict logical isolation of data at the storage and compute layers.

*   **Decision Gap:** The specific technical mechanism for tenant isolation (e.g., row-level security vs. schema-per-tenant) is not yet ratified.
*   **Action:** Design phase must specify the isolation model that satisfies HITRUST CSF requirements for logical separation.
*   **Assumption:** Default to row-level security with tenant-ID partitioning unless a higher-priority source dictates schema-per-tenant for regulatory reasons.

## 3. Human-in-the-Loop Financial Controls

### 3.1 Mandatory Confirmation Gate
**Constraint:** A mandatory human-in-the-loop confirmation gate is required before any financial commitment is made by AI agents.

*   **Rationale:** AI agents may autonomously detect low stock, identify compliant vendors, and pre-fill requisitions. However, the final conversion of a requisition to a Purchase Order (PO) requires explicit human authorization.
*   **Binding Decision:** The system must prevent the automatic generation of a PO or the transmission of an order to a vendor without a signed digital confirmation from an authorized role (e.g., `ACT-3435DBDA4A` - Procurement Manager).
*   **Scope:** This applies to all `AgenticProcurementAutomation` flows. The AI may suggest, but the human must commit.
*   **Verification:** System logs must track the transition from `requisition_created` to `po_confirmed` and require a `human_approval_timestamp` and `approver_id`.

### 3.2 Maverick Spend Prevention
**Constraint:** AI must flag cheaper compliant alternatives and prevent maverick spend before order submission.

*   **Rationale:** To enforce GPO contract rates and reduce waste, the system must act as a pre-approval gate, not a post-approval auditor.
*   **Binding Decision:** The ordering interface (`IntelligentOrdering&Catalog`) must block submission of orders that deviate from GPO-negotiated pricing or approved catalog items, unless explicitly overridden by an authorized role with a documented justification.
*   **Verification:** Automated audit trails must compare order line items against active GPO contract rates (`SUR-E34DE4E4A9`).

## 4. Compliance and Audit Architecture

### 4.1 Immutable Audit Trails
**Constraint:** All procurement actions, AI decisions, and human approvals must be recorded in an immutable audit trail.

*   **Rationale:** To satisfy HITRUST and SOC2 requirements for accountability and non-repudiation.
*   **Binding Decision:** The `audit_trail` surface (`SUR-5E4A75DEE7`) must append-only log all state changes in the procurement lifecycle, including:
    *   Requisition creation and modification.
    *   AI agent suggestions and vendor selections.
    *   Human approvals and overrides.
    *   Invoice matching results and variance flags.
*   **Retention:** Data retention periods for audit logs must be defined in accordance with healthcare record-keeping regulations.
*   **Decision Gap:** The specific retention period (e.g., 7 years) is not yet established.
*   **Action:** Legal/Compliance must define the binding retention period for procurement and financial records.

### 4.2 Regulatory Alignment
**Constraint:** The platform must align with HIPAA, HITRUST, and SOC2 frameworks.

*   **Binding Decision:** Security controls must be designed to meet the intersection of these frameworks.
*   **Evidence Surface:** `CAP_inception_compliance_security_architecture` will detail the specific technical controls (encryption, access management) required to satisfy these frameworks.

## 5. Unresolved Strategic Decisions and Gaps

The following decisions must be resolved before the Design phase can finalize technical specifications:

1.  **Supplier Network Integration Depth:** The extent of PunchOut integration (cXML/OCI) for specific vendor catalogs is not yet defined. *Decision Axis:* Which vendor catalogs require PunchOut vs. manual entry?
2.  **Data Residency Requirements:** Specific geographic or jurisdictional data residency requirements for multi-tenant clients are not yet established. *Decision Axis:* Are there specific state or federal mandates requiring data to reside in specific regions?
3.  **Audit Log Retention Period:** The binding retention period for procurement and financial audit logs is not yet defined. *Decision Axis:* What is the legal retention period for healthcare procurement records?

## 6. Traceability and References

*   **SoftwareDNA Product Definition:** Governs AI inference constraints and human-in-the-loop requirements.
*   **System Blueprint Scope:** Defines the procurement platform domain and local runtime deployment.
*   **Asset Registry:**
    *   `ACT-2BACA7884B` (Inventory Manager)
    *   `ACT-3435DBDA4A` (Procurement Manager)
    *   `ACT-F622146FED` (Physician)
    *   `ACT-FB2D634F18` (Auditor)
    *   `JNY-51AEF4D0ED` (InventoryReplenishment)
    *   `JNY-AC859AD751` (PurchaseRequisitionandApproval)
    *   `JNY-C9BBD72EA4` (SpendAnalyticsandForecasting)
    *   `JNY-FA8FB27872` (ComplianceandAudit)
    *   `SUR-5E4A75DEE7` (audit_trail)
    *   `SUR-E34DE4E4A9` (gpo_contract_management)
    *   `CAP_inception_compliance_security_architecture`
    *   `CAP_inception_success_criteria`
    *   `CAP_inception_risk_register`
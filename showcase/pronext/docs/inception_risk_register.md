# Inception Risk Register: ProNext Healthcare Procurement Platform

## 1. Executive Summary
This register captures the strategic, operational, and compliance risks identified during the inception phase for the ProNext AI-native healthcare procurement platform. It focuses on validating the core product assumptions—specifically the unified data model viability, competitive positioning against incumbents, and workflow adoption friction—while explicitly flagging open decisions that must be resolved before the Design phase.

## 2. Strategic & Market Risks

| ID | Risk Description | Impact | Likelihood | Mitigation Strategy | Owner |
|---|---|---|---|---|---|
| STR-001 | Unified Data Model Viability: The assumption that a single data model can seamlessly ingest and normalize data from disparate legacy EHR/ERP systems (e.g., PointClickCare, Meditech, Epic) without significant custom mapping layers. | High | High | Define strict data ingestion contracts per system type. Use the Architectural surface: vendor_integration (inception_whole_product_vision) (SUR-365F106CEF) to standardize API interactions. Gap: Specific mapping complexity for non-standard legacy systems is not yet quantified. | Product Lead |
| STR-002 | Competitive Threat from Incumbents: Legacy competitors (e.g., McKesson, Henry Schein) leveraging existing GPO relationships to bundle AI features, potentially undercutting ProNext's pricing or adoption curve. | Medium | Medium | Emphasize ProNext's "one platform, one login" advantage and superior AI-driven spend forecasting (SUR-AD039605C0) as the differentiator. Focus on post-acute niches underserved by incumbents. | CPO |
| STR-003 | Workflow Adoption Friction: Resistance from Inventory Manager (ACT-2BACA7884B) and Physician (ACT-F622146FED) roles to AI-driven autonomous ordering, perceiving it as a threat to clinical or operational autonomy. | High | Medium | Design the PurchaseRequisitionandApproval journey (JNY-AC859AD751) to be transparent. The HITL gate ensures human oversight. Provide clear "why this recommendation" explanations in the UI. | UX Lead |

## 3. Operational & Governance Risks

| ID | Risk Description | Impact | Likelihood | Mitigation Strategy | Owner |
|---|---|---|---|---|---|
| OPS-001 | HITL Bottleneck: Over-reliance on human approval for every AI-generated requisition could create a bottleneck, slowing down the procurement cycle and reducing the perceived value of automation. | Medium | Medium | Implement tiered approval workflows. Low-value, high-confidence recommendations could be auto-approved after a learning period. Gap: Criteria for "low-value" and "high-confidence" auto-approval are not yet defined. | Ops Lead |
| OPS-002 | Vendor Onboarding Complexity: Difficulty in onboarding new suppliers onto the ProNext platform, especially those without modern API capabilities. | Medium | High | Provide multiple integration methods (API, cXML, OCI, manual upload). Gap: Specific onboarding SLA for new vendors is not yet defined. | Vendor Mgmt |

## 4. Compliance & Security Risks (Residual)

Note: The HIPAA-native perimeter and HITL gates are architectural controls. This section addresses the residual risks that persist despite these controls, avoiding overlap with the Compliance Security Architecture artifact.

| ID | Risk Description | Impact | Likelihood | Mitigation Strategy | Owner |
|---|---|---|---|---|---|
| SEC-001 | Audit Trail Tampering: Although the audit trail (SUR-5E4A75DEE7) is immutable, there is a risk of unauthorized access to the audit logs themselves, potentially covering tracks. | High | Low | Implement strict RBAC for audit log access. Logs must be stored in a separate, highly secured storage bucket. Gap: Specific retention period for audit logs is not yet defined. | Security Lead |
| SEC-002 | Model Weights Exfiltration: Risk of model weights or inference containers being extracted from the client's infrastructure, violating the "local runtime" constraint. | Medium | Low | Enforce strict container isolation and network policies. Gap: Specific encryption standards for model weights at rest are not yet defined. | Security Lead |

## 5. Open Decisions & Knowledge Gaps

The following items are critical blockers for the Design phase and must be resolved:

1. GPO Data Freshness SLA: What is the acceptable latency for GPO contract data updates?
2. Audit Log Retention Period: What is the binding retention period for audit logs to satisfy HITRUST and SOC2 requirements?
3. AI Confidence Threshold: What is the numerical threshold for "low confidence" AI recommendations that require mandatory human review?
4. Auto-Approval Criteria: What are the specific business rules (value, risk score, vendor history) for enabling auto-approval of AI-generated requisitions?

## 6. Cross-Reference to Sibling Artifacts

Compliance Security Architecture: Detailed technical controls for the HIPAA-native perimeter and audit trail immutability are defined in the `Compliance Security Architecture` artifact. This register focuses on the residual risks and strategic implications.
Operational Constraints: Binding decisions regarding deployment models and data residency are defined in the `Operational Constraints` artifact.
Success Criteria: KPIs for measuring the success of the AI-driven procurement workflow are defined in the `Success Criteria` artifact.
# Inception Risk Register: ProNext Healthcare Procurement Platform

## 1. Executive Summary
This artifact defines the strategic, technical, and compliance risk posture for the ProNext AI-native healthcare procurement platform during the Inception Phase. It addresses the core concerns mandated by the project scope: **Model Accuracy and Bias** (CON-95542CBAB2) and **Local Processing Resilience** (CON-F50BC9696D). 

The register prioritizes risks that threaten the platform's foundational value proposition: a unified, HIPAA-native, on-premise procurement system. It explicitly identifies gaps in GPO pricing enforcement logic and the critical human-in-the-loop (HITL) governance required for the `RequisitiontoOrderConversion` journey. Technical implementation details (e.g., specific encryption protocols, SBOM tooling) are deferred to the Security Architecture and Operational Constraints artifacts to maintain phase-appropriate scope.

### R-001 | Data Residency / Exfiltration | AI Inference Data Leakage
**Risk Description:** The risk that patient or financial data (PHI/PII) embedded in procurement prompts or invoice OCR data is transmitted outside the client's on-premise network to external LLM providers or cloud-based APIs, violating HIPAA and the `HIPAA-NativeAIRuntime` constraint.
**Frameworks:** HIPAA (45 CFR 164.312), HITRUST (H1), SOC2 (CC6.1)
**Severity:** Critical
**Control Objective:** Enforce strict network egress filtering at the container level. The `HIPAA-NativeAIRuntime` must operate in an air-gapped or strictly whitelisted mode where outbound API calls to external inference engines are blocked by default. All model weights and inference containers must reside within the client infrastructure perimeter.
**Owner:** System Operator (ACT-0FC1969E12)
**Status:** Open
**Traceability:** SUR-BAFA208216 (data_perimeter)

### R-002 | Auditability & Integrity | Agent Action Log Tampering
**Risk Description:** The risk that the immutable audit trail of AI agent decisions (e.g., PO conversions, invoice matching) is altered, lost, or fails to capture the necessary context for forensic review during a HIPAA or SOC2 audit.
**Frameworks:** HIPAA (164.312(b)), HITRUST (CSF v11), SOC2 (CC7.2)
**Severity:** High
**Control Objective:** Implement append-only, cryptographically signed audit logs for all `RequisitiontoOrderConversion` and `ComplianceDriftReconciliation` events. Logs must capture the exact input data, the AI model version used, the decision output, and the mandatory human-in-the-loop confirmation status.
**Owner:** System Operator (ACT-0FC1969E12)
**Status:** Open
**Traceability:** SUR-D93C62C328 (agent_governance)

### R-003 | Access Control & Segregation | Unauthorized Model Access
**Risk Description:** The risk that a `Procurement Requester` or `Finance Approver` gains access to raw model weights, training data, or the underlying inference container environment, violating the principle of least privilege and data segregation.
**Frameworks:** HIPAA (164.312(a)(1)), HITRUST (CSF v11), SOC2 (CC6.3)
**Severity:** High
**Control Objective:** Enforce strict RBAC where `Procurement Requester` (ACT-FA0309AFC6) and `Finance Approver` (ACT-D0B70FB938) interact only with the UI/API layer. The `System Operator` (ACT-0FC1969E12) is the sole role with access to the underlying container orchestration and model weights.
**Owner:** System Operator (ACT-0FC1969E12)
**Status:** Open
**Traceability:** SUR-BAFA208216 (data_perimeter)

### R-004 | Data Minimization & Retention | Excessive Data Retention in AI Contexts
**Risk Description:** The risk that the LLM runtime caches or retains PHI/PII in temporary inference memory, vector databases, or prompt history beyond the necessary duration for the procurement transaction, violating HIPAA's minimum necessary standard.
**Frameworks:** HIPAA (164.514(b)), HITRUST (H1)
**Severity:** Medium
**Control Objective:** Configure the `HIPAA-NativeAIRuntime` to use ephemeral storage for all inference contexts. Ensure that no PHI is written to persistent logs or vector stores without explicit, audited human-in-the-loop approval and subsequent data masking or deletion.
**Owner:** System Operator (ACT-0FC1969E12)
**Status:** Open
**Traceability:** SUR-BAFA208216 (data_perimeter)

### R-005 | Third-Party & Supply Chain | Open-Source Component Vulnerabilities
**Risk Description:** The risk that open-source libraries used within the locally-containerised LLM services contain unpatched vulnerabilities that could be exploited to bypass the on-premise data perimeter.
**Frameworks:** HITRUST (CSF v11), SOC2 (CC9.1)
**Severity:** Medium
**Control Objective:** Maintain a continuously updated SBOM for all container images. Implement automated vulnerability scanning in the CI/CD pipeline before any container is deployed to the client network.
**Owner:** System Operator (ACT-0FC1969E12)
**Status:** Open
**Traceability:** SUR-BAEC685276 (operational_constraints)

### R-007 | Human-in-the-Loop (HITL) | Financial Commitment Bypass
**Risk Description:** The risk that the `RequisitiontoOrderConversion` journey bypasses the mandatory human-in-the-loop confirmation gate, resulting in unauthorized financial commitments. This directly contradicts the `RequisitiontoOrderConversion` journey definition which requires approval.
**Frameworks:** Internal Business Rule (Mandatory HITL)
**Severity:** Critical
**Control Objective:** The system must enforce a hard stop at the PO conversion stage. No order may be submitted to a supplier without a recorded, cryptographically signed approval from a `Finance Approver` (ACT-D0B70FB938). The `System Operator` (ACT-0FC1969E12) must monitor for any bypass attempts.
**Owner:** System Operator (ACT-0FC1969E12)
**Status:** Open
**Traceability:** JNY-9A5F9E3C00 (RequisitiontoOrderConversion)

### R-008 | Model Accuracy & Bias | Procurement Recommendation Bias
**Risk Description:** The risk that the AI agent exhibits bias in supplier recommendations, favoring certain suppliers over others based on flawed training data or prompt engineering, leading to inequitable procurement practices or compliance violations.
**Frameworks:** CON-95542CBAB2 (Implied concern: Model Accuracy and Bias)
**Severity:** High
**Control Objective:** Implement bias detection mechanisms in the AI agent's decision logs. Regularly audit supplier recommendation patterns for statistical anomalies. Ensure the AI flags cheaper compliant alternatives objectively, without bias toward specific vendor relationships.
**Owner:** System Operator (ACT-0FC1969E12)
**Status:** Open
**Traceability:** CON-95542CBAB2

## 2. Compliance Mapping & Control Objectives

The following table maps the identified risks to the specific control objectives required by the governing frameworks for the ProNext Healthcare Procurement Platform.

| Control Objective | HIPAA Reference | HITRUST Reference | SOC2 Reference | Implementation Note |
|---|---|---|---|---|
| Data in Transit Protection | 164.312(e)(1) | H1 (Data in Transit) | CC6.1 | All internal API calls between the UI, agent layer, and LLM runtime must use mTLS. No external data transit is permitted. |
| Access Control | 164.312(a)(1) | CSF v11 (AC) | CC6.3 | RBAC enforced at the API gateway and container level. `System Operator` (ACT-0FC1969E12) has elevated privileges; `Procurement Requester` (ACT-FA0309AFC6) and `Finance Approver` (ACT-D0B70FB938) are restricted. |
| Audit Controls | 164.312(b) | CSF v11 (AU) | CC7.2 | Immutable logs for all AI decisions, human confirmations, and system access. Logs must be tamper-evident. |
| Integrity Controls | 164.312(c)(1) | CSF v11 (IV) | CC6.1 | Cryptographic hashing of model weights and inference outputs to detect unauthorized modifications. |
| Disaster Recovery | 164.308(a)(7) | CSF v11 (DR) | CC7.1 | On-premise deployment ensures data residency. Backup strategies must be defined for the local container registry and audit logs. |
| GPO Compliance | N/A | N/A | N/A | AI catalog search must enforce GPO pricing rules before order submission. |
| HITL Enforcement | N/A | N/A | N/A | Mandatory approval gate for all PO conversions. |

## 3. Knowledge Gaps & Assumptions

| ID | Type | Description | Impact | Resolution Path |
|---|---|---|---|---|
| KG-001 | Knowledge Gap | Specific data retention period for AI inference logs is not defined. HIPAA does not mandate a specific period for AI logs, but HITRUST requires a defined retention policy. | Affects the design of the immutable logging system (R-002). | Define retention period in `inception_operational_constraints` or `inception_compliance_security_architecture`. |
| KG-002 | Knowledge Gap | Exact network egress rules for the client's on-premise environment are not specified. | Affects the feasibility of the air-gapped runtime (R-001). | Consult with client IT security team to define allowed egress paths (if any). |
| KG-003 | Knowledge Gap | Specific bias detection metrics and thresholds for the AI agent are not defined. | Affects the design of the bias monitoring system (R-008). | Define bias metrics in `inception_compliance_security_architecture_agent_governance`. |
| ASS-001 | Assumption | The `HIPAA-NativeAIRuntime` is assumed to be fully isolated from the public internet. | If this assumption is false, R-001 becomes a critical, unmitigated risk. | Validate network architecture with client infrastructure team. |
| ASS-002 | Assumption | GPO contract data is assumed to be available in a structured format for AI ingestion at go-live. | If this assumption is false, R-006 (GPO Pricing Enforcement) cannot be implemented as designed. | Confirm data availability with GPO partners during inception. |

## 4. Sibling Artifact References

- **Data Perimeter and AI Inference Constraints:** This artifact's R-001 (Data Residency / Exfiltration) defers to `inception_compliance_security_architecture_data_perimeter` for the detailed technical implementation of the network egress filtering and container isolation. See that artifact for the full treatment.
- **Agent Governance and Human-in-the-Loop Confirmation:** This artifact's R-002 (Agent Action Log Tampering) and R-007 (HITL Bypass) defer to `inception_compliance_security_architecture_agent_governance` for the detailed workflow of the mandatory human-in-the-loop confirmation gate. See that artifact for the full treatment.
- **Operational Constraints and Integration Requirements:** This artifact's R-005 (Open-Source Component Vulnerabilities) and R-006 (GPO Pricing Enforcement) defer to `inception_operational_constraints` for the detailed integration requirements and SBOM management processes. See that artifact for the full treatment.

## 5. Conclusion

The ProNext Healthcare Procurement Platform's compliance posture is heavily dependent on the strict enforcement of the `HIPAA-NativeAIRuntime` constraint and the mandatory human-in-the-loop governance. The primary risks revolve around data exfiltration, auditability, access control, and GPO pricing compliance. By implementing structural guarantees such as air-gapped inference, immutable logging, strict RBAC, and explicit GPO enforcement, ProNext can mitigate these risks and meet the requirements of HIPAA, HITRUST, and SOC2 Type II. The identified knowledge gaps must be resolved in the subsequent design phase to finalize the control objectives.
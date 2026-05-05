# Persona Definitions for Intake System (Overview)

## Persona Definitions for Patient Intake System (Overview)

The following personas capture the primary human actors who will interact with the PatientIntake system. They are derived directly from the project requirements (collect demographics, secure storage, audit logging, PDF export) and the stakeholder list (ST-01 Clinical staff, ST-02 Patients, ST-03 Compliance officer). Each persona includes role‑specific goals, motivations, constraints, and security considerations that inform downstream design and testing.

### PER-02: Front‑Desk Staff (Receptionist / Registration Clerk)
1. **Role Summary**: Administrative personnel responsible for initial patient registration, data entry of demographics and insurance details, and initiating PDF intake summaries for authorized staff.
2. **Primary Goals**
   - Accurately enter required fields with validation feedback to reduce data entry errors (<1 % error rate – KPI-004).
   - Generate a PDF intake summary that includes a watermark identifying the staff member and an access timestamp (FR‑005).
   - Initiate audit log entries for every create/read/write operation (AU‑6).
3. **Motivations**
   - Minimize re‑work caused by incomplete or incorrect submissions.
   - Demonstrate compliance during internal audits.
4. **Constraints**
   - Operates on shared terminals with limited privileges; cannot view clinical notes beyond what is required for registration.
   - Must follow a documented air‑gap setup guide; no external internet connectivity.
   - Uses field‑level encryption keys managed by the system; does not handle raw keys.
   - Session timeout after 10 minutes of inactivity to mitigate shoulder‑surfing risk.
   - Handling of validation failures (e.g., missing insurance number) must provide inline guidance without exposing PHI.
   - Need assurance that generated PDFs cannot be altered after export; watermark and timestamp must be immutable.
5. **Security Considerations**
   - Authentication via unique staff ID; MFA enforced per 45 CFR 164.312(a)(2)(iv).
   - All actions logged immutably (AU‑6) with hash chaining for integrity.

### PER-03: Compliance Officer (Auditor / HIPAA Officer)
1. **Role Summary**: Oversees regulatory compliance, conducts periodic audits of the intake system, and validates that security controls meet HIPAA technical safeguard requirements.
2. **Primary Goals**
   - Verify that every read/write operation is recorded in an immutable audit log (FR‑003, NFR‑003).
   - Confirm that field‑level encryption is applied consistently across all PHI fields (NFR‑001).
   - Review PDF export logs to ensure watermarks and timestamps are present for each export (FR‑005).
3. **Motivations**
   - Avoid penalties from non‑compliance; maintain organization’s certification status.
   - Provide evidence of compliance during external audits.
4. **Constraints**
   - Access limited to read‑only views of audit logs; cannot modify patient data.
   - Must operate within an air‑gapped environment; all audit data stored locally on PostgreSQL with row‑level security.
   - Requires multi‑factor authentication for login (45 CFR 164.312(a)(2)(iv)).
   - Audit log retention period of 7 years as per HIPAA retention policy.
   - Needs tooling to filter audit logs by user ID, operation type, and date range without exporting raw data.
5. **Security Considerations**
   - MFA enforced; session logs signed with digital signatures.
   - Log integrity checks (hash chaining) verifiable during audits.

---

### Personas Table
| Persona ID | Role | Description | Primary Needs | Constraints |
|-----------|------|-------------|----------------|--------------|
| PER-01 | Clinical Staff | Nurse / Clinician reviewing intake data | Reliable access to complete, accurate intake summary; assurance of data integrity and provenance | Works on secured workstations; role‑based access only |
| PER-02 | Front Desk Staff | Receptionist initiating registration | Fast data entry, validation assistance, ability to correct errors quickly | Cannot view full medical history; air‑gap environment |
| PER-03 | Compliance Officer | Auditor ensuring HIPAA compliance | Ability to query immutable audit logs, verify encryption compliance, generate compliance reports | Read‑only audit view; MFA required |
| PER-04 | Patient | Individual receiving care who provides personal and medical information via the web form | Simple and accessible UI, immediate feedback on submission status, privacy of health data | May use mobile device, limited technical expertise |

---

## User Stories

| Story ID | Actor | Goal | Acceptance Criteria Reference |
|----------|-------|------|-------------------------------|
| US-001 | Front Desk Staff | Capture patient demographics, insurance information, and medical history via a structured web form with field‑level encryption at rest and in transit | AC-001 |
| US-002 | Clinician | View a PDF intake summary for a patient that includes a watermark and an access timestamp | AC-002 |
| US-003 | Compliance Officer | Audit the operation log for every read and write operation on patient records | AC-003 |

---

## Acceptance Criteria

| AC ID | Story ID | Given | When | Then |
|-------|----------|-------|------|------|
| AC-001 | US-001 | The front‑desk staff member is authenticated via MFA and has an active session on a secured terminal. | They complete the web form with all mandatory fields filled correctly and submit it. | The system stores the data encrypted at rest and in transit, creates an immutable audit log entry (AU‑6) with user ID, timestamp, and operation type, and displays a success message within 2 seconds (KPI-001). |
| AC-002 | US-002 | The clinician is logged in with appropriate role‑based permissions and selects a patient record that has a completed intake form. | They request to generate the PDF intake summary. | The system produces a PDF that includes a visible watermark containing the clinician’s name and an access timestamp, stores the PDF securely, logs the generation event immutably (AU‑6), and the PDF cannot be altered without detection (NFR‑003). |
| AC-003 | US-003 | The compliance officer has read‑only access to the audit log database in the air‑gapped environment. | They apply a filter for a specific date range or user ID and request the audit report. | The system returns a filtered list of audit entries showing user ID, operation type, timestamp, and cryptographic hash chain verification passes; the report respects the 7‑year retention policy (NFR‑003) and no raw PHI is exposed. |

---

*All functional references map to existing asset IDs:* FR‑001 (Secure demographic capture), FR‑002 (Insurance verification), FR‑003 (Immutable audit logging), FR‑005 (PDF generation with watermark), NFR‑001 (Encryption at rest & transit), NFR‑003 (Audit log integrity), KPI-001 (Form submission response time <200 ms), KPI-004 (Data entry error rate <1 %).

{'status': 'error', 'error': 'All micro-goals failed', 'failed_micro_goals': [{'status': 'error', 'error': "Refiner specialized logic failed: Template rendering failed due to undefined variable: 'watermark' is undefined. This indicates a system error where required context variables were not set. Available context keys: ['artifact_name', 'artifact_description', 'artifact_id', 'dbs_id', 'artifact_type', 'role', 'agent_role', 'phase_name', 'artifact_dependencies', 'forward_dependents', 'project_requirement_text', 'project_requirement_full', 'requirement_text', 'context_summary', 'project_id', 'goal', 'total_micro_goals', 'micro_goal_index', 'acceptance_criteria', 'binding_manifest', 'micro_goal', 'micro_goal_axis', 'micro_goal_level', 'micro_goal_parent_id', 'reasoning_summary', 'artifact_definition', 'dbs_item', 'cipher_context', 'episodic_patterns', 'software_dna_context', 'existing_artifacts', 'existing_artifacts_summary', 'sibling_artifacts', 'decomposer_artifact_ids_so_far', 'decomposer_cot_commitment', 'previous_phase_artifacts', 'jigsaw_map', 'coordinated_insights', 'coordination_available', 'domain_knowledge_context', 'research_context', 'vp_feedback', 'vp_primary_gaps', 'task_context', 'multi_turn_instruction', 'content_to_refine', 'reviewer_feedback', 'executor_output', 'original_output', 'peer_reviews', 'refinement_context_mode', 'refinement_segment_index', 'refinement_segment_total', 'current_agent_role', 'templates', 'contracts', 'technology_stack', 'chain_of_thought_context', 'reasoning_for_current_goal', 'decomposition_reasoning_context', 'executor_reasoning_digest', 'executor_self_critique', '_stage_context', 'previous_phase_learnings', 'previous_phase_context', 'pipeline_conductor_context', 'pipeline_conductor_hint', 'pipeline_conductor_focus_artifacts', 'pipeline_conductor_metadata', 'decomposition_retry_delta_block', 'generated_content', 'artifact_content', 'content', 'previous_output', 'content_to_review', 'reviewer_feedback_markdown', 'refined_outputs_markdown', 'executor_inputs_markdown', 'micro_goal_context', 'dna_insights', 'previous_phase_dna', 'dna_domain_concepts', 'consolidation_manifest', 'completed_sections', 'sections_already_produced', 'project_grounding_facts', 'project_grounding_summary', 'context_tier', 'include_methodology_deep', 'stage_name', 'jigsaw_universal_contract', '_cbr_reference_metadata', 'phase_prompt_preamble', 'artifact_prompt_delta', 'phase_prompt_scope_id', 'content_to_approve', 'episodic_patterns_summary', 'pass_name', 'reflection_critique_summary', 'task_description', 'focus_area', 'research_reasoning', 'research_results', 'results_count', 'results_used', 'existing_knowledge_summary', 'project_context', 'project_description', 'project_domain', 'artifact_summary', 'tech_stack', 'query_analysis', 'query_type', 'level_1_relevance', 'level_1_results_count', 'level_2_relevance', 'level_2_results_count', 'next_level', 'purpose', 'requirement', 'sequence_number', 'source', 'total_goals', 'context', 'phase', 'context_keys', 'phase_key', 'quality_criteria', 'quality_score', 'execution_content', 'dependencies', 'success_criteria', 'phase_blueprint', 'description_one_line', 'goal_id', 'micro_goal_description', 'role_specific_field', 'role_specific_field_description', 'required_item_fields', 'output_content', 'content_size', 'context_ref_id', 'ref_id', 'ref_type', 'relevance_score', 'summary', 'codebase_content', 'codebase_chunk', 'codebase_sample', 'entities_to_analyze', 'extracted_dna', 'relational_context', 'structural_context', 'behavioral_context', 'architectural_context', 'filename', 'document_type', 'document_path', 'content_preview', 'diagram_type', 'flow_type', 'new_content', 'old_content', 'extraction_results', 'ingested_documents', 'content_to_classify', 'artifacts', 'reasoning_scaffold']. This should trigger self-correction to retry with proper context.. No code fallback.", 'goal_index': 0}]}

# Patient Intake System – Feature Specification (Refined)

## Overview
This document defines the user‑value artefacts for the **Patient Intake** SaaS product. It captures personas, user stories, acceptance criteria, and priority rationale that are directly traceable to the functional requirements (FR‑001 – FR‑004) and compliance obligations (HIPAA, SOC 2). All artefacts are written for a multi‑tenant cloud deployment.

### US‑001 – Expired Encryption Key Handling
**Requirement ID:** FR‑001
**Description:** When a field‑level encryption key reaches its rotation date, decryption attempts must fail with a clear error and trigger admin notification.

**Acceptance Criteria**
- **Given** a patient form contains data encrypted with a key whose rotation date has passed,
- **When** the system attempts to decrypt the field,
- **Then** the operation returns a `KeyRotationRequired` error,
- **And** an email/notification is sent to the system administrator with details of the affected key and instructions to rotate it,
- **And** new submissions are rejected until the key is rotated.

### US‑002 – Data Validation on Expired Key
**Requirement ID:** FR‑002
**Description:** Prevent submission of records that would be encrypted with an expired key.

**Acceptance Criteria**
- **Given** a user fills out the intake form,
- **When** they attempt to submit and the underlying encryption key is expired,
- **Then** the UI displays an inline validation message "Encryption key expired – contact admin",
- **And** the submission is blocked.

### US‑003 – Concurrent Edit Conflict Detection
**Requirement ID:** FR‑003
**Description:** Detect simultaneous edits of the same patient record and present a conflict resolution dialog.

**Acceptance Criteria**
- **Given** two front‑desk users load the same patient record version `v1`,
- **When** User A saves changes creating version `v2` and User B subsequently attempts to save their edits based on `v1`,
- **Then** optimistic locking detects the version mismatch,
- **And** a conflict dialog shows both versions side‑by‑side,
- **And** the user can choose to merge or overwrite.

### US‑004 – PDF Export Access Control
**Requirement ID:** FR‑004
**Description:** Restrict PDF export functionality to authorized roles and log unauthorized attempts.

**Acceptance Criteria**
- **Given** a front‑desk user with role `staff` views a patient record,
- **When** they click the "Export PDF" button,
- **Then** the button is disabled (grayed out) per RBAC policy,
- **And** any attempt to invoke the export endpoint results in an `UnauthorizedAccess` audit event recorded with timestamp, user ID, and patient ID.

## Priority Rationale
| Priority | User Story(s) | Rationale |
|----------|----------------|----------|
| **High (1)** | US‑001, US‑003, US‑004 | Directly enforce HIPAA technical safeguards (encryption key management, audit logging, access control). Mandatory for compliance certification. |
| **Medium (2)** | US‑002 | Improves data quality and operational efficiency but does not affect core security posture. |

## Traceability Matrix
| User Story | Functional Requirement | KPI | Risk Mitigated |
|-------------|--------------------------|-----|----------------|
| US‑001 | FR‑001 | KPI-004 (PDF export security compliance) | RISK-001 (Unauthorized data exposure) |
| US‑002 | FR‑002 | KPI-005 (Test coverage targets) | RISK-002 (Open‑source component vulnerabilities) |
| US‑003 | FR‑003 | KPI-003 (Successful audit log generation) | RISK-003 (Deployment misconfiguration) |
| US‑004 | FR‑004 | KPI-002 (System availability) | RISK-001 (Unauthorized data exposure) |
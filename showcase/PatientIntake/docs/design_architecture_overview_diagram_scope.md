# System Architecture Diagram and Description

{'status': 'error', 'error': 'All micro-goals failed', 'failed_micro_goals': [{'status': 'error', 'error': "Refiner specialized logic failed: Template rendering failed due to undefined variable: 'username' is undefined. This indicates a system error where required context variables were not set. Available context keys: ['artifact_name', 'artifact_description', 'artifact_id', 'dbs_id', 'artifact_type', 'role', 'agent_role', 'phase_name', 'artifact_dependencies', 'forward_dependents', 'project_requirement_text', 'project_requirement_full', 'requirement_text', 'context_summary', 'project_id', 'goal', 'total_micro_goals', 'micro_goal_index', 'acceptance_criteria', 'binding_manifest', 'micro_goal', 'micro_goal_axis', 'micro_goal_level', 'micro_goal_parent_id', 'reasoning_summary', 'artifact_definition', 'dbs_item', 'cipher_context', 'episodic_patterns', 'software_dna_context', 'existing_artifacts', 'existing_artifacts_summary', 'sibling_artifacts', 'decomposer_artifact_ids_so_far', 'decomposer_cot_commitment', 'previous_phase_artifacts', 'jigsaw_map', 'coordinated_insights', 'coordination_available', 'domain_knowledge_context', 'research_context', 'vp_feedback', 'vp_primary_gaps', 'task_context', 'multi_turn_instruction', 'content_to_refine', 'reviewer_feedback', 'executor_output', 'original_output', 'peer_reviews', 'refinement_context_mode', 'refinement_segment_index', 'refinement_segment_total', 'current_agent_role', 'templates', 'contracts', 'technology_stack', 'chain_of_thought_context', 'reasoning_for_current_goal', 'decomposition_reasoning_context', 'executor_reasoning_digest', 'executor_self_critique', '_stage_context', 'previous_phase_learnings', 'previous_phase_context', 'pipeline_conductor_context', 'pipeline_conductor_hint', 'pipeline_conductor_focus_artifacts', 'pipeline_conductor_metadata', 'decomposition_retry_delta_block', 'generated_content', 'artifact_content', 'content', 'previous_output', 'content_to_review', 'reviewer_feedback_markdown', 'refined_outputs_markdown', 'executor_inputs_markdown', 'micro_goal_context', 'dna_insights', 'previous_phase_dna', 'dna_domain_concepts', 'consolidation_manifest', 'completed_sections', 'sections_already_produced', 'project_grounding_facts', 'project_grounding_summary', 'context_tier', 'include_methodology_deep', 'stage_name', 'jigsaw_universal_contract', '_cbr_reference_metadata', 'phase_prompt_preamble', 'artifact_prompt_delta', 'phase_prompt_scope_id', 'content_to_approve', 'episodic_patterns_summary', 'pass_name', 'reflection_critique_summary', 'task_description', 'focus_area', 'research_reasoning', 'research_results', 'results_count', 'results_used', 'existing_knowledge_summary', 'project_context', 'project_description', 'project_domain', 'artifact_summary', 'tech_stack', 'query_analysis', 'query_type', 'level_1_relevance', 'level_1_results_count', 'level_2_relevance', 'level_2_results_count', 'next_level', 'purpose', 'requirement', 'sequence_number', 'source', 'total_goals', 'context', 'phase', 'context_keys', 'phase_key', 'quality_criteria', 'quality_score', 'execution_content', 'dependencies', 'success_criteria', 'phase_blueprint', 'description_one_line', 'goal_id', 'micro_goal_description', 'role_specific_field', 'role_specific_field_description', 'required_item_fields', 'output_content', 'content_size', 'context_ref_id', 'ref_id', 'ref_type', 'relevance_score', 'summary', 'codebase_content', 'codebase_chunk', 'codebase_sample', 'entities_to_analyze', 'extracted_dna', 'relational_context', 'structural_context', 'behavioral_context', 'architectural_context', 'filename', 'document_type', 'document_path', 'content_preview', 'diagram_type', 'flow_type', 'new_content', 'old_content', 'extraction_results', 'ingested_documents', 'content_to_classify', 'artifacts', 'reasoning_scaffold']. This should trigger self-correction to retry with proper context.. No code fallback.", 'goal_index': 0}]}

## Overview
This document defines the concrete RESTful contracts that the **Intake Service** (SVC‑001) must expose to satisfy functional requirements **FR‑001 – FR‑003** and non‑functional requirements **NFR‑001 – NFR‑003**. All endpoints are secured with TLS 1.3 (as mandated by the global `tls_version` setting) and require a Bearer JWT token that encodes the user role (admin, clinician, front‑desk). Field‑level encryption is performed client‑side for PHI fields; the server stores only ciphertext blobs.

## API Endpoints

### 1. `POST /api/v1/intake` – Create a new patient intake record (FR‑001)
**Request Schema**
| Field | Type | Required | Description |
|---|---|---|---|
| patient_id | string (UUID) | Yes | Unique identifier of the patient in the master patient index |
| demographics.first_name | string | Yes | Patient's given name |
| demographics.last_name | string | Yes | Patient's family name |
| demographics.dob | string (date) | Yes | Date of birth (ISO‑8601) |
| demographics.ssn_encrypted | string (base64) | Yes | SSN encrypted client‑side |
| demographics.address_encrypted | string (base64) | Yes | Address encrypted client‑side |
| insurance.provider | string | Yes | Insurance carrier name |
| insurance.policy_number_encrypted | string (base64) | Yes | Policy number encrypted client‑side |
| medical_history_encrypted | string (base64) | Yes | Full medical history encrypted client‑side |

**Response Schema**
| Field | Type | Description |
|---|---|---|
| record_id | string (UUID) | Identifier of the newly created intake record |
| status | string | Fixed value `created` |
| created_at | string (datetime, ISO‑8601) | Timestamp of creation |

**Security / RBAC**: Requires role `admin` or `front‑desk`.

### 3. `POST /api/v1/intake/{record_id}/pdf` – Generate and download a PDF summary (FR‑003)
**Request Schema**
| Field | Type | Required | Description |
|---|---|---|---|
| watermark_text | string | Yes | Text to appear as watermark on each PDF page |
| include_timestamp | boolean | Yes | Whether to embed generation timestamp |

**Response Schema**
| Field | Type | Description |
|---|---|---|
| pdf_url | string (URL) | Pre‑signed URL where the generated PDF can be downloaded |
| expires_at | string (datetime) | Expiration time of the URL (default 15 min) |

**Failure Handling**: Propagates `ERR-PDFGEN` (HTTP 502). On service unavailability, request is queued for asynchronous processing.

## Error Taxonomy (ERR‑001)
| Error Code   | HTTP Status | Description                                            | User Message                                                                                 | Retryable |
|--------------|-------------|--------------------------------------------------------|----------------------------------------------------------------------------------------------|-----------|
| ERR‑VALIDATION   | 400         | Request payload failed schema validation               | "The submitted data is invalid or missing required fields."                                 | |
| ERR‑AUTH         | 401         | Missing or invalid JWT token                           | "Authentication required. Please log in again."                                            | |
| | | | "Token expired – re‑authenticate."                                                       | |
| ERR‑FORBIDDEN   | 403         | | "You do not have permission to perform this action."                                    | |
| ERR‑NOTFOUND    | 404         | | "The requested intake record could not be found."                                      | |
| ERR‑ENCRYPTION  | 500         | | "A system error occurred while processing protected data. Please contact support."    | |
| ERR‑PDFGEN      | 502         | | "Unable to generate PDF at this time. Please retry later."                            | |

*Retryable column indicates whether the client should automatically retry after exponential back‑off.*

## Integration Points & Failure Handling
a) **Key Management Service (KMS)** – Public key retrieval endpoint (`/kms/public`). If KMS unreachable, service returns **ERR‑ENCRYPTION** with HTTP 503; client must retry with exponential back‑off.
b) **PDF Generation Service** – Internal container `pdf-generator` exposing `/generate`. Non‑200 responses are mapped to **ERR‑PDFGEN**; fallback queues request for later processing.
c) **PostgreSQL Database** – Local container `postgres:13-alpine`. On connection loss, service returns **ERR‑DBUNAVAILABLE** (HTTP 503); automatic retry logic attempts up to three times before bubbling error.
d) **Authentication Service** – `/api/v1/auth/login`. Invalid credentials → **ERR‑AUTH`; token expiration → **ERR‑AUTH`; service down → **ERR‑AUTH` with HTTP 503.

## Service Boundaries
| Service               | Responsibility                                          | External Dependencies                         |
|-----------------------|----------------------------------------------------------|-|
| Intake Service (SVC‑001)   | Handles CRUD of intake records |
- Orchestrates PDF generation
- Emits domain events (`IntakeCreated`, `IntakeUpdated`, `IntakeDeleted`, `PdfGenerated`)
- Performs RBAC enforcement
- Writes audit entries via Audit Log Service| PostgreSQL DB
- PDF Generator Service
- Audit Log Service\																|	|	|	|	|	|	|	|	|	|	|	|	|	|	|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	-	ttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt
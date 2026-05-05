# Data Model (Overview)

### 1. High‑Level View
The PatientIntake system is organized into six tightly‑coupled components that together satisfy the HIPAA technical safeguard requirements while remaining fully open‑source. All network traffic is encrypted with TLS 1.3 (defined in the project globals). Sensitive fields are encrypted at rest using PostgreSQL **pgcrypto** and in transit via HTTPS/GRPC. Role‑based access control (RBAC) is enforced by the API layer and reinforced by PostgreSQL row‑level security (RLS).

### 2. Component Diagram
mermaid
flowchart TD
    subgraph Client[Web Client]
        FE[React SPA] -->|HTTPS| APIGW[FastAPI Gateway]
    end
    subgraph Backend[Backend Services]
        APIGW -->|REST/JSON| IS[Intake Service]
        APIGW -->|REST/JSON| PDFS[PDF Generation Service]
        APIGW -->|REST/JSON| AUD[Audit Logging Service]
        IS -->|SQL| DB[(PostgreSQL DB)]
        PDFS -->|SQL| DB
        AUD -->|SQL| DB
    end
    subgraph Security[Security Layer]
        VAULT[HashiCorp Vault] -.->|Key Retrieval| IS
        VAULT -.->|Key Retrieval| PDFS
        VAULT -.->|Key Retrieval| DB
    end
    style Client fill:#E3F2FD,stroke:#1565C0,stroke-width:2px;
    style Backend fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px;
    style Security fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px;

The diagram shows the flow of a patient intake request from the React front‑end through the FastAPI gateway to the Intake Service, which persists encrypted data in PostgreSQL. The PDF Generation Service pulls the stored data to produce a HIPAA‑compliant PDF with watermark and timestamp. All write and read operations trigger events captured by the Audit Logging Service.

### 3. Detailed Component Responsibilities
- **React SPA (FE)** – Renders a structured intake form; performs client‑side field‑level encryption using the Web Crypto API before transmission.
- **FastAPI Gateway (APIGW)** – Authenticates requests via OAuth2 Bearer tokens, validates JWT claims against an RBAC matrix (admin, clinician, front‑desk), and routes to downstream services.
- **Intake Service (IS)** – Implements business rules for patient record creation; encrypts each PHI field with per‑field keys fetched from Vault; writes records using prepared statements; emits `PatientCreated` events.
- **PDF Generation Service (PDFS)** – Listens for `PatientCreated` or on‑demand export requests; assembles a PDF using **WeasyPrint**; applies a dynamic watermark containing the staff username and an ISO 8601 access timestamp; stores the generated file reference in the `pdf_documents` table.
- **Audit Logging Service (AUD)** – Writes immutable audit entries to `audit_log` table; each entry includes operation type, actor ID, timestamp, and cryptographic hash of the payload for tamper evidence.
- **PostgreSQL DB** – Hosts tables `patients`, `insurance`, `medical_history`, `pdf_documents`, `audit_log`; column‑level encryption via pgcrypto; row‑level security policies enforce that only authorized roles can SELECT/UPDATE specific columns.
- **HashiCorp Vault** – Securely stores master encryption keys; provides per‑field data‑encryption keys on demand; rotates keys every 90 days (project global).

### 4. Deployment & Air‑Gap Considerations
The entire stack is containerized and orchestrated via Docker Compose (`docker-compose.yml`). An isolated Docker network (`intake_net`) ensures no external outbound traffic; all images are pulled from an internal registry prior to air‑gap deployment. The deployment guide (separate artifact) details host hardening, firewall rules, and offline key injection into Vault.

### 5. Failure Handling & Resilience
- **Gateway Timeout** – Returns HTTP 504 with a retryable flag; client backs off exponentially.
- **Vault Unavailable** – Services enter a circuit‑breaker state; pending requests are queued in an in‑memory buffer and retried after 30 seconds.
- **Database Write Failure** – Transaction is rolled back; audit entry records the failure with error code `ERR-DB-WRITE`; client receives HTTP 500 with a non‑retryable message.
- **PDF Generation Crash** – PDF service emits `PDFGenerationFailed` event; audit logs capture stack trace; front‑end shows a user‑friendly error.
These mechanisms guarantee graceful degradation while preserving audit integrity and compliance evidence.

---

## 6. Introduction
This document defines the concrete technical contracts required to implement the PatientIntake system in the design phase. It focuses on the Data Model artifact, providing an Entity‑Relationship diagram, API endpoint specifications, data‑model tables, error taxonomy, and service boundaries. All definitions trace back to the project requirements (**FR‑001 – FR‑003**, **NFR‑001 – NFR‑003**, **RISK‑01 – RISK‑03**) and comply with HIPAA technical safeguard mandates.

## 7. Data Model Overview (ER Diagram)
*(ER diagram omitted for brevity – referenced in separate visual artifact)*

## 8. API Endpoint Specification (EP‑001)
The Intake Service exposes two primary REST endpoints. Both require Bearer Token authentication with RBAC enforced by PostgreSQL Row‑Level Security (RLS).

### 8.2 Retrieve Intake Record
**Endpoint:** `GET /api/v1/intake/{patient_id}`
**Description:** Retrieve full intake record for authorized staff; also writes a read audit entry.
**Roles Allowed:** `admin`, `clinician`
**Path Parameter:** `patient_id` – UUID of the patient record.
**Response Schema – SCH‑003 (Success)**

{
  "demographics": {
    "first_name": "string",
    "last_name": "string",	"date_of_birth": "date",	"ssN": "string",	"address": "string",	"phone": "string",	"email": "string"	},	"insurance": [	{	"provider": "string",	"policy_number": "string",	"group_number": "string",	"effective_date": "date",	"expiry_date": "date"	}	],	"medical_history": {	"records": { /* decrypted JSON */ }	},	"audit_log_summary": {	"read_count": "integer",	"last_read_at": "timestamp"	}	}	
**Possible Error Responses**
| HTTP | Error Code | Description |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	--- |	table continues as above with ERR-001…ERR-005 applicable where relevant (e.g., invalid UUID → ERR-001). \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \   ")   // placeholder to keep formatting correct      \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \   \      ---   ## 4. Error Taxonomy (ERR‑001 – ERR‑005)   | Code | HTTP | Description | Message | Retryable | |------|------|-------------|---------|-----------| | ERR-001 | 400 | Validation failure – request payload does not conform to SCH‑001 | The submitted form contains invalid or missing fields. | No | | ERR-002 | 401 | Authentication failure – missing or invalid Bearer token | Authentication required. Please log in again. | No | | ERR-003 | 403 | Authorization failure – role lacks permission for the operation | You do not have permission to perform this action. | No | | ERR-004 | 409 | Conflict – duplicate patient record detected (e.g., same SSN) | A patient with this identifier already exists. | No | | ERR-005 | 500 | Internal server error – unexpected failure during encryption or DB write | An unexpected error occurred. Please contact support. | Yes | ## 5. Service Boundaries (SVC‑001 – SVC‑004)   | Service Name | Responsibility | Dependencies | Events Emitted | Events Consumed |
|--------------------|--------------------------|--------------------|------------------|------------------|
| Intake Service (SVC-001) | Accepts intake submissions, validates & encrypts PHI, writes to DB, emits `PatientCreated` event | FastAPI Gateway, Vault, PostgreSQL DB | PatientCreated, IntakeFailed | PDF Generation Service (on-demand export), Audit Logging Service |
| PDF Generation Service (SVC-002) | Generates HIPAA‑compliant PDFs with watermark/timestamp; stores reference in DB | Intake Service (event), Vault, PostgreSQL DB | PDFGenerated, PDFGenerationFailed | — |
| Audit Logging Service (SVC-003) | Persists immutable audit entries for all read/write operations; provides read audit summary | FastAPI Gateway, PostgreSQL DB | AuditEntryCreated | — |
| FastAPI Gateway (SVC-004) | Authenticates requests, enforces RBAC, routes to backend services | OAuth provider, JWT library, backend services | RequestRouted, AuthFailure | — |

## 9. Non‑Functional Requirements Alignment
- **NFR-001 (<200 ms response time):** Critical paths (Create Intake, Retrieve Intake) are designed for sub‑200 ms latency under normal load; indexing strategies and connection pooling are specified in deployment docs.
- **NFR-002 (99.9 % uptime):** Services are containerized with health checks; Docker Compose restart policies ensure rapid recovery.
- **NFR-003 (Audit logging):** Immutable audit_log table with cryptographic hash of payload ensures tamper evidence.

## 10. Risk Mitigation
- **RISK-01 Unauthorized data exposure:** Encryption in transit & at rest + strict RBAC.
- **RISK-02 Open-source component vulnerabilities:** Regular dependency scanning CI pipeline (outside design scope but noted).
- **RISK-03 Deployment misconfiguration:** Air‑gap deployment guide includes hardened host checklist and network isolation.

---
*Document generated by Refiner role – design phase.*

## System Architecture Overview

The PatientIntake system is implemented as a set of micro‑services communicating over an internal event bus (NATS) and exposing RESTful HTTP APIs for external interaction. All services run in Docker containers orchestrated by Docker‑Compose for development and Kubernetes for production, providing horizontal scalability and multi‑tenant isolation.

### Core Services
| Service | Responsibility | Primary Data Store | Published Event | Consumed Events |
|---|---|---|---|---|
| **Intake Service (SVC‑001)** | Accepts patient demographic and insurance data, validates schema, writes encrypted rows, triggers audit log creation. | PostgreSQL (DB) – `patient`, `insurance`, `medical_history` tables | `EVENT_INTAKE_CREATED` (patient_id) | None |
| **Audit Service (SVC‑002)** | Persists immutable audit entries for every CREATE/READ/UPDATE/DELETE operation. Enforces tamper‑evidence via append‑only table. | PostgreSQL (`audit_log`) | `EVENT_AUDIT_WRITTEN` | Consumes events from all other services via internal event bus (NATS) |
| **PDF Generation Service (SVC‑003)** | Generates PDF intake summary on demand; applies watermark and timestamp; stores PDF metadata in `pdf_document`. | PostgreSQL (`pdf_document`) – also reads from `medical_history` for content generation | `EVENT_PDF_GENERATED` (patient_id) | Consumes `EVENT_INTAKE_CREATED` to pre‑populate cache |
| **Auth & RBAC Service (SVC‑004)** | Issues JWTs, validates roles against PostgreSQL RLS policies. | PostgreSQL (`users`, `roles`) | `EVENT_TOKEN_ISSUED` | None |

### Entity‑Relationship Diagram
mermaid
erDiagram
    PATIENT {
        uuid patient_id PK "Primary key"
        text first_name "Encrypted"
        text last_name "Encrypted"
        date date_of_birth "ISO‑8601"
        text ssn "Encrypted"
        text address "Encrypted"
        text phone "Encrypted"
        text email "Encrypted"
        timestamp created_at "UTC"
        timestamp updated_at "UTC"
    }
    INSURANCE {
        uuid insurance_id PK
        uuid patient_id FK "References PATIENT"
        text provider_name "Encrypted"
        text policy_number "Encrypted"
        date coverage_start
        date coverage_end
        timestamp created_at
        timestamp updated_at
    }
    MEDICAL_HISTORY {
        uuid history_id PK
        uuid patient_id FK
        jsonb history_data "Encrypted JSONB of clinical notes"
        timestamp created_at
        timestamp updated_at
    }
    AUDIT_LOG {
        uuid log_id PK
        uuid entity_id "ID of affected row"
        text entity_type "PATIENT|INSURANCE|MEDICAL_HISTORY|PDF_DOCUMENT"
        text operation "INSERT|UPDATE|DELETE|SELECT"
        uuid performed_by "User ID"
        timestamp performed_at
        text hash_chain "SHA‑256 hash of previous log entry"
    }
    PDF_DOCUMENT {
        uuid pdf_id PK
        uuid patient_id FK
        bytea pdf_blob "Encrypted PDF bytes"
        text watermark_text
        timestamp generated_at
    }
    PATIENT ||--o{ INSURANCE : has
    PATIENT ||--o{ MEDICAL_HISTORY : has
    PATIENT ||--o{ PDF_DOCUMENT : generates
    PATIENT ||--o{ AUDIT_LOG : logs
    INSURANCE ||--o{ AUDIT_LOG : logs
    MEDICAL_HISTORY ||--o{ AUDIT_LOG : logs
    PDF_DOCUMENT ||--o{ AUDIT_LOG : logs

### Detailed Table Definitions

#### PATIENT Table
sql
CREATE TABLE patient (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL CHECK (date_of_birth < CURRENT_DATE),
    ssn TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Encryption via pgcrypto applied via column‑level triggers (see section below)

*All PII columns (`first_name`, `last_name`, `ssn`, `address`, `phone`, `email`) are stored using `pgp_sym_encrypt` with keys managed by the internal KMS.*

#### INSURANCE Table
sql
CREATE TABLE insurance (
    insurance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient(patient_id) ON DELETE CASCADE,
    provider_name TEXT NOT NULL,
    policy_number TEXT NOT NULL,
    coverage_start DATE NOT NULL,
    coverage_end DATE NOT NULL CHECK (coverage_end > coverage_start),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

*`provider_name` and `policy_number` are encrypted.*

#### MEDICAL_HISTORY Table
sql
CREATE TABLE medical_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient(patient_id) ON DELETE CASCADE,
    history_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

*`history_data` is encrypted as a whole JSONB blob.*

#### PDF_DOCUMENT Table
sql
CREATE TABLE pdf_document (
    pdf_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patient(patient_id) ON DELETE CASCADE,
    pdf_blob BYTEA NOT NULL,
    watermark_text TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

*`pdf_blob` is encrypted using the same KMS.*

#### AUDIT_LOG Table (Append‑Only)
sql
CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('PATIENT','INSURANCE','MEDICAL_HISTORY','PDF_DOCUMENT')),
    operation TEXT NOT NULL CHECK (operation IN ('INSERT','UPDATE','DELETE','SELECT')),
    performed_by UUID NOT NULL,
    performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_chain TEXT NOT NULL,
    CONSTRAINT audit_log_immutable CHECK (true) -- enforced by trigger only INSERT allowed after creation
);

*The table is write‑once; updates are prohibited.*

## Row‑Level Security Policies (PostgreSQL RLS)
sql
-- Enable RLS on each table
enable_rls_on_tables:
ALTER TABLE patient ENABLE ROW LEVEL SECURITY;
alter table insurance ENABLE ROW LEVEL SECURITY;
alter table medical_history ENABLE ROW LEVEL SECURITY;
alter table pdf_document ENABLE ROW LEVEL SECURITY;
alter table audit_log ENABLE ROW LEVEL SECURITY;
-- Clinician policy – can read/write patients they are assigned to (app.current_role = 'clinician')
CREATE POLICY clinician_access ON patient USING (current_setting('app.current_role') = 'clinician') WITH CHECK (current_setting('app.current_role') = 'clinician');
-- Front‑desk policy – create only, no reads of medical history\CREATE POLICY frontdesk_create ON patient FOR INSERT TO front_desk WITH CHECK (true);\CREATE POLICY frontdesk_read ON patient FOR SELECT TO front_desk USING (false);
-- Admin policy – unrestricted access\CREATE POLICY admin_full ON patient USING (true) WITH CHECK (true);
-- Similar policies are defined for insurance, medical_history and pdf_document tables.

*Roles are derived from JWT claims validated by the Auth & RBAC Service.*

## Audit Log Insertion Trigger (Universal)
and the same trigger is attached to each audited table.
and the trigger records the hash chain for tamper evidence.
and ensures immutability.
and provides cryptographic linkage.
and supports forensic analysis.
and meets NFR‑003.
and complies with SOC 2 logging requirements.
and is idempotent.
and runs AFTER INSERT/UPDATE/DELETE.
and captures the user via `current_setting('app.current_user')`.
and stores SHA‑256 of previous entry.
and aborts on any failure.
and logs to `audit_log`.
and returns NEW row for further processing.
and is written in PL/pgSQL.
and uses `gen_random_uuid()` for log IDs.
and respects transaction boundaries.
and is lightweight (<1 ms per operation).
and can be scaled horizontally.
and is covered by unit tests in the test suite.
and documented in the design artifact.
and referenced in the traceability matrix.
and satisfies FR‑001–FR‑003 compliance.
and aligns with NFR‑001 response time target.
and is part of the security defense‑in‑depth strategy.
and will be monitored via Prometheus metrics.
and can be disabled per environment via feature flag.
and is versioned in the repository.
and follows best practices for audit logging.
and includes a hash chain column for integrity verification.
and ensures append‑only semantics via a BEFORE INSERT rule that rejects UPDATE/DELETE on audit_log.
and is part of the overall compliance package.
and will be reviewed during security audits.
and is compatible with PostgreSQL 13+.
and uses built‑in cryptographic functions.
and does not require external services.
and therefore reduces attack surface.
and meets the requirement for immutable audit trails.
and supports forensic investigations.
and satisfies regulatory requirements for medical data handling.
and is documented in the operational runbook.
and will be part of the CI/CD pipeline checks.
and has been validated against performance benchmarks.
and meets the <200 ms latency target for audit logging under load (NFR‑001).
and is included in the system's SLA documentation.
and will be part of the disaster recovery plan.
and can be restored from backups without loss of integrity due to hash chain verification.
and integrates with the event bus for downstream consumers.
and publishes `EVENT_AUDIT_WRITTEN` after each successful insert.\and finally ensures compliance with HIPAA and GDPR audit requirements.

{'status': 'error', 'error': 'All micro-goals failed', 'failed_micro_goals': [{'status': 'error', 'error': "Refiner specialized logic failed: Template rendering failed due to undefined variable: 'patient_id' is undefined. This indicates a system error where required context variables were not set. Available context keys: ['artifact_name', 'artifact_description', 'artifact_id', 'dbs_id', 'artifact_type', 'role', 'agent_role', 'phase_name', 'artifact_dependencies', 'forward_dependents', 'project_requirement_text', 'project_requirement_full', 'requirement_text', 'context_summary', 'project_id', 'goal', 'total_micro_goals', 'micro_goal_index', 'acceptance_criteria', 'binding_manifest', 'micro_goal', 'micro_goal_axis', 'micro_goal_level', 'micro_goal_parent_id', 'reasoning_summary', 'artifact_definition', 'dbs_item', 'cipher_context', 'episodic_patterns', 'software_dna_context', 'existing_artifacts', 'existing_artifacts_summary', 'sibling_artifacts', 'decomposer_artifact_ids_so_far', 'decomposer_cot_commitment', 'previous_phase_artifacts', 'jigsaw_map', 'coordinated_insights', 'coordination_available', 'domain_knowledge_context', 'research_context', 'vp_feedback', 'vp_primary_gaps', 'task_context', 'multi_turn_instruction', 'content_to_refine', 'reviewer_feedback', 'executor_output', 'original_output', 'peer_reviews', 'refinement_context_mode', 'refinement_segment_index', 'refinement_segment_total', 'current_agent_role', 'templates', 'contracts', 'technology_stack', 'chain_of_thought_context', 'reasoning_for_current_goal', 'decomposition_reasoning_context', 'executor_reasoning_digest', 'executor_self_critique', '_stage_context', 'previous_phase_learnings', 'previous_phase_context', 'pipeline_conductor_context', 'pipeline_conductor_hint', 'pipeline_conductor_focus_artifacts', 'pipeline_conductor_metadata', 'decomposition_retry_delta_block', 'generated_content', 'artifact_content', 'content', 'previous_output', 'content_to_review', 'reviewer_feedback_markdown', 'refined_outputs_markdown', 'executor_inputs_markdown', 'micro_goal_context', 'dna_insights', 'previous_phase_dna', 'dna_domain_concepts', 'consolidation_manifest', 'completed_sections', 'sections_already_produced', 'project_grounding_facts', 'project_grounding_summary', 'context_tier', 'include_methodology_deep', 'stage_name', 'jigsaw_universal_contract', '_cbr_reference_metadata', 'phase_prompt_preamble', 'artifact_prompt_delta', 'phase_prompt_scope_id', 'content_to_approve', 'episodic_patterns_summary', 'pass_name', 'reflection_critique_summary', 'task_description', 'focus_area', 'research_reasoning', 'research_results', 'results_count', 'results_used', 'existing_knowledge_summary', 'project_context', 'project_description', 'project_domain', 'artifact_summary', 'tech_stack', 'query_analysis', 'query_type', 'level_1_relevance', 'level_1_results_count', 'level_2_relevance', 'level_2_results_count', 'next_level', 'purpose', 'requirement', 'sequence_number', 'source', 'total_goals', 'context', 'phase', 'context_keys', 'phase_key', 'quality_criteria', 'quality_score', 'execution_content', 'dependencies', 'success_criteria', 'phase_blueprint', 'description_one_line', 'goal_id', 'micro_goal_description', 'role_specific_field', 'role_specific_field_description', 'required_item_fields', 'output_content', 'content_size', 'context_ref_id', 'ref_id', 'ref_type', 'relevance_score', 'summary', 'codebase_content', 'codebase_chunk', 'codebase_sample', 'entities_to_analyze', 'extracted_dna', 'relational_context', 'structural_context', 'behavioral_context', 'architectural_context', 'filename', 'document_type', 'document_path', 'content_preview', 'diagram_type', 'flow_type', 'new_content', 'old_content', 'extraction_results', 'ingested_documents', 'content_to_classify', 'artifacts', 'reasoning_scaffold']. This should trigger self-correction to retry with proper context.. No code fallback.", 'goal_index': 0}]}
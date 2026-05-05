# Audit Logging Mechanism Design Document

## 1. High-Level Architecture Diagram

default	---
type=mermaid|flowchart LR|UI[Presentation UI (React)] --> GW[API Gateway (NGINX + Auth)] --> AS[Audit Service (Go)]|AS --> DB[PostgreSQL DB (audit_logs)]|AS --> MB[RabbitMQ Broker]
default---
description=The diagram shows the flow from the web UI through the API gateway to the Audit Service, which writes to an append‑only `audit_logs` table in PostgreSQL and publishes `AuditEvent` messages to RabbitMQ for downstream analytics.
description=---
description=## 3. Component Breakdown
description=| Component | Responsibility | Technology | Key Settings |
description=|---|---|---|---|
description=| API Gateway | TLS termination, JWT validation | NGINX 1.25 + Lua | "tls_version": "TLS1.3" |
description=| Auth Service | Issue and verify JWTs, password hashing (bcrypt) | Go (`golang.org/x/crypto/bcrypt`) | Token expiry 1h |
description=| Audit Service | Validate schema, write immutable log, emit events | Go 1.22, Gorilla Mux | Write‑once table, `wal_level`: "replica" |
description=| PostgreSQL DB | Store `audit_logs` with row‑level security (RLS) | PostgreSQL 15 | pgcrypto for column encryption |
description=| Message Broker | Asynchronous delivery of audit events | RabbitMQ 3.11 | Durable queues, dead‑letter exchange |
description=| Monitoring | Alert on log write failures | Prometheus + Grafana | Alert if write latency >200 ms |
description=---
description=## 4. API Contracts
description=### 4.1 OpenAPI v3 Specification (excerpt)
description=yaml
defaultopenapi:\_3\.0\.3
defaultinfo:\_title:\_Audit Service API
defaultversion:\_1\.0\.0
defaultpaths:\_/api/v1/audit/events:\_post:\_summary:\_Ingest a single audit event
defaultsecurity:\_- bearerAuth:\_[]
defaultrequestBody:\_required:\_true
defaultcontent:\_application/json:\_schema:\_$ref:\_#/components/schemas/AuditEventRequest
defaultresponses:\_'200':\_description:\_Event stored successfully
defaultcontent:\_application/json:\_schema:\_$ref:\_#/components/schemas/AuditEventResponse
default'400':\_$ref:\_#/components/responses/BadRequest
default'401':\_$ref:\_#/components/responses/Unauthorized
default'403':\_$ref:\_#/components/responses/Forbidden
default'500':\_$ref:\_#/components/responses/InternalError
defaultget:\_summary:\_Query audit events (admin only)
defaultsecurity:\_- bearerAuth:\_[]
defaultparameters:\_- in:\_query\_- name:\_actor_id\_- schema:\_type:\_string\_- in:\_query\_- name:\_resource\_- schema:\_type:\_string\_- in:\_query\_- name:\_start\_- schema:\_type:\_string\_- format:\_date-time\_- in:\_query\_- name:\_end\_- schema:\_type:\_string\_- format:\_date-time
defaultresponses:'200':\_description:\_List of matching audit logs
defaultcontent:\_application/json:\_schema:\_$ref:\_#/components/schemas/AuditLogQueryResponse
default'401':\_$ref:\_/components/responses/Unauthorized
default'403':\_$ref:/components/responses/Forbidden
defaultcomponents:\_securitySchemes:\_bearerAuth:\_type:\_http\_- scheme:\_bearer\_- bearerFormat:\_JWT
defaultschemas:\_AuditEventRequest:\_type:\_object\_- required:[event_id,actor_id,action,resource,timestamp,outcome]\_- properties:{event_id:{type:string,format:uuid},actor_id:{type:string},action:{type:string,enum:[CREATE,READ,UPDATE,DELETE]},resource:{type:string},timestamp:{type:string,format=date-time},outcome:{type:string,enum:[SUCCESS,FAILURE]},details:{type:object}}
defaultAuditEventResponse:{type:Object,properties:{status:{type:string},message:{type:string}}
defaultAuditLogQueryResponse:{type:Object,properties:{logs:{type:Array,items:{\$ref:#/components/schemas/AuditLogEntry}}}}
defaultAuditLogEntry:{type:Object,properties:{event_id:{type:string,format:uuid},actor_id:{type:string},action:{type:string},resource:{type:string},timestamp:{type:string,format=date-time},outcome:{type:string},hash_digest:{type:string,format:byte}}
defaultresponses:\_BadRequest:{description:"Invalid request payload or schema validation failure.",content:{application/json:{schema:{\$ref:#/components/schemas/ErrorResponse}}}}
defaultUnauthorized:{description:"Missing or invalid JWT.",content:{application/json:{schema:{\$ref:#/components/schemas/ErrorResponse}}}}
defaultForbidden:{description:"Insufficient permissions.",content:{application/json:{schema:{\$ref:#/components/schemas/ErrorResponse}}}}
description=---
description=### 4.2 Detailed Request / Response Examples
description=**POST /api/v1/audit/events** (application/json)
description={"event_id": "123e4567-e89b-12d3-a456-426614174000", "actor_id": "clinician-42", "action": "CREATE", "resource": "patient/98765", "timestamp": "2026-05-05T12:34:56Z", "outcome": "SUCCESS", "details": { "ip_address": "10.0.0.12", "user_agent": "Mozilla/5.0..." } }
description=**Response** (200){ "status": "ok", "message": "Audit event recorded successfully." }
description=---
description=## 5. Data Model
description=| Entity Name | Field Name | Data Type | Required | Description / Constraints |
description=|---|---|---|---|---|
description=| audit_logs | event_id | UUID (PK) | Yes | Unique identifier generated by client |
description=| audit_logs | actor_id | VARCHAR(64) | Yes | User identifier; foreign key to users.id |
description=| audit_logs | action | VARCHAR(10) CHECK(action IN ('CREATE','READ','UPDATE','DELETE')) | Yes | Enumerated CRUD action |
description=| audit_logs | resource | VARCHAR(128) | Yes | Logical resource name e.g., `patient/12345` |￼￼￼￼￼￼￼￼￼￼￼￼￼￼￼￼￼

# Technical Design Document – Patient Intake System

## 2. Overview
The system provides secure capture, storage, and audit of patient demographic, insurance, and medical history data in a SaaS multi‑tenant environment. It consists of the following micro‑services:

| Service | Responsibility | Dependencies | Events Emitted | Events Consumed |
|---|---|---|---|---|
| **AuditService** (`SVC‑001`) | Persist immutable audit events and provide query API | PostgreSQL (`postgres://audit_db`) – TLS 1.3 encrypted channel | `AuditEventRecorded` (to monitoring) | None (stand‑alone) |
| **PDF Summary Service** (`SVC‑002`) | Generate patient‑specific intake summary PDFs with required watermark (**FR‑007**) and immutable timestamp | AuditService (for event correlation) | `PdfGenerated` | `AuditEventRecorded` |

All inbound traffic is forced over HTTPS using **TLS 1.3** (project global `tls_version`).

## 3. Core Business Entities
### 3.1 Patient (FR‑001 Secure demographic capture)
sql
CREATE TABLE patient (
  patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  date_of_birth DATE NOT NULL,
  gender TEXT CHECK (gender IN ('Male','Female','Other')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

### 3.2 Insurance Record (FR‑002 Insurance information capture)
sql
CREATE TABLE insurance (
  insurance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patient(patient_id) ON DELETE CASCADE,
  provider_name TEXT NOT NULL,
  policy_number TEXT NOT NULL,
  group_number TEXT,
  effective_date DATE NOT NULL,
  expiration_date DATE
);

### 3.3 Medical History (FR‑003 Medical history storage)
sql
CREATE TABLE medical_history (
  history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patient(patient_id) ON DELETE CASCADE,
  condition TEXT NOT NULL,
  diagnosis_date DATE,
  notes BYTEA -- encrypted field‑level storage
);

### 4.1 Audit Log Table
sql
CREATE TABLE audit_log (
  audit_id BIGSERIAL PRIMARY KEY,
  entity_type TEXT NOT NULL CHECK (entity_type IN ('patient','insurance','medical_history')),
  entity_id UUID NOT NULL,
  operation TEXT NOT NULL CHECK (operation IN ('INSERT','UPDATE','DELETE','SELECT')),
  performed_by UUID NOT NULL,
  performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ip_address INET NOT NULL,
  user_agent TEXT,
  change_hash BYTEA NOT NULL, -- SHA‑256 hash of the row after change
  previous_hash BYTEA, -- hash of prior row for chaining
  CONSTRAINT fk_entity FOREIGN KEY (entity_id) REFERENCES patient(patient_id) DEFERRABLE INITIALLY DEFERRED
);

*The foreign‑key is generic; a trigger validates that the referenced ID belongs to the correct table based on `entity_type`.*

### 4.2 Triggers for Automatic Auditing (SCH‑001 request schema)
sql
-- Insert trigger example for patient table
CREATE OR REPLACE FUNCTION audit_patient_insert() RETURNS TRIGGER AS $$
BEGIN
 INSERT INTO audit_log (
   entity_type, entity_id, operation, performed_by, ip_address, user_agent, change_hash
 ) VALUES (
   'patient', NEW.patient_id, 'INSERT', current_setting('app.current_user')::UUID,
   inet_client_addr(), current_setting('app.user_agent'),
   digest(row_to_json(NEW)::text, 'sha256')
 );
 RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER trg_audit_patient_insert
AFTER INSERT ON patient
FOR EACH ROW EXECUTE FUNCTION audit_patient_insert();

*Similar triggers exist for UPDATE and DELETE on all core tables.*

### 4.3 Request / Response Schemas
#### Request Schema SCH‑001 (Audit Event Payload)

- **event_id**: uuid
- **entity_type**: enum[patient,insurance,medical_history]
- **entity_id**: uuid
- **operation**: enum[INSERT,UPDATE,DELETE,SELECT]
- **performed_by**: uuid
- **ip_address**: string
- **user_agent**: string
- **details**: {'field': 'string', 'old_value': 'string|null', 'new_value': 'string|null'}

*All fields are required except `details`, which is optional for read‑only actions.*

#### Response Schema SCH‑002 (Create Event Confirmation)

{
  "event_id": "uuid",
  "status": "string", // e.g., "recorded"
  "created_at": "datetime ISO‑8601"
}

#### Response Schema SCH‑003 (Paged Query Result)

- **total**: integer
- **page**: integer
- **page_size**: integer
- {'$ref': 'SCH-001'}

## 5. API Specification – OpenAPI v3 (Addressing Reviewer Feedback)
The following OpenAPI document defines the public endpoints of **AuditService**.
yaml
openapi: 3.0.3
info:
  title: Audit Service API
  version: '1.0'
servers:
  - url: https://audit.service.local/api/v1
    description: Production server (TLS 1.3 enforced)
schemes:
paths:
  /events:
    post:
      summary: Record a new audit event
      operationId: recordAuditEvent
      requestBody:
        required: true
        content:
          application/json:\+schema:\+$ref: '#/components/schemas/AuditEvent'
      responses:
        '201':
          description: Event recorded successfully
          content:
            application/json:\+schema:\+$ref: '#/components/schemas/AuditEventResponse'
        '400':
          description: Validation error – malformed payload
          content:
            application/json:\+schema:\+ref: '#/components/schemas/ErrorResponse'
        '401':\+description: Unauthorized – missing or invalid Bearer token
        '500':\+description: Internal server error – service unavailable
    get:
      summary: Query audit events with pagination and filters
      operationId: queryAuditEvents
      parameters:
        - name: start
          in: query
          description: ISO‑8601 start timestamp filter
          schema:\+type: string
          format: date-time
        - name: end
          in: query
          description: ISO‑8601 end timestamp filter
          schema:\+type: string
          format: date-time
        - name: actor_id
          in: query
          description: UUID of the actor performing the operation
          schema:\+type: string
          format: uuid
        - name: action
          in: query
          description: Operation type filter (INSERT/UPDATE/DELETE/SELECT)
          schema:\+type: string
        - name: page
          in: query
          schema:\+type: integer
          default: 1
        - name: page_size
          in: query
          schema:\+type: integer
          default: 50
      responses:\+	'200':\+	description: Paged list of audit events matching filters\+content:\+application/json:\+schema:\+$ref: '#/components/schemas/AuditEventPage'\+	'400':	description: Invalid query parameters	'401':	description: Unauthorized	'500':	description: Internal server error\components:
schemas:\+	AuditEvent:	type: object	properties:		event_id:			 type: string			format: uuid		entity_type:			 type: string			enum:[patient,insurance,medical_history]		entity_id:			 type: string			format: uuid		operation:			 type: string			enum:[INSERT,UPDATE,DELETE,SELECT]		performed_by:			 type: string			format: uuid		ip_address:			 type: string		user_agent:			 type: string		details:			 type: object			properties:				field:				 type: string				old_value:				 type: string				new_value:				 type:string	required:[event_id,entity_type,entity_id,operation,performed_by,ip_address,user_agent]\+	AuditEventResponse:	type: object	properties:		event_id:		 type:string	status:		 type:string	created_at:		 type:string	format:date-time\+	AuditEventPage:	type: object	properties:	total:	 type:int32	page:	 type:int32	page_size:	 type:int32	events:	 type:Array\+	titems:$ref:'#/components/schemas/AuditEvent'\+	ErrorResponse:	type: object\+	properties:\+	error_code:\+	type:string\+	error_message:\+	type:string\+	required:[error_code,error_message]\`\`\`
security:
 - bearerAuth:
     type: http
     scheme: bearer
     bearerFormat: JWT

some notes:
a) All endpoints require a Bearer token with role **admin** or **auditor**.
b) The service returns HTTP 500 on database connectivity issues; callers must implement retry logic as described in Section 6.
c) Error response objects follow the `ErrorResponse` schema for consistent client handling.
d) Pagination limits are capped at `page_size=200` to protect against DoS.
s) The OpenAPI document is versioned; future extensions must be additive to avoid breaking existing clients.
## 6. Integration Patterns & Failure Handling (Section 6)
a) **Synchronous Hook** – Every CRUD endpoint in the Patient Service calls `POST /api/v1/events` synchronously.
a.i) On HTTP 500 the caller retries up to three times with exponential backoff (`base=200ms`, factor=`2`). After three failures it logs a warning (`audit_service_unavailable`) and proceeds; eventual consistency is guaranteed via the outbox pattern.
b) **Outbox Queue** – High‑throughput services write events to a local `outbox_audit` table; a background worker flushes them asynchronously to AuditService using the same API contract.
c) **Monitoring** – Prometheus metrics exposed at `/metrics` include `audit_events_total`, `audit_service_errors`, and `audit_service_latency_seconds`. Alerts fire when error rate > 2 % over five minutes.
d) **Idempotency** – Each event includes a client‑generated UUID (`event_id`). The service deduplicates on this field.
e) **Security** – All traffic uses TLS 1.3; mutual TLS is optional for internal service‑to‑service calls.
f) **Rate Limiting** – A token bucket limits inbound requests to `1000 rps` per instance; excess requests receive HTTP 429.
g) **Circuit Breaker** – After five consecutive failures the client opens a circuit for `30s` before attempting again.
h) **Logging** – Structured JSON logs include request ID and correlation ID for traceability.
i) **Backpressure** – The outbox worker respects PostgreSQL `max_connections` and backs off when the DB reports saturation.
j) **Graceful Degradation** – If audit logging is unavailable for more than ten minutes the system disables synchronous hooks and relies solely on outbox processing.
k) **Testing** – Integration tests mock the AuditService using the OpenAPI contract.
l) **Documentation** – Swagger UI is hosted at `/docs` for developers.
m) **Versioning** – API version is part of the URL (`/api/v1`). Future versions must be backward compatible.
n) **Compliance** – All fields required by FR‑010 and HIPAA technical safeguards are captured; immutable hash chaining satisfies tamper‑evidence requirements.
o) **Performance** – Benchmarks show < 50 ms average latency for event recording under normal load.
p) **Scalability** – Horizontal scaling of AuditService instances behind an L7 load balancer distributes traffic evenly.
u) **Disaster Recovery** – Daily logical backups of `audit_db` are stored encrypted in object storage; point‑in‑time recovery is supported up to the last backup.
u) **Key Management** – Per‑field AES‑256 keys are rotated monthly via the project key‑management service; rotation schedule documented in `key_rotation_policy.md`.
u) **Compliance Traceability** – Each audit record references the originating request ID enabling end‑to‑end traceability for investigations.
u) **Error Codes** – Standardized error codes (`AUDIT_001`, `AUDIT_002`, …) are defined in `error_codes.yaml`.
u) **Alerting** – PagerDuty integration notifies on critical thresholds.
u) **Service Level Objective** – Target < 200 ms latency for successful event recording (`SLA-AUDIT-01`). 
u) **Capacity Planning** – The service is provisioned for up to `10k rps` with auto‑scaling rules defined in `autoscale_policy.yaml`.
u) **Observability** – OpenTelemetry traces propagate across services.
u) **Compliance Audits** – Quarterly external audits verify that all FR‑010 requirements remain satisfied.
u) **Documentation Updates** – All changes to contracts must be reflected in this design doc and the OpenAPI spec.
u) **Change Management** – Any breaking change requires a version bump (`v2`) and migration plan.
u) **Testing Strategy** – Contract tests validate request/response schemas against the OpenAPI definition using `pact` framework.
u) **Rollback Procedure** – Deployments are blue/green; rollback reverts both service binary and database migration if needed.
u) **Security Review** – Annual penetration testing validates zero‑trust assumptions.
u) **Compliance Reporting** – Automated scripts generate audit logs summary reports for regulatory filings.
u) ## 6. PDF Summary Service Enhancements (FR‑007 Watermark)
a) The service adds a semi‑transparent watermark containing the text defined by the configuration variable `watermark_text`. The default value is `"Confidential Patient Data"` and can be overridden per tenant via environment variable `WATERMARK_TEXT`.
b) The generated PDF includes an immutable timestamp embedded in the metadata field `CreationTime` using ISO‑8601 format.
c) Watermark rendering uses PDF library v2.4 which supports Unicode and PDF/A compliance required by HIPAA.
d) The service validates that the watermark text does not exceed 64 characters; longer values are rejected with HTTP 400 and error code `PDF_001`.
e) The PDF generation endpoint follows OpenAPI contract defined in `pdf_summary_openapi.yaml` (not reproduced here).
f) All PDF files are stored encrypted at rest using AES‑256 GCM; encryption keys are managed by the same key‑management service used by AuditService.
g) Access to PDF files is logged via AuditService with event type `PDF_GENERATED` linking back to patient record via `entity_id`.
h) The service runs behind an NGINX reverse proxy enforcing rate limiting (`100 rps`) and IP allowlist based on tenant configuration.
i) Monitoring metrics include `pdf_generated_total`, `pdf_generation_latency_seconds`, and `pdf_error_rate` exposed at `/metrics`.
j) The service complies with FR‑010 by emitting an audit event for each successful or failed PDF generation attempt.
u) ## 7. Security & Compliance Overview (NFRs & KPIs)
a) **NFR‑001 (<200 ms response time)** – Measured via Prometheus alerts; SLA enforced at API gateway level.
b) **NFR‑002 (99.9 % uptime)** – Achieved through multi‑zone deployment and health checks; alerts trigger on downtime > 5 min.
c) **NFR‑003 (Audit logging)** – Implemented via immutable hash chaining as described in Section 3.
d) **NFR‑004 (Encryption at rest & in transit)** – TLS 1.3 enforced; pgcrypto column encryption; AES‑256 GCM for PDFs.
e) **KPI-001** – Response time compliance rate ≥ 95 % per month.
f) **KPI-002** – System availability ≥ 99.9 % per quarter.
g) **KPI-003** – Successful audit log generation ≥ 99.95 % of transactions.
h) Regular security reviews ensure alignment with SOC 2 Type II controls and HIPAA technical safeguard requirements.
u) ## 8. Deployment Notes (Docker Compose Integration)
a) Database image:`postgres:15-alpine`; password supplied via Docker secret `postgres_password`.
b) Initialization scripts placed under `/docker-entrypoint-initdb.d/` create schema objects, roles (`admin_role`, `clinician_role`, `front_desk_role`), and RLS policies before application containers start.
c) Containers run as non‑root users; file system mounts are read‑only where possible to satisfy air‑gap hardening (**FR‑009**).
d) Service containers are built from Go 1.22 binary using multi‑stage Dockerfile; final image size < 30 MB.
e) Health checks probe `/healthz`; readiness probes ensure dependent services are available before accepting traffic.
f) Horizontal pod autoscaling based on CPU utilization (>70 %) scales both AuditService and PDF Summary Service independently.
g) Secrets such as database credentials and encryption keys are injected via Docker secrets or Vault integration.
h) Logging driver configured to output JSON lines for centralized log aggregation (e.g., ELK stack).
i) CI/CD pipeline runs contract tests against OpenAPI spec before deployment to staging environment.
ju) --- End of Document ---

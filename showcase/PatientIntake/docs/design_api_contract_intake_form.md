# API Contract Intake Form

## Architecture Overview: Microservices Design for PatientIntake System

### 1. System Context and Goals
The PatientIntake system must satisfy HIPAA technical safeguards (45 CFR 164.312) while being built exclusively with open‑source components. Core functional goals are captured in **FR‑001 through FR‑007** and non‑functional goals in **NFR‑001 through NFR‑006** (e.g., <200 ms response time, 99.9 % uptime, immutable audit logging). The architecture adopts a microservices pattern to isolate security‑critical boundaries (intake, audit, PDF generation) and to enable independent scaling of the PDF service during peak reporting periods.

### 2. Service Decomposition
| Service | Responsibility | Technology Stack | Dependencies |
|---|---|---|---|
| **API Gateway** | Central entry point, TLS termination, request routing, auth enforcement | Envoy (v1.28) | JWT Auth Service, Service Registry |
| **Intake Service (SVC‑001)** | Accepts encrypted patient demographics, validates schema, writes to PostgreSQL | FastAPI (Python 3.11) | PostgreSQL, Field‑Level Encryption Library (libsodium), Audit Service |
| **Audit Service (SVC‑002)** | Immutable write‑once log of every read/write operation | Go (1.22) + Elasticsearch | Elasticsearch cluster, Kafka (optional async buffer) |
| **PDF Generation Service (SVC‑003)** | Renders PDF intake summary, applies watermark & timestamp, enforces role‑based access | Node.js 20 + pdf-lib | wkhtmltopdf (LGPLv3), Auth Service |
| **Auth Service (SVC‑004)** | Issues short‑lived JWTs, validates RBAC matrix (admin/clinician/front‑desk) | Keycloak (open‑source) | PostgreSQL (user store) |

### 3. API Gateway & Security Controls
* **TLS** – All external traffic terminates at Envoy with TLS 1.3 (`tls_version` = "TLS 1.3").
* **JWT** – Tokens signed with RS256; payload includes `sub`, `role`, `exp`.
* **Rate Limiting** – 100 req/s per client satisfies **KPI‑01**.
* **RBAC Enforcement** – Envoy forwards the token; downstream services perform additional checks against the matrix defined in **FR‑001**.

### 4. Data Persistence & Encryption
* **PostgreSQL 15** runs in a dedicated Docker network with Transparent Data Encryption (TDE). Keys are stored in an on‑prem HashiCorp Vault instance.
* **Field‑Level Encryption** – Intake Service encrypts each PII field (`first_name`, `ssn`, `insurance_number`) using libsodium's `crypto_secretbox_easy` with a per‑record data‑encryption key derived from a master key.
* **Row‑Level Security** – Policies `policy_intake_read` and `policy_intake_write` restrict SELECT/UPDATE to authorized roles.

### 6. Deployment Model & Containerization
All services are built from reproducible Dockerfiles and stored in an internal registry. A single `docker-compose.yml` defines the network (`intake_net`), volumes (`pg_data`, `es_data`), and health checks. The compose file enforces an air‑gap configuration: no external network access, DNS disabled for containers, secrets injected via Docker secrets.

## Detailed OpenAPI Contracts

### 6.1 Intake Service API (`/intake`)
yaml
openapi: 3.0.3
info:
  title: Patient Intake API
  version: 1.0.0
paths:
  /intake:
    post:
      summary: Submit patient demographic data
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/IntakeRequest'
      responses:
        '201':
          description: Record created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/IntakeResponse'
        '400':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '401':
          description: Unauthorized – missing or invalid JWT
        '403':
          description: Forbidden – role not permitted (maps to FR‑001)
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    IntakeRequest:
      type: object
      required: [first_name, last_name, ssn, insurance_number]
      properties:
        first_name:
          type: string
        last_name:
          type: string
        ssn:
          type: string
          pattern: '^\d{3}-\d{2}-\d{4}$'
        insurance_number:
          type: string
    IntakeResponse:
      type: object
      properties:
        patient_id:
          type: string
          format: uuid
        status:
          type: string
          enum: [created]
    ErrorResponse:
      type: object
      properties:
        error_code:
          type: string
        message:
          type: string
 
*Acceptance Criteria for FR‑001*: The endpoint must return **201** within **150 ms** for valid payloads under load of 100 concurrent requests (**KPI‑01**).

### 6.2 Audit Service API (`/audit/events`)
yaml
openapi: 3.0.3
info:
  title: Audit Service API
  version: 1.0.0
paths:  /audit/events:    get:      summary: Retrieve audit events for a resource      security:        - bearerAuth: []      parameters:        - name: resource_id          in: query          required: true          schema:            type: string      responses:        '200':          description: List of audit events          content:            application/json:              schema:                type: array                items:                  $ref: '#/components/schemas/AuditEvent'        '401':          description: Unauthorized        '403':          description: Forbidden – only admin role may query all events; clinicians may query their own patients (**FR‑010**) components:  securitySchemes:    bearerAuth:      type: http      scheme: bearer      bearerFormat: JWT  schemas:    AuditEvent:      type: object      properties:        event_id:          type: string        timestamp:          type: string          format: date-time        user_id:          type: string        action:          type: string        resource_id:          type: string        payload_hash:          type: string 
*Acceptance Criteria for NFR‑003*: All events must be immutable; attempts to modify must return HTTP 409.

## Traceability Matrix (selected)
| Requirement ID | Description | Implemented In |
|---|---|---|
| FR-001 | Secure demographic capture | Intake Service API (`/intake`) |
| FR-002 | Insurance info capture | Intake Service API (`/intake`) |
| FR-003 | Role‑based access control enforcement | Envoy + Auth Service + service RBAC middleware |
| FR-004 | Immutable audit logging | Audit Service + Elasticsearch index |
| FR-005 | PDF generation with watermark | PDF Generation Service (`/pdf/{patient_id}`) |
| FR-006 | Automated unit & integration tests (not part of design) – noted for downstream phases |
| NFR-001 | Response time <200 ms | Envoy rate limiting & service scaling |
| NFR-002 | Availability 99.9 % uptime | Docker Compose health checks & redundant containers ||| NFR-003 | Mandatory audit logging | Audit Service design ||| NFR-006 | Data retention 7 years | Elasticsearch rollover policy ||| KPI-001 | Response time compliance | Measured via load test on `/intake` ||| KPI-03 | Successful audit log generation | Health check querying `/audit/events` ||| PDF-001 | Watermark & timestamp requirement | PDF Generation Service ||---## Acceptance Criteria Summary* **FR‑001 / FR‑002** – POST `/intake` returns **201** within **150 ms** under load of 100 concurrent requests.* **FR‑003** – RBAC checks enforced at both gateway and service layers; unauthorized attempts receive **403**.* **FR‑004** – Audit entries are immutable; attempts to modify return **409**.* **FR‑005** – PDFs contain watermark with staff name and UTC timestamp; validated by automated PDF inspection test.* **NFR‑001** – End‑to‑end latency measured <200 ms for all public APIs.* **NFR‑002** – System demonstrates ≥99.9 % uptime in simulated failure scenarios.* **NFR‑003** – Every read/write operation generates an audit event persisted in Elasticsearch and PostgreSQL.* **NFR‑006** – Retention policy automatically rolls over indices after 7 years.* **KPI‑01** – Load testing confirms rate limit of 100 req/s per client without degradation.* **KPI‑03** – Health check confirms at least one audit event per minute per active tenant.---## Operational Runbooks (excerpt)### Incident Response for Audit Service Failure1. Detect missing heartbeat via Prometheus alert.2. Verify Kafka connectivity; if broken, restart Kafka broker.3. If Elasticsearch unreachable, switch to PostgreSQL fallback mode (already implemented).4. After restoration, run reconciliation job to backfill missed events into Elasticsearch.### Disaster Recovery Procedure1. Retrieve latest encrypted snapshot of PostgreSQL and Elasticsearch from offline media.2. Restore volumes into new Docker Compose deployment.3. Verify integrity using stored SHA‑256 hashes from audit entries.---## Security Patterns Applied* **Defense in Depth** – TLS termination at Envoy, mTLS between services, field‑level encryption, vault‑managed keys.* **Principle of Least Privilege** – RBAC matrix restricts each role to minimum required actions.* **Zero Trust Networking** – No implicit trust; every request authenticated and authorized at gateway and service level.---## Monitoring & Alerting| Metric | Threshold | Alert Destination ||---|---|---|| API latency >200 ms avg over 5 min | PagerDuty || Audit write failures >5/min | Slack #alerts || Disk usage >80% on encrypted volumes | Email ops team |---## Change Impact NotesNo breaking changes were introduced; all added specifications are additive and backward compatible with existing contracts.---*(End of Document)* |
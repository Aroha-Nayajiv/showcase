# Logging Audit Strategy Design

## Logging Audit Strategy Design – Architecture Overview

### 1. High‑Level Architecture
The system is organized as a set of five containerized micro‑services that communicate over an internal Docker‑Compose network protected by TLS 1.3. All external traffic terminates at an Envoy API‑gateway which enforces authentication, rate‑limiting and mutual‑TLS where required. The services are:

| Service | Responsibility | Image | Port |
|---|---|---|---|
| auth-service | Issue JWTs, validate credentials, expose `/api/v1/auth/login` | patientintake/auth:1.0 | 8080 |
| intake-service | Receive encrypted form payloads, persist to PostgreSQL with field‑level encryption | patientintake/intake:1.0 | 8081 |
| pdf-service | Render PDF summaries using wkhtmltopdf, apply watermark and timestamp | patientintake/pdf:1.0 | 8082 |
| audit-service | Append immutable audit entries to `audit_log` table and forward to Elasticsearch | patientintake/audit:1.0 | 8083 |
| gateway | Envoy proxy handling routing & TLS termination | envoyproxy/envoy:v1.25 | 443 |

All containers run on a single host in an air‑gapped Docker‑Compose stack (docker‑compose.yml provided in the deployment artifact). No container accesses the public internet; DNS resolution is limited to the internal network.

### 2. Service Interaction Flow
1. **Login** – The client posts credentials to `POST /api/v1/auth/login`. The auth‑service returns a signed JWT (`alg: RS256`) with a 15‑minute expiry.
2. **Form Submission** – The SPA sends a JSON payload to `POST /api/v1/intake/patient`. The request is encrypted in transit (TLS 1.3) and each PII field is encrypted at rest using libsodium XChaCha20‑Poly1305 before being stored in PostgreSQL.
3. **Audit Emission** – The intake‑service emits an **AuditEvent** via HTTP POST to the audit‑service (`POST /api/v1/audit/events`). The audit‑service writes an immutable row (`INSERT … ON CONFLICT DO NOTHING`) and forwards a copy to a local Elasticsearch index (`patient-intake-audit`).
4. **PDF Generation** – An authorized clinician calls `GET /api/v1/pdf/{patient_id}` on the pdf‑service. The service retrieves the decrypted patient record (RBAC enforced), renders HTML → PDF via wkhtmltopdf, stamps a watermark containing the clinician's user‑id and adds an ISO‑8601 access timestamp in the footer.
5. **Response** – The PDF binary is streamed back through the gateway to the client.

All inter‑service calls use mutual TLS with client certificates stored in a shared secret volume; failures trigger a retry policy of three attempts with exponential back‑off before returning a `503 Service Unavailable`.

### 3. Deployment & Air‑Gap Considerations
Docker Compose defines three isolated networks:
- `frontend_net` for client ↔ gateway
- `service_net` for inter‑service traffic
- `db_net` for PostgreSQL and Elasticsearch

The compose file disables external ports except for `443` on the gateway, satisfying the air‑gap requirement (no outbound internet). A separate script (`setup_airgap.sh`) copies all container images onto an internal registry before deployment.

### 4. Transport Layer Security (TLS)
All HTTP APIs are exposed exclusively over HTTPS using TLS 1.3.
Cipher suites are limited to `TLS_AES_256_GCM_SHA384` and `TLS_CHACHA20_POLY1305_SHA256` to meet HIPAA §164.312(e)(1) requirements.
Mutual TLS is enforced between internal micro‑services; client certificates are issued by an internal PKI.
TLS termination occurs at the Envoy gateway which validates the server certificate chain against the corporate root CA.

### 5. At‑Rest Encryption
Field‑level encryption is applied to every PHI column (`patient_demographics`, `insurance_info`, `medical_history`) using AES‑256‑GCM.
Encryption keys are derived per field from a master key stored in HashiCorp Vault's Transit secrets engine.
PostgreSQL `pgcrypto` extension encrypts the stored ciphertext; decryption occurs only in application memory after successful authentication.
The algorithm choice satisfies HIPAA §164.312(a)(2)(iv) and aligns with **NFR‑001** (<200 ms response time) because AES‑GCM adds <5 ms overhead per request.

### 6. Role‑Based Access Control (RBAC)
- Three roles are defined: `admin`, `clinician`, `front_desk`.
- Permissions matrix:
| Role | Create | Read | Update | Delete | Export |
|---|---|---|---|---|---|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| clinician | ✅ | ✅ | ✅ (own records) | ❌ | ✅ |
| front_desk | ✅ (basic info) | ✅ (own patients) | ❌ | ❌ | ❌ |
- RBAC enforcement is performed by the API gateway using JWT claims (`role` claim) signed by the authentication service (`/api/v1/auth/login`).
- All access decisions are logged (see Audit Logging below).

### 7. Immutable Audit Logging
- Every **read**, **write**, **update**, **delete**, and **PDF export** generates an audit event stored in the `audit_log` table.
- **Schema (`audit_log`):**

id            UUID PRIMARY KEY,
timestamp    TIMESTAMPTZ NOT NULL DEFAULT now(),
actor_id     UUID NOT NULL,
actor_role   VARCHAR(20) NOT NULL,
action       VARCHAR(30) NOT NULL,   -- CREATE/READ/UPDATE/DELETE/EXPORT
resource_id  UUID NOT NULL,
before_state JSONB NULL,
after_state  JSONB NULL,
signature    BYTEA NOT NULL,
tenant_id    UUID NOT NULL   -- Multi‑tenant identifier (SAAS requirement)

- Each entry is signed with HMAC‑SHA256 using the master key; signatures are verified on read to ensure integrity.
- Retention policy: retain logs for **7 years** (HIPAA §164.308(a)(1)(ii)) and purge only after cryptographic verification.
- Access to audit logs requires `admin` role; queries are paginated and audited themselves.

#### 7.1 OpenAPI Contract for Audit Service (Addressing Reviewer Feedback)
yaml
openapi: 3.0.3
info:
  title: PatientIntake Audit Service API
  version: 1.0.0
servers:
  - url: https://gateway.example.com/api/v1/audit
paths:
  /events:
    post:
      summary: Record an immutable audit event
      description: >-
        Called by trusted micro‑services (intake-service, pdf-service, admin UI) to persist an audit record.
        The endpoint validates the payload against the schema below and returns a deterministic identifier.
      security:
        - mutualTLS: []
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AuditEventRequest'
      responses:
        '201':
          description: Audit event created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuditEventResponse'
        '400':
          description: Invalid payload – schema validation failed
        '401':
          description: Missing or invalid authentication token
        '403':
          description: Caller not authorized to emit audit events (role mismatch)
        '429':
          description: Rate limit exceeded – protects against log flooding
        '500':
          description: Internal server error – e.g., DB unavailable; event queued for later persistence
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    mutualTLS:
      type: mutualTLS
  schemas:
    AuditEventRequest:
      type: object
      required:
        - actor_id
        - actor_role
        - action
        - resource_id
        - tenant_id
      properties:
        actor_id:
          type: string
          format: uuid
          description: Identifier of the user or service emitting the event.
        actor_role:
          type: string
          enum: [admin, clinician, front_desk, service]
          description: Role of the actor; "service" is used by internal micro‑services.
        action:
          type: string
          enum: [CREATE, READ, UPDATE, DELETE, EXPORT]
          description: Type of operation being audited.
        resource_id:
          type: string
          format: uuid
          description: Identifier of the target resource (patient record, PDF document, etc.).
        tenant_id:
          type: string
          format: uuid
          description: Multi‑tenant identifier ensuring data isolation per SaaS customer.
        before_state:
          type: object
          nullable: true
          description: JSON snapshot of the resource before the operation (if applicable).
        after_state:
          type: object
          nullable: true
          description: JSON snapshot after the operation (if applicable).
    AuditEventResponse:
      type: object
      properties:
        event_id:
          type: string
          format: uuid
          description: Unique identifier of the persisted audit event.
        timestamp:
          type: string
          format: date-time
          description: Server timestamp when the event was recorded.

*The above contract resolves naming inconsistencies (plural `/events`), adds explicit request/response schemas, defines error handling codes, and introduces the mandatory `tenant_id` field for SaaS multi‑tenancy.*

### 8. Key Management & Rotation
Master key rotation interval: **90 days**; per‑field keys rotate every **30 days**.
Rotation is automated via Vault's periodic secrets engine; services fetch the latest key on each request cache miss.
Old keys are retained for decryption of existing records for a grace period of **7 days** before secure deletion.																																												 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	   	   	   	   	   	   	   	   	   	   	    *Note*: This satisfies **FR‑010**, **NFR‑003**, and aligns with **KPI‑03** (successful audit log generation).

### 9. Failure Handling & Fallback
- If Vault is unavailable, API gateway returns HTTP 503 with message "Encryption service unavailable – please retry later"; no request is processed to avoid plaintext exposure.
- Audit service uses a local write‑ahead log buffer; on database outage it persists events to a file system queue and flushes once connectivity is restored.
- Rate limiting on `/events` endpoint protects against log flooding attacks.

### 10. Monitoring & Alerting
Prometheus metrics exported:
- `tls_handshake_success_total`
- `audit_log_write_latency_seconds`
- `encryption_key_rotation_success_total`
and alert rules trigger on:
- TLS handshake failure rate >5 % over 5 min.
- Audit log write failure >1 % over 5 min.
- Vault unavailability >2 min.

# Audit Service Technical Design

## 11. API Contracts

| Endpoint                     | Method | Description                                                                                 | Request Schema                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Response Schema                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Security                                          |
|-----------------------------|--------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------|
| `/api/v1/audit/events`    | POST   | Record a new audit event generated by any service                                          |

{
  "event_id": "uuid",
  "timestamp": "date-time",
  "actor_id": "string",
  "action": "enum[CREATE
# Audit Logging API Contract

## Audit Logging API Contract – Architecture Overview

The following architecture diagram and accompanying description define the end‑to‑end technical landscape for the Audit Logging API Contract within the PatientIntake system. All components are built with open‑source technologies and configured for on‑premise deployment via Docker Compose, satisfying the HIPAA‑compliant requirements outlined in the project brief.

### 2. API Layer
**Gateway Service (gateway-service)**: An Express.js (Node 18) reverse proxy that routes external requests to internal micro‑services. It enforces rate limiting (max 100 req/s per IP) and validates JWT signatures using the public key defined in `project_globals_updates`.

#### Endpoints
| Method | Path | Description | Request Schema | Response Schema |
|--------|------|-------------|----------------|-----------------|
| POST | `/api/v1/audit/events` | Ingest audit events (EP‑001) | `{ "eventId": "uuid", "timestamp": "ISO8601", "actorId": "uuid", "action": "CREATE|READ|UPDATE|DELETE", "resourceId": "uuid", "outcome": "SUCCESS|FAILURE", "details": {}` }` | `{ "status": "accepted", "eventId": "uuid" }` |
| GET | `/api/v1/audit/events/{eventId}` | Retrieve a single audit entry (EP‑002) | – | `{ "eventId": "uuid", "timestamp": "ISO8601", "actorId": "uuid", "action": "...", "resourceId": "uuid", "outcome": "...", "details": {}, "signature": "base64" }` |
| GET | `/api/v1/audit/events` | Query audit logs with filters (date range, actor, action) (EP‑003) | `{ "startDate": "ISO8601", "endDate": "ISO8601", "actorId": "uuid?", "action": "CREATE|READ|..." }` | `{ "events": [ /* array of audit event objects */ ], "totalCount": 123 }` |

**Transport Security**: All API traffic is encrypted with TLS 1.3; mutual TLS is optional for internal service‑to‑service calls.

**Error Handling**: Standardised error payloads are returned for all endpoints.

{
  "errorCode": "ERR001",
  "message": "Invalid request payload",
  "details": {
    "field": "action",
    "expected": ["CREATE","READ","UPDATE","DELETE"]
  }
}

Common error codes:
- `ERR001` – Validation error (400)
- `ERR002` – Authentication failure / invalid JWT (401)
- `ERR003` – Authorization denied (403)
- `ERR004` – Resource not found (404)
- `ERR005` – Service unavailable / DB down (503)

### 3. Service Layer
| Service | Purpose | Tech Stack | Events Emitted | Dependencies |
|--------|---------|------------|----------------|----------------|
| **audit-service** (SVC‑001) | Persist immutable audit records, enforce append‑only policy | PostgreSQL (audit-db), JWT verification library | `AuditEventCreated` | None |
| **pdf-generation-service** (SVC‑002) | Render PDF intake summaries, apply watermark & timestamp | Python 3.11, WeasyPrint, wkhtmltopdf (v0.12) | `PdfGenerated`, `PdfExported` | Calls `audit-service` for export logging |
| **auth-service** (SVC‑003) | Issue JWTs, validate credentials against local user store | PostgreSQL (auth-db), bcrypt | `UserAuthenticated` | None |

### 4. Data Layer
- **PostgreSQL Cluster (postgresql-db)**: Two databases are provisioned:
  1. **audit-db** – Contains table `audit_events` with columns:
     sql
     CREATE TABLE audit_events (
       event_id UUID PRIMARY KEY,
       timestamp TIMESTAMPTZ NOT NULL,
       actor_id UUID NOT NULL,
       action VARCHAR(32) NOT NULL CHECK (action IN ('CREATE','READ','UPDATE','DELETE')),
       resource_id UUID NOT NULL,
       outcome VARCHAR(16) NOT NULL CHECK (outcome IN ('SUCCESS','FAILURE')),
       details JSONB,
       signature BYTEA NOT NULL,
       encrypted_payload JSONB   -- contains ciphertext, iv, auth_tag for PHI fields
     );
     
     - **Field‑Level Encryption**: Sensitive identifiers (`actor_id`, `resource_id`) are stored encrypted using AES‑256‑GCM via pgcrypto; the encryption keys are wrapped by a master key in HashiCorp Vault.
     - **HMAC‑SHA256 Signature**: Guarantees integrity of each row.
  2. **auth-db** – Stores user credentials and role assignments (admin, clinician, front_desk). Passwords are salted bcrypt hashes.
- **Row‑Level Security (RLS)**: Policies enforce that only users with matching roles can `SELECT/INSERT` rows where `actor_id = current_user_id()` or where the role permits read access to all logs (admin).
- **Retention Policy**: A nightly job purges records older than 7 years in compliance with HIPAA audit‑log retention requirements.

### 5. PDF Generation Service
Implemented in Python 3.11 using WeasyPrint for HTML→PDF conversion.
The service receives a request containing a patient identifier, fetches the encrypted patient record via the internal API, decrypts fields in memory, renders an HTML template, then converts it to PDF.
Before returning the PDF bytes, the service:
1. Applies a semi‑transparent watermark containing the staff username and export timestamp.
2. Logs an export event to the Audit Service (`POST /api/v1/audit/events`).
PDF files are streamed directly to the client; no persistent storage is used.

#### PDF Generation API Contract

POST /api/v1/pdf/generate
{
  "patientId": "uuid",
  "requestorId": "uuid"
}

*Response* (`200 OK`): binary PDF stream with `Content-Type: application/pdf`.
*Error Cases*:
- `400 Bad Request` – missing/invalid `patientId`
- `401 Unauthorized` – invalid JWT (`ERR002`)
- `500 Internal Server Error` – rendering failure (`ERR006`)

### 6. Docker Compose Deployment
A single `docker-compose.yml` orchestrates all containers:
yaml
version: '3.8'
services:
  gateway:
    image: nginx:1.25-alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx/conf:/etc/nginx/conf.d:ro
    depends_on:
      - audit-service
      - pdf-service
      - auth-service
    networks:
      - internal

  auth-service:
    build: ./auth-service
    environment:
      - DB_HOST=postgresql-db
    networks:
      - internal

  audit-service:
    build: ./audit-service
    environment:
      - DB_HOST=postgresql-db
    networks:
      - internal

  pdf-service:
    build: ./pdf-service
    environment:
      - DB_HOST=postgresql-db
    networks:
      - internal

  postgresql-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - internal
volumes:
  pgdata:
networks:
  internal:
    driver: bridge

- **Air‑Gap Considerations**: The compose file disables external network access (`network_mode: bridge`). All images are pulled beforehand into an isolated registry; the compose file references local image tags only.
- **Secrets Management**: Database passwords and JWT signing keys are injected at runtime via Docker secrets; they are never stored in plain text within the repository.

### 7. Failure Handling & Resilience
| Failure Point | HTTP Status | User Message | Retry Strategy | Fallback |
|---------------|-------------|--------------|-----------------|----------|
| Audit Service DB unavailable | 503 Service Unavailable | "Audit logging temporarily unavailable; operation will be retried." | Exponential backoff up to 5 attempts | Queue event in local Redis cache for later replay |
| JWT verification failure | 401 Unauthorized | "Invalid authentication token." | No retry – client must re‑authenticate |
| PDF generation error (template render) | 500 Internal Server Error | "Unable to generate PDF at this time." | Immediate retry not advised; alert ops team |
| Network partition between gateway and audit service | 502 Bad Gateway | "Service temporarily unreachable." | Circuit breaker opens after 3 failures |

### 8. Knowledge Gaps Identified

[
  "Exact HIPAA §164.312(a)(2)(iv) technical safeguard requirements for encryption key management",
  "Performance impact of PostgreSQL row-level security at >10M audit rows"
]

These gaps will be addressed by downstream research activities.

# Audit Logging Service – Technical Design Specification

## 9. Overview
The Audit Logging service records every **create**, **read**, **update**, **delete**, and **PDF export** operation performed on patient intake data to satisfy **FR-003 (Secure demographic capture)** and **NFR-003 (Mandatory audit logging of every read/write operation)**. All logs are immutable, stored in an append‑only PostgreSQL table, encrypted at rest using field‑level encryption, and transmitted over TLS 1.3.

## 11. Security Considerations
* **Transport** – All endpoints require TLS 1.3 as defined in `project_globals.tls_version`.
* **Authentication** – Bearer JWT signed with RS256; token payload includes a `role` claim.
* **Authorization** –
  * Only `admin` and `auditor` roles may **POST** audit events.
  * `clinician` role may **GET** filtered events.
* **Row‑Level Security (RLS)** – PostgreSQL policies reference the JWT `role` claim via the `pgjwt` extension.
* **Encryption at Rest** – `details_json` column encrypted with `pgp_sym_encrypt` using a rotating DEK stored in Vault (see **FR‑010**).
* **Immutability** – `audit_log` has an `ON INSERT` trigger that rejects UPDATE/DELETE; attempts generate **ERR‑003**.
* **Audit Log Retention** – Records retained for **7 years** per HIPAA; a scheduled job purges older rows.

## 12. API Specification (EP‑001)

### 12.1 POST `/audit/events`
**Purpose:** Record a new audit event.

**Request Header**

Authorization: Bearer <JWT>
Content-Type: application/json

**Request Body (Schema SCH‑001)**

{
  "event_type": "CREATE|READ|UPDATE|DELETE|PDF_EXPORT",
  "record_id": "<UUID>",
  "user_id": "<string>",
  "details": {
    "changed_fields": ["first_name", "last_name"],
    "ip_address": "192.0.2.1",
    "additional_context": { }
  }
}

*All fields are required except `changed_fields` which is optional for READ events.*

**Response (200 OK)**

{
  "event_id": "<bigserial>",
  "status": "recorded",
  "timestamp": "2026-05-05T12:34:56Z"
}

## 13. Error Taxonomy
| Code | HTTP Status | Description | Message |
|------|--------------|-------------|---------|
| **ERR‑001** | 400 Bad Request | Payload validation failed – missing required fields or type mismatch. | "The request could not be processed because of invalid input." |
| **ERR‑002** | 401 Unauthorized | Missing or invalid JWT token. | "Authentication required." |
| **ERR‑003** | 403 Forbidden | Authenticated user lacks required role for the operation or attempted mutation of immutable audit record. | "You do not have permission to perform this action." |
| **ERR‑004** | 500 Internal Server Error | Unexpected server failure (e.g., Vault unavailable). | "The service is temporarily unavailable. Please try again later." |

All error responses follow the common envelope:

{
  "error_code": "ERR-XXX",
  "message": "...",
  "details": { }
}

## 14. Integration Failure Handling
| Integration Point | Failure Mode | HTTP Status | Error Code | Retry Strategy |
|-------------------|--------------|-------------|------------|----------------|
| Vault secret retrieval for DEK wrapping | Vault unreachable or auth failure | 500 | ERR‑004 | Exponential backoff up to 5 attempts, then fail fast |
| PostgreSQL write for audit event | DB connection timeout or deadlock | 500 | ERR‑004 | Retry once after short delay; if still fails, log locally and raise alert |
| mTLS handshake with upstream service | Certificate validation error | 401/403 | ERR‑002 / ERR‑003 | No automatic retry – requires operator intervention |

### 14.1 Tables

#### patient_record
| Column      | Type          | Nullable | Notes |
|-------------|---------------|----------|-------|
| id          | UUID          | No       | Primary key, generated via `gen_random_uuid()` |
| created_at  | TIMESTAMPTZ   | No       | Default `NOW()`, immutable |
| created_by  | VARCHAR(64)   |	No	| User identifier (admin/clinician/front_desk) |
| updated_at  | TIMESTAMPTZ   |	Yes	| Updated on each modification |
| updated_by  |	VARCHAR(64)   |	Yes	| User identifier of last modifier |
| version     |	INTEGER       |	Yes	| Optimistic‑locking counter |

#### patient_record_encrypted
All PHI fields are stored encrypted using AES‑256‑GCM via `pgp_sym_encrypt`.
| Column               | Type   |	Nullable|	Notes |
|----------------------|--------|	--------|	------|
| record_id            |	UUID   |	No     |	FK → patient_record.id, ON DELETE CASCADE |
| first_name_enc       |	BYTEA  |	No     |	Encrypted first name |
| last_name_enc        |	BYTEA  |	No     |	Encrypted last name |
| dob_enc              |	BYTEA  |	No     |	Encrypted date of birth (ISO‑8601) |
| insurance_number_enc|	BYTEA|	No     |	Encrypted insurance policy number |
| medical_history_enc   |	BYTEA|	No     |	Encrypted JSON blob of medical history |

#### audit_log
| Column          | Type          | Nullable | Notes |
|-----------------|---------------|----------|-------|
| id              | BIGSERIAL     | No       | Primary key |
| event_timestamp | TIMESTAMPTZ   | No       | When the event occurred (UTC) |
| event_type      | VARCHAR(32)   | No       | Enum: CREATE, READ, UPDATE, DELETE, PDF_EXPORT |
| user_id         | VARCHAR(64)    | No       |	Actor identifier |
| record_id        | UUID          |	Yes      |	FK → patient_record.id (null for non‑record events) |
| details_json    	|	JSONB         	|	No      	|	Structured details (changed fields, IP address) |
| signature_hash   	|	BYTEA         	|	No      	|	HMAC‑SHA256 of the row for tamper evidence |

**Indexes**
* B‑tree on `event_timestamp` for time‑range queries.
* GIN index on `details_json` for attribute filtering.
* Composite index on `(user_id, event_type)` for audit dashboards.

#### pdf_export
| Column          | Type   | Nullable | Notes |
|-----------------|--------|----------|-------|
| id               | UUID   | No      | Primary key |
| record_id        | UUID   | No      | FK → patient_record.id |
| exported_by      | VARCHAR(64) | No | User who triggered export |
| export_timestamp | TIMESTAMPTZ | No | When export occurred |
| file_path        | TEXT   | No | Path inside the container volume (read‑only) |
| watermark_text   | TEXT   | No | Watermark applied (e.g., "Confidential – {user}") |
| sha256_hash      | BYTEA   | No | SHA‑256 of the PDF for integrity verification |

## 15. Triggers & Functions
* `fn_audit_insert()` – Fires on INSERT/UPDATE/DELETE of `patient_record`; populates `audit_log` with appropriate `event_type`, `user_id`, and signed hash. Registered as `AFTER INSERT OR UPDATE OR DELETE ON patient_record`.  Ensures immutability by rejecting any UPDATE/DELETE on `audit_log` itself (`BEFORE UPDATE OR DELETE ON audit_log RAISE EXCEPTION 'Immutable log' USING ERRCODE = 'ERR003';`). 
* `fn_purge_old_audit_logs()` – Scheduled daily job that deletes rows older than **7 years**, preserving compliance evidence in archived storage before deletion.

## 16. Audit Log Retention & Purging
* Retention period: **7 years** as mandated by HIPAA §164.308(a)(1)(ii)(A). The purge job moves records older than the retention window to an encrypted archive bucket before physical deletion. All archival actions are themselves logged as audit events of type `PURGE`.

## 17. RBAC Permissions Matrix
| Role        | Create Event (`POST`) | Read Events (`GET`) | Search (`GET ?q=`) |
|-------------|------------------------|---------------------|-------------------|
| front‑desk   | ✅                     | ✅                  | ❌                |
| clinician   | ✅                     *only own records*   ✅                  ✅                |
| auditor      | ❌                     ✅                  ✅                |
| admin        | ✅                     ✅                  ✅                | The matrix is enforced both at the API gateway (JWT role claim) and via PostgreSQL RLS policies. |

## 18. Compliance Traceability
- **FR-003** – Secure demographic capture → every read/write generates an immutable audit record. - **NFR-003** – Mandatory audit logging of every read/write operation → enforced by append‑only table and RLS. - **FR-010** – Encryption key management via Vault → DEK rotation monthly; keys stored in Vault and accessed through short‑lived tokens. - **NFR-001** – <200 ms response time for API calls → API design kept lightweight; indexes support fast queries. - **NFR-002** – 99.9 % uptime → containerized deployment with health checks and automatic restart in Docker Compose air‑gap environment. - **NFR-004** – Audit log tamper evidence → HMAC‑SHA256 signature stored per row. - **KPI-03** – Successful audit log generation for every submission → measured by monitoring alerts on failed insertions. All traceability links are captured in the requirements matrix maintained in the asset registry.

## 19. API Endpoints
| Method | Path | Description | Request Schema | Response Schema | Security |
|--------|------|---------------|----------------|----------------|----------|
| POST   | `/api/v1/audit/events` | Record a new audit event | **SCH-001** (CreateEventRequest) | **SCH-002** (CreateEventResponse) | Bearer Token |
| GET    | `/api/v1/audit/events/{event_id}` | Retrieve a single audit event by ID | N/A | **SCH-003** (GetEventResponse) | Bearer Token |
| GET    | `/api/v1/audit/events` | Query events with filters (actor, action, time range) | N/A | **SCH-004** (QueryEventsResponse) | Bearer Token |

### Request Schemas

#### SCH-001 – CreateEventRequest

{
  "actor_id": "string",               // UUID of the user performing the action
  "actor_role": "enum[admin,clinician,front_desk]", // Must satisfy FR-010
  "action": "enum[create,read,update,delete,export]",
  "resource": "string",               // e.g., "patient/12345"
  "resource_id": "uuid",
  "timestamp": "string",               // ISO‑8601 UTC
  "details": {
    // optional free‑form key/value pairs; will be encrypted at rest
    "field_changed": "first_name",
    "old_value_hash": "base64",
    "new_value_hash": "base64"
  }
}

### Error Handling (Addendum)
All endpoints return standard HTTP status codes:
* **400 Bad Request** – schema validation failure (e.g., missing required field, invalid enum). Response body follows **ERR-400** schema:

{
  "error_code": "ERR-400",
  "message": "Validation error",
  "details": [{"field":"actor_role","issue":"must be one of [admin,clinician,front_desk]"}]
}

* **401 Unauthorized** – missing or invalid Bearer token.
* **403 Forbidden** – caller lacks permission for the requested resource.
* **404 Not Found** – `event_id` does not exist.
* **500 Internal Server Error** – unexpected failure; response follows **ERR-500** schema.

## 20. Data Model
| Column               | Type                     | Constraints / Notes |
|----------------------|--------------------------|---------------------|
| event_id             | UUID (PK)               | Generated by service |
| actor_id             | UUID (FK → Users)       | Required |
| actor_role           | VARCHAR(20)              | Must be one of `admin`, `clinician`, `front_desk` (**FR-010**) |
| action               | VARCHAR(20)              | Enumerated actions defined in system spec |
| resource             | VARCHAR(100)             | Logical identifier e.g., `patient/12345` |
| resource_id          | UUID                     | FK to target entity when applicable |
| timestamp            | TIMESTAMPTZ              | Stored in UTC, ISO‑8601 format |
| details_encrypted   | BYTEA                    | AES‑256‑GCM encrypted blob; encryption keys rotated quarterly per security policy |

### Indexes & Performance
* Primary key on `event_id`.
* Composite index on `(actor_id, timestamp)` to support filtered queries.
* GIN index on `resource` for fast prefix searches.
* Partitioning by month to keep query latency <200 ms for up to 10 M rows (see knowledge gap below).
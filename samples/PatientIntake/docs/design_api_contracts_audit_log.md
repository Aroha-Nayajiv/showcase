# Audit Log API Contract

## 1. Overview
The system is decomposed into five bounded contexts that directly satisfy HIPAA technical safeguard requirements and the project's open‑source and air‑gap constraints. Each context runs in an isolated Docker network namespace and communicates over mutually authenticated TLS (mTLS). The high‑level flow is:
Presentation Layer (React SPA) → API Gateway (Traefik) → Service Layer (Go micro‑services) → Data Layer (PostgreSQL with pgcrypto & Row‑Level Security)
PDF Generation Service (Node.js + PDFKit) → Encrypted Object Store. All containers are orchestrated via a single docker‑compose.yml without external registries.

## 15. Presentation Layer
**Technology**: React 18, Vite, OpenSSL‑validated client certificates for mTLS.
**Responsibilities**: Capture patient demographics, insurance, and medical history; perform client‑side field‑level encryption using the Web Crypto API (AES‑256‑GCM) before transmission.
**Security Controls**:
- Content‑Security‑Policy: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'`;
- Referrer‑Policy: `strict-origin-when-cross-origin`;
- CSP nonce handling for dynamic scripts;
- CSP header and Subresource Integrity for third‑party libraries.

## 16. API Gateway
**Technology**: Traefik 2.10 (reverse proxy & TLS terminator).
**Exposed Endpoints**:
- `/api/v1/audit/` → Audit Log Service
- `/api/v1/patient/` → Patient Intake Service
- `/api/v1/pdf/` → PDF Generation Service
**Authentication**: OAuth2.0 Resource Owner Password Credentials flow; access tokens signed with RS256 and validated by each downstream service.
**Rate Limiting**: 100 requests/second per client IP; burst of 200; HTTP 429 on exceed.
**TLS**: TLS 1.3 enforced; client certificates required for mutual auth.

## 17. Service Layer – Audit Log Service
**Language**: Go 1.22, Gin framework.
**Core API Endpoints**:
- `POST /api/v1/audit/logs` – Create immutable audit entry.
- `GET /api/v1/audit/logs` – Query logs with RBAC filters (`user_id`, `action`, `date_range`).
**Request / Response Schemas**:

{
  "log_id": "uuid",
  "user_id": "uuid",
  "action": "CREATE|READ|UPDATE|DELETE|EXPORT",
  "resource": "string",
  "resource_id": "uuid",
  "timestamp": "RFC3339",
  "metadata": { }
}

{
  "logs": [
    {
      "log_id": "uuid",
      "user_id": "uuid",
      "action": "READ",
      "resource": "intake_record",
      "resource_id": "uuid",
      "timestamp": "RFC3339",
      "metadata": { }
    }
  ]
}

**Data Model** (PostgreSQL):
| Column | Type | Constraints | Description |
|---|---|---|---|
| log_id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier for the audit entry |
| user_id | UUID | NOT NULL, FOREIGN KEY → users(user_id) | Actor performing the action |
| action | VARCHAR(10) | NOT NULL, CHECK (action IN ('CREATE','READ','UPDATE','DELETE','EXPORT')) | Enumerated action type |
| resource | VARCHAR(30) | NOT NULL | Logical name of the protected resource |
| resource_id | UUID | NOT NULL | Identifier of the affected resource |
| timestamp | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Immutable event time (UTC) |
| metadata | JSONB | NULL | Additional context; encrypted if containing PHI |
**Immutability Enforcement**: INSERT‑only policy; UPDATE/DELETE disabled via a dedicated DB role (`audit_role`) with only INSERT privileges. Row‑Level Security (RLS) policies restrict SELECT to `admin_role` and `auditor_role`.
**Compliance**: Retention 7 years (FR‑003); write‑once storage satisfies NIST AU‑6.

## 5. Data Layer – PostgreSQL Instance
**Configuration**: `ssl = on`, `password_encryption = scram-sha-256`, `shared_buffers = 25% of RAM`.
**Roles & Privileges**:
- `admin_role` – full DDL/DML, audit log management.
- `clinician_role` – SELECT/INSERT on patient tables, limited to own patients via RLS.
- `frontdesk_role` – INSERT on intake tables, no SELECT on audit logs.
**Encryption**: Column‑level encryption using pgcrypto for PHI fields (`AES-256-GCM`). Disk‑level encryption via LUKS with TPM‑backed key storage.
**Backup Strategy**: Daily encrypted base‑backup stored on air‑gapped external media; incremental WAL archiving retained 30 days (NFR‑009).

## 14. PDF Generation Service
**Technology**: Node.js 20, PDFKit, OpenSSL for TLS client auth.
**Endpoint**: `POST /api/v1/patients/{patient_id}/export/pdf/{patient_id}` – Generates PDF, applies watermark containing `export_timestamp` and `user_id`, stores in encrypted object store (AES‑256‑GCM). Returns `{ "pdf_url": "https://storage/.../record_id.pdf", "export_audit_id": "uuid" }`.
**Authorization**: JWT scope `pdf:export` required; service validates scope before processing.
**Audit Integration**: After successful export, service calls `POST /api/v1/audit/logs` with action `EXPORT` and includes watermark metadata.
**Performance Metric**: Median PDF generation time ≤ 500 ms for 1 KB input (KPI‑030).

## 18. Deployment & Air‑Gap Considerations
All services are defined in a single `docker-compose.yml`. Key points:
- No external image registries; images built locally from vetted open‑source bases and signed with Notary v2.
- Volume mounts map encrypted host directories (`/var/lib/postgres`, `/var/lib/pdfstore`).
- Startup script (`entrypoint.sh`) verifies host network isolation (no internet access) before launching containers.
- Docker Compose version 2.x used; `depends_on` ensures correct start order.
- Healthchecks enforce TLS handshake success and DB connectivity before service becomes ready.

## 19. Traceability Matrix
| Component | Requirement ID(s) | KPI(s) | NFR(s) |
|---|---|---|---|
| Audit Log Service | FR‑003 | KPI‑042 (log write latency <100 ms) | NFR‑009 (encrypted backups) |
| PDF Generation Service | FR‑008 | KPI‑030 (watermark accuracy 100 %) | NFR‑011 (air‑gap compliance) |
| Presentation Layer | FR‑001 (view latency ≤2 s), FR‑006 (receipt ≤1 s) | KPI‑042, KPI‑030 | NFR‑009 |

## 20. Performance & Latency Requirements
- **View Latency (FR‑001)**: All UI read operations must render within 2 seconds p95 after form submission; measured from button click to data display. Backend read APIs (`GET /api/v1/patient/{id}`) must respond ≤150 ms under normal load (≤200 concurrent users).
- **Receipt Latency (FR‑006)**: After successful form submission the UI must display a confirmation receipt within 1 second; backend must acknowledge (`201 Created`) within 500 ms. Healthcheck metrics are exported to Prometheus and visualized in Grafana dashboards.
- **Audit Log Write Latency (KPI‑042)**: Log insertion must complete within 100 ms p95; achieved via INSERT‑only table and connection pooling.
- **PDF Export Latency (KPI‑030)**: PDF generation and storage must complete within 500 ms median; watermarking adds ≤50 ms overhead. All latency metrics are instrumented via OpenTelemetry spans.

## 18. Traceability to Project Requirements
FR-003 (full audit log) → audit_log entity and /api/v1/audit/logs endpoint.
FR-006 (confirmation receipt) → export endpoint returns export_audit_id.
NFR-009 (encrypted backups) → field‑level encryption description.
KPI-042 (audit log write latency <100 ms) → service design notes on async write queue.
FR-009 (Docker Compose deployment) → all services containerised and defined in docker‑compose.yml.
FR-001 (view latency ≤2 s p95) → added response‑time constraint to patient view API.
FR-006 (receipt latency ≤1 s) → added receipt endpoint latency spec.

---

## Audit Log API Contract – PostgreSQL Data Model

### 15. Data Model
| Entity | Field | Data Type | Required | Constraints |
|--------|------|-----------|----------|-------------|
| audit_log | log_id | UUID | Yes | Primary key, generated by pgcrypto `gen_random_uuid()` |
| audit_log | patient_id | UUID | Yes | Foreign key → patient.patient_id, ON DELETE RESTRICT |
| audit_log | user_id | UUID | Yes | Foreign key → user.user_id |
| audit_log | action_type | TEXT | Yes | CHECK (action_type IN ('CREATE','READ','UPDATE','DELETE','EXPORT')) |
| audit_log | action_timestamp | TIMESTAMPTZ | Yes | DEFAULT now() |
| audit_log | ip_address | INET 	No 	Valid IPv4/IPv6 address 																																																 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 No 	 Valid IPv4/IPv6 address 	 	 	 	 	 	 	 	 	 \ t? (Note: placeholder for formatting) |
| audit_log | details | JSONB 	No 	Stores request payload snapshot, encrypted at rest via pgcrypto column encryption 					\ t? |
| audit_log | details_hash | TEXT 	No 	SHA‑256 hash of original request payload for tamper detection 	\ t? |
| patient   | patient_id   | UUID   	Yes   	Primary key   		\ t? |
| patient   ... (remaining rows omitted for brevity); All PHI fields (e.g., details JSONB) use pgcrypto column‑level encryption and row_security policies restrict SELECT/UPDATE/DELETE to roles matching required permission (admin, clinician, front_desk). |

### 16. API Endpoints
| Endpoint               | Method | Purpose                                            | Request Schema                                            | Response Schema                                            | Auth                                          |
|-----------------------|--------|----------------------------------------------------|-----------------------------------------------------------|-----------------------------------------------------------|-----------------------------------------------|
| /api/v1/audit/logs    | POST   | Create a new audit entry after any protected operation   | {"patient_id":"uuid","action_type":"string","ip_address":"string","details":"object"}   | {"log_id":"uuid","status":"created"}               | Bearer JWT with scope `audit:write`            |
| /api/v1/audit/logs/{log_id}   | GET    | Retrieve a specific audit entry (admin only)          | None (path param)                                          | {"log_id":"uuid","patient_id":"uuid","user_id":"uuid","action_type":"string","action_timestamp":"datetime","ip_address":"string","details":"object","details_hash":"string"}   | Bearer JWT with scope `audit:read`             |
| /api/v1/audit/logs?patient_id=...&action_type=...&start_time=...&end_time=...   | GET    | Query audit entries for reporting and compliance checks   | Query parameters as shown; { "logs": [ { ... }, { ... } ] }                         |; Bearer JWT with scope `audit:read`            |; All request and response bodies conform to JSON Schema SCH-001. |

### 17. Error Taxonomy
| Error Code            | HTTP Status | Description                                            | User Message                                            | Retryable? |
|----------------------|-------------|--------------------------------------------------------|--------------------------------------------------------|-----------|
| ERR-001-VALIDATION   | 400         | Request payload fails JSON schema validation           | "Invalid request format; please correct the highlighted fields." |
| ERR-002-AUTHORIZATION| 401         | Missing or invalid JWT token                          | "Authentication required; please log in again." | No |
| ERR-003-FORBIDDEN    |  403         |  Authenticated user lacks required scope or role |  "You do not have permission to perform this action." |  No |
| ERR-004-NOTFOUND     |  404         |  Requested log entry does not exist or has been purged per retention policy |  "The requested audit record could not be found." |  No |
| ERR-005-DBFAILURE   |  500         |  Unexpected database error, e.g., connection loss or constraint violation |  "A server error occurred; please try again later." |  Yes |
| ERR-006-RATELIMIT   |  429         |  API rate limit exceeded at gateway |  "Too many requests; please retry after a short pause." |  Yes |
| ERR-007-LATENCYVIOLATION |  503   |  Service unable to meet KPI‑042 latency target (<100 ms) for audit log write |  "Service temporarily overloaded; try again later." |  Yes |

### 14. Integration Points
- Patient Service: Calls POST `/api/v1/audit/logs` after any CREATE/UPDATE/READ/DELETE on patient, insurance, or medical_history tables.
- If Patient Service is unavailable, Audit Service queues the log entry in RabbitMQ exchange `audit_events` and retries every 30 seconds; after 5 attempts the entry is persisted to dead‑letter table `audit_log_dlq` for later analysis.
- Receipt Service: After successful form submission, calls `/api/v1/receipt` (not shown) which returns a receipt ID within 1 second (FR‑006) and logs an audit entry.
- View Service: Patient record retrieval endpoint `/api/v1/patients/{id}` guarantees p95 response time ≤2 seconds (FR‑001) and logs a READ audit entry.
---
*Document generated by Refiner role for the Audit Log API Contract.*

## Technical Design Specification for Patient Intake Audit Logging Service

### 15. Architecture Diagram (textual description)
- **Client Applications** (Web UI, Mobile) → **AuthGateway (SVC-002)** → **AuditLogService (SVC-001)** → **PostgreSQL (encrypted at rest)**
- **Vault** provides secret management for DB credentials and JWT public keys.
- **Prometheus** scrapes metrics from both services for alerting on error rates and latency.
- **Docker Compose** orchestrates all containers in an air‑gapped environment.

### 16. Service Boundaries
| Service | Responsibility | Dependencies | Events Emitted | Events Consumed |
|---|---|---|---|---|
| **AuditLogService (SVC-001)** | Persist encrypted audit entries, enforce row‑level security (RLS), compute hash chain for integrity, expose Prometheus metrics | PostgreSQL, Vault, TLS termination proxy | `AuditLogCreated`, `AuditExportRequested` | None |
| **AuthGateway (SVC-002)** | Validate Bearer tokens and client certificates, map to RBAC roles, enforce least‑privilege access | Identity Provider (OIDC), Vault (CRL) | `AuthSuccess`, `AuthFailure` | None |

### 17. API Specifications

#### 17.1 Endpoints
**POST /api/v1/audit/logs** – Record a new audit event

{
  "action": "string",
  "resource_id": "uuid",
  "user_id": "uuid",
  "details": "string"
}

_Response (201 Created):

{
  "log_id": "uuid",
  "status": "created",
  "timestamp": "2026-05-03T12:34:56Z"
}

**GET /api/v1/audit/logs** – Query audit events with optional filters

{
  "resource_id": "uuid?",
  "user_id": "uuid?",
  "action": "string?",
  "start_time": "datetime?",
  "end_time": "datetime?",
  "page": "int",
  "page_size": "int"
}

_Response (200 OK):

{
  "logs": [
    {
      "log_id":"uuid",
      "action":"string",
      "resource_id":"uuid",
      "user_id":"uuid",
      "timestamp":"datetime",
      "details":"string"
    }
  ],
  "total": "int",
  "page": "int",
  "page_size": "int"
}

**POST /api/v1/audit/logs/export** – Export filtered logs as PDF with watermark

{
  "filter": {
    "resource_id": "uuid?",
    "user_id": "uuid?",
    "action": "string?",
    "start_time": "datetime?",
    "end_time": "datetime?"
  }
}

_Response (202 Accepted):

{
  "export_url": "https://service.local/exports/abcd1234.pdf",
  "expires_at": "2026-05-04T12:00:00Z"
}

#### 17.2 Error Handling (expanded per reviewer feedback)
| Error Code | HTTP Status | Description | User Message | Retryable |
|---|---|---|---|---|
| `ERR-001` | 400 | Malformed request payload | "The request could not be parsed. Please check the JSON format." | false |
| `ERR-002` | 401 | Missing or invalid authentication token | "Authentication required. Please log in again." | false |
| `ERR-003` | 403 | Insufficient permissions for the requested action | "You do not have permission to perform this operation." | false |
| `ERR-004` | 429 | Rate limit exceeded on audit ingestion endpoint | "Too many requests. Please try again later." | true |
| `ERR-005` | 500 | Internal server error during log persistence | "An unexpected error occurred. Please contact support." | true |
| `ERR-006` | 504 | Export service timeout | "The export request timed out. Please retry later." | true |

### 18. Docker‑Compose & Air‑Gap Deployment
yaml
version: "3.8"
services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: patient_intake
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - pg_data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "app_user"]
      interval: 30s
      timeout: 10s
      retries: 5

  audit_service:
    build: ./audit_service
    environment:
      - DATABASE_URL=postgresql://app_user:${DB_PASSWORD}@postgres:5432/patient_intake
      - JWT_PUBLIC_KEY=/run/secrets/jwt_pub_key
    secrets:
      - db_password
      - jwt_pub_key
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - backend
    ports:
      - "8082:8080"
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

networks:
  backend:
    driver: bridge
volumes:
  pg_data:
secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_pub_key:
    file: ./secrets/jwt_pub_key.pem

**Air‑Gap Procedure**:
1. Copy the entire repository (including `docker-compose.yml`, secret files, and source directories) onto an isolated USB drive.
2. On the target host, install Docker Engine 20+ and Docker Compose.
3. Load container images from internal registry or local tar archives (`docker load -i audit_service.tar`).
4. Run `docker compose up -d`. No external network calls are made because all services are defined within the private backend network.

### 19. Compliance Mapping
| Requirement ID | Description | Design Artifact |
|---|---|---|
| FR-001 | View patient intake records within 2 s (p95) | Service latency metric `audit_log_request_duration_seconds` with SLA <100 ms ensures overall response time budget. |
| FR-002 | Role‑based access control for patient records | RLS policies on `audit_log` table; AuthGateway RBAC mapping. |
| FR-003 | Log all view actions with retention 7 years | `audit_log` schema, retention policy, immutable storage. |
| REQ-001 | WCAG 2.1 AA for form content (not directly applicable) – noted for UI layer. |
| REQ-002 | Keyboard navigation – UI concern; documented for downstream teams. |
| KPI-042 | Audit log write latency <100 ms and monitoring – implemented via Prometheus histogram. |

### 20. Open Issues / Knowledge Gaps
- Exact HIPAA § 164.312(a)(2)(iv) technical safeguard wording for encryption key management.
- Performance characteristics of PostgreSQL RLS with >10 M audit rows.

*End of Document*
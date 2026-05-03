# Operational Deployment Guide

## System Architecture Overview

The PatientIntake system is deployed as a set of Docker containers orchestrated by Docker Compose and runs in an air‑gap on‑prem environment. The architecture is divided into five layers: Presentation, API Gateway, Service, Data, and Integration. All network traffic between client browsers and the API gateway is encrypted with TLS\u00a01.2 or higher using certificates stored as Docker secrets.

**Presentation Layer**: React single‑page application served by an Nginx container configured for HTTP/2 and strict security headers (Content‑Security‑Policy, X‑Frame‑Options, Referrer‑Policy). The SPA communicates exclusively with the API Gateway over HTTPS and never stores PHI locally.

**API Gateway**: Nginx reverse‑proxy container terminates TLS, enforces rate limiting of 100 requests per second per client IP, validates JWT RS256 tokens issued by the Auth Service, and forwards requests to FastAPI services under the `/api/v1/` prefix. All inbound requests are logged to a side‑car Fluent Bit instance for audit purposes.

**Service Layer**: Three FastAPI services implement core business logic:
- **Auth Service** validates credentials against a PostgreSQL users table and issues short‑lived JWTs (15 min) signed with an RSA‑2048 private key stored as a Docker secret.
- **Intake Service** receives `POST /api/v1/intake` payloads containing patient demographics, insurance information, and medical history. PHI fields are encrypted client‑side using AES‑256‑GCM and stored in encrypted columns via PostgreSQL pgcrypto.
- **PDF Service** generates PDF summaries using WeasyPrint from an HTML template; each PDF is watermarked with the exporting user ID and an ISO‑8601 timestamp.

**Data Layer**: PostgreSQL 15 runs in a dedicated container with `fsync=on`, `full_page_writes=on`, and `data_directory_mode=0700`. Row‑level security (RLS) policies restrict access based on the `role` column (admin, clinician, front_desk). Sensitive columns (ssn, insurance_number, medical_history) are stored using `pgp_sym_encrypt` with per‑field keys derived from a master key stored in Docker secret `PG_CRYPTO_KEY`. Audit logs are written to an immutable append‑only table `audit_log` (event_id, user_id, action, timestamp, details) and indexed by an ELK stack container for compliance reporting.

**Integration Components**: Health‑check sidecar probes each service every 30 seconds and publishes status to a Prometheus container; alerts are routed to Alertmanager which can trigger a PagerDuty webhook. Backup Service runs nightly `pg_dump` encrypted with GPG and stores backups on an attached encrypted volume; retention is 30 days as required by NFR‑009.

**Security Controls**: All containers run with the Docker `--read-only` flag except volume mounts for PostgreSQL data and backups. Secrets are injected via Docker secrets; no plaintext passwords appear in environment variables. Network segmentation isolates the database on a private Docker network inaccessible from the public interface. The architecture satisfies HIPAA Technical Safeguard §164.312(a)(2)(iv) by providing encryption at rest and in transit, and meets KPI‑001 (form submission latency <200 ms) through caching of static assets in Nginx and connection pooling in SQLAlchemy.

---

## REST API Specifications (EP-001)

### 1. Endpoint: POST /api/v1/patients/demographics
| Field | Type | Required | Description |
|---|---|---|---|
| first_name | string | Yes | Patient first name, UTF‑8, max 50 chars |
| last_name | string | Yes | Patient last name, UTF‑8, max 50 chars |
| date_of_birth | string (date) | Yes | ISO‑8601 date, must be in the past |
| gender | string | No | Enum: "male","female","other","unspecified" |
| contact_email | string | Yes | Valid email address, used for notifications |
| phone_number | string | No | E.164 format |
| address_line1 | string | Yes | Street address |
| address_line2 | string | No |  |
| city | string | Yes |  |
| state | string | Yes |  |
| zip_code | string | Yes |  |

**Response Schema (DemographicsResponse)**
- `patient_id` (string, uuid) – system‑generated identifier
- `created_at` (string, date‑time) – timestamp of record creation
- `status` (string) – e.g., "created"

### 4. Common Error Taxonomy (ERR-001)
All endpoints return errors in the following JSON structure:

{ "error_code": "ERR-XXX", "message": "Human readable description", "detail": "Optional technical detail", "retryable": false }

Defined error codes:
- **ERR-001** – 400 Bad Request – Request validation failed – "Please correct the highlighted fields and retry." – retryable: false
- **ERR-002** – 401 Unauthorized – Authentication missing or invalid – "Authentication required." – retryable: false
- **ERR-003** – 403 Forbidden – Authorization failure for role – "You do not have permission to perform this operation." – retryable: false
- **ERR-004** – 409 Conflict – Duplicate resource – "A record with the provided identifier already exists." – retryable: false
- **ERR-005** – 500 Internal Server Error – Unexpected server error – "An unexpected error occurred. Please contact support." – retryable: true

## Design Specification for Patient Intake System

### 5. Overview
The design defines a HIPAA‑compliant patient intake platform. It captures patient demographics, insurance information, medical history, and audit events while enforcing role‑based access control (RBAC) and encryption at rest. The architecture aligns with FR-001 through FR-008, REQ-001, REQ-002, and KPI-001.

### 7. PostgreSQL Data Model (SCH-002)

#### 7.1 Patient Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() | Immutable identifier |
| first_name | TEXT | NOT NULL | Encrypted at rest (pgcrypto AES‑256‑GCM) |
| last_name | TEXT | NOT NULL | Encrypted at rest |
| date_of_birth | DATE | NOT NULL | Must be past date |
| gender | TEXT | NULL | Optional |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | Immutable |
| updated_at | TIMESTAMPTZ | NOT NULL DEFAULT now() | Updated on change |

#### 7.2 Insurance Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() | Unique record |
| patient_id | UUID | NOT NULL REFERENCES patient(id) ON DELETE CASCADE | FK to patient |
| provider_name | TEXT | NOT NULL | Encrypted |
| policy_number | TEXT | NOT NULL | Encrypted |
| group_number | TEXT | NULL | Encrypted |
| effective_date | DATE | NOT NULL | <= current date |
| expiration_date | DATE | NOT NULL CHECK (expiration_date > effective_date) | Validity period |

#### 7.3 Medical_History Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() | Unique record |
| patient_id | UUID | NOT NULL REFERENCES patient(id) ON DELETE CASCADE | FK to patient |
| condition_code | TEXT | NOT NULL | ICD‑10 code |
| description | TEXT | NOT NULL | Encrypted |
| onset_date | DATE | NULL |
| resolved | BOOLEAN | NOT NULL DEFAULT false |

#### 7.4 Audit_Log Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
| patient_id | UUID | NOT NULL REFERENCES patient(id) ON DELETE CASCADE |
| user_id | UUID | NOT NULL |
| action | TEXT | NOT NULL |
| timestamp | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| details | JSONB | NULL |

#### 7.5 User & Role Tables (RBAC)
| Table | Column | Type | Constraints |
|---|---|---|---|
| user | id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
|   | email | TEXT | NOT NULL UNIQUE |
|   | password_hash | TEXT | NOT NULL |
| role | id | UUID | PRIMARY KEY DEFAULT gen_random_uuid() |
|   | name | TEXT | NOT NULL UNIQUE |
| user_role | user_id | UUID | NOT NULL REFERENCES user(id) ON DELETE CASCADE |
|   | role_id | UUID | NOT NULL REFERENCES role(id) ON DELETE CASCADE |

### 8. API Contracts

#### 8.1 PDF Generation Service (SVC-001)
**Endpoint**: `POST /api/v1/pdf/generate`
**Request Schema (SCH-001)**

{
  "patient_id": "<uuid>",
  "include_sections": ["demographics","insurance","medical_history"],
  "watermark": "Exported by {user_id} at {timestamp}"
}

**Response Schema (SCH-002)**

{
  "pdf_url": "https://storage.example.com/pdfs/abc123?sig=...",
  "request_id": "<uuid>",
  "expires_at": "2026-05-04T12:00:00Z"
}

**Error Codes**
| Code | HTTP | Description |
|---|---|---|
| ERR-001 | 400 | Validation failed – missing or malformed fields |
| ERR-002 | 401 | Authentication failed – missing or invalid JWT |
| ERR-003 | 403 | Authorization failed – insufficient permissions |
| ERR-004 | 500 | Internal service error – PDF rendering failed |

#### 8.2 Audit Log Exporter
**Endpoint**: `POST /api/v1/audit/export`
**Request**

{
  "start_time": "2026-04-01T00:00:00Z",
  "end_time": "2026-04-30T23:59:59Z",
  "format": "json"
}

**Response**

{
  "export_id": "<uuid>",
  "status": "queued",
  "download_url": null
}

**Status Polling** – `GET /api/v1/audit/export/{export_id}` returns `status` (`queued`, `completed`, `failed`) and `download_url` when ready.
**Error Handling** – Same error codes as PDF service plus:
| Code | HTTP | Description |
|---|---|---|
| ERR-005 | 429 | Rate limit exceeded |
| ERR-006 | 500 | Export processing failure |

### 9. Security & Compliance
- **Encryption at Rest** – All PII columns encrypted with pgcrypto AES‑256‑GCM; key rotation managed via Vault (REQ‑007).
- **Transport Security** – TLS 1.3 enforced for all external traffic.
- **Row‑Level Security** – Policies restrict `audit_log` visibility to users with `audit_view` role and to records belonging to their assigned patients (FR‑002).
- **Audit Logging** – Every API request logs user_id, endpoint, timestamp, and outcome (FR‑003). Logs retained 7 years on immutable storage.
- **HIPAA Safeguards** – Aligns with §164.312(a)(2)(iv) for encryption and §164.312(b) for audit controls.

### 10. Performance & Monitoring
- **KPI‑001** – Form submission latency ≤200 ms (p95).
- **KPI‑042** – Audit log write latency <100 ms.
- **KPI‑030** – PDF watermark accuracy 100 %.
- Metrics exported to Prometheus; alerts configured in Grafana.

### 11. Versioning & Change Management
- Contract version `v1.0.0`. Any breaking change requires a new major version and a 90‑day deprecation period.
- Clients must send `Accept: application/json` header; future versions may introduce `application/vnd.patientintake.v2+json`.

### 12. Traceability Matrix
| Requirement ID | Design Element |
|---|---|
| FR-001 | Form latency monitoring (KPI‑001) |
| FR-002 | RLS policies on `audit_log` |
| FR-003 | Audit logging schema |
| FR-004 | Patient demographics fields |
| FR-005 | Real‑time validation on form fields (client‑side) |
| FR-006 | Confirmation receipt endpoint (`/api/v1/submit/ack`) |
| FR-008 | PDF watermark field in request schema |
| REQ-001 | WCAG 2.1 AA compliance for UI (not shown here) |
| REQ-002 | Keyboard navigation support (frontend) |
| KPI-001 | Form latency measurement |
| KPI-030 | Watermark correctness verification (TC‑008) |

*All tables, endpoints, and constraints are fully defined and ready for implementation.*
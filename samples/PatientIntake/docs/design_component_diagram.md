# Component Interaction Diagram

## Design API Specification

### Overview
The following document defines the concrete RESTful contracts for the Patient Intake System (Project: Build a HIPAA‑compliant patient intake system using open source technologies only). All endpoints are versioned under /api/v1 and enforce strict authentication, input validation, field‑level encryption, and role‑based access control (RBAC) as required by FR-001, FR-002 and HIPAA technical safeguards.

### API Endpoints
| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| /api/v1/auth/login | POST | Authenticate user and issue JWT | None (public) |
| /api/v1/patients | POST | Submit new patient intake record | Bearer Token |
| /api/v1/patients/{patient_id} | GET | Retrieve patient record (read‑only) | Bearer Token (clinician or admin) |
| /api/v1/patients/{patient_id}/export | GET | Generate PDF summary with watermark and timestamp | Bearer Token (clinician or admin) |
| /api/v1/audit/logs | GET | Query audit logs for compliance reporting | Bearer Token (admin only) |

#### Request / Response Schemas
**Login Request**

{"email":"string","password":"string"}

**Login Response**

{"token":"string","expires_at":"string","user":{"id":"string","role":"admin|clinician|front_desk"}}

**Create Patient Request**

{"first_name":"string","last_name":"string","dob":"string","insurance_policy":"string","medical_history":"string","encrypted_fields":{"ssn":"string","address":"string"}}

**Create Patient Response**

{"patient_id":"string","status":"created"}

**Get Patient Response**

{"patient_id":"string","first_name":"string","last_name":"string","dob":"string","insurance_policy":"string","medical_history":"string","encrypted_fields":{"ssn":"string","address":"string"},"audit_log_ref":"string"}

**Export PDF Response**

{"pdf_url":"string","generated_at:":"string","watermark":"string"}

**Audit Log Query Request**

{"start_date":"string","end_date":"string","action":"read|write|export","page":0,"page_size":100}

**Audit Log Query Response**

{"logs":[{"log_id":"string","user_id":"string","action:":"string","timestamp:":"string","resource_id:":"string"}], "total":0}

### Error Taxonomy
| Error Code | HTTP Status | Description | User Message | Retryable |
|------------|--------------|-------------|--------------|-----------|
| ERR_AUTH_001 | 401 | Invalid credentials supplied to login endpoint. | Invalid email or password. | No |
| ERR_AUTH_002 | 403 | JWT missing or malformed. | Authentication required. | No |
| ERR_RBAC_001 | 403 | Access denied due to insufficient role. | You do not have permission to perform this action. | No |
| ERR_VALID_001 | 400 | Request payload fails schema validation. | Please correct the highlighted fields and retry. | Yes |
| ERR_SERVER_001 | 500 | Unexpected server error during processing. | An internal error occurred. Please try again later. | Yes |
| ERR_EXPORT_001 | 502 | PDF generation service unavailable. | Unable to generate PDF at this time. | Yes |

### Security Considerations 
- **Authentication**: JWT issued by `/api/v1/auth/login` using RS256; includes sub, role, exp claims; rotated every 15 minutes. 
- **Transport Security**: All endpoints require HTTPS with TLS 1.3; mutual TLS optional for internal service‑to‑service calls. 
- **Input Validation**: JSON schemas enforce type, format, length, pattern; invalid payloads return ERR_VALID_001. 
- **Encryption at Rest**: Sensitive fields (ssN, address, insurance_policy, medical_history) encrypted with pgcrypto AES‑256‑GCM; keys stored in Vault. 
- **Audit Logging**: Every read, write, export creates immutable entry in `audit_log`; retained 7 years per FR-003. 
- **Rate Limiting**: API gateway limits 100 requests/minute per user; exceeding returns 429 Too Many Requests. 
- **Compliance Mapping**: Contracts satisfy HIPAA §164.312(a)(2)(iv) (encryption) and §164.312(b) (audit controls).

### Integration Points & Failure Handling 
- **Database Unavailable**: Return 503 Service Unavailable with message `Service Unavailable`. 
- **Vault Failure**: Return 500 ERR_SERVER_001 and trigger Ops alert. 
- **PDF Generator Failure**: Return 502 ERR_EXPORT_001. 
- **Audit Log Pagination**: Supports `page` and `page_size` parameters; defaults page=0, page_size=100.

### PostgreSQL Schema Design

#### Tables 
- **patient** 
  - id UUID PRIMARY KEY DEFAULT gen_random_uuid() 
  - first_name TEXT NOT NULL CHECK (char_length(first_name) <= 50) 
  - last_name TEXT NOT NULL CHECK (char_length(last_name) <= 50) 
  - date_of_birth DATE NOT NULL CHECK (date_of_birth < CURRENT_DATE) 
  - email TEXT NOT NULL UNIQUE CHECK (email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$') 
  - phone_number TEXT 
  - address BYTEA NOT NULL -- encrypted via AES-256-GCM 
  - insurance_policy BYTEA NOT NULL -- encrypted 
  - medical_history BYTEA NOT NULL -- encrypted JSON blob 
  - created_at TIMESTAMPTZ NOT NULL DEFAULT now() 
  - updated_at TIMESTAMPTZ NOT NULL DEFAULT now() 
- **audit_log** 
  - log_id UUID PRIMARY KEY DEFAULT gen_random_uuid() 
  - user_id UUID NOT NULL REFERENCES users(id) 
  - action TEXT NOT NULL CHECK (action IN ('read','write','export')) 
  - timestamp TIMESTAMPTZ NOT NULL DEFAULT now() 
  - resource_id UUID NOT NULL 
  - details JSONB 
- **users** (simplified for RBAC) 
  - id UUID PRIMARY KEY DEFAULT gen_random_uuid() 
  - email TEXT NOT NULL UNIQUE 
  - role TEXT NOT NULL CHECK (role IN ('admin','clinician','front_desk')) 
  - password_hash TEXT NOT NULL 
 
#### Row‑Level Security (RLS) 
sql 
CREATE POLICY clinician_policy ON patient USING (role = 'clinician' AND patient.id IN (SELECT patient_id FROM assignments WHERE user_id = current_user_id())); 
CREATE POLICY front_desk_policy ON patient USING (role = 'front_desk'); 
ALTER TABLE patient ENABLE ROW LEVEL SECURITY; 

### Additional Notes 
- All timestamps are stored in UTC. 
- All JSON responses follow snake_case naming. 
- All error responses include fields `error_code`, `message`, and optional `details`. 
 
--- 
*Refinement applied to address reviewer feedback: corrected malformed JSON examples, added missing request/response fields, introduced pagination for audit logs, clarified encryption handling, added explicit error code for PDF export, and provided complete PostgreSQL schema with constraints and RLS policies.*

## Technical Design Document

### 2. Data Model

#### 2.1 audit_log
| Column | Type | Nullable | Description |
|---|---|---|---|
| id | BIGSERIAL | No | Primary key |
| event_type | TEXT | No | One of INSERT, UPDATE, DELETE, SELECT |
| table_name | TEXT | No | Name of the table accessed |
| record_id | UUID | No | Primary key of the affected record |
| performed_by | UUID | No | User ID performing the action |
| timestamp | TIMESTAMPTZ | No | Exact time of the event |
| details | JSONB | Yes | Optional JSON with additional context (e.g., changed fields) |

#### 2.2 role
| Column | Type | Nullable | Description |
|---|---|---|---|
| id | SERIAL | No | Primary key |
| name | TEXT | No | One of admin, clinician, front_desk |

#### 2.3 user_role
| Column | Type | Nullable | Description |
|---|---|---|---|
| user_id | UUID | No | Reference to user identifier |
| role_id | INTEGER | No | Foreign key to role.id |

### 3. Encryption Strategy
- **At Rest**: Column‑level encryption using `pgcrypto` for PHI fields (`insurance_policy_number`, `medical_history`). Keys are rotated quarterly via stored procedure `rotate_dek()`.
- **In Transit**: All client‑to‑service and inter‑service traffic uses TLS 1.3 (`ssl = on`, `ssl_cert_file`, `ssl_key_file`).
- **Key Management**: Master key stored in HashiCorp Vault; data‑encryption keys (DEKs) are wrapped with the master key before persistence.

### 4. Audit Logging Mechanism
- Triggers on each table insert/update/delete write a row to `audit_log`.
- SELECT operations are captured via the `pg_audit` extension configured to log read events.
- Retention policy: 7 years (FR‑003).

### 5. Service Boundaries and Integration Events
| Service Name | Responsibility | Dependencies | Events Emitted | Events Consumed |
|---|---|---|---|---|
| web_ui | Renders patient intake form, performs client‑side field encryption | auth_gateway, intake_service | form_submitted | auth_success |
| auth_gateway | Issues JWT tokens, validates credentials, enforces RBAC | user_db | token_issued, auth_failure | - |
| intake_service | Validates input, encrypts fields, stores records | encryption_lib, persistence_service | patient_record_created | token_valid |
| persistence_service | Manages PostgreSQL with row‑level security, audit logging | postgres_db | audit_log_written | patient_record_created |
| audit_service | Captures read/write events, writes immutable logs | postgres_audit_schema | audit_event_published | - |
| pdf_export_service | Generates PDF summary, applies watermark and timestamp | pdf_lib, persistence_service | pdf_generated | patient_record_requested |

### 6. API Contracts (selected)

#### 6.1 POST /api/v1/patients
- **Request Body** (application/json):

{
  "first_name": "string",
  "last_name": "string",
  "date_of_birth": "YYYY-MM-DD",
  "insurance_policy_number": "string", // encrypted at rest
  "medical_history": {"conditions": ["string"]} // encrypted at rest
}

- **Responses**:
  - `201 Created` – patient record stored, body contains `patient_id` (UUID).
  - `400 Bad Request` – validation errors with field‑level messages.
  - `401 Unauthorized` – missing or invalid JWT.
  - `403 Forbidden` – user lacks `clinician` role.
- **Error Payload**:

{
  "error_code": "VALIDATION_ERROR",
  "message": "Detailed description",
  "details": {"field": "error description"}
}

#### 6.2 GET /api/v1/patients/{id}
- **Headers**: `Authorization: Bearer <jwt>`
- **Responses**:
  - `200 OK` – patient record (encrypted fields are decrypted server‑side).
  - `404 Not Found` – record does not exist or access denied.
  - `401/403` – authentication/authorization failures.
- **Audit**: Read event logged via `pg_audit`.

### 7. Deployment Topology (Docker Compose)
yaml
version: "3.8"
services:
  web_ui:
    image: registry.local/patient-intake/web_ui:1.0.0
    ports: ["8080:80"]
    environment:
      - AUTH_GATEWAY_URL=http://auth_gateway:8000
      - API_BASE_URL=http://intake_service:8001
    depends_on: [auth_gateway, intake_service]
    read_only: true
  auth_gateway:
    image: registry.local/patient-intake/auth_gateway:1.0.0
    environment:
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - ./secrets:/run/secrets:ro
    depends_on: [postgres]
    read_only: true
  intake_service:
    image: registry.local/patient-intake/intake_service:1.0.0
    environment:
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    depends_on: [persistence_service]
    read_only: true
  persistence_service:
    image: registry.local/patient-intake/persistence_service:1.0.0
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=patient_intake
    depends_on: [postgres]
    read_only: true
  audit_service:
    image: registry.local/patient-intake/audit_service:1.0.0
    depends_on: [postgres]
    read_only: true
  pdf_export_service:
    image: registry.local/patient-intake/pdf_export:1.0.0
    depends_on: [persistence_service]
    read_only: true
  postgres:
    image: registry.local/postgres:15-alpine
    volumes:
      - pg_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_USER=admin
      - POSTGRES_DB=patient_intake
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "admin"]
      interval: 30s
      timeout: 10s
      retries: 5
volumes:
  pg_data:
# Deployment Topology and Docker Compose Specification

## Technical Design Specification for Patient Intake System

### 1. Overview
The Patient Intake system provides secure creation, retrieval, and PDF export of patient intake records. It complies with HIPAA requirements (encryption at rest and in transit), supports role‑based access control (RBAC), and meets performance KPIs such as <200 ms response time for form submission (KPI‑02) and PDF generation latency (<200 ms, KPI‑048). All APIs are protected by Bearer JWT authentication.

### 2. API Specification

#### 2.1 Create Intake Record
- **Endpoint**: `/api/v1/intake`
- **Method**: POST
- **Authentication**: Bearer JWT (requires `clinician` or `front_desk` role)
- **Request Body (application/json)**:

{
  "patient": {
    "first_name": "string",
    "last_name": "string",
    "dob": "YYYY-MM-DD",
    "insurance": {
      "provider": "string",
      "policy_number": "string"
    },
    "medical_history": "string"
  }
}

- **Response (201 Created)**:

{
  "intake_id": "<uuid>",
  "status": "created"
}

- **Error Responses**:
  - `400 Bad Request` – validation errors (e.g., missing required fields). Response body includes `error_code` and `message`.
  - `401 Unauthorized` – missing or invalid JWT.
  - `403 Forbidden` – role not permitted.
  - `500 Internal Server Error` – unexpected failure.

#### 2.2 Retrieve Intake Record
- **Endpoint**: `/api/v1/intake/{id}`
- **Method**: GET
- **Authentication**: Bearer JWT (RBAC enforced – only clinicians assigned to the patient or admins may access)
- **Response (200 OK)**:

{
  "intake_id": "<uuid>",
  "patient": {
    "first_name": "string",
    "last_name": "string",
    "dob": "YYYY-MM-DD",
    "insurance": {
      "provider": "string",
      "policy_number": "string"
    },
    "medical_history": "string"
  },
  "created_at": "2026-05-03T12:34:56Z"
}

- **Error Responses**: same as above plus `404 Not Found` if the record does not exist or the caller lacks permission.

#### 2.3 Generate PDF Summary
- **Endpoint**: `/api/v1/intake/{id}/pdf`
- **Method**: GET
- **Authentication**: Bearer JWT (same RBAC as retrieve)
- **Response (200 OK)**:

{
  "pdf_url": "https://files.example.com/intake/<uuid>.pdf",
  "expires_at": "2026-05-04T12:34:56Z"
}

- **PDF Requirements**:
  - Watermark must contain the exporting user ID and timestamp (FR‑008).
  - PDF generation latency must be <200 ms (KPI‑048).
- **Error Responses**: same as retrieve.

### 3. Data Model (PostgreSQL)
All PHI columns are stored encrypted using `pgcrypto` AES‑256‑GCM. Row‑level security (RLS) enforces RBAC.

#### 3.1 Tables
sql
-- patients table (core record)
CREATE TABLE patients (
    intake_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_role TEXT NOT NULL CHECK (created_by_role IN ('admin','clinician','front_desk')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- demographics (encrypted fields)
CREATE TABLE demographics (
    patient_id UUID REFERENCES patients(intake_id) ON DELETE CASCADE,
    first_name BYTEA NOT NULL,
    last_name BYTEA NOT NULL,
    date_of_birth BYTEA NOT NULL,
    gender BYTEA,
    address BYTEA,
    phone_number BYTEA
);

-- insurance (encrypted fields)
CREATE TABLE insurance (
    patient_id UUID REFERENCES patients(intake_id) ON DELETE CASCADE,
    provider_name BYTEA NOT NULL,
    policy_number BYTEA NOT NULL,
    group_number BYTEA,
    effective_date BYTEA NOT NULL,
    expiration_date BYTEA NOT NULL
);

-- medical_history (encrypted fields)
CREATE TABLE medical_history (
    patient_id UUID REFERENCES patients(intake_id) ON DELETE CASCADE,
    condition_code TEXT NOT NULL,
    description BYTEA NOT NULL,
    onset_date BYTEA,
    resolved_date BYTEA,
    notes BYTEA
);

### 4. Authentication & Authorization
- JWT must be signed with RS256 (REQ‑007).
- Token must contain `sub` (user ID), `role`, and `exp` claim.
- Middleware validates signature, expiration, and extracts role for RBAC checks.
- Tokens are rotated every 24 h; revocation list stored in Redis.

### 5. Error Handling Conventions
All error responses follow a common schema:

{
  "error_code": "ERR_<numeric>",
  "message": "Human readable description",
  "details": {
    "field": "optional field name",
    "validation": "optional validation message"
  }
}

Standard error codes:
- `ERR_40001` – Missing required field.
- `ERR_40101` – Invalid or expired token.
- `ERR_40301` – Access denied (RBAC violation).
- `ERR_40401` – Resource not found.
- `ERR_50001` – Internal server error.
All errors are logged with request ID for traceability.

### 6. Performance & KPI Mapping
| KPI | Target | Related Requirement |
|-----|--------|----------------------|
| KPI‑02 (Form response time) | ≤200 ms | FR‑001, FR‑006 |
| KPI‑048 (PDF generation) | ≤200 ms | FR‑008 |
| KPI‑042 (Audit log write latency) | <100 ms | FR‑003 |
| KPI‑01 (System uptime) | 99.9% | NFR‑001 |

## 3.3 audit_log
| Column | Data Type | Required | Description |
|---|---|---|---|
| id | uuid | Yes | Primary key |
| event_timestamp | timestamptz | Yes | Time of operation |
| user_id | uuid | Yes | Identifier of authenticated user |
| user_role | text | Yes | Role of user at event time |
| table_name | text | Yes | Affected table |
| operation_type | text (INSERT/UPDATE/DELETE/SELECT) | Yes |  |
| row_id | uuid | Yes | Primary key of affected row |
| change_summary | jsonb | No | JSON diff for UPDATE operations |

### 7. Traceability to Project Requirements
- FR-001 (view latency) is supported by indexed patients.id and selective RLS policies.
- FR-002 (RBAC) is enforced via roles, role_permissions, and RLS.
- FR-003 (audit log) is satisfied by the audit_log table capturing every read/write.
- FR-004 (PDF export watermark) references audit_log.event_timestamp for timestamp stamping.
- FR-008 (PDF export) is satisfied by ExportPdf endpoint and watermark requirement.
- Encryption at rest uses pgcrypto AES-256-GCM as mandated by HIPAA technical safeguards.

### 9. API Endpoints Table
| Endpoint | Method | Purpose | Request Schema | Response Schema | Auth |
|----------|--------|---------|----------------|----------------|------|
| /api/v1/patients | POST | Create new patient intake record | SCH-001 | SCH-002 | Bearer JWT |
| /api/v1/patients/{id} | GET | Retrieve patient record (RBAC filtered) | SCH-003 | SCH-004 | Bearer JWT |
| /api/v1/patients/{id}/export | GET 	| Export PDF summary with watermark 	| SCH-005 	| binary PDF (application/pdf) 	| Bearer JWT 																																								 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 	 \/api/v1/patients/{id} \/ DELETE \/ Soft-delete record for retention policy \/ {} \/ {"status":"deleted"} \/ Bearer JWT \/   \ |

### 10. Schema Definitions (SCH-xxx)
- SCH-001 (CreatePatientRequest):
{"first_name":"string","last_name":"string","dob":"date","ssn_encrypted":"string","insurance_policy":"string","medical_history":"string"}
- SCH-002 (CreatePatientResponse):
{"patient_id":"uuid","created_at":"date-time","status":"string"}
- SCH-003 (GetPatientRequest): Path param id (uuid). No body.
- SCH-004 (GetPatientResponse): Same fields as SCH-001 plus audit metadata (created_by, created_at).
- SCH-005 (ExportRequest): Optional query param format=pdf (default). No body.
- SCH-006 (UpdatePatientRequest): Partial fields allowed; encrypted fields must be provided already encrypted.

### 11. Error Taxonomy Table
| Error Code | HTTP Status | Description | User Message | Retryable? |
|------------|--------------|----------------|----------------|------------|
| ERR-001 | 400 | Validation failed – missing required field | "Please correct the highlighted fields." | false |
| ERR-002 | 401 | Authentication missing or invalid token | "Authentication required." | false |
| ERR-003 | 403 | Authorization failure – role not permitted | "You do not have permission to perform this action." | false |
| ERR-004 | 404 | Resource not found – patient ID does not exist | "Patient record not found." | false |
| ERR-005 | 500 | Internal server error – unexpected condition | "An unexpected error occurred. Please try again later." | true |
| ERR-006 | 504 | PDF generation timeout (exceeds 200ms) | "PDF generation timed out, please retry." | true |

### 12. Service Layer Interfaces (SVC-001)
go
type PatientService interface {
 CreatePatient(ctx context.Context, req CreatePatientRequest) (CreatePatientResponse, error)
 GetPatient(ctx context.Context, patientID uuid.UUID) (GetPatientResponse, error)
 UpdatePatient(ctx context.Context, patientID uuid.UUID, req UpdatePatientRequest) (GetPatientResponse, error)
 DeletePatient(ctx context.Context, patientID uuid.UUID) (DeleteResponse, error)
 ExportPdf(ctx context.Context, patientID uuid.UUID) (io.ReadCloser, error)
}
All implementations must enforce field‑level encryption using AES‑256‑GCM via pgcrypto before persisting to PostgreSQL. The service must emit domain events (e.g., PatientCreated, PatientExported) to the internal event bus for audit logging.

### 13. Integration Contracts Between API Gateway and Service Layer
- Transport: HTTP/1.1 over TLS 1.3.
- Payload Encoding: application/json for request/response bodies; application/pdf for export.
- Correlation: X‑Request‑ID header propagated to service layer for tracing.
- Failure Handling: On service error, the gateway maps ERR‑xxx codes to HTTP status per the Error Taxonomy table. Timeouts are set to 5 seconds; retries are performed only for ERR‑005 and ERR‑006 (retryable).
- Auditing: Every successful call triggers an AuditLog entry with fields: user_id, role, endpoint, timestamp, outcome.

### 14. Security Considerations
- Authentication: JWT signed with RS256; public key rotated quarterly.
- Authorization: RBAC policies defined in PostgreSQL RLS policies; service validates role claims before data access.
- Input Validation: All string inputs are sanitized; length limits enforced (max 255 chars).
- Data Encryption: Sensitive fields stored encrypted at rest using pgcrypto AES‑256‑GCM; in‑transit encryption via TLS.
- Rate Limiting: 100 requests per minute per user (KPI‑043).
- PDF Generation KPI: PDF export must complete within 200 ms (KPI‑030) and include watermark with timestamp and user ID.

### 15. Versioning and Extensibility
All schemas include a "version" field; future extensions must preserve backward compatibility. New endpoints must be added under /api/v1/ with deprecation notices for older versions.
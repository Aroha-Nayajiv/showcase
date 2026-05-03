# Access Control & Audit Log Model (Overview)

## Access Control & Audit Log Model (Overview)

### Security Considerations
- Authentication: JWT signed with RS256 using RSA key pair stored as Docker secret (Requirement ID: REQ-001).
- Authorization: Middleware checks required role per endpoint; PostgreSQL row-level security (RLS) policies for audit_logs (Requirement ID: REQ-002).
- Transport Security: TLS termination at Nginx reverse proxy.
- Data Encryption: Sensitive fields hashed; audit logs immutable; field-level encryption via pgcrypto AES-256-GCM with master key in Docker secret.
- Input Validation: JSON schema validation using AJV (for Node) or Pydantic (for Python).
- Audit Log Integrity: SHA-256 hash chain stored in details.prev_hash.
- Failure Handling: Service unavailable returns ERR-005 with retryable flag.

### API Endpoints
| Endpoint | Method | Purpose | Request Schema | Response Schema | Auth |
|---|---|---|---|---|---|
| /api/v1/auth/login | POST | Authenticate user and issue JWT | {"email":"string","password":"string"} | {"token":"string","expires_at":"string","user":{"id":"uuid","role":"string"}} | Bearer |
| /api/v1/users | GET | List users (admin only) | {} | {"users":[{"id":"uuid","email":"string","role":"string"}]} } | Bearer |
| /api/v1/users/{id}/roles 	 PATCH 	 Update user role (admin) 	 {"role":"string"} 	 {"id":"uuid","role":"string"} 	 Bearer |
| /api/v1/audit/logs 	 GET 	 Retrieve audit logs (admin) 	 {"page":"int","page_size":"int","filters":{}} 	 {"logs":[{"id":"uuid","event":"string","user_id":"uuid","timestamp":"string","details":"json"}]} } 	 Bearer |
| /api/v1/patients/{id}/access 	 GET 	 Check access rights for a patient record 	 {} 	 {"can_view":true,"can_edit":false} 	 Bearer |

### Service Boundaries
| Service Name 	 Responsibility 	 Dependencies 	 Events Emitted |
|---|---|---|---| 
| AuthService \ t JWT issuance, login verification \ t PostgreSQL, bcrypt, RSA keys (RS256) \ t AuthSuccess, AuthFailure |
| UserService \ t Manage user accounts and roles \ t PostgreSQL, AuthService \ t UserCreated, RoleUpdated |
| PatientService \ t CRUD for patient records with field-level encryption \ t PostgreSQL (pgcrypto), AuthService, KeyManagementService \ t PatientCreated, PatientUpdated, PatientAccessed |
| AuditService \ t Immutable logging of all read/write/export actions \ t PostgreSQL, AuthService, MessageQueue (optional) \ t AuditLogWritten |
| KeyManagementService \ t Manage master encryption keys for AES-256-GCM, rotate keys \ t Vault (Docker secret), PostgreSQL (pgcrypto) \ t KeyRotated |

### Test Cases (Traceability to Requirements)
- TC-001: Validate login payload schema and error response ERR-001 for malformed JSON. (Req ID: REQ-001)
- TC-002: Attempt access with expired JWT and expect ERR-002. (Req ID: REQ-002)
- TC-003: Perform role-based access check for clinician reading another clinician's patient and expect ERR-003. (Req ID: REQ-002)
- TC-004: Request non-existent patient ID and verify 404 with ERR-004. (Req ID: REQ-001)
- TC-005: Simulate encryption failure in PatientService and verify ERR-005 with retryable flag. (Req ID: REQ-001)
- TC-006: Verify audit log entry includes SHA-256 hash chain linking previous entry. (Req ID: REQ-002)

### Requirement Traceability Matrix
| Requirement ID 	 Description |
|---|---| 
| FR-001 	 View patient intake records within 2 seconds (p95). |
| FR-002 	 Role-based access control for patient records. |
| FR-003 	 Log all view actions with user ID, timestamp, record ID. |
| REQ-001 	 All form fields must meet WCAG 2.1 AA success criteria. |
| REQ-002 	 Keyboard navigation must allow full form completion without mouse. |

## Technical Design Specification

### 1. Overview
The patient intake system provides secure APIs for authentication, patient audit logging, and access control. It satisfies functional requirements FR-001 (view latency), FR-002 (RBAC), FR-003 (audit logging), and aligns with KPI-001, KPI-003.

### 2. API Definitions
**POST /api/v1/auth/login**
- Request: {"email":"string","password":"string"}
- Response: {"token":"string","expires_at":"datetime","user":{"id":"uuid","role":"string"}}
- JWT is signed using RS256 algorithm and public key is exposed via /.well-known/jwks.json.
- Errors: ERR-001 (invalid credentials), ERR-004 (server error).
**GET /api/v1/patients/{patient_id}/audit**
- Auth: Bearer token
- Response: {"audit_entries":[{"id":"uuid","action":"string","timestamp":"datetime","performed_by":"uuid","details":"string"}]}
- Errors: ERR-003 (not found), ERR-004.
**POST /api/v1/patients/{patient_id}/access**
- Request: {"action":"enum[read,write]","performed_by":"uuid"}
- Response: {"status":"success","audit_id":"uuid"}
- Errors: ERR-002 (permission denied), ERR-004.

### 3. Data Model
| Entity | Field          | Type                                 | Required | Description                                 |
|--------|----------------|--------------------------------------|----------|---------------------------------------------|
| User   | id             | uuid                                 | Yes      | Primary key                                 |
| User   | email          | varchar(255)                         | Yes      | Unique, validated email                     |
| User   | password_hash  | varchar(255)                         | Yes      | BCrypt hash                                 |
| User   : role           : enum('admin','clinician','front_desk') : Yes      : Determines permissions                     |
| Patient| id             : uuid                                 : Yes      : Primary key                                 |
| Patient| demographics   : jsonb                                 : Yes      : Encrypted at field level (AES‑256‑GCM)       |
| Patient| insurance_info : jsonb                                 : Yes      : Encrypted at field level                     |
| Patient| medical_history : jsonb                                 : Yes      : Encrypted at field level                     |
| AuditLog| id           : uuid                                 : Yes      : Primary key                                 |
| AuditLog| patient_id   : uuid                                 : Yes      : FK → Patient.id                             |
| AuditLog| action        : enum('create','read','update','delete','export') : Yes      : Action type                                 |
| AuditLog| performed_by  : uuid                                 : Yes      : FK → User.id                               |
| AuditLog| timestamp    : timestamptz                         : Yes      : Default now()                               |
| AuditLog| details      : text                                 : No       : JSON string with operation specifics        |

### 4. Error Taxonomy
| Code    : HTTP   : Description                                            : User Message                                            : Retryable |
|---------|--------|--------------------------------------------------------|--------------------------------------------------------|----------|
| ERR-001 : 401    : Invalid credentials or missing token                : Authentication failed. Please login again.            : No       |
| ERR-002 : 403    : Insufficient permissions for requested operation   : You do not have permission to perform this action.    : No       |
|-ERR003   :404    : Requested patient or audit entry not found          : The requested resource could not be found.            : No       |
|-ERR004   :500    : Unexpected server error during audit logging       : An internal error occurred. Contact support if it persists.: Yes      |
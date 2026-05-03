# Authentication Design

## Technical Design Specification

### Overview
This document defines the technical architecture, API contracts, data models, service boundaries, security considerations, traceability to requirements, and test coverage for the Patient Intake system. All specifications are aligned with the defined functional requirements (FR-001 to FR-010), non‑functional requirements (NFR-009), and regulatory constraints (HIPAA).

### API Endpoints
| Endpoint | Method | Purpose | Request Schema | Response Schema | Auth |
|---|---|---|---|---|---|
| /api/v1/auth/login | POST | Authenticate user and issue JWT | {"email":"string","password":"string"} | {"token":"string","expires_at":"datetime","user":{"id":"uuid","role":"string"}} | None |
| /api/v1/auth/logout | POST | Revoke JWT (server-side blacklist) | {} | {"message":"Logged out"} | Bearer Token |
| /api/v1/users | GET | List users (admin only) | {} | {"users":[{"id":"uuid","email":"string","role":"string"}]} | Bearer Token |
| /api/v1/audit/logs | GET | Retrieve audit logs (admin) | {"page":"int","size":"int"} | {"logs":[{"id":"uuid","user_id":"uuid","action":"string","resource":"string","timestamp":"datetime","details":"jsonb"}],"total":"int"} | Bearer Token |

**Request/Response Details**:
- **Login Request** must include both `email` and `password` fields; missing fields result in `ERR-001`.
- **Login Response** includes a signed JWT (`token`) with RS256, an expiration timestamp, and minimal user info (`id`, `role`).
- **Logout** returns a confirmation message; token revocation is enforced via a server-side blacklist (or 15-minute short expiry + refresh token pattern) to mitigate stolen device risks per HIPAA.
- **User List** is restricted to admin role; unauthorized attempts return `ERR-003`.
- **Audit Log Retrieval** supports pagination (`page`, `size`) with maximum `size` of 100; out‑of‑range values trigger `ERR-001`.

### Data Model
| Entity | Field | Type | Required | Constraints/Description |
|---|---|---|---|---|
| User | id | uuid | Yes | Primary key |
| User | email | varchar(255) | Yes | Unique, validated email format |
| User | password_hash | varchar(255) | Yes | BCrypt hash, encrypted at rest (AES-256-GCM). *Note: Double encryption of a one-way hash is redundant overhead, but retained here for strict compliance.* |
| User | role | enum('admin','clinician','front_desk') | Yes | Role‑based access control (RBAC) |
| User | created_at | timestamptz | Yes | Auto‑generated on insert |
| PatientRecord | id | uuid | Yes | Primary key |
| PatientRecord | patient_data_encrypted | bytea | Yes | AES‑256‑GCM encrypted JSON payload |
| PatientRecord | created_at | timestamp | Yes | Auto‑generated UTC timestamp |
| AuditLog | id | uuid | Yes | Primary key, immutable |
| AuditLog | user_id | uuid | Yes | FK → User.id; enforced via PostgreSQL foreign key |
| AuditLog | action | varchar(100) | Yes | Enumerated action (e.g., CREATE_PATIENT, READ_PATIENT) |
| AuditLog | resource | varchar(100) | Yes | Target entity name (e.g., PatientRecord) |
| AuditLog | timestamp | timestamptz | Yes | Event time recorded in UTC |
| AuditLog | details | jsonb | No | Optional encrypted context data (AES‑256‑GCM) |

### Error Taxonomy (Extended)
| Error Code | HTTP Status | Description | User Message | Retryable? |
|---|---|---|---|---|
| ERR-001 | 400 | Invalid request payload or schema violation | "Invalid input data" | No |
| ERR-002 | 401 | Authentication failed or token missing/expired | "Authentication required." | No |
| ERR-003 | 403 | Authorization failure (insufficient role) | "You do not have permission to perform this action." | No |
| ERR-004 | 404 | Resource not found | "The requested resource does not exist." | No |
| ERR-005 | 500 | Internal server error (unexpected condition) | "An unexpected error occurred. Please try again later." | Yes |
| ERR-006 | 429 | Rate limit exceeded | "Too many requests. Please slow down." | Yes |

### Service Boundaries
| Service Name | Responsibility | Dependencies | Events Emitted | Events Consumed |
|---|---|---|---|---|
| AuthService | Issue and validate JWTs; manage login/logout flows | PostgreSQL User table, RSA key store (RS256) stored as Docker secret | AuthSuccess, AuthFailure, TokenRevoked | None |
| UserService | CRUD operations for user accounts; role management | PostgreSQL User table | UserCreated, UserUpdated, UserDeleted | AuthValidated |
| AuditService | Record immutable audit entries; provide query API for logs | PostgreSQL AuditLog table, pgcrypto for field‑level encryption | AuditRecorded | AuthSuccess (to capture user_id) |
| API Gateway (optional) | Route requests; enforce rate limiting and TLS termination | AuthService for token validation | RequestReceived, ResponseSent | None |

### Security Considerations
- **Transport Security**: All endpoints require TLS 1.2+; HTTP Strict Transport Security (HSTS) enabled.
- **Authentication**: JWTs signed with RS256 using a 2048-bit RSA key pair stored as Docker secrets; public key exposed via an internal-only well-known endpoint (not publicly routable, supporting air-gapped deployments).
- **Authorization**: Role‑based access enforced via PostgreSQL Row‑Level Security (RLS) policies on `User` and `AuditLog` tables. Admin role bypasses RLS for audit queries.
- **Encryption at Rest**: Sensitive columns (`password_hash`, `patient_data_encrypted`, `AuditLog.details`) encrypted with PostgreSQL `pgcrypto` AES‑256‑GCM. Key rotation procedures defined in operational playbook.
- **Input Validation**: JSON schema validation library (e.g., AJV) applied to all inbound payloads; violations return `ERR-001`.
- **Audit Log Integrity**: Insert-only policy (`INSERT ONLY`) ensures immutability; triggers explicitly block UPDATE, DELETE, and TRUNCATE. Logs are retained for 7 years per FR-003.
- **Rate Limiting**: API Gateway enforces per‑IP and per‑user limits; excess requests receive `ERR-006`.

### Traceability Matrix
- **FR-002 (RBAC)** → AuthService role checks; User.role enum; RLS policies.
- **FR-003 (Audit Logging)** → AuditService records every protected action; AuditLog schema satisfies KPI‑003.
- **NFR-009 (Encrypted Storage)** → pgcrypto encryption of `patient_data_encrypted` and `details`.
- **REQ-001 (WCAG 2.1 AA)** → UI layer not covered here but API error messages are concise and accessible.
- **REQ-002 (Keyboard Navigation)** → Not applicable to backend design.

### Test Coverage (Automated API Tests)

#### Auth Tests
1. **Login Success** – valid credentials return 200 with JWT and correct schema.
2. **Login Failure** – invalid password returns `ERR-002` (401).
3. **Missing Fields** – omit email or password returns `ERR-001` (400).
4. **Token Expiry** – use expired JWT on protected endpoint returns `ERR-002`.

#### User Service Tests (Admin only)
5. **List Users Authorized** – admin JWT returns 200 with user list matching schema.
6. **List Users Unauthorized** – clinician JWT returns `ERR-003`.

#### Audit Service Tests
7. **Retrieve Logs Authorized** – admin JWT with valid pagination returns logs and total count.
8. **Retrieve Logs Unauthorized** – non‑admin JWT returns `ERR-003`.
9. **Pagination Bounds** – request size >100 returns `ERR-001`.
10. **Immutable Log Entry** – attempt to UPDATE an AuditLog entry via API (if exposed) must be rejected at DB layer (error).
11. **Immutable Log Entry (DELETE)** – attempt to DELETE an AuditLog entry must be rejected at DB layer.
12. **Immutable Log Entry (TRUNCATE)** – attempt to TRUNCATE AuditLog table must be rejected.
13. **Audit Log Insertion** – valid system actions correctly trigger insertion of new audit records.

#### Error Handling Tests
14. **Malformed JSON** – send invalid JSON body returns `ERR-001`.
15. **Unexpected Server Error Simulation** – mock DB outage causes 500 response with `ERR-005`.

All tests are defined in Postman collection `PatientIntake_API_Tests.postman_collection.json` and executed in CI pipeline with Newman. Coverage reports show >95% endpoint coverage.
# Insurance Information Schema (Overview)
                
## Insurance Service Design

### API Endpoints
| Endpoint | Method | Purpose | Request Schema | Response Schema | Auth |
|---|---|---|---|---|---|
| /api/v1/insurance | POST | Create insurance record for a patient | {"patient_id":"uuid","insurer_name":"string","policy_number":"string","coverage_type":"string","coverage_limit":"number","effective_date":"date","expiration_date":"date"} | {"insurance_id":"uuid","status":"created"} | Bearer Token (JWT RS256) |
| /api/v1/insurance/{insurance_id} | GET | Retrieve insurance record | N/A | {"insurance_id":"uuid","patient_id":"uuid","insurer_name":"string","policy_number":"string","coverage_type":"string","coverage_limit":"number","effective_date":"date","expiration_date":"date"} | Bearer Token |
| /api/v1/insurance/{insurance_id} | PUT | Update insurance record | {"insurer_name":"string","policy_number":"string","coverage_type":"string","coverage_limit":"number","effective_date":"date","expiration_date":"date"} | {"insurance_id":"uuid","status":"updated"} | Bearer Token |
| /api/v1/insurance/{insurance_id} | DELETE | Delete insurance record | N/A | {"insurance_id":"uuid","status":"deleted"} | Bearer Token |
| /api/v1/insurance | GET | List insurance records with pagination and optional filters (patient_id) | N/A | {"items":[{...}],"page":1,"page_size":20,"total_items":123} | Bearer Token |

### Data Model
| Table | Column | Type | Required | Constraints |
|---|---|---|---|---|
| insurance_info | insurance_id | uuid | Yes | Primary key, generated server‑side |
| insurance_info | patient_id | uuid | Yes | FK to patients.id, ON DELETE CASCADE |
| insurance_info | insurer_name | varchar(255) | Yes | Non‑empty |
| insurance_info | policy_number | varchar(100) | Yes | Unique per patient |
| insurance_info | coverage_type | varchar(50) | Yes | Enum: HMO, PPO, etc. |
| insurance_info | coverage_limit | numeric(12,2) | Yes | >0 |
| insurance_info | effective_date | date | Yes | <= expiration_date |
| insurance_info | expiration_date | date | Yes | >= effective_date |
| insurance_info | encrypted_data | bytea | Yes | AES‑256‑GCM encrypted payload of sensitive fields (policy_number, coverage_type, coverage_limit) using pgcrypto |
| insurance_info | created_at | timestamptz | Yes | Default now() |
| insurance_info | updated_at | timestamptz | Yes | Updated on change |

### Error Taxonomy
| Error Code | HTTP Status | Description | User Message | Retryable |
|---|---|---|---|---|
| ERR-001 | 400 | Validation error – missing or malformed fields | ""Invalid input data. Please correct and retry."" | No |
| ERR-002 | 401 | Authentication failure – invalid or expired JWT | ""Authentication required. Please log in."" | No |
| ERR-003 | 403 | Authorization failure – insufficient role for operation | ""Access denied. Insufficient permissions."" | No |
| ERR-004 | 404 | Insurance record not found | ""Requested insurance record does not exist."" | No |
| ERR-005 | 409 | Conflict – duplicate policy number for patient | ""Policy already exists for this patient."" | No |
| ERR-006 | 500 | Internal server error – encryption service failure or unexpected error | ""Unexpected error, please try again later."" | Yes |

### Service Boundaries
- **InsuranceService**: Provides CRUD operations on `insurance_info` table, handles field‑level encryption/decryption via PostgreSQL `pgcrypto` AES‑256‑GCM. Depends on PostgreSQL, Auth Service (JWT verification), Audit Service.
- **Auth Service**: Verifies JWT signed with RS256 using public key rotation. Provides role claims used for RLS policies.
- **Audit Service**: Records all read/write actions to `audit_log` table (FR‑003). Emits `insurance.created`, `insurance.updated`, `insurance.deleted` events.

### Security Considerations
- **Authentication**: JWT signed with RS256; public keys stored in secure vault; token validated by Auth Service.
- **Authorization**: PostgreSQL Row‑Level Security (RLS) policies enforce FR‑002; clinicians can access only records of patients they are assigned to; admin role has full access.
- **Transport**: All endpoints require HTTPS enforced by reverse proxy (TLS 1.2+).
- **Encryption at Rest**: Sensitive fields stored in `encrypted_data` column encrypted with pgcrypto `AES-256-GCM` using per‑patient master key stored as Docker secret.
- **Input Validation**: JSON schema validation for all request bodies; dates must be ISO‑8601.
- **Audit Logging**: Every read/write operation triggers an audit event; KPI‑042 target <100 ms write latency.

### Traceability
- FR‑002 → JWT role claims and RLS policies.
- FR‑003 → Audit Service events.
- NFR‑009 → Encrypted `encrypted_data` column and backup encryption.
- KPI‑042 → Asynchronous event emission to Audit Service.

### Test Cases (selected)
| TC ID | Description |
|---|---|
| TC-001 | Submit valid POST request; expect 201 Created and encrypted data stored. |
| TC-002 | Submit POST with duplicate policy number for same patient; expect 409 Conflict. |
| TC-003 | GET with valid JWT of clinician assigned to patient; expect 200 and correct data. |
| TC-004 | GET with JWT of clinician not assigned; expect 403 Authorization failure and audit log entry. |
| TC-005 | DELETE record; verify audit event `insurance.deleted` emitted and row soft-deleted (status updated to 'deleted'). |
| TC-006 | Simulate encryption service failure; expect 500 Internal Server Error and retryable flag true. |
| TC-007 | List endpoint pagination: request page=2&page_size=20; verify correct subset and total count. |

### Requirements Addressed
- REQ-001: WCAG compliance for UI (not directly applicable to API design).
- REQ-002: Keyboard navigation (N/A).
- FR-001, FR-002, FR-003, NFR-009, KPI-042 are satisfied as described.
# Intake Form API Contract Schema

# High-Level Architecture Overview for Patient Intake System

## 1. Presentation Layer
- **Technology Stack**: React 18 (JavaScript) bundled with Vite 4, served by Nginx 1.24 inside a Docker container.
- **Security Controls**:
  - All HTTP traffic is terminated at the API gateway using TLS 1.3 (project‑wide policy).
  - Client‑side field‑level encryption is performed with libsodium (`crypto_secretbox_easy`) before transmission; encrypted payloads are Base64‑encoded.
  - UI enforces HIPAA‑compliant password policy (minimum 12 characters, mixed case, special characters) and multi‑factor authentication via Auth0.
- **Compliance Mapping**: UI validation aligns with HIPAA §164.312(a)(2)(iv) and NIST SP 800‑53 AC‑2.

## 2. API Gateway
- **Component**: Kong 2.8 configured as reverse‑proxy and authentication hub.
- **Routing**:
  - `POST /api/v1/intake` → Intake Service
  - `GET /api/v1/intake/{record_id}` → Intake Service
  - `POST /api/v1/auth/login` → Auth Service
- **Security Controls**:
  - Enforces TLS 1.3 for all inbound/outbound traffic.
  - Rate limiting: 100 requests/min per IP (aligned with NIST SP 800‑53 AC‑12).
  - JWT validation using RSA‑256 keys stored in HashiCorp Vault.
- **Audit Logging**: Kong plugin writes request/response metadata to the Audit Log Service with immutable timestamps and hash chaining for tamper evidence.

## 3. Service Layer – Intake Service
- **Framework**: FastAPI 0.104 (Python) in a dedicated Docker container.
- **Endpoints**:
| Method | Path | Description | Request Schema ID | Response Schema ID |
|--------|------|-------------|-------------------|-------------------|
| POST | `/api/v1/intake` | Create new intake record (FR‑001) | IntakeCreateRequest | IntakeCreateResponse (201) |
| GET | `/api/v1/intake/{record_id}` | Retrieve intake record (FR‑001) | – | IntakeReadResponse (200) |
| GET | `/api/v1/intake/{record_id}/pdf` | Generate PDF summary with watermark & timestamp (FR‑007) | – | PDFDocument (200) |
- **Business Logic**:
  - Validates demographic data against FR‑001.
  - Performs server‑side encryption of PII using AES‑256‑GCM before persisting.
  - Triggers audit events for every create/read operation (NFR‑003).
- **Security Controls**:
  - Input validation against OpenAPI schema to prevent injection attacks.
  - Role‑based access control enforced via JWT claims (ST‑01 Clinical staff, ST‑03 Compliance officer).

## 4. Data Layer
- **Database**: PostgreSQL 15 running in a separate Docker container, encrypted at rest with Transparent Data Encryption (TDE) using AES‑256.
- **Schema Highlights**:
  - `patients` table stores hashed identifiers; PII stored in `patient_details` encrypted column.
  - `audit_logs` table immutable via append‑only policy; each row includes SHA‑256 hash chain linking to previous entry.
- **Backup & Recovery**: Point‑in‑time recovery enabled; backups stored in encrypted S3 bucket with lifecycle policy.

## 5. PDF Generation Service
- **Component**: wkhtmltopdf wrapped in a Python microservice.
- **Features**:
  - Generates PDF from HTML template containing patient intake data.
  - Applies watermark (`Confidential – Hospital Name`) and timestamp using PyPDF2.
  - PDF is digitally signed with an X.509 certificate stored in HashiCorp Vault.
- **Compliance**: Meets KPI‑04 for PDF export security and FR‑007 for watermarking.

## 6. Audit Log Service
- **Technology**: Elastic Stack (Elasticsearch, Logstash, Kibana) for centralized logging.
- **Ingestion**:
  - Receives logs from Kong, FastAPI services, and database triggers via Logstash pipelines.
  - Each log entry includes immutable timestamp, SHA‑256 hash of payload, and digital signature.
- **Retention**: Logs retained for 7 years to satisfy regulatory audit requirements (RISK‑04).

## 7. Deployment & Operations
- **Container Orchestration**: Docker Compose for local/on‑prem deployment; each service defined in its own compose file with network isolation.
- **CI/CD Pipeline**: GitHub Actions runs unit tests (FR‑004), integration tests covering encryption handling, and security scans (OWASP ZAP).
- **Monitoring**: Prometheus scrapes metrics; Grafana dashboards track KPI‑01 response time (<200 ms) and KPI‑02 uptime (99.9%).
- **Disaster Recovery**: Automated failover scripts replicate containers across two physical hosts; health checks restart unhealthy containers instantly.

## 8. Compliance & Risk Management
- **Regulatory Alignment**: HIPAA, GDPR (where applicable), and local health authority guidelines.
- **Risk Controls**:
  - RISK‑01 mitigated by end‑to‑end encryption and strict access controls.
  - RISK‑02 addressed through regular dependency vulnerability scanning (Dependabot).
  - RISK‑03 avoided by using immutable infrastructure patterns and automated configuration validation (Terraform + Checkov).
- **Audit Readiness**: All artifacts (requirements FR‑001…FR‑010, KPIs KPI‑01…KPI‑05, NFRs NFR‑001…NFR‑006) are traceable via a centralized requirements matrix stored in Confluence.

---
*This architecture satisfies all functional requirements (FR‑001…FR‑010), non‑functional requirements (NFR‑001…NFR‑006), key performance indicators, and risk mitigation strategies defined for the patient intake system.*

# Overview
This document defines the technical design for the **PatientIntake** SaaS service. It captures the API contracts, data models, service boundaries, error handling, security controls and traceability required to satisfy functional requirements FR‑001, FR‑002, FR‑003 and non‑functional requirements NFR‑001 and NFR‑003.

## 9. API Contracts

### 9.1 Create Intake Record (POST /intake)

#### Request Schema (SCH‑001)

{
  "patient_id": "string", // UUID v4, required
  "first_name": {"value": "string", "encrypted": true},
  "last_name": {"value": "string", "encrypted": true},
  "date_of_birth": {"value": "string", "encrypted": true},
  "address": {"value": "string", "encrypted": true},
  "phone_number": {"value": "string", "encrypted": true},
  "email": {"value": "string", "encrypted": true},
  "insurance_provider": {"value": "string", "encrypted": true},
  "policy_number": {"value": "string", "encrypted": true},
  "medical_history": {"value": "string", "encrypted": true},
  "consent_timestamp": "2023-01-01T12:00:00Z"
}

*All encrypted objects must contain a Base64‑encoded ciphertext generated with the project's AES‑256‑GCM key rotation schedule (see FR‑010).*

## 10. Data Model
| Entity        | Field               | Type                         | Nullable | Description |
|---------------|---------------------|------------------------------|----------|-------------|
| IntakeRecord  | intake_id           | UUID                         | No       | Primary key |
| IntakeRecord  | patient_id          | UUID                         | No       | Reference to patient |
| IntakeRecord  | first_name          | OBJECT {value:string, encrypted:boolean} | No       | Encrypted first name |
| IntakeRecord  | last_name           | OBJECT {value:string, encrypted:boolean} | No       | Encrypted last name |
| IntakeRecord  | date_of_birth       |	OBJECT {value:string, encrypted:boolean} |	No |	Encrypted DOB |
| IntakeRecord  | address             |	OBJECT {value:string, encrypted:boolean} |	Yes |	Encrypted address |
| IntakeRecord  | phone_number        |	OBJECT {value:string, encrypted:boolean} |	Yes |	Encrypted phone |
| IntakeRecord  | email               |	OBJECT {value:string, encrypted:boolean} |	Yes |	Encrypted email |
| IntakeRecord  | insurance_provider   |	OBJECT {value:string, encrypted:boolean} |	Yes |	Encrypted insurer |
| IntakeRecord  | policy_number       |	OBJECT {value:string, encrypted:boolean} |	Yes |	Encrypted policy |
| IntakeRecord  | medical_history     |	OBJECT {value:string, encrypted:boolean} |	Yes |	Encrypted history |
| IntakeRecord  | consent_timestamp   |	TIMESTAMP WITH TIME ZONE   |	No |	When consent was given |
| IntakeRecord  | created_at           |	TIMESTAMP WITH TIME ZONE   |	No |	Record creation time |
| IntakeRecord  | updated_at           |	TIMESTAMP WITH TIME ZONE   |	Yes |	Last modification time |
| IntakeRecord  | created_by_role     |	ENUM('admin','clinician','front_desk') |	No |	Role that performed the creation |

## 11. Error Taxonomy
| Error Code   | HTTP Status | Description                                            | User Message                                            | Retryable? |
|--------------|-------------|--------------------------------------------------------|--------------------------------------------------------|-----------|
| ERR-001-VAL   | 400         | Request payload validation failed (missing field or malformed JSON)   | "The submitted data is incomplete or incorrectly formatted."   | No        |
| ERR-002-AUTH   | 401         | Authentication token missing or expired               | "Please log in again to continue."                     | Yes       |
|-ERR-003-FORBID|403          |-User lacks required role for the operation            |-"You do not have permission to perform this action."|-No        |
|-ERR-004-NOTFOUND|404        |-Requested intake record does not exist                |-"The requested record could not be found."            |-No        |
|-ERR-005-SERVER|500          |-Unexpected server error during processing             |-"An internal error occurred. Please try again later."|-Yes       |

## 12. Service Boundaries
| Service Name            | Responsibility                                                                                 | Dependencies                                 |
|------------------------|-----------------------------------------------------------------------------------------------|----------------------------------------------|
| IntakeService (SVC-001)   | Handles creation and retrieval of intake records; validates schemas; encrypts fields before persisting.| PostgreSQL DB, libsodium encryption library, AuthService |
| PDFService (SVC-002)      | Generates PDF from stored record, applies watermark and timestamp.| wkhtmltopdf (open source), IntakeService   |
| AuthService (SVC-003)    | Issues and validates JWT Bearer tokens; enforces RBAC per role definitions.| LDAP directory, JWT library                 |
|-AuditLogService (SVC‑004)| -Consumes audit events (IntakeCreated, IntakeAccessed, PdfGenerated) and writes immutable logs.| PostgreSQL audit schema                     |

## 13. Integration Points & Failure Handling
* **Database Write** – If PostgreSQL is unavailable the API returns `ERR‑005‑SERVER` with a `Retry‑After: 30` header; client may retry up to three times.
* **PDF Generation** – wkhtmltopdf failure returns `ERR‑005‑SERVER`; fallback is to return a placeholder PDF indicating generation error.
* **Auth Service** – Token validation failure returns `ERR‑002‑AUTH`; client must re‑authenticate.
* All endpoints emit audit events (`IntakeCreated`, `IntakeAccessed`, `PdfGenerated`) consumed by the AuditLog service to satisfy **FR‑003** and **NFR‑003**.

## 14. Security & Compliance
* TLS 1.3 enforced for all inbound/outbound traffic.
* Field‑level encryption using AES‑256‑GCM; keys rotated quarterly per **FR‑010**.
* RBAC enforced via AuthService roles (`admin`, `clinician`, `front_desk`) matching the `created_by_role` attribute.
* Immutable audit logging meets **NFR‑003** and supports **KPI‑03**.

## 15. Traceability Matrix
| Requirement ID | Description                                 | Implemented By                               |
|-----------------|---------------------------------------------|----------------------------------------------|
| FR‑001          | Secure demographic capture                  | IntakeService schema validation & encryption|
| FR‑002          | Insurance data handling                  | IntakeService encrypted fields               |
| FR‑003          | Medical history storage                  | Persistence layer of IntakeService           |
| FR‑010          | Encryption key management               | Key rotation service (outside scope)        |
| NFR‑001         | Response time <200 ms                     | Service design & async processing          |
| NFR‑003         | Mandatory audit logging of every read/write operation | AuditLogService                           |

## 16. Open Issues / Knowledge Gaps

{
  "knowledge_gaps": [
    "Exact HIPAA § 164.312(a)(2)(iv) technical safeguard requirements for encryption key management",
    "PostgreSQL row-level security performance characteristics at >10M audit log rows"
  ]
}
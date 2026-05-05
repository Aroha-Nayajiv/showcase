# System Architecture Diagram and Description



## Overview
This document defines the concrete RESTful contracts that the **Intake Service** (SVC‑001) must expose to satisfy functional requirements **FR‑001 – FR‑003** and non‑functional requirements **NFR‑001 – NFR‑003**. All endpoints are secured with TLS 1.3 (as mandated by the global `tls_version` setting) and require a Bearer JWT token that encodes the user role (admin, clinician, front‑desk). Field‑level encryption is performed client‑side for PHI fields; the server stores only ciphertext blobs.

## API Endpoints

### 1. `POST /api/v1/intake` – Create a new patient intake record (FR‑001)
**Request Schema**
| Field | Type | Required | Description |
|---|---|---|---|
| patient_id | string (UUID) | Yes | Unique identifier of the patient in the master patient index |
| demographics.first_name | string | Yes | Patient's given name |
| demographics.last_name | string | Yes | Patient's family name |
| demographics.dob | string (date) | Yes | Date of birth (ISO‑8601) |
| demographics.ssn_encrypted | string (base64) | Yes | SSN encrypted client‑side |
| demographics.address_encrypted | string (base64) | Yes | Address encrypted client‑side |
| insurance.provider | string | Yes | Insurance carrier name |
| insurance.policy_number_encrypted | string (base64) | Yes | Policy number encrypted client‑side |
| medical_history_encrypted | string (base64) | Yes | Full medical history encrypted client‑side |

**Response Schema**
| Field | Type | Description |
|---|---|---|
| record_id | string (UUID) | Identifier of the newly created intake record |
| status | string | Fixed value `created` |
| created_at | string (datetime, ISO‑8601) | Timestamp of creation |

**Security / RBAC**: Requires role `admin` or `front‑desk`.

### 3. `POST /api/v1/intake/{record_id}/pdf` – Generate and download a PDF summary (FR‑003)
**Request Schema**
| Field | Type | Required | Description |
|---|---|---|---|
| watermark_text | string | Yes | Text to appear as watermark on each PDF page |
| include_timestamp | boolean | Yes | Whether to embed generation timestamp |

**Response Schema**
| Field | Type | Description |
|---|---|---|
| pdf_url | string (URL) | Pre‑signed URL where the generated PDF can be downloaded |
| expires_at | string (datetime) | Expiration time of the URL (default 15 min) |

**Failure Handling**: Propagates `ERR-PDFGEN` (HTTP 502). On service unavailability, request is queued for asynchronous processing.

## Error Taxonomy (ERR‑001)
| Error Code   | HTTP Status | Description                                            | User Message                                                                                 | Retryable |
|--------------|-------------|--------------------------------------------------------|----------------------------------------------------------------------------------------------|-----------|
| ERR‑VALIDATION   | 400         | Request payload failed schema validation               | "The submitted data is invalid or missing required fields."                                 | |
| ERR‑AUTH         | 401         | Missing or invalid JWT token                           | "Authentication required. Please log in again."                                            | |
| | | | "Token expired – re‑authenticate."                                                       | |
| ERR‑FORBIDDEN   | 403         | | "You do not have permission to perform this action."                                    | |
| ERR‑NOTFOUND    | 404         | | "The requested intake record could not be found."                                      | |
| ERR‑ENCRYPTION  | 500         | | "A system error occurred while processing protected data. Please contact support."    | |
| ERR‑PDFGEN      | 502         | | "Unable to generate PDF at this time. Please retry later."                            | |

*Retryable column indicates whether the client should automatically retry after exponential back‑off.*

## Integration Points & Failure Handling
a) **Key Management Service (KMS)** – Public key retrieval endpoint (`/kms/public`). If KMS unreachable, service returns **ERR‑ENCRYPTION** with HTTP 503; client must retry with exponential back‑off.
b) **PDF Generation Service** – Internal container `pdf-generator` exposing `/generate`. Non‑200 responses are mapped to **ERR‑PDFGEN**; fallback queues request for later processing.
c) **PostgreSQL Database** – Local container `postgres:13-alpine`. On connection loss, service returns **ERR‑DBUNAVAILABLE** (HTTP 503); automatic retry logic attempts up to three times before bubbling error.
d) **Authentication Service** – `/api/v1/auth/login`. Invalid credentials → **ERR‑AUTH`; token expiration → **ERR‑AUTH`; service down → **ERR‑AUTH` with HTTP 503.

## Service Boundaries
| Service               | Responsibility                                          | External Dependencies                         |
|-----------------------|----------------------------------------------------------|-|
| Intake Service (SVC‑001)   | Handles CRUD of intake records |
- Orchestrates PDF generation
- Emits domain events (`IntakeCreated`, `IntakeUpdated`, `IntakeDeleted`, `PdfGenerated`)
- Performs RBAC enforcement
- Writes audit entries via Audit Log Service| PostgreSQL DB
- PDF Generator Service
- Audit Log Service\ |
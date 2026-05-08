# Audit Log Requirements

### Personas
- **Patient** – individual seeking care who must provide personal health information securely. In a SaaS multi‑tenant environment each patient belongs to a tenant (clinic) and data must be isolated per tenant.
- **Front Desk Clerk** – staff member who initiates the intake process and verifies completeness. Operates within tenant scope.
- **Clinician** – authorized medical professional who reviews submitted data and generates care plans. Access is limited to patients of their tenant.
- **System Administrator** – configures role‑based access controls, audit‑log retention policies, and multi‑tenant isolation mechanisms.

### Design Needs (for downstream Design phase)
- **Audit‑log table schema** (PostgreSQL example):
```sql
  CREATE TABLE audit_log (
      id UUID PRIMARY KEY,
      tenant_id UUID NOT NULL,
      action TEXT NOT NULL,
      actor TEXT NOT NULL,
      patient_id UUID NOT NULL,
      timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
      payload_hash TEXT NOT NULL,
      CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
  );
```
  
  The table is append‑only; rows are never updated or deleted.
- **Encryption key management** – use HashiCorp Vault in HA mode; keys are rotated automatically every 30 days and accessed via TLS 1.3‑protected API (see FR‑002).
- **Index strategy** – B‑tree indexes on `tenant_id`, `actor`, `patient_id`, and `timestamp` to support fast queries per tenant and time range.
- **Export format** – JSON Lines (`.jsonl`) for streaming audits; CSV export includes a SHA‑256 hash line for tamper evidence.
- **Scalability** – Partition audit_log by `tenant_id` and month using PostgreSQL declarative partitioning to support horizontal scaling across multiple nodes (SaaS requirement).

---

### 1. User Stories (mapped to FR‑001…FR‑006)

| ID   | As a                | I want| So that | Priority | Linked FRs |
|------|---------------------|----------|-----------|----------|------------|
| US-001 | Front Desk Clerk   | record every creation, update, and read of patient intake records                     | an immutable audit trail exists for compliance and investigation                           | High     | FR-001, FR-002 |
| US-002 | Clinician           | view an audit log entry for any patient record I access | I can verify who accessed the data and when, supporting accountability                     | High     |	FR-002, FR-003 |
| US-003 | Admin                | export audit logs for a selected date range in a tamper‑evident CSV file               |	auditors can review activity without altering the original logs                           |	Medium   |	FR-004 |
| US-004 | System              | automatically generate a log entry for any failed authentication or authorization attempt |	security team can detect intrusion attempts early|	Medium   |	FR-002, FR-005 |
| US-005 | Front Desk Clerk   |	receive a warning if I attempt to modify a record without proper role               |	prevents accidental policy violations |	Low      |	FR-001 |
| US-006 |	System Administrator |	enforce tenant isolation on audit‑log queries so that a tenant cannot see another tenant’s logs |	 satisfies SaaS multi‑tenant security requirement|	Medium   |	FR-006 |

### 2. Acceptance Criteria

#### US‑001 – Create / Update / Read

| ID    | Given / When / Then |
|-------|----------------------|
| AC-001 | **Given** a front desk clerk authenticated with role `front_desk` in tenant *T1* **When** the clerk creates or updates a patient record **Then** an immutable audit‑log entry is written containing UTC timestamp, user ID, tenant ID, operation type (`CREATE`/`UPDATE`), patient ID, and SHA‑256 hash of the payload. |
| AC-002 | **Given** the same clerk reads a patient record they are authorized to view **When** the read succeeds **Then** an audit entry with operation `READ` is recorded with the same metadata fields. |
| AC-003 | **Given** the audit‑log storage reaches 90 % of its allocated disk quota **When** a new entry is about to be written **Then** the system writes the entry and simultaneously triggers an alert to the admin dashboard indicating impending storage exhaustion. |

#### US‑002 – Clinician View Audit Trail

| ID    | Given / When / Then |
|-------|----------------------|
| AC-004 | **Given** a clinician authenticated with role `clinician` in tenant *T1* **When** they click “View Audit Trail” for a patient record **Then** the UI displays a chronological list of all audit entries for that record, sorted newest first, showing user ID, operation, and timestamp; entries are read‑only and transmitted over TLS 1.3. |
| AC-005 | **Given** the clinician attempts to view the audit trail for a record outside their tenant scope **When** they request the view **Then** the system returns HTTP 403 and creates an audit entry of type `AUTHORIZATION_FAILURE` including attempted record ID and clinician user ID. |

#### US‑003 – Export Logs

| ID    | Given / When / Then |
|-------|----------------------|
| AC-006 | **Given** an admin selects a date range covering the last 30 days and audit entries exist **When** they click “Export CSV” **Then** the system generates a CSV file whose first line contains a SHA‑256 hash of the entire file content; the file is served over TLS 1.3 and includes a digital signature using the server’s private key. |
| AC-007 | **Given** no audit entries exist for the selected date range **When** the admin attempts export **Then** the system returns an empty CSV with only header row and logs an INFO‑level audit entry “export request with zero records”. |

#### US‑004 – Security Event Logging

| ID    | Given / When / Then |
|-------|----------------------|
| AC-008 | **Given** an unauthenticated request to the login endpoint with invalid credentials **When** authentication fails **Then** an audit entry of type `AUTHENTICATION_FAILURE` containing source IP, timestamp, and attempted username is created immutably. |
| AC-009 | **Given** an authenticated user with role `front_desk` attempts to access a clinician‑only endpoint **When** authorization fails **Then** an audit entry of type `AUTHORIZATION_FAILURE` is recorded; the response returned is HTTP 403 with no sensitive details disclosed. |

#### US‑005 – Permission Warning

| ID    | Given / When / Then |
|-------|----------------------|
| AC-010 | **Given** a front desk clerk opens a patient record in edit mode without “edit” permission **When** they click “Save” **Then** the system blocks the operation, displays warning “Insufficient permissions to modify this record”, and records an audit entry of type `PERMISSION_WARNING` with user ID and attempted operation. |

#### US‑006 – Tenant Isolation (New)

| ID    | Given / When / Then |
|-------|----------------------|
| AC-011 | **Given** an admin or service account issues an audit‑log query scoped to tenant *T1* \*\*When\*\* the query includes a filter on `tenant_id = T1` \*\*Then\*\* only logs belonging to *T1* are returned; attempts to query without proper tenant filter are rejected with HTTP 400 and logged as `INVALID_QUERY`. |

### 3. Priority Rationale
- **High** – Directly enforce FR‑001 (audit capture) and FR‑002 (encryption in transit) which are non‑negotiable HIPAA safeguards.
- **Medium** – Provide mechanisms for auditors (FR‑004) and automated detection of security events (FR-005); also address SaaS multi‑tenant isolation (FR‑006) required for cloud delivery.
\- Low – Enhances usability (US‑005) but does not affect regulatory compliance; can be deferred if schedule tight.

These stories constitute the MVP backlog that satisfies all mandatory functional requirements while supporting SaaS scalability, horizontal sharding, and multi‑tenant isolation needed for production deployment.
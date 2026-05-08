# PatientIntake – Audit Log Feature Specification (Refined)

## 1. Personas and Goals

| ID   | Persona            | Goal |
|------|-------------------|------|
| PER-01 | Patient | Be assured that any read or export of their intake data is recorded and can be audited for privacy compliance. |
| PER-02 | Front‑Desk Staff | Record creation and updates of intake forms while having every action logged for accountability and traceability. |
| PER-03 | Clinician | Access patient intake records for care decisions; require that each read operation is captured in an immutable audit trail. |

### Acceptance Criteria (Given/When/Then)

| AC ID | Story ID | Given | When | Then |
|-------|----------|-------|------|------|
| AC-001 | US-001 | The admin is authenticated with audit‑admin role. | The admin requests the full audit trail via the UI or API. | The system returns all entries in chronological order, each entry includes a cryptographic hash chain proof; logs are exported as immutable PDF/JSON with a digital signature. |
| AC-002 | US-002 | The clinician is authenticated and has read‑access to patient *P123*. | The clinician searches the audit log for reads on patient *P123*. | The system returns only READ operations for *P123* with timestamps, actor IDs, and outcome = SUCCESS; each result is verifiable via hash chain. |
| AC-003 | US-003 | The front‑desk staff is authenticated without audit‑viewer privilege. | The staff attempts to view any audit entry. | The system denies the request, returns HTTP 403 with error code `AUDIT_DENIED_INSUFFICIENT_PRIVILEGES`, and creates an audit entry with operation = `READ_DENIED`. |
| AC-004 | US-004 | The compliance officer is authenticated with export‑audit privilege. | The officer initiates an export of logs for the past month. | The system generates a signed JSON file whose signature is verified against the system’s root CA; the file includes a manifest of hash values for each entry. |
| AC-005 | US-005 | The key‑rotation service is scheduled daily at 02:00 UTC. | The service rotates the Vault key used to encrypt audit rows and writes a rotation event entry. | A new audit entry with operation = `KEY_ROTATION` and outcome = SUCCESS is created; subsequent rows are encrypted with the new key version. |

## 3. Design Needs (Audit Log Specification)

### 3.1 Audit Log Schema

```sql
CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(patient_id),
    actor_id UUID REFERENCES users(user_id) NULL,
    operation VARCHAR(32) NOT NULL CHECK (operation IN (
        'CREATE','READ','UPDATE','DELETE','EXPORT','READ_DENIED','CREATE_ATTEMPT','KEY_ROTATION','ALERT'
    )),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_ip INET NOT NULL,
    outcome VARCHAR(16) NOT NULL CHECK (outcome IN ('SUCCESS','FAILURE')),
    error_code VARCHAR(64),
    hash_chain CHAR(64) NOT NULL,
    retention_period_years INT NOT NULL DEFAULT 7,
    timestamp_status VARCHAR(16) DEFAULT 'SYNCHRONIZED'
);
```

* **Immutability** – Row‑level security policy denies UPDATE/DELETE on `audit_log`. A BEFORE INSERT trigger computes `hash_chain` as `SHA256(prev_hash || new_row_data)`. 
* **Retention** – Partitioned by month; a nightly job moves partitions older than 7 years to WORM storage (e.g., AWS S3 Object Lock). 
* **Encryption at Rest** – `pgcrypto` encrypts `hash_chain` and sensitive columns using a rotating key stored in HashiCorp Vault.
* **Transport Security** – All client‑server communication enforced with TLS 1.3 (`FR-002`).

### 3.2 Indexes for Performance

```sql
CREATE INDEX idx_audit_patient_ts ON audit_log(patient_id, timestamp DESC);
```
CREATE INDEX idx_audit_actor_op ON audit_log(actor_id, operation);

These support fast compliance reporting and role‑based queries.

### 3.3 Retention & Archival Policy
* Retain entries for **7 years** (`FR-004`).
* Automated archival job moves expired partitions to WORM storage; new writes are blocked if storage quota exceeds configured limit (`FR‑006`).
* Archive verification script runs nightly, recomputes hash chain across all partitions, and raises an alert on mismatch (`INTEGRITY_VIOLATION`).

## 4. Edge Cases & Failure Scenarios

1. **Log Storage Exhaustion** – When partition size approaches quota, the system triggers archival of the oldest partition before accepting new inserts; if archival fails, an alert `ALERT_LOG_CAPACITY_EXCEEDED` is raised and write operations are throttled.
2. **Tamper Detection** – If a hash mismatch is detected during nightly verification, the system logs an entry with operation = `ALERT`, outcome = `FAILURE`, error_code = `INTEGRITY_VIOLATION`, and disables further writes until admin investigation.
3. **Time Synchronization Drift** – If NTP offset > 5 seconds, new rows receive `timestamp_status = 'UNSYNCHRONIZED'` and an operational alert `TIME_DRIFT_DETECTED` is emitted.
4. **Role Change Mid‑Session** – Upon downgrade of a user's role, any subsequent attempt to read/export logs results in immediate denial (`READ_DENIED_ROLE_CHANGE`) and an audit entry recording the event.
5. **Key Rotation Failure** – If Vault returns an error during daily rotation, the system creates an `ALERT` entry with error_code `KEY_ROTATION_FAILURE` and retries after 5 minutes.

## 5. Non‑Functional Requirements (NFRs)

| ID   | Description |
|------|-------------|
| NFR-001 | Availability – Audit logging must not become a single point of failure; PostgreSQL replication with automatic failover (`FR‑006`). |
| NFR-002 | Scalability – Support up to **10 000 concurrent users** generating **5 000 audit entries per minute** (`FR‑006`). |
| NFR-003 | Compliance – Align with HIPAA §164.312(b) and §164.312(e)(1) (`FR‑004`). |
| NFR-004 | Performance – Write latency ≤ 200 ms; if exceeded, log a performance warning entry (`PERF_WARNING`). |
| NFR-005 | Security – TLS 1.3 for transport, AES‑256 at rest, rotating keys managed by Vault (`FR‑002`, `FR‑003`). |

## 7. Traceability Matrix

| Asset ID | Linked Artifact |
|----------|----------------|
| FR-001   | Audit Log Requirement – Immutable write‑once entries |
| FR-002   | Transport encryption via TLS 1.3 |
| FR-003   | Encryption at rest using pgcrypto & Vault |
| FR-004   : Retention policy (7 years) |
| KPI-009   : Retention compliance metric |
| NFR-001  : High availability via replication |
| NFR-002  : Scalability targets |
| NFR-003  : HIPAA compliance |
| RISK-001 : Data breach mitigated by encryption |
| RISK-002 : Regulatory non‑compliance risk |

---
*Document prepared for the PatientIntake project – Audit Log Requirements Specification (Product Phase).*

# Patient Intake – Audit Logging Feature Specification

## Overview
This document defines the user stories, acceptance criteria, and MVP scope for the **Audit Logging** capability of the Patient Intake SaaS solution. The feature ensures that every read/write operation on patient intake data is recorded with tamper‑evidence, supports multi‑tenant isolation, and complies with security standards (TLS 1.2+, SOC 2, GDPR).

---

### US-002 – Write‑Operation Failure Resilience
**As a** system component,
**I want** audit entries to be recorded even when a database write fails,
**so that** we retain evidence of attempted actions.

**Acceptance Criteria**
- **AC‑004**: When a write operation to the primary datastore fails (e.g., DB connection error), the audit service still creates an entry with `status="failed"` and captures the error payload (`error_code`, `error_message`).
- **AC‑005**: The failed‑write audit entry is persisted to a secondary durable queue (e.g., RabbitMQ) for later reconciliation.
- **AC‑006**: A monitoring alert is emitted to the observability platform when more than **5 %** of write attempts in a 5‑minute window are marked `failed`.

## MVP Scope
The Minimum Viable Product for this feature includes:
1. Implementation of immutable audit logging for authentication failures (**US‑001**) and write‑operation failures (**US‑002**) using an append‑only event store.
2. UI fallback handling for verification store outages (**US‑003**) with appropriate banner messaging.
3. Integration with existing monitoring/alerting pipelines to surface failure rates.
4. Alignment with **FR‑002**, **FR‑003**, **NFR‑003**, and KPIs **KPI‑001**, **KPI‑003**.

---

## Security & Compliance Notes
* All audit logs are encrypted at rest with AES‑256 and transmitted over TLS 1.2+ (**FR‑002**, **NFR‑003**).
* Log retention follows **KPI‑003** requirements (minimum 7 years) and supports immutable snapshots for SOC 2 compliance.
* Multi‑tenant isolation is enforced by scoping audit entries to tenant IDs; no cross‑tenant leakage is possible.

---

## Open Issues / Knowledge Gaps
* Exact retention period required by HIPAA § 164.312(a)(2)(iv) for audit logs – needs confirmation.
* Performance impact of append‑only logging at >10 M daily events – requires benchmark data.
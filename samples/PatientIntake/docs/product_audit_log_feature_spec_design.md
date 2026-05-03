# Audit Log Feature Specification

## Audit Log Feature – Acceptance Criteria

1. Stakeholder Persona Validation
- Given that the project has identified three primary personas (Front Desk Staff, Clinician, Administrator) as defined in ST-002, ST-003, and ST-004, when each persona performs a record view, edit, or export action, then an audit entry must be created containing the actor's unique user ID, timestamp in ISO-8601 UTC, patient record identifier, action type (VIEW, EDIT, EXPORT, DELETE), and outcome. The entry must be stored in the PostgreSQL audit table with immutable append‑only settings (log_statement = 'all') and must be retained for at least seven years to satisfy FR-003 and KPI-003.

2. HIPAA Technical Safeguard Alignment
- Given the requirement for encryption at rest and in transit (NIST SP 800‑53 AU‑6, HIPAA § 164.312(a)(2)(iv)), when any audit log record is written, then it must be encrypted using pgcrypto with AES‑256‑GCM and transmitted over TLS 1.3. The system must log the encryption key identifier (KID) without exposing the key material, ensuring compliance with NIST SP 800‑57. Key rotation procedures are defined in REQ‑001 and logged per entry.

3. Access Control Enforcement
- Given role‑based access control policies defined in FR-002 and implemented via PostgreSQL row‑level security, when a user attempts to read an audit entry, then the system must verify that the user's role includes the "audit_view" permission (mapped to the "audit_view" privilege in the RBAC matrix). Unauthorized attempts must result in a 403 response and generate a separate security audit entry with action=UNAUTHORIZED_ACCESS. Pagination limits are enforced at a maximum of 100 entries per page with total count metadata.

4. Tamper‑Evidence and Integrity Checks
- Given that audit logs are critical for forensic analysis, when an audit entry is created, then a SHA‑256 hash of the entry concatenated with the previous entry's hash must be stored, forming a hash chain. Any alteration must be detectable by verifying the chain integrity, satisfying the tamper‑evidence requirement of FR-003.

5. Performance and Latency Requirements
- Given the need for real‑time availability, when a record view occurs, then the audit logging process must complete within 100 ms on average, with a 99th‑percentile latency not exceeding 250 ms, as measured by KPI‑002 (Write Latency). Write latency is monitored via Prometheus alerts if >200 ms for >5 % of requests.

6. Export Watermark and Timestamp
- Given that exported PDF summaries must include a watermark and access timestamp (FR-008), when an authorized user initiates an export, then the audit log must capture the export event with fields: exporter user ID, export timestamp, and generated watermark hash. The watermark must embed the timestamp and user ID in a verifiable manner.

7. Audit Log Retention and Archival
- Given regulatory retention of seven years (FR-003), when audit entries exceed 30 days of age, then they must be moved to immutable WORM storage while preserving the hash chain. Archive verification scripts run weekly to confirm 100 % retention compliance.

8. Error Handling and Edge Cases
- Given a failure to write to the audit table (e.g., disk full or DB connection loss), when the failure occurs, then the application must queue the audit event in a local persistent buffer and retry every 30 seconds with exponential backoff up to five attempts. Each retry attempt is logged with attempt count. If retries exceed five attempts, an alert is raised to the Administrator role and a SECURITY_ALERT entry is created.

9. Compliance Reporting
- Given internal audit requirements, when a compliance officer requests an audit log report for a specific period, then the system must generate a CSV export that includes all required fields and a cryptographic signature verifying report integrity. The report size is limited to 10 MB; larger reports are split into multiple files with sequential naming.

## 1. User Stories

US-001 | Front‑Desk Staff | Record each view, edit, and export of patient intake records | Complete audit trail for compliance | High
US-002 | Clinician | View audit entries for a patient's record | Verify who accessed the data and when | High
US-003 | Administrator | Purge or archive audit logs older than 90 days | Storage costs stay within policy and logs remain immutable for required retention | Medium

## 3. Priority Ranking & Business Justification

US-001 – High: Directly satisfies HIPAA §164.312(b) "Audit Controls" by ensuring every access and export is recorded.
US-002 – High: Enables clinicians to perform forensic review, supporting compliance audits and incident response (HIPAA §164.308(a)(1)).
US-003 – Medium: Addresses data retention policies (HIPAA §164.310(d)) while controlling storage cost; can be deferred to post‑MVP if needed.

## 4. Design Needs (to be handed to Design)

1. Log Format – JSON lines with fields: timestamp_utc, actor_id, actor_role, action, patient_id, resource_id (if applicable), outcome, hash (optional), encryption_kid, metadata (e.g., field_changes).
2. Timestamp Source – System clock synchronized via NTP; all services must use UTC.
3. Immutability Mechanism – PostgreSQL `log_statement = 'all'` plus write‑once append‑only table or external write‑ahead log (WAL) archiving to an immutable object store (e.g., MinIO with bucket versioning).
4. Correlation ID – Every request receives a UUID propagated to the audit logger; required for traceability across micro‑services.
5. Retention & Archival – Retain logs for 7 years as required by HIPAA; archive after 90 days to cheaper WORM storage; bucket lifecycle policy enforces transition and expiration.
6. Access Controls – Only roles admin and auditor may query audit logs; clinicians have read‑only view limited to their patients via row‑level security; permission name is "audit_view" defined in RBAC matrix.
7. Error Handling – All failures to write an audit entry must be captured in a fallback error log and trigger an alert (e.g., Prometheus alert rule). Persistent buffer retries up to five times before escalation.
8. Encryption Key Management – KIDs are stored in a secure key vault; rotation occurs every 90 days per REQ‑001; each log entry records the KID used for encryption without exposing key material.
9. Performance Monitoring – KPI‑002 measures write latency; alerts fire if 99th‑percentile >250 ms or average >100 ms over 5‑minute windows.

## 5. Edge Cases & Failure Scenarios

Log Write Failure – If the database is unavailable, the application queues audit events in an in‑memory buffer persisted to local disk; retries occur every 30 seconds with exponential backoff up to five attempts; after five failures a critical alert is raised and a SECURITY_ALERT entry is logged.
Clock Skew – If NTP sync fails, timestamps fall back to system time with a warning flag `clock_skew=true` in the log entry.
Unauthorized Access Attempt – Attempt to read audit logs without proper role creates an UNAUTHORIZED_ACCESS audit entry and returns HTTP 403.
Large Export – Exporting >10 MB PDF triggers chunked logging; each chunk logs its own hash and sequence number to avoid oversized entries.
Archive Job Failure – Archive job failure records an ARCHIVE_FAILURE entry with error details and does not delete original rows; Ops team is notified via alerting pipeline.
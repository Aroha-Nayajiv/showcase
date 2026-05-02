# Risk Assessment Register (Overview)

### Strategic Objectives
- **Data Security**: End‑to‑end encryption (AES‑256 at rest, TLS 1.3 in transit) for all PHI, role‑based access controls (admin, clinician, front‑desk), and immutable audit logging retained for seven years.
- **Accessibility**: Form response time ≤200 ms (p95) and PDF export latency ≤1 s for authorized staff; WCAG 2.1 AA compliance for all user‑facing components.
- **Operational Reliability**: System uptime ≥99.9 % monthly; Docker‑Compose deployment reproducible on any Linux host without external dependencies.
- **Compliance Transparency**: Automated evidence collection for HIPAA Security Rule §164.312(a)(2)(iv) and related audit artifacts.

## Stakeholder Analysis
| Stakeholder | Primary Need | Key Pain Point | RBAC Tier | Linked Objective |
|------------|--------------|----------------|-----------|-------------------|
| Patient | Secure PHI submission | Data exposure concerns | None (external) | OBJ‑001 |
| Front‑Desk Staff | Fast validated entry | Manual re‑entry errors | Operator | OBJ‑002 |
| Clinician | Immediate data access | Delayed/incomplete records | Clinician | OBJ‑003 |
| Administrator | Configurable security controls | Complex permission management | Administrator | OBJ‑004 |
| Compliance Officer | Audit evidence | Labor‑intensive reporting | Auditor | OBJ‑005 |

## Functional Requirements
- **FR-001**: Collect patient demographics, insurance details, and medical history via a single structured web form. *Acceptance*: 100 % of required fields captured for every submission; validation errors flagged in real time with error rate <1 % per batch.
- **FR-002**: Enforce role‑based read/write permissions per stakeholder tier. *Acceptance*: Unauthorized role attempts are denied, logged with user ID, timestamp, and record ID; audit verifies 100 % denial events recorded.
- **FR-003**: Generate a PDF intake summary per patient with a dynamic watermark containing user ID and timestamp. *Acceptance*: Watermark appears on every page; export limited to authorized roles; export latency ≤1 s.
- **FR-004**: Retain a complete immutable audit log of all read and write operations for seven years. *Acceptance*: Log entries are append‑only, digitally signed, and cannot be altered; integrity script confirms 100 % of transactions logged.
- **FR-005**: Provide automated unit and integration test suites covering form validation, encryption enforcement, and RBAC edge cases. *Acceptance*: Test coverage ≥80 % and all tests pass in CI pipeline.

## Success Criteria / KPIs
- **KPI-001** – Encryption compliance rate: 100 % of PHI encrypted at rest and in transit. Measured by weekly compliance scans.
- **KPI-002** – Form latency: ≤200 ms p95. Measured by automated performance tests.
- **KPI-003** – Audit log completeness: 100 % of read/write events recorded with immutable signatures. Verified nightly by log integrity script.
- **KPI-004** – PDF export latency: ≤1 s per export. Validated by end‑to‑end functional test.
- **KPI-005** – System uptime: ≥99.9 % monthly. Tracked by infrastructure monitoring tools.

## Risk Assessment Register
- **RISK-001** – Unauthorized PHI access due to misconfigured RBAC. *Mitigation*: Automated RBAC validation scripts run on each release; quarterly role review meetings; alerts on permission changes.
- **RISK-002** – Encryption key compromise. *Mitigation*: Store keys in HSM; rotate keys every 90 days; audit key usage logs; enforce multi‑factor authentication for key access.
- **RISK-003** – Audit log tampering or loss. *Mitigation*: Write logs to append‑only immutable storage with digital signatures; weekly backup to air‑gapped media; periodic integrity verification.
- **RISK-004** – Deployment in non‑air‑gapped environment exposing PHI. *Mitigation*: Pre‑deployment environment validation script aborts if external network interfaces are detected; enforce network isolation policies.
- **RISK-005** – Performance degradation under peak load affecting SLA. *Mitigation*: Conduct regular stress testing; auto‑scale Docker services within on‑prem capacity limits; implement circuit‑breaker patterns for degraded components.

## Traceability Matrix
| Requirement ID | Stakeholder Owner | KPI Link |
|------------------|-------------------|----------|
| FR-001 | Front‑Desk Staff | KPI-002 |
| FR-002 | Administrator | KPI-003 |
| FR-003 | Clinician | KPI-004 |
| FR-004 | Compliance Officer | KPI-001 |
| FR-005 | Development Team | KPI-005 |
| NFR-001 | Security Engineer | KPI-001 |
| NFR-002 | Security Engineer | KPI-001 |
| NFR-003 | Performance Engineer | KPI-002 |
| NFR-004 | Operations Lead | KPI-005 |
| NFR-005 | Accessibility Lead | KPI-003 |

*All functional and non‑functional requirements are explicitly linked to measurable KPIs and assigned stakeholder owners to ensure accountability throughout the project lifecycle.*
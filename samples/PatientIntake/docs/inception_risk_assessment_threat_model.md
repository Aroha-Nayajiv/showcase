# Threat Model for Patient Intake System

## Stakeholder Analysis and Objectives
| Stakeholder | Primary Need | Business Objective (linked FR/KPI) |
|---|---|---|
| Patient | Confidentiality of PHI and assurance that data is only accessed by authorized staff | OBJ‑005: Demonstrate 100% encryption compliance and audit‑log integrity (FR‑001, FR‑003, KPI‑001, KPI‑003) |
| Front‑Desk Staff | Efficient data entry with real‑time validation and immediate submission receipt | OBJ‑002: Achieve >99% form completion success rate (FR‑001, KPI‑004) |
| Clinician | Immediate access to complete intake records to support timely care decisions | OBJ‑003: Ensure <200 ms average read latency (FR‑001, KPI‑002) |
| Administrator | Ability to configure roles, enforce RBAC, and review audit logs for compliance | OBJ‑004: Provide 100% audit‑log completeness and 7‑year retention (FR‑003, KPI‑003) |
| Compliance Officer | Evidence that system satisfies HIPAA Security Rule technical safeguards | OBJ‑005: Demonstrate 100% encryption compliance and audit‑log integrity (FR‑001, FR‑002, FR‑003, KPI‑001, KPI‑003) |

## Critical Business Requirements (Top 3)
1. **FR‑001 – Fast, Secure Data Capture**
   *Acceptance Criteria*: All mandatory fields validated; submission stored within 2 seconds; field‑level AES‑256 encryption applied before transmission; TLS 1.3 used for all network traffic.
2. **FR‑002 – Role‑Based Access Control**
   *Acceptance Criteria*: Admins have full read/write; Clinicians have read/export rights to all records; Front‑Desk staff can create and read only their own entries; RBAC enforced via PostgreSQL row‑level security policies; unauthorized access attempts are denied and logged.
3. **FR‑003 – Immutable Audit Logging**
   *Acceptance Criteria*: Every read, write, and export operation creates a log entry with user ID, timestamp, operation type, and record ID; logs are append‑only, digitally signed, and retained for 7 years; log completeness verified by automated script comparing operation count vs log entries (KPI‑003).

Additional high‑priority requirements include FR‑009 (air‑gap deployment) and FR‑004 (real‑time validation error rate <1%).

## Success Metrics (KPIs)
- **KPI‑001** – Encryption compliance: 100 % of PHI fields encrypted at rest (automated DB scan).
- **KPI‑002** – Transmission security: TLS 1.3 enforced for all connections (network scan).
- **KPI‑003** – Audit log completeness: 100 % of read/write/export events logged (log audit script).
- **KPI‑004** – Export watermark accuracy: 100 % of PDFs contain correct user ID and ISO‑8601 timestamp (PDF inspection test suite).
- **KPI‑005** – Deployment air‑gap validation: No outbound connections detected on start‑up (deployment health check).

All metrics are measured automatically during CI/CD pipelines and reported in the compliance dashboard for continuous monitoring.

{'status': 'error', 'error': 'All micro-goals failed', 'failed_micro_goals': [{'micro_goal_id': 'auto_goal_1', 'description': 'Consolidate executor content with reviewer feedback into a single coherent artifact artifact. Apply all reviewer improvements while preserving all original content, IDs, and structure. Do not create summaries - enhance and integrate intelligently.', 'result': {'status': 'error', 'error': 'No content generated'}, 'status': 'error', 'error': 'No content generated', 'model': 'gpt-oss-120b'}]}

## Business Vision
The PatientIntake system enables secure, rapid collection of patient demographics, insurance information, and medical history via a web form that encrypts data at rest and in transit, stores submissions in a locally hosted PostgreSQL database with strict role‑based access control, generates auditable PDF summaries with watermarking, and is deployed via Docker Compose in an air‑gapped environment. This vision supports timely clinical decision‑making, regulatory compliance (HIPAA, NIST), and operational reliability for on‑premise healthcare facilities.

## Measurable Success Criteria (KPIs)
- **KPI-001**: Encryption compliance rate – 100 % of PHI fields encrypted at rest (AES‑256).
- **KPI-002**: Form response time (p95) – ≤ 200 ms per request.
- **KPI-003**: Audit log completeness – 100 % of read/write events logged.
- **KPI-004**: Accessibility compliance score – 100 % WCAG 2.1 AA pass rate.
- **KPI-005**: Deployment air‑gap verification success – 100 % of deployments pass network isolation check.

## Risk Register (selected high‑impact risks)
| ID | Description | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| RISK-001 | Unauthorized PHI access due to misconfigured RBAC | M | H | Automated role‑permission matrix validation before each release; quarterly audit of role assignments | Security Engineer |
| RISK-002 | Encryption key compromise | L | H | Use HSM for key storage; rotate keys every 90 days; enforce MFA for vault access | Security Engineer |
| RISK-003 | Audit log tampering or loss | L | H | Write logs to append‑only immutable storage with digital signatures; daily checksum verification | Ops Manager |
| RISK-004 | Deployment in non‑air‑gapped environment inadvertently exposing PHI | M | H | Pre‑deployment script validates network isolation; aborts on external connectivity detection | DevOps Lead |
| RISK-005 | Accessibility non‑compliance leading to legal risk | L | M | Automated WCAG 2.1 AA testing integrated in CI pipeline; remediate failures before release | UX Lead |

## Acceptance Criteria
Each functional requirement (FR‑001‑FR‑005) and business requirement (REQ‑001‑REQ‑002) must have measurable acceptance criteria linked to the appropriate KPI and stakeholder owner. For example, FR‑001 is considered satisfied when monitoring shows 95th‑percentile view latency ≤ 200 ms for clinician role users over a 24‑hour period. All mitigations listed in the risk register must be verified through automated tests or manual audit procedures before sign‑off.
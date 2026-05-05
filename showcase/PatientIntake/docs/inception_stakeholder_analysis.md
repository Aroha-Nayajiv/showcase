# Stakeholder Analysis

### Strategic Objectives
1. **Regulatory Assurance** – Achieve full compliance with HIPAA Security Rule §164.312(a)(2)(iv) for encryption at rest and in transit (OBJ-001).
2. **Operational Efficiency** – Reduce manual data entry time by 40 % compared with paper-based intake, measured via average form completion duration (OBJ-002).
3. **Data Integrity & Traceability** – Maintain an immutable audit log for every read/write operation with a retention period of 7 years (OBJ-003).
4. **Open-Source Sustainability** – Use only community-maintained libraries and tools, avoiding vendor lock-in and minimizing licensing costs (OBJ-004).
5. **Secure Export Capability** – Provide authorized staff the ability to generate watermarked PDF summaries with embedded access timestamps (OBJ-005).

### Out of Scope
- Integration with external electronic health record (EHR) systems.
- Cloud-based hosting or managed database services.
- Mobile native applications; only web interface is covered in this phase.

### Stakeholder Table
| Stakeholder       | Primary Need                                            | Pain Point                                          | Role                     | Objective ID |
|-------------------|----------------------------------------------------------|------------------------------------------------------|--------------------------|--------------|
| Patient           | Secure and private intake of personal health information   | Fear of data breach and manual paperwork errors      | End User (no direct system access)   | OBJ-001 |
| Front-Desk Staff  | Efficient data capture and submission workflow            | Time spent re-entering data from paper forms         | Operator (create)       |
| Clinician         |

## Objectives Definitions
- **OBJ-001** – Ensure HIPAA-compliant privacy for all captured PHI.
- **OBJ-002** – Reduce intake processing time to meet the 40 % efficiency target.
- **OBJ-003** – Enable timely clinical decisions through rapid access to verified records.
- **OBJ-004** – Maintain governance and compliance via role-based controls and auditability.
- **OBJ-005** – Demonstrate regulatory compliance through auditable logs and encryption validation.

### Success Criteria / KPIs
| KPI ID   | Metric                     | Target                                            | Measurement Method                     |
|----------|----------------------------|---------------------------------------------------|------------------------------------------|
| KPI-001  |

## Functional Requirements
1. **FR-001** – Collect patient demographics, insurance information, and medical history via a structured web form.
   *Acceptance Criteria*: Form captures all mandatory fields (name, DOB, address, insurance policy number, medical conditions), validates input formats, stores encrypted data within 2 seconds of submission.
2. **FR-002** – Store submissions in a local PostgreSQL database with role-based access control (admin, clinician, front-desk) and immutable audit logging.
   *Acceptance Criteria*: RBAC enforces least privilege access; every read/write creates a tamper-evident audit entry retained for 7 years; unauthorized attempts are denied and logged.
3. **FR-003** – Generate a PDF intake summary per patient that is exportable only by authorized staff.
   *Acceptance Criteria*: PDF includes visible watermark with staff name and export timestamp; export action is logged; generation completes within 1 second for typical records.
4. **FR-004** – Provide automated unit and integration tests covering form validation, encryption handling, and access-control edge cases.
   *Acceptance Criteria*: Test suite achieves ≥90 % code coverage; tests run in CI pipeline on every commit and must all pass.
5. **FR-005** – Deploy the entire system via Docker Compose for on-premise air-gapped environments.
   *Acceptance Criteria*: Deployment script provisions all containers without external network calls; installation guide verifies successful setup on a fresh host within 30 minutes.

## Risk Assessment
| Risk ID |

## Compliance Alignment
The above requirements map directly to HIPAA Security Rule §164.312(a)(2)(iv) (encryption), §164.308(a)(1)(ii) (audit controls), and §164.312(b) (access control). Each functional and non-functional requirement includes a measurable acceptance criterion that can be demonstrated during a formal HIPAA audit.

## Scope Statement
- **In-Scope**: Development of a HIPAA-compliant patient intake system using only open-source technologies. Includes web-based structured form collection, encrypted storage in a local PostgreSQL instance, role-based access control (admin, clinician, front-desk), immutable audit logging, PDF summary generation with watermark and timestamp, automated unit/integration testing, and Docker-compose deployment for air-gapped on-prem environments.
- **Out-of-Scope**: Any cloud-hosted services, proprietary encryption libraries, third-party SaaS analytics, post-deployment operational monitoring tools beyond the defined audit log retention.
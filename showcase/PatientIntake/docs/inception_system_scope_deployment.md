# Deployment Topology and Docker Compose Specification

## 1. High‑Level Component Overview

| Component            | Description| Primary Functions| Security / Compliance Highlights |
|---------------------|-------------|--------------|---------------|
| **Web Front‑End**   | Static HTML/JS served over TLS 1.3, hosted in an isolated Docker network.   | Captures patient demographics, insurance data, and medical history; performs client‑side validation; initiates mutual TLS session with Application Service.  | Enforces TLS 1.3, uses Content‑Security‑Policy headers, and sanitizes all inputs to prevent XSS.  |
| **Application Service** | Stateless microservice written in Go/Python (open‑source only) that receives encrypted payloads. | Performs field‑level AES‑256 encryption at rest, enforces RBAC checks per FR-003, writes audit entries per FR-004, and forwards records to Data Store Service.  | Mutual TLS between Front‑End and service; logs security events to Audit Log Aggregator.  |
| **Data Store Service** | PostgreSQL 15 running in a private Docker overlay network with row‑level security (RLS) enabled. | Persists encrypted patient records; stores immutable audit logs; exposes read/write APIs only to Application Service via internal network.  | Encryption keys managed per‑tenant; RLS policies enforce least‑privilege access aligned with FR-003.  |
| **Audit Log Aggregator** | Side‑car container that consumes write/read events from Application Service and stores them in write‑once storage (e.g., immutable object store).  | Aggregates audit entries, timestamps each event, and retains logs for 7 years as required by HIPAA (FR-004).  | Logs are cryptographically signed; access limited to Compliance Officer (ST‑\u005).  |
| **Monitoring & Alerting** | Open‑source Prometheus/Grafana stack deployed in a dedicated monitoring network.   | Scrapes health metrics from all containers, defines SLA alerts for latency, error rates, and security incidents.  | Alerts trigger automated incident response playbooks; metrics feed KPI-001 – KPI-005 dashboards.  |

## 2. Stakeholder Identification, Needs & Objectives

| Stakeholder ID |	Role               |	Business Need  |	Pain Point Addressed|	Assigned RBAC Tier|	Linked Objective ID |
|----------------|	-----               |	----------											|	--------------------------						|	------------------------		|	-------------------|
| ST-001         |	Patient            |	Secure self‑service intake of demographics, insurance, | and medical history |	Paper forms are error‑prone and expose PHI        |	No system login (read‑only receipt)           |	OBJ-001                 |
| ST-002         |	Front‑Desk Staff   |	Fast, accurate entry of patient information without re‑keying data   |	Manual transcription leads to delays and errors   |	Write access to intake API; read audit logs       |	OBJ-002                 |
| ST-003         |	Clinician          |	Immediate access to complete patient intake summary for care decisions   |	Delayed retrieval of paper charts hampers treatment   |	Read‑only access to encrypted records; | request PDF export with watermark                |	OBJ-003                 |
| ST-004         |	Administrator      |	Centralized control over configuration, user provisioning, | and monitoring                         |	Disparate config files increase drift risk          |	Full admin rights across all containers           |	OBJ-004                 |
| ST-005         |	Compliance Officer  |	Ability to audit all data accesses and verify encryption controls meet HIPAA & SOC 2 standards   |	Lack of immutable audit trail makes reporting difficult   |	Read‑only access to audit log service & compliance reporting container   |	OBJ-005                 |

### Objective Definitions

* **OBJ-001** – Ensure HIPAA-compliant data capture at point of entry.
* **OBJ-002** – Streamline workflow and reduce transcription errors.
* **OBJ-003** – Provide clinicians with timely, secure patient information.
* **OBJ-004** – Maintain operational governance and high availability.
* **OBJ-005** – Demonstrate regulatory compliance and audit readiness.

## Business Requirements
**Functional Requirements**
| ID | Description | Acceptance Criteria |
|---|---|---|
| FR-001 | Collect patient demographics, insurance information, and medical history via a structured web form. | Form validates required fields, encrypts each PHI field at rest (AES-256) and in transit (TLS 1.3). |
| FR-002 | Store submissions in a local PostgreSQL database with role-based access control (admin, clinician, front-desk). | RBAC enforced via PostgreSQL Row-Level Security; unauthorized queries are denied (log entry created). |
| FR-003 | Generate a PDF intake summary per patient, exportable only by authorized staff. | PDF contains cryptographic watermark and immutable export timestamp; export attempts are logged. |
|
| FR-004 | Provide automated unit and integration tests covering form validation, encryption, and access control edge cases. CI pipeline runs ≥ 90% test coverage; all tests pass on each commit. |
|
| FR-005 Deploy the entire stack via Docker Compose for on-prem environments with no external cloud dependencies. |
 Docker Compose brings up all services on a clean air-gapped host within 45 minutes. |
|
| FR-006 Enforce TLS 1.3 on all ingress points using an Envoy sidecar with mutual TLS; disable legacy ciphers; automate certificate rotation via cert-manager. |
 Scans show 100% of inbound connections use TLS 1.3; certificates rotate without manual intervention. |
|
| FR-007 Maintain an immutable audit log of every read and write operation with tamper-evident hash chaining. |
 Log retention ≥ 7 years; audit-log completeness ≥ 99% per KPI-002. |
|
| FR-008 Provide a documented air-gap setup guide that includes image verification (SHA-256) and offline signature checks. |
 Guide enables first-time deployment without internet access; verification steps succeed on all test hosts. |
|

**Non-Funcional Requirements**
| ID | Description |
|---|---|
| NFR-001 AES-256 encryption at rest for all PHI fields. |
|
| NFR-002 TLS 1.3 or higher for all network traffic (HIPAA §164.312(a)(2)(iv)). |
|
| NFR-003 Horizontal scalability to support up to 5 000 concurrent users with ≤200 ms p95 latency (KPI‑006). |
|
| NFR-004 Service availability ≥ 99.9% monthly (KPI‑005). |
|

## Success Criteria & KPIs
The solution is considered successful when all of the following measurable conditions are met:

1. **Regulatory Compliance** – 100% of TLS connections use TLS 1.3 or higher and field-level AES‑256 encryption is verified (KPI‑001).
2. **Audit Log Integrity** – Tamper-evident audit entries for every read/write; completeness ≥ 99% (KPI‑002).
3. **PDF Export Security** – Cryptographic watermark and immutable timestamp present; zero unauthorized export incidents (KPI‑003).
4. **Deployment Reproducibility** – Full stack instantiated on a clean air-gapped host within 45 minutes (KPI‑004).
5. **High Availability** – Service uptime ≥ 99.9% monthly (KPI‑005).
6. **Scalability Readiness** – Horizontal scaling to 5 additional replicas does not exceed 200 ms p95 latency (KPI‑006).
7. **Stakeholder Satisfaction** – ≥ 90% positive rating in post-deployment survey (KPI‑007).

## Deployment Overview
The Docker Compose file defines three primary services: `web` (NGINX + Envoy sidecar), `app` (Python/Flask handling encryption and PDF generation), and `db` (PostgreSQL with RLS policies). All images are pre-downloaded into an internal registry; secrets are injected via Docker secrets to avoid plaintext credentials. The compose stack can be launched with a single `docker compose up -d` command after executing the air-gap setup guide (FR‑008).

---
*Document prepared by Refiner Agent – senior business analyst.*

# Patient Intake System – Inception Artifact

## 5. Business Objectives
| Objective ID | Owner | Description |
|---|---|---|
| OBJ‑001 | Front‑Desk Staff | Efficient entry and retrieval of intake forms; eliminate manual re‑entry errors |
| OBJ‑002 | Clinician | Quick access to patient history for care decisions |
| OBJ‑003 | Administrator | Manage system configuration and user permissions across multiple clinics |
| OBJ‑004 | Compliance Officer | Verify audit logs and encryption compliance; prove HIPAA adherence |
| OBJ‑005 | Security Lead | Ensure end‑to‑end encryption of PHI during transmission and storage |

## 6. Risk Assessment
| Risk ID | Description | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|---|
| RISK‑001 | PHI data breach during transmission | Medium (M) | High (H) | Enforce TLS 1.3 with perfect forward secrecy; field‑level AES‑256 encryption at rest |
| RISK‑002 | Unauthorized access due to misconfigured RBAC | Low (L) | High (H) | Automated RBAC policy validation tests; quarterly manual review |
| RISK‑003 | Failure to meet audit retention in air‑gap environment | Medium (M) | Medium (M) | Use immutable WORM storage; schedule quarterly compliance verification |
| RISK‑004 | Deployment delays from missing offline images | Low (L) | Medium (M) | Pre‑packaged image tarballs validated via SHA256 checksum before installation |
| RISK-005 | Performance degradation under peak load | Medium (M) | Medium (M) | Define horizontal scaling guidelines in Docker Compose; run automated load tests before release |

## 7. Governance Sign‑off
The charter will be presented to the Project Governance Board comprising the Administrator, Compliance Officer, Security Lead, and Architecture Lead. **Approval criteria:**
1. All functional and non‑functional requirements satisfied.
2. KPI baselines met in pilot validation.
3. No open high‑likelihood risks remain.

Upon sign‑off, the project proceeds to detailed design.
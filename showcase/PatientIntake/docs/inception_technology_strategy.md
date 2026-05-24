# Open-Source & Air-Gap Technology Strategy

## 1. Executive Summary
This artifact defines the strategic mandate for the PatientIntake system to operate exclusively on open-source software (OSS) within a strictly air-gapped, on-premises environment. It establishes the selection criteria for OSS components based on HIPAA Security Rule alignment, defines the operational model for offline dependency management, and specifies the data import/export protocols required to maintain system integrity without external cloud dependencies.

### 2.1 Strategic Constraint
The PatientIntake system is bound by a hard business constraint: **No proprietary software, SaaS dependencies, or external cloud services are permitted.** All components must be open-source, self-hosted, and capable of running in an isolated network environment.

### 2.2 OSS Selection Criteria
All selected technologies must satisfy the following criteria to ensure compliance, security, and maintainability:

| Criterion | Requirement | Rationale |
| :--- | :--- | :--- |
| **License** | Permissive (MIT, Apache 2.0) or Copyleft (GPL, AGPL) with clear commercial usage rights. | Ensures legal compliance and avoids vendor lock-in. |
| **HIPAA Alignment** | Must support field-level encryption, role-based access control (RBAC), and immutable audit logging. | Directly satisfies HIPAA Security Rule technical safeguards. |
| **Air-Gap Capability** | Must function without external network calls (e.g., no telemetry, no auto-update checkers). | Ensures data sovereignty and compliance with air-gap operational model. |
| **Community Support** | Active maintenance, documented security advisories, and available local deployment guides. | Ensures long-term viability and security patching in isolation. |
| **Data Residency** | Must store all data locally (PostgreSQL) with no external data exfiltration. | Meets organizational data sovereignty requirements. |

### 2.3 Prohibited Patterns
- **Telemetry/Analytics:** No embedded analytics or usage tracking that transmits data externally.
- **Auto-Updates:** No background processes that check for updates or download patches from the internet.
- **Proprietary Extensions:** No use of proprietary plugins or extensions that require external licensing servers.

## 3. Air-Gap Operational Model

### 3.1 Definition
The "Air-Gap" model requires that the PatientIntake system operates in a network segment with no direct connection to the public internet. All software updates, dependency installations, and data transfers must occur via secure, manual, or offline pipelines.

### 3.2 Offline Dependency Management
To maintain the open-source stack without external connectivity:
1. **Dependency Mirroring:** A designated "Update Workstation" (connected to the internet) will periodically fetch the latest secure versions of all OSS dependencies (e.g., PostgreSQL, Python packages, Docker images) and store them in a local, air-gapped repository (e.g., local PyPI mirror, local Docker registry).
2. **Secure Transfer:** Updates are transferred to the production environment via encrypted, tamper-evident media (e.g., encrypted USB drives) or a secure, one-way data diode.
3. **Verification:** All transferred artifacts must be verified against cryptographic checksums (SHA-256) before installation to ensure integrity.

### 3.3 Update Pipeline
1. **Patch Identification:** Security advisories are monitored on the Update Workstation.
2. **Artifact Build:** New Docker images and dependency bundles are built locally.
3. **Transfer:** Artifacts are moved to the air-gapped environment.
4. **Deployment:** Docker Compose is used to update services with zero downtime, using named volumes to preserve data.

### 4.1 Secure Data Export (PDF Intake Summary)
Authorized staff (Admin, Clinician) can generate PDF intake summaries. To ensure integrity and traceability in an air-gapped environment:
- **Watermarking:** Every exported PDF must include a dynamic watermark containing the user's identity, timestamp, and IP address.
- **Audit Logging:** Every export event is logged in the PostgreSQL audit table with the user ID, timestamp, and file hash.
- **Access Control:** Only users with the `Clinician` or `Admin` role can trigger the export. `Front Desk` and `Patient` roles are denied.

### 4.2 Data Import Protocol
For initial data migration or bulk updates:
- **Format:** CSV or JSON files, encrypted at rest using AES-256.
- **Validation:** All imported data must pass schema validation and HIPAA compliance checks (e.g., no PII in non-encrypted fields) before ingestion.
- **Audit Trail:** Import operations are logged as bulk transactions, with a summary of records processed and any errors encountered.

## 5. HIPAA Security Rule Mapping

The following table maps key HIPAA Security Rule technical safeguards to specific open-source configuration parameters or architectural patterns:

| HIPAA Safeguard | Technical Implementation | OSS Component/Configuration |
| :--- | :--- | :--- |
| **Access Control (164.312(a)(1))** | Role-Based Access Control (RBAC) with least privilege. | PostgreSQL Row-Level Security (RLS) + Application-level RBAC. |
| **Audit Controls (164.312(b))** | Immutable audit log of all read/write operations. | PostgreSQL `pgAudit` extension + Application-level logging. |
| **Integrity (164.312(c)(1))** | Field-level encryption for PHI at rest and in transit. | PostgreSQL `pgcrypto` + TLS 1.3 for transit. |
| **Transmission Security (164.312(e)(1))** | Encryption of PHI during transmission. | TLS 1.3 for all web traffic; no HTTP. |
| **Person or Entity Authentication (164.312(d))** | Multi-factor authentication (MFA) for administrative access. | Application-level MFA (e.g., TOTP) for Admin/Clinician roles. |

## 6. Technology Stack Selection

### 6.1 Core Components
- **Database:** PostgreSQL (with `pgcrypto` and `pgAudit` extensions).
- **Deployment:** Docker Compose (for deterministic, isolated environments).
- **Runtime:** Python (with `PYTHONUNBUFFERED=1` for logging integrity).
- **Web Server:** Nginx (reverse proxy with TLS termination).

### 6.2 Justification
- **PostgreSQL:** Industry-standard, robust, supports row-level security and encryption extensions, aligns with open-source mandate.
- **Docker Compose:** Simplifies on-premises deployment, ensures environment consistency, supports air-gap deployment via image export/import.
- **Field-Level Encryption:** Provides granular protection for PHI, ensuring that even if the database is compromised, specific fields remain unreadable without the encryption key.

## 7. Governance and Accountability

| Role | Responsibility |
| :--- | :--- |
| **Project Sponsor** | Ultimate authority for budget and strategic alignment. |
| **Product Owner** | Responsible for prioritizing requirements and accepting deliverables. |
| **Technical Lead** | Responsible for architectural decisions and technical feasibility. |
| **Compliance Officer** | Responsible for validating HIPAA compliance of the design and implementation. |

## 8. Knowledge Gaps

| Gap | Owner | Evidence Needed |
| :--- | :--- | :--- |
| **Specific Encryption Algorithm** | Compliance Officer | HIPAA Security Rule technical safeguard specifications or internal security policy. |
| **Data Retention Period** | Compliance Officer | State/federal retention laws or internal data retention policy. |
| **Hardware Requirements** | IT Operations | Performance benchmarks for expected patient volume and concurrent users. |

## 9. Approval and Sign-Off

| Role | Name | Date |
| :--- | :--- | :--- |
| **Prepared By** | Executor (Inception Phase) | [Current Date] |
| **Reviewed By** | [To be defined by VP] | [Date] |
| **Approved By** | [To be defined by VP] | [Date] |

This strategy establishes the foundational constraints and operational model for the PatientIntake system, ensuring compliance with HIPAA and organizational data sovereignty requirements.
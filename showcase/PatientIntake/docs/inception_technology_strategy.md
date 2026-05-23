# Inception Technology Strategy

## 1. Executive Summary

This document defines the technology strategy for the PatientIntake system, a HIPAA-compliant patient intake web application. The strategy mandates the exclusive use of open-source technologies to ensure cost efficiency, vendor independence, and alignment with the on-premises deployment model. The architecture is built around a structured web form for data capture, a local PostgreSQL database for secure storage, and Docker Compose for deterministic, air-gap capable deployment. This strategy explicitly maps the required open-source components to the project's functional and compliance requirements, establishing the foundational technical decisions for the Design and Development phases.

## 2. Open-Source Technology Stack Selection

The following table defines the approved open-source technology stack. Each selection is justified by its ability to meet HIPAA compliance requirements, support on-premises deployment, and maintain a robust open-source ecosystem for long-term maintenance.

| Component Category | Selected Technology | Justification & Strategic Fit |
| :--- | :--- | :--- |
| **Web Form Framework** | React (with TypeScript) | Industry-standard open-source library for building structured, accessible, and type-safe user interfaces. Enables robust client-side validation for patient demographics and medical history, reducing server load and improving user experience. |
| **Backend API** | Python (FastAPI) | High-performance, open-source web framework. Native support for asynchronous operations and automatic API documentation (OpenAPI/Swagger). Strong ecosystem for data validation (Pydantic) and integration with PostgreSQL. |
| **Primary Data Store** | PostgreSQL | The mandated relational database. Chosen for its ACID compliance, robust JSONB support for flexible medical history storage, and advanced security features (row-level security, encryption extensions). Fully open-source and suitable for on-premises deployment. |
| **PDF Generation** | WeasyPrint | Open-source library for converting HTML/CSS to PDF. Allows for the generation of standardized, watermarked intake summaries using the same HTML templates as the web form, ensuring consistency and reducing maintenance overhead compared to binary PDF libraries. |
| **Container Orchestration** | Docker Compose | The mandated deployment tool. Provides a declarative, single-file definition of the multi-container application (Web, API, DB). Essential for the air-gap requirement, as it allows the entire environment to be version-controlled and deployed without external cloud dependencies. |
| **Encryption/Security** | OpenSSL / libsodium | Standard open-source cryptographic libraries. Used for implementing field-level encryption at rest and in transit (TLS 1.2+). Ensures compliance with HIPAA Security Rule 164.312(c) and (e) without relying on proprietary key management services. |

### 2.1 Docker Compose Architecture

The system is deployed as a set of interconnected services defined in a single `docker-compose.yml` file. This architecture ensures that all dependencies are explicitly declared and version-controlled.

*   **Frontend Service:** Serves the React application. Static files are served via a lightweight Nginx container.
*   **Backend Service:** Runs the FastAPI application. Handles business logic, form validation, and encryption/decryption operations.
*   **Database Service:** Runs PostgreSQL. Stores all patient data, audit logs, and user credentials. Data is persisted via a named Docker volume to ensure durability across container restarts.

### 2.2 Air-Gap Deployment Constraints

The on-premises, air-gapped deployment model imposes strict constraints on technology selection and operational procedures:

1.  **No External Dependencies:** All Docker images must be built from scratch or from official open-source base images that are cached locally. No runtime pulls from public registries (e.g., Docker Hub) are permitted during deployment.
2.  **Dependency Management:** The Software Bill of Materials (SBOM) for all containers must be generated during the build process. This SBOM is used to verify the integrity of the air-gapped environment against known CVEs using offline scanning tools.
3.  **Patch Management:** Security patches and dependency updates must be applied in a connected development environment, tested, and then manually imported into the air-gapped production environment via secure, audited transfer mechanisms (e.g., encrypted USB drives or secure file transfer protocols over isolated networks).
4.  **Monitoring:** Local monitoring tools (e.g., Prometheus/Grafana stack, deployed as additional Docker containers) must be used to track system health, as external cloud-based monitoring services are unavailable.

## 3. Security & Compliance Technology Controls

### 3.1 Field-Level Encryption

To comply with HIPAA Security Rule 164.312(c)(1) and (c)(2)(i), sensitive patient data (demographics, insurance, medical history) must be encrypted at the application level before being stored in PostgreSQL.

*   **Strategy:** The Backend Service will handle encryption and decryption. Sensitive fields will be encrypted using AES-256-GCM (via OpenSSL or libsodium) before insertion into the database.
*   **Key Management:** Encryption keys will be managed via a local Key Management Service (KMS) or environment variables injected into the Backend Service container. Key rotation policies will be defined in the Design phase.
*   **Audit Trail:** All encryption/decryption operations will be logged in the audit trail to ensure traceability.

### 3.2 Role-Based Access Control (RBAC)

Access to the system will be enforced at both the application and database layers.

*   **Application Layer:** The Backend Service will implement RBAC middleware to restrict access to API endpoints based on user roles (Admin, Clinician, Front Desk). Each user will have a unique identifier, and shared accounts are prohibited.
*   **Database Layer:** PostgreSQL Row-Level Security (RLS) policies will be configured to ensure that users can only access data relevant to their role. For example, Front Desk staff may only create records, while Clinicians can read and update them.

### 3.3 Audit Logging

HIPAA Security Rule 164.312(b) requires full audit logs of all access to electronic protected health information (ePHI).

*   **Implementation:** The Backend Service will log every read and write operation to a dedicated `audit_logs` table in PostgreSQL. Logs will include timestamps, user ID, action performed, and record ID.
*   **Immutability:** Audit logs will be designed to be append-only and immutable to prevent tampering. Retention will be set to 6 years, as required by HIPAA.

## 4. Risk Management: Open-Source & On-Premises

## 5. Next Steps

1.  **Design Phase:** Define specific encryption algorithms and key management procedures. Detail the API contracts and database schemas. Finalize the RBAC matrix.
2.  **Development Phase:** Implement the React frontend, FastAPI backend, and PostgreSQL database. Integrate field-level encryption and audit logging.
3.  **Testing Phase:** Validate access controls, encryption, and audit logging. Perform security scanning of the Docker images.
4.  **Deployment Phase:** Deploy via Docker Compose with air-gap configuration. Document the air-gap setup guide.
5.  **Operations Phase:** Conduct regular access reviews and audit log reviews. Monitor system health using local tools.

This technology strategy ensures that the PatientIntake system is built on a secure, compliant, and maintainable open-source foundation, fully aligned with the on-premises deployment and air-gap constraints.
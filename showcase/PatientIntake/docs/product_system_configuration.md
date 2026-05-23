# System Configuration & Deployment

### 1.1 Service Definitions

| Service Name | Role | Technology | Health Check Strategy |
| :--- | :--- | :--- | :--- |
| `app-server` | Handles business logic, form processing, and API endpoints. | Python (FastAPI/Flask) | HTTP GET `/health` returns 200 OK. |
| `db` | Stores patient intake data, user credentials, and audit logs. | PostgreSQL | `pg_isready` command checks database readiness. |
| `proxy` | Routes external traffic to the application server and terminates TLS. | Nginx | HTTP GET `/nginx-health` returns 200 OK. |

### 1.2 Deployment Constraints

- **On-Premises Only**: The system must run entirely within the client's local network infrastructure.
- **Air-Gap Capability**: The deployment must support offline initialization. All dependencies (Docker images, configuration files, and assets) must be importable via local storage (e.g., USB drives) without internet access.
- **Open Source Only**: All software components must be open-source technologies. No proprietary licenses are permitted.
- **Data Persistence**: All data must be stored in named Docker volumes to survive container restarts and updates.

## 1. User Stories & Acceptance Criteria

### US-ADM-001: Admin User Provisioning
**As a** System Administrator,
**I want to** create new user accounts and assign them specific roles (Clinician or Front Desk),
**So that** authorized staff can access the system to perform their duties while maintaining strict access control.

**Acceptance Criteria:**
- **AC-ADM-001.1 (Happy Path)**: Given the Admin is logged in with 'Admin' privileges, When they submit a new user form with a valid email, full name, and selected role, Then the system creates the account, generates a temporary secure credential, and displays a success confirmation.
- **AC-ADM-001.2 (Invalid Input)**: Given the Admin attempts to create a user with an invalid email format (e.g., 'admin@'), When they click 'Create', Then the system displays 'Invalid email format. Expected name@domain.com' and prevents submission.
- **AC-ADM-001.3 (Duplicate User)**: Given the Admin attempts to create a user with an email that already exists in the system, When they click 'Create', Then the system displays 'A user with this email already exists' and prevents submission.
- **AC-ADM-001.4 (System Dependency Failure)**: Given the PostgreSQL database is unavailable, When the Admin attempts to create a user, Then the system displays 'Service temporarily unavailable. Please try again later.' and preserves the entered form data.

### US-ADM-002: System Configuration & Health Verification
**As a** System Administrator,
**I want to** view system health status and verify deployment integrity,
**So that** I can ensure the on-premises system is operational and compliant with air-gap constraints.

**Acceptance Criteria:**
- **AC-ADM-002.1 (Health Check)**: Given the Admin is on the system dashboard, When they view the 'System Status' widget, Then they see the status of PostgreSQL, Application Server, and Reverse Proxy as 'Healthy' or 'Unhealthy' based on real-time health checks.
- **AC-ADM-002.2 (Configuration Update)**: Given the Admin is in the 'System Configuration' section, When they update a parameter (e.g., session timeout to 15 minutes), Then the system saves the configuration and applies it to the running containers without requiring a full restart.
- **AC-ADM-002.3 (Air-Gap Verification)**: Given the Admin initiates a 'System Integrity Check', When the process completes, Then the system reports that no external cloud endpoints were contacted during the last 24 hours, confirming air-gap compliance.

### US-ADM-003: Admin Audit Log Review
**As a** System Administrator,
**I want to** view and filter audit logs of all user actions and system events,
**So that** I can investigate suspicious activity and demonstrate compliance with HIPAA audit requirements.

**Acceptance Criteria:**
- **AC-ADM-003.1 (Log Visibility)**: Given the Admin is on the 'Audit Log' page, When they view the log entries, Then they see a table with columns: Timestamp, User, Action, Resource, and IP Address.
- **AC-ADM-003.2 (Filtering)**: Given the Admin is viewing audit logs, When they filter by 'Action: User Login', Then only entries matching that action are displayed.
- **AC-ADM-003.3 (Data Integrity)**: Given the Admin attempts to delete an audit log entry, When they click 'Delete', Then the system denies the action and displays 'Audit logs are immutable for compliance purposes.'

## 2. Security & Compliance Configuration

### 2.1 Field-Level Encryption
- **At Rest**: All sensitive patient fields (e.g., medical history, insurance details) must be encrypted at the application level before being written to PostgreSQL. The encryption key must be managed via environment variables or a local key management service, not hardcoded in the container.
- **In Transit**: All communication between the Reverse Proxy and the Application Server, and between the Application Server and the Database, must use TLS 1.2 or higher. Internal services must use mutual TLS (mTLS) where possible.

### 2.2 Role-Based Access Control (RBAC)
- **Admin**: Full access to system configuration, user management, and audit logs.
- **Clinician**: Access to patient intake forms, record review, and update capabilities. No access to system configuration or user management.
- **Front Desk**: Access to patient intake forms and submission. No access to record review or system configuration.
- **Patient**: Access to view their own intake summary and export PDF (if enabled).

### 2.3 Audit Logging
- All user actions (login, logout, create, update, delete, view) must be logged to an immutable audit log.
- Audit logs must be stored in a separate volume from the main application data to prevent accidental deletion.
- Logs must include: Timestamp, User ID, Action, Resource ID, and IP Address.

## 3. Air-Gap Setup Guide

### 3.1 Asset Import
1. **Prepare Local Storage**: Copy all Docker images (`.tar` files), configuration files (`docker-compose.yml`, `.env`), and any required assets to a local USB drive or internal network share.
2. **Import Images**: On the target machine, load the Docker images using `docker load -i <image_file>.tar`.
3. **Verify Checksums**: Before deployment, verify the checksums of all imported files against a pre-generated manifest to ensure integrity.

### 3.2 Offline Initialization
1. **Environment Setup**: Ensure the target machine has Docker and Docker Compose installed.
2. **Configuration**: Copy the `docker-compose.yml` and `.env` files to the deployment directory. Update the `.env` file with local secrets (e.g., database passwords, encryption keys).
3. **Start Services**: Run `docker-compose up -d` to start the services.
4. **Health Verification**: Use the system health check endpoint to verify all services are running correctly.

### 3.3 Update Procedure
1. **Download Update Package**: Obtain the new version's Docker images and configuration files from the internal update server or USB drive.
2. **Backup Data**: Before updating, backup the PostgreSQL volume and configuration files.
3. **Apply Update**: Replace the old Docker images and configuration files with the new ones.
4. **Restart Services**: Run `docker-compose down` followed by `docker-compose up -d` to apply the update.
5. **Verify**: Check the system health and audit logs to ensure the update was successful.

## 4. Design Needs

- **Design Artifact**: `product_admin_management` must define the UI for user provisioning, de-provisioning, and system configuration.
- **Design Artifact**: `product_admin_management` must define the audit log viewer interface with filtering capabilities.
- **Design Artifact**: `product_admin_management` must define the system health dashboard layout.
- **Constraint**: All admin actions must be logged in the audit trail (see `product_audit_logging`).
- **Constraint**: System configuration changes must be persisted in a way that survives container restarts (e.g., mounted volumes).

## 5. Knowledge Gaps

- **Gap 1**: Exact password complexity requirements for initial credentials generated by the Admin. Decision Owner: Product Owner. Evidence Needed: HIPAA Security Rule 164.308(a)(5) specific implementation guidance or client policy.
- **Gap 2**: Specific retention period for audit logs. Decision Owner: Compliance Officer. Evidence Needed: HIPAA retention requirements or client policy.
- **Gap 3**: Backup and recovery procedure for the PostgreSQL database in an air-gapped environment. Decision Owner: System Administrator. Evidence Needed: Client's backup infrastructure capabilities.
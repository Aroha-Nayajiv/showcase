# Admin & User Management Specification

## 1. Overview
This specification defines the administrative controls for the HIPAA-compliant patient intake system. It governs the creation, modification, and deactivation of user accounts, the assignment of role-based access control (RBAC) permissions, and the management of the audit log infrastructure. The system supports three distinct roles: **Admin**, **Clinician**, and **Front Desk**.

## 2. User Roles & Permissions Matrix

| Permission Category | Admin | Clinician | Front Desk |
| :--- | :---: | :---: | :---: |
| **User Management** | | | |
| Create/Edit/Deactivate Users | ✅ | ❌ | ❌ |
| Assign/Change Roles | ✅ | ❌ | ❌ |
| Reset User Passwords | ✅ | ❌ | ❌ |
| **Patient Data Access** | | | |
| View Patient Demographics | ✅ | ✅ | ✅ |
| View Insurance Information | ✅ | ✅ | ✅ |
| View Medical History | ✅ | ✅ | ❌ |
| **Intake Operations** | | | |
| Submit New Intake Forms | ✅ | ✅ | ✅ |
| Edit Submitted Forms | ✅ | ✅ | ✅ |
| **Reporting & Audit** | | | |
| View System Audit Logs | ✅ | ❌ | ❌ |
| Export Intake Summaries (PDF) | ✅ | ✅ | ❌ |
| **System Configuration** | | | |
| Manage Encryption Keys | ✅ | ❌ | ❌ |
| Configure System Settings | ✅ | ❌ | ❌ |

## 3. User Lifecycle Management

### 3.1 User Creation
*   **Actor**: Admin
*   **Trigger**: Admin initiates user creation via the Admin Dashboard.
*   **Process**:
    1.  Admin enters user details: Full Name, Email Address, and Initial Role.
    2.  System validates email format and uniqueness.
    3.  System generates a temporary, cryptographically secure password.
    4.  System sends an automated email to the user with login instructions and the temporary password.
    5.  System logs the creation event in the Audit Log.
*   **Acceptance Criteria**:
    *   AC-1: Admin can create a user with any of the three valid roles.
    *   AC-2: System rejects duplicate email addresses.
    *   AC-3: Temporary password must meet HIPAA complexity requirements (min 12 chars, mixed case, numbers, symbols).
    *   AC-4: Audit log entry includes: `action: user_created`, `actor_id`, `target_user_id`, `timestamp`, `ip_address`.

## 5. Knowledge Gaps
*   **Password Expiration Policy**: The project DNA does not specify a password expiration policy (e.g., 90 days). This is a HIPAA best practice but not explicitly required. *Decision Owner: Product Owner. Evidence Needed: Client preference or industry standard for password rotation.*
*   **Multi-Factor Authentication (MFA)**: The project DNA does not specify if MFA is required for Admin or Clinician roles. *Decision Owner: Security Officer. Evidence Needed: HIPAA security risk assessment findings.*

## 6. Role-Based Access Control (RBAC) Matrix
Access is enforced at the API and UI layer. All endpoints require authentication via JWT tokens containing the user's role claims.

| Feature / Action | Admin | Clinician | Front Desk |
| :--- | :---: | :---: | :---: |
| **User Management** | | | |
| Create/Edit/Deactivate Users | ✅ | ❌ | ❌ |
| Assign Roles | ✅ | ❌ | ❌ |
| Reset User Passwords | ✅ | ❌ | ❌ |
| **Patient Data** | | | |
| View Patient Intake Forms | ✅ | ✅ | ✅ |
| Edit Patient Demographics | ✅ | ✅ | ✅ |
| Edit Medical History | ✅ | ✅ | ❌ |
| **System & Audit** | | | |
| View System Audit Logs | ✅ | ❌ | ❌ |
| Export Audit Logs (CSV/PDF) | ✅ | ❌ | ❌ |
| Manage System Configuration | ✅ | ❌ | ❌ |

### 6.4 Password Policy
- **Complexity**: Minimum 12 characters, at least one uppercase, one lowercase, one number, one special character.
- **Rotation**: Passwords must be changed every 90 days. System sends a warning email 14 days before expiration.
- **History**: System prevents reuse of the last 5 passwords.

## 7. Audit Logging Requirements
All administrative actions and user access events must be logged to an immutable audit table.

### 7.1 Audit Log Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `log_id` | UUID | Unique identifier for the log entry |
| `timestamp` | ISO 8601 | UTC timestamp of the event |
| `user_id` | UUID | ID of the user performing the action (null for system events) |
| `action` | String | e.g., `USER_CREATED`, `LOGIN_SUCCESS`, `LOGIN_FAILED`, `DATA_EXPORT` |
| `resource_type` | String | e.g., `USER`, `PATIENT_RECORD`, `AUDIT_LOG` |
| `resource_id` | UUID | ID of the affected resource |
| `ip_address` | String | IP address of the request |
| `user_agent` | String | Browser/Client user agent |
| `outcome` | String | `SUCCESS` or `FAILURE` |
| `details` | JSON | Optional additional context (e.g., old/new role values) |

### 7.2 Log Retention
- Audit logs must be retained for a minimum of 6 years to comply with HIPAA documentation requirements.
- Logs must be stored in a separate, read-only database schema or table with restricted write access.

## 8. Integration Points
- **Authentication Service**: Integrates with the system's JWT provider for token issuance and validation.
- **Email Service**: Integrates with the SMTP service for sending activation and password reset emails.
- **Database**: Writes to the `audit_logs` table in PostgreSQL. All writes must be synchronous to ensure no audit gaps.

## 9. Edge Cases & Error Handling
- **Duplicate Email**: If an Admin attempts to create a user with an existing email, the system returns a `409 Conflict` error with the message "User with this email already exists."
- **Invalid Token**: If a user attempts to activate with an expired or invalid token, the system returns a `400 Bad Request` error.
- **Concurrent Sessions**: If a user is deactivated while logged in, their next API request will receive a `401 Unauthorized` error, forcing re-authentication.
- **Audit Log Failure**: If the audit log write fails, the primary action (e.g., user creation) should still proceed, but the system must alert the Admin immediately via an internal error notification. *Note: For strict HIPAA compliance, consider making the audit log write synchronous and failing the primary action if the log write fails, depending on final risk assessment.*

## 10. Cross-Artifact Coherence Check
- **Role Names**: Consistent use of "Admin", "Clinician", "Front Desk" across all user stories.
- **Success Criteria**: Audit logging is a shared requirement with the Data Storage artifact; this spec defines the *what* and *who*, while the Data Storage artifact defines the *where* and *how* (encryption).
- **Design Gaps**: The Admin Dashboard UI design is owned by the Design artifact; this spec provides the functional requirements for it.
- **User Journey**: User creation (Admin) -> Activation (User) -> Login (All) -> Data Access (Role-based). No gaps identified.

Cross-artifact coherence: PASS
# Admin Reporting & Audit Log

This artifact defines the administrative oversight capabilities, specifically the Role-Based Access Control (RBAC) matrix, audit log viewing, and PDF export workflows for the Admin role within the PatientIntake system. It establishes the user-facing permissions and compliance requirements for administrative actions, deferring technical implementation details (such as PostgreSQL Row-Level Security or specific encryption algorithms) to the Design phase.

## 1. Admin Role Definition & RBAC Matrix

The Admin role is the highest-privilege operational role in the PatientIntake system, responsible for system integrity, user management, and HIPAA compliance auditing. The Admin role does not perform clinical data entry or patient intake submission.

### RBAC Permission Matrix

| Feature Area | Action | Admin | Clinician | Front Desk |
| :--- | :--- | :--- | :--- | :--- |
| User Management | Create/Edit/Delete Users | Yes | No | No |
| User Management | Assign/Revoke Roles | Yes | No | No |
| Audit Logs | View All System Logs | Yes | No | No |
| Audit Logs | Export Audit Logs (CSV/PDF) | Yes | No | No |
| Patient Records | View All Patient Records | Yes | Yes (Assigned) | No |
| Patient Records | Edit Patient Records | No | Yes (Assigned) | No |
| PDF Export | Generate Watermarked PDFs | Yes | Yes (Assigned) | No |
| System Config | Modify System Settings | Yes | No | No |
| System Config | View Deployment Status | Yes | No | No |

**Decision Rationale:** The Admin role requires unrestricted access to audit logs and user management to fulfill HIPAA Security Rule (45 CFR 164.312) requirements for access control and audit controls. Clinicians and Front Desk staff are restricted to their respective operational scopes to minimize the attack surface and enforce the principle of least privilege.

## 2. User Stories & Acceptance Criteria

### US-001: Admin Audit Log Dashboard Access
As an Admin,
I want to access a centralized dashboard displaying all system audit logs,
So that I can monitor system activity, detect unauthorized access attempts, and ensure HIPAA compliance.

**Acceptance Criteria:**
1. Given I am logged in as an Admin,
   When I navigate to the "Audit Log" section,
   Then I see a paginated table of all system events (logins, data reads, data writes, exports).
2. Given I am on the Audit Log Dashboard,
   When I apply filters (e.g., date range, user, event type),
   Then the table updates to show only matching records within 2 seconds.
3. Given I am logged in as a Clinician or Front Desk staff,
   When I attempt to access the "Audit Log" URL or menu item,
   Then I am denied access and shown a "403 Forbidden" error message.

> This story requires design artifact: design_admin_dashboard_ui

### US-004: Admin Manage User Accounts
As an Admin,
I want to create, edit, and delete user accounts and assign roles,
So that I can onboard new staff and revoke access for terminated employees.

**Acceptance Criteria:**
1. Given I am on the "User Management" page,
   When I click "Create New User" and fill in required fields (name, email, role),
   Then the system creates the user account and sends an invitation email.
2. Given I am editing a user account,
   When I change a user's role from "Clinician" to "Front Desk",
   Then the system updates the user's permissions immediately and logs the role change in the audit log.
3. Given I am deleting a user account,
   When I confirm the deletion,
   Then the user is deactivated, and the system logs the deletion action in the audit log.
4. Given I am logged in as a Clinician or Front Desk staff,
   When I attempt to access the "User Management" page,
   Then I am denied access and shown a "403 Forbidden" error message.

> This story requires design artifact: design_user_management_ui

## 3. Failure Modes & Edge Cases

*   **Admin Session Expiry:** If an Admin's session expires while viewing audit logs, the system redirects to the login page upon next action. No data is lost.
*   **Audit Log Storage Full:** If the audit log storage reaches capacity, the system alerts the Admin via email and UI banner, and stops logging new events until space is cleared.
*   **PDF Generation Failure:** If PDF generation fails (e.g., missing data), the system displays an error message "Failed to generate PDF. Please try again." and logs the error.
*   **Unauthorized Export Attempt:** If a non-Admin user attempts to access the export API directly, the system returns a 403 Forbidden error and logs the attempt.
*   **Concurrent User Edit:** If two Admins try to edit the same user account simultaneously, the system uses optimistic locking and shows a "Conflict" error to the second user.

## 4. Design Needs for Downstream Phases

1.  **UI/UX Design:** Design the Admin Dashboard layout, ensuring high-density data presentation for audit logs and clear, distinct workflows for user management.
2.  **API Design:** Define the RESTful endpoints for retrieving paginated audit logs and exporting filtered data, ensuring strict RBAC middleware enforcement.
3.  **Data Model:** Define the schema for audit log entries, ensuring fields for `actor_id`, `action_type`, `timestamp`, and `ip_address` are captured for every system event.
4.  **PDF Service:** Design the PDF generation service to support dynamic watermarking with the requester's identity and timestamp, ensuring compliance with HIPAA traceability requirements.

## 5. Knowledge Gaps & Assumptions

*   **Audit Log Retention Policy:** The specific duration for which audit logs must be retained (e.g., 6 years per HIPAA guidelines) is not explicitly defined in the project DNA. This is a critical compliance requirement that must be resolved by the Product Owner or Compliance Officer.
*   **Export Format Standards:** While CSV and PDF are mentioned, the specific structural requirements for the CSV export (e.g., delimiter, encoding) and PDF template (e.g., specific HIPAA-compliant headers) are not defined. These should be specified in the Design phase based on the retention policy.
*   **Real-time vs. Batch Logging:** It is assumed that audit logs are written synchronously with the action to ensure immediate availability for Admin review. If performance constraints arise, a batched logging approach may be considered, but this must be explicitly decided in the Design phase.

## 6. Cross-Artifact Dependencies

*   **product_admin_management:** This artifact relies on the user management workflows defined in `product_admin_management` for the creation and deletion of user accounts.
*   **product_audit_logging:** This artifact defines the *viewing* and *exporting* of audit logs, while `product_audit_logging` defines the *ingestion* and *storage* of these logs. The two artifacts must align on the data schema and API contracts.
*   **product_pdf_export:** This artifact defines the *watermarking* and *access control* for PDF exports, while `product_pdf_export` defines the *generation* and *formatting* of the PDFs. The two artifacts must align on the PDF template and watermarking logic.
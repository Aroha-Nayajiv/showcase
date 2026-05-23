# Patient Identity & Access Management

This artifact defines the product requirements for the authentication, session management, and role-based access control (RBAC) layer of the PatientIntake system. It ensures that only authorized personnel (Admin, Clinician, Front Desk) can access the system and that their actions are strictly governed by their assigned roles. This feature is a prerequisite for all other product artifacts, as no data submission, review, or export can occur without a valid, authenticated session.

## 1. User Stories & Acceptance Criteria

### US-001: Secure Login with Role-Based Redirection
**Priority:** P1 (Must Have) - Core entry point for all system interactions.
**Actor:** Admin, Clinician, or Front Desk Staff

**Acceptance Criteria:**

| ID | Scenario | Action | Expected Result |
| :--- | :--- | :--- | :--- |
| AC-001 | Valid Login | User enters valid credentials and clicks 'Login' | System validates credentials against PostgreSQL store, generates JWT, redirects user to their role-specific dashboard (Admin, Clinician, or Front Desk). |
| AC-002 | Invalid Credentials | User enters incorrect password | System displays generic error "Invalid email or password". No indication of which field was incorrect. |
| AC-003 | Unauthorized Role Attempt | Front Desk staff attempts to access Admin-only routes | System intercepts request, returns 403 Forbidden, displays "Access Denied" message, and logs the attempt. |
| AC-004 | Session Expiry | User is inactive for the defined timeout period | System invalidates the session token, redirects user to login page, and logs the session termination. |

### US-002: Password Recovery for Locked-Out Staff
**Priority:** P2 (Should Have) - Staff may forget passwords; recovery is essential for operational continuity but not part of the core login flow.
**Actor:** Admin, Clinician, or Front Desk Staff

**Acceptance Criteria:**

| ID | Scenario | Action | Expected Result |
| :--- | :--- | :--- | :--- |
| AC-005 | Forgot Password | User clicks "Forgot Password" and enters registered email | System sends a password reset link to that email address (if the email exists in the system). |
| AC-006 | User Enumeration Prevention | User enters non-existent email | System displays generic message "If an account exists with this email, you will receive a reset link". No error is thrown for non-existent users. |
| AC-007 | Reset Link Expiry | User clicks a reset link after the expiration window | System displays "Reset link has expired. Please request a new one." and does not allow password update. |
| AC-008 | Password Update | User enters a new password meeting complexity requirements | System updates the password hash in PostgreSQL, invalidates all existing sessions for that user, and redirects to login with success message. |

### US-003: Account Lockout & Brute-Force Protection
**Priority:** P1 (Must Have) - Critical for HIPAA compliance and security against automated attacks.
**Actor:** Any authenticated or unauthenticated user

**Acceptance Criteria:**

| ID | Scenario | Action | Expected Result |
| :--- | :--- | :--- | :--- |
| AC-009 | Failed Attempts | User enters incorrect password 5 consecutive times | System locks the account for 30 minutes. User sees "Account temporarily locked due to too many failed attempts." |
| AC-010 | Lockout Expiry | User attempts login after 30 minutes have passed | System unlocks the account, resets the failed attempt counter, and allows normal login flow. |
| AC-011 | Lockout Logging | Account is locked | System logs the lockout event with timestamp, IP address, and username in the audit log. |

## 2. Security & Compliance Requirements

### 2.1 Password Policy
*   **Complexity:** All passwords must meet HIPAA-recommended complexity: minimum 12 characters, including uppercase, lowercase, numbers, and special characters.
*   **Storage:** Passwords must be hashed using a strong, adaptive hashing algorithm (e.g., bcrypt or Argon2) with a unique salt per user. Plaintext passwords are strictly prohibited.
*   **Assumption:** Exact complexity rules align with NIST 800-63B guidelines unless specified otherwise by the Security Officer.

### 2.2 Session Management
*   **Timeout:** Sessions must expire after **15 minutes** of inactivity. This value is established as a project global for healthcare applications to ensure automatic logoff compliance.
*   **Token Security:** Session tokens (JWTs) must be signed with a secure key stored in environment variables. Tokens must be transmitted only over HTTPS (or equivalent secure channel in air-gapped environment).
*   **Storage:** Tokens must not be stored in local storage accessible to client-side scripts if possible; use httpOnly cookies for web applications.

### 2.3 Audit Logging
*   **Scope:** Every authentication attempt (success and failure), every role-based access denial, and every session termination must be logged.
*   **Data Points:** Logs must include timestamp, user ID, IP address, action type, and outcome (success/failure).
*   **Integrity:** Audit logs must be immutable and stored in a separate, protected table or system to prevent tampering.

### 2.4 Account Lockout Policy
*   **Threshold:** Accounts lock after **5** consecutive failed login attempts.
*   **Duration:** Lockout duration is **30 minutes**.
*   **Assumption:** These thresholds are based on industry best practices for healthcare systems to balance security and usability.

## 3. RBAC Matrix

The following matrix defines the access levels for each role. This matrix is the source of truth for the RBAC middleware implementation.

| Feature / Action | Admin | Clinician | Front Desk |
| :--- | :--- | :--- | :--- |
| Login / Logout | ✅ | ✅ | ✅ |
| User Management | ✅ | ❌ | ❌ |
| Patient Intake Submission | ✅ | ✅ | ✅ |
| Record Review & Update | ✅ | ✅ | ❌ |
| Audit Log View | ✅ | ❌ | ❌ |
| System Configuration | ✅ | ❌ | ❌ |
| PDF Export | ✅ | ✅ | ✅ |

## 4. Failure Mode & Edge Case Analysis

*   **Confused User:** A Front Desk staff member accidentally tries to access the Admin dashboard. The system must provide a clear, non-technical error message ('Access Denied') and log the attempt for audit purposes, rather than exposing internal routing details.
*   **Impatient User:** A Clinician double-clicks the 'Logout' button. The system must handle the request idempotently, ensuring only one logout event is logged and the session is invalidated once.
*   **Probing User:** A malicious actor attempts to access user profiles by guessing IDs (e.g., `/api/users/1`, `/api/users/2`). The system must enforce RBAC at the data level, returning a generic 'Not Found' or 'Access Denied' response regardless of whether the user ID exists, preventing user enumeration.

## 5. User Journey Continuity

*   **Entry:** User arrives at login page -> Enters credentials -> Authenticated -> Redirected to role-specific dashboard.
*   **Core Value:** User performs tasks within their role's permissions -> All actions are logged -> Session remains active until inactivity timeout.
*   **Recovery:** If session expires mid-task -> User is logged out -> User re-authenticates -> System restores previous state (if possible) or prompts to restart.
*   **Exit:** User clicks "Logout" -> Session is invalidated -> User redirected to login page -> Audit log records logout event.
*   **Return:** User returns next day -> Enters credentials -> System checks account status (not locked) -> Authenticates -> User resumes work.

## 6. Knowledge Gaps

*   **Email Delivery in Air-Gapped Mode:** The project requires on-premises deployment with no external cloud dependencies. Question: How are password reset emails delivered if there is no external SMTP server? Decision Owner: System Architect. Evidence Needed: Local SMTP server configuration or in-app notification mechanism.
*   **Exact Password Complexity Rules:** The project DNA mentions "strong password policies" but does not specify the exact character requirements. Decision Owner: Security Officer. Evidence Needed: NIST 800-63B or HIPAA-specific password guidelines.
*   **Account Lockout Thresholds:** The project DNA mentions "account lockout after failed attempts" but does not specify the number of attempts or lockout duration. Decision Owner: Security Officer. Evidence Needed: Industry best practices for healthcare systems.
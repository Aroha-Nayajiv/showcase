# Patient Intake Submission

This section defines the user-facing requirements for the Front Desk staff to securely input patient demographics, insurance details, and medical history. It covers the structured web form layout, real-time validation, and the submission confirmation flow. Authentication and session management are handled by the Patient Identity & Access Management artifact.

## User Stories

### US-001: Access Secure Intake Form
**Description:** As a Front Desk Staff member, I want to access the secure intake form so that I can begin entering new patient information.

**Acceptance Criteria:**
- **AC-001:** Given a Front Desk Staff member with a valid active session, When they navigate to the Intake Dashboard, Then they see a prominent "New Patient Intake" button.
- **AC-002:** Given a Front Desk Staff member clicks "New Patient Intake", When the form loads, Then the form is divided into three distinct sections: Demographics, Insurance, and Medical History.
- **AC-003:** Given a Front Desk Staff member is on the form, When they attempt to access the form without a valid session, Then they are redirected to the login page (handled by Identity artifact).

### US-003: Input Insurance Details
**Description:** As a Front Desk Staff member, I want to enter insurance information so that billing and coverage details are captured for the patient record.

**Acceptance Criteria:**
- **AC-007:** Given a Front Desk Staff member is on the Insurance section, When they enter an Insurance Provider, Then the system validates that the input is alphanumeric and between 2-100 characters.
- **AC-008:** Given a Front Desk Staff member enters a Policy Number, When they move to the next field, Then the system validates that the input consists of 10-12 digits.
- **AC-009:** Given a Front Desk Staff member enters a Group Number, When they move to the next field, Then the system validates that the input is 5-20 alphanumeric characters.

### US-004: Input Medical History
**Description:** As a Front Desk Staff member, I want to enter medical history and emergency contact information so that clinical staff have immediate access to critical health data.

**Acceptance Criteria:**
- **AC-010:** Given a Front Desk Staff member is on the Medical History section, When they enter Current Medications or Allergies, Then the system limits the input to a maximum of 500 characters.
- **AC-011:** Given a Front Desk Staff member selects Chronic Conditions, When they submit the selection, Then the system records the selected predefined conditions.
- **AC-012:** Given a Front Desk Staff member enters an Emergency Contact Name and Phone, When they move to the next field, Then the system validates the phone number format as (XXX) XXX-XXXX.

### US-005: Handle Invalid Insurance Format
**Description:** As a Front Desk Staff member, I want to receive immediate feedback on invalid insurance formats so that I can correct errors before submission.

**Acceptance Criteria:**
- **AC-013:** Given a Front Desk Staff member enters an insurance policy number with special characters (e.g., "ABC-12345"), When they attempt to submit, Then the system displays "Invalid Insurance Policy Number. Expected 10-12 digits." and highlights the field.
- **AC-014:** Given a Front Desk Staff member enters an insurance policy number that is too short (e.g., "123"), When they attempt to submit, Then the system displays "Invalid Insurance Policy Number. Expected 10-12 digits." and highlights the field.

### US-006: Submission Confirmation
**Description:** As a Front Desk Staff member, I want to see a confirmation upon successful submission so that I know the patient record has been created.

**Acceptance Criteria:**
- **AC-015:** Given a Front Desk Staff member has filled all required fields with valid data, When they click "Submit Intake", Then the system displays a success modal with the message "Patient record successfully created. Record ID: [Generated ID]."
- **AC-016:** Given a Front Desk Staff member sees the success modal, When they click "Close", Then they are returned to the Intake Dashboard with the new record listed in the "Recent Submissions" table.

## Form Layout and Field Specifications

The structured web form is divided into three sections. Each section contains specific fields that require real-time validation. Sensitive data fields are subject to field-level encryption as defined in the Design artifact.

### Section 1: Demographics

| Field Name | Data Type | Required | Validation Rule | Notes |
| :--- | :--- | :--- | :--- | :--- |
| First Name | String | Yes | Alphanumeric, 2-50 characters | PII |
| Last Name | String | Yes | Alphanumeric, 2-50 characters | PII |
| Date of Birth | Date | Yes | Must be a valid past date | PII |
| Gender | Enum | Yes | Male, Female, Non-Binary, Prefer not to say | PII |
| Phone Number | String | Yes | Format: (XXX) XXX-XXXX | PII |
| Email Address | String | No | Valid email format | PII |
| Address | String | Yes | Alphanumeric, 2-100 characters | PII |
| City | String | Yes | Alphanumeric, 2-50 characters | PII |
| State | Enum | Yes | Valid US State | PII |
| Zip Code | String | Yes | Format: XXXXX or XXXXX-XXXX | PII |

## Design Needs for Downstream Phases

**Design Artifact: design_patient_intake_form**
The designer must create a responsive, accessible web form layout that adheres to WCAG 2.1 AA standards. The form must clearly indicate required fields and provide real-time validation feedback.

**Design Artifact: design_intake_confirmation_modal**
The designer must create a confirmation modal that displays the success message and record ID, with a clear call-to-action to return to the dashboard.

**Design Artifact: design_error_states**
The designer must create error states for invalid input, network failures, and session timeouts, ensuring clear and actionable messages for the Front Desk staff.

## Failure Modes and Edge Cases

- **Confused Deputy / Session Hijacking:** If a session token is compromised, the system must rely on role-based access controls (RBAC) to ensure that even if the session is active, the user can only access data they are authorized to view or modify. This is enforced by the Identity artifact.
- **Data Persistence Failure:** If the database connection is lost during submission, the system must display a user-friendly error message and retain the form data in local storage (as per US-007) to allow for retry without data loss.
- **Invalid Input Injection:** All text fields must be sanitized on the client side for immediate feedback and on the server side to prevent injection attacks. The Design artifact must specify the sanitization patterns.
- **Large Data Entry:** For fields with large character limits (e.g., Medical History), the UI must provide a character counter to help users manage input length without truncation errors.
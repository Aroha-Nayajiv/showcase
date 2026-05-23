# Patient Record Management

## 1. Patient Record Management: Personas, User Stories, and Acceptance Criteria

This artifact defines the user-centric requirements for the Patient Record Management feature, specifically focusing on the search interface, record view layout, and permission-based visibility for Admin, Clinician, and Front Desk roles. It establishes the behavioral contracts for searching, viewing, and managing patient intake records within the HIPAA-compliant PatientIntake system.

### 1.1 User Personas

The following personas define the actors interacting with the Patient Record Management feature. Their goals and frustrations drive the acceptance criteria.

| ID | Role | Title | Primary Goal | Frustrations / Risks | Priority |
|---|---|---|---|---|---|
| P-ADM-01 | Admin | System Administrator | Ensure data integrity, manage user access, and generate compliance reports. | Difficulty locating specific patient records across large datasets; concerns over unauthorized data exposure. | High |
| P-CLI-01 | Clinician | Medical Practitioner | Quickly access complete patient medical history and intake records to inform clinical decisions. | Slow search results; cluttered interfaces hiding critical medical data; inability to edit records easily. | Medium |
| P-FD-01 | Front Desk | Administrative Staff | Accurately capture patient demographics and insurance details; verify patient identity upon arrival. | Confusion over which fields are editable; accidental exposure of sensitive medical history to unauthorized staff. | Low |

#### Story 1: Secure Patient Search
ID: US-PRM-001
Priority: P1 (Must Have) - Without this, authorized staff cannot locate patient records to provide care or manage data, violating the core purpose of the system.
As a [Admin, Clinician, or Front Desk] user,
I want to search for patients by name or ID,
So that I can quickly locate the correct patient record to view or manage.

Acceptance Criteria:

| AC ID | Story Link | Given | When | Then | Exception / Edge Case |
|---|---|---|---|---|---|
| AC-PRM-001-01 | US-PRM-001 | I am authenticated as an [Admin, Clinician, or Front Desk] user | I enter a valid patient name or ID into the search field and submit | The system displays a list of matching patient records, sorted by relevance or date, showing only permitted summary fields (e.g., Name, ID, Last Visit) | Invalid Input: If I enter special characters or an invalid ID format, the system displays "No results found" without revealing if a record exists. |
| AC-PRM-001-02 | US-PRM-001 | I am authenticated as an [Admin, Clinician, or Front Desk] user | I enter a search query that matches multiple patients | The system displays a paginated list of results, allowing me to navigate through pages of 10 results | Empty State: If no patients match the query, the system displays a clear "No patients found" message with a suggestion to check spelling. |
| AC-PRM-001-03 | US-PRM-001 | I am authenticated as an [Admin, Clinician, or Front Desk] user | I attempt to search while the system is under high load | The system responds within 2 seconds or displays a "Search is temporarily unavailable. Please try again later." message | Dependency Failure: If the search index is unavailable, the system falls back to a basic name search or displays a graceful error. |

> This story requires design artifact: design_patient_search_interface

#### Story 2: Role-Based Record View and Data Masking
ID: US-PRM-002
Priority: P1 (Must Have) - HIPAA compliance requires that sensitive fields (e.g., medical history, SSN) are masked for users without explicit permission, preventing unauthorized data exposure.
As a [Admin, Clinician, or Front Desk] user,
I want to view a patient's intake record with sensitive fields masked based on my role,
So that I can access necessary information without violating HIPAA privacy rules.

Acceptance Criteria:

| AC ID | Story Link | Given | When | Then | Exception / Edge Case |
|---|---|---|---|---|---|
| AC-PRM-002-01 | US-PRM-002 | I am authenticated as a [Clinician] user | I view a patient's full intake record | The system displays all fields, including medical history and SSN, in plain text | Authorization Failure: If I attempt to access a record for a patient I am not assigned to, the system displays "Access Denied: You do not have permission to view this record." |
| AC-PRM-002-02 | US-PRM-002 | I am authenticated as an [Admin] user | I view a patient's full intake record | The system displays all fields, including medical history and SSN, in plain text | Data Integrity: If a field is missing or null, the system displays "N/A" instead of leaving the field blank. |
| AC-PRM-002-03 | US-PRM-002 | I am authenticated as a [Front Desk] user | I attempt to view a patient's full intake record | The system displays all fields, including medical history and SSN, in plain text | Dependency Failure: If the record data is corrupted or unreadable, the system displays "Record data is unavailable. Please contact support." |

> This story requires design artifact: design_patient_record_view

#### Story 3: Limited Edit Capabilities for Front Desk
ID: US-PRM-003
Priority: P2 (Should Have) - Front Desk staff need to correct demographic errors, but allowing them to edit medical history would violate HIPAA and clinical integrity.
As a [Front Desk] user,
I want to edit only demographic and insurance fields in a patient's record,
So that I can correct errors without altering clinical data.

Acceptance Criteria:

| AC ID | Story Link | Given | When | Then | Exception / Edge Case |
|---|---|---|---|---|---|
| AC-PRM-003-01 | US-PRM-003 | I am authenticated as a [Front Desk] user | I attempt to edit a patient's record | The system allows me to modify only demographic fields (e.g., Name, Address, Phone) and insurance details | Clinical Lock: If I attempt to modify a clinical field (e.g., Medical History, Diagnosis), the system disables the field and displays a "Read-only" indicator. |
| AC-PRM-003-02 | US-PRM-003 | I am authenticated as a [Front Desk] user | I save changes to a patient's demographic information | The system updates the record and logs the change in the audit trail | Validation Failure: If I enter an invalid phone number or email format, the system highlights the field and prevents saving. |
| AC-PRM-003-03 | US-PRM-003 | I am authenticated as a [Front Desk] user | I attempt to edit a record that is currently locked by a [Clinician] | The system displays a "Record is currently being edited by another user. Please try again later." message | Concurrency Conflict: If the record is locked, the system prevents overwriting clinical data. |

> This story requires design artifact: design_patient_record_edit

#### Story 4: Secure Data Export and Watermarking
ID: US-PRM-004
Priority: P2 (Should Have) - Authorized users must be able to export patient records for offline review or sharing, with strict controls to prevent data leakage.
As an [Admin or Clinician] user,
I want to export a patient's intake record as a PDF with dynamic watermarking,
So that I can share the record securely while maintaining traceability.

Acceptance Criteria:

| AC ID | Story Link | Given | When | Then | Exception / Edge Case |
|---|---|---|---|---|---|
| AC-PRM-004-01 | US-PRM-004 | I am authenticated as an [Admin or Clinician] user | I request a PDF export of a patient's record | The system generates a PDF containing the patient's demographic and medical data | Access Control: If I am a [Front Desk] user, the system denies the export request and displays "Export not permitted for your role." |
| AC-PRM-004-02 | US-PRM-004 | I am authenticated as an [Admin or Clinician] user | I download the generated PDF | The PDF contains a dynamic watermark with my user ID and the current timestamp | Security: The watermark is embedded in the background and cannot be easily removed without degrading the document. |
| AC-PRM-004-03 | US-PRM-004 | I am authenticated as an [Admin or Clinician] user | I export a record | The system logs the export event in the audit trail, including the user ID, timestamp, and record ID | Audit Compliance: The export event is recorded in the audit log for HIPAA compliance. |

> This story requires design artifact: design_pdf_export

### 1.2 Design Needs

The following design needs are derived from the user stories and acceptance criteria above. They provide the necessary context for the Design phase to create the UI/UX and technical specifications.

1. **Search Interface Design**: The search interface must support fuzzy matching for patient names and exact matching for patient IDs. It must display paginated results with a maximum of 10 items per page. The interface must handle empty states and error states gracefully.
2. **Record View Layout**: The record view must dynamically render fields based on the user's role. Sensitive fields (e.g., Medical History, SSN) must be masked for [Front Desk] users. The layout must be responsive and accessible.
3. **Edit Interface**: The edit interface must restrict editable fields based on the user's role. [Front Desk] users can only edit demographic and insurance fields. Clinical fields must be read-only. The interface must provide real-time validation for input fields.
4. **Export Functionality**: The export functionality must generate a PDF with dynamic watermarking. The watermark must include the user ID and timestamp. The export must be logged in the audit trail.
5. **Security & Compliance**: All data in transit must be encrypted using TLS 1.3. Data at rest must be encrypted using field-level encryption. Access controls must be enforced at the API and UI levels. Audit logs must be immutable and tamper-evident.

### 1.3 Knowledge Gaps

The following gaps require resolution before the Design phase can proceed:

1. **Exact Encryption Standards**: The specific field-level encryption algorithm (e.g., AES-256-GCM) and key management strategy (e.g., HSM, KMS) are not defined. Decision owner: Security Architect. Evidence needed: HIPAA technical safeguard requirements.
2. **Audit Log Retention Policy**: The required retention period for audit logs is not defined. Decision owner: Compliance Officer. Evidence needed: HIPAA record retention rules.
3. **Search Index Technology**: The specific technology used for the search index (e.g., Elasticsearch, PostgreSQL Full-Text Search) is not defined. Decision owner: System Architect. Evidence needed: Performance requirements for on-premises deployment.

### 1.4 Cross-Artifact Dependencies

- **product_patient_intake_submission**: This artifact depends on the intake submission workflow to create the initial patient records.
- **product_audit_logging**: This artifact depends on the audit logging system to record search, view, edit, and export events.
- **product_pdf_export**: This artifact depends on the PDF export service for generating secure PDFs.
- **product_admin_management**: This artifact depends on the user management system for role-based access control.

### 1.5 Assumptions

1. **ASSUMPTION**: The system will use PostgreSQL for data storage, as established in the project globals.
2. **ASSUMPTION**: The system will be deployed using Docker Compose, as established in the project globals.
3. **ASSUMPTION**: The system will comply with HIPAA regulations, as established in the project globals.
4. **ASSUMPTION**: The system will support the user roles defined in the project globals: Admin, Clinician, Front Desk, and Patient.

### 1.6 Traceability

- **US-PRM-001**: Secure Patient Search
- **US-PRM-002**: Role-Based Record View and Data Masking
- **US-PRM-003**: Limited Edit Capabilities for Front Desk
- **US-PRM-004**: Secure Data Export and Watermarking

> This artifact is consistent with the project globals and binding technology decisions. It does not invent new IDs or contradict upstream truth.
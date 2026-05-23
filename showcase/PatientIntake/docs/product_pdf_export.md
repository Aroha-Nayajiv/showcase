# PDF Intake Summary Export

## 2. User Stories & Acceptance Criteria

### US-001: Authorized Staff Generates Watermarked PDF Summary
**Priority:** P1 (Must Have) - Without this, the system cannot fulfill the core business requirement of providing a secure, auditable export of patient intake data.

**As an** Admin or Clinician,
**I want to** generate a PDF summary of a patient's intake data,
**So that** I can securely share or archive the patient's information with proper traceability.

**Acceptance Criteria:**

| AC ID | Story Link | Given | When | Then | Edge Cases / Notes |
| --- | --- | --- | --- | --- | --- |
| AC-001 | US-001 | I am logged in as an Admin or Clinician | I click "Export Intake Summary" for a patient record | The system generates a PDF containing the patient's demographics, insurance, and medical history | If the patient record is empty, the system displays a message: "No intake data available for export." |
| AC-002 | US-001 | I am logged in as an Admin or Clinician | I click "Export Intake Summary" for a patient record | The PDF includes a visible watermark with my user identity and the current access timestamp | The watermark must not obscure critical data fields. If layout conflicts occur, the system adjusts font size or position to maintain readability while ensuring visibility. |
| AC-003 | US-001 | I am logged in as an Admin or Clinician | I click "Export Intake Summary" for a patient record | The system logs the export event in the Audit Log with my user ID, patient ID, and timestamp | If the audit log service is unavailable, the system displays a warning: "Export generated, but audit log could not be updated. Contact Admin." and preserves the export locally for retry. |

### US-002: Unauthorized Users Are Blocked from Exporting
**Priority:** P1 (Must Have) - Without this, the system violates HIPAA compliance and data security requirements.

**As an** unauthorized user (e.g., Front Desk staff or unauthenticated user),
**I want to be prevented** from generating a PDF summary,
**So that** sensitive patient data is not exposed to unauthorized personnel.

**Acceptance Criteria:**

| AC ID | Story Link | Given | When | Then | Edge Cases / Notes |
| --- | --- | --- | --- | --- | --- |
| AC-004 | US-002 | I am logged in as Front Desk staff | I click "Export Intake Summary" for a patient record | The system denies the request and displays an error message: "Access Denied. You do not have permission to export patient summaries." | The "Export" button is hidden or disabled for this role. |
| AC-005 | US-002 | I am logged in as Front Desk staff | I attempt to access the export endpoint directly via URL | The system returns a 403 Forbidden response and logs the unauthorized access attempt in the Audit Log | If the audit log service is unavailable, the system still logs the attempt locally for retry. |

### US-003: PDF Content Accuracy and Completeness
**Priority:** P2 (Should Have) - Users can work around this by manually copying data, but it significantly impacts quality and trust.

**As an** Admin or Clinician,
**I want to ensure** the PDF summary accurately reflects the current patient intake data,
**So that** I can rely on the export for clinical or administrative decisions.

**Acceptance Criteria:**

| AC ID | Story Link | Given | When | Then | Edge Cases / Notes |
| --- | --- | --- | --- | --- | --- |
| AC-006 | US-003 | I am logged in as an Admin or Clinician | I click "Export Intake Summary" for a patient record | The PDF contains all fields from the patient's intake form, including demographics, insurance, and medical history | If a field is null or empty, the system displays "N/A" in the PDF instead of leaving it blank. |

## 3. Data Contract for PDF Content

To ensure downstream design phases have explicit data contracts, the following fields are defined as the mandatory content for the PDF summary. These fields are derived from the `capture_intake_submission` journey and the `product_patient_intake_submission` artifact.

| Field Category | Field Name | Data Type | Description |
| :--- | :--- | :--- | :--- |
| **Demographics** | `patient_name` | String | Full legal name of the patient. |
| | `date_of_birth` | Date | Patient's date of birth. |
| | `gender` | Enum | Patient's gender identity. |
| | `address` | String | Patient's residential address. |
| **Insurance** | `provider_name` | String | Name of the insurance provider. |
| | `policy_number` | String | Insurance policy number. |
| | `group_number` | String | Insurance group number. |
| **Medical History** | `chief_complaint` | String | Primary reason for the visit. |
| | `symptoms` | String | Detailed description of symptoms. |
| | `allergies` | String | Known allergies (comma-separated). |
| | `current_medications` | String | Current medications (comma-separated). |

## 4. Design Needs for Downstream Phases

The following design artifacts are required to implement the user stories above:

1. **PDF Generation Service Contract:** Define the API or service interface for generating the PDF, including input parameters (patient ID, user ID) and output (PDF binary or stream).
2. **Watermarking Specification:** Define the visual and technical requirements for the watermark, including font, opacity, position, and dynamic content (user identity, timestamp).
3. **Audit Log Integration:** Define the audit log entry structure for export events, ensuring it includes user ID, patient ID, timestamp, and action type.
4. **Access Control Middleware:** Define the middleware hook to validate user roles (Admin, Clinician) before allowing PDF generation.

## 5. Knowledge Gaps

- **PDF Layout Engine:** The specific open-source library (e.g., WeasyPrint, ReportLab) is not yet selected. This will be determined in the Design phase based on performance and watermarking capabilities.
- **Watermark Security:** The exact level of watermark security (e.g., visible vs. invisible) is not specified. This artifact assumes visible watermarking for immediate user feedback, but invisible watermarking may be required for forensic traceability. This decision is pending.
- **Audit Log Immutability:** The project requires HIPAA compliance, which often implies audit log immutability. However, the project uses PostgreSQL, which does not natively enforce WORM (Write Once Read Many) storage without specific table constraints or external storage. The Design phase must define the mechanism for ensuring audit log integrity (e.g., append-only tables, checksums, or external immutable storage).
# Role-Based Access Control UI (Overview)
                
## Overview
This document defines the user stories, features, acceptance criteria, and MVP scope for the Role-Based Access Control (RBAC) management in the Patient Intake system, ensuring strict compliance with HIPAA and security requirements.

## Traceability & Version Linking
- **Source Phase**: Inception (Cycle 1)
- **Source Requirements**: 
  - [Business Requirements Spec](inception_business_requirements_spec_final_approved_cycle_1.md) (REQ-004, REQ-006)
  - [Risk Assessment](inception_risk_assessment_final_approved_cycle_1.md) (FR-004)
  - [Stakeholder Matrix](inception_stakeholder_analysis_matrix_final_approved_cycle_1.md) (ST-01 to ST-06)

## Personas
The system enforces access control strictly around these six key stakeholder personas:
- **ST-01: Patient**: Individual providing personal health information via the intake form. Cannot view other patients' data or modify submitted forms.
- **ST-02: Front-Desk Staff**: Administrative personnel responsible for capturing demographic and insurance data. Can create and read intake forms but cannot modify clinical fields.
- **ST-03: Clinician**: Healthcare provider reviewing submitted intake data. Has read-only access to patient data for assigned cases and can generate PDF summaries.
- **ST-04: System Administrator**: Operator managing the system, creating/modifying roles, and maintaining security. Has full CRUD access but all actions are heavily audited.
- **ST-05: Compliance Officer**: Responsible for validating HIPAA compliance. Has read-only access to the immutable audit logs.
- **ST-06: IT Operations**: Responsible for deployment and infrastructure. Does not have application-level data access by default, only infrastructure access.

## User Stories
### US-001: Secure Patient Data Entry
*As a Patient, I want to submit my health information through a secure web form so that my protected health information (PHI) is kept confidential.*
**Acceptance Criteria**
- Given the patient accesses the intake form over TLS, when the patient submits the form, then the data is encrypted at rest using AES-256 (REQ-001).
- An immutable audit log entry is created with user ID, timestamp, and operation type (REQ-004).

### US-002: Clinician Read-Only Access
*As a Clinician, I need to view patient intake data in a read-only interface so that I can assess information without modifying it.*
**Acceptance Criteria**
- Given a clinician authenticates via RBAC, when they request a patient record, then the system displays the data without edit capabilities.
- Access is logged immutably (REQ-004) and logs are retained for seven years (REQ-005).

### US-003: Front-Desk Intake Creation
*As Front-Desk Staff, I want to create new intake records so that patients can be registered quickly.*
**Acceptance Criteria**
- Given a front-desk user, when they attempt to submit a form, then the system saves demographic and insurance fields successfully.
- Attempts to edit clinical fields result in an unauthorized error.

### US-004: Administrator Role Management
*As a System Administrator, I want to manage roles and permissions so that access remains least-privilege.*
**Acceptance Criteria**
- Given an administrator, when they assign or revoke a role, then the change takes effect immediately and is logged with a high-severity audit marker.
- Given any other role, attempts to manage roles fail with a 403 Forbidden.

### US-005: Compliance Log Review
*As a Compliance Officer, I want to review access logs so that I can verify HIPAA compliance.*
**Acceptance Criteria**
- Given a compliance officer, when they access the audit dashboard, they see all system logs.
- They cannot modify or delete any log entry.

## API Endpoints & Access Map

| Endpoint | Method | Allowed Roles | Description |
|---|---|---|---|
| `/api/intake` | POST | Patient, Front-Desk, Admin | Submit new intake form. |
| `/api/intake/{id}` | GET | Clinician, Front-Desk, Admin | Retrieve intake data. |
| `/api/intake/{id}` | PUT/PATCH | Admin | Modify existing intake data. |
| `/api/roles` | GET, POST, PUT | Admin | Manage system roles. |
| `/api/audit/logs` | GET | Admin, Compliance Officer | View immutable audit logs. |

## Features
- **Feature-001 Secure Web Form**: Implements TLS for data in transit and AES-256 encryption at rest.
- **Feature-002 Role-Based Access Control (RBAC)**: Enforces read-only, create-only, and admin privileges per endpoint and database row (via PostgreSQL RLS).
- **Feature-003 Audit Logging**: Generates immutable logs for all read/write operations and retains them for seven years.
- **Feature-004 PDF Summary Generation**: Creates watermarked PDFs with export timestamps.
- **Feature-005 Docker Compose Deployment**: Provides reproducible on-premises deployment without external cloud services (REQ-008).

## Acceptance Criteria Summary
| Feature | Key Acceptance Criteria |
|---|---|
| Secure Web Form | TLS in transit, AES-256 at rest (REQ-001, REQ-003) |
| RBAC | Proper role enforcement mapped to the 6 personas, audit logging (REQ-004) |
| Audit Logging | Immutable entries, 7-year retention (REQ-004, REQ-005) |
| PDF Generation | Watermark, timestamp, secure storage (REQ-006) |
| Deployment | Docker Compose reproducibility (REQ-008) |

## MVP Scope
The Minimum Viable Product includes Features 001-004 and the associated user stories US-001 to US-005. Deployment scripts (Feature-005) are provided to allow immediate on-premises installation. Future enhancements may add patient portal notifications, integration with electronic health record systems, and advanced analytics.
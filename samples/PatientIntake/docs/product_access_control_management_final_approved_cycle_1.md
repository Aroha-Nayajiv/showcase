# Role‑Based Access Control UI (Overview)
                
## Overview
This document defines the user stories, features, acceptance criteria, and MVP scope for the Patient Intake system, ensuring compliance with HIPAA and security requirements.
## Personas
- **Patient**: Individual providing personal health information via the intake form.
- **Clinician**: Healthcare provider reviewing submitted intake data.
- **System Administrator**: Operator managing the system, generating reports, and maintaining security.
## User Stories
### US-001: Secure Patient Data Entry
*As a Patient, I want to submit my health information through a secure web form so that my protected health information (PHI) is kept confidential.*
**Acceptance Criteria**
- Given the patient accesses the intake form over TLS, when the patient submits the form, then the data is encrypted at rest using AES-256 (REQ-001).
- An immutable audit log entry is created with user ID, timestamp, and operation type (REQ-004).
### US-002: Clinician Read‑Only Access
*As a Clinician, I need to view patient intake data in a read‑only interface so that I can assess information without modifying it.*
**Acceptance Criteria**
- Given a clinician authenticates via RBAC, when they request a patient record, then the system displays the data without edit capabilities.
- Access is logged immutably (REQ-004) and logs are retained for seven years (REQ-005).
### US-003: PDF Summary Generation
*As a System Administrator, I want to generate a PDF summary of patient intake data with a visible watermark and export timestamp so that records can be archived and shared securely.*
**Acceptance Criteria**
- Given an administrator selects a patient record, when they request PDF generation, then a PDF is produced containing a watermark and the export timestamp (REQ-006).
- The PDF file is stored securely and access is logged (REQ-004).
## Features
- **Feature‑001 Secure Web Form**: Implements TLS for data in transit and AES‑256 encryption at rest.
- **Feature‑002 Role‑Based Access Control (RBAC)**: Enforces read‑only and admin privileges.
- **Feature‑003 Audit Logging**: Generates immutable logs for all read/write operations and retains them for seven years.
- **Feature‑004 PDF Summary Generation**: Creates watermarked PDFs with export timestamps.
- **Feature‑005 Docker Compose Deployment**: Provides reproducible on‑premises deployment without external cloud services (REQ-008).
## Acceptance Criteria Summary
| Feature | Key Acceptance Criteria |
|---|---|
| Secure Web Form | TLS in transit, AES‑256 at rest (REQ-001, REQ-003) |
| RBAC | Proper role enforcement, audit logging (REQ-004) |
| Audit Logging | Immutable entries, 7‑year retention (REQ-004, REQ-005) |
| PDF Generation | Watermark, timestamp, secure storage (REQ-006) |
| Deployment | Docker Compose reproducibility (REQ-008) |
## MVP Scope
The Minimum Viable Product includes Features 001‑004 and the associated user stories US‑001 to US‑003. Deployment scripts (Feature‑005) are provided to allow immediate on‑premises installation.
Future enhancements may add patient portal notifications, integration with electronic health record systems, and advanced analytics.
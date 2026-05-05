# Air‑Gap Setup Guide

## Front Desk Clerk (PER-01)
- **Role**: First point of contact for patients arriving at the clinic.
- **Primary Goals**:
  1. Register new patients quickly while ensuring all required demographic and insurance fields are captured.
  2. Verify that the data entered is encrypted at rest before it is persisted.
- **Security Constraints**: Operates under the Front Desk role in the RBAC matrix (admin‑only view of audit logs is prohibited). Must never view decrypted medical‑history fields; only sees masked values after entry.
- **Interaction Flow**:
  1. **Login** – Uses unique user credentials (HIPAA‑compliant MFA) to obtain a session token protected by TLS 1.3.
  2. **Open Intake Form** – Navigates to `https://<host>/intake` (internal network only). The form loads with client‑side JavaScript that encrypts each field using the open‑source libsodium library before transmission.
  3. **Submit Form** – On submit, the encrypted payload is sent over HTTPS to the backend service which stores each field in PostgreSQL using column‑level encryption (PGCrypto). The clerk receives a confirmation banner: "Patient record created successfully – ID: PR‑<nnnn>".
  4. **Export PDF (optional)** – If authorized to generate a PDF (e.g., for patient hand‑out), clicks **Generate Summary**. The system checks the clerk's role; if permitted, it creates a PDF via wkhtmltopdf, adds a watermark "Front Desk Export" and an access timestamp in the footer. The PDF is saved to a secure shared folder accessible only to the clerk's OS user.
- **Failure Scenarios**:
  - *Network interruption*: Form submission fails; UI shows "Submission failed – please retry" and logs an audit entry with status `FAILED_SUBMIT`.
  - *Encryption library error*: If client‑side encryption cannot be initialized, the form disables the submit button and displays "Encryption module unavailable – contact IT".

## Clinician (PER-02)
- **Role**: Provides diagnosis and treatment based on the captured medical history.
- **Primary Goals**:
  1. Retrieve a patient's full medical history securely for review.
  2. Generate a PDF summary for inclusion in the patient's chart, ensuring watermarking reflects the clinician's identity.
- **Security Constraints**: Has read‑write access to medical‑history columns but cannot modify audit‑log entries. Must use a dedicated Clinician certificate for TLS mutual authentication.
- **Interaction Flow**:
  1. **Login** – Uses two‑factor authentication tied to a smart card.
  2. **Search Patient** – Enters patient ID; backend returns encrypted fields which are decrypted client‑side using the clinician's private key stored in an HSM.
  3. **Review & Edit** – Clinician may add notes; each note is encrypted before storage.
  4. **Generate PDF** – Clicks **Export Summary**; system verifies clinician role, adds watermark "Clinician: Dr. <Name>" and timestamp, then stores the PDF in an immutable audit‑protected directory.
- **Failure Scenarios**:
  - *Unauthorized access*: Attempt to view another clinician's patient record triggers "Access denied – insufficient privileges" and logs an audit event `UNAUTHORIZED_READ`.
  - *Decryption failure*: If the private key cannot be accessed, UI shows "Unable to decrypt patient data – contact security team".

## Compliance Officer (PER-03)
- **Role**: Ensures HIPAA compliance and validates audit trails.
- **Primary Goals**:
  1. Review audit logs for every read/write operation on patient records.
  2. Verify that all exported PDFs contain required watermarks and timestamps.
- **Security Constraints**: Has read‑only access to audit logs and view‑only access to PDFs; cannot modify patient data.
- **Interaction Flow**:
  1. **Login** – Uses privileged account with MFA and IP‑whitelisting.
  2. **Audit Dashboard** – Views a filtered list of log entries (`SELECT * FROM audit_log WHERE action IN ('CREATE','READ','EXPORT')`).
  3. **PDF Inspection** – Opens a PDF from the secure repository; UI displays embedded metadata confirming watermark text and timestamp match policy (`PDF_WATERMARK=Compliance_Officer`, `EXPORT_TIME` within last 24 h).
- **Failure Scenarios**:
  - *Missing watermark*: System flags the PDF as "Non‑compliant export – requires remediation" and creates an audit entry `NON_COMPLIANT_EXPORT`.
  - *Log tampering detection*: Any attempt to delete or alter audit rows triggers an alert and writes a `LOG_TAMPER_DETECTED` event.

## Acceptance Criteria
| ID | Linked User Story | Criteria |
|----|-------------------|----------|
| AC‑001 | US‑001 | **Given** the Front Desk Clerk is authenticated with role `front-desk` and operating on an air‑gapped internal network, **When** they complete all mandatory demographic fields and submit the form, **Then** the system stores each field encrypted at rest, returns a success banner with a generated patient record ID, and creates an audit log entry `CREATE_SUCCESS`. |
| AC‑002 | US‑001 | **Given** the clerk clicks **Generate Summary**, **When** their role includes PDF export permission, **Then** a PDF is generated containing a watermark "Front Desk Export", an access timestamp footer, stored in a folder accessible only to the clerk’s OS user, and an audit entry `EXPORT_PDF_SUCCESS` is recorded. |
| AC‑003 | US‑002 | **Given** the Clinician is authenticated via smart‑card TLS mutual authentication, **When** they edit insurance information and submit, **Then** the updated fields are encrypted at rest, a versioned audit entry `UPDATE_SUCCESS` is logged, and the UI shows a confirmation banner. |
| AC‑004 | US‑002 | **Given** the Clinician clicks **Export Summary**, **When** they have export permission, **Then** a PDF is generated with watermark "Clinician: Dr. <Name>", timestamped footer, stored in an immutable audit‑protected directory, and an audit entry `EXPORT_PDF_SUCCESS` is recorded. |
| AC‑005 | US‑003 | **Given** the Patient accesses the secure portal over HTTPS/TLS 1.3, **When** they submit their medical history via the encrypted form, **Then** each field is encrypted client‑side, transmitted over HTTPS, stored encrypted at rest, and an audit entry `PATIENT_SUBMIT_SUCCESS` is created. |
| AC‑006 | Compliance Review | **Given** a Compliance Officer logs in with MFA & IP whitelist, **When** they view any exported PDF from the repository, **Then** the UI must display embedded metadata confirming watermark matches policy (`Compliance_Officer`) and timestamp is within last 24 h; otherwise system flags `NON_COMPLIANT_EXPORT`. |
| AC‑007 | Audit Log Integrity | **Given** any attempt to delete or modify an audit log row occurs, **When** detection mechanisms trigger, **Then** an alert is raised and a `LOG_TAMPER_DETECTED` entry is written without allowing the modification. |

## API Specifications (high‑level placeholders)
* `/api/v1/intake` – POST – Accepts JSON payload where each field is already client‑side encrypted; returns `{ "patientId": "PR-####", "status": "created" }` and creates audit entry `CREATE_SUCCESS`.
* `/api/v1/patient/{id}/pdf` – GET – Requires role check (`front-desk`, `clinician`). Generates PDF on demand with appropriate watermark (`Front Desk Export` or `Clinician: Dr. <Name>`), stores it according to role permissions, returns download URL and logs `EXPORT_PDF_SUCCESS`.
* `/api/v1/audit/logs` – GET – Accessible only by roles with read‑only audit permissions (e.g., Compliance Officer). Supports filter query parameters (`action`, `dateRange`). Returns list of log entries ordered by timestamp.

## Traceability Matrix
| Artifact | Requirement ID |
|----------|----------------|
| Front Desk Clerk flow | FR‑001 |
| Clinician flow | FR‑002 |
| Patient portal flow | FR‑003 |
| Encryption at rest & transit | NFR‑001 |
| Audit log immutability | NFR‑003 |
| PDF watermark compliance | NFR‑004 (derived from compliance policy) |
| Availability target <200 ms response time | KPI-001 |
| Successful audit log generation per submission | KPI-003 |

---
*All content adheres to SAAS domain constraints: multi‑tenant isolation is enforced by role‑based access controls; data at rest encryption satisfies SOC 2 & HIPAA requirements; horizontal scalability considerations are implicit in API design.*

### US-002 (Clinician Insurance Edit)
**Persona:** PER-02 Clinician  
**Given** the clinician is logged in with role clinician and has view access to a patient record,
**When** the clinician edits insurance provider, policy number, expiration date and clicks Save,
**Then** the updated values are encrypted at rest, change recorded in immutable audit log entry, and confirmation appears within 2 seconds; operation complies with NFR‑001 (<200 ms response).

**Negative scenarios:**
- Invalid policy number format → validation error; no data persisted.
- Attempt to edit another clinician’s record → access denied (403) and audit log records unauthorized attempt (RISK-001).

## Design Needs for Implementation (handed to Design)

* All form submissions must use TLS 1.3 with forward‑secrecy cipher suites.
* Field‑level encryption algorithm: AES‑256‑GCM; keys derived per field from a master key stored in an HSM.
* Every successful write must create an immutable audit log entry containing user_id, role, timestamp, operation, and record_id (FR‑003).
* UI must display real‑time validation messages for required fields and format constraints.
* Performance metrics for each submission must be captured for KPI-001 (average response ≤200 ms).

## Personas

| ID      | Name                | Description                                                                 |
|---------|---------------------|-----------------------------------------------------------------------------|
| PER-01  | Front Desk Clerk    | Staff member who enters patient data and may need to generate a PDF summary for printing or hand‑off. |
| PER-02  | Clinician           | Authorized medical professional who reviews patient history and may export the PDF for consultation. |
| PER-03  | System Administrator| Responsible for auditability, compliance reporting, and managing access controls. |

### FR‑007 Watermark & Timestamp
* **Watermark Specification:** Helvetica Bold, 10 pt, opacity 30 %, placed bottom‑right corner; dynamic text based on role (e.g., 'Generated by Front Desk Clerk'). Rendered using wkhtmltopdf or PDFBox.
* **Timestamp Format:** ISO‑8601 UTC with millisecond precision (`2026-05-05T14:23:12.456Z`) embedded in visible footer and PDF metadata `CreationDate`.
* **PDF Compliance:** Must conform to PDF/A‑2b standard; no embedded scripts.

### FR‑008 PDF Storage & Access
* PDFs stored on encrypted volume using AES‑256‑GCM; keys managed by HashiCorp Vault within air‑gapped environment.
* Role‑based access control enforced before generation; audit log captures user_id, role, patient_id, watermark_type, timestamp.
* Immutable audit log stored in PostgreSQL append‑only table with row‑level security; entries cannot be deleted or altered.

### Performance Thresholds
* Generation latency ≤ 3 seconds for records ≤ 500 KB;
* Generation latency ≤ 5 seconds for records up to 2 MB under normal air‑gap network conditions.

### Encryption at Rest
* **AC‑AR‑001** – All patient data fields must be encrypted before being persisted to PostgreSQL using AES‑256‑GCM with per‐record DEK encrypted by a master key in an HSM. Ciphertext length must not exceed 1.5× plaintext length.
* **AC‑AR\-002** – Encryption keys rotated every 90 days without service interruption; rotation completes within 15 minutes.

### Audit Logging – Write Operations
* **AC\-AL\-WR\-001** – Every create/update/delete generates immutable audit log entry with event_id (UUID), UTC ISO 8601 timestamp, user_id, role, operation type, record_id, hash_before/after.
* **AC\-AL\-WR\-002** – Log entries tamper‐evident and retained ≥7 years.

## KPI Mapping

| KPI ID   | Description                                 | Linked Acceptance Criteria |
|----------|---------------------------------------------|----------------------------|
| KPI‐01   | Average form submission response ≤200 ms    | US‐001 negative latency scenario |
| KPI‐02   | System availability ≥99.9 %                | NFR‐002 |
| KPI‐03   | Successful audit log generation for every submission | AC\_AL\_WR\_001 |
| KPI‐04   | PDF export security compliance (PDF/A‐2b) | AC\_PDF\_001 / AC\_PDF\_002 |
| KPI‐05   | Test coverage ≥80 % for form validation & encryption modules | FR\_004 |

## Risks & Mitigations

| Risk ID   | Description                                 | Mitigation |
|-----------|---------------------------------------------|------------|
| RISK‐01   | Unauthorized data exposure                  | Enforce RBAC; immutable audit logs |
| RISK‐02   | Open-source component vulnerabilities    | Use vetted libraries; SBOM scanning |
| RISK‐03   | Deployment misconfiguration               | Automated CI/CD checks; container hardening |
| RISK‐04   | Compliance audit gaps                    | Continuous compliance monitoring dashboards |
| RISK‐05   | Capacity constraints in air‐gap environment   | Capacity planning; resource buffers |

### User Stories

**US‑001 – Secure Demographic Capture**
> **As** a *clinical staff* (ST-001)  
> **I want** to enter patient demographic data into a web form that encrypts the data before storage  
> **So that** patient information is protected in accordance with HIPAA §164.312(a)(2)(iv).

*Acceptance Criteria* (traceability: **FR‑001**, **KPI-001**, **RISK-001**):
1. Given the web form is loaded over HTTPS, when the staff submits the form, then the payload is encrypted with AES‑256‑GCM before being written to PostgreSQL.
2. The encryption key is wrapped by a master key stored in a hardware security module (HSM) or encrypted file; decryption failures trigger AC‑KM‑001.
3. Response time for the audit log write is <200 ms (KPI-001).
4. All encryption operations are logged with operation = ENCRYPTION_SUCCESS.

**US‑002 – Insurance Validation**
> **As** a *patient* (ST-002)  
> **I want** the system to validate my insurance number against a reference service before submission  
> **So that** only valid policies are stored.

*Acceptance Criteria* (traceability: **FR‑002**, **KPI-001**):
1. Given a valid insurance number format, when the form is submitted, then the system performs a synchronous lookup against the offline reference table and returns success/failure within 200 ms.
2. Invalid numbers produce an inline error message without exposing internal details.

**US‑003 – Immutable Audit Logging**
> **As** a *compliance officer* (ST-003)  
> **I want** every read/write operation on patient data to be recorded immutably with role information  
> **So that** I can demonstrate compliance during audits.

*Acceptance Criteria* (traceability: **FR‑003**, **KPI-003**, **RISK-001**):
1. All INSERT/UPDATE/SELECT statements generate an entry in `audit_log` with columns: `timestamp`, `operation`, `user_id`, `role`, `hash_chain`.
2. The hash chain links each entry to the previous one using SHA‑512; any mismatch raises an alert to ST-003.
3. Entries older than 7 years are archived to read‑only storage but never deleted.
4. Audit log write latency ≤200 ms (KPI-001).

**US‑004 – PDF Intake Summary Generation**
> **As** a *clinical staff* (ST-001)  
> **I want** an offline PDF summary of the patient intake form that includes a watermark and timestamp  
> **So that** I can print and store it securely without internet access.

*Acceptance Criteria* (traceability: **FR‑005**, **FR‑007**, **KPI-004**, **RISK-001**):
1. Given a completed intake record, when the staff clicks “Generate PDF”, then wkhtmltopdf creates a PDF using only local resources.
2. The PDF contains a visible watermark “Confidential – Patient Intake” and a timestamp of generation.
3. The PDF file is stored in an encrypted volume; access requires the same role-based permissions as the source record.
4. No external network calls are made during PDF generation (validated by AC‑001).
5. PDF generation completes within 500 ms on typical hardware (performance target).

**US‑005 – Air‑Gap Enforcement Validation**
> **As** an *IT operations* engineer (ST-004)  
> **I want** automated checks that confirm no container can resolve external DNS or reach the internet  
> **So that** the air‑gapped environment remains isolated.

*Acceptance Criteria* (traceability: **FR‑008**, **RISK-003**):
1. A health check script runs hourly; it attempts `nslookup google.com` inside each container and expects NXDOMAIN.
2. Network traffic capture shows zero outbound packets on ports 80/443 after startup.
3. Any violation triggers an alert to ST-004 and logs `AIRGAP_VIOLATION`.

## MVP Scope

The Minimum Viable Product includes the following features:
1. Secure web form for demographic and insurance capture (US‑001 & US‑002).
2. Immutable audit logging backend (US‑003).
3. Offline PDF summary generation with watermark (US‑004).
4. Docker Compose deployment scripts for air‑gap installation (FR‑008).
5. Basic health checks validating air-gap isolation (US‑005).

Non‑included for MVP but planned for later releases:
- Multi‑tenant isolation for separate clinic deployments.
- Real-time monitoring dashboard.
- Automated backup & restore UI.

## Air‑Gap Setup Guide for PatientIntake System

### 1. Prerequisites
| Component | Version / Requirement | Source |
|------------|-----------------------|--------|
| Host OS | Ubuntu 22.04 LTS (or equivalent Debian) | — |
| Docker Engine | 20.10.24 or later (offline installer) | — |
| Docker Compose | 2.20.0 binary (offline) | — |
| PDF generator | wkhtmltopdf 0.12.6 static binary | — |
| PostgreSQL | 14.x server package (deb) | — |
| TLS certificates | Self‑signed or internal CA certs for HTTPS | — |
| Air‑gap media | USB drive or secure internal network share for transferring packages | — All packages must be downloaded on a machine with internet access, verified via SHA256 checksums, and transferred to the target air‑gapped host using the secure media. |

### 2. Transfer and Verify Packages on the Air‑Gapped Host
bash
mkdir -p /opt/airgap-packages && mount /dev/sdx1 /mnt/airgap
cp /mnt/airgap/* /opt/airgap-packages/
sha256sum -c /opt/airgap-packages/checksums.txt || { echo "Checksum mismatch"; exit 1; }

Any mismatch aborts the installation.

### 3. Install System Dependencies (Offline)
bash
sudo dpkg -i docker-ce_20.10.*_amd64.deb docker-ce-cli_20.10.*_amd64.deb containerd.io_1.6.*_amd64.deb
sudo dpkg -i postgresql-14_*_amd64.deb libpq-dev_14.*_amd64.deb
sudo dpkg -i wkhtmltopdf_0.12.6-1_amd64.deb

Resolve any dependency errors using the same offline package pool.

### 4. Generate Internal TLS Assets (No Internet Required)
bash
mkdir -p /etc/patientintake/tls && cd /etc/patientintake/tls
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt -subj "/C=US/ST=State/L=City/O=HealthOrg/OU=IT/CN=HealthOrg-CA"
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=State/L=City/O=HealthOrg/OU=App/CN=patientintake.local"
ossp x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 825 -sha256
chmod 600 server.key

These certificates will be mounted into the Docker containers.

### 5. Prepare Docker Images for Offline Use
On a machine with internet access:
bash
docker pull python:3.11-slim
docker pull nginx:1.25-alpine
docker pull postgres:14-alpine
docker save -o patientintake_app.tar python:3.11-slim nginx:1.25-alpine postgres:14-alpine

Transfer `patientintake_app.tar` to `/opt/airgap-images` on the target host and load:
bash
sudo docker load -i /opt/airgap-images/patientintake_app.tar

All images are now available locally; no registry calls will be made at runtime.

### 6. Create Offline Docker Compose File
yaml
version: "3.9"
services:
  web:
    image: python:3.11-slim
    container_name: patientintake_web
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://patientintake:securepwd@db/patientdb
      TLS_CERT: /tls/server.crt
      TLS_KEY: /tls/server.key
    volumes:
      - ./tls:/tls:ro
    ports:
      - "443:443"
    networks:
      - internal
  nginx:
    image: nginx:1.25-alpine
    container_name: patientintake_nginx
    depends_on:
      - web
    volumes:
      - ./nginx/conf:/etc/nginx/conf.d:ro
      - ./tls:/tls:ro
    ports:
      - "80:80"
    networks:
      - internal
  db:
    image: postgres:14-alpine
    container_name: patientintake_db
    environment:
      POSTGRES_USER: patientintake
      POSTGRES_PASSWORD: securepwd
      POSTGRES_DB: patientdb
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - internal
networks:
  internal:
    driver: bridge
volumes:
  pgdata:

save as `/opt/patientintake/docker-compose.yml`.
and note that all network traffic stays within the internal bridge; no external ports are exposed beyond HTTPS (443) and HTTP (80) on the host firewall.

### 7. Harden Host Firewall (Air‑Gap Enforcement)

Apply the following checklist to lock down the host and enforce air‑gap isolation, while properly accounting for Docker's `iptables` behavior.

#### 7.1 Configure Docker-UFW Integration
Docker bypasses UFW by default. You must secure the `DOCKER-USER` chain to prevent containers from exposing published ports to the internet.
1. Add the following to `/etc/ufw/after.rules` to force Docker traffic through UFW:
   ```bash
   *filter
   :DOCKER-USER - [0:0]
   -A DOCKER-USER -j RETURN -s 10.0.0.0/8
   -A DOCKER-USER -j RETURN -s 172.16.0.0/12
   -A DOCKER-USER -j RETURN -s 192.168.0.0/16
   -A DOCKER-USER -p tcp -m tcp --dport 80 -j RETURN
   -A DOCKER-USER -p tcp -m tcp --dport 443 -j RETURN
   -A DOCKER-USER -j DROP
   COMMIT
   ```

#### 7.2 Block Outbound Connections
2. Reset UFW to a deny-all default and allow standard HTTP/HTTPS:
   ```bash
   sudo ufw default deny incoming
   sudo ufw default deny outgoing
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```
3. Enable the firewall:
   ```bash
   sudo ufw enable
   sudo systemctl restart docker
   ```

#### 7.3 Lock Down DNS
4. Configure `/etc/resolv.conf` to point only to an internal DNS server (e.g., `nameserver 10.0.0.1`). Remove any public resolvers (`8.8.8.8`, `1.1.1.1`).
5. Verify resolution of external domains fails from within each container:
   ```bash
   docker exec patientintake_web nslookup google.com && echo "FAIL: external DNS resolves" || echo "PASS"
   ```

#### 7.4 Verify Zero Outbound Traffic
6. Run a packet capture targeting outgoing packets specifically originating from the host's subnet to external public IPs:
   ```bash
   sudo tcpdump -i eth0 -c 100 'src net 10.0.0.0/8 and not dst net 10.0.0.0/8 and (tcp dst port 80 or tcp dst port 443)' -w /tmp/airgap_verify.pcap
   ```
7. Confirm the capture file contains **zero packets**. Any outbound traffic constitutes an air-gap violation and must be investigated before proceeding.

#### 7.5 Persist and Document
8. Document any exceptions required for internal monitoring (e.g., health‑check endpoints on `10.x.x.x`). Keep exceptions minimal and approved by the System Administrator (ST-004).
9. Record all firewall changes in the project change log repository. Every change must follow the change management process and include ST-004 approval.

#### 7.5 Log Retention and Backup
12. Retain firewall and audit logs per compliance policy (minimum 7 years per KPI-003).
13. Encrypt logs at rest using AES‑256; rotate encryption keys per the documented security schedule.
14. Test restoration from log backups quarterly and verify integrity using SHA‑256 hash verification.
15. Store backups on encrypted offline media; maintain an inventory of backup media locations with strict access controls.
16. Log all backup retrieval actions. Destroy expired media securely per the data disposal policy.
17. Ensure all steps comply with RISK-001 mitigation strategies throughout this process.

## Patient Intake Feature Specification

### Functional Requirements (Traceability)

| ID | Description |
|----|-------------|
| **FR‑001** | Secure capture of patient demographic data. |
| **FR‑002** | Capture and validation of insurance information. |
| **FR‑003** | Store medical history securely. |
| **FR‑004** | Provide automated unit and integration tests covering form validation, encryption handling, and access control. |
| **FR‑005** | Generate PDF Intake Summary after successful submission. |
| **FR‑006** | Apply watermark & timestamp to generated PDFs. |
| **FR‑007** | Ensure PDF generation complies with on‑premise security policies. |
| **FR‑008** | Deploy the service using Docker Compose for containerized environments. |
| **FR‑009** | Conduct quarterly disaster‑recovery drills with full restore on an air‑gap host. |

#### US‑001: Capture Demographic Data
*As a **Clinical Staff (ST-001)** I want to enter patient demographic information so that the system records accurate patient records.*

**Acceptance Criteria**
1. **Given** the staff is authenticated,
   **When** they navigate to the "New Patient" form,
   **Then** the form displays fields for name, DOB, address, phone.
2. **Given** all mandatory fields are filled with valid data,
   **When** the staff clicks *Submit*,
   **Then** the data is persisted encrypted at rest (**NFR‑005**) and an audit log entry is created (**NFR‑003**, **KPI-003**).
3. **Given** invalid data is entered,
   **When** the staff attempts submission,
   **Then** inline validation messages are shown and submission is blocked.

#### US‑002: Capture Insurance Information
*As a **Clinical Staff (ST-001)** I need to record insurance details so that billing can be processed.*

**Acceptance Criteria**
1. Form includes insurer name, policy number, group number.
2. Validation ensures policy number matches insurer format.
3. Successful submission creates encrypted record (**NFR‑005**) and logs the event (**NFR‑003**, **KPI-003**).

#### US‑003: Store Medical History Securely
*As a **Clinical Staff (ST-001)** I want to add medical history so that clinicians have context for care.*

**Acceptance Criteria**
1. History is stored in a separate encrypted column.
2. Access is restricted to users with *Medical_History_Read* permission (**NFR‑005**, **NFR‑006**).
3. Audit log entry created on each create/update (**NFR‑003**, **KPI-003**).

#### US‑004: Generate PDF Intake Summary
*As a **Patient (ST-002)** I want to receive a PDF summary of my submitted information so I have a personal record.*

**Acceptance Criteria**
1. After successful form submission, the system generates a PDF (**FR‑005**) containing all captured fields.
2. PDF includes a watermark and timestamp (**FR‑006**, **FR‑007**) complying with security policy.
3. PDF is stored securely and a download link is presented to the patient.
4. Generation process is logged for audit (**NFR‑003**, **KPI-004**).

#### US‑005: API Specification for Intake Submission
*As a **System Administrator (ST-004)** I need an API endpoint so that external systems can submit intake data programmatically.*

**API Endpoint**: `POST /api/v1/intake`

- **patient**: {'firstName': 'string', 'lastName': 'string', 'dob': 'YYYY-MM-DD', 'address': 'string', 'phone': 'string'}
- **insurance**: {'provider': 'string', 'policyNumber': 'string', 'groupNumber': 'string'}
- **medicalHistory**: {'conditions': ['string'], 'medications': ['string']}

**Response (201 Created)** includes `location` header pointing to the generated PDF summary.
*Security*: OAuth2 Bearer token required; payload encrypted in transit (**NFR‑005**) and validated against schema.
*Rate limiting*: 100 requests per minute per client.
*Audit*: Each request creates an audit log entry (**NFR‑003**, **KPI-003**) .

#### US‑006: Log Retention & Offline Storage
*As a **Compliance Officer (ST-003)** I need logs older than 90 days moved to offline storage so we meet retention policy (**NFR‑002**) .*

**Acceptance Criteria**
1. System automatically archives Hive logs older than 90 days to encrypted offline storage bucket.
2. Archived logs are immutable and searchable for audit purposes.
3. Retention process runs nightly; success/failure recorded in monitoring dashboard (**KPI-002**).

#### US‑007: Quarterly Disaster Recovery Drill
*As a **System Administrator (ST-004)** I must perform a full restore from backup on an air‑gap host quarterly (**FR‑009**) to validate recovery procedures.*

**Acceptance Criteria**
1. Backup of database and file storage is taken weekly.
2. Every quarter a restore is executed on a separate isolated environment.
3. Restoration completes within 4 hours and passes verification tests.
4. Results are logged; any failures trigger an incident ticket.
5. Drill outcome is reported to compliance officer (**KPI-002**, **KPI-003**) .
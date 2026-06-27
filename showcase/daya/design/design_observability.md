# Observability & Monitoring Design

## 1. AWS X-Ray Distributed Tracing Strategy

This section defines the distributed tracing architecture for the MealCredit platform, ensuring end-to-end visibility of donor funding and beneficiary redemption flows across the Expo client, GraphQL API, and gRPC financial services. The strategy prioritizes PCI-DSS Level 1 compliance by strictly preventing PII leakage into trace data.

### 1.1. Trace Context Propagation

To maintain a unified trace across heterogeneous service boundaries, the platform adopts the W3C TraceContext standard (traceparent header) for HTTP/HTTPS traffic and gRPC metadata for internal service communication.

 Expo Client (React Native): The Expo mobile application must inject the traceparent header into all outgoing HTTP requests to the GraphQL API. This requires a custom networking layer configuration within the Expo v51 / React Native Fabric architecture to ensure the header is present on every API call, including those triggered by background events.
 GraphQL API (Orchestration Layer): The GraphQL API acts as the primary trace context carrier. It extracts the traceparent header from incoming client requests and propagates it to downstream gRPC financial services. If a traceparent header is missing (e.g., internal service-to-service calls), the API generates a new valid W3C TraceContext ID.
 gRPC Financial Services: The gRPC services (Transaction & Financial Engine, Dispute Resolution) must extract the trace context from gRPC metadata (specifically the traceparent key) and inject it into outgoing calls to Aurora PostgreSQL and Stripe APIs. This ensures that the financial transaction trace remains linked to the original client request.

### 1.2. AWS X-Ray SDK Integration

AWS X-Ray SDKs will be integrated into the Node.js (GraphQL API) and Go (gRPC services) runtimes to automatically capture subsegments for database calls, external API interactions, and service boundaries.

 Node.js (GraphQL API): The X-Ray SDK for Node.js will be configured to automatically capture HTTP/HTTPS requests and responses. Custom annotations will be added to key resolvers to capture business context (e.g., anonymous_voucher_id, donor_pool_id) without capturing PII.
 Go (gRPC Services): The X-Ray SDK for Go will be integrated into the gRPC middleware to capture service entry and exit points. Subsegments will be created for each financial ledger mutation and Stripe API call.
 Aurora PostgreSQL: X-Ray will be enabled for Aurora PostgreSQL to capture database-level metrics and query performance. Database calls will be automatically instrumented by the X-Ray SDK, linking them to the parent trace.
 Stripe API: Calls to the Stripe API (for webhook processing and payment intent creation) will be captured as external subsegments. The X-Ray SDK will automatically mask sensitive card data in accordance with PCI-DSS requirements.

### 1.3. PII Sanitization and Data Isolation

Strict data isolation constraints ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4), [CON-92F07E31B0](../project_glossary.md#con-92f07e31b0)) must be enforced at the tracing layer to prevent PII or beneficiary demographic data from being exposed in monitoring dashboards or logs.

 Automatic Redaction: The X-Ray SDKs will be configured with a custom filter rule that automatically redacts any field containing known PII patterns (e.g., email, phone, legal_name, ssn) from trace segments before they are sent to AWS X-Ray.
 Annotation Policy: Only non-PII business keys (e.g., anonymous_voucher_id, donor_pool_id, merchant_id) will be captured as X-Ray annotations. These annotations are searchable and filterable in the X-Ray console but do not contain sensitive data.
 Service Map Visibility: The AWS X-Ray Service Map will be configured to display only service names and request counts, ensuring that no PII is visible in the architectural visualization.

### 1.4. Sampling Strategy

To balance observability depth with cost and latency, a tiered sampling strategy will be implemented:

 Error Sampling: 100% of all requests resulting in HTTP 4xx or 5xx errors will be sampled to ensure full visibility into failure modes.
 Health Sampling: 10% of all successful requests will be sampled to provide a representative view of healthy traffic patterns and performance baselines.
 Critical Path Sampling: 100% of requests to critical endpoints (e.g., `/redemption/scan`, `/donor/fund`) will be sampled to ensure complete visibility into high-value user journeys.

### 1.5. Validation and Acceptance Criteria

 End-to-End Traceability: A single end-to-end trace must be retrievable in the AWS X-Ray console for a completed beneficiary redemption, showing the Expo client request, GraphQL API processing, gRPC financial service call, and Aurora PostgreSQL ledger update.
 PII Verification: No PII (e.g., beneficiary names, donor PII) must be present in the raw trace segments. This will be verified by inspecting the raw trace data in the X-Ray console.
 Context Propagation: Trace context must be correctly propagated across all service boundaries (Expo -> GraphQL -> gRPC -> Aurora/Stripe) without breaks or orphaned segments.

## 2. CloudWatch Metric and Log Schema for Financial Ledger Auditing

This section defines the CloudWatch metric and log schema for financial ledger auditing, ensuring all mutations are captured with append-only cryptographic log auditing in Aurora PostgreSQL. This design directly supports the project's compliance and trust objectives, specifically Implied concern: Implement append-only cryptographic log auditing in Aurora PostgreSQL for all financial ledger mutations. ([CON-1762EA5021](../project_glossary.md#con-1762ea5021)) and Implied concern: Log all administrative ledger operations and infrastructure changes to AWS CloudTrail for SOC2 Type II evidence. ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2)).

### 2.1. Aurora PostgreSQL Append-Only Ledger Schema

To guarantee the immutability of financial records, the ledger will utilize a dedicated ledger_audit_log table. This table is designed to be append-only, meaning no UPDATE or DELETE operations are permitted on its rows. Every financial mutation (e.g., credit issuance, redemption, refund) is recorded as a new row.

Table Schema:

| Column Name | Data Type | Constraints & Defaults | Description |
| :--- | :--- | :--- | :--- |
| mutation_id | UUID | `PRIMARY KEY`, `DEFAULT gen_random_uuid()` | Unique identifier for the financial mutation event. |
| timestamp | TIMESTAMPTZ | `NOT NULL`, `DEFAULT NOW()` | The exact time the mutation was committed to the ledger. |
| operation_type | `VARCHAR(20)` | `NOT NULL`, `CHECK (operation_type IN ('ISSUANCE', 'REDEMPTION', 'REFUND', 'ADJUSTMENT'))` | The type of financial operation being audited. |
| table_affected | `VARCHAR(50)` | `NOT NULL` | The logical table or entity impacted by the mutation (e.g., beneficiary_credits, donor_funding). |
| row_id | UUID | `NOT NULL` | The primary key of the row in the affected table that was mutated. |
| old_values | JSONB | `DEFAULT '{}'::jsonb` | The state of the affected row before the mutation. Captured via OLD in triggers. |
| new_values | JSONB | `DEFAULT '{}'::jsonb` | The state of the affected row after the mutation. Captured via NEW in triggers. |
| actor_id | UUID | `NOT NULL` | The ID of the actor (e.g., Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)), NGO Operator ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0))) initiating the mutation. |
| cryptographic_hash | `VARCHAR(64)` | `NOT NULL` | SHA-256 hash of the previous row's cryptographic_hash concatenated with the current mutation's data. Ensures chain integrity. |
| previous_hash | `VARCHAR(64)` | `NOT NULL` | The cryptographic_hash of the immediately preceding row in this audit log. |

Immutability Enforcement:

A PostgreSQL TRIGGER function will be implemented on all financial tables to automatically insert records into ledger_audit_log on INSERT, UPDATE, and DELETE operations. Additionally, a database-level REVOKE statement will be executed to remove UPDATE and DELETE permissions on the ledger_audit_log table for all application roles, ensuring that only the database superuser (or an automated CI/CD pipeline with explicit approval) can modify it, and only for forensic recovery purposes.

### 2.2. CloudWatch Log Schema for Ledger Auditing

CloudWatch Logs will ingest structured JSON logs from the application layer and database triggers. These logs will provide real-time visibility into ledger mutations and their cryptographic integrity.

Log Group: `/mealcredit/financial/ledger_audit`

Log Stream Naming Convention: `{service_name}/{environment}/{date}` (e.g., `grpc-financial-service/prod/2024-05-20`)

Log Event Schema:

| Field Name | Type | Description |
| :--- | :--- | :--- |
| log_level | String | INFO, WARN, ERROR |
| service_name | String | The microservice handling the mutation (e.g., grpc-financial-service). |
| trace_id | String | The AWS X-Ray trace ID for end-to-end visibility. |
| ledger_mutation_id | String | The mutation_id from the ledger_audit_log table. |
| operation_type | String | The type of operation (e.g., REDEMPTION). |
| hash_chain_status | String | VALID or INVALID. Indicates if the cryptographic_hash chain was verified successfully. |
| latency_ms | Float | The time taken to process the mutation and write to the ledger. |
| actor_id | String | The ID of the actor performing the mutation. |
| metadata | Object | Additional context, such as metro_region (SF, NYC, CHI) and anonymous_voucher_id (if applicable). |

Data Isolation & PII Protection:

To adhere to Implied concern: Implement strict data isolation where beneficiary demographic status and legal names are cryptographically segregated from public ... (CON-92F07E31B0) and Implied concern: Adhere to FTC guidelines on anonymity, ensuring no de-anonymization attacks can link beneficiaries to donors through metadata anal... ([CON-C22D030D21](../project_glossary.md#con-c22d030d21)), the CloudWatch log schema will strictly exclude any PII or beneficiary demographic data. The metadata field will only contain anonymized identifiers (e.g., anonymous_voucher_id) and non-sensitive operational data. Any attempt to log PII will be caught by a pre-log sanitization layer in the application code, which will redact sensitive fields before the log event is emitted.

### 2.3. CloudWatch Custom Metrics for Ledger Integrity

Custom metrics will be published to CloudWatch to monitor the health and integrity of the financial ledger in real-time. These metrics will be used for automated alerting and SOC2 Type II evidence generation.

Metric 1: LedgerMutationCount

Namespace: `MealCredit/Financial`
Metric Name: LedgerMutationCount
Dimensions: OperationType, MetroRegion, ActorRole
Unit: Count
Description: The number of financial ledger mutations per operation type, metro region, and actor role.
Alert Threshold: `> 0` for ERROR log levels.

Metric 2: HashChainIntegrityFailures

Namespace: `MealCredit/Financial`
Metric Name: HashChainIntegrityFailures
Dimensions: ServiceName
Unit: Count
Description: The number of times a cryptographic hash chain verification failed during a ledger mutation.
Alert Threshold: `> 0` (Immediate critical alert).

Metric 3: AuditLogLatencyP99

Namespace: `MealCredit/Financial`
Metric Name: AuditLogLatencyP99
Dimensions: ServiceName
Unit: Milliseconds
Description: The p99 latency for writing to the ledger_audit_log table.
Alert Threshold: `> 500ms` (Indicates potential performance degradation in the audit logging process).

Metric 4: CreditPoolUtilizationRate

Namespace: `MealCredit/Financial`
Metric Name: CreditPoolUtilizationRate
Dimensions: MetroRegion
Unit: Percent
Description: The percentage of the total credit pool that has been utilized in a given metro region. This supports Implied concern: Monitor Credit Pool Utilization Rate with automated alerts triggering when thresholds exceed 85%. ([CON-2059B17FB2](../project_glossary.md#con-2059b17fb2)).
Alert Threshold: `> 85%` (Warning), `> 95%` (Critical).

### 2.4. SOC2 Type II Evidence Integration

To streamline SOC2 Type II compliance, CloudWatch Logs will be integrated with AWS CloudTrail. All administrative ledger operations (e.g., manual adjustments by a Platform Administrator (ACT-086A974D63)) and infrastructure changes will be logged to CloudTrail. CloudWatch Logs will then ingest these CloudTrail logs, creating a unified audit trail.

Integration Pattern:

1. CloudTrail: Captures all API calls to AWS services and application-level administrative actions.
2. CloudWatch Logs: Ingests CloudTrail logs via a CloudWatch Logs subscription filter.
3. CloudWatch Metrics: Custom metrics are derived from both application logs and CloudTrail logs to provide a holistic view of system integrity.

This integration ensures that all administrative actions are immutable, traceable, and readily available for SOC2 Type II audits, supporting Implied concern: Ensure SOC2 Type II structural planning is baked into the infrastructure-as-code and access control policies. ([CON-81FB01F06B](../project_glossary.md#con-81fb01f06b)).

### 2.5. Validation and Verification

- Done Criteria: A single end-to-end trace can be retrieved in the X-Ray console for a completed beneficiary redemption, showing the Expo client request, GraphQL API processing, gRPC financial service call, and Aurora PostgreSQL ledger update. No PII is present in the trace data. Trace context is correctly propagated across all service boundaries.
- Validation: Verify that no PII is present in the trace data by inspecting the raw trace segments. Confirm that trace context is correctly propagated across all service boundaries.

### 2.6. Knowledge Gaps and Assumptions

KNOWLEDGE_GAP: Audit Log Retention Period - The exact retention period for the ledger_audit_log table and CloudWatch Logs must be established by the Compliance & Legal team to align with financial regulations governing quasi-cash instruments, specifically regarding unclaimed property and escheatment laws (Implied concern: Comply with financial regulations governing quasi-cash instruments, specifically regarding unclaimed property and escheatment laws... ([CON-B1DFEBEC8C](../project_glossary.md#con-b1dfebec8c))).
ASSUMPTION: SHA-256 Hashing Algorithm - SHA-256 is assumed to be the approved cryptographic hashing algorithm for the ledger chain. If a different algorithm is mandated by PCI-DSS Level 1 or SOC2 Type II requirements, this must be updated. Owner: Security Architecture & Access Control.
ASSUMPTION: Aurora PostgreSQL Trigger Performance - It is assumed that the overhead of the PostgreSQL trigger for the ledger_audit_log table will not significantly impact the p99 latency of financial transactions. If performance degradation is observed, an asynchronous logging mechanism (e.g., using a message queue) may be required. Owner: Infrastructure Topology & Deployment Design.

---

## 3. Real-Time Metric Collection Architecture

This section defines the real-time metric collection architecture for the MealCredit platform, specifically targeting the Credit Pool Utilization Rate and Donation-to-Redemption Velocity (DRV). The architecture leverages the event-driven serverless backbone to ensure sub-second metric aggregation, enabling automated alerting for liquidity health and operational anomalies across the SF, NYC, and Chicago metropolitan footprints.

### 3.1. Credit Pool Utilization Rate (CPU) Architecture

The Credit Pool Utilization Rate is a critical liquidity metric that tracks the percentage of total donor-funded credits that have been redeemed within a specific regional pool. This metric directly impacts the platform's ability to honor redemption requests and requires high-frequency monitoring to prevent liquidity shortfalls.

#### 3.1.1. Metric Definition and Calculation

 Metric Name: mealcredit.credit_pool.utilization_rate
 Type: Gauge (percentage, 0.0 to 1.0)
 Dimensions:
  metro_region: (e.g., "SF", "NYC", "CHI") - Aligns with the 3 initial metropolitan footprints.
  ngo_tenant_id: (Optional) For granular monitoring of specific NGO operator pools.
 Calculation Logic:
  `CPU = (Total_Credits_Redemptions / Total_Credits_Issued)  100`
  Calculated in real-time by the Transaction & Financial Engine ([CAP-TRANSACTION-FINANCIAL-ENGINE](../project_glossary.md#cap-transaction-financial-engine)) upon successful POS clearance.
  Aggregated via a serverless stream processor (e.g., AWS Lambda triggered by DynamoDB Streams or Kinesis) to update a high-performance time-series store (e.g., Amazon Timestream or CloudWatch Custom Metrics).

#### 3.1.3. Automated Alert Thresholds

To proactively manage liquidity, the following alert thresholds are established, aligned with the requirement to monitor Credit Pool Utilization Rate with automated alerts triggering when thresholds exceed 85% (CON-2059B17FB2, [CON-7031BE57B3](../project_glossary.md#con-7031be57b3)).

| Severity Level | Threshold | Action | Notification Channel |
| :--- | :--- | :--- | :--- |
| Info | > 60% | Log to CloudWatch; Update Dashboard | Internal Ops Dashboard |
| Warning | > 75% | Trigger automated liquidity check; Notify Platform Administrator (ACT-086A974D63) | Slack / PagerDuty |
| Critical | > 85% | Automated Alert Trigger; Initiate emergency donor funding request workflow; Notify NGO Operator (ACT-09E028AEB0) and Platform Administrator | PagerDuty / SMS / Email |
| Emergency | > 95% | Halt New Credit Issuance (if configured); Escalate to Executive Leadership | Executive PagerDuty |

### 3.2. Donation-to-Redemption Velocity (DRV) Architecture

The Donation-to-Redemption Velocity (DRV) measures the speed at which donated funds are converted into redeemed credits. This metric is vital for monitoring liquidity health against the 14-day target and ensuring that donor funds are being utilized effectively to support beneficiaries.

#### 3.2.2. Data Ingestion Pipeline

1. Event Sources:
  DonationReceivedEvent emitted by the Donor Onboarding & Funding Activation flow ([JNY-62D850E94B](../project_glossary.md#jny-62d850e94b)).
  CreditRedemptionEvent emitted by the Transaction & Financial Engine.
2. Stream Processing: A dedicated Lambda function consumes both event streams, maintaining a rolling window state (stored in DynamoDB or Redis) to calculate the current DRV for each metro_region.
3. Storage: Metrics are stored with a 1-hour granularity for real-time dashboards.

### 3.3. Stripe Webhook Processing Latency

To ensure a seamless user experience, the platform must monitor the latency of Stripe webhook processing, which triggers the credit issuance and POS clearance flows.

 Metric Name: mealcredit.stripe.webhook_processing_latency
 Type: Histogram (milliseconds)
 Dimensions:
  event_type: (e.g., "payment_intent.succeeded", "charge.refunded")
  metro_region: (Optional)
 Target: Average latency below 150ms from card tap to merchant ledger entry ([CON-06232374D9](../project_glossary.md#con-06232374d9), [CON-A0B785A40D](../project_glossary.md#con-a0b785a40d)).
 Alert Threshold:
  Warning: p95 latency > 200ms.
  Critical: p99 latency > 500ms or failure rate > 1%.

## 4. Distributed Tracing Standards for Asynchronous gRPC and Synchronous GraphQL

This section defines the specific distributed tracing standards for asynchronous gRPC financial transactions and synchronous GraphQL CRUD operations, fulfilling the design phase acceptance criteria for observability contracts.

### 4.1. Synchronous GraphQL Tracing Standards

For the synchronous GraphQL API layer, tracing must adhere to the W3C TraceContext standard to ensure seamless propagation from the Expo client through the API Orchestration Layer ([SUR-85E4A5B6E7](../project_glossary.md#sur-85e4a5b6e7)) to downstream services.

 Header Propagation: The `traceparent` header must be injected by the Expo client and extracted by the GraphQL API resolvers. The API must propagate this context to all downstream gRPC calls.
 Span Naming Convention: GraphQL spans must follow the pattern `GraphQL/{OperationType}/{FieldName}` (e.g., `GraphQL/Mutation/redemptionScan`).
 Error Handling: Any GraphQL resolver error must be captured as a span event with the error details, ensuring that the root cause of a failed transaction is visible in the X-Ray service map.

### 4.2. Asynchronous gRPC Tracing Standards

For the asynchronous gRPC financial services, tracing must utilize gRPC metadata to propagate context across service boundaries, ensuring that financial ledger mutations are linked to the originating client request.

 Metadata Propagation: The `traceparent` value must be stored in the gRPC metadata under the key `traceparent`. The receiving gRPC service must extract this value and initialize a new X-Ray segment with the correct parent context.
 Span Naming Convention: gRPC spans must follow the pattern `gRPC/{ServiceName}/{MethodName}` (e.g., `gRPC/FinancialService/ProcessRedemption`).
 Timeout and Retry Tracing: If a gRPC call times out or is retried, the X-Ray SDK must capture the retry attempt as a subsegment, allowing operators to distinguish between transient network issues and persistent business logic failures.

### 4.3. Cross-Service Trace Correlation

To ensure end-to-end visibility, the platform must implement a trace correlation strategy that links synchronous and asynchronous spans.

 Correlation Key: A unique `correlation_id` (UUIDv4) must be generated for each donor funding or beneficiary redemption event. This ID must be included in both the GraphQL request and the gRPC metadata, allowing X-Ray to stitch together the synchronous and asynchronous spans into a single logical transaction view.
 Service Map Visualization: The AWS X-Ray Service Map must be configured to display the correlation between the GraphQL API and gRPC services, providing a clear visual representation of the financial transaction flow.

### 4.1. AWS CloudTrail Integration for Administrative Auditing

AWS CloudTrail will be configured to capture all management events and data events related to the MealCredit platform's infrastructure and data layers. This provides the foundational audit trail for SOC2 Type II compliance.

#### 4.1.1. Management Events Configuration

CloudTrail will be enabled across all AWS regions where MealCredit operates (SF, NYC, Chicago) to capture API calls made to AWS services. This includes:

IAM Events: All changes to IAM roles, policies, and users, particularly those associated with the Platform Administrator (ACT-086A974D63) and NGO Operator (ACT-09E028AEB0) roles.
EC2/ECS/Lambda Events: All changes to compute resources, including scaling events, configuration changes, and deployment actions.
S3 Events: All access and modification events to S3 buckets storing application artifacts, logs, and backups.
RDS/Aurora Events: All changes to the Aurora PostgreSQL database configuration, including security group modifications and parameter group changes.

#### 4.1.2. Data Events Configuration

To support SOC2 Type II evidence for data integrity and access, CloudTrail will capture data events for critical resources:

- Aurora PostgreSQL Data Events: Capture all INSERT, UPDATE, and DELETE operations on the financial ledger tables. This is critical for verifying the append-only cryptographic log auditing (CON-1762EA5021, [CON-6061FCCA83](../project_glossary.md#con-6061fcca83)).
- S3 Data Events: Capture all GetObject, PutObject, and DeleteObject events for sensitive data buckets, ensuring no unauthorized access or modification occurs.

#### 4.1.3. CloudTrail Log File Integrity and Storage

Log File Validation: CloudTrail will be configured with log file validation enabled, ensuring that all log files are signed and can be verified for tampering.
S3 Storage: CloudTrail logs will be stored in a dedicated, encrypted S3 bucket with strict access controls. This bucket will be versioned and enabled with Object Lock to prevent deletion or modification of logs for the required retention period.
Retention Period: Logs will be retained for a minimum of 7 years, aligning with SOC2 Type II audit requirements. [KNOWLEDGE_GAP: retention_period - Compliance team must establish the exact retention period required by SOC2 Type II auditors for financial and administrative logs.]

### 4.2. CloudWatch Logs Integration for Application Auditing

CloudWatch Logs will be used to capture structured application logs from the MealCredit platform's services, providing detailed context for administrative actions and financial transactions.

#### 4.2.1. Log Group Structure

CloudWatch Logs will be organized into logical log groups:

`/mealcredit/admin/operations`: Logs related to administrative actions, including user management, role assignments, and system configuration changes.
`/mealcredit/financial/ledger`: Logs related to financial ledger operations, including credit pool updates, donor funding activations, and beneficiary redemptions.
`/mealcredit/infrastructure/deployments`: Logs related to infrastructure changes, including CI/CD pipeline executions, IaC deployments, and service updates.

#### 4.2.2. Log Entry Schema

All logs will adhere to a structured JSON schema to facilitate automated evidence generation and querying:

timestamp: ISO 8601 formatted timestamp of the event.
event_id: Unique identifier for the event, correlated with distributed tracing (X-Ray trace ID).
actor_id: Identifier of the actor performing the action (e.g., Platform Administrator, NGO Operator).
action_type: Type of action performed (e.g., CREATE, UPDATE, DELETE, APPROVE).
resource_type: Type of resource affected (e.g., User, LedgerEntry, Configuration).
resource_id: Identifier of the affected resource.
metadata: Additional context-specific metadata (e.g., old values, new values, approval reason).
ip_address: IP address of the actor (if applicable).
user_agent: User agent string of the actor (if applicable).

#### 4.2.3. Log Ingestion and Forwarding

- Application Logging: All services (GraphQL API, gRPC Financial Services) will be configured to emit logs in the defined structured JSON format to CloudWatch Logs.
- CloudTrail to CloudWatch: CloudTrail logs will be forwarded to CloudWatch Logs for centralized analysis and correlation with application logs. This enables cross-referencing of infrastructure changes with application-level actions.

### 4.3. SOC2 Type II Evidence Generation

The integration of CloudTrail and CloudWatch Logs will support the generation of SOC2 Type II evidence through automated reporting and monitoring.

#### 4.3.1. Automated Evidence Reports

Access Control Reports: Automated reports will be generated from CloudTrail and CloudWatch Logs to demonstrate that access to sensitive data and administrative functions is restricted to authorized personnel (Platform Administrator, NGO Operator).
Change Management Reports: Automated reports will be generated to demonstrate that all infrastructure and application changes are logged, reviewed, and approved.
Data Integrity Reports: Automated reports will be generated from CloudTrail data events and application logs to demonstrate that financial ledger data is immutable and tamper-evident.

#### 4.3.2. Real-time Monitoring and Alerting

- Anomalous Activity Detection: CloudWatch Alarms will be configured to detect anomalous activity, such as unauthorized access attempts, unusual API call patterns, or unexpected data modifications. [KNOWLEDGE_GAP: alert_thresholds - Security team must establish specific thresholds for anomalous activity detection based on SOC2 Type II requirements.]
- Compliance Violation Alerts: Alerts will be configured to notify the compliance team of any potential SOC2 Type II violations, such as logs being deleted or modified, or unauthorized access to sensitive resources.

### 4.4. Data Isolation and PII Protection in Logs

To ensure compliance with data isolation constraints (CON-0A0288EED4, CON-92F07E31B0) and PCI-DSS Level 1 requirements, all logs will be sanitized to remove PII and sensitive data before storage.

PII Redaction: All logs will be processed through a PII redaction layer before being written to CloudWatch Logs or S3. This layer will identify and redact fields such as beneficiary names, donor PII, and payment card details.
Anonymization: Beneficiary-related data will be anonymized in logs, using hashed identifiers or UUIDs instead of raw PII. This ensures that beneficiary demographic status and legal names are cryptographically segregated from public logs (CON-0A0288EED4, CON-92F07E31B0).
PCI-DSS Compliance: No raw card data will be present in any logs. All payment-related events will reference Stripe token IDs or transaction IDs, ensuring PCI-DSS Level 1 compliance ([CON-66390130AA](../project_glossary.md#con-66390130aa), [CON-C4F0E02638](../project_glossary.md#con-c4f0e02638)).

### 4.5. Cross-Reference and Deferrals

Distributed Tracing: This artifact's logging design integrates with the distributed tracing strategy defined in the Distributed Tracing & Log Aggregation artifact. Trace IDs from X-Ray will be included in all log entries to enable end-to-end correlation.
Financial Ledger Data Model: This artifact's logging design references the financial ledger data model defined in the Financial Ledger Data Model artifact. Log entries will reference ledger entry IDs to provide context for financial transactions.
Security Architecture: This artifact's PII redaction and data isolation strategies align with the security architecture defined in the Security Architecture & Access Control artifact.

### 4.7. Validation and Testing

Log Integrity Verification: Regular tests will be conducted to verify the integrity of CloudTrail and CloudWatch Logs, ensuring that logs are not tampered with or deleted.
PII Redaction Testing: Automated tests will be conducted to verify that PII is correctly redacted from all logs before storage.
Evidence Generation Testing: Automated tests will be conducted to verify that SOC2 Type II evidence reports are generated correctly and contain all required information.
Alerting Testing: Automated tests will be conducted to verify that CloudWatch Alarms are triggered correctly for anomalous activity and compliance violations.

This design ensures that the MealCredit platform meets SOC2 Type II compliance requirements through comprehensive logging, auditing, and evidence generation, while maintaining strict data isolation and PII protection.

---

## 5. Observability Validation Plan

This section defines the validation strategy to ensure the MealCredit observability architecture (AWS X-Ray, CloudWatch, Aurora PostgreSQL) accurately reflects system state, maintains PCI-DSS Level 1 and SOC2 Type II compliance, and guarantees that no raw card data or PII leaks into monitoring surfaces.

### 5.1. End-to-End Trace Integrity Validation

The validation plan ensures that distributed traces correctly propagate context across the Expo client, GraphQL API, and gRPC financial services, verifying the integrity of the donor-to-beneficiary flow.

 Trace Context Propagation Test:
  Objective: Verify that a traceparent header injected by the Expo client is correctly parsed by the GraphQL API and mapped to gRPC metadata for the financial transaction service.
  Method: Execute a synthetic `Beneficiary Eligibility & Voucher Redemption` ([JNY-E82B8A88D8](../project_glossary.md#jny-e82b8a88d8)) flow using a test beneficiary account. Inject a known traceparent value.
  Success Criteria: The AWS X-Ray console must display a single, contiguous service map showing the request path: `Expo Client -> GraphQL API -> gRPC Transaction Service -> Aurora PostgreSQL`. The traceparent ID must be visible in the root segment of the GraphQL API.
  Compliance Check: Ensure that the trace segment metadata does not contain any PII fields (e.g., beneficiary_name, donor_email). Only anonymous voucher IDs and transaction amounts should be present.

 gRPC Asynchronous Trace Correlation:
  Objective: Validate that asynchronous gRPC calls (e.g., Stripe webhook processing) are correctly correlated with the originating GraphQL request.
  Method: Trigger a Stripe webhook event (simulated) and verify that the traceparent from the original donor funding activation (JNY-62D850E94B) is propagated to the webhook handler.
  Success Criteria: The X-Ray service map must link the webhook handler segment to the original donor funding segment via the shared trace ID.

### 5.2. Financial Ledger Audit Integrity Validation

This validates the append-only cryptographic log auditing mechanism in Aurora PostgreSQL (CON-1762EA5021, CON-6061FCCA83) to ensure financial mutations are immutable and verifiable.

 Append-Only Mutation Test:
  Objective: Confirm that the ledger_audit_log table rejects any UPDATE or DELETE operations on financial records.
  Method: Attempt to modify a completed transaction record in the financial ledger via an administrative API call. Verify that the database trigger prevents the mutation and logs the attempt in the audit log.
  Success Criteria: The transaction remains unchanged. The ledger_audit_log contains a new entry with operation_type = 'ATTEMPTED_MODIFICATION', actor_id = 'Platform Administrator' (ACT-086A974D63), and the cryptographic hash of the previous audit log entry is correctly updated.

 Cryptographic Hash Chain Verification:
  Objective: Ensure the integrity of the append-only log by verifying the hash chain.
  Method: Write a validation script that iterates through the ledger_audit_log table, recalculating the SHA-256 hash for each entry based on the previous entry's hash and the current mutation data.
  Success Criteria: The calculated hash for every entry must match the stored cryptographic_hash field. Any mismatch indicates tampering and must trigger an immediate SOC2 Type II incident alert.

### 5.3. Real-Time Metric Accuracy Validation

This validates the accuracy and latency of key business and operational metrics, including Credit Pool Utilization, Donation-to-Redemption Velocity (DRV), and Stripe Webhook Processing Latency.

 Credit Pool Utilization Rate Validation:
  Objective: Verify that the `Credit Pool Utilization Rate` metric (CON-2059B17FB2, CON-7031BE57B3) accurately reflects the ratio of redeemed credits to total available credits in real-time.
  Method: Simulate a batch of donor funding activations (JNY-62D850E94B) and subsequent beneficiary redemptions (JNY-E82B8A88D8). Compare the calculated utilization rate from the CloudWatch metric against a direct query of the financial ledger.
  Success Criteria: The CloudWatch metric value must match the ledger query result within a 1% tolerance. Alerts must trigger when the threshold exceeds 85%.

 Donation-to-Redemption Velocity (DRV) Validation:
  Objective: Ensure the DRV metric ([CON-D0F5814F21](../project_glossary.md#con-d0f5814f21), [CON-F89C70071E](../project_glossary.md#con-f89c70071e)) accurately tracks the time delta between donor funding and beneficiary redemption.
  Method: Inject a donor funding event and immediately trigger a beneficiary redemption. Measure the time delta recorded in the CloudWatch custom metric.
  Success Criteria: The recorded DRV must match the actual time delta within 100ms. The metric must correctly aggregate DRV across the 3 metro footprints (SF, NYC, Chicago).

 Stripe Webhook Processing Latency Validation:
  Objective: Verify that Stripe Webhook Processing Latency (CON-06232374D9, CON-A0B785A40D) averages below 150ms.
  Method: Simulate high-volume Stripe webhook events (1000 events/minute) and measure the end-to-end processing time from webhook receipt to financial ledger update.
  Success Criteria: The p99 latency must remain below 250ms, and the average latency must be below 150ms. If thresholds are exceeded, the system must trigger an automated alert to the Platform Administrator (ACT-086A974D63).

### 5.4. Data Isolation and PII Leakage Validation

This ensures that no PII or raw card data touches MealCredit servers or appears in monitoring dashboards, adhering to PCI-DSS Level 1 and FTC guidelines on anonymity (CON-66390130AA, [CON-B3D71A437D](../project_glossary.md#con-b3d71a437d)).

 PII Redaction Verification:
  Objective: Confirm that all PII fields are redacted before being sent to AWS X-Ray or CloudWatch.
  Method: Execute a trace containing PII fields (e.g., beneficiary_name, donor_email) in the request payload. Inspect the raw X-Ray segment data and CloudWatch log streams.
  Success Criteria: No PII fields should be present in the X-Ray segment data or CloudWatch logs. Only anonymized identifiers (e.g., voucher_id, anonymous_donor_id) should be visible.

 Raw Card Data Containment:
  Objective: Ensure that no raw card data (PAN, CVV) is stored or logged by MealCredit servers.
  Method: Inspect the Aurora PostgreSQL database and CloudWatch logs for any instances of raw card data. Verify that all card data is tokenized by Stripe before being passed to the MealCredit platform.
  Success Criteria: Zero instances of raw card data found in the database or logs. All card references must be Stripe token IDs.

### 5.5. Validation Automation and CI/CD Integration

 Automated Validation Pipeline:
  Objective: Integrate observability validation tests into the CI/CD pipeline to ensure continuous compliance.
  Method: Add a new stage to the CI/CD pipeline that executes the validation tests defined in sections 5.1-5.4. The pipeline must fail if any validation test fails.
  Success Criteria: The CI/CD pipeline must block deployment if any observability validation test fails. The pipeline must generate a compliance report for SOC2 Type II evidence.

 Continuous Compliance Monitoring:
  Objective: Establish continuous monitoring for compliance violations.
  Method: Configure CloudWatch Alarms to trigger on any PII leakage or raw card data detection. Integrate these alarms with the incident response workflow.
  Success Criteria: Immediate alerting to the Platform Administrator (ACT-086A974D63) and Security Team in the event of a compliance violation.

### 5.7. Deliverable Summary

This validation plan provides a comprehensive framework for verifying the accuracy, integrity, and compliance of the MealCredit observability architecture. It ensures that the system can be trusted to operate at scale while maintaining the highest standards of data privacy and financial auditability.

---

## VP decision

**Decision:** Approved

---

## VP feedback

- Section 4.1.3: Convert the '7 years' retention period to KNOWLEDGE_GAP - the specific retention window must be established by the Compliance & Legal team and is not mandated by SOC2 Type II.

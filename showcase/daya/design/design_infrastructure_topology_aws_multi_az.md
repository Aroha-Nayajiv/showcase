# AWS Multi-AZ Deployment Topology

## 1. Architectural Strategy: Multi-VPC, Single-Account Hub-and-Spoke

To balance operational simplicity with strict data isolation and PCI-DSS compliance, the platform will utilize a Single AWS Account with three distinct VPCs (one per metro footprint). This approach avoids the complexity of cross-account IAM and billing while allowing for granular network boundaries.

VPC Isolation: Each metro footprint (SF, NYC, CHI) will have its own dedicated VPC. This ensures that network traffic, security groups, and routing tables are strictly localized to the respective region. Interconnectivity: A central AWS Transit Gateway (TGW) will serve as the hub, connecting all three metro VPCs. This enables secure, low-latency communication between services across metros (e.g., a NYC Beneficiary app querying a Chicago Merchant) while maintaining strict segmentation. Data Residency: All data generated within a metro VPC (e.g., Beneficiary PII, Merchant transaction logs) will remain within that VPC's boundaries unless explicitly routed for cross-metro analytics via the TGW. This supports the requirement for strict data residency and jurisdictional compliance.

## 2. Metro Footprint Topology (SF, NYC, CHI)

Each of the three metro VPCs will follow an identical, highly available topology structure.

### 2.1 Availability Zones (AZs)

Requirement: Each VPC must span at least two Availability Zones (AZs) to ensure fault tolerance against AZ-level failures.

Implementation:
SF VPC: us-west-2a, us-west-2b
NYC VPC: us-east-1a, us-east-1b
CHI VPC: us-east-2a, us-east-2b

Rationale: Spreading critical services across AZs ensures that a single AZ outage does not take down the entire metro footprint.

### 2.2 Subnet Architecture

Each VPC will be divided into Public and Private subnets, distributed across the two AZs.

Public Subnets (2 per AZ):
Purpose: Host internet-facing load balancers (ALBs) for the API Orchestration Layer and Client Interface Layer.
Routing: Route table points to an Internet Gateway (IGW).
Security: Strictly limited to ALBs. No EC2 instances or containers will be deployed directly in public subnets.

Private Application Subnets (2 per AZ):
Purpose: Host stateless services (API Orchestration, Client Interface) and stateful services (Aurora PostgreSQL, Redis) via private endpoints.
Routing: Route table points to a NAT Gateway (located in the Public Subnet) for outbound internet access (e.g., Stripe API calls, external vendor integrations).
Security: No direct inbound internet access. Access is restricted via Security Groups and NACLs.

Private Data Subnets (2 per AZ):
Purpose: Host the most sensitive components, such as the Financial Ledger and PII storage, if not fully managed by AWS (e.g., Aurora). Note: Managed services like Aurora and ElastiCache are deployed in private subnets by default.
Routing: Route table points to a NAT Gateway.
Security: Most restrictive Security Groups. Only specific application subnets can communicate with these subnets.

## 3. Critical Service Placement

### 3.2 Financial Ledger (Aurora PostgreSQL)

Deployment: Amazon Aurora PostgreSQL (Multi-AZ).
Placement: Deployed in Private Data Subnets across both AZs.
High Availability: Aurora Multi-AZ provides automatic failover to a standby replica in the secondary AZ. The primary and standby are in different AZs.
Security: Access is restricted to the API Orchestration Layer via Security Groups. No direct public access is permitted.

### 3.4 SOC2 Type II Structural Planning

Logging: AWS CloudTrail will be enabled for all API calls across the account, with logs stored in a dedicated, encrypted S3 bucket with strict access controls.
Monitoring: AWS Config will be used to continuously monitor resource configurations for compliance with predefined rules (e.g., "S3 bucket is not public," "Security group allows unrestricted SSH access").
Access Control: IAM roles and policies will follow the principle of least privilege. MFA will be enforced for all root and administrative accounts.

### 4.1 Stateless Service Orchestration (Amazon ECS Fargate)

The API Orchestration Layer and Client Interface Layer are designated as stateless services. These services handle high-throughput, low-latency requests such as GraphQL queries, REST API endpoints, and Server-Sent Events (SSE) for real-time updates.

Service Selection: Amazon ECS with Fargate launch type. Fargate eliminates the need to manage EC2 instances, reducing operational overhead and ensuring automatic scaling based on demand.
Service Boundaries:
API Orchestration Layer: Hosts the GraphQL API gateway and gRPC service proxies. This layer is responsible for routing requests to the appropriate backend services, handling authentication/authorization (deferred to Access Control & Multi-Tenant Isolation), and enforcing rate limits.
Client Interface Layer: Hosts the Next.js Edge Runtimes for web dashboards (Admin, Restaurant, NGO) and serves as the entry point for Expo mobile app API calls. This layer handles server-side rendering (SSR) and static site generation (SSG) for optimal performance.
Scaling Strategy:
Horizontal Pod Autoscaling (HPA): ECS services will be configured with target tracking scaling policies based on CPU and Memory utilization. <br> `ASSUMPTION: Initial thresholds will be set at 70% CPU and 80% Memory utilization, with a cooldown period of 60 seconds - pending capacity planning review.`
Event-Driven Scaling: For bursty traffic patterns (e.g., peak donation times), AWS EventBridge will trigger scaling events to pre-warm ECS services.
Resource Allocation:
API Orchestration Layer: <br> `ASSUMPTION: Default task size of 512 MB RAM and 256 vCPU, scalable up to 4 GB RAM and 2 vCPU per task - pending capacity planning review.`
Client Interface Layer: <br> `ASSUMPTION: Default task size of 1024 MB RAM and 512 vCPU, scalable up to 8 GB RAM and 4 vCPU per task - pending capacity planning review.`
Networking: Services will be deployed in private subnets within each metro VPC. Public access will be provided via Application Load Balancers (ALBs) in public subnets, which will terminate TLS and route traffic to the ECS services.

### 4.2 Stateful Service Orchestration (Amazon ECS Fargate)

The Transaction & Financial Engine and Fraud Detection & Fraud Prevention Screening are designated as stateful workloads. These services require strict resource isolation, persistent storage, and low-latency access to the financial ledger. To maintain architectural consistency with the project mandate, these services are also deployed via Amazon ECS Fargate.

Service Selection: Amazon ECS with Fargate launch type. This ensures a unified operational model across all platform services, simplifying IAM policies, networking, and scaling strategies.
Service Boundaries:
Transaction & Financial Engine: Hosts the core financial logic, including credit pool management, voucher issuance, and payout processing. This service interacts directly with the Aurora PostgreSQL database.
Fraud Detection & Fraud Prevention Screening: Hosts the real-time fraud detection engine, which analyzes transaction patterns and flags suspicious activities. This service requires high computational power and low-latency access to the Redis cache.
Scaling Strategy:
Horizontal Pod Autoscaling (HPA): ECS services will use HPA to scale tasks based on CPU, Memory, and custom metrics (e.g., queue depth for fraud screening).
Resource Allocation:
Transaction & Financial Engine: <br> `ASSUMPTION: Default task resource requests of 2 GB RAM and 1 vCPU, with limits of 4 GB RAM and 2 vCPU - pending capacity planning review.`
Fraud Detection & Fraud Prevention Screening: <br> `ASSUMPTION: Default task resource requests of 4 GB RAM and 2 vCPU, with limits of 8 GB RAM and 4 vCPU - pending capacity planning review.`
Storage: Persistent storage for stateful ECS Fargate tasks will be managed via Amazon EFS (Elastic File System) mounted to the task definition, or via EBS volumes attached to tasks where supported. This replaces non-applicable Kubernetes PV/PVC concepts with standard Fargate storage patterns.
Networking: Tasks will be assigned IP addresses from the VPC CIDR range using the AWS VPC CNI plugin. Security Groups will be enforced to restrict traffic between tasks, ensuring that only authorized services can communicate with the financial engine and fraud detection services.

To ensure high availability and fault tolerance, all ECS services will be deployed across multiple Availability Zones (AZs) within each metropolitan footprint.

- ECS Services: Tasks will be distributed across at least two AZs in each metro VPC. The ALB will route traffic to healthy tasks in any AZ.
- Service Discovery: AWS Cloud Map will be used for service discovery within the VPCs. ECS services will register themselves with Cloud Map, allowing other services to discover and communicate with them using DNS names.

### 4.3 Cross-Reference to Sibling Artifacts

Access Control & Multi-Tenant Isolation: This artifact defers to the Access Control & Multi-Tenant Isolation artifact for the specific IAM policies and RBAC configurations required for each service.
Data Residency & Jurisdictional Compliance: This artifact defers to the Data Residency & Jurisdictional Compliance artifact for the specific KMS key management and data encryption strategies required for each metro footprint.
Distributed Tracing & Log Aggregation: This artifact defers to the Distributed Tracing & Log Aggregation artifact for the specific OpenTelemetry and CloudWatch configurations required for monitoring ECS services.
Metrics Collection & Alerting Design: This artifact defers to the Metrics Collection & Alerting Design artifact for the specific CloudWatch alarms and dashboards required for monitoring ECS services.

## 5. Data Persistence Layer Design

This section defines the data persistence architecture for the MealCredit platform, leveraging Amazon Aurora PostgreSQL for ACID-compliant financial ledgering and Amazon DynamoDB for high-throughput transactional state management. The design ensures strict data isolation for beneficiary demographic status and legal names, aligning with the platform's compliance and trust objectives.

### 5.1 Amazon Aurora PostgreSQL: Financial Ledger

The financial ledger is the system of record for all monetary transactions, including donor contributions, credit pool allocations, and merchant payouts. It must guarantee ACID compliance and support append-only cryptographic logging for auditability.

Deployment Topology: Multi-AZ deployment across the three initial metropolitan footprints (SF, NYC, Chicago). Each region will have its own Aurora PostgreSQL cluster to ensure data residency and low-latency access for local POS transactions.
Data Isolation: Beneficiary demographic status and legal names will be stored in a separate, highly restricted schema within the Aurora PostgreSQL database. Access to this schema will be restricted to cryptographic hashing layers only, as required by compliance.
Append-Only Logging: All financial ledger mutations will be logged to an append-only table. This table will be cryptographically signed to prevent tampering and support SOC2 Type II evidence collection.
Performance: The Aurora PostgreSQL cluster will be configured for high availability and read scalability. Read replicas will be used for reporting and analytics queries to avoid impacting transactional performance.

### 5.2 Amazon DynamoDB: Transactional State Management

DynamoDB will be used for high-throughput transactional state management, including user sessions, merchant profiles, and real-time credit pool balances. This ensures low-latency responses for the Expo mobile application and Next.js dashboards.

Transactional State Management: Frequently accessed data, such as merchant profiles and restaurant search results, will be stored in DynamoDB. Session Management: User sessions for the Expo mobile application and Next.js dashboards will be stored in the Redis Enterprise Cluster. This allows for scalable and stateless session management across the platform. Data Isolation: DynamoDB tables will be partitioned by metro footprint to ensure data isolation and compliance with data residency requirements.

### 5.3 Validation Criteria

Each metro VPC has at least two subnets in different AZs.
Critical services (Aurora, Redis) are deployed in Multi-AZ.
Public subnets are isolated from private subnets via NACLs and Security Groups.
Cross-VPC traffic is routed exclusively through the Transit Gateway.
All AWS service endpoints are configured via VPC Endpoints to prevent public internet egress.
Beneficiary demographic status and legal names are stored in a separate, highly restricted schema within the Aurora PostgreSQL database.
All financial ledger mutations are logged to an append-only table that is cryptographically signed.
DynamoDB tables are partitioned by metro footprint to ensure data isolation and compliance with data residency requirements.
The cache hit ratio (CHR) for the Redis Enterprise Cluster is monitored and maintained above 92%.
User sessions for the Expo mobile application and Next.js dashboards are stored in the Redis Enterprise Cluster.
The Donation-to-Redemption Velocity (DRV) metric is tracked using regional pools implemented as physically separate DynamoDB tables per metro footprint (SF, NYC, CHI).
Cross-border data residency compliance is ensured if the platform expands beyond the initial US metro footprints.
Data Residency Validation: Each metro VPC is isolated in its designated region (SF in us-west-2, NYC in us-east-1, CHI in us-east-2) to satisfy data residency requirements.
The 'Stripe Proxy' service is deployed within each metro VPC to minimize latency and keep PCI scope contained.

### 6.1 Stripe Proxy Adapter

The Stripe Proxy Adapter is a stateless, high-throughput service deployed within each metro VPC. It acts as the sole point of contact for Stripe API interactions, ensuring that raw card data never touches MealCredit servers and that all financial transactions are processed with sub-150ms latency ([CON-06232374D9](../project_glossary.md#con-06232374d9)).

#### 6.1.1. Interface Contract

The Stripe Proxy Adapter exposes a gRPC service interface (defined in sibling artifact `gRPC Service Contracts & Definitions`). Key methods include:

ProcessPayment(PaymentRequest) -> PaymentResponse: Initiates a payment via Stripe PaymentIntent. Input: PaymentRequest contains merchant_id, amount, currency, tokenized_card_data (from Stripe Elements), and beneficiary_id (hashed). Output: PaymentResponse contains payment_intent_id, status (succeeded, failed, requires_action), and ledger_entry_id. Error Handling: Returns INVALID_TOKEN if the tokenized data is malformed; STRIPE_API_ERROR for upstream failures, triggering a retry with exponential backoff (max 3 retries).

HandleWebhook(WebhookEvent) -> AckResponse: Processes Stripe webhook events (e.g., payment_intent.succeeded, charge.failed). Security: Validates the Stripe signature using the webhook secret stored in AWS Secrets Manager. Rejects any request with an invalid signature. Idempotency: Uses the idempotency_key from the webhook payload to prevent duplicate ledger entries. If a duplicate event is detected, returns `200 OK` without processing.

#### 6.1.2. Operational Behavior

Latency SLA: <br> `KNOWLEDGE_GAP: The exact p99 latency requirement for the Stripe Proxy Adapter is not established in the project requirement; the requirement specifies average webhook latency below 150ms (CON-06232374D9). The specific p99 target must be defined by the performance engineering team.`
Retry Logic: For transient errors (e.g., RATE_LIMIT_EXCEEDED), the adapter implements exponential backoff with jitter. For permanent errors (e.g., CARD_DECLINED), it returns the error to the caller immediately.
Observability: All requests and responses are logged to AWS CloudWatch Logs with structured JSON format. Metrics are exported to CloudWatch for monitoring ([SUR-BE18433C9C](../project_glossary.md#sur-be18433c9c)).

### 7.1 Logging Strategy

Structured Logging: All services (ECS Fargate, Aurora, DynamoDB) will emit structured JSON logs to AWS CloudWatch Logs. Logs will include trace IDs, service names, and severity levels.
Centralized Aggregation: CloudWatch Logs will be aggregated into a central S3 bucket for long-term retention and compliance auditing. Access to these logs will be restricted via IAM policies.
Audit Trails: AWS CloudTrail will capture all API calls made to AWS services, providing an immutable audit trail for SOC2 Type II compliance.

### 7.2 Alerting and Incident Response

CloudWatch Alarms: Alarms will be configured for critical thresholds (e.g., high error rates, low CHR, high latency). These alarms will trigger notifications via Amazon SNS.
Incident Response: In the event of a critical failure, the platform will automatically scale resources (if possible) and notify the Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) via SMS and email.
Disaster Recovery: Automated failover procedures will be tested regularly to ensure that the platform can recover from AZ or region-level failures within the defined RTO and RPO targets.

## 8. Architectural Overview

This document defines the AWS multi-AZ deployment topology for the MealCredit platform. The architecture is designed to transition from a single-city MVP to a resilient, event-driven, serverless hybrid system optimized for 50,000 active users across three initial metropolitan footprints: San Francisco (SF), New York City (NYC), and Chicago (CHI).

The topology leverages a multi-tenant architecture with strict data isolation, ensuring that beneficiary demographic status and legal names are cryptographically segregated from public analytics. The system relies on the `API Orchestration Layer` ([SUR-85E4A5B6E7](../project_glossary.md#sur-85e4a5b6e7)) and `Client Interface Layer` ([SUR-43E71C4E2B](../project_glossary.md#sur-43e71c4e2b)) to manage high-throughput GraphQL queries and gRPC financial service calls, while the `Payment Processing Surface` ([SUR-5B18C8719F](../project_glossary.md#sur-5b18c8719f)) handles external integrations with Stripe.

### 8.1 Core Design Principles
- **High Availability:** Critical services are deployed across multiple Availability Zones (AZs) within each metro region to ensure fault tolerance.
- **Data Isolation:** Multi-tenancy is enforced at the database and network layer to comply with FTC Anonymity Guidelines and PCI-DSS Level 1 requirements.
- **Event-Driven Decoupling:** Asynchronous communication via Amazon EventBridge and SQS ensures that financial ledger updates do not block real-time POS clearance.
- **Security by Design:** Zero raw card data touches MealCredit servers. All sensitive data is encrypted at rest and in transit, with access controlled via AWS IAM and Cognito.

## 9. Network Topology & Isolation

To support the three metropolitan footprints, the platform utilizes a hub-and-spoke network architecture with dedicated VPCs for each metro region.

### 9.1 Metro-Specific VPCs
Each metro footprint (SF, NYC, CHI) has its own dedicated Amazon VPC. This ensures network-level isolation and allows for localized data residency compliance.
- **Subnets:** Each VPC contains public subnets (for NAT Gateways and load balancers) and private subnets (for ECS tasks, RDS instances, and ElastiCache clusters) spread across at least two AZs.
- **Interconnectivity:** VPC Peering or AWS Transit Gateway is used to allow secure communication between metro VPCs for centralized logging and cross-metro analytics, while maintaining strict data boundaries.
- **Security Groups:** Strict ingress/egress rules are applied to ensure that only authorized services can communicate. For example, the `API Orchestration Layer` can only communicate with the `Payment Processing Surface` and the `Data Persistence Layer` ([SUR-FA61592CD4](../project_glossary.md#sur-fa61592cd4)).

## 10. Compute & Application Layer

The application layer is composed of microservices deployed on Amazon ECS Fargate, providing serverless container orchestration that scales automatically with demand.

### 10.1 Payment Processing Surface (SUR-5B18C8719F)
- **Service:** gRPC financial service handling Stripe Issuing and Stripe Connect integrations.
- **Deployment:** Deployed in multiple AZs within each metro VPC.
- **Security:** This service is placed in private subnets and only accessible via the API Orchestration Layer. It uses IAM roles for service-to-service authentication.
- **Resilience:** Implements retry logic with exponential backoff for external Stripe API calls.

### 10.2 Client Interface Layer (SUR-43E71C4E2B)
- **Service:** Next.js dashboards for NGO Operators and Platform Administrators.
- **Deployment:** Hosted on AWS Amplify or S3 + CloudFront for global low-latency access.
- **Authentication:** Secured via Amazon Cognito User Pools, integrating with the `Platform Administrator` (ACT-086A974D63) and `NGO Operator` ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) roles.

### 11.1 Aurora PostgreSQL (SUR-FA61592CD4)
- **Role:** Primary relational database for financial ledger, user profiles, and transaction history.
- **Deployment:** Multi-AZ deployment with a primary instance in one AZ and a standby in another for automatic failover.
- **Read Replicas:** Read replicas are used to offload read-heavy queries from the API Orchestration Layer.
- **Encryption:** Data at rest is encrypted using AWS KMS keys. Connection strings are stored in AWS Secrets Manager.

### 11.2 DynamoDB
- **Role:** High-throughput NoSQL database for user states, geo-indexing, and session management metadata.
- **Deployment:** Global tables are used to replicate data across regions if needed, but primary writes are localized to the metro VPC.
- **Indexing:** Global Secondary Indexes (GSIs) are used to optimize queries for beneficiary location and merchant proximity.

### 11.3 Redis Enterprise Cluster (SUR-5B18C8719F)
- **Role:** In-memory data store for session management, caching frequently accessed merchant data, and managing the `Credit Pool Utilization Rate` ([CON-2059B17FB2](../project_glossary.md#con-2059b17fb2)).
- **Deployment:** Multi-AZ cluster mode enabled for high availability.
- **Security:** Access is restricted to the API Orchestration Layer and Payment Processing Surface via security groups.
- **Observability:** Cache Hit Ratio (CHR) is monitored to ensure performance targets are met.

## 12. Observability and Monitoring Framework

This section defines the operational visibility architecture for the MealCredit platform, ensuring real-time tracking of financial liquidity, system health, and compliance evidence across the three metropolitan footprints (SF, NYC, Chicago). The framework is designed to support the 50,000 MAU target while maintaining strict data isolation and PCI-DSS Level 1 compliance.

### 12.1 Administrative Logging and Compliance Evidence (AWS CloudTrail)

To satisfy SOC2 Type II structural planning and provide an immutable audit trail for all administrative actions, AWS CloudTrail will be configured as the central logging authority for control plane operations.

**Scope of Logging:** CloudTrail will be enabled across all three metro VPCs (SF, NYC, CHI) and centralized in a dedicated `Security & Audit` VPC. All API calls made to AWS services (EC2, RDS, Lambda, S3, KMS) by the `Platform Administrator` (ACT-086A974D63) and `NGO Operator` (ACT-09E028AEB0) roles will be captured.

**Data Integrity:** To prevent tampering with audit logs, CloudTrail logs will be delivered to an S3 bucket with Object Lock enabled in Compliance Mode. This ensures that logs cannot be deleted or modified for a configurable retention period, satisfying the requirement to `Log all administrative ledger operations and infrastructure changes to AWS CloudTrail for SOC2 Type II evidence` ([CON-BB253DF0A2](../project_glossary.md#con-bb253df0a2)).

**Access Control:** Access to the CloudTrail log bucket will be restricted via S3 Bucket Policies to only the `Platform Administrator` role and the automated compliance scanning service. No other actor, including Merchant ([ACT-AF904DCFF9](../project_glossary.md#act-af904dcff9)) or Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)), will have read access to these logs.

**Integration:** CloudTrail Insights will be enabled to detect unusual control plane activity, such as repeated failed login attempts or unauthorized changes to IAM policies, triggering immediate alerts to the security team.

### 12.2 Application Metrics and Health Monitoring (Amazon CloudWatch)

Amazon CloudWatch will serve as the primary metrics collection and alerting engine for the platform's application layer, focusing on the performance of the `API Orchestration Layer` (SUR-85E4A5B6E7) and the `Payment Processing Surface` (SUR-5B18C8719F).

**Custom Metrics:** The platform's microservices (deployed via Amazon ECS Fargate) will publish custom metrics to CloudWatch using the PutMetricData API. Key metrics include:
- **POS_Clearance_Latency:** The time taken from a Beneficiary scanning a voucher to the Merchant receiving confirmation. This directly supports the requirement to `Ensure Stripe Webhook Processing Latency averages below 150ms from card tap to merchant ledger entry` (CON-06232374D9).
- **Credit_Pool_Utilization_Rate:** A percentage metric representing the ratio of active credits to total donated funds per metro region. This supports the requirement to `Monitor Credit Pool Utilization Rate with automated alerts triggering when thresholds exceed 85%` (CON-2059B17FB2).
- **Donation_to_Redemption_Velocity (DRV):** A rate metric tracking the speed at which donated funds are converted into redeemed credits. This supports the requirement to `Track Donation-to-Redemption Velocity (DRV) to monitor liquidity health against the 14-day target` ([CON-D0F5814F21](../project_glossary.md#con-d0f5814f21)).
- **Voucher_Scan_Success_Rate:** The percentage of successful voucher scans vs. total attempts, used to detect potential fraud or system errors.

**Alarms and Notifications:** CloudWatch Alarms will be configured for each critical metric. When a threshold is breached (e.g., POS Latency > 200ms for 5 consecutive minutes), an SNS topic will trigger notifications to the on-call engineering team via PagerDuty and to the `Platform Administrator` via email. For Credit_Pool_Utilization_Rate, an alarm at 85% will trigger a warning, and an alarm at 95% will trigger a critical alert, potentially triggering automated fund top-up workflows (if defined in the Financial Reconciliation artifact).

**Log Aggregation:** Application logs from ECS tasks and Lambda functions will be streamed to CloudWatch Logs. Log groups will be organized by service (e.g., `/mealcredit/api-orchestration`, `/mealcredit/payment-proxy`). Log retention will be set to 90 days for operational debugging, with a copy of critical error logs forwarded to S3 for long-term archival.

### 12.3 Operational Dashboards and Business Intelligence

To provide real-time visibility into the platform's health and business performance, custom CloudWatch Dashboards will be created for different stakeholder groups.

**Platform Operations Dashboard:** This dashboard will be accessible to the `Platform Administrator` and engineering teams. It will display:
- Real-time POS Latency (p50, p95, p99) across all three metros.
- System Uptime and Error Rates (5xx responses) for all microservices.
- CloudTrail Insights alerts and security events.
- Infrastructure resource utilization (CPU, Memory, Network) for ECS tasks and RDS instances.

**Business Intelligence Dashboard:** This dashboard will be accessible to `NGO Operators` and Donors ([ACT-80C62C7814](../project_glossary.md#act-80c62c7814)) in a read-only, anonymized format. It will display:
- Credit_Pool_Utilization_Rate per metro region, with a visual indicator for the 85% threshold.
- Donation-to-Redemption Velocity (DRV) trends over the last 14 days.
- Total number of Beneficiary redemptions and Merchant partners active per region.

*Note: All data in this dashboard will be aggregated and anonymized to comply with `FTC guidelines on anonymity` ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d)) and `strict data isolation` ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4)). No PII or individual beneficiary data will be visible.*

**Merchant Dashboard:** A simplified view for Merchant partners will show their daily redemption volume, average clearance latency, and payout status (deferred to the Financial Reconciliation artifact for payout details).

### 12.4 Data Residency and Isolation in Observability

To ensure compliance with data residency requirements, CloudWatch metrics and logs will be scoped to individual metro VPCs where possible. Cross-region metric aggregation will be handled by a centralized CloudWatch Dashboard in a single region (e.g., us-east-1), but the underlying data will remain in the source region. CloudTrail logs will be centralized for audit purposes, but access to these logs will be strictly controlled to prevent cross-region data leakage.

### 12.5 Knowledge Gaps and Assumptions

- **KNOWLEDGE_GAP: Alert Escalation Policy** - The specific escalation matrix (who gets notified at which severity level) and the integration with PagerDuty or similar tools must be established by the Platform Operations team.
- **KNOWLEDGE_GAP: Log Retention Policy** - The exact retention period for CloudTrail logs (beyond the 90-day operational window) and the archival strategy (e.g., S3 Glacier) must be defined by the Compliance team to meet SOC2 Type II requirements.
- **ASSUMPTION: CloudWatch Custom Metrics** - The platform's microservices will be instrumented with a standard metrics library (e.g., AWS X-Ray or OpenTelemetry) to publish custom metrics to CloudWatch. This is a standard practice for ECS Fargate and Lambda deployments.
- **ASSUMPTION: Dashboard Access Control** - Access to the Business Intelligence Dashboard will be managed via Cognito User Pools, with roles mapped to `NGO Operator` and Donor groups. This defers to the Access Control & Multi-Tenant Isolation artifact for detailed IAM policies.

## 13. Integration Adapters & Offline Fallback

#### 6.2.1. Interface Contract
The Offline Token Adapter exposes a RESTful API interface. Key endpoints include:

- **`POST /v1/tokens`:** Generates a new QR code token. Input: `GenerateTokenRequest` contains `beneficiary_id` (hashed), `merchant_id`, and `amount` (optional, for capped redemptions). Output: `GenerateTokenResponse` contains `qr_code_data` (base64-encoded QR string), `token_id`, and `expires_at` (ISO 8601 timestamp). Error Handling: Returns `400 BAD_REQUEST` if the beneficiary is inactive or has insufficient credits. Returns `500 INTERNAL_SERVER_ERROR` if KMS signing fails.
- **`POST /v1/verify`:** Verifies a QR code token (for online verification). Input: `VerifyTokenRequest` contains `token_id` and `merchant_id`. Output: `VerifyTokenResponse` contains `is_valid`, `beneficiary_id` (hashed), and `amount`. Idempotency: Uses a DynamoDB table to track redeemed tokens. If a token is already redeemed, returns `409 CONFLICT`.

#### 6.2.2. Operational Behavior
- **Token Lifecycle:**
  1. **Generation:** Beneficiary app requests a token via the API Orchestration Layer, which calls the Offline Token Adapter.
  2. **Redemption:** Merchant POS scans the QR code. If online, it calls the Verify endpoint. If offline, it validates the signature locally using the public key.
  3. **Reconciliation:** Redeemed tokens are synced to the central ledger when connectivity is restored. The Offline Token Adapter queues sync events in an Amazon SQS queue for eventual consistency.
- **Security:** Tokens are signed using HMAC-SHA256 with a rotating key (rotated every 24 hours via AWS KMS). POS systems must cache the latest public key and validate the signature before accepting a token.
- **Observability:** All token generation and verification events are logged to CloudWatch. Metrics include `TokenGenerationRate`, `TokenVerificationSuccessRate`, and `TokenReconciliationLag`.

### 13.1 Cross-Adapter Coordination

Both adapters must coordinate to ensure consistency in the financial ledger:
- **Event-Driven Sync:** Both adapters publish events to an Amazon EventBridge bus. The Financial Ledger Worker (sibling artifact) subscribes to these events to update the ledger.
- **Conflict Resolution:** In the event of a discrepancy between the Stripe Proxy and Offline Token Adapter (e.g., a token is redeemed twice), the Financial Ledger Worker uses the append-only log (sibling artifact `Financial Ledger Data Model`) to resolve conflicts based on the earliest valid timestamp.

## 14. Disaster Recovery & Business Continuity

### 14.2 Failover Procedures
- **Multi-AZ Failover:** AWS RDS and ElastiCache automatically handle AZ failures. The failover time is typically less than 60 seconds.
- **Multi-Region Failover:** In the event of a complete region outage, DNS routing via Amazon Route 53 will be updated to direct traffic to the secondary region. This process is manual but scripted to minimize downtime.

### 14.3 Recovery Time Objective (RTO) and Recovery Point Objective (RPO)
- **RTO:** < 1 hour for critical services (API, Payment Processing).
- **RPO:** < 5 minutes for financial transactions (due to event-driven architecture and frequent syncing).

### 14.4 Identity and Access Management (IAM)
- **Least Privilege:** IAM roles and policies are defined with the minimum permissions required for each service.
- **Role-Based Access Control (RBAC):** Access to the platform is controlled via Cognito User Pools, mapping users to roles such as `Platform Administrator` (ACT-086A974D63), `NGO Operator` (ACT-09E028AEB0), `Donor` (ACT-80C62C7814), `Beneficiary` (ACT-ADA6716160), and `Merchant` (ACT-AF904DCFF9).

### 14.5 Data Encryption
- **At Rest:** All data in Aurora PostgreSQL, DynamoDB, and S3 is encrypted using AWS KMS keys.
- **In Transit:** All communication between clients and the API, and between microservices, is encrypted using TLS 1.2 or higher.

## 15. Conclusion

This AWS Multi-AZ Deployment Topology provides a robust, scalable, and secure foundation for the MealCredit platform. By leveraging AWS managed services and adhering to strict security and compliance standards, the platform is well-positioned to support its mission of decoupling food assistance from social stigma while serving 50,000 active users across three metropolitan footprints.

## 16. References

- **Project Requirement:** Build Daya - a tripartite, social-impact fintech marketplace platform (product name: MealCredit).
- **System Blueprint:** AWS multi-AZ deployment, PCI-DSS Level 1, SOC2 Type II.
- **SoftwareDNA:** Pseudo-AnonymousRedemptionEngine, DonorModule, BeneficiaryModule, MerchantModule, NGOCentralCommand.
- **Canonical IDs:** ACT-086A974D63, ACT-09E028AEB0, [ACT-7BA340FF76](../project_glossary.md#act-7ba340ff76), ACT-80C62C7814, ACT-ADA6716160, ACT-AF904DCFF9, CON-06232374D9, CON-2059B17FB2, CON-D0F5814F21, CON-BB253DF0A2, SUR-85E4A5B6E7, SUR-5B18C8719F, SUR-43E71C4E2B, SUR-FA61592CD4.
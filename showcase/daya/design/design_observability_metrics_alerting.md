# MealCredit Metrics Collection & Alerting Design

This artifact defines the metrics collection, alerting thresholds, and observability strategy for the MealCredit platform. It establishes the Key Performance Indicators (KPIs) and automated alerts required to monitor system health, financial integrity, and compliance across the three initial metropolitan footprints (SF, NYC, Chicago). This design ensures that the platform can maintain PCI-DSS Level 1 compliance, SOC2 Type II structural planning, and absolute anonymization of beneficiary data while scaling to 50,000 MAU.

## 1. Architectural Surface & Observability Strategy

The observability strategy is built upon the established architectural surfaces, ensuring that metrics are collected at the precise boundaries where data crosses trust zones or undergoes transformation.

### 1.1 API Orchestration Layer (SUR-85E4A5B6E7)
Metrics for the API Orchestration Layer focus on latency, throughput, and error rates for the GraphQL and gRPC endpoints. This layer acts as the primary ingress point for Beneficiary ([ACT-ADA6716160](../project_glossary.md#act-ada6716160)) mobile clients and Platform Administrator ([ACT-086A974D63](../project_glossary.md#act-086a974d63)) dashboards.

*   **Latency Monitoring:** p99 latency for GraphQL queries must be tracked to ensure responsiveness for the location-aware allocation engine. gRPC calls to the financial engine must be monitored for timeouts.
*   **Throughput:** Request counts per target are monitored to trigger auto-scaling for the ECS Fargate services hosting this layer.
*   **Error Rates:** HTTP 4xx and 5xx error rates are aggregated to detect systemic failures or specific endpoint degradation.

### 1.2 Payment Processing Surface (SUR-5B18C8719F)
This surface encompasses the Stripe Proxy Adapter and the Pseudo-Anonymous Redemption Engine. Metrics here are critical for PCI-DSS Level 1 compliance and financial integrity.

*   **Stripe Webhook Processing Latency:** The time from receiving a Stripe webhook event to processing it internally must average below 150ms ([CON-06232374D9](../project_glossary.md#con-06232374d9), [CON-A0B785A40D](../project_glossary.md#con-a0b785a40d)). Delays here directly impact the speed of donor impact receipts and merchant payouts.
*   **Token Provisioning Latency:** The time to generate a single-use virtual card token via Stripe Issuing API must be tracked to ensure it does not bottleneck the POS clearance flow.
*   **PCI-DSS Compliance Events:** Any attempt to log raw card data or access restricted fields outside of authorized roles is logged as a critical security metric.

### 1.3 Data Persistence Layer (SUR-FA61592CD4)
Metrics for the Data Persistence Layer focus on database health, query performance, and data integrity.

*   **Aurora PostgreSQL Performance:** Connection pool utilization, query latency, and replication lag are monitored. The append-only cryptographic log auditing ([CON-1762EA5021](../project_glossary.md#con-1762ea5021), [CON-6061FCCA83](../project_glossary.md#con-6061fcca83)) must be verified for completeness.
*   **DynamoDB Performance:** Read/write capacity utilization and throttling events are tracked. The Cache Hit Ratio (CHR) for restaurant search queries must be maintained above 92% ([CON-527BFA6796](../project_glossary.md#con-527bfa6796), [CON-EA7C3EFECB](../project_glossary.md#con-ea7c3efecb)).
*   **Data Isolation:** Access logs to the segregated beneficiary demographic data table are monitored to ensure only authorized NGO Operators ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) and Platform Administrators (ACT-086A974D63) access this data.

### 2.1 Critical Alerts

*   **Credit Pool Utilization > 85%:** Triggers an immediate alert to the Platform Administrator (ACT-086A974D63) and financial operations team. Requires manual review of donor funding rates and beneficiary redemption patterns.
*   **POS Clearance Latency p99 > 250ms:** Indicates a systemic performance issue in the payment processing surface or data persistence layer. Requires immediate investigation to prevent merchant frustration and beneficiary experience degradation.
*   **Cross-Region PII Transfer Detected:** Any attempt to transfer beneficiary demographic data across metropolitan footprints triggers a critical security alert. This is a potential compliance violation and requires immediate isolation of the affected service.
*   **Append-Only Ledger Integrity Failure:** If the cryptographic hash-checksums of the Aurora PostgreSQL financial ledger do not match expected values, a critical alert is triggered. This indicates potential data corruption or tampering.

## 3. Data Retention & Archival

*   **Financial Ledger Data:** Retained indefinitely in Aurora PostgreSQL for audit and compliance purposes, in accordance with PCI-DSS Level 1 and SOC2 Type II requirements.
*   **Beneficiary Demographic Data:** Retained only for the duration of the beneficiary's active status and any required legal hold periods. Upon offboarding by an NGO Operator (ACT-09E028AEB0), all PII is cryptographically purged from operational logs ([JNY-4C4BA15817](../project_glossary.md#jny-4c4ba15817)).
*   **Analytics Data:** Anonymized redemption and donation data is retained for historical trend analysis and impact reporting. PII is never included in these datasets.
*   **Audit Logs:** AWS CloudTrail logs are retained for a minimum of 7 years to satisfy SOC2 Type II and financial regulatory requirements.

## 4. Integration with Sibling Artifacts

*   **System Topology:** This metrics design relies on the AWS Multi-AZ deployment topology defined in the System Topology artifact. Metrics are collected per metropolitan footprint (SF, NYC, Chicago) to ensure data residency compliance.
*   **Integration Adapters:** The Stripe Proxy Adapter and Offline Token Adapter emit metrics that are ingested by this design. Specific adapter contracts are defined in the Integration Adapters artifact.
*   **Compliance, Security & Audit:** This metrics design supports the compliance requirements defined in the Compliance, Security & Audit artifact, particularly regarding data isolation, anonymization, and audit logging.

## 5. Validation Criteria

*   All financial transactions are recorded in an append-only manner in Aurora PostgreSQL, with metrics tracking the integrity of this log.
*   Beneficiary demographic status and legal names are cryptographically segregated, and access to this data is monitored via metrics.
*   Cache Hit Ratio (CHR) for restaurant search queries is monitored and alerts are triggered if it falls below 90%.
*   Credit Pool Utilization Rate alerts trigger when thresholds exceed 85%.
*   All data is encrypted at rest and in transit, with metrics verifying the status of encryption keys and certificates.
*   Data residency requirements are met for all three metropolitan footprints, with metrics tracking cross-region data transfers.
*   POS clearance latency is monitored and alerts are triggered if p99 latency exceeds 250ms.
*   Stripe webhook processing latency is monitored and alerts are triggered if average latency exceeds 150ms.

## 6. Knowledge Gaps & Assumptions

*   **KNOWLEDGE_GAP:** The exact retention period for anonymized analytics data is not specified in the project requirement. This must be established by the Compliance, Security & Audit artifact to ensure alignment with FTC Anonymity Guidelines and long-term business needs.
*   **KNOWLEDGE_GAP:** The specific thresholds for "Warning" level alerts for DynamoDB throttling events are not defined. This requires input from the infrastructure team to determine acceptable levels of throttling before it impacts user experience.
*   **ASSUMPTION:** The Pseudo-Anonymous Redemption Engine routes POS clearing exclusively through real-time Stripe Issuing virtual card provisioning, with deterministic HMAC-signed fallback voucher systems for low-latency/high-availability scenarios. This assumption is reversible pending resolution of the decision in the Envisioning phase.
*   **ASSUMPTION:** The 'Regional Pool' for Donation-to-Redemption Velocity (DRV) metric is implemented as a logical isolation layer within a single DynamoDB table, partitioned by metro footprint. This assumption is reversible pending resolution of the decision in the Envisioning phase.

## 7. Executive Summary & Scope

This artifact defines the metrics collection, alerting thresholds, and log aggregation strategy for the MealCredit platform. It establishes the Key Performance Indicators (KPIs) required to monitor platform health, financial liquidity, and compliance posture across the three initial metropolitan footprints (SF, NYC, Chicago). 

**Scope Boundaries:**
- **In-Scope:** CloudWatch metrics configuration, custom business logic metrics, alerting severity definitions, log aggregation strategy, and compliance audit logging (CloudTrail).
- **Out-of-Scope:** Infrastructure topology (System Topology artifact), Integration Adapter implementation contracts (Integration Adapters artifact), and detailed UI/UX dashboard rendering (UI/UX artifact).

## 8. Key Performance Indicators (KPIs)

The following KPIs are critical for monitoring the health and performance of the MealCredit platform. These metrics map directly to the implied concerns and system evolution objectives defined in the project blueprint.

| KPI Name | Definition / Business Context | Target / Threshold | Data Source / Service |
| :--- | :--- | :--- | :--- |
| **Stripe Webhook Latency** | Time from card tap to merchant ledger entry. Measures the speed of the financial rail. | Average < 150ms | Stripe Proxy Adapter |
| **POS Clearance Latency** | p99 latency for voucher creation and scanning callbacks. Ensures queue stagnation is prevented. | p99 < 250ms | Offline Token Adapter |
| **Cache Hit Ratio (CHR)** | Ratio of cache hits to total requests for restaurant search. Indicates search engine efficiency. | > 92% | ElastiCache (Redis) |
| **Credit Pool Utilization** | Percentage of total donor funds currently allocated as credits. Monitors liquidity health. | Alert if > 85% | DynamoDB (Metrics Table) |
| **Donation-to-Redemption Velocity (DRV)** | Time taken for donated funds to be redeemed by beneficiaries. Tracks liquidity flow. | Monitor against 14-day target | Financial Ledger (Aurora) |
| **Operational Uptime** | Percentage of time critical service endpoints are available. | 99.99% | AWS CloudWatch |
| **PCI-DSS Compliance Score** | Automated scan results for raw card data exposure. | 100% (Zero violations) | Stripe Proxy Adapter |

### 9.1 Severity Definitions

| Severity | Definition | Notification Channel | Primary Owner |
| :--- | :--- | :--- | :--- |
| **P1 (Critical)** | Operational Uptime < 99.99% for > 5 minutes; PCI-DSS Compliance Violation Detected. | PagerDuty, SMS, Email | Platform Administrator (ACT-086A974D63) |
| **P2 (High)** | Credit Pool Utilization > 85%; Stripe Webhook Latency > 150ms (Average) for > 10 minutes. | Slack, Email | Platform Administrator (ACT-086A974D63) |
| **P3 (Medium)** | Cache Hit Ratio (CHR) < 92% for > 30 minutes; POS Clearance Latency p99 > 250ms for > 15 minutes. | Slack | Platform Administrator (ACT-086A974D63) |

### 9.2 Alert Routing Logic

- **PagerDuty Integration:** Configured for P1 alerts only. Ensures immediate human intervention for system-wide outages or compliance breaches.
- **Slack Integration:** Configured for P2 and P3 alerts. Routes to the `#platform-engineering` and `#ops-alerts` channels for visibility and asynchronous triage.
- **Email Integration:** Configured for P1 and P2 alerts. Provides a persistent audit trail for high-severity events.

### 10.1 Log Aggregation Strategy

All application logs, access logs, and audit logs are aggregated into a central logging service to enable real-time querying and historical analysis.

- **Aggregation Service:** AWS CloudWatch Logs is the primary aggregation layer for application and infrastructure logs.
- **Structured Logging:** All services emit structured JSON logs containing `timestamp`, `service`, `trace_id`, `user_id` (anonymized for beneficiaries), `event_type`, `status`, `latency_ms`, and `metro_region`.
- **Distributed Tracing:** `trace_id` is propagated across all services (via gRPC and GraphQL) to enable end-to-end request tracing, linking donor transactions to merchant redemptions.

### 10.2 Long-Term Storage & Retention

- **Retention Period:** Logs are retained for a minimum of 1 year for SOC2 Type II compliance.
- **Querying:** Logs are indexed for real-time querying using CloudWatch Logs Insights.
- **KNOWLEDGE_GAP:** The exact retention period for donor transaction history vs. anonymous redemption analytics is not explicitly defined in the project requirement. This decision must be made by the Platform Administrator in consultation with legal and compliance teams.

### 11.1 Scope of Logging

- **Management Events:** All API calls made to AWS services (e.g., ECS task definitions, Aurora parameter changes, IAM role assumptions) will be logged.
- **Data Events:** Critical data-plane events for Amazon S3 (access to donor impact receipts and anonymized analytics buckets) and Amazon Aurora PostgreSQL (access to the financial ledger) will be enabled.
- **Multi-Region Aggregation:** CloudTrail will be configured as a Multi-Region Trail, aggregating logs from all three metro VPCs into a single, centralized, immutable S3 bucket in a dedicated "Security & Compliance" AWS account (or isolated S3 bucket with strict bucket policies) to prevent tampering.

### 11.2 Retention and Integrity

- **Retention Period:** Logs will be retained for a minimum of [KNOWLEDGE_GAP: retention_period - Compliance/Security team must establish this based on SOC2 Type II and financial regulatory requirements].
- **Integrity:** S3 Object Lock will be enabled in "Compliance" mode to ensure logs cannot be deleted or overwritten for the duration of the retention period.

### 11.3 Key Administrative Entities Monitored

- **Platform Administrator (ACT-086A974D63):** All actions related to system configuration, fund pool adjustments, and global platform settings.
- **NGO Operator (ACT-09E028AEB0):** Actions related to beneficiary eligibility updates, onboarding, and offboarding.
- **Dispute Adjudicator ([ACT-7BA340FF76](../project_glossary.md#act-7ba340ff76)):** Actions related to dispute resolution, chargeback management, and transaction reversals.

## 12. Application Performance Monitoring (Amazon CloudWatch)

Amazon CloudWatch will serve as the primary metrics collection and alerting engine for the platform's microservices, infrastructure, and custom business logic. Metrics will be collected at a 1-minute granularity for real-time visibility, with detailed monitoring enabled for critical services.

### 12.1 Alerting Strategy

- **Severity Levels:**
  - **P1 (Critical):** Service down, data integrity risk, PCI-DSS compliance breach. Immediate PagerDuty notification to On-Call Engineer and Platform Administrator.
  - **P2 (High):** Degraded performance (latency > 500ms), high error rates (> 1%), resource exhaustion. Slack notification to Engineering Channel and On-Call Engineer.
  - **P3 (Medium):** Non-critical service degradation, unusual but non-blocking patterns. Daily digest report.
- **Thresholds:** Specific numerical thresholds for CPU, Memory, and Latency will be established based on load testing results. [KNOWLEDGE_GAP: specific_cpu_memory_thresholds - Engineering team must establish these based on load testing results].

### 12.2 Dashboard 1: Credit Pool Utilization Rate

- **Purpose:** Monitor the health of the anonymous credit distribution engine and prevent liquidity crises.
- **Key Metrics:**
  - Credit Pool Utilization Rate: (Total Credits Redeemed / Total Credits Distributed) * 100. Alert threshold: 85% ([CON-2059B17FB2](../project_glossary.md#con-2059b17fb2), [CON-7031BE57B3](../project_glossary.md#con-7031be57b3)).
  - Credits Distributed per Metro: SF, NYC, Chicago.
  - Credits Redeemed per Metro: SF, NYC, Chicago.
  - Pending Reconciliation: Number of transactions pending financial reconciliation.
- **Visualization:** Time-series graph for utilization rate, bar chart for credits distributed/redeemed per metro.

### 12.3 Dashboard 2: Donation-to-Redemption Velocity (DRV)

- **Purpose:** Track the liquidity health and donor impact velocity against the 14-day target.
- **Key Metrics:**
  - DRV (Days): Average time from donor contribution to beneficiary redemption. Target: 14 days ([CON-D0F5814F21](../project_glossary.md#con-d0f5814f21), [CON-F89C70071E](../project_glossary.md#con-f89c70071e)).
  - Donation Volume: Total donations received per day/week/month.
  - Redemption Volume: Total redemptions per day/week/month.
  - Donor Impact Receipts Generated: Number of anonymized impact receipts sent to donors.
- **Visualization:** Time-series graph for DRV, line chart for donation vs. redemption volume.

### 12.4 Dashboard 3: Platform Health & Compliance

- **Purpose:** Ensure PCI-DSS Level 1 compliance and SOC2 Type II structural planning.
- **Key Metrics:**
  - PCI-DSS Compliance Score: [KNOWLEDGE_GAP: pci_dss_compliance_score_metric - Compliance team must define how this score is calculated and tracked].
  - SOC2 Type II Audit Events: Number of audit events logged in the last 24 hours.
  - Anonymization Success Rate: Percentage of beneficiary redemptions successfully anonymized before analytics storage.
  - Data Residency Compliance: Number of cross-region data access attempts (should be zero).
- **Visualization:** Gauge chart for compliance score, bar chart for audit events, line chart for anonymization success rate.
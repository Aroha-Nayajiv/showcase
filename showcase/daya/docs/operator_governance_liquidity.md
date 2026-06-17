# Operator Governance & Liquidity

### 1.0 Operator Governance & Liquidity Management

This artifact defines the Operator (ACT-FE96DD3975) product interface for the OperatorGovernance&LiquidityManagement (JNY-039CC03FAB) journey. The Operator is responsible for the financial health, liquidity stability, and operational compliance of the MealCredit platform across the three initial metropolitan footprints: San Francisco (SF), New York City (NYC), and Chicago (Chicago).

The primary objective is to provide real-time visibility into the Donation-to-Redemption Velocity (DRV) and Credit Pool Utilization Rate, enabling proactive liquidity management and automated alerting to prevent service degradation or ledger stagnation. All Operator actions are governed by strict Identity & Access Management (CAP-361A59708B) and logged in an append-only, cryptographic audit ledger (CON-199A4FEDC7) to satisfy SOC2 Type II compliance.

### 2.0 Core Dashboard: Credit Pool Liquidity Overview

The Operator dashboard serves as the single pane of glass for monitoring the financial ecosystem. It aggregates data from the Core Transaction & Ledger Service (SUR-DD602DB92C) and presents it in a clear, actionable format.

#### 2.1 Regional Liquidity Aggregation
The dashboard must display real-time credit pool balances and utilization rates for each of the three metro areas. This allows the Operator to identify regional imbalances and trigger targeted interventions.

| Metric | San Francisco (SF) | New York City (NYC) | Chicago (CHI) |
| :--- | :--- | :--- | :--- |
| Current Pool Balance | $[Value] |  |  |
| Utilization Rate | [Value]% |  |  |
| DRV (Days) | [Value] |  |  |
| Status | Normal | Normal | Normal |

*Note: Exact currency values and utilization percentages are dynamic and sourced from the live ledger.*

#### 2.2 Donation-to-Redemption Velocity (DRV)
The Operator must monitor the DRV to ensure that donations are being converted into redemptions efficiently. A high DRV indicates a liquidity bottleneck, while a low DRV may indicate a lack of donor engagement or beneficiary activity.

*   **Definition:** DRV is the average number of days between a micro-donation being added to the pool and the corresponding credit being redeemed by a beneficiary.
*   **Target:** The system must track DRV against a target threshold. **KNOWLEDGE_GAP:** The exact target DRV threshold (e.g., 14 days) must be established by the Product Owner based on historical MVP data.
*   **Visualization:** A time-series line chart showing DRV over the last 30 days for each metro area.

### 3.0 Automated Alerting System

The platform must enforce automated alerts to notify the Operator of critical liquidity events. These alerts are governed by CON-AA14245C03.

#### 3.1 Credit Pool Utilization Alert
*   **Trigger:** When the Credit Pool Utilization Rate for any metro area exceeds 85%.
*   **Action:** The system must trigger an automated alert to the Operator via the dashboard and email.
*   **Operator Response:** The alert should provide a direct link to the "Liquidity Management" action panel, allowing the Operator to initiate a manual top-up or reallocate credits from a surplus region.
*   **Rationale:** This threshold is critical to prevent the platform from running out of credits during peak donation cycles, which would directly impact beneficiary dignity and platform trust.

#### 3.2 DRV Anomaly Alert
*   **Trigger:** When the DRV for any metro area exceeds the target threshold (see 2.2) for more than 48 hours.
*   **Action:** The system must trigger a "Liquidity Stagnation" alert.
*   **Operator Response:** The Operator can investigate potential causes, such as a drop in donor funding or a technical issue with the Redemption flow.

### 4.0 Liquidity Management Actions

The Operator interface must provide actionable controls to manage liquidity in real-time.

#### 4.1 Manual Credit Top-Up
*   **Function:** Allows the Operator to manually add credits to a specific metro area's pool.
*   **Use Case:** Emergency response to a sudden spike in redemption requests or a temporary drop in donor funding.
*   **Audit Trail:** All manual top-ups must be logged in the append-only, cryptographic audit ledger (CON-199A4FEDC7) for SOC2 Type II compliance.

#### 4.2 Regional Credit Reallocation
*   **Function:** Allows the Operator to transfer credits from a surplus region to a deficit region.
*   **Use Case:** Balancing liquidity across SF, NYC, and Chicago during uneven donation cycles.
*   **Constraint:** Reallocation must be instantaneous and reflected in the real-time dashboard.

#### 5.1 Credit Lifecycle State Machine
The platform manages emergency credits through a strict state machine. The Operator's interface must reflect these states:

1.  **Issued:** Credit is allocated to a beneficiary's wallet.
2.  **Active:** Credit is available for redemption.
3.  **Expiring:** Credit is within the final 24 hours of its 72-hour validity window.
4.  **Rolled Back:** Credit has expired and been returned to the regional pool.

#### 5.2 Auto-Rollback Execution
*   **Rule:** Unused emergency credits must automatically roll back to the central regional pool after 72 hours of expiration to prevent ledger stagnation.
*   **Visibility:** The Operator dashboard must display a "Pending Rollback" queue, showing the total value of credits scheduled for return to the pool within the next 24 hours.
*   **Audit:** Every rollback event must be logged as a distinct transaction in the append-only ledger (CON-199A4FEDC7), linking the original issuance ID to the pool re-entry ID.

### 6.0 Edge Cases and Error Flows

#### 6.1 Partial Failure in Top-Up
If a manual top-up fails due to a payment gateway error (e.g., Stripe Issuing API timeout), the system must log the error, notify the Operator, and retry the transaction up to three times with exponential backoff. If all retries fail, the Operator must be prompted to resolve the payment method issue.

#### 6.2 Data Latency
In the event of a delay in data aggregation from the Core Transaction & Ledger Service, the dashboard must display a "Data Latency Warning" and show the last known good state, rather than displaying stale or incorrect data.

#### 6.3 Zero-Balance Pool
If a metro area's pool reaches zero, the system must immediately disable the redemption flow for that region and display a "Service Temporarily Unavailable" message to beneficiaries, while alerting the Operator to initiate an emergency top-up.

### 7.0 System-Wide Success Criteria Monitoring

The Operator dashboard must provide visibility into the platform's adherence to its primary success criteria, ensuring operational stability and financial health.

#### 7.1 Operational Metrics
*   **Donation-to-Redemption Velocity (DRV):** Monitored against the target threshold established in Section 2.2.
*   **Credit Pool Utilization Rate:** Monitored against the 85% alert threshold.
*   **System Uptime:** Monitored against the 99.99% operational uptime target across AWS multi-AZ configurations.
*   **API Responsiveness:** Monitored against the p99 latency target of below 250ms under 10,000 concurrent connections.
*   **Cache Hit Ratio (CHR):** Monitored against the target of above 92% for restaurant search queries.

#### 7.2 Financial Reconciliation
*   **Reconciliation Integrity:** The system must ensure robust financial reconciliation against partial failures, ensuring that credits issued but not cleared do not leave the ledger in an inconsistent state (CON-6A9F6E50CE).
*   **Audit Trail Completeness:** All infrastructure and administrative changes must be pushed to unalterable AWS CloudTrail logs (CON-0B2D40801A) to support SOC2 Type II compliance.

#### 8.1 Absolute Anonymization
The Operator dashboard must strictly enforce absolute anonymization. No beneficiary demographic data (legal name, domestic background, PII) may be displayed or exported from the Operator interface. All beneficiary analytics must map to high-entropy UUIDv4 keys (CON-9DEA275205).

#### 8.2 Data Retention
The Operator must enforce data retention policies where unused emergency credits auto-roll back to the regional pool after 72 hours (CON-AEB925BD12). Any residual transaction logs must comply with SOC2 Type II data retention standards.

#### 8.3 Regulatory Compliance
The platform must comply with financial services regulations regarding virtual gift card issuance and money transmission licensing across the 3 metro areas (CON-0E1893E6A7). The Operator interface must provide tools to generate compliance reports linking financial flows to high-level events without linking to individual beneficiaries (CON-DE21E04933).
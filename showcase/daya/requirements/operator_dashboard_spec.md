# Operator Monitoring & Management Dashboard

## 1. Operator Persona Definition

The Platform Operator is the central governance authority for the MealCredit tripartite marketplace. This role is distinct from regional admins and NGO facilitators; the Operator possesses platform-wide visibility and control across the three initial metropolitan footprints: San Francisco (SF), New York City (NYC), and Chicago (CHI).

### Primary Responsibilities
- **Liquidity Oversight:** Monitor real-time 'Credit Pool Utilization Rate' across all three regions to prevent liquidity crises or capital stagnation.
- **Compliance & Trust:** Ensure absolute adherence to PCI-DSS Level 1 and SOC2 Type II structural planning, specifically verifying that beneficiary data remains absolutely anonymized in all operational logs and dashboards.
- **Incident Triage:** Respond to automated alerts regarding transaction anomalies, POS integration failures, or dispute escalations that exceed regional resolution thresholds.
- **NGO Credentialing:** Review and approve digital identity and proof of organizational legitimacy for new NGO partners before they can onboard beneficiaries.

### Key Constraints
- The Operator must never view or access Personally Identifiable Information (PII) of beneficiaries, donors, or merchants to maintain the platform's core mission of decoupling food assistance from social stigma.
- All actions taken by the Operator are logged in an immutable, append-only audit trail for regulatory reporting.

---

### 2.4 Liquidity State Definitions
I want the dashboard to clearly define the 'Credit Pool Utilization Rate' and the thresholds for 'Warning' and 'Critical' states,
So that I have a consistent understanding of what the metrics mean and what actions are required.

### 2.5 Edge Cases and Failure States
- **Data Latency:** If the Aurora ledger query fails or exceeds 10 seconds, the dashboard will display the last known value with a 'Data Stale' indicator. No alert will be triggered based on stale data.
- **Multi-Tenant Isolation:** Alerts are scoped to the specific metropolitan footprint (SF, NYC, Chicago) unless the global utilization exceeds the threshold, in which case a global alert is also triggered.

---

## 3. Automated Alerting and Liquidity Thresholds

### 3.1 Credit Pool Utilization Rate (CPU) Definition
The CPU is the primary metric for liquidity health. It is calculated per metropolitan footprint (SF, NYC, Chicago) and aggregated globally.

- **Formula:** `CPU = (Total Credits Redeemed / Total Credits Available) * 100`
- **Data Source:** Real-time query against the Aurora ledger for active, non-expired credits.
- **Refresh Rate:** < 5 seconds (via Server-Sent Events to the Operator Dashboard).

### 3.2 Alert Thresholds and Logic
The system will trigger automated alerts based on the following thresholds. These thresholds are critical for maintaining the 'Decoupled Food Assistance' mission by ensuring beneficiaries always have access to credits.

| State | Threshold | Condition | Notification Channel | Action Required |
| :--- | :--- | :--- | :--- | :--- |
| **Warning** | > 85% | CPU exceeds 85% | Email, In-App Banner (Orange) | Review donor contribution velocity; consider activating 'Directed Impact Flows' to specific regions. |
| **Safe** | 50% - 85% | CPU within normal operating range | None | None. |

**Note on Thresholds:** The 85% threshold is explicitly mandated by the project requirement as the trigger for alerts. Other potential thresholds (e.g., critical levels or low-liquidity triggers) are not established in the project requirement and are deferred.

### 3.3 Notification Mechanism
Alerts are delivered to Operators via the following channels, ensuring no single point of failure:
1. **In-App Dashboard Banner:** Persistent banner at the top of the Operator Dashboard, color-coded by severity.
2. **Email Notification:** Detailed email with a link to the specific regional liquidity view and suggested actions.

### 3.5 Alignment with Project Truth
- **Project Requirement:** Explicitly mandates 'Credit Pool Utilization Rate triggers alerts if above 85%'.
- **Project Definition:** Aligns with 'Dynamic liquidity management' and 'Real-time synchronization' capabilities.
- **Success Criteria:** Supports the 'Credit Pool Utilization Rate' success criterion.

---

### 4.2 Offline-First Resilience and Error Handling
To ensure operational continuity in low-connectivity environments or during system outages, the NGO Credentialing module must implement specific resilience strategies.

**User Story:**
As a Platform Operator,
I want to have the credentialing interface handle network failures gracefully,
So that I can continue to review pending submissions without data loss or corruption.

#### Acceptance Criteria
1. **Offline Verification Workflow:** If the network connection is lost during a credentialing review, the Operator's local actions (approve/reject) are cached locally and synchronized automatically once connectivity is restored.
2. **Graceful Degradation:** If the document upload service is unavailable, the Operator can still view previously cached documentation and make decisions based on available data, with a clear 'Pending Sync' indicator.
3. **Error State Handling:** If a credentialing submission fails validation (e.g., expired document), the system provides a clear, actionable error message to the Operator, specifying exactly which document failed and why.
4. **Data Integrity:** In the event of a partial sync failure, the system maintains a conflict-resolution log, allowing the Operator to manually reconcile discrepancies between local and server-side states.

## 5. Merchant Partner (Restaurant) Onboarding and POS Integrations

### 5.1 Merchant Onboarding Workflow
The Operator Dashboard provides a centralized interface for reviewing, approving, and managing Merchant Partner (Restaurant) onboarding. This workflow ensures that only verified commercial establishments can accept MealCredits.

**User Story:**
As a Platform Operator,
I want to review Merchant Partner onboarding submissions,
So that I can verify business status and configure payment settlement endpoints.

### 5.2 Financial Dispute Resolution
**Goal:** Provide the Operator with the tools to review and resolve high-level financial disputes that cannot be resolved at the regional or merchant level.

**User Story:**
As a Platform Operator,
I want to review flagged financial disputes linked to high-entropy transaction IDs,
So that I can verify transaction validity using the immutable audit log and authorize financial reversals when necessary.

---

## 6. Cross-Regional Operational Nuances

- **Data Segregation:** The dashboard must enforce strict multi-tenant data segregation, ensuring the Operator can view aggregated data across all three regions but cannot accidentally mix or misattribute transaction data between SF, NYC, and CHI.
- **Time Zone Awareness:** All timestamps in the dashboard must be displayed in the local time zone of the respective metropolitan footprint, with an option to view in UTC for global consistency.
- **Regulatory Variations:** The Operator must be able to filter compliance alerts by jurisdiction (e.g., CCPA for SF, local NYC regulations, Illinois financial laws) to ensure region-specific compliance requirements are met.

## 7. Executive Summary

This artifact defines the functional requirements, user stories, and acceptance criteria for the **Operator Monitoring & Management Dashboard**. This interface serves as the primary control surface for platform governance, operational health, and financial integrity. It enables Operators to manage NGO credentialing, monitor real-time liquidity pools across the three target metropolitan areas (SF, NYC, Chicago), and resolve financial disputes while maintaining strict adherence to PCI-DSS Level 1 and absolute beneficiary anonymization standards.

## 8. User Personas & Roles

### 8.1 Platform Operator
**Identity:** Internal staff responsible for platform governance, compliance, and operational continuity.
**Primary Goals:**
- Ensure liquidity pools remain healthy across all metro footprints.
- Resolve financial disputes and chargebacks efficiently.
- Verify merchant partner (Restaurant) onboarding and POS integration health.
- Maintain absolute anonymity of Beneficiaries in all audit trails.

### 8.2 Senior Operations Director
**Identity:** Escalation point for complex liquidity or compliance issues.
**Primary Goals:**
- Approve manual liquidity transfers between regional pools during crises.
- Review escalated "Audit Integrity Failure" cases.

## 9. Core Capabilities & User Stories

### 9.1 Real-Time Liquidity Monitoring
**User Story:**
As a Platform Operator, I want to view the real-time `Credit Pool Utilization Rate` across SF, NYC, and Chicago, so that I can proactively manage liquidity and prevent service disruptions for Beneficiaries.

**Acceptance Criteria:**
1. The dashboard displays a real-time overview of liquidity pools for each metro region.
2. The system triggers automated alerts when the `Credit Pool Utilization Rate` exceeds 85% or drops below safe liquidity thresholds.
3. The interface provides drill-down capabilities to view pool composition (e.g., total credits issued vs. redeemed) for each region.
4. Data updates reflect the latest state from the Aurora ledger with minimal latency.

### 9.2 Immutable Audit Log Investigation
**User Story:**
As a Platform Operator, I want to view the immutable, append-only ledger audit log for a specific disputed transaction, so that I can verify the validity of the transaction and the cryptographic token signature without needing to access raw beneficiary PII.

**Acceptance Criteria:**
1. Upon selecting a dispute, the Operator sees a detailed "Investigation View".
2. The view displays the full transaction history from the Aurora ledger, including:
   - The initial credit pool allocation.
   - The generation of the single-use virtual card token.
   - The POS clearing event.
   - The cryptographic token signature hash.
3. The interface explicitly masks or redacts any fields containing Beneficiary PII (e.g., legal name, address), displaying only the anonymous ID or token hash.
4. The Operator can view the "Offline Token Verification" status if the transaction occurred in a low-connectivity environment, confirming the hardware-backed SecureStore validation.

### 9.3 Dispute Resolution & Financial Reversal
**User Story:**
As a Platform Operator, I want to authorize a financial reversal or refund for a verified dispute, so that the affected party (Merchant or Donor) is compensated and the regional credit pool balance is accurately updated.

**Acceptance Criteria:**
1. The Operator can select a resolution action: "Approve Refund" or "Reject Dispute".
2. If "Approve Refund" is selected, the Operator must provide a mandatory justification note (stored in the audit log).
3. Upon confirmation, the system triggers a reversal via Stripe Connect/Issuing rails.
4. The system automatically updates the `Credit Pool Utilization Rate` for the specific metro region to reflect the reversed funds.
5. The affected Merchant Partner receives a notification of the resolution status via their Edge Dashboard.
6. The dispute status transitions to "Resolved" and is removed from the active triage list.

## 10. Edge Cases & Error Flows

This section defines the system's behavior for exceptional states, ensuring graceful degradation and robust error handling for the Operator Dashboard.

### 10.1 Concurrent Resolution Attempt
- **Scenario:** Two Operators attempt to resolve the same dispute simultaneously.
- **System Behavior:** The system uses optimistic locking on the dispute record. The first submission succeeds; the second receives a "Conflict: Dispute Already Resolved" error and refreshes the view.

### 10.2 Insufficient Pool Balance for Refund
- **Scenario:** A dispute resolution requires a refund that exceeds the available balance in the specific regional credit pool.
- **System Behavior:** The system blocks the reversal and displays an "Insufficient Regional Liquidity" error. The Operator is prompted to initiate a manual liquidity transfer from the central global pool (if permitted by policy) or escalate to a Senior Operations Director.

### 10.3 Missing Ledger Entry
- **Scenario:** The immutable audit log for a specific Transaction ID is corrupted or missing a critical step.
- **System Behavior:** The system flags the transaction as "Audit Integrity Failure" and prevents automatic resolution. The Operator is forced to escalate the case to the Compliance & Trust team for manual forensic review.

### 10.4 Merchant Non-Response
- **Scenario:** A Merchant Partner does not respond to a refund request within the defined SLA.
- **System Behavior:** The system automatically escalates the dispute to "High Severity" and notifies the Operator via the dashboard alerting system.

### 10.5 Graceful Degradation for Real-Time Liquidity Dashboard
- **Scenario:** The real-time liquidity dashboard fails to update due to a temporary outage in the Aurora ledger connection.
- **System Behavior:** The dashboard displays a "Data Stale" warning and reverts to showing the last known valid `Credit Pool Utilization Rate` for each metro region. The system continues to log events locally and attempts to reconnect automatically. Operators are notified of the data staleness via a non-blocking banner.

## 11. POS Integration Management

The Operator Dashboard provides tools for monitoring and managing POS integrations with various restaurant partners (Toast, Clover, Square).

**User Story:**
As a Platform Operator, I want to monitor the health of POS integrations across all merchant partners, so that I can quickly identify and resolve integration failures that impact beneficiary redemption.

**Acceptance Criteria:**
1. The dashboard displays a real-time status indicator for each merchant's POS integration (Active, Degraded, Down).
2. The Operator can view detailed logs for any integration failure, including error codes and timestamps.
3. The Operator can trigger a manual re-sync of a merchant's catalogue if discrepancies are detected between the platform and the POS system.
4. The system automatically notifies the Operator if a merchant's POS integration has been down for more than 15 minutes.

## 12. Administrative Governance and Audit Closure

### 12.2 Dispute Resolution and Chargeback Handling
**User Story:**
As a Platform Operator, I want to review and resolve financial disputes and chargebacks, so that I can maintain trust and integrity in the platform's financial transactions.

**Acceptance Criteria:**
1. The dashboard displays a list of all open disputes and chargebacks, sorted by severity and timestamp.
2. The Operator can view detailed information for each dispute, including transaction metadata, audit log entries, and cryptographic token signatures.
3. The Operator can authorize a financial reversal via the integrated Stripe Connect interface, which automatically updates the regional credit pool balance.
4. The system notifies the involved merchant and donor of the resolution status.

## 13. Success Criteria and Alignment

This section maps the Operator Monitoring & Management Dashboard requirements to the project's success criteria and business rules.

| Success Criterion | Dashboard Feature | Alignment |
| :--- | :--- | :--- |
| Credit Pool Utilization Rate triggers alerts if above 85% | Real-Time Liquidity Overview, Threshold Alerting | Directly addressed by US-1.1 and the liquidity state definitions. |
| Merchant Retention Rate (MRR) measured month-over-month | Merchant Partner Onboarding, POS Integration Management | Supports MRR by ensuring smooth onboarding and reliable POS integrations. |
| Credit Pool Utilization Rate triggers alerts if above 85% | Automated Alerting and Liquidity Thresholds | Directly addressed by Section 3. |
| Stripe Webhook Processing Latency average below 150ms | Real-Time Liquidity Overview | Supports latency monitoring via real-time data updates. |
| Cache Hit Ratio (CHR) for restaurant search queries above 92% | Merchant Partner Onboarding | Supports search performance by ensuring accurate and up-to-date merchant catalogues. |
| API Responsiveness p99 latency below 250ms under 10,000 concurrent connections | Real-Time Liquidity Overview | Supports API responsiveness by providing a scalable dashboard interface. |
| 99.99% operational uptime across AWS multi-AZ configurations | Administrative Governance and Audit Closure | Supports uptime monitoring via comprehensive audit trails and alerting. |

This section provides the Design team with clear, testable user stories and acceptance criteria for the Operator Monitoring & Management Dashboard, ensuring that Operators have the visibility and tools they need to manage platform liquidity, compliance, and merchant partnerships effectively across the three metropolitan footprints.

## 14. Sibling Dependencies

- **Identity, Access & Offline Capability Foundation:** This artifact defers to the Identity artifact for the specific technical implementation of cryptographic key generation and secure storage. See Identity, Access & Offline Capability Foundation for the full treatment.
- **Restaurant Partner Onboarding & POS Integration:** This artifact defers to the Restaurant Partner artifact for the specific POS integration credentials that NGOs may need to manage for their associated merchants. See Restaurant Partner Onboarding & POS Integration for the full treatment.

## 15. Knowledge Gaps & Assumptions

**KNOWLEDGE_GAP:** Dispute SLA Thresholds - The specific time limits (e.g., 24h, 48h, 72h) for Merchant Partner responses and Operator resolution targets must be established by the Compliance & Trust team to align with PCI-DSS and Stripe chargeback windows.

**KNOWLEDGE_GAP:** Liquidity Transfer Policy - The rules governing whether and how Operators can manually transfer funds between regional credit pools (SF, NYC, Chicago) during a liquidity crisis are not yet defined. This requires input from the Financial Governance team.

**ASSUMPTION:** Stripe Connect Reversal API - The system assumes that Stripe Connect supports the specific reversal workflow required for MealCredit transactions (e.g., partial refunds, full reversals) within the 120-second receipt generation window. Verification of Stripe's API capabilities for this specific flow is needed.

**ASSUMPTION:** Operator Role Permissions - It is assumed that the "Platform Operator" role has read-only access to the immutable audit log and write access to the dispute resolution status, but does not have direct access to modify the underlying Aurora ledger entries. All ledger changes are triggered by the system upon Operator approval.
# Success Criteria & Operational Metrics

## 1.0 Executive Summary

This artifact establishes the definitive success criteria and operational metrics for the Daya (MealCredit) platform. It translates the high-level mission of decoupling food assistance from social stigma into quantifiable, testable targets across financial, operational, and user-experience dimensions. These metrics serve as the primary validation layer for the inception phase, ensuring that the hybrid architecture (GraphQL for high-throughput CRUD and asynchronous gRPC for financial services) is designed to meet strict latency, throughput, and privacy requirements.

## 2.0 Performance Thresholds (Hybrid Architecture)

To ensure a frictionless user experience for Beneficiaries and Merchant Partners, the system must meet the following latency and throughput targets under peak load conditions.

### 2.1 Transactional Latency and Throughput

*   **Voucher Creation & Scanning Latency:** The system must achieve a p99 latency of <250ms for Voucher Creation and Scanning Callback Processing under 10,000 concurrent connections. This ensures that the Beneficiary Dignified Redemption journey (JNY-1A3DBC558B) remains seamless, even during peak meal times.
    *   *Governance:* Enforced by the Transaction & Ledger Engine (CAP-1E2CFB2DE3) and the Dignified Redemption Engine (CAP-AEF45AC9BE).
    *   *Traceability:* CON-78A549ECB3
*   **Stripe Webhook Processing:** The system must process Stripe Webhook events to merchant ledger entry within an average latency of <150ms. This is critical for real-time settlement and preventing ledger discrepancies.
    *   *Traceability:* CON-AE9B9C163C
*   **Cache Hit Ratio (CHR):** To support the high-volume restaurant search queries in the Expo mobile app, the Cache Hit Ratio for restaurant search queries must exceed 92% via the Redis Enterprise Cluster. This minimizes database load and ensures rapid location-based filtering.
    *   *Traceability:* CON-59F8C209D1
*   **Operational Uptime:** The platform must maintain 99.99% operational uptime across AWS multi-AZ configurations. This high availability is non-negotiable for a fintech platform handling financial transactions and essential food assistance.
    *   *Traceability:* CON-725D8AA177

## 4.0 Data Privacy & Anonymization Metrics

To uphold the mission of decoupling food assistance from social stigma, the platform must enforce strict data privacy and anonymization standards. These metrics ensure that the dignity of the Beneficiary (ACT-ADA6716160) is protected by design.

*   **Beneficiary PII Classification:** All Beneficiary PII must be classified as 'Restricted No-PII'. No legal names, SSNs, or demographics are stored on-platform beyond cryptographic aliases. This is a hard constraint enforced by the Identity & Access Management (CAP-361A59708B) and Data Retention & Privacy Automation (CAP-42740533D7) capabilities.
    *   *Traceability:* CON-5CA3E5A67B
*   **WCAG 2.1 AA Compliance:** The Expo mobile app and Next.js dashboards must comply with WCAG 2.1 AA standards for vision and motor impairments. This ensures that both Donors (ACT-80C62C7814) and Beneficiaries can access the platform with dignity and ease.
    *   *Traceability:* CON-860AF558CE
*   **Immutable Receipt Generation:** Donors must receive immutable transactional receipts within 120 seconds of redemption. These receipts must strictly prohibit the transmission of any identifying beneficiary parameters, ensuring absolute anonymization.
    *   *Traceability:* CON-2CF76A097A

## 5.0 Operational Resilience & Security

*   **Offline Token Cryptographic Validation:** The system must support offline fallback QR codes that are large enough and high-contrast enough for easy scanning by cashiers (CON-ED34D14363). Offline token generation must use hardware-backed SecureStore with time-bound, signature-verified cryptograms (CON-F348873C08) to ensure that transactions can be processed or validated even during network outages (CON-83B6B3C1D2).
*   **Fraud Detection & Prevention:** The system must implement real-time anomaly detection to prevent double-spending of digital assets or fraudulent merchant activity (CON-29859B910F). Merchant collusion detection and cash-out fraud prevention mechanisms (CON-551B582DA3) must be active to protect the integrity of the financial ledger.
*   **Audit Trail Integrity:** All infrastructure modifications and API adjustments must be pushed to AWS CloudTrail for SOC2 Type II audit evidence (CON-00789EFED7). Append-only cryptographic log auditing in PostgreSQL must be implemented for all financial transactions (CON-13289BD04C).

## 6.0 Knowledge Gaps & Assumptions

The following items represent unresolved decisions or assumptions that must be addressed in subsequent phases to finalize the operational metrics.

*   **KNOWLEDGE_GAP:** Exact data retention period for Donor transaction history and impact receipts (e.g., 7 years for tax purposes) requires confirmation from Legal/Compliance to ensure alignment with IRS and local regulations.
    *   *Owner:* Legal/Compliance
    *   *Traceability:* CON-746AF68070
*   **KNOWLEDGE_GAP:** Specific anomaly detection thresholds for Fraud Detection & Prevention (CAP-50F5F57DBF) to prevent double-spending and merchant collusion need to be defined in the Design phase based on historical fraud data or industry benchmarks.
    *   *Owner:* Security Engineering
    *   *Traceability:* CON-29859B910F
*   **ASSUMPTION:** The target scale of 50,000 MAU across 3 initial metropolitan footprints (SF, NYC, Chicago) is a hard strategic constraint, not a soft goal. This assumption drives the capacity planning for the hybrid architecture.
*   **ASSUMPTION:** The 'Daya' brand and 'MealCredit' product name are ratified and will be used consistently across all artifacts and user-facing interfaces.

## 7.0 Traceability Matrix

| ID | Description | Category |
| :--- | :--- | :--- |
| CON-78A549ECB3 | Achieve p99 latency <250ms for Voucher Creation and Scanning Callback Processing under 10,000 concurrent connections. | Performance |
| CON-AE9B9C163C | Process Stripe Webhook events to merchant ledger entry within 150ms average latency. | Performance |
| CON-59F8C209D1 | Ensure Cache Hit Ratio (CHR) for restaurant search queries exceeds 92% via Redis Enterprise Cluster. | Performance |
| CON-725D8AA177 | Maintain 99.99% operational uptime across AWS multi-AZ configurations. | Resilience |
| CON-5CA3E5A67B | Classify Beneficiary PII as 'Restricted No-PII'; ensure no legal names, SSNs, or demographics are stored on-platform beyond cryptographic aliases. | Privacy |
| CON-860AF558CE | Ensure the Expo mobile app complies with WCAG 2.1 AA standards for vision and motor impairments. | Accessibility |
| CON-746AF68070 | Define data retention policies for Donor transaction history and impact receipts (e.g., 7 years for tax purposes). | Compliance |
| CON-A016F9DA51 | Offline Token Cryptographic Signature Validation Logic. | Security |
| CON-29859B910F | Financial fraud prevention: Implementing real-time anomaly detection to prevent double-spending of digital assets or fraudulent merchant activity. | Security |
| JNY-1A3DBC558B | Beneficiary Dignified Redemption. | Journey |
| JNY-338E53854C | Cross-Metro Liquidity Rebalancing. | Journey |
| JNY-A4C99AE47D | Merchant Fulfillment & Settlement. | Journey |
| CAP-6A13D9607A | Marketplace Liquidity. | Capability |
| CAP-361A59708B | Identity & Access Management. | Capability |
| CAP-42740533D7 | Data Retention & Privacy Automation. | Capability |
| CAP-50F5F57DBF | Fraud Detection & Prevention. | Capability |
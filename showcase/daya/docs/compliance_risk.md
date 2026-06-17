# Compliance, Risk & Regulatory Obligations

## 1. Executive Summary & Regulatory Posture

This document establishes the binding regulatory, compliance, and risk posture for the Daya platform (product name: MealCredit). The platform operates as a tripartite social-impact fintech marketplace connecting Contributors (Donors), Recipients (Beneficiaries), and Merchant Partners (Restaurants) through local non-profit organizations (NGOs).

The primary regulatory challenge is the decoupling of financial transaction processing from beneficiary identity. The platform must navigate the intersection of Money Transmission regulations, PCI-DSS Level 1 security mandates, and Data Privacy laws across three initial metropolitan footprints: San Francisco (SF), New York City (NYC), and Chicago (Chicago).

This artifact translates the project's explicit requirements for absolute anonymization, financial transaction processing, and operational uptime into enforceable compliance obligations and risk registers. It serves as the authoritative source for regulatory licensing gaps, data handling constraints, and operational risk controls.

### 1.1 Money Transmission Licensing (MTL)

The platform acts as an intermediary in the flow of funds, necessitating compliance with Money Transmission Laws. The specific licensing requirements vary by jurisdiction. The Operator (ACT-FE96DD3975) must secure all necessary Money Transmission Licenses or partner with a licensed entity (e.g., via a Banking-as-a-Service provider) before launching in any jurisdiction. Failure to secure these licenses constitutes a critical business risk.

| Jurisdiction | Regulating Body | Required License | Status / Gap |
| :--- | :--- | :--- | :--- |
| San Francisco (SF) | California Department of Financial Protection and Innovation (DFPI) | California Money Transmission Act (MTLA) License | KNOWLEDGE_GAP: Specific application requirements and bonding requirements for SF footprint must be established by Legal. |
| New York City (NYC) | New York State Department of Financial Services (NYDFS) | New York BitLicense / Money Transmitter License | KNOWLEDGE_GAP: Specific application requirements and bonding requirements for NYC footprint must be established by Legal. |
| Chicago (Chicago) | Illinois Department of Financial and Professional Regulation (IDFPR) | Illinois Money Transmitter License | KNOWLEDGE_GAP: Specific application requirements and bonding requirements for Chicago footprint must be established by Legal. |

### 1.2 Anti-Money Laundering (AML) & KYC

While the platform anonymizes beneficiary data, it must maintain robust AML/KYC (Know Your Customer) controls for Contributors and Merchant Partners.

*   **Contributor Verification:** Contributors (ACT-2A20B038B1) must undergo identity verification via Plaid/Stripe to prevent fraud and ensure funding source legitimacy.
*   **Merchant Partner Verification:** Merchant Partners (ACT-A14D3CDC5D) must undergo KYC/KYB (Know Your Business) verification to ensure they are legitimate commercial entities eligible to accept food credits.
*   **Transaction Monitoring:** The platform must implement automated monitoring for suspicious transaction patterns (e.g., rapid micro-donations followed by immediate large redemptions) to detect potential money laundering or fraud.

## 2. Data Privacy & Anonymization Architecture

The core value proposition of MealCredit is the decoupling of food assistance from social stigma. This requires an architecture that enforces Absolute Anonymization at the system level.

### 2.1 Beneficiary Data Classification

*   **Off-Platform Classification:** Beneficiary demographic data (name, address, phone number, dietary restrictions) is classified as strictly off-platform. This data resides with the NGO partners and is never transmitted to the Daya platform.
*   **Anonymized Credits:** The platform stores only derived, anonymized credits. These credits are mapped to high-entropy UUIDv4 keys, preventing any possibility of PII reconstruction from platform logs.

Reference: CON-4DB27D2227 (Classify beneficiary demographic data as strictly off-platform; platform stores only derived, anonymized credits). Reference: CON-9DEA275205 (Implement absolute anonymization where all beneficiary analytics map to high-entropy UUIDv4 keys, preventing PII reconstruction).

### 2.2 Data Minimization & Storage

*   **Client-Side Storage:** The Client Application Layer (SUR-E3E75E96CF) must not cache any user profile data (name, address, phone number) in local storage or state management stores. All user-specific context must be derived from the token claims on-demand.
*   **Secure Token Storage:** Authentication tokens (JWTs) must be stored exclusively in device-level SecureStore (iOS Keychain / Android Keystore), encrypted at rest using hardware-backed keystore mechanisms.
*   **Log Sanitization:** All infrastructure and administrative logs (AWS CloudTrail) must be scrubbed of any potential PII. Logs must only contain anonymized UUIDs and transaction hashes.

Reference: CON-0A6423E6B0 (Operate within SOC2 Type II control environments, generating detailed tracking logs for all infrastructure and administrative channels).

## 3. Operational Risk & Financial Reconciliation

### 3.1 Financial Reconciliation & Partial Failures

Financial reconciliation must be robust against partial failures, ensuring that credits issued but not cleared do not leave the ledger in an inconsistent state. The platform must implement idempotent transaction processing to prevent double-spending or credit loss during network interruptions or Stripe webhook delivery delays.

Reference: CON-6A9F6E50CE (Financial reconciliation must be robust against partial failures, ensuring that credits issued but not cleared do not leave the ledger in an inconsistent state).

### 3.2 Operational Uptime & Graceful Degradation

The platform must achieve 99.99% operational uptime across AWS multi-AZ configurations. Graceful degradation protocols must be in place to handle POS partner failures or network outages without compromising the integrity of the financial ledger.

Reference: CON-8BD1F56A44 (Achieve 99.99% operational uptime across AWS multi-AZ configurations with graceful degradation if POS partners fail).

## 4. Unresolved Regulatory Gaps & Decision Axes

The following gaps require resolution by Legal, Compliance, and the Operator (ACT-FE96DD3975) prior to the Design phase.

| Decision Axis | Owner | Status | Impact |
| :--- | :--- | :--- | :--- |
| Money Transmission Licensing Specifics (SF, NYC, Chicago) | Legal / Operator | KNOWLEDGE_GAP | Determines go-to-market timeline and BaaS partner requirements. |
| NGO Data Sharing Agreements | Legal / Operator | KNOWLEDGE_GAP | Defines the legal boundary of off-platform data handling and liability. |
| Beneficiary Anonymization Standards | Compliance / Operator | KNOWLEDGE_GAP | Establishes the technical baseline for UUIDv4 mapping and PII stripping. |
| Merchant Partner Onboarding KYC Depth | Compliance / Operator | KNOWLEDGE_GAP | Balances friction against fraud risk for restaurant onboarding. |

## 5. Success Signals & Compliance Metrics

*   **Donation-to-Redemption Velocity (DRV):** Must remain under 14 days to ensure liquidity and donor confidence.
*   **Merchant Retention Rate (MRR):** Measured month-over-month to assess partner satisfaction and platform viability.
*   **Credit Pool Utilization Rate:** Triggers alerts if above 85% to prevent liquidity shortages.
*   **Stripe Webhook Processing Latency:** Average must remain below 150ms for merchant ledger entry clearance.
*   **Cache Hit Ratio (CHR):** For restaurant search queries must exceed 92% to ensure low-latency beneficiary discovery.
*   **API Responsiveness:** p99 latency must remain below 250ms under 10,000 concurrent connections.
*   **Operational Uptime:** Must maintain 99.99% availability across AWS multi-AZ configurations.
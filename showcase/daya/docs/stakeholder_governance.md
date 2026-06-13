# Stakeholder Map and Decision Rights

## 1. Executive Summary
This artifact establishes the governance backbone for the Daya (MealCredit) platform by mapping the three primary actor groups (Donors, Beneficiaries, Merchant Partners) and the critical NGO intermediaries to their respective decision rights and engagement surfaces. It defines the executive concern surface, identifying who owns the strategic decisions around the pseudo-anonymized redemption lifecycle, data anonymization boundaries, and cross-metro operational resilience.

## 2. Primary Actor Groups and Engagement Surfaces
The following table maps the three core actor groups to their primary engagement surfaces and strategic decision rights. These rights are assigned to functional owner classes to ensure accountability without prematurely locking specific personnel.

| Actor Group | Primary Engagement Surfaces | Strategic Decision Rights | Governance Owner |
| :--- | :--- | :--- | :--- |
| **Donors** | Mobile App, Web Dashboard | **Funding Allocation:** Decide between global impact, regional (zip code), or specific merchant type targeting. | Compliance Owner |
| **Beneficiaries** | Mobile App, Apple/Google Wallet Passes | **Redemption Dignity:** Right to absolute anonymity; no PII (legal name, domestic background) stored on-platform. | Product Owner (Anonymization) |
| **Merchant Partners** | POS Integration, Edge Dashboard | **Fulfillment Terms:** Ability to toggle real-time throttle parameters to prevent structural overload. | Merchant Operations Lead |
| **NGO Partners** | NGO Vetting Dashboard | **Vetting & Onboarding:** Authority to onboard beneficiaries and monitor regional credit pool utilization. | System Administrator |
| **System Administrator** | System Admin Dashboard | **Access & Vetting:** Reviews NGO applications, verifies status, and grants delegated vetting permissions. | System Administrator |

## 3. Cross-Metro Escalation Matrix
To ensure operational resilience across the SF, NYC, and Chicago footprints, the following escalation matrix is established for cross-functional conflicts and technical failures.

| Level | Concern Category | Primary Owner | Escalation Target |
| :--- | :--- | :--- | :--- |
| **Level 1: Operational** | POS integration failure or throttle parameter conflict | Merchant Operations Lead | Technical Support |
| **Level 2: Compliance** | PCI-DSS Level 1 or SOC2 Type II structural breach | Compliance Owner | Legal & Risk Management |
| **Level 3: Strategic** | Multi-tenant architecture scaling issue (50,000 MAU target) | Product Owner | Executive Steering Committee |

## 4. Stakeholder Map and Decision Rights Matrix
The following matrix assigns RACI (Responsible, Accountable, Consulted, Informed) roles for the core platform functions. This ensures clear ownership and prevents governance gaps in the fractional credit issuance and redemption lifecycle.

| Function / Capability | Donor | Beneficiary | Merchant Partner | NGO Partner | System Administrator | Product Owner |
| --- | --- | --- | --- | --- | --- | --- |
| **Credit Issuance & Pool Management** | | | | | | |
| Micro-Donation Round-Up Configuration | C | I | I | I | A | C |
| Directed Impact Flow Assignment | A | I | I | C | R | I |
| Credit Pool Utilization Rate Monitoring | I | I | I | C | A | I |
| **Beneficiary Redemption & Anonymization** | | | | | | |
| Beneficiary Vetting & Onboarding | I | I | I | A | R | C |
| Pseudo-Anonymized Redemption Execution | I | A | R | C | R | C |
| Absolute Anonymization of Beneficiary Data | I | I | I | C | A | R |
| **Merchant Fulfillment & Payouts** | | | | | | |
| POS Integration & Zero-Footprint Dashboard | I | I | A | I | R | C |
| Real-Time Throttle Parameter Toggling | I | I | A | I | C | I |
| Merchant Payout & Reconciliation | I | I | A | I | R | C |
| **Multi-Metro Expansion (SF, NYC, Chicago)** | | | | | | |
| Metro Footprint Selection & Prioritization | I | I | C | C | A | C |
| Local NGO Partner Onboarding | I | I | I | A | R | C |

## 5. Governance Boundaries and Compliance Ownership
To ensure absolute anonymization of beneficiary data and PCI-DSS Level 1 adherence, the following governance boundaries are established:

*   **Data Anonymization Owner:** The Platform Ops (Daya) team is Accountable for the technical implementation of the AbsoluteAnonymization invariant. This includes client-side generation of clean tokenized vouchers and ensuring no PII (legal name, domestic background) crosses into production logs or is transmitted to merchants/donors.
*   **Compliance Oversight:** Compliance/Legal is Accountable for defining the regulatory requirements (PCI-DSS Level 1, SOC2 Type II) and auditing the Platform Ops' implementation. They are Consulted on any changes to the data flow that might impact the anonymization boundary.
*   **Beneficiary Data Access:** NGO Partners are Responsible for the initial vetting and onboarding of beneficiaries. However, they are explicitly Informed only of aggregated, anonymized data regarding credit pool utilization and redemption trends. They do not have direct access to raw beneficiary PII stored on the platform.
*   **Merchant Data Access:** Merchant Partners are Informed of transactional settlement data and payout reconciliation reports. They are explicitly prohibited from accessing donor or beneficiary PII under any circumstances.

## 6. Knowledge Gaps and Assumptions
The following knowledge gaps and assumptions are identified to ensure the artifact is actionable while acknowledging unresolved project-wide decisions.

*   **KNOWLEDGE_GAP:** Specific local regulatory requirements for financial services and food assistance in SF, NYC, and Chicago. Owner: Legal Counsel. Evidence Needed: Jurisdiction-specific compliance review.
*   **ASSUMPTION:** The 'Compliance Owner' role is a functional class that will be mapped to a specific individual or team during the Design phase. Owner: Product Owner. Evidence Needed: Organizational structure definition.
*   **ASSUMPTION:** The 'Merchant Operations Lead' role is responsible for all merchant-related disputes and payout reconciliations. Owner: Product Owner. Evidence Needed: Merchant contract templates.

This artifact's Risk Register and Compliance Obligations are covered in the Risk Register and Compliance Obligations artifact; this artifact defers to it for detailed risk entries and specific compliance control mappings.

This artifact's Technical Strategy and Constraints are covered in the Technical Strategy and Constraints artifact; this artifact defers to it for hybrid GraphQL/gRPC architecture details.
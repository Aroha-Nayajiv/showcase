# pronext

## Project Requirements
[0;34m🏥 DEVAI SIMPLE — Procurement Partners (ProNext) Platform[0m
============================================================
[0;36mProject : pronext[0m
[0;36mCommand : [0m
[0;36mAPI     : http://localhost:5003[0m

[0;33m🔍 Checking API...[0m
[0;32m✅ API running at http://localhost:5003[0m
[0;34m📁 Creating project: pronext[0m
============================================================
[0;36m▶ Create project — pronext[0m
[0;33m  POST http://localhost:5003/api/projects/create[0m
[0;33m  {
  "project_name": "pronext",
  "requirement_text": "Build ProNext — a unified, AI-native healthcare procurement and supply chain platform targeting post-acute and non-acute providers: skilled nursing facilities, assisted living and senior care communities, rehabilitation centres, critical access hospitals, community hospitals, urgent care clinics, surgery centres, and physician groups. Unlike legacy competitors who bolt two disconnected products together, ProNext is one platform with one data model, one AI layer, one supplier network, and one UX — giving any care-setting operator the full procurement lifecycle from order to payment in a single login.

INTELLIGENT ORDERING & CATALOG: staff place orders in natural language or via a clean UI — the AI agent interprets intent, searches across 9,000+ supplier catalogs, surfaces GPO-negotiated pricing automatically, enforces contract compliance, and prevents maverick spend before it happens. PunchOut via cXML/OCI for direct supplier shopping (McKesson, Medline, Cardinal Health, Sysco). Hosted internal catalogs for pre-approved items. AI flags when a cheaper compliant alternative exists before the order is submitted — not after.

AGENTIC PROCUREMENT AUTOMATION: AI agents handle entire procurement workflows autonomously — detecting low-stock across all facilities, identifying the best compliant vendor, pre-filling a Purchase Requisition with negotiated pricing, routing it through the correct approval chain, and converting approved requisitions to Purchase Orders — without staff touching a keyboard. Mandatory human-in-the-loop confirmation gate before any financial commitment. This replaces the manual phone-call, email, and clipboard workflows endemic in post-acute care.

REAL-TIME BUDGET INTELLIGENCE: approvers see the exact budget impact of every order before they approve — monthly and quarterly spend-to-budget visualised at facility, department, and GL-code level. AI-powered spend forecasting alerts finance teams to overruns 2-4 weeks in advance. Built-in ROI calculator personalised to each facility's actual spend history showing freight savings, order-processing time savings, and AP savings.

UNIFIED INVENTORY WITH MOBILE-FIRST OPERATIONS: single real-time inventory view across all facilities. Mobile app (iOS and Android) with barcode and QR-code scanning for stock counts, cycle counting, goods receipt, FIFO rotation, expiry tracking, and inter-facility transfers — the primary workflow tool for floor staff. Par-level thresholds auto-trigger replenishment. AI predicts usage spikes from seasonal illness and occupancy changes and pre-emptively adjusts par levels.

SMART AP AUTOMATION & THREE-WAY MATCHING: ingest invoices via EDI 810, cXML, or OCR (PDF and image formats). Auto-match every invoice line to the originating PO and goods receipt. AI flags price variances, duplicate invoices, and quantity discrepancies in real time and drafts the vendor dispute communication. Multi-facility AP consolidation so a central finance team processes everything from one queue. Digital payment workflows with remittance advice.

SPEND INTELLIGENCE & ANOMALY DETECTION: LLM-driven continuous analysis of purchase and invoice data — surfaces savings opportunities, identifies price drift against GPO contract rates, catches duplicate orders across facilities, and flags compliance drift before it becomes an audit finding. Personalised savings reports for finance leadership showing exactly which vendors and categories have the most recovery potential.

SUPPLIER & VENDOR MANAGEMENT: supplier self-service portal for catalog updates, pricing, order acknowledgements, and invoice submission. AI scores supplier performance on fill rate, on-time delivery, and invoice accuracy, surfacing that score during ordering to steer staff toward better vendors. GPO contract management with automated loading of contracted rates at go-live.

AI RUNTIME — ON-PREM, HIPAA-NATIVE (the structural competitive moat): ProNext's AI layer connects exclusively to locally-containerised LLM services via OpenAI-compatible endpoints (/v1/chat/completions) — no patient or financial data ever leaves the client network. AI endpoint URL and model name are fully configurable per deployment (Ollama, vLLM, LM Studio, LocalAI, llama.cpp server) with zero code changes. All model weights, inference containers, and agent decision logs stay within the client infrastructure perimeter. This is a HIPAA compliance guarantee cloud-only competitors structurally cannot match. Agent action logs provide complete HITRUST and SOC2 audit trails automatically. Pluggable agentic runtime compatible with the Model Context Protocol (MCP).

INTEGRATIONS & COMPLIANCE: ERP integrations (NetSuite, Sage Intacct, QuickBooks, MAS 90) and EHR/PMS connectors. SOC2 Type II, HIPAA, and HITRUST compliance. Full procurement lifecycle audit trail from requisition to payment.

IMPLEMENTATION & SERVICES: AI-guided onboarding playbook that gets a facility live in days not months. GPO contracts auto-loaded at go-live. Ongoing spend-optimisation advisory powered by the platform's own analytics — data-driven, not consultant-hour-driven.",
  "domain": "enterprise",
  "complexity": "high"
}[0m
[0;36m  HTTP 201[0m
{
  "data": {
    "contextId": "context_0e7e6874",
    "projectName": "pronext"
  },
  "message": "Project 'pronext' created successfully.",
  "status": "success",
  "timestamp": "2026-06-09T16:15:53.905954"
}

[0;34m🚀 Starting full pipeline (inception → deployment)[0m
============================================================
[0;36m▶ Start pipeline for pronext[0m
[0;33m  POST http://localhost:5003/api/projects/pronext/pipeline/start[0m
[0;33m  {
  "requirement_json": {
    "requirements": "Build ProNext — a unified, AI-native healthcare procurement and supply chain platform targeting post-acute and non-acute providers: skilled nursing facilities, assisted living and senior care communities, rehabilitation centres, critical access hospitals, community hospitals, urgent care clinics, surgery centres, and physician groups. Unlike legacy competitors who bolt two disconnected products together, ProNext is one platform with one data model, one AI layer, one supplier network, and one UX — giving any care-setting operator the full procurement lifecycle from order to payment in a single login.

INTELLIGENT ORDERING & CATALOG: staff place orders in natural language or via a clean UI — the AI agent interprets intent, searches across 9,000+ supplier catalogs, surfaces GPO-negotiated pricing automatically, enforces contract compliance, and prevents maverick spend before it happens. PunchOut via cXML/OCI for direct supplier shopping (McKesson, Medline, Cardinal Health, Sysco). Hosted internal catalogs for pre-approved items. AI flags when a cheaper compliant alternative exists before the order is submitted — not after.

AGENTIC PROCUREMENT AUTOMATION: AI agents handle entire procurement workflows autonomously — detecting low-stock across all facilities, identifying the best compliant vendor, pre-filling a Purchase Requisition with negotiated pricing, routing it through the correct approval chain, and converting approved requisitions to Purchase Orders — without staff touching a keyboard. Mandatory human-in-the-loop confirmation gate before any financial commitment. This replaces the manual phone-call, email, and clipboard workflows endemic in post-acute care.

REAL-TIME BUDGET INTELLIGENCE: approvers see the exact budget impact of every order before they approve — monthly and quarterly spend-to-budget visualised at facility, department, and GL-code level. AI-powered spend forecasting alerts finance teams to overruns 2-4 weeks in advance. Built-in ROI calculator personalised to each facility's actual spend history showing freight savings, order-processing time savings, and AP savings.

UNIFIED INVENTORY WITH MOBILE-FIRST OPERATIONS: single real-time inventory view across all facilities. Mobile app (iOS and Android) with barcode and QR-code scanning for stock counts, cycle counting, goods receipt, FIFO rotation, expiry tracking, and inter-facility transfers — the primary workflow tool for floor staff. Par-level thresholds auto-trigger replenishment. AI predicts usage spikes from seasonal illness and occupancy changes and pre-emptively adjusts par levels.

SMART AP AUTOMATION & THREE-WAY MATCHING: ingest invoices via EDI 810, cXML, or OCR (PDF and image formats). Auto-match every invoice line to the originating PO and goods receipt. AI flags price variances, duplicate invoices, and quantity discrepancies in real time and drafts the vendor dispute communication. Multi-facility AP consolidation so a central finance team processes everything from one queue. Digital payment workflows with remittance advice.

SPEND INTELLIGENCE & ANOMALY DETECTION: LLM-driven continuous analysis of purchase and invoice data — surfaces savings opportunities, identifies price drift against GPO contract rates, catches duplicate orders across facilities, and flags compliance drift before it becomes an audit finding. Personalised savings reports for finance leadership showing exactly which vendors and categories have the most recovery potential.

SUPPLIER & VENDOR MANAGEMENT: supplier self-service portal for catalog updates, pricing, order acknowledgements, and invoice submission. AI scores supplier performance on fill rate, on-time delivery, and invoice accuracy, surfacing that score during ordering to steer staff toward better vendors. GPO contract management with automated loading of contracted rates at go-live.

AI RUNTIME — ON-PREM, HIPAA-NATIVE (the structural competitive moat): ProNext's AI layer connects exclusively to locally-containerised LLM services via OpenAI-compatible endpoints (/v1/chat/completions) — no patient or financial data ever leaves the client network. AI endpoint URL and model name are fully configurable per deployment (Ollama, vLLM, LM Studio, LocalAI, llama.cpp server) with zero code changes. All model weights, inference containers, and agent decision logs stay within the client infrastructure perimeter. This is a HIPAA compliance guarantee cloud-only competitors structurally cannot match. Agent action logs provide complete HITRUST and SOC2 audit trails automatically. Pluggable agentic runtime compatible with the Model Context Protocol (MCP).

INTEGRATIONS & COMPLIANCE: ERP integrations (NetSuite, Sage Intacct, QuickBooks, MAS 90) and EHR/PMS connectors. SOC2 Type II, HIPAA, and HITRUST compliance. Full procurement lifecycle audit trail from requisition to payment.

IMPLEMENTATION & SERVICES: AI-guided onboarding playbook that gets a facility live in days not months. GPO contracts auto-loaded at go-live. Ongoing spend-optimisation advisory powered by the platform's own analytics — data-driven, not consultant-hour-driven.",
    "domain": "enterprise",
    "complexity": "high"
  },
  "start_phase": "inception",
  "end_phase": "deployment",
  "skip_post_steps": true
}[0m
[0;36m  HTTP 409[0m
{
  "message": "Pipeline for project 'pronext' is already running."
}

[0;31m❌ Pipeline start failed (HTTP 409)[0m
[0;33m⚠️  Pipeline already running. Use phase commands to resume specific phases.[0m

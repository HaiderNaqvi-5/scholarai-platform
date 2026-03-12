# ScholarAI — System Architecture

> **Document Version:** 1.0 — **Date:** 2026-03-08  
> **Classification:** FYP Technical Design Document  

---

## 1. Problem Statement

### 1.1 The Scholarship Discovery Problem

International scholarship applications are one of the most **informationally asymmetric** processes in higher education. Students — particularly from developing countries — face systemic barriers:

| Barrier | Description |
|---|---|
| **Fragmented Information** | Scholarships scattered across thousands of websites with no unified index |
| **Opaque Eligibility** | Requirements buried in lengthy policy documents |
| **No Feedback Loop** | Zero visibility into why applications were accepted or rejected |
| **Repetitive Credential Submission** | Same documents re-uploaded for every application |
| **No Preparation Pathway** | Existing platforms list scholarships but provide no application guidance |

### 1.2 Limitations of Existing Platforms

| Platform Type | Example | Limitation |
|---|---|---|
| Aggregator portals | ScholarshipPortal, Scholars4Dev | Keyword search only; no AI matching |
| University websites | Individual `.edu` sites | Silo'd, inconsistent, no cross-referencing |
| Social media groups | Facebook, Reddit | Unstructured, anecdotal, not scalable |
| Commercial SOP tools | Grammarly, generic LLM chat | General-purpose; not scholarship-specific |

**No existing platform combines** discovery, AI matching, explainability, interview preparation, and credential verification.

---

## 2. Research Novelty

### 2.1 Primary Research Contributions

| # | Contribution | Research Area |
|---|---|---|
| 1 | **Explainable scholarship recommendation** — SHAP/LIME in a domain where recommendation transparency is unstudied | Explainable AI (XAI) |
| 2 | **Knowledge-graph-augmented recommendation** — using graph structure to improve matching quality | Knowledge Graphs + RecSys |
| 3 | **Blockchain credential passport** — reusable, verifiable credential layer using hash verification | Decentralized Identity |
| 4 | **AI interview simulation** — domain-specific dialogue system for scholarship interview readiness | NLP / Dialogue Systems |

### 2.2 Novelty Justification

- **XAI for scholarship matching** is largely unexplored. Existing XAI literature focuses on credit scoring, healthcare, and hiring — scholarship recommendations constitute a **novel application domain**.
- **Knowledge graph recommendations** (KGAT, RippleNet) have been explored in e-commerce but **not in scholarship ecosystems** where entities form natural graph structures.
- Prior credential verification focuses on degree attestation; this system extends to **per-application document reuse** with on-chain hash verification.

### 2.3 Honest Assessment

> [!CAUTION]
> **Data scarcity is the primary research risk.** Public datasets of scholarship outcomes do not exist. The model must be trained on synthetic or voluntarily contributed data. All metrics must report this caveat.

> [!WARNING]
> The interview simulator produces **subjective quality scores**. These should be validated via correlation studies with human evaluators but cannot replace expert judgment.

---

## 3. Layered System Architecture

```
┌─────────────────────────────────────────────────────┐
│              PRESENTATION LAYER                     │
│    Next.js + React   (Student / Mentor / Admin)     │
├─────────────────────────────────────────────────────┤
│              API GATEWAY LAYER                      │
│       FastAPI   (REST + WebSocket endpoints)        │
├─────────────────────────────────────────────────────┤
│              AI / ML LAYER                          │
│  RecSys │ Multi-LLM Orchestration (LangGraph) │ RAG │
├─────────────────────────────────────────────────────┤
│              DATA LAYER                             │
│  PostgreSQL │ Neo4j │ Qdrant (Vector) │ Redis │ MinIO│
├─────────────────────────────────────────────────────┤
│              BLOCKCHAIN LAYER                       │
│       Polygon zkEVM  (Credential Passport)          │
└─────────────────────────────────────────────────────┘
```

### Component Descriptions

| Layer | Technology | Justification |
|---|---|---|
| **Presentation** | Next.js 14 (App Router), React 18 | SSR for SEO, mature ecosystem, built-in routing |
| **API Gateway** | FastAPI (Python 3.11+) | Native async, auto OpenAPI docs, Pydantic validation, same language as ML layer |
| **AI/ML** | scikit-learn, XGBoost, LightGBM, SHAP, LIME, Whisper, AutoGen/CrewAI/LangGraph | Best-in-class ML libraries; Orchestration frameworks for RAG and multi-agent workflows |
| **Data** | PostgreSQL, Neo4j, Qdrant/Weaviate, Redis, MinIO | Relational + Graph + Vector + Cache + Object storage |
| **Blockchain** | Polygon, Ethereum L2, Solidity | Low gas, high-throughput verification |
| **DevOps** | Docker, GitHub Actions, MLflow | Containerization, CI/CD, experiment tracking |

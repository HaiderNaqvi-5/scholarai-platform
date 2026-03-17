# ScholarAI — Product Requirements Document (PRD)

> **Version:** 1.0 — **Date:** 2026-03-08  
> **Project Type:** Final Year Project (FYP)

---

## Vision

An AI-driven platform that helps students prioritize scholarships through an explicitly transparent, 3-stage recommendation pipeline powered by Graph relationships, semantic vector search, and Explainable ML.

---

## Strict MVP Data Constraint

To guarantee high data quality, the MVP is forcefully locked to:
- **Location:** Canada
- **Degree:** MS (Master's)
- **Fields:** Data Science, Artificial Intelligence, Analytics
- **Providers:** DAAD, Fulbright, and specifically targeted university portals.

Global scraping is explicitly disabled for the MVP timeline.

---

## 6 Core Modules

### 1. Targeted Scholarship Discovery Engine
- **Technology:** Playwright, Browserless, Pandas, Pydantic.
- **Pipeline:** HTML Extraction → Parsing → Pydantic Schema Validation (prevents DB corruption) → Cleaning → Deduplication → PostgreSQL Insertion.

### 2. Hybrid Scholarship Recommendation Engine
- **Stage 1 (Graph):** Neo4j Knowledge Graph filters out hard ineligibility constraints (GPA, Citizenship).
- **Stage 2 (Vector Search):** PostgreSQL `pgvector` HuggingFace semantic search.
- **Stage 3 (Admission Probability):** XGBoost/Random Forest classifying synthetic data distributions to calculate success probability.

### 3. Explainable AI (XAI) Research Module
- **Purpose:** Provide transparent features contributions for UI matching.
- **Tools:** SHAP, LIME.
- **UX Example:** "GPA Contribution: +32%, Low IELTS penalty: -8%".

### 4. RAG-Powered AI Application Assistant
- **Purpose:** Critiques SOPs, CVs, and application essays.
- **Safety Restriction:** Context must be retrieved strictly from `pgvector` to absolutely eliminate generative hallucination.
- **Framework:** LangChain.

### 5. AI Mock Interview System
- **Pipeline:** Speech/Text Input → Gemini 2.0 Flash (Multimodal) → Feedback Generation.
- **Metrics Evaluated:** Answer clarity, content relevance, and confidence.
- **Infrastructure Note:** Uses Google Gemini Free Tier for MVP to avoid local Whisper GPU requirements. Must upgrade to a paid API tier for production scaling.

### 6. Role-Based Dashboards
- **Roles:** Student (discovery, interviews, tracking), Mentor (SOP reviews, feedback), and Admin (scraper health monitors, analytics).

---

## Technology Stack

| Category | Technologies |
|---|---|
| Frontend | Next.js 14, React 18, TypeScript, TailwindCSS |
| Backend | FastAPI (Python 3.11+) |
| Databases | PostgreSQL (primary config), Neo4j (graph), pgvector |
| Search Engine | OpenSearch |
| Task Queue | Celery, Redis |
| AI Processing | HuggingFace, LangChain, SHAP, LIME, Gemini 2.0 |
| Scraping | Playwright, Browserless |
| Containerization | Docker |

---

## LLM Integration Strategy (via LangChain Router)

- **Gemini 2.0 Flash:** Primary multimodal engine for mock interviews (audio-to-text evaluation) and RAG document assistance.
- **Claude 3.5 / GPT-4o (Deferred):** Optional future integrations for deep, long-form SOP review or complex logical routing.

**Scaling Requirement:** The MVP relies on the Gemini API Free Tier (15 RPM limits). To deploy for a wider student body, the project must migrate to a paid Google AI Studio or Vertex AI billing account.

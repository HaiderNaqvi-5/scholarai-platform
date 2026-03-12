# ScholarAI — Product Requirements Document (PRD)

> **Version:** 1.0 — **Date:** 2026-03-08  
> **Project Type:** Final Year Project (FYP)

---

## Vision

An AI-powered platform that guides students through the entire scholarship lifecycle — from discovery to preparation to application — while providing explainable recommendations, verified credentials, and mentorship connections.

---

## Core Modules

### Module 1: Scholarship Discovery Engine
- **Status:** To be implemented
- Automated web scraping via Playwright/Browserless/Scrapy/BeautifulSoup
- Extracts: scholarship name, host university, country, degree level, field of study, minimum GPA, required documents, funding amount, application deadline
- Data ingestion methods: web scraping, public APIs, structured data extraction
- Sourced from DAAD, Erasmus+, Fulbright, university portals, UNESCO, World Bank

### Module 2: Scholarship Knowledge Graph
- **Status:** To be implemented
- Neo4j graph connecting students, scholarships, universities, fields, countries
- Enables semantic scholarship search and relationship inference

### Module 3: AI Recommendation System
- **Status:** To be implemented (primary FYP deliverable)
- Random Forest, XGBoost, and LightGBM for match scoring and success probability
- Input: GPA, research experience, field of study, publications, volunteer work, language test scores
- Output: match score (e.g., 89%), success probability (e.g., 53%)

### Module 4: Explainable AI Module *(Research Component)*
- **Status:** To be implemented (primary research contribution)
- SHAP and LIME for per-feature contribution percentages
- User-facing explanations: "GPA contributed +32% to your match"

### Module 5: Retrieval Augmented Generation (RAG)
- **Status:** To be implemented
- Pipeline: User query → embedding generation → vector search → relevant documents retrieved → LLM reasoning
- Ask questions like: "Which scholarships in Germany fit my GPA?"
- Vector DBs: Qdrant, Weaviate, or Chroma

### Module 6: Multi-LLM Orchestration
- **Status:** To be implemented
- GPT: application guidance, interview simulation, SOP improvement
- Claude: long document analysis, policy summarization
- Gemini: structured data extraction
- Orchestration frameworks: LangGraph, CrewAI, AutoGen

### Module 7: AI Interview Simulation System
- **Status:** To be implemented
- Voice-based interview practice system (Whisper speech-to-text → LLM evaluation → feedback)
- Metrics: confidence score, communication clarity, content relevance

### Module 8: Blockchain Credential Passport
- **Status:** To be implemented
- Student uploads transcript → institution verifies document → hash stored on blockchain → instant verification
- Networks: Polygon, Ethereum L2 networks

### Module 9: Mentorship System
- **Status:** To be implemented
- Past scholarship winners mentor applicants
- Session types: SOP review, mock interviews, application guidance
- Mentors earn reputation points

### Module 10: Role-Based Dashboard System
- **Status:** To be implemented
- Dashboards: Student, Mentor, Admin, University
- Admin capabilities: scraper monitoring, mentor approval, analytics dashboard

---

## Technology Stack

| Category | Technologies |
|---|---|
| Frontend | Next.js 14, React 18, TypeScript |
| Backend | FastAPI, Python 3.11+, Celery, Redis |
| Database | PostgreSQL (Supabase), Neo4j |
| AI/ML | scikit-learn, XGBoost, SHAP, LangChain, Whisper |
| LLMs | GPT-4, Claude 3, Gemini 1.5 Pro |
| Blockchain | Polygon zkEVM, Solidity, Hardhat, ethers.js |
| DevOps | Docker, GitHub Actions, MLflow |

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| API response time | < 500ms (cached), < 3s (ML inference) |
| Concurrent users | 100+ (MVP), 1000+ (production) |
| Availability | 99.5% uptime |
| Security | JWT auth, RBAC, rate limiting, encrypted credentials |
| Accessibility | WCAG 2.1 AA compliance |

---

## Scope Clarification

> [!IMPORTANT]
> For a solo FYP, the **minimum viable scope** is:
> 1. Recommendation engine + SHAP explainability
> 2. Basic scholarship scraper (4+ sources: DAAD, Fulbright, Vanier Canada, Erasmus Mundus)  
> 3. Student dashboard with match results
> 4. Interview simulator (basic)
> 
> Blockchain, knowledge graph, and mentorship can be proof-of-concept or Phase 2.

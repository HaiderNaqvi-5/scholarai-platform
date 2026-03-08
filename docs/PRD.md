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
- Automated web scraping via Playwright/Browserless
- Extracts: name, country, field, GPA, deadline, funding, documents
- LLM-based structured extraction (Gemini) for resilience to page format changes
- Scheduled via Celery Beat; monitored via Admin dashboard

### Module 2: AI Recommendation System
- **Status:** To be implemented (primary FYP deliverable)
- XGBoost for match scoring, Random Forest for success probability
- Input: student profile features + scholarship features
- Output: match score (0–100%), success probability (0–100%)

### Module 3: Explainable AI Module *(Research Component)*
- **Status:** To be implemented (primary research contribution)
- SHAP TreeExplainer for per-feature contribution percentages
- LIME as secondary validation method
- User-facing explanations: "GPA contributed +32% to your match"

### Module 4: AI Interview Simulator
- **Status:** To be implemented
- Whisper speech-to-text → LLM evaluation → structured feedback
- Scores: relevance, confidence, clarity, overall
- Per-scholarship customized question sets

### Module 5: Blockchain Credential Passport
- **Status:** To be implemented (proof of concept)
- Polygon zkEVM smart contract for document hash storage
- Institution-verified credentials reusable across applications
- Students do not need blockchain wallets

### Module 6: Mentorship System
- **Status:** To be implemented
- Past scholarship winners mentor applicants
- Session types: SOP review, mock interviews, general advice
- Reputation points for active mentors

### Module 7: Knowledge Graph
- **Status:** To be implemented
- Neo4j graph connecting students, scholarships, universities, fields, countries
- Enables semantic matching and graph-based recommendations
- Research value: compare graph-augmented vs. flat recommendations

### Module 8: Role-Based Dashboards
- **Status:** To be implemented
- Student, Mentor, Admin, University interfaces
- Admin: user management, mentor approval, scraper monitoring, analytics

### Module 9: Platform Analytics
- **Status:** To be implemented
- Metrics: active users, scholarship listings, match accuracy, usage statistics

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
> 2. Basic scholarship scraper (3+ sources)  
> 3. Student dashboard with match results
> 4. Interview simulator (basic)
> 
> Blockchain, knowledge graph, and mentorship can be proof-of-concept or Phase 2.

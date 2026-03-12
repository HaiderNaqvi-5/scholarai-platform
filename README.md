# ScholarAI Platform — Technical Blueprint

**AI-Powered Scholarship Discovery and Preparation Platform**

An end-to-end platform that guides students globally through discovering scholarships, generating AI-based eligibility matches, preparing with an AI interview simulator, and verifying their credentials on the blockchain.

---

## 🏗️ 10 Core Modules

1. **Scholarship Discovery Engine**: Automated web scraping via Playwright/Gemini.
2. **Scholarship Knowledge Graph**: Neo4j graph connecting students to opportunities.
3. **AI Recommendation System**: XGBoost and Random Forest for match scoring.
4. **Explainable AI**: SHAP and LIME providing transparent recommendation logic.
5. **Retrieval Augmented Generation (RAG)**: Qdrant/Weaviate for querying PDF policy docs.
6. **Multi-LLM Orchestration**: LangGraph routing requests answering between Claude, GPT, and Gemini based on task.
7. **AI Interview Simulation**: Whisper speech-to-text with LLM dynamic rubrics.
8. **Blockchain Credential Passport**: Polygon zkEVM for reusable, verified document hashes.
9. **Mentorship System**: Matching students with past winners.
10. **Role-Based Dashboards**: Portals for Students, Mentors, Admins, and Universities.

---

## 🛠️ Technology Stack (2025-2026)

- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend:** FastAPI (Python 3.11+), Celery
- **Databases:** PostgreSQL (Supabase), Neo4j (Graph), Qdrant (Vector), Redis (Cache)
- **AI/ML:** scikit-learn, XGBoost, LangGraph, Whisper, MLflow
- **Blockchain:** Polygon L2, Solidity, Hardhat
- **DevOps:** Docker, Kubernetes

---

## 📁 Repository Structure

```text
scholarai-platform/
├── docs/                    # Architectural Specifications (PRD, API, DB Schema)
├── backend/                 # FastAPI REST Services and Application Logic
├── frontend/                # Next.js Application UI
├── ml_models/               # Training pipelines and isolated synthetic datasets
├── scrapers/                # Core Playwright scraping logic
├── blockchain/              # Solidity Smart Contracts (Credential Passport)
└── scripts/                 # Data ingestion, seeding, and DB migration utilities
```

Complete technical documentation resides in the [docs/](/docs) folder. Please read `docs/PRD.md` and `docs/architecture.md` for in-depth system designs.

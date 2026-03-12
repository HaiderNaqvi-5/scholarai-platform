# ScholarAI Platform — Technical Blueprint

**AI-Powered Scholarship Discovery and Preparation Platform**

An end-to-end platform that guides students through discovering scholarships, generating AI-based eligibility matches, preparing with an AI interview simulator, and connecting with mentors.

---

## 🏗️ 6 Core Modules

1. **Targeted Discovery Engine**: Playwright scraping for MS DS/AI programs in Canada.
2. **Hybrid Recommendation Engine**: 3-stage pipeline (Knowledge Graph → Vector Search → XGBoost).
3. **Explainable AI (XAI)**: SHAP/LIME feature contributions for match transparency.
4. **RAG Application Assistant**: LangChain-powered SOP/CV critique.
5. **AI Mock Interview System**: Whisper speech-to-text with GPT-4 evaluation rubrics.
6. **Role-Based Dashboards**: Portals for Students, Mentors, and Admins.

---

## 🛠️ Technology Stack (2025-2026)

- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend:** FastAPI (Python 3.11+), Celery
- **Databases:** PostgreSQL (pgvector), Neo4j (Graph), OpenSearch (Text Search)
- **AI/ML:** scikit-learn, XGBoost, LangChain, Whisper, MLflow, HuggingFace
- **DevOps:** Docker, GitHub Actions

---

## 📁 Repository Structure

```text
scholarai-platform/
├── docs/                    # Architectural Specifications (PRD, API, DB Schema)
├── backend/                 # FastAPI REST Services and Application Logic
├── frontend/                # Next.js Application UI
├── ai_services/             # LangChain agents, MLflow, XGBoost pipelines
├── scrapers/                # Core Playwright scraping logic
└── setup/                   # Docker-compose and seeding scripts
```

Complete technical documentation resides in the [docs/](/docs) folder. Please read `docs/PRD.md` and `docs/architecture.md` for in-depth system designs.

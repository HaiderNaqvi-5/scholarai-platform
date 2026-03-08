# ScholarAI

**AI-Powered Scholarship Discovery and Preparation Platform**

---

## Overview

ScholarAI assists students through the entire scholarship journey: discovering opportunities globally, receiving AI-powered matches with explainable recommendations, preparing applications with AI-based SOP assistance and interview simulation, verifying credentials via blockchain, and connecting with past scholarship winners.

## Architecture

- **Frontend:** Next.js 14 + React 18
- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL (Supabase) + Neo4j (Knowledge Graph) + Redis
- **AI/ML:** XGBoost, SHAP, LangChain, Whisper
- **LLMs:** GPT-4, Claude 3, Gemini 1.5 Pro
- **Blockchain:** Polygon zkEVM (Solidity)
- **DevOps:** Docker, GitHub Actions, MLflow

## Project Structure

```
scholarai-platform/
├── docs/                    # Technical documentation
│   ├── PRD.md               # Product requirements
│   ├── architecture.md      # System architecture
│   ├── architecture_diagrams.md  # Mermaid diagrams
│   ├── database_schema.md   # Full DB schema + ER diagram
│   ├── api_design.md        # REST API endpoints
│   ├── ai_models.md         # ML models + explainability
│   ├── blockchain_design.md # Smart contract design
│   ├── deployment.md        # Deployment, timeline, risks
│   └── skills.md            # Team skills matrix
├── backend/                 # FastAPI application
├── frontend/                # Next.js application
├── ml_models/               # Training, evaluation, datasets
├── blockchain/              # Smart contracts (Hardhat)
└── scripts/                 # Scrapers + data pipeline
```

## Core Modules

| # | Module | Key Technology |
|---|---|---|
| 1 | Scholarship Discovery Engine | Playwright, Gemini |
| 2 | AI Recommendation System | XGBoost, Random Forest |
| 3 | Explainable AI (Research) | SHAP, LIME |
| 4 | Interview Simulator | Whisper, GPT-4 |
| 5 | Blockchain Credential Passport | Polygon zkEVM, Solidity |
| 6 | Mentorship System | Neo4j, reputation scoring |
| 7 | Knowledge Graph | Neo4j, Cypher |
| 8 | Role-Based Dashboards | Next.js (Student/Mentor/Admin/University) |
| 9 | Analytics Dashboard | Platform metrics |

## Quick Start

```bash
# Clone
git clone https://github.com/your-org/scholarai-platform.git
cd scholarai-platform

# Start services
docker-compose up -d

# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Documentation

See the `docs/` directory for complete technical documentation including architecture diagrams, database schema, API design, AI model specifications, and deployment guides.

## License

MIT

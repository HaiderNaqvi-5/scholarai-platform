# ScholarAI repository guidance

## Mission
This repository contains the planning and implementation artifacts for ScholarAI, an AI-powered scholarship platform being built as:
- a 16-week computer science FYP
- by a 3-person team
- with a realistic path to startup scaling after MVP

## Working mode
- Prefer the simplest defensible solution.
- Optimize for MVP feasibility first.
- Separate every recommendation into:
  - MVP
  - Future Research Extensions
  - Post-MVP Startup Features
- Resolve ambiguities autonomously using the simplest defensible assumption, then record that assumption explicitly.
- Do not block on open questions unless the task is impossible without user input.
- For large tasks, create or update a work plan before editing many files.

## Architecture defaults
- MVP architecture = modular monolith
- Frontend = Next.js + React + TypeScript + TailwindCSS
- Backend = FastAPI
- Async jobs = Celery + Redis
- Primary database = PostgreSQL
- Vector search = pgvector
- Default embedding model = sentence-transformers/all-MiniLM-L6-v2
- Knowledge Graph Layer is mandatory as a logical layer, but MVP implementation may be:
  - a narrowly scoped Neo4j graph, or
  - a relationally derived graph abstraction if simpler and more feasible
- Data ingestion = Playwright + Pandas + Pydantic
- Deployment = Docker Compose
- Migrations = Alembic
- CI/CD = GitHub Actions
- Prefer lightweight experiment tracking unless MLflow is clearly justified

## Delivery constraints
- Team size = 3 developers
- Timeline = 16 weeks
- Budget = limited
- AI coding tools may assist development, but they do not increase official team capacity
- Do not propose architecture that depends on large ops overhead, distributed microservices, or expensive infrastructure for MVP

## Data scope
- Canada is the main MVP university and program corpus
- USA is allowed only for:
  - Fulbright-related provider information
  - directly relevant funding rules
  - narrowly scoped cross-border scholarship logic
- General USA university discovery and broad USA scraping are not MVP by default
- DAAD is deferred to Future Research Extensions
- MVP programs:
  - MS Data Science
  - MS Artificial Intelligence
  - MS Analytics

## Data and research guardrails
- Do not invent datasets, APIs, legal guarantees, or performance numbers
- Structured validated data is the source of truth for:
  - eligibility
  - deadlines
  - funding rules
  - official scholarship requirements
- RAG may assist with:
  - SOP improvement
  - essay feedback
  - interview-answer feedback
  - document quality suggestions
- RAG must not be treated as the authority for scholarship rules
- If real outcome labels do not exist, frame the ML target as:
  - Estimated Scholarship Fit Score
  - or Application Competitiveness Score
- Do not claim causal prediction of scholarship success without real labels
- Always include threats to validity and reproducibility
- Maintain provenance states:
  - raw
  - validated
  - published

## UX and design bar
- The frontend should feel premium, minimal, deliberate, and polished
- Aim for Apple-like clarity and restraint in thinking, without copying any brand directly
- Avoid generic dashboard-template aesthetics
- Keep the design implementable by one strong frontend developer plus AI assistance

## Documentation-first behavior
- Documentation comes before broad implementation when scope is still evolving
- Prefer writing or updating files under `docs/scholarai/`
- For a full documentation task, start with:
  - `docs/scholarai/WORKPLAN.md`
  - `docs/scholarai/README.md`
- Keep terminology and section naming consistent across files
- End every documentation file with:
  - MVP decision
  - Deferred items
  - Assumptions
  - Risks

## Preferred initial file set
When asked to generate the core documentation pack, prefer these files:
- `docs/scholarai/01_executive_summary.md`
- `docs/scholarai/02_prd_and_scope.md`
- `docs/scholarai/03_brand_and_design_system.md`
- `docs/scholarai/04_requirements_and_governance.md`
- `docs/scholarai/05_system_architecture.md`
- `docs/scholarai/06_data_models.md`
- `docs/scholarai/07_ingestion_and_curation.md`
- `docs/scholarai/08_recommendation_and_ml.md`
- `docs/scholarai/09_xai_rag_and_interview.md`
- `docs/scholarai/10_backend_api_and_repo.md`
- `docs/scholarai/11_research_and_evaluation.md`
- `docs/scholarai/12_execution_plan.md`
- `docs/scholarai/13_qa_devops_and_risks.md`
- `docs/scholarai/14_future_roadmap.md`

## Verification
Before claiming work is complete, verify that:
- terminology is consistent across files
- diagrams match the architecture text
- MVP scope matches the roadmap
- research claims match the data assumptions
- startup ideas do not leak into MVP scope
- no section is left as vague placeholder text

## Definition of done
A documentation task is only done when:
- files are created in `docs/scholarai/`
- terminology is consistent across files
- diagrams match the written architecture
- MVP scope matches the roadmap
- risks and assumptions are explicit
- no section is left as vague placeholder text

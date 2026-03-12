# ScholarAI — Architecture Diagrams

> All diagrams are provided in **Mermaid** syntax for rendering, strictly aligned to the MVP Master Blueprint.

---

## 1. High-Level System Architecture

This diagram illustrates the separation of concerns across the React frontend, FastAPI gateway, and the distinct search/graph/relational data stores. Note the inclusion of OpenSearch for general text querying, Neo4j for the knowledge graph, and PostgreSQL (with pgvector) as the primary relational ML-backing store. The blockchain module has been entirely removed from the MVP.

```mermaid
graph TB
    subgraph "Frontend UI (Next.js)"
        STU["Student Dashboard"]
        MEN["Mentor Dashboard"]
        ADM["Admin Dashboard"]
    end

    subgraph "API Gateway Layer (FastAPI)"
        API["Core REST API"]
        AUTH["JWT Auth Middleware"]
    end

    subgraph "AI / ML Services"
        REC["Hybrid RecSysPipeline"]
        INT["Interview Simulator<br/>(Whisper + LLM)"]
        SOP["SOP Assistant<br/>(LangChain RAG)"]
        ORCH["LLM Orchestrator<br/>(LangChain)"]
    end

    subgraph "Data & Search Stores"
        PG["PostgreSQL + pgvector<br/>(Profiles & Similarity)"]
        NEO["Neo4j<br/>(Knowledge Graph Filter)"]
        OS["OpenSearch<br/>(Text Indexing)"]
        RD["Redis<br/>(Celery Queue)"]
    end

    subgraph "Ingestion Services"
        PW["Playwright Scrapers"]
        CEL["Celery Workers"]
    end

    STU & MEN & ADM --> AUTH --> API
    API --> REC & INT & SOP & ORCH
    API --> PG & NEO & OS & RD
    CEL --> PW -->|Cleaned JSON| PG & NEO & OS
```

---

## 2. Hybrid Recommendation Pipeline

This outlines the strict 3-stage recommendation engine. Stage 1 operates purely on Graph relationships to filter out hard eligibility constraints (citizenship, degree). Stage 2 uses `pgvector` HuggingFace embeddings for soft similarity math. Stage 3 applies the XGBoost classifier to generate the final admission probability and SHAP explainability mask.

```mermaid
graph TD
    subgraph "Input"
        SD["Scraped Scholarships"]
        SP["Student Profile<br/>(Canada, MS, AI)"]
    end

    subgraph "Stage 1: Knowledge Graph Filter (Neo4j)"
        KG["Cypher Query:<br/>Match Degree, Field, Citizenship"]
    end

    subgraph "Stage 2: Vector Similarity Search (pgvector)"
        EMB["HuggingFace Embeddings"]
        HNSW["HNSW Cosine Similarity"]
    end

    subgraph "Stage 3: ML Admission Predictor"
        XGB["XGBoost / Random Forest"]
        SHAP["SHAP Explainer"]
    end

    subgraph "Output"
        FINAL["Match Score (87%)<br/>+ Explainability JSON"]
    end

    SD & SP --> KG
    KG -->|Filtered Sub-set| EMB --> HNSW
    HNSW -->|Top K Similar| XGB
    XGB --> SHAP --> FINAL
```

---

## 3. AI Processing & RAG Pipeline

This diagram showcases the LangChain orchestration flow. It demonstrates how different LLMs are routed based on their specialization, and how the RAG pipeline forces context retrieval directly from PostgreSQL to prevent hallucinations when reviewing SOPs or answering system queries.

```mermaid
graph TD
    subgraph "User Input"
        REQ["Student Request<br/>(e.g., 'Review my SOP for DAAD')"]
    end

    subgraph "LangChain Orchestrator"
        ROUTER["Task Router"]
    end

    subgraph "Retrieval Augmented Generation (RAG)"
        EMB_REQ["Embed Request"]
        PG_DB[("PostgreSQL (pgvector)<br/>Table: scholarships")]
        CTX["Retrieve Constraints & Policy Context"]
    end

    subgraph "Specialized LLM Execution"
        CLAUDE["Claude 3.5 Sonnet<br/>(Long-form SOP Review)"]
        GPT4["GPT-4o<br/>(System Orchestration/Reasoning)"]
        GEMINI["Gemini 1.5 Pro<br/>(Data Extraction/Summarization)"]
    end

    REQ --> ROUTER
    ROUTER -->|SOP/Document Request| EMB_REQ
    EMB_REQ --> PG_DB --> CTX
    CTX --> CLAUDE
    ROUTER -->|General QA| GPT4
    ROUTER -->|Ingestion Parsing| GEMINI
    CLAUDE & GPT4 & GEMINI --> RESP["Synthesized Output"]
```

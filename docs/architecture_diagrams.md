# ScholarAI — Architecture Diagrams

> All diagrams are provided in **Mermaid** syntax for rendering.

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        STU["Student Dashboard"]
        MEN["Mentor Dashboard"]
        ADM["Admin Dashboard"]
        UNI["University Dashboard"]
    end

    subgraph "API Gateway"
        API["FastAPI Server"]
        AUTH["JWT Auth"]
        RATE["Rate Limiter"]
    end

    subgraph "AI / ML Services"
        REC["Recommendation Engine<br/>(XGBoost + SHAP)"]
        INT["Interview Simulator<br/>(Whisper + LLM)"]
        SOP["SOP Assistant<br/>(RAG + LLM)"]
        LLM_O["LLM Orchestrator<br/>(LangChain)"]
    end

    subgraph "Data Stores"
        PG["PostgreSQL (Supabase)"]
        NEO["Neo4j (Knowledge Graph)"]
        RD["Redis Cache"]
        OBJ["MinIO (Documents)"]
    end

    subgraph "External Services"
        SCR["Scrapers (Playwright)"]
        BC["Polygon zkEVM"]
        LLM_EXT["LLM APIs"]
    end

    STU & MEN & ADM & UNI --> API
    API --> AUTH --> RATE
    API --> REC & INT & SOP & LLM_O
    API --> PG & NEO & RD & OBJ
    API --> BC
    LLM_O --> LLM_EXT
    SCR --> PG & NEO
```

---

## 2. AI Pipeline Architecture

```mermaid
graph LR
    subgraph "Input"
        SP["Student Profile"]
        SD["Scholarship Data"]
    end

    subgraph "Feature Engineering"
        FE["Feature Extractor<br/>GPA normalization<br/>One-hot encoding<br/>Text embeddings"]
    end

    subgraph "Model Layer"
        XGB["XGBoost<br/>(Match Scoring)"]
        RF["Random Forest<br/>(Success Probability)"]
    end

    subgraph "Explainability"
        SHAP_M["SHAP TreeExplainer"]
        LIME_M["LIME Tabular"]
    end

    subgraph "Output"
        MS["Match Score 0-100%"]
        SUC["Success Probability"]
        EXP["Feature Contributions"]
    end

    SP & SD --> FE --> XGB & RF
    XGB --> SHAP_M --> MS & EXP
    RF --> SHAP_M --> SUC
    XGB -.-> LIME_M -.-> EXP
```

---

## 3. Data Ingestion Pipeline

```mermaid
graph TD
    subgraph "Sources"
        UW["University Websites"]
        SPO["Scholarship Portals"]
        GP["Government Programs"]
    end

    subgraph "Scraping Layer"
        PW["Playwright Scrapers"]
        SC["Celery Beat Scheduler"]
    end

    subgraph "Extraction"
        GEM["Gemini LLM<br/>(Structured Extraction)"]
        VAL["Pydantic Validator"]
    end

    subgraph "Storage"
        PG2["PostgreSQL"]
        NEO2["Neo4j"]
        RD2["Redis (Dedup)"]
    end

    subgraph "Post-Processing"
        GPT2["GPT (Description Simplification)"]
        CL["Claude (Policy Summarization)"]
    end

    SC --> PW
    UW & SPO & GP --> PW --> GEM --> VAL
    VAL --> RD2
    RD2 -->|"New"| PG2 & NEO2
    PG2 --> GPT2 & CL
```

---

## 4. Blockchain Verification Flow

```mermaid
sequenceDiagram
    participant S as Student
    participant P as Platform API
    participant I as Institution
    participant SC as Smart Contract (Polygon)
    participant C as Scholarship Committee

    S->>P: Upload transcript (PDF)
    P->>P: Generate SHA-256 hash
    P->>I: Request verification
    I->>P: Confirm authenticity
    P->>SC: storeCredentialHash(studentId, docHash, institutionId)
    SC-->>P: Transaction receipt (txHash)
    P-->>S: Credential verified

    Note over S,C: Later during application

    C->>P: Verify credential
    P->>SC: verifyCredential(studentId, docHash)
    SC-->>P: verified: true, institution, timestamp
    P-->>C: Credential authentic
```

---

## 5. User Journey Flow

```mermaid
graph TD
    A["1. Sign Up / Login"] --> B["2. Complete Profile"]
    B --> C["3. Upload Credentials"]
    C --> D["4. Get AI Recommendations"]
    D --> E["5. View SHAP Explanations"]
    E --> F["6. Prepare Application"]
    F --> G["6a. AI SOP Assistant"]
    F --> H["6b. Interview Simulator"]
    F --> I["6c. Connect with Mentor"]
    G & H & I --> J["7. Submit Application"]
    J --> K["8. Track Status"]
```

---

## 6. AI Interview System Pipeline

```mermaid
graph LR
    A["Student Audio"] --> B["Whisper STT"]
    B --> C["Timestamped Transcript"]
    C --> D["LLM Evaluator (GPT-4)"]
    D --> E["Relevance Score"]
    D --> F["Confidence Score"]
    D --> G["Clarity Score"]
    D --> H["Improvement Tips"]
```

---

## 7. RAG Pipeline

```mermaid
graph TD
    subgraph "Vector DB Ingestion"
        DOC["Policy Documents (PDF/HTML)"] --> CHUNK["Text Chunker"]
        CHUNK --> EMB1["Embedding Model<br/>(text-embedding-3-small)"]
        EMB1 --> QDR["Qdrant / Weaviate<br/>(Vector DB)"]
    end

    subgraph "Query Retrieval"
        UQ["User Query"] --> EMB2["Embedding Model"]
        EMB2 --> SEARCH["Vector Similarity Search"]
        SEARCH -->|Nearest Neighbors| QDR
        QDR --> RET["Retrieved Context Chunks"]
    end

    subgraph "Generation"
        RET & UQ --> PRMT["Prompt Formulation"]
        PRMT --> LLM_GEN["LLM (GPT-4 / Claude)"]
        LLM_GEN --> ANS["Generated Answer"]
    end
```

---

## 8. LLM Orchestration Architecture

```mermaid
graph TD
    subgraph "User Interface"
        USER["Student Query"]
    end

    subgraph "LangGraph / CrewAI Orchestrator"
        ROUTER["Intent Router"]
    end

    subgraph "Specialized Agents"
        AGT_SOP["SOP Assistant Agent<br/>(GPT-4)"]
        AGT_POL["Policy Expert Agent<br/>(Claude 3 + RAG)"]
        AGT_EXT["Extraction Agent<br/>(Gemini 1.5)"]
        AGT_INT["Interview Coach Agent<br/>(GPT-4 + Whisper)"]
    end

    USER --> ROUTER
    ROUTER -->|Document Analysis| AGT_POL
    ROUTER -->|Data Scraping| AGT_EXT
    ROUTER -->|Essay Review| AGT_SOP
    ROUTER -->|Mock Interview| AGT_INT

    AGT_POL --> RDB[("Qdrant Vector DB")]
    AGT_EXT --> GDB[("Neo4j Knowledge Graph")]
    
    AGT_SOP & AGT_POL & AGT_EXT & AGT_INT --> RESP["Synthesized Response"]
    RESP --> USER
```

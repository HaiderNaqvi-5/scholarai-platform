# ScholarAI — Knowledge Graph Design

> **Description:** The Neo4j graph database acts as **Stage 1 of the Hybrid Recommendation Pipeline**, serving as a rigid, deterministic eligibility filter before the semantic vector search takes over.

---

## 1. Graph Concept & Architecture

The graph models the scholarship domain natively. It connects students to scholarships indirectly through requirements (e.g., a student "HOLDING" a specific citizenship is connected to a scholarship "REQUIRING" that citizenship).

This allows instantaneous, 100% accurate filtering. A student will never see a Canadian MS AI scholarship if they don't hold the correct citizenship or degree prerequisites.

## 2. Node Types (Labels)

| Label | Description | Key Properties |
|---|---|---|
| `Student` | The applicant. | `id`, `name`, `gpa` |
| `Scholarship` | The funding opportunity. | `id`, `name`, `deadline`, `min_gpa_req` |
| `Degree` | MS, BS, PhD. MVP is restricted to **MS**. | `name` |
| `FieldOfStudy` | Academic disciplines. MVP is restricted to **Data Science, AI, Analytics**. | `name` |
| `Country` | Geographic locations. MVP is restricted to **Canada**. | `name`, `iso_code` |
| `Skill` | Required hard/soft skills parsed from descriptions. | `name` |

## 3. Relationship Types (Edges)

| Source Node | Edge | Target Node | Properties |
|---|---|---|---|
| `Student` | `HAS_CITIZENSHIP` | `Country` | |
| `Student` | `SEEKS_DEGREE` | `Degree` | |
| `Student` | `INTERESTED_IN` | `FieldOfStudy` | |
| `Scholarship` | `HOSTED_IN` | `Country` | |
| `Scholarship` | `AWARDS_DEGREE` | `Degree` | |
| `Scholarship` | `FUNDS_FIELD` | `FieldOfStudy` | |
| `Scholarship` | `REQUIRES_CITIZENSHIP`| `Country` | `is_mandatory` (boolean) |

## 4. Cypher Schema Examples

### Node Creation
```cypher
// Create constrained fields for MVP
CREATE (ds:FieldOfStudy {name: "Data Science"})
CREATE (ai:FieldOfStudy {name: "Artificial Intelligence"})
CREATE (an:FieldOfStudy {name: "Analytics"})

CREATE (can:Country {name: "Canada"})
CREATE (ms:Degree {name: "MS"})

// Create a scholarship
CREATE (s:Scholarship {id: "uuid-1234", name: "Vector Institute AI Scholarship", min_gpa_req: 3.5})
MERGE (s)-[:HOSTED_IN]->(can)
MERGE (s)-[:AWARDS_DEGREE]->(ms)
MERGE (s)-[:FUNDS_FIELD]->(ai)
```

### Stage 1: Eligibility Filtering Query
*This query finds scholarships the student is fundamentally eligible for before passing the subgraph IDs back to PostgreSQL for pgvector Stage 2 calculations.*

```cypher
MATCH (student:Student {id: $student_id})
// Find scholarships matching the student's desired degree
MATCH (student)-[:SEEKS_DEGREE]->(deg:Degree)<-[:AWARDS_DEGREE]-(scholar:Scholarship)
// Find scholarships matching the student's field of study
MATCH (student)-[:INTERESTED_IN]->(field:FieldOfStudy)<-[:FUNDS_FIELD]-(scholar)
// Verify GPA boundary
WHERE student.gpa >= scholar.min_gpa_req

// Ensure the scholarship is in the target country (MVP: Canada)
MATCH (scholar)-[:HOSTED_IN]->(country:Country {name: "Canada"})

RETURN scholar.id, scholar.name
```

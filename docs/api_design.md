# ScholarAI — API Design

> **Framework:** FastAPI (Python 3.11+)  
> **Base URL:** `/api/v1`  
> **Authentication:** JWT Bearer tokens  
> **Documentation:** Auto-generated at `/docs` (Swagger) and `/redoc`

---

## 1. Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Register new user | Public |
| POST | `/auth/login` | Login → returns JWT | Public |
| POST | `/auth/refresh` | Refresh access token | Refresh token |
| GET | `/auth/me` | Current user profile | Bearer |

---

## 2. Student Profile

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/profile` | Get student profile | Student |
| PUT | `/profile` | Update student profile | Student |
| POST | `/profile/sop` | Upload/update SOP draft | Student |

---

## 3. Scholarship Discovery & Matching

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/scholarships` | List scholarships (paginated, filterable) | Bearer |
| GET | `/scholarships/{id}` | Scholarship detail | Bearer |
| POST | `/scholarships/match` | **AI matching** — ranked list with scores | Student |
| GET | `/scholarships/{id}/explanation` | SHAP explanation for match | Student |

### `POST /scholarships/match` — Request

```json
{
  "student_id": "uuid",
  "filters": {
    "countries": ["Germany", "Netherlands"],
    "degree_level": "master",
    "min_funding": 10000,
    "deadline_after": "2026-06-01"
  },
  "limit": 20
}
```

### Response

```json
{
  "matches": [
    {
      "scholarship_id": "uuid",
      "scholarship_name": "DAAD Research Grant",
      "match_score": 89.2,
      "success_probability": 53.1,
      "top_contributing_features": [
        {"feature": "gpa", "contribution": 32.1},
        {"feature": "research_publications", "contribution": 18.5},
        {"feature": "field_match", "contribution": 15.3}
      ]
    }
  ],
  "model_version": "v1.2.0",
  "computed_at": "2026-03-08T12:00:00Z"
}
```

---

## 4. Credentials (Blockchain)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/credentials/upload` | Upload document for verification | Student |
| GET | `/credentials` | List student credentials | Student |
| POST | `/credentials/{id}/verify` | Institution verifies document | University |
| GET | `/credentials/{id}/blockchain-status` | On-chain verification status | Bearer |

---

## 5. Interview Simulator

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/interview/start` | Start interview session | Student |
| POST | `/interview/{id}/submit-audio` | Submit audio response | Student |
| GET | `/interview/{id}/feedback` | Get AI feedback | Student |
| GET | `/interview/history` | Past interview sessions | Student |

### `POST /interview/start` — Request

```json
{
  "scholarship_id": "uuid (optional)",
  "interview_type": "general",
  "difficulty": "intermediate"
}
```

### Response

```json
{
  "session_id": "uuid",
  "questions": [
    {
      "id": 1,
      "text": "Tell us about your research experience and how it aligns with this scholarship.",
      "time_limit_seconds": 120,
      "evaluation_criteria": ["relevance", "specificity", "confidence"]
    }
  ]
}
```

---

## 6. Mentorship

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/mentors` | List available mentors (filterable) | Bearer |
| GET | `/mentors/{id}` | Mentor profile | Bearer |
| POST | `/mentorship/request` | Request session | Student |
| PUT | `/mentorship/{id}/rate` | Rate completed session | Student |

---

## 7. SOP Assistant

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/sop/analyze` | Analyze SOP for improvements | Student |
| POST | `/sop/generate-suggestions` | AI improvement suggestions | Student |
| POST | `/sop/tailor` | Tailor SOP for specific scholarship | Student |

---

## 8. Admin

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/admin/users` | List/search users | Admin |
| PUT | `/admin/users/{id}/status` | Activate/deactivate user | Admin |
| GET | `/admin/mentors/pending` | Pending mentor approvals | Admin |
| PUT | `/admin/mentors/{id}/approve` | Approve/reject mentor | Admin |
| GET | `/admin/scrapers` | Scraper run history | Admin |
| POST | `/admin/scrapers/trigger` | Trigger scraper manually | Admin |
| GET | `/admin/analytics` | Platform analytics | Admin |

---

## Error Response Format

```json
{
  "error": {
    "code": "SCHOLARSHIP_NOT_FOUND",
    "message": "Scholarship with id '...' not found",
    "status": 404
  }
}
```

## Pagination

All list endpoints support:
- `?page=1&per_page=20` — offset-based pagination
- Response includes `total`, `page`, `per_page`, `total_pages`

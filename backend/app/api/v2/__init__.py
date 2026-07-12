from fastapi import APIRouter

from app.api.v1.routes import analytics, documents, interview, recommendations, scholarships, students

# broken-#3 (2026-07-10): `/api/v2` is a TEMPORARY ALIAS of v1, not an
# independently-evolvable surface. It re-mounts the same v1 route objects
# under a new prefix so `Link: </api/v2>; rel="successor-version"` (see
# main.py's deprecation middleware) resolves to something live, without
# committing to a real v2 contract yet. Do NOT add v2-only routes or fork
# these handlers here — that's a new feature (parallel v2 routers), not a
# fix, and needs its own product decision first. The one thing v2 must NOT
# inherit from v1 is the Deprecation/Sunset headers; main.py's middleware
# gates strictly on `API_V1_PREFIX`, not `API_V2_PREFIX`, so this alias
# stays undeprecated by construction. Pinned by
# tests/integration/test_api_versioning.py.
router = APIRouter()

router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations v2"])
router.include_router(documents.router, prefix="/documents", tags=["Documents v2"])
router.include_router(interview.router, prefix="/interviews", tags=["Interview Practice v2"])
router.include_router(students.router, prefix="/profile", tags=["Student Profile v2"])
router.include_router(scholarships.router, prefix="/scholarships", tags=["Scholarships v2"])
router.include_router(analytics.router, prefix="/analytics", tags=["Admin Analytics v2"])

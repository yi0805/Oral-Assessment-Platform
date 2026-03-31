"""
Central API router — aggregates all route modules under /api/v1.

Route prefixes
--------------
/auth         Authentication (Google OAuth, JWT, user profile)
/courses      Course management and enrollment
(none)        Materials, rubrics, questions, assessments, sessions, feedback
              — these route files declare their own full paths because they
                span multiple resource prefixes (e.g. /courses/:id/materials
                and /materials/:id in the same file).
"""
from fastapi import APIRouter

from app.api.routes import (
    assessments,
    auth,
    courses,
    feedback,
    materials,
    questions,
    rubrics,
    sessions,
)

api_router = APIRouter()

api_router.include_router(auth.router,        prefix="/auth",    tags=["Auth"])
api_router.include_router(courses.router,     prefix="/courses", tags=["Courses"])
api_router.include_router(materials.router,   prefix="",         tags=["Materials"])
api_router.include_router(rubrics.router,     prefix="",         tags=["Rubrics"])
api_router.include_router(questions.router,   prefix="",         tags=["Questions"])
api_router.include_router(assessments.router, prefix="",         tags=["Assessments"])
api_router.include_router(sessions.router,    prefix="",         tags=["Sessions"])
api_router.include_router(feedback.router,    prefix="",         tags=["Feedback"])

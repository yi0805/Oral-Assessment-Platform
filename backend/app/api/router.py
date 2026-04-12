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

# swagger ui display and url prefix for each router

api_router = APIRouter()

api_router.include_router(auth.router,        prefix="/auth",    tags=["Auth"])
api_router.include_router(courses.router,     prefix="/courses", tags=["Courses"])
api_router.include_router(materials.router,   prefix="",         tags=["Materials"])
api_router.include_router(rubrics.router,     prefix="",         tags=["Rubrics"])
api_router.include_router(questions.router,   prefix="",         tags=["Questions"])
api_router.include_router(assessments.router, prefix="",         tags=["Assessments"])
api_router.include_router(sessions.router,    prefix="",         tags=["Sessions"])
api_router.include_router(feedback.router,    prefix="",         tags=["Feedback"])

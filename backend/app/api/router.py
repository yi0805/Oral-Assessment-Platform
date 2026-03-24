"""
Central API router — aggregates all route modules.

This file is imported by app/main.py to register all endpoints.

Each route file in routes/ handles one domain of the API contract.

"""
from fastapi import APIRouter

# TODO: Import and include each route module as it's built
# from app.api.routes import auth, courses, materials, rubrics
# from app.api.routes import questions, assessments, sessions, feedback

api_router = APIRouter()

# TODO: Uncomment as routes are implemented
# api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
# api_router.include_router(materials.router, prefix="", tags=["Materials"])
# api_router.include_router(rubrics.router, prefix="", tags=["Rubrics"])
# api_router.include_router(questions.router, prefix="", tags=["Questions"])
# api_router.include_router(assessments.router, prefix="", tags=["Assessments"])
# api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
# api_router.include_router(feedback.router, prefix="", tags=["Feedback"])

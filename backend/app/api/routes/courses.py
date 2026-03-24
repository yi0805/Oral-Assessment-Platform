"""
Course management routes.



Endpoints:
  POST /courses → create a new course (instructor only)
  GET /courses → list courses for current user
  GET /courses/:id → get course details
  POST /courses/:id/enroll → enroll user in course
  GET /courses/:id/students → list enrolled students

TODO:
- [ ] POST /courses with CourseCreate schema
- [ ] GET /courses filtered by current user's enrollments
- [ ] GET /courses/:id with enrollment check
- [ ] POST /courses/:id/enroll (instructor-only)
"""
from fastapi import APIRouter

router = APIRouter()

# TODO: Implement course endpoints

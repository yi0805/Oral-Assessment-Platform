from pydantic import BaseModel, Field, model_validator
from typing import List
from uuid import UUID

# Rubrics are fixed at 100 points to consistent with the rest of the application
RUBRIC_TOTAL_POINTS = 100


# Single criteria
class RubricCriteriaItem(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    max_points: int = Field(gt=0)


# Rubric Form
class RubricCreate(BaseModel):
    total_points: int = RUBRIC_TOTAL_POINTS
    criteria_data: List[RubricCriteriaItem] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_total_points(self) -> "RubricCreate":
        if self.total_points != RUBRIC_TOTAL_POINTS:
            raise ValueError(
                f"total_points must equal {RUBRIC_TOTAL_POINTS}."
            )

        submitted_sum = sum(item.max_points for item in self.criteria_data)
        if submitted_sum != RUBRIC_TOTAL_POINTS:
            raise ValueError(
                f"Criteria max_points must sum to {RUBRIC_TOTAL_POINTS}, got {submitted_sum}."
            )

        return self


# Rubric Form Response
class RubricOut(RubricCreate):
    id: UUID

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import List
from uuid import UUID

# Single criteria 
class RubricCriteriaIteam(BaseModel):
    title: str          # "Part 1"
    description: str    # Criteria content
    max_points: int     # 20 points for Part 1

# Rubric Form Request
class RubricCreate(BaseModel):
    total_points: int = 100
    criteria_data: List[RubricCriteriaIteam] # Contains multiple criteria

# Rubric Form Response
class RubricOut(RubricCreate):
    id: UUID
    assessment_config_id: UUID

    class Config:
        from_attributes = True
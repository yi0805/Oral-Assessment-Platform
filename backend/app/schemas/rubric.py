from pydantic import BaseModel
from typing import List
from uuid import UUID

# Single criteria 
class RubricCriteriaIteam(BaseModel):
    title: str
    description: str
    max_points: int

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
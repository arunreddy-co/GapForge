"""
Pydantic schemas for study plan generation input and output.
"""
from typing import Dict, List, Literal
from pydantic import BaseModel, Field

from schemas.diagnostic import DiagnosticOutput


class DailyTask(BaseModel):
    """Schema for a single task within a study plan."""
    day: int = Field(ge=1)
    topic: str
    resource_url: str
    resource_type: Literal["video", "notes", "practice"]
    alternate_resource_url: str
    duration_minutes: int = Field(ge=15, le=240)
    description: str
    milestone_quiz: bool


class PlannerOutput(BaseModel):
    """Gemini structured output schema for the generated study plan."""
    total_days: int
    daily_tasks: List[DailyTask] = Field(min_length=1)
    milestone_days: List[int] = Field(min_length=1)
    spaced_recall_map: Dict[str, List[str]]
    improvement_baseline: float = Field(ge=0.0, le=1.0)


class PlanRequest(BaseModel):
    """Schema for requesting a new study plan."""
    student_id: str
    subject: str
    goal: str
    daily_hours: float = Field(gt=0)
    diagnostic_output: DiagnosticOutput


class PlanResponse(BaseModel):
    """Schema for responding with the final study plan."""
    student_id: str
    subject: str
    total_days: int
    milestone_days: List[int]
    daily_tasks: List[DailyTask]
    message: str

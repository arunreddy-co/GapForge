"""
Pydantic schemas for student input and response.
"""
from datetime import datetime
from typing import Dict, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudentCreate(BaseModel):
    """Schema for creating a new student profile."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    branch: str = Field(min_length=2, max_length=100)
    semester: int = Field(ge=1, le=8)
    daily_hours: float = Field(ge=0.5, le=12.0)
    goal: Literal["crack_interview", "pass_exam", "understand"]
    exam_date: str
    declared_levels: Dict[str, Literal["beginner", "basic", "intermediate", "advanced"]]

    @field_validator("exam_date")
    @classmethod
    def validate_future_date(cls, v: str) -> str:
        """Validate that the exam date is in the future."""
        try:
            exam_dt = datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("exam_date must be in YYYY-MM-DD format")
        
        if exam_dt <= datetime.today():
            raise ValueError("exam_date must be a future date")
        
        return v


class StudentResponse(BaseModel):
    """Schema for responding with student details."""
    student_id: str
    name: str
    goal: str
    message: str

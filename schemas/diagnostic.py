"""
Pydantic schemas for diagnostic assessment input, Gemini structured output, and diagnostic response.
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class AnswerSubmission(BaseModel):
    """Schema for a student submitting an answer to a diagnostic question."""
    student_id: str
    question_id: str
    student_answer: str = Field(min_length=1)
    time_taken_seconds: int = Field(ge=1, le=3600)


class ConceptFailure(BaseModel):
    """Schema detailing a concept failure identified during the diagnostic."""
    concept: str
    evidence: str
    severity: Literal["critical", "moderate", "minor"]


class DiagnosticOutput(BaseModel):
    """Gemini structured output schema for the diagnostic evaluation."""
    declared_level: str
    verified_level: Literal[
        "beginner",
        "basic", 
        "intermediate",
        "advanced"
    ]
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=20)
    concept_failures: List[ConceptFailure]
    root_cause_topic: str
    recommended_start_point: str
    time_pattern_note: Optional[str] = None


class DiagnosticRequest(BaseModel):
    """Schema for requesting a diagnostic assessment."""
    student_id: str
    subject: str
    declared_level: str


class DiagnosticResponse(BaseModel):
    """Schema for the final diagnostic response to the student."""
    student_id: str
    subject: str
    declared_level: str
    verified_level: str
    confidence_score: float
    reasoning: str
    root_cause_topic: str
    recommended_start_point: str
    questions_asked: int

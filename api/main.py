"""
GapForge FastAPI application.
Exposes the core routing layer for student onboarding, diagnostic assessment,
and pipeline orchestration as deployed API endpoints.
"""
import json
import logging
import os
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.orchestrator import onboard_student, run_full_pipeline
from schemas.student import StudentCreate, StudentResponse
from db.queries import get_student as db_get_student

# PART 1 — App Setup
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager for startup and shutdown execution."""
    logger.info("GapForge API starting...")
    yield
    logger.info("GapForge API shutting down...")

app = FastAPI(
    title="GapForge API",
    description="AI-powered adaptive diagnostic learning engine for CS students",
    version="1.0.0",
    lifespan=lifespan
)

# PART 2 — CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/app",
         response_class=HTMLResponse)
async def serve_frontend():
    """Serve the GapForge frontend."""
    html_path = os.path.join(
        os.path.dirname(__file__),
        "..", "static", "index.html"
    )
    with open(html_path, "r") as f:
        return f.read()


# PART 3 — Health Check Endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Check the running status of the API.
    """
    return {
        "status": "healthy",
        "service": "GapForge API",
        "version": "1.0.0"
    }


# PART 4 — Onboard Student Endpoint
@app.post("/students", response_model=StudentResponse)
async def create_student(student: StudentCreate) -> StudentResponse:
    """
    Register a new student within the system and initiate their profile.
    """
    try:
        return onboard_student(
            name=student.name,
            branch=student.branch,
            semester=student.semester,
            daily_hours=student.daily_hours,
            goal=student.goal,
            exam_date=student.exam_date,
            declared_levels=student.declared_levels
        )
    except Exception as e:
        logger.error("Failed to onboard student: %s", e)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# PART 5 — Run Diagnostic Endpoint
class FullDiagnosticRequest(BaseModel):
    """Inline request model unifying diagnostic payloads and user answers."""
    student_id: str
    subject: str
    declared_level: str
    goal: str
    daily_hours: float
    answers: List[Dict[str, Any]]


@app.post("/diagnose")
async def run_diagnostic_endpoint(request: FullDiagnosticRequest) -> Dict[str, Any]:
    """
    Execute the entire analytical pipeline, encompassing the diagnostic sweep 
    and generating the study plan based on student answers.
    """
    try:
        return run_full_pipeline(
            student_id=request.student_id,
            subject=request.subject,
            declared_level=request.declared_level,
            goal=request.goal,
            daily_hours=request.daily_hours,
            answers=request.answers
        )
    except Exception as e:
        logger.error("Failed to process diagnostic endpoint: %s", e)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# PART 6 — Get Student Endpoint
@app.get("/students/{student_id}")
async def get_student(student_id: str) -> Dict[str, Any]:
    """
    Retrieve the student's profile utilizing robust JSON formatting for UUIDs.
    """
    result = db_get_student(student_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Student not found: {student_id}"
        )
        
    return json.loads(json.dumps(result, default=str))


@app.get("/questions/diagnostic")
async def get_diagnostic_questions(
    subject: str,
    declared_level: str,
    student_id: str = ""
) -> List[Dict[str, Any]]:
    """
    Get 5 diagnostic questions for a subject
    and difficulty level. Returns questions
    the student has not seen before.
    One question per top topic by
    marks_weightage.
    """
    from db.queries import get_questions, \
        get_topics_by_subject
    import json

    topics = get_topics_by_subject(subject)
    if not topics:
        raise HTTPException(
            status_code=404,
            detail=f"No topics for {subject}"
        )

    difficulty_order = {
        "beginner": ["beginner", "basic"],
        "basic": ["basic", "beginner",
                  "intermediate"],
        "intermediate": ["intermediate",
                         "basic", "advanced"],
        "advanced": ["advanced",
                     "intermediate", "basic"]
    }
    allowed = difficulty_order.get(
        declared_level, ["basic", "intermediate"])

    filtered_topics = [
        t for t in topics
        if t["difficulty"] in allowed
    ]
    top_topics = filtered_topics[:5]

    if len(top_topics) < 5:
        top_topics = topics[:5]
    questions = []
    exclude_ids = []

    for topic in top_topics:
        topic_id = str(topic["id"])
        q_list = get_questions(
            subject=subject,
            difficulty=declared_level,
            count=1,
            exclude_ids=exclude_ids
        )
        if q_list:
            q = q_list[0]
            exclude_ids.append(str(q["id"]))
            questions.append(
                json.loads(
                    json.dumps(q, default=str)
                )
            )

    return questions


# PART 7 — Root Endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """
    Landing endpoint providing basic operational paths.
    """
    return {
        "service": "GapForge",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

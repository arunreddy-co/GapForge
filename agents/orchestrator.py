"""
OrchestratorAgent implementation for GapForge.
Main entry point coordinating the complete pipeline sequence from student
onboarding to diagnostic assessment and final study plan generation.
"""
import logging
from typing import Dict, Any, List

from google.adk.agents import Agent

from agents.diagnostic import diagnostic_agent, run_diagnostic
from agents.planner import planner_agent, run_planner
import db.queries
from schemas.student import StudentResponse

# Module-level logger setup
logger = logging.getLogger(__name__)


def onboard_student(
    name: str,
    branch: str,
    semester: int,
    daily_hours: float,
    goal: str,
    exam_date: str,
    declared_levels: Dict[str, str]
) -> StudentResponse:
    """
    Onboard a new student into the GapForge system.
    
    Registers the student in the database. Note that declared_levels are ignored
    at this step as they are heavily utilized later in the diagnostic phase.
    
    Args:
        name: Name of the student.
        branch: Academic branch or major.
        semester: Current academic semester (1-8).
        daily_hours: Daily time commitment in hours.
        goal: The designated GapForge goal (e.g. crack_interview, pass_exam).
        exam_date: Encoded target date String.
        declared_levels: Student's self-assessed confidence per subject.

    Returns:
        Structured StudentResponse confirming the onboarding.
    """
    logger.info("Onboarding student %s...", name)
    
    # 1. Call db.queries.create_student() with all fields.
    # Ignore declared_levels for now, as it will be used during the diagnostic step.
    new_id = db.queries.create_student(
        name=name,
        branch=branch,
        semester=semester,
        daily_hours=daily_hours,
        goal=goal,
        exam_date=exam_date
    )
    
    # 2. Return StudentResponse
    return StudentResponse(
        student_id=str(new_id),
        name=name,
        goal=goal,
        message=f"Welcome {name}. Profile created. Ready for diagnostic."
    )


def run_full_pipeline(
    student_id: str,
    subject: str,
    declared_level: str,
    goal: str,
    daily_hours: float,
    answers: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Execute the entire GapForge intelligence pipeline for a specific student.
    
    Routes through the runtime endpoints for the diagnostic toolset to map skill
    limitations and finally pipes the conclusions straight into the planner sequence
    to return a highly contextualized schedule.
    
    Args:
        student_id: UUID of the onboarded student.
        subject: Target concept set (e.g., 'DSA').
        declared_level: Student's starting baseline guess.
        goal: Student's long-term motivation parameter.
        daily_hours: Committing metric.
        answers: Formatted dictionary answers returned from UI.
        
    Returns:
        A dictionary containing dumped models of both diagnostic and plan phases,
        as well as a status confirmation message.
        
    Raises:
        RuntimeError: If the student does not exist.
    """
    logger.info("Running full pipeline for student %s on %s...", student_id, subject)
    
    # 1. Check student exists
    student = db.queries.get_student(student_id)
    if not student:
        raise RuntimeError(f"Student not found: {student_id}")
        
    # 2. Call run_diagnostic
    diagnostic_result = run_diagnostic(
        student_id=student_id,
        subject=subject,
        declared_level=declared_level,
        goal=goal,
        daily_hours=daily_hours,
        answers=answers
    )
    
    # 3. Call run_planner
    plan_result = run_planner(
        student_id=student_id,
        subject=subject,
        goal=goal,
        daily_hours=daily_hours,
        diagnostic=diagnostic_result
    )
    
    # 4. Return combined dict execution
    return {
        "diagnostic": diagnostic_result.model_dump(),
        "plan": plan_result.model_dump(),
        "status": "complete",
        "message": f"GapForge analysis complete for {subject}. "
                   f"Your {plan_result.total_days}-day plan starts with {diagnostic_result.recommended_start_point}."
    }


# PART 4: ADK Agent Definition
orchestrator_agent = Agent(
    name="orchestrator_agent",
    model="gemini-2.5-flash",
    description="Main GapForge coordinator. Routes students through onboarding, diagnostic assessment, and study plan generation",
    instruction="""
      You are the OrchestratorAgent for GapForge — the main coordinator.

      You manage the complete student journey in this exact order:
      1. Onboard student via onboard_student()
      2. Run diagnostic via run_full_pipeline()
      3. Return complete results

      Never skip steps.
      Never call Gemini directly.
      Delegate all intelligence to diagnostic_agent and planner_agent.

      If any step fails, return the error clearly. Never silently swallow errors.
    """,
    tools=[
        onboard_student,
        run_full_pipeline
    ],
    sub_agents=[
        diagnostic_agent,
        planner_agent
    ]
)

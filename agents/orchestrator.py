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
from agents.content import (
    content_agent,
    run_content_enrichment
)
import db.queries
from schemas.student import StudentResponse
from mcp_servers.notion_planner import create_study_roadmap

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

    # Fix resource URLs from AlloyDB
    topics_list = db.queries.get_topics_by_subject(
        subject)
    topic_url_map = {
        t["topic_name"]: {
            "resource_url": str(
                t.get("resource_url", "")),
            "resource_type": str(
                t.get("resource_type", "video")),
            "alternate_resource_url": str(
                t.get("alternate_resource_url") or
                t.get("resource_url", ""))
        }
        for t in topics_list
    }

    logger.info(
        "Sample URL map entry: %s",
        next(iter(topic_url_map.items()),
        None))

    corrected_tasks = []
    for task in plan_result.daily_tasks:
        topic_data = topic_url_map.get(
            task.topic)
        if topic_data:
            from schemas.plan import DailyTask
            corrected = DailyTask(
                day=task.day,
                topic=task.topic,
                resource_url=topic_data[
                    "resource_url"],
                resource_type=topic_data[
                    "resource_type"],
                alternate_resource_url=topic_data[
                    "alternate_resource_url"],
                duration_minutes=task
                    .duration_minutes,
                description=task.description,
                milestone_quiz=task.milestone_quiz
            )
            corrected_tasks.append(corrected)
        else:
            corrected_tasks.append(task)

    from schemas.plan import PlanResponse
    plan_result = PlanResponse(
        student_id=plan_result.student_id,
        subject=plan_result.subject,
        total_days=plan_result.total_days,
        milestone_days=plan_result.milestone_days,
        daily_tasks=corrected_tasks,
        message=plan_result.message
    )
    
    # Step 3.5: Enrich with WHY explanations
    why_explanations = {}
    try:
        why_explanations = run_content_enrichment(
            subject=subject,
            goal=goal,
            root_cause_topic=diagnostic_result
                .root_cause_topic,
            verified_level=diagnostic_result
                .verified_level,
            daily_tasks=corrected_tasks
        )
        logger.info(
            "Content enrichment complete: "
            "%d topics enriched",
            len(why_explanations)
        )
    except Exception as e:
        logger.error(
            "Content enrichment failed: %s", e)

    # Get Notion page URL if available
    notion_url = None
    try:
        task_dicts = []
        for task in plan_result.daily_tasks:
            d = task.model_dump()
            d["why_learn"] = why_explanations.get(
                task.topic, "")
            task_dicts.append(d)
        notion_result = create_study_roadmap(
            student_name=student_id,
            subject=subject,
            verified_level=diagnostic_result.verified_level,
            root_cause_topic=diagnostic_result.root_cause_topic,
            total_days=plan_result.total_days,
            daily_tasks=task_dicts,
            milestone_days=plan_result.milestone_days
        )
        notion_url = notion_result.get("notion_page_url")
        logger.info("Notion page: %s", notion_url)
    except Exception as e:
        logger.error("Notion failed: %s", e)

    # 4. Return combined dict execution
    return {
        "diagnostic": diagnostic_result.model_dump(),
        "plan": plan_result.model_dump(),
        "status": "complete",
        "notion_page_url": notion_url,
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
        planner_agent,
        content_agent
    ]
)

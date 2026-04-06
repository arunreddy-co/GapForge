"""
PlannerAgent implementation for GapForge.
Takes diagnostic results and generates an actionable, personalized study plan
using curated topics and spaced repetition mapping.
"""
import json
import logging
from typing import List, Dict, Any

from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed
from google.genai import Client
from google.genai.types import GenerateContentConfig
from google.adk.agents import Agent

import db.queries
from db.connection import settings
from schemas.diagnostic import DiagnosticResponse
from schemas.plan import PlannerOutput, PlanResponse

# Module-level logger setup
logger = logging.getLogger(__name__)

# Initialize genai.Client using Vertex AI and db.connection settings
client = Client(
    vertexai=True,
    project=settings.GOOGLE_CLOUD_PROJECT,
    location=settings.GOOGLE_CLOUD_LOCATION
)

# Reasoning Prompt Constant
PLANNER_PROMPT = """
You are an expert CS learning path designer.

Generate a personalized study plan for this
student based on their diagnostic results.

Student Profile:
- Student ID: {student_id}
- Subject: {subject}
- Goal: {goal}
- Daily study hours: {daily_hours}
- Verified level: {verified_level}
- Root cause gap: {root_cause_topic}
- Recommended start: {recommended_start_point}
- Confidence score: {confidence_score}

Available Topics (ordered by importance):
{topics_json}

RESOURCE SELECTION RULES:
- Use resource_url from topics table only.
  Never invent URLs.
- Match resource_type to goal:
  crack_interview → practice first
  pass_exam → notes and past questions first
  understand → video first
  freelance → project-based first
- Always provide alternate_resource_url
  from a different topic at same level.
  If none exists use the same URL.
- resource_url must always be the
  YouTube video URL
- alternate_resource_url must always
  be the GFG notes URL
- Never use a YouTube URL as
  alternate_resource_url
- Never use a GFG URL as resource_url
- Match by resource_type field:
  resource_type="video" → resource_url
  resource_type="notes" → alternate_resource_url

DAILY PLAN RULES:
- Each day: 1 topic only
- duration_minutes = daily_hours * 60 * 0.8
  Round to nearest 15 minutes.
- Start from root_cause_topic always.
  Never skip prerequisites.
- milestone_quiz = True every 3 days.

SPACED RECALL RULES:
- spaced_recall_map keys are day numbers
  as strings.
- Day 4+: always include topics from
  days 1-3 in spaced_recall_map.
- Day 7+: include topics from days 1-6.
- Pattern: current day topics + all
  previous milestone topics.

CONFIDENCE ADJUSTMENT:
- confidence_score below 0.6:
  add 2 extra revision days at start
- confidence_score above 0.85:
  can skip beginner topics if covered

OUTPUT rules:
- Return structured JSON only.
- No preamble. No explanation outside JSON.
- daily_tasks must have at least 1 item.
- milestone_days must have at least 1 item.
- improvement_baseline = confidence_score
  from diagnostic.
- description for each day must be
  maximum 1 sentence. No more.
- Do not include spaced_recall_map
  if it makes the response too long.
  Set it to empty dict if needed.
- Keep total response under 3000 tokens.
"""

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def call_gemini_planner(prompt: str) -> PlannerOutput:
    """
    Call the Gemini LLM to process the diagnostic data and generate a study plan.
    
    Uses GenerateContentConfig to enforce JSON schema output. Validates the response
    with pydantic. On failure, raises a RuntimeError containing the initial slice of 
    the raw output for debugging.

    Args:
        prompt: Formatted prompt containing student data and available topics.

    Returns:
        A validated PlannerOutput object.
        
    Raises:
        RuntimeError: If schema validation fails.
    """
    logger.info("Calling Gemini for study plan generation...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PlannerOutput,
            temperature=0.2,
            max_output_tokens=8192,
        )
    )
    
    try:
        return PlannerOutput.model_validate_json(response.text)
    except ValidationError as e:
        raw_snippet = response.text[:200] if response and response.text else "No response"
        raise RuntimeError(f"Validation Error: {str(e)}\nRaw Response Snippet: {raw_snippet}")
    except Exception as e:
        raw_snippet = response.text[:500] \
            if response and response.text \
            else "No response"
        logger.error(
            "Planner validation failed. "
            "Error: %s. Raw: %s",
            str(e), raw_snippet
        )
        raise RuntimeError(
            f"Planner failed: {str(e)}"
        ) from e


def run_planner(
    student_id: str,
    subject: str,
    goal: str,
    daily_hours: float,
    diagnostic: DiagnosticResponse
) -> PlanResponse:
    """
    Generate a personalized study plan leveraging the diagnostic results.
    
    This function pulls available topics for the given subject, serializes them, 
    injects them alongside the diagnostic payload into the Planner prompt, 
    and asks Gemini to construct a curriculum sequence.
    
    Args:
        student_id: UUID of the student.
        subject: Subject identifier (e.g., 'DSA').
        goal: The student's learning goal.
        daily_hours: Hours committed daily by the student.
        diagnostic: The complete diagnostic payload generated prior to this step.
        
    Returns:
        A complete PlanResponse containing the schedule and timeline.
        
    Raises:
        RuntimeError: If no topics are found for the requested subject.
    """
    # Step 1: Fetch topics
    topics = db.queries.get_topics_by_subject(subject)
    if not topics:
        raise RuntimeError(f"No topics found for subject: {subject}")
        
    # Step 2: Build topics_json
    topics_trimmed = [
        {
            "topic_name": t["topic_name"],
            "difficulty": t["difficulty"],
            "marks_weightage": t["marks_weightage"],
            "resource_url": t["resource_url"],
            "resource_type": t["resource_type"],
            "alternate_resource_url": t.get(
                "alternate_resource_url", "")
        }
        for t in topics
    ]
    topics_json = json.dumps(
        topics_trimmed,
        indent=2,
        default=str
    )
    
    # Step 3: Build complete prompt
    prompt = PLANNER_PROMPT \
        .replace("{student_id}", student_id) \
        .replace("{subject}", subject) \
        .replace("{goal}", goal) \
        .replace("{daily_hours}",
                 str(daily_hours)) \
        .replace("{verified_level}",
                 diagnostic.verified_level) \
        .replace("{root_cause_topic}",
                 diagnostic.root_cause_topic) \
        .replace("{recommended_start_point}",
                 diagnostic.recommended_start_point) \
        .replace("{confidence_score}",
                 str(diagnostic.confidence_score)) \
        .replace("{topics_json}", topics_json)
    
    # Step 4: Call gemini
    planner_output = call_gemini_planner(prompt)
    
    # Step 5: Save study plan
    db.queries.save_study_plan(
        student_id=student_id,
        subject=subject,
        plan_json=planner_output.model_dump_json()
    )

    # Step 6: Return Response
    return PlanResponse(
        student_id=student_id,
        subject=subject,
        total_days=planner_output.total_days,
        milestone_days=planner_output.milestone_days,
        daily_tasks=planner_output.daily_tasks,
        message=f"Study plan generated for {subject}. Start with {diagnostic.recommended_start_point}."
    )


# PART 5: ADK Agent Definition
planner_agent = Agent(
    name="planner_agent",
    model="gemini-2.5-flash",
    description="Generates personalized study plans based on diagnostic results with free curated resources",
    instruction="""
      You are the PlannerAgent for GapForge.
      Your only job is to generate personalized study plans.

      When called use run_planner() to generate the plan.

      Never invent resource URLs.
      Always use URLs from the topics table.
      
      Always start the plan from the root cause topic identified by DiagnosticAgent.

      Return PlanResponse only.
    """,
    tools=[run_planner]
)

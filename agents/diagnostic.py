"""
DiagnosticAgent implementation for GapForge.
Handles adaptive diagnostic assessments, analyzes student's answer history,
identifies knowledge gaps, and determines the root cause prerequisite.
"""
import json
import logging
from typing import List, Dict, Any

from tenacity import retry, stop_after_attempt, wait_fixed
from pydantic import ValidationError
from google.genai import Client
from google.genai.types import GenerateContentConfig
from google.adk.agents import Agent

import db.queries
from db.connection import settings
from schemas.diagnostic import DiagnosticOutput, DiagnosticResponse, ConceptFailure

# Module-level logger setup
logger = logging.getLogger(__name__)

# Initialize genai.Client using Vertex AI and db.connection settings
client = Client(
    vertexai=True,
    project=settings.GOOGLE_CLOUD_PROJECT,
    location=settings.GOOGLE_CLOUD_LOCATION
)

# Reasoning Prompt Constant
DIAGNOSTIC_PROMPT = """
You are an expert learning diagnostician
for CS education.

Analyze this student's complete answer
history and reason about WHY they fail,
not just WHAT they got wrong.

Student Profile:
- Subject: {subject}
- Declared proficiency: {declared_level}
- Goal: {goal}
- Daily study hours: {daily_hours}

Answer History:
{answer_history_json}

Each entry has: question_text, topic_id,
difficulty, student_answer, correct_answer,
is_correct, time_taken_seconds.

DETERMINE verified_level using this logic:
- 4-5 correct at declared level → same level
- 2-3 correct at declared level → one level down
- 0-1 correct at declared level → two levels down

IMPORTANT: verified_level MUST be
exactly one of these 4 values only:
beginner, basic, intermediate, advanced
Never use any other word.

SEVERITY rules for concept_failures:
- critical: wrong on 2+ questions same concept
- moderate: wrong once, slow on related question
- minor: wrong once with no pattern

TIME PATTERN rule:
- Correct answer taking 3x average time =
  procedural uncertainty, NOT mastery.
  Flag this explicitly in time_pattern_note.

CONFIDENCE rules:
- Clear consistent pattern → 0.85 to 1.0
- Mixed signals → 0.60 to 0.84
- Insufficient data → 0.40 to 0.59
- Never output confidence above 0.95
  unless all 5 questions show clear pattern.

OUTPUT rules:
- reasoning must cite specific question text
  as evidence. Never generic statements.
- root_cause_topic must be the earliest
  broken prerequisite, not the surface error.
- Return structured JSON only.
- No preamble. No explanation outside JSON.
- reasoning field must be maximum
  2-3 sentences. NEVER quote full
  question text. Reference questions
  by number only (e.g. "Q3 showed...")
  Keep reasoning under 100 words.
"""

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1.5))
def call_gemini(prompt: str, temperature: float) -> DiagnosticOutput:
    """
    Call the Gemini LLM to process the assessment data and extract a DiagnosticOutput.
    
    Uses GenerateContentConfig to enforce JSON schema output. Validates the response
    with pydantic. On failure, raises a RuntimeError containing the initial slice of 
    the raw output for debugging.

    Args:
        prompt: Formatted prompt containing student answers and instructions.
        temperature: LLM temperature setting.

    Returns:
        A validated DiagnosticOutput object.
        
    Raises:
        RuntimeError: If schema validation fails.
    """
    logger.info("Calling Gemini for diagnostic analysis...")
    logger.debug("Sending prompt to Gemini: %s", prompt[:500])
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DiagnosticOutput,
            temperature=temperature,
            max_output_tokens=4096,
        )
    )
    logger.debug("Raw Gemini response: %s", response.text[:500] if response and response.text else "None")
    
    try:
        return DiagnosticOutput.model_validate_json(response.text)
    except Exception as e:
        raw_snippet = (response.text[:300]
            if response and response.text
            else "No response")
        logger.error(
            "Gemini validation failed. "
            "Error type: %s. "
            "Error: %s. "
            "Raw response snippet: %s",
            type(e).__name__, e, raw_snippet
        )
        raise RuntimeError(
            f"Gemini failed: {type(e).__name__}: "
            f"{str(e)}"
        ) from e


def run_diagnostic(
    student_id: str,
    subject: str,
    declared_level: str,
    goal: str,
    daily_hours: float,
    answers: List[Dict[str, Any]]
) -> DiagnosticResponse:
    """
    Run the adaptive diagnostic assessment to identify knowledge gaps.
    
    This function simulates evaluating a 5-question test according to the student's 
    declared skill level. It saves answers and calls Gemini to obtain a final 
    diagnostic profile.

    Args:
        student_id: UUID of the student.
        subject: Subject identifier (e.g., 'DSA').
        declared_level: The student's self-assessed level.
        goal: The student's long-term goal.
        daily_hours: Hourly commitment per day.
        answers: A list of dicts, each with question_id, student_answer, time_taken_seconds.

    Returns:
        A fully built DiagnosticResponse object.
    """
    # Step 1: Define difficulty map
    difficulty_map = {
        "beginner": ["beginner", "beginner", "basic", "beginner", "basic"],
        "basic": ["basic", "basic", "intermediate", "basic", "intermediate"],
        "intermediate": ["intermediate", "intermediate", "advanced", "basic", "advanced"],
        "advanced": ["advanced", "advanced", "advanced", "intermediate", "advanced"]
    }
    
    level_key = declared_level.lower()
    if level_key not in difficulty_map:
        level_key = "basic"
        
    levels_needed = difficulty_map[level_key]
    
    # Step 2: Fetch 5 questions total
    exclude_ids = []
    questions = []
    
    for diff in levels_needed:
        # We need each unique difficulty dynamically or just one by one to accumulate exclusions
        q_list = db.queries.get_questions(subject=subject, difficulty=diff, count=1, exclude_ids=exclude_ids)
        if q_list:
            q = q_list[0]
            questions.append(q)
            if "id" in q:
                exclude_ids.append(q["id"])
    
    if len(questions) < len(answers):
        answers = answers[:len(questions)]

    # Step 3 & 4: Simulate answer collection and build answer history
    answer_history = []
    
    topics_list = db.queries.get_topics_by_subject(subject)
    topic_id_to_name = {
        str(t["id"]): t["topic_name"]
        for t in topics_list
    }
    
    for idx, q in enumerate(questions):
        if idx < len(answers):
            ans = answers[idx]
            q_id = q.get("id") or ans.get("question_id")
            student_ans = ans.get("student_answer", "")
            time_taken = ans.get("time_taken_seconds", 0)
            
            # Fetch evaluation data
            eval_data = db.queries.get_question_evaluation_data(q_id)
            correct_ans = eval_data.get("correct_answer", "")
            
            is_correct = student_ans.strip().lower() == correct_ans.strip().lower()
            
            # Save to Database
            db.queries.save_assessment(
                student_id=student_id,
                question_id=q_id,
                student_answer=student_ans,
                time_taken_seconds=time_taken,
                is_correct=is_correct
            )
            
            # Build answer history entry
            answer_history.append({
                "question_text": q.get("question_text", ""),
                "topic_name": topic_id_to_name.get(
                    str(q.get("topic_id", "")),
                    "Unknown Topic"
                ),
                "difficulty": q.get("difficulty", ""),
                "student_answer": student_ans,
                "correct_answer": correct_ans,
                "is_correct": is_correct,
                "time_taken_seconds": time_taken
            })
            
    # Step 5: Build complete prompt
    prompt = DIAGNOSTIC_PROMPT.format(
        subject=subject,
        declared_level=declared_level,
        goal=goal,
        daily_hours=daily_hours,
        answer_history_json=json.dumps(answer_history, indent=2)
    )
    
    # Step 6: Call call_gemini
    output = call_gemini(prompt=prompt, temperature=0.2)
    
    # Step 7: Save skill profile
    db.queries.save_skill_profile(
        student_id=student_id,
        subject=subject,
        declared_level=declared_level,
        verified_level=output.verified_level,
        confidence_score=output.confidence_score,
        root_cause_topic=output.root_cause_topic
    )
    
    # Step 8: Return DiagnosticResponse
    return DiagnosticResponse(
        student_id=student_id,
        subject=subject,
        declared_level=declared_level,
        verified_level=output.verified_level,
        confidence_score=output.confidence_score,
        reasoning=output.reasoning,
        root_cause_topic=output.root_cause_topic,
        recommended_start_point=output.recommended_start_point,
        questions_asked=len(questions)
    )


# PART 5: ADK Agent Definition
diagnostic_agent = Agent(
    name="diagnostic_agent",
    model="gemini-2.5-flash",
    description="Runs adaptive diagnostic assessment and identifies knowledge gaps with root cause analysis",
    instruction="""
      You are the DiagnosticAgent for GapForge.
      Your only job is to run diagnostic assessments and identify exactly where a student's knowledge breaks.
      
      When called, use run_diagnostic() to complete the assessment.
      
      Never guess or fabricate results.
      Always base diagnosis on actual answer patterns and timing data.
      
      Return DiagnosticResponse only.
    """,
    tools=[run_diagnostic]
)

"""
ContentAgent implementation for GapForge.
Enriches study plans with personalized 'why_learn' explanations connecting each
topic to the student's diagnosed root cause.
"""
import json
import logging

from google.genai import Client
from google.genai.types import GenerateContentConfig
from google.adk.agents import Agent

from db.connection import settings

# Module-level logger setup
logger = logging.getLogger(__name__)

# PART 1 — Setup:
client = Client(
    vertexai=True,
    project=settings.GOOGLE_CLOUD_PROJECT,
    location=settings.GOOGLE_CLOUD_LOCATION
)

# PART 2 — CONTENT_PROMPT constant:
CONTENT_PROMPT = """
You are a CS learning advisor for
engineering students.

A student has been diagnosed with
knowledge gaps in {subject}.

Diagnostic summary:
- Root cause: {root_cause_topic}
- Verified level: {verified_level}
- Goal: {goal}

Their study plan covers these topics
in order:
{topics_list}

For each topic, write exactly ONE
sentence explaining WHY this student
specifically needs to learn it.
Connect it back to their root cause.
Make it personal and motivating.
Be specific — mention the root cause
topic by name.

Return ONLY this JSON:
{
  "explanations": {
    "TOPIC_NAME": "one sentence why"
  }
}

No preamble. No explanation outside JSON.
"""

# PART 3 — run_content_enrichment() function:
def run_content_enrichment(
    subject: str,
    goal: str,
    root_cause_topic: str,
    verified_level: str,
    daily_tasks: list
) -> dict:
    """
    Generates personalized 'why_learn' explanations for study plan topics.
    
    Args:
        subject: The subject of the study plan.
        goal: The student's learning goal.
        root_cause_topic: The diagnosed root cause of the knowledge gap.
        verified_level: The student's verified proficiency level.
        daily_tasks: A list of daily task objects or dictionaries.
        
    Returns:
        A dictionary mapping topic names to their explanation strings.
        Returns an empty dictionary if the enrichment fails.
    """
    # 1. Build topics_list as comma separated topic names from daily_tasks
    topics = []
    for task in daily_tasks:
        if hasattr(task, 'topic'):
            topics.append(task.topic)
        elif isinstance(task, dict) and 'topic' in task:
            topics.append(task['topic'])
            
    # Deduplicate while preserving order
    unique_topics = list(dict.fromkeys(topics))
    topics_list_str = ", ".join(unique_topics)

    # 2. Build prompt using CONTENT_PROMPT with .replace() not .format()
    prompt = CONTENT_PROMPT \
        .replace("{subject}", subject) \
        .replace("{root_cause_topic}", root_cause_topic) \
        .replace("{verified_level}", verified_level) \
        .replace("{goal}", goal) \
        .replace("{topics_list}", topics_list_str)

    # 3. Call Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,
            max_output_tokens=1024
        )
    )

    # 4. Parse response
    try:
        import json
        text = response.text.strip()
        data = json.loads(text)
        return data.get("explanations", {})
    except Exception as e:
        logger.error("Content enrichment failed: %s", e)
        return {}

# PART 4 — ADK Agent:
content_agent = Agent(
    name="content_agent",
    model="gemini-2.5-flash",
    description="""Enriches study plans with
      personalized why_learn explanations
      connecting each topic to the
      student's diagnosed root cause""",
    instruction="""
      You are the ContentAgent for GapForge.
      Your job is to explain WHY each topic
      matters for this specific student.
      Always connect explanations to the
      diagnosed root cause.
      Return explanations as JSON only.
    """,
    tools=[run_content_enrichment]
)
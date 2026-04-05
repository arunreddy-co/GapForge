"""
This script generates diagnostic MCQ questions for GapForge using Gemini and inserts them into AlloyDB.
"""

import json
import logging
import time
import uuid
from typing import List, Optional

from google.genai import Client
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed

from db.connection import get_db_connection, settings

# Module-level logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# PART 1 — Pydantic Schema for Gemini output
class MCQOption(BaseModel):
    text: str

class MCQQuestion(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: str
    tags: List[str]

class MCQBatch(BaseModel):
    questions: List[MCQQuestion]

# PART 2 — Gemini client setup
client = Client(
    vertexai=True,
    project=settings.GOOGLE_CLOUD_PROJECT,
    location=settings.GOOGLE_CLOUD_LOCATION
)

# PART 3 — QUESTION_PROMPT constant
QUESTION_PROMPT = """
You are generating diagnostic MCQ questions
for CS engineering students.

Topic: {topic_name}
Subject: {subject}
Difficulty: {difficulty}
Prerequisites: {prerequisites}

Generate exactly {count} MCQ questions.

QUESTION TYPES — generate in this mix:
- Q1: Direct application
  (tests if concept works in practice)
- Q2: Misconception trap
  (tests if student truly understands
  vs memorized)
- Q3: Prerequisite probe
  (tests if foundation exists)

RULES:
1. Each question has exactly 4 options
2. Exactly 1 option is correct
3. correct_answer must match one option
   exactly word for word
4. Explanation must be 1-2 sentences,
   genuinely corrective not just
   restating the answer
5. Tags must be concept-level:
   good: recursion, pointer-manipulation,
         rotation, balance-factor
   bad: {topic_name}, {subject}, easy, hard
6. Questions must require THINKING
   not just memorization
7. For intermediate/advanced: include
   at least 1 timing trap — a question
   where the obvious answer is wrong
8. Never use "all of the above" or
   "none of the above" as options
9. Options must be plain text only.
   NEVER prefix options with A., B., C.,
   D. or A), B), C), D) or any letter.
   Write the option content directly.
   BAD:  "A. Linear Search"
   GOOD: "Linear Search"

Return structured JSON only.
No preamble. No markdown.
"""

# PART 4 — generate_questions function
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2.0))
def generate_questions(
    topic_name: str,
    subject: str,
    difficulty: str,
    prerequisites: List[str],
    count: int = 3
) -> List[MCQQuestion]:
    """
    Generates MCQ questions using Gemini based on topic and prerequisites.
    
    Args:
        topic_name: Name of the topic.
        subject: Subject of the topic.
        difficulty: Difficulty level.
        prerequisites: List of prerequisite topic names.
        count: Number of questions to generate.
        
    Returns:
        List of valid MCQQuestion objects.
    """
    prompt = QUESTION_PROMPT.format(
        topic_name=topic_name,
        subject=subject,
        difficulty=difficulty,
        prerequisites=", ".join(prerequisites) if prerequisites else "None",
        count=count
    )
    
    config = GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=MCQBatch,
        temperature=0.4,
        max_output_tokens=4096,
    )
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=config,
    )
    
    if response is None or response.text is None:
        raise RuntimeError(
            "Gemini returned empty response"
            " for topic: " + topic_name
        )

    try:
        batch = MCQBatch.model_validate_json(response.text)
    except ValidationError as e:
        logger.error("Validation error parsing Gemini response: %s", e)
        raise RuntimeError(f"Failed to validate Gemini response: {e}")
        
    valid_questions = []
    for q in batch.questions:
        if q.correct_answer not in q.options:
            logger.warning("Skipping invalid question: correct_answer not in options: %s", q.question_text)
            continue
        if len(q.question_text) < 20:
            logger.warning("Skipping invalid question: question_text too short: %s", q.question_text)
            continue
        if len(q.options) != 4:
            logger.warning("Skipping invalid question: options count != 4: %s", q.question_text)
            continue
        valid_questions.append(q)
        
    return valid_questions

# PART 5 — get_all_topics function
def get_all_topics() -> List[dict]:
    """
    Fetches all topics from AlloyDB.
    
    Returns:
        List of dictionaries containing topic details.
    """
    query = '''
        SELECT id, subject, topic_name, difficulty, prerequisites
        FROM topics
        ORDER BY subject, difficulty
    '''
    topics = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            for row in cur.fetchall():
                topics.append({
                    "id": row[0],
                    "subject": row[1],
                    "topic_name": row[2],
                    "difficulty": row[3],
                    "prerequisites": row[4]
                })
    return topics

# PART 6 — get_prerequisite_names function
def get_prerequisite_names(prereq_ids: List[str]) -> List[str]:
    """
    Given a list of prerequisite UUID strings, returns list of topic_name strings.
    
    Args:
        prereq_ids: List of UUID strings.
        
    Returns:
        List of topic name strings.
    """
    if not prereq_ids:
        return []
        
    query = '''
        SELECT topic_name FROM topics
        WHERE id = ANY(%s)
    '''
    names = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (prereq_ids,))
            for row in cur.fetchall():
                names.append(row[0])
    return names

# PART 7 — insert_questions function
def insert_questions(
    topic_id: str,
    subject: str,
    difficulty: str,
    questions: List[MCQQuestion]
) -> int:
    """
    Inserts validated MCQ questions into AlloyDB.
    
    Args:
        topic_id: UUID of the topic.
        subject: Subject.
        difficulty: Difficulty level.
        questions: List of MCQQuestion objects to insert.
        
    Returns:
        Count of successfully inserted questions.
    """
    check_query = '''
        SELECT 1 FROM questions
        WHERE topic_id = %s
        AND lower(trim(question_text)) = lower(trim(%s))
        LIMIT 1
    '''
    
    insert_query = '''
        INSERT INTO questions (
            id, topic_id, subject, difficulty,
            question_text, question_type,
            options, correct_answer,
            explanation, tags
        ) VALUES (
            %s, %s, %s, %s, %s,
            'mcq', %s::jsonb, %s, %s, %s
        )
    '''
    
    inserted = 0
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for q in questions:
                # Check if exists
                cur.execute(check_query, (topic_id, q.question_text))
                if cur.fetchone():
                    logger.warning("Question already exists, skipping: %s", q.question_text)
                    continue
                    
                # Insert
                qid = str(uuid.uuid4())
                cur.execute(insert_query, (
                    qid,
                    topic_id,
                    subject,
                    difficulty,
                    q.question_text,
                    json.dumps(q.options),
                    q.correct_answer,
                    q.explanation,
                    q.tags
                ))
                inserted += 1
    return inserted

# PART 8 — seed_questions main function
def seed_questions(
    subjects: Optional[List[str]] = None,
    dry_run: bool = False
) -> None:
    """
    Main function to generate and seed questions.
    
    Args:
        subjects: List of subjects to filter by. Defaults to ["DSA", "DBMS", "OS"].
        dry_run: If True, only generates and logs, does not insert.
    """
    if subjects is None:
        subjects = ["DSA", "DBMS", "OS"]
        
    topics = get_all_topics()
    topics_to_process = [t for t in topics if t["subject"] in subjects]
    
    total_inserted = 0
    topic_count = len(topics_to_process)
    
    for i, topic in enumerate(topics_to_process, 1):
        topic_id = topic["id"]
        subject = topic["subject"]
        topic_name = topic["topic_name"]
        difficulty = topic["difficulty"]
        prerequisites_ids = topic["prerequisites"] or []
        
        prereq_names = get_prerequisite_names(prerequisites_ids)
        
        try:
            questions = generate_questions(
                topic_name=topic_name,
                subject=subject,
                difficulty=difficulty,
                prerequisites=prereq_names,
                count=3
            )
            
            if dry_run:
                logger.info("[DRY RUN] Generated %d for topic '%s': %s", len(questions), topic_name, questions)
                inserted = 0
            else:
                inserted = insert_questions(topic_id, subject, difficulty, questions)
                
            total_inserted += inserted
            logger.info("Topic %d/%d: %s — inserted %d questions", i, topic_count, topic_name, inserted)
            
        except Exception as e:
            logger.error("Error processing topic %s: %s", topic_name, e)
            
        time.sleep(1)
        
    logger.info("Seeded %d questions across %d topics", total_inserted, topic_count)

# PART 9 — main block
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--subjects",
        type=str,
        default="DSA,DBMS,OS",
        help="Comma separated subjects"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate but don't insert"
    )
    args = parser.parse_args()

    # Parse subjects
    subjects = [s.strip() for s in args.subjects.split(",")]

    seed_questions(
        subjects=subjects,
        dry_run=args.dry_run
    )

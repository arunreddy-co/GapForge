"""
Database queries for GapForge.
Provides strictly parameterized SQL operations for retrieving questions,
fetching evaluation data, recursive tracing of the prerequisite topics tree,
and managing student records, assessments, skill profiles, and study plans.
"""

from typing import List, Optional, Dict, Any
from db.connection import get_db_connection

def get_questions(subject: str, difficulty: str, count: int, exclude_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Get diagnostic questions from AlloyDB for a specific subject and difficulty.
    Never returns questions the student has already seen if exclude_ids is provided.
    
    Args:
        subject: Subject matter (e.g., 'DSA').
        difficulty: Difficulty level classification.
        count: Maximum number of questions to retrieve.
        exclude_ids: Optional list of question UUIDs to skip.
        
    Returns:
        List of question dictionaries containing id, text, and options.
    """
    query = """
        SELECT id, topic_id, subject, difficulty, question_text, options 
        FROM questions 
        WHERE subject = %s AND difficulty = %s
    """
    params: List[Any] = [subject, difficulty]
    
    if exclude_ids and len(exclude_ids) > 0:
        query += " AND id != ALL(%s)"
        params.append(exclude_ids)
        
    query += " LIMIT %s"
    params.append(count)
    
    questions = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            if not rows:
                return []
            col_names = [desc[0] for desc in cur.description]
            for row in rows:
                questions.append(dict(zip(col_names, row)))
        return questions


def get_question_evaluation_data(question_id: str) -> Dict[str, Any]:
    """
    Get the evaluation data (correct answer and explanation) for a specific question.
    
    Args:
        question_id: The UUID of the question.
        
    Returns:
        Dictionary containing 'correct_answer' and 'explanation'.
        
    Raises:
        RuntimeError: If the question is not found.
    """
    query = "SELECT correct_answer, explanation FROM questions WHERE id = %s"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (question_id,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Question not found for evaluation: {question_id}")
            return {
                "correct_answer": row[0],
                "explanation": row[1]
            }


def get_prerequisite_chain(topic_id: str) -> List[Dict[str, Any]]:
    """
    Traverse UUID[] prerequisites recursively to return ordered chain
    from root to current topic. Uses a CTE recursion with depth limit.
    
    Args:
        topic_id: The UUID of the initial topic to trace backwards from.
        
    Returns:
        List of topic dictionaries in prerequisite order.
    """
    query = """
    WITH RECURSIVE topic_tree AS (
        SELECT id, subject, topic_name, difficulty, prerequisites, 1 AS depth
        FROM topics
        WHERE id = %s
        
        UNION ALL
        
        SELECT t.id, t.subject, t.topic_name, t.difficulty, t.prerequisites, tt.depth + 1
        FROM topics t
        JOIN topic_tree tt ON t.id = ANY(tt.prerequisites)
        WHERE tt.depth < 10
    )
    SELECT id, subject, topic_name, difficulty, prerequisites
    FROM topic_tree
    ORDER BY depth DESC;
    """
    chain = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (topic_id,))
            rows = cur.fetchall()
            if rows:
                col_names = [desc[0] for desc in cur.description]
                for row in rows:
                    chain.append(dict(zip(col_names, row)))
        return chain


def create_student(name: str, branch: str, semester: int, daily_hours: float, goal: str, exam_date: str) -> str:
    """
    Create a new student record and return their newly generated UUID.
    
    Args:
        name: Student's name.
        branch: Student's branch of study.
        semester: Current semester of study.
        daily_hours: Dedicated daily study hours.
        goal: The student's primary academic goal.
        exam_date: Date string for the upcoming exam.
        
    Returns:
        The UUID string of the newly created student.
    """
    query = """
    INSERT INTO students (id, name, branch, semester, daily_hours, goal, exam_date)
    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s)
    RETURNING id;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (name, branch, semester, daily_hours, goal, exam_date))
            return str(cur.fetchone()[0])


def get_student(student_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a student record by ID.
    
    Args:
        student_id: The UUID of the student to fetch.
        
    Returns:
        Dictionary containing student details, or None if not found.
    """
    query = "SELECT id, name, branch, semester, daily_hours, goal, exam_date FROM students WHERE id = %s"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (student_id,))
            row = cur.fetchone()
            if not row:
                return None
            col_names = [desc[0] for desc in cur.description]
            return dict(zip(col_names, row))


def save_assessment(student_id: str, question_id: str, student_answer: str, is_correct: bool, time_taken_seconds: int) -> None:
    """
    Save a student assessment response to the database.
    
    Args:
        student_id: UUID of the student.
        question_id: UUID of the diagnostic question.
        student_answer: The textual answer provided by the student.
        is_correct: Whether the answer was correct.
        time_taken_seconds: Seconds spent answering the question.
    """
    query = """
    INSERT INTO assessments (id, student_id, question_id, student_answer, is_correct, time_taken_seconds, assessed_at)
    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (student_id, question_id, student_answer, is_correct, time_taken_seconds))


# NOTE: skill_profiles table requires
# UNIQUE(student_id, subject) constraint.
# This is created in seed/schema.sql.
def save_skill_profile(student_id: str, subject: str, declared_level: str, verified_level: str, confidence_score: float, root_cause_topic: str) -> None:
    """
    Save or update a student's skill profile for a specific subject.
    Updates the existing row if it conflicts on (student_id, subject).
    
    Args:
        student_id: UUID of the student.
        subject: The subject matter.
        declared_level: Level claimed by the student initially.
        verified_level: Level assessed by the diagnostic engine.
        confidence_score: Float between 0.00 and 1.00 indicating confidence.
        root_cause_topic: Name or ID of the root cause prerequisite gap.
    """
    query = """
    INSERT INTO skill_profiles (id, student_id, subject, declared_level, verified_level, confidence_score, root_cause_topic, last_assessed)
    VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (student_id, subject) 
    DO UPDATE SET 
        declared_level = EXCLUDED.declared_level,
        verified_level = EXCLUDED.verified_level,
        confidence_score = EXCLUDED.confidence_score,
        root_cause_topic = EXCLUDED.root_cause_topic,
        last_assessed = CURRENT_TIMESTAMP
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (student_id, subject, declared_level, verified_level, confidence_score, root_cause_topic))


def get_topics_by_subject(subject: str) -> List[Dict[str, Any]]:
    """
    Retrieve all topics for a given subject ordered by marks weightage descending.
    
    Args:
        subject: The subject matter.
        
    Returns:
        List of topic dictionaries ordered by weightage.
    """
    query = """
    SELECT id, subject, topic_name, difficulty, prerequisites, marks_weightage, resource_url, resource_type 
    FROM topics 
    WHERE subject = %s 
    ORDER BY marks_weightage DESC
    """
    topics = []
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (subject,))
            rows = cur.fetchall()
            if not rows:
                return []
            col_names = [desc[0] for desc in cur.description]
            for row in rows:
                topics.append(dict(zip(col_names, row)))
        return topics


def save_study_plan(student_id: str, subject: str, plan_json: str) -> None:
    """
    Save a generated study plan by updating the skill_profile row for this student and subject.
    
    Args:
        student_id: UUID of the student.
        subject: The subject matter.
        plan_json: A JSON string containing the complete study plan details.
    """
    query = """
    UPDATE skill_profiles
    SET study_plan = %s::jsonb
    WHERE student_id = %s AND subject = %s
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (plan_json, student_id, subject))

"""
FastMCP Server exposing the Question Bank tools to the DiagnosticAgent.

Provides tools for fetching unseen questions, evaluating student answers,
and retrieving prerequisite conceptual chains for topics.
"""
from typing import List, Optional
from fastmcp import FastMCP

import db.queries

mcp = FastMCP("Question Bank")

@mcp.tool()
def get_questions(
    subject: str,
    difficulty: str,
    count: int,
    exclude_ids: Optional[List[str]] = None
) -> List[dict]:
    """
    Fetch a list of questions for a specific subject and difficulty level.
    
    This function utilizes the exclude_ids parameter to ensure that it never 
    returns questions that the student has already seen, protecting the integrity
    of the diagnostic assessment.

    Args:
        subject: Subject name e.g. 'DSA'
        difficulty: One of beginner, basic, intermediate, advanced
        count: Number of questions to return
        exclude_ids: Optional list of question UUIDs already seen by this student

    Returns:
        List of question dicts with id, topic_id, subject, difficulty, question_text, options

    Raises:
        RuntimeError: If database query fails
    """
    return db.queries.get_questions(subject, difficulty, count, exclude_ids)


@mcp.tool()
def evaluate_answer(
    question_id: str,
    student_answer: str
) -> dict:
    """
    Evaluate a submitted student answer against the known correct answer.

    Args:
        question_id: UUID of the question
        student_answer: Answer text from student

    Returns:
        Dict with is_correct bool, correct_answer str, explanation str

    Raises:
        RuntimeError: If question not found
    """
    eval_data = db.queries.get_question_evaluation_data(question_id)
    
    correct_answer = eval_data["correct_answer"]
    explanation = eval_data["explanation"]
    
    is_correct = student_answer.strip().lower() == correct_answer.strip().lower()
    
    return {
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "explanation": explanation
    }


@mcp.tool()
def get_prerequisite_chain(
    topic_id: str
) -> List[dict]:
    """
    Retrieve the prerequisite topic chain for a given topic ID.
    
    Returns an ordered chain from the root concept down to the current topic,
    with a depth limit of 10 to prevent infinite recursion and ensure performance.

    Args:
        topic_id: UUID of the topic to trace

    Returns:
        List of topic dicts ordered from root prerequisite to current topic

    Raises:
        RuntimeError: If database query fails
    """
    return db.queries.get_prerequisite_chain(topic_id)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8001
    )

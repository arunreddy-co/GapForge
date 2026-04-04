---
name: gapforge-dev
description: >
  Use when building, modifying, or debugging any GapForge component.
  Triggers on: agent code, MCP server tools, database queries,
  FastAPI endpoints, Gemini prompts, Pydantic schemas, seed scripts,
  AlloyDB schema, Dockerfile, or any .py file in gapforge/.
  Do not use for: general Python questions unrelated to GapForge.
---

# GapForge Development Skill

## DiagnosticAgent — Implementation Rules

### The 5-Question Policy Flow
The diagnostic flow is POLICY-DRIVEN. Never let Gemini freely
decide the next question. Always follow this exact sequence:

Q1: Declared difficulty         → verify baseline
Q2: Same difficulty             → confirm baseline
Q3: One level above             → test ceiling
Q4: Prerequisite probe          → expose root gap
Q5: Two levels above (stretch)  → confidence calibration

Collect all 5 answers first.
Call Gemini ONCE with the complete answer history.
Never call Gemini after each individual question.

### DiagnosticOutput Schema
```python
from pydantic import BaseModel
from typing import List, Optional, Literal

class ConceptFailure(BaseModel):
    concept: str
    evidence: str       # exact question text that revealed this
    severity: Literal["critical", "moderate", "minor"]

class DiagnosticOutput(BaseModel):
    declared_level: str
    verified_level: str
    confidence_score: float          # 0.00 to 1.00
    reasoning: str                   # specific, evidence-backed, max 3 sentences
    concept_failures: List[ConceptFailure]
    root_cause_topic: str
    recommended_start_point: str
    time_pattern_note: Optional[str] = None  # note if timing reveals uncertainty
```

### Diagnostic Reasoning Prompt Template
```python
DIAGNOSTIC_PROMPT = """
You are an expert learning diagnostician for CS education.
Analyze this student's complete assessment and reason about
WHY they fail, not just WHAT they got wrong.

Student Profile:
- Subject: {subject}
- Declared proficiency: {declared_level}
- Goal: {goal}
- Daily study hours: {daily_hours}

Answer History (JSON):
{answer_history_json}

Each entry contains:
question_text, topic, difficulty, student_answer,
correct_answer, is_correct, time_taken_seconds

ANALYZE the complete pattern and determine:

1. WHAT concept is broken
   BAD: "failed AVL Trees"
   GOOD: "cannot sequence multi-step pointer operations"

2. WHY it is broken
   Options: knowledge gap | procedural gap | application gap
   | working memory gap | prerequisite gap

3. PATTERN — consistent failure or situational?

4. ROOT CAUSE — the earliest broken prerequisite

5. EVIDENCE — cite the specific question(s) that prove this

6. CONFIDENCE — honest 0.0-1.0 score with justification

7. TIME PATTERNS — correct answer taking 3x average time
   indicates procedural uncertainty, not mastery.
   Note this explicitly if present.

CRITICAL RULES:
- If pattern is unclear: lower confidence, never fabricate certainty
- Be specific. Vague diagnoses have zero value.
- Return structured JSON only. No preamble. No explanation outside JSON.
"""
```

---

## PlannerAgent — Implementation Rules

### Resource Selection Logic
Resources are hardcoded in the topics table.
PlannerAgent does NOT search the internet.

Selection rules:
- Gap > 2 levels: use beginner resource first
- Gap == 1 level: use intermediate resource
- Always provide 1 alternate resource per topic
- Match resource_type to student goal:
  - crack_interview → practice problems first
  - pass_exam → notes and past questions first
  - understand → video explanations first
  - freelance → project-based resources first

### PlannerOutput Schema
```python
from pydantic import BaseModel
from typing import List, Dict

class DailyTask(BaseModel):
    day: int
    topic: str
    resource_url: str
    resource_type: str          # video | notes | practice
    alternate_resource_url: str
    duration_minutes: int
    description: str
    milestone_quiz: bool        # True = quiz triggered after this day

class PlannerOutput(BaseModel):
    student_id: str
    subject: str
    goal: str
    total_days: int
    daily_tasks: List[DailyTask]
    milestone_days: List[int]   # days where milestone quiz fires
    spaced_recall_map: Dict[str, List[str]]  # day -> topics to revisit
    improvement_baseline: float  # confidence_score from DiagnosticOutput
```

### Spaced Recall Rule
At every milestone quiz:
- Include questions from the current module (70%)
- Include questions from ALL previous modules (30%)

This is non-negotiable. It is the core retention mechanism.

---

## MCP Server — question-bank-server

### 3 Tools Only — No More
```python
from fastmcp import FastMCP
mcp = FastMCP("GapForge Question Bank")

@mcp.tool()
def get_questions(
    subject: str,
    difficulty: str,
    count: int,
    exclude_ids: Optional[List[str]] = None
) -> List[dict]:
    """Get diagnostic questions from AlloyDB.
    
    Never returns questions the student has already seen.
    Uses parameterized queries only.
    """

@mcp.tool()
def evaluate_answer(
    question_id: str,
    student_answer: str
) -> dict:
    """Evaluate student answer against correct answer.
    
    Returns: is_correct, correct_answer, explanation, time_hint
    """

@mcp.tool()
def get_prerequisite_chain(
    topic_id: str
) -> List[dict]:
    """Traverse UUID[] prerequisites recursively.
    
    Returns ordered chain from root to current topic.
    Stops when prerequisites array is empty.
    """
```

---

## AlloyDB Schema Reference
```sql
students:
  id UUID, name VARCHAR, branch VARCHAR,
  semester INTEGER, daily_hours DECIMAL,
  goal VARCHAR, exam_date DATE

topics:
  id UUID, subject VARCHAR, topic_name VARCHAR,
  difficulty VARCHAR, prerequisites UUID[],
  marks_weightage INTEGER, resource_url VARCHAR,
  resource_type VARCHAR

questions:
  id UUID, topic_id UUID, subject VARCHAR,
  difficulty VARCHAR, question_text TEXT,
  options JSONB, correct_answer TEXT,
  explanation TEXT, tags TEXT[]

assessments:
  id UUID, student_id UUID, question_id UUID,
  student_answer TEXT, is_correct BOOLEAN,
  time_taken_seconds INTEGER, assessed_at TIMESTAMP

skill_profiles:
  id UUID, student_id UUID, subject VARCHAR,
  declared_level VARCHAR, verified_level VARCHAR,
  confidence_score DECIMAL, root_cause_topic VARCHAR,
  last_assessed TIMESTAMP
```

---

## Common Failure Modes — Avoid These

| Failure | Root Cause | Prevention |
|---------|-----------|------------|
| JSON truncation from Gemini | max_output_tokens too high | Always 2048 |
| Hallucinated MCQ options | No few-shot examples | Add 1 good/bad example per prompt |
| psycopg2 connection leak | No context manager | Always use get_db_connection() |
| Import error on Cloud Run | Package outside requirements.txt | Check before every import |
| Pydantic validation crash | Schema mismatch | Validate before using, not after |
| AlloyDB connection timeout | No timeout set | connect_timeout=10 always |
| Agent loop without exit | No termination condition | Always define done state explicitly |

---

## Pre-Commit Checklist — Run Before Every Commit
□ No credentials anywhere in any file
□ No packages outside requirements.txt imported
□ No function truncated or stubbed out
□ Every Gemini call has temperature + max_output_tokens=2048
□ Every Gemini response validated against Pydantic schema
□ Every SQL query uses parameterized format (%s)
□ Every function has complete docstring
□ Every file has module-level comment
□ No bare except: or except Exception: pass
□ No mock data or hardcoded test values

If any box is unchecked: fix before committing.
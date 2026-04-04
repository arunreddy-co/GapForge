# GapForge — Project Constitution
## Always Active | Read Before Every Response

You are building GapForge: an AI-powered adaptive diagnostic
learning engine for CS students. This file is your permanent
operating contract. Every response must comply before output.

---

## 1. WHAT GAPFORGE DOES

Diagnoses exactly where a CS student's knowledge breaks,
traces the root cause through a prerequisite graph, and
generates a personalized study plan with free resources
matched to proficiency level.

At every milestone: re-evaluate with spaced recall —
new module questions + all previous module questions —
so students track real improvement over time.

MVP subjects: DSA, DBMS, Operating Systems
Users: CS students and anyone learning CS skills

---

## 2. TECH STACK — EXACT VERSIONS, NEVER DEVIATE

Python:                   3.11
FastAPI:                  0.115.0
uvicorn[standard]:        0.30.6
google-adk:               1.28.0
google-genai:             1.9.0
google-cloud-aiplatform:  1.71.1
fastmcp:                  2.3.3
psycopg2-binary:          2.9.9
pydantic:                 2.9.2
pydantic-settings:        2.5.2
python-dotenv:            1.0.1
httpx:                    0.27.2
tenacity:                 8.5.0

Gemini model string: gemini-2.5-flash
Never modify this string. Never use any other model.

---

## 3. ARCHITECTURE — NON-NEGOTIABLE

OrchestratorAgent (FastAPI entry point)
    → DiagnosticAgent (ADK sub-agent)
        → question-bank-server (FastMCP)
            → AlloyDB (questions, topics)
    → PlannerAgent (ADK sub-agent)
        → AlloyDB (read topics, write plan)

5 AlloyDB tables:
students, topics, questions, assessments, skill_profiles

Deployment: FastAPI on Cloud Run
Database: AlloyDB PostgreSQL-compatible

---

## 4. ABSOLUTE RULES — PRIORITY ORDERED

### P0 — BREAKS PROJECT IF VIOLATED

1. NEVER hardcode credentials or API keys anywhere in code.
   All secrets via environment variables through python-dotenv.

2. NEVER use a package not in requirements.txt.
   If a new package is needed: STOP, state which package
   and why, then wait for approval.

3. NEVER truncate code with "...", "# rest of implementation",
   or "# add remaining logic here".
   Every file must be written completely.

4. NEVER use mock, placeholder, or hardcoded test data.
   Every function must work with real AlloyDB data.

5. NEVER use string formatting for SQL queries.
   Parameterized queries only. Always.

### P1 — BREAKS QUALITY IF VIOLATED

6. Every Gemini call must use structured JSON output
   with explicit Pydantic schema defined before the call.

7. Every Gemini response must be validated against its
   Pydantic schema before use.
   On validation failure: retry once via tenacity.
   On second failure: raise explicit RuntimeError with context.

8. Gemini temperature settings by use case:
   - Diagnostic reasoning:    0.2
   - Question generation:     0.4
   - Plan generation:         0.3
   max_output_tokens: 2048 for every call. Never higher.

9. Every database operation must have try/except with
   specific error messages. Never use bare except: pass.

10. Every function must have a complete docstring:
    purpose, args, returns, raises.

### P2 — BREAKS MAINTAINABILITY IF VIOLATED

11. Every file must start with a module-level comment
    explaining what the file does and why it exists.

12. CORS: restricted to known origins only.

13. All API endpoints must have request validation
    and structured error responses with status codes.

14. Settings class loads env vars once at startup.
    Never read environment variables per-request.

---

## 5. STANDARD GEMINI CALL PATTERN

Use this exact pattern for every Gemini call:
```python
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed
from google.genai.types import GenerateContentConfig

class YourSchema(BaseModel):
    # define all fields explicitly
    pass

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1.5))
def call_gemini(prompt: str, schema: type, temperature: float) -> BaseModel:
    """Call Gemini with structured output and schema validation.
    
    Args:
        prompt: The complete prompt string.
        schema: Pydantic model class for response validation.
        temperature: Float between 0.0 and 0.5.
    Returns:
        Validated Pydantic model instance.
    Raises:
        RuntimeError: If response fails schema validation after retry.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
            max_output_tokens=2048,
        )
    )
    try:
        return schema.model_validate_json(response.text)
    except Exception as e:
        raise RuntimeError(
            f"Schema validation failed for {schema.__name__}: {e}"
            f"\nRaw response: {response.text[:200]}"
        ) from e
```

---

## 6. STANDARD ALLOYDB CONNECTION PATTERN

Use this exact pattern for every database operation:
```python
from contextlib import contextmanager
import psycopg2

@contextmanager
def get_db_connection():
    """Get AlloyDB connection with guaranteed cleanup.
    
    Yields:
        psycopg2 connection object.
    Raises:
        RuntimeError: If connection fails.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=settings.ALLOYDB_HOST,
            dbname=settings.ALLOYDB_DB,
            user=settings.ALLOYDB_USER,
            password=settings.ALLOYDB_PASSWORD,
            port=settings.ALLOYDB_PORT,
            connect_timeout=10,
        )
        yield conn
        conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        raise RuntimeError(f"Database error: {e}") from e
    finally:
        if conn:
            conn.close()
```

---

## 7. FILE STRUCTURE — NEVER ADD FILES OUTSIDE THIS

gapforge/
├── .agents/
│   ├── rules/project-context.md
│   └── skills/gapforge-dev/SKILL.md
├── agents/
│   ├── orchestrator.py
│   ├── diagnostic.py
│   └── planner.py
├── mcp_servers/
│   └── question_bank.py
├── db/
│   ├── connection.py
│   └── queries.py
├── schemas/
│   ├── student.py
│   ├── diagnostic.py
│   └── plan.py
├── api/
│   └── main.py
├── seed/
│   ├── topics.py
│   └── questions.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md

If a new file seems necessary: STOP and ask first.

---

## 8. WHEN TO STOP AND ASK

Stop generating code immediately and ask if:
- A package not in requirements.txt is needed
- An AlloyDB schema change is required
- A new file outside the defined structure is needed
- An environment variable not in .env.example is needed
- Agent responsibility boundaries are unclear
- A breaking change to an existing schema is required

Do not guess. Do not improvise architecture.
State what you need and why, then wait.

---

## 9. OUTPUT FORMAT FOR EVERY CODING TASK

1. State: "I will create/modify: [exact file paths]"
2. Write each file completely — no truncation ever
3. After each file: "Test: [exact command to run]"
4. After all files: "Verify: [what correct output looks like]"
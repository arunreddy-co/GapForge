# GapForge — AI Diagnostic Learning Engine

> *"Your college tests you once a semester. GapForge tests you every day — and tells you exactly why you're failing."*

GapForge is a multi-agent AI system that diagnoses knowledge gaps in CS engineering students, traces the root cause of each gap through a prerequisite knowledge graph, and generates a personalized study plan with curated free resources — all delivered via a clean API and a structured Notion roadmap.

Built for the **Google Cloud Gen AI Academy APAC 2026 Hackathon**.

---

## The Problem

India produces 1.5 million engineering graduates per year. Over 80% struggle to find relevant employment. The gap between Tier-1 and Tier-3 college outcomes isn't content — it's **directed, personalized momentum**.

Students don't know where they're actually broken. They self-assess incorrectly. They study topics they already know while skipping their actual weak areas. No existing system diagnoses the **root cause** of their gaps.

GapForge fixes this.

---

## How It Works
Student fills profile
↓
Selects subject + declares proficiency level
↓
DiagnosticAgent serves 5 adaptive MCQ questions
(via question-bank MCP server → AlloyDB)
↓
Student answers all 5
↓
Gemini 2.5 Flash reasons about WHY they failed
— not just what topic, but the cognitive gap
↓
PlannerAgent generates personalized study plan
— starts from root cause, not surface topic
— 90 min/day matched to student's schedule
— free curated resources (YouTube + GFG)
↓
Notion MCP creates structured roadmap page
↓
Student gets: diagnosis + plan + Notion URL

---

## Architecture
```
┌─────────────────────────────────────────┐
│         FastAPI on Cloud Run            │
│         (Public API Endpoint)           │
└──────────────┬──────────────────────────┘
               ↓
    ┌──────────────────────┐
    │   OrchestratorAgent  │
    │   (ADK + Gemini)     │
    └──┬──────────┬────────┘
       ↓          ↓          ↓
  ┌─────────┐ ┌─────────┐ ┌─────────┐
  │Diagnost-│ │ Planner │ │ Content │
  │ic Agent │ │  Agent  │ │  Agent  │
  └────┬────┘ └────┬────┘ └────┬────┘
       ↓           └─────┬─────┘
  ┌─────────┐            ↓
  │question │      ┌──────────┐
  │bank MCP │      │Notion MCP│
  └────┬────┘      └────┬─────┘
       ↓                ↓
  ┌─────────┐     ┌──────────┐
  │ AlloyDB │     │  Notion  │
  │5 tables │     │Workspace │
  └─────────┘     └──────────┘

4 Agents. 2 MCP Servers. 1 AlloyDB. 1 Cloud Run.
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agents | Google ADK 1.28.0 |
| LLM | Gemini 2.5 Flash via Vertex AI |
| MCP Servers | FastMCP 2.3.3 |
| Database | AlloyDB (PostgreSQL-compatible) |
| API | FastAPI 0.124.1 |
| Deployment | Google Cloud Run |
| External Tool | Notion API |
| Language | Python 3.11 |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health check |
| GET | `/docs` | Interactive Swagger UI |
| POST | `/students` | Create student profile |
| GET | `/students/{id}` | Get student details |
| GET | `/questions/diagnostic` | Fetch 5 diagnostic questions |
| POST | `/diagnose` | Run full pipeline |
| GET | `/app` | Frontend UI |

### Example: Create Student
```bash
curl -X POST \
  https://gapforge-1074139615204.us-central1.run.app/students \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rahul",
    "branch": "CSE",
    "semester": 3,
    "daily_hours": 2.0,
    "goal": "crack_interview",
    "exam_date": "2026-12-01",
    "declared_levels": {"DSA": "intermediate"}
  }'
```

### Example: Run Diagnostic
```bash
curl -X POST \
  https://gapforge-1074139615204.us-central1.run.app/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "YOUR_STUDENT_ID",
    "subject": "DSA",
    "declared_level": "intermediate",
    "goal": "crack_interview",
    "daily_hours": 2.0,
    "answers": [
      {
        "question_id": "QUESTION_UUID",
        "student_answer": "The selected option text",
        "time_taken_seconds": 30
      }
    ]
  }'
```

### Example Response
```json
{
  "diagnostic": {
    "verified_level": "basic",
    "confidence_score": 0.91,
    "reasoning": "Student failed Q1 and Q3 on
      recursion-based problems. Q4 revealed
      a gap in base case understanding —
      root cause is foundational recursion,
      not the surface DSA topics.",
    "root_cause_topic": "Recursion",
    "recommended_start_point": "Introduction
      to Recursion"
  },
  "plan": {
    "total_days": 10,
    "milestone_days": [3, 6, 9],
    "daily_tasks": [...]
  },
  "notion_page_url": "https://notion.so/...",
  "status": "complete"
}
```

---

## Database Schema
```sql
students        — profile, goal, daily hours
topics          — 30 CS topics with prerequisite
                  graph (UUID[] array)
questions       — 90 diagnostic MCQs with
                  explanations and tags
assessments     — every student answer logged
skill_profiles  — declared vs verified level,
                  confidence score, root cause,
                  generated study plan (JSONB)
```

The prerequisite graph uses PostgreSQL's
native `UUID[]` array type. `get_prerequisite_chain()`
traverses it recursively with a CTE query,
tracing backwards from failed topic to root cause.

---

## MCP Servers

### question-bank-server
Exposes 3 tools to DiagnosticAgent:
- `get_questions(subject, difficulty, count)` — fetches unseen MCQs from AlloyDB
- `evaluate_answer(question_id, answer)` — checks correctness, returns explanation
- `get_prerequisite_chain(topic_id)` — traces prerequisite graph to root cause

### notion-planner-server
Exposes 1 tool to OrchestratorAgent:
- `create_study_roadmap(...)` — creates structured Notion page with daily plan, milestone markers, and resource links

---

## Subjects Covered (MVP)

| Subject | Topics | Questions |
|---------|--------|-----------|
| DSA | 10 | 30 |
| DBMS | 10 | 30 |
| Operating Systems | 10 | 30 |

---

## Local Setup

### Prerequisites
- Python 3.11
- Google Cloud project with Vertex AI enabled
- AlloyDB instance
- Notion integration

### Installation
```bash
git clone https://github.com/YOUR_USERNAME/gapforge.git
cd gapforge

pip install -r requirements.txt

cp .env.example .env
# Fill in your values
```

### Environment Variables
```env
ALLOYDB_HOST=your_alloydb_ip
ALLOYDB_DB=gapforge_db
ALLOYDB_USER=postgres
ALLOYDB_PASSWORD=your_password
ALLOYDB_PORT=5432
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=TRUE
NOTION_API_KEY=ntn_your_key
NOTION_PARENT_PAGE_ID=your_page_id
```

### Seed Database
```bash
# Seed topics with prerequisite graph
PYTHONPATH=. python seed/topics.py

# Generate diagnostic questions via Gemini
PYTHONPATH=. python seed/questions.py
```

### Run Locally
```bash
PYTHONPATH=. uvicorn api.main:app \
  --host 0.0.0.0 --port 8080 --reload
```

Open `http://localhost:8080/app` for the UI
or `http://localhost:8080/docs` for the API.

---

## Deployment
```bash
# Build Docker image
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/PROJECT_ID/gapforge-repo/gapforge:v1

# Deploy to Cloud Run
gcloud run deploy gapforge \
  --image us-central1-docker.pkg.dev/PROJECT_ID/gapforge-repo/gapforge:v1 \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars KEY=VALUE,...
```

---

## Live Demo

- **API:** https://gapforge-1074139615204.us-central1.run.app
- **Frontend:** https://gapforge-1074139615204.us-central1.run.app/app
- **Swagger UI:** https://gapforge-1074139615204.us-central1.run.app/docs
- **Demo Video:** https://drive.google.com/file/d/1J-duq_qaaZWsIttsf0LkLnMmfFIjgFnQ/view?usp=sharing

---

## Project Structure
```
gapforge/
├── agents/
│   ├── orchestrator.py   # Main coordinator agent
│   ├── diagnostic.py     # Assessment + Gemini reasoning
│   └── planner.py        # Study plan generation
├── mcp_servers/
│   ├── question_bank.py  # Question fetching tools
│   └── notion_planner.py # Notion page creation
├── db/
│   ├── connection.py     # AlloyDB connection manager
│   └── queries.py        # All parameterized SQL queries
├── schemas/
│   ├── student.py        # Student input/output schemas
│   ├── diagnostic.py     # Diagnostic schemas + Gemini output
│   └── plan.py           # Study plan schemas
├── api/
│   └── main.py           # FastAPI endpoints
├── seed/
│   ├── topics.py         # Seed 30 topics with prereq graph
│   └── questions.py      # Generate 90 MCQs via Gemini
├── static/
│   └── index.html        # Single-file frontend
├── requirements.txt
├── Dockerfile
└── README.md
```
---

## What's Next (Phase 2)

- Milestone quizzes with spaced recall
- Company-specific interview tracks
- GATE and university exam modes
- Coding question support via Judge0
- Progress tracking across sessions
- Mobile app

---

## Built With

- Google ADK — multi-agent orchestration
- Gemini 2.5 Flash — diagnostic reasoning
- AlloyDB — prerequisite knowledge graph
- FastMCP — MCP server implementation
- Notion API — study roadmap delivery
- Google Cloud Run — serverless deployment

---

*GapForge — Because knowing what to study
is harder than studying itself.*

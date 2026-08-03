GapForge — AI Diagnostic Learning Engine

> "Your college tests you once a semester. GapForge tests you continuously — and tells you exactly why you are struggling."

GapForge is a multi-agent AI learning diagnostic system that identifies knowledge gaps in computer science students, traces the root cause of those gaps through a prerequisite knowledge graph, and generates personalized learning roadmaps with curated resources.

Instead of recommending generic learning content, GapForge understands **why a student is failing**, identifies missing foundations, and creates a structured path to improve.

Built for the **Google Cloud Gen AI Academy APAC 2026 Hackathon**.

---

# The Problem

Computer science students today have access to thousands of learning resources.

The challenge is not finding content.

The challenge is knowing:

- What concepts are actually weak?
- Why are they struggling?
- What should they learn first?
- Which foundational gaps are blocking advanced topics?

Students often self-assess incorrectly.

A student struggling with Dynamic Programming may not have a Dynamic Programming problem.

The actual gap may be:

Dynamic Programming
        ↓
    Recursion
        ↓
   Functions
        ↓
Programming Fundamentals

Most learning platforms recommend resources, but they rarely diagnose the root cause behind a student's difficulty.

GapForge solves this by combining AI reasoning with prerequisite-based knowledge tracing.

---

# How It Works

Student Profile
        ↓
Subject + Goal Selection
        ↓
Adaptive Diagnostic Assessment
        ↓
Diagnostic Agent
        ↓
Gemini Reasoning + Knowledge Graph Analysis
        ↓
Root Cause Identification
        ↓
Planner Agent
        ↓
Personalized Learning Roadmap
        ↓
Notion Learning Workspace

---

# Core Workflow

## 1. Student Profiling

The student provides:

- Branch
- Semester
- Subject
- Current proficiency level
- Learning goal
- Available daily study time


Example:

Branch:
CSE
Subject:
DSA
Goal:
Interview Preparation
Daily Time:
2 hours

---

## 2. Adaptive Diagnosis

The Diagnostic Agent generates targeted questions using the Question Bank MCP Server.

The system evaluates:

- Correctness
- Difficulty level
- Topic relationships
- Concept dependencies


The goal is not only finding:

"What question did the student get wrong?"

but identifying:

"Which underlying concept caused the student to get it wrong?"

---

## 3. AI Root Cause Analysis

Gemini 2.5 Flash analyzes assessment results and identifies:

- Verified skill level
- Confidence score
- Weak concepts
- Missing prerequisites
- Recommended starting point


Example:

Traditional approach:

Weak Area:
Dynamic Programming


GapForge approach:

Root Cause:
Weak Recursion Fundamentals
Recommended Starting Point:
Introduction to Recursion

---

## 4. Personalized Learning Plan

The Planner Agent generates:

- Daily study tasks
- Topic ordering
- Milestones
- Learning resources


The roadmap is automatically created inside Notion using the Notion MCP Server.

---

# Why Agentic AI?

A traditional chatbot can answer questions.

GapForge requires multiple reasoning steps:

1. Diagnose current student ability.
2. Analyze mistakes and misconceptions.
3. Trace prerequisite knowledge gaps.
4. Generate an optimized learning sequence.
5. Execute external actions like creating Notion roadmaps.


This workflow requires specialized agents working together rather than a single conversational model.

---

# Architecture

┌─────────────────────────────────────────┐
│          FastAPI on Cloud Run            │
│          Public API Endpoint             │
└──────────────┬──────────────────────────┘
               ↓
  ┌───────────────────┐
  │ OrchestratorAgent │
  │    ADK + Gemini   │
  └───────┬───────────┘
          |
-----------------------------
|             |             |
↓             ↓             ↓
Diagnostic     Planner      Content
 Agent         Agent        Agent
↓                           ↓
Question Bank MCP          Notion MCP
 Server                     Server
↓                           ↓

    AlloyDB        Notion Workspace

---

# Agent Architecture

GapForge uses specialized AI agents.

## Orchestrator Agent

Responsible for:

- Managing workflow execution
- Coordinating multiple agents
- Maintaining context between steps


---

## Diagnostic Agent

Responsible for:

- Generating assessments
- Evaluating answers
- Identifying conceptual weaknesses


---

## Planner Agent

Responsible for:

- Creating personalized learning paths
- Scheduling daily tasks
- Selecting learning resources


---

## Content Agent

Responsible for:

- Resource recommendations
- Learning material generation


---

# MCP Integration

GapForge uses Model Context Protocol servers to provide external capabilities to AI agents.

---

# Question Bank MCP Server

Provides three tools:

## `get_questions()`

Fetches diagnostic questions from AlloyDB.

## `evaluate_answer()`

Evaluates student responses and returns explanations.

## `get_prerequisite_chain()`

Traverses the knowledge graph to identify missing foundations.

---

# Notion Planner MCP Server

Provides:

## `create_study_roadmap()`

Creates structured Notion pages containing:

- Daily tasks
- Milestones
- Learning resources
- Study timeline

---

# Knowledge Graph Based Diagnosis

The core idea behind GapForge is that computer science concepts are connected.

Example:

Dynamic Programming
        |
        ↓
    Recursion
        |
        ↓
   Functions
        |
        ↓
Programming Fundamentals

When a student fails a concept, GapForge traverses backwards through the prerequisite graph to identify the earliest missing foundation.

Implementation:

- PostgreSQL-compatible AlloyDB
- Recursive CTE traversal
- UUID-based prerequisite relationships
- JSONB storage for generated learning plans

---

# My Contribution

I designed and implemented the overall system architecture including:

- Multi-agent workflow design
- Knowledge graph approach
- Database schema
- MCP server integration
- API architecture
- Cloud deployment workflow


AI tools were used during development for faster iteration, debugging, and exploration.

Architecture decisions, integration logic, testing, and deployment workflows were manually reviewed and validated.

---

# Technology Stack

| Component | Technology |
|-|-|
| Agent Framework | Google ADK 1.28.0 |
| LLM | Gemini 2.5 Flash via Vertex AI |
| MCP Servers | FastMCP 2.3.3 |
| Database | AlloyDB |
| Backend API | FastAPI 0.124.1 |
| Deployment | Google Cloud Run |
| External Integration | Notion API |
| Language | Python 3.11 |

---

# Current Implementation

## Subjects Covered

| Subject | Topics | Questions |
|-|-|-|
| DSA | 10 | 30 |
| DBMS | 10 | 30 |
| Operating Systems | 10 | 30 |

---

# Current Capabilities

✅ Multi-agent AI orchestration  
✅ Adaptive diagnostic testing  
✅ Root cause analysis  
✅ Prerequisite knowledge graph  
✅ Personalized learning plan generation  
✅ Notion roadmap generation  
✅ Cloud deployment  
✅ REST API interface  

---

# API Endpoints

| Method | Endpoint | Description |
|-|-|-|
| GET | `/` | Service information |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger documentation |
| POST | `/students` | Create student profile |
| GET | `/students/{id}` | Retrieve student details |
| GET | `/questions/diagnostic` | Fetch diagnostic questions |
| POST | `/diagnose` | Run complete diagnosis pipeline |
| GET | `/app` | Frontend interface |

---

# Example Diagnosis Output

```json
{
  "diagnostic": {
    "verified_level": "basic",
    "confidence_score": 0.91,
    "root_cause_topic": "Recursion",
    "recommended_start_point": "Introduction to Recursion"
  },

  "plan": {
    "total_days": 10,
    "milestone_days": [3,6,9]
  },

  "status": "complete"
}
Database Schema
students
    ↓
Student profile, goals, available time


topics
    ↓
CS topics + prerequisite relationships


questions
    ↓
Diagnostic MCQs, explanations, difficulty


assessments
    ↓
Student answers and evaluation history


skill_profiles
    ↓
Verified level, confidence score,
root cause and generated roadmap
Local Setup
Prerequisites
Python 3.11
Google Cloud Project
Vertex AI Enabled
AlloyDB Instance
Notion Integration
Installation
git clone https://github.com/arunreddy-co/GapForge.git

cd GapForge

pip install -r requirements.txt

cp .env.example .env
Configure:
ALLOYDB_HOST=
ALLOYDB_DB=
ALLOYDB_USER=
ALLOYDB_PASSWORD=

GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=

NOTION_API_KEY=
NOTION_PARENT_PAGE_ID=
Deployment
GapForge is deployed using Google Cloud Run.
Architecture:
Docker Container
        ↓
Google Cloud Run
        ↓
FastAPI API
        ↓
Vertex AI + AlloyDB
Live Demo
API:
https://gapforge-1074139615204.us-central1.run.app
Frontend:
https://gapforge-1074139615204.us-central1.run.app/app
Swagger:
https://gapforge-1074139615204.us-central1.run.app/docs
Demo Video:
(Add Link)
Project Structure
gapforge/

├── agents/
│   ├── orchestrator.py
│   ├── diagnostic.py
│   └── planner.py

├── mcp_servers/
│   ├── question_bank.py
│   └── notion_planner.py

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

├── static/
│   └── index.html

├── requirements.txt

└── Dockerfile
Engineering Challenges
Diagnosing Root Causes Instead of Topics
Traditional recommendation systems identify topics.
GapForge identifies the underlying reason behind failure.
Example:
Failed Topic:
Dynamic Programming


Detected Root Cause:
Weak Recursion Fundamentals
Building Agent Workflows
The system required coordination between multiple AI components:
Diagnostic reasoning
Knowledge graph traversal
Resource planning
External tool execution
Designing a Learning Knowledge Graph
The system needed to answer:
"What should the student learn first?"
rather than only:
"What did the student fail?"
Current Limitations
Diagnostic accuracy depends on question quality.
Current knowledge graph covers selected CS subjects only.
Resource recommendations are based on predefined sources.
Long-term progress tracking is planned for future versions.
Future Roadmap
Phase 2
Spaced repetition tracking
Progress monitoring
Company-specific interview tracks
GATE preparation mode
Coding problem evaluation
Mobile application
Built With
Google ADK
Gemini 2.5 Flash
AlloyDB
FastMCP
Notion API
Google Cloud Run  
GapForge
Because knowing what to study next is harder than studying itself.
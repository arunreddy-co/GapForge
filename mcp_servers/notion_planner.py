"""
FastMCP server that creates structured study roadmap pages in Notion.
It takes the diagnostic results and generated study plan from the planner agent
and creates an actionable, formatted Notion page for the student.
"""

import logging
from typing import List, Dict, Any

import httpx
from fastmcp import FastMCP

from db.connection import settings

# PART 1 — Setup
mcp = FastMCP("Notion Planner")
NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

logger = logging.getLogger(__name__)


# PART 2 — get_headers() function
def get_headers() -> Dict[str, str]:
    """
    Constructs and returns the HTTP headers required for Notion API requests.
    
    Returns:
        A dictionary containing Authorization, Content-Type, and Notion-Version headers.
    """
    return {
        "Authorization": f"Bearer {settings.NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }


# PART 3 — create_study_roadmap tool
@mcp.tool()
def create_study_roadmap(
    student_name: str,
    subject: str,
    verified_level: str,
    root_cause_topic: str,
    total_days: int,
    daily_tasks: List[Dict[str, Any]],
    milestone_days: List[int]
) -> Dict[str, Any]:
    """
    Creates a structured study roadmap page in Notion.
    
    Args:
        student_name: The name of the student.
        subject: The subject being studied.
        verified_level: The diagnosed proficiency level.
        root_cause_topic: The earliest broken prerequisite topic.
        total_days: The total duration of the plan in days.
        daily_tasks: A list of task dictionaries containing daily study plan details.
        milestone_days: A list of day numbers that feature a milestone quiz.
        
    Returns:
        A dictionary containing the status, the created Notion page URL, and the page ID.
        
    Raises:
        RuntimeError: If the Notion API request fails.
    """
    # 1. Build Notion blocks list
    blocks = [
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"Diagnosed Level: {verified_level}\nRoot Cause: {root_cause_topic}\nDuration: {total_days} days"
                        }
                    }
                ],
                "icon": {"emoji": "💡"}
            }
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Daily Study Plan"
                        }
                    }
                ]
            }
        }
    ]

    for task in daily_tasks:
        day = task.get("day")
        topic = task.get("topic")
        is_milestone = day in milestone_days or task.get("milestone_quiz", False)
        
        title = f"Day {day}: {topic}"
        if is_milestone:
            title += " MILESTONE QUIZ"
            
        task_block = {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": title
                        }
                    }
                ],
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"Duration: {task.get('duration_minutes')} minutes | Type: {task.get('resource_type')}"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": str(task.get('description', ''))
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "bookmark",
                        "bookmark": {
                            "url": task.get('resource_url', 'https://example.com')
                        }
                    }
                ]
            }
        }
        blocks.append(task_block)

    # 2. Create page via POST
    payload = {
        "parent": {
            "page_id": settings.NOTION_PARENT_PAGE_ID
        },
        "icon": {"emoji": "📖"},
        "properties": {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": f"{student_name} — {subject} Study Plan"
                        }
                    }
                ]
            }
        },
        "children": blocks
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{NOTION_API_URL}/pages",
            headers=get_headers(),
            json=payload
        )

    # 3. Handle response errors
    if response.status_code != 200:
        raise RuntimeError(f"Notion API Error (Status {response.status_code}): {response.text[:200]}")

    # 4. Return
    data = response.json()
    return {
        "status": "created",
        "notion_page_url": data.get("url"),
        "page_id": data.get("id")
    }


# PART 4 — main block
if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8002
    )
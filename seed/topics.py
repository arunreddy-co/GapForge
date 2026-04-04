"""
Seed script for gapforge topics.
Seeds predefined CS topics into AlloyDB handling self-referencing UUID prerequisites.
"""
import logging
import uuid
from typing import List, Dict

from db.connection import get_db_connection
from db.queries import get_topics_by_subject

# Module-level logger setup
logger = logging.getLogger(__name__)

TOPICS: List[Dict] = [
    {
        "subject": "DSA",
        "topic_name": "Arrays and Strings",
        "difficulty": "beginner",
        "prerequisites": [],
        "marks_weightage": 8,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/array-data-structure/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=eXFBpVVGnhw"
    },
    {
        "subject": "DSA",
        "topic_name": "Recursion",
        "difficulty": "basic",
        "prerequisites": ["Arrays and Strings"],
        "marks_weightage": 7,
        "semester": 3,
        "resource_url": "https://www.youtube.com/watch?v=IJDJ0kBx2LM",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/recursion/"
    },
    {
        "subject": "DSA",
        "topic_name": "Linked Lists",
        "difficulty": "basic",
        "prerequisites": ["Arrays and Strings"],
        "marks_weightage": 8,
        "semester": 3,
        "resource_url": "https://www.youtube.com/watch?v=R9PTBwOzceo",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/data-structures/linked-list/"
    },
    {
        "subject": "DSA",
        "topic_name": "Stacks and Queues",
        "difficulty": "basic",
        "prerequisites": ["Linked Lists"],
        "marks_weightage": 7,
        "semester": 3,
        "resource_url": "https://www.youtube.com/watch?v=wjI1WNcIntg",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/stack-data-structure/"
    },
    {
        "subject": "DSA",
        "topic_name": "Sorting Algorithms",
        "difficulty": "basic",
        "prerequisites": ["Arrays and Strings", "Recursion"],
        "marks_weightage": 9,
        "semester": 3,
        "resource_url": "https://www.youtube.com/watch?v=pkkFqlG0Cf4",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/sorting-algorithms/"
    },
    {
        "subject": "DSA",
        "topic_name": "Binary Trees",
        "difficulty": "intermediate",
        "prerequisites": ["Recursion", "Linked Lists"],
        "marks_weightage": 8,
        "semester": 3,
        "resource_url": "https://www.youtube.com/watch?v=H5JubkIy_p8",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/binary-tree-data-structure/"
    },
    {
        "subject": "DSA",
        "topic_name": "BST and AVL Trees",
        "difficulty": "intermediate",
        "prerequisites": ["Binary Trees"],
        "marks_weightage": 8,
        "semester": 3,
        "resource_url": "https://www.youtube.com/watch?v=h6AGSZJar3s",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/avl-tree-set-1-insertion/"
    },
    {
        "subject": "DSA",
        "topic_name": "Graph Traversals",
        "difficulty": "intermediate",
        "prerequisites": ["Recursion", "Stacks and Queues"],
        "marks_weightage": 9,
        "semester": 3,
        "resource_url": "https://www.youtube.com/watch?v=pcKY4hjDrxk",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/graph-data-structure-and-algorithms/"
    },
    {
        "subject": "DSA",
        "topic_name": "Dynamic Programming",
        "difficulty": "advanced",
        "prerequisites": ["Recursion", "Graph Traversals"],
        "marks_weightage": 10,
        "semester": 3,
        "resource_url": "https://www.youtube.com/watch?v=oBt53YbR9Kk",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/dynamic-programming/"
    },
    {
        "subject": "DSA",
        "topic_name": "Hashing",
        "difficulty": "intermediate",
        "prerequisites": ["Arrays and Strings"],
        "marks_weightage": 7,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/hashing-data-structure/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=jalSiaIi8j4"
    },
    {
        "subject": "DBMS",
        "topic_name": "ER Model and Diagrams",
        "difficulty": "beginner",
        "prerequisites": [],
        "marks_weightage": 6,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/introduction-of-er-model/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=QpdhBUYk7Kk"
    },
    {
        "subject": "DBMS",
        "topic_name": "Relational Model",
        "difficulty": "basic",
        "prerequisites": ["ER Model and Diagrams"],
        "marks_weightage": 7,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/relational-model-in-dbms/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=_tqFDpAlznk"
    },
    {
        "subject": "DBMS",
        "topic_name": "SQL Basics",
        "difficulty": "basic",
        "prerequisites": ["Relational Model"],
        "marks_weightage": 9,
        "semester": 3,
        "resource_url": "https://www.w3schools.com/sql/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=HXV3zeQKqGY"
    },
    {
        "subject": "DBMS",
        "topic_name": "Joins and Subqueries",
        "difficulty": "intermediate",
        "prerequisites": ["SQL Basics"],
        "marks_weightage": 9,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/sql-join-set-1-cross-join/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=9yeOJ0ZMUYw"
    },
    {
        "subject": "DBMS",
        "topic_name": "Normalization",
        "difficulty": "intermediate",
        "prerequisites": ["Relational Model"],
        "marks_weightage": 9,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/introduction-of-database-normalization/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=ABwD8IYByfk"
    },
    {
        "subject": "DBMS",
        "topic_name": "Transactions and ACID",
        "difficulty": "intermediate",
        "prerequisites": ["SQL Basics"],
        "marks_weightage": 8,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/acid-properties-in-dbms/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=pomxJOFVcQs"
    },
    {
        "subject": "DBMS",
        "topic_name": "Indexing and B-Trees",
        "difficulty": "advanced",
        "prerequisites": ["Normalization", "Transactions and ACID"],
        "marks_weightage": 8,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/indexing-in-databases-set-1/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=aZjYr87r1b8"
    },
    {
        "subject": "DBMS",
        "topic_name": "Concurrency Control",
        "difficulty": "advanced",
        "prerequisites": ["Transactions and ACID"],
        "marks_weightage": 8,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/concurrency-control-in-dbms/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=MoOmJECJNe4"
    },
    {
        "subject": "DBMS",
        "topic_name": "Query Optimization",
        "difficulty": "advanced",
        "prerequisites": ["Indexing and B-Trees", "Joins and Subqueries"],
        "marks_weightage": 7,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/query-optimization-in-relational-algebra/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=P7fCZEAFkIU"
    },
    {
        "subject": "DBMS",
        "topic_name": "NoSQL and Databases",
        "difficulty": "intermediate",
        "prerequisites": ["SQL Basics"],
        "marks_weightage": 6,
        "semester": 3,
        "resource_url": "https://www.geeksforgeeks.org/introduction-to-nosql/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=uD3p_rZPBUQ"
    },
    {
        "subject": "OS",
        "topic_name": "Process and Threads",
        "difficulty": "beginner",
        "prerequisites": [],
        "marks_weightage": 8,
        "semester": 4,
        "resource_url": "https://www.geeksforgeeks.org/processes-in-linuxunix/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=OrM7nZcxXZU"
    },
    {
        "subject": "OS",
        "topic_name": "CPU Scheduling",
        "difficulty": "basic",
        "prerequisites": ["Process and Threads"],
        "marks_weightage": 9,
        "semester": 4,
        "resource_url": "https://www.youtube.com/watch?v=EWkQl0n0w5M",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/cpu-scheduling-in-operating-systems/"
    },
    {
        "subject": "OS",
        "topic_name": "Synchronization",
        "difficulty": "basic",
        "prerequisites": ["Process and Threads"],
        "marks_weightage": 8,
        "semester": 4,
        "resource_url": "https://www.youtube.com/watch?v=ph2awKa8r5Y",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/process-synchronization-set-1/"
    },
    {
        "subject": "OS",
        "topic_name": "Inter Process Communication",
        "difficulty": "basic",
        "prerequisites": ["Process and Threads", "Synchronization"],
        "marks_weightage": 7,
        "semester": 4,
        "resource_url": "https://www.geeksforgeeks.org/inter-process-communication-ipc/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=dJuYKfR8vec"
    },
    {
        "subject": "OS",
        "topic_name": "Deadlocks",
        "difficulty": "intermediate",
        "prerequisites": ["Synchronization"],
        "marks_weightage": 9,
        "semester": 4,
        "resource_url": "https://www.youtube.com/watch?v=UVo9mGARkhQ",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/introduction-of-deadlock-in-operating-system/"
    },
    {
        "subject": "OS",
        "topic_name": "Memory Management",
        "difficulty": "intermediate",
        "prerequisites": ["Process and Threads"],
        "marks_weightage": 8,
        "semester": 4,
        "resource_url": "https://www.youtube.com/watch?v=qdkxgs3EWvE",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/memory-management-in-operating-system/"
    },
    {
        "subject": "OS",
        "topic_name": "Paging and Segmentation",
        "difficulty": "intermediate",
        "prerequisites": ["Memory Management"],
        "marks_weightage": 8,
        "semester": 4,
        "resource_url": "https://www.youtube.com/watch?v=pJ6qrCB8pDw",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/paging-in-operating-system/"
    },
    {
        "subject": "OS",
        "topic_name": "Virtual Memory",
        "difficulty": "advanced",
        "prerequisites": ["Paging and Segmentation"],
        "marks_weightage": 8,
        "semester": 4,
        "resource_url": "https://www.youtube.com/watch?v=2quKyPnUShQ",
        "resource_type": "video",
        "alternate_resource_url": "https://www.geeksforgeeks.org/virtual-memory-in-operating-system/"
    },
    {
        "subject": "OS",
        "topic_name": "File Systems",
        "difficulty": "advanced",
        "prerequisites": ["Virtual Memory", "Memory Management"],
        "marks_weightage": 7,
        "semester": 4,
        "resource_url": "https://www.geeksforgeeks.org/file-systems-in-operating-system/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=KN8YgJnShPM"
    },
    {
        "subject": "OS",
        "topic_name": "IO Systems",
        "difficulty": "advanced",
        "prerequisites": ["File Systems"],
        "marks_weightage": 6,
        "semester": 4,
        "resource_url": "https://www.geeksforgeeks.org/io-interface-interrupt-dma-mode/",
        "resource_type": "notes",
        "alternate_resource_url": "https://www.youtube.com/watch?v=F18RiREDkwE"
    }
]


def seed_topics() -> None:
    """
    Seeds the predefined TOPICS into the AlloyDB database through a 2-pass sequence
    to appropriately resolve UUID-based self-referential prerequisite relationships.
    """
    topic_map: Dict[str, str] = {}
    
    # Generate UUIDs and build copied list
    topics_with_ids = []
    for t in TOPICS:
        t_copy = t.copy()
        t_copy["_id"] = str(uuid.uuid4())
        topic_map[t_copy["topic_name"]] = t_copy["_id"]
        topics_with_ids.append(t_copy)
        
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # First pass: Insert
            for t in topics_with_ids:
                cur.execute(
                    """
                    INSERT INTO topics (
                        id, subject, topic_name, difficulty,
                        prerequisites, marks_weightage,
                        semester, resource_url, resource_type,
                        alternate_resource_url
                    ) VALUES (
                        %s, %s, %s, %s, %s::uuid[],
                        %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        t["_id"],
                        t["subject"],
                        t["topic_name"],
                        t["difficulty"],
                        [],
                        t["marks_weightage"],
                        t["semester"],
                        t["resource_url"],
                        t["resource_type"],
                        t["alternate_resource_url"]
                    )
                )
                
            # Second pass: Update prerequisites
            for t in topics_with_ids:
                if t["prerequisites"]:
                    prereq_uuids = [topic_map[p] for p in t["prerequisites"]]
                    cur.execute(
                        """
                        UPDATE topics
                        SET prerequisites = %s::uuid[]
                        WHERE id = %s
                        """,
                        (prereq_uuids, t["_id"])
                    )

    logger.info("Seeded %d topics", len(topics_with_ids))


def check_existing() -> bool:
    """
    Checks if topics have already been seeded.
    Returns:
        True if records are found, False otherwise.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM topics")
            count = cur.fetchone()[0]
            
            if count > 0:
                logger.warning("Topics already exist (%d).", count)
                return True
                
            return False

if __name__ == "__main__":
    if check_existing():
        print("Topics already seeded. Delete existing rows to reseed.")
    else:
        seed_topics()
        print("Topics seeded successfully.")

"""Scan git commits for task-related keywords and auto-update task status."""

import subprocess
import re
import os
from tasks import TaskStore

DONE_PATTERNS = [
    r"(?:closes?|fixes?|done|erledigt|completed?)\s*#(\w+)",  # closes #abc123
    r"(?:closes?|fixes?|done|erledigt|completed?)\s*:\s*(.+)",  # done: Task Title
]


def scan_commits(project_id, since_days=7):
    """Scan recent git commits and mark matching tasks as done."""
    store = TaskStore(project_id)
    git_repo = store.data.get("git_repo", "")
    if not git_repo or not os.path.isdir(git_repo):
        return {"error": f"No valid git repo configured for project '{project_id}'"}

    try:
        result = subprocess.run(
            ["git", "log", f"--since={since_days} days ago", "--oneline", "--no-decorate"],
            capture_output=True, text=True, cwd=git_repo
        )
        if result.returncode != 0:
            return {"error": f"git log failed: {result.stderr}"}
    except FileNotFoundError:
        return {"error": "git not found"}

    commits = result.stdout.strip().split("\n") if result.stdout.strip() else []
    matched = []

    for commit_line in commits:
        for pattern in DONE_PATTERNS:
            for match in re.finditer(pattern, commit_line, re.IGNORECASE):
                identifier = match.group(1).strip()

                # Try matching by task ID
                task = store.get_task(identifier)
                if task and task["status"] != "done":
                    store.update_task(identifier, status="done")
                    matched.append({"task_id": identifier, "title": task["title"], "commit": commit_line})
                    continue

                # Try matching by title substring
                for task in store.list_tasks():
                    if task["status"] != "done" and identifier.lower() in task["title"].lower():
                        store.update_task(task["id"], status="done")
                        matched.append({"task_id": task["id"], "title": task["title"], "commit": commit_line})
                        break

    return {"scanned_commits": len(commits), "matched": matched}


if __name__ == "__main__":
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else "generative_fashion"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    result = scan_commits(project, days)
    print(f"Scanned {result.get('scanned_commits', 0)} commits")
    for m in result.get("matched", []):
        print(f"  ✓ {m['title']} (#{m['task_id']}) — {m['commit']}")
    if not result.get("matched"):
        print("  No new matches found.")

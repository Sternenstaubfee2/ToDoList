"""Import tasks from a TODO.md file into the dashboard JSON format."""

import re
import sys
import os
import json
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Category colors
CATEGORY_COLORS = {
    "done": "#6c757d",
    "prio1": "#e74c3c",
    "prio2": "#3498db",
    "prio3": "#2ecc71",
    "general": "#9b59b6",
}


def parse_todo_md(filepath):
    """Parse a TODO.md file and return categories + tasks."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    categories = []
    tasks = []
    current_category = None
    current_task = None
    in_done_section = False
    now = datetime.now().isoformat(timespec="seconds")

    for line in lines:
        stripped = line.rstrip()

        # Detect "## Erledigt" section
        if re.match(r"^##\s+Erledigt", stripped):
            in_done_section = True
            current_category = "done"
            if not any(c["id"] == "done" for c in categories):
                categories.append({
                    "id": "done",
                    "label": "Erledigt",
                    "color": CATEGORY_COLORS["done"],
                })
            continue

        # Detect "## Offen" — end of done section
        if re.match(r"^##\s+Offen", stripped):
            in_done_section = False
            if current_task:
                tasks.append(current_task)
                current_task = None
            continue

        # Detect priority headers: ### Priorität N — Label
        prio_match = re.match(r"^###\s+Priorität\s+(\d+)\s*[—–-]\s*(.+)", stripped)
        if prio_match:
            if current_task:
                tasks.append(current_task)
                current_task = None
            prio_num = int(prio_match.group(1))
            prio_label = prio_match.group(2).strip()
            cat_id = f"prio{prio_num}"
            current_category = cat_id
            in_done_section = False
            if not any(c["id"] == cat_id for c in categories):
                categories.append({
                    "id": cat_id,
                    "label": f"Priorität {prio_num} — {prio_label}",
                    "color": CATEGORY_COLORS.get(cat_id, "#9b59b6"),
                })
            continue

        # Detect top-level task: - [x] or - [ ] with bold title
        task_match = re.match(r"^- \[([ xX])\]\s+\*\*(.+?)\*\*\s*(.*)", stripped)
        if task_match:
            if current_task:
                tasks.append(current_task)
            checked = task_match.group(1).lower() == "x"
            title = task_match.group(2).strip()
            rest = task_match.group(3).strip()

            if in_done_section or checked:
                status = "done"
                cat = current_category if current_category else "done"
            else:
                status = "todo"
                cat = current_category if current_category else "general"

            # Clean leading ": " from inline descriptions
            if rest.startswith(": "):
                rest = rest[2:]

            current_task = {
                "id": uuid.uuid4().hex[:8],
                "title": title,
                "description": rest,
                "status": status,
                "priority": int(cat.replace("prio", "")) if cat.startswith("prio") else 0,
                "category": cat,
                "notes": "",
                "created_at": now,
                "updated_at": now,
            }
            continue

        # Sub-items or description lines (indented under a task)
        if current_task and stripped and (stripped.startswith("  ") or stripped.startswith("\t")):
            detail = stripped.strip()
            # Remove checkbox prefix from sub-items
            detail = re.sub(r"^- \[[ xX]\]\s*", "• ", detail)
            detail = re.sub(r"^- ", "• ", detail)
            if current_task["description"]:
                current_task["description"] += "\n" + detail
            else:
                current_task["description"] = detail
            continue

        # Separator or empty line
        if not stripped or stripped.startswith("---"):
            continue

    # Don't forget last task
    if current_task:
        tasks.append(current_task)

    return categories, tasks


def import_todo(todo_path, project_id, project_label=None, git_repo=None):
    """Import a TODO.md into a project JSON file."""
    categories, tasks = parse_todo_md(todo_path)

    project_data = {
        "project": project_id,
        "project_label": project_label or project_id,
        "git_repo": git_repo or "",
        "categories": categories,
        "tasks": tasks,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, f"{project_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    print(f"Imported {len(tasks)} tasks ({sum(1 for t in tasks if t['status']=='done')} done) into {out_path}")
    return project_data


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python importer.py <TODO.md path> <project_id> [project_label] [git_repo]")
        sys.exit(1)

    todo_path = sys.argv[1]
    project_id = sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else None
    repo = sys.argv[4] if len(sys.argv) > 4 else None
    import_todo(todo_path, project_id, label, repo)

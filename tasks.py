"""Task storage layer — JSON-based, one file per project."""

import json
import os
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _now():
    return datetime.now().isoformat(timespec="seconds")


class TaskStore:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.path = os.path.join(DATA_DIR, f"{project_id}.json")
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {
                "project": self.project_id,
                "project_label": self.project_id,
                "git_repo": "",
                "categories": [],
                "tasks": [],
                "members": ["Julia"],
            }

    def _save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        self._export_todo_md()

    def _export_todo_md(self):
        """Sync changes back to the project's TODO.md file."""
        todo_path = self.data.get("todo_md_path", "")
        if not todo_path:
            # Fallback: look for TODO.md in git_repo
            git_repo = self.data.get("git_repo", "")
            if git_repo:
                todo_path = os.path.join(git_repo, "TODO.md")
        if not todo_path or not os.path.isdir(os.path.dirname(todo_path)):
            return

        label = self.data.get("project_label", self.project_id)
        cats = {c["id"]: c for c in self.data.get("categories", [])}
        tasks = self.data.get("tasks", [])

        # Separate done tasks from open tasks
        done_tasks = [t for t in tasks if t["status"] == "done"]
        open_tasks = [t for t in tasks if t["status"] != "done"]

        # Group open tasks by category, preserving category order
        cat_order = [c["id"] for c in self.data.get("categories", []) if c["id"] != "done"]
        open_by_cat = {}
        for t in open_tasks:
            open_by_cat.setdefault(t["category"], []).append(t)

        lines = []
        lines.append(f"# {label} — TODO-Liste\n")

        # Done section
        lines.append("## Erledigt\n")
        for t in done_tasks:
            meta_parts = []
            if t.get("effort"):
                meta_parts.append(t["effort"])
            if t.get("time_estimate"):
                meta_parts.append(t["time_estimate"])
            if t.get("assignee"):
                meta_parts.append(f"@{t['assignee']}")
            meta_str = f" [{', '.join(meta_parts)}]" if meta_parts else ""
            lines.append(f"- [x] **{t['title']}**{meta_str}")
            if t.get("description"):
                for desc_line in t["description"].split("\n"):
                    cleaned = desc_line.strip()
                    if cleaned.startswith("• "):
                        cleaned = "- " + cleaned[2:]
                    elif cleaned and not cleaned.startswith("- "):
                        cleaned = "- " + cleaned
                    lines.append(f"  {cleaned}")
            if t.get("notes"):
                lines.append(f"  <!-- notes: {t['notes']} -->")
        lines.append("")

        # Open section
        lines.append("---\n")
        lines.append("## Offen\n")

        for cat_id in cat_order:
            cat_tasks = open_by_cat.pop(cat_id, [])
            if not cat_tasks and cat_id not in cats:
                continue
            cat_info = cats.get(cat_id, {"label": cat_id})
            lines.append(f"### {cat_info['label']}\n")
            for t in cat_tasks:
                check = "x" if t["status"] == "done" else " "
                status_marker = ""
                if t["status"] == "in-progress":
                    status_marker = " *(in Arbeit)*"
                meta_parts = []
                if t.get("effort"):
                    meta_parts.append(t["effort"])
                if t.get("time_estimate"):
                    meta_parts.append(t["time_estimate"])
                if t.get("assignee"):
                    meta_parts.append(f"@{t['assignee']}")
                meta_str = f" [{', '.join(meta_parts)}]" if meta_parts else ""
                lines.append(f"- [{check}] **{t['title']}**{status_marker}{meta_str}")
                if t.get("description"):
                    for desc_line in t["description"].split("\n"):
                        cleaned = desc_line.strip()
                        if cleaned.startswith("• "):
                            cleaned = "- " + cleaned[2:]
                        elif cleaned and not cleaned.startswith("- "):
                            cleaned = "- " + cleaned
                        lines.append(f"  {cleaned}")
                if t.get("notes"):
                    lines.append(f"  <!-- notes: {t['notes']} -->")
            lines.append("")

        # Any remaining categories not in the predefined order
        for cat_id, cat_tasks in open_by_cat.items():
            if not cat_tasks:
                continue
            cat_info = cats.get(cat_id, {"label": cat_id.replace("_", " ").title()})
            lines.append(f"### {cat_info['label']}\n")
            for t in cat_tasks:
                check = "x" if t["status"] == "done" else " "
                status_marker = ""
                if t["status"] == "in-progress":
                    status_marker = " *(in Arbeit)*"
                meta_parts = []
                if t.get("effort"):
                    meta_parts.append(t["effort"])
                if t.get("time_estimate"):
                    meta_parts.append(t["time_estimate"])
                if t.get("assignee"):
                    meta_parts.append(f"@{t['assignee']}")
                meta_str = f" [{', '.join(meta_parts)}]" if meta_parts else ""
                lines.append(f"- [{check}] **{t['title']}**{status_marker}{meta_str}")
                if t.get("description"):
                    for desc_line in t["description"].split("\n"):
                        cleaned = desc_line.strip()
                        if cleaned.startswith("• "):
                            cleaned = "- " + cleaned[2:]
                        elif cleaned and not cleaned.startswith("- "):
                            cleaned = "- " + cleaned
                        lines.append(f"  {cleaned}")
                if t.get("notes"):
                    lines.append(f"  <!-- notes: {t['notes']} -->")
            lines.append("")

        with open(todo_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # --- queries ---

    def list_tasks(self, status=None, category=None):
        tasks = self.data["tasks"]
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if category:
            tasks = [t for t in tasks if t["category"] == category]
        return tasks

    def get_task(self, task_id):
        for t in self.data["tasks"]:
            if t["id"] == task_id:
                return t
        return None

    def get_categories(self):
        return self.data.get("categories", [])

    # --- mutations ---

    def get_members(self):
        return self.data.get("members", ["Julia"])

    def add_member(self, name):
        members = self.data.setdefault("members", ["Julia"])
        if name not in members:
            members.append(name)
            self._save()
        return members

    def remove_member(self, name):
        members = self.data.get("members", [])
        if name in members:
            members.remove(name)
            self._save()
        return members

    def add_task(self, title, description="", status="todo", priority=2,
                 category="general", notes="", effort="", time_estimate="",
                 assignee="Julia"):
        task = {
            "id": uuid.uuid4().hex[:8],
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "category": category,
            "notes": notes,
            "effort": effort,
            "time_estimate": time_estimate,
            "assignee": assignee,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.data["tasks"].append(task)
        self._save()
        return task

    def update_task(self, task_id, **fields):
        task = self.get_task(task_id)
        if not task:
            return None
        allowed = {"title", "description", "status", "priority", "category", "notes",
                   "effort", "time_estimate", "assignee"}
        for k, v in fields.items():
            if k in allowed:
                task[k] = v
        task["updated_at"] = _now()
        self._save()
        return task

    def delete_task(self, task_id):
        before = len(self.data["tasks"])
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != task_id]
        if len(self.data["tasks"]) < before:
            self._save()
            return True
        return False

    def reorder_task(self, task_id, new_index):
        tasks = self.data["tasks"]
        task = None
        old_index = None
        for i, t in enumerate(tasks):
            if t["id"] == task_id:
                task = t
                old_index = i
                break
        if task is None:
            return False
        tasks.pop(old_index)
        tasks.insert(min(new_index, len(tasks)), task)
        self._save()
        return True


def list_projects():
    os.makedirs(DATA_DIR, exist_ok=True)
    projects = []
    for f in sorted(os.listdir(DATA_DIR)):
        if f.endswith(".json"):
            pid = f[:-5]
            try:
                with open(os.path.join(DATA_DIR, f), "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                projects.append({
                    "id": pid,
                    "label": data.get("project_label", pid),
                    "task_count": len(data.get("tasks", [])),
                    "git_repo": data.get("git_repo", ""),
                })
            except Exception:
                projects.append({"id": pid, "label": pid, "task_count": 0, "git_repo": ""})
    return projects


def detect_project(cwd=None):
    """Auto-detect which project the current directory belongs to.
    Walks up from cwd to find a git repo that matches a registered project.
    Returns project_id or None."""
    import subprocess

    if cwd is None:
        cwd = os.getcwd()

    # Get git root of cwd
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=cwd
        )
        if result.returncode != 0:
            return None
        git_root = os.path.normpath(result.stdout.strip())
    except Exception:
        return None

    # Match against registered projects
    os.makedirs(DATA_DIR, exist_ok=True)
    for f in os.listdir(DATA_DIR):
        if not f.endswith(".json"):
            continue
        try:
            with open(os.path.join(DATA_DIR, f), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            repo = data.get("git_repo", "")
            if repo and os.path.normpath(repo) == git_root:
                return f[:-5]
        except Exception:
            continue

    return None

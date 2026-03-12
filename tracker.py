"""Track git changes and write summaries into task tickets."""

import subprocess
import os
import re
from datetime import datetime
from tasks import TaskStore

TODOLISTS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_git_summary(repo_path, commit_hash=None):
    """Get a structured summary of changes from a git commit or working tree."""
    result = {}

    if commit_hash:
        # Specific commit
        cmd_msg = ["git", "log", "-1", "--pretty=format:%s", commit_hash]
        cmd_files = ["git", "diff-tree", "--no-commit-id", "-r", "--name-status", commit_hash]
        cmd_stats = ["git", "diff-tree", "--no-commit-id", "--stat", commit_hash]
        cmd_hash = ["git", "log", "-1", "--pretty=format:%h", commit_hash]
    else:
        # Latest commit
        cmd_msg = ["git", "log", "-1", "--pretty=format:%s"]
        cmd_files = ["git", "diff-tree", "--no-commit-id", "-r", "--name-status", "HEAD"]
        cmd_stats = ["git", "diff-tree", "--no-commit-id", "--stat", "HEAD"]
        cmd_hash = ["git", "log", "-1", "--pretty=format:%h"]

    def run(cmd):
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_path)
        return r.stdout.strip() if r.returncode == 0 else ""

    result["hash"] = run(cmd_hash)
    result["message"] = run(cmd_msg)
    result["stats"] = run(cmd_stats)

    # Parse file changes
    raw_files = run(cmd_files)
    changes = {"added": [], "modified": [], "deleted": [], "renamed": []}
    for line in raw_files.split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0][0]  # First char: A, M, D, R
        filepath = parts[-1]
        if status == "A":
            changes["added"].append(filepath)
        elif status == "M":
            changes["modified"].append(filepath)
        elif status == "D":
            changes["deleted"].append(filepath)
        elif status == "R":
            changes["renamed"].append(f"{parts[1]} → {parts[2]}" if len(parts) > 2 else filepath)

    result["changes"] = changes
    return result


def format_change_entry(summary, timestamp=None):
    """Format a git summary into a readable ticket entry."""
    ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M")
    changes = summary["changes"]

    lines = []
    lines.append(f"--- Commit {summary['hash']} ({ts}) ---")
    lines.append(f"{summary['message']}")
    lines.append("")

    if changes["added"]:
        lines.append(f"  Neue Dateien ({len(changes['added'])}):")
        for f in changes["added"]:
            lines.append(f"    + {f}")
    if changes["modified"]:
        lines.append(f"  Geänderte Dateien ({len(changes['modified'])}):")
        for f in changes["modified"]:
            lines.append(f"    ~ {f}")
    if changes["deleted"]:
        lines.append(f"  Gelöschte Dateien ({len(changes['deleted'])}):")
        for f in changes["deleted"]:
            lines.append(f"    - {f}")
    if changes["renamed"]:
        lines.append(f"  Umbenannt ({len(changes['renamed'])}):")
        for f in changes["renamed"]:
            lines.append(f"    ↔ {f}")

    total = sum(len(v) for v in changes.values())
    lines.append(f"  Gesamt: {total} Dateien betroffen")

    # Add short stats if available
    if summary.get("stats"):
        stat_lines = summary["stats"].strip().split("\n")
        if stat_lines:
            last_line = stat_lines[-1].strip()
            lines.append(f"  {last_line}")

    return "\n".join(lines)


def track_commit_to_ticket(project_id, ticket_id, repo_path, commit_hash=None):
    """Read a git commit and append its summary to a task's notes."""
    store = TaskStore(project_id)
    task = store.get_task(ticket_id)
    if not task:
        return {"error": f"Task #{ticket_id} not found in project '{project_id}'"}

    summary = get_git_summary(repo_path, commit_hash)
    if not summary["hash"]:
        return {"error": "Could not read git commit"}

    entry = format_change_entry(summary)
    existing_notes = task.get("notes", "")
    new_notes = (existing_notes + "\n\n" + entry).strip() if existing_notes else entry
    store.update_task(ticket_id, notes=new_notes)

    return {
        "ok": True,
        "task": task["title"],
        "commit": summary["hash"],
        "files_changed": sum(len(v) for v in summary["changes"].values()),
    }


def find_ticket_ids_in_message(message):
    """Extract ticket IDs from commit message. Supports #abc123 format."""
    return re.findall(r"#([a-f0-9]{6,8})", message, re.IGNORECASE)


def auto_track_from_commit(repo_path, project_id=None):
    """Called by post-commit hook. Reads latest commit, finds ticket refs, updates tasks."""
    # Auto-detect project from repo path if not given
    if not project_id:
        project_id = _detect_project(repo_path)
        if not project_id:
            return {"error": "Could not detect project ID"}

    summary = get_git_summary(repo_path)
    ticket_ids = find_ticket_ids_in_message(summary["message"])

    if not ticket_ids:
        return {"skipped": True, "reason": "No ticket IDs in commit message"}

    results = []
    for tid in ticket_ids:
        result = track_commit_to_ticket(project_id, tid, repo_path)
        results.append(result)

    return {"tracked": results}


def _detect_project(repo_path):
    """Try to find which project a repo path belongs to."""
    from tasks import detect_project
    return detect_project(repo_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python tracker.py track <project_id> <ticket_id> [repo_path] [commit_hash]")
        print("  python tracker.py hook <repo_path> [project_id]")
        print("  python tracker.py install <repo_path> [project_id]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "track":
        project_id = sys.argv[2]
        ticket_id = sys.argv[3]
        repo_path = sys.argv[4] if len(sys.argv) > 4 else "."
        commit_hash = sys.argv[5] if len(sys.argv) > 5 else None
        result = track_commit_to_ticket(project_id, ticket_id, repo_path, commit_hash)
        if result.get("ok"):
            print(f"  Tracked commit {result['commit']} → #{ticket_id} ({result['task']})")
            print(f"  {result['files_changed']} files changed")
        else:
            print(f"  Error: {result.get('error')}")

    elif cmd == "hook":
        repo_path = sys.argv[2] if len(sys.argv) > 2 else "."
        project_id = sys.argv[3] if len(sys.argv) > 3 else None
        result = auto_track_from_commit(repo_path, project_id)
        if result.get("skipped"):
            pass  # Silent — no ticket refs in commit
        elif result.get("tracked"):
            for r in result["tracked"]:
                if r.get("ok"):
                    print(f"  Tracked → #{r.get('commit')} → {r.get('task')}")
        elif result.get("error"):
            print(f"  Error: {result['error']}")

    elif cmd == "install":
        repo_path = sys.argv[2]
        project_id = sys.argv[3] if len(sys.argv) > 3 else None

        hook_dir = os.path.join(repo_path, ".git", "hooks")
        hook_path = os.path.join(hook_dir, "post-commit")
        os.makedirs(hook_dir, exist_ok=True)

        tracker_abs = os.path.abspath(__file__).replace("\\", "/")
        repo_abs = os.path.abspath(repo_path).replace("\\", "/")
        project_arg = f' "{project_id}"' if project_id else ""

        hook_content = f"""#!/bin/sh
# Auto-track commits to TaskBoard tickets
# Referenziere Tickets mit #ticket_id in der Commit-Message
python "{tracker_abs}" hook "{repo_abs}"{project_arg}
"""
        with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(hook_content)

        # Make executable (Unix)
        try:
            os.chmod(hook_path, 0o755)
        except Exception:
            pass

        print(f"  Post-commit hook installed: {hook_path}")
        print(f"  Tracker: {tracker_abs}")
        print(f"  Repo: {repo_abs}")
        if project_id:
            print(f"  Project: {project_id}")
        print()
        print("  Nutze #ticket_id in Commit-Messages, z.B.:")
        print('  git commit -m "Crop-Top Panels konfiguriert #a1b2c3d4"')

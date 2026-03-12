"""CLI tool for managing tasks from the terminal."""

import argparse
import sys
import os
from tasks import TaskStore, list_projects, detect_project

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

STATUS_COLORS = {"todo": YELLOW, "in-progress": BLUE, "done": GREEN}
PRIO_COLORS = {1: RED, 2: BLUE, 3: GREEN}


def cmd_list(args):
    store = TaskStore(args.project)
    tasks = store.list_tasks(status=args.status, category=args.category)
    if not tasks:
        print(f"  {GRAY}No tasks found.{RESET}")
        return

    # Group by category
    by_cat = {}
    for t in tasks:
        by_cat.setdefault(t["category"], []).append(t)

    cats = {c["id"]: c["label"] for c in store.get_categories()}
    for cat_id, cat_tasks in by_cat.items():
        label = cats.get(cat_id, cat_id)
        print(f"\n  {BOLD}{MAGENTA}{label}{RESET}")
        for t in cat_tasks:
            sc = STATUS_COLORS.get(t["status"], "")
            pc = PRIO_COLORS.get(t.get("priority"), "")
            status_icon = {"todo": "○", "in-progress": "◐", "done": "●"}.get(t["status"], "?")
            print(f"    {sc}{status_icon}{RESET} {GRAY}#{t['id']}{RESET}  {pc}P{t.get('priority','?')}{RESET}  {t['title']}")
    print()


def cmd_done(args):
    store = TaskStore(args.project)
    task = store.update_task(args.task_id, status="done")
    if task:
        print(f"  {GREEN}●{RESET} Marked as done: {BOLD}{task['title']}{RESET}")
    else:
        print(f"  {RED}Task #{args.task_id} not found.{RESET}")


def cmd_progress(args):
    store = TaskStore(args.project)
    task = store.update_task(args.task_id, status="in-progress")
    if task:
        print(f"  {BLUE}◐{RESET} In progress: {BOLD}{task['title']}{RESET}")
    else:
        print(f"  {RED}Task #{args.task_id} not found.{RESET}")


def cmd_todo(args):
    store = TaskStore(args.project)
    task = store.update_task(args.task_id, status="todo")
    if task:
        print(f"  {YELLOW}○{RESET} Back to todo: {BOLD}{task['title']}{RESET}")
    else:
        print(f"  {RED}Task #{args.task_id} not found.{RESET}")


def cmd_add(args):
    store = TaskStore(args.project)
    task = store.add_task(
        title=args.title,
        category=args.category or "general",
        priority=args.priority or 2,
        description=args.description or "",
    )
    print(f"  {GREEN}+{RESET} Added: {BOLD}{task['title']}{RESET}  {GRAY}#{task['id']}{RESET}")


def cmd_note(args):
    store = TaskStore(args.project)
    task = store.get_task(args.task_id)
    if not task:
        print(f"  {RED}Task #{args.task_id} not found.{RESET}")
        return
    existing = task.get("notes", "")
    new_notes = (existing + "\n" + args.text).strip() if existing else args.text
    store.update_task(args.task_id, notes=new_notes)
    print(f"  {CYAN}📝{RESET} Note added to: {BOLD}{task['title']}{RESET}")


def cmd_track(args):
    from tracker import track_commit_to_ticket
    repo = args.repo or "."
    result = track_commit_to_ticket(args.project, args.task_id, repo, args.commit)
    if result.get("ok"):
        print(f"  {GREEN}+{RESET} Tracked commit {CYAN}{result['commit']}{RESET} → {BOLD}{result['task']}{RESET}")
        print(f"    {result['files_changed']} Dateien betroffen")
    else:
        print(f"  {RED}{result.get('error')}{RESET}")


def cmd_install_hook(args):
    from tracker import auto_track_from_commit
    import subprocess
    tracker_abs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker.py").replace("\\", "/")
    repo_abs = os.path.abspath(args.repo).replace("\\", "/")
    project_arg = f' "{args.project}"' if args.project != "generative_fashion" else ' "generative_fashion"'

    hook_dir = os.path.join(args.repo, ".git", "hooks")
    hook_path = os.path.join(hook_dir, "post-commit")
    os.makedirs(hook_dir, exist_ok=True)

    hook_content = f"""#!/bin/sh
# Auto-track commits to TaskBoard tickets
python "{tracker_abs}" hook "{repo_abs}"{project_arg}
"""
    with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(hook_content)
    try:
        os.chmod(hook_path, 0o755)
    except Exception:
        pass

    print(f"  {GREEN}+{RESET} Post-commit hook installiert in {CYAN}{hook_path}{RESET}")
    print(f"    Nutze {BOLD}#ticket_id{RESET} in Commit-Messages, z.B.:")
    print(f'    git commit -m "Crop-Top Panels konfiguriert {CYAN}#a1b2c3d4{RESET}"')


def cmd_init(args):
    import subprocess
    repo_path = os.path.abspath(args.repo or ".")

    # Auto-generate project_id from folder name if not given
    project_id = args.id or os.path.basename(repo_path).lower().replace(" ", "_").replace("-", "_")
    label = args.label or os.path.basename(repo_path)

    # Check if already registered
    existing = detect_project(repo_path)
    if existing:
        print(f"  {YELLOW}!{RESET} Repo bereits registriert als {BOLD}{existing}{RESET}")
        return

    store = TaskStore(project_id)
    store.data["project_label"] = label
    store.data["git_repo"] = repo_path.replace("\\", "/")
    store.data["members"] = ["Julia"]
    store.data["categories"] = [
        {"id": "bug", "label": "Bugs & Fixes", "color": "#e74c3c"},
        {"id": "feature", "label": "Features", "color": "#3498db"},
        {"id": "ops", "label": "Ops & Infra", "color": "#2ecc71"},
        {"id": "docs", "label": "Dokumentation", "color": "#f59e0b"},
    ]
    store._save()

    print(f"  {GREEN}+{RESET} Projekt erstellt: {BOLD}{label}{RESET}  {GRAY}({project_id}){RESET}")
    print(f"    Repo: {repo_path}")
    print(f"    Daten: {store.path}")

    # Optionally install hook
    if args.hook:
        args.project = project_id
        cmd_install_hook(args)
    else:
        print(f"\n    Hook installieren mit:")
        print(f"    {CYAN}python cli.py install-hook \"{repo_path}\"{RESET}")


def cmd_projects(args):
    projects = list_projects()
    if not projects:
        print(f"  {GRAY}No projects found. Run 'cli.py init' first.{RESET}")
        return
    for p in projects:
        repo_info = f", repo: {p['git_repo']}" if p.get("git_repo") else ""
        print(f"  {BOLD}{p['label']}{RESET}  {GRAY}({p['id']}, {p['task_count']} tasks{repo_info}){RESET}")


def main():
    parser = argparse.ArgumentParser(description="Task Dashboard CLI")
    auto_project = detect_project() or "generative_fashion"
    parser.add_argument("-p", "--project", default=auto_project,
                        help=f"Project ID (auto-detected: {auto_project})")
    sub = parser.add_subparsers(dest="command")

    # list
    ls = sub.add_parser("list", aliases=["ls"], help="List tasks")
    ls.add_argument("-s", "--status", choices=["todo", "in-progress", "done"])
    ls.add_argument("-c", "--category")
    ls.set_defaults(func=cmd_list)

    # done
    d = sub.add_parser("done", help="Mark task as done")
    d.add_argument("task_id")
    d.set_defaults(func=cmd_done)

    # progress
    p = sub.add_parser("progress", aliases=["wip"], help="Mark task as in-progress")
    p.add_argument("task_id")
    p.set_defaults(func=cmd_progress)

    # todo
    t = sub.add_parser("todo", help="Mark task as todo")
    t.add_argument("task_id")
    t.set_defaults(func=cmd_todo)

    # add
    a = sub.add_parser("add", help="Add a new task")
    a.add_argument("title")
    a.add_argument("-c", "--category")
    a.add_argument("-P", "--priority", type=int)
    a.add_argument("-d", "--description", default="")
    a.set_defaults(func=cmd_add)

    # note
    n = sub.add_parser("note", help="Add a note to a task")
    n.add_argument("task_id")
    n.add_argument("text")
    n.set_defaults(func=cmd_note)

    # track
    tr = sub.add_parser("track", help="Track a git commit to a task ticket")
    tr.add_argument("task_id", help="Task/Ticket ID")
    tr.add_argument("-r", "--repo", default=".", help="Git repo path")
    tr.add_argument("-c", "--commit", default=None, help="Specific commit hash (default: HEAD)")
    tr.set_defaults(func=cmd_track)

    # install-hook
    ih = sub.add_parser("install-hook", help="Install post-commit hook in a repo")
    ih.add_argument("repo", help="Path to git repo")
    ih.set_defaults(func=cmd_install_hook)

    # init
    ini = sub.add_parser("init", help="Register a new project from a git repo")
    ini.add_argument("-r", "--repo", default=".", help="Git repo path (default: current dir)")
    ini.add_argument("--id", default=None, help="Project ID (default: folder name)")
    ini.add_argument("-l", "--label", default=None, help="Display name")
    ini.add_argument("--hook", action="store_true", help="Also install post-commit hook")
    ini.set_defaults(func=cmd_init)

    # projects
    sub.add_parser("projects", help="List all projects").set_defaults(func=cmd_projects)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

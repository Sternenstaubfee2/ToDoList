"""Flask dashboard app — colorful Kanban-style task board."""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from tasks import TaskStore, list_projects
from git_sync import scan_commits
from tracker import track_commit_to_ticket

app = Flask(__name__)


@app.route("/")
def index():
    projects = list_projects()
    if projects:
        return redirect(url_for("board", project=projects[0]["id"]))
    return render_template("board.html", project=None, projects=[], categories=[], tasks=[])


@app.route("/board/<project>")
def board(project):
    store = TaskStore(project)
    projects = list_projects()
    return render_template(
        "board.html",
        project=store.data,
        projects=projects,
        categories=store.get_categories(),
        tasks=store.list_tasks(),
        members=store.get_members(),
        current_project=project,
    )


# --- API ---

@app.route("/api/<project>/tasks", methods=["GET"])
def api_list_tasks(project):
    store = TaskStore(project)
    return jsonify(store.list_tasks())


@app.route("/api/<project>/tasks", methods=["POST"])
def api_add_task(project):
    store = TaskStore(project)
    data = request.json
    task = store.add_task(
        title=data.get("title", ""),
        description=data.get("description", ""),
        status=data.get("status", "todo"),
        priority=data.get("priority", 2),
        category=data.get("category", "general"),
        notes=data.get("notes", ""),
        effort=data.get("effort", ""),
        time_estimate=data.get("time_estimate", ""),
        assignee=data.get("assignee", "Julia"),
    )
    return jsonify(task), 201


@app.route("/api/<project>/tasks/<task_id>", methods=["PUT"])
def api_update_task(project, task_id):
    store = TaskStore(project)
    data = request.json
    task = store.update_task(task_id, **data)
    if task:
        return jsonify(task)
    return jsonify({"error": "not found"}), 404


@app.route("/api/<project>/tasks/<task_id>", methods=["DELETE"])
def api_delete_task(project, task_id):
    store = TaskStore(project)
    if store.delete_task(task_id):
        return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404


@app.route("/api/<project>/tasks/<task_id>/reorder", methods=["PUT"])
def api_reorder_task(project, task_id):
    store = TaskStore(project)
    data = request.json
    store.reorder_task(task_id, data.get("index", 0))
    return jsonify({"ok": True})


@app.route("/api/<project>/members", methods=["GET"])
def api_get_members(project):
    store = TaskStore(project)
    return jsonify(store.get_members())


@app.route("/api/<project>/members", methods=["POST"])
def api_add_member(project):
    store = TaskStore(project)
    name = request.json.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    return jsonify(store.add_member(name))


@app.route("/api/<project>/members/<name>", methods=["DELETE"])
def api_remove_member(project, name):
    store = TaskStore(project)
    return jsonify(store.remove_member(name))


@app.route("/api/<project>/tasks/<task_id>/track", methods=["POST"])
def api_track_commit(project, task_id):
    store = TaskStore(project)
    repo_path = store.data.get("git_repo", "")
    data = request.json or {}
    commit_hash = data.get("commit")
    result = track_commit_to_ticket(project, task_id, repo_path, commit_hash)
    return jsonify(result)


@app.route("/api/<project>/git-sync", methods=["POST"])
def api_git_sync(project):
    result = scan_commits(project)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5555)

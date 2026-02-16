#!/bin/bash

# Fix 1: models.py — add next_id increment after creating a task
cat > /app/models.py << 'PYEOF'
class TaskStore:
    def __init__(self):
        self.tasks = {}
        self.next_id = 1

    def create(self, title, description=""):
        task = {
            "id": self.next_id,
            "title": title,
            "description": description,
            "done": False,
        }
        self.tasks[self.next_id] = task
        self.next_id += 1
        return task

    def get(self, task_id):
        return self.tasks.get(task_id)

    def get_all(self):
        return list(self.tasks.values())

    def update(self, task_id, **kwargs):
        task = self.tasks.get(task_id)
        if task is None:
            return None
        for key in ("title", "description", "done"):
            if key in kwargs:
                task[key] = kwargs[key]
        return task

    def delete(self, task_id):
        return self.tasks.pop(task_id, None)


store = TaskStore()
PYEOF

# Fix 2 & 3: routes.py — POST returns 201, DELETE returns 204 with no body
cat > /app/routes.py << 'PYEOF'
from flask import Blueprint, jsonify, request

from models import store

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/tasks", methods=["GET"])
def list_tasks():
    return jsonify(store.get_all()), 200


@tasks_bp.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "title is required"}), 400
    task = store.create(
        title=data["title"],
        description=data.get("description", ""),
    )
    return jsonify(task), 201


@tasks_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = store.get(task_id)
    if task is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(task), 200


@tasks_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "request body required"}), 400
    task = store.update(task_id, **data)
    if task is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(task), 200


@tasks_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = store.delete(task_id)
    if task is None:
        return jsonify({"error": "not found"}), 404
    return "", 204
PYEOF

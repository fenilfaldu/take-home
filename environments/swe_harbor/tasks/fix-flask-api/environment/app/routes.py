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
    # BUG: should return 201 Created, not 200
    return jsonify(task), 200


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
    # BUG: should return 204 No Content with empty body, not 200 with JSON
    return jsonify({"message": "deleted"}), 200

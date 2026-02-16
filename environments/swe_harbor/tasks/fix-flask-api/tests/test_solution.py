import sys

sys.path.insert(0, "/app")

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Reset the store before each test
        from models import store

        store.tasks.clear()
        store.next_id = 1
        yield client


# --- GET /tasks ---


def test_list_tasks_empty(client):
    resp = client.get("/tasks")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.get_json() == [], "Empty task list should return []"


def test_list_tasks_with_data(client):
    client.post("/tasks", json={"title": "Task 1"})
    client.post("/tasks", json={"title": "Task 2"})
    resp = client.get("/tasks")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2, f"Expected 2 tasks, got {len(data)}"


# --- POST /tasks ---


def test_create_task_status_code(client):
    resp = client.post("/tasks", json={"title": "New task"})
    assert resp.status_code == 201, (
        f"POST /tasks should return 201 Created, got {resp.status_code}"
    )


def test_create_task_returns_task(client):
    resp = client.post(
        "/tasks", json={"title": "Buy milk", "description": "2% milk"}
    )
    data = resp.get_json()
    assert data["title"] == "Buy milk", f"Expected title 'Buy milk', got {data['title']}"
    assert data["description"] == "2% milk"
    assert data["done"] is False, "New task should not be done"


def test_create_task_assigns_unique_ids(client):
    resp1 = client.post("/tasks", json={"title": "Task 1"})
    resp2 = client.post("/tasks", json={"title": "Task 2"})
    id1 = resp1.get_json()["id"]
    id2 = resp2.get_json()["id"]
    assert id1 != id2, (
        f"Each task should get a unique ID, but both got id={id1}"
    )


def test_create_task_increments_ids(client):
    resp1 = client.post("/tasks", json={"title": "Task 1"})
    resp2 = client.post("/tasks", json={"title": "Task 2"})
    resp3 = client.post("/tasks", json={"title": "Task 3"})
    ids = [r.get_json()["id"] for r in [resp1, resp2, resp3]]
    assert ids == [1, 2, 3], f"IDs should be [1, 2, 3], got {ids}"


def test_create_task_missing_title(client):
    resp = client.post("/tasks", json={"description": "no title"})
    assert resp.status_code == 400, "Missing title should return 400"


def test_create_task_default_description(client):
    resp = client.post("/tasks", json={"title": "Simple"})
    data = resp.get_json()
    assert data["description"] == "", "Default description should be empty string"


# --- GET /tasks/<id> ---


def test_get_task_by_id(client):
    create_resp = client.post("/tasks", json={"title": "Find me"})
    task_id = create_resp.get_json()["id"]
    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Find me"


def test_get_task_not_found(client):
    resp = client.get("/tasks/999")
    assert resp.status_code == 404, (
        f"Getting non-existent task should return 404, got {resp.status_code}"
    )


# --- PUT /tasks/<id> ---


def test_update_task(client):
    create_resp = client.post("/tasks", json={"title": "Original"})
    task_id = create_resp.get_json()["id"]
    resp = client.put(f"/tasks/{task_id}", json={"title": "Updated", "done": True})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["title"] == "Updated", "Title should be updated"
    assert data["done"] is True, "Done should be updated to True"


def test_update_task_not_found(client):
    resp = client.put("/tasks/999", json={"title": "Ghost"})
    assert resp.status_code == 404


def test_update_task_partial(client):
    create_resp = client.post(
        "/tasks", json={"title": "Original", "description": "Keep me"}
    )
    task_id = create_resp.get_json()["id"]
    resp = client.put(f"/tasks/{task_id}", json={"title": "Changed"})
    data = resp.get_json()
    assert data["title"] == "Changed"
    assert data["description"] == "Keep me", (
        "Description should be unchanged in partial update"
    )


# --- DELETE /tasks/<id> ---


def test_delete_task_status_code(client):
    create_resp = client.post("/tasks", json={"title": "Delete me"})
    task_id = create_resp.get_json()["id"]
    resp = client.delete(f"/tasks/{task_id}")
    assert resp.status_code == 204, (
        f"DELETE should return 204 No Content, got {resp.status_code}"
    )


def test_delete_task_empty_body(client):
    create_resp = client.post("/tasks", json={"title": "Delete me"})
    task_id = create_resp.get_json()["id"]
    resp = client.delete(f"/tasks/{task_id}")
    assert resp.data == b"" or resp.data == b"", (
        "DELETE 204 response should have no body"
    )


def test_delete_task_removes_it(client):
    create_resp = client.post("/tasks", json={"title": "Gone"})
    task_id = create_resp.get_json()["id"]
    client.delete(f"/tasks/{task_id}")
    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 404, "Deleted task should not be found"


def test_delete_task_not_found(client):
    resp = client.delete("/tasks/999")
    assert resp.status_code == 404

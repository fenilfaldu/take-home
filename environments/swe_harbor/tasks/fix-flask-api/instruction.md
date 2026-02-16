## Fix the Flask Task Manager API

The file `/app/` contains a Flask REST API for a simple task manager. The API has **3 bugs** that need to be fixed. The application should work as follows:

### Endpoints

- `GET /tasks` — Return all tasks as a JSON array. Status: **200**.
- `POST /tasks` — Create a new task. Accepts JSON with a `"title"` field (required) and an optional `"description"` field. Returns the created task as JSON. Status: **201**.
- `GET /tasks/<id>` — Return a single task by ID. Status: **200**, or **404** if not found.
- `PUT /tasks/<id>` — Update a task by ID. Accepts JSON with optional `"title"`, `"description"`, and `"done"` fields. Returns the updated task. Status: **200**, or **404** if not found.
- `DELETE /tasks/<id>` — Delete a task by ID. Status: **204** (no response body), or **404** if not found.

### Task format

```json
{
    "id": 1,
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "done": false
}
```

### What to fix

Find and fix all 3 bugs in the existing code. The bugs are in `models.py` and `routes.py`. Do **not** modify `app.py`. Each bug causes incorrect HTTP behavior — look at the endpoint specifications above and compare them with the actual code behavior.

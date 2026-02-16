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
        # BUG: next_id is never incremented, so all tasks get id=1
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

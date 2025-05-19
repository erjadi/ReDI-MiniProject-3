# 🛠️ Mini Project Assignment: To-Do API Backend

## 🎯 Objective

Your assignment is to implement a RESTful API backend for a **To-Do application**, using Python and FastAPI.
You must support managing tasks, tags, completion status, recurrence, due dates, and flexible **lists**.

---

## ✅ Requirements

### 1. General

* Use **FastAPI** (with `pydantic` models).
* Use either **in-memory** storage (for simplicity) or **SQLite**.
* Enable **CORS** for all origins (to allow frontend development).

---

### 2. Task Model

A task has the following fields:

| Field                 | Type      | Required | Description                           |
| --------------------- | --------- | -------- | ------------------------------------- |
| id                    | string    | auto     | Unique task identifier (UUID)         |
| title                 | string    | Yes      | Task title                            |
| description           | string    | No       | Task details                          |
| tags                  | string\[] | No       | List of category labels               |
| completed             | boolean   | No       | Task is done (default: false)         |
| due\_date             | datetime  | No       | Deadline for task (ISO8601)           |
| recurrence            | string    | No       | "daily", "weekly", "monthly", or null |
| recurrence\_end\_date | date      | No       | When recurrence ends                  |
| list                  | string    | No       | List name (default: "Personal")       |
| created\_at           | datetime  | auto     | Timestamp set by backend              |

---

### 3. List Model

* Each task **must** belong to one list.
* There are at least two default lists: `"Personal"` and `"Work"`.
* Lists can be created and deleted (but `"Personal"` cannot be deleted).
* You **cannot delete** a list that has tasks assigned to it.

---

### 4. API Endpoints

Your API **must** implement these endpoints with the described behavior:

#### Tasks

* `GET /tasks`
  List all tasks. Filter by: `completed`, `tags`, or `list` (via query params).

* `POST /tasks`
  Create a new task. List must exist, or return error 400.

* `GET /tasks/{task_id}`
  Fetch a task by its ID. Return 404 if not found.

* `PUT /tasks/{task_id}`
  Update any fields of a task. Changing `list` requires the list to exist.

* `DELETE /tasks/{task_id}`
  Delete a task by its ID.

#### Lists

* `GET /lists`
  List all available lists (as objects: `{ "name": "..." }`).

* `POST /lists`
  Create a new list by name. List names must be unique.

* `DELETE /lists/{name}`
  Delete a list by name.
  Cannot delete `"Personal"` or lists that have tasks.

---

## 🌟 API Interface Definition

**Task Object Example:**

```json
{
  "id": "c4e4a84b-5166-4a7b-88a5-f2c7c53cbbfa",
  "title": "Buy milk",
  "description": "Get 2 liters",
  "tags": ["shopping", "urgent"],
  "completed": false,
  "due_date": "2025-08-01T12:00:00",
  "recurrence": "weekly",
  "recurrence_end_date": "2025-12-01",
  "list": "Personal",
  "created_at": "2025-06-01T10:00:00"
}
```

**List Object Example:**

```json
{ "name": "Personal" }
```

---

## 💻 API Endpoints & Sample Requests

### List Tasks

```
GET /tasks?list=Personal&completed=false&tags=urgent,shopping
```

### Create Task

```
POST /tasks
{
  "title": "Write essay",
  "list": "Work",
  "tags": ["school"],
  "due_date": "2025-09-10T17:00:00"
}
```

### List All Lists

```
GET /lists
```

### Create New List

```
POST /lists
{
  "name": "Groceries"
}
```

### Delete a List

```
DELETE /lists/Groceries
```

---

## 🔥 Submission Checklist

* [ ] All endpoints above are implemented
* [ ] Returns correct status codes (400/404/201/204)
* [ ] Uses CORS middleware
* [ ] Follows interface definition
* [ ] Handles error cases (e.g. cannot delete "Personal" list)

---

**Tip:** You can start by returning `501 Not Implemented` and then fill in the logic step by step!

Good luck 🚀

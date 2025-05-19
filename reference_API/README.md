# 📝 To-Do API Exercise

Welcome to the ReDI To-Do API exercise! This project will guide you through creating a RESTful API backend for a To-Do application using Python and FastAPI.

## 🎯 Project Overview

In this exercise, you will implement a backend API for a task management application that supports:
- Creating, reading, updating, and deleting tasks
- Organizing tasks into lists
- Adding tags, due dates, and recurrence settings
- Filtering tasks by various criteria

## 🚀 Getting Started

### Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Examine the API specification in `api_definition.md` for detailed requirements

3. Start with the skeleton implementation:
   ```bash
   uvicorn api_skeleton:app --reload
   ```

4. Access the API documentation at http://localhost:8000/docs when the server is running

## 📋 API Structure

The API consists of two main resource types:

1. **Tasks**: The core entities with properties like title, description, tags, due dates, and recurrence
2. **Lists**: Containers for organizing related tasks (e.g., "Personal", "Work")

See `api_definition.md` for the complete API specification and requirements.

## 💻 Implementation Options

You can choose one of two storage implementations:

1. **In-memory storage**: Simpler approach using Python data structures
2. **SQLite database**: More robust persistence using a local database file

If you choose the SQLite option, you can use this table creation script:

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT,
    completed INTEGER DEFAULT 0,
    due_date TEXT,
    recurrence TEXT,
    recurrence_end_date TEXT,
    created_at TEXT,
    list TEXT DEFAULT 'Personal'
)
```

## 🧪 Testing Tools

The `./Testing` directory contains tools to help you test your implementation:

1. **test_todo_api.py**: A comprehensive test suite that verifies all API requirements
   - Run it with: `python ../testing/test_todo_api.py`
   - Tests are organized by endpoint category (/tasks, /lists, General)
   - Provides a detailed summary of passing and failing tests

2. **create_tasks.py**: A utility to populate your API with sample data
   - Create lists: `python ../testing/create_tasks.py --create-list "Study"`
   - Generate tasks: `python ../testing/create_tasks.py --keywords "study,homework" --count 5 --list "Study"`
   - Show lists: `python ../testing/create_tasks.py --show-lists`

## 📈 Development Approach

1. Start with the skeleton implementation in `api_skeleton.py`
2. Implement the endpoints one by one, following the specification
3. Run tests regularly to check your progress
4. Aim to make more tests pass with each iteration

Happy coding! 🚀
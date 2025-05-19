import httpx
import json
import uuid
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"
results = []

def run_test(group, name, func):
    try:
        func()
        print(f"  ✅ {name}")
        results.append((group, name, True, ""))
    except AssertionError as e:
        print(f"  ❌ {name} — {e}")
        results.append((group, name, False, str(e)))
    except Exception as e:
        print(f"  ❌ {name} — Exception: {e}")
        results.append((group, name, False, str(e)))

def cleanup():
    """Attempt to reset the API to a clean state for testing"""
    # Get all tasks and delete them
    try:
        r = httpx.get(f"{BASE_URL}/tasks")
        if r.status_code == 200:
            tasks = r.json()
            for task in tasks:
                httpx.delete(f"{BASE_URL}/tasks/{task['id']}")
        
        # Get all lists and delete non-default ones
        r = httpx.get(f"{BASE_URL}/lists")
        if r.status_code == 200:
            lists = r.json()
            for list_obj in lists:
                if list_obj["name"] not in ["Personal", "Work"]:
                    httpx.delete(f"{BASE_URL}/lists/{list_obj['name']}")
    except Exception as e:
        print(f"Warning: Cleanup failed: {e}")

# =====================================================================
# TASK ENDPOINT TESTS
# =====================================================================
class TaskTests:
    @staticmethod
    def test_create_minimal_task():
        """Create a task with only required fields (title)"""
        payload = {"title": "Minimal Task"}
        r = httpx.post(f"{BASE_URL}/tasks", json=payload)
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["title"] == "Minimal Task"
        assert data["list"] == "Personal"  # Default list
        assert data["completed"] is False  # Default value
        assert isinstance(data["id"], str)
        assert isinstance(data["created_at"], str)
        return data["id"]  # Return for use in other tests
    
    @staticmethod
    def test_create_full_task():
        """Create a task with all available fields"""
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat().split(".")[0]
        end_date = (datetime.now() + timedelta(days=30)).date().isoformat()
        
        payload = {
            "title": "Full Task",
            "description": "This is a detailed description",
            "tags": ["important", "work", "project"],
            "due_date": tomorrow,
            "recurrence": "weekly",
            "recurrence_end_date": end_date,
            "list": "Work"
        }
        
        r = httpx.post(f"{BASE_URL}/tasks", json=payload)
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
        data = r.json()
        
        # Check that all fields are present and correct
        assert data["title"] == "Full Task"
        assert data["description"] == "This is a detailed description"
        assert set(data["tags"]) == set(["important", "work", "project"])
        assert data["due_date"].startswith(tomorrow.split("T")[0])
        assert data["recurrence"] == "weekly"
        assert data["recurrence_end_date"] == end_date
        assert data["list"] == "Work"
        assert data["completed"] is False
        assert isinstance(data["id"], str)
        assert isinstance(data["created_at"], str)
        return data["id"]
    
    @staticmethod
    def test_create_task_validation():
        """Test validation rules for task creation"""
        # Missing required field (title)
        r = httpx.post(f"{BASE_URL}/tasks", json={"description": "No title"})
        assert r.status_code == 422, f"Expected 422 for missing title, got {r.status_code}"
        
        # Invalid recurrence value
        r = httpx.post(f"{BASE_URL}/tasks", json={"title": "Invalid Recurrence", "recurrence": "yearly"})
        assert r.status_code == 422, f"Expected 422 for invalid recurrence, got {r.status_code}"
        
        # Non-existent list
        r = httpx.post(f"{BASE_URL}/tasks", json={"title": "Invalid List", "list": "NonExistent"})
        assert r.status_code == 400, f"Expected 400 for non-existent list, got {r.status_code}"
    
    @staticmethod
    def test_get_task_by_id():
        """Test retrieving a task by ID"""
        # First create a task
        task_id = TaskTests.test_create_minimal_task()
        
        # Get the task by ID
        r = httpx.get(f"{BASE_URL}/tasks/{task_id}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["id"] == task_id
        assert data["title"] == "Minimal Task"
        
        # Test non-existent task ID
        r = httpx.get(f"{BASE_URL}/tasks/{uuid.uuid4()}")
        assert r.status_code == 404, f"Expected 404 for non-existent task, got {r.status_code}"
    
    @staticmethod
    def test_update_task():
        """Test updating a task"""
        # First create a task
        task_id = TaskTests.test_create_minimal_task()
        
        # Update title and description
        update_payload = {
            "title": "Updated Title",
            "description": "New description"
        }
        r = httpx.put(f"{BASE_URL}/tasks/{task_id}", json=update_payload)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "New description"
        
        # Update completion status
        update_payload = {"completed": True}
        r = httpx.put(f"{BASE_URL}/tasks/{task_id}", json=update_payload)
        assert r.status_code == 200
        assert r.json()["completed"] is True
        
        # Try to update to a non-existent list
        update_payload = {"list": "NonExistent"}
        r = httpx.put(f"{BASE_URL}/tasks/{task_id}", json=update_payload)
        assert r.status_code == 400, f"Expected 400 for non-existent list, got {r.status_code}"
        
        # Try to update non-existent task
        r = httpx.put(f"{BASE_URL}/tasks/{uuid.uuid4()}", json={"title": "Won't Work"})
        assert r.status_code == 404, f"Expected 404 for non-existent task, got {r.status_code}"
    
    @staticmethod
    def test_delete_task():
        """Test deleting a task"""
        # First create a task
        task_id = TaskTests.test_create_minimal_task()
        
        # Delete the task
        r = httpx.delete(f"{BASE_URL}/tasks/{task_id}")
        assert r.status_code == 204, f"Expected 204, got {r.status_code}"
        
        # Verify it's gone
        r = httpx.get(f"{BASE_URL}/tasks/{task_id}")
        assert r.status_code == 404, f"Expected 404 after deletion, got {r.status_code}"
        
        # Try to delete it again
        r = httpx.delete(f"{BASE_URL}/tasks/{task_id}")
        assert r.status_code == 404, f"Expected 404 for already deleted task, got {r.status_code}"
    
    @staticmethod
    def test_list_tasks_no_filters():
        """Test listing all tasks without filters"""
        # Create a few tasks
        httpx.post(f"{BASE_URL}/tasks", json={"title": "Task One"})
        httpx.post(f"{BASE_URL}/tasks", json={"title": "Task Two"})
        
        # List all tasks
        r = httpx.get(f"{BASE_URL}/tasks")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert all("id" in task for task in data)
        assert all("title" in task for task in data)
    
    @staticmethod
    def test_filter_tasks_by_completion():
        """Test filtering tasks by completion status"""
        # Create completed and non-completed tasks
        r1 = httpx.post(f"{BASE_URL}/tasks", json={"title": "Completed Task"})
        completed_id = r1.json()["id"]
        httpx.put(f"{BASE_URL}/tasks/{completed_id}", json={"completed": True})
        
        httpx.post(f"{BASE_URL}/tasks", json={"title": "Not Completed Task"})
        
        # Get only completed tasks
        r = httpx.get(f"{BASE_URL}/tasks", params={"completed": "true"})
        assert r.status_code == 200
        data = r.json()
        assert all(task["completed"] is True for task in data)
        assert any(task["title"] == "Completed Task" for task in data)
        
        # Get only non-completed tasks
        r = httpx.get(f"{BASE_URL}/tasks", params={"completed": "false"})
        assert r.status_code == 200
        data = r.json()
        assert all(task["completed"] is False for task in data)
        assert any(task["title"] == "Not Completed Task" for task in data)
    
    @staticmethod
    def test_filter_tasks_by_list():
        """Test filtering tasks by list"""
        # Create tasks in different lists
        httpx.post(f"{BASE_URL}/tasks", json={"title": "Personal Task", "list": "Personal"})
        httpx.post(f"{BASE_URL}/tasks", json={"title": "Work Task", "list": "Work"})
        
        # Filter by Personal list
        r = httpx.get(f"{BASE_URL}/tasks", params={"list": "Personal"})
        assert r.status_code == 200
        data = r.json()
        assert all(task["list"] == "Personal" for task in data)
        assert any(task["title"] == "Personal Task" for task in data)
        
        # Filter by Work list
        r = httpx.get(f"{BASE_URL}/tasks", params={"list": "Work"})
        assert r.status_code == 200
        data = r.json()
        assert all(task["list"] == "Work" for task in data)
        assert any(task["title"] == "Work Task" for task in data)
    
    @staticmethod
    def test_filter_tasks_by_tags():
        """Test filtering tasks by tags"""
        # Create tasks with different tags
        httpx.post(f"{BASE_URL}/tasks", json={"title": "Project Task", "tags": ["project", "important"]})
        httpx.post(f"{BASE_URL}/tasks", json={"title": "Meeting Task", "tags": ["meeting", "important"]})
        httpx.post(f"{BASE_URL}/tasks", json={"title": "No Tags Task"})
        
        # Filter by single tag
        r = httpx.get(f"{BASE_URL}/tasks", params={"tags": "project"})
        assert r.status_code == 200
        data = r.json()
        assert all("project" in task["tags"] for task in data if "tags" in task and task["tags"])
        assert any(task["title"] == "Project Task" for task in data)
        assert not any(task["title"] == "Meeting Task" for task in data)
        
        # Filter by multiple tags (should return tasks with any of these tags)
        r = httpx.get(f"{BASE_URL}/tasks", params={"tags": "project,meeting"})
        assert r.status_code == 200
        data = r.json()
        titles = [task["title"] for task in data]
        assert "Project Task" in titles
        assert "Meeting Task" in titles
        assert "No Tags Task" not in titles
        
        # Test with whitespace in tag parameter
        r = httpx.get(f"{BASE_URL}/tasks", params={"tags": "project, important"})
        assert r.status_code == 200
        data = r.json()
        assert any(task["title"] == "Project Task" for task in data)
    
    @staticmethod
    def test_combined_filters():
        """Test combining multiple filter parameters"""
        # Create tasks with different combinations of properties
        httpx.post(f"{BASE_URL}/tasks", json={
            "title": "Important Work Meeting",
            "tags": ["meeting", "important"],
            "list": "Work"
        })
        
        r1 = httpx.post(f"{BASE_URL}/tasks", json={
            "title": "Completed Personal Task",
            "tags": ["important"],
            "list": "Personal"
        })
        completed_id = r1.json()["id"]
        httpx.put(f"{BASE_URL}/tasks/{completed_id}", json={"completed": True})
        
        # Filter by list AND tag
        r = httpx.get(f"{BASE_URL}/tasks", params={"list": "Work", "tags": "meeting"})
        assert r.status_code == 200
        data = r.json()
        assert all(task["list"] == "Work" and "meeting" in task["tags"] for task in data)
        assert any(task["title"] == "Important Work Meeting" for task in data)
        
        # Filter by list AND completion status
        r = httpx.get(f"{BASE_URL}/tasks", params={"list": "Personal", "completed": "true"})
        assert r.status_code == 200
        data = r.json()
        assert all(task["list"] == "Personal" and task["completed"] is True for task in data)
        assert any(task["title"] == "Completed Personal Task" for task in data)
        
        # Filter by tag AND completion status
        r = httpx.get(f"{BASE_URL}/tasks", params={"tags": "important", "completed": "true"})
        assert r.status_code == 200
        data = r.json()
        assert all("important" in task["tags"] and task["completed"] is True for task in data)
        
        # All three filters combined
        r = httpx.get(f"{BASE_URL}/tasks", params={
            "list": "Personal", 
            "tags": "important", 
            "completed": "true"
        })
        assert r.status_code == 200
        data = r.json()
        assert all(
            task["list"] == "Personal" and
            "important" in task["tags"] and
            task["completed"] is True
            for task in data
        )
        assert any(task["title"] == "Completed Personal Task" for task in data)
    
    @staticmethod
    def test_recurrence_fields():
        """Test creating and retrieving tasks with recurrence fields"""
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat().split(".")[0]
        end_date = (datetime.now() + timedelta(days=30)).date().isoformat()
        
        # Test all recurrence types
        recurrence_types = ["daily", "weekly", "monthly"]
        for rec_type in recurrence_types:
            payload = {
                "title": f"{rec_type.capitalize()} Recurring Task",
                "recurrence": rec_type,
                "recurrence_end_date": end_date,
                "due_date": tomorrow
            }
            
            r = httpx.post(f"{BASE_URL}/tasks", json=payload)
            assert r.status_code == 201, f"Expected 201 for {rec_type} recurrence, got {r.status_code}: {r.text}"
            data = r.json()
            assert data["recurrence"] == rec_type
            assert data["recurrence_end_date"] == end_date
            assert data["due_date"].startswith(tomorrow.split("T")[0])
            
            # Verify it can be retrieved
            task_id = data["id"]
            r = httpx.get(f"{BASE_URL}/tasks/{task_id}")
            assert r.status_code == 200
            data = r.json()
            assert data["recurrence"] == rec_type
            assert data["recurrence_end_date"] == end_date
    
    @staticmethod
    def test_update_recurrence_fields():
        """Test updating recurrence fields of a task"""
        # First create a non-recurring task
        r = httpx.post(f"{BASE_URL}/tasks", json={"title": "Regular Task"})
        assert r.status_code == 201
        task_id = r.json()["id"]
        
        # 1. Add recurrence to an existing task
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat().split(".")[0]
        end_date = (datetime.now() + timedelta(days=30)).date().isoformat()
        
        update_payload = {
            "recurrence": "weekly",
            "recurrence_end_date": end_date,
            "due_date": tomorrow
        }
        
        r = httpx.put(f"{BASE_URL}/tasks/{task_id}", json=update_payload)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["recurrence"] == "weekly"
        assert data["recurrence_end_date"] == end_date
        
        # 2. Change recurrence type
        update_payload = {"recurrence": "monthly"}
        r = httpx.put(f"{BASE_URL}/tasks/{task_id}", json=update_payload)
        assert r.status_code == 200
        data = r.json()
        assert data["recurrence"] == "monthly"
        assert data["recurrence_end_date"] == end_date  # Should remain unchanged
        
        # 3. Remove recurrence end date
        update_payload = {"recurrence_end_date": None}
        r = httpx.put(f"{BASE_URL}/tasks/{task_id}", json=update_payload)
        assert r.status_code == 200
        data = r.json()
        assert data["recurrence"] == "monthly"  # Still has recurrence type
        assert data["recurrence_end_date"] is None  # End date was removed
        
        # 4. Add back recurrence end date
        new_end_date = (datetime.now() + timedelta(days=60)).date().isoformat()
        update_payload = {"recurrence_end_date": new_end_date}
        r = httpx.put(f"{BASE_URL}/tasks/{task_id}", json=update_payload)
        assert r.status_code == 200
        data = r.json()
        assert data["recurrence_end_date"] == new_end_date
        
        # 5. Remove recurrence completely
        update_payload = {"recurrence": None}
        r = httpx.put(f"{BASE_URL}/tasks/{task_id}", json=update_payload)
        assert r.status_code == 200
        data = r.json()
        assert data["recurrence"] is None
        # End date might still be there, that's implementation-dependent

# =====================================================================
# LIST ENDPOINT TESTS
# =====================================================================
class ListTests:
    @staticmethod
    def test_get_default_lists():
        """Test retrieving default lists"""
        r = httpx.get(f"{BASE_URL}/lists")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert isinstance(data, list)
        # Check expected format
        assert all(isinstance(list_obj, dict) and "name" in list_obj for list_obj in data)
        # Check default lists
        list_names = [list_obj["name"] for list_obj in data]
        assert "Personal" in list_names, f"Missing Personal in lists: {list_names}"
        assert "Work" in list_names, f"Missing Work in lists: {list_names}"
    
    @staticmethod
    def test_create_list():
        """Test creating a new list"""
        # Create a new list
        r = httpx.post(f"{BASE_URL}/lists", json={"name": "Study"})
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["name"] == "Study"
        
        # Verify it exists
        r = httpx.get(f"{BASE_URL}/lists")
        list_names = [list_obj["name"] for list_obj in r.json()]
        assert "Study" in list_names, f"Newly created list not found in lists: {list_names}"
    
    @staticmethod
    def test_create_list_validation():
        """Test validation rules for list creation"""
        # Try to create a list with an empty name
        r = httpx.post(f"{BASE_URL}/lists", json={"name": ""})
        assert r.status_code == 400, f"Expected 400 for empty list name, got {r.status_code}"
        
        # Try to create a list with just whitespace
        r = httpx.post(f"{BASE_URL}/lists", json={"name": "  "})
        assert r.status_code == 400, f"Expected 400 for whitespace list name, got {r.status_code}"
        
        # Try to create a duplicate list
        httpx.post(f"{BASE_URL}/lists", json={"name": "Unique"})
        r = httpx.post(f"{BASE_URL}/lists", json={"name": "Unique"})
        assert r.status_code == 400, f"Expected 400 for duplicate list name, got {r.status_code}"
    
    @staticmethod
    def test_delete_list():
        """Test deleting a list"""
        # Create a list to delete
        httpx.post(f"{BASE_URL}/lists", json={"name": "ToDelete"})
        
        # Delete the list
        r = httpx.delete(f"{BASE_URL}/lists/ToDelete")
        assert r.status_code == 204, f"Expected 204, got {r.status_code}"
        
        # Verify it's gone
        r = httpx.get(f"{BASE_URL}/lists")
        list_names = [list_obj["name"] for list_obj in r.json()]
        assert "ToDelete" not in list_names, f"List was not deleted: {list_names}"
        
        # Try to delete it again
        r = httpx.delete(f"{BASE_URL}/lists/ToDelete")
        assert r.status_code == 404, f"Expected 404 for already deleted list, got {r.status_code}"
    
    @staticmethod
    def test_delete_list_restrictions():
        """Test restrictions on list deletion"""
        # Try to delete Personal (not allowed)
        r = httpx.delete(f"{BASE_URL}/lists/Personal")
        assert r.status_code == 400, f"Expected 400 for attempting to delete Personal, got {r.status_code}"
        
        # Create a list and add a task to it
        httpx.post(f"{BASE_URL}/lists", json={"name": "ListWithTask"})
        httpx.post(f"{BASE_URL}/tasks", json={"title": "Task in list", "list": "ListWithTask"})
        
        # Try to delete the list with a task (should fail)
        r = httpx.delete(f"{BASE_URL}/lists/ListWithTask")
        assert r.status_code == 400, f"Expected 400 for list with tasks, got {r.status_code}"
        
        # Delete the task
        r = httpx.get(f"{BASE_URL}/tasks", params={"list": "ListWithTask"})
        task_id = r.json()[0]["id"]
        httpx.delete(f"{BASE_URL}/tasks/{task_id}")
        
        # Now should be able to delete the list
        r = httpx.delete(f"{BASE_URL}/lists/ListWithTask")
        assert r.status_code == 204, f"Expected 204 after removing tasks, got {r.status_code}"

# =====================================================================
# CORS & API CONSISTENCY TESTS
# =====================================================================
class GeneralTests:
    @staticmethod
    def test_cors_headers():
        """Test CORS headers for cross-origin requests"""
        headers = {
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "POST"
        }
        r = httpx.options(f"{BASE_URL}/tasks", headers=headers)
        assert "access-control-allow-origin" in r.headers.keys(), "CORS headers missing"
        assert r.headers.get("access-control-allow-origin") == "*", "CORS origin should be '*'"
    
    @staticmethod
    def test_api_interface_consistency():
        """Test API interface consistency"""
        # Create a task with all fields and verify the response structure
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat().split(".")[0]
        end_date = (datetime.now() + timedelta(days=30)).date().isoformat()
        
        payload = {
            "title": "API Interface Test",
            "description": "Testing interface consistency",
            "tags": ["test", "api"],
            "due_date": tomorrow,
            "recurrence": "weekly",
            "recurrence_end_date": end_date,
            "list": "Personal"
        }
        
        r = httpx.post(f"{BASE_URL}/tasks", json=payload)
        assert r.status_code == 201
        data = r.json()
        
        # Check all required fields are present
        required_fields = [
            "id", "title", "description", "tags", "completed",
            "due_date", "recurrence", "recurrence_end_date",
            "list", "created_at"
        ]
        for field in required_fields:
            assert field in data, f"Missing field {field} in response"
        
        # Check the field types
        assert isinstance(data["id"], str)
        assert isinstance(data["title"], str)
        assert isinstance(data["description"], str)
        assert isinstance(data["tags"], list)
        assert isinstance(data["completed"], bool)
        assert isinstance(data["due_date"], str)
        assert data["recurrence"] in ["daily", "weekly", "monthly", None]
        assert isinstance(data["recurrence_end_date"], str) or data["recurrence_end_date"] is None
        assert isinstance(data["list"], str)
        assert isinstance(data["created_at"], str)

def summary():
    print("\n📋 Test Summary:")
    
    # Calculate tests by category
    categories = {}
    for group, name, passed, _ in results:
        if group not in categories:
            categories[group] = {"passed": 0, "failed": 0, "total": 0, "tests": []}
        
        categories[group]["total"] += 1
        if passed:
            categories[group]["passed"] += 1
        else:
            categories[group]["failed"] += 1
        
        categories[group]["tests"].append((name, passed))
    
    # Print summary by category with headings
    for category, stats in categories.items():
        pass_pct = int((stats["passed"] / stats["total"]) * 100) if stats["total"] > 0 else 0
        
        if category == "Tasks":
            print("\n== /tasks Endpoint Tests ==")
        elif category == "Lists":
            print("\n== /lists Endpoint Tests ==")
        elif category == "General":
            print("\n== General API Tests ==")
            
        print(f"{category}: {stats['passed']}/{stats['total']} passed ({pass_pct}%)")
        
        # Print individual test results within category
        for name, passed in stats["tests"]:
            status = "✅" if passed else "❌"
            print(f"  {status} {name}")
    
    # Overall summary
    total_passed = sum(1 for g, n, s, m in results if s is True)
    total_failed = sum(1 for g, n, s, m in results if s is False)
    total = total_passed + total_failed
    pass_pct = int((total_passed / total) * 100) if total > 0 else 0
    
    print(f"\n== Overall Results ==")
    print(f"Total: {total_passed}/{total} tests passed ({pass_pct}%)")
    
    if total_failed > 0:
        print("\n== Failed Tests ==")
        for group, name, passed, message in results:
            if not passed:
                print(f"  - {group}: {name}\n    {message}")

if __name__ == "__main__":
    print("🔧 Running To-Do API Test Suite...\n")
    
    # First clean up any existing data
    cleanup()
    
    print("\n== Running /tasks Endpoint Tests ==")
    # Task Endpoint Tests
    run_test("Tasks", "Create minimal task", TaskTests.test_create_minimal_task)
    run_test("Tasks", "Create fully-populated task", TaskTests.test_create_full_task)
    run_test("Tasks", "Create task validation", TaskTests.test_create_task_validation)
    run_test("Tasks", "Get task by ID", TaskTests.test_get_task_by_id)
    run_test("Tasks", "Update task", TaskTests.test_update_task)
    run_test("Tasks", "Delete task", TaskTests.test_delete_task)
    run_test("Tasks", "List tasks (no filters)", TaskTests.test_list_tasks_no_filters)
    run_test("Tasks", "Filter tasks by completion", TaskTests.test_filter_tasks_by_completion)
    run_test("Tasks", "Filter tasks by list", TaskTests.test_filter_tasks_by_list)
    run_test("Tasks", "Filter tasks by tags", TaskTests.test_filter_tasks_by_tags)
    run_test("Tasks", "Combined filters", TaskTests.test_combined_filters)
    run_test("Tasks", "Recurrence fields", TaskTests.test_recurrence_fields)
    run_test("Tasks", "Update recurrence fields", TaskTests.test_update_recurrence_fields)
    
    print("\n== Running /lists Endpoint Tests ==")
    # List Endpoint Tests
    run_test("Lists", "Get default lists", ListTests.test_get_default_lists)
    run_test("Lists", "Create list", ListTests.test_create_list)
    run_test("Lists", "Create list validation", ListTests.test_create_list_validation)
    run_test("Lists", "Delete list", ListTests.test_delete_list)
    run_test("Lists", "Delete list restrictions", ListTests.test_delete_list_restrictions)
    
    print("\n== Running General API Tests ==")
    # General API Tests
    # run_test("General", "CORS headers", GeneralTests.test_cors_headers)
    run_test("General", "API interface consistency", GeneralTests.test_api_interface_consistency)
    
    # Print summary
    summary()
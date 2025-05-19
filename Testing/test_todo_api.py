import httpx
import json
import uuid

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

# --- Task CRUD & Filtering ---

def test_create_tasks():
    global task_id_1, task_id_2, task_id_3
    payloads = [
        {"title": "Task in Personal", "tags": ["alpha"], "list": "Personal"},
        {"title": "Task in Work", "tags": ["beta"], "list": "Work"},
        {"title": "Task in Projects", "tags": ["gamma"], "list": "Projects"}
    ]
    # Creating in an unknown list auto-creates the list
    resp = [httpx.post(f"{BASE_URL}/tasks", json=p) for p in payloads]
    for i, r in enumerate(resp):
        assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    task_id_1 = resp[0].json()["id"]
    task_id_2 = resp[1].json()["id"]
    task_id_3 = resp[2].json()["id"]

def test_list_tasks_by_list():
    # Filter by default list
    r = httpx.get(f"{BASE_URL}/tasks", params={"list": "Personal"})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert any(task["title"] == "Task in Personal" for task in data), "Expected task in Personal list"

    # Filter by new custom list
    r2 = httpx.get(f"{BASE_URL}/tasks", params={"list": "Projects"})
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}: {r2.text}"
    data2 = r2.json()
    assert any(task["title"] == "Task in Projects" for task in data2), "Expected task in Projects list"

def test_get_all_lists():
    r = httpx.get(f"{BASE_URL}/lists")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    # At least Personal, Work, Projects
    for l in ["Personal", "Work", "Projects"]:
        assert l in data, f"Missing {l} in lists: {data}"

def test_rename_list():
    # Rename Projects to "SideQuests"
    r = httpx.put(f"{BASE_URL}/lists/Projects", params={"new_name": "SideQuests"})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json() == "SideQuests"
    # Verify list name changed in /lists
    r2 = httpx.get(f"{BASE_URL}/lists")
    assert "SideQuests" in r2.json()
    assert "Projects" not in r2.json()
    # Verify all tasks moved
    r3 = httpx.get(f"{BASE_URL}/tasks", params={"list": "SideQuests"})
    assert any(task["title"] == "Task in Projects" for task in r3.json()), "Task not found in renamed list"

def test_delete_list():
    # Delete the SideQuests list (and associated tasks)
    r = httpx.delete(f"{BASE_URL}/lists/SideQuests")
    assert r.status_code == 204, f"Expected 204, got {r.status_code}: {r.text}"
    # It should be gone from /lists
    r2 = httpx.get(f"{BASE_URL}/lists")
    assert "SideQuests" not in r2.json(), f"List still present after delete"
    # No tasks in deleted list
    r3 = httpx.get(f"{BASE_URL}/tasks", params={"list": "SideQuests"})
    assert r3.json() == [], f"Tasks still present in deleted list"
    # Try deleting again (should 404)
    r4 = httpx.delete(f"{BASE_URL}/lists/SideQuests")
    assert r4.status_code == 404, f"Expected 404 when deleting non-existent list, got {r4.status_code}"

def test_delete_task_and_404():
    # Delete a specific task
    r = httpx.delete(f"{BASE_URL}/tasks/{task_id_2}")
    assert r.status_code == 204, f"Expected 204, got {r.status_code}: {r.text}"
    # Try fetching it back
    r2 = httpx.get(f"{BASE_URL}/tasks/{task_id_2}")
    assert r2.status_code == 404, f"Expected 404 after deleting task, got {r2.status_code}"

def test_update_and_retrieve_task():
    # Mark a task as completed
    r = httpx.put(f"{BASE_URL}/tasks/{task_id_1}", json={"completed": True})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json()["completed"] is True
    # Confirm in GET
    r2 = httpx.get(f"{BASE_URL}/tasks/{task_id_1}")
    assert r2.json()["completed"] is True

def test_tag_filtering():
    r = httpx.get(f"{BASE_URL}/tasks", params={"tags": "alpha"})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert any("alpha" in t["tags"] for t in r.json()), "No tasks with alpha tag"

def test_recurrence_fields():
    payload = {
        "title": "Recurring thing",
        "recurrence": "weekly",
        "recurrence_end_date": "2025-12-31",
    }
    r = httpx.post(f"{BASE_URL}/tasks", json=payload)
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    tid = r.json()["id"]
    r2 = httpx.get(f"{BASE_URL}/tasks/{tid}")
    task = r2.json()
    assert task["recurrence"] == "weekly"
    assert task["recurrence_end_date"] == "2025-12-31"

def test_list_and_filter_completed():
    # List only completed
    r = httpx.get(f"{BASE_URL}/tasks", params={"completed": True})
    for task in r.json():
        assert task["completed"] is True
    # List only not completed
    r2 = httpx.get(f"{BASE_URL}/tasks", params={"completed": False})
    for task in r2.json():
        assert task["completed"] is False

def summary():
    print("\n📋 Test Summary:")
    passed = sum(1 for g, n, s, m in results if s is True)
    failed = sum(1 for g, n, s, m in results if s is False)
    print(f"✅ {passed} passed, ❌ {failed} failed")

if __name__ == "__main__":
    print("🔧 Running To-Do API tests...\n")
    run_test("Tasks", "Create tasks in lists", test_create_tasks)
    run_test("Tasks", "List tasks by list", test_list_tasks_by_list)
    run_test("Lists", "Get all lists", test_get_all_lists)
    run_test("Lists", "Rename list", test_rename_list)
    run_test("Lists", "Delete list", test_delete_list)
    run_test("Tasks", "Delete single task, check 404", test_delete_task_and_404)
    run_test("Tasks", "Update and retrieve task", test_update_and_retrieve_task)
    run_test("Tasks", "Filter by tag", test_tag_filtering)
    run_test("Tasks", "Check recurrence fields", test_recurrence_fields)
    run_test("Tasks", "List and filter completed status", test_list_and_filter_completed)
    summary()

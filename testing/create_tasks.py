from openai import OpenAI
from dotenv import load_dotenv
import os, json
import httpx
from typing import List
import time

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

API_BASE = os.getenv("TODO_API_BASE_URL", "http://localhost:8000")

def generate_task_ideas(keywords: List[str], num_tasks: int, list_name: str = None) -> List[dict]:
    prompt = (
        f"Generate {num_tasks} realistic to-do tasks related to: {', '.join(keywords)}.\n"
        "Each task should be in JSON format like:\n"
        "{\n"
        "  \"title\": string,\n"
        "  \"description\": string,\n"
        "  \"tags\": [string],\n"
        "  \"list\": string,  // List name (default: 'Personal')\n"
        "  \"recurrence\": string|null,  // allowed values: 'daily', 'weekly', 'monthly', or null\n"
        "  \"recurrence_end_date\": string|null (ISO 8601),\n"
        "  \"due_date\": string|null (ISO 8601)\n"
        "}\n"
        f"Use the list name: '{list_name if list_name else 'Personal'}' for all tasks.\n"
        "Return a JSON array of task objects, not code blocks or explanations."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{ "role": "user", "content": prompt }],
        temperature=0.7
    )

    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("⚠️ Failed to parse JSON from LLM.")
        print(content)
        return []

def post_tasks_to_api(tasks: List[dict]):
    start_time = time.time()
    with httpx.Client() as client:
        success = 0
        for i, task in enumerate(tasks):
            res = client.post(f"{API_BASE}/tasks", json=task)
            if res.status_code == 201:
                print(f"✅ Task {i+1}: {task['title']}")
                success += 1
            else:
                print(f"❌ Task {i+1} failed: {res.status_code} {res.text}")
        elapsed_time = time.time() - start_time
        print(f"\n📊 {success}/{len(tasks)} tasks posted successfully in {elapsed_time:.2f} seconds.")

def get_all_lists():
    """Fetch all available lists from the API"""
    with httpx.Client() as client:
        res = client.get(f"{API_BASE}/lists")
        if res.status_code == 200:
            return res.json()
        else:
            print(f"❌ Failed to get lists: {res.status_code}")
            return []

def create_list(name: str):
    """Create a new list with the given name"""
    with httpx.Client() as client:
        res = client.post(f"{API_BASE}/lists", json={"name": name})
        if res.status_code == 201:
            print(f"✅ Created list: {name}")
            return True
        else:
            print(f"❌ Failed to create list: {res.status_code} {res.text}")
            return False

def delete_list(name: str):
    """Delete a list with the given name"""
    with httpx.Client() as client:
        res = client.delete(f"{API_BASE}/lists/{name}")
        if res.status_code == 204:
            print(f"✅ Deleted list: {name}")
            return True
        else:
            print(f"❌ Failed to delete list: {res.status_code} {res.text}")
            return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", help="Comma-separated keywords")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", help="List name to use for tasks")
    parser.add_argument("--create-list", help="Create a new list with given name")
    parser.add_argument("--delete-list", help="Delete a list with given name")
    parser.add_argument("--show-lists", action="store_true", help="Show all available lists")

    args = parser.parse_args()

    # Handle list management
    if args.show_lists:
        lists = get_all_lists()
        print("📋 Available lists:")
        for list_obj in lists:
            print(f" - {list_obj['name']}")
        exit(0)
    
    if args.create_list:
        if create_list(args.create_list):
            print("✅ List created successfully")
        exit(0)
    
    if args.delete_list:
        if delete_list(args.delete_list):
            print("✅ List deleted successfully")
        exit(0)

    # Ensure keywords are provided for task generation
    if not args.keywords:
        parser.error("--keywords are required for task generation")

    keywords = [k.strip() for k in args.keywords.split(",")]
    count = args.count
    list_name = args.list

    # Validate list existence
    if list_name and not args.dry_run:
        lists = get_all_lists()
        list_names = [list_obj['name'] for list_obj in lists]
        if list_name not in list_names:
            print(f"⚠️ List '{list_name}' doesn't exist. Creating it now...")
            if not create_list(list_name):
                print("❌ Failed to create list. Tasks will use default list.")
                list_name = None

    # Start timing total execution
    total_start_time = time.time()
    print(f"🧠 Generating {count} tasks for: {keywords}...")
    tasks = generate_task_ideas(keywords, count, list_name)

    if not tasks:
        print("❌ No tasks generated.")
    elif args.dry_run:
        print("📋 Tasks (dry run):")
        print(json.dumps(tasks, indent=2))
        total_elapsed = time.time() - total_start_time
        print(f"\n⏱️ Total execution time: {total_elapsed:.2f} seconds")
    else:
        post_tasks_to_api(tasks)
        total_elapsed = time.time() - total_start_time
        print(f"⏱️ Total execution time: {total_elapsed:.2f} seconds")

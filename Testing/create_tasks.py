from openai import OpenAI
from dotenv import load_dotenv
import os, json
import httpx
from typing import List

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

API_BASE = os.getenv("TODO_API_BASE_URL", "http://localhost:8000")

def generate_task_ideas(keywords: List[str], num_tasks: int) -> List[dict]:
    prompt = (
        f"Generate {num_tasks} realistic to-do tasks related to: {', '.join(keywords)}.\n"
        "Each task should be in JSON format like:\n"
        "{\n"
        "  \"title\": string,\n"
        "  \"description\": string,\n"
        "  \"tags\": [string],\n"
        "  \"recurrence\": string|null,  // allowed values: 'daily', 'weekly', 'monthly', or null\n"
        "  \"recurrence_end_date\": string|null (ISO 8601),\n"
        "  \"due_date\": string|null (ISO 8601)\n"
        "}\n"
        "Return a JSON array of task objects, not code blocks or explanations."
    )


    response = client.chat.completions.create(
        model="gpt-4.1-nano",
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
    with httpx.Client() as client:
        success = 0
        for i, task in enumerate(tasks):
            res = client.post(f"{API_BASE}/tasks", json=task)
            if res.status_code == 201:
                print(f"✅ Task {i+1}: {task['title']}")
                success += 1
            else:
                print(f"❌ Task {i+1} failed: {res.status_code} {res.text}")
        print(f"\n📊 {success}/{len(tasks)} tasks posted successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", required=True, help="Comma-separated keywords")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    keywords = [k.strip() for k in args.keywords.split(",")]
    count = args.count

    print(f"🧠 Generating {count} tasks for: {keywords}...")
    tasks = generate_task_ideas(keywords, count)

    if not tasks:
        print("❌ No tasks generated.")
    elif args.dry_run:
        print("📋 Tasks (dry run):")
        print(json.dumps(tasks, indent=2))
    else:
        post_tasks_to_api(tasks)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from enum import Enum

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENUM for recurrence
class Recurrence(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"

# BASE models
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = ""
    tags: List[str] = []
    due_date: Optional[datetime] = None
    recurrence: Optional[Recurrence] = None
    recurrence_end_date: Optional[date] = None
    list: Optional[str] = "Personal"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    completed: Optional[bool] = None
    due_date: Optional[datetime] = None
    recurrence: Optional[Recurrence] = None
    recurrence_end_date: Optional[date] = None
    list: Optional[str] = None

class TaskOut(TaskBase):
    id: str
    completed: bool
    created_at: datetime

class ListCreate(BaseModel):
    name: str

class ListOut(BaseModel):
    name: str

# --- TASK ENDPOINTS ---

@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: TaskCreate):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.get("/tasks", response_model=List[TaskOut])
def list_tasks(
    completed: Optional[bool] = None,
    tags: Optional[str] = Query(default=None, description="Comma-separated tags"),
    list_name: Optional[str] = Query(default=None, alias="list", description="Filter by list name")
):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: str):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: str, update: TaskUpdate):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    raise HTTPException(status_code=501, detail="Not implemented")

# --- LIST ENDPOINTS ---

@app.get("/lists", response_model=List[ListOut])
def get_lists():
    raise HTTPException(status_code=501, detail="Not implemented")

@app.post("/lists", response_model=ListOut, status_code=201)
def create_list(list_data: ListCreate):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.delete("/lists/{name}", status_code=204)
def delete_list(name: str):
    raise HTTPException(status_code=501, detail="Not implemented")

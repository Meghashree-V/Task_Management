from fastapi import APIRouter, HTTPException, Query
from models import Task, TaskCreate, TaskUpdate, PriorityEnum, StatusEnum
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import os
from google.cloud import pubsub_v1
import json
import logging

router = APIRouter()

tasks = {}

@router.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate):
    task_id = str(uuid4())
    now = datetime.utcnow()
    new_task = Task(
        id=task_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=StatusEnum.pending,
        created_at=now
    )
    tasks[task_id] = new_task

    # Pub/Sub publishing logic
    project_id = os.environ.get("GCP_PROJECT_ID")
    topic_id = os.environ.get("PUBSUB_TOPIC")
    if project_id and topic_id:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_id)
        event = {
            "event_type": "task.created",
            "task_id": task_id,
            "timestamp": now.isoformat(),
            "data": {
                "title": task.title,
                "description": task.description,
                "priority": task.priority.value
            }
        }
        try:
            future = publisher.publish(topic_path, json.dumps(event).encode("utf-8"))
            message_id = future.result()
            logging.info(f"Published task.created event to {topic_path} with message_id={message_id}")
        except Exception as e:
            logging.error(f"Failed to publish task.created event to Pub/Sub: {e}")

    return new_task

@router.get("/tasks", response_model=List[Task])
def list_tasks(priority: Optional[PriorityEnum] = Query(None), status: Optional[StatusEnum] = Query(None)):
    result = list(tasks.values())
    if priority:
        result = [t for t in result if t.priority == priority]
    if status:
        result = [t for t in result if t.status == status]
    return result

@router.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, task_update: TaskUpdate):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updated_task = task.copy(update={"status": task_update.status})
    tasks[task_id] = updated_task
    return updated_task

@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    return None

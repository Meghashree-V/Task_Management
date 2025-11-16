from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class StatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: PriorityEnum

class TaskUpdate(BaseModel):
    status: StatusEnum

class Task(BaseModel):
    id: str
    title: str
    description: str
    priority: PriorityEnum
    status: StatusEnum
    created_at: datetime

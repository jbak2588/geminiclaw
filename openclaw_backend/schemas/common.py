from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class ProjectCreate(BaseModel):
    name: str
    description: str = ''


class TaskCreate(BaseModel):
    title: str
    instruction: str
    project_id: Optional[str] = None
    team_id: Optional[str] = None
    source: str = 'dashboard'


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern='^(approved|rejected)$')
    actor: str
    comment: str = ''


class ChannelMessageCreate(BaseModel):
    channel: str
    sender: str
    message: str
    create_task: bool = False

from __future__ import annotations

import asyncio
from fastapi import APIRouter, HTTPException

from core.in_memory_store import store
from schemas.common import TaskCreate
from api.websockets import broadcaster, run_task_workflow

router = APIRouter()


@router.get('')
def list_tasks():
    return {'tasks': store.list_tasks()}


@router.get('/{task_id}')
def get_task(task_id: str):
    if task_id not in store.tasks:
        raise HTTPException(status_code=404, detail='Task not found')
    return store.get_task(task_id)


@router.post('')
async def create_task(payload: TaskCreate):
    project_id = payload.project_id or next(iter(store.projects.keys()))
    task = store.create_task(
        title=payload.title,
        instruction=payload.instruction,
        project_id=project_id,
        team_id=payload.team_id,
        source=payload.source,
    )
    await broadcaster.broadcast_json(
        {
            'type': 'task_event',
            'task_id': task['id'],
            'task_title': task['title'],
            'node': 'control',
            'status': 'queued',
            'message': 'Task accepted by Company OS.',
        }
    )
    asyncio.create_task(run_task_workflow(task['id']))
    return {'task_id': task['id'], 'status': 'queued'}

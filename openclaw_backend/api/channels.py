from __future__ import annotations

import asyncio
from fastapi import APIRouter

from core.in_memory_store import store
from schemas.common import ChannelMessageCreate
from api.websockets import broadcaster, run_task_workflow

router = APIRouter()


@router.get('/messages')
def list_messages():
    return {'messages': store.list_channel_messages()}


@router.post('/messages')
async def create_message(payload: ChannelMessageCreate):
    item = store.create_channel_message(payload.channel, payload.sender, payload.message)
    await broadcaster.broadcast_json(
        {
            'type': 'channel_event',
            'channel': payload.channel,
            'message': payload.message,
            'sender': payload.sender,
        }
    )

    created_task_id = None
    if payload.create_task:
        project_id = next(iter(store.projects.keys()))
        default_team_id = next(iter(store.teams.keys()))
        task = store.create_task(
            title=f'Channel request from {payload.channel}',
            instruction=payload.message,
            project_id=project_id,
            team_id=default_team_id,
            source=f'channel:{payload.channel}',
        )
        created_task_id = task['id']
        asyncio.create_task(run_task_workflow(task['id']))

    return {'message': item, 'created_task_id': created_task_id}

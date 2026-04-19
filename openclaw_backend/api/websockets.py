from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.in_memory_store import store

router = APIRouter()


class Broadcaster:
    def __init__(self) -> None:
        self.connections: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        self.connections.pop(client_id, None)

    async def send_json(self, client_id: str, payload: dict[str, Any]) -> None:
        ws = self.connections.get(client_id)
        if ws:
            await ws.send_text(json.dumps(payload))

    async def broadcast_json(self, payload: dict[str, Any]) -> None:
        disconnected: list[str] = []
        for client_id, ws in self.connections.items():
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                disconnected.append(client_id)
        for client_id in disconnected:
            self.disconnect(client_id)


broadcaster = Broadcaster()
active_workflow_tasks: set[str] = set()


def build_nodes(task: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    team = store.get_team(task.get('team_id'))
    config = (team or {}).get('config') or [{'name': 'control'}, {'name': 'pm'}, {'name': 'planning'}, {'name': 'reviewer'}]
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for index, item in enumerate(config):
        node_name = item['name']
        nodes.append(
            {
                'id': node_name,
                'label': node_name.capitalize(),
                'role': node_name,
                'status': 'pending',
            }
        )
        if index > 0:
            edges.append({'from': config[index - 1]['name'], 'to': node_name})
    return nodes, edges


async def push_graph(task: dict[str, Any], nodes: list[dict[str, Any]], edges: list[dict[str, Any]], active_node: str) -> None:
    await broadcaster.broadcast_json(
        {
            'type': 'node_update',
            'task_id': task['id'],
            'task_title': task['title'],
            'nodes': nodes,
            'edges': edges,
            'active_node': active_node,
        }
    )


async def push_event(task: dict[str, Any], node: str, status: str, message: str) -> None:
    store.update_task(task['id'], status=status, latest_node=node)
    store.append_log(task['id'], f'[{node}] {status}: {message}')
    await broadcaster.broadcast_json(
        {
            'type': 'task_event',
            'task_id': task['id'],
            'task_title': task['title'],
            'node': node,
            'status': status,
            'message': message,
        }
    )
    await broadcaster.broadcast_json(
        {
            'type': 'log_append',
            'task_id': task['id'],
            'line': f'[{node}] {status}: {message}',
        }
    )
    from channels.telegram_bot import notify_telegram_task_event
    await notify_telegram_task_event(task=task, node=node, status=status, message=message)


def is_workflow_active(task_id: str) -> bool:
    return task_id in active_workflow_tasks


async def resume_task_from_approval_resolution(approval: dict[str, Any]) -> bool:
    """
    Recovery fallback:
    if backend restarted while waiting on approval, there may be no live workflow coroutine.
    In that case, continue/finish the reviewer step from the approval decision.
    """
    task_id = approval.get('task_id')
    if not task_id:
        return False
    if is_workflow_active(task_id):
        return False

    task = store.tasks.get(task_id)
    if not task:
        return False
    if task.get('status') in {'completed', 'rejected'}:
        return False

    node = approval.get('node') or task.get('latest_node') or 'reviewer'
    decision_status = approval.get('status')
    if decision_status == 'rejected':
        await push_event(task, node, 'rejected', 'Workflow stopped because approval was rejected.')
        store.update_task(task_id, status='rejected', latest_node=node)
        return True

    if decision_status == 'approved':
        await push_event(task, node, 'approved', 'Approval received. Resuming workflow.')
        await asyncio.sleep(1)
        await push_event(task, node, 'completed', f'{str(node).capitalize()} node completed.')
        store.update_task(task_id, status='completed', latest_node=node)
        await broadcaster.broadcast_json(
            {
                'type': 'task_event',
                'task_id': task_id,
                'task_title': task['title'],
                'node': 'system',
                'status': 'completed',
                'message': 'Workflow Completed.',
            }
        )
        return True

    return False


def _needs_approval(task: dict[str, Any]) -> bool:
    prompt = task['instruction'].lower()
    keywords = ['deploy', 'publish', 'payment', 'delete', 'send outside', 'contract', 'approval']
    return any(word in prompt for word in keywords)


async def run_task_workflow(task_id: str) -> None:
    if is_workflow_active(task_id):
        return
    active_workflow_tasks.add(task_id)
    try:
        task = store.get_task(task_id)
        nodes, edges = build_nodes(task)
        node_index = {node['id']: i for i, node in enumerate(nodes)}

        async def mark_node(node_name: str, status: str) -> None:
            if node_name in node_index:
                nodes[node_index[node_name]]['status'] = status
            await push_graph(task, nodes, edges, node_name)

        team = store.get_team(task.get('team_id'))
        sequence = [item['name'] for item in (team or {}).get('config', [])] or ['control', 'pm', 'planning', 'reviewer']

        await mark_node(sequence[0], 'running')
        await push_event(task, sequence[0], 'running', 'Task received and interpreted by control agent.')
        await asyncio.sleep(1)

        for idx, node in enumerate(sequence):
            await mark_node(node, 'running')
            if node == 'control':
                await push_event(task, node, 'running', 'Routing task to the correct department team.')
            elif node == 'pm':
                await push_event(task, node, 'running', 'Breaking instruction into structured work steps.')
            elif node == 'planning':
                await push_event(task, node, 'running', 'Preparing planning document and execution approach.')
            elif node == 'developer':
                await push_event(task, node, 'running', 'Producing implementation or technical execution output.')
            elif node == 'marketing':
                await push_event(task, node, 'running', 'Drafting campaign, copy, and delivery assets.')
            elif node == 'operations':
                await push_event(task, node, 'running', 'Checking channel, field, and operational follow-up items.')
            elif node == 'reviewer':
                await push_event(task, node, 'running', 'Reviewing output quality and risk before release.')
            else:
                await push_event(task, node, 'running', f'Processing node: {node}')
            await asyncio.sleep(1)

            requires_final_approval = node == 'reviewer' and _needs_approval(task)
            if requires_final_approval:
                approval = store.create_approval(
                    task_id=task['id'],
                    task_title=task['title'],
                    node=node,
                    title='Final human approval required',
                    message='This task includes a risky or external action. Please approve or reject.',
                )
                await broadcaster.broadcast_json({**approval, 'type': 'approval_request'})
                from channels.telegram_bot import notify_telegram_approval_request
                await notify_telegram_approval_request(task=task, approval=approval)
                await mark_node(node, 'pending')
                decision = await store.wait_for_approval(approval['approval_id'])
                if decision['status'] == 'rejected':
                    await mark_node(node, 'error')
                    await push_event(task, node, 'rejected', 'Workflow stopped because approval was rejected.')
                    store.update_task(task['id'], status='rejected')
                    return
                await mark_node(node, 'running')
                await push_event(task, node, 'approved', 'Approval received. Resuming workflow.')
                await asyncio.sleep(1)

            await mark_node(node, 'completed')
            await push_event(task, node, 'completed', f'{node.capitalize()} node completed.')

            if idx + 1 < len(sequence):
                await mark_node(sequence[idx + 1], 'pending')

        store.update_task(task['id'], status='completed', latest_node=sequence[-1])
        await broadcaster.broadcast_json(
            {
                'type': 'task_event',
                'task_id': task['id'],
                'task_title': task['title'],
                'node': 'system',
                'status': 'completed',
                'message': 'Workflow Completed.',
            }
        )
    finally:
        active_workflow_tasks.discard(task_id)


@router.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await broadcaster.connect(client_id, websocket)
    try:
        await websocket.send_text(json.dumps({'type': 'connected', 'client_id': client_id}))
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            if payload.get('type') == 'ping':
                await broadcaster.send_json(client_id, {'type': 'pong'})
    except WebSocketDisconnect:
        broadcaster.disconnect(client_id)

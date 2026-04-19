from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from core.config import settings


class InMemoryStore:
    def __init__(self) -> None:
        self.projects: dict[str, dict[str, Any]] = {}
        self.teams: dict[str, dict[str, Any]] = {}
        self.tasks: dict[str, dict[str, Any]] = {}
        self.approvals: dict[str, dict[str, Any]] = {}
        self.channels: list[dict[str, Any]] = []
        self.knowledge_docs: list[dict[str, Any]] = []
        self.log_buffers: dict[str, list[str]] = {}
        self.pending_gates: dict[str, asyncio.Event] = {}
        self.seed_defaults()

    def now(self) -> str:
        return datetime.utcnow().isoformat()

    def seed_defaults(self) -> None:
        if self.projects:
            return
        project_id = str(uuid.uuid4())
        self.projects[project_id] = {
            'id': project_id,
            'name': 'Default Company Workspace',
            'description': 'Initial workspace for Company OS',
            'created_at': self.now(),
        }

        for name, description, config in [
            (
                'Core Product Team',
                'Control + planning + development + review',
                [
                    {'name': 'control'},
                    {'name': 'pm'},
                    {'name': 'planning'},
                    {'name': 'developer'},
                    {'name': 'reviewer'},
                ],
            ),
            (
                'Operations Team',
                'Control + operations + review',
                [
                    {'name': 'control'},
                    {'name': 'pm'},
                    {'name': 'operations'},
                    {'name': 'reviewer'},
                ],
            ),
            (
                'Marketing Team',
                'Control + planning + marketing + review',
                [
                    {'name': 'control'},
                    {'name': 'pm'},
                    {'name': 'planning'},
                    {'name': 'marketing'},
                    {'name': 'reviewer'},
                ],
            ),
        ]:
            team_id = str(uuid.uuid4())
            self.teams[team_id] = {
                'id': team_id,
                'name': name,
                'description': description,
                'config': config,
                'created_at': self.now(),
            }

    def create_project(self, name: str, description: str) -> dict[str, Any]:
        project_id = str(uuid.uuid4())
        project = {
            'id': project_id,
            'name': name,
            'description': description,
            'created_at': self.now(),
        }
        self.projects[project_id] = project
        return project

    def list_projects(self) -> list[dict[str, Any]]:
        return list(self.projects.values())

    def list_teams(self) -> list[dict[str, Any]]:
        return list(self.teams.values())

    def get_team(self, team_id: str | None) -> dict[str, Any] | None:
        if not team_id:
            return next(iter(self.teams.values()), None)
        return self.teams.get(team_id)

    def create_task(self, title: str, instruction: str, project_id: str, team_id: str | None, source: str) -> dict[str, Any]:
        task_id = str(uuid.uuid4())
        task = {
            'id': task_id,
            'title': title,
            'instruction': instruction,
            'project_id': project_id,
            'team_id': team_id,
            'source': source,
            'status': 'queued',
            'created_at': self.now(),
            'updated_at': self.now(),
            'latest_node': '',
        }
        self.tasks[task_id] = task
        self.log_buffers[task_id] = [f'[{self.now()}] Task created: {title}']
        self._write_task_log(task_id, self.log_buffers[task_id][0])
        return task

    def update_task(self, task_id: str, **updates: Any) -> dict[str, Any]:
        task = self.tasks[task_id]
        task.update(updates)
        task['updated_at'] = self.now()
        return task

    def list_tasks(self) -> list[dict[str, Any]]:
        return list(self.tasks.values())

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self.tasks[task_id]

    def create_approval(self, task_id: str, task_title: str, node: str, title: str, message: str) -> dict[str, Any]:
        approval_id = str(uuid.uuid4())
        approval = {
            'approval_id': approval_id,
            'task_id': task_id,
            'task_title': task_title,
            'node': node,
            'title': title,
            'message': message,
            'status': 'pending',
            'created_at': self.now(),
        }
        self.approvals[approval_id] = approval
        self.pending_gates[approval_id] = asyncio.Event()
        self.append_log(task_id, f'Approval requested: {title}')
        return approval

    def resolve_approval(self, approval_id: str, decision: str, actor: str, comment: str = '') -> dict[str, Any]:
        approval = self.approvals[approval_id]
        approval['status'] = decision
        approval['actor'] = actor
        approval['comment'] = comment
        approval['resolved_at'] = self.now()
        gate = self.pending_gates.get(approval_id)
        if gate:
            gate.set()
        self.append_log(approval['task_id'], f'Approval {decision} by {actor}')
        return approval

    async def wait_for_approval(self, approval_id: str) -> dict[str, Any]:
        gate = self.pending_gates[approval_id]
        await gate.wait()
        return self.approvals[approval_id]

    def list_approvals(self) -> list[dict[str, Any]]:
        return list(self.approvals.values())

    def append_log(self, task_id: str, line: str) -> None:
        stamped = f'[{self.now()}] {line}'
        self.log_buffers.setdefault(task_id, []).append(stamped)
        self._write_task_log(task_id, stamped)

    def get_log_content(self, task_id: str) -> str:
        return '\n'.join(self.log_buffers.get(task_id, []))

    def list_log_files(self) -> list[dict[str, Any]]:
        log_dir = Path(settings.log_dir)
        files: list[dict[str, Any]] = []
        for path in sorted(log_dir.glob('task_*.txt'), key=lambda p: p.stat().st_mtime, reverse=True):
            stat = path.stat()
            files.append(
                {
                    'filename': path.name,
                    'size_bytes': str(stat.st_size),
                    'modified_at': str(stat.st_mtime),
                }
            )
        return files

    def read_log_file(self, filename: str) -> str:
        path = Path(settings.log_dir) / filename
        return path.read_text(encoding='utf-8')

    def create_channel_message(self, channel: str, sender: str, message: str) -> dict[str, Any]:
        item = {
            'id': str(uuid.uuid4()),
            'channel': channel,
            'sender': sender,
            'message': message,
            'created_at': self.now(),
        }
        self.channels.insert(0, item)
        return item

    def list_channel_messages(self) -> list[dict[str, Any]]:
        return self.channels[:100]

    def create_knowledge_doc(self, project_id: str, title: str, filename: str, summary: str) -> dict[str, Any]:
        item = {
            'id': str(uuid.uuid4()),
            'project_id': project_id,
            'title': title,
            'filename': filename,
            'summary': summary,
            'uploaded_at': self.now(),
        }
        self.knowledge_docs.insert(0, item)
        return item

    def list_knowledge_docs(self, project_id: str | None = None) -> list[dict[str, Any]]:
        if project_id is None:
            return self.knowledge_docs
        return [doc for doc in self.knowledge_docs if doc['project_id'] == project_id]

    def dashboard_overview(self) -> dict[str, int]:
        return {
            'projects_count': len(self.projects),
            'tasks_count': len(self.tasks),
            'pending_approvals': sum(1 for item in self.approvals.values() if item['status'] == 'pending'),
            'knowledge_count': len(self.knowledge_docs),
            'channel_messages': len(self.channels),
        }

    def _write_task_log(self, task_id: str, line: str) -> None:
        path = Path(settings.log_dir) / f'task_{task_id}.txt'
        with path.open('a', encoding='utf-8') as fp:
            fp.write(line + '\n')


store = InMemoryStore()

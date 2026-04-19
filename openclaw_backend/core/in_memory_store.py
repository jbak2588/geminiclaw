from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from core.config import settings


class InMemoryStore:
    """Phase-1 store backed by SQLite while keeping legacy in-memory contracts."""

    def __init__(self) -> None:
        self.projects: dict[str, dict[str, Any]] = {}
        self.teams: dict[str, dict[str, Any]] = {}
        self.tasks: dict[str, dict[str, Any]] = {}
        self.approvals: dict[str, dict[str, Any]] = {}
        self.channels: list[dict[str, Any]] = []
        self.channel_outbound_audits: list[dict[str, Any]] = []
        self.knowledge_docs: list[dict[str, Any]] = []
        self.log_buffers: dict[str, list[str]] = {}
        self.pending_gates: dict[str, asyncio.Event] = {}

        self._lock = threading.RLock()
        self._conn = sqlite3.connect(settings.state_db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        self._ensure_schema()
        self.seed_defaults()
        self._load_cache()
        self._rebuild_pending_gates()

    def now(self) -> str:
        return datetime.utcnow().isoformat()

    def _ensure_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS teams (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    instruction TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    team_id TEXT,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    latest_node TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    task_title TEXT NOT NULL,
                    node TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    actor TEXT,
                    comment TEXT,
                    resolved_at TEXT
                );

                CREATE TABLE IF NOT EXISTS channels (
                    id TEXT PRIMARY KEY,
                    channel TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS channel_outbound_audits (
                    id TEXT PRIMARY KEY,
                    channel TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    task_id TEXT,
                    approval_id TEXT,
                    event_type TEXT NOT NULL,
                    message_preview TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    delivery_status TEXT NOT NULL,
                    error_text TEXT
                );

                CREATE TABLE IF NOT EXISTS knowledge_docs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
                CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
                CREATE INDEX IF NOT EXISTS idx_approvals_task_id ON approvals(task_id);
                CREATE INDEX IF NOT EXISTS idx_channel_outbound_sent_at ON channel_outbound_audits(sent_at);
                """
            )
            self._conn.commit()

    def _load_cache(self) -> None:
        with self._lock:
            self.projects = {}
            for row in self._conn.execute(
                'SELECT id, name, description, created_at FROM projects ORDER BY created_at ASC'
            ).fetchall():
                self.projects[row['id']] = {
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'created_at': row['created_at'],
                }

            self.teams = {}
            for row in self._conn.execute(
                'SELECT id, name, description, config_json, created_at FROM teams ORDER BY created_at ASC'
            ).fetchall():
                try:
                    config = json.loads(row['config_json']) if row['config_json'] else []
                except json.JSONDecodeError:
                    config = []
                self.teams[row['id']] = {
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'config': config,
                    'created_at': row['created_at'],
                }

            self.tasks = {}
            for row in self._conn.execute(
                """
                SELECT id, title, instruction, project_id, team_id, source, status, created_at, updated_at, latest_node
                FROM tasks
                ORDER BY created_at ASC
                """
            ).fetchall():
                self.tasks[row['id']] = {
                    'id': row['id'],
                    'title': row['title'],
                    'instruction': row['instruction'],
                    'project_id': row['project_id'],
                    'team_id': row['team_id'],
                    'source': row['source'],
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'latest_node': row['latest_node'],
                }

            self.approvals = {}
            for row in self._conn.execute(
                """
                SELECT approval_id, task_id, task_title, node, title, message, status, created_at, actor, comment, resolved_at
                FROM approvals
                ORDER BY created_at ASC
                """
            ).fetchall():
                approval = {
                    'approval_id': row['approval_id'],
                    'task_id': row['task_id'],
                    'task_title': row['task_title'],
                    'node': row['node'],
                    'title': row['title'],
                    'message': row['message'],
                    'status': row['status'],
                    'created_at': row['created_at'],
                }
                if row['actor'] is not None:
                    approval['actor'] = row['actor']
                if row['comment'] is not None:
                    approval['comment'] = row['comment']
                if row['resolved_at'] is not None:
                    approval['resolved_at'] = row['resolved_at']
                self.approvals[row['approval_id']] = approval

            self.channels = []
            for row in self._conn.execute(
                'SELECT id, channel, sender, message, created_at FROM channels ORDER BY created_at DESC'
            ).fetchall():
                self.channels.append(
                    {
                        'id': row['id'],
                        'channel': row['channel'],
                        'sender': row['sender'],
                        'message': row['message'],
                        'created_at': row['created_at'],
                    }
                )

            self.channel_outbound_audits = []
            for row in self._conn.execute(
                """
                SELECT id, channel, direction, recipient, task_id, approval_id, event_type, message_preview, sent_at, delivery_status, error_text
                FROM channel_outbound_audits
                ORDER BY sent_at DESC
                """
            ).fetchall():
                item = {
                    'id': row['id'],
                    'channel': row['channel'],
                    'direction': row['direction'],
                    'recipient': row['recipient'],
                    'event_type': row['event_type'],
                    'message_preview': row['message_preview'],
                    'sent_at': row['sent_at'],
                    'delivery_status': row['delivery_status'],
                }
                if row['task_id'] is not None:
                    item['task_id'] = row['task_id']
                if row['approval_id'] is not None:
                    item['approval_id'] = row['approval_id']
                if row['error_text'] is not None:
                    item['error_text'] = row['error_text']
                self.channel_outbound_audits.append(item)

            self.knowledge_docs = []
            for row in self._conn.execute(
                'SELECT id, project_id, title, filename, summary, uploaded_at FROM knowledge_docs ORDER BY uploaded_at DESC'
            ).fetchall():
                self.knowledge_docs.append(
                    {
                        'id': row['id'],
                        'project_id': row['project_id'],
                        'title': row['title'],
                        'filename': row['filename'],
                        'summary': row['summary'],
                        'uploaded_at': row['uploaded_at'],
                    }
                )

    def _rebuild_pending_gates(self) -> None:
        self.pending_gates = {}
        for approval in self.approvals.values():
            if approval['status'] == 'pending':
                self.pending_gates[approval['approval_id']] = asyncio.Event()

    def seed_defaults(self) -> None:
        with self._lock:
            row = self._conn.execute('SELECT COUNT(*) AS count FROM projects').fetchone()
            if row and int(row['count']) > 0:
                return

            created_at = self.now()
            project_id = str(uuid.uuid4())
            self._conn.execute(
                'INSERT INTO projects (id, name, description, created_at) VALUES (?, ?, ?, ?)',
                (project_id, 'Default Company Workspace', 'Initial workspace for Company OS', created_at),
            )

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
                self._conn.execute(
                    'INSERT INTO teams (id, name, description, config_json, created_at) VALUES (?, ?, ?, ?, ?)',
                    (team_id, name, description, json.dumps(config), created_at),
                )

            self._conn.commit()

    def create_project(self, name: str, description: str) -> dict[str, Any]:
        project_id = str(uuid.uuid4())
        project = {
            'id': project_id,
            'name': name,
            'description': description,
            'created_at': self.now(),
        }
        with self._lock:
            self._conn.execute(
                'INSERT INTO projects (id, name, description, created_at) VALUES (?, ?, ?, ?)',
                (project['id'], project['name'], project['description'], project['created_at']),
            )
            self._conn.commit()
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
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO tasks (id, title, instruction, project_id, team_id, source, status, created_at, updated_at, latest_node)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task['id'],
                    task['title'],
                    task['instruction'],
                    task['project_id'],
                    task['team_id'],
                    task['source'],
                    task['status'],
                    task['created_at'],
                    task['updated_at'],
                    task['latest_node'],
                ),
            )
            self._conn.commit()

        self.tasks[task_id] = task
        self.log_buffers[task_id] = [f'[{self.now()}] Task created: {title}']
        self._write_task_log(task_id, self.log_buffers[task_id][0])
        return task

    def update_task(self, task_id: str, **updates: Any) -> dict[str, Any]:
        if task_id not in self.tasks:
            raise KeyError(task_id)

        allowed_fields = {'title', 'instruction', 'project_id', 'team_id', 'source', 'status', 'latest_node'}
        filtered_updates = {key: value for key, value in updates.items() if key in allowed_fields}

        updated_at = self.now()
        set_fragments = [f'{key} = ?' for key in filtered_updates]
        values = list(filtered_updates.values())
        set_fragments.append('updated_at = ?')
        values.append(updated_at)
        values.append(task_id)

        with self._lock:
            self._conn.execute(
                f'UPDATE tasks SET {", ".join(set_fragments)} WHERE id = ?',
                values,
            )
            self._conn.commit()

        task = self.tasks[task_id]
        task.update(filtered_updates)
        task['updated_at'] = updated_at
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
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO approvals (approval_id, task_id, task_title, node, title, message, status, created_at, actor, comment, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval['approval_id'],
                    approval['task_id'],
                    approval['task_title'],
                    approval['node'],
                    approval['title'],
                    approval['message'],
                    approval['status'],
                    approval['created_at'],
                    None,
                    None,
                    None,
                ),
            )
            self._conn.commit()

        self.approvals[approval_id] = approval
        self.pending_gates[approval_id] = asyncio.Event()
        self.append_log(task_id, f'Approval requested: {title}')
        return approval

    def resolve_approval(self, approval_id: str, decision: str, actor: str, comment: str = '') -> dict[str, Any]:
        approval = self.approvals[approval_id]
        resolved_at = self.now()
        with self._lock:
            self._conn.execute(
                'UPDATE approvals SET status = ?, actor = ?, comment = ?, resolved_at = ? WHERE approval_id = ?',
                (decision, actor, comment, resolved_at, approval_id),
            )
            self._conn.commit()

        approval['status'] = decision
        approval['actor'] = actor
        approval['comment'] = comment
        approval['resolved_at'] = resolved_at

        gate = self.pending_gates.get(approval_id)
        if gate and not gate.is_set():
            gate.set()

        self.append_log(approval['task_id'], f'Approval {decision} by {actor}')
        return approval

    async def wait_for_approval(self, approval_id: str) -> dict[str, Any]:
        approval = self.approvals[approval_id]
        if approval['status'] != 'pending':
            return approval

        gate = self.pending_gates.get(approval_id)
        if gate is None:
            gate = asyncio.Event()
            self.pending_gates[approval_id] = gate
        await gate.wait()
        return self.approvals[approval_id]

    def list_approvals(self) -> list[dict[str, Any]]:
        return list(self.approvals.values())

    def append_log(self, task_id: str, line: str) -> None:
        stamped = f'[{self.now()}] {line}'
        self.log_buffers.setdefault(task_id, []).append(stamped)
        self._write_task_log(task_id, stamped)

    def get_log_content(self, task_id: str) -> str:
        buffered = self.log_buffers.get(task_id)
        if buffered:
            return '\n'.join(buffered)

        path = Path(settings.log_dir) / f'task_{task_id}.txt'
        if not path.exists():
            return ''
        return path.read_text(encoding='utf-8').rstrip('\n')

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
        with self._lock:
            self._conn.execute(
                'INSERT INTO channels (id, channel, sender, message, created_at) VALUES (?, ?, ?, ?, ?)',
                (item['id'], item['channel'], item['sender'], item['message'], item['created_at']),
            )
            self._conn.commit()
        self.channels.insert(0, item)
        return item

    def list_channel_messages(self) -> list[dict[str, Any]]:
        return self.channels[:100]

    def create_channel_outbound_audit(
        self,
        channel: str,
        recipient: str,
        event_type: str,
        message_preview: str,
        delivery_status: str,
        direction: str = 'outbound',
        task_id: str | None = None,
        approval_id: str | None = None,
        error_text: str | None = None,
    ) -> dict[str, Any]:
        preview = message_preview.replace('\r', ' ').strip()
        if len(preview) > 500:
            preview = preview[:497] + '...'

        item = {
            'id': str(uuid.uuid4()),
            'channel': channel,
            'direction': direction,
            'recipient': recipient,
            'event_type': event_type,
            'message_preview': preview,
            'sent_at': self.now(),
            'delivery_status': delivery_status,
        }
        if task_id:
            item['task_id'] = task_id
        if approval_id:
            item['approval_id'] = approval_id
        if error_text:
            item['error_text'] = error_text[:500]

        with self._lock:
            self._conn.execute(
                """
                INSERT INTO channel_outbound_audits (
                    id, channel, direction, recipient, task_id, approval_id, event_type, message_preview, sent_at, delivery_status, error_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item['id'],
                    item['channel'],
                    item['direction'],
                    item['recipient'],
                    item.get('task_id'),
                    item.get('approval_id'),
                    item['event_type'],
                    item['message_preview'],
                    item['sent_at'],
                    item['delivery_status'],
                    item.get('error_text'),
                ),
            )
            self._conn.commit()
        self.channel_outbound_audits.insert(0, item)
        return item

    def list_channel_outbound_audits(self, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))
        return self.channel_outbound_audits[:safe_limit]

    def create_knowledge_doc(self, project_id: str, title: str, filename: str, summary: str) -> dict[str, Any]:
        item = {
            'id': str(uuid.uuid4()),
            'project_id': project_id,
            'title': title,
            'filename': filename,
            'summary': summary,
            'uploaded_at': self.now(),
        }
        with self._lock:
            self._conn.execute(
                'INSERT INTO knowledge_docs (id, project_id, title, filename, summary, uploaded_at) VALUES (?, ?, ?, ?, ?, ?)',
                (
                    item['id'],
                    item['project_id'],
                    item['title'],
                    item['filename'],
                    item['summary'],
                    item['uploaded_at'],
                ),
            )
            self._conn.commit()
        self.knowledge_docs.insert(0, item)
        return item

    def list_knowledge_docs(self, project_id: str | None = None) -> list[dict[str, Any]]:
        if project_id is None:
            return self.knowledge_docs
        return [doc for doc in self.knowledge_docs if doc['project_id'] == project_id]

    def dashboard_overview(self) -> dict[str, int]:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM projects) AS projects_count,
                    (SELECT COUNT(*) FROM tasks) AS tasks_count,
                    (SELECT COUNT(*) FROM approvals WHERE status = 'pending') AS pending_approvals,
                    (SELECT COUNT(*) FROM knowledge_docs) AS knowledge_count,
                    (SELECT COUNT(*) FROM channels) AS channel_messages
                """
            ).fetchone()

        return {
            'projects_count': int(row['projects_count']),
            'tasks_count': int(row['tasks_count']),
            'pending_approvals': int(row['pending_approvals']),
            'knowledge_count': int(row['knowledge_count']),
            'channel_messages': int(row['channel_messages']),
        }

    def _write_task_log(self, task_id: str, line: str) -> None:
        path = Path(settings.log_dir) / f'task_{task_id}.txt'
        with path.open('a', encoding='utf-8') as fp:
            fp.write(line + '\n')


store = InMemoryStore()

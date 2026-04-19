"""Telegram bot integration for phase-1 task dispatch and status feedback."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional


logger = logging.getLogger(__name__)

_Application = None


def _get_telegram() -> bool:
    """Lazily import python-telegram-bot."""
    global _Application
    if _Application is None:
        try:
            from telegram.ext import Application
        except ImportError:
            logger.warning("[Telegram] python-telegram-bot is not installed.")
            return False
        _Application = Application
    return True


def _chat_id_from_source(source: str | None) -> int | None:
    if not source or not source.startswith("telegram:"):
        return None
    try:
        return int(source.split(":", 1)[1])
    except (TypeError, ValueError):
        return None


async def process_inbound_telegram_text(chat_id: int, sender_name: str, text: str) -> dict[str, Any]:
    """Create channel + task records for a Telegram inbound message and start workflow."""
    from core.in_memory_store import store
    from api.websockets import broadcaster, run_task_workflow

    project_id = next(iter(store.projects.keys()), None)
    team_id = next(iter(store.teams.keys()), None)
    if not project_id or not team_id:
        raise RuntimeError("Backend is not seeded with default project/team.")

    store.create_channel_message(
        channel="telegram",
        sender=f"{sender_name} ({chat_id})",
        message=text,
    )
    await broadcaster.broadcast_json(
        {
            "type": "channel_event",
            "channel": "telegram",
            "message": text,
            "sender": f"{sender_name} ({chat_id})",
        }
    )

    short_text = text.replace("\n", " ").strip()
    if len(short_text) > 60:
        short_text = short_text[:57] + "..."
    title = f"Telegram: {short_text}"
    task = store.create_task(
        title=title,
        instruction=text,
        project_id=project_id,
        team_id=team_id,
        source=f"telegram:{chat_id}",
    )
    await broadcaster.broadcast_json(
        {
            "type": "task_event",
            "task_id": task["id"],
            "task_title": task["title"],
            "node": "control",
            "status": "queued",
            "message": "Task accepted by Company OS.",
        }
    )
    asyncio.create_task(run_task_workflow(task["id"]))
    return task


class TelegramBot:
    """Telegram bot that converts inbound text into backend tasks."""

    def __init__(self, token: str):
        self.token = token
        self.app = None
        self._running = False

    async def start(self) -> None:
        if not _get_telegram():
            logger.error("[Telegram] Cannot start: missing python-telegram-bot dependency.")
            return

        from telegram.ext import CommandHandler, MessageHandler, filters

        self.app = _Application.builder().token(self.token).build()
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("help", self._handle_start))
        self.app.add_handler(CommandHandler("status", self._handle_status))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

        await self.app.initialize()
        await self.app.start()
        if self.app.updater is None:
            logger.error("[Telegram] Updater is unavailable. Bot cannot poll updates.")
            return
        await self.app.updater.start_polling(drop_pending_updates=True)
        self._running = True
        logger.info("[Telegram] Bot started.")

    async def stop(self) -> None:
        if not self.app:
            return
        if self.app.updater:
            await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        self._running = False
        logger.info("[Telegram] Bot stopped.")

    def _record_outbound_audit(
        self,
        *,
        chat_id: int,
        event_type: str,
        text: str,
        delivery_status: str,
        task_id: str | None = None,
        approval_id: str | None = None,
        error_text: str | None = None,
    ) -> None:
        from core.in_memory_store import store

        try:
            store.create_channel_outbound_audit(
                channel='telegram',
                recipient=str(chat_id),
                event_type=event_type,
                message_preview=text,
                delivery_status=delivery_status,
                task_id=task_id,
                approval_id=approval_id,
                error_text=error_text,
            )
        except Exception as exc:
            logger.warning("[Telegram] Failed to persist outbound audit: %s", exc)

    async def send_text(
        self,
        chat_id: int,
        text: str,
        *,
        event_type: str = 'telegram_message',
        task_id: str | None = None,
        approval_id: str | None = None,
    ) -> None:
        if not text.strip():
            return

        if not self.app or not self._running:
            self._record_outbound_audit(
                chat_id=chat_id,
                event_type=event_type,
                text=text,
                delivery_status='failed',
                task_id=task_id,
                approval_id=approval_id,
                error_text='bot_not_running',
            )
            return

        chunks = [text[i : i + 4000] for i in range(0, len(text), 4000)] or [text]
        multi_chunk = len(chunks) > 1
        for idx, chunk in enumerate(chunks):
            chunk_event_type = event_type if not multi_chunk else f'{event_type}.chunk{idx + 1}'
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=chunk)
            except Exception as exc:
                self._record_outbound_audit(
                    chat_id=chat_id,
                    event_type=chunk_event_type,
                    text=chunk,
                    delivery_status='failed',
                    task_id=task_id,
                    approval_id=approval_id,
                    error_text=str(exc),
                )
                raise
            self._record_outbound_audit(
                chat_id=chat_id,
                event_type=chunk_event_type,
                text=chunk,
                delivery_status='sent',
                task_id=task_id,
                approval_id=approval_id,
            )

    async def notify_task_event(self, task: dict[str, Any], node: str, status: str, message: str) -> None:
        chat_id = _chat_id_from_source(task.get("source"))
        if chat_id is None:
            return
        if status not in {"queued", "approved", "rejected", "completed"}:
            return
        text = (
            f"Task update\n"
            f"- Task: {task['title']}\n"
            f"- Task ID: {task['id']}\n"
            f"- Node: {node}\n"
            f"- Status: {status}\n"
            f"- Message: {message}"
        )
        await self.send_text(
            chat_id,
            text,
            event_type=f'task_update.{status}',
            task_id=task['id'],
        )

    async def notify_approval_request(self, task: dict[str, Any], approval: dict[str, Any]) -> None:
        chat_id = _chat_id_from_source(task.get("source"))
        if chat_id is None:
            return
        text = (
            f"Approval required\n"
            f"- Task: {task['title']}\n"
            f"- Task ID: {task['id']}\n"
            f"- Approval ID: {approval['approval_id']}\n"
            f"- Action: approve/reject in Approval Center (desktop UI)"
        )
        await self.send_text(
            chat_id,
            text,
            event_type='approval_request',
            task_id=task['id'],
            approval_id=approval['approval_id'],
        )

    async def notify_approval_resolved(self, approval: dict[str, Any]) -> None:
        from core.in_memory_store import store

        task = store.tasks.get(approval.get("task_id"))
        if not task:
            return
        chat_id = _chat_id_from_source(task.get("source"))
        if chat_id is None:
            return
        text = (
            f"Approval resolved\n"
            f"- Task: {task['title']}\n"
            f"- Approval ID: {approval['approval_id']}\n"
            f"- Decision: {approval['status']}"
        )
        await self.send_text(
            chat_id,
            text,
            event_type='approval_resolved',
            task_id=task['id'],
            approval_id=approval['approval_id'],
        )

    async def _handle_start(self, update, context) -> None:
        if not update.effective_chat:
            return
        await self.send_text(
            update.effective_chat.id,
            "GeminiClaw Telegram channel is active.\n"
            "Send any text to create a task.\n"
            "Commands:\n"
            "/status <task_id> - check task status",
            event_type='command.start',
        )

    async def _handle_status(self, update, context) -> None:
        from core.in_memory_store import store

        if not update.effective_chat:
            return
        chat_id = update.effective_chat.id

        if not context.args:
            await self.send_text(chat_id, "Usage: /status <task_id>", event_type='command.status.usage')
            return

        task_id = context.args[0].strip()
        task = store.tasks.get(task_id)
        if not task:
            await self.send_text(chat_id, "Task not found.", event_type='command.status.not_found')
            return

        expected_source = f"telegram:{chat_id}"
        if task.get("source") != expected_source:
            await self.send_text(chat_id, "Task not found.", event_type='command.status.not_found')
            return

        await self.send_text(
            chat_id,
            f"Task status\n"
            f"- Task ID: {task['id']}\n"
            f"- Title: {task['title']}\n"
            f"- Status: {task['status']}\n"
            f"- Latest node: {task.get('latest_node') or '-'}",
            event_type='command.status.result',
            task_id=task['id'],
        )

    async def _handle_message(self, update, context) -> None:
        if not update.message or not update.message.text:
            return
        if not update.effective_chat:
            return

        text = update.message.text.strip()
        if not text:
            await self.send_text(update.effective_chat.id, "Please send a non-empty message.", event_type='task_create.invalid_text')
            return

        chat_id = update.effective_chat.id
        sender_name = str(chat_id)
        if update.effective_user:
            sender_name = update.effective_user.username or update.effective_user.full_name or str(chat_id)
        try:
            task = await process_inbound_telegram_text(chat_id=chat_id, sender_name=sender_name, text=text)
        except RuntimeError as exc:
            await self.send_text(chat_id, str(exc), event_type='task_create.error')
            return

        await self.send_text(
            chat_id,
            f"Task created.\n"
            f"- Task ID: {task['id']}\n"
            f"- Title: {task['title']}\n"
            f"Status updates will be sent here.",
            event_type='task_create.accepted',
            task_id=task['id'],
        )


_bot_instance: Optional[TelegramBot] = None


def get_telegram_bot() -> Optional[TelegramBot]:
    global _bot_instance
    from core.config import settings

    if not settings.TELEGRAM_BOT_TOKEN:
        return None

    if _bot_instance is None:
        _bot_instance = TelegramBot(settings.TELEGRAM_BOT_TOKEN)
    return _bot_instance


async def notify_telegram_task_event(task: dict[str, Any], node: str, status: str, message: str) -> None:
    bot = get_telegram_bot()
    if not bot:
        return
    try:
        await bot.notify_task_event(task=task, node=node, status=status, message=message)
    except Exception as exc:
        logger.warning("[Telegram] Failed to send task event: %s", exc)


async def notify_telegram_approval_request(task: dict[str, Any], approval: dict[str, Any]) -> None:
    bot = get_telegram_bot()
    if not bot:
        return
    try:
        await bot.notify_approval_request(task=task, approval=approval)
    except Exception as exc:
        logger.warning("[Telegram] Failed to send approval request: %s", exc)


async def notify_telegram_approval_resolved(approval: dict[str, Any]) -> None:
    bot = get_telegram_bot()
    if not bot:
        return
    try:
        await bot.notify_approval_resolved(approval=approval)
    except Exception as exc:
        logger.warning("[Telegram] Failed to send approval resolution: %s", exc)

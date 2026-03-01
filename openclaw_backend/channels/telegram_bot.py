"""
Telegram Bot Channel: Bridges Telegram messages to Pi Agent.
Uses python-telegram-bot v21+ for async Telegram Bot API integration.

Setup:
1. Create a bot via BotFather (https://t.me/BotFather)
2. Set TELEGRAM_BOT_TOKEN in .env
3. Restart the backend — bot auto-starts if token is configured
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy import to avoid ImportError if python-telegram-bot is not installed
_Application = None

def _get_telegram():
    """Lazy import telegram module."""
    global _Application
    if _Application is None:
        try:
            from telegram import Update
            from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
            _Application = Application
            return True
        except ImportError:
            logger.warning("[Telegram] python-telegram-bot not installed. Run: pip install python-telegram-bot")
            return False
    return True


class TelegramBot:
    """Telegram Bot that routes messages to Pi Agent."""
    
    def __init__(self, token: str):
        self.token = token
        self.app = None
        self._running = False
    
    async def start(self):
        """Initialize and start the Telegram bot."""
        if not _get_telegram():
            logger.error("[Telegram] Cannot start — python-telegram-bot not installed")
            return
        
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        
        self.app = Application.builder().token(self.token).build()
        
        # Register handlers
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("compact", self._handle_compact))
        self.app.add_handler(CommandHandler("reset", self._handle_reset))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        
        self._running = True
        logger.info("[Telegram] Bot started successfully")
    
    async def stop(self):
        """Stop the Telegram bot."""
        if self.app and self._running:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            self._running = False
            logger.info("[Telegram] Bot stopped")
    
    async def _handle_start(self, update, context):
        """Handle /start command."""
        await update.message.reply_text(
            "🤖 안녕하세요! GeminiClaw Pi Agent입니다.\n\n"
            "메시지를 보내면 Pi가 응답합니다.\n"
            "명령어:\n"
            "  /compact — 대화 이력 압축\n"
            "  /reset — 세션 초기화"
        )
    
    async def _handle_compact(self, update, context):
        """Handle /compact command — compress session history."""
        from core.memory import memory_store
        from agents.pi_agent import pi_agent_instance
        
        session_id = f"telegram_{update.effective_chat.id}"
        history = memory_store.get_session_history(session_id)
        msg_count = memory_store.get_message_count(session_id)
        
        if msg_count <= 2:
            await update.message.reply_text("📦 세션이 이미 충분히 짧습니다.")
            return
        
        await update.message.reply_text(f"📦 {msg_count}개 메시지를 요약 중...")
        
        summary = pi_agent_instance.compact_history(history)
        saved = memory_store.compact_session(session_id, summary)
        
        await update.message.reply_text(
            f"✅ 세션 압축 완료!\n"
            f"• 삭제된 메시지: {saved}개\n"
            f"• 요약:\n{summary}"
        )
    
    async def _handle_reset(self, update, context):
        """Handle /reset command — clear session."""
        from core.memory import memory_store
        
        session_id = f"telegram_{update.effective_chat.id}"
        memory_store.clear_session(session_id)
        await update.message.reply_text("🔄 세션이 초기화되었습니다.")
    
    async def _handle_message(self, update, context):
        """Handle incoming text messages — route to Pi Agent."""
        from core.memory import memory_store
        from agents.pi_agent import pi_agent_instance
        
        user_message = update.message.text
        if not user_message:
            return
        
        session_id = f"telegram_{update.effective_chat.id}"
        history = memory_store.get_session_history(session_id)
        memory_store.add_message(session_id, "user", user_message)
        
        # Send typing indicator
        await update.message.chat.send_action("typing")
        
        try:
            result = pi_agent_instance.chat(user_message, history, project_id="default")
            reply = result.get("text", "Error: No response")
            
            if result.get("status") == "awaiting_approval":
                reply = f"⚠️ 승인 필요\n{reply}\n\n(WebSocket UI에서 승인해주세요)"
            
            # Save assistant reply
            memory_store.add_message(session_id, "assistant", reply)
            
            # Telegram has a 4096 char limit per message
            if len(reply) > 4000:
                for i in range(0, len(reply), 4000):
                    await update.message.reply_text(reply[i:i+4000])
            else:
                await update.message.reply_text(reply)
                
        except Exception as e:
            logger.error(f"[Telegram] Error processing message: {e}")
            await update.message.reply_text(f"❌ 오류가 발생했습니다: {str(e)[:200]}")


# Singleton instance (created when token is available)
_bot_instance: Optional[TelegramBot] = None

def get_telegram_bot() -> Optional[TelegramBot]:
    """Get or create the Telegram bot singleton."""
    global _bot_instance
    from core.config import settings
    
    if not settings.TELEGRAM_BOT_TOKEN:
        return None
    
    if _bot_instance is None:
        _bot_instance = TelegramBot(settings.TELEGRAM_BOT_TOKEN)
    
    return _bot_instance

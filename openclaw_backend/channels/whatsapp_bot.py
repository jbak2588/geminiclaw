"""
WhatsApp Cloud API Channel: Bridges WhatsApp messages to Pi Agent.
Uses Meta's Cloud API (Webhook + REST) for WhatsApp Business integration.

Setup:
1. Create a Meta Developer App (https://developers.facebook.com/)
2. Add WhatsApp product to the app
3. Set WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN in .env
4. Configure webhook URL: https://your-domain/webhook/whatsapp
5. Subscribe to 'messages' webhook field
"""
import logging
import httpx
from fastapi import APIRouter, Request, Response, Query

logger = logging.getLogger(__name__)

router = APIRouter()

# ─────────────────────────────────────────────
# WhatsApp Cloud API helpers
# ─────────────────────────────────────────────

async def send_whatsapp_message(to: str, text: str, token: str, phone_number_id: str):
    """Send a text message via WhatsApp Cloud API."""
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # WhatsApp has a ~4096 char limit
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)] if len(text) > 4000 else [text]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for chunk in chunks:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"body": chunk}
            }
            try:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"[WhatsApp] Send failed: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"[WhatsApp] Send error: {e}")


# ─────────────────────────────────────────────
# Webhook endpoints
# ─────────────────────────────────────────────

@router.get("/whatsapp")
async def verify_webhook(
    request: Request,
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """
    WhatsApp Webhook verification endpoint.
    Meta sends a GET request to verify the webhook URL.
    """
    from core.config import settings
    
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("[WhatsApp] Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")
    
    logger.warning(f"[WhatsApp] Webhook verification failed: mode={mode}")
    return Response(content="Forbidden", status_code=403)


@router.post("/whatsapp")
async def receive_webhook(request: Request):
    """
    WhatsApp Webhook receiver.
    Processes incoming messages and routes them to Pi Agent.
    """
    from core.config import settings
    from core.memory import memory_store
    from agents.pi_agent import pi_agent_instance
    
    if not settings.WHATSAPP_TOKEN:
        return {"status": "ok"}  # Silently ignore if not configured
    
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok"}
    
    # Extract message from webhook payload
    entry = body.get("entry", [])
    if not entry:
        return {"status": "ok"}
    
    for e in entry:
        changes = e.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            
            for msg in messages:
                msg_type = msg.get("type", "")
                sender = msg.get("from", "")
                
                if msg_type != "text" or not sender:
                    continue
                
                user_message = msg.get("text", {}).get("body", "")
                if not user_message:
                    continue
                
                session_id = f"whatsapp_{sender}"
                
                # Handle /compact command
                if user_message.strip().lower() == "/compact":
                    history = memory_store.get_session_history(session_id)
                    msg_count = memory_store.get_message_count(session_id)
                    
                    if msg_count <= 2:
                        await send_whatsapp_message(
                            sender, "📦 세션이 이미 충분히 짧습니다.",
                            settings.WHATSAPP_TOKEN, settings.WHATSAPP_PHONE_NUMBER_ID
                        )
                        continue
                    
                    summary = pi_agent_instance.compact_history(history)
                    saved = memory_store.compact_session(session_id, summary)
                    
                    await send_whatsapp_message(
                        sender,
                        f"✅ 세션 압축 완료!\n• 삭제: {saved}개\n• 요약:\n{summary}",
                        settings.WHATSAPP_TOKEN, settings.WHATSAPP_PHONE_NUMBER_ID
                    )
                    continue
                
                # Handle /reset command
                if user_message.strip().lower() == "/reset":
                    memory_store.clear_session(session_id)
                    await send_whatsapp_message(
                        sender, "🔄 세션이 초기화되었습니다.",
                        settings.WHATSAPP_TOKEN, settings.WHATSAPP_PHONE_NUMBER_ID
                    )
                    continue
                
                # Normal message → Pi Agent
                history = memory_store.get_session_history(session_id)
                memory_store.add_message(session_id, "user", user_message)
                
                try:
                    result = pi_agent_instance.chat(user_message, history, project_id="default")
                    reply = result.get("text", "Error: No response")
                    
                    if result.get("status") == "awaiting_approval":
                        reply = f"⚠️ 승인 필요\n{reply}\n\n(WebSocket UI에서 승인해주세요)"
                    
                    memory_store.add_message(session_id, "assistant", reply)
                    
                    await send_whatsapp_message(
                        sender, reply,
                        settings.WHATSAPP_TOKEN, settings.WHATSAPP_PHONE_NUMBER_ID
                    )
                    
                except Exception as e:
                    logger.error(f"[WhatsApp] Error processing message: {e}")
                    await send_whatsapp_message(
                        sender, f"❌ 오류: {str(e)[:200]}",
                        settings.WHATSAPP_TOKEN, settings.WHATSAPP_PHONE_NUMBER_ID
                    )
    
    return {"status": "ok"}

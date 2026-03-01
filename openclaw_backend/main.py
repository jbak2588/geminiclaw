import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.websockets import router as ws_router
from api.rest import router as rest_router
from api.knowledge import router as knowledge_router
from api.logs import router as logs_router
from channels.whatsapp_bot import router as whatsapp_router
from core.config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Lifespan: start/stop Telegram bot alongside FastAPI
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown lifecycle."""
    # ── Startup ──
    telegram_bot = None
    if settings.TELEGRAM_BOT_TOKEN:
        try:
            from channels.telegram_bot import get_telegram_bot
            telegram_bot = get_telegram_bot()
            if telegram_bot:
                await telegram_bot.start()
                logger.info("Telegram bot started")
        except Exception as e:
            logger.warning(f"Telegram bot failed to start: {e}")
    else:
        logger.info("Telegram bot disabled (TELEGRAM_BOT_TOKEN not set)")
    
    if settings.WHATSAPP_TOKEN:
        logger.info("WhatsApp webhook enabled")
    else:
        logger.info("WhatsApp webhook disabled (WHATSAPP_TOKEN not set)")
    
    yield  # App runs here
    
    # ── Shutdown ──
    if telegram_bot:
        await telegram_bot.stop()
        logger.info("Telegram bot stopped")


app = FastAPI(
    title="Agentic Team Orchestrator",
    description="Backend engine for the CTO-driven Gemini Agent platform.",
    version="1.1.0",
    lifespan=lifespan
)

# Configure CORS — controlled via ALLOWED_ORIGINS env var
allowed_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ws_router)
app.include_router(rest_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api/projects")
app.include_router(logs_router, prefix="/api/logs")
app.include_router(whatsapp_router, prefix="/webhook")

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "Agentic Team Engine is running.",
        "channels": {
            "telegram": bool(settings.TELEGRAM_BOT_TOKEN),
            "whatsapp": bool(settings.WHATSAPP_TOKEN),
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

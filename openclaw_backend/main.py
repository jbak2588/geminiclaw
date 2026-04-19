from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api.dashboard import router as dashboard_router
from api.projects import router as projects_router
from api.teams import router as teams_router
from api.tasks import router as tasks_router
from api.approvals import router as approvals_router
from api.logs import router as logs_router
from api.channels import router as channels_router
from api.knowledge import router as knowledge_router
from api.websockets import router as ws_router
from channels.telegram_bot import get_telegram_bot


def _configure_console_logging() -> None:
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        )
    else:
        root_logger.setLevel(logging.INFO)
    # Prevent sensitive URL components (e.g., bot token in request URL) from appearing in logs.
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)


_configure_console_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        '[Startup] Booting backend env=%s provider=%s',
        settings.app_env,
        settings.ai_provider,
    )
    logger.info(
        '[Startup] Paths state_db=%s storage=%s logs=%s',
        settings.state_db_path,
        settings.storage_dir,
        settings.log_dir,
    )
    telegram_bot = get_telegram_bot()
    if telegram_bot:
        try:
            logger.info('[Startup] Starting Telegram polling bot...')
            await telegram_bot.start()
            logger.info('[Startup] Telegram polling bot started.')
        except Exception as exc:
            logger.warning("[Telegram] Bot failed to start: %s", exc)
    else:
        logger.info('[Startup] Telegram bot disabled (TELEGRAM_BOT_TOKEN not set).')
    yield
    logger.info('[Shutdown] Stopping backend services...')
    if telegram_bot:
        try:
            await telegram_bot.stop()
        except Exception as exc:
            logger.warning("[Telegram] Bot failed to stop cleanly: %s", exc)
    logger.info('[Shutdown] Backend shutdown complete.')


app = FastAPI(
    title='GeminiClaw Company OS Backend',
    version='0.2.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(ws_router)
app.include_router(dashboard_router, prefix='/api/dashboard', tags=['dashboard'])
app.include_router(projects_router, prefix='/api/projects', tags=['projects'])
app.include_router(teams_router, prefix='/api/teams', tags=['teams'])
app.include_router(tasks_router, prefix='/api/tasks', tags=['tasks'])
app.include_router(approvals_router, prefix='/api/approvals', tags=['approvals'])
app.include_router(logs_router, prefix='/api/logs', tags=['logs'])
app.include_router(channels_router, prefix='/api/channels', tags=['channels'])
app.include_router(knowledge_router, prefix='/api/projects', tags=['knowledge'])


@app.get('/')
def read_root():
    return {
        'status': 'ok',
        'message': 'GeminiClaw Company OS backend is running.',
        'provider': settings.ai_provider,
    }


@app.get('/health')
def health_check():
    return {'status': 'healthy'}


if __name__ == '__main__':
    import uvicorn

    logger.info('[Startup] Launching uvicorn host=0.0.0.0 port=8001 reload=true')
    uvicorn.run('openclaw_backend.main:app', host='0.0.0.0', port=8001, reload=True)

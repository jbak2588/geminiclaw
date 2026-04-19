from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

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

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


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

    uvicorn.run('openclaw_backend.main:app', host='0.0.0.0', port=8001, reload=True)

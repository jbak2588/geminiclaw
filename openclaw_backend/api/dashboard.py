from fastapi import APIRouter

from core.in_memory_store import store

router = APIRouter()


@router.get('/overview')
def get_overview():
    return store.dashboard_overview()


@router.get('/summary')
def get_summary():
    return store.dashboard_overview()

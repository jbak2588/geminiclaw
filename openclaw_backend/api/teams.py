from fastapi import APIRouter

from core.in_memory_store import store

router = APIRouter()


@router.get('')
def list_teams():
    return {'teams': store.list_teams()}

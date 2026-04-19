from fastapi import APIRouter

from core.in_memory_store import store
from schemas.common import ProjectCreate

router = APIRouter()


@router.get('')
def list_projects():
    return {'projects': store.list_projects()}


@router.post('')
def create_project(payload: ProjectCreate):
    project = store.create_project(payload.name, payload.description)
    return project

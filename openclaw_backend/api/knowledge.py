from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException

from core.in_memory_store import store
from core.config import settings

router = APIRouter()


@router.get('/knowledge')
def list_global_knowledge():
    return {'documents': store.list_knowledge_docs()}


@router.get('/{project_id}/knowledge')
def list_project_knowledge(project_id: str):
    return {'documents': store.list_knowledge_docs(project_id)}


@router.post('/{project_id}/knowledge')
async def upload_knowledge(project_id: str, file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail='Empty file')

    knowledge_dir = Path(settings.storage_dir) / 'knowledge' / project_id
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    target = knowledge_dir / file.filename
    target.write_bytes(content)

    summary = f'Uploaded file {file.filename} ({len(content)} bytes). AI summary adapter can be connected here later.'
    doc = store.create_knowledge_doc(
        project_id=project_id,
        title=file.filename,
        filename=file.filename,
        summary=summary,
    )
    return {'status': 'success', 'document': doc}

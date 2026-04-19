from fastapi import APIRouter, HTTPException

from core.in_memory_store import store

router = APIRouter()


@router.get('')
def list_logs():
    return {'logs': store.list_log_files()}


@router.get('/{filename}')
def get_log(filename: str):
    if '..' in filename:
        raise HTTPException(status_code=400, detail='Invalid filename')
    try:
        content = store.read_log_file(filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Log file not found')
    return {'filename': filename, 'content': content}

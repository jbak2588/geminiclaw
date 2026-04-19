from fastapi import APIRouter, HTTPException

from core.in_memory_store import store
from schemas.common import ApprovalDecision
from api.websockets import broadcaster

router = APIRouter()


@router.get('')
def list_approvals():
    return {'approvals': store.list_approvals()}


@router.post('/{approval_id}/decision')
async def decide_approval(approval_id: str, payload: ApprovalDecision):
    if approval_id not in store.approvals:
        raise HTTPException(status_code=404, detail='Approval not found')
    approval = store.resolve_approval(
        approval_id=approval_id,
        decision=payload.decision,
        actor=payload.actor,
        comment=payload.comment,
    )
    await broadcaster.broadcast_json(
        {
            'type': 'approval_resolved',
            'approval_id': approval_id,
            'status': approval['status'],
            'task_id': approval['task_id'],
            'actor': payload.actor,
        }
    )
    return approval

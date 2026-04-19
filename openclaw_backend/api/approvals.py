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
    existing = store.approvals[approval_id]
    if existing.get('status') != 'pending':
        return existing
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
    from channels.telegram_bot import notify_telegram_approval_resolved
    await notify_telegram_approval_resolved(approval)
    from api.websockets import resume_task_from_approval_resolution
    await resume_task_from_approval_resolution(approval)
    return approval

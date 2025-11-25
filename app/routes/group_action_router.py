from fastapi import APIRouter, HTTPException
from app.schemas.group_action_schema import (
    GroupInviteRequest,
    GroupInviteResponse,
    GroupApplyRequest,
    GroupApplyResponse
)
from app.services.group_action_service import (
    invite_user_to_group,
    apply_to_join_group
)

router = APIRouter(prefix="/api/group-action", tags=["Group Actions"])


@router.post("/invite", response_model=GroupInviteResponse)
def invite_user(req: GroupInviteRequest):
    return invite_user_to_group(req)


@router.post("/apply", response_model=GroupApplyResponse)
def apply_to_group(req: GroupApplyRequest):
    return apply_to_join_group(req)

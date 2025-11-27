from fastapi import APIRouter, HTTPException, Depends
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
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/group-action", tags=["Group Actions"])


@router.post("/invite", response_model=GroupInviteResponse)
def invite_user(
    req: GroupInviteRequest,
    current_user: dict = Depends(get_current_user)
    ):
    requester_user_doc_id = current_user["user_doc_id"]
    return invite_user_to_group(req, requester_user_doc_id)


@router.post("/apply", response_model=GroupApplyResponse)
def apply_to_group(
    req: GroupApplyRequest,
    current_user: dict = Depends(get_current_user)
):
    requester_user_doc_id = current_user["user_doc_id"]
    return apply_to_join_group(req, requester_user_doc_id)

from fastapi import APIRouter, HTTPException, Query
from app.schemas.group_schema import GroupCreate, GroupUpdate
from app.services.group_service import (
    create_group, update_group, get_group_list, get_group_detail,
    get_group_members, get_my_groups, join_group, invite_member, leave_group
)

router = APIRouter(prefix="/api/group", tags=["Group"])

@router.post("/create")
def create_group_api(group: GroupCreate):
    try:
        return create_group(group)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{group_id}")
def update_group_api(group_id: str, group: GroupUpdate):
    try:
        return update_group(group_id, group)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
def get_group_list_api(
    category: str = Query(None),
    page: int = 1,
    size: int = 10
):
    try:
        return get_group_list(category, page, size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}")
def get_group_detail_api(group_id: str):
    try:
        return get_group_detail(group_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/members")
def get_group_members_api(group_id: str):
    try:
        return get_group_members(group_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my")
def get_my_groups_api(user_id: str):
    try:
        return get_my_groups(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/join")
def join_group_api(group_id: str, user_id: str):
    try:
        return join_group(group_id, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/invite")
def invite_member_api(group_id: str, user_id: str):
    try:
        return invite_member(group_id, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{group_id}/leave")
def leave_group_api(group_id: str, user_id: str):
    try:
        return leave_group(group_id, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

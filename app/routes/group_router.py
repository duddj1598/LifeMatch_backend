from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional

from app.schemas.group_schema import GroupCreate, GroupRead
from app.services.group_service import (
    create_group,
    search_groups,
    get_group_by_id,
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/group", tags=["Group"])


# -------------------------------------------------
# 🔒 그룹 생성 (리더 = 현재 로그인 유저)
# -------------------------------------------------
@router.post("/create", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_group_api(
    group: GroupCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    소모임 생성 API  
    - 프론트에서 leader_id는 보내지 않아도 됨 (보내도 무시함)  
    - 리더는 무조건 현재 로그인한 유저(JWT의 user_doc_id)
    """
    try:
        leader_id = current_user["user_doc_id"]
        result = create_group(group, leader_id=leader_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# 그룹 목록 조회 / 검색 (공개)
# -------------------------------------------------
@router.get("", response_model=List[GroupRead])
def list_or_search_groups(
    q: Optional[str] = Query(None, alias="q", description="그룹 이름 부분 검색"),
    category: Optional[str] = Query(None, description="카테고리"),
    min_member: Optional[int] = Query(None, ge=1, description="최소 인원"),
    max_member: Optional[int] = Query(None, ge=1, description="최대 인원"),
    sort_by: str = Query("created_at", description="정렬 필드"),
    desc: bool = Query(True, description="내림차순 여부"),
    limit: int = Query(50, ge=1, le=200, description="조회 수"),
    offset: int = Query(0, ge=0, description="오프셋"),
):
    try:
        results = search_groups(
            group_name=q,
            category=category,
            min_member=min_member,
            max_member=max_member,
            sort_by=sort_by,
            desc=desc,
            limit=limit,
            offset=offset,
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# 그룹 상세 조회 (공개)
# -------------------------------------------------
@router.get("/{group_id}", response_model=GroupRead)
def read_group_api(group_id: str):
    try:
        group = get_group_by_id(group_id)
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )
        return group
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    try:
        leader_id = current_user["user_doc_id"]
        result = create_group(group, leader_id=leader_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# 그룹 목록 조회 / 검색 (자연어 + 카테고리만 사용)
# -------------------------------------------------
@router.get("", response_model=List[GroupRead])
def list_or_search_groups(
    q: Optional[str] = Query(None, alias="q", description="자연어 검색어"),
    category: Optional[str] = Query(None, description="카테고리"),
    current_user: dict = Depends(get_current_user),
):
    """
    - q: 자연어 검색어 (예: '주말에 러닝할 사람')
    - category: 카테고리 문자열 (예: '여가·문화')
    """
    try:
        user_id = current_user["user_doc_id"]
        results = search_groups(
            query=q,
            category=category,
            user_id=user_id,
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

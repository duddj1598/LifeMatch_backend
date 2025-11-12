from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.schemas.group_schema import GroupCreate, GroupRead
from app.services.group_service import create_group, search_groups, get_group_by_id

router = APIRouter(prefix="/api/group", tags=["Group"])

@router.post("/create", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_group_api(group: GroupCreate):
    try:
        result = create_group(group)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[GroupRead])
def list_or_search_groups(
    q: Optional[str] = Query(None, alias="q", description="그룹 이름 부분 검색"),
    category: Optional[str] = Query(None, description="카테고리 정확 매칭"),
    min_member: Optional[int] = Query(None, ge=1, description="최소 멤버 수"),
    max_member: Optional[int] = Query(None, ge=1, description="최대 멤버 수"),
    sort_by: str = Query("created_at", description="정렬 필드"),
    desc: bool = Query(True, description="내림차순 정렬 여부"),
    limit: int = Query(50, ge=1, le=200, description="조회 수"),
    offset: int = Query(0, ge=0, description="오프셋")
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
            offset=offset
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}", response_model=GroupRead)
def read_group_api(group_id: str):
    try:
        group = get_group_by_id(group_id)
        if group is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        return group
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

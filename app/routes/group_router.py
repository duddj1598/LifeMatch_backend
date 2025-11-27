from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional

from app.schemas.group_schema import GroupCreate, GroupRead, GroupUpdateRequest
from app.services.group_service import (
    create_group,
    search_groups,
    get_group_by_id,
    update_group_detail,
)
from app.middleware.auth import get_current_user

class NotFoundException(Exception): pass 
class ForbiddenException(Exception): pass

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


# -------------------------------------------------
# 그룹 정보 수정
# -------------------------------------------------
@router.patch(
    "/{group_id}",
    summary="그룹 정보 수정 (이름, 주제, 설명)",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def update_group_details_api(
    group_id: str,
    update_data: GroupUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        current_user_doc_id = current_user.get("user_doc_id") 
        
        if not current_user_doc_id:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Authentication failed: User ID not found."
             )

        result = update_group_detail(
            group_id=group_id,
            current_user_doc_id=current_user_doc_id,
            update_data=update_data
        )
        return result
        
    except Exception as e:
        error_msg = str(e)
        
        # ⭐️ [핵심 수정] 오류 메시지를 분석하여 상태 코드 변환
        if error_msg.startswith("404:"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg.replace("404: ", ""))
        elif error_msg.startswith("403:"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg.replace("403: ", ""))
        elif error_msg.startswith("500:"):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg.replace("500: ", ""))
        else:
            # 예상치 못한 기타 오류는 500으로 처리
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")
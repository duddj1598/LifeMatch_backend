from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.schemas.chat_schema import (ChatMessageCreate, ChatRoomCreateRequest, ChatRoomCreateResponse)
from app.services.chat_service import (
    get_chat_list,
    leave_chat_room,
    send_message,
    get_chat_history,
    create_chat_room
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# -------------------------------------------------
# 🔒 채팅방 목록 조회 (내가 속한 소모임 채팅)
# -------------------------------------------------
@router.get("/list")
def chat_room_list(current_user: dict = Depends(get_current_user)):
    """
    JWT 기준 현재 로그인한 사용자가 속한 소모임 채팅방 목록 조회
    """
    try:
        user_id = current_user["user_doc_id"]  # Firestore users 문서 ID
        return get_chat_list(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# 🔒 채팅방 퇴장
# -------------------------------------------------
@router.delete("/leave")
def chat_leave(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    현재 로그인한 사용자가 특정 채팅방(=group_id)에서 나가기
    """
    try:
        user_id = current_user["user_doc_id"]
        return leave_chat_room(chat_id, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# 🔒 메시지 보내기
# -------------------------------------------------
@router.post("/{chat_id}/message")
def chat_send_message(
    chat_id: str,
    payload: ChatMessageCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    채팅방에 메시지 전송
    """
    try:
        user_id = current_user["user_doc_id"]
        return send_message(chat_id, user_id, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# 🔒 채팅 내역 조회 (페이징)
# -------------------------------------------------
@router.get("/{chat_id}/message")
def chat_history(
    chat_id: str,
    message_id: Optional[int] = None,
    size: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """
    채팅 내역 조회  
    - message_id 없으면: 최신 메시지부터 size개  
    - message_id 있으면: 그 message_id보다 이전 메시지들 중 size개 (위로 스크롤)
    """
    try:
        user_id = current_user["user_doc_id"]
        return get_chat_history(chat_id, user_id, message_id, size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------
# 🔥 채팅방 생성 (group / dm)
# -------------------------------------------------
@router.post("/create", response_model=ChatRoomCreateResponse)
def chat_create(
    req: ChatRoomCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    채팅방 생성 API  
    - group 생성 → group_id 필요  
    - dm 생성 → target_ids = [user1, user2]
    """
    try:
        user_id = current_user["user_doc_id"]   # 🔥 내 Firestore 문서 ID
        return create_chat_room(req, current_user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
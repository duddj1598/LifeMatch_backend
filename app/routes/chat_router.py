from fastapi import APIRouter, HTTPException, Depends, Header
from app.services.chat_service import (
    get_chat_list, leave_chat_room, send_message, get_chat_history
)
from app.schemas.chat_schema import ChatMessageCreate
from app.middleware.auth import verify_token
from typing import Optional

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def get_current_user(authorization: str = Header(...)):
    """Authorization 헤더에서 JWT 토큰 검증"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    return payload.get("sub")  # user_email 또는 user_id 반환


@router.get("/list")
def chat_room_list(current_user: str = Depends(get_current_user)):
    """유저의 소모임 채팅방 목록 조회"""
    try:
        return get_chat_list(current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/leave")
def chat_leave(chat_id: str, current_user: str = Depends(get_current_user)):
    """유저가 속한 소모임 채팅방에서 퇴장합니다"""
    try:
        return leave_chat_room(chat_id, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{chat_id}/message")
def chat_send_message(
    chat_id: str, 
    payload: ChatMessageCreate,
    current_user: str = Depends(get_current_user)
):
    """채팅방에 보낼 메시지를 입력합니다"""
    try:
        return send_message(chat_id, current_user, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chat_id}/message")
def chat_history(
    chat_id: str, 
    message_id: Optional[str] = None, 
    size: int = 10,
    current_user: str = Depends(get_current_user)
):
    """채팅방 참여자의 채팅 내역을 불러옵니다"""
    try:
        return get_chat_history(chat_id, current_user, message_id, size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
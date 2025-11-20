from pydantic import BaseModel
from typing import Optional, List


class ChatRoom(BaseModel):
    """채팅방 정보"""
    group_name: str
    category: str
    current_member: int


class ChatRoomListResponse(BaseModel):
    """채팅방 목록 응답"""
    status: int
    list: List[ChatRoom]


class ChatMessageCreate(BaseModel):
    """메시지 전송 요청"""
    content: str
    attachments: Optional[List[str]] = None


class ChatMessage(BaseModel):
    """메시지 정보"""
    message_id: int
    user_id: int
    content: str
    attachments: List[str]
    time: str


class ChatMessageResponse(BaseModel):
    """메시지 전송 응답"""
    status: int
    message_id: int
    chat_id: str
    user_id: int
    content: str
    attachments: List[str]
    time: str


class ChatHistoryResponse(BaseModel):
    """채팅 내역 응답"""
    messages: List[ChatMessage]
    next_message_id: Optional[int]
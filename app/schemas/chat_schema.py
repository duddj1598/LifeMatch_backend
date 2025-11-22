from pydantic import BaseModel
from typing import Optional, List

class ChatRoom(BaseModel):
    group_name: str
    category: str
    current_member: int


class ChatRoomListResponse(BaseModel):
    status: int
    list: List[ChatRoom]


class ChatMessageCreate(BaseModel):
    content: str
    attachments: Optional[List[str]] = None


class ChatMessage(BaseModel):
    message_id: int
    user_id: str            # 🔥 Firestore user_doc_id
    content: str
    attachments: List[str]
    time: str


class ChatMessageResponse(BaseModel):
    status: int
    message_id: int
    chat_id: str
    user_id: str            # 🔥 문자열로 통일
    content: str
    attachments: List[str]
    time: str


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]
    next_message_id: Optional[int]

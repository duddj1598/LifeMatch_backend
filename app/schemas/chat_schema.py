from pydantic import BaseModel
from typing import Optional, List, Literal

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

class ChatRoomCreateRequest(BaseModel):
    type: Literal["group", "dm"]     # "group" 또는 "dm"
    group_id: Optional[str] = None   # 그룹 채팅일 때만 사용
    target_ids: Optional[List[str]] = None  # DM일 때 상대 user_id 리스트 (1명)

class ChatRoomCreateResponse(BaseModel):
    status: int
    chat_id: str
    members: List[str]
    message: str

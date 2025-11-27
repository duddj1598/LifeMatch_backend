from pydantic import BaseModel, Field
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str = Field(..., description="자연어 질의")
    category: Optional[str] = Field(None, description="카테고리 (기술, 여가·문화 등)")

class SearchResponse(BaseModel):
    id: List[str]

class QueryOutputSchema(BaseModel):
    sql: str = Field(description="panel_demographic에서 사용할 SQL")
    queries_to_embedding: List[str] = Field(description="임베딩 기반 검색용 문장 리스트")

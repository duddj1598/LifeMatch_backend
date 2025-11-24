from pydantic import BaseModel, Field
from typing import List

class SearchRequest(BaseModel):
    query: str = Field(..., description="자연어 질의")

class SearchResponse(BaseModel):
    final_ids: List[str]
    panel_demographic_count: int
    embedding_matched_count: int
    elapsed_seconds: float

class QueryOutputSchema(BaseModel):
    sql: str = Field(description="panel_demographic에서 사용할 SQL")
    queries_to_embedding: List[str] = Field(description="임베딩 기반 검색용 문장 리스트")
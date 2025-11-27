from typing import Dict, Optional
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

# 통계 출력 스키마
class StatsSchema(BaseModel):
    # final_ids에 해당하는 도메인값만 key에 포함
    gender_distribution: Dict[str, int] # 성별 분포
    age_group_distribution: Dict[str, int] # 연령대 분포
    income_range_distribution: Dict[str, int] # 소득 분포
    region_distribution: Dict[str, int] # 지역 분포
    married_distribution: Dict[str, int] # 결혼 여부 분포
    car_ownership_distribution: Dict[str, int] # 자동차 소유 분포
    null_gender_count: Optional[int] = None # 성별 정보 누락 수
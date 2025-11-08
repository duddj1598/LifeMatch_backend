from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional

from app.services.panel_service import search

router = APIRouter(prefix="/api/panel", tags=["Panel"])

# TODO: 실제 DB 세션을 주입하기 위한 의존성 함수를 app.deps 등에 추가.
def get_db_session():
    """
    플레이스홀더 DB 세션 의존성.
    실제로는 app.deps.get_db 또는 SQLAlchemy sessionmaker 등을 반환하도록 교체.
    """
    return None

@router.get("/search")
def search_panel(
    query: str = Query(..., description="자연어 검색어 예: 러닝에 관심있는 20대"),
    mode: str = Query("field", description="검색 모드: field | semantic | hybrid"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    db_session = Depends(get_db_session),
):
    """
    /api/panel/search
    - query: 자연어 질의
    - mode: "field" (필드 매핑), "semantic" (임베딩 기반), "hybrid" (둘 조합)
    - limit/offset/min_score: 페이징 및 필터 옵션
    """

    if not query or query.strip() == "":
        raise HTTPException(status_code=400, detail="query는 빈 값일 수 없습니다")

    try:
        # 서비스에 DB 세션과 옵션을 전달
        results = search(
            query,
            db_session=db_session,
            mode=mode,
            limit=limit,
            offset=offset,
            min_score=min_score
        )

        return {
            "status": 200,
            "message": f"'{query}'에 해당하는 패널 {len(results)}명 검색됨",
            "results": results
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # TODO: 로깅을 추가해 내부 에러 정보를 기록하세요.
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")

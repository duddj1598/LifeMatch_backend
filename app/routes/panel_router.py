from fastapi import APIRouter, Query, HTTPException
from app.services.panel_service import search

router = APIRouter(prefix="/api/panel", tags=["Panel"])

@router.get("/search")
def search_panel(query: str = Query(..., description="자연어 검색어 예: 러닝에 관심있는 20대")):
    try:
        results = search(query)
        return {
            "status": 200,
            "message": f"'{query}'에 해당하는 패널 {len(results)}명 검색됨",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")

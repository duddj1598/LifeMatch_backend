from fastapi import APIRouter, Depends, HTTPException
from app.schemas.panel_schema import SearchRequest, SearchResponse, StatsSchema
from app.config.postgresql_config import get_db_conn, put_db_conn
from app.services.panel_service import decompose_and_search, get_stats

router = APIRouter(prefix="/api/panel", tags=["panel"])

def db_dependency():
    conn = get_db_conn()
    try:
        yield conn
    finally:
        put_db_conn(conn)

@router.post("/search", response_model=SearchResponse)
def search_panel(req: SearchRequest, conn = Depends(db_dependency)):
    try:
        result = decompose_and_search(req.query, req.category, conn)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    return SearchResponse(**result)

@router.post("/search_stat", response_model=StatsSchema)
def search_panel_stat(req: SearchResponse, conn = Depends(db_dependency)):
    try:
        result = decompose_and_search(req.query, req.category, conn)
        stats = get_stats(result["id"], conn)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
    return stats
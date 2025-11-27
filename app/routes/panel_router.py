from fastapi import APIRouter, Depends, HTTPException
from app.schemas.panel_schema import SearchRequest, SearchResponse
from app.config.postgresql_config import get_db_conn, put_db_conn
from app.services.panel_service import decompose_and_search

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

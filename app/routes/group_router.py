from fastapi import APIRouter, HTTPException
from app.schemas.group_schema import GroupCreate
from app.services.group_service import create_group

router = APIRouter(prefix="/api/group", tags=["Group"])

@router.post("/create")
def create_group_api(group: GroupCreate):
    try:
        result = create_group(group)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

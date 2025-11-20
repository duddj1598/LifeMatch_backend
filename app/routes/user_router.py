from fastapi import APIRouter, HTTPException
from app.schemas.user_schema import UserCreate
from app.services.user_service import create_user, login_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/signup")
def signup(user: UserCreate):
    try:
        result = create_user(user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/login")
def login(id: str, password: str):
    try:
        result = login_user(id, password)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter, HTTPException, Body, Depends
from app.schemas.user_schema import (
    UserCreate,
    FindIdRequest,
    FindIdResponse,
    ResetPasswordRequest,
)
from app.services.user_service import (
    create_user,
    login_user,
    find_user_id,
    reset_password,
    get_managed_groups,
    get_joined_groups
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])



# 회원가입
@router.post("/signup")
def signup(user: UserCreate):
    try:
        print("recieved user data:", user)
        return create_user(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# 로그인 (JWT 발급)
@router.get("/login")
def login(id: str, password: str):
    try:
        return login_user(id, password)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# 아이디(닉네임) 찾기
@router.post(
    "/find-id",
    response_model=FindIdResponse,
    summary="아이디(닉네임) 찾기"
)
def api_find_user_id(request: FindIdRequest = Body(...)):
    try:
        user_id = find_user_id(
            email=request.user_email,
            question=request.security_question,
            answer=request.security_answer
        )
        return FindIdResponse(status=200, user_id=user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {str(e)}")


# 비밀번호 재설정
@router.put(
    "/reset-password",
    summary="비밀번호 재설정"
)
def api_reset_password(request: ResetPasswordRequest = Body(...)):
    try:
        reset_password(
            login_id=request.login_id,
            email=request.user_email,
            question=request.security_question,
            answer=request.security_answer,
            new_password=request.new_password
        )
        return {"status": 200, "message": "비밀번호가 성공적으로 변경되었습니다."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {str(e)}")

# -------------------------------------------------
# 🔥 내가 리더인 소모임 목록 조회
# -------------------------------------------------
@router.get("/managed")
def my_managed_groups(current_user: dict = Depends(get_current_user)):
    try:
        user_doc_id = current_user["user_doc_id"]
        return get_managed_groups(user_doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# 🔥 내가 참여 중인 소모임 목록 조회
# -------------------------------------------------
@router.get("/joined")
def my_joined_groups(current_user: dict = Depends(get_current_user)):
    try:
        user_doc_id = current_user["user_doc_id"]
        return get_joined_groups(user_doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
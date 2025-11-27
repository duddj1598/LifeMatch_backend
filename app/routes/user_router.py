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
    get_joined_groups,
    is_id_duplicate,
    is_nickname_duplicate,
    is_email_duplicate
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])


# 중복 확인
@router.get("/check/id")
def check_duplicate_id(user_id: str):
    """아이디 중복 확인: 중복이면 409 에러"""
    if is_id_duplicate(user_id):
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.")
    return {"status": 200, "message": "사용 가능한 아이디입니다."}


@router.get("/check/nickname")
def check_duplicate_nickname(nickname: str):
    """닉네임 중복 확인: 중복이면 409 에러"""
    if is_nickname_duplicate(nickname):
        raise HTTPException(status_code=409, detail="이미 사용 중인 닉네임입니다.")
    return {"status": 200, "message": "사용 가능한 닉네임입니다."}


@router.get("/check/email")
def check_duplicate_email(email: str):
    """이메일 중복 확인: 중복이면 409 에러"""
    if is_email_duplicate(email):
        raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다.")
    return {"status": 200, "message": "사용 가능한 이메일입니다."}


# 회원가입
@router.post("/signup")
def signup(user: UserCreate):
    try:
        print("recieved user data:", user)
        return create_user(user)
    except HTTPException as e:
        raise e
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
    summary="아이디(닉네임) 찾기"
)
def api_find_user_id(request: FindIdRequest = Body(...)):
    try:
        user_id = find_user_id(
            nickname=request.nickname,                     # ⭐ 그대로
            question=request.security_question,             # ⭐ 그대로
            answer=request.security_answer                  # ⭐ 그대로
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
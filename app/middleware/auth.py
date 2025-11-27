import os
from datetime import datetime
from typing import Dict

import jwt
from fastapi import HTTPException, Header, Depends

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"


def verify_token(token: str) -> dict:
    """
    JWT 토큰을 검증하고 payload를 반환합니다.
    
    Args:
        token: JWT 토큰 문자열
        
    Returns:
        dict: 토큰 페이로드 (sub, email, login_id, nickname 등)
        
    Raises:
        HTTPException: 토큰이 유효하지 않거나 만료된 경우
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 만료 시간 수동 체크 (PyJWT의 exp 검증과 중복이지만 안전하게 유지)
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"토큰 검증 실패: {str(e)}")


def get_current_user(authorization: str = Header(...)) -> Dict[str, str]:
    """
    Authorization 헤더(Bearer 토큰)에서 현재 로그인한 유저 정보를 추출합니다.

    반환 값 예시:
    {
        "user_doc_id": "firestore-user-doc-id",
        "email": "test@example.com",
        "login_id": "test123",
        "nickname": "테스트유저"
    }
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization 헤더 형식이 올바르지 않습니다.")

    token = authorization.replace("Bearer ", "").strip()
    payload = verify_token(token)

    user_doc_id = payload.get("sub")
    if not user_doc_id:
        # sub에는 Firestore users 컬렉션의 문서 ID가 들어가야 함
        raise HTTPException(status_code=401, detail="토큰에 사용자 식별자가 없습니다.")

    return {
        "user_doc_id": user_doc_id,
        "email": payload.get("email", ""),
        "login_id": payload.get("login_id") or payload.get("id", ""),  # 호환용
        "nickname": payload.get("nickname", "")
    }

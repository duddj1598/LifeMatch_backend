import jwt
import os
from fastapi import HTTPException
from datetime import datetime

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = "HS256"


def verify_token(token: str) -> dict:
    """
    JWT 토큰을 검증하고 payload를 반환합니다.
    
    Args:
        token: JWT 토큰 문자열
        
    Returns:
        dict: 토큰 페이로드 (sub, nickname 등)
        
    Raises:
        HTTPException: 토큰이 유효하지 않거나 만료된 경우
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 만료 시간 확인
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
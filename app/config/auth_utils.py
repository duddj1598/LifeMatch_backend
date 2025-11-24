# app/config/auth_utils.py

import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta

SECRET_KEY = "YOUR_JWT_SECRET_KEY"
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)

# JWT 생성
def create_access_token(data: dict, expires_delta: int = 3600):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# JWT 검증
async def verify_token(request: Request):
    # 1) HEADER 직접 꺼냄
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

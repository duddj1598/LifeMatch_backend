# main.py (기존 파일을 이렇게 수정합니다)

from fastapi import FastAPI
# 기존 라우터 import 삭제
from app.routes import user_router, group_router, panel_router 

# 새로 만든 라우터 import
from app.routes import lifestyle_test_router 

app = FastAPI(title="LifeMatch Backend")

app.include_router(user_router.router)
app.include_router(group_router.router)
app.include_router(panel_router.router)

# 새로 만든 라우터 include
app.include_router(lifestyle_test_router.router)

@app.get("/")
def root():
    return {"message": "LifeMatch Backend 서버 실행 중"}
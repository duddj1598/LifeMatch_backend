from fastapi import FastAPI
from app.routes import (
    chat_router,group_router, home_router, lifestyle_test_router, notification_router, panel_router, profile_router, user_router, group_action_router
    )
from app.config.postgresql_config import init_db_pool
from app.config.llm_config import get_embedding_model, get_chroma_db, get_llm_client
import logging

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="LifeMatch Backend")

app.include_router(user_router.router)
app.include_router(group_router.router)
app.include_router(panel_router.router)
app.include_router(lifestyle_test_router.router)
app.include_router(home_router.router)
app.include_router(notification_router.router)
app.include_router(profile_router.router)
app.include_router(chat_router.router)
app.include_router(group_action_router.router)

@app.on_event("startup")
def startup_event():
    # DB 커넥션 풀 초기화
    try:
        init_db_pool()
        print("DB pool initialized")
    except Exception as e:
        # 로그만 남기고 계속 실행
        print("Warning: DB pool initialization failed:", e)

    # LLM / Embedding / Chroma 초기화 시도 (실패해도 서버는 띄움)
    try:
        get_embedding_model()
        get_chroma_db()
        get_llm_client()
        print("LLM and embedding models initialized")
    except Exception as e:
        print("Warning: model initialization failed on startup:", e)

@app.get("/")
def root():
    return {"message": "LifeMatch Backend 서버 실행 중"}

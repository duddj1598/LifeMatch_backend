from fastapi import FastAPI
from app.routes import (
    chat_router,group_router, home_router, lifestyle_test_router, notification_router, panel_router, profile_router, user_router
    )

app = FastAPI(title="LifeMatch Backend")

app.include_router(user_router.router)
app.include_router(group_router.router)
app.include_router(panel_router.router)
app.include_router(lifestyle_test_router.router)
app.include_router(home_router.router)
app.include_router(notification_router.router)
app.include_router(profile_router.router)
app.include_router(chat_router.router)
                   
@app.get("/")
def root():
    return {"message": "LifeMatch Backend 서버 실행 중"}
from fastapi import FastAPI
from app.routes import user_router, group_router, panel_router 
from app.routes import lifestyle_test_router 
from app.routes import home_router
from app.routes import notification_router
from app.routes import profile_router

app = FastAPI(title="LifeMatch Backend")

app.include_router(user_router.router)
app.include_router(group_router.router)
app.include_router(panel_router.router)
app.include_router(lifestyle_test_router.router)
app.include_router(home_router.router)
app.include_router(notification_router.router)
app.include_router(profile_router.router)
                   
@app.get("/")
def root():
    return {"message": "LifeMatch Backend 서버 실행 중"}
from fastapi import FastAPI
from app.routes import user_router, group_router, panel_router

app = FastAPI(title="LifeMatch Backend")

app.include_router(user_router.router)
app.include_router(group_router.router)
app.include_router(panel_router.router)

@app.get("/")
def root():
    return {"message": "LifeMatch Backend 서버 실행 중"}

from fastapi import FastAPI
from app.routes import user_router

app = FastAPI(title="FastAPI Firebase Signup")

app.include_router(user_router.router)

@app.get("/")
def root():
    return {"message": "회원가입 API 서버 실행 중"}

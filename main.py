from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import datetime

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="Local Backend Health Check",
    description="A simple FastAPI server to verify connectivity from a Flutter app."
)

@app.get("/health", response_class=JSONResponse, status_code=200)
def health_check():
    """
    서버의 상태를 확인하는 엔드포인트입니다.
    Flutter 앱에서 200 응답을 기대하며 호출합니다.
    """
    return {
        "status": "ok",
        "message": "Backend is running and healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "LifeMatch-Backend"
    }

# 이 파일이 직접 실행될 때 Uvicorn 서버를 시작합니다.
# 호스트를 '0.0.0.0'으로 설정하면 외부(예: 에뮬레이터/시뮬레이터)에서의 접속을 허용합니다.
# 포트 8080은 Flutter 앱의 기본 설정에 맞춰져 있습니다.
if __name__ == "__main__":
    print("FastAPI 서버를 시작합니다. (http://127.0.0.1:8080/health)")
    uvicorn.run(app, host="0.0.0.0", port=8080)

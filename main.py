# main.py
from fastapi import FastAPI, Response, File, UploadFile, Request
from fastapi.responses import RedirectResponse, PlainTextResponse
import uvicorn
import asyncio
import os

app = FastAPI()

@app.get("/")
def root():
    """메인 페이지 - 환경변수로 설정된 컨트롤러 이름 출력"""
    controller_name = os.getenv("CONTROLLER_NAME", "unknown")
    return {"msg": f"Hello {controller_name}"}

# ===== Cookie & Session Affinity 테스트 =====
@app.get("/set-cookie")
def set_cookie(response: Response, request: Request):
    """쿠키 설정 테스트 - JSESSIONID 쿠키가 설정되는지 확인"""
    response.set_cookie("JSESSIONID", "test-session-value", httponly=False) 
    return {
        "msg": "쿠키가 설정되었습니다",
        "설정된_쿠키": "JSESSIONID",
        "확인방법": "브라우저 개발자도구에서 응답 헤더의 Set-Cookie를 확인하세요"
    }

@app.get("/check-session")
def check_session(request: Request):
    """세션 쿠키 확인 테스트 - route 쿠키가 설정되었는지 확인"""
    route_cookie = request.cookies.get("route", "없음")
    return {
        "msg": "세션 쿠키 확인",
        "route_쿠키": route_cookie,
        "결과": "설정됨" if route_cookie != "없음" else "설정되지 않음"
    }

# ===== CORS 테스트 =====
@app.options("/cors-test")
def cors_preflight():
    """CORS preflight 요청 테스트"""
    return PlainTextResponse("", status_code=204)

@app.post("/cors-test")
def cors_post():
    """CORS POST 요청 테스트"""
    return {
        "msg": "CORS POST 요청 성공",
        "확인방법": "응답 헤더에 Access-Control-Allow-Origin이 있는지 확인하세요"
    }

@app.get("/cors-test")
def cors_get(request: Request):
    """CORS GET 요청 테스트"""
    origin = request.headers.get("origin", "없음")
    return {
        "msg": "CORS GET 요청 성공",
        "요청_Origin": origin,
        "확인방법": "응답 헤더에 Access-Control-Allow-Origin이 있는지 확인하세요"
    }

# ===== Security Headers 테스트 =====
@app.get("/security-headers")
def security_headers():
    """보안 헤더 테스트"""
    return {
        "msg": "보안 헤더 확인",
        "확인할_헤더": [
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "X-Frame-Options",
            "Pragma",
            "Cache-Control"
        ],
        "확인방법": "브라우저 개발자도구에서 응답 헤더를 확인하세요"
    }

# ===== Redirect 테스트 =====
@app.get("/redirect")
def redirect():
    """리다이렉트 테스트 - 루트로 리다이렉트"""
    return RedirectResponse(url="/")

@app.get("/redirect-external")
def redirect_external():
    """외부 리다이렉트 테스트"""
    return RedirectResponse(url="https://example.com", status_code=301)

# ===== Proxy Timeout 테스트 =====
@app.get("/timeout-test")
async def timeout_test(seconds: int = 5):
    """프록시 타임아웃 테스트"""
    if seconds > 60:
        return {"오류": "최대 60초까지만 가능합니다"}
    
    await asyncio.sleep(seconds)
    return {
        "msg": f"{seconds}초 후 응답 완료",
        "결과": "타임아웃이 발생하면 프록시 설정을 확인하세요"
    }

# ===== File Upload 테스트 =====
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """파일 업로드 테스트"""
    content = await file.read()
    return {
        "msg": "파일 업로드 성공",
        "파일명": file.filename,
        "크기": f"{len(content)} bytes",
        "타입": file.content_type
    }

# ===== Request Info (디버깅용) =====
@app.get("/request-info")
def request_info(request: Request):
    """요청 정보 확인"""
    controller_name = os.getenv("CONTROLLER_NAME", "unknown")
    return {
        "컨트롤러": controller_name,
        "요청_메서드": request.method,
        "URL": str(request.url),
        "클라이언트_IP": request.client.host if request.client else None,
        "확인방법": "X-Forwarded-For 헤더를 확인하세요"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)


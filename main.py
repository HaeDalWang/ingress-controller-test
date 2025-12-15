# main.py
from fastapi import FastAPI, Response, File, UploadFile, Request
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
import uvicorn
import asyncio
import os
from datetime import datetime

app = FastAPI()

def generate_html_dashboard(request: Request):
    """대시보드 HTML 생성"""
    controller_name = os.getenv("CONTROLLER_NAME", "unknown")
    
    # 요청 정보 수집
    cookies = dict(request.cookies)
    headers = dict(request.headers)
    client_ip = request.client.host if request.client else None
    
    # 쿠키 정보 포맷팅
    cookies_html = ""
    if cookies:
        for name, value in cookies.items():
            cookies_html += f"<tr><td><strong>{name}</strong></td><td>{value}</td></tr>"
    else:
        cookies_html = "<tr><td colspan='2'>쿠키 없음</td></tr>"
    
    # 헤더 정보 포맷팅 (중요한 것만)
    important_headers = [
        "host", "user-agent", "x-forwarded-for", "x-real-ip", 
        "origin", "referer", "accept", "accept-language"
    ]
    headers_html = ""
    for header_name in important_headers:
        header_value = headers.get(header_name.lower(), "없음")
        if header_value != "없음":
            headers_html += f"<tr><td><strong>{header_name}</strong></td><td>{header_value}</td></tr>"
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ingress Controller Test Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .header .controller {{
            margin-top: 10px;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .links {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .link-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: transform 0.2s;
        }}
        .link-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .link-card h3 {{
            margin: 0 0 10px 0;
            color: #667eea;
        }}
        .link-card a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        .link-card a:hover {{
            text-decoration: underline;
        }}
        .status {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.9em;
            font-weight: 500;
        }}
        .status.ok {{
            background-color: #d4edda;
            color: #155724;
        }}
        .status.none {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Ingress Controller Test Dashboard</h1>
        <div class="controller">Controller: <strong>{controller_name}</strong></div>
        <div class="timestamp">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>

    <div class="section">
        <h2>📊 현재 요청 정보</h2>
        <table>
            <tr>
                <th>항목</th>
                <th>값</th>
            </tr>
            <tr>
                <td><strong>클라이언트 IP</strong></td>
                <td>{client_ip or "알 수 없음"}</td>
            </tr>
            <tr>
                <td><strong>요청 URL</strong></td>
                <td>{request.url}</td>
            </tr>
            <tr>
                <td><strong>요청 메서드</strong></td>
                <td>{request.method}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>🍪 쿠키 정보</h2>
        <table>
            <tr>
                <th>쿠키 이름</th>
                <th>값</th>
            </tr>
            {cookies_html}
        </table>
        <div style="margin-top: 15px;">
            <span class="status {'ok' if cookies else 'none'}">
                {'쿠키 ' + str(len(cookies)) + '개 발견' if cookies else '쿠키 없음'}
            </span>
            <span class="status {'ok' if 'route' in cookies else 'none'}" style="margin-left: 10px;">
                route 쿠키: {'있음' if 'route' in cookies else '없음'}
            </span>
        </div>
    </div>

    <div class="section">
        <h2>📋 주요 헤더 정보</h2>
        <table>
            <tr>
                <th>헤더 이름</th>
                <th>값</th>
            </tr>
            {headers_html}
        </table>
    </div>

    <div class="section">
        <h2>🔗 테스트 기능</h2>
        <div class="links">
            <div class="link-card">
                <h3>쿠키 설정</h3>
                <p>JSESSIONID 쿠키를 설정합니다</p>
                <a href="/set-cookie" target="_blank">/set-cookie</a>
            </div>
            <div class="link-card">
                <h3>세션 확인</h3>
                <p>route 쿠키 확인</p>
                <a href="/check-session" target="_blank">/check-session</a>
            </div>
            <div class="link-card">
                <h3>CORS 테스트</h3>
                <p>CORS 헤더 확인</p>
                <a href="/cors-test" target="_blank">/cors-test</a>
            </div>
            <div class="link-card">
                <h3>보안 헤더</h3>
                <p>Security headers 확인</p>
                <a href="/security-headers" target="_blank">/security-headers</a>
            </div>
            <div class="link-card">
                <h3>리다이렉트</h3>
                <p>내부 리다이렉트 테스트</p>
                <a href="/redirect" target="_blank">/redirect</a>
            </div>
            <div class="link-card">
                <h3>타임아웃 테스트</h3>
                <p>프록시 타임아웃 확인</p>
                <a href="/timeout-test?seconds=5" target="_blank">/timeout-test</a>
            </div>
            <div class="link-card">
                <h3>파일 업로드</h3>
                <p>파일 업로드 테스트 (POST)</p>
                <a href="/upload" target="_blank">/upload</a>
            </div>
            <div class="link-card">
                <h3>요청 정보</h3>
                <p>전체 요청 정보 확인</p>
                <a href="/request-info" target="_blank">/request-info</a>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>💡 사용 방법</h2>
        <ul>
            <li>브라우저 개발자 도구(F12)를 열어 Network 탭에서 응답 헤더를 확인하세요</li>
            <li>Application 탭에서 쿠키를 확인할 수 있습니다</li>
            <li>각 테스트 링크를 클릭하여 기능을 확인하세요</li>
            <li>페이지를 새로고침하면 최신 쿠키/헤더 정보가 표시됩니다</li>
        </ul>
    </div>
</body>
</html>"""
    return html

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """메인 페이지 - 대시보드"""
    return generate_html_dashboard(request)

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


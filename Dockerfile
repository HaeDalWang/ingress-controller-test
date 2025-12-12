FROM python:3.13-slim
WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 의존성 파일 복사 및 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 애플리케이션 코드 복사
COPY main.py .

# 포트 설정 (values.yaml의 service.port와 일치)
EXPOSE 8001

# uv로 실행
CMD ["uv", "run", "main.py"]

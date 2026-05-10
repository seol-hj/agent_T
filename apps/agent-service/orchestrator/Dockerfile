# Orchestrator Service Dockerfile

FROM python:3.11-slim

WORKDIR /app

# 공통 라이브러리 복사
COPY libs/common /app/libs/common

# Orchestrator 앱 복사
COPY apps/orchestrator /app/apps/orchestrator

# 의존성 설치
RUN pip install --no-cache-dir -r /app/apps/orchestrator/requirements.txt

# Python path 설정
ENV PYTHONPATH=/app/libs:/app

# 환경변수 기본값
ENV LLM_PROVIDER=mock
ENV LLM_MODEL_ID=mock-model
ENV PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "apps.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Scenario Builder Service Dockerfile

FROM python:3.11-slim

WORKDIR /app

# 공통 라이브러리 복사
COPY libs/common /app/libs/common

# Scenario Builder 앱 복사
COPY apps/scenario-builder /app/apps/scenario-builder

# 의존성 설치
RUN pip install --no-cache-dir -r /app/apps/scenario-builder/requirements.txt

# Python path 설정
ENV PYTHONPATH=/app/libs:/app

# 환경변수 기본값
ENV PORT=8001

EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

CMD ["python", "-m", "uvicorn", "apps.scenario-builder.main:app", "--host", "0.0.0.0", "--port", "8001"]

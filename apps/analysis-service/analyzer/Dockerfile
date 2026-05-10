# Analyzer Service Dockerfile

FROM python:3.11-slim

WORKDIR /app

# 공통 라이브러리 복사
COPY libs/common /app/libs/common

# Analyzer 앱 복사
COPY apps/analyzer /app/apps/analyzer

# 의존성 설치
RUN pip install --no-cache-dir -r /app/apps/analyzer/requirements.txt

# Python path 설정
ENV PYTHONPATH=/app/libs:/app

# 환경변수 기본값
ENV STORAGE_PROVIDER=local
ENV STORAGE_BASE_PATH=/app/data/analysis
ENV PORT=8005

# 데이터 디렉토리 생성
RUN mkdir -p /app/data/analysis

EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health')"

CMD ["python", "-m", "uvicorn", "apps.analyzer.main:app", "--host", "0.0.0.0", "--port", "8005"]

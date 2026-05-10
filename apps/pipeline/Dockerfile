# Pipeline Service Dockerfile

FROM python:3.11-slim

WORKDIR /app

# 공통 라이브러리 복사
COPY libs /app/libs

# Pipeline 앱 복사
COPY apps/pipeline /app/apps/pipeline

# 의존성 설치
RUN pip install --no-cache-dir -r /app/apps/pipeline/requirements.txt

# /data 디렉토리 생성 및 권한 설정
RUN mkdir -p /data && chmod -R 777 /data

# Python path 설정
ENV PYTHONPATH=/app:/app/libs:/app/apps/pipeline

# 환경변수 기본값
ENV ORCHESTRATOR_URL=http://orchestrator:8001
ENV SCENARIO_BUILDER_URL=http://scenario-builder:8002
ENV NETWORK_BUILDER_URL=http://network-builder:8003
ENV DEMAND_BUILDER_URL=http://demand-builder:8004
ENV SIMULATOR_RUNNER_URL=http://simulator-runner:8005
ENV ANALYZER_URL=http://analyzer:8006
ENV REPORTER_URL=http://reporter:8007
ENV PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "apps.pipeline.main:app", "--host", "0.0.0.0", "--port", "8000"]

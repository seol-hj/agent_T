# Report Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 공통 라이브러리 복사
COPY libs /app/libs

# Python 의존성 설치
COPY apps/report-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY apps/report-service /app

# 비root 사용자 생성 및 /data 디렉토리 권한 설정
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /data && \
    chown -R appuser:appuser /data && \
    chmod -R 777 /data
USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 노출
EXPOSE 8000

# 환경 변수 기본값
ENV LLM_PROVIDER=bedrock \
    STORAGE_PROVIDER=s3 \
    PYTHONPATH=/app:/app/libs

# 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

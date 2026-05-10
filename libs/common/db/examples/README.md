# DB Repository 예제

---

## 1. 기본 사용 예제 (basic_usage.py)

SQLite 인메모리 DB를 사용한 Repository 기본 CRUD 작업.

### 실행

```bash
cd /mnt/c/Users/gandd/OneDrive/Desktop/proj/agent-t
python libs/common/db/examples/basic_usage.py
```

### 예제 내용

1. 데이터베이스 초기화
2. 사용자 요청 생성
3. 실험 생성 및 상태 업데이트
4. 시나리오 생성 (Baseline + Alternative)
5. Agent 로그 생성
6. 데이터 조회 (시나리오, 로그, 토큰 사용량, 평균 실행 시간)
7. 실험 완료 처리
8. 최근 실험 조회

---

## 2. FastAPI 통합 예제 (fastapi_integration.py)

FastAPI 앱에서 Repository를 사용하는 REST API.

### 실행

```bash
cd /mnt/c/Users/gandd/OneDrive/Desktop/proj/agent-t
python libs/common/db/examples/fastapi_integration.py
```

서버 시작 후: http://localhost:8080

### API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 서비스 정보 |
| POST | `/user-requests` | 사용자 요청 생성 |
| POST | `/experiments` | 실험 생성 |
| GET | `/experiments` | 실험 목록 조회 |
| GET | `/experiments/{exp_id}` | 실험 상세 조회 |
| PATCH | `/experiments/{exp_id}/status` | 실험 상태 업데이트 |
| DELETE | `/experiments/{exp_id}` | 실험 삭제 |
| GET | `/experiments/{exp_id}/logs` | 실험별 로그 조회 |
| GET | `/experiments/{exp_id}/stats` | 실험 통계 |

### 사용 예시

```bash
# 사용자 요청 생성
curl -X POST http://localhost:8080/user-requests \
  -H "Content-Type: application/json" \
  -d '{"request_text": "강남역 교통량 증가 시뮬레이션", "language": "ko"}'

# 실험 생성
curl -X POST http://localhost:8080/experiments \
  -H "Content-Type: application/json" \
  -d '{"user_request_id": "req_12345", "status": "pending"}'

# 실험 목록 조회
curl http://localhost:8080/experiments

# 실험 상세 조회
curl http://localhost:8080/experiments/exp_12345

# 실험 상태 업데이트
curl -X PATCH http://localhost:8080/experiments/exp_12345/status \
  -H "Content-Type: application/json" \
  -d '"completed"'

# 실험 로그 조회
curl http://localhost:8080/experiments/exp_12345/logs

# 실험 통계
curl http://localhost:8080/experiments/exp_12345/stats
```

---

## 3. RDS PostgreSQL 연결 예제

### 환경변수 설정

```bash
export DATABASE_URL=postgresql://admin:password@rds-endpoint.amazonaws.com:5432/agent_t
```

### 코드 수정 (fastapi_integration.py)

```python
@app.on_event("startup")
def startup_event():
    # PostgreSQL 사용
    setup_database(echo=False)  # DATABASE_URL 환경변수 사용
    print("✓ 데이터베이스 초기화 완료")
```

### 실행

```bash
export DATABASE_URL=postgresql://admin:password@rds-endpoint.amazonaws.com:5432/agent_t
python libs/common/db/examples/fastapi_integration.py
```

---

## 4. Secrets Manager 통합 예제

```python
import boto3
import json
from common.db.session import setup_database

def get_db_credentials():
    client = boto3.client('secretsmanager', region_name='ap-northeast-2')
    secret = client.get_secret_value(SecretId='agent-t/db/credentials')
    return json.loads(secret['SecretString'])

@app.on_event("startup")
def startup_event():
    credentials = get_db_credentials()
    database_url = (
        f"postgresql://{credentials['username']}:{credentials['password']}"
        f"@{credentials['host']}:{credentials['port']}/{credentials['dbname']}"
    )
    setup_database(database_url=database_url)
```

---

## 5. Docker에서 실행

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY libs/common /app/libs/common
COPY libs/common/db/examples /app/examples

RUN pip install -r /app/libs/common/requirements.txt

ENV DATABASE_URL=sqlite:///./example.db

CMD ["python", "examples/fastapi_integration.py"]
```

### 빌드 및 실행

```bash
docker build -t db-example .
docker run -p 8080:8080 db-example
```

---

## 문제 해결

### ModuleNotFoundError

```bash
# PYTHONPATH 설정
export PYTHONPATH=/mnt/c/Users/gandd/OneDrive/Desktop/proj/agent-t:$PYTHONPATH

# 또는 스크립트에서
import sys
sys.path.insert(0, '/path/to/agent-t')
```

### SQLite 동시성 에러

SQLite는 단일 쓰기만 지원. 프로덕션에서는 PostgreSQL 사용 필수.

### PostgreSQL 연결 에러

```bash
# 연결 테스트
psql -h rds-endpoint.amazonaws.com -U admin -d agent_t -c "SELECT 1"

# 방화벽 확인
nc -zv rds-endpoint.amazonaws.com 5432

# VPC Security Group 확인
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

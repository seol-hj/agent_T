# Database Layer

SQLAlchemy 기반 데이터베이스 추상화 계층.

---

## 개요

AI Agent T 플랫폼의 모든 실험 데이터, 산출물, 로그를 RDS PostgreSQL에 저장.

- **ORM**: SQLAlchemy
- **마이그레이션**: Alembic (향후)
- **Repository Pattern**: 데이터 접근 로직 추상화
- **Local 테스트**: SQLite 지원

---

## 테이블 구조

### 1. **experiments**
실험 메타데이터 (상태, 시작/완료 시간, 에러 메시지)

### 2. **user_requests**
사용자의 원본 자연어 요청

### 3. **experiment_specs**
Orchestrator가 생성한 실험 명세 (JSON)

### 4. **scenarios**
Scenario Builder가 생성한 시나리오 계획 (Baseline + Alternatives)

### 5. **network_artifacts**
Network Builder 산출물 (.net.xml URI)

### 6. **demand_artifacts**
Demand Builder 산출물 (.rou.xml URI)

### 7. **simulation_runs**
SUMO 시뮬레이션 실행 기록 (상태, 실행 시간, 산출물 URI)

### 8. **analysis_results**
Analyzer 분석 결과 (KPI, 비교 데이터)

### 9. **reports**
Reporter 리포트 산출물 (Markdown/PDF URI, 요약)

### 10. **agent_logs**
각 Agent의 실행 로그 (입출력, 토큰 사용량, 실행 시간)

### 11. **model_versions**
LLM 모델 버전 추적 (모델명, 제공자, 파라미터)

### 12. **prompt_versions**
프롬프트 버전 추적 (프롬프트명, 텍스트, 타입)

### 13. **rag_documents**
RAG 문서 메타데이터 (URI, 카테고리, 태그, 전체 텍스트)

---

## 설치

```bash
pip install sqlalchemy psycopg2-binary alembic
```

---

## 사용법

### 1. 환경변수 설정

```bash
# Local (SQLite)
export DATABASE_URL=sqlite:///./agent_t.db

# Development (RDS PostgreSQL)
export DATABASE_URL=postgresql://user:pass@dev-rds.amazonaws.com:5432/agent_t_dev

# Production (RDS PostgreSQL)
export DATABASE_URL=postgresql://user:pass@prod-rds.amazonaws.com:5432/agent_t_prod
```

### 2. 데이터베이스 초기화

```python
from libs.common.db.session import setup_database

# 앱 시작 시 한 번만 호출
setup_database(echo=False)
```

### 3. Repository 사용 (기본)

```python
from libs.common.db.session import get_global_db
from libs.common.db.repositories import ExperimentRepository

# 세션 생성
for db in get_global_db():
    # Repository 생성
    exp_repo = ExperimentRepository(db)

    # Create
    exp = exp_repo.create(
        id="exp_001",
        status="pending"
    )

    # Read
    exp = exp_repo.get("exp_001")

    # Update
    exp = exp_repo.update("exp_001", status="completed")

    # Delete
    exp_repo.delete("exp_001")
```

### 4. Repository 사용 (FastAPI)

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from libs.common.db.session import setup_database, get_global_db
from libs.common.db.repositories import ExperimentRepository

app = FastAPI()

@app.on_event("startup")
def startup():
    setup_database()

@app.get("/experiments/{exp_id}")
def get_experiment(exp_id: str, db: Session = Depends(get_global_db)):
    repo = ExperimentRepository(db)
    exp = repo.get(exp_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp
```

### 5. 복잡한 쿼리 예시

```python
from libs.common.db.repositories import (
    ExperimentRepository,
    SimulationRunRepository,
    AgentLogRepository,
)

# 실험별 시뮬레이션 실행 조회
exp_repo = ExperimentRepository(db)
sim_repo = SimulationRunRepository(db)

exp = exp_repo.get_with_relations("exp_001")
sims = sim_repo.get_by_experiment("exp_001")

for sim in sims:
    print(f"Variant: {sim.variant_id}, Status: {sim.execution_status}")

# 실험별 토큰 사용량
log_repo = AgentLogRepository(db)
total_tokens = log_repo.get_token_usage_by_experiment("exp_001")
print(f"Total tokens: {total_tokens}")

# 단계별 평균 실행 시간
avg_time = log_repo.get_average_execution_time_by_step("orchestrator")
print(f"Avg orchestrator time: {avg_time}ms")
```

---

## Repository Pattern

모든 Repository는 `BaseRepository`를 상속하여 공통 CRUD 메서드 제공:

- `create(**kwargs)`: 레코드 생성
- `get(id)`: ID로 조회
- `get_all(limit, offset)`: 전체 조회
- `get_by_filter(**filters)`: 필터 조건 조회
- `update(id, **kwargs)`: 업데이트
- `delete(id)`: 삭제
- `count(**filters)`: 개수 세기
- `exists(id)`: 존재 여부 확인

각 Repository는 도메인별 특화 메서드 추가:

```python
# ExperimentRepository
exp_repo.get_by_status("running")
exp_repo.get_recent(limit=10)
exp_repo.update_status("exp_001", "completed")

# AgentLogRepository
log_repo.get_by_experiment("exp_001")
log_repo.get_token_usage_by_experiment("exp_001")
log_repo.get_average_execution_time_by_step("orchestrator")

# RAGDocumentRepository
doc_repo.get_by_category("policy")
doc_repo.search_by_text("교통")
```

---

## 마이그레이션

현재는 `Base.metadata.create_all()`로 테이블 자동 생성.

향후 Alembic으로 전환 예정:

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "Add new table"

# 마이그레이션 실행
alembic upgrade head

# 롤백
alembic downgrade -1
```

자세한 내용은 [migrations/README.md](migrations/README.md) 참조.

---

## 테스트

### 단위 테스트

```bash
pytest libs/common/db/tests/test_repositories.py -v
```

### Session 테스트

```bash
pytest libs/common/db/tests/test_session.py -v
```

### 전체 테스트

```bash
pytest libs/common/db/tests/ -v
```

테스트는 인메모리 SQLite 사용 (실제 DB 불필요).

---

## 디렉토리 구조

```
libs/common/db/
├── models.py                # SQLAlchemy ORM 모델 (13개 테이블)
├── session.py               # 세션 관리 (setup_database, get_global_db)
├── repositories/            # Repository Pattern
│   ├── __init__.py
│   ├── base_repository.py   # 공통 CRUD
│   ├── experiment_repository.py
│   ├── user_request_repository.py
│   ├── experiment_spec_repository.py
│   ├── scenario_repository.py
│   ├── network_artifact_repository.py
│   ├── demand_artifact_repository.py
│   ├── simulation_run_repository.py
│   ├── analysis_result_repository.py
│   ├── report_repository.py
│   ├── agent_log_repository.py
│   ├── model_version_repository.py
│   ├── prompt_version_repository.py
│   └── rag_document_repository.py
├── migrations/              # Alembic 마이그레이션 (향후)
│   └── README.md
├── tests/                   # 테스트
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_repositories.py # Repository 테스트
│   └── test_session.py      # Session 관리 테스트
└── README.md                # 문서 (현재 파일)
```

---

## RDS PostgreSQL 연결

### AWS Secrets Manager 사용 (권장)

```python
import boto3
import json
from libs.common.db.session import setup_database

def get_db_credentials():
    client = boto3.client('secretsmanager', region_name='ap-northeast-2')
    secret = client.get_secret_value(SecretId='agent-t/db/credentials')
    return json.loads(secret['SecretString'])

# 앱 시작 시
credentials = get_db_credentials()
database_url = f"postgresql://{credentials['username']}:{credentials['password']}@{credentials['host']}:{credentials['port']}/{credentials['dbname']}"
setup_database(database_url=database_url)
```

### 환경변수 직접 사용

```bash
export DATABASE_URL=postgresql://admin:password@prod-rds.amazonaws.com:5432/agent_t_prod
```

```python
from libs.common.db.session import setup_database

# DATABASE_URL 환경변수 자동 사용
setup_database()
```

---

## 성능 최적화

### 1. 연결 풀링

PostgreSQL 사용 시 자동으로 연결 풀 생성:

```python
# session.py 내부
engine = create_engine(
    url,
    pool_size=10,        # 기본 연결 수
    max_overflow=20,     # 추가 연결 수
    pool_pre_ping=True   # 연결 유효성 체크
)
```

### 2. 인덱스

주요 필드에 인덱스 적용:

```python
# models.py
__table_args__ = (
    Index("idx_experiments_status", "status"),
    Index("idx_experiments_created_at", "created_at"),
)
```

### 3. 관계 로딩 최적화

```python
# Lazy loading (기본)
exp = exp_repo.get("exp_001")
sims = exp.simulation_runs  # 별도 쿼리

# Eager loading (join)
exp = session.query(Experiment).options(
    joinedload(Experiment.simulation_runs)
).filter(Experiment.id == "exp_001").first()
```

---

## 로컬 ↔ RDS 전환

### Local (SQLite)

```bash
export DATABASE_URL=sqlite:///./agent_t.db
python -m uvicorn apps.pipeline.main:app
```

### RDS (PostgreSQL)

```bash
export DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/agent_t
python -m uvicorn apps.pipeline.main:app
```

코드 변경 없이 환경변수만 수정하면 전환 가능.

---

## 문제 해결

### SQLite → PostgreSQL 마이그레이션

```bash
# SQLite에서 데이터 내보내기
sqlite3 agent_t.db .dump > dump.sql

# PostgreSQL로 임포트 (수정 필요)
psql -h rds-endpoint -U user -d agent_t < dump.sql
```

### 연결 에러

```python
# 연결 테스트
from sqlalchemy import create_engine, text

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.fetchone())
```

### 테이블 초기화

```python
from libs.common.db.session import init_db, get_engine

engine = get_engine()
init_db(engine=engine, drop_all=True)  # 주의: 모든 데이터 삭제
```

---

## 다음 단계

- [ ] Alembic 마이그레이션 설정
- [ ] RDS 프로비저닝 (Terraform)
- [ ] Secrets Manager 통합
- [ ] VPC Endpoint for RDS
- [ ] Read Replica 추가 (읽기 부하 분산)
- [ ] Backup 정책 설정

---

## 참고

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [RDS PostgreSQL Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)

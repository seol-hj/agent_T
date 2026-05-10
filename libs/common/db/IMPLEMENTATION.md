# DB Repository 구현 완료

SQLAlchemy 기반 RDS PostgreSQL 연동 완료.

---

## 구현 내용

### 1. **ORM Models** (models.py, 300+ lines)

13개 테이블 정의:

| 테이블 | 설명 | 주요 필드 |
|--------|------|-----------|
| experiments | 실험 메타데이터 | id, status, created_at, completed_at, error_message |
| user_requests | 사용자 요청 원본 | id, request_text, language, user_id |
| experiment_specs | Orchestrator 출력 | id, spec_json, confidence_score, model_version_id |
| scenarios | 시나리오 계획 | id, experiment_id, scenario_type, plan_json |
| network_artifacts | 네트워크 산출물 | id, scenario_id, variant_id, network_file_uri |
| demand_artifacts | 수요 산출물 | id, scenario_id, variant_id, routes_file_uri |
| simulation_runs | SUMO 실행 기록 | id, experiment_id, variant_id, execution_status, output URIs |
| analysis_results | 분석 결과 | id, experiment_id, result_json, baseline_kpis, comparisons |
| reports | 리포트 산출물 | id, experiment_id, report_type, report_markdown_uri, summary |
| agent_logs | Agent 실행 로그 | id, experiment_id, step_name, tokens_used, execution_time_ms |
| model_versions | LLM 모델 버전 | id, model_name, model_provider, version_tag, is_active |
| prompt_versions | 프롬프트 버전 | id, prompt_name, version_tag, prompt_text, is_active |
| rag_documents | RAG 문서 메타데이터 | id, document_uri, category, tags, content_text |

**특징**:
- Foreign Key 관계 설정 (experiments ↔ scenarios ↔ artifacts)
- JSON 필드로 복잡한 데이터 저장
- 인덱스 자동 생성 (status, created_at, variant_id 등)
- SQLAlchemy Relationship으로 조인 간소화

### 2. **Session Management** (session.py, 150+ lines)

- `get_engine()`: SQLite/PostgreSQL 엔진 생성
- `get_session_factory()`: SessionFactory 생성
- `init_db()`: 테이블 자동 생성
- `setup_database()`: 앱 시작 시 DB 초기화
- `get_global_db()`: FastAPI 의존성 주입용

**환경변수**:
```bash
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

**연결 풀링** (PostgreSQL):
- pool_size: 10
- max_overflow: 20
- pool_pre_ping: True

### 3. **Repository Pattern** (repositories/, 1000+ lines)

13개 Repository 구현:

- `BaseRepository`: 공통 CRUD (create, get, get_all, update, delete, count, exists)
- `ExperimentRepository`: 실험 관리 (get_by_status, get_recent, update_status, get_with_relations)
- `UserRequestRepository`: 사용자 요청 (get_by_user, search_by_text)
- `ExperimentSpecRepository`: 실험 명세 (get_by_model_version, get_high_confidence)
- `ScenarioRepository`: 시나리오 (get_by_experiment, get_by_type)
- `NetworkArtifactRepository`: 네트워크 산출물 (get_by_scenario, get_by_variant)
- `DemandArtifactRepository`: 수요 산출물 (get_by_scenario, get_by_variant)
- `SimulationRunRepository`: 시뮬레이션 실행 (get_by_experiment, get_by_variant, update_status)
- `AnalysisResultRepository`: 분석 결과 (get_by_experiment, get_all_by_experiment)
- `ReportRepository`: 리포트 (get_by_experiment, get_by_type, get_recent)
- `AgentLogRepository`: Agent 로그 (get_by_experiment, get_by_step, get_token_usage, get_average_execution_time)
- `ModelVersionRepository`: 모델 버전 (get_active, get_by_name, activate/deactivate)
- `PromptVersionRepository`: 프롬프트 버전 (get_active, get_by_name, get_active_by_name, activate/deactivate)
- `RAGDocumentRepository`: RAG 문서 (get_active, get_by_category, search_by_text, search_by_title, activate/deactivate)

### 4. **Migrations** (migrations/, placeholder)

현재: `Base.metadata.create_all()` 사용

향후: Alembic 마이그레이션 전환 예정
- `alembic init`
- `alembic revision --autogenerate`
- `alembic upgrade head`

### 5. **Tests** (tests/, 800+ lines)

- `conftest.py`: Pytest fixtures (test_engine, test_session)
- `test_repositories.py`: 13개 Repository 통합 테스트
  - CRUD 작업
  - 필터링 및 검색
  - 관계 조회
  - 통계 계산
- `test_session.py`: Session 관리 테스트
  - SQLite/PostgreSQL 엔진
  - SessionFactory
  - 테이블 초기화

**테스트 실행**:
```bash
pytest libs/common/db/tests/ -v
```

### 6. **Examples** (examples/, 300+ lines)

- `basic_usage.py`: 기본 CRUD 예제 (SQLite 인메모리)
- `fastapi_integration.py`: FastAPI REST API 예제
- `README.md`: 실행 가이드 및 문제 해결

### 7. **Documentation**

- `README.md`: 전체 가이드 (2000+ lines)
  - 테이블 구조
  - 사용법 (기본, FastAPI, 복잡한 쿼리)
  - Repository Pattern 설명
  - 마이그레이션
  - RDS 연결
  - 성능 최적화
  - 로컬 ↔ RDS 전환
- `migrations/README.md`: Alembic 가이드
- `examples/README.md`: 예제 실행 가이드
- `IMPLEMENTATION.md`: 구현 요약 (현재 파일)

---

## 특징

### 1. **Repository Pattern**
- 비즈니스 로직과 데이터 접근 로직 분리
- 테스트 가능성 향상 (Mock Repository)
- 공통 CRUD 로직 재사용

### 2. **Database Agnostic**
- SQLite (로컬 개발/테스트)
- PostgreSQL (프로덕션)
- 환경변수만 변경하면 전환 가능

### 3. **Type Safety**
- SQLAlchemy ORM으로 타입 안전성
- Pydantic과 통합 가능 (FastAPI)

### 4. **Performance**
- 연결 풀링 (PostgreSQL)
- 인덱스 자동 생성
- Lazy/Eager loading 선택 가능

### 5. **Observability**
- Agent 실행 로그 (토큰, 실행 시간)
- 모델/프롬프트 버전 추적
- 실험 상태 추적

---

## 사용 예시

### 기본 CRUD

```python
from libs.common.db.session import setup_database, get_global_db
from libs.common.db.repositories import ExperimentRepository

setup_database()

for db in get_global_db():
    repo = ExperimentRepository(db)
    
    # Create
    exp = repo.create(id="exp_001", status="pending")
    
    # Read
    exp = repo.get("exp_001")
    
    # Update
    exp = repo.update("exp_001", status="running")
    
    # Delete
    repo.delete("exp_001")
```

### FastAPI 통합

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
    return repo.get(exp_id)
```

### 복잡한 쿼리

```python
# 실험별 토큰 사용량
log_repo = AgentLogRepository(db)
total_tokens = log_repo.get_token_usage_by_experiment("exp_001")

# 단계별 평균 실행 시간
avg_time = log_repo.get_average_execution_time_by_step("orchestrator")

# 고신뢰도 실험 명세
spec_repo = ExperimentSpecRepository(db)
high_conf = spec_repo.get_high_confidence(min_confidence=0.9)

# 활성 RAG 문서 (카테고리별)
doc_repo = RAGDocumentRepository(db)
policy_docs = doc_repo.get_by_category("policy")
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
export DATABASE_URL=postgresql://admin:pass@rds.amazonaws.com:5432/agent_t
python -m uvicorn apps.pipeline.main:app
```

코드 변경 없음!

---

## 테스트 실행

```bash
# Repository 테스트
pytest libs/common/db/tests/test_repositories.py -v

# Session 테스트
pytest libs/common/db/tests/test_session.py -v

# 전체 테스트
pytest libs/common/db/tests/ -v
```

---

## 디렉토리 구조

```
libs/common/db/
├── models.py                        # ORM 모델 (13개 테이블)
├── session.py                       # 세션 관리
├── repositories/                    # Repository Pattern
│   ├── __init__.py
│   ├── base_repository.py           # 공통 CRUD
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
├── migrations/                      # Alembic (향후)
│   └── README.md
├── tests/                           # 테스트
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_repositories.py
│   └── test_session.py
├── examples/                        # 예제
│   ├── basic_usage.py
│   ├── fastapi_integration.py
│   └── README.md
├── README.md                        # 전체 가이드
└── IMPLEMENTATION.md                # 구현 요약 (현재 파일)
```

---

## 다음 단계

### 1. RDS 프로비저닝 (Terraform)

```hcl
resource "aws_db_instance" "agent_t" {
  identifier          = "agent-t-prod"
  engine              = "postgres"
  engine_version      = "15.4"
  instance_class      = "db.t3.medium"
  allocated_storage   = 100
  storage_type        = "gp3"
  
  db_name  = "agent_t_prod"
  username = "admin"
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.agent_t.name
  
  backup_retention_period = 7
  skip_final_snapshot     = false
  final_snapshot_identifier = "agent-t-final-snapshot"
}
```

### 2. Secrets Manager 통합

```python
import boto3
import json

def get_db_credentials():
    client = boto3.client('secretsmanager', region_name='ap-northeast-2')
    secret = client.get_secret_value(SecretId='agent-t/db/credentials')
    return json.loads(secret['SecretString'])

credentials = get_db_credentials()
database_url = f"postgresql://{credentials['username']}:{credentials['password']}@{credentials['host']}:{credentials['port']}/{credentials['dbname']}"
setup_database(database_url=database_url)
```

### 3. Alembic 마이그레이션

```bash
alembic init alembic
alembic revision --autogenerate -m "Initial tables"
alembic upgrade head
```

### 4. Read Replica (읽기 부하 분산)

```hcl
resource "aws_db_instance" "agent_t_read_replica" {
  identifier          = "agent-t-read-replica"
  replicate_source_db = aws_db_instance.agent_t.identifier
  instance_class      = "db.t3.medium"
}
```

### 5. VPC Endpoint (PrivateLink)

```hcl
resource "aws_vpc_endpoint" "rds" {
  vpc_id            = aws_vpc.agent_t.id
  service_name      = "com.amazonaws.ap-northeast-2.rds"
  vpc_endpoint_type = "Interface"
  subnet_ids        = aws_subnet.private[*].id
}
```

### 6. 모니터링 (CloudWatch)

- RDS 성능 메트릭
- 슬로우 쿼리 로그
- 연결 수 모니터링
- CPU/메모리 사용률

---

## 요약

✅ **13개 테이블** ORM 모델 정의  
✅ **Repository Pattern** 구현 (13개 Repository)  
✅ **SQLite ↔ PostgreSQL** 전환 가능  
✅ **FastAPI 통합** 예제 및 의존성 주입  
✅ **테스트** 작성 (800+ lines)  
✅ **문서화** 완료 (README, 예제, 가이드)  
✅ **Migration** placeholder (Alembic 향후 전환)  

**다음**: RDS 프로비저닝 → Secrets Manager → Alembic 마이그레이션 → Read Replica

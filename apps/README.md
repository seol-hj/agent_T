# Agent T - Applications

Agent T 플랫폼의 마이크로서비스 애플리케이션 모음

---

## 📁 디렉토리 구조

```
apps/
├── api-service/              # API Gateway (외부 인터페이스)
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── agent-service/            # AI Agent (Orchestrator + Scenario Builder)
│   ├── main.py              # 통합 라우팅
│   ├── orchestrator/        # 전체 흐름 제어
│   │   ├── services/
│   │   ├── prompts/
│   │   └── README.md
│   ├── scenario_builder/    # 자연어 → 실험 명세
│   │   ├── services/
│   │   ├── models/
│   │   └── README.md
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── simulation-service/       # SUMO Simulation (Network + Demand + Runner)
│   ├── main.py              # 통합 라우팅
│   ├── network_builder/     # OSM → SUMO 도로망
│   │   ├── services/
│   │   ├── builders/
│   │   └── README.md
│   ├── demand_builder/      # 교통 수요 생성
│   │   ├── services/
│   │   ├── generators/
│   │   └── README.md
│   ├── runner/              # SUMO 실행
│   │   ├── executors/
│   │   ├── job-runner.py
│   │   └── README.md
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── analysis-service/         # KPI Analysis (Analyzer)
│   ├── main.py              # 통합 라우팅
│   ├── analyzer/            # KPI 추출 및 분석
│   │   ├── services/
│   │   ├── processors/
│   │   └── README.md
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── report-service/           # Report Generation (Reporter)
│   ├── main.py              # 통합 라우팅
│   ├── reporter/            # 정책 리포트 생성
│   │   ├── services/
│   │   ├── templates/
│   │   └── README.md
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── pipeline/                 # E2E Pipeline (개발/테스트용)
│   ├── main.py
│   ├── services/
│   │   └── pipeline_service.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
└── frontend/                 # React UI (향후 구현)
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    ├── vite.config.js
    ├── nginx.conf
    ├── Dockerfile
    └── package.json
```

---

## 🎯 서비스 개요

### 1. api-service (API Gateway)

**역할**: 외부 클라이언트와 내부 서비스 간 라우팅

**엔드포인트**:
- `POST /experiments` - 실험 생성
- `GET /experiments/{id}` - 실험 조회
- `GET /experiments/{id}/status` - 실험 상태 확인

**의존성**: PostgreSQL, Redis, agent-service

---

### 2. agent-service (AI Agent)

**역할**: AI 기반 자연어 처리 및 흐름 제어

**통합 모듈**:
- **orchestrator**: 전체 워크플로우 제어, 모듈 간 라우팅
- **scenario_builder**: 사용자 요청 → 실험 명세 변환

**엔드포인트**:
- `POST /orchestrator/parse` - 사용자 요청 파싱
- `POST /scenario/build` - 시나리오 생성

**의존성**: Bedrock (Claude), LLM Gateway

---

### 3. simulation-service (SUMO Simulation)

**역할**: 교통 시뮬레이션 전체 파이프라인

**통합 모듈**:
- **network_builder**: OpenStreetMap → SUMO 도로망
- **demand_builder**: OD Matrix → 교통 수요 생성
- **runner**: SUMO 시뮬레이션 실행 (Kubernetes Job)

**엔드포인트**:
- `POST /network/build` - 도로망 생성
- `POST /demand/build` - 교통 수요 생성
- `POST /simulation/run` - 시뮬레이션 실행

**의존성**: SUMO, OSM, S3, Kubernetes API

---

### 4. analysis-service (KPI Analysis)

**역할**: 시뮬레이션 결과 분석

**통합 모듈**:
- **analyzer**: KPI 추출, 통계 분석, 변형 비교

**엔드포인트**:
- `POST /analysis/run` - 분석 실행
- `GET /analysis/results/{id}` - 분석 결과 조회

**의존성**: S3 (시뮬레이션 결과), PostgreSQL

---

### 5. report-service (Report Generation)

**역할**: 정책 리포트 생성

**통합 모듈**:
- **reporter**: Markdown/PDF/HTML 리포트 생성

**엔드포인트**:
- `POST /report/generate` - 리포트 생성
- `GET /report/{id}` - 리포트 조회

**의존성**: Bedrock (LLM), S3, KPI 데이터

---

### 6. pipeline (E2E Pipeline)

**역할**: 전체 워크플로우 통합 (개발/테스트용)

**사용처**:
- E2E 테스트
- 로컬 개발 환경
- 데모 및 검증

**엔드포인트**:
- `POST /pipeline/run` - E2E 실행

**참고**: 프로덕션에서는 api-service가 직접 각 서비스 호출

---

### 7. frontend (UI)

**역할**: 사용자 인터페이스 (향후 구현)

**기술 스택**: React + Vite + Nginx

---

## 📊 서비스 매트릭스

| 서비스 | 통합 모듈 | 포트 | 역할 | 상태 |
|--------|-----------|------|------|------|
| **api-service** | - | 8000 | API Gateway | ✅ 구현 |
| **agent-service** | orchestrator + scenario_builder | 8001 | AI Agent | ✅ 통합 완료 |
| **simulation-service** | network + demand + runner | 8005 | SUMO Simulation | ✅ 통합 완료 |
| **analysis-service** | analyzer | 8006 | KPI Analysis | ✅ 통합 완료 |
| **report-service** | reporter | 8007 | Report Generation | ✅ 통합 완료 |
| **pipeline** | - | 8000 | E2E Pipeline | ✅ 구현 |
| **frontend** | - | 3000 | UI | 📝 향후 |

---

## 🚀 빠른 시작

### Docker Compose로 전체 실행

```bash
# 전체 서비스 시작
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f agent-service
```

### 개별 서비스 실행

```bash
# Python 가상환경 설정
cd apps/agent-service
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서비스 실행
python main.py
# 또는
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Health Check

```bash
# 각 서비스 확인
curl http://localhost:8000/health  # api-service
curl http://localhost:8001/health  # agent-service
curl http://localhost:8005/health  # simulation-service
curl http://localhost:8006/health  # analysis-service
curl http://localhost:8007/health  # report-service
```

---

## 🔄 데이터 플로우

```
사용자 요청 (자연어)
    │
    ▼
API Service
    │
    ▼
Agent Service
    ├── Orchestrator (흐름 제어)
    └── Scenario Builder (명세 생성)
        │
        ▼
Simulation Service
    ├── Network Builder (도로망)
    ├── Demand Builder (교통 수요)
    └── Runner (SUMO 실행)
        │
        ▼
Analysis Service
    └── Analyzer (KPI 추출)
        │
        ▼
Report Service
    └── Reporter (리포트 생성)
        │
        ▼
API Service (결과 반환)
```

---

## 🛠️ 개발 가이드

### 새 엔드포인트 추가

```python
# apps/agent-service/main.py

@app.post("/orchestrator/parse")
async def parse_request(request: UserRequest):
    """사용자 요청 파싱"""
    from .orchestrator.services.orchestrator_service import OrchestratorService
    
    orchestrator = OrchestratorService()
    result = await orchestrator.parse(request.user_request)
    return result
```

### 모듈 간 통신

```python
# agent-service에서 simulation-service 호출
import httpx

async def call_simulation_service(config: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://simulation-service:8005/simulation/run",
            json=config
        )
        return response.json()
```

### 환경 변수 설정

```python
# apps/agent-service/main.py
import os

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "bedrock")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
```

**Helm values**:
```yaml
# infra/helm/services/agent-service/values-dev.yaml
env:
  LLM_PROVIDER: "bedrock"
  LLM_MODEL_ID: "anthropic.claude-3-5-sonnet-20241022-v2:0"
```

---

## 🧪 테스트

### 단위 테스트

```bash
# 특정 서비스 테스트
cd apps/agent-service
pytest tests/ -v

# 커버리지
pytest tests/ --cov=. --cov-report=html
```

### 통합 테스트

```bash
# Docker Compose로 서비스 시작
docker-compose up -d

# E2E 테스트 실행
./scripts/test-services-local.sh
```

---

## 📦 배포

### CI/CD 흐름

1. **Git Push** → `develop` 브랜치
2. **GitHub Actions** → Docker 빌드 & ECR Push
3. **Argo CD** → Helm Chart 동기화 & EKS 배포
4. **Health Check** → Ready

### 수동 배포 (개발 환경)

```bash
# Docker 이미지 빌드
docker build -t agent-service:dev apps/agent-service/

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com

# 태그 & Push
docker tag agent-service:dev <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/agent-service:sha-abc123
docker push <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/agent-service:sha-abc123

# Kubernetes 배포
helm upgrade --install agent-service infra/helm/services/agent-service \
  --values infra/helm/services/agent-service/values-dev.yaml \
  --set image.tag=sha-abc123
```

---

## 🔧 문제 해결

### 서비스 간 통신 실패

```bash
# Kubernetes 환경에서 DNS 확인
kubectl exec -it <pod-name> -- nslookup simulation-service

# Service 확인
kubectl get svc

# 포트 확인
kubectl describe svc simulation-service
```

### 모듈 import 오류

```python
# 통합 후 import 경로 변경
# Before
from orchestrator.services import OrchestratorService

# After
from agent_service.orchestrator.services.orchestrator_service import OrchestratorService
```

### Docker 빌드 실패

```bash
# 캐시 없이 재빌드
docker-compose build --no-cache agent-service

# 빌드 로그 상세 확인
docker-compose build agent-service 2>&1 | tee build.log
```

---

## 📚 참고 문서

- [서비스 상세 문서](../docs/services.md)
- [GitOps 배포](../docs/gitops.md)
- [CI/CD 파이프라인](../docs/cicd.md)
- [환경 재구축](../docs/rebuild-environment.md)
- [정리 계획](../CLEANUP_PLAN.md)

---

## 📝 변경 이력

### 2026-05-07: 서비스 통합

**Before (14개 서비스)**:
- api-service, frontend, pipeline
- orchestrator, scenario-builder (독립)
- network-builder, demand-builder, simulator-runner (독립)
- analyzer (독립)
- reporter (독립)
- agent-service, simulation-service, analysis-service, report-service (Placeholder)

**After (7개 서비스)**:
- api-service, frontend, pipeline (유지)
- agent-service (orchestrator + scenario-builder 통합)
- simulation-service (network + demand + runner 통합)
- analysis-service (analyzer 통합)
- report-service (reporter 통합)

**이유**: 
- 서비스 개수 감소 (14 → 7)
- 배포 단위 명확화
- CLAUDE.md 초기 설계 준수
- 중복 제거 및 유지보수성 향상

---

**버전**: 0.2.0 (통합 완료)  
**최종 업데이트**: 2026-05-07

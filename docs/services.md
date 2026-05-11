# 서비스 구조

Agent T 플랫폼의 마이크로서비스 구조 및 각 서비스 설명

---

## 개요

Agent T는 **6개의 마이크로서비스**로 구성된다:

```
┌─────────────┐
│  Frontend   │ ← 사용자 인터페이스
└──────┬──────┘
       │
┌──────▼──────┐
│ API Service │ ← 실험 관리 및 오케스트레이션
└──────┬──────┘
       │
       ├──────────────────┬──────────────────┬──────────────────┐
       │                  │                  │                  │
┌──────▼──────┐  ┌────────▼────────┐  ┌─────▼──────┐  ┌──────▼──────┐
│   Agent     │  │  Simulation     │  │  Analysis  │  │   Report    │
│  Service    │  │    Service      │  │  Service   │  │  Service    │
└─────────────┘  └─────────────────┘  └────────────┘  └─────────────┘
LLM 자연어 처리   SUMO 시뮬레이션      KPI 분석        정책 리포트
```

---

## 서비스 목록

### 1. Frontend

**역할**: 사용자 인터페이스

**기술 스택**:
- React 18 + Vite
- Nginx (production)

**포트**: 3000

**엔드포인트**:
- `/` - 메인 페이지 (서비스 상태 대시보드)
- `/health` - Health check

**특징**:
- SPA (Single Page Application)
- Nginx에서 백엔드 API로 프록시
- Kubernetes 내부에서 Service 이름으로 라우팅

**파일 구조**:
```
apps/frontend/
├── src/
│   ├── App.jsx          # 메인 컴포넌트
│   ├── App.css          # 스타일
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── index.html
├── vite.config.js       # Vite 설정
├── nginx.conf           # Nginx 설정 (API 프록시)
├── Dockerfile           # Multi-stage build
└── package.json
```

---

### 2. API Service

**역할**: 실험 관리 및 전체 워크플로우 오케스트레이션

**기술 스택**:
- Python 3.11 + FastAPI

**포트**: 8000

**엔드포인트**:
| Method | Path | 설명 |
|---|---|---|
| GET | `/` | 서비스 정보 |
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe |
| GET | `/api/experiments` | 실험 목록 (placeholder) |
| POST | `/api/experiments` | 실험 생성 (TODO) |
| GET | `/docs` | Swagger UI |

**책임**:
1. 실험 생성 요청 수신
2. Agent Service 호출 (시나리오 생성)
3. Simulation Service 호출 (시뮬레이션 실행)
4. Analysis Service 호출 (결과 분석)
5. Report Service 호출 (리포트 생성)
6. 상태 관리 및 모니터링

**파일 구조**:
```
apps/api-service/
├── main.py              # FastAPI 앱
├── requirements.txt     # Python 의존성
├── Dockerfile
└── .dockerignore
```

**다음 단계**:
- PostgreSQL 연결 (실험 메타데이터 저장)
- Redis 캐시 (상태 관리)
- S3 통합 (시나리오 파일 저장)
- 워크플로우 오케스트레이션 로직

---

### 3. Agent Service

**역할**: LLM 기반 자연어 처리 및 시나리오 생성

**기술 스택**:
- Python 3.11 + FastAPI

**포트**: 8000

**엔드포인트**:
| Method | Path | 설명 |
|---|---|---|
| GET | `/` | 서비스 정보 |
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe |
| POST | `/agent/chat` | 채팅 (placeholder) |
| POST | `/agent/scenario` | 시나리오 생성 (TODO) |
| GET | `/docs` | Swagger UI |

**책임**:
1. 자연어 요구사항 해석
2. LLM Gateway 호출 (Bedrock/Claude)
3. 실험 명세(JSON/YAML) 생성
4. 시나리오 검증

**파일 구조**:
```
apps/agent-service/
├── main.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

**다음 단계**:
- LLM Gateway 통합
- Prompt Engineering (시나리오 생성)
- Vector DB 통합 (RAG)
- 시나리오 템플릿 관리

---

### 4. Simulation Service

**역할**: SUMO 기반 교통 시뮬레이션 실행

**기술 스택**:
- Python 3.11 + FastAPI
- SUMO (향후 추가)

**포트**: 8000

**엔드포인트**:
| Method | Path | 설명 |
|---|---|---|
| GET | `/` | 서비스 정보 |
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe |
| POST | `/simulation/run` | 시뮬레이션 실행 (placeholder) |
| GET | `/simulation/status/{id}` | 상태 조회 (placeholder) |
| GET | `/docs` | Swagger UI |

**책임**:
1. OSM → SUMO 도로망 변환 (Network Builder)
2. 교통 수요 생성 (Demand Builder)
3. SUMO 시뮬레이션 실행
4. 결과 파일 S3 업로드

**파일 구조**:
```
apps/simulation-service/
├── main.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

**다음 단계**:
- SUMO 설치 및 통합
- OSM → SUMO 변환 로직 (netconvert)
- 교통 수요 생성 (randomTrips.py, duarouter)
- S3 결과 저장
- 비동기 작업 큐 (Celery?)

---

### 5. Analysis Service

**역할**: 시뮬레이션 결과 분석 및 KPI 추출

**기술 스택**:
- Python 3.11 + FastAPI
- Pandas, NumPy (데이터 분석)

**포트**: 8000

**엔드포인트**:
| Method | Path | 설명 |
|---|---|---|
| GET | `/` | 서비스 정보 |
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe |
| POST | `/analysis/run` | 분석 실행 (placeholder) |
| GET | `/analysis/results/{id}` | 결과 조회 (placeholder) |
| GET | `/docs` | Swagger UI |

**책임**:
1. SUMO 출력 파일 파싱 (tripinfo.xml, summary.xml)
2. KPI 계산:
   - 평균 통행 시간
   - 평균 대기 시간
   - 평균 속도
   - 총 통행량
   - 배출량 (CO2, NOx)
3. 통계 분석 및 시각화 데이터 생성

**파일 구조**:
```
apps/analysis-service/
├── main.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

**다음 단계**:
- SUMO XML 파서
- KPI 계산 로직
- 시각화 데이터 생성 (차트용)
- PostgreSQL 결과 저장

---

### 6. Report Service

**역할**: 정책 리포트 자동 생성

**기술 스택**:
- Python 3.11 + FastAPI
- LLM Gateway (리포트 생성)

**포트**: 8000

**엔드포인트**:
| Method | Path | 설명 |
|---|---|---|
| GET | `/` | 서비스 정보 |
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe |
| POST | `/reports/generate` | 리포트 생성 (placeholder) |
| GET | `/reports/{id}` | 리포트 조회 (placeholder) |
| GET | `/docs` | Swagger UI |

**책임**:
1. 분석 결과 수신
2. LLM Gateway 호출 (정책 리포트 생성)
3. 리포트 포맷팅 (Markdown, PDF)
4. S3 업로드

**파일 구조**:
```
apps/report-service/
├── main.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

**다음 단계**:
- LLM Gateway 통합
- 리포트 템플릿 관리
- PDF 생성 (WeasyPrint?)
- S3 업로드

---

## 공통 사항

### Health Check

모든 서비스는 다음 엔드포인트를 제공한다:

- `GET /health`: Liveness probe (서비스 실행 여부)
- `GET /ready`: Readiness probe (의존성 준비 완료 여부)

Kubernetes Deployment에서 사용:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

### 환경 변수

각 서비스는 환경 변수를 통해 설정을 받는다:

**공통**:
- `ENV`: 환경 (dev, prod)
- `LOG_LEVEL`: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
- `AWS_REGION`: AWS 리전

**서비스별**:
- API Service: `DATABASE_URL`, `REDIS_URL`, `S3_BUCKET_SCENARIOS`
- Agent Service: `LLM_GATEWAY_URL`, `VECTOR_DB_URL`
- Simulation Service: `SUMO_HOME`, `S3_BUCKET_SIMULATIONS`
- Analysis Service: `S3_BUCKET_SIMULATIONS`, `DATABASE_URL`
- Report Service: `LLM_GATEWAY_URL`, `S3_BUCKET_REPORTS`

### Dockerfile 패턴

모든 Python 서비스는 동일한 Dockerfile 패턴을 따른다:

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 코드 복사
COPY . .

# 비root 사용자
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Frontend는 multi-stage build:
1. Node.js 빌드 (npm run build)
2. Nginx 서빙 (dist/ 복사)

---

## 로컬 테스트

### 개별 서비스 실행

```bash
# Python 서비스
cd apps/api-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend
cd apps/frontend
npm install
npm run dev
```

### Docker 빌드 및 실행

```bash
# 개별 서비스
cd apps/api-service
docker build -t api-service:local .
docker run -p 8000:8000 api-service:local

# 모든 서비스 테스트
./scripts/test-services-local.sh
```

### Health Check 확인

```bash
# API Services
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health

# Frontend
curl http://localhost:3000/health
```

---

## 배포 흐름

### 1. 로컬 개발

```bash
# 코드 수정
vi apps/api-service/main.py

# 로컬 테스트
cd apps/api-service
python main.py

# Docker 빌드 테스트
docker build -t api-service:local .
```

### 2. Git Push

```bash
git add apps/api-service/
git commit -m "feat(api): add experiment creation endpoint"
git push origin develop
```

### 3. CI (GitHub Actions)

- Path filtering: `apps/api-service/**` 변경 감지
- Docker 빌드
- ECR Push: `agent-t-dev/api-service:sha-a1b2c3d`
- Helm values 업데이트 (TODO)

### 4. CD (Argo CD)

- Git 변경 감지 (3분 polling)
- Helm Chart 동기화
- EKS Pod 배포
- Health check 통과 시 트래픽 전환

### 5. 확인

```bash
# Argo CD UI
kubectl port-forward -n argocd svc/argocd-server 8080:443
open https://localhost:8080

# Pod 상태
kubectl get pods
kubectl logs -f <pod-name>

# Ingress 확인
kubectl get ingress
kubectl describe ingress gateway
```

---

## 참고 문서

- [GitOps with Argo CD](./gitops.md)
- [CI/CD Pipeline](./cicd.md)
- [EKS 클러스터 관리](./eks.md)
- [환경 재구성 가이드](./troubleshooting.md)

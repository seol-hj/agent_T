# AI Agent T

AI 에이전트 기반 교통 시뮬레이션 지능화 플랫폼

사용자의 자연어 요청을 AI가 해석하여 SUMO 교통 시뮬레이션을 자동으로 실행하고 정책 리포트를 생성합니다.

---

## 🎯 프로젝트 개요

```
사용자 자연어 입력
    ↓
AI 에이전트 (Claude 3.5 Sonnet)
    ↓
시나리오 생성 → OSM 도로망 → SUMO 시뮬레이션 → KPI 분석 → 정책 리포트
```

**핵심 기능**:
- 🤖 자연어로 시뮬레이션 요청 ("강남역 일대 교통량 20% 증가 시 영향 분석")
- 🗺️ OpenStreetMap 기반 자동 도로망 생성
- 🚗 SUMO 시뮬레이터 실행
- 📊 실시간 진행률 모니터링 (웹 UI)
- 📈 KPI 분석 및 정책 리포트 자동 생성

---

## 🚀 빠른 시작

### 1️⃣ 로컬 테스트 (5분)

Docker Compose로 전체 시스템을 로컬에서 실행:

```bash
# 1. 레포지토리 클론
git clone https://github.com/<your-org>/agent-t.git
cd agent-t

# 2. Docker Compose 실행
docker compose up --build

# 3. 프론트엔드 접속
open http://localhost:3000

# 4. 테스트 스크립트 실행 (별도 터미널)
./scripts/test-services-local.sh
```

**로컬 환경 구성**:
- 6개 서비스 (pipeline, agent, simulation, analysis, report, frontend)
- PostgreSQL 15 (파이프라인 상태 추적)
- Mock LLM (하드코딩 응답)
- Local Storage (/data 볼륨)

📖 **상세 가이드**: [QUICKSTART.md](./QUICKSTART.md)

---

### 2️⃣ AWS 배포 (30분)

Terraform + EKS로 프로덕션 환경 배포:

```bash
# 1. AWS 인증
aws configure

# 2. 전체 인프라 구축 (VPC, EKS, RDS, S3, Bedrock)
cd infra/terraform/envs/dev
terraform init
terraform apply

# 3. EKS 클러스터 접속
aws eks update-kubeconfig --name agent-t-dev --region ap-northeast-2

# 4. 서비스 배포 (Argo CD)
kubectl apply -f infra/argocd/applications/dev/

# 5. ALB URL 접속
kubectl get ingress -n agent-t
```

**AWS 환경 구성**:
- EKS Cluster (Kubernetes)
- RDS PostgreSQL 15 (Multi-AZ)
- S3 (시뮬레이션 결과 저장)
- Amazon Bedrock (Claude 3.5 Sonnet)
- ALB + CloudWatch

📖 **상세 가이드**: [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 📂 프로젝트 구조

```
agent-t/
├── apps/                      # 마이크로서비스
│   ├── pipeline/              # E2E 파이프라인 오케스트레이터
│   ├── agent-service/         # AI 에이전트 (Scenario Builder)
│   ├── simulation-service/    # SUMO 시뮬레이션
│   ├── analysis-service/      # KPI 분석
│   ├── report-service/        # 리포트 생성
│   └── frontend/              # Next.js 14 웹 UI
├── libs/                      # 공통 라이브러리
│   └── common/
│       ├── gateways/          # LLM/Storage Gateway 추상화
│       └── schemas/           # Pydantic 스키마
├── infra/                     # Infrastructure as Code
│   ├── terraform/             # AWS 리소스 (VPC, EKS, RDS, S3)
│   ├── helm/                  # Kubernetes Helm Charts
│   └── argocd/                # GitOps 배포 설정
├── scripts/                   # 자동화 스크립트
├── docs/                      # 상세 문서
├── docker-compose.yaml        # 로컬 개발 환경
├── QUICKSTART.md              # 로컬 테스트 가이드
├── DEPLOYMENT.md              # AWS 배포 가이드
└── README.md                  # 이 파일
```

---

## 🏗️ 아키텍처

### 서비스 구성

| 서비스 | 포트 | 역할 |
|--------|------|------|
| **Frontend** | 3000 | Next.js 14 웹 UI, 실시간 모니터링 |
| **API Service** | 8000 | RESTful API Gateway |
| **Agent Service** | 8000 | AI 에이전트, 시나리오 생성 (Orchestrator 통합) |
| **Simulation Service** | 8000 | OSM → SUMO 네트워크 + 수요 + 실행 (통합) |
| **Analysis Service** | 8000 | KPI 분석 (통행 시간, 속도, 혼잡도) |
| **Report Service** | 8000 | 정책 리포트 생성 (AI 요약) |

**Note**: 모든 백엔드 서비스는 표준 포트 8000 사용 (ClusterIP로 격리)

### 기술 스택

**Backend**:
- Python 3.11, FastAPI, Pydantic
- PostgreSQL 15 (RDS)
- SQLAlchemy 2.0 (async)
- HTTPX (비동기 HTTP 클라이언트)

**Frontend**:
- Next.js 14 (App Router)
- React 18, TypeScript 5
- TailwindCSS + shadcn/ui
- React Query (TanStack Query v5)

**Infrastructure**:
- AWS EKS (Kubernetes)
- Terraform (IaC)
- Argo CD (GitOps)
- GitHub Actions (CI)
- Docker + ECR

**AI/Storage**:
- Amazon Bedrock (Claude 3.5 Sonnet)
- S3 (파일 저장)
- LLM/Storage Gateway 추상화 (교체 가능)

---

## 📊 실행 흐름

**단계별 처리**:
1. **Scenario Building**: 자연어 → 실험 명세 (위치, 파라미터)
2. **Network Building**: OpenStreetMap → SUMO 도로망 (.net.xml)
3. **Demand Building**: 교통 수요 생성 (.rou.xml)
4. **Simulation**: SUMO 실행 → 결과 파일 (tripinfo.xml, summary.xml)
5. **Analysis**: KPI 추출 (평균 통행 시간, 속도, 혼잡도)
6. **Report**: AI 기반 정책 리포트 생성

---

## 🧪 테스트

### 로컬 테스트

```bash
# Docker Compose 실행
docker compose up --build

# 별도 터미널에서 테스트
./scripts/test-services-local.sh
```

**테스트 항목**:
- Health Check (모든 서비스)
- 시나리오 빌드
- 네트워크/수요 생성 (placeholder)
- E2E 파이프라인 실행
- 진행률 API 동작 확인

---

## 📖 문서

### 시작하기
- **[QUICKSTART.md](./QUICKSTART.md)** - 로컬 Docker Compose 테스트
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - AWS 배포 전체 가이드

### 참고 문서 (docs/)
- **[architecture.md](./docs/architecture.md)** - 시스템 아키텍처 상세
- **[services.md](./docs/services.md)** - 각 서비스 API 명세
- **[cicd.md](./docs/cicd.md)** - CI/CD 파이프라인
- **[troubleshooting.md](./docs/troubleshooting.md)** - 문제 해결
- **[contributing.md](./docs/contributing.md)** - 개발 기여 가이드
- **[EXTERNAL-ACCESS-GUIDE.md](./docs/EXTERNAL-ACCESS-GUIDE.md)** - 외부 접속 설정
- **[ARCHITECTURE-COMPLIANCE.md](./docs/ARCHITECTURE-COMPLIANCE.md)** - 아키텍처 준수 점검
- **[ARCHIVE-INDEX.md](./docs/ARCHIVE-INDEX.md)** - 보관 파일 목록

### 프로젝트 규칙
- **[CLAUDE.md](./CLAUDE.md)** - Claude Code를 위한 프로젝트 가이드라인

---

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

📖 [기여 가이드](./docs/contributing.md)

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

---

## 🔗 링크

- **GitHub**: https://github.com/<your-org>/agent-t
- **Issues**: https://github.com/<your-org>/agent-t/issues
- **SUMO**: https://sumo.dlr.de/
- **Amazon Bedrock**: https://aws.amazon.com/bedrock/

---

**버전**: 1.0.0  
**최종 업데이트**: 2026-05-11  
**상태**: ✅ Production Ready - 모든 서비스 정상 작동, 외부 접속 가능

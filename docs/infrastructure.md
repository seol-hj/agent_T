# Infrastructure

## 결정된 스택 (재논의 금지)

| 영역 | 선택 | 근거 |
|---|---|---|
| IaC | **Terraform** | 광범위한 AWS 커버리지, 팀 친숙도, state 격리 |
| 오케스트레이션 | **EKS** | 관리형 control plane, IRSA, ALB Controller 통합 |
| Ingress | **AWS Load Balancer Controller + ALB** | NGINX Ingress 대체 — TLS·WAF·OIDC를 ALB에서 처리, NLB가 필요한 경우만 NLB |
| CI | **GitHub Actions** | OIDC로 AWS 자격증명, 무료 티어 충분 |
| CD | **Argo CD** | 선언적 GitOps, drift 감지·자동 동기화 |
| 컨테이너 레지스트리 | **ECR** | EKS와 IRSA 통합, Image Scan |
| RDB | **RDS PostgreSQL** | 메타데이터·KPI 시계열 |
| 캐시/큐 | **ElastiCache Redis** | 단기 컨텍스트, 작업 큐 후보 |
| 객체 저장소 | **S3** | 도로망/수요/시뮬레이션 산출물·리포트 |
| 시크릿 | **AWS Secrets Manager** | DB 자격증명, 외부 API 키 |
| LLM | **Bedrock (LLM Gateway 경유)** | 다중 모델, IRSA로 키 없이 호출 |

## 네트워크

- **단일 VPC, 다중 AZ**
  - dev: 2 AZ
  - prod: 3 AZ
- 서브넷 분류:
  - public — ALB, NAT
  - private — EKS 노드, 서비스
  - intra (NAT 없음) — RDS, Redis, VPC Endpoints
- **VPC Endpoint 적극 활용** (NAT 비용·외부 노출 감소):
  - Gateway endpoint: S3, DynamoDB
  - Interface endpoint: ECR(api/dkr), STS, Secrets Manager, Logs, EKS, Bedrock 등

## EKS

- Managed node group (general workload용)
- 별도 노드그룹: SUMO 시뮬레이션용 (CPU/메모리 큰 인스턴스, taint 적용)
- Add-ons:
  - AWS Load Balancer Controller
  - External DNS
  - EBS CSI / EFS CSI (필요 시)
  - Cluster Autoscaler (또는 Karpenter — 추후 결정)
  - Argo CD
  - External Secrets Operator (Secrets Manager → K8s Secret)

## Terraform 구조

```
infra/terraform/
├── envs/
│   ├── dev/    # 진입점: versions, providers, variables, locals, main, outputs
│   │          # + terraform.tfvars.example
│   └── prod/   # dev 와 같은 파일 구성, 다른 기본값
└── modules/
    ├── vpc/             ── 3단계 구현
    ├── vpc-endpoints/   ── 3단계
    ├── ecr/             ── 4단계
    ├── s3/              ── 4단계
    ├── rds/             ── 4단계
    ├── redis/           ── 4단계
    ├── secrets-manager/ ── 4단계
    ├── bedrock/         ── 4단계
    ├── eks/             ── 5단계
    ├── iam-irsa/        ── 5단계
    ├── alb-controller/  ── 5단계
    └── argocd/          ── 5단계
```

각 환경은 같은 모듈 셋을 호출한다. 환경 차이는 `terraform.tfvars` + 모듈 내부 분기로만 표현.

### 파일 분리 규약 (envs/<env>/)

| 파일 | 내용 |
|---|---|
| `versions.tf`           | terraform / provider 버전 핀, backend stub |
| `providers.tf`          | aws / kubernetes / helm provider 설정 |
| `variables.tf`          | 환경 입력 변수 (project_name, env, region, vpc_cidr, azs, tags) |
| `locals.tf`             | name_prefix, common_tags |
| `main.tf`               | 모든 모듈 wiring (단계별 활성화 표시) |
| `outputs.tf`            | 외부에서 의존할 안정적 출력 키 |
| `terraform.tfvars.example` | tfvars 템플릿 (실제 tfvars 는 .gitignore) |

## State backend

- **S3** (버전관리 on, SSE) + **DynamoDB** (lock 테이블)
- envs/<env>/versions.tf 의 `backend "s3"` 블록은 **현재 주석 처리**
- 부트스트랩 절차로 백엔드 리소스 생성 후 활성화 → `terraform init -migrate-state`

## 추상화 원칙

비즈니스 로직은 AWS SDK를 **직접 사용하지 않는다.**

```
apps/agent-service           apps/report-service
        │                            │
        ▼                            ▼
   LLMGateway                   StorageProvider
        │                            │
        ▼                            ▼
   BedrockAdapter               S3Adapter
   (교체 가능: Local LLM,        (교체 가능: GCS, MinIO, …)
    fine-tuned)
```

이 계층 덕분에:
- 통합 테스트에서 Mock으로 교체 가능
- 자체 호스팅 LLM 도입 시 비즈니스 로직 변경 0
- 멀티 클라우드 검토 시 마이그레이션 비용 최소화

## 운영 규칙

- 이미지 태그는 **명시적 버전** (커밋 SHA 또는 SemVer). `latest` 사용 금지.
- 시크릿은 **Git에 커밋 금지**. Secrets Manager 또는 .env.example 템플릿만.
- 모든 stateful 리소스는 prod에서 **삭제 보호 on**.
- prod에서 RDS Multi-AZ, 자동 백업 30일, 시점 복구 활성.

## Terraform 실행 순서

> 각 단계는 **이전 단계가 통과한 뒤에만** 실행한다. 2단계 skeleton 시점에는 init/validate/plan 만 실행해 구조를 검증한다.

### A. 사전 준비 (1회)

```bash
# 1. AWS 자격증명 확인
aws sts get-caller-identity

# 2. 도구 점검
./scripts/check-env.sh
```

### B. State backend 부트스트랩 (1회, 추후 단계에서 자동화)

S3 버킷 + DynamoDB 락 테이블을 먼저 만든다. 이 자체를 Terraform 으로 만들면 "닭과 달걀" 문제가 생기므로 보통은 별도 디렉터리(`infra/terraform/_bootstrap/`)나 `aws cli` 직접 호출로 처리한다 — **추후 단계에서 스크립트화**.

```bash
# 예정: ./scripts/bootstrap-tf-backend.sh dev
```

생성 후, `envs/<env>/versions.tf` 의 `backend "s3"` 주석 해제 + `terraform init -migrate-state`.

### C. 환경별 실행 (현재 단계에서 가능한 범위)

```bash
cd infra/terraform/envs/dev

# 실제 값으로 채운 tfvars 준비 (실파일은 .gitignore 됨)
cp terraform.tfvars.example terraform.tfvars
$EDITOR terraform.tfvars

# 1) 초기화 — 모듈 다운로드, provider 다운로드, lock 파일 생성
terraform init

# 2) 포맷·검증 — skeleton 단계의 통과 기준
terraform fmt -recursive -check
terraform validate

# 3) plan — skeleton 단계에서는 "0 to add, 0 to change, 0 to destroy" 가 정상
terraform plan -out=plan.out

# 4) (3·4·5단계 이후) apply
# terraform apply plan.out
```

### D. 단계별 활성화

| 단계 | 활성화되는 모듈 | 주요 산출물 |
|---|---|---|
| 3 | `vpc`, `vpc-endpoints` | VPC, subnet, NAT, VPC Endpoint |
| 4 | `ecr`, `s3`, `rds`, `redis`, `secrets-manager`, `bedrock` | 데이터/보안 리소스 |
| 5 | `eks`, `iam-irsa`, `alb-controller`, `argocd` | 클러스터 + 부가 컴포넌트 |

각 단계에서:
1. 해당 모듈의 `main.tf` 에 리소스 정의 추가
2. `envs/<env>/main.tf` 에서 cross-module 인풋(vpc_id 등) 연결
3. `envs/<env>/outputs.tf` 의 해당 단계 주석 해제
4. `terraform plan` 으로 차이 확인 → `terraform apply`

### E. 환경 파괴

```bash
cd infra/terraform/envs/dev
terraform destroy
```

prod 는 stateful 리소스에 삭제 보호가 켜져 있어 추가 절차 필요.

## 단계별 구체화

이 문서는 2~5단계가 진행되면서 점진적으로 구체 값(인스턴스 타입, CIDR, 서브넷 사이즈, 모듈 입출력 등)이 채워진다.

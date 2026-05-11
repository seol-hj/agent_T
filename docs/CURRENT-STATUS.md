# 현재 상태 및 다음 작업

**최종 업데이트**: 2026-05-11  
**전체 완성도**: 90% (인프라), 70% (애플리케이션)  
**즉시 실행 가능**: ✅ Yes (Route 53 설정 대기)

---

## 📊 완성도 요약

| 계층 | 완성도 | 상태 |
|------|--------|------|
| 인프라 (Terraform) | 100% | ✅ 완료 |
| 플랫폼 (ALB, Argo CD) | 100% | ✅ 완료 |
| CI/CD (GitHub Actions) | 100% | ✅ 완료 |
| 배포 설정 (Helm, GitOps) | 100% | ✅ 완료 |
| 외부 접속 | 80% | ⏳ Route 53 대기 |
| 애플리케이션 로직 | 30% | 🚧 진행 중 |
| 모니터링 | 0% | ❌ 미구현 |

---

## ✅ 완료된 작업

### 인프라 (Terraform)
- VPC, Subnets, NAT Gateway, Internet Gateway
- EKS Cluster + Managed Node Groups
- RDS PostgreSQL, ElastiCache Redis
- S3 Buckets (4개), ECR Repositories (7개)
- Secrets Manager, IAM IRSA
- VPC Endpoints (S3, ECR, Secrets Manager 등)
- AWS Load Balancer Controller IAM Policy
- Bedrock IAM Policy

### 플랫폼 컴포넌트
- AWS Load Balancer Controller (Helm)
- Argo CD (Helm)

### 애플리케이션 구조
- Helm Charts (infra/helm/services/)
  - frontend, api-service, agent-service, simulation-service, analysis-service, report-service
- Argo CD Applications (infra/argocd/applications/dev/)
- GitHub Actions CI/CD (이미지 빌드 & Helm values 업데이트)

### 보안 설정
- Argo CD ingress: `internet-facing` → `disabled` (port-forward 사용)
- Frontend ingress: `internet-facing` (외부 접속 허용)

---

## 📋 실행 대기 중

### 1. Argo CD 재배포 (Internal로 변경)
```bash
kubectl delete ingress -n argocd argocd-server 2>/dev/null || true
cd scripts
./install-platform.sh
```

### 2. Frontend 배포 및 ALB 생성
```bash
# Argo CD가 자동 배포
# 또는 수동:
helm upgrade --install frontend infra/helm/services/frontend \
  -f infra/helm/services/frontend/values.yaml \
  -f infra/helm/services/frontend/values-dev.yaml \
  --namespace agent-t \
  --create-namespace
```

### 3. ALB DNS 확인 후 Route 53 설정
```bash
# ALB DNS 확인
kubectl get ingress -n agent-t frontend \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# 다른 계정에서 Route 53 A 레코드 생성
# seolphung.com → k8s-agentt-frontend-xxx.ap-northeast-2.elb.amazonaws.com
```

---

## 🏗️ 아키텍처

### 인프라 vs 애플리케이션 분리

| 영역 | 도구 | 변경 빈도 | 파일 위치 |
|------|------|-----------|-----------|
| **인프라** | Terraform | 낮음 (주 1회 이하) | `infra/terraform/` |
| **애플리케이션** | Helm + Argo CD | 높음 (일 수십 회) | `infra/helm/services/` |
| **CI** | GitHub Actions | 코드 푸시마다 | `.github/workflows/` |
| **CD** | Argo CD | Git 변경 감지 (30초) | `infra/argocd/` |

### CI/CD 파이프라인

```
[개발자] git push
    ↓
[GitHub Actions]
    ├─ 테스트 실행
    ├─ 이미지 빌드
    ├─ ECR 푸시 (sha-abc123)
    └─ values-dev.yaml 업데이트 (image.tag)
    ↓
[Argo CD] (자동, 3분 이내)
    ├─ Git 폴링 (30초마다)
    ├─ 변경 감지
    └─ Helm sync → EKS 배포
```

### 네트워크 접근

```
[외부 인터넷]
    ↓
[ALB - internet-facing]
    ↓
seolphung.com → Frontend Service (agent-t namespace)

[VPN / Port-forward만]
    ↓
Argo CD (argocd namespace)
```

---

## 📁 주요 파일 구조

```
agent-t/
├── infra/
│   ├── terraform/              # 인프라 (AWS 리소스)
│   │   ├── modules/
│   │   └── envs/dev/
│   │
│   ├── helm/
│   │   ├── platform/           # Argo CD 등
│   │   │   └── argocd/
│   │   │       └── values-dev.yaml  # ingress.enabled=false
│   │   │
│   │   └── services/           # 애플리케이션 Helm Charts
│   │       ├── frontend/
│   │       │   ├── Chart.yaml
│   │       │   ├── values.yaml       # ingress.enabled=true
│   │       │   ├── values-dev.yaml   # image.tag (CI가 업데이트)
│   │       │   └── templates/
│   │       │       ├── deployment.yaml
│   │       │       ├── service.yaml
│   │       │       └── ingress.yaml  # 신규 추가
│   │       ├── api-service/
│   │       └── agent-service/
│   │
│   └── argocd/
│       └── applications/dev/
│           └── frontend.yaml   # Argo CD Application
│
├── apps/                       # 애플리케이션 소스 코드
│   ├── frontend/
│   ├── api-service/
│   └── agent-service/
│
├── .github/workflows/          # CI/CD
│   ├── ci-frontend.yml
│   └── build-and-push.yml      # yq로 values-dev.yaml 업데이트
│
└── scripts/
    ├── bootstrap-dev.sh
    └── install-platform.sh
```

---

## 🔧 GitHub Actions 동작

### build-and-push.yml
```yaml
1. 이미지 빌드 & ECR 푸시
   - 태그: sha-abc123

2. Helm values 업데이트
   - yq eval ".image.tag = \"sha-abc123\"" -i infra/helm/services/frontend/values-dev.yaml

3. Git commit & push
   - commit message: "chore(helm): update frontend image to sha-abc123"

4. Argo CD가 자동 감지 → 배포
```

---

## 🚀 실무 표준

### ✅ 권장
1. **Argo CD는 내부 전용**
   - Port-forward 사용: `kubectl port-forward -n argocd svc/argocd-server 8080:80`
   - 또는 Internal ALB + VPN

2. **Frontend는 외부 노출**
   - Public ALB (internet-facing)
   - 도메인 연결 (seolphung.com)

3. **모든 배포는 Git을 거침**
   - GitHub Actions → values.yaml 업데이트 → Git push
   - Argo CD → Git 감지 → 자동 배포
   - kubectl 수동 변경 금지 (Argo CD가 되돌림)

4. **인프라 변경은 Pull Request**
   - Terraform 변경 → PR → 리뷰 → terraform apply

### ❌ 안티패턴
1. Argo CD를 internet-facing으로 노출 ❌
2. kubectl apply로 직접 배포 ❌
3. Terraform으로 Kubernetes 리소스 관리 ❌
4. GitHub Actions에서 kubectl 직접 실행 ❌

---

## 📊 현재 ALB 상태

### 예상 ALB
1. **Frontend ALB** (internet-facing)
   - 생성 위치: Frontend Ingress
   - 도메인: seolphung.com
   - 대상: Frontend Service (agent-t namespace)

2. **Argo CD ALB** (삭제됨)
   - 이전: internet-facing → 보안 위험
   - 현재: disabled → Port-forward 사용

---

## ⚠️ 주의사항

### Bedrock 모델 활성화 (수동, 1회)
```
AWS Console → Bedrock → Model access → Request model access
- Claude 3.5 Sonnet
- Claude 3 Opus
```

### Secrets 값 주입 (수동, 1회)
```bash
# Bedrock 설정
aws secretsmanager put-secret-value \
  --secret-id agent-t-dev-bedrock-config \
  --secret-string '{"model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0"}'

# 외부 API Keys (필요 시)
aws secretsmanager put-secret-value \
  --secret-id agent-t-dev-app-secrets \
  --secret-string '{"openai_api_key": "sk-..."}'
```

### GitHub Repository Secrets
```
Settings → Secrets and variables → Actions
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
```

---

## 🔍 트러블슈팅

### ALB가 생성되지 않음
```bash
# ALB Controller 로그 확인
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Subnet 태그 확인
aws ec2 describe-subnets \
  --filters "Name=tag:project,Values=agent-t" \
  --query 'Subnets[*].[SubnetId,Tags[?Key==`kubernetes.io/role/elb`].Value|[0]]'
```

### Argo CD 접속 불가
```bash
# Pod 상태 확인
kubectl get pods -n argocd

# Port-forward
kubectl port-forward -n argocd svc/argocd-server 8080:80

# 비밀번호
kubectl get secret -n argocd argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
```

### 이미지 Pull 실패
```bash
# ECR 권한 확인 (IRSA)
kubectl describe sa -n agent-t frontend

# IAM Role 확인
aws iam get-role \
  --role-name agent-t-dev-frontend-irsa
```

---

## 📈 다음 우선순위

### P0 (필수)
1. ✅ Argo CD Internal로 변경
2. ✅ Frontend Ingress 추가
3. ⏳ ALB 생성 확인
4. ⏳ Route 53 A 레코드 설정
5. ⏳ CI/CD 테스트 (git push → 자동 배포)

### P1 (중요)
- API Service, Agent Service Ingress 추가
- HTTPS 설정 (ACM 인증서)
- External Secrets Operator (Secrets Manager → K8s Secret 자동 동기화)

### P2 (개선)
- Monitoring (Prometheus + Grafana)
- Logging (Loki)
- Network Policy (Pod 간 통신 제한)
- HPA (Horizontal Pod Autoscaler)

---

## 💰 예상 비용 (dev 환경, 월간)

| 리소스 | 비용 |
|--------|------|
| EKS Cluster | $73 |
| EC2 (t3.medium x2) | $60 |
| NAT Gateway | $32 |
| RDS (db.t4g.micro) | $15 |
| Redis (cache.t4g.micro) | $12 |
| ALB (Frontend) | $16 + LCU |
| S3 | $5 |
| VPC Endpoints | $14 |
| **Total** | **~$227/월** |

---

## 📚 참고 문서

- `docs/bootstrap-checklist.md` - Bootstrap 전체 가이드
- `docs/implementation-status.md` - 구현 상태 상세
- `docs/deployment-architecture.md` - 배포 아키텍처 (새로 생성)
- `docs/infra-vs-cicd-separation.md` - 인프라/CI/CD 분리 원칙 (새로 생성)
- `CLAUDE.md` - 프로젝트 전체 가이드라인

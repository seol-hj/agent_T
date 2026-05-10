# 플랫폼 컴포넌트

EKS 클러스터의 핵심 플랫폼 컴포넌트 설치 및 관리 방법.

---

## 개요

Agent T 프로젝트는 다음 플랫폼 컴포넌트를 사용한다:

| 컴포넌트 | 용도 | Namespace | 설치 방법 |
|---|---|---|---|
| **AWS Load Balancer Controller** | Ingress → ALB 자동 프로비저닝 | `kube-system` | Helm |
| **Argo CD** | GitOps 기반 배포 자동화 | `argocd` | Helm |
| **External Secrets Operator** | Secrets Manager → K8s Secret 동기화 | `external-secrets-system` | Helm (추후) |
| **Metrics Server** | Pod/Node 메트릭 수집 | `kube-system` | kubectl apply (추후) |
| **Cluster Autoscaler** | 노드 Auto-scaling | `kube-system` | Helm (추후) |

---

## 설치 순서

1. **Terraform Apply** (EKS, IRSA 등 인프라)
2. **AWS Load Balancer Controller** (Ingress 처리)
3. **Argo CD** (GitOps 배포)
4. **External Secrets Operator** (Secrets 동기화)
5. **애플리케이션 배포** (Helm + Argo CD)

---

## 1. AWS Load Balancer Controller

### 개요

Kubernetes Ingress 리소스를 AWS Application Load Balancer (ALB)로 자동 변환한다.

- **버전**: v2.7.1
- **Namespace**: `kube-system`
- **IRSA**: 필요 (ALB 생성/수정/삭제 권한)

### 설치

#### 사전 요구사항

1. **Terraform으로 IRSA 권한 생성**

```hcl
# infra/terraform/envs/dev/main.tf
module "irsa" {
  source = "../../modules/iam-irsa"

  # ...

  service_accounts = {
    aws-load-balancer-controller = {
      namespace       = "kube-system"
      service_account = "aws-load-balancer-controller"
      policy_arns     = [aws_iam_policy.alb_controller.arn]
    }
  }
}

# IAM Policy (공식 정책 다운로드)
resource "aws_iam_policy" "alb_controller" {
  name   = "${var.project_name}-${var.env}-alb-controller-policy"
  policy = file("${path.module}/policies/alb-controller-policy.json")
}
```

IAM Policy 다운로드:
```bash
curl -o alb-controller-policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json
```

2. **Public Subnet 태그 추가**

Public subnet에 태그 필요 (ALB 배치용):
```hcl
# infra/terraform/modules/vpc/main.tf
resource "aws_subnet" "public" {
  # ...
  tags = {
    "kubernetes.io/role/elb" = "1"
  }
}
```

#### 설치 명령

```bash
# dev 환경
./scripts/install-platform.sh dev alb

# prod 환경
./scripts/install-platform.sh prod alb
```

#### 확인

```bash
# Pod 확인
kubectl get deployment aws-load-balancer-controller -n kube-system
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# IngressClass 확인
kubectl get ingressclass

# 로그 확인
kubectl logs -f deployment/aws-load-balancer-controller -n kube-system
```

### 사용 방법

#### Ingress 예시 (HTTP)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-service
  namespace: default
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'
    alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  ingressClassName: alb
  rules:
  - host: api.dev.agent-t.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8000
```

#### Ingress 예시 (HTTPS)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-service
  namespace: default
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:123456789012:certificate/abc123
spec:
  ingressClassName: alb
  rules:
  - host: api.prod.agent-t.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8000
```

#### 주요 Annotations

| Annotation | 설명 | 예시 |
|---|---|---|
| `alb.ingress.kubernetes.io/scheme` | ALB 타입 | `internet-facing` / `internal` |
| `alb.ingress.kubernetes.io/target-type` | 타겟 타입 | `ip` / `instance` |
| `alb.ingress.kubernetes.io/certificate-arn` | ACM 인증서 ARN | `arn:aws:acm:...` |
| `alb.ingress.kubernetes.io/ssl-redirect` | HTTP → HTTPS 리다이렉트 | `'443'` |
| `alb.ingress.kubernetes.io/healthcheck-path` | Health check 경로 | `/health` |
| `alb.ingress.kubernetes.io/wafv2-acl-arn` | WAF ACL ARN | `arn:aws:wafv2:...` |

전체 목록: https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress/annotations/

### 문제 해결

**1. Ingress가 ALB로 생성 안 됨**

확인:
```bash
kubectl describe ingress <ingress-name>
kubectl logs -f deployment/aws-load-balancer-controller -n kube-system
```

원인:
- IngressClass 지정 안 됨 (`spec.ingressClassName: alb`)
- Public subnet 태그 누락 (`kubernetes.io/role/elb = 1`)
- IRSA 권한 부족

**2. ALB Health Check 실패**

원인:
- Service의 targetPort와 Pod의 containerPort 불일치
- Health check 경로 오류 (`alb.ingress.kubernetes.io/healthcheck-path`)

---

## 2. Argo CD

### 개요

GitOps 기반 Kubernetes 배포 도구. Git repository를 Single Source of Truth로 사용한다.

- **버전**: Latest (Helm Chart)
- **Namespace**: `argocd`
- **IRSA**: 선택사항 (ECR pull 등)

### 설치

#### 설치 명령

```bash
# dev 환경
./scripts/install-platform.sh dev argocd

# prod 환경
./scripts/install-platform.sh prod argocd
```

#### 확인

```bash
# Pod 확인
kubectl get pods -n argocd
kubectl get all -n argocd

# Admin 비밀번호 확인
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### 접근

#### Port Forward

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

브라우저에서 https://localhost:8080 접속.

- Username: `admin`
- Password: (위에서 확인한 비밀번호)

#### Ingress (ALB)

dev 환경:
```
http://argocd.dev.agent-t.local
```

prod 환경:
```
https://argocd.prod.agent-t.com
```

#### CLI

```bash
# Argo CD CLI 설치
brew install argocd  # macOS

# 로그인
argocd login localhost:8080 --username admin --password <password>
```

### Git Repository 연동

#### Public Repository

```bash
# UI에서 Settings → Repositories → Connect Repo
# 또는 CLI
argocd repo add https://github.com/YOUR_ORG/agent-t.git
```

#### Private Repository (SSH)

```bash
# SSH 키 생성
ssh-keygen -t ed25519 -C "argocd@agent-t" -f argocd-deploy-key

# GitHub에 Deploy Key 추가
cat argocd-deploy-key.pub

# Secret 생성
kubectl create secret generic agent-t-repo \
  --from-file=sshPrivateKey=argocd-deploy-key \
  --from-literal=type=git \
  --from-literal=url=git@github.com:YOUR_ORG/agent-t.git \
  -n argocd

kubectl label secret agent-t-repo \
  argocd.argoproj.io/secret-type=repository \
  -n argocd
```

### Application 생성

#### Manifest로 생성 (권장)

```yaml
# infra/argocd/applications/api-service.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: api-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR_ORG/agent-t.git
    targetRevision: main
    path: infra/helm/services/api-service
    helm:
      valueFiles:
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

적용:
```bash
kubectl apply -f infra/argocd/applications/api-service.yaml
```

#### CLI로 생성

```bash
argocd app create api-service \
  --repo https://github.com/YOUR_ORG/agent-t.git \
  --path infra/helm/services/api-service \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default \
  --values values-dev.yaml \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

### Sync Policy

#### Automated Sync (자동 동기화)

Git 변경 사항을 자동으로 클러스터에 반영.

```yaml
syncPolicy:
  automated:
    prune: true       # Git에서 삭제된 리소스 자동 삭제
    selfHeal: true    # 클러스터에서 변경된 리소스 자동 복구
```

#### Manual Sync (수동 동기화)

Git 변경 사항을 수동으로 반영.

```yaml
syncPolicy: {}
```

수동 sync:
```bash
argocd app sync api-service
```

### 문제 해결

**1. Application이 Sync 안 됨**

확인:
```bash
argocd app get <app-name>
kubectl describe application <app-name> -n argocd
```

원인:
- Git repository 접근 실패 (credentials 확인)
- Helm Chart 오류 (`helm template` 로컬 검증)

**2. Out of Sync 상태**

클러스터에서 직접 리소스를 수정한 경우 발생.

해결:
```bash
argocd app sync <app-name>  # Git으로 되돌리기
```

---

## 3. External Secrets Operator (추후 구현)

### 개요

AWS Secrets Manager의 비밀 정보를 Kubernetes Secret으로 자동 동기화.

- **Namespace**: `external-secrets-system`
- **IRSA**: 필요 (Secrets Manager 읽기 권한)

### 사용 예시

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: default
spec:
  provider:
    aws:
      service: SecretsManager
      region: ap-northeast-2
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
  namespace: default
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: db-credentials
    creationPolicy: Owner
  data:
  - secretKey: username
    remoteRef:
      key: agent-t-dev-db-credentials
      property: username
  - secretKey: password
    remoteRef:
      key: agent-t-dev-db-credentials
      property: password
```

---

## 배포 워크플로우

### 1. Git 기반 배포 (GitOps)

```
개발자 코드 변경
      │
      ▼
Git PR/MR 생성
      │
      ▼
코드 리뷰 + 승인
      │
      ▼
main 브랜치 머지
      │
      ▼
Argo CD 자동 감지
      │
      ▼
Kubernetes 배포
      │
      ▼
Slack 알림
```

### 2. 수동 배포 (Emergency)

```bash
# Helm으로 직접 배포
helm upgrade --install api-service ./infra/helm/services/api-service \
  --namespace default \
  --values values-dev.yaml

# Argo CD에서 Git으로 되돌리기 (다음 sync 시)
argocd app sync api-service
```

---

## Best Practices

### 1. Git을 Single Source of Truth로 사용

- 클러스터에서 직접 수정 금지 (`kubectl edit` 금지)
- 모든 변경은 Git PR/MR을 통해 진행

### 2. Environment별 Values 분리

```
infra/helm/services/api-service/
  ├── Chart.yaml
  ├── values.yaml         # 공통 기본값
  ├── values-dev.yaml     # dev 환경 override
  └── values-prod.yaml    # prod 환경 override
```

### 3. Secrets는 Git에 저장 금지

- External Secrets Operator 사용 (Secrets Manager → K8s Secret)
- 또는 Sealed Secrets 사용

### 4. Ingress는 Environment별 분리

- dev: HTTP, internal ALB
- prod: HTTPS (ACM), WAF, IP 화이트리스트

### 5. Resource Limits 설정

모든 Pod에 resource requests/limits 설정:
```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### 6. Health Check 구현

모든 애플리케이션에 health check 엔드포인트 구현:
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

---

## 참고 문서

- [AWS Load Balancer Controller 문서](../infra/helm/platform/aws-load-balancer-controller/README.md)
- [Argo CD 문서](../infra/helm/platform/argocd/README.md)
- [EKS 문서](./eks.md)
- [Secrets 관리](./secrets.md)

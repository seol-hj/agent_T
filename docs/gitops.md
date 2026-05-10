# GitOps with Argo CD

Agent T 프로젝트의 **GitOps 배포 전략 및 Argo CD 사용 방법**을 설명한다.

---

## 개요

**GitOps**는 Git repository를 Single Source of Truth로 사용하는 배포 방식이다.

```
Git Repository (Helm Charts)
       │
       ▼
  Argo CD (자동 감지)
       │
       ▼
  EKS Cluster (배포)
```

**핵심 원칙**:
1. **Git = Single Source of Truth** (모든 변경은 Git을 통해)
2. **선언적 배포** (Desired State를 Git에 선언)
3. **자동 동기화** (Argo CD가 Git 변경 사항 자동 반영)
4. **Self-Healing** (클러스터에서 수동 변경 시 자동 복구)

---

## 저장소 구조

```
agent-t/
├── infra/
│   ├── helm/
│   │   ├── services/              # 서비스별 Helm Chart
│   │   │   ├── api-service/
│   │   │   ├── agent-service/
│   │   │   ├── simulation-service/
│   │   │   ├── analysis-service/
│   │   │   ├── report-service/
│   │   │   └── frontend/
│   │   └── gateway/               # Ingress Gateway (통합 ALB)
│   └── argocd/
│       ├── applications/          # 개별 Application 정의
│       │   ├── dev/
│       │   │   ├── api-service.yaml
│       │   │   ├── agent-service.yaml
│       │   │   ├── simulation-service.yaml
│       │   │   ├── analysis-service.yaml
│       │   │   ├── report-service.yaml
│       │   │   ├── frontend.yaml
│       │   │   └── gateway.yaml
│       │   └── prod/
│       └── applicationsets/       # ApplicationSet (일괄 관리)
│           └── services-dev.yaml
```

---

## Helm Chart 구조

각 서비스는 표준 Helm Chart 구조를 따른다.

### 파일 구조

```
api-service/
├── Chart.yaml              # Chart 메타데이터
├── values.yaml             # 기본 values
├── values-dev.yaml         # dev 환경 override
├── values-prod.yaml        # prod 환경 override
└── templates/
    ├── deployment.yaml     # Deployment
    ├── service.yaml        # Service
    ├── serviceaccount.yaml # ServiceAccount (IRSA)
    ├── configmap.yaml      # ConfigMap (환경 변수)
    ├── hpa.yaml            # HPA (optional)
    └── _helpers.tpl        # Template helpers
```

### 주요 설정

#### 1. Image 설정

```yaml
# values-dev.yaml
image:
  repository: 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t-dev/api-service
  tag: "sha-a1b2c3d"  # CI에서 자동 업데이트
  pullPolicy: IfNotPresent
```

#### 2. IRSA (ServiceAccount)

```yaml
serviceAccount:
  create: true
  name: api-service
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::123456789012:role/agent-t-dev-api-service-irsa"
```

#### 3. Resource Limits

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

#### 4. Health Checks

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

#### 5. HPA (Horizontal Pod Autoscaler)

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

---

## Ingress Gateway

### Path-Based Routing

모든 서비스는 단일 ALB를 통해 path-based routing으로 노출된다.

```yaml
# infra/helm/gateway/values-dev.yaml
ingress:
  hosts:
    - host: agent-t.dev.local
      paths:
        - path: /              # → frontend
        - path: /api           # → api-service
        - path: /agent         # → agent-service
        - path: /simulation    # → simulation-service
        - path: /analysis      # → analysis-service
        - path: /reports       # → report-service
```

**장점**:
- 단일 ALB로 비용 절감
- 통합된 접근 제어 (WAF, Security Group)
- 일관된 도메인

**URL 예시**:
```
http://agent-t.dev.local/                  # Frontend
http://agent-t.dev.local/api/experiments   # API Service
http://agent-t.dev.local/agent/chat        # Agent Service
```

---

## Argo CD Application

### Application 정의

```yaml
# infra/argocd/applications/dev/api-service.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: api-service
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://github.com/YOUR_ORG/agent-t.git
    targetRevision: develop
    path: infra/helm/services/api-service
    helm:
      valueFiles:
        - values-dev.yaml

  destination:
    server: https://kubernetes.default.svc
    namespace: default

  syncPolicy:
    automated:
      prune: true        # Git에서 삭제된 리소스 자동 삭제
      selfHeal: true     # 클러스터 변경 사항 자동 복구
```

### ApplicationSet (일괄 관리)

여러 서비스를 한 번에 관리:

```yaml
# infra/argocd/applicationsets/services-dev.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: services-dev
spec:
  generators:
  - list:
      elements:
      - name: api-service
      - name: agent-service
      # ...
  template:
    metadata:
      name: '{{name}}'
    spec:
      source:
        path: 'infra/helm/services/{{name}}'
```

**사용 시기**:
- 신규 서비스 추가: `elements`에 이름만 추가
- 모든 서비스 일괄 업데이트
- 환경별 일괄 배포

---

## 배포 워크플로우

### 1. 개별 Application 배포

```bash
# Application 적용
kubectl apply -f infra/argocd/applications/dev/api-service.yaml

# Argo CD가 자동으로 Git → Cluster 동기화
# 3분마다 polling 또는 Webhook으로 즉시 감지

# 확인
argocd app list
argocd app get api-service
argocd app sync api-service  # 수동 sync
```

### 2. ApplicationSet 배포

```bash
# ApplicationSet 적용
kubectl apply -f infra/argocd/applicationsets/services-dev.yaml

# 모든 서비스 Application이 자동으로 생성됨
argocd app list
```

### 3. 서비스 업데이트

```bash
# 1. Helm values 수정 (image tag 업데이트)
vi infra/helm/services/api-service/values-dev.yaml
# image.tag: sha-x7y8z9a

# 2. Git commit & push
git add infra/helm/services/api-service/values-dev.yaml
git commit -m "chore: update api-service image tag"
git push origin develop

# 3. Argo CD 자동 감지 및 배포 (3분 이내)
# 또는 수동 sync
argocd app sync api-service
```

---

## Sync Policy

### Automated Sync (dev 환경 권장)

```yaml
syncPolicy:
  automated:
    prune: true       # Git에서 삭제된 리소스 자동 삭제
    selfHeal: true    # 클러스터 변경 시 자동 복구
```

**동작**:
- Git 변경 사항을 3분마다 polling
- 변경 감지 시 자동으로 `kubectl apply`
- 클러스터에서 수동 변경 시 Git 상태로 자동 복구

**장점**:
- 빠른 피드백 루프
- 수동 개입 최소화

**단점**:
- 의도하지 않은 변경 자동 배포 가능

### Manual Sync (prod 환경 권장)

```yaml
syncPolicy: {}
```

**동작**:
- Git 변경 사항을 감지하지만 자동 배포하지 않음
- 운영자가 Argo CD UI/CLI에서 수동으로 Sync 버튼 클릭

**장점**:
- 안전성 우선
- 변경 사항 검토 후 배포

**단점**:
- 수동 개입 필요

---

## Health Check

Argo CD는 Application의 Health 상태를 자동으로 모니터링한다.

### Health Status

| Status | 설명 |
|---|---|
| **Healthy** | 모든 리소스가 정상 동작 |
| **Progressing** | 배포 진행 중 (Rollout) |
| **Degraded** | 일부 리소스 실패 (Pod CrashLoopBackOff 등) |
| **Suspended** | 리소스가 의도적으로 중지됨 |
| **Missing** | 리소스가 클러스터에 없음 |
| **Unknown** | 상태 확인 불가 |

### Sync Status

| Status | 설명 |
|---|---|
| **Synced** | Git과 클러스터 상태 일치 |
| **OutOfSync** | Git과 클러스터 상태 불일치 |

---

## Notification (Slack 연동)

Argo CD는 배포 성공/실패 시 Slack으로 알림을 보낼 수 있다.

### 설정

```yaml
# infra/helm/platform/argocd/values-prod.yaml
notifications:
  enabled: true
  triggers:
    trigger.on-deployed: |
      - when: app.status.operationState.phase in ['Succeeded']
        send: [app-deployed]
    trigger.on-sync-failed: |
      - when: app.status.operationState.phase in ['Error', 'Failed']
        send: [app-sync-failed]
```

### Application에 Annotation 추가

```yaml
metadata:
  annotations:
    notifications.argoproj.io/subscribe.on-deployed.slack: agent-t-deployments
    notifications.argoproj.io/subscribe.on-sync-failed.slack: agent-t-alerts
```

---

## Rollback

### Git Revert

```bash
# 1. Git에서 이전 커밋으로 revert
git revert HEAD
git push origin develop

# 2. Argo CD 자동 감지 및 롤백
# 또는 수동 sync
argocd app sync api-service
```

### Argo CD History

```bash
# 배포 히스토리 확인
argocd app history api-service

# 특정 revision으로 롤백
argocd app rollback api-service <revision-number>
```

---

## Troubleshooting

### 1. Application이 OutOfSync 상태

**원인**: Git과 클러스터 상태 불일치

**확인**:
```bash
argocd app get api-service
argocd app diff api-service
```

**해결**:
```bash
# Git 상태로 동기화
argocd app sync api-service

# 또는 클러스터 변경 사항 무시하고 강제 sync
argocd app sync api-service --force
```

### 2. Application이 Degraded 상태

**원인**: Pod CrashLoopBackOff, ImagePullBackOff 등

**확인**:
```bash
kubectl get pods -n default
kubectl describe pod <pod-name> -n default
kubectl logs <pod-name> -n default
```

**해결**:
- 이미지 태그 확인
- ConfigMap/Secret 확인
- Resource Limits 확인
- Health Check 확인

### 3. Sync 실패

**원인**: Helm Chart 오류, 권한 부족 등

**확인**:
```bash
argocd app get api-service
kubectl describe application api-service -n argocd
```

**해결**:
- Helm Chart 로컬 검증: `helm template infra/helm/services/api-service --values values-dev.yaml`
- RBAC 권한 확인
- Git repository 접근 확인

---

## Best Practices

### 1. Git을 Single Source of Truth로 사용

❌ **잘못된 방법**:
```bash
kubectl edit deployment api-service
kubectl set image deployment/api-service api-service=new-image:tag
```

✅ **올바른 방법**:
```bash
# Git에서 values.yaml 수정
vi infra/helm/services/api-service/values-dev.yaml
git commit -m "chore: update image tag"
git push
```

### 2. Environment별 Values 분리

```
api-service/
├── values.yaml         # 공통 기본값
├── values-dev.yaml     # dev 환경 override
└── values-prod.yaml    # prod 환경 override
```

### 3. Image Tag 명시

❌ **잘못된 방법**:
```yaml
image:
  tag: "latest"
```

✅ **올바른 방법**:
```yaml
image:
  tag: "sha-a1b2c3d"  # 명시적 SHA tag
```

### 4. Resource Limits 설정

모든 Pod에 resource requests/limits 설정:
```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### 5. Health Check 구현

모든 애플리케이션에 health check 엔드포인트 구현:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
```

### 6. Self-Healing 활성화 (dev)

dev 환경에서는 빠른 피드백을 위해 self-healing 활성화:
```yaml
syncPolicy:
  automated:
    selfHeal: true
```

### 7. Manual Sync (prod)

prod 환경에서는 안전성을 위해 manual sync:
```yaml
syncPolicy: {}
```

---

## 참고 문서

- [Argo CD 공식 문서](https://argo-cd.readthedocs.io/)
- [CI/CD Pipeline](./cicd.md)
- [플랫폼 컴포넌트](./platform-components.md)
- [Helm Chart 작성 가이드](https://helm.sh/docs/chart_template_guide/)

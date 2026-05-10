# Argo CD

GitOps 기반 Kubernetes 배포 도구. Git repository를 Single Source of Truth로 사용한다.

---

## 개요

Argo CD는 Git repository의 변경 사항을 자동으로 감지하고 Kubernetes 클러스터에 배포한다.

- **Helm Chart**: https://github.com/argoproj/argo-helm/tree/main/charts/argo-cd
- **공식 문서**: https://argo-cd.readthedocs.io/

---

## 설치

### 1. Bootstrap 스크립트로 설치

```bash
# dev 환경
./scripts/install-platform.sh dev argocd

# prod 환경
./scripts/install-platform.sh prod argocd
```

### 2. 수동 설치 (Helm)

```bash
# Helm Repo 추가
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# argocd namespace 생성
kubectl create namespace argocd

# 설치
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --values values-dev.yaml \
  --wait
```

---

## 접근

### 1. Admin 초기 비밀번호 확인

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### 2. Port Forward로 접근

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

브라우저에서 https://localhost:8080 접속.

### 3. Ingress로 접근 (ALB)

dev 환경:
- URL: http://argocd.dev.agent-t.local
- `/etc/hosts`에 ALB DNS 추가 필요

prod 환경:
- URL: https://argocd.prod.agent-t.com
- ACM 인증서 필요

### 4. CLI 로그인

```bash
# Argo CD CLI 설치
brew install argocd  # macOS
# 또는 https://argo-cd.readthedocs.io/en/stable/cli_installation/

# 로그인 (port-forward 사용)
argocd login localhost:8080 --username admin --password <password>

# 또는 Ingress 사용
argocd login argocd.prod.agent-t.com --username admin --password <password>
```

---

## Git Repository 연동

### 1. Public Repository

```yaml
# infra/argocd/repository.yaml
apiVersion: v1
kind: Secret
metadata:
  name: agent-t-repo
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  type: git
  url: https://github.com/YOUR_ORG/agent-t.git
```

### 2. Private Repository (SSH)

```bash
# SSH 키 생성
ssh-keygen -t ed25519 -C "argocd@agent-t" -f argocd-deploy-key

# GitHub에 Deploy Key 추가 (Read-only)
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

### 3. Private Repository (HTTPS + Token)

```bash
kubectl create secret generic agent-t-repo \
  --from-literal=type=git \
  --from-literal=url=https://github.com/YOUR_ORG/agent-t.git \
  --from-literal=username=YOUR_USERNAME \
  --from-literal=password=YOUR_TOKEN \
  -n argocd

kubectl label secret agent-t-repo \
  argocd.argoproj.io/secret-type=repository \
  -n argocd
```

---

## Application 생성

### 1. UI로 생성

Argo CD UI → Applications → New App

### 2. CLI로 생성

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

### 3. Manifest로 생성 (권장)

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

---

## ApplicationSet (여러 서비스 일괄 관리)

```yaml
# infra/argocd/applicationsets/services.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: services
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - name: api-service
        namespace: default
      - name: agent-service
        namespace: default
      - name: simulation-service
        namespace: default
      - name: analysis-service
        namespace: default
      - name: report-service
        namespace: default
  template:
    metadata:
      name: '{{name}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/YOUR_ORG/agent-t.git
        targetRevision: main
        path: 'infra/helm/services/{{name}}'
        helm:
          valueFiles:
            - values-dev.yaml
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

---

## Sync Policy

### Automated Sync (자동 동기화)

```yaml
syncPolicy:
  automated:
    prune: true       # Git에서 삭제된 리소스 자동 삭제
    selfHeal: true    # 클러스터에서 변경된 리소스 자동 복구
```

### Manual Sync (수동 동기화)

```yaml
syncPolicy: {}
```

수동 sync:
```bash
argocd app sync api-service
```

---

## Notification (Slack 연동)

### 1. Slack Bot 생성

1. Slack App 생성: https://api.slack.com/apps
2. OAuth Token 발급
3. Bot을 채널에 초대

### 2. Secret 생성

```bash
kubectl create secret generic argocd-notifications-secret \
  --from-literal=slack-token=xoxb-YOUR-SLACK-TOKEN \
  -n argocd
```

### 3. ConfigMap 설정

```yaml
# values-prod.yaml에 이미 포함됨
notifications:
  enabled: true
  secret:
    items:
      slack-token: xoxb-YOUR-SLACK-TOKEN
  notifiers:
    service.slack: |
      token: $slack-token
  triggers:
    trigger.on-deployed: |
      - when: app.status.operationState.phase in ['Succeeded']
        send: [app-deployed]
  templates:
    template.app-deployed: |
      message: Application {{.app.metadata.name}} has been deployed.
      slack:
        attachments: |
          [{
            "title": "{{.app.metadata.name}}",
            "color": "good"
          }]
```

### 4. Application에 Annotation 추가

```yaml
metadata:
  annotations:
    notifications.argoproj.io/subscribe.on-deployed.slack: your-channel
```

---

## RBAC (권한 관리)

### 1. 기본 Role

- `role:admin`: 모든 권한
- `role:readonly`: 읽기 전용

### 2. Custom Role

```yaml
# values.yaml
configs:
  rbac:
    policy.csv: |
      p, role:deployer, applications, sync, */*, allow
      p, role:deployer, applications, get, */*, allow
      g, deployer-team, role:deployer
```

### 3. SSO 연동 (Optional)

Dex를 통한 GitHub/Google OAuth 연동 가능.

---

## 확인

### 1. Argo CD Pod 확인
```bash
kubectl get pods -n argocd
kubectl logs -f deployment/argocd-server -n argocd
```

### 2. Application 확인
```bash
argocd app list
argocd app get api-service
argocd app history api-service
```

### 3. Sync 상태 확인
```bash
kubectl get applications -n argocd
kubectl describe application api-service -n argocd
```

---

## 문제 해결

### Application이 Sync 안 됨

**확인**:
```bash
argocd app get <app-name>
kubectl describe application <app-name> -n argocd
```

**원인 1**: Git repository 접근 실패
- Repository Secret 확인

**원인 2**: Helm Chart 오류
- `helm template` 로컬 검증

**원인 3**: RBAC 권한 부족
- ServiceAccount 권한 확인

### Out of Sync 상태

클러스터에서 직접 리소스를 수정한 경우 발생.

**해결**:
```bash
# Git으로 되돌리기 (selfHeal)
argocd app sync <app-name>

# 클러스터 변경 사항 무시
argocd app sync <app-name> --force
```

### Sync Timeout

**해결**:
```yaml
# Application에 timeout 설정
spec:
  syncPolicy:
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

---

## Best Practices

1. **Git을 Single Source of Truth로 사용**
   - 클러스터에서 직접 수정 금지
   - 모든 변경은 Git PR/MR을 통해 진행

2. **Environment별 values 분리**
   - `values-dev.yaml`, `values-prod.yaml`

3. **Application은 Manifest로 관리**
   - UI로 생성하지 말고 `infra/argocd/applications/` 디렉토리에 YAML 저장

4. **Automated Sync + Prune + SelfHeal**
   - prod 환경은 신중하게 (manual sync 고려)

5. **Notification 설정**
   - Slack으로 배포 알림 받기

6. **Secrets는 Git에 저장 금지**
   - External Secrets Operator 사용 (Secrets Manager → Kubernetes Secret)

---

## 참고

- [공식 문서](https://argo-cd.readthedocs.io/)
- [Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
- [Sync Strategies](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-options/)

# Bootstrap/Ingress/ACM 문제 해결 가이드

## 문제 상황

```
frontend Pod가 안 올라옴
  ↓
Ingress 생성 안 됨
  ↓
Route53 레코드 등록 안 됨
  ↓
ACM 인증서 검증 실패
  ↓
Bootstrap 스크립트 실패
```

**순환 의존성**: 모든 것이 서로를 기다리는 상황

---

## 해결 순서

### 1단계: ECR 권한 문제 해결 (완료 ✅)

이미 완료했습니다:
- ECR 계정 ID 수정 (123456789012 → 190484841865)
- gitops/dev에 push 완료

**확인**:
```bash
# Argo CD가 자동 동기화 (3분 이내)
watch kubectl get pods -n default

# 수동 동기화 (빠르게)
for app in api-service frontend agent-service analysis-service report-service simulation-service; do
  kubectl patch application $app -n argocd --type merge -p '{"operation":{"sync":{"revision":"gitops/dev"}}}'
done
```

**예상 결과**: 5-10분 후 모든 Pod가 Running

---

### 2단계: Ingress 생성 확인

```bash
# Ingress 확인
kubectl get ingress -A

# 출력 예시:
# NAMESPACE   NAME       CLASS   HOSTS                    ADDRESS
# default     frontend   alb     app.seolphung.com        xxx.elb.amazonaws.com
```

**Ingress가 없으면**:
- Pod가 아직 Ready가 아님 (1단계 대기)
- Helm chart에 Ingress 리소스 없음 (확인 필요)

---

### 3단계: ACM 인증서 분리 전략

**문제**: ACM 인증서 검증이 Route53 레코드 필요 → Route53은 Ingress 필요 → Ingress는 Pod 필요

**해결책 A: DNS 검증을 수동으로 먼저**

```bash
# 1. ACM 인증서 요청 (Terraform 없이)
aws acm request-certificate \
  --domain-name "seolphung.com" \
  --subject-alternative-names "*.seolphung.com" \
  --validation-method DNS \
  --region ap-northeast-2

# 2. 검증 CNAME 레코드 확인
aws acm describe-certificate \
  --certificate-arn <arn> \
  --region ap-northeast-2 \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'

# 출력:
# {
#   "Name": "_xxx.seolphung.com",
#   "Type": "CNAME",
#   "Value": "_yyy.acm-validations.aws."
# }

# 3. Route53에 수동 등록
aws route53 change-resource-record-sets \
  --hosted-zone-id <zone-id> \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "_xxx.seolphung.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "_yyy.acm-validations.aws."}]
      }
    }]
  }'

# 4. 검증 대기 (5-30분)
aws acm wait certificate-validated \
  --certificate-arn <arn> \
  --region ap-northeast-2

# 5. Terraform에 import
cd infra/terraform/envs/dev
terraform import aws_acm_certificate.main <arn>
```

---

**해결책 B: Bootstrap 스크립트 순서 변경** (권장)

Bootstrap 스크립트를 2단계로 분리:

#### Phase 1: 인프라만 (ACM 제외)
```bash
#!/bin/bash
# scripts/bootstrap-phase1.sh

echo "=== Phase 1: Core Infrastructure ==="

cd infra/terraform/envs/dev

# ACM 리소스 제외하고 적용
terraform apply -target=module.vpc \
  -target=module.eks \
  -target=module.ecr \
  -target=module.rds \
  -target=module.s3 \
  -target=module.secrets_manager \
  -target=module.redis

echo "✅ Phase 1 완료"
echo "다음: 애플리케이션 배포 후 Phase 2 실행"
```

#### Phase 2: ACM & Ingress (Pod Running 후)
```bash
#!/bin/bash
# scripts/bootstrap-phase2.sh

echo "=== Phase 2: ACM & Ingress ==="

# Pod 확인
echo "1️⃣ Pod 상태 확인..."
kubectl get pods -n default

# Ingress 확인
echo "2️⃣ Ingress 확인..."
kubectl get ingress -A

# ALB 주소 확인
ALB_DNS=$(kubectl get ingress frontend -n default -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "ALB DNS: $ALB_DNS"

# Route53에 A 레코드 등록 (수동 또는 External DNS 사용)
echo "3️⃣ Route53 레코드 등록..."
# ... (External DNS가 자동으로 할 수도 있음)

# ACM 적용
echo "4️⃣ ACM 인증서 적용..."
cd infra/terraform/envs/dev
terraform apply -target=aws_acm_certificate.main

echo "✅ Phase 2 완료"
```

---

### 4단계: External DNS 사용 (가장 간단)

**External DNS가 자동으로 처리**:
- Ingress 생성 시 ALB 생성됨
- External DNS가 Route53에 자동으로 레코드 추가
- ACM 검증 자동 완료

**확인**:
```bash
# External DNS Pod 확인
kubectl get pods -n kube-system | grep external-dns

# 없으면 설치 (Terraform에 있어야 함)
# infra/terraform/modules/eks/main.tf
```

---

### 5단계: Frontend Ingress 확인

```bash
# Helm chart에 Ingress 정의 확인
cat infra/helm/services/frontend/templates/ingress.yaml

# 필수 필드:
# - host: app.seolphung.com
# - annotations:
#     alb.ingress.kubernetes.io/scheme: internet-facing
#     alb.ingress.kubernetes.io/certificate-arn: <acm-arn>
```

**Ingress가 없으면 생성**:
```yaml
# infra/helm/services/frontend/templates/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Chart.Name }}
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: {{ .Values.ingress.certificateArn }}
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
spec:
  rules:
  - host: {{ .Values.ingress.host }}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {{ .Chart.Name }}
            port:
              number: 80
```

```yaml
# infra/helm/services/frontend/values-dev.yaml
ingress:
  enabled: true
  host: app.seolphung.com
  certificateArn: arn:aws:acm:ap-northeast-2:190484841865:certificate/xxx
```

---

## 권장 해결 순서

### 🎯 Option 1: ACM 나중에 (권장)

```bash
# 1. ECR 문제 해결 완료 ✅
# 2. Pod 올라올 때까지 대기 (5-10분)
watch kubectl get pods -n default

# 3. 모든 Pod가 Running이면
kubectl get ingress -A

# 4. Ingress 있으면 ALB DNS 확인
kubectl get ingress frontend -n default

# 5. Route53에 수동으로 CNAME 추가 (임시)
aws route53 change-resource-record-sets --hosted-zone-id <id> --change-batch '{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "app.seolphung.com",
      "Type": "CNAME",
      "TTL": 300,
      "ResourceRecords": [{"Value": "<alb-dns>"}]
    }
  }]
}'

# 6. HTTP로 접속 테스트
curl http://app.seolphung.com

# 7. ACM 나중에 적용 (선택)
# terraform apply -target=aws_acm_certificate.main
```

---

### 🎯 Option 2: External DNS 사용 (자동화)

```bash
# 1. External DNS 설치 (Helm)
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm install external-dns external-dns/external-dns \
  --namespace kube-system \
  --set provider=aws \
  --set aws.region=ap-northeast-2 \
  --set txtOwnerId=agent-t-dev \
  --set domainFilters[0]=seolphung.com

# 2. Pod 올라오면 External DNS가 자동으로 Route53 업데이트
# 3. ACM도 자동 검증

# 단, IAM 권한 필요:
# - route53:ChangeResourceRecordSets
# - route53:ListResourceRecordSets
# - route53:ListHostedZones
```

---

### 🎯 Option 3: HTTP만 먼저 (HTTPS 나중)

```bash
# 1. ACM 완전히 제거 (Terraform)
# 2. Ingress를 HTTP만 허용
# 3. 나중에 ACM 추가

# Ingress annotations 변경:
annotations:
  alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'
  # certificate-arn 제거
```

---

## 즉시 실행 가능한 명령어

### 1. Pod 상태 실시간 모니터링
```bash
watch kubectl get pods -n default
```

### 2. 수동으로 Argo CD 동기화 (즉시)
```bash
for app in frontend api-service agent-service analysis-service report-service simulation-service; do
  kubectl patch application $app -n argocd --type merge -p '{"operation":{"sync":{"revision":"gitops/dev"}}}'
  echo "✅ $app synced"
done
```

### 3. 5분 후 Ingress 확인
```bash
kubectl get ingress -A
kubectl describe ingress frontend -n default
```

### 4. ALB 생성 확인
```bash
aws elbv2 describe-load-balancers --region ap-northeast-2 | grep DNSName
```

---

## 예상 타임라인

```
00:00 - gitops/dev push 완료 ✅
00:03 - Argo CD 자동 동기화
00:05 - Pod Running (이미지 pull 시간)
00:08 - Ingress 생성
00:10 - ALB 생성 완료
00:12 - Route53 레코드 추가 (수동 또는 External DNS)
00:15 - HTTP 접속 가능
00:20 - ACM 검증 (나중에)
00:50 - HTTPS 완료 (ACM 검증 시간)
```

---

## 현재 상태 확인

```bash
# 1. Pod 상태 (지금 바로)
kubectl get pods -n default

# 2. 5분 후
kubectl get pods -n default
# 모두 Running이어야 함

# 3. Ingress
kubectl get ingress -A

# 4. ALB
aws elbv2 describe-load-balancers --region ap-northeast-2
```

---

**다음 단계**: 
1. ✅ ECR 계정 ID 수정 완료
2. ⏳ Pod Running 대기 (5-10분)
3. ⏳ Ingress 생성 확인
4. 🔜 Route53 수동 등록 또는 External DNS 설치
5. 🔜 ACM은 나중에 (선택)

---

**작성일**: 2026-05-11  
**상태**: ECR 문제 해결 완료, Pod 올라오는 중

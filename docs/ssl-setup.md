# SSL/TLS 인증서 및 도메인 설정 가이드

## 1. 개요

Agent T 프로젝트의 HTTPS 설정을 위한 완전 자동화 가이드입니다.

### 사용 기술
- **Route 53**: DNS 호스팅
- **ACM (AWS Certificate Manager)**: 무료 SSL 인증서
- **ALB (Application Load Balancer)**: HTTPS 종단점
- **Terraform**: 완전 자동화

### 도메인 정보
- **메인 도메인**: `seolphung.com`
- **다른 계정에서 소유**: NS 레코드 수동 설정 필요

---

## 2. 수동 작업 (1회)

### Step 1: Route 53 Hosted Zone 생성 및 NS 확인

```bash
cd infra/terraform/envs/dev

# Terraform apply (Route 53 Hosted Zone 생성)
terraform apply -target=module.route53
```

**출력 예시:**
```
route53_name_servers = [
  "ns-1234.awsdns-12.org",
  "ns-5678.awsdns-56.com",
  "ns-9012.awsdns-90.net",
  "ns-3456.awsdns-34.co.uk",
]
```

### Step 2: 다른 계정에서 NS 레코드 설정

**다른 AWS 계정의 Route 53에서:**

1. `seolphung.com` Hosted Zone으로 이동
2. NS 레코드 편집
3. 위에서 출력된 4개의 Name Server로 교체

**또는 외부 도메인 등록업체에서:**
- 가비아, GoDaddy, Namecheap 등
- DNS 설정 메뉴에서 Name Server 변경

### Step 3: DNS 전파 대기 및 확인

```bash
# NS 레코드 확인 (최대 48시간, 보통 1-2시간)
dig seolphung.com NS

# 또는
nslookup -type=NS seolphung.com

# 새 NS가 보이면 전파 완료
```

---

## 3. 자동화 작업 (Terraform)

### Step 4: ACM 인증서 발급

NS 전파가 완료되면:

```bash
cd infra/terraform/envs/dev

# ACM 인증서 발급 및 DNS 자동 검증
terraform apply -target=module.acm

# 검증 완료 확인 (5-10분 소요)
terraform output acm_certificate_status
# "ISSUED" 출력되면 완료
```

**자동으로 수행되는 작업:**
1. ACM 인증서 요청
2. DNS 검증 레코드 자동 생성 (Route 53)
3. 검증 완료 대기
4. 인증서 발급

**발급되는 도메인:**
- `seolphung.com` (메인)
- `*.seolphung.com` (와일드카드)
- `api.seolphung.com`
- `argocd.seolphung.com`
- `grafana.seolphung.com`

### Step 5: 전체 인프라 적용

```bash
# 모든 변경사항 적용
terraform apply

# 인증서 ARN 확인
terraform output acm_certificate_arn
# arn:aws:acm:ap-northeast-2:123456789:certificate/xxx-xxx-xxx
```

---

## 4. Kubernetes Ingress 설정

### Argo CD Ingress 예시

**infra/helm/platform/argocd/values-dev.yaml:**

```yaml
server:
  ingress:
    enabled: true
    ingressClassName: alb
    annotations:
      alb.ingress.kubernetes.io/scheme: internet-facing
      alb.ingress.kubernetes.io/target-type: ip
      alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
      alb.ingress.kubernetes.io/ssl-redirect: '443'
      # ACM 인증서 ARN (terraform output에서 가져오기)
      alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:190484841865:certificate/xxx
      alb.ingress.kubernetes.io/healthcheck-path: /healthz
      alb.ingress.kubernetes.io/backend-protocol: HTTP
    hosts:
      - argocd.seolphung.com
    paths:
      - /
```

### Frontend Ingress 예시

**apps/frontend/k8s/ingress.yaml:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:...:certificate/xxx
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
spec:
  ingressClassName: alb
  rules:
  - host: api.seolphung.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

### 배포 후 Ingress 주소 확인

```bash
kubectl get ingress -A

# ALB DNS 확인
kubectl get ingress argocd-server -n argocd -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
# k8s-argocd-argocdse-xxx.ap-northeast-2.elb.amazonaws.com
```

---

## 5. Route 53 A 레코드 연결 (선택적 자동화)

### 방법 1: Terraform으로 자동 (권장)

**main.tf에 추가:**

```hcl
# ALB DNS를 data source로 가져오기
data "kubernetes_ingress_v1" "argocd" {
  metadata {
    name      = "argocd-server"
    namespace = "argocd"
  }

  depends_on = [module.argocd]
}

# Route 53 A 레코드
module "route53" {
  # ... 기존 설정 ...
  
  alb_dns_name = data.kubernetes_ingress_v1.argocd.status[0].load_balancer[0].ingress[0].hostname
  alb_zone_id  = "Z1234567890ABC"  # ALB Zone ID (리전별 고정값)
  
  alb_subdomains = {
    argocd = {
      subdomain = "argocd.seolphung.com"
    }
    api = {
      subdomain = "api.seolphung.com"
    }
  }
}
```

**ALB Zone ID 확인:**
```bash
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(LoadBalancerName, `k8s`)].CanonicalHostedZoneId' \
  --output text
```

**적용:**
```bash
terraform apply
```

### 방법 2: 수동으로 Route 53에서 추가

AWS Console → Route 53 → Hosted Zone (`seolphung.com`) → Create Record

- **Record name**: `argocd`
- **Record type**: `A - Routes traffic to an IPv4 address and some AWS resources`
- **Alias**: Yes
- **Route traffic to**: Alias to Application and Classic Load Balancer
- **Region**: ap-northeast-2
- **Load Balancer**: (Ingress에서 생성된 ALB 선택)

---

## 6. 접속 테스트

```bash
# DNS 전파 확인
dig argocd.seolphung.com

# HTTPS 접속 테스트
curl -I https://argocd.seolphung.com
# HTTP/2 200 OK

# 브라우저 접속
open https://argocd.seolphung.com
```

---

## 7. 자동화 체크리스트

### ✅ Terraform으로 자동화됨
- [x] Route 53 Hosted Zone 생성
- [x] ACM 인증서 발급
- [x] DNS 검증 레코드 자동 생성
- [x] 인증서 검증 대기
- [x] Route 53 A 레코드 생성 (선택)

### ✋ 수동 작업 필요
- [ ] 다른 계정에서 NS 레코드 설정 (1회)
- [ ] DNS 전파 대기 (1-2시간)
- [ ] Ingress에 ACM ARN 추가 (values 또는 manifest 수정)

---

## 8. 트러블슈팅

### 인증서가 PENDING_VALIDATION 상태에서 멈춤

**원인**: DNS 검증 레코드가 전파되지 않음

**해결:**
```bash
# 검증 레코드 확인
dig _xxx.seolphung.com CNAME

# Route 53에 레코드가 있는지 확인
aws route53 list-resource-record-sets --hosted-zone-id Z123456 \
  | jq '.ResourceRecordSets[] | select(.Type=="CNAME")'
```

### ALB가 생성되지 않음

**원인**: ALB Controller 권한 부족

**해결:**
```bash
# ALB Controller 로그 확인
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# 권한 오류가 보이면 IAM Policy 업데이트 필요
```

### HTTPS 접속 시 "NET::ERR_CERT_COMMON_NAME_INVALID"

**원인**: Ingress host와 실제 도메인 불일치

**해결:**
- Ingress의 `spec.rules[].host`가 ACM 인증서의 도메인과 일치하는지 확인
- 와일드카드 인증서(`*.seolphung.com`)는 서브도메인만 매칭 (메인 도메인은 별도 추가 필요)

---

## 9. 비용

- **Route 53 Hosted Zone**: $0.50/월
- **ACM 인증서**: **무료**
- **Route 53 쿼리**: $0.40/100만 쿼리
- **총 예상**: ~$1/월

---

## 10. 다음 단계

1. ✅ Route 53 + ACM 설정 완료
2. 🔄 Ingress에 ACM ARN 추가
3. 🔄 ALB Controller 권한 수정 (현재 오류 해결)
4. 📝 Monitoring 설정 (CloudWatch, Grafana)
5. 📝 WAF 설정 (필요 시)
6. 📝 CD 파이프라인 (Argo CD Application 등록)

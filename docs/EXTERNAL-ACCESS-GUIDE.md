# 외부 접속 가이드

## 현재 상태

✅ **Frontend ALB가 이미 생성되어 있습니다**
- ALB DNS: `k8s-default-frontend-5a9d8add64-2006189360.ap-northeast-2.elb.amazonaws.com`
- 도메인: `seolphung.com`
- Protocol: HTTP (포트 80)

## 접속 방법

### 방법 1: ALB DNS로 직접 접속 (즉시 가능)

```bash
curl http://k8s-default-frontend-5a9d8add64-2006189360.ap-northeast-2.elb.amazonaws.com
```

또는 브라우저에서:
```
http://k8s-default-frontend-5a9d8add64-2006189360.ap-northeast-2.elb.amazonaws.com
```

### 방법 2: 도메인으로 접속 (Route53 설정 필요)

#### 2-1. Route53 Hosted Zone 확인

```bash
# seolphung.com의 Hosted Zone ID 확인
aws route53 list-hosted-zones-by-name --dns-name seolphung.com
```

#### 2-2. A 레코드 생성

```bash
# ALB DNS 주소
ALB_DNS="k8s-default-frontend-5a9d8add64-2006189360.ap-northeast-2.elb.amazonaws.com"

# Hosted Zone ID (위에서 확인한 값)
HOSTED_ZONE_ID="Z0XXXXXXXXXX"  # 실제 값으로 교체

# A 레코드 생성 (ALIAS)
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "seolphung.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z3JE5OI70TWKCP",
          "DNSName": "dualstack.'$ALB_DNS'",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'
```

**주의**: `Z3JE5OI70TWKCP`는 ap-northeast-2 리전의 ALB Hosted Zone ID입니다.

#### 2-3. DNS 전파 대기 (5~10분)

```bash
# DNS 전파 확인
dig seolphung.com

# 또는
nslookup seolphung.com
```

#### 2-4. 브라우저 접속

```
http://seolphung.com
```

---

## HTTPS 설정 (선택 사항)

HTTPS를 사용하려면 ACM(AWS Certificate Manager)에서 SSL 인증서를 발급받아야 합니다.

### 1. ACM 인증서 발급

```bash
# 인증서 요청
aws acm request-certificate \
  --domain-name seolphung.com \
  --validation-method DNS \
  --region ap-northeast-2

# 인증서 ARN 확인
aws acm list-certificates --region ap-northeast-2
```

### 2. DNS 검증

ACM 콘솔에서 CNAME 레코드 정보를 확인하고 Route53에 추가합니다.

### 3. Helm values 업데이트

`infra/helm/services/frontend/values-dev.yaml`:

```yaml
ingress:
  enabled: true
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:190484841865:certificate/YOUR_CERT_ID
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'
  hosts:
    - host: seolphung.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - hosts:
        - seolphung.com
```

### 4. Argo CD Sync

변경사항을 gitops/dev에 push하면 Argo CD가 자동으로 배포합니다.

---

## 트러블슈팅

### ALB가 응답하지 않는 경우

```bash
# ALB 상태 확인
kubectl describe ingress frontend -n default

# Pod 상태 확인
kubectl get pods -l app.kubernetes.io/name=frontend -n default

# Service 확인
kubectl get svc frontend -n default

# ALB Target Group 상태 확인 (AWS 콘솔)
```

### 502 Bad Gateway

- Frontend Pod가 정상 실행 중인지 확인
- Health check 경로(`/`)가 응답하는지 확인
- Service와 Pod의 포트 매핑 확인 (3000번 포트)

### 도메인 접속 안 됨

- Route53 레코드가 올바르게 설정되었는지 확인
- DNS 전파 대기 (최대 48시간, 보통 5~10분)
- 네임서버가 Route53으로 설정되었는지 확인

---

## 현재 아키텍처

```
Internet
    ↓
[Route53: seolphung.com]
    ↓
[ALB (internet-facing)]
    ↓
[EKS Cluster]
    ↓
[Frontend Service (ClusterIP:80)]
    ↓
[Frontend Pods (port 3000)]
```

## 보안 그룹

ALB는 자동으로 생성된 보안 그룹을 사용합니다:
- Inbound: 0.0.0.0/0 → 80, 443 (HTTPS 설정 시)
- Outbound: EKS Node Security Group

EKS Node Security Group:
- ALB로부터의 트래픽 허용
- Pod 간 통신 허용

---

## 참고

- Frontend는 Next.js 14 기반
- 포트: 3000
- Health check: `/` (root path)
- 현재 이미지: `sha-0a871c8` (최신)

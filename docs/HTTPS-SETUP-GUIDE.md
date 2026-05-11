# HTTPS 설정 가이드

**목적**: HTTP를 차단하고 HTTPS only + 도메인 기반 접속 설정

---

## 설정 개요

### Before (HTTP)
```
http://k8s-default-frontend-xxxxx.elb.amazonaws.com
http://seolphung.com
```

### After (HTTPS Only)
```
https://agent.seolphung.com  ✅ 
http://agent.seolphung.com   → 자동으로 HTTPS로 리다이렉트
```

---

## 자동 설정 스크립트 (권장)

```bash
# 1회 실행으로 모든 설정 완료
./scripts/setup-https-domain.sh
```

**스크립트가 수행하는 작업:**
1. Route53 Hosted Zone 조회
2. ACM DNS 검증 레코드 추가
3. 인증서 검증 대기 (5-10분)
4. A 레코드 (ALIAS) 추가: `agent.seolphung.com` → ALB

---

## 수동 설정 (상세)

자동 스크립트 대신 수동으로 설정하려면 아래 단계를 따르세요.

### 1단계: ACM 인증서 발급

```bash
# 인증서 요청
aws acm request-certificate \
  --domain-name agent.seolphung.com \
  --validation-method DNS \
  --region ap-northeast-2

# Certificate ARN 저장
CERT_ARN="arn:aws:acm:ap-northeast-2:190484841865:certificate/03e82b5c-961c-43ea-93d5-027c5e9d1d6c"
```

### 2단계: DNS 검증 레코드 추가

```bash
# DNS 검증 정보 조회
aws acm describe-certificate \
  --certificate-arn "${CERT_ARN}" \
  --region ap-northeast-2 \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'

# 출력 예시:
# {
#     "Name": "_xxx.agent.seolphung.com.",
#     "Type": "CNAME",
#     "Value": "_yyy.acm-validations.aws."
# }
```

**Route53에 CNAME 레코드 추가:**

1. AWS Console → Route53 → Hosted zones → seolphung.com
2. Create record
   - Record name: `_xxx.agent.seolphung.com`
   - Record type: `CNAME`
   - Value: `_yyy.acm-validations.aws.`
   - TTL: `300`
3. Create records

### 3단계: 인증서 검증 대기

```bash
# 검증 완료까지 대기 (보통 5-10분)
aws acm wait certificate-validated \
  --certificate-arn "${CERT_ARN}" \
  --region ap-northeast-2

# 검증 완료 확인
aws acm describe-certificate \
  --certificate-arn "${CERT_ARN}" \
  --region ap-northeast-2 \
  --query 'Certificate.Status' \
  --output text
# 출력: ISSUED
```

### 4단계: Route53 A 레코드 추가

```bash
# Hosted Zone ID 조회
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
  --dns-name seolphung.com \
  --query 'HostedZones[0].Id' \
  --output text | cut -d'/' -f3)

# ALB 정보
ALB_DNS="k8s-default-frontend-5a9d8add64-2006189360.ap-northeast-2.elb.amazonaws.com"
ALB_HOSTED_ZONE_ID="Z3JE5OI70TWKCP"  # ap-northeast-2 ALB

# A 레코드 (ALIAS) 추가
aws route53 change-resource-record-sets \
  --hosted-zone-id "${HOSTED_ZONE_ID}" \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "agent.seolphung.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "'${ALB_HOSTED_ZONE_ID}'",
          "DNSName": "dualstack.'${ALB_DNS}'",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'
```

### 5단계: Helm Values 업데이트

**파일**: `infra/helm/services/frontend/values-dev.yaml`

```yaml
ingress:
  enabled: true
  annotations:
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:190484841865:certificate/03e82b5c-961c-43ea-93d5-027c5e9d1d6c
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/ssl-redirect: '443'  # HTTP → HTTPS 강제 리다이렉트
  hosts:
    - host: agent.seolphung.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - hosts:
        - agent.seolphung.com
```

### 6단계: GitOps 배포

```bash
# 1. 변경사항 커밋
git checkout gitops/dev
git pull origin gitops/dev
# values-dev.yaml 수정
git add infra/helm/services/frontend/values-dev.yaml
git commit -m "feat: enable HTTPS with ACM certificate for agent.seolphung.com"
git push origin gitops/dev

# 2. Argo CD 자동 sync 대기 (3분 이내)
# 또는 수동 sync:
kubectl rollout restart deployment/frontend -n default
```

### 7단계: DNS 전파 대기 & 테스트

```bash
# DNS 전파 확인 (5-10분)
dig agent.seolphung.com

# HTTPS 접속 테스트
curl -I https://agent.seolphung.com
# HTTP → HTTPS 리다이렉트 확인
curl -I http://agent.seolphung.com
# 출력: 301 Moved Permanently → https://agent.seolphung.com

# 브라우저 접속
open https://agent.seolphung.com
```

---

## ALB 설정 상세

### HTTP → HTTPS 자동 리다이렉트

ALB는 다음 설정으로 HTTP 요청을 자동으로 HTTPS로 리다이렉트합니다:

```yaml
annotations:
  alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
  alb.ingress.kubernetes.io/ssl-redirect: '443'
```

**동작:**
1. 사용자가 `http://agent.seolphung.com` 접속
2. ALB가 `301 Moved Permanently` 응답
3. Location 헤더: `https://agent.seolphung.com`
4. 브라우저가 자동으로 HTTPS로 재접속

### HTTP 완전 차단 (선택 사항)

HTTP 리스너를 완전히 제거하려면:

```yaml
annotations:
  alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS": 443}]'  # HTTP 80 제거
  # ssl-redirect 불필요 (HTTP 리스너 없음)
```

**트레이드오프:**
- ✅ 보안 강화 (HTTP 완전 차단)
- ❌ HTTP 접속 시 연결 실패 (사용자 혼란 가능)

**권장**: 리다이렉트 유지 (사용자 경험 향상)

---

## 인증서 갱신

ACM 인증서는 **자동으로 갱신**됩니다.

- ACM이 만료 60일 전부터 자동 갱신 시도
- DNS 검증 레코드가 Route53에 유지되어 있으면 자동 성공
- 별도 작업 불필요

**확인 방법:**
```bash
aws acm describe-certificate \
  --certificate-arn "${CERT_ARN}" \
  --region ap-northeast-2 \
  --query 'Certificate.NotAfter' \
  --output text
```

---

## 환경별 설정

### Dev 환경

**도메인**: `agent.seolphung.com`  
**인증서**: `arn:aws:acm:ap-northeast-2:190484841865:certificate/03e82b5c-961c-43ea-93d5-027c5e9d1d6c`

**Helm values** (`values-dev.yaml`):
```yaml
ingress:
  hosts:
    - host: agent.seolphung.com
  annotations:
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:190484841865:certificate/03e82b5c-961c-43ea-93d5-027c5e9d1d6c
```

### Prod 환경 (미구축)

**도메인**: `agent.seolphung.com` (동일) 또는 `app.seolphung.com`  
**인증서**: 별도 발급 필요

**Helm values** (`values-prod.yaml`):
```yaml
ingress:
  hosts:
    - host: agent.seolphung.com  # 또는 app.seolphung.com
  annotations:
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:xxx:certificate/PROD_CERT_ID
    alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:...  # WAF 추가
```

---

## 트러블슈팅

### 1. 인증서 검증 실패

**증상**: `acm wait certificate-validated` 타임아웃

**원인**:
- DNS 검증 레코드가 잘못 추가됨
- Route53 Hosted Zone이 도메인 네임서버와 일치하지 않음

**해결**:
```bash
# 1. 검증 레코드 확인
aws acm describe-certificate --certificate-arn "${CERT_ARN}" \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'

# 2. Route53 레코드 확인
aws route53 list-resource-record-sets \
  --hosted-zone-id "${HOSTED_ZONE_ID}" \
  --query "ResourceRecordSets[?Type=='CNAME']"

# 3. 네임서버 확인
dig NS seolphung.com
# Route53 네임서버와 일치해야 함
```

### 2. HTTPS 접속 실패 (502 Bad Gateway)

**원인**:
- Frontend Pod가 비정상
- Health check 실패

**해결**:
```bash
# Pod 상태 확인
kubectl get pods -l app.kubernetes.io/name=frontend

# Pod 로그 확인
kubectl logs -l app.kubernetes.io/name=frontend --tail=50

# Health check 확인
kubectl exec -it <frontend-pod> -- curl localhost:3000/
```

### 3. HTTP → HTTPS 리다이렉트 안됨

**원인**: ALB 설정이 아직 반영 안됨

**해결**:
```bash
# Ingress 확인
kubectl describe ingress frontend

# ALB annotation 확인
kubectl get ingress frontend -o yaml | grep ssl-redirect

# Argo CD sync 강제 실행
kubectl rollout restart deployment/frontend
```

### 4. DNS 전파 안됨

**증상**: `dig agent.seolphung.com` 응답 없음

**해결**:
```bash
# Route53 레코드 확인
aws route53 list-resource-record-sets \
  --hosted-zone-id "${HOSTED_ZONE_ID}" \
  --query "ResourceRecordSets[?Name=='agent.seolphung.com.']"

# 강제 DNS 조회 (Route53 직접)
dig @8.8.8.8 agent.seolphung.com

# 최대 48시간 대기 (보통 5-10분)
```

---

## 보안 권장 사항

### 1. HSTS (HTTP Strict Transport Security) 활성화

**Helm values에 추가**:
```yaml
annotations:
  alb.ingress.kubernetes.io/actions.ssl-redirect: |
    {
      "Type": "redirect",
      "RedirectConfig": {
        "Protocol": "HTTPS",
        "Port": "443",
        "StatusCode": "HTTP_301"
      }
    }
  # HSTS 헤더 추가 (Frontend에서 설정)
```

**Frontend (Next.js) `next.config.js`**:
```javascript
async headers() {
  return [
    {
      source: '/(.*)',
      headers: [
        {
          key: 'Strict-Transport-Security',
          value: 'max-age=31536000; includeSubDomains; preload'
        }
      ]
    }
  ]
}
```

### 2. TLS 버전 제한

ALB는 기본적으로 TLS 1.2+만 허용 (안전).

확인:
```bash
kubectl describe ingress frontend | grep ssl-policy
```

### 3. WAF 추가 (Prod 환경)

```yaml
annotations:
  alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:ap-northeast-2:190484841865:regional/webacl/agent-t-prod-waf/xxx
```

---

## 비용

| 항목 | 비용 |
|---|---|
| ACM 인증서 | **무료** (공인 인증서) |
| Route53 Hosted Zone | $0.50/월 |
| Route53 쿼리 | $0.40/백만 쿼리 |
| ALB | ~$16/월 (기본) + 데이터 전송 |

**예상 총 비용**: ~$20/월

---

## 체크리스트

- [ ] ACM 인증서 발급 (`aws acm request-certificate`)
- [ ] DNS 검증 레코드 추가 (Route53 CNAME)
- [ ] 인증서 검증 완료 (`ISSUED` 상태)
- [ ] Route53 A 레코드 추가 (ALIAS → ALB)
- [ ] Helm values 업데이트 (`certificate-arn`, `ssl-redirect`)
- [ ] GitOps 배포 (`gitops/dev` push)
- [ ] DNS 전파 확인 (`dig agent.seolphung.com`)
- [ ] HTTPS 접속 테스트 (`curl -I https://agent.seolphung.com`)
- [ ] HTTP 리다이렉트 확인 (`curl -I http://agent.seolphung.com`)
- [ ] 브라우저 테스트 (자물쇠 아이콘 확인)

---

**현재 상태**: 설정 완료 대기 중  
**다음 단계**: `./scripts/setup-https-domain.sh` 실행

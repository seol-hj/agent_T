# 도메인 설정 점검 가이드

**도메인**: seolphung.com  
**서브도메인**: agent.seolphung.com

---

## ⚠️ 중요: 도메인이 다른 AWS 계정에 등록된 경우

### 현재 상황

1. **도메인 등록 계정**: 다른 AWS 계정 (확인 필요)
2. **Route53 Hosted Zone**: 현재 계정 (190484841865)
3. **문제**: 네임서버 위임이 되어있지 않으면 DNS 조회 및 ACM 검증 실패

---

## 1단계: 네임서버 확인

### 1-1. Route53 Hosted Zone의 네임서버 확인

```bash
aws route53 get-hosted-zone --id Z09342513JSE2P349RU1N \
  --query 'DelegationSet.NameServers' \
  --output json
```

**결과** (현재):
```json
[
    "ns-289.awsdns-36.com",
    "ns-1766.awsdns-28.co.uk",
    "ns-952.awsdns-55.net",
    "ns-1080.awsdns-07.org"
]
```

### 1-2. 실제 도메인의 네임서버 확인

**방법 1: 웹 DNS 조회**
- https://www.whatsmydns.net/#NS/seolphung.com
- https://dnschecker.org/all-dns-records-of-domain.php?query=seolphung.com

**방법 2: 로컬 명령어**
```bash
dig NS seolphung.com +short
# 또는
nslookup -type=NS seolphung.com
```

**방법 3: Python**
```python
import dns.resolver
result = dns.resolver.resolve('seolphung.com', 'NS')
for ns in result:
    print(ns)
```

---

## 2단계: 네임서버 일치 확인

### ✅ 일치하는 경우 (정상)

**Hosted Zone NS** = **도메인 실제 NS**

→ DNS 조회 정상, ACM 검증 가능, HTTPS 설정 가능

**다음 단계:**
- `docs/HTTPS-SETUP-GUIDE.md` 계속 진행
- 인증서 검증 대기

### ❌ 불일치하는 경우 (수정 필요)

**Hosted Zone NS** ≠ **도메인 실제 NS**

→ DNS 조회 실패, ACM 검증 불가

**해결 방법:** 도메인 등록 계정에서 네임서버 변경

---

## 3단계: 네임서버 변경 (불일치 시)

### 옵션 1: 도메인 등록 AWS 계정에서 변경

1. **도메인이 등록된 AWS 계정 로그인**

2. **Route 53 → Registered domains → seolphung.com**

3. **Name servers 변경**
   ```
   ns-289.awsdns-36.com
   ns-1766.awsdns-28.co.uk
   ns-952.awsdns-55.net
   ns-1080.awsdns-07.org
   ```

4. **저장 및 전파 대기** (24-48시간, 보통 1-2시간)

### 옵션 2: 다른 도메인 레지스트라에서 변경

**GoDaddy, Namecheap, Gabia 등**:

1. 도메인 관리 페이지 접속
2. DNS 설정 또는 Nameservers 메뉴
3. Custom Nameservers 선택
4. Route53 네임서버 4개 입력
5. 저장

### 옵션 3: 서브도메인 위임 (간단)

**현재 계정에서 서브도메인만 사용:**

도메인 등록 계정의 Route53/DNS에서:

```
agent.seolphung.com NS 레코드 추가:
  ns-289.awsdns-36.com
  ns-1766.awsdns-28.co.uk
  ns-952.awsdns-55.net
  ns-1080.awsdns-07.org
```

**장점**: 루트 도메인 설정 변경 불필요  
**단점**: agent.seolphung.com만 현재 계정에서 관리 가능

---

## 4단계: 네임서버 전파 확인

### 4-1. 전파 확인 (글로벌)

https://www.whatsmydns.net/#NS/seolphung.com

**목표**: 전 세계 DNS 서버에서 새 네임서버 확인

### 4-2. ACM DNS 검증 레코드 확인

```bash
# ACM 검증 레코드 조회
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:ap-northeast-2:190484841865:certificate/03e82b5c-961c-43ea-93d5-027c5e9d1d6c \
  --region ap-northeast-2 \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'
```

**웹 DNS 조회**:
```
https://www.whatsmydns.net/#CNAME/_4958f073b83f02ceb894cdd37dd8b54b.agent.seolphung.com
```

**기대 결과**:
```
_4958f073b83f02ceb894cdd37dd8b54b.agent.seolphung.com
→ _9b0b7e7e3e8ef6fad0b5e00e643735b2.jkddzztszm.acm-validations.aws.
```

### 4-3. 서브도메인 A 레코드 확인

```
https://www.whatsmydns.net/#A/agent.seolphung.com
```

**기대 결과**:
```
agent.seolphung.com → <ALB-IP>
```

---

## 5단계: ACM 인증서 검증 대기

### 정상 시나리오

```
1. Route53 Hosted Zone 생성 (완료)
2. 네임서버 위임 (확인 필요)
3. DNS 전파 (1-2시간)
4. ACM DNS 검증 레코드 조회 가능
5. ACM 인증서 검증 완료 (5-10분)
6. HTTPS 접속 가능
```

### 현재 상태 확인

```bash
# 인증서 상태
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:ap-northeast-2:190484841865:certificate/03e82b5c-961c-43ea-93d5-027c5e9d1d6c \
  --region ap-northeast-2 \
  --query 'Certificate.{Status:Status,ValidationStatus:DomainValidationOptions[0].ValidationStatus}' \
  --output json
```

**예상 상태:**
- ✅ `ISSUED` - 검증 완료 (정상)
- ⏳ `PENDING_VALIDATION` - 검증 대기 중 (DNS 전파 필요)
- ❌ `FAILED` - 검증 실패 (네임서버 불일치)

---

## 트러블슈팅

### 문제 1: ACM 검증 실패 (PENDING_VALIDATION 계속)

**원인**: DNS 검증 레코드를 조회할 수 없음

**확인**:
```bash
# 웹 DNS 조회
https://www.whatsmydns.net/#CNAME/_4958f073b83f02ceb894cdd37dd8b54b.agent.seolphung.com
```

**해결**:
1. 네임서버 일치 확인
2. DNS 전파 대기 (최대 48시간)
3. Route53 레코드 재확인

### 문제 2: agent.seolphung.com 접속 안됨

**원인**: A 레코드가 조회되지 않음

**확인**:
```bash
https://www.whatsmydns.net/#A/agent.seolphung.com
```

**해결**:
1. Route53에 A 레코드 확인
2. 네임서버 전파 대기
3. 캐시 초기화

### 문제 3: 인증서는 발급되었으나 HTTPS 접속 안됨

**원인**: ALB가 인증서를 아직 반영하지 않음

**확인**:
```bash
kubectl get ingress frontend -o yaml | grep certificate-arn
```

**해결**:
```bash
# Argo CD 수동 sync
kubectl rollout restart deployment/frontend -n default

# 또는 Ingress 재생성
kubectl delete ingress frontend
# Argo CD가 자동으로 재생성
```

---

## 권장 사항

### 즉시 확인 사항

1. **네임서버 일치 여부 확인**
   - https://www.whatsmydns.net/#NS/seolphung.com
   - Hosted Zone NS와 비교

2. **불일치 시 수정**
   - 도메인 등록 계정에서 네임서버 변경
   - 또는 서브도메인 위임

3. **전파 대기**
   - 네임서버 변경: 1-2시간 (최대 48시간)
   - ACM 검증: 5-10분

### 대안: 다른 도메인 사용

현재 계정에서 새 도메인 등록:

```bash
# Route53에서 도메인 등록
aws route53domains register-domain \
  --domain-name your-new-domain.com \
  --duration-in-years 1 \
  --admin-contact file://contact.json \
  --registrant-contact file://contact.json \
  --tech-contact file://contact.json \
  --auto-renew
```

**장점**: 네임서버 자동 설정  
**단점**: 도메인 비용 ($12/년)

---

## 체크리스트

- [ ] Route53 Hosted Zone 네임서버 확인
- [ ] 도메인 실제 네임서버 확인 (https://www.whatsmydns.net)
- [ ] 네임서버 일치 여부 확인
- [ ] 불일치 시: 도메인 등록 계정에서 네임서버 변경
- [ ] DNS 전파 대기 (1-2시간)
- [ ] ACM 검증 레코드 조회 가능 확인
- [ ] ACM 인증서 ISSUED 상태 확인
- [ ] agent.seolphung.com A 레코드 조회 확인
- [ ] HTTPS 접속 테스트

---

**중요**: 네임서버가 일치하지 않으면 ACM 검증이 절대 완료되지 않습니다!

**다음 문서**: 네임서버 확인 후 `docs/HTTPS-SETUP-GUIDE.md` 계속 진행

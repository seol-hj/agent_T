# 문제 해결 가이드

Agent T 사용 중 발생할 수 있는 문제와 해결 방법

---

## 🐳 Docker Compose 관련

### 포트 충돌

**증상**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```

**원인**: 다른 프로세스가 동일한 포트를 사용 중

**해결**:
```bash
# 사용 중인 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>

# 또는 docker-compose.yaml에서 호스트 포트 변경
ports:
  - "8001:8000"  # 8001로 변경
```

### 메모리 부족

**증상**:
```
pipeline-1 | Killed
simulation-service-1 exited with code 137
```

**해결**:
- Docker Desktop → Settings → Resources → Memory를 8GB 이상으로 증가
- 불필요한 컨테이너 정리: `docker system prune -a`

### 프론트엔드 빌드 실패

**증상**:
```
frontend-1 | ERROR: failed to solve: process "/bin/sh -c npm run build" did not complete successfully
```

**해결**:
```bash
# 캐시 없이 재빌드
docker compose build --no-cache frontend
docker compose up frontend
```

---

## 🗄️ PostgreSQL 관련

### 연결 실패

**증상**:
```
pipeline-1 | sqlalchemy.exc.OperationalError: could not connect to server
```

**해결**:
```bash
# PostgreSQL이 완전히 시작될 때까지 대기 (30-60초)
docker compose logs postgres | grep "ready to accept connections"

# 또는 재시작
docker compose restart postgres
sleep 10
docker compose restart pipeline
```

### 데이터베이스 초기화

**증상**: 기존 데이터를 삭제하고 싶을 때

**해결**:
```bash
# 볼륨까지 삭제
docker compose down -v

# 재시작
docker compose up --build
```

---

## 🌐 프론트엔드 관련

### 진행률 조회 실패

**증상**: "진행률 조회 실패" 메시지

**원인 및 해결**:

1. **API 호출 실패 확인**:
```bash
# 브라우저 F12 → Network 탭 확인
# GET /pipeline/{id}/status 요청이 있는지 확인
```

2. **Backend 로그 확인**:
```bash
docker compose logs pipeline | grep execution
```

3. **PostgreSQL 연결 확인**:
```bash
docker compose logs postgres
```

4. **해결**:
```bash
docker compose restart pipeline
```

### API 연결 안됨

**증상**: "Failed to fetch" 에러

**원인**: CORS 또는 네트워크 문제

**해결**:
```bash
# Backend Health Check
curl http://localhost:8000/health

# Frontend 환경변수 확인
docker compose logs frontend | grep API_BASE_URL

# 재시작
docker compose restart frontend pipeline
```

---

## 🤖 SUMO 시뮬레이션 관련

### OSM 다운로드 실패

**증상**:
```
simulation-service-1 | OSM 다운로드 실패: Client error '406 Not Acceptable'
```

**원인**: Overpass API User-Agent 헤더 필요 또는 Rate Limit

**해결**:
- Placeholder 모드로 자동 전환됨 (정상 동작)
- 실제 OSM 다운로드가 필요하면 User-Agent 헤더 추가 필요

### Demand Builder 실패

**증상**:
```
simulation-service-1 | INFO: POST /demand/build HTTP/1.1 500 Internal Server Error
```

**원인**: Placeholder 네트워크 파일 파싱 실패

**해결**:
```bash
# 로그 확인
docker compose logs simulation-service | tail -100

# 이미 수정됨: Placeholder 네트워크 자동 감지 구현
```

---

## ☁️ AWS 배포 관련

### Terraform 초기화 실패

**증상**:
```
Error: Failed to get existing workspaces: operation error S3
```

**원인**: S3 backend 버킷이 없거나 권한 부족

**해결**:
```bash
# S3 버킷 수동 생성
aws s3 mb s3://agent-t-terraform-state-dev --region ap-northeast-2

# DynamoDB 테이블 생성
aws dynamodb create-table \
  --table-name agent-t-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 재시도
terraform init
```

### EKS 클러스터 접속 실패

**증상**:
```
error: You must be logged in to the server (Unauthorized)
```

**해결**:
```bash
# kubeconfig 업데이트
aws eks update-kubeconfig --name agent-t-dev --region ap-northeast-2

# 권한 확인
aws sts get-caller-identity
kubectl auth can-i get pods --all-namespaces
```

### Pod가 CrashLoopBackOff

**증상**:
```
pipeline-xxx   0/1   CrashLoopBackOff   5   10m
```

**해결**:
```bash
# 로그 확인
kubectl logs -n agent-t pipeline-xxx

# 이전 로그 확인
kubectl logs -n agent-t pipeline-xxx --previous

# Describe로 상세 확인
kubectl describe pod -n agent-t pipeline-xxx

# 주요 원인:
# 1. 환경변수 누락 (DATABASE_URL 등)
# 2. Secret 없음
# 3. Image pull 실패
# 4. Health check 실패
```

### ImagePullBackOff

**증상**:
```
Failed to pull image: unauthorized
```

**해결**:
```bash
# ECR 로그인 확인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지가 ECR에 있는지 확인
aws ecr list-images --repository-name agent-t/pipeline

# IRSA 권한 확인 (EKS에서 ECR pull 권한)
kubectl describe sa -n agent-t pipeline-service
```

---

## 🔐 Secrets Manager 관련

### Secret 조회 실패

**증상**:
```
botocore.exceptions.ClientError: An error occurred (ResourceNotFoundException)
```

**해결**:
```bash
# Secret 존재 확인
aws secretsmanager list-secrets | grep agent-t

# Secret 생성
aws secretsmanager create-secret \
  --name agent-t/dev/db-password \
  --secret-string "your-password"

# IRSA 권한 확인
# ServiceAccount에 IAM Role이 연결되어 있는지 확인
```

---

## 🚀 Argo CD 관련

### Application이 OutOfSync

**증상**: Argo CD UI에서 "OutOfSync" 표시

**원인**: Git의 YAML과 클러스터 상태가 다름

**해결**:
```bash
# 수동 Sync
argocd app sync pipeline

# 또는 UI에서 SYNC 버튼 클릭

# Auto-sync 활성화
argocd app set pipeline --sync-policy automated
```

### Application이 Degraded

**증상**: Health Status가 "Degraded"

**원인**: Pod가 정상 실행되지 않음

**해결**:
```bash
# Application 상태 확인
argocd app get pipeline

# 해당 리소스 확인
kubectl get pods -n agent-t
kubectl logs -n agent-t <pod-name>
```

---

## 🧪 테스트 관련

### test-services-local.sh 실패

**증상**: "일부 테스트 실패"

**해결**:
```bash
# 서비스 상태 확인
docker compose ps

# 개별 서비스 로그 확인
docker compose logs agent-service
docker compose logs simulation-service

# 재시작
docker compose restart
sleep 30
./scripts/test-services-local.sh
```

---

## 🐛 일반적인 디버깅 팁

### 로그 확인

```bash
# Docker Compose
docker compose logs -f <service-name>
docker compose logs --tail=100 <service-name>

# Kubernetes
kubectl logs -n agent-t <pod-name>
kubectl logs -n agent-t <pod-name> --previous
kubectl logs -n agent-t -l app=pipeline
```

### 상태 확인

```bash
# Docker Compose
docker compose ps
docker compose top

# Kubernetes
kubectl get pods -n agent-t
kubectl get svc -n agent-t
kubectl get ingress -n agent-t
kubectl describe pod -n agent-t <pod-name>
```

### 컨테이너 내부 접속

```bash
# Docker Compose
docker compose exec pipeline bash

# Kubernetes
kubectl exec -it -n agent-t <pod-name> -- bash
```

### 네트워크 확인

```bash
# Docker Compose 내부 통신 확인
docker compose exec pipeline curl http://agent-service:8001/health

# Kubernetes 내부 통신 확인
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://agent-service.agent-t.svc.cluster.local:8001/health
```

---

## 📞 추가 지원

문제가 해결되지 않으면:

1. **GitHub Issues**: https://github.com/<your-org>/agent-t/issues
2. **로그 첨부**: 전체 로그 파일을 첨부해주세요
3. **환경 정보**:
   - OS 및 버전
   - Docker 버전
   - Kubernetes 버전 (AWS 배포 시)

---

**최종 업데이트**: 2026-05-11  
**버전**: 0.4.0

# Kubernetes Job Executor 구현 완료

SUMO Runner를 Kubernetes Job으로 실행하는 기능 구현 완료.

---

## 구현 내용

### 1. **KubernetesJobExecutor** (kubernetes_executor.py, 400+ lines)

Kubernetes Job 생성, 상태 폴링, 로그 수집, 삭제를 담당하는 Executor.

**주요 기능**:
- Job manifest 자동 생성 (DNS-1123 호환 이름)
- 환경변수로 artifact URI 전달
- Job 상태 폴링 (성공/실패/타임아웃)
- Pod 로그 수집 및 반환
- Job 자동 정리 (cleanup)

**환경변수 전달**:
```python
env_vars = [
    V1EnvVar(name="CONFIG_FILE_URI", value=config_file_uri),
    V1EnvVar(name="EXPERIMENT_ID", value=experiment_id),
    V1EnvVar(name="SCENARIO_ID", value=scenario_id),
    V1EnvVar(name="VARIANT_ID", value=variant_id),
    V1EnvVar(name="NETWORK_ARTIFACT_URI", value=network_artifact_uri),
    V1EnvVar(name="DEMAND_ARTIFACT_URI", value=demand_artifact_uri),
    V1EnvVar(name="STORAGE_GATEWAY_URL", value=storage_gateway_url),
]
```

**Job 이름 생성** (DNS-1123 호환):
```
sumo-sim-exp001-baseline-20260507120000-a1b2c3d4
```
- 소문자, 숫자, 하이픈만 허용
- 63자 제한
- 타임스탬프 + UUID로 유니크 보장

**상태 폴링**:
- 주기: 5초 (기본값)
- 타임아웃: 600초 (기본값)
- 성공: `job.status.succeeded == 1`
- 실패: `job.status.failed == 1`

**리소스 제한**:
```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi
```

### 2. **job-runner.py** (200+ lines)

Kubernetes Job 내부에서 실행되는 스크립트.

**실행 흐름**:
1. 환경변수에서 artifact URI 읽기
2. StorageGateway를 통해 config/network/demand 파일 다운로드
3. `/tmp/sumo_job` 디렉토리에 파일 저장
4. SUMO 실행 (`sumo -c simulation.sumocfg`)
5. 결과 파일 업로드 (tripinfo.xml, summary.xml, queue.xml, emission.xml)

**환경변수**:
- `CONFIG_FILE_URI`: SUMO config 파일 URI (필수)
- `EXPERIMENT_ID`: 실험 ID
- `SCENARIO_ID`: 시나리오 ID
- `VARIANT_ID`: 변형 ID (baseline, alt_1 등)
- `NETWORK_ARTIFACT_URI`: 네트워크 파일 URI
- `DEMAND_ARTIFACT_URI`: 수요 파일 URI
- `STORAGE_GATEWAY_URL`: StorageGateway URL
- `SUMO_BINARY`: SUMO 바이너리 경로 (기본: sumo)

**에러 처리**:
- 다운로드 실패: 즉시 종료 (exit 1)
- SUMO 실행 실패: 즉시 종료 (exit 1)
- 업로드 실패: 경고 후 종료 (exit 1)
- 성공: exit 0

### 3. **Dockerfile.job** (30+ lines)

SUMO + Python 환경 이미지.

```dockerfile
FROM sumo:1.18.0
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install httpx aiofiles
COPY apps/simulator-runner/job-runner.py /app/job-runner.py
CMD ["python3", "/app/job-runner.py"]
```

**빌드 및 푸시**:
```bash
docker build -f apps/simulator-runner/Dockerfile.job -t simulation-runner:v1.0 .
docker tag simulation-runner:v1.0 <ECR_URI>/simulation-runner:v1.0
docker push <ECR_URI>/simulation-runner:v1.0
```

### 4. **RBAC** (k8s/rbac/sumo-runner.yaml, 100+ lines)

Kubernetes Job 생성/조회/삭제 권한.

**ServiceAccount**:
- `sumo-runner`: Job이 사용하는 ServiceAccount

**Role**:
- `sumo-runner-creator`: Job 생성/조회/삭제 권한
  - `batch/jobs`: create, get, list, watch, delete
  - `batch/jobs/status`: get
  - `pods`: get, list (로그 조회용)
  - `pods/log`: get

**RoleBinding**:
- `simulator-runner-job-creator`: simulator-runner 서비스에 권한 부여
  - Subject: `agent-t-app` ServiceAccount
  - Role: `sumo-runner-creator`

**적용**:
```bash
kubectl apply -f k8s/rbac/sumo-runner.yaml
```

### 5. **Kubernetes Deployment 업데이트** (k8s/apps/simulator-runner.yaml)

환경변수 추가:

```yaml
env:
  - name: SUMO_EXECUTOR_TYPE
    value: "kubernetes"
  - name: K8S_NAMESPACE
    value: "agent-t"
  - name: K8S_JOB_IMAGE
    value: "<ECR_URI>/simulation-runner:v1.0"
  - name: K8S_IMAGE_PULL_POLICY
    value: "Always"
  - name: K8S_JOB_TIMEOUT
    value: "600"
  - name: K8S_POLL_INTERVAL
    value: "5"
  - name: K8S_IN_CLUSTER
    value: "true"
  - name: STORAGE_GATEWAY_URL
    value: "http://storage-gateway:9002"
```

ServiceAccount 변경:
```yaml
serviceAccountName: agent-t-app
```

### 6. **테스트** (tests/test_kubernetes_executor.py, 400+ lines)

Mock Kubernetes client를 사용한 단위 테스트.

**테스트 케이스**:
- ✅ 환경 검증 (in-cluster, out-of-cluster)
- ✅ Job 이름 생성 (DNS-1123 호환, 63자 제한)
- ✅ Job manifest 생성 (환경변수, 리소스, ServiceAccount)
- ✅ Job 실행 성공 (Job succeeded)
- ✅ Job 실행 실패 (Job failed)
- ✅ Job 타임아웃
- ✅ 환경 검증 실패 시 에러 처리
- ✅ Pod 로그 없음 처리
- ✅ Job 삭제 실패 처리 (404)

**실행**:
```bash
pytest apps/simulator-runner/tests/test_kubernetes_executor.py -v
```

### 7. **문서** (K8S_JOB.md, KUBERNETES_JOB_IMPLEMENTATION.md)

- 아키텍처 설명
- 설정 방법
- 사용법
- Job manifest 예시
- 상태 폴링 로직
- 에러 처리
- 모니터링
- 문제 해결

---

## 배포 절차

### 1. RBAC 적용

```bash
kubectl apply -f k8s/rbac/sumo-runner.yaml
```

### 2. Job Runner 이미지 빌드 및 푸시

```bash
# 빌드
docker build -f apps/simulator-runner/Dockerfile.job -t simulation-runner:v1.0 .

# 태그
docker tag simulation-runner:v1.0 <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/simulation-runner:v1.0

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com

# 푸시
docker push <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/simulation-runner:v1.0
```

### 3. Simulator Runner 배포

```bash
# manifest 업데이트 (이미지 URI 변경)
vim k8s/apps/simulator-runner.yaml

# 적용
kubectl apply -f k8s/apps/simulator-runner.yaml

# 재시작
kubectl rollout restart deployment/simulator-runner -n agent-t
```

### 4. 상태 확인

```bash
# Deployment 확인
kubectl get deployment -n agent-t simulator-runner

# Pod 확인
kubectl get pods -n agent-t -l app=simulator-runner

# 로그 확인
kubectl logs -n agent-t -l app=simulator-runner --tail=50
```

---

## 사용 예시

### API 호출

```bash
curl -X POST http://simulator-runner:8004/simulation/run \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_001",
    "experiment_id": "exp_001",
    "variant_id": "baseline",
    "network_artifact_uri": "s3://agent-t-simulations/network_baseline.net.xml",
    "demand_artifact_uri": "s3://agent-t-simulations/demand_baseline.rou.xml",
    "simulation_duration_seconds": 3600,
    "output_options": {
      "tripinfo": true,
      "summary": true,
      "queue": true,
      "emission": true
    }
  }'
```

### Job 상태 확인

```bash
# Job 목록
kubectl get jobs -n agent-t -l app=sumo-runner

# 특정 Job 상태
kubectl describe job <job-name> -n agent-t

# Pod 목록
kubectl get pods -n agent-t -l app=sumo-runner

# Pod 로그
kubectl logs -n agent-t <pod-name>

# Job 삭제
kubectl delete job <job-name> -n agent-t
```

### Job 모니터링

```bash
# 실시간 Job 상태
kubectl get jobs -n agent-t -l app=sumo-runner -w

# 실시간 Pod 로그
kubectl logs -n agent-t -l app=sumo-runner --tail=100 -f

# 리소스 사용량
kubectl top pods -n agent-t -l app=sumo-runner
```

---

## 전환 가이드

### Local → Kubernetes Job

**변경 사항**:
```yaml
# Before (Local Executor)
env:
  - name: SUMO_EXECUTOR_TYPE
    value: "local"
  - name: SUMO_BINARY
    value: "/usr/local/bin/sumo"

# After (Kubernetes Job Executor)
env:
  - name: SUMO_EXECUTOR_TYPE
    value: "kubernetes"
  - name: K8S_NAMESPACE
    value: "agent-t"
  - name: K8S_JOB_IMAGE
    value: "<ECR_URI>/simulation-runner:v1.0"
  - name: K8S_IN_CLUSTER
    value: "true"
```

**장점**:
- ✅ API 서버 리소스 격리
- ✅ 동시 시뮬레이션 실행 가능
- ✅ 수평 확장
- ✅ Job별 리소스 제한
- ✅ 장시간 실행 가능

**단점**:
- ❌ Job 생성 오버헤드 (5-10초)
- ❌ 추가 이미지 필요 (simulation-runner)
- ❌ RBAC 설정 필요

---

## 성능 비교

| 항목 | Local Executor | Kubernetes Job Executor |
|------|----------------|-------------------------|
| 시작 시간 | ~1초 | ~5-10초 (Pod 생성) |
| 리소스 격리 | ❌ | ✅ |
| 동시 실행 | 제한적 (서버 리소스) | 무제한 (노드 리소스) |
| 장시간 실행 | HTTP 타임아웃 | 제한 없음 |
| 모니터링 | 어려움 | Kubernetes 네이티브 |
| 실패 처리 | 수동 | Job 자동 정리 |

---

## 문제 해결

### Job이 Pending 상태

**원인**: 리소스 부족

**해결**:
```bash
# 노드 리소스 확인
kubectl top nodes

# Job 리소스 요청 확인
kubectl describe job <job-name> -n agent-t

# 리소스 제한 감소 또는 노드 추가
```

### Job이 ImagePullBackOff

**원인**: 이미지 없음 또는 ECR 권한 부족

**해결**:
```bash
# 이미지 존재 확인
aws ecr describe-images --repository-name simulation-runner --region ap-northeast-2

# ECR 권한 확인
kubectl get serviceaccount agent-t-app -n agent-t -o yaml

# IRSA (IAM Role for Service Accounts) 확인
```

### Job이 Failed 상태

**원인**: SUMO 실행 실패, 다운로드 실패 등

**해결**:
```bash
# Pod 로그 확인
kubectl logs -n agent-t <pod-name>

# Pod 이벤트 확인
kubectl describe pod <pod-name> -n agent-t

# StorageGateway 연결 확인
kubectl get svc -n agent-t storage-gateway
```

### RBAC 권한 에러

**원인**: RoleBinding 누락 또는 ServiceAccount 불일치

**해결**:
```bash
# RoleBinding 확인
kubectl get rolebindings -n agent-t

# 권한 테스트
kubectl auth can-i create jobs --as=system:serviceaccount:agent-t:agent-t-app -n agent-t

# RBAC 재적용
kubectl apply -f k8s/rbac/sumo-runner.yaml
```

---

## 다음 단계

### 1. 리소스 최적화
- [ ] Job별 리소스 커스터마이징
- [ ] Spot Instance 활용 (비용 절감)
- [ ] Job 우선순위 설정

### 2. 모니터링 강화
- [ ] Prometheus 메트릭 추가
- [ ] Grafana 대시보드
- [ ] CloudWatch Logs 통합

### 3. 실패 처리 개선
- [ ] 재시도 정책 (backoffLimit)
- [ ] Job 실행 이력 DB 저장
- [ ] 실패 알림 (Slack, Email)

### 4. 고급 기능
- [ ] Job 큐잉 (동시 실행 제한)
- [ ] Job 우선순위
- [ ] 중간 체크포인트 저장
- [ ] 실시간 진행 상황 스트리밍

---

## 요약

✅ **KubernetesJobExecutor 구현** (400+ lines)  
✅ **job-runner.py 스크립트** (200+ lines)  
✅ **Dockerfile.job 작성** (30+ lines)  
✅ **RBAC manifest 작성** (100+ lines)  
✅ **Kubernetes Deployment 업데이트**  
✅ **Mock 테스트 작성** (400+ lines)  
✅ **문서화 완료** (K8S_JOB.md)  

**결과**: SUMO Runner를 API 서버와 분리하여 Kubernetes Job으로 실행 가능. 리소스 격리, 수평 확장, 동시 실행 지원.

**다음**: 프로덕션 배포 → 모니터링 → 성능 최적화

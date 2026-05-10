# Kubernetes Job Executor

SUMO Runner를 Kubernetes Job으로 실행하는 구현.

---

## 개요

기존 로컬 실행 방식의 한계:
- API 서버 리소스 부족 (SUMO는 CPU/메모리 집약적)
- 동시 시뮬레이션 실행 제한
- 장시간 실행 시 HTTP 타임아웃

해결책:
- **Kubernetes Job으로 분리 실행**
- 각 시뮬레이션이 독립된 Pod에서 실행
- 수평 확장 가능 (동시에 여러 시뮬레이션)
- 리소스 격리 및 제한

---

## 아키�ecture

```
┌─────────────────────┐
│ Simulator Runner    │
│ (FastAPI Service)   │
│                     │
│ ┌─────────────────┐ │
│ │KubernetesJob    │ │
│ │Executor         │ │
│ └────────┬────────┘ │
└──────────┼──────────┘
           │ creates
           ▼
┌──────────────────────┐
│ Kubernetes Job       │
│                      │
│ ┌──────────────────┐ │
│ │ Pod              │ │
│ │                  │ │
│ │ job-runner.py    │ │
│ │   ↓              │ │
│ │ 1. Download      │ │
│ │    artifacts     │ │
│ │ 2. Run SUMO      │ │
│ │ 3. Upload        │ │
│ │    results       │ │
│ └──────────────────┘ │
└──────────────────────┘
```

---

## 구성 요소

### 1. **KubernetesJobExecutor** (kubernetes_executor.py)

Kubernetes Job 생성 및 관리.

```python
from apps.simulatorrunner.executors.kubernetes_executor import KubernetesJobExecutor

executor = KubernetesJobExecutor(
    namespace="agent-t",
    image="simulation-runner:v1.0",
    timeout_seconds=600,
    in_cluster=True  # 클러스터 내부에서 실행
)

result = await executor.execute(
    config_file_path="s3://bucket/config.sumocfg",
    working_directory="/tmp/sumo",  # 사용되지 않음 (Job 내부에서 생성)
    experiment_id="exp_001",
    scenario_id="scenario_001",
    variant_id="baseline",
    network_artifact_uri="s3://bucket/network.net.xml",
    demand_artifact_uri="s3://bucket/demand.rou.xml",
)

print(result.success)  # True/False
print(result.stdout)
print(result.stderr)
```

**주요 메서드**:
- `validate_environment()`: Kubernetes 연결 및 네임스페이스 확인
- `execute()`: Job 생성 및 완료 대기
- `_create_job_manifest()`: Job YAML 생성
- `_wait_for_job_completion()`: Job 상태 폴링
- `_get_pod_logs()`: Pod 로그 수집
- `_cleanup_job()`: Job 삭제

### 2. **job-runner.py**

Kubernetes Job 내부에서 실행되는 스크립트.

**흐름**:
1. 환경변수에서 artifact URI 읽기
2. StorageGateway를 통해 config/network/demand 파일 다운로드
3. SUMO 실행
4. 결과 파일 업로드 (tripinfo.xml, summary.xml, queue.xml, emission.xml)

**환경변수**:
```bash
CONFIG_FILE_URI=s3://bucket/config.sumocfg
EXPERIMENT_ID=exp_001
SCENARIO_ID=scenario_001
VARIANT_ID=baseline
NETWORK_ARTIFACT_URI=s3://bucket/network.net.xml
DEMAND_ARTIFACT_URI=s3://bucket/demand.rou.xml
STORAGE_GATEWAY_URL=http://storage-gateway:9002
SUMO_BINARY=sumo
```

### 3. **Dockerfile.job**

SUMO + Python 환경 이미지.

```dockerfile
FROM sumo:1.18.0
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install httpx aiofiles
COPY apps/simulator-runner/job-runner.py /app/job-runner.py
CMD ["python3", "/app/job-runner.py"]
```

**빌드**:
```bash
docker build -f apps/simulator-runner/Dockerfile.job -t simulation-runner:v1.0 .
docker tag simulation-runner:v1.0 <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/simulation-runner:v1.0
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/simulation-runner:v1.0
```

### 4. **RBAC** (k8s/rbac/sumo-runner.yaml)

Kubernetes Job 생성 권한.

- **ServiceAccount**: `sumo-runner` (Job이 사용)
- **Role**: `sumo-runner-creator` (Job 생성/삭제/조회 권한)
- **RoleBinding**: `simulator-runner-job-creator` (simulator-runner 서비스에 권한 부여)

**적용**:
```bash
kubectl apply -f k8s/rbac/sumo-runner.yaml
```

---

## Job Manifest

KubernetesJobExecutor가 생성하는 Job manifest 예시:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: sumo-sim-exp001-baseline-20260507120000-a1b2c3d4
  namespace: agent-t
  labels:
    app: sumo-runner
    experiment-id: exp_001
    variant-id: baseline
spec:
  backoffLimit: 0  # 재시도 없음
  ttlSecondsAfterFinished: 3600  # 1시간 뒤 자동 삭제
  template:
    metadata:
      labels:
        app: sumo-runner
        job-name: sumo-sim-exp001-baseline-20260507120000-a1b2c3d4
        experiment-id: exp_001
        variant-id: baseline
    spec:
      restartPolicy: Never
      serviceAccountName: sumo-runner
      containers:
        - name: sumo-runner
          image: simulation-runner:v1.0
          imagePullPolicy: Always
          env:
            - name: CONFIG_FILE_URI
              value: s3://bucket/config.sumocfg
            - name: EXPERIMENT_ID
              value: exp_001
            - name: SCENARIO_ID
              value: scenario_001
            - name: VARIANT_ID
              value: baseline
            - name: NETWORK_ARTIFACT_URI
              value: s3://bucket/network.net.xml
            - name: DEMAND_ARTIFACT_URI
              value: s3://bucket/demand.rou.xml
            - name: STORAGE_GATEWAY_URL
              value: http://storage-gateway:9002
            - name: SUMO_BINARY
              value: sumo
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              cpu: 2000m
              memory: 4Gi
```

---

## 설정

### 환경변수 (simulator-runner 서비스)

```bash
# Kubernetes Job 사용
SUMO_EXECUTOR_TYPE=kubernetes

# Job 설정
K8S_NAMESPACE=agent-t
K8S_JOB_IMAGE=<AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/simulation-runner:v1.0
K8S_JOB_TIMEOUT=600
K8S_POLL_INTERVAL=5
K8S_IN_CLUSTER=true

# StorageGateway URL (Job에 전달)
STORAGE_GATEWAY_URL=http://storage-gateway:9002
```

### Kubernetes Deployment 수정

```yaml
# k8s/apps/simulator-runner.yaml
env:
  - name: SUMO_EXECUTOR_TYPE
    value: "kubernetes"
  - name: K8S_NAMESPACE
    value: "agent-t"
  - name: K8S_JOB_IMAGE
    value: "<AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/simulation-runner:v1.0"
  - name: K8S_IN_CLUSTER
    value: "true"
  - name: STORAGE_GATEWAY_URL
    value: "http://storage-gateway:9002"
```

---

## 사용법

### 1. RBAC 적용

```bash
kubectl apply -f k8s/rbac/sumo-runner.yaml
```

### 2. 이미지 빌드 및 푸시

```bash
docker build -f apps/simulator-runner/Dockerfile.job -t simulation-runner:v1.0 .
docker tag simulation-runner:v1.0 <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/simulation-runner:v1.0
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/simulation-runner:v1.0
```

### 3. Simulator Runner 재배포

```bash
kubectl apply -f k8s/apps/simulator-runner.yaml
kubectl rollout restart deployment/simulator-runner -n agent-t
```

### 4. 시뮬레이션 실행

```bash
curl -X POST http://simulator-runner:8005/simulation/run \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_001",
    "experiment_id": "exp_001",
    "variant_id": "baseline",
    "network_artifact_uri": "s3://bucket/network.net.xml",
    "demand_artifact_uri": "s3://bucket/demand.rou.xml",
    "simulation_duration_seconds": 3600,
    "output_options": {
      "tripinfo": true,
      "summary": true,
      "queue": true,
      "emission": true
    }
  }'
```

### 5. Job 상태 확인

```bash
# Job 목록
kubectl get jobs -n agent-t -l app=sumo-runner

# 특정 Job 상태
kubectl describe job <job-name> -n agent-t

# Pod 로그
kubectl logs -n agent-t -l job-name=<job-name>
```

---

## 상태 폴링

KubernetesJobExecutor는 Job이 완료될 때까지 주기적으로 상태를 확인:

```python
while True:
    job = batch_v1.read_namespaced_job_status(name=job_name, namespace=namespace)
    
    if job.status.succeeded:
        # 성공
        return True, stdout, stderr, output_files
    
    elif job.status.failed:
        # 실패
        return False, stdout, stderr, {}
    
    # 타임아웃 체크
    if elapsed > timeout_seconds:
        return False, stdout, "Job timeout", {}
    
    await asyncio.sleep(poll_interval_seconds)
```

---

## 리소스 제한

Job Pod에 리소스 제한 설정:

```yaml
resources:
  requests:
    cpu: 500m      # 최소 0.5 코어
    memory: 1Gi    # 최소 1GB
  limits:
    cpu: 2000m     # 최대 2 코어
    memory: 4Gi    # 최대 4GB
```

**조정 방법**:

KubernetesJobExecutor 생성 시 전달 (향후 구현):

```python
executor = KubernetesJobExecutor(
    resources={
        "requests": {"cpu": "1000m", "memory": "2Gi"},
        "limits": {"cpu": "4000m", "memory": "8Gi"}
    }
)
```

---

## 에러 처리

### Job 실패

- Job이 실패하면 `job.status.failed == 1`
- Pod 로그 수집 후 stderr 반환
- `ExecutionResult(success=False)`

### 타임아웃

- `timeout_seconds` 초과 시 Job 강제 종료
- stderr에 "Job timeout" 메시지

### Kubernetes API 에러

- Job 생성 실패, 네임스페이스 없음 등
- `ExecutionResult(success=False, stderr="Kubernetes API error")`

---

## 테스트

### 단위 테스트 (Mock)

```bash
pytest apps/simulator-runner/tests/test_kubernetes_executor.py -v
```

Mock을 사용하여 Kubernetes API 호출 없이 테스트.

### 통합 테스트 (Minikube)

```bash
# Minikube 시작
minikube start

# 네임스페이스 생성
kubectl create namespace agent-t

# RBAC 적용
kubectl apply -f k8s/rbac/sumo-runner.yaml

# 이미지 빌드 (Minikube Docker)
eval $(minikube docker-env)
docker build -f apps/simulator-runner/Dockerfile.job -t simulation-runner:v1.0 .

# Simulator Runner 배포
kubectl apply -f k8s/apps/simulator-runner.yaml

# 시뮬레이션 실행
kubectl port-forward -n agent-t svc/simulator-runner 8005:8005
curl -X POST http://localhost:8005/simulation/run -H "Content-Type: application/json" -d '...'

# Job 확인
kubectl get jobs -n agent-t
kubectl logs -n agent-t -l app=sumo-runner
```

---

## 모니터링

### Job 상태

```bash
kubectl get jobs -n agent-t -l app=sumo-runner -w
```

### Pod 로그

```bash
kubectl logs -n agent-t -l app=sumo-runner --tail=100 -f
```

### 리소스 사용량

```bash
kubectl top pods -n agent-t -l app=sumo-runner
```

### CloudWatch Logs (EKS)

FluentBit 또는 CloudWatch Container Insights로 자동 수집.

---

## 성능 최적화

### 1. 동시 실행 제한

```yaml
# k8s/apps/simulator-runner.yaml
env:
  - name: MAX_CONCURRENT_JOBS
    value: "10"
```

### 2. Job Cleanup

```yaml
spec:
  ttlSecondsAfterFinished: 3600  # 1시간 뒤 자동 삭제
```

수동 삭제:

```bash
kubectl delete jobs -n agent-t -l app=sumo-runner --field-selector status.successful=1
```

### 3. 리소스 Quota

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: sumo-runner-quota
  namespace: agent-t
spec:
  hard:
    requests.cpu: "20"
    requests.memory: "40Gi"
    limits.cpu: "40"
    limits.memory: "80Gi"
```

---

## 문제 해결

### Job이 Pending 상태

- 리소스 부족: 노드 추가 또는 리소스 제한 감소
- ImagePullBackOff: 이미지 경로 확인, ECR 권한 확인

### Job이 Failed 상태

```bash
# Pod 이벤트 확인
kubectl describe pod -n agent-t -l job-name=<job-name>

# Pod 로그 확인
kubectl logs -n agent-t -l job-name=<job-name>
```

### RBAC 권한 에러

```bash
# ServiceAccount 확인
kubectl get sa -n agent-t

# RoleBinding 확인
kubectl get rolebindings -n agent-t

# 권한 테스트
kubectl auth can-i create jobs --as=system:serviceaccount:agent-t:agent-t-app -n agent-t
```

---

## 다음 단계

- [ ] 리소스 제한 커스터마이징 지원
- [ ] Job 우선순위 설정
- [ ] Job 실행 이력 DB 저장
- [ ] Prometheus 메트릭 추가
- [ ] 실패 시 재시도 정책
- [ ] Spot Instance 활용

---

## 참고

- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [SUMO Documentation](https://sumo.dlr.de/docs/)

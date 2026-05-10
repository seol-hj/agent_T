# Common Library

Agent T 플랫폼의 **Gateway/Provider 추상화 계층** 공통 라이브러리

---

## 개요

모든 외부 의존성(LLM, Storage, Vector DB, Secrets 등)을 추상화하여:
- **Provider 교체가 쉽다** (Bedrock → OpenAI, S3 → MinIO)
- **테스트가 쉽다** (Mock Provider 사용)
- **추적/관찰이 쉽다** (메타데이터 자동 기록)
- **비즈니스 로직과 인프라 분리**

---

## 아키텍처

```
┌─────────────────────┐
│  Service (FastAPI)  │
└──────────┬──────────┘
           │ import common
           ▼
┌─────────────────────┐
│   Gateway Layer     │  ← 추상화 인터페이스
│  (Base Classes)     │
└──────────┬──────────┘
           │ 환경변수로 선택
           ▼
┌─────────────────────┐
│  Provider Layer     │  ← 실제 구현
│  (Implementations)  │
└─────────────────────┘
   │      │       │
   ▼      ▼       ▼
Bedrock  S3   Secrets
OpenAI  MinIO  Vault
Mock    Local  Env
```

---

## 포함된 Gateway

### 1. LLMGateway

**목적**: LLM API 호출 추상화

**Providers**:
- `MockLLMProvider` - 테스트용 더미 응답
- `BedrockProvider` - Amazon Bedrock (Claude, Titan 등)
- `LocalLLMProvider` - Ollama, llama.cpp (TODO)
- `OpenAIProvider` - OpenAI API (TODO)

**환경 변수**:
```bash
LLM_PROVIDER=mock          # mock | bedrock | local | openai
LLM_MODEL_ID=mock-model-v1  # Provider별 모델 ID
AWS_REGION=ap-northeast-2   # Bedrock용
```

**사용 예시**:
```python
from common import get_llm_gateway

# 환경변수 기반 자동 선택
llm = get_llm_gateway()

# 또는 명시적 선택
llm = get_llm_gateway(
    provider="bedrock",
    model_id="anthropic.claude-3-sonnet-20240229-v1:0"
)

# 텍스트 생성
response = await llm.generate(
    prompt="교통 시뮬레이션 시나리오를 생성해주세요",
    system_prompt="당신은 교통 전문가입니다",
    temperature=0.7,
    prompt_version="scenario-gen-v2.0",  # 추적용
)

print(response.content)
print(f"Model: {response.model_id}")
print(f"Provider: {response.provider}")
print(f"Latency: {response.latency_ms}ms")
print(f"Tokens: {response.total_tokens}")
```

**응답 형식** (LLMResponse):
```python
@dataclass
class LLMResponse:
    content: str                # 생성된 텍스트
    model_id: str               # 모델 ID
    provider: str               # Provider 이름
    prompt_version: str         # 프롬프트 버전 (추적용)
    latency_ms: float           # 응답 시간 (ms)
    usage: LLMUsageMetadata     # 토큰 사용량
    request_id: Optional[str]   # 요청 ID
    timestamp: datetime         # 타임스탬프
```

---

### 2. StorageGateway

**목적**: 파일 스토리지 추상화

**Providers**:
- `LocalStorageProvider` - 로컬 파일시스템
- `S3StorageProvider` - Amazon S3
- `MinIOStorageProvider` - MinIO (TODO)

**환경 변수**:
```bash
STORAGE_PROVIDER=local              # local | s3 | minio
STORAGE_BASE_PATH=./data            # local용
STORAGE_BUCKET=agent-t-scenarios    # S3/MinIO용
AWS_REGION=ap-northeast-2           # S3용
```

**사용 예시**:
```python
from common import get_storage_gateway

storage = get_storage_gateway()

# 파일 업로드
uri = await storage.upload(
    "scenarios/exp-001/scenario.json",
    b'{"duration": 3600}',
    content_type="application/json",
    metadata={"experiment_id": "exp-001"}
)

# 파일 다운로드
content = await storage.download("scenarios/exp-001/scenario.json")

# 파일 존재 확인
exists = await storage.exists("scenarios/exp-001/scenario.json")

# 파일 목록
files = await storage.list("scenarios/")

# Presigned URL 생성 (다운로드 링크)
url = await storage.get_url("scenarios/exp-001/scenario.json", expires_in=3600)
```

---

### 3. VectorStoreGateway (Placeholder)

**목적**: Vector DB 추상화 (RAG용)

**Providers**:
- `MockVectorStoreProvider` - 메모리 기반 Mock
- TODO: Pinecone, Weaviate, ChromaDB

**환경 변수**:
```bash
VECTOR_STORE_PROVIDER=mock
```

---

### 4. SimulationExecutionGateway

**목적**: 시뮬레이션 실행 방식 추상화

**Executors**:
- `DryRunExecutor` - 실행 없이 검증만
- `LocalSumoExecutor` - 로컬 SUMO 실행
- `KubernetesJobExecutor` - K8s Job으로 실행 (TODO)

**환경 변수**:
```bash
SIMULATION_EXECUTOR=dryrun   # dryrun | local_sumo | k8s_job
SUMO_HOME=/usr/share/sumo    # local_sumo용
```

**사용 예시**:
```python
from common import get_simulation_gateway

executor = get_simulation_gateway()

# 시뮬레이션 실행
result = await executor.execute(
    scenario_config={"duration": 3600},
    network_file="network.net.xml",
    route_file="routes.rou.xml",
    output_dir="/tmp/output"
)

print(result.simulation_id)
print(result.status)  # queued, running, completed, failed
print(result.duration_seconds)
print(result.output_files)

# 상태 조회
status = await executor.get_status(result.simulation_id)
```

---

### 5. SecretConfigProvider

**목적**: 비밀/설정 관리 추상화

**Providers**:
- `EnvVarProvider` - 환경 변수
- `AWSSecretsManagerProvider` - AWS Secrets Manager
- `FileBasedProvider` - 로컬 파일

**환경 변수**:
```bash
SECRET_PROVIDER=env      # env | aws | file
AWS_REGION=ap-northeast-2   # aws용
SECRETS_DIR=./secrets    # file용
```

**사용 예시**:
```python
from common import get_secret_provider

secrets = get_secret_provider()

# 비밀 조회
db_creds = await secrets.get_secret("database/credentials")
print(db_creds["username"])
print(db_creds["password"])

# 설정 조회
config = await secrets.get_config("app/config")
```

---

## 설치

### 공통 라이브러리

```bash
cd libs/common
pip install -r requirements.txt
```

### 테스트 실행

```bash
cd libs/common
pip install -r tests/requirements.txt
pytest tests/ -v
```

---

## 원칙

### 1. 직접 SDK 호출 금지

❌ **잘못된 방법**:
```python
import boto3

bedrock = boto3.client("bedrock-runtime")
response = bedrock.invoke_model(...)
```

✅ **올바른 방법**:
```python
from common import get_llm_gateway

llm = get_llm_gateway()
response = await llm.generate(...)
```

### 2. 환경 변수 기반 선택

Provider 선택은 **환경 변수**로:
```bash
# 개발 환경
LLM_PROVIDER=mock
STORAGE_PROVIDER=local

# 프로덕션 환경
LLM_PROVIDER=bedrock
STORAGE_PROVIDER=s3
```

### 3. 메타데이터 추적

모든 LLM 호출은 메타데이터를 기록:
- `model_id`: 사용한 모델
- `provider`: Provider 이름
- `prompt_version`: 프롬프트 버전
- `latency_ms`: 응답 시간

→ 디버깅, 비용 분석, 성능 모니터링에 활용

### 4. 테스트 가능

Mock Provider로 외부 의존성 없이 테스트:
```python
# 테스트
LLM_PROVIDER=mock pytest tests/
```

---

## 디렉토리 구조

```
libs/common/
├── __init__.py              # 공개 API
├── requirements.txt         # 의존성
├── models/
│   ├── __init__.py
│   └── llm_response.py      # LLMResponse 모델
├── gateways/
│   ├── __init__.py
│   ├── llm.py               # LLM Gateway
│   ├── storage.py           # Storage Gateway
│   ├── vector_store.py      # Vector Store Gateway
│   ├── simulation.py        # Simulation Gateway
│   └── secrets.py           # Secrets Gateway
└── tests/
    ├── __init__.py
    ├── requirements.txt     # 테스트 의존성
    ├── test_llm_gateway.py
    ├── test_storage_gateway.py
    └── test_simulation_gateway.py
```

---

## agent-service 통합 예시

```python
import sys
from pathlib import Path

# Common library를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "libs"))

from common import get_llm_gateway, get_storage_gateway

# Gateway 초기화
llm = get_llm_gateway()
storage = get_storage_gateway()

# 시나리오 생성
@app.post("/agent/generate")
async def generate_scenario(request: dict):
    response = await llm.generate(
        prompt=request["requirement"],
        system_prompt="당신은 교통 시나리오 생성 전문가입니다",
        prompt_version="scenario-gen-v2.0",
    )

    # Storage에 저장
    await storage.upload(
        f"scenarios/{scenario_id}.json",
        response.content.encode(),
        metadata={"model_id": response.model_id}
    )

    return {"scenario_id": scenario_id}
```

---

## Best Practices

### 1. Lazy 초기화

```python
_llm_gateway = None

def get_llm() -> LLMGateway:
    global _llm_gateway
    if _llm_gateway is None:
        _llm_gateway = get_llm_gateway()
    return _llm_gateway
```

### 2. 에러 처리

```python
response = await llm.generate(prompt)

if not response.success:
    # 에러 처리
    raise HTTPException(status_code=500, detail=response.error)

return response.content
```

### 3. 프롬프트 버전 관리

```python
# 프롬프트 변경 시 버전 업데이트
response = await llm.generate(
    prompt=prompt,
    prompt_version="scenario-gen-v2.1",  # v2.0 → v2.1
)

# 추적: 어떤 버전으로 생성되었는지 확인
print(response.prompt_version)
```

### 4. 비용 추적

```python
response = await llm.generate(prompt)

# 로그에 기록
logger.info(
    f"LLM Call: model={response.model_id}, "
    f"tokens={response.total_tokens}, "
    f"latency={response.latency_ms}ms"
)
```

---

## 다음 단계

1. **Bedrock 통합 테스트**: 실제 Bedrock API 호출
2. **S3 통합 테스트**: 실제 S3 버킷 사용
3. **추가 Provider 구현**:
   - OpenAI Provider
   - Local LLM Provider (Ollama)
   - Vector Store Providers (Pinecone, Weaviate)
4. **Observability**:
   - OpenTelemetry 통합
   - 비용 추적 대시보드
5. **Caching**:
   - LLM 응답 캐싱 (Redis)
   - 동일 프롬프트 중복 호출 방지

---

**버전**: 0.1.0

**상태**: Gateway 추상화 완료, 주요 Provider 구현 완료
